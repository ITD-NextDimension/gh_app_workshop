import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.web import serve
from xiangqi import Game

game = Game()
lock = threading.Lock()


def get_api(path):
    if path != "/api/state":
        raise ValueError("Unknown API")
    with lock:
        return game.state()


def post_api(path, body):
    global game
    with lock:
        if path == "/api/select":
            start = body["start"]
            if not isinstance(start, list) or len(start) != 2:
                raise ValueError("请选择棋盘交点。")
            return {"moves": game.moves(tuple(start))}
        if path == "/api/move":
            start, end = body["start"], body["end"]
            if not all(isinstance(p, list) and len(p) == 2 for p in (start, end)):
                raise ValueError("Invalid coordinates")
            game.move(tuple(start), tuple(end))
        elif path == "/api/undo":
            game.undo()
        elif path == "/api/reset":
            game = Game()
        else:
            raise ValueError("Unknown API")
        return game.state()


if __name__ == "__main__":
    serve(Path(__file__).parent, 8011, get_api=get_api, post_api=post_api, files={
        "/": "index.html", "/generated.html": "generated.html",
        "/style.css": "style.css", "/app.js": "app.js",
    })
