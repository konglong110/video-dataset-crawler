# 工单 INFRA-7 — 程序异常邮件告警

- **类型**：基础设施（`common/` 层，8 个数据集共用） · **依赖**：建议 INFRA-6（日志）先做 · **预估**：~0.5 人天
- **必读**：`docs/DEV_GUIDE.md`、`config.py`
- **要改/新增**：新增 `common/notify.py`；改 `config.py`（加 SMTP 配置）；在数据集入口接一层"崩溃即邮件"

## 目标

爬虫是长时间无人值守跑的，**程序异常/崩溃要能主动邮件通知**用户，而不是等他回来看日志才发现挂了。
提供一个统一的告警发送入口，并在采集入口包一层：**未捕获异常 → 发邮件 → 再抛出**。

## 设计决策（照此实现）

1. **配置全部从 `config.py` 读**（走环境变量，禁止硬编码密码）：
   `VDC_SMTP_HOST` / `VDC_SMTP_PORT` / `VDC_SMTP_USER` / `VDC_SMTP_PASSWORD` /
   `VDC_ALERT_FROM` / `VDC_ALERT_TO` / `VDC_ALERT_ENABLED`（默认 "0" 关闭，配好了置 "1"）。
2. **只用标准库 `smtplib` + `email`**，不引第三方。
3. **不要每个失败视频都发邮件**（会变垃圾邮件轰炸）。邮件只在两种情况发：
   - **程序级崩溃**（未捕获异常）；
   - **一批跑完的汇总**（可选：失败率超过阈值时提醒）。
   单个视频下载失败 → 只进日志（INFRA-6），不发邮件。
4. `VDC_ALERT_ENABLED != "1"` 或 SMTP 没配全时，`send_alert` **静默跳过并打日志**，绝不因为发信失败把主流程带崩。

## 实现要求

1. 新建 `common/notify.py`：
   - `send_alert(subject: str, body: str) -> bool`：用 smtplib 发纯文本邮件；未启用/配置缺失/发送异常都要
     捕获并记日志返回 False，不抛出。
   - `notify_on_crash(context: str)`：一个上下文管理器或装饰器，包住采集主流程；
     捕获未处理异常时组织 subject/body（含 context、异常类型、traceback 摘要）调 `send_alert`，然后 **re-raise**。
2. `config.py`：加上上述 SMTP/告警配置项。
3. 在数据集入口示范接入：`datasets/videocc/crawl.py` 的 `__main__` 用 `with notify_on_crash("videocc"):` 包住
   `register()/run_batch(...)`（作为其他数据集的样板；本工单只接 videocc 一个做示范）。

## 不要做

- 不做短信/钉钉/Webhook（本期只邮件）。
- 不对每条失败任务发信。
- 不把 SMTP 密码写进代码或提交进仓库。

## 验收标准

1. 配好一个测试邮箱（或用 `smtplib` 的调试/本地假 SMTP），`send_alert("测试","正文")` 能发出并返回 True。
2. `VDC_ALERT_ENABLED=0`（或不配 SMTP）时，`send_alert` 返回 False、打一条日志、**不抛异常**。
3. 用 `with notify_on_crash("videocc"):` 包一段故意抛异常的代码：能触发一封含 traceback 的邮件，且异常照常向上抛出（不被吞）。
4. 单个视频下载失败不会触发邮件（确认只在崩溃/汇总处发）。

## 交付

- 提交到本窗口指派的开发分支，commit 说明"新增邮件告警 + 采集入口崩溃通知"。
- 不创建 PR。回报：①改/增哪些文件 ②验收怎么验的（尤其"未启用时不崩") ③给用户的 SMTP 环境变量配置清单。
