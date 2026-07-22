# HD-VILA-100M

- 官方仓库：https://github.com/microsoft/XPretrain/tree/main/hd-vila-100m
- 难度：★★★

## 获取方式

仓库提供 URL 列表 + 每个视频的切片时间戳（jsonlines 格式），示例：
```
{'video_id':'QMi8x8o55Ns', 'url': 'https://www.youtube.com/watch?v=QMi8x8o55Ns',
 'clip': [{'clip_id': 'QMi8x8o55Ns.1.mp4', 'span': ['00:00:17.759','00:00:23.279']}, ...]}
```
下载原始视频后用官方 `src/cut_videos.py` 切片（脚本已有现成实现，可以直接抄）。

## 已知坑（写脚本前务必先确认）

仓库 Issue（#2、#29）里有多个用户反映**下载解压后的 `hdvila100m.zip` 里找不到对应文字描述**，
caption/ASR 转写的获取路径官方文档写得不够清楚。**这个数据集的第一步不是写下载脚本，
而是先花半天时间人工确认清楚"文本描述到底在哪个文件里、怎么跟 clip_id 对齐"**，
避免脚本写完了才发现拿到的只有视频没有文本。

## TODO

1. 先人工确认 caption 数据的实际获取路径（见上）。
2. 解析 jsonlines 元数据，登记任务（`source_video_id` 建议用 `clip_id` 而不是 `video_id`，
   因为下载粒度是按 clip 切片的）。
3. `fetch_one` 里注意：先下载整段 `video_id` 对应的原始视频（一个原视频对应多个 clip，
   避免同一个原视频被下载 N 次），再本地切片，不要每个 clip 单独发一次下载请求。
