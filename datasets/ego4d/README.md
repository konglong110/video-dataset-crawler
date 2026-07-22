# Ego4D

- 官方仓库：https://github.com/facebookresearch/Ego4d
- 难度：★★★（清单里门槛最高的一档之一）

## 获取方式（跟其他数据集不一样，走官方 CLI，不是直接爬）

> **状态：license 已签署完成（2026-07），可以合规采集。**

1. 许可协议在 https://ego4ddataset.com 审批通过后，官方会**邮件发一组 AWS Access Key / Secret Key**
   （不是简单的一个 license key 字符串）。
2. 用 `aws configure`（或 `aws configure --profile ego4d`）把这组凭证配置到本地，`ego4d` CLI 会自动读取。
3. **这组 AWS 凭证 14 天过期**，过期后需要重新登录 ego4ddataset.com 申请获取新的一组，
   不能自动续期，务必在项目排期里留出定期重新申请的提醒。
4. 安装：`pip install ego4d`，下载命令示例：
   ```bash
   ego4d --output_directory="~/ego4d_data" --datasets full_scale annotations --metadata --version v2 --yes
   ```
   （`--yes` 跳过确认提示，方便脚本化调用）
5. **务必先用小范围数据集/子集试跑**，全量 `full_scale` 体积达 TB 级别，建议先只下 `metadata` +
   `annotations`，视需要再决定要不要下 `full_scale` 全量视频。

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
