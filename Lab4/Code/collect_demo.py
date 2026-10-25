"""Run the same read -> review -> plan idea against explicitly fictional DOM."""
import html
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent


def main():
    data = json.loads((ROOT / "data/demo.json").read_text())
    chunks = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>虚构训练资料 · 不是 Outlook</title>',
              '<style>body{font:16px/1.8 system-ui;background:#f5f8f9;color:#213a45;padding:40px;max-width:1100px;margin:auto}h1{font-size:36px}header{background:#dceef6;padding:20px;border-radius:10px}section{background:white;border:1px solid #d9e2e6;padding:24px;margin:20px 0;border-radius:10px}small{color:#6d8794}table{width:100%;text-align:left}td{padding:12px;border-bottom:1px solid #eee}</style>',
              '<header>虚构练习资料 · 本页不是 Outlook，也不含真实邮件或账户</header>',
              '<h1>本周的故事，藏在三封邮件里。</h1>',
              '<p>演示时钟：2026-10-19 09:00 / Asia/Shanghai</p>']
    for mail in data["emails"]:
        chunks.append(f'<section data-mail-id="{mail["id"]}" data-received="{mail["received"]}">'
                      f'<small>{mail["id"]} · {mail["received"]}</small>'
                      f'<h2>{html.escape(mail["subject"])}</h2><p class="body">{html.escape(mail["body"])}</p></section>')
    chunks.append('<h2>已核对的本周日历（虚构）</h2><table>')
    for event in data["events"]:
        chunks.append(f'<tr data-event-id="{event["id"]}" data-start="{event["start"]}" data-end="{event["end"]}">'
                      f'<td class="title">{html.escape(event["title"])}</td><td>{event["start"]}</td><td>{event["end"]}</td></tr>')
    chunks.append('</table></html>')
    fixture = ROOT / "data/training-pages.html"
    fixture.write_text("".join(chunks))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1100}, device_scale_factor=1)
        page.goto(fixture.resolve().as_uri())
        emails = page.locator("[data-mail-id]").evaluate_all(
            "nodes=>nodes.map(n=>({id:n.dataset.mailId,received:n.dataset.received,subject:n.querySelector('h2').textContent,body:n.querySelector('.body').textContent}))")
        events = page.locator("[data-event-id]").evaluate_all(
            "nodes=>nodes.map(n=>({id:n.dataset.eventId,start:n.dataset.start,end:n.dataset.end,title:n.querySelector('.title').textContent}))")
        assert emails == data["emails"] and events == data["events"]
        result = {**data, "emails": emails, "events": events, "capture_method": "Playwright local fictional DOM"}
        (ROOT / "data/collected-demo.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        page.screenshot(path=str(ROOT / "../screenshots/03-training-capture.png"), full_page=True)
        browser.close()
    print("Playwright 已核对 3 封虚构邮件和 3 个日历事件，未访问真实邮箱。")


if __name__ == "__main__":
    main()
