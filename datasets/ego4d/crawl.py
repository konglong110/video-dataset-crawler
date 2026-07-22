"""
Ego4D 采集脚本。

license 已签署，AWS 凭证需要提前用 `aws configure` 配置好（不在这个脚本里处理密钥，
密钥属于敏感信息，不应该硬编码或作为命令行参数传递）。

这个数据集不走 common/downloader.py 的多进程队列，下载本身交给官方 ego4d CLI
（它自己管重试/断点续传），crawl.py 只做两件事：
1. 调用官方 CLI 下载指定 datasets；
2. 下载完成后解析每个 dataset 目录下的 manifest.csv，登记进 common/db.py，
   方便跟其他数据集统一做 MD5 去重和存储分层管理。

用法：
    # 前提：已经跑过 aws configure --profile ego4d 配置好凭证
    python datasets/ego4d/crawl.py --datasets metadata annotations --aws-profile ego4d
    python datasets/ego4d/crawl.py --register-only --output-dir data/warm/ego4d
"""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import db

DATASET = "ego4d"


def run_official_cli(datasets: list[str], output_dir: str, aws_profile: str, version: str = "v2"):
    """
    调用官方 ego4d CLI。凭证从 --aws-profile 指定的 AWS profile 读取，
    不在这里传密钥。凭证 14 天过期，过期会在这一步直接报错（AWS 认证失败），
    看到认证报错先去 ego4ddataset.com 重新申请一组新凭证再 aws configure。
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    cmd = [
        "ego4d",
        f"--output_directory={output_dir}",
        "--datasets", *datasets,
        "--version", version,
        "--yes",
    ]
    if aws_profile:
        cmd.append(f"--aws_profile_name={aws_profile}")

    print(f"[{DATASET}] 执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{DATASET}] CLI 执行失败:\n{result.stderr[-3000:]}")
        print("如果是认证相关报错，大概率是 AWS 凭证过期(14天)，需要去 "
              "ego4ddataset.com 重新申请后 aws configure 更新。")
        sys.exit(1)
    print(f"[{DATASET}] CLI 执行完成")


def register_from_manifest(output_dir: str, version: str = "v2"):
    """
    遍历 <output_dir>/<version>/<dataset_name>/manifest.csv，登记进数据库。
    manifest.csv 里每行至少包含 video_uid，具体列名以官方实际文件为准，
    这里做了容错：优先找 video_uid 列，找不到就退而求其次用第一列。
    """
    version_dir = Path(output_dir) / version
    if not version_dir.exists():
        print(f"[{DATASET}] 没找到 {version_dir}，确认是否已经跑过下载步骤。")
        return

    total = 0
    for manifest_path in version_dir.glob("*/manifest.csv"):
        dataset_name = manifest_path.parent.name  # full_scale / annotations / ...
        with open(manifest_path, newline="") as f:
            reader = csv.DictReader(f)
            id_col = "video_uid" if reader.fieldnames and "video_uid" in reader.fieldnames \
                else reader.fieldnames[0]
            for row in reader:
                video_uid = row[id_col]
                # source_video_id 带上子数据集名，避免 full_scale/annotations 下
                # 同名 video_uid 互相覆盖
                source_video_id = f"{dataset_name}_{video_uid}"
                local_file = manifest_path.parent / f"{video_uid}.mp4"

                db.upsert_pending(DATASET, source_video_id, source_url=None)
                record = db.get_one(DATASET, source_video_id)
                # 文件已经被官方 CLI 下载到本地了，这里直接标成功，不走下载队列；
                # MD5 留空 —— full_scale 全量算 MD5 很慢，如果需要跨数据集查重
                # （比如后面对比 Ego-Exo4D 有没有重叠），再单独跑一次批量补算脚本。
                if record and record["download_status"] != db.STATUS_SUCCESS:
                    db.mark_result(
                        record["id"], db.STATUS_SUCCESS,
                        local_path=str(local_file) if local_file.exists() else None,
                    )
                total += 1
        print(f"[{DATASET}] 已登记 {dataset_name}: {manifest_path}（{total} 条）")

    print(f"[{DATASET}] 共处理 {total} 条 manifest 记录。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["metadata", "annotations"],
                         help="要下载的 dataset 名称，例如 metadata annotations full_scale")
    parser.add_argument("--version", default="v2")
    parser.add_argument("--output-dir", default="data/warm/ego4d")
    parser.add_argument("--aws-profile", default="ego4d",
                         help="aws configure 时用的 profile 名")
    parser.add_argument("--register-only", action="store_true",
                         help="跳过 CLI 下载，只解析已有 manifest 登记数据库")
    args = parser.parse_args()

    db.init_db()

    if not args.register_only:
        run_official_cli(args.datasets, args.output_dir, args.aws_profile, args.version)
    register_from_manifest(args.output_dir, args.version)
