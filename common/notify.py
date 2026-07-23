"""
程序异常邮件告警。爬虫是长时间无人值守跑的，程序级崩溃要能主动邮件通知用户，
而不是等他回来翻日志才发现挂了。

设计要点（见工单 INFRA-7）：
- 配置全部从 config.py 读（走环境变量，禁止硬编码密码）。
- 只用标准库 smtplib + email，不引第三方。
- 只在"程序崩溃 / 一批汇总"这种时刻发，绝不逐条失败发邮件（否则变垃圾邮件轰炸）；
  单条视频下载失败只进日志（INFRA-6），不走这里。
- 未启用 / 配置缺失 / 发送异常，都捕获记日志并返回 False，绝不抛出——
  发信失败不能把主采集流程带崩。
"""
import smtplib
import traceback
from contextlib import contextmanager
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    ALERT_FROM, ALERT_TO, ALERT_ENABLED, REQUEST_TIMEOUT_SEC,
)
from common.logging_setup import get_logger

# 告警自身用固定的 "notify" 日志通道，落 LOG_DIR/notify.log
_log = get_logger("notify")


def _recipients():
    """收件人支持逗号分隔多个，顺手去掉空白项。"""
    return [addr.strip() for addr in ALERT_TO.split(",") if addr.strip()]


def send_alert(subject: str, body: str) -> bool:
    """
    发一封纯文本告警邮件，成功返回 True。

    未启用（VDC_ALERT_ENABLED != "1"）、SMTP 配置缺失、或发送过程抛异常，
    都会被捕获、记一条日志并返回 False——绝不抛出，保证发信失败不拖垮主流程。
    """
    if ALERT_ENABLED != "1":
        _log.info("告警未启用（VDC_ALERT_ENABLED != 1），跳过发信：%s", subject)
        return False

    recipients = _recipients()
    # 配置没配全就静默跳过，别在无人值守时因为发信报错把爬虫带崩
    if not (SMTP_HOST and ALERT_FROM and recipients):
        _log.warning("SMTP 配置不全（HOST/FROM/TO 缺失），跳过发信：%s", subject)
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = ALERT_FROM
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)

    try:
        # 465 走 SSL，其余（如 587）走 STARTTLS——覆盖常见邮箱服务商配置
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=REQUEST_TIMEOUT_SEC)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=REQUEST_TIMEOUT_SEC)
            server.starttls()
        with server:
            # 有账号密码才登录；有些内网中继匿名直发，就不强制登录
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_FROM, recipients, msg.as_string())
        _log.info("告警邮件已发送：%s -> %s", subject, recipients)
        return True
    except Exception as e:  # noqa: BLE001 - 发信任何异常都不能拖垮主流程
        _log.error("告警邮件发送失败（%s）：%s", type(e).__name__, e)
        return False


@contextmanager
def notify_on_crash(context: str):
    """
    包住采集主流程的上下文管理器：主流程抛出未捕获异常时，组织一封含
    context / 异常类型 / traceback 的告警邮件，发出后 **re-raise**——
    异常照常向上抛出（不吞掉，崩溃行为不变，只是崩之前多发一封提醒）。

    单条下载失败不会走到这里（那些在 worker 里被兜底成重试，只进日志），
    所以不会造成逐条失败刷邮件。

        with notify_on_crash("videocc"):
            register()
            run_batch(...)
    """
    try:
        yield
    except Exception as e:
        tb = traceback.format_exc()
        subject = f"[视频爬虫告警] {context} 崩溃：{type(e).__name__}"
        body = (
            f"数据集/上下文：{context}\n"
            f"异常类型：{type(e).__name__}\n"
            f"异常信息：{e}\n\n"
            f"Traceback:\n{tb}"
        )
        # send_alert 内部已兜底，不会因发信失败再抛新异常盖掉原始异常
        send_alert(subject, body)
        raise
