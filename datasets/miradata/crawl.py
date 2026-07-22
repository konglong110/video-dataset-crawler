"""
MiraData 采集脚本 —— TODO，尚未实现。

实现思路参照 datasets/videocc/crawl.py，需要额外处理：
1. 结构化 caption 是多字段 JSON，不是单一文本，落盘时建议整条存成
   datasets/miradata/captions/<video_id>.json，db 里 caption_path 指过去。
2. 注意跟 HD-VILA-100M 的视频源重叠，见 README「与其他数据集的重叠」。

用法约定（跟其他数据集保持一致，实现时照这个补上）：
    python datasets/miradata/crawl.py --register
    python datasets/miradata/crawl.py --limit 20
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "miradata"


def register():
    raise NotImplementedError(
        "TODO: 下载官方标注文件并解析，逐条调用 db.upsert_pending(DATASET, video_id, url)"
    )


def fetch_one(task: dict) -> dict:
    raise NotImplementedError(
        "TODO: 参照 datasets/videocc/crawl.py 的 fetch_one，用 "
        "common.youtube_fetch.download_youtube 下载，返回 dict(success, local_path, error)"
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
