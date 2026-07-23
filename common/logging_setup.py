"""
统一日志入口。所有数据集脚本、公共模块都用 get_logger(dataset) 拿 logger，
不要各自 print 或自己 basicConfig —— 这样格式统一、按数据集落文件、还能自动轮转。

只用标准库 logging，不引第三方（loguru 等）。
"""
import logging
from logging.handlers import RotatingFileHandler

from config import LOG_DIR, LOG_LEVEL

# 统一格式：时间 级别 [dataset] 消息，例如
# 2026-07-23 12:00:00 INFO [videocc] 下载成功 id=123
_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 单文件 10MB、保留 5 份：长时间无人值守跑，防止日志把磁盘写爆
_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5


def get_logger(dataset: str) -> logging.Logger:
    """
    拿到某个数据集专属的 logger：控制台 + LOG_DIR/<dataset>.log（轮转）双路输出。

    幂等：同一 dataset 重复调用不会重复挂 handler（否则同一条日志会成倍打印）。
    logger 名直接用 dataset，这样格式里的 %(name)s 就是 [dataset]。
    """
    logger = logging.getLogger(dataset)
    logger.setLevel(LOG_LEVEL)
    # 不往 root logger 冒泡，避免和别的库在 root 上挂的 handler 造成重复输出
    logger.propagate = False

    # 已经挂过 handler 就直接返回，保证幂等（防止重复打印）
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    # 控制台输出
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 按数据集落文件，超过大小自动轮转
    file_handler = RotatingFileHandler(
        LOG_DIR / f"{dataset}.log",
        maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
