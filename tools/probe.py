"""Record public capabilities, never authentication tokens."""
import asyncio
import dataclasses
import importlib.metadata
import json
import shutil
from pathlib import Path

from copilot import CopilotClient, RuntimeConnection

ROOT = Path(__file__).resolve().parents[1]


async def main():
    async with CopilotClient(
        connection=RuntimeConnection.for_stdio(path=shutil.which("copilot")),
    ) as client:
        models = await client.list_models()
        def plain(item):
            if dataclasses.is_dataclass(item):
                return dataclasses.asdict(item)
            if hasattr(item, "model_dump"):
                return item.model_dump(mode="json")
            return item
        result = {
            "sdk": importlib.metadata.version("github-copilot-sdk"),
            "models": [plain(m) for m in models],
        }
        target = ROOT / "verification" / "capabilities.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(target)
        print([plain(m).get("id") for m in models])


asyncio.run(main())
