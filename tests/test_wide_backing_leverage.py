"""Exact planar equilibrium, sign and current attachment identity."""
import json
import math

import pytest

from fea import wide_backing_leverage as model
from mini_moonboard import box_frame as b
from mini_moonboard import wide_frame as frame


@pytest.mark.parametrize("x,force", [(-791.15, 100), (809.45, 100), (0, -100), (-82.55, 1), (44.45, 1)])
def test_force_and_moment_balance(x, force):
    left, right = model.reactions(-82.55, 44.45, x, force)
    assert left+right == pytest.approx(force)
    assert left*(-82.55)+right*44.45 == pytest.approx(force*x)
    if x < -82.55 and force > 0:
        assert left > force and right < 0
    if x > 44.45 and force > 0:
        assert right > force and left < 0


@pytest.mark.parametrize("args", [(0, 0, 1, 1), (2, 1, 0, 1), (0, 1, math.nan, 1)])
def test_invalid_input_rejected(args):
    with pytest.raises(ValueError):
        model.reactions(*args)


def test_current_schedule_replays_without_equal_share_assumption():
    report = model.build()
    assert json.loads(model.OUTPUT.read_text()) == report
    assert report["support_x_mm"] == [-82.55, 44.45]
    assert report["support_s_mm"] == pytest.approx(40)
    rows = report["rows"]
    assert len({r["attachment"] for r in rows}) == 6
    assert max(r["largest_positive_retention_multiplier"] for r in rows) == pytest.approx(892/127)
    assert sorted(r["unrepresented_world_x_moment_nmm_per_n"] for r in rows) == pytest.approx(
        [-20, -20, 20.95, 20.95, 20.95, 20.95])
    connections = {c.name: c for c in frame.connections()}
    reference = connections["timber_backing_bolt_left"].start
    for row in rows:
        lever = connections[row["attachment"]].start-reference
        assert row["unrepresented_world_x_moment_nmm_per_n"] == pytest.approx(
            lever.cross(-b.normal()).x)
