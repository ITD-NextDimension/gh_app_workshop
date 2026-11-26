import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chess = load("xiangqi", "Lab1/Code/xiangqi.py")
finance = load("finance", "Lab3/Code/finance.py")
schedule = load("schedule", "Lab4/Code/schedule.py")
store_module = load("store", "Lab4/Code/store.py")
collect_module = load("collect_live", "Lab4/Code/collect.py")
sys.path.insert(0, str(ROOT / "Lab4/Code"))
normalizer = load("normalize_live_capture", "Lab4/Code/normalize_capture.py")


def test_calendar_capture_normalization():
    event = normalizer.normalize_event(
        "Private name, 11:00 PM to 12:00 AM, Wednesday, October 21, 2026 to Thursday, October 22, 2026, Busy",
        "calendar-001", "Asia/Shanghai")
    assert event["start"] == "2026-10-21T23:00:00+08:00"
    assert event["end"] == "2026-10-22T00:00:00+08:00"
    assert "Private" not in json.dumps(event)


def test_calendar_capture_all_day():
    event = normalizer.normalize_event(
        "Private name, All day, Monday, October 19, 2026, Busy",
        "calendar-002", "Asia/Shanghai")
    assert event["end"] == "2026-10-20T00:00:00+08:00"


@pytest.mark.parametrize("label", [
    "Next day",
    "Canceled: Private, 9:00 AM to 10:00 AM, Monday, October 19, 2026, Busy",
    "Private, 9:00 AM to 10:00 AM, Monday, October 19, 2026, Free",
])
def test_calendar_capture_excludes_non_busy_entries(label):
    assert normalizer.normalize_event(label, "calendar-001", "Asia/Shanghai") is None


@pytest.mark.parametrize("label", [
    "Private, 9:00 AM",
    "Private, 11:00 PM to 12:00 AM, Monday, October 19, 2026, Busy",
    "Private, Monday, October 19, 2026, Busy",
])
def test_calendar_capture_rejects_ambiguous_timing(label):
    with pytest.raises(ValueError):
        normalizer.normalize_event(label, "calendar-001", "Asia/Shanghai")


@pytest.mark.parametrize("url", [
    "https://login.microsoftonline.com/",
    "https://outlook.office.com.example.org/mail/",
    "http://outlook.office.com/mail/",
    "https://example.org/outlook.office.com/mail/",
])
def test_outlook_rejects_login_or_wrong_origin(url):
    page = Mock(url=url)
    with pytest.raises(ValueError, match="停止采集"):
        collect_module.read_outlook_main(page, "日历", 20)
    page.get_by_role.assert_not_called()


@pytest.mark.parametrize("host", [
    "outlook.office.com", "outlook.live.com", "outlook.cloud.microsoft"
])
def test_outlook_extracts_single_main(host):
    page = Mock(url=f"https://{host}/calendar/view/week")
    main = page.get_by_role.return_value
    main.count.return_value = 1
    main.inner_text.return_value = "  " + "visible calendar event " * 3 + "  "
    assert collect_module.read_outlook_main(page, "日历", 20) == main.inner_text.return_value.strip()


@pytest.mark.parametrize("count", [0, 2])
def test_outlook_rejects_ambiguous_main(count):
    page = Mock(url="https://outlook.office.com/mail/")
    page.get_by_role.return_value.count.return_value = count
    with pytest.raises(ValueError, match="唯一确认"):
        collect_module.read_outlook_main(page, "邮件", 30)


def test_outlook_rejects_empty_calendar():
    page = Mock(url="https://outlook.office.com/calendar/view/week")
    main = page.get_by_role.return_value
    main.count.return_value = 1
    main.inner_text.return_value = " "
    with pytest.raises(ValueError, match="未加载"):
        collect_module.read_outlook_main(page, "日历", 20)


def empty():
    game = chess.Game()
    game.board = [[None] * 9 for _ in range(10)]
    game.board[9][4] = "rK"
    game.board[0][3] = "bK"
    return game


def test_initial_board_and_undo():
    game = chess.Game()
    assert sum(bool(p) for row in game.board for p in row) == 32
    game.move((0, 6), (0, 5))
    assert game.turn == "b" and len(game.history) == 1
    game.undo()
    assert game.turn == "r" and game.board[6][0] == "rP"
    with pytest.raises(ValueError):
        game.undo()


