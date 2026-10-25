"""Load the real .mjs Canvas adapter in a runtime, then drive it via Canvas RPC."""
import asyncio
import json
import shutil
import sys
import urllib.request
from pathlib import Path

from copilot import CopilotClient, RuntimeConnection
from copilot.generated.rpc import CanvasOpenRequest, CanvasActionInvokeRequest, CanvasCloseRequest
from copilot.session import PermissionHandler
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.agent import plain
from install_canvas import install

ROOT = Path(__file__).parent


async def main(args):
    async with CopilotClient(connection=RuntimeConnection.for_stdio(path=shutil.which("copilot"))) as client:
        async with await client.create_session(
            model="gpt-6-luna", on_permission_request=PermissionHandler.approve_all,
            request_extensions=True, request_canvas_renderer=True,
            extension_sdk_path=str(args.sdk_path), available_tools=["extensions_manage", "extensions_reload"],
            skip_custom_instructions=True, enable_config_discovery=False,
        ) as session:
            target = install(session.session_id)
            try:
                message = await session.send_and_wait(
                    "Call extensions_reload, then extensions_manage operation list and operation inspect "
                    "name hol-weekboard. Do not call any other tools. Return the load status.", timeout=120)
                report = {"runtime_status": message.data.content if message else None,
                          "scope": "Real scaffold-derived extension loaded in SDK runtime; NOT App native UI screenshot"}
                canvases = await session.rpc.canvas.list()
                report["discovery"] = plain(canvases)
                if not any(c.canvas_id == "hol-weekboard" for c in canvases.canvases):
                    raise RuntimeError("Canvas extension did not register")
                opened = await session.rpc.canvas.open(CanvasOpenRequest(
                    canvas_id="hol-weekboard", instance_id="extension-board",
                    input={"document_id": "weekly-demo"}))
                with urllib.request.urlopen(opened.url + "api/plan", timeout=10) as response:
                    state = json.load(response)
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch()
                    page = await browser.new_page(viewport={"width": 1440, "height": 1100})
                    await page.goto(opened.url)
                    await page.locator(".task").first.wait_for()
                    assert await page.locator(".task").count() == 3
                    await page.screenshot(path=str(ROOT / "../screenshots/08-extension-renderer.png"))
                    await browser.close()
                first = state["tasks"][0]
                response = await session.rpc.canvas.action.invoke(CanvasActionInvokeRequest(
                    action_name="complete", instance_id="extension-board",
                    input={"id": first["id"], "done": not first["done"]}))
                result = response.get("result", response)
                assert result["tasks"][0]["done"] is not first["done"]
                await session.rpc.canvas.action.invoke(CanvasActionInvokeRequest(
                    action_name="complete", instance_id="extension-board",
                    input={"id": first["id"], "done": first["done"]}))
                report["checks"] = ["extensions_reload/list/inspect", "real extension discovery",
                                     "open -> Python loopback renderer", "action -> Python persisted state"]
                report["opened"] = plain(opened)
                await session.rpc.canvas.close(CanvasCloseRequest(instance_id="extension-board"))
                for index in range(3):
                    instance_id = f"reopened-{index}"
                    reopened = await session.rpc.canvas.open(CanvasOpenRequest(
                        canvas_id="hol-weekboard", instance_id=instance_id,
                        input={"document_id": "weekly-demo"}))
                    with urllib.request.urlopen(reopened.url + "api/plan", timeout=10) as response:
                        assert json.load(response)["tasks"][0]["done"] is first["done"]
                    await asyncio.sleep(0.1)
                    focused = await session.rpc.canvas.open(CanvasOpenRequest(
                        canvas_id="hol-weekboard", instance_id=f"peer-{index}",
                        input={"document_id": "weekly-demo"}))
                    assert focused.url == reopened.url
                    await session.rpc.canvas.close(CanvasCloseRequest(instance_id=f"peer-{index}"))
                    await session.rpc.canvas.close(CanvasCloseRequest(instance_id=instance_id))
                report["checks"].append("close/reopen x3: persisted state and stable shared Python bridge")
                (ROOT / "../../verification/canvas-extension.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2))
                print(json.dumps(report, ensure_ascii=False, indent=2))
            finally:
                # Only remove the two files and exact directory created by this test.
                for name in ("extension.mjs", "config.json"):
                    path = target / name
                    if path.exists():
                        path.unlink()
                target.rmdir()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk-path", type=Path, required=True,
                        help="Canonical extension SDK path from extensions_manage guide.")
    asyncio.run(main(parser.parse_args()))
