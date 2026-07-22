# Ego-Exo4D

- 官方仓库：https://github.com/facebookresearch/Ego4d（与 Ego4D 同一个仓库）
- 难度：★★★

## 获取方式

流程与 `datasets/ego4d/` 完全一致（同一个申请、同一个 license、同一个 CLI），
区别只是用 `egoexo` 命令而不是 `ego4d` 命令，数据结构上多了同一场景的
第一人称（Aria 眼镜）+ 第三人称（GoPro）多视角对齐信息。

## TODO

1. 复用 `datasets/ego4d/` 里的申请和环境（同一个 license，不用重复申请）。
2. `crawl.py` 直接照抄 ego4d 的结构，把 CLI 命令换成 `egoexo`。
3. 额外注意：manifest 里会有多路视频对应同一个 take_uid（第一/三人称各一条），
   登记进数据库时 `source_video_id` 要带上视角标记（如 `<take_uid>_ego` /
   `<take_uid>_exo1`），否则会被当成同一条记录互相覆盖。
