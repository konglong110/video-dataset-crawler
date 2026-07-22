# video-dataset-crawler

多源开放视频数据集（文本-视频对 / 第一人称视频等）批量采集项目。

覆盖数据集：MiraData / Ego4D / Ego-Exo4D / VideoCC / LVD-2M / HD-VG-130M / HD-VILA-100M / InternVid。

## 现状

这是一个**脚手架仓库**：公共基础设施（任务队列、去重、存储分层、数据库表结构）已经搭好并可运行；
8 个数据集各自的采集脚本目前是 TODO 占位，按 `datasets/<name>/README.md` 里的说明分别实现即可，互相独立，可以并行开发。

## 目录结构

```
video-dataset-crawler/
├── common/                  # 公共基础设施，各数据集脚本复用
│   ├── db.py                 # SQLite 索引表（可选切换 MySQL），任务状态管理
│   ├── downloader.py          # 多进程下载队列 + 重试 + 断点续传
│   ├── dedupe.py              # MD5 去重
│   ├── storage.py             # 冷/温/热三层落盘路径管理
│   └── youtube_fetch.py       # yt-dlp 封装，统一下载参数/代理
├── datasets/                 # 每个数据集一个子目录，互相独立
│   ├── videocc/
│   ├── miradata/
│   ├── ego4d/
│   ├── ego_exo4d/
│   ├── hd_vg_130m/
│   ├── hd_vila_100m/
│   ├── lvd_2m/
│   └── internvid/
│       ├── README.md          # 该数据集的获取方式、难度点、TODO 说明
│       └── crawl.py           # 入口脚本，跑 `python crawl.py --limit 100` 验证
├── scripts/
│   └── init_db.py             # 初始化 SQLite 库表
├── config.py                  # 全局配置（代理、并发数、存储路径）
├── requirements.txt
└── data/                      # 下载产物，已加入 .gitignore，不进仓库
```

## 环境准备

本项目使用 conda 管理 Python 环境，本地开发环境为：

```bash
conda activate video-crawler   # Python 3.11
```

## 快速开始

```bash
conda activate video-crawler
pip install -r requirements.txt
python scripts/init_db.py          # 初始化本地 video_assets.db
python datasets/videocc/crawl.py --limit 20   # 跑一个数据集的小样本验证
```

## 设计约定（各数据集脚本需要遵守）

1. **不要自己造轮子**：下载、重试、去重、路径管理统一走 `common/` 里的模块，只在 `datasets/<name>/crawl.py` 里写"怎么拿到这个数据集的 URL 列表 + 怎么解析它的标注格式"。
2. **每条待下载记录先写入 `video_assets` 表再下载**，状态机：`0待下载 → 1成功 / 2失效 / 3重试超限`，方便断点续传，不用每次重跑全量。
3. **代理统一从 `config.py` 读**，不要在各脚本里硬编码代理地址。
4. **下载完成后必须算 MD5** 存回数据库，防止跨数据集重复（例如 LVD-2M 本身就复用了 HD-VG-130M / InternVid 的视频源）。

## 已知难点（对应之前调研结论，写脚本前先看对应数据集的 README）

| 数据集 | 主要难点 |
|---|---|
| Ego4D / Ego-Exo4D | 需先到 ego4ddataset.com 申请许可证，14 天过期需重签 |
| HD-VG-130M | 元数据在 Google Drive，需代理；130M 规模，YouTube 限流是大头 |
| HD-VILA-100M | 官方仓库 caption/转写获取路径不完整，需先确认数据结构再写脚本 |
| LVD-2M | 视频源是 YouTube/HDVG/WebVid 三者组合，逻辑最绕 |
| 其余（VideoCC/MiraData/InternVid） | 相对标准：元数据/标注现成，视频体走 YouTube 爬取 |

## TODO

- [ ] 8 个数据集的 `crawl.py` 逐个实现（每个约 1.5-3 人天，见项目排期表）
- [ ] 代理池接入（目前 `config.py` 里只留了单代理占位）
- [ ] 存储分层的 OSS 上传脚本（`common/storage.py` 里 `upload_to_cold_storage` 待接 SDK）
