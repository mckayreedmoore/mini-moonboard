"""PB04 composes the two isolated PB03 geometry revisions."""

import cadquery as cq
import pytest

from fea.floor_flush_run import face_contacts
from scripts import simple_pb03_outer_counterbore_revision as counterbore
from scripts import simple_pb03_upper_outer_edge_revision as upper_revision
from scripts.simple_center_pb02_native import PB02Native, prepare_case
from scripts.simple_pb03_lower_center_pair import TARGET_STATIONS as CENTER_STATIONS
from scripts.simple_pb03_native import PB03Native
from scripts.simple_pb04_native import SELECTED_OFFSET_MM, SOURCE_ID, PB04Native, screen


@pytest.fixture(scope="module")
def module():
    return PB04Native()


@pytest.fixture(scope="module")
def parent():
    return PB03Native()


def _connection_signature(row):
    return (
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.members,
        row.kind,
        row.grip,
    )


def test_pb04_composes_exact_upper_offset_and_counterbores(module, parent):
    geometries = module.pb03_geometries()
    parts = {part.name: part for part in module.wood_parts()}
    viewer_parts = {part.name: part for part in module.parts()}

    assert module.KEY == SOURCE_ID
    assert len(geometries) == 8
    for station in upper_revision.upper.TARGET_STATIONS:
        rail_bolts = [
            row
            for row in geometries[station].bolts
            if row.members[0] == geometries[station].rail_name
        ]
        original = parent.pb03_geometries()[station]
        old_rail_bolts = [
            row for row in original.bolts if row.members[0] == original.rail_name
        ]
        assert [
            (new.start - old.start).dot(cq.Vector(0, *upper_revision.pb01.N))
            for new, old in zip(rail_bolts, old_rail_bolts, strict=True)
        ] == pytest.approx(
            [SELECTED_OFFSET_MM - upper_revision.CURRENT_OFFSET_MM] * 2,
            abs=1.0e-6,
        )

    for station in counterbore.TARGET_STATIONS:
        geometry = geometries[station]
        actual = parts[geometry.block_name].shape
        assert viewer_parts[geometry.block_name].shape.Volume() == pytest.approx(
            actual.Volume(), abs=1.0e-5
        )
        assert geometry.block.Volume() - actual.Volume() > 0
        assert geometry.block.BoundingBox().xlen == pytest.approx(
            actual.BoundingBox().xlen
        )
    for station in CENTER_STATIONS:
        geometry = geometries[station]
        assert parts[geometry.block_name].shape.Volume() == pytest.approx(
            geometry.block.Volume(), abs=1.0e-5
        )


def test_pb04_preserves_connection_and_fixed_axis_inventories(module, parent):
    connections = module.connections()
    pb04_bolts = {row.name: row for row in connections if row.name.startswith("pb03_")}
    parent_bolts = {
        row.name: row for row in parent.connections() if row.name.startswith("pb03_")
    }

    assert len(pb04_bolts) == len(parent_bolts) == 32
    assert len(module.legacy_proxy_stations()) == 14
    assert sum(row.name.startswith("clip_") for row in connections) == 84
    assert len(module.panel_connections()) == 66
    assert len(connections) == 194
    changed = {
        name
        for name in pb04_bolts
        if _connection_signature(pb04_bolts[name])
        != _connection_signature(parent_bolts[name])
    }
    assert changed == {
        f"pb03_upper_outer_{side}_rail_{index}"
        for side in ("left", "right")
        for index in (1, 2)
    }


def test_pb04_screen_is_source_bound_and_never_releases(module):
    result = screen(module)

    assert result["schema"] == "simple_pb04_native/v1"
    assert result["pb04_source_id"] == SOURCE_ID
    assert len(result["source_fingerprint_sha256"]) == 64
    assert result["upper_outer_rail_offset_mm"] == pytest.approx(35.709)
    assert result["counterbore_depth_mm"] == pytest.approx(36.9824)
    assert result["counterbore_diameter_mm"] == pytest.approx(25.4)
    assert result["inventory"] == {
        "pb03_stations": 8,
        "counterbored_outer_blocks": 6,
        "unchanged_lower_center_blocks": 2,
        "counterbores": 12,
        "through_bolt_axes": 32,
        "legacy_proxy_stations": 14,
        "legacy_sds_axes": 84,
        "fixed_panel_kicker_axes": 66,
        "total_connections": 194,
    }
    assert result["offset_search"] == {
        "authenticated_edge_intervals_mm": [[28.4, 51.159], [109.159, 111.3]],
        "combined_clearance_requirement_mm": 3.0,
        "passing_intervals_mm": [[28.4, 35.709]],
        "rejected_upper_interval_required_start_mm": pytest.approx(119.609),
        "selected_offset_mm": pytest.approx(35.709),
        "selection_rule": (
            "closest to 125 mm among combined geometries retaining at least "
            "3.0 mm loaded-edge and counterbore clearance"
        ),
    }
    assert result["minimum_clearances_mm"] == pytest.approx(
        {
            "loaded_edge_reserve": 10.309,
            "counterbore_to_unintended_bore": 3.0,
            "counterbore_to_preserved_stack": 3.575,
        },
        abs=1.0e-6,
    )
    assert result["cross_interaction_hits"] == {
        "counterbore_to_unintended_bore_mm3": {},
        "counterbore_to_preserved_stack_mm3": {},
    }
    assert result["combined_geometry_gates_pass"] is True
    assert result["eight_station_cad_gates_pass"] is True
    assert result["cross_family_cad_gates_pass"] is True
    assert result["decision"] == "PASS_COMBINED_GEOMETRY_ONLY"
    assert result["native_preparation_supported"] is True
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_pb04_exact_interface_points_follow_revised_axes(module):
    points = module.pb03_bolt_interface_points()
    bolts = {
        row.name: row for row in module.connections() if row.name.startswith("pb03_")
    }
    assert set(points) == set(bolts)
    for name, row in bolts.items():
        assert module.bolt_interface_point(row).toTuple() == pytest.approx(
            points[name].toTuple(), abs=1.0e-8
        )


def test_pb04_native_preparation_uses_counterbored_members(module):
    structure, metadata = prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=700.0,
        bolt_lateral_n_per_mm=1200.0,
        face_normal_total_n_per_mm=2400.0,
        module=module,
        expected_candidate=SOURCE_ID,
        member_contacts=face_contacts(PB02Native()),
        expected_legacy_station_count=14,
        post_prepare=module.validate_prepared_case,
    )

    assert metadata["pb04_preparation_validated"] is True
    assert metadata["pb04_candidate"] == SOURCE_ID
    assert metadata["solved"] is False
    assert metadata["qualified_for_design"] is False
    assert metadata["drilling_released"] is False
    assert metadata["fabrication_released"] is False
    assert set(module.block_part_names()) <= set(structure.members)
