# 任务看板（TASK_BOARD）

> 项目状态的**唯一权威来源**。开发窗口是冷启动的，看板 = 大家共享的记忆。
> 架构师维护本表：派单前把工单写进 `docs/tasks/`，派单/验收后更新这里的状态。
>
> 状态：⬜ 待办 · 🟡 进行中（已派开发窗口） · 🔵 待验收（开发已交回） · ✅ 已验收 · ⛔ 阻塞

## 一、优先级与排期总览

| 序 | 任务 | 类型 | 状态 | 工单 | 依赖 | 说明 |
|---|---|---|---|---|---|---|
| 1 | **T01 VideoCC**（含 schema 补齐） | A | ✅ | [T01](tasks/T01-videocc.md) | — | 首个端到端样板已验收并**已并入 main**（`6cdc5d8`），后续任务以 main 为基线 |
| 2 | **T02 Ego4D** | B | ⬜ | [T02](tasks/T02-ego4d.md) | license（**已签署，14 天窗口**） | 抢 license 窗口，独立轨道可并行 |
| 3 | T03 Ego-Exo4D | B | ⬜ | — | T02（共用 license/CLI 经验） | 照抄 T02，命令换 `egoexo`，视角后缀 |
| 4 | **T04 InternVid** | A | ⬜（**建议下一个派**） | — | T01 已验收，样板可复用 | 标注 HF 现成，第二个跑通的 A 类 |
| 5 | T05 MiraData | A | ⬜ | — | T01；建议在 T07 后 | 结构化 caption 存 JSON；与 HD-VILA 视频源重叠 |
| 6 | T06 HD-VG-130M | A | ⬜ | — | T01 | 规模最大 130M，分批注册；YouTube 限流是大头 |
| 7 | T07 HD-VILA-100M | A | ⬜ | — | T01；**先人工确认 caption 位置** | 一原视频对应多 clip，先下原片再本地切 |
| 8 | T08 LVD-2M | C | ⬜ | — | T06（HDVG 部分复用） | 三源组合，逻辑最绕；WebVid 源不稳定 |

## 二、基础设施任务

| 序 | 任务 | 状态 | 归属 | 说明 |
|---|---|---|---|---|
| INFRA-1 | schema 加 clip 时间戳列 | ✅ | 已随 **T01** 完成 | 实际实现为 `clip_start_us`/`clip_end_us`（微秒 INTEGER，非最初拟的秒 REAL，见 T01 验收结论）；`init_db()` 自带幂等迁移，老库自动补列。HD-VILA(T07) 复用同两列 |
| INFRA-2 | 代理池接入 | ⬜ | 待排 | `config.py` 现为单代理占位；量大后 YouTube 限流需要 |
| INFRA-3 | OSS 冷存储上传 | ⬜ | 待排 | `storage.upload_to_cold_storage` 接 oss2 SDK |
| INFRA-4 | MySQL backend | ⬜ | 待排（量级触发） | `db.get_conn` mysql 分支；SQLite 撑不住再做 |
| **INFRA-6** | **统一日志系统** | ⬜（**就绪可派**） | [INFRA-6](tasks/INFRA-6-logging.md) | 控制台+按数据集轮转文件，标准库 logging；建议三者中最先做 |
| **INFRA-7** | **程序异常邮件告警** | ⬜（**就绪可派**） | [INFRA-7](tasks/INFRA-7-email-alert.md) | smtplib，崩溃即邮件；只在崩溃/汇总发，不逐条发 |
| **INFRA-5** | **重试退避机制** | ⬜（**就绪可派**） | [INFRA-5](tasks/INFRA-5-retry-backoff.md) | 加 `next_retry_at`，退避期内不取任务（替掉 `time.sleep(0)` 占位） |

## 三、依赖关系图

```
T01 VideoCC (含 INFRA-1 schema) ──┬─► T04 InternVid
   │  (样板 + schema)             ├─► T05 MiraData ◄── 建议在 T07 之后
   │                              ├─► T06 HD-VG-130M ──► T08 LVD-2M(hdvg 部分复用)
   │                              └─► T07 HD-VILA-100M（先人工确认 caption）
   │
T02 Ego4D ──► T03 Ego-Exo4D        （B 类独立轨道，不依赖 T01，可并行；受 license 14 天窗口驱动）

INFRA-2/3/4/5 按需插入，不阻塞数据集主线
```

## 四、跨数据集注意事项（架构师维护的全局约束）

- **视频源重叠**：MiraData↔HD-VILA、LVD-2M↔HD-VG-130M 存在同源视频。先跑被复用方，
  靠 `common/dedupe.py` 的 MD5 查重跳过重复下载。派单顺序已在依赖图体现。
- **license 窗口**：Ego4D/Ego-Exo4D 共用一张 14 天过期的 license。写脚本不消耗 license，
  但**实际 CLI 下载要尽早在采集环境跑一次**验证有效性，别让窗口空耗。
- **到手率预期**：老标注（VideoCC）+ 超大规模（HD-VG-130M）+ 不稳定源（LVD-2M/WebVid）
  的实际到手率会明显偏低，验收时以"流程跑通 + 小样本到手率实测数字"为准，不苛求 100%。

## 五、变更记录

| 日期 | 变更 | 由谁 |
|---|---|---|
| 2026-07-23 | 建立看板；确定 T01→T02 优先级；Ego4D license 已签署 | 架构师窗口 |
| 2026-07-23 | T01 验收通过（5 项验收实跑）；INFRA-1 随之完成；clip 列定为微秒 INTEGER；建议下一个派 T04 | 架构师窗口 |
| 2026-07-23 | 应用户需求新增 3 张基础设施工单：INFRA-6 日志 / INFRA-7 邮件告警 / INFRA-5 重试退避（建议按此序做） | 架构师窗口 |
| 2026-07-23 | T01 已并入 main（`6cdc5d8`）；派出 INFRA-6/7/5 开发（分支 `claude/infra-log-mail-retry`） | 架构师窗口 |
