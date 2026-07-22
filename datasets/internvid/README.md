# InternVid

- 官方仓库：https://github.com/OpenGVLab/InternVideo/tree/main/Data/InternVid
- 难度：★★☆（清单里相对最省事的一个）

## 获取方式

跟其他数据集不同，230M 视频-文本标注**全量已经直接托管在 OpenDataLab / HuggingFace**，
不是只给 URL 列表 —— 标注文件本身可以直接下载，不需要自己爬。
另外还有精选子集 InternVid-10M-FLT / InternVid-Aesthetics-18M 可选，体量更小，
建议客户不缺"全量"的话优先用子集，能省下大量下载时间。

视频原始文件本体仍然没有直接托管，需要按标注里的 video id 去 YouTube 补爬。

## TODO

1. 从 HuggingFace 或 OpenDataLab 下载标注文件（不需要写爬虫，直接 `huggingface_hub` 下载或手动下载）。
2. 确认要用全量（230M）还是子集（10M-FLT / 18M-Aesthetics），体量差异很大，建议先跟客户确认清楚。
3. 解析标注，登记任务，`fetch_one` 复用 `common/youtube_fetch.py`。

## 建议

这是 8 个数据集里"标注拿起来最快"的一个，可以作为整个项目里第二个跑通的数据集
（第一个是 VideoCC，参考 `datasets/videocc/crawl.py` 的模式）。
