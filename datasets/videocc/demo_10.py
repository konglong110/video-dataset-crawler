"""
VideoCC Demo：采集 10 条数据，看看端到端跑出来长什么样。

用法（在项目根目录跑）：
    pip install -r requirements.txt
    python datasets/videocc/demo_10.py

前置条件：
    1. yt-dlp 已安装（pip install yt-dlp）
    2. 如果在墙内，config.py 里的 HTTP_PROXY 要配好，否则 YouTube 下不动
    3. 不需要提前下载官方 CSV —— 脚本自动拉取前 10 行

产出：
    - data/warm/videocc/ 目录下的 .mp4 片段文件
    - video_assets.db 里的记录（脚本末尾会打印出来）
"""
import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from io import StringIO

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from common import db
from common.youtube_fetch import download_youtube
from common.storage import local_path_for
from common.dedupe import file_md5
from config import SQLITE_PATH

DATASET = "videocc"
DEMO_LIMIT = 10
CSV_URL = "https://storage.googleapis.com/videocc-data/videocc.tsv"


def us_to_timestamp(microseconds: int) -> str:
    total_sec = int(microseconds) // 1_000_000
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def fetch_csv_head(n: int = DEMO_LIMIT) -> pd.DataFrame:
    """从官方地址拉 CSV 的前 n 行，不下载整个文件。"""
    import requests

    print(f"[1/4] 从官方地址拉取前 {n} 行元数据...")
    print(f"      URL: {CSV_URL}")

    resp = requests.get(CSV_URL, stream=True, timeout=30)
    resp.raise_for_status()

    lines = []
    for line in resp.iter_lines(decode_unicode=True):
        if line:
            lines.append(line)
        if len(lines) >= n:
            break
    resp.close()

    # 官方文件是 TSV（tab 分隔），列顺序: video_url, start_us, end_us, caption
    text = "\n".join(lines)
    df = pd.read_csv(StringIO(text), sep="\t", header=None,
                     names=["video_url", "start_us", "end_us", "caption"])
    print(f"      拿到 {len(df)} 条，前 3 条预览：")
    for i, row in df.head(3).iterrows():
        clip_sec = (int(row["end_us"]) - int(row["start_us"])) / 1_000_000
        print(f"        [{i}] {row['video_url']}  clip={clip_sec:.1f}s  caption={row['caption'][:60]}")
    return df


def register_demo(df: pd.DataFrame):
    """把 demo 数据注册进 video_assets 表。"""
    print(f"\n[2/4] 注册 {len(df)} 条任务到数据库...")
    for _, row in df.iterrows():
        video_id = row["video_url"].rstrip("/").split("=")[-1] + f"_{row['start_us']}"
        db.upsert_pending(
            DATASET, video_id, source_url=row["video_url"],
            clip_start_us=int(row["start_us"]), clip_end_us=int(row["end_us"]),
        )
    print(f"      注册完成")


def download_demo():
    """逐条下载，不走多进程，方便看清每条的输出。"""
    tasks = db.fetch_pending(DATASET, limit=DEMO_LIMIT)
    if not tasks:
        print("      没有待下载任务")
        return

    print(f"\n[3/4] 开始下载 {len(tasks)} 条（单进程顺序执行，方便观察）...\n")

    for i, task in enumerate(tasks, 1):
        vid = task["source_video_id"]
        out_path = str(local_path_for(DATASET, vid))

        start = us_to_timestamp(task["clip_start_us"]) if task.get("clip_start_us") is not None else None
        end = us_to_timestamp(task["clip_end_us"]) if task.get("clip_end_us") is not None else None

        clip_info = f"{start}~{end}" if start and end else "整段"
        print(f"  [{i}/{len(tasks)}] {vid}  clip={clip_info}")
        print(f"         url={task['source_url']}")
        print(f"         out={out_path}")

        ok, err = download_youtube(task["source_url"], out_path, start=start, end=end)

        if ok:
            md5 = file_md5(out_path)
            size_mb = os.path.getsize(out_path) / 1024 / 1024
            db.mark_result(task["id"], db.STATUS_SUCCESS, local_path=out_path, md5=md5)
            print(f"         ✓ 成功  size={size_mb:.2f}MB  md5={md5}")
        else:
            db.mark_result(task["id"], db.STATUS_PENDING, error_msg=err)
            db.bump_retry(task["id"], 3)
            print(f"         ✗ 失败  error={err[:200]}")
        print()


def show_results():
    """打印数据库里 videocc 的全部记录，让你看看采集到的数据长什么样。"""
    print("=" * 90)
    print("[4/4] 数据库记录一览（video_assets 表，dataset=videocc）")
    print("=" * 90)

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM video_assets WHERE dataset = ? ORDER BY id", (DATASET,)
    ).fetchall()
    conn.close()

    if not rows:
        print("  （空，没有记录）")
        return

    status_map = {0: "待下载", 1: "成功", 2: "失效", 3: "重试超限"}

    for r in rows:
        r = dict(r)
        st = status_map.get(r["download_status"], str(r["download_status"]))
        clip_start_s = r["clip_start_us"] / 1_000_000 if r["clip_start_us"] else None
        clip_end_s = r["clip_end_us"] / 1_000_000 if r["clip_end_us"] else None
        clip_str = f"{clip_start_s:.1f}s ~ {clip_end_s:.1f}s" if clip_start_s is not None else "N/A"

        print(f"\n  ── id={r['id']} ──")
        print(f"  source_video_id : {r['source_video_id']}")
        print(f"  source_url      : {r['source_url']}")
        print(f"  clip 片段       : {clip_str}  (原始微秒: {r['clip_start_us']} ~ {r['clip_end_us']})")
        print(f"  状态            : {st}")
        print(f"  local_path      : {r['local_path'] or '(未下载)'}")
        print(f"  md5             : {r['md5'] or '-'}")
        print(f"  error           : {r['error_msg'] or '-'}")

    # 汇总
    total = len(rows)
    ok = sum(1 for r in rows if r["download_status"] == 1)
    fail = total - ok
    print(f"\n  汇总: 共 {total} 条, 成功 {ok}, 失败/待重试 {fail}")

    # 文件列表
    out_dir = local_path_for(DATASET, "_").parent
    files = sorted(out_dir.glob("*.mp4")) if out_dir.exists() else []
    if files:
        total_size = sum(f.stat().st_size for f in files)
        print(f"\n  落盘目录: {out_dir}")
        print(f"  文件数: {len(files)},  总大小: {total_size / 1024 / 1024:.2f} MB")
        for f in files[:5]:
            print(f"    {f.name}  ({f.stat().st_size / 1024:.1f} KB)")
        if len(files) > 5:
            print(f"    ... 共 {len(files)} 个文件")


if __name__ == "__main__":
    db.init_db()

    df = fetch_csv_head(DEMO_LIMIT)
    register_demo(df)
    download_demo()
    show_results()
