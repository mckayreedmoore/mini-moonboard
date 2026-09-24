import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wood_joint_wj04_early_mechanics import (
    CONTACT_EDGE_BAND_WIDTH_MM,
    CONTACT_EDGE_RESULTANT_INSET_MM,
    INVENTORY_PATH,
    PROBE_PATH,
    _add,
    _candidate_contact_group,
    _candidate_material_axes,
    _candidate_member_fastener_placement,
    _complete_joint_capacity_status,
    _contact_supported_group_wrench,
    _dot,
    _read,
    _require_point_inside_contact_rectangle,
    _scale,
    _sub,
)


def _contact_group(negative_edge_mm=40.0, positive_edge_mm=50.0):
    return {
        "points_global_xyz_mm": ((-12.7, 0.0, 0.0), (12.7, 0.0, 0.0)),
        "centroid_global_xyz_mm": (0.0, 0.0, 0.0),
        "row_axis_global_xyz": (1.0, 0.0, 0.0),
        "bolt_axis_global_xyz": (0.0, 1.0, 0.0),
        "face_normal_global_xyz": (0.0, 1.0, 0.0),
        "spacing_mm": 25.4,
        "contact_face_geometry": {
            "group_centroid_projected_to_contact_face_global_xyz_mm": (0.0, 0.0, 0.0),
            "face_center_global_xyz_mm": (0.0, 0.0, 0.0),
            "edge_axis_global_xyz": (0.0, 0.0, 1.0),
            "row_axis_global_xyz": (1.0, 0.0, 0.0),
            "face_normal_global_xyz": (0.0, 1.0, 0.0),
            "edge_axis_coordinate_bounds_mm": (-negative_edge_mm, positive_edge_mm),
            "row_axis_coordinate_bounds_mm": (-50.0, 50.0),
            "edge_distances_from_bolt_row_centroid_mm": {
                "negative": negative_edge_mm,
                "positive": positive_edge_mm,
            },
            "row_span_mm": 100.0,
        },
    }


@pytest.mark.parametrize(
    ("row_moment_nmm", "expected_edge", "expected_q_mm"),
    ((1000.0, "positive", 45.0), (-1000.0, "negative", -35.0)),
)
def test_wj04_finite_edge_band_couple_closes_signed_moment_in_face(
    row_moment_nmm, expected_edge, expected_q_mm,
):
    group = _contact_group()
    result = _contact_supported_group_wrench(
        (0.0, 0.0, 0.0), (row_moment_nmm, 0.0, 0.0), group,
    )

    witness = result["row_axis_moment_path"]
    couple = next(
        item for item in result["contact_compression_resultants"]
        if item["source"] == "row_axis_moment_face_compression_couple"
    )
    q = couple["point_global_xyz_mm"][2]
    face = group["contact_face_geometry"]
    q_low, q_high = face["edge_axis_coordinate_bounds_mm"]
    row_low, row_high = face["row_axis_coordinate_bounds_mm"]
    edge_coordinate = q_high if expected_edge == "positive" else q_low
    inset = edge_coordinate - q if expected_edge == "positive" else q - edge_coordinate

    assert witness["contact_edge_side"] == expected_edge
    assert witness["edge_band_width_mm"] == CONTACT_EDGE_BAND_WIDTH_MM == 10.0
    assert witness["resultant_inset_from_edge_mm"] == CONTACT_EDGE_RESULTANT_INSET_MM == 5.0
    assert witness["actual_face_edge_distance_mm"] == pytest.approx(
        face["edge_distances_from_bolt_row_centroid_mm"][expected_edge]
    )
    assert witness["available_edge_lever_arm_mm"] == pytest.approx(
        witness["actual_face_edge_distance_mm"] - CONTACT_EDGE_RESULTANT_INSET_MM
    )
    assert q == pytest.approx(expected_q_mm)
    assert inset == pytest.approx(CONTACT_EDGE_RESULTANT_INSET_MM)
    assert couple["contact_band_edge_axis_coordinate_bounds_mm"] == pytest.approx(
        (q_high - 10.0, q_high) if expected_edge == "positive" else (q_low, q_low + 10.0)
    )
    assert row_low <= couple["point_global_xyz_mm"][0] <= row_high
    assert q_low <= q <= q_high
    assert couple["finite_contact_resultant_lies_in_face"]
    assert couple["contact_band_fits_actual_face"]
    assert couple["contact_band_area_mm2"] == pytest.approx(1000.0)

    # The finite-area resultant has a shorter lever and therefore greater force
    # than the zero-area edge-resultant upper-bound baseline.
    assert couple["finite_band_couple_force_n"] > couple["zero_area_edge_resultant_force_n"]
    assert couple["finite_band_couple_force_n"] == pytest.approx(
        abs(row_moment_nmm) / witness["available_edge_lever_arm_mm"]
    )
    assert couple["finite_band_force_increase_ratio"] > 1.0
    assert result["full_wrench_balanced_by_bolts_and_contact"]
    assert result["force_residual_norm_n"] < 1e-8
    assert result["moment_residual_norm_nmm"] < 1e-8
    assert result["capacity_or_contact_pressure_calculated"] is False


