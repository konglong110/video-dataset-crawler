"""MD5 计算 + 跨数据集去重。下载成功后必须调用一次。"""
import hashlib
from pathlib import Path


def file_md5(path: str, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def dedupe_or_keep(path: str) -> tuple[str, bool]:
    """
    计算 MD5，如果这份内容在库里已经存在（来自任意数据集），
    删掉这份新文件，返回 (md5, True 表示是重复) 交给调用方决定要不要写软链接。
    """
    from . import db  # 延迟导入，避免 dedupe 单独被测试时也要求配好 config

    md5 = file_md5(path)
    if db.is_duplicate_md5(md5):
        Path(path).unlink(missing_ok=True)
        return md5, True
    return md5, False
