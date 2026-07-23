"""
全局配置。所有数据集脚本、公共模块都从这里读配置，不要在业务代码里硬编码。
"""
import os
from pathlib import Path

# ---------- 路径 ----------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("VDC_DATA_ROOT", PROJECT_ROOT / "data"))

HOT_DIR = DATA_ROOT / "hot"        # 当前正在用/处理中的子集
WARM_DIR = DATA_ROOT / "warm"      # 下载完暂不用，等待转存
LOG_DIR = DATA_ROOT / "logs"

for _d in (HOT_DIR, WARM_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------- 日志 ----------
# 统一日志级别，供 common/logging_setup.py 读取；控制台 + 按数据集落 LOG_DIR/<dataset>.log
LOG_LEVEL = os.environ.get("VDC_LOG_LEVEL", "INFO")   # DEBUG | INFO | WARNING | ERROR

# ---------- 数据库 ----------
# 默认用 SQLite，零配置直接跑；后续量大了可以切 MySQL（改这里 + common/db.py 的连接部分）
DB_BACKEND = os.environ.get("VDC_DB_BACKEND", "sqlite")  # "sqlite" | "mysql"
SQLITE_PATH = str(PROJECT_ROOT / "video_assets.db")

MYSQL_CONFIG = {
    "host": os.environ.get("VDC_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("VDC_MYSQL_PORT", 3306)),
    "user": os.environ.get("VDC_MYSQL_USER", "root"),
    "password": os.environ.get("VDC_MYSQL_PASSWORD", ""),
    "database": os.environ.get("VDC_MYSQL_DB", "video_datasets"),
}

# ---------- 网络 / 代理 ----------
# WSL 环境下常见走本地代理，按需修改或留空（留空则不走代理）
HTTP_PROXY = os.environ.get("VDC_HTTP_PROXY", "")   # 例如 "http://127.0.0.1:8118"
HTTPS_PROXY = os.environ.get("VDC_HTTPS_PROXY", HTTP_PROXY)

# ---------- 并发 / 重试 ----------
MAX_WORKERS = int(os.environ.get("VDC_MAX_WORKERS", 4))   # 多进程下载并发数，先保守设置防止被限流
MAX_RETRIES = int(os.environ.get("VDC_MAX_RETRIES", 3))
RETRY_BACKOFF_SEC = 10          # 重试间隔基数，实际等待 = RETRY_BACKOFF_SEC * 重试次数
REQUEST_TIMEOUT_SEC = 30

# ---------- yt-dlp ----------
YTDLP_FORMAT = os.environ.get("VDC_YTDLP_FORMAT", "bestvideo[height<=1080]+bestaudio/best")

# ---------- 邮件告警 ----------
# 全部走环境变量，禁止硬编码密码。未启用（默认）或配置缺全时，common/notify.py
# 会静默跳过并记日志，绝不因发信失败把主流程带崩。
# 端口约定：465 走 SSL，其余（如 587）走 STARTTLS。
SMTP_HOST = os.environ.get("VDC_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("VDC_SMTP_PORT", 465))
SMTP_USER = os.environ.get("VDC_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("VDC_SMTP_PASSWORD", "")
ALERT_FROM = os.environ.get("VDC_ALERT_FROM", "")
ALERT_TO = os.environ.get("VDC_ALERT_TO", "")           # 收件人，多个用逗号分隔
ALERT_ENABLED = os.environ.get("VDC_ALERT_ENABLED", "0")  # "1" 开启，默认 "0" 关闭
