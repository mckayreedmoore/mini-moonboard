from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import host_actions as ha


def simple_frame() -> dict:
    return {
        "host": "test_host",
        "grain_axis_global_xyz": [1.0, 0.0, 0.0],
        "section_u_global_xyz": [0.0, 1.0, 0.0],
        "section_v_global_xyz": [0.0, 0.0, 1.0],
        "member_start_xyz_mm": [0.0, 0.0, 0.0],
        "member_end_xyz_mm": [10.0, 0.0, 0.0],
        "member_grain_length_mm": 10.0,
        "width_mm_from_source_model": 2.0,
        "depth_mm_from_source_model": 3.0,
        "step_path": "unused.step",
        "step_sha256": "0" * 64,
        "section_u_source_label": "test-u",
        "section_v_source_label": "test-v",
    }


def action(name: str, point: list[float], force: list[float], source_kind="physical_connection") -> dict:
    return {
        "action_id": name,
        "source_name": name,
        "source_row_ids": [name],
        "source_kind": source_kind,
        "role": "test",
        "body": "test_host",
        "other_body": "test_other" if source_kind == "physical_connection" else None,
        "point_xyz_mm": point,
        "force_xyz_n": force,
        "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
        "grain_station_mm": point[0],
        "finite_footprint_station_bounds_mm": [point[0], point[0]],
        "source_area_mm2": None,
        "contact_patch": None,
    }


def test_two_sided_cut_keeps_signed_shear_components_and_moments():
    frame = simple_frame()
    actions = [
        action("left", [1.0, 0.5, 0.25], [1.0, 3.0, 4.0]),
        action("right", [3.0, -0.3, 0.4], [-0.5, -1.0, -2.0]),
    ]
    datum = [0.0, 0.0, 0.0]
    whole = ha.wrench(actions, datum)
    whole["_datum_xyz_mm"] = datum

    cut = ha.cut_trace(actions, 2.0, frame, "approached_from_negative_station", whole)
    positive = cut["internal_cut_wrench_on_positive_side_local"]
    negative = cut["internal_cut_wrench_on_negative_side_local"]
    assert positive["force_N_Vu_Vv_n"] == {"N": 0.5, "Vu": 1.0, "Vv": 2.0}
    assert negative["force_N_Vu_Vv_n"] == {"N": -1.0, "Vu": -3.0, "Vv": -4.0}
    assert positive["transverse_uv_resultant_n_diagnostic_only"] == pytest.approx(math.sqrt(5.0))
    assert negative["transverse_uv_resultant_n_diagnostic_only"] == pytest.approx(5.0)
    assert positive["moment_T_Mu_Mv_nmm"] != {"T": 0.0, "Mu": 0.0, "Mv": 0.0}
    assert negative["moment_T_Mu_Mv_nmm"] != {"T": 0.0, "Mu": 0.0, "Mv": 0.0}
    assert cut["two_side_external_closure_at_cut"]["whole_host_residual_reproduced_at_cut"]