@pytest.mark.parametrize("start,end,allowed", [
    ((0, 6), (0, 5), True), ((0, 6), (1, 6), False),
    ((0, 6), (0, 7), False), ((1, 9), (2, 7), True),
    ((1, 9), (3, 8), False), ((2, 9), (4, 7), True),
    ((3, 9), (4, 8), True), ((4, 9), (4, 8), True),
    ((4, 9), (6, 9), False), ((0, 9), (0, 5), False),
    ((0, 3), (0, 4), False), ((-1, 6), (0, 5), False),
    ((True, 6), (0, 5), False),
])
def test_rules(start, end, allowed):
    assert bool(chess.Game().legal(start, end)) == allowed


def test_horse_leg_elephant_eye_and_river():
    game = empty()
    game.board[7][1] = "rH"
    game.board[7][2] = "rP"
    assert not game.pseudo((1, 7), (3, 6))
    game.board[6][4] = "rE"
    game.board[5][3] = "rP"
    assert not game.pseudo((4, 6), (2, 4))
    game.board[5][3] = None
    assert not game.pseudo((4, 6), (2, 4))
    game.board[7][5] = "rP"
    assert not game.pseudo((4, 6), (6, 8))


def test_cannon_screen():
    game = empty()
    game.board[7][1], game.board[2][1] = "rC", "bR"
    assert not game.pseudo((1, 7), (1, 2))
    game.board[5][1] = "rP"
    assert game.pseudo((1, 7), (1, 2))
    game.board[4][1] = "rP"
    assert not game.pseudo((1, 7), (1, 2))


def test_cannot_expose_flying_generals_or_check():
    game = empty()
    game.board[0][3], game.board[0][4] = None, "bK"
    game.board[5][4] = "rR"
    assert not game.legal((4, 5), (5, 5))
    game.board[0][4], game.board[0][3] = None, "bK"
    game.board[5][4] = "bR"
    assert game.checked("r")
    assert not game.legal((4, 9), (4, 8))


def test_crossed_pawn():
    game = empty()
    game.board[4][0] = "rP"
    assert game.legal((0, 4), (1, 4))
    assert not game.legal((0, 4), (0, 5))


def test_stalemate_is_loss():
    game = empty()
    game.board[1][0] = "rR"
    game.board[2][4] = "rR"
    game.board[3][1] = "rR"
    game.move((1, 3), (1, 2))
    assert game.winner == "r"


def test_financial_reconciliation():
    data = finance.dataset()
    assert data["metrics"]["Revenue"]["2025"] == 281724
    assert data["metrics"]["Operating income"]["2025"] == 128528
    assert data["metrics"]["Net income"]["2025"] == 101832
    assert finance.view()["margin_pct"] == pytest.approx(45.622, abs=.001)
    cloud = finance.view(segment="Intelligent Cloud")
    assert cloud["revenue"] == 106265
    assert finance.view("2024")["yoy_pct"] is None


def test_single_agent_real_trace():
    result = json.loads((ROOT / "Lab3/Code/output/analysis.json").read_text())
    assert result["trace"]["model"] == "gpt-6-luna"
    assert result["trace"]["mode"] == "autopilot"
    assert all(e["agent_id"] is None for e in result["trace"]["events"])
    assert len(result["findings"]) == 3


def test_three_real_agents_and_grounded_tasks():
    plan = json.loads((ROOT / "Lab4/Code/output/plan.json").read_text())
    demo = json.loads((ROOT / "Lab4/Code/data/demo.json").read_text())
    sources = {m["id"]: m for m in demo["emails"]}
    assert len({t["session_id"] for t in plan["traces"]}) == 3
    assert all(t["model"] == "gpt-6-luna" for t in plan["traces"])
    assert len(plan["tasks"]) == 3
    allocated = []
    for task in plan["tasks"]:
        assert task["evidence"] in sources[task["source_id"]]["body"]
        a, b = map(schedule.aware, (task["scheduled_start"], task["scheduled_end"]))
        assert a >= schedule.aware(plan["reference_now"])
        assert not any(a < schedule.aware(e["end"]) and b > schedule.aware(e["start"]) for e in plan["events"])
        assert not any(a < y and b > x for x, y in allocated)
        allocated.append((a, b))


