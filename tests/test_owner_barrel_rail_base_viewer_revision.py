"""Viewer-only trial poses preserve the historical producer defaults."""

import pytest

from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_outer_top_layout as outer
from scripts import owner_barrel_rail_layout as rail


@pytest.fixture(scope="module")
def wood():
    return center._wood()[1]


def test_right_center_rail_viewer_trial_moves_only_front_rows(wood):
    source = rail.build_layout(wood)
    revised = rail.build_revised_layout(wood)
    targets = (
        "clip_horizontal_lower_right_1",
        "clip_horizontal_upper_right_1",
    )
    assert set(revised["stations"]) == set(source["stations"])
    for station in targets:
        original = source["stations"][station]
        trial = revised["stations"][station]
        old_bolts = list(original["bolts"].values())
        new_bolts = list(trial["bolts"].values())
        assert new_bolts[0].start.y != pytest.approx(old_bolts[0].start.y)
        assert new_bolts[1].start.y == pytest.approx(old_bolts[1].start.y)
        assert trial["disposition"] != "APPROVED"
    unaffected = "clip_horizontal_lower_left_1"
    assert (
        next(iter(revised["stations"][unaffected]["bolts"].values())).start.toTuple()
        == next(iter(source["stations"][unaffected]["bolts"].values())).start.toTuple()
    )
    assert revised["diagnostics"]["viewer_trial_front_n_mm"] == 50.0


def test_outer_base_viewer_trial_moves_only_two_axes_inward(wood):
    source = outer.build_layout(wood)
    revised = outer.build_revised_layout(wood)
    assert set(revised["stations"]) == set(source["stations"])
    for side, sign in (("left", 1), ("right", -1)):
        station = f"clip_angle_base_{side}"
        old_bolts = list(source["stations"][station]["bolts"].values())
        new_bolts = list(revised["stations"][station]["bolts"].values())
        assert all(
            new.start.x - old.start.x == pytest.approx(sign * 10.0)
            for old, new in zip(old_bolts, new_bolts, strict=True)
        )
        assert revised["stations"][station]["disposition"] == "REVISE"
    unchanged = "clip_timber_header_outer_left"
    assert (
        next(iter(revised["stations"][unchanged]["bolts"].values())).start.toTuple()
        == next(iter(source["stations"][unchanged]["bolts"].values())).start.toTuple()
    )
    assert revised["diagnostics"]["viewer_trial_outer_base_inward_mm"] == 10.0
