"""Install only into an explicitly supplied current-session extension directory."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent


def install(session_id):
    UUID(session_id)
    home = Path(os.environ.get("COPILOT_HOME", Path.home() / ".copilot"))
    session = home / "session-state" / session_id
    if not session.is_dir():
        raise ValueError("此本地会话目录不存在。请使用 App 当前本地会话的真实 ID，不要猜测。")
    target = session / "extensions/hol-weekboard"
    entry = target / "extension.mjs"
    if entry.exists():
        raise FileExistsError("已存在同名扩展；为避免覆盖，先检查当前会话已有内容。")
    target.mkdir(parents=True)
    shutil.copyfile(ROOT / "canvas-extension/extension.mjs", entry)
    (target / "config.json").write_text(json.dumps({
        "python": sys.executable,
        "bridge": str(ROOT / "bridge.py"),
    }, indent=2))
    print(f"已安装会话级扩展：{target}")
    print("请在同一 App 会话请求 extensions_reload，再 list/inspect/open 验收。")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()
    install(args.session_id)
