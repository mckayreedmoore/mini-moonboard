"""Pure and synthetic checks for the isolated outer-node probe."""

import math

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_geometry import (
    LocalFrame,
    local_extrema,
    washer_support_report,
)
from scripts.wood_joint_wj03_compact_outer_probe import (
    HYPOTHESES,
    _body_timber_hits,
    _bridge_fabrication_method,
    _clip_above_local_n,
    _cross_stack_hits,
    _stack,
    _stack_timber_hits,
    _world_tn,
)


def test_three_hypotheses_preserve_the_initial_bridges_and_add_named_bevel():
    full, compact, chamfered = HYPOTHESES

    assert (full.bridge_depth_mm, full.bridge_rear_y_mm, full.bevel_n_limit_mm) == (
        88.9,
        -270.95,
        137.0,
    )
    assert (
        compact.bridge_depth_mm,
        compact.bridge_rear_y_mm,
        compact.bevel_n_limit_mm,
    ) == (38.1, -220.15, 137.7)
    assert full.bridge_rear_y_mm + full.bridge_depth_mm == pytest.approx(-182.05)
    assert compact.bridge_rear_y_mm + compact.bridge_depth_mm == pytest.approx(-182.05)
    assert full.bridge_bevel_n_limit_mm is None
    assert compact.bridge_bevel_n_limit_mm is None
    assert chamfered.id == "compact_bridge_rear_bevel_4x6_spine_137_7"
    assert (
        chamfered.bridge_depth_mm,
        chamfered.bridge_rear_y_mm,
        chamfered.bevel_n_limit_mm,
        chamfered.bridge_bevel_n_limit_mm,
    ) == (38.1, -220.15, 137.7, 137.7)
    assert (chamfered.bridge_depth_mm, chamfered.bridge_rear_y_mm) == (
        compact.bridge_depth_mm,
        compact.bridge_rear_y_mm,
    )
    assert _bridge_fabrication_method(compact) == "crosscuts and through-bores"
    assert (
        _bridge_fabrication_method(chamfered)
        == "crosscuts, one rear bevel, and through-bores"
    )


def test_proposed_side_centers_are_projected_in_source_TN_axes():
    angle = math.radians(50.0)
    side_frame = LocalFrame(
        (-1219.2, -41.497331207980935, 277.0),
        (1, 0, 0),
        (0, math.cos(angle), math.sin(angle)),
        (0, -math.sin(angle), math.cos(angle)),
    )

    first = _world_tn(side_frame, 0.0, 84.5)
    second = _world_tn(side_frame, 45.0, 84.5)

    assert first.toTuple() == pytest.approx((-1219.2, -106.2280866, 331.3155530))
    assert second.toTuple() == pytest.approx((-1219.2, -77.3026442, 365.7875530))


def test_bevel_clips_a_small_solid_to_mathematical_local_N_limit():
    frame = LocalFrame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    stock = cq.Solid.makeBox(10, 10, 10)

    finished = _clip_above_local_n(stock, frame, 6.0)
    extrema = local_extrema(finished, frame)

    assert finished.Volume() == pytest.approx(600.0)
    assert extrema.n_mm == pytest.approx((0.0, 6.0), abs=1e-6)


def test_compact_bridge_rear_bevel_caps_corner_and_preserves_washer_seat():
    angle = math.radians(50.0)
    datum = LocalFrame(
        (0.0, -36.0, 238.9),
        (1, 0, 0),
        (0, math.cos(angle), math.sin(angle)),
        (0, -math.sin(angle), math.cos(angle)),
    )
    raw = cq.Solid.makeBox(383.2, 38.1, 88.9, cq.Vector(0, -220.15, 150.0))
    finished = _clip_above_local_n(raw, datum, 137.7)
    removed = raw.cut(finished).clean()
    extrema = local_extrema(finished, datum)

    assert extrema.n_mm[1] == pytest.approx(137.7, abs=1e-6)
    assert removed.Volume() == pytest.approx(4411.456, abs=0.1)
    assert finished.BoundingBox().ymax == pytest.approx(-182.05, abs=1e-6)

    stack = _stack(
        "synthetic_compact_bridge_link",
        (50.0, -220.15, 194.45),
        (0, 1, 0),
        (("bridge", 38.1), ("under", 88.9)),
        152.4,
    )
    support = washer_support_report(stack.head_seat, finished, stack.hardware)
    assert support.full_seat
    assert support.unsupported_area_mm2 == pytest.approx(0.0, abs=1e-6)


def test_collision_screens_include_other_timber_and_only_skip_same_stack_pairs():
    body = cq.Solid.makeBox(10, 10, 10)
    touching = cq.Solid.makeBox(10, 10, 10, cq.Vector(10, 0, 0))
    overlap = cq.Solid.makeBox(10, 10, 10, cq.Vector(9, 0, 0))

    assert _body_timber_hits(
        {"candidate": body}, {"candidate": body, "face_contact": touching}
    ) == []
    body_hits = _body_timber_hits(
        {"candidate": body}, {"candidate": body, "other_timber": overlap}
    )
    assert [hit["unintended_timber_id"] for hit in body_hits] == ["other_timber"]

    stack_hits = _stack_timber_hits(
        {"left": {"bolt_a": {"shaft": body}}}, {"timber": overlap}
    )
    assert [hit["unintended_timber_id"] for hit in stack_hits] == ["timber"]

    cross_hits = _cross_stack_hits(
        {
            "left": {
                "bolt_a": {"head": body, "shaft": body},
                "bolt_b": {"head": body},
            }
        }
    )
    assert len(cross_hits) == 2
    assert all("bolt_a/" in hit["first"] for hit in cross_hits)
    assert all(hit["second"] == "bolt_b/head" for hit in cross_hits)
