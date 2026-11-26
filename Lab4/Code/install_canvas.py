"""Install the Canvas extension into the current local session only.

By default the session is found automatically: a folder under
<COPILOT_HOME>/session-state whose workspace.yaml points at this course root,
that holds an in-use lock of a running process, and whose event log was
written most recently (the session running this command). An explicit
--session-id still works. Nothing is installed into the global directory.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent
COURSE_ROOT = ROOT.parents[1]
# Two live sessions written within this many seconds of each other are
# treated as a tie rather than guessing between them.
TIE_SECONDS = 5


def copilot_home():
    return Path(os.environ.get("COPILOT_HOME", Path.home() / ".copilot"))


def workspace_cwd(session):
    """Read the cwd line of workspace.yaml without a YAML dependency."""
    try:
        for line in (session / "workspace.yaml").read_text(encoding="utf-8").splitlines():
            if line.startswith("cwd:"):
                return line.split(":", 1)[1].strip().strip("'\"")
    except OSError:
        return None
    return None


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return False
    return True


def has_live_lock(session, alive=pid_alive):
    for lock in session.glob("inuse.*.lock"):
        parts = lock.name.split(".")
        if len(parts) == 3 and parts[1].isdigit() and alive(int(parts[1])):
            return True
    return False


def last_activity(session):
    times = [p.stat().st_mtime for p in (session / "events.jsonl", session / "workspace.yaml") if p.exists()]
    return max(times, default=session.stat().st_mtime)


def find_session(home=None, course_root=COURSE_ROOT, alive=pid_alive):
    """Return the UUID of the live session working in course_root."""
    state = (home or copilot_home()) / "session-state"
    if not state.is_dir():
        raise ValueError(f"找不到 {state}。请在 Copilot App 的本地会话里运行本命令。")
    root = Path(course_root).resolve()
    candidates = []
    for session in state.iterdir():
        try:
            UUID(session.name)
        except ValueError:
            continue
        cwd = workspace_cwd(session)
        if not cwd or Path(cwd).resolve() != root:
            continue
        if has_live_lock(session, alive):
            candidates.append((last_activity(session), session.name))
    if not candidates:
        raise ValueError(
            f"没有找到正在 {root} 中运行的本地会话。"
            "请在 App 中用 Run on: This computer、Where to work: Current checkout 打开课程根目录后，在该会话里运行本命令。"
        )
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] - candidates[1][0] < TIE_SECONDS:
        listed = "、".join(name for _, name in candidates)
        raise ValueError(
            f"有多个会话同时在使用 {root}：{listed}。"
            "请关闭其他会话后重试，或用 --session-id 明确指定。"
        )
    return candidates[0][1]


def install(session_id, home=None):
    UUID(session_id)
    session = (home or copilot_home()) / "session-state" / session_id
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
    parser.add_argument("--session-id", default="auto",
                        help="本地会话 UUID；默认 auto，自动找到正在课程根目录中运行的会话")
    args = parser.parse_args()
    session_id = find_session() if args.session_id == "auto" else args.session_id
    if args.session_id == "auto":
        print(f"已自动识别当前会话：{session_id}")
    install(session_id)
