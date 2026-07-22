"""
LVD-2M 采集脚本 —— TODO，尚未实现。

三个来源(youtube/hdvg/webvid)分开处理，见本目录 README。
建议 register() 按 split 字段分别调用不同的 fetch 实现，而不是用一个 fetch_one
处理所有 split（三种来源的下载方式完全不同）。

用法约定：
    python datasets/lvd_2m/crawl.py --register
    python datasets/lvd_2m/crawl.py --limit 20 --split youtube
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "lvd_2m"


def register():
    raise NotImplementedError(
        "TODO: 下载官方 annotation 文件，按 split 字段(youtube/hdvg/webvid)分别"
        "upsert_pending，source_video_id 建议带上 split 前缀区分。"
    )


def fetch_one(task: dict) -> dict:
    raise NotImplementedError(
        "TODO: 根据 source_video_id 前缀判断走哪种下载方式："
        "youtube -> common.youtube_fetch；"
        "hdvg -> 先查 hd_vg_130m 数据集是否已下载同一视频，是则软链接，否则走同样的YouTube爬取；"
        "webvid -> 官方源不稳定，需要单独调研当前可用下载方式。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--split", choices=["youtube", "hdvg", "webvid"], default=None)
    args = parser.parse_args()

    db.init_db()

    if args.register:
        register()
    else:
        from common.downloader import run_batch
        run_batch(DATASET, fetch_one, limit=args.limit)
