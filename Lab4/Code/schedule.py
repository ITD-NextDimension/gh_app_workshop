"""Half-open intervals, local Monday week, no meetings or past-time overlap."""
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo


def aware(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("时间必须包含时区偏移。")
    return parsed


def week_bounds(reference, timezone):
    zone = ZoneInfo(timezone)
    now = aware(reference).astimezone(zone)
    monday = now.date() - timedelta(days=now.weekday())
    return now, datetime.combine(monday, time.min, zone), datetime.combine(monday + timedelta(days=7), time.min, zone)


def free_slots(events, reference, timezone):
    now, start, end = week_bounds(reference, timezone)
    zone = ZoneInfo(timezone)
    busy = []
    for event in events:
        a, b = aware(event["start"]), aware(event["end"])
        if b <= a:
            raise ValueError("日历事件结束时间必须晚于开始时间。")
        busy.append((a, b))
    slots = []
    for offset in range(5):
        day = start.date() + timedelta(days=offset)
        left = max(datetime.combine(day, time(9), zone), now)
        right = datetime.combine(day, time(17), zone)
        if left >= right:
            continue
        cursor = left
        for a, b in sorted(busy):
            if b <= cursor or a >= right:
                continue
            if a > cursor:
                slots.append((cursor, min(a, right)))
            cursor = max(cursor, b)
        if cursor < right:
            slots.append((cursor, right))
    return slots


def allocate(tasks, events, reference, timezone):
    slots = free_slots(events, reference, timezone)
    output = []
    for task in sorted(tasks, key=lambda t: (t["deadline"] is None, t["deadline"] or "", t["priority"])):
        task = dict(task)
        minutes = task["estimate_minutes"]
        if type(minutes) is not int or not 1 <= minutes <= 480:
            raise ValueError("任务时长必须是 1–480 分钟的整数。")
        deadline = aware(task["deadline"]) if task["deadline"] else None
        task["scheduled_start"] = task["scheduled_end"] = None
        for i, (a, b) in enumerate(slots):
            finish = a + timedelta(minutes=minutes)
            if finish <= b and (deadline is None or finish <= deadline):
                task["scheduled_start"], task["scheduled_end"] = a.isoformat(), finish.isoformat()
                slots[i] = (finish, b)
                break
        task["scheduling_note"] = "建议时段，未写入 Outlook" if task["scheduled_start"] else "本周剩余工作时间不足或已过截止时间，请人工安排。"
        output.append(task)
    return output
