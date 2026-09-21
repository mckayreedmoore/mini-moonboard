"""PB02 native adapter preserves kerf-right scope and canonical spring rows."""

import numpy as np
import pytest

from scripts.simple_center_connected_kinematics import (
    CONTACT_PARTITION,
    EDGES,
    contact_partition,
)
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_pb02_native import (
    NEW_MEMBERS,
    REMOVED_POST,
    REMOVED_STATIONS,
    RETARGETED_PANEL_CONNECTIONS,
    PB02Native,
    add_native_paths,
    native_contact_partition,
    native_row_inventory,
    screen,
)


@pytest.fixture(scope="module")
def module():
    return PB02Native()


def test_candidate_overlays_only_pb02_members_on_kerf_right_frame(module):
    raw = {part.name: part for part in module.raw.uncut_wood_parts()}
    actual = {part.name: part for part in module.uncut_wood_parts()}

    assert len(actual) == 31
    assert REMOVED_POST not in actual
    assert set(NEW_MEMBERS) <= set(actual)
    for name in set(raw) - {REMOVED_POST}:
        before, after = raw[name].shape, actual[name].shape
        assert after.Volume() == pytest.approx(before.Volume(), abs=1e-3)
        assert after.Center().toTuple() == pytest.approx(before.Center().toTuple())
        assert (
            after.BoundingBox().xmin,
            after.BoundingBox().xmax,
        ) == pytest.approx((before.BoundingBox().xmin, before.BoundingBox().xmax))
    response_parts = {part.name: part for part in module.current_response_wood_parts()}
    assert set(response_parts) == set(actual)
    for name in NEW_MEMBERS:
        assert response_parts[name].shape.Volume() == pytest.approx(
            actual[name].shape.Volume(), abs=1e-3
        )


def test_only_displaced_clips_are_removed_and_panel_axes_are_frozen(module):
    connections = module.connections()
    panels = {row.name: row for row in module.panel_connections()}
    baseline = {row.name: row for row in module.raw.panel_connections()}
    stations = {row[0] for row in module.stations()}

    assert len(stations) == 22
    assert not (stations & REMOVED_STATIONS)
    assert sum(row.name.startswith("clip_") for row in connections) == 132
    assert sum(row.kind == "bolt" for row in connections) == 12
    assert len(panels) == len(baseline) == 66
    for name, before in baseline.items():
        after = panels[name]
        assert type(after) is type(before)
        assert after.name == before.name
        assert after.start == before.start
        assert after.direction == before.direction
        assert after.length == before.length
        assert after.diameter == before.diameter
        if name in RETARGETED_PANEL_CONNECTIONS:
            assert after.members == ("kicker_right", "backer")
        else:
            assert after.members == before.members


def test_native_rows_match_shared_connected_kinematics():
    rows = native_row_inventory()
    assert len(rows) == 30 + CONTACT_PARTITION["contact_row_count"]
    assert {row["edge"] for row in rows} == set(EDGES)
    assert sum(row["kind"] == "bolt_shear" for row in rows) == 20
    assert sum(row["kind"] == "bolt_tension" for row in rows) == 10
    assert (
        sum(row["kind"] == "contact_compression" for row in rows)
        == (CONTACT_PARTITION["contact_row_count"])
    )
    for row in rows:
        assert {"first_part", "second_part", "point_mm", "direction"} <= set(row)


def test_native_paths_reject_rows_from_a_different_contact_partition():
    _, refined_partition = contact_partition(4)

    with pytest.raises(ValueError, match="rows do not match partition"):
        add_native_paths(
            object(),
            {},
            bolt_axial_n_per_mm=700.0,
            bolt_lateral_n_per_mm=1200.0,
            face_normal_total_n_per_mm=2400.0,
            row_inventory=native_row_inventory(),
            contact_partition_data=refined_partition,
        )


def test_native_refinement_coalescing_preserves_exact_area_and_first_moments():
    cells, partition = native_contact_partition(4)

    for edge, rows in cells.items():
        interface = partition["interfaces"][edge]
        assert sum(row["tributary_area_mm2"] for row in rows) == pytest.approx(
            interface["net_overlap_area_mm2"], abs=1e-5
        )
        first_moment = sum(
            (
                row["tributary_area_mm2"] * np.asarray(row["point_mm"])
                for row in rows
            ),
            np.zeros(3),
        )
        np.testing.assert_allclose(
            first_moment,
            interface["net_first_moment_mm3"],
            atol=1e-4,
        )

    merged = {
        edge: next(
            row for row in rows if row.get("coalesced_for_native_attachment")
        )
        for edge, rows in cells.items()
        if any(row.get("coalesced_for_native_attachment") for row in rows)
    }
    assert set(merged) == {
        "principal_block_principal",
        "principal_upright_block",
    }
    assert all(
        row["source_cell_ids"]
        == ["r1c1p1", "r1c2p1", "r2c1p1", "r2c2p1"]
        for row in merged.values()
    )
    assert merged["principal_block_principal"]["point_mm"] == pytest.approx(
        (50.95, -148.275, 293.75)
    )
    assert merged["principal_upright_block"]["point_mm"] == pytest.approx(
        (89.05, -160.121899, 309.296088), abs=1e-6
    )


def test_eight_by_eight_partition_refines_perforated_cells_and_remains_finite():
    cells, partition = native_contact_partition(8)

    assert partition["contact_row_count"] == 413
    assert sum(
        row["native_attachment_coalesced_count"]
        for row in partition["interfaces"].values()
    ) == 30
    assert all(
        cell["tributary_area_mm2"] > 0
        and cell["inside_both_true_faces"]
        and cell["outside_all_bore_footprints"]
        for rows in cells.values()
        for cell in rows
    )


def test_screen_keeps_claim_boundary(module):
    result = screen()
    assert result["active_fingerprint"] == ACTIVE_FINGERPRINT
    assert result["moved_panel_kicker_axes"] == []
    assert set(result["changed_panel_kicker_receivers"]) == (
        RETARGETED_PANEL_CONNECTIONS
    )
    assert result["native_rows"] == {
        "bolt_shear": 20,
        "bolt_tension": 10,
        "contact_compression": CONTACT_PARTITION["contact_row_count"],
    }
    assert result["rear_cleat_floor_clearance_mm"] == 5.0
    assert result["developmental_only"] is True
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
