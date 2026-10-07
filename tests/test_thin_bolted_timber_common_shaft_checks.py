"""Independent known answers for own-host and same-cut timber consumption."""

from __future__ import annotations

import copy

import pytest

from scripts import thin_bolted_timber_common_shaft_checks as common


@pytest.fixture
def own_wood_coupon():
    identity = {"state_id": "method-only", "case_id": "method-only", "accessory_placement": "method-only"}
    axis = {"id": "coupon-axis", "direction": [1., 0., 0.], "point": [0., 0., 0.], "diameter_mm": 12.7}
    layout = {"installed_axes": [axis]}
    receiver = {"axis_id": axis["id"], "member": "wood", "grain_axis_xyz": [0., 0., 1.],
        "finished_full_wall_intervals_from_axis_point_mm": [[0., 40.]],
        "sampled_minimum_distances_to_first_finished_boundary_mm": {
            "grain": {"negative": 80., "positive": 100.},
            "cross_grain": {"negative": 45., "positive": 65.}}}
    bearings = []
    for index, (station, force) in enumerate(((10., [0., 10., 30.]), (30., [0., -2., 20.]))):
        bearings.append({"id": f"bearing{index}", "axis_id": axis["id"], "second": "wood",
            "surface_material": "wood", "surface_interval_mm": [0., 40.], "surface_index": 0,
            "quad_index": index, "axis_station_mm": station, "weight_length_mm": 20.,
            "point_xyz_mm": [station, 0., 0.], "force_on_second_xyz_n": force,
            "force_on_first_xyz_n": [-a for a in force], "moment_on_second_at_point_xyz_nmm": [1., 0., 0.]})
    # The support datum is deliberately retained separately from the outer
    # pressure datum. This method coupon also supplies an explicit free couple.
    capture = {"id": "head-own", "axis_id": axis["id"], "second": "wood", "first": "shaft/coupon-axis",
        "point_xyz_mm": [-5., 0., 0.], "host_support_point_xyz_mm": [0., 0., 0.],
        "force_on_second_xyz_n": [5., 0., 0.], "force_on_first_xyz_n": [-5., 0., 0.],
        "moment_on_second_at_point_xyz_nmm": [0., 4., 0.], "compression_n": 5., "end": {"end": "head"}}
    saved = {**identity, "axis_id": axis["id"], "member": "wood", "surface_index": 0,
        "point_xyz_mm": [20., 0., 0.], "surface_interval_mm": [0., 40.], "grain_axis_xyz": [0., 0., 1.],
        "own_bearing_points": ["bearing0", "bearing1"], "own_end_captures": ["head-own"],
        "force_on_host_xyz_n": [5., 8., 50.], "moment_on_host_at_point_xyz_nmm": [2., 104., -120.]}
    field = {**identity, "common_shaft_bearing_actions": bearings, "shaft_end_capture_actions": [capture],
             "common_shaft_wood_bearing_actions": [saved]}
    packet = {"finished_geometry_queries": {"receiver_boundary_geometry": [receiver]}}
    return layout, packet, field


def test_own_wood_resultant_preserves_bearing_couple_and_only_own_capture(own_wood_coupon):
    layout, packet, field = own_wood_coupon
    # A different receiver's capture must not enter this wood host's wrench.
    foreign = copy.deepcopy(field["shaft_end_capture_actions"][0])
    foreign.update(id="foreign", second="other", force_on_second_xyz_n=[999., 0., 0.],
                   force_on_first_xyz_n=[-999., 0., 0.])
    field["shaft_end_capture_actions"].append(foreign)
    result = common.aggregate_wood_bearings(layout, packet, field)[0]
    assert result["force_on_wood_xyz_n"] == pytest.approx([5., 8., 50.])
    assert result["moment_on_wood_at_point_xyz_nmm"] == pytest.approx([2., 104., -120.])
    assert result["radial_bearing_resultant_xyz_n"] == pytest.approx([0., 8., 50.])
    assert result["own_capture_ids"] == ["head-own"]
    assert result["resolved_resultant"]["axial_signed_n"] == pytest.approx(5.)
    assert result["opposed_flange_or_other_wood_force_inferred"] is False


