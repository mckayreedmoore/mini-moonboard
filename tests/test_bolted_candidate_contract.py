"""LB-06 scaffold and baseline-preservation contract."""

import pytest

from mini_moonboard import compact_floor_flush_bolted_frame as candidate
from mini_moonboard.bolted_layouts import FAMILY_NAMES, registered_layouts


def test_candidate_identity_and_scope_are_explicit() -> None:
    metadata = candidate.candidate_metadata()
    assert candidate.KEY == "compact-floor-flush-bolted-development"
    assert metadata["baseline_candidate"] == "compact-floor-flush-development"
    assert metadata["selected_as_repository_default"] is False
    assert metadata["panel_policy"] == "retain_existing_66_hillman_screws"
    assert metadata["future_panel_inserts"] == "deferred_not_a_dependency"
    assert metadata["owner_connector_scope"] == "factory_connectors_only"
    assert metadata["custom_cut_drilled_steel_allowed"] is False
    assert metadata["direct_wood_lap_joint_allowed"] is False
    assert metadata["structural_connector_schedule_status"] == (
        "factory_connector_unselected"
    )
    assert metadata["hidden_frame_changes_allowed"] is True
    assert metadata["panel_screw_axis_policy"] == "preserve_all_66_coordinates"
    assert metadata["climbing_surface_policy"] == "preserve_panel_outlines_and_angle"


def test_scaffold_preserves_raw_inventory_and_panel_connections() -> None:
    parts = candidate.uncut_wood_parts()
    assert len(parts) == 26
    assert sum(part.name.startswith(("main_", "kicker_")) for part in parts) == 6
    assert len(parts) - 6 == 20
    assert len(candidate.panel_connections()) == 66
    assert sum(connection.kind == "bolt" for connection in candidate.connections()) == 12
    assert sum(connection.kind == "screw" for connection in candidate.connections()) == 66
    records = candidate.structural_joint_records()
    assert len(records) == 24
    assert all(record.assessment_status == "prototype" for record in records)


def test_finished_parts_are_rejected_until_all_families_exist() -> None:
    with pytest.raises(candidate.IncompleteCandidateError, match="mechanics/resistance/access"):
        candidate.parts()


def test_all_six_families_cover_exactly_24_prototype_stations() -> None:
    layouts = registered_layouts()
    assert tuple(layouts) == FAMILY_NAMES
    assert [len(layouts[name]) for name in FAMILY_NAMES] == [4, 4, 8, 4, 2, 2]
    assert sum(len(layouts[name]) for name in FAMILY_NAMES) == 24
    assert len(candidate.fastener_stack_records()) == 48
    assert len(candidate.assembly_interface_records()) == 24


def test_reported_retrofit_bore_is_explicit_and_does_not_release_finished_geometry() -> None:
    reported = candidate.ReportedExistingHole(
        member_name="base_principal_center_left",
        entry_xyz_mm=(-70.0, -124.9, 320.0),
        direction_xyz=(1.0, 0.0, 0.0),
        diameter_mm=6.35,
        depth_mm=38.1,
        source="synthetic test fixture only",
    )
    original = candidate.machining_records()
    with_existing = candidate.machining_records((reported,))
    assert with_existing[:-1] == original
    assert with_existing[-1]["status"] == "reported_not_geometry_verified"
    assert with_existing[-1]["member_name"] == reported.member_name
    with pytest.raises(candidate.IncompleteCandidateError):
        candidate.parts()


def test_retrofit_input_rejects_panel_receiver_and_unsourced_hole() -> None:
    with pytest.raises(ValueError, match="structural timber"):
        candidate.machining_records((candidate.ReportedExistingHole(
            "main_lower_left", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.35, 38.1,
            "owner note"),))
    with pytest.raises(ValueError, match="evidence source"):
        candidate.ReportedExistingHole(
            "base_header", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 6.35, 38.1,
            "")
