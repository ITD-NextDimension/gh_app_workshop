import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.web import serve
from finance import dataset

ROOT = Path(__file__).parent


def get_api(path):
    if path == "/api/data":
        return dataset()
    if path == "/api/analysis":
        return json.loads((ROOT / "output/analysis.json").read_text())
    raise ValueError("Unknown API")


if __name__ == "__main__":
    serve(ROOT, 8013, get_api=get_api)
