"""
HD-VILA-100M 采集脚本 —— TODO，尚未实现。

关键点：一个原始视频对应多个 clip，下载粒度应该是"按 video_id 下载原视频一次，
本地切出多个 clip"，不要对每个 clip 都发一次下载请求。
caption 获取路径需要先人工确认，见本目录 README。

用法约定：
    python datasets/hd_vila_100m/crawl.py --register
    python datasets/hd_vila_100m/crawl.py --limit 20
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "hd_vila_100m"


def register():
    raise NotImplementedError(
        "TODO: 解析官方 jsonlines 元数据，source_video_id 用 clip_id，"
        "source_url 存原始 video_id 对应的 YouTube 链接 + span 信息"
        "（span 目前没有单独字段，需要在 db.py 加列或另建辅助表存)。"
    )


def fetch_one(task: dict) -> dict:
    raise NotImplementedError(
        "TODO: 先检查同一个 video_id 是否已经下载过原始视频（避免重复下载整段原片），"
        "参考官方 src/cut_videos.py 的切片逻辑本地切出对应 clip。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db.init_db()

    if args.register:
        register()
    else:
        from common.downloader import run_batch
        run_batch(DATASET, fetch_one, limit=args.limit)