@pytest.mark.parametrize("mutation", ["force", "grain", "interval", "duplicate", "foreign_capture", "state"])
def test_wood_alias_or_geometry_tampering_fails_closed(own_wood_coupon, mutation):
    layout, packet, field = own_wood_coupon
    saved = field["common_shaft_wood_bearing_actions"][0]
    if mutation == "force":
        saved["force_on_host_xyz_n"][2] += 1.
    elif mutation == "grain":
        saved["grain_axis_xyz"] = [0., 1., 0.]
    elif mutation == "interval":
        saved["surface_interval_mm"][1] = 45.
    elif mutation == "duplicate":
        field["common_shaft_wood_bearing_actions"].append(copy.deepcopy(saved))
    elif mutation == "foreign_capture":
        saved["own_end_captures"] = ["another-capture"]
    else:
        saved["case_id"] = "another-case"
    with pytest.raises(ValueError):
        common.aggregate_wood_bearings(layout, packet, field)


def test_all_aggregate_and_nested_cut_aliases_bind_complete_state():
    identity = {"state_id": "method", "case_id": "C", "accessory_placement": "rear"}
    field = {**identity, "common_shaft_wood_bearing_actions": [dict(identity)],
        "common_shaft_steel_port_actions": [dict(identity)], "member_element_actions": [dict(identity)],
        "common_shaft_section_cut_actions": [{**identity, "cuts": [dict(identity)]}]}
    common.verify_alias_state_labels(field)
    field["common_shaft_section_cut_actions"][0]["cuts"][0]["accessory_placement"] = "front"
    with pytest.raises(ValueError, match="state/load identity"):
        common.verify_alias_state_labels(field)


def test_patch_pressure_is_a_parameter_diagnostic_without_duration_or_capacity(own_wood_coupon):
    layout, packet, field = own_wood_coupon
    wood = common.aggregate_wood_bearings(layout, packet, field)
    result = common.bearing_parameter_diagnostics(wood, layout)
    body, root = result
    p = body["same_state_radial_patch_components"][0]
    assert p["foundation_patch_average_pressure_n_mm2"] == pytest.approx((10.**2 + 30.**2)**.5 / (12.7 * 20.))
    assert root["same_state_radial_patch_components"][0]["foundation_patch_average_pressure_n_mm2"] == pytest.approx(p["foundation_patch_average_pressure_n_mm2"] / .8)
    assert p["adjusted_allowable_patch_stress_or_connection_utilization"] is None
    assert body["NDS_general_common_shaft_adjusted_resistance_n"] is None


def test_own_wood_annulus_uses_actual_capture_and_does_not_increase_Fc_perp(own_wood_coupon):
    _, packet, field = own_wood_coupon
    packet["washer_wood_interface_references"] = [{"axis_id": "coupon-axis", "role": "head_washer",
        "support_material": "wood", "ideal_full_contact_wood_annulus_reference_n": 10.}]
    result = common.own_wood_washer_references(field, packet)[0]
    assert result["own_model_capture_over_ideal_annulus_component_ratio"] == .5
    assert result["actual_host_support_point_xyz_mm"] == [0., 0., 0.]
    assert result["shaft_pressure_face_point_xyz_mm"] == [-5., 0., 0.]
    assert result["duration_factor_applied_to_Fc_perp"] == 1.
    assert result["actual_wood_pressure_distribution_or_complete_axial_capacity"] is None


def test_capture_host_support_datum_reaches_cut_replay():
    field = {"common_shaft_bearing_actions": [], "panel_screw_actions": [], "contact_actions": [],
        "floor_actions": [], "body_applied_loads": [], "shaft_end_capture_actions": [{"first": "shaft",
            "second": "wood", "point_xyz_mm": [105., 0., 0.], "host_support_point_xyz_mm": [100., 0., 0.],
            "force_on_first_xyz_n": [-10., 0., 0.], "moment_on_first_at_point_xyz_nmm": [0., 0., 0.]}]}
    actions, _ = common.member_point_inputs(field)
    assert actions["shaft"][0][0] == [105., 0., 0.]
    assert actions["wood"][0][0] == [100., 0., 0.]
    assert actions["wood"][0][1] == [10., 0., 0.]


