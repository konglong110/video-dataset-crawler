# VideoCC

- 官方仓库：https://github.com/google-research-datasets/videoCC-data
- 难度：★☆☆（清单里最简单的一个）

## 获取方式

仓库 README 直接提供**单一 CSV 文件**下载链接（点开即下载），列为：
`Video URL, Start timestamp(us), End timestamp(us), Caption`。
不需要额外解析元数据格式，也不需要账号/申请。

## TODO

1. 把官方 CSV 下载到 `datasets/videocc/meta/videocc_raw.csv`（手动下载或写个 `requests.get` 都行，链接是静态的）。
2. 用 pandas 读 CSV，起止时间戳单位是**微秒**，喂给 `common/youtube_fetch.py` 前要转成 `HH:MM:SS` 格式。
3. 调用 `common/db.py` 的 `upsert_pending` 把每行注册成一条任务。
4. 实现 `fetch_one`，调用 `common/youtube_fetch.download_youtube`，接入 `common/downloader.run_batch`。

## 注意

CSV 是几年前生成的，YouTube 视频失效率预计偏高，建议先跑小样本（`--limit 50`）估算实际到手率，
再决定要不要全量跑。
