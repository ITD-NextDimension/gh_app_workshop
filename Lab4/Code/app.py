import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.web import serve
from store import Store

ROOT = Path(__file__).parent


def apis(store):
    def get_api(path):
        if path == "/api/plan":
            return store.read()
        raise ValueError("Unknown API")

    def post_api(path, body):
        if path == "/api/complete":
            return store.complete(body["id"], body["done"])
        raise ValueError("Unknown API")
    return get_api, post_api


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    store = Store(ROOT / ("private" if args.live else "output") / "plan.json")
    get, post = apis(store)
    serve(ROOT, 8014, get_api=get, post_api=post)
