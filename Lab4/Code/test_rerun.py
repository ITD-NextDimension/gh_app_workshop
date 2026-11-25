# From the repository root, with Lab4/Code/app.py serving on 127.0.0.1:8014:
# PYTHONPATH=Lab4/Code python3 Lab4/Code/test_rerun.py
import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from schedule import allocate, aware, week_bounds
from store import Store

ROOT = Path('Lab4/Code')
SOURCE = json.loads((ROOT / 'data/demo.json').read_text())
PLAN_PATH = ROOT / 'output/plan.json'
BASE = 'http://127.0.0.1:8014'


def fetch_plan():
    with urlopen(BASE + '/api/plan', timeout=5) as response:
        return json.load(response)


def post_done(task_id, done):
    body = json.dumps({'id': task_id, 'done': done}).encode()
    request = Request(BASE + '/api/complete', data=body,
                      headers={'Content-Type': 'application/json', 'X-Workshop': '1'},
                      method='POST')
    with urlopen(request, timeout=5) as response:
        return json.load(response)


class Lab4TargetedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN_PATH.read_text())
        cls.events = cls.plan['events']
        cls.tasks = cls.plan['tasks']

    def test_fixed_clock_week_is_local_monday_through_next_monday(self):
        now, start, end = week_bounds(SOURCE['reference_now'], SOURCE['timezone'])
        self.assertEqual(now.isoformat(), '2026-10-19T09:00:00+08:00')
        self.assertEqual(start.isoformat(), '2026-10-19T00:00:00+08:00')
        self.assertEqual(end.isoformat(), '2026-10-26T00:00:00+08:00')

    def test_utc_reference_converts_to_shanghai_week(self):
        now, start, end = week_bounds('2026-10-18T16:00:00+00:00', 'Asia/Shanghai')
        self.assertEqual(now.isoformat(), '2026-10-19T00:00:00+08:00')
        self.assertEqual(start.date().isoformat(), '2026-10-19')
        self.assertEqual(end.date().isoformat(), '2026-10-26')

    def test_naive_datetimes_are_rejected(self):
        with self.assertRaises(ValueError):
            aware('2026-10-19T09:00:00')

    def test_each_task_has_exact_source_evidence_and_only_explicit_deadline(self):
        emails = {mail['id']: mail for mail in SOURCE['emails']}
        self.assertEqual(len(self.tasks), 3)
        for task in self.tasks:
            self.assertIn(task['source_id'], emails)
            self.assertTrue(task['evidence'])
            self.assertIn(task['evidence'], emails[task['source_id']]['body'])
            if task['deadline']:
                self.assertIn(datetime.fromisoformat(task['deadline']).date().isoformat(),
                              emails[task['source_id']]['body'])
        no_deadline = next(task for task in self.tasks if task['source_id'] == 'mail-103')
        self.assertIsNone(no_deadline['deadline'])

    def test_scheduled_tasks_stay_in_current_week_and_work_hours(self):
        _, week_start, week_end = week_bounds(SOURCE['reference_now'], SOURCE['timezone'])
        for task in self.tasks:
            start, end = aware(task['scheduled_start']), aware(task['scheduled_end'])
            self.assertGreaterEqual(start, week_start)
            self.assertLess(end, week_end)
            self.assertGreaterEqual(start.hour, 9)
            self.assertLessEqual(end.hour + (end.minute > 0), 17)

    def test_scheduled_tasks_do_not_overlap_meetings(self):
        for task in self.tasks:
            start, end = aware(task['scheduled_start']), aware(task['scheduled_end'])
            for event in self.events:
                busy_start, busy_end = aware(event['start']), aware(event['end'])
                self.assertTrue(end <= busy_start or busy_end <= start)

    def test_scheduled_tasks_do_not_overlap_each_other(self):
        intervals = [(aware(task['scheduled_start']), aware(task['scheduled_end']))
                     for task in self.tasks]
        for index, (start, end) in enumerate(intervals):
            for other_start, other_end in intervals[index + 1:]:
                self.assertTrue(end <= other_start or other_end <= start)

    def test_expired_deadline_is_left_unscheduled(self):
        task = {'id': 'expired', 'title': 'expired', 'source_id': 'mail-expired',
                'evidence': 'expired', 'deadline': '2026-10-19T08:59:00+08:00',
                'estimate_minutes': 15, 'priority': 1, 'done': False}
        result = allocate([task], [], SOURCE['reference_now'], SOURCE['timezone'])[0]
        self.assertIsNone(result['scheduled_start'])
        self.assertIsNone(result['scheduled_end'])
        self.assertIn('过截止时间', result['scheduling_note'])

    def test_deadline_equal_to_reference_time_cannot_fit(self):
        task = {'id': 'due-now', 'title': 'due-now', 'source_id': 'mail-now',
                'evidence': 'due-now', 'deadline': SOURCE['reference_now'],
                'estimate_minutes': 1, 'priority': 1, 'done': False}
        result = allocate([task], [], SOURCE['reference_now'], SOURCE['timezone'])[0]
        self.assertIsNone(result['scheduled_start'])

    def test_invalid_calendar_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            allocate([], [{'start': '2026-10-19T10:00:00+08:00',
                           'end': '2026-10-19T09:00:00+08:00'}],
                     SOURCE['reference_now'], SOURCE['timezone'])

    def test_invalid_task_duration_is_rejected(self):
        task = {'id': 'bad', 'title': 'bad', 'source_id': 'mail-bad',
                'evidence': 'bad', 'deadline': None, 'estimate_minutes': 0,
                'priority': 1, 'done': False}
        with self.assertRaises(ValueError):
            allocate([task], [], SOURCE['reference_now'], SOURCE['timezone'])

    def test_store_completion_persists_when_reopened_and_can_be_reset(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            path.write_text(json.dumps(self.plan))
            task_id = self.tasks[0]['id']
            Store(path).complete(task_id, True)
            self.assertTrue(next(t for t in Store(path).read()['tasks']
                                 if t['id'] == task_id)['done'])
            Store(path).complete(task_id, False)
            self.assertFalse(next(t for t in Store(path).read()['tasks']
                                  if t['id'] == task_id)['done'])

    def test_store_rejects_non_boolean_completion(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            path.write_text(json.dumps(self.plan))
            with self.assertRaises(ValueError):
                Store(path).complete(self.tasks[0]['id'], 1)

    def test_store_rejects_unknown_task(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            path.write_text(json.dumps(self.plan))
            with self.assertRaises(ValueError):
                Store(path).complete('missing-task', True)

    def test_running_app_api_is_zero_of_three(self):
        plan = fetch_plan()
        self.assertEqual(len(plan['tasks']), 3)
        self.assertEqual(sum(task['done'] for task in plan['tasks']), 0)

    def test_private_route_is_404_and_unauthenticated_post_is_403(self):
        with self.assertRaises(HTTPError) as private:
            urlopen(BASE + '/private/live-input.json', timeout=5)
        self.assertEqual(private.exception.code, 404)
        request = Request(BASE + '/api/complete', data=b'{"id":"invalid","done":true}',
                          headers={'Content-Type': 'application/json'}, method='POST')
        with self.assertRaises(HTTPError) as unauthorized:
            urlopen(request, timeout=5)
        self.assertEqual(unauthorized.exception.code, 403)

    def test_authorized_api_post_persists_and_restores_zero_of_three(self):
        before = fetch_plan()
        self.assertEqual(sum(task['done'] for task in before['tasks']), 0)
        task_id = before['tasks'][0]['id']
        try:
            post_done(task_id, True)
            self.assertEqual(sum(task['done'] for task in fetch_plan()['tasks']), 1)
        finally:
            post_done(task_id, False)
        self.assertEqual(sum(task['done'] for task in fetch_plan()['tasks']), 0)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(Lab4TargetedTests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
print(json.dumps({'tests_run': result.testsRun, 'passed': passed,
                  'failed': len(result.failures) + len(result.errors),
                  'skipped': len(result.skipped)}, ensure_ascii=False))
if not result.wasSuccessful():
    raise SystemExit(1)
