"""
Ego4D 采集脚本 —— TODO，尚未实现。

跟其他数据集不同，这里不走 common/downloader.py 的多进程队列，
下载本身交给官方 CLI（见 README）。crawl.py 只做两件事：调用 CLI + 登记结果。

用法约定：
    python datasets/ego4d/crawl.py --license-key <KEY> --datasets metadata annotations
    python datasets/ego4d/crawl.py --register-only   # CLI 下载完之后，单独跑登记
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "ego4d"


def run_official_cli(license_key: str, datasets: list[str], output_dir: str):
    raise NotImplementedError(
        "TODO: subprocess 调用官方 ego4d CLI，例如：\n"
        "  ego4d --output_directory=<output_dir> --datasets metadata annotations "
        "--yes --license_key=<license_key>\n"
        "注意 license_key 14 天过期，调用前最好先检查有效期或提示用户重新申请。"
    )


def register_from_manifest(output_dir: str):
    raise NotImplementedError(
        "TODO: 读 <output_dir> 下的 manifest.csv，逐条 db.upsert_pending + "
        "db.mark_result(status=SUCCESS) 直接标记成功（因为文件已经由官方 CLI 下载完了，"
        "这里只是登记，不需要再走 downloader 队列）。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--license-key", type=str)
    parser.add_argument("--datasets", nargs="+", default=["metadata"])
    parser.add_argument("--output-dir", type=str, default="data/warm/ego4d")
    parser.add_argument("--register-only", action="store_true")
    args = parser.parse_args()

    db.init_db()

    if not args.register_only:
        run_official_cli(args.license_key, args.datasets, args.output_dir)
    register_from_manifest(args.output_dir)
