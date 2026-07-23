# 架构设计文档（ARCHITECTURE）

> 本文件是**框架层**的权威说明，描述"这个项目为什么这样搭、各部分怎么协作"。
> 开发窗口动手前应先读本文 + `DEV_GUIDE.md` + 对应工单，不要凭 crawl.py 里的注释猜整体设计。
> 本文由架构师维护，改动架构（新增公共模块、改数据模型、改协作方式）必须先更新本文。

## 1. 项目目标

批量、可断点续传地采集 8 个公开视频数据集（文本-视频对 / 第一人称视频）到本地/对象存储，
统一做跨数据集去重与存储分层，供下游训练使用。

覆盖：VideoCC · InternVid · MiraData · HD-VG-130M · HD-VILA-100M · LVD-2M · Ego4D · Ego-Exo4D。

## 2. 架构总览

分层原则：**公共基础设施沉到 `common/`，各数据集只写自己特有的"取 URL + 解析标注"逻辑。**

```
                 ┌─────────────────────────────────────────────┐
                 │  config.py  全局配置单一来源                  │
                 │  (代理 / 并发 / 路径 / DB backend / yt-dlp)    │
                 └─────────────────────────────────────────────┘
                                    ▲ 所有模块只从这里读配置
   datasets/<name>/crawl.py         │
   ┌────────────────────────┐       │        common/ 公共基础设施
   │ register()             │       │   ┌──────────────────────────────┐
   │  解析该数据集标注格式   │───────┼──▶│ db.py       video_assets 索引表 │
   │  → upsert_pending      │       │   │             + 任务状态机        │
   │                        │       │   │ downloader.py 多进程队列+重试   │
   │ fetch_one(task)        │       │   │ youtube_fetch.py yt-dlp 封装    │
   │  该数据集特有的下载方式 │◀──────┼───│ dedupe.py    MD5 跨集去重       │
   │  → run_batch 调用       │       │   │ storage.py   冷/温/热分层       │
   └────────────────────────┘       │   └──────────────────────────────┘
                                     ▼
                          data/  (hot/warm/logs, 不进仓库)
```

**只有两类东西是数据集脚本自己写的**：`register()`（怎么把这个数据集的标注解析成任务）
和 `fetch_one()`（怎么把一条任务落地成本地文件）。其余全部复用 `common/`。

## 3. 标准数据流（以 YouTube 类数据集为例）

```
①解析标注  register()  ──►  upsert_pending(dataset, video_id, url, [start,end])
                                        │  先写库，状态=0 待下载
                                        ▼
②取批       run_batch(dataset, fetch_one, limit)
                                        │  fetch_pending() 捞 status=0 的行
                                        ▼
③下载       多进程 Pool 里跑 fetch_one(task) ──► download_youtube(...)
                                        │
                              成功 ┌────┴────┐ 失败
                                   ▼         ▼
④回写   mark_result(SUCCESS,       bump_retry() 重试计数+1
        local_path, md5=file_md5)   超限则 status=3，否则回到 0 等下一批
                                   │
                                   ▼
⑤去重/分层   file_md5 存库 → is_duplicate_md5 跨集查重 → storage 分层落盘
```

关键设计：**先写库再下载**。进度、去重、断点续传全部以 `video_assets` 表为准，
永远不靠"扫文件系统看下过没有"。中途中断后重跑，已成功的行不会被再次下载。

## 4. 数据模型：`video_assets` 单表

所有数据集共用一张表（`common/db.py` 的 `_SCHEMA`）。脚本**只调 db.py 的函数，不直接写 SQL**，
这样将来从 SQLite 切 MySQL 时业务代码零改动。

| 字段 | 含义 | 备注 |
|---|---|---|
| `dataset` + `source_video_id` | 唯一键 `UNIQUE(dataset, source_video_id)` | 同一原视频被切成多 clip 时，video_id 要带区分后缀（时间戳/视角/split） |
| `source_url` | 原始下载地址 | |
| `local_path` / `caption_path` | 视频、标注落盘路径 | 复杂 caption 存 JSON 文件，路径指过来 |
| `md5` | 下载完计算，跨集去重用 | 索引 `idx_md5` |
| `download_status` | **状态机**，见下 | 索引 `idx_status` |
| `retry_count` / `error_msg` | 重试计数、最后一次错误 | |
| `resolution` / `duration_sec` | 元信息 | |

**状态机**（`db.py` 常量）：

```
        upsert_pending
              │
              ▼
        0 PENDING ──成功──► 1 SUCCESS
           ▲   │
      重试  │   └─失败─► bump_retry ──超限──► 3 RETRY_EXCEEDED
     (回 0) │
            └───────────── 源失效直接置 ──► 2 INVALID（不再重试）
```

> **clip 时间戳列（T01 已落地）**：clip 起止时间戳作为通用列 `clip_start_us`/`clip_end_us`
> （**微秒 INTEGER**）加在本表上，不为单个数据集另建辅助表——保持"单表"设计。
> 单位取微秒是为无损保留源标注精度并复用现成的 `us_to_timestamp`（喂给 yt-dlp 前再转 HH:MM:SS）。
> `init_db()` 自带幂等迁移（`_apply_migrations`），老库会自动补列。HD-VILA(T07) 切片复用同两列。

## 5. 数据集分三类（决定 crawl.py 的写法）

| 类型 | 数据集 | 下载路径 | crawl.py 骨架 |
|---|---|---|---|
| **A. 标准 YouTube 爬取** | VideoCC / InternVid / MiraData / HD-VG-130M / HD-VILA-100M | `register` 解析标注 → `run_batch(fetch_one)` → `youtube_fetch` | 参照 `datasets/videocc/crawl.py` |
| **B. 官方 CLI 托管** | Ego4D / Ego-Exo4D | 官方 CLI 自己管下载/重试，crawl.py **只调 CLI + 解析 manifest 回填库** | **不走** `common/downloader.py`，只用 db.py 登记 |
| **C. 组合源** | LVD-2M | 一份标注按 split 拆成 YouTube/HDVG/WebVid 三批，分别用不同 fetch | 按 split 前缀分发到不同下载逻辑 |

这张表决定了每张工单的实现形态，写工单时先归类。

## 6. 扩展点（当前是占位，各有独立任务）

| 扩展点 | 现状 | 对应任务 |
|---|---|---|
| 代理池 | `config.py` 只有单代理占位 `HTTP_PROXY` | INFRA-2 |
| OSS 冷存储 | `storage.upload_to_cold_storage` 抛 NotImplementedError | INFRA-3 |
| MySQL backend | `db.get_conn` 的 mysql 分支抛 NotImplementedError | INFRA-4 |
| clip 时间戳列 | ✅ 已完成（`clip_start_us`/`clip_end_us`，随 T01 落地） | — |

## 7. 设计原则（所有工单继承）

1. **不造轮子**：下载/重试/去重/路径/代理统一走 `common/`，脚本只写数据集特有解析。
2. **先写库再下载**：任务状态以 `video_assets` 为准，天然断点续传。
3. **配置单一来源**：一切配置从 `config.py` 读，禁止硬编码代理/路径/并发。
4. **下完必算 MD5**：跨数据集去重（如 LVD-2M 复用 HDVG/InternVid 视频源）。
5. **数据集之间强隔离**：一个数据集的改动不应影响另一个，可并行开发。
