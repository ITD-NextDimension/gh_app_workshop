"""Read selected Outlook pages only after a human signs in and confirms scope."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent


def read_outlook_main(page, label, minimum_length):
    url = urlsplit(page.url)
    if url.scheme != "https" or url.hostname not in (
        "outlook.office.com", "outlook.live.com", "outlook.cloud.microsoft"
    ):
        raise ValueError(f"当前页面不是 Outlook {label}；可能尚未登录或登录已过期，停止采集。")
    main = page.get_by_role("main")
    if main.count() != 1:
        raise ValueError(f"无法唯一确认{label}正文区域；停止采集，不猜选择器。")
    text = main.inner_text().strip()
    if len(text) < minimum_length:
        raise ValueError(f"{label}正文为空或未加载；停止采集。")
    return text


def live():
    private = ROOT / "private"
    private.mkdir(exist_ok=True, mode=0o700)
    print("仅在新开的隔离浏览器中登录本人 Outlook。不要在终端输入密码或 MFA。")
    print("本工具不发送、不删除、不创建会议；打开邮件可能被 Outlook 标记已读。")
    print("采集结果仅保存在 private；还未脱敏，不会自动发送给模型。")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://outlook.office.com/mail/", wait_until="domcontentloaded")
        input("请完成登录，并打开本周你允许分析的第一封邮件。准备好后在此按 Enter：")
        messages = []
        while True:
            text = read_outlook_main(page, "邮件", 30)
            url = page.url
            subject = input("请填写当前邮件主题（随后可脱敏）：").strip()
            received = input("请核对收件时间，输入 ISO8601（例如 2026-10-19T08:10:00+08:00）：").strip()
            date = datetime.fromisoformat(received)
            if date.tzinfo is None:
                raise ValueError("收件时间必须有时区")
            messages.append({"id": f"mail-{len(messages)+1:03}", "subject": subject,
                             "received": received, "body": text, "url": url})
            if len(messages) >= 10 or input("继续采集下一封已打开邮件？输入 y，其他输入结束：").strip().lower() != "y":
                break
            input("请在同一浏览器标签页打开下一封本周邮件，再按 Enter：")
        page.goto("https://outlook.office.com/calendar/view/week", wait_until="domcontentloaded")
        input("请确认日历显示本周，所有待分析事件已可见，再按 Enter：")
        calendar_text = read_outlook_main(page, "日历", 20)
        result = {
            "data_mode": "live", "needs_review": True, "timezone": "Asia/Shanghai",
            "reference_now": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
            "emails": messages, "events": [],
            "calendar_capture": calendar_text,
            "review_instructions": "脱敏邮件；只保留本人选中的正文；核对收件日期；将可见日历事件核对为 id/title/start/end，包含时区；完成后设 needs_review=false。",
        }
        output = private / "live-input.json"
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        output.chmod(0o600)
        context.close()
        browser.close()
        print("采集结束。请人工核对 private/live-input.json；没有自动调用模型。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args()
    live()
