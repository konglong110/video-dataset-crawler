"""
冷/温/热三层存储路径管理。

- hot:  当前正在用于训练/处理的子集，本地盘
- warm: 下载完暂不用，等待转存到对象存储
- cold: OSS 归档存储，基本不会再读（upload_to_cold_storage 待接 SDK）
"""
from pathlib import Path

from config import HOT_DIR, WARM_DIR


def dataset_dir(dataset: str, tier: str = "warm") -> Path:
    """
    返回某个数据集在指定层级下的落盘目录，自动创建。
    tier: "hot" | "warm"（cold 层不落在本地，直接走 upload_to_cold_storage）
    """
    base = HOT_DIR if tier == "hot" else WARM_DIR
    d = base / dataset
    d.mkdir(parents=True, exist_ok=True)
    return d


def local_path_for(dataset: str, video_id: str, ext: str = "mp4", tier: str = "warm") -> Path:
    return dataset_dir(dataset, tier) / f"{video_id}.{ext}"


def upload_to_cold_storage(local_path: str, dataset: str) -> str:
    """
    TODO: 接入阿里云 OSS SDK（oss2），上传到形如
    oss://<bucket>/video-datasets/<dataset>/<filename> 的归档存储类型 key，
    上传成功后删除本地 warm 层文件，返回 OSS 上的完整路径。

    目前是占位实现，只返回本地路径，不做真正上传/删除，避免脚手架阶段
    误删数据。
    """
    raise NotImplementedError(
        "OSS 上传待接入：装 oss2，用已有的 阿里云 OSS 凭证初始化 bucket，"
        "参考 dataset_dir() 里的路径规则拼 object key。"
    )