def test_wj04_finite_edge_band_fails_closed_when_selected_face_edge_is_too_short():
    group = _contact_group(negative_edge_mm=9.999, positive_edge_mm=50.0)

    with pytest.raises(ValueError, match="10 mm contact band does not fit selected negative face edge"):
        _contact_supported_group_wrench(
            (0.0, 0.0, 0.0), (-1000.0, 0.0, 0.0), group,
        )


def test_wj04_rail_contact_face_rejects_bolt_row_centroid_beyond_face_bound():
    inventory = _read(INVENTORY_PATH)
    probe = _read(PROBE_PATH)
    group = _candidate_contact_group(WJ04_TRIAL, inventory, "rail_to_cleat", probe)
    face = group["contact_face_geometry"]
    row_shift = _scale(60.0, group["row_axis_global_xyz"])
    shifted_center = _add(group["centroid_global_xyz_mm"], row_shift)
    projected = _add(
        shifted_center,
        _scale(
            _dot(_sub(face["face_center_global_xyz_mm"], shifted_center),
                 group["face_normal_global_xyz"]),
            group["face_normal_global_xyz"],
        ),
    )

    with pytest.raises(
        ValueError,
        match="bolt-row centroid projected to contact face is outside the canonical bounds contact rectangle along the bolt row",
    ):
        _require_point_inside_contact_rectangle(
            projected,
            face["face_center_global_xyz_mm"],
            group["face_normal_global_xyz"],
            group["row_axis_global_xyz"],
            face["edge_axis_global_xyz"],
            face["row_axis_coordinate_bounds_mm"],
            face["edge_axis_coordinate_bounds_mm"],
            "bolt-row centroid projected to contact face",
        )


def test_wj04_contact_area_fails_closed_on_unbound_probe():
    inventory = _read(INVENTORY_PATH)
    probe = _read(PROBE_PATH)
    probe["trial_config_sha256"] = "stale-config-hash"

    with pytest.raises(ValueError, match="Contact-area probe does not match canonical"):
        _candidate_contact_group(WJ04_TRIAL, inventory, "rail_to_cleat", probe)