def test_week_boundary_and_past_deadline():
    now, monday, end = schedule.week_bounds("2026-10-25T23:59:00+08:00", "Asia/Shanghai")
    assert monday.day == 19 and end.day == 26
    assert schedule.free_slots([], now.isoformat(), "Asia/Shanghai") == []
    result = schedule.allocate([{"deadline": "2026-10-18T17:00:00+08:00",
        "priority": 1, "estimate_minutes": 30}], [], "2026-10-19T09:00:00+08:00", "Asia/Shanghai")
    assert result[0]["scheduled_start"] is None


def test_overlapping_and_all_day_events():
    events = [{"start": "2026-10-19T00:00:00+08:00", "end": "2026-10-20T00:00:00+08:00"},
              {"start": "2026-10-19T10:00:00+08:00", "end": "2026-10-19T11:00:00+08:00"}]
    slots = schedule.free_slots(events, "2026-10-19T09:00:00+08:00", "Asia/Shanghai")
    assert slots[0][0].day == 20


def test_dst_week_uses_local_monday():
    _, start, end = schedule.week_bounds("2026-11-01T12:00:00-05:00", "America/New_York")
    assert start.isoformat() == "2026-10-26T00:00:00-04:00"
    assert end.isoformat() == "2026-11-02T00:00:00-05:00"


def test_persistent_completion_and_invalid_input(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"tasks":[{"id":"a","done":false}]}')
    store = store_module.Store(path)
    store.complete("a", True)
    assert store_module.Store(path).read()["tasks"][0]["done"] is True
    with pytest.raises(ValueError):
        store.complete("a", "yes")
    with pytest.raises(ValueError):
        store.complete("missing", True)


canvas_installer = load("install_canvas", "Lab4/Code/install_canvas.py")
SESSION_A = "11111111-1111-4111-8111-111111111111"
SESSION_B = "22222222-2222-4222-8222-222222222222"


def fake_session(home, uuid, cwd, pid, mtime):
    import os
    session = home / "session-state" / uuid
    session.mkdir(parents=True)
    (session / "workspace.yaml").write_text(f"id: {uuid}\ncwd: {cwd}\nclient_name: github/autopilot\n")
    (session / "events.jsonl").write_text("{}\n")
    (session / f"inuse.{pid}.lock").write_text("")
    os.utime(session / "events.jsonl", (mtime, mtime))
    os.utime(session / "workspace.yaml", (mtime, mtime))
    return session


def test_canvas_finds_the_live_session_in_course_root(tmp_path):
    course, other = tmp_path / "course", tmp_path / "other"
    course.mkdir(), other.mkdir()
    home = tmp_path / "copilot"
    fake_session(home, SESSION_A, course, 101, 1_000)
    fake_session(home, SESSION_B, other, 102, 2_000)       # another folder
    fake_session(home, "33333333-3333-4333-8333-333333333333", course, 999, 3_000)  # dead pid
    alive = lambda pid: pid in (101, 102)
    assert canvas_installer.find_session(home, course, alive) == SESSION_A


def test_canvas_prefers_the_session_written_most_recently(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    home = tmp_path / "copilot"
    fake_session(home, SESSION_A, course, 101, 1_000)
    fake_session(home, SESSION_B, course, 102, 1_600)
    assert canvas_installer.find_session(home, course, lambda pid: True) == SESSION_B


def test_canvas_refuses_when_no_session_or_a_tie(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    home = tmp_path / "copilot"
    (home / "session-state").mkdir(parents=True)
    with pytest.raises(ValueError, match="没有找到"):
        canvas_installer.find_session(home, course, lambda pid: True)
    fake_session(home, SESSION_A, course, 101, 1_000)
    fake_session(home, SESSION_B, course, 102, 1_002)
    with pytest.raises(ValueError, match="多个会话"):
        canvas_installer.find_session(home, course, lambda pid: True)


def test_canvas_installs_into_session_only(tmp_path):
    home = tmp_path / "copilot"
    (home / "session-state" / SESSION_A).mkdir(parents=True)
    target = canvas_installer.install(SESSION_A, home)
    assert (target / "extension.mjs").is_file()
    assert json.loads((target / "config.json").read_text())["bridge"].endswith("bridge.py")
    with pytest.raises(FileExistsError):
        canvas_installer.install(SESSION_A, home)
