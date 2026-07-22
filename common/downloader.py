"""
多进程下载队列，不引入 Celery/Redis —— 用 multiprocessing.Pool 就够，
任务状态全部记在 common/db.py 的 video_assets 表里，天然支持断点续传：
中途中断后重跑，已成功的记录不会重复下载。

各数据集的 crawl.py 用法示例：

    from common.downloader import run_batch

    def fetch_one(task: dict) -> dict:
        # task 是 db.fetch_pending() 返回的一行 dict
        # 在这里实现"怎么把 task['source_url'] 下载到本地"，
        # 返回 {"success": bool, "local_path": str, "error": str}
        ...

    run_batch(dataset="videocc", fetch_fn=fetch_one, limit=100)
"""
import time
from multiprocessing import Pool

from config import MAX_WORKERS, MAX_RETRIES, RETRY_BACKOFF_SEC
from common import db
from common.dedupe import file_md5


def _worker(args):
    task, fetch_fn = args
    try:
        result = fetch_fn(task)
    except Exception as e:  # noqa: BLE001 - 下载任务里什么异常都可能出现，统一兜底进重试
        result = {"success": False, "error": str(e)}
    return task, result


def run_batch(dataset: str, fetch_fn, limit: int = 100, workers: int = None):
    """
    从数据库取 limit 条待下载任务，多进程执行 fetch_fn，写回状态。
    fetch_fn(task: dict) -> {"success": bool, "local_path": str|None, "error": str|None}
    """
    workers = workers or MAX_WORKERS
    tasks = db.fetch_pending(dataset, limit=limit)
    if not tasks:
        print(f"[{dataset}] 没有待下载任务了（要么全下完了，要么还没 upsert_pending）")
        return

    print(f"[{dataset}] 本批 {len(tasks)} 条任务，并发 {workers}")

    with Pool(processes=workers) as pool:
        for task, result in pool.imap_unordered(_worker, [(t, fetch_fn) for t in tasks]):
            _handle_result(dataset, task, result)


def _handle_result(dataset: str, task: dict, result: dict):
    if result.get("success"):
        local_path = result.get("local_path")
        md5 = file_md5(local_path) if local_path else None
        db.mark_result(
            task["id"], db.STATUS_SUCCESS,
            local_path=local_path, md5=md5,
        )
    else:
        error = result.get("error", "unknown error")
        print(f"[{dataset}] 失败 id={task['id']} video_id={task['source_video_id']}: {error}")
        db.mark_result(task["id"], db.STATUS_PENDING, error_msg=error)
        db.bump_retry(task["id"], MAX_RETRIES)
        # 简单的退避：让下一次批量运行前有个间隔，避免同一时间点持续被限流
        time.sleep(0)  # 占位：如需真正 sleep 退避，在这里按 RETRY_BACKOFF_SEC * retry_count 等待