def test_wj04_candidate_groups_use_canonical_axes_positions_and_finite_faces():
    inventory = _read(INVENTORY_PATH)
    probe = _read(PROBE_PATH)
    rail = _candidate_contact_group(WJ04_TRIAL, inventory, "rail_to_cleat", probe)
    principal = _candidate_contact_group(WJ04_TRIAL, inventory, "principal_to_cleat", probe)

    assert rail["stack_ids"] == ("rail_1", "rail_2")
    assert rail["stack_points_global_xyz_mm"] == tuple(
        WJ04_TRIAL.axis_point_global(stack.stack_id)
        for stack in WJ04_TRIAL.stacks
        if stack.interface_id == "rail_to_cleat"
    )
    assert rail["stack_nominal_bolt_lengths_mm"] == (95.25, 95.25)
    assert rail["stack_hardware_candidates"][0]["sku"] == "25C375HCS5Z"
    assert rail["stack_layers_head_to_nut"][0] == (
        {"member_id": "base_rail_service_lower_right", "thickness_mm": 38.1},
        {"member_id": "wj04_cleat", "thickness_mm": 38.1},
    )
    assert rail["bolt_axis_global_xyz"] == pytest.approx(WJ04_TRIAL.frame.t_global)
    rail_face = rail["contact_face_geometry"]
    assert rail_face["finite_probe_contact_area_mm2"] == pytest.approx(
        probe["contact_area_mm2"]["rail_to_cleat"]
    )
    assert rail_face["finite_probe_contact_area_mm2"] == pytest.approx(11401.398713)
    assert rail_face["canonical_bounds_rectangle_area_mm2"] == pytest.approx(95.25 * 119.7)
    assert rail_face["finite_probe_minus_rectangle_area_mm2"] == pytest.approx(
        rail_face["finite_probe_contact_area_mm2"]
        - rail_face["canonical_bounds_rectangle_area_mm2"]
    )
    assert rail_face["finite_probe_area_measurement"]["method_id"] == (
        "thin_inward_intersection_volume_divided_by_probe_depth"
    )
    assert rail_face["finite_probe_area_measurement"]["probe_depth_mm"] == pytest.approx(0.1)
    assert rail_face["finite_probe_area_measurement"]["capacity_or_contact_pressure_calculated"] is False
    assert rail["contact_face_geometry"]["edge_distances_from_bolt_row_centroid_mm"] == pytest.approx(
        {"negative": 35.159032, "positive": 84.540968}
    )
    rail_host_placement = _candidate_member_fastener_placement(
        WJ04_TRIAL, inventory, rail, "base_rail_service_lower_right"
    )
    rail_cleat_placement = _candidate_member_fastener_placement(
        WJ04_TRIAL, inventory, rail, "wj04_cleat"
    )
    assert rail_host_placement["grain_local_axis"] == "X"
    assert rail_host_placement["stack_placement"][0]["placement_by_local_axis"]["X"][
        "distance_to_negative_boundary_mm"
    ] == pytest.approx(38.1)
    assert rail_host_placement["stack_placement"][0]["placement_by_local_axis"]["X"][
        "conditional_7d_reserve_mm"
    ]["negative"] == pytest.approx(-6.35)
    assert rail_cleat_placement["stack_placement"][0]["placement_by_local_axis"]["N"][
        "conditional_7d_reserve_mm"
    ]["negative"] == pytest.approx(-9.290968)

    assert principal["stack_ids"] == ("upright_1", "upright_2")
    assert principal["stack_nominal_bolt_lengths_mm"] == (152.4, 152.4)
    assert principal["stack_hardware_candidates"][0]["sku"] == "25C600HCS5Z"
    assert principal["stack_layers_head_to_nut"][0] == (
        {"member_id": "wj04_cleat", "thickness_mm": 95.25},
        {"member_id": "base_principal_center_right", "thickness_mm": 38.1},
    )
    assert principal["bolt_axis_global_xyz"] == pytest.approx((-1.0, 0.0, 0.0))
    assert principal["row_axis_global_xyz"] == pytest.approx(WJ04_TRIAL.frame.n_global)
    principal_face = principal["contact_face_geometry"]
    assert principal_face["finite_probe_contact_area_mm2"] == pytest.approx(
        probe["contact_area_mm2"]["principal_to_cleat"]
    )
    assert principal_face["canonical_bounds_rectangle_area_mm2"] == pytest.approx(38.1 * 119.7)
    assert principal_face["finite_probe_minus_rectangle_area_mm2"] == pytest.approx(
        principal_face["finite_probe_contact_area_mm2"]
        - principal_face["canonical_bounds_rectangle_area_mm2"]
    )
    assert principal["contact_face_geometry"]["edge_distances_from_bolt_row_centroid_mm"] == pytest.approx(
        {"negative": 19.05, "positive": 19.05}
    )
    cleat_placement = _candidate_member_fastener_placement(
        WJ04_TRIAL, inventory, principal, "wj04_cleat"
    )
    upright_2 = cleat_placement["stack_placement"][1]["placement_by_local_axis"]
    assert upright_2["T"]["distance_to_negative_boundary_mm"] == pytest.approx(19.05)
    assert upright_2["T"]["conditional_4d_reserve_mm"]["negative"] == pytest.approx(-6.35)
    assert upright_2["N"]["distance_to_positive_boundary_mm"] == pytest.approx(29.540968)
    assert upright_2["N"]["conditional_4d_reserve_mm"]["positive"] == pytest.approx(4.140968)


def test_wj04_canonical_grain_axes_and_complete_capacity_fail_closed():
    inventory = _read(INVENTORY_PATH)
    probe = _read(PROBE_PATH)
    groups = {
        "rail": _candidate_contact_group(WJ04_TRIAL, inventory, "rail_to_cleat", probe),
        "principal": _candidate_contact_group(WJ04_TRIAL, inventory, "principal_to_cleat", probe),
    }
    axes = _candidate_material_axes(WJ04_TRIAL, inventory, groups)
    capacity = _complete_joint_capacity_status(WJ04_TRIAL, groups)

    assert axes["base_rail_service_lower_right"]["grain_axis_global_xyz"] == pytest.approx((1.0, 0.0, 0.0))
    assert axes["base_principal_center_right"]["grain_axis_global_xyz"] == pytest.approx(
        WJ04_TRIAL.frame.t_global
    )
    assert axes["wj04_cleat"]["grain_axis_global_xyz"] == pytest.approx(WJ04_TRIAL.frame.n_global)
    assert groups["rail"]["material_axes"]["host"]["bolt_axis_parallel_to_grain"] is False
    assert groups["principal"]["material_axes"]["host"]["bolt_axis_parallel_to_grain"] is False

    assert capacity["complete_bounded_joint_capacity_feasible_now"] is False
    methods = {item["method_id"]: item for item in capacity["limit_state_methods"]}
    assert methods["wood_bearing_end_edge_group_net_section_splitting"]["status"] == (
        "UNRESOLVED_GEOMETRY_MATERIAL_DEMAND"
    )
    assert methods["bolt_steel_tension_shear_interaction"]["status"] == (
        "UNRESOLVED_MATERIAL_DEMAND_METHOD"
    )
    assert methods["unilateral_contact_pressure_opening"]["status"] == "GEOMETRY_WITNESS_ONLY"
    assert methods["complete_joint_capacity_envelope"]["status"] == "UNRESOLVED"
