# 工单 T02 — Ego4D 采集脚本（官方 CLI 登记回填）

- **类型**：B 类（官方 CLI 托管，**不走** `common/downloader.py`） · **依赖**：license（已签署，14 天窗口） · **预估**：~1 人天
- **必读**：`docs/ARCHITECTURE.md`（§5 B 类）、`docs/DEV_GUIDE.md`、`datasets/ego4d/README.md`、`datasets/ego4d/crawl.py`
- **要改的文件**：`datasets/ego4d/crawl.py`（只动 ego4d 目录，不碰其他数据集）

## 背景与时间敏感性

Ego4D 数据由**官方 `ego4d` CLI** 托管在 AWS S3，CLI 自带重试/断点续传，所以**本项目不用多进程下载队列**。
`crawl.py` 只做两件事：① 调官方 CLI 完成下载；② 下载完遍历 manifest，把结果登记进 `video_assets` 表
（目的是让 Ego4D 也纳入统一的 MD5 去重 / 存储分层，不是接管下载过程）。

> **license 已签署，但 14 天过期。** 写脚本不消耗 license；真正 CLI 下载要在用户的采集环境、
> 用户的 license key 下执行（本开发窗口的沙箱跑不了官方 CLI）。因此本工单**只交付脚本 + 自测**，
> 实际下载由用户在采集环境运行。脚本要为"license 可能已过期"留出清晰报错。

## 架构师已定的设计决策

1. **登记即成功**：文件已由 CLI 下好，`register_from_manifest` 对每条 `upsert_pending` 后直接
   `mark_result(id, STATUS_SUCCESS, local_path=..., md5=file_md5(local_path))`——**要算 MD5 落库**（铁律 4，
   B 类不走 run_batch 的自动 MD5，必须自己补）。大文件 MD5 耗时，允许加 `--skip-md5` 开关先跳过、后补。
2. **`source_video_id`** 用 manifest 里的 video/clip uid；Ego4D 单视角，无需视角后缀（那是 T03 Ego-Exo4D 的事）。
3. CLI 参数**必须支持子集过滤**：默认只下 `metadata`，通过 `--datasets` / `--benchmarks` / `--video-uids`
   控制，**绝不默认全量**（全量 5TB 级）。

## 实现要求

改 `datasets/ego4d/crawl.py`，落地当前两个 `NotImplementedError`：

1. **`run_official_cli(license_key, datasets, output_dir, ...)`**：
   - 用 `subprocess` 调官方 CLI，形如：
     `ego4d --output_directory=<output_dir> --datasets metadata annotations --yes --license_key=<key>`
   - 透传 `--benchmarks` / `--video_uids` 等过滤参数（做成可选命令行参数）。
   - 调用前**检查 license_key 是否传入**，未传或 CLI 报鉴权/过期错误时，给出"请到 ego4ddataset.com 重新签署"的清晰提示，
     不要吞掉 CLI 的 stderr。
   - CLI 未安装（`FileNotFoundError`）时提示安装官方 `ego4d` 模块。
2. **`register_from_manifest(output_dir, skip_md5=False)`**：
   - 读 `<output_dir>` 下的 `manifest.csv`（字段以官方为准，实现时按实际列名解析，解析不出来先回报而非硬猜）。
   - 逐条 `db.upsert_pending(DATASET, video_id, source_url=...)` → `db.mark_result(id, STATUS_SUCCESS, local_path, md5)`。
   - `local_path` 用 CLI 实际落盘路径；`md5` 用 `common.dedupe.file_md5`（`skip_md5=True` 时置 None）。
3. **`__main__`**：保留现有参数，补上 `--benchmarks`、`--video-uids`、`--skip-md5`；
   `--register-only` 时跳过 CLI、只跑登记（CLI 已在别处下过的场景）。

## 不要做

- 不要接 `common/downloader.py` / `run_batch`（B 类不走队列）。
- 不要在本沙箱真跑 `ego4d` CLI（跑不了，也不该消耗 license）；用**假的 `manifest.csv` + 假文件**验证登记逻辑。
- 不要硬编码 license key / 路径，全部走命令行参数或 `config.py`。

## 验收标准（提交前逐条自查）

1. `python datasets/ego4d/crawl.py --help` 正常，含 `--datasets/--benchmarks/--video-uids/--skip-md5/--register-only`。
2. 造一个假 `output_dir/manifest.csv` + 几个假视频文件，`--register-only` 能把它们登记进库并置为 SUCCESS，
   `md5` 有值（`--skip-md5` 时为空）；用 `db.stats("ego4d")` 或直接查库验证。
3. 不传 license key 直接跑（非 register-only）时，报清晰的"缺少/需重签 license"提示，不抛裸栈。
4. 未破坏其他数据集 import；未误提交假数据 / `data/` / `*.db`。

## 交付

- 提交到本窗口指派的开发分支，commit message 说明"Ego4D CLI 调用 + manifest 登记回填"。
- **不创建 PR**（除非另行要求）。
- 回报：① 改了哪些文件 ② 各验收怎么验的 ③ 给用户的"在采集环境实跑"操作提示（含 license key 怎么传、
  建议先 `--datasets metadata` + 少量 `--video-uids` 小样本验证 license 有效）。
