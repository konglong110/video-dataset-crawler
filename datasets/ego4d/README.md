# Ego4D

- 官方仓库：https://github.com/facebookresearch/Ego4d
- 难度：★★★（清单里门槛最高的一档之一）

## 获取方式（跟其他数据集不一样，走官方 CLI，不是直接爬）

1. 到 https://ego4ddataset.com 申请许可证（license），审批通过后拿到 license key。
2. **license key 14 天过期**，需要用同一邮箱定期重新签署，务必在项目排期里预留自动提醒/重签流程，
   不要假设申请一次就一劳永逸。
3. 安装官方 `ego4d` python 模块（conda 环境），用 `ego4d --output_directory=... --datasets ...`
   下载，数据托管在 AWS S3。
4. **务必用 `--benchmarks` / `--video_uids` 过滤**，全量下载体积达 5TB 级别，先按需要的子集下载。

## 与本项目公共基础设施的关系

这个数据集**不走 `common/downloader.py` 的多进程队列**，因为下载本身由官方 CLI 管理
（它自己有重试/断点续传）。`crawl.py` 这里只负责：
1. 调用官方 CLI 完成下载；
2. 下载完成后遍历 `manifest.csv`，把结果登记进 `common/db.py` 的 `video_assets` 表
   （主要是为了跟其他数据集统一做 MD5 去重和存储分层管理，不是为了控制下载过程本身）。

## TODO

1. license 申请 + CLI 环境搭建（这一步有人工审批等待时间，不算在开发工时里）。
2. 写 `crawl.py`：调用 CLI + 解析 `manifest.csv` 回填数据库。
3. 确认清单要用的具体 benchmark 子集（不确定就先只下 `metadata` + 少量 `full_scale` 样本试跑）。
