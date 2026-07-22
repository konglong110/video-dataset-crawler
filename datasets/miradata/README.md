# MiraData

- 官方仓库：https://github.com/mira-space/MiraData
- 协议：GPL-v3，可商用
- 难度：★★☆

## 获取方式

仓库提供元文件 + 结构化字幕（多维度，GPT-4V 生成：主体描述/背景/运镜等）。
视频源本身来自 YouTube 频道 + HD-VILA-100M/Videovo/Pixabay/Pexels，需要按元数据里的
video id/url 自行下载或复用其他数据集已下载的文件（见下方"与其他数据集的重叠"）。

## TODO

1. 下载仓库里的标注文件（参考 `assets/miradata_v1_100_samples.csv` 这类文件，全量标注地址以仓库最新 README 为准）。
2. 解析结构化 caption（多个维度字段，需要设计怎么存 —— 建议整体存成 JSON 落到
   `caption_path` 指向的文件，而不是拆列存数据库，字段结构较复杂）。
3. 参照 `datasets/videocc/crawl.py` 的模式写 `register()` + `fetch_one()`。

## 与其他数据集的重叠（务必注意）

MiraData 部分视频源自 HD-VILA-100M。如果 HD-VILA-100M 也在下载队列里，
**建议先跑完 HD-VILA-100M 再跑 MiraData 里重叠的部分**，靠 `common/dedupe.py`
的跨数据集 MD5 查重自动跳过重复下载，省时间和流量。

## 风险提示

官方声明"应版权方要求可能随时下架样本"，长期可用性没有保证，建议下载后走
`common/storage.py` 尽快转存一份到自己的存储，不要依赖官方仓库长期可访问。
