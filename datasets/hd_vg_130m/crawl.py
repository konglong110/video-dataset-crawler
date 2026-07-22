"""
HD-VG-130M 采集脚本 —— TODO，尚未实现。

规模最大（130M 条），务必分批处理，不要一次性读全量元数据进内存/一次性
upsert 全部任务。建议先在 register() 里加一个 --sample-size 参数,
小规模验证流程跑通了再考虑全量。

用法约定：
    python datasets/hd_vg_130m/crawl.py --register --sample-size 10000
    python datasets/hd_vg_130m/crawl.py --limit 50
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "hd_vg_130m"


def register(sample_size: int = None):
    raise NotImplementedError(
        "TODO: 手动下载 Google Drive 元数据文件后，分批(chunksize)解析并 upsert_pending，"
        "sample_size 不为 None 时只注册前 N 条，用于先验证流程。"
    )


def fetch_one(task: dict) -> dict:
    raise NotImplementedError(
        "TODO: 同 videocc 模式，调用 common.youtube_fetch.download_youtube。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db.init_db()

    if args.register:
        register(args.sample_size)
    else:
        from common.downloader import run_batch
        run_batch(DATASET, fetch_one, limit=args.limit)
