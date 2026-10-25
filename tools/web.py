"""Small loopback-only HTTP host shared by the Python labs."""
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


def make_server(root, port, get_api=None, post_api=None, files=None):
    root = Path(root)
    public = files or {"/": "index.html", "/style.css": "style.css", "/app.js": "app.js"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def reply(self, status, body, mime="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in public:
                file = root / public[path]
                if not file.is_file():
                    self.reply(404, {"error": "文件尚未生成，请先执行 README 中的前置命令。"})
                    return
                mime = mimetypes.guess_type(file)[0] or "application/octet-stream"
                self.reply(200, file.read_bytes(), mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
            elif path.startswith("/api/") and get_api:
                try:
                    self.reply(200, get_api(path))
                except (ValueError, FileNotFoundError) as error:
                    self.reply(400, {"error": str(error)})
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if self.headers.get("X-Workshop") != "1":
                self.reply(403, {"error": "需要同源实验页面的 X-Workshop 请求标记。"})
                return
            origin = self.headers.get("Origin")
            if origin and origin != f"http://{self.headers.get('Host')}":
                self.reply(403, {"error": "拒绝跨来源写入。"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384:
                self.reply(400, {"error": "Invalid request size"})
                return
            try:
                if not post_api:
                    raise ValueError("此实验没有写入接口。")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("JSON body must be an object")
                self.reply(200, post_api(urlsplit(self.path).path, body))
            except (ValueError, KeyError, TypeError) as error:
                self.reply(400, {"error": str(error)})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(root, port, **kwargs):
    server = make_server(root, port, **kwargs)
    print(f"实验已启动：http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n实验已停止。")
    finally:
        server.server_close()
