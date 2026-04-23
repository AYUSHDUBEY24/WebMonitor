import csv
import tempfile
import unittest
from pathlib import Path

from monitor import CheckResult, append_results, read_last_status_by_name, state_change_messages


class MonitorTests(unittest.TestCase):
    def test_append_and_read_last_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "uptime_log.csv"
            data = [
                CheckResult("2026-01-01T00:00:00+00:00", "ServiceA", "https://a.test", 200, 200, 100, True, ""),
                CheckResult("2026-01-01T00:01:00+00:00", "ServiceA", "https://a.test", 200, 500, 120, False, "fail"),
            ]
            append_results(data, path)
            status = read_last_status_by_name(path)
            self.assertIn("ServiceA", status)
            self.assertFalse(status["ServiceA"])

            with path.open("r", newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)

    def test_state_change_messages(self) -> None:
        previous = {"A": True, "B": False}
        current = [
            CheckResult("2026-01-01T00:00:00+00:00", "A", "https://a.test", 200, 500, 88, False, "timeout"),
            CheckResult("2026-01-01T00:00:00+00:00", "B", "https://b.test", 200, 200, 44, True, ""),
        ]
        messages = state_change_messages(previous, current)
        self.assertEqual(len(messages), 2)
        self.assertTrue(any(msg.startswith("DOWN: A") for msg in messages))
        self.assertTrue(any(msg.startswith("RECOVERED: B") for msg in messages))


if __name__ == "__main__":
    unittest.main()
