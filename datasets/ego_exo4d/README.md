# Ego-Exo4D

- 官方仓库：https://github.com/facebookresearch/Ego4d（与 Ego4D 同一个仓库）
- 难度：★★★

## 获取方式

跟 Ego4D 是**两个独立的申请**（分别到 ego4d.dev/request/ego-exo4d 签署协议），
但机制完全一样：审批通过后（约48小时）邮件发一组 AWS Access Key/Secret Key，
`aws configure` 配置后用 `egoexo` 命令（而不是 `ego4d`）下载，凭证同样 **14 天过期**。
数据结构上多了同一场景的第一人称（Aria 眼镜）+ 第三人称（GoPro）多视角对齐信息。

## TODO

1. 复用 `datasets/ego4d/` 里的申请和环境（同一个 license，不用重复申请）。
2. `crawl.py` 直接照抄 ego4d 的结构，把 CLI 命令换成 `egoexo`。
3. 额外注意：manifest 里会有多路视频对应同一个 take_uid（第一/三人称各一条），
   登记进数据库时 `source_video_id` 要带上视角标记（如 `<take_uid>_ego` /
   `<take_uid>_exo1`），否则会被当成同一条记录互相覆盖。
