"""
VideoCC 采集脚本。

这个数据集结构最简单，写成了相对完整的参考实现，其余 7 个数据集的 crawl.py
可以照着这个模式改（"注册任务 -> run_batch(fetch_one)"这个骨架是通用的）。

用法：
    python datasets/videocc/crawl.py --register        # 第一次跑，把 CSV 解析进数据库
    python datasets/videocc/crawl.py --limit 20         # 下载一批，可反复跑直到跑完
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd

from common import db
from common.downloader import run_batch
from common.youtube_fetch import download_youtube
from common.storage import local_path_for

DATASET = "videocc"
META_CSV = Path(__file__).parent / "meta" / "videocc_raw.csv"


def us_to_timestamp(microseconds: int) -> str:
    total_sec = int(microseconds) // 1_000_000
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def register():
    """
    TODO: 先把官方 CSV 下载到 META_CSV（见 README），这里只负责解析入库。
    官方 CSV 目前没有表头，列顺序是: video_url, start_us, end_us, caption
    """
    if not META_CSV.exists():
        print(f"没找到 {META_CSV}，先按 README 说明下载官方 CSV 到这个路径。")
        return

    df = pd.read_csv(META_CSV, header=None,
                      names=["video_url", "start_us", "end_us", "caption"])
    for _, row in df.iterrows():
        # 用 URL 里的 video id 当唯一键；不同 clip 共享同一个 video_id 时
        # source_video_id 需要带上时间戳做区分，避免多个 clip 互相覆盖
        video_id = row["video_url"].rstrip("/").split("=")[-1] + f"_{row['start_us']}"
        db.upsert_pending(DATASET, video_id, source_url=row["video_url"])
    print(f"[{DATASET}] 已注册 {len(df)} 条任务")


def fetch_one(task: dict) -> dict:
    out_path = str(local_path_for(DATASET, task["source_video_id"]))
    # TODO: 这里简化了，实际应该从 db 里把 start/end 时间戳也存下来一起取出，
    # 当前 schema 没有单独字段存 caption/start/end，需要的话在 db.py 的
    # video_assets 表里加列，或者另建一张 videocc_clips 辅助表存这些信息。
    ok, err = download_youtube(task["source_url"], out_path)
    return {"success": ok, "local_path": out_path if ok else None, "error": err}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true", help="解析CSV并注册任务到数据库")
    parser.add_argument("--limit", type=int, default=20, help="本次下载多少条")
    args = parser.parse_args()

    db.init_db()

    if args.register:
        register()
    else:
        run_batch(DATASET, fetch_one, limit=args.limit)
