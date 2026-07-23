# 工单 INFRA-6 — 统一日志系统

- **类型**：基础设施（`common/` 层，8 个数据集共用） · **依赖**：无 · **预估**：~0.5 人天
- **必读**：`docs/DEV_GUIDE.md`、`config.py`（已有 `LOG_DIR`）、`common/downloader.py`（现在用 `print`）
- **要改/新增**：新增 `common/logging_setup.py`；改 `config.py`（加日志级别配置）；把 `common/downloader.py` 的 `print` 换成 logger

## 目标

现在只有零散 `print`，排查问题、留存审计都不方便。用 Python 标准库 `logging` 做一个统一入口：
**同时输出到控制台 + 按数据集落文件**，格式统一，文件自动轮转不撑爆磁盘。**不引入第三方日志库。**

## 设计决策（照此实现）

1. **一个数据集一个日志文件**：`LOG_DIR/<dataset>.log`，用 `RotatingFileHandler`（如单文件 10MB、保留 5 份）。
2. **统一格式**：`时间 级别 [dataset] 消息`，例如 `2026-07-23 12:00:00 INFO [videocc] 下载成功 id=123`。
3. **级别可配**：`config.py` 加 `LOG_LEVEL = os.environ.get("VDC_LOG_LEVEL", "INFO")`。
4. **对外只暴露一个函数**：`get_logger(dataset: str) -> logging.Logger`，各脚本 `log = get_logger(DATASET)` 后用 `log.info/warning/error`。
5. 幂等：同一 dataset 重复调 `get_logger` 不重复挂 handler（防止日志重复打印）。

## 实现要求

1. 新建 `common/logging_setup.py`，实现 `get_logger(dataset)`：控制台 handler + 该数据集的 RotatingFileHandler，
   级别读 `config.LOG_LEVEL`，`logger.propagate = False`，重复调用不重复加 handler。
2. `config.py`：加 `LOG_LEVEL`（`LOG_DIR` 已存在，复用）。
3. 改 `common/downloader.py`：`run_batch` / `_handle_result` 里的 `print` 改成 `log.info` / `log.warning`
   （失败用 warning，成功可 info）。logger 用 `get_logger(dataset)`。

## 不要做

- 不引入 loguru 等第三方库（标准库够用）。
- 不改数据集脚本的业务逻辑，只替换输出方式。
- 不做日志上报/ELK 之类（超出范围）。

## 验收标准

1. `get_logger("videocc")` 后打日志，控制台能看到、`data/logs/videocc.log` 里也有同样内容，格式含 `[videocc]`。
2. 连续调用 `get_logger("videocc")` 两次，日志不重复打印（handler 没被加两遍）。
3. `VDC_LOG_LEVEL=WARNING` 时 info 级别不输出。
4. `run_batch` 跑一批（可用假 fetch_fn）时，成功/失败都进了日志文件而非只 print。

## 交付

- 提交到本窗口指派的开发分支，commit 说明"新增统一日志(控制台+按数据集轮转文件)"。
- 不创建 PR。回报：①改/增哪些文件 ②验收怎么验的 ③遗留问题。
