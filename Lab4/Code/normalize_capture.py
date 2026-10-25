"""Normalize this verified English Outlook capture without exposing identities."""
import argparse
import json
import re
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from schedule import week_bounds

ROOT = Path(__file__).parent
DATE = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), [A-Z][a-z]+ \d{1,2}, \d{4}"
CLOCK = r"\b\d{1,2}:\d{2} [AP]M\b"


def normalize_event(label, event_id, timezone):
    dates = re.findall(DATE, label)
    clocks = re.findall(CLOCK, label)
    if not dates:
        if clocks or re.search(r"\ball.day\b", label, re.I):
            raise ValueError("Event timing found without a date; review required")
        return None
    if label.lower().startswith("canceled:") or ", Free" in label:
        return None
    zone = ZoneInfo(timezone)
    days = [datetime.strptime(d, "%A, %B %d, %Y").date() for d in dates]
    if re.search(r"\ball.day\b", label, re.I):
        start = datetime.combine(days[0], time.min, zone)
        end = datetime.combine(days[-1] + timedelta(days=1), time.min, zone)
    else:
        if len(clocks) != 2 or len(days) not in (1, 2):
            raise ValueError("Unsupported event date/time shape; review required")
        times = [datetime.strptime(c, "%I:%M %p").time() for c in clocks]
        start = datetime.combine(days[0], times[0], zone)
        end = datetime.combine(days[-1], times[1], zone)
        if end <= start:
            raise ValueError("Event end is not after start; review required")
    return {"id": event_id, "title": f"已脱敏会议 {event_id.rsplit('-', 1)[-1]}",
            "start": start.isoformat(), "end": end.isoformat()}


def normalize(folder, reference_now):
    timezone = "Asia/Shanghai"
    _, week_start, week_end = week_bounds(reference_now, timezone)
    events = []
    for filename in ("live-calendar-week.json", "live-calendar-sunday.json"):
        capture = json.loads((folder / filename).read_text())
        for item in capture["events"]:
            event = normalize_event(item["label"], f"calendar-{len(events)+1:03}", timezone)
            if event and datetime.fromisoformat(event["start"]) < week_end and datetime.fromisoformat(event["end"]) > week_start:
                events.append(event)
    mail = json.loads((folder / "selected-mail.json").read_text())
    if not re.search(r"(?:course|training)\s+by\s+20 November 2026\b", mail["body"], re.I):
        raise ValueError("Expected explicit course deadline was not found")
    received = re.search(r"\bWed 10/21/2026 1:13 AM\b", mail["pane"])
    if not received:
        raise ValueError("Expected receipt timestamp was not found")
    return {
        "data_mode": "live", "needs_review": True, "timezone": timezone,
        "reference_now": reference_now,
        "emails": [{
            "id": "mail-001", "subject": "完成必修培训（已脱敏）",
            "received": "2026-10-21T01:13:00+08:00",
            "body": "请完成必修培训。明确截止日期为 2026-11-20；本地日期截止约定为当天 23:59:59（Asia/Shanghai）。",
        }],
        "events": events,
        "normalization": {
            "scope": "One selected training reminder, not the entire inbox",
            "removed": ["identities", "addresses", "links", "meeting titles", "mail signatures"],
            "date_policy": "Date-only deadline uses local end of day; not an original time-of-day claim",
            "timezone_evidence": "Browser Asia/Shanghai and Outlook current-time label matched local capture time",
            "calendar_scope": "Monday Oct 19 through Sunday Oct 25; UI Sunday-start week plus Sunday day view",
            "excluded": "Navigation labels, previous Sunday, canceled and explicitly Free events",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, default=ROOT / "private")
    parser.add_argument("--reference-now", required=True)
    args = parser.parse_args()
    result = normalize(args.folder, args.reference_now)
    target = args.folder / "live-input.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    target.chmod(0o600)
    print(f"Normalized 1 selected email and {len(result['events'])} anonymized busy events; needs_review=true")
