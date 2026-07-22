"""
InternVid 采集脚本 —— TODO，尚未实现。

标注文件可直接从 HuggingFace/OpenDataLab 下载，不需要爬取这一步，
省下来的时间可以多花在 fetch_one 的 YouTube 下载稳定性上。

用法约定：
    python datasets/internvid/crawl.py --register --subset 10m-flt
    python datasets/internvid/crawl.py --limit 20
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "internvid"


def register(subset: str = "10m-flt"):
    raise NotImplementedError(
        "TODO: 用 huggingface_hub.hf_hub_download 或手动下载标注文件，"
        "解析后 upsert_pending。subset 参数用于选择全量还是精选子集，先跟客户确认要哪个。"
    )


def fetch_one(task: dict) -> dict:
    raise NotImplementedError(
        "TODO: 同 videocc 模式，调用 common.youtube_fetch.download_youtube。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--subset", choices=["full", "10m-flt", "18m-aesthetics"], default="10m-flt")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db.init_db()

    if args.register:
        register(args.subset)
    else:
        from common.downloader import run_batch
        run_batch(DATASET, fetch_one, limit=args.limit)