def test_replayed_station_keeps_complete_signed_wrench_and_affine_weight():
    identity = {"state_id": "method", "case_id": "gravity-only", "accessory_placement": "none"}
    field = {**identity, "common_shaft_bearing_actions": [], "shaft_end_capture_actions": [],
        "panel_screw_actions": [], "contact_actions": [], "floor_actions": [],
        "body_applied_loads": [{"id": "self-weight/coupon", "body": "coupon", "point_xyz_mm": [60., 10., 0.],
                                "force_xyz_n": [-20., 0., 0.]}],
        "member_element_actions": [{**identity, "member": "coupon", "start_xyz_mm": [0., 0., 0.],
            "end_xyz_mm": [100., 0., 0.], "basis_grain_u_v_xyz": [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]}]}
    full = {"finished_member_sections": [{"member": "coupon", "grain_axis_xyz": [1., 0., 0.],
        "sampled_sections": [{"station_global_grain_projection_mm": 25., "finished_area_mm2": 100.},
                             {"station_global_grain_projection_mm": 75., "finished_area_mm2": 50.}]}]}
    spans = {"coupon": {key: field["member_element_actions"][0][key]
                         for key in ("start_xyz_mm", "end_xyz_mm", "basis_grain_u_v_xyz")}}
    result = common.replay_existing_member_cuts(field, full, spans)[0]
    witness = result["maximum_tension_average_area_witness"]
    assert witness["cut_grain_station_mm"] == 75.
    assert witness["force_on_lower_portion_xyz_n"] == pytest.approx([12.75, 0., 0.])
    assert witness["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx([0., 0., -127.5])
    assert witness["tension_average_area_reference"]["conditional_CD1p6_same_state_component_ratio"] is None
    assert result["independently_located_component_extrema_combined"] is False
    assert witness["complete_net_section_resistance_or_utilization"] is None


def test_member_span_guard_allows_refinement_and_rejects_changed_physical_line():
    basis = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    spans = {"coupon": {"start_xyz_mm": [0., 0., 0.], "end_xyz_mm": [100., 0., 0.], "basis_grain_u_v_xyz": basis}}
    field = {"member_element_actions": [{"member": "coupon", "start_xyz_mm": [0., 0., 0.],
        "end_xyz_mm": [40., 0., 0.], "basis_grain_u_v_xyz": basis},
        {"member": "coupon", "start_xyz_mm": [40., 0., 0.], "end_xyz_mm": [100., 0., 0.], "basis_grain_u_v_xyz": basis}]}
    assert common.verify_member_span_geometry(field, spans)["interior_refinement_allowed"] is True
    changed = copy.deepcopy(field)
    changed["member_element_actions"][1]["end_xyz_mm"][1] = 1.
    with pytest.raises(ValueError, match="centerline"):
        common.verify_member_span_geometry(changed, spans)
    changed = copy.deepcopy(field)
    changed["member_element_actions"][1]["end_xyz_mm"][0] = 99.
    with pytest.raises(ValueError, match="physical extents"):
        common.verify_member_span_geometry(changed, spans)
    changed = copy.deepcopy(field)
    changed["member_element_actions"][1]["start_xyz_mm"][0] = 30.
    with pytest.raises(ValueError, match="overlaps"):
        common.verify_member_span_geometry(changed, spans)


def test_steel_alias_comparison_rejects_mismatched_actual_wrench():
    port = {"axis_id": "axis", "angle_id": "angle", "flange": "post", "point_xyz_mm": [0., 0., 0.],
        "force_on_steel_xyz_n": [0., 0., 4.], "moment_on_steel_at_point_xyz_nmm": [0., 5., 0.]}
    field = {"common_shaft_steel_port_actions": [copy.deepcopy(port)]}
    common.verify_steel_aliases(field, [port])
    field["common_shaft_steel_port_actions"][0]["moment_on_steel_at_point_xyz_nmm"][1] = 0.
    with pytest.raises(ValueError, match="independent own-point"):
        common.verify_steel_aliases(field, [port])
