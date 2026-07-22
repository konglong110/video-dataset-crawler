# HD-VG-130M

- 官方仓库：https://github.com/daooshee/HD-VG-130M
- 协议：仅限学术用途
- 难度：★★★（规模最大，130M 文本-视频对）

## 获取方式

元数据通过 **Google Drive** 下载（需要代理，见 `config.py` 的 `HTTP_PROXY`），
视频本体需要按元数据里的 YouTube 链接自行爬取切片。

## TODO

1. 从仓库 README 拿到 Google Drive 元数据下载链接（人工下载，Drive 大文件不好用脚本批量拉）。
2. 元数据体量大（130M 条），落盘后**不要整份读进内存**，用 pandas `chunksize` 或逐行读 jsonl。
3. 参照 `datasets/videocc/crawl.py` 写 `register()`（注意分批 upsert，不要一次性 130M 条塞数据库，
   建议先跑一个几万条的子集验证流程，再决定要不要全量注册）。
4. `fetch_one` 复用 `common/youtube_fetch.download_youtube`。

## 风险提示

130M 规模下 YouTube 限流/失效会非常明显，`config.py` 里的 `MAX_WORKERS` 建议先保守设置（4 左右），
观察失败率再调整；这个数据集大概率是整个项目里最耗时间的一个。
