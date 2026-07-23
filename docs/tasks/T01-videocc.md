# 工单 T01 — 打通 VideoCC 端到端（含 schema 补齐）

> **状态：✅ 已验收（2026-07-23）** ｜ 实现分支 `claude/videocc-end-to-end-m4gl47`（commit `6cdc5d8`），待并入 main。
>
> **验收结论（架构师）**：5 项验收全部实跑通过——① 全新库含新列；② `--register` 正确写入 clip 起止 + 多 clip 区分；
> ③ `fetch_one` 把 start/end 转 HH:MM:SS 传入 `download_youtube`，且 `start=0`（片头）边界处理正确；
> ④ 其余 7 个数据集 import 不受影响；⑤ 无脏文件提交。
>
> **两处对工单的偏差，均接受**：
> 1. **单位/列名**：工单原定"秒 REAL / `clip_start_sec`"，实现改为"**微秒 INTEGER / `clip_start_us`**"。
>    接受——微秒无损保留源精度，且复用现成 `us_to_timestamp`，比原方案更好。**以实现为准**，
>    已同步 `ARCHITECTURE.md`；后续 HD-VILA(T07) 按 `clip_start_us`/`clip_end_us` 复用。
> 2. **额外加了幂等迁移**（`_apply_migrations`，老库自动补列），超出"老库重建即可"的要求，是有价值的加固，接受。
>
> **流程提醒**：偏差①改动了工单里标注"不要自行更改"的决策——即使结果更优，按 `DEV_GUIDE §6`
> 应在回报里显式指出该偏差并说明理由，供架构师确认，而非默默改掉。下次注意。
> 以下为原始工单内容，存档备查。

---

- **类型**：A 类（YouTube 爬取） · **依赖**：无 · **预估**：~1 人天
- **必读**：`docs/ARCHITECTURE.md`、`docs/DEV_GUIDE.md`、`README.md`、`datasets/videocc/README.md`
- **要改的文件**：`common/db.py`、`datasets/videocc/crawl.py`（只动这两处及 videocc 目录，**不碰其他数据集**）

## 目标

VideoCC 是全项目第一个端到端样板，也是另外几个 A 类数据集照抄的骨架。当前 `datasets/videocc/crawl.py`
已有雏形，但 `fetch_one` 是简化版——因为 `video_assets` 表**没有字段存 clip 起止时间戳**，
所以现在只能整段下 YouTube 视频、无法按 clip 截取。本工单先补 schema，再把 VideoCC 做透。

## 架构师已定的设计决策（不要自行更改）

1. **时间戳的规范单位是"秒"（REAL）**。DB 里存秒，不存 HH:MM:SS 字符串。理由：秒无歧义、便于算时长。
2. clip 时间戳作为**通用列**加在 `video_assets` 上（`clip_start_sec` / `clip_end_sec`），
   **不要**为 VideoCC 单独建辅助表——保持单表设计，后续 HD-VILA 切片复用同两列。
3. **喂给 `download_youtube` 前**再把秒转成它文档约定的 `HH:MM:SS` 字符串（尊重 youtube_fetch 的现有契约）。

## Phase 0 — 补 schema（前置，INFRA-1）

改 `common/db.py`：

1. `_SCHEMA` 的 `video_assets` 表增加两列：
   ```sql
   clip_start_sec REAL,
   clip_end_sec   REAL,
   ```
   放在合适位置（如 `duration_sec` 附近），**不要改动已有列名、状态常量、表名、索引**。
2. `upsert_pending()` 增加两个**可选**参数 `clip_start_sec=None`、`clip_end_sec=None`，
   INSERT 时带上；保持向后兼容——其他数据集不传，就是 NULL，不受影响。
3. 若 `mark_result` 之外需要读回这两列，`fetch_pending()` 已是 `SELECT *`，天然带出，无需改。

> 兼容性注意：`init_db()` 用 `CREATE TABLE IF NOT EXISTS`，对**已存在的旧库不会自动加列**。
> 脚手架阶段可接受"删掉旧 `video_assets.db` 重建"。请在回报里注明这一点（老库需重新 init）。

## Phase 1 — 补全 VideoCC

改 `datasets/videocc/crawl.py`：

1. **`register()`**：
   - 读 `meta/videocc_raw.csv`（无表头，列序：`video_url, start_us, end_us, caption`）。
   - 微秒 → 秒（`/ 1_000_000`），把 `clip_start_sec` / `clip_end_sec` 传给 `upsert_pending`。
   - `source_video_id` 维持现有做法：URL 里的 video id + `_{start_us}`（保证同一原视频多 clip 不互相覆盖）。
   - CSV 不存在时保持现有的清晰提示，不要抛栈。
2. **`fetch_one()`**：
   - 从 `task` 取 `clip_start_sec` / `clip_end_sec`，转成 `HH:MM:SS`（可复用/改写现有 `us_to_timestamp`，
     或新增一个 `sec_to_hms` 小函数），作为 `start` / `end` 传给
     `download_youtube(task["source_url"], out_path, start=..., end=...)`，做**片段下载**而非整段下。
   - 返回 `{"success": ok, "local_path": out_path if ok else None, "error": err}`。
   - 落盘路径继续用 `storage.local_path_for(DATASET, task["source_video_id"])`。
3. 删掉 `fetch_one` 里那段"schema 没字段所以简化了"的 TODO 注释（已解决）。

## 不要做

- 不要真去下载官方 CSV / 不要联网跑全量（那是运行期的事，不属于本工单）。
- 不要引入新依赖（pandas 已在 requirements）。
- 不要动 `common/downloader.py`、`storage.py`、`youtube_fetch.py` 的对外签名。

## 验收标准（提交前逐条自查，并在回报里对应说明）

1. `python scripts/init_db.py` 在**全新库**上建表成功，且新库含 `clip_start_sec` / `clip_end_sec` 两列
   （可 `sqlite3 video_assets.db ".schema video_assets"` 或 `PRAGMA table_info` 验证）。
2. 造一个 3~5 行的假 `datasets/videocc/meta/videocc_raw.csv`（**不要提交这个假数据**），
   `python datasets/videocc/crawl.py --register` 能解析入库，且抽查记录 `clip_start_sec/clip_end_sec` 有正确的秒值。
3. `fetch_one` 的调用链确实把 `start`/`end`（HH:MM:SS）传进了 `download_youtube`
   ——无需真联网，重点是参数正确（可临时打印/单测验证，验证后移除打印）。
4. 其他 7 个数据集的 `crawl.py --help` 仍能正常跑（没被你的 db.py 改动带崩）。
5. 未误提交 `data/`、`*.db`、假 CSV。

## 交付

- 提交到本窗口指派的开发分支，commit message 说明"补 clip 时间戳列 + VideoCC 片段下载打通"。
- **不创建 PR**（除非另行要求）。
- 回报：① 改了哪些文件 ② 上面 5 条验收各自怎么验的（贴命令/输出）③ 遗留问题（尤其"老库需重建"要点出来）。
