"""Public sources and an unauthenticated sign-in screen only."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        for url, target in [
            ("https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions",
             "Lab1/screenshots/02-app-official-guide.png"),
            ("https://www.microsoft.com/investor/reports/ar25/index.html",
             "Lab3/screenshots/02-official-annual-report.png"),
        ]:
            response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
            assert response and response.ok
            page.screenshot(path=str(ROOT / target))
            results.append({"url": page.url, "screenshot": target, "kind": "public source"})
        page.goto("https://outlook.office.com/mail/", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_url(lambda url: urlsplit(str(url)).hostname in
                          ("login.microsoftonline.com", "login.live.com"), timeout=60000)
        assert urlsplit(page.url).hostname in ("login.microsoftonline.com", "login.live.com")
        page.screenshot(path=str(ROOT / "Lab4/screenshots/02-outlook-sign-in.png"))
        results.append({"host": urlsplit(page.url).hostname,
                        "screenshot": "Lab4/screenshots/02-outlook-sign-in.png",
                        "kind": "unauthenticated login only; NO mailbox accessed"})
        browser.close()
    (ROOT / "verification/public-screenshots.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
