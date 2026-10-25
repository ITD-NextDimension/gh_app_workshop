"""Canvas child process: one JSON readiness line on stdout; Python owns the app."""
import json
from pathlib import Path

from app import apis
from store import Store
from tools.web import make_server

ROOT = Path(__file__).parent


if __name__ == "__main__":
    store = Store(ROOT / "output/plan.json")
    store.read()
    get, post = apis(store)
    server = make_server(ROOT, 0, get_api=get, post_api=post)
    print(json.dumps({"url": f"http://127.0.0.1:{server.server_port}/"}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
