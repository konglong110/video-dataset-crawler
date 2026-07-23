# 工单 INFRA-5 — 重试退避机制（真正落地）

- **类型**：基础设施（`common/` 层，8 个数据集共用） · **依赖**：无（建议 INFRA-6 日志先做，便于观察） · **预估**：~0.5 人天
- **必读**：`docs/ARCHITECTURE.md`（状态机）、`common/downloader.py`（现有占位 `time.sleep(0)`）、`common/db.py`（`bump_retry`）
- **要改**：`common/db.py`、`common/downloader.py`

## 目标

现在重试是"半成品"：`bump_retry` 会计数并在超限时置 `RETRY_EXCEEDED`，但**没有真正的退避**——
`downloader._handle_result` 里是 `time.sleep(0)` 占位。失败任务立刻又可被取出重试，容易在被限流时继续硬撞。
本工单让重试**按 `RETRY_BACKOFF_SEC * 重试次数` 的间隔延后**，且要能跨进程/跨重启生效（符合断点续传设计）。

## 设计决策（照此实现）

1. **用"下次可重试时间"驱动，而不是在 worker 里 sleep 阻塞**（阻塞会占死多进程 worker，也扛不住程序重启）。
   给 `video_assets` 加一列 `next_retry_at TEXT`（ISO 时间字符串，NULL 表示随时可取）。
2. `bump_retry` 失败时：`next_retry_at = now + RETRY_BACKOFF_SEC * retry_count` 秒。
3. `fetch_pending` 只取 `next_retry_at IS NULL 或 next_retry_at <= now` 的任务——退避期内的自动跳过，等下一轮再取。
4. 沿用 T01 的幂等迁移（`_apply_migrations`）给老库补这一列。
5. 删掉 `downloader._handle_result` 里的 `time.sleep(0)` 占位（退避改由 DB 时间控制，不再靠 sleep）。

## 实现要求

1. `common/db.py`：
   - `_SCHEMA` + `_MIGRATIONS` 加 `next_retry_at TEXT`。
   - `bump_retry`：未超限回 PENDING 时写入 `next_retry_at`；超限置 RETRY_EXCEEDED（此时 next_retry_at 可不管）。
   - `fetch_pending`：SQL 加 `AND (next_retry_at IS NULL OR next_retry_at <= ?)`，参数传当前 UTC ISO 时间。
2. `common/downloader.py`：去掉 `time.sleep(0)` 占位那段（连同已过时的注释）。失败路径仍走 `bump_retry`。

## 不要做

- 不在 worker 进程里 `time.sleep` 长时间阻塞。
- 不引入 Celery/APScheduler 等调度库（DB 时间戳足够）。
- 不改状态常量语义（0/1/2/3 含义不变）。

## 验收标准

1. 新库/老库经 `init_db()` 后都含 `next_retry_at` 列（老库走迁移补上）。
2. 造一条任务，让它失败一次：`bump_retry` 后该行 `download_status=0` 且 `next_retry_at` ≈ now + `RETRY_BACKOFF_SEC`。
3. 紧接着 `fetch_pending` **取不到**这条（在退避窗口内）；把 `next_retry_at` 手动改成过去时间后，又能取到。
4. 重试到达 `MAX_RETRIES` 时状态变为 `3 RETRY_EXCEEDED`，不再被 `fetch_pending` 取出。

## 交付

- 提交到本窗口指派的开发分支，commit 说明"重试退避:加 next_retry_at,退避期内不取任务"。
- 不创建 PR。回报：①改哪些文件 ②验收怎么验的 ③遗留问题。
