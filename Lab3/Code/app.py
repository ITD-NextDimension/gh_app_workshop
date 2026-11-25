import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.web import serve
from finance import dataset, views

ROOT = Path(__file__).parent


def get_api(path):
    if path == "/api/data":
        data = dataset()
        data["views"] = views(data)
        return data
    if path == "/api/analysis":
        analysis = json.loads((ROOT / "output/analysis.json").read_text())
        if analysis.get("trace", {}).get("session_id"):
            analysis["trace"]["session_id"] = "本机 analysis.json 已记录"
        return analysis
    raise ValueError("Unknown API")


if __name__ == "__main__":
    serve(ROOT, 8013, get_api=get_api)
