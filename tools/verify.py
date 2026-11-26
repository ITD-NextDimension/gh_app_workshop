"""Reproducible Python Playwright assertions + real screenshots; servers cleaned up."""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.evidence import build_all

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


@contextmanager
def process(command, url, name, cwd=ROOT):
    log_path = ROOT / "verification" / (name + ".log")
    with log_path.open("w") as log:
        child = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(160):
                if child.poll() is not None:
                    raise RuntimeError(f"{name} 提前退出，请检查 {log_path}")
                try:
                    with urllib.request.urlopen(url, timeout=1) as r:
                        if r.status == 200:
                            break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(.25)
            else:
                raise RuntimeError(f"{name} 未就绪")
            yield
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)


def shot(page, lab, name, full=False):
    page.screenshot(path=str(ROOT / lab / "screenshots" / name), full_page=full,
                    animations="disabled")


def main():
    build_all()
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "checks": [],
              "limitations": [
                  "Native setup and plan approval captured separately; custom Canvas sidebar remains blocked by missing native extension tools.",
                  "This runner uses demo fixtures. Authenticated selected Outlook data verified separately in outlook-live.json.",
              ]}
    with ExitStack() as stack:
        for lab, port in ((1, 8011), (3, 8013), (4, 8014)):
            stack.enter_context(process([PYTHON, str(ROOT / f"Lab{lab}/Code/app.py")],
                                        f"http://127.0.0.1:{port}/", f"lab{lab}-server"))
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            for lab in range(1, 5):
                page.goto((ROOT / f"Lab{lab}/Code/output/evidence.html").as_uri())
                shot(page, f"Lab{lab}", "01-execution-record.png", full=True)
            page.goto((ROOT / "Lab4/Code/output/extension-evidence.html").as_uri())
            shot(page, "Lab4", "07-extension-runtime.png", full=True)
            page.goto((ROOT / "Lab4/Code/output/live-evidence.html").as_uri())
            shot(page, "Lab4", "09-live-validation.png", full=True)
            page.goto("http://127.0.0.1:8011/generated.html")
            expect(page.locator(".cell")).to_have_count(90)
            expect(page.locator(".piece")).to_have_count(32)
            expect(page.locator("#status")).to_contain_text("红方")
            shot(page, "Lab1", "03-generated-game.png")
            page.locator('[data-x="0"][data-y="6"]').click()
            expect(page.locator(".target")).to_have_count(1)
            shot(page, "Lab1", "04-legal-target.png")
            page.locator('[data-x="0"][data-y="5"]').click()
            expect(page.locator("#status")).to_contain_text("黑方")
            expect(page.locator("#status")).to_contain_text("1 步")
            shot(page, "Lab1", "05-first-move.png")
            page.get_by_role("button", name="悔一步", exact=True).click()
            expect(page.locator("#status")).to_contain_text("0 步")
            shot(page, "Lab1", "06-undo.png")
            page.get_by_role("button", name="重新开局", exact=True).click()
            expect(page.locator(".piece")).to_have_count(32)
            page.set_viewport_size({"width": 390, "height": 1100})
            assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
            shot(page, "Lab1", "07-mobile.png", full=True)
            page.set_viewport_size({"width": 1440, "height": 1000})
            report["checks"].append("Lab1 generated HTML: 90 positions, 32 pieces, legal hint, move, undo, reset, mobile")
            page.set_viewport_size({"width": 1080, "height": 1920})
            for t, name in ((10, "04-video-opening.png"), (30, "05-video-ai.png"),
                            (50, "06-video-display.png"), (70, "07-video-workflow.png"),
                            (90, "08-video-ports.png"), (110, "09-video-repair.png")):
                frame = ROOT / f"Lab2/Code/film/output/frame-{t}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i",
                    str(ROOT / "Lab2/Code/film/output/surface-ultra.mp4"),
                    "-frames:v", "1", "-y", str(frame)], check=True)
                page.goto(frame.as_uri())
                assert page.locator("img").evaluate("img=>img.naturalWidth===1080&&img.naturalHeight===1920")
                page.locator("img").screenshot(path=str(ROOT / "Lab2/screenshots" / name))
            page.set_viewport_size({"width": 1440, "height": 1000})
            report["checks"].append("Lab2 CLI-rendered MP4: six real decoded frames (one per 20s scene) at 1080x1920; no custom player UI")
            page.goto("http://127.0.0.1:8013/")
            expect(page.locator("#cards")).to_contain_text("281,724")
            expect(page.locator("#findings .finding")).to_have_count(3)
            shot(page, "Lab3", "03-overview.png")
            page.get_by_role("button", name="筛选 Intelligent Cloud").click()
            expect(page.locator("#cards")).to_contain_text("106,265")
            shot(page, "Lab3", "04-cloud-filter.png")
            page.locator("#year").select_option("2024")
            expect(page.locator("#cards")).to_contain_text("87,464")
            shot(page, "Lab3", "05-year-filter.png")
            page.get_by_role("button", name="业务分部", exact=True).click()
            expect(page.locator("#segment-table tr")).to_have_count(3)
            shot(page, "Lab3", "06-segment-view.png")
            page.get_by_role("button", name="数据与来源", exact=True).click()
            expect(page.locator("#provenance")).to_contain_text("sha256")
            shot(page, "Lab3", "07-source-view.png")
            report["checks"].append("Lab3 totals, single-agent narrative, cloud/year cross-filter and provenance views")
            page.goto("http://127.0.0.1:8014/")
            expect(page.locator(".task")).to_have_count(3)
            expect(page.locator("#mode")).to_contain_text("虚构")
            shot(page, "Lab4", "04-weekly-board.png")
            page.locator("details").first.locator("summary").click()
            expect(page.locator("blockquote").first).to_be_visible()
            shot(page, "Lab4", "05-mail-evidence.png")
            checkbox = page.get_by_role("checkbox").first
            initial = checkbox.is_checked()
            checkbox.set_checked(not initial)
            expect(page.get_by_role("checkbox").first).to_be_checked(checked=not initial)
            page.reload()
            expect(page.get_by_role("checkbox").first).to_be_checked(checked=not initial)
            shot(page, "Lab4", "06-persistent-completion.png")
            page.get_by_role("checkbox").first.set_checked(initial)
            expect(page.get_by_role("checkbox").first).to_be_checked(checked=initial)
            response = page.request.get("http://127.0.0.1:8014/private/live-input.json")
            assert response.status == 404
            response = page.request.post("http://127.0.0.1:8014/api/complete", data={"id": "x", "done": True})
            assert response.status == 403
            report["checks"].append("Lab4 source expansion, persistent completion/reload and private-file access denied")
            report["browser_errors"] = errors
            assert not errors, errors
            browser.close()
    subprocess.run(["ffmpeg", "-v", "error", "-i",
        str(ROOT / "Lab2/Code/film/output/surface-ultra.mp4"), "-f", "null", "-"],
        check=True, capture_output=True)
    report["checks"].append("All 3600 final MP4 frames decode without errors")
    (ROOT / "verification/playwright.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