def test_wrench_transport_preserves_moment_about_new_datum():
    source = {
        "force_xyz_n": [0.0, 2.0, 0.0],
        "moment_about_datum_xyz_nmm": [0.0, 0.0, 0.0],
        "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
        "moment_rounding_radius_xyz_nmm": [0.0, 0.0, 0.0],
    }
    moved = ha.transport_wrench(source, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    assert moved["moment_about_datum_xyz_nmm"] == [0.0, 0.0, -2.0]


def test_action_exactly_on_cut_has_explicit_one_sided_trace_assignment():
    frame = simple_frame()
    actions = [action("on-plane", [2.0, 0.0, 0.0], [0.0, -3.0, 4.0])]
    whole = ha.wrench(actions, frame["member_start_xyz_mm"])
    whole["_datum_xyz_mm"] = frame["member_start_xyz_mm"]
    from_negative = ha.cut_trace(actions, 2.0, frame, "approached_from_negative_station", whole)
    from_positive = ha.cut_trace(actions, 2.0, frame, "approached_from_positive_station", whole)
    assert from_negative["source_actions_on_positive_station_side"] == ["on-plane"]
    assert from_negative["source_actions_on_negative_station_side"] == []
    assert from_negative["on_plane_action_assignment"] == "positive-side external set"
    assert from_positive["source_actions_on_positive_station_side"] == []
    assert from_positive["source_actions_on_negative_station_side"] == ["on-plane"]
    assert from_positive["on_plane_action_assignment"] == "negative-side external set"


def test_global_plus_n_projection_keeps_host_specific_local_v_sign():
    rail = {
        **simple_frame(),
        "host": "base_rail_top",
        "grain_axis_global_xyz": [1.0, 0.0, 0.0],
        "section_u_global_xyz": [0.0, 0.6427876099290708, 0.7660444429154699],
        "section_v_global_xyz": [0.0, -0.76604444291547, 0.6427876099290709],
    }
    side = {
        **simple_frame(),
        "host": "base_side_left",
        "grain_axis_global_xyz": [0.0, 0.6427876099290708, 0.7660444429154699],
        "section_u_global_xyz": [1.0, 0.0, 0.0],
        "section_v_global_xyz": [0.0, 0.76604444291547, -0.6427876099290709],
    }
    source = {
        "force_xyz_n": rail["section_v_global_xyz"],
        "moment_about_datum_xyz_nmm": [0.0, 0.0, 0.0],
        "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
        "moment_rounding_radius_xyz_nmm": [0.0, 0.0, 0.0],
    }
    rail_local = ha.local_wrench(source, rail)
    side_local = ha.local_wrench({**source, "force_xyz_n": side["section_v_global_xyz"]}, side)
    assert rail_local["force_N_Vu_Vv_n"]["Vv"] == pytest.approx(1.0)
    assert rail_local["candidate_global_plus_N_crossgrain_projection_n"] == pytest.approx(1.0)
    assert side_local["force_N_Vu_Vv_n"]["Vv"] == pytest.approx(1.0)
    assert side_local["candidate_global_plus_N_crossgrain_projection_n"] == pytest.approx(-1.0)


def test_candidate_loaded_edge_maps_global_positive_n_to_correct_section_edge():
    frame = {
        **simple_frame(),
        "host": "base_side_left",
        "section_v_global_xyz": [0.0, 0.0, -1.0],
    }
    geometry = {
        "plane_origin_xyz_mm": [0.0, 100.0, 200.0],
        "section_local_bounds_mm": {"v": [-5.0, 5.0]},
    }
    axes = [
        {"lateral_plane_xyz_mm": [1.0, 102.0, 198.0]},
        {"lateral_plane_xyz_mm": [2.0, 103.0, 202.0]},
    ]
    result = ha.candidate_loaded_edge(
        {"force_xyz_n": [0.0, 0.0, 10.0], "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0]},
        frame,
        geometry,
        axes,
        "v",
        -1.0,
    )
    assert result["signed_group_force_component_on_host_n"] == 10.0
    assert result["candidate_boundary_name"] == "v_minimum"
    assert result["target_fastener_local_coordinates_mm"] == [2.0, -2.0]
    assert result["candidate_edge_to_farthest_fastener_distance_mm"] == 7.0


def test_bracket_uses_entire_finite_patch_not_just_its_point_station():
    frame = simple_frame()
    rows = [
        {"grain_station_mm": 5.0, "finite_footprint_station_bounds_mm": [5.0, 5.0]},
        {"grain_station_mm": 4.0, "finite_footprint_station_bounds_mm": [0.5, 9.5]},
    ]
    result = ha.bracket_plan(frame, rows)
    assert result["target_finite_group_station_bounds_mm"] == [0.5, 9.5]
    assert result["cut_before_group_station_mm"] == 0.0
    assert result["cut_after_group_station_mm"] == 10.0
    assert result["target_point_actions_all_between_cuts"]
    assert result["target_finite_contact_footprints_all_between_or_touching_cuts"]

    rows[-1]["finite_footprint_station_bounds_mm"] = [-0.1, 9.5]
    with pytest.raises(ha.SourceRefusal, match="extends beyond"):
        ha.bracket_plan(frame, rows)


def test_group_jump_preserves_target_competing_and_body_load_identities():
    frame = simple_frame()
    actions = [
        action("target-bolt", [1.5, 0.0, 0.0], [0.0, 3.0, 0.0]),
        action("neighbor-contact", [2.0, 0.0, 0.0], [0.0, -1.0, 2.0]),
        action("weight-node-4", [2.5, 0.0, 0.0], [1.0, 0.0, -2.0], "discrete_body_or_gravity_load"),
    ]
    external = ha.wrench(actions, frame["member_start_xyz_mm"])
    external["_datum_xyz_mm"] = frame["member_start_xyz_mm"]
    low = ha.cut_trace(actions, 1.0, frame, "approached_from_negative_station", external)
    high = ha.cut_trace(actions, 3.0, frame, "approached_from_positive_station", external)
    target_rows = [actions[0]]
    bracket = {"cut_before_group_station_mm": 1.0, "cut_after_group_station_mm": 3.0}

    result = ha.group_jump(actions, target_rows, bracket, frame, low, high)
    ownership = result["interval_source_ownership"]
    assert ownership["target_group_source_names"] == ["target-bolt"]
    assert ownership["competing_connection_source_names"] == ["neighbor-contact"]
    assert ownership["discrete_body_or_gravity_load_node_names"] == ["weight-node-4"]
    assert result["positive_side_internal_wrench_jump_at_common_datum"]["matches_target_plus_competing_sources_and_body_loads"]


def test_discrete_body_load_is_scaled_by_the_frozen_increment_factor():
    frame = simple_frame()
    model = {
        "contact_cell_ownership": [],
        "connection_attachment_rows": [],
        "physical_body_loads": {"test_host": {"7": [10.0, -4.0, 2.0]}},
        "nodes": {"7": [5.0, 0.0, 0.0]},
    }
    empty_geometry = {"contact_patches": []}
    ten_percent = {"load_factor": 0.1, "physical_connection_forces": {}, "exact_floor_tangent_reactions": []}
    full = {"load_factor": 1.0, "physical_connection_forces": {}, "exact_floor_tangent_reactions": []}
    actions_10, _, _ = ha.host_actions_for_state(model, ten_percent, "test_host", frame, empty_geometry)
    actions_100, _, _ = ha.host_actions_for_state(model, full, "test_host", frame, empty_geometry)
    assert actions_10[0]["force_xyz_n"] == [1.0, -0.4, 0.2]
    assert actions_10[0]["load_factor_applied"] == 0.1
    assert actions_100[0]["force_xyz_n"] == [10.0, -4.0, 2.0]


def test_contact_point_owner_and_source_patch_pair_must_match():
    frame = simple_frame()
    row = {"role": "timber_or_panel_contact", "first": "test_host", "second": "block", "point": [2.0, 0.0, 0.0]}
    ownership = {"contact_x": {"source_patch_index": 0}}
    geometry = {"contact_patches": [{"member_ids": ["test_host", "other"], "vertices_xyz_mm": [[1, 0, 0], [2, 0, 0], [2, 1, 0]], "area_mm2": 1.0}]}
    with pytest.raises(ha.SourceRefusal, match="owners differ"):
        ha.contact_patch_for_row("contact_x", row, ownership, geometry, frame)


def test_pinned_source_refuses_missing_inputs(tmp_path: Path):
    with pytest.raises(ha.SourceRefusal, match="required pinned input is missing"):
        ha.verify_pins(tmp_path)


def test_saved_step_section_query_finds_net_annulus_area(tmp_path: Path):
    cq = pytest.importorskip("cadquery")
    from cadquery import exporters

    step = tmp_path / "bored_host.step"
    block = cq.Solid.makeBox(10.0, 20.0, 30.0)
    bore = cq.Solid.makeCylinder(2.0, 10.0, cq.Vector(0.0, 10.0, 15.0), cq.Vector(1.0, 0.0, 0.0))
    exporters.export(block.cut(bore), str(step))
    frame = {
        "host": "known-answer-bored-host",
        "grain_axis_global_xyz": [1.0, 0.0, 0.0],
        "section_u_global_xyz": [0.0, 1.0, 0.0],
        "section_v_global_xyz": [0.0, 0.0, 1.0],
        "member_start_xyz_mm": [0.0, 0.0, 0.0],
        "step_path": str(step),
        "step_sha256": ha.sha256_file(step),
    }
    section = ha.query_step_section(tmp_path, frame, 5.0)
    expected = 600.0 - math.pi * 2.0**2
    assert section["section_area_mm2_from_saved_finished_step"] == pytest.approx(expected, abs=1e-5)
    assert section["distinct_planar_component_face_count"] == 1
    assert section["cut_face_wire_count"] == 2
    assert section["component_faces"][0]["area_mm2"] == pytest.approx(expected, abs=1e-5)
