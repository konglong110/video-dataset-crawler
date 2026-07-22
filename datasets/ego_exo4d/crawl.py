"""
Ego-Exo4D 采集脚本 —— TODO，尚未实现。

结构与 datasets/ego4d/crawl.py 完全一致，把官方 CLI 命令换成 `egoexo`。
详见该文件注释和本目录 README「与其他数据集的重叠」。

用法约定：
    python datasets/ego_exo4d/crawl.py --license-key <KEY> --datasets metadata annotations
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "ego_exo4d"


def run_official_cli(license_key: str, datasets: list[str], output_dir: str):
    raise NotImplementedError(
        "TODO: subprocess 调用官方 egoexo CLI（同 ego4d，命令名不同）。"
    )


def register_from_manifest(output_dir: str):
    raise NotImplementedError(
        "TODO: 解析 manifest，注意 take_uid 需要带上视角后缀(_ego/_exo1...)"
        "作为 source_video_id，避免多视角互相覆盖，参考本目录 README。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--license-key", type=str)
    parser.add_argument("--datasets", nargs="+", default=["metadata"])
    parser.add_argument("--output-dir", type=str, default="data/warm/ego_exo4d")
    parser.add_argument("--register-only", action="store_true")
    args = parser.parse_args()

    db.init_db()

    if not args.register_only:
        run_official_cli(args.license_key, args.datasets, args.output_dir)
    register_from_manifest(args.output_dir)
