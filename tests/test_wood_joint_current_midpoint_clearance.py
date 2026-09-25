"""Focused contracts for the current-revision hypothetical midpoint adapter."""

import hashlib
import json
from collections import Counter
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_current_access_screen as current_access
from scripts import wood_joint_current_midpoint_clearance as current_midpoints
from scripts import wood_joint_current_retained_access as retained_access
from scripts.wood_joint_midpoint_clearance import midpoint_sites

CURRENT_G2 = (1405.0, 199.20000000000005)


def test_current_grid_preserves_491_historical_sites_and_moves_only_four_g2_led_edges():
    historical = midpoint_sites()
    current = current_midpoints.midpoint_sites_for_current_revision({"G2": CURRENT_G2})

    assert [row["id"] for row in current] == [row["id"] for row in historical]
    assert Counter((row["family"], row["direction"]) for row in current) == {
        ("LED", "horizontal"): 120,
        ("LED", "vertical"): 121,
        ("T-nut", "horizontal"): 120,
        ("T-nut", "vertical"): 121,
        ("kicker T-nut", "horizontal"): 9,
    }

    by_id = {row["id"]: row for row in current}
    old_by_id = {row["id"]: row for row in historical}
    affected = {
        "LED:F2-G2",
        "LED:G2-H2",
        "LED:G1-G2",
        "LED:G2-G3",
    }
    assert {
        row["id"]
        for row in current
        if row["family"] == "LED" and "G2" in row["endpoints"]
    } == affected
    for site_id, row in by_id.items():
        expected_delta = 2.5 if site_id in affected else 0.0
        assert row["x_mm"] - old_by_id[site_id]["x_mm"] == pytest.approx(expected_delta)
        assert row["s_mm"] == pytest.approx(old_by_id[site_id]["s_mm"])


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"G2": (1400.0, 199.2)},
        {"G2": (1405.0, 200.0)},
        {"G2": (1405.0, 199.2), "G3": (1400.0, 399.2)},
    ],
)
def test_current_grid_rejects_stale_or_unreviewed_led_datum_overrides(overrides):
    with pytest.raises(ValueError, match="G2 override|exactly the recorded"):
        current_midpoints.midpoint_sites_for_current_revision(overrides)


def test_live_g2_body_is_checked_in_panel_coordinates():
    basis = SimpleNamespace(
        HALF=500.0,
        point=lambda x, s, n: cq.Vector(x, s, n),
    )
    geometry = SimpleNamespace(source=SimpleNamespace(b=basis))
    light = cq.Solid.makeSphere(
        1.0, cq.Vector(CURRENT_G2[0] - basis.HALF, CURRENT_G2[1], 60.0)
    )

    assert current_midpoints._validate_current_g2_shape(
        geometry, {"light_G2": light}
    ) == pytest.approx(CURRENT_G2)

    stale = cq.Solid.makeSphere(
        1.0, cq.Vector(CURRENT_G2[0] - basis.HALF - 5.0, CURRENT_G2[1], 60.0)
    )
    with pytest.raises(ValueError, match="does not match"):
        current_midpoints._validate_current_g2_shape(geometry, {"light_G2": stale})


def test_obstacle_inventory_is_exact_and_excludes_display_only_roles():
    ordinary_roles = current_access.ORDINARY_ROLES
    retained_roles = retained_access.FRAME_ROLE_ORDER
    wood = {f"timber_{index:02d}": object() for index in range(44)}
    candidates = {
        f"candidate_{axis:02d}": {role: object() for role in ordinary_roles}
        for axis in range(92)
    }
    retained = {
        f"retained_{axis:02d}": {"roles": {role: object() for role in retained_roles}}
        for axis in range(12)
    }
    fixed = {f"panel_screw_{axis:02d}": object() for axis in range(66)}
    tnuts = {f"tnut_{index:03d}": object() for index in range(142)}
    lights = {f"light_{index:03d}": object() for index in range(132)}

    counts = current_midpoints._validate_pool_counts(
        wood, candidates, retained, fixed, tnuts, lights
    )

    assert counts["candidate_bolt_components"] == 460
    assert counts["retained_frame_bolt_components"] == 60
    assert counts["tested_obstacle_shapes"] == 904
    retained["retained_00"]["roles"]["source_occupied_axis"] = object()
    with pytest.raises(ValueError, match="five physical roles"):
        current_midpoints._validate_pool_counts(
            wood, candidates, retained, fixed, tnuts, lights
        )


def test_g2_override_comes_from_hash_verified_current_revision_bundle():
    report, report_sha256, verification_sha256 = (
        current_midpoints._load_current_revision_report()
    )

    assert report["revision_id"] == current_midpoints.CURRENT_REVISION_ID
    assert report["led_datum_overrides_mm"] == {"G2": list(CURRENT_G2)}
    assert len(report_sha256) == len(verification_sha256) == 64


def test_current_panel_axis_reconciliation_uses_revision_report_not_snapshot():
    root = current_midpoints.ROOT
    source_inventory = json.loads(
        (root / "docs/wood-joints-mvp/source-inventory.json").read_text()
    )
    frozen_snapshot_path = (
        root
        / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json"
    )
    frozen_snapshot_bytes = frozen_snapshot_path.read_bytes()
    assert hashlib.sha256(frozen_snapshot_bytes).hexdigest() == (
        "0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187"
    )
    frozen_snapshot = json.loads(frozen_snapshot_bytes)
    revision_report, revision_report_sha256, _verification_sha256 = (
        current_midpoints._load_current_revision_report()
    )
    assert revision_report_sha256 == (
        "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695"
    )
    assert "moved_panel_axes" not in frozen_snapshot
    assert len(revision_report["moved_panel_axes"]) == 8

    source_axis_ids = {
        row["axis_id"] for row in source_inventory["fixed_panel_kicker_screws"]
    }
    geometry = SimpleNamespace(
        source_inventory=source_inventory,
        fixed_axes={axis_id: object() for axis_id in source_axis_ids},
    )
    current_rows = current_midpoints._current_panel_axis_rows(geometry, revision_report)
    assert len(current_rows) == 66
    assert sum(row["current_location_status"] == "moved" for row in current_rows) == 8
    assert (
        sum(
            row["current_location_status"] == "source_station_retained"
            for row in current_rows
        )
        == 58
    )
    with pytest.raises(ValueError, match="current report lacks moved_panel_axes"):
        current_midpoints._current_panel_axis_rows(geometry, frozen_snapshot)
