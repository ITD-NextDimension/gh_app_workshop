"""Real Python SDK Canvas provider; not a fake App screenshot or JS plugin."""
import sys
import threading
from pathlib import Path

from copilot.canvas import CanvasDeclaration, CanvasError, CanvasHandler
from copilot.generated.rpc import CanvasAction, CanvasProviderOpenResult

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.web import make_server
from app import apis
from store import Store

ROOT = Path(__file__).parent
OPEN_SCHEMA = {"type": "object", "properties": {"document_id": {"const": "weekly-demo"}},
               "required": ["document_id"], "additionalProperties": False}
ACTION_SCHEMA = {"type": "object", "properties": {
    "id": {"type": "string"}, "done": {"type": "boolean"}},
    "required": ["id", "done"], "additionalProperties": False}
DECLARATION = CanvasDeclaration(
    id="weekly-compass", display_name="每周行动清单",
    description="查看多 Agent 整理的本周任务，核对来源并保存本地完成状态。",
    input_schema=OPEN_SCHEMA,
    actions=[CanvasAction(name="complete", description="设置本地任务完成状态", input_schema=ACTION_SCHEMA)],
)


class WeeklyCanvas(CanvasHandler):
    def __init__(self, path=ROOT / "output/plan.json"):
        self.store = Store(path)
        self.server = None
        self.thread = None
        self.panels = set()

    async def on_open(self, ctx):
        if ctx.input != {"document_id": "weekly-demo"}:
            raise CanvasError("invalid_document", "Only the public training document is allowed.")
        if self.server is None:
            get, post = apis(self.store)
            self.server = make_server(ROOT, 0, get_api=get, post_api=post)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
        self.panels.add(ctx.instance_id)
        return CanvasProviderOpenResult(
            url=f"http://127.0.0.1:{self.server.server_port}/",
            title="每周行动清单 · 虚构练习数据",
            status="ready",
        )

    async def on_action(self, ctx):
        if ctx.action_name != "complete":
            raise CanvasError.no_handler()
        try:
            return self.store.complete(ctx.input["id"], ctx.input["done"])
        except (ValueError, KeyError, TypeError) as error:
            raise CanvasError("invalid_task", str(error)) from error

    async def on_close(self, ctx):
        self.panels.discard(ctx.instance_id)
        if not self.panels:
            self.shutdown()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.thread.join(timeout=5)
