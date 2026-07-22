"""
video_assets 索引表：所有数据集的下载任务、去重、状态都记录在这一张表里，
不要靠扫文件系统来判断"哪些下载过了"。

默认走 SQLite（零配置），量大后可以切 MySQL —— 表结构不变，只换连接方式，
所以 datasets/*/crawl.py 里应该只调用本模块提供的函数，不要直接写 SQL。
"""
import sqlite3
import datetime
from contextlib import contextmanager

from config import DB_BACKEND, SQLITE_PATH, MYSQL_CONFIG

# 下载状态常量
STATUS_PENDING = 0
STATUS_SUCCESS = 1
STATUS_INVALID = 2      # 源链接失效 / 不可用，不再重试
STATUS_RETRY_EXCEEDED = 3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS video_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset TEXT NOT NULL,
    source_video_id TEXT NOT NULL,
    source_url TEXT,
    local_path TEXT,
    resolution TEXT,
    duration_sec REAL,
    md5 TEXT,
    caption_path TEXT,
    download_status INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_msg TEXT,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(dataset, source_video_id)
);
CREATE INDEX IF NOT EXISTS idx_status ON video_assets(dataset, download_status);
CREATE INDEX IF NOT EXISTS idx_md5 ON video_assets(md5);
"""


@contextmanager
def get_conn():
    """
    统一连接入口。当前只实现了 sqlite；MySQL 分支留了位置，
    真要切换时装 pymysql 后把下面这段接上（表结构直接复用 _SCHEMA，语法基本兼容，
    AUTOINCREMENT 需要改成 AUTO_INCREMENT）。
    """
    if DB_BACKEND == "sqlite":
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    elif DB_BACKEND == "mysql":
        raise NotImplementedError(
            "MySQL 分支待接入：pip install pymysql，然后参照 MYSQL_CONFIG 用 "
            "pymysql.connect(**MYSQL_CONFIG) 实现，返回对象需兼容 execute/commit 用法。"
        )
    else:
        raise ValueError(f"未知 DB_BACKEND: {DB_BACKEND}")


def init_db():
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


def upsert_pending(dataset: str, source_video_id: str, source_url: str = None):
    """登记一条待下载任务，已存在则忽略（不会重置已成功的状态）。"""
    now = datetime.datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO video_assets (dataset, source_video_id, source_url,
                                       download_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(dataset, source_video_id) DO NOTHING
            """,
            (dataset, source_video_id, source_url, STATUS_PENDING, now, now),
        )
        conn.commit()


def fetch_pending(dataset: str, limit: int = 100):
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT * FROM video_assets
            WHERE dataset = ? AND download_status = ?
            ORDER BY id LIMIT ?
            """,
            (dataset, STATUS_PENDING, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def mark_result(record_id: int, status: int, local_path: str = None,
                 md5: str = None, duration_sec: float = None,
                 resolution: str = None, error_msg: str = None):
    now = datetime.datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE video_assets
            SET download_status = ?, local_path = COALESCE(?, local_path),
                md5 = COALESCE(?, md5), duration_sec = COALESCE(?, duration_sec),
                resolution = COALESCE(?, resolution), error_msg = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (status, local_path, md5, duration_sec, resolution, error_msg, now, record_id),
        )
        conn.commit()


def bump_retry(record_id: int, max_retries: int):
    """重试计数 +1，超过上限则标记为 RETRY_EXCEEDED。"""
    with get_conn() as conn:
        cur = conn.execute("SELECT retry_count FROM video_assets WHERE id = ?", (record_id,))
        row = cur.fetchone()
        retry_count = (row["retry_count"] if row else 0) + 1
        status = STATUS_RETRY_EXCEEDED if retry_count >= max_retries else STATUS_PENDING
        conn.execute(
            "UPDATE video_assets SET retry_count = ?, download_status = ? WHERE id = ?",
            (retry_count, status, record_id),
        )
        conn.commit()


def is_duplicate_md5(md5: str) -> bool:
    """跨数据集查重：同一份视频被多个数据集引用时，用这个避免重复占用存储。"""
    with get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM video_assets WHERE md5 = ? LIMIT 1", (md5,))
        return cur.fetchone() is not None


def stats(dataset: str = None):
    with get_conn() as conn:
        if dataset:
            cur = conn.execute(
                "SELECT download_status, COUNT(*) c FROM video_assets WHERE dataset = ? GROUP BY download_status",
                (dataset,),
            )
        else:
            cur = conn.execute(
                "SELECT dataset, download_status, COUNT(*) c FROM video_assets GROUP BY dataset, download_status"
            )
        return [dict(r) for r in cur.fetchall()]
