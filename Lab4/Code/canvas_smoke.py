"""Exercise runtime Canvas routing without claiming the App rendered a panel."""
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

from copilot.canvas import CanvasProviderIdentity
from copilot.generated.rpc import CanvasOpenRequest, CanvasActionInvokeRequest, CanvasCloseRequest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.agent import client, plain
from canvas_provider import DECLARATION, WeeklyCanvas

ROOT = Path(__file__).parent


async def main():
    provider = WeeklyCanvas()
    report = {"scope": "Python SDK runtime RPC only, NOT Copilot App native UI", "checks": []}
    async with client() as copilot:
        async with await copilot.create_session(
            model="gpt-6-luna", available_tools=[], enable_config_discovery=False,
            skip_custom_instructions=True, canvases=[DECLARATION],
            canvas_handler=provider,
            canvas_provider=CanvasProviderIdentity(id="hol:weekly", name="HOL Python Provider"),
            request_canvas_renderer=True,
        ) as session:
            try:
                report["discovery"] = plain(await session.rpc.canvas.list())
                opened = await session.rpc.canvas.open(CanvasOpenRequest(
                    canvas_id="weekly-compass", instance_id="weekly-a",
                    input={"document_id": "weekly-demo"}))
                report["opened"] = plain(opened)
                with urllib.request.urlopen(opened.url, timeout=10) as response:
                    assert response.status == 200
                report["checks"].append("open returns responsive loopback renderer")
                original = provider.store.read()
                first = original["tasks"][0]
                result = await session.rpc.canvas.action.invoke(CanvasActionInvokeRequest(
                    action_name="complete", instance_id="weekly-a",
                    input={"id": first["id"], "done": True}))
                if isinstance(result, dict) and "result" in result:
                    result = result["result"]
                assert result["tasks"][0]["done"] is True
                report["checks"].append("complete action persisted through runtime routing")
                await session.rpc.canvas.open(CanvasOpenRequest(
                    canvas_id="weekly-compass", instance_id="weekly-b",
                    input={"document_id": "weekly-demo"}))
                assert provider.store.read()["tasks"][0]["done"] is True
                report["checks"].append("second panel shares stable document state")
                for label, operation in (
                    ("invalid open rejected", session.rpc.canvas.open(CanvasOpenRequest(
                        canvas_id="weekly-compass", instance_id="invalid-a", input={"document_id": "../private"}))),
                    ("invalid action rejected", session.rpc.canvas.action.invoke(CanvasActionInvokeRequest(
                        action_name="complete", instance_id="weekly-a", input={"id": first["id"], "done": "yes"}))),
                    ("reserved verb rejected", session.rpc.canvas.action.invoke(CanvasActionInvokeRequest(
                        action_name="canvas.open", instance_id="weekly-a", input={}))),
                ):
                    try:
                        await operation
                    except Exception as error:
                        report["checks"].append(label)
                        report.setdefault("expected_errors", {})[label] = str(error)
                    else:
                        raise AssertionError(label + " did not fail")
                provider.store.complete(first["id"], first["done"])
                for panel in ("weekly-a", "weekly-b"):
                    await session.rpc.canvas.close(CanvasCloseRequest(instance_id=panel))
                report["checks"].append("close lifecycle completed")
            finally:
                provider.shutdown()
    target = ROOT / "../../verification/canvas-rpc.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
