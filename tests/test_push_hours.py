"""Agent publication windows use Denver time, independent of machine timezone."""
import runpy
from datetime import datetime

import pytest

blocked = runpy.run_path(".githooks/pre-push")["blocked"]


@pytest.mark.parametrize("timestamp,expected", [
    ("2026-09-07T07:29:59-06:00", False),
    ("2026-09-07T07:30:00-06:00", True),
    ("2026-09-08T12:00:00-06:00", True),
    ("2026-09-09T12:00:00-06:00", True),
    ("2026-09-10T17:59:59-06:00", True),
    ("2026-09-10T18:00:00-06:00", False),
    ("2026-09-11T12:00:00-06:00", False),
    ("2026-09-12T12:00:00-06:00", False),
    ("2026-09-13T12:00:00-06:00", False),
    ("2026-09-08T13:30:00+00:00", True),
    ("2026-12-07T14:29:59+00:00", False),
    ("2026-12-07T14:30:00+00:00", True),
    ("2026-12-08T01:00:00+00:00", False),
])
def test_quiet_hours(timestamp, expected):
    assert blocked(datetime.fromisoformat(timestamp)) is expected
