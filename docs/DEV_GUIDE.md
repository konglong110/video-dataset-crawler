# 开发规约（DEV_GUIDE）

> **每个开发窗口动手前必读。** 本文是所有 crawl.py 的通用约定与验收基线，
> 工单（`docs/tasks/T0x-*.md`）只写"这一个任务特有的东西"，通用部分不再重复。
> 与本文冲突时以工单为准；工单没写到的，回落到本文。

## 0. 你的角色

你是执行**单张工单**的开发工程师。只实现被指派的任务，**不扩大范围**、不顺手重构无关代码、
不做架构决策（要改架构/数据模型/协作方式，回报给架构师，不要自己拍板）。

## 1. 四条铁律（违反直接打回）

1. **不造轮子**：下载、重试、去重、路径、代理，一律调 `common/`，不要自己 `subprocess` yt-dlp、
   不要自己写重试循环、不要自己算存储路径。
2. **先写库再下载**：每条待下载记录先 `db.upsert_pending(...)`，再由 `run_batch` 驱动下载。
3. **配置只从 `config.py` 读**：代理、并发数、超时、路径、yt-dlp format 全部走 config，禁止硬编码。
4. **下载完必算 MD5**：`run_batch` 已在成功回调里自动 `file_md5` 存库；你若走非标准路径（如 B 类 CLI），
   要自己确保 MD5 有落库。

## 2. A 类数据集（YouTube 爬取）的 crawl.py 骨架

所有 A 类数据集照这个结构写，参考实现是 `datasets/videocc/crawl.py`：

```python
DATASET = "<name>"

def register(...):
    # 1. 读该数据集的标注文件（CSV/jsonl/HF 下载物）
    # 2. 逐条（大数据集要分批/chunksize）解析出 video_id + url [+ start/end/caption]
    # 3. db.upsert_pending(DATASET, video_id, source_url=url, ...)
    #    - video_id 必须全局唯一：多 clip 共享原视频时带后缀（时间戳/视角/split）
    ...

def fetch_one(task: dict) -> dict:
    # task 是 db.fetch_pending() 返回的一行 dict
    # 用 common.youtube_fetch.download_youtube 下载到 storage.local_path_for(...) 的路径
    # 必须返回 {"success": bool, "local_path": str|None, "error": str|None}
    ...

if __name__ == "__main__":
    # --register 走 register()；否则 run_batch(DATASET, fetch_one, limit=args.limit)
```

- **B 类（Ego4D/Ego-Exo4D）**不走这个骨架：调官方 CLI 下载，再遍历 manifest 用
  `upsert_pending` + `mark_result(SUCCESS)` 登记。见 `ARCHITECTURE.md` §5。
- **C 类（LVD-2M）**在 `fetch_one` 里按 `source_video_id` 前缀分发到不同下载实现。

## 3. 命令行约定（保持 8 个数据集一致）

```
python datasets/<name>/crawl.py --register [数据集特有参数]   # 解析标注入库，跑一次
python datasets/<name>/crawl.py --limit N                     # 下载一批，可反复跑到跑完
```

`crawl.py` 开头统一 `sys.path.insert(0, <repo_root>)` 后再 import `common`（现有文件已有，照抄）。

## 4. 代码风格

- 跟随现有代码：**中文注释**，注释解释"为什么这么做"而非复述代码；命名、缩进、docstring 风格对齐 `common/` 和 `videocc/crawl.py`。
- 不引入新依赖除非工单批准；用到的第三方库要加进 `requirements.txt`。
- 不追求过度抽象，脚手架阶段以"能跑通、易读、好接手"为先。

## 5. 通用验收基线（每张工单在此之上再加专项验收）

提交前逐条自查：

1. `python scripts/init_db.py` 在全新库上能建表成功。
2. `python datasets/<name>/crawl.py --register` 能把标注解析入库（可用小样本/假数据验证）。
3. `python datasets/<name>/crawl.py --limit <小数>` 能跑起下载流程（无网络时至少参数、调用链正确，不崩在自己代码里）。
4. 你的改动**不破坏其他数据集的 import**（`python -c "import datasets... "` 或直接跑别的 crawl.py 的 `--help`）。
5. 没有把 `data/`、`*.db`、大文件、标注原始文件误提交（`.gitignore` 已覆盖，注意别 `git add -f`）。

## 6. 提交与回报

- 提交到**本窗口被指派的开发分支**，commit message 用中文简述改了什么、为什么。
- **不要创建 PR，除非架构师/用户明确要求。**
- 完成后回报三件事：① 改了哪些文件 ② 如何自测的（贴关键命令/输出）③ 遗留问题或需要架构师决策的点。
- 遇到工单没覆盖的设计岔路（例如"标注里字段和文档对不上"），**停下来回报，不要自行猜测拍板**。
