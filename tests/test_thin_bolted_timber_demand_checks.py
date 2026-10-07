"""Known-answer checks for immutable single-state timber demand consumption."""

from __future__ import annotations

import copy
import json

import pytest

from scripts import thin_bolted_timber_demand_checks as demand


@pytest.fixture
def method_field(monkeypatch):
    """Zero-action method fixture on real identities; never an issued load case."""
    packet, native, layout = demand.read_unit()
    support = {r["axis_id"]: r for r in packet["finished_geometry_queries"]["physical_shaft_wood_support"]}
    field = {"candidate": demand.unit.CANDIDATE, "layout_report_sha256": demand.unit.LAYOUT_SHA,
             "geometry_cache_sha256": demand.NATIVE_SHA, "case_id": "method-fixture-only",
             "accessory_placement": "method-fixture-only", "parameters": {"fixture": "zero-action",
                 "floor_support_basis": demand.FLOOR_BASIS, "floor_contact_geometry_sha256": demand.CONTACT_SHA},
             "source_sha256": {demand.FRAME_PRODUCER: demand.FRAME_PRODUCER_SHA,
                 str(demand.CONTACT.relative_to(demand.ROOT)): demand.CONTACT_SHA},
             "usable_conditional_actions": True,
             "response": {"converged": True, "physical_residual_uses_unmodified_laws": True,
                          "gradient_inf_n": 0., "generalized_residual_tolerance_n": 1e-5},
             "equilibrium_verification": {"all_body_and_global_checks_pass": True},
             "common_wrench_reference_xyz_mm": [0., 0., 0.],
             "release": demand.unit.RELEASE, "attachment_actions": [], "retained_bolt_actions": [],
             "panel_screw_actions": [], "contact_actions": [], "floor_actions": [],
             "member_element_actions": [], "body_applied_loads": [], "body_equilibrium_residuals": []}
    # This fixture checks timber-only identity contracts. Its deliberately
    # synthetic zero-action case cannot be represented as an issued frame
    # state, so the shared audit is replaced only within this method fixture.
    monkeypatch.setattr(demand.support_audit, "audit_finished_state", lambda value: {
        "independent_finished_support_and_equilibrium_checks_pass": True,
        "equilibrium": {"body_count": 62, "maximum_body_or_global_force_norm_n": 0.},
        "support": {"finished_host_count": 8}, "method_fixture_only": True})
    field["state_id"] = demand.state_identity(field)
    for axis in layout["installed_axes"]:
        if axis["attachments"]:
            for attachment in axis["attachments"]:
                field["attachment_actions"].append({"axis_id": axis["id"], "angle_id": attachment["angle_id"],
                    "flange": attachment["flange"], "receiver": attachment["receiver"],
                    "first": attachment["receiver"], "second": attachment["angle_id"],
                    "point_xyz_mm": attachment["entry_xyz_mm"], "force_on_first_xyz_n": [0., 0., 0.],
                    "force_on_receiver_xyz_n": [0., 0., 0.], "moment_on_receiver_at_point_xyz_nmm": [0., 0., 0.]})
        else:
            first, second = axis["receivers"]
            intervals = support[axis["id"]]["member_intervals"]
            aa = [r["interval_mm"] for r in intervals if r["member"] == first]
            bb = [r["interval_mm"] for r in intervals if r["member"] == second]
            t = next(a for interval in aa for a in interval if any(abs(a - b) < 1e-5 for other in bb for b in other))
            point = demand.add(axis["point"], demand.scale(demand.unit.unit(axis["direction"]), t))
            field["retained_bolt_actions"].append({"axis_id": axis["id"], "first": first, "second": second,
                "point_xyz_mm": point, "force_on_first_xyz_n": [0., 0., 0.],
                "moment_at_point_model_xyz_nmm": [0., 0., 0.]})
    bodies = [p for p in native["parts"] if p["kind"] in ("timber", "panel", "bracket")]
    for body in bodies:
        field["body_equilibrium_residuals"].append({"body": body["id"], "force_xyz_n": [0., 0., 0.],
            "moment_about_reference_xyz_nmm": [0., 0., 0.]})
    for table in ("attachment_actions", "retained_bolt_actions"):
        for row in field[table]:
            row.update(state_id=field["state_id"], case_id=field["case_id"], accessory_placement=field["accessory_placement"])
    return field, layout, native, packet


def test_single_state_hash_and_exact_action_census(method_field):
    field, layout, native, packet = method_field
    checked = demand.validate_field(field, layout, native, packet)
    assert checked["equilibrium"]["body_count"] == 62
    assert checked["equilibrium"]["maximum_body_or_global_force_norm_n"] == 0.
    assert checked["method_fixture_only"] is True
    changed = copy.deepcopy(field)
    changed["parameters"]["clearance"] = 1.5875
    with pytest.raises(ValueError, match="state identity"):
        demand.validate_field(changed, layout, native, packet)
    mixed = copy.deepcopy(field)
    mixed["retained_bolt_actions"][0]["state_id"] = "another-state"
    with pytest.raises(ValueError, match="mixes"):
        demand.validate_field(mixed, layout, native, packet)
    missing = copy.deepcopy(field)
    missing["attachment_actions"].pop()
    with pytest.raises(ValueError, match="exact72"):
        demand.validate_field(missing, layout, native, packet)


def test_retained_interface_rejects_tampering(method_field):
    field, layout, native, packet = method_field
    changed = copy.deepcopy(field)
    changed["retained_bolt_actions"][0]["point_xyz_mm"][2] += 1.
    with pytest.raises(ValueError, match="physical shaft|actual member interface"):
        demand.validate_field(changed, layout, native, packet)


def test_affine_cut_known_answer_includes_distributed_weight_and_actual_point_arm():
    grain = [1., 0., 0.]
    # Uniform20Ndown over100mm: half-member force10Ndown,25mm arm=>250Nmm.
    cut = demand.member_cut_wrench(grain, 0., 100., [50., 0., 0.], [50., 0., 0.],
                                  [0., 0., -20.], [])
    assert cut["force_on_lower_portion_xyz_n"] == pytest.approx([0., 0., 10.])
    assert cut["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx([0., 250., 0.])
    point = ([25., 10., 0.], [100., 0., 0.], [0., 0., 0.])
    loaded = demand.member_cut_wrench(grain, 0., 100., [50., 0., 0.], [50., 0., 0.],
                                     [0., 0., -20.], [point])
    assert loaded["axial_tension_positive_n"] == pytest.approx(-100.)
    assert loaded["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx([0., 250., 1000.])
    # Affineweight centroid60mm:20Ntotal and600Nmmaboutmidpoint recover exactly.
    end = demand.member_cut_wrench(grain, 0., 100., [100., 0., 0.], [60., 0., 0.],
                                  [0., 0., -20.], [])
    assert end["force_on_lower_portion_xyz_n"] == pytest.approx([0., 0., 20.])
    assert end["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx([0., 800., 0.])


def test_retained_signed_angles_and_boundary_rules_are_separate():
    axis = {"id": "coupon", "receivers": ["runner", "leg"], "direction": [1., 0., 0.], "diameter_mm": 12.7}
    source = {"state_id": "method-only", "force_on_first_xyz_n": [0., 100., 0.]}
    distances = {"grain": {"negative": 100., "positive": 50.}, "cross_grain": {"negative": 40., "positive": 60.}}
    receivers = {("coupon", "runner"): {"member": "runner", "grain_axis_xyz": [0., 1., 0.],
        "finished_full_wall_length_mm": 38.1, "sampled_minimum_distances_to_first_finished_boundary_mm": distances},
        ("coupon", "leg"): {"member": "leg", "grain_axis_xyz": [0., 0., 1.],
        "finished_full_wall_length_mm": 50.8, "sampled_minimum_distances_to_first_finished_boundary_mm": distances}}
    value = demand.retained_reference(axis, source, receivers, 1.)
    assert [m["load_to_grain_degrees"] for m in value["members"]] == pytest.approx([0., 90.])
    assert value["mode_values_n"]["Im"] == pytest.approx(.5 * 1.5 * 5600. / 5. * demand.unit.N_PER_LBF)
    assert value["members"][0]["signed_boundary_diagnostics"]["grain_loaded_end"] == "positive"
    assert value["members"][1]["signed_boundary_diagnostics"]["complete_Cdelta"] is None
    assert value["complete_connection_utilization"] is None
    assert value["required_Fyb_for_this_unadjusted_component"]["required_Fyb_psi"] > 0.
    overloaded = demand.retained_reference(axis, dict(source, force_on_first_xyz_n=[0., 10000., 0.]), receivers, 1.)
    inverse = overloaded["required_Fyb_for_this_unadjusted_component"]
    assert inverse["status"] == "unattainable_by_Fyb_alone"
    assert inverse["required_Fyb_psi"] is None
    assert inverse["Fyb_independent_component_ceiling_n"] == min(overloaded["mode_values_n"][m] for m in ("Im", "Is", "II"))


def test_thread_window_checks_far_steel_and_does_not_require_entire_wood_smooth():
    axis = {"id": "paired", "diameter_mm": 12.7, "nominal_under_head_length_mm": 76.2,
            "hardware_scenario": {"washer_thickness_mm": 3.175}, "before_plate_mm": 5.55625,
            "after_plate_mm": 5.55625, "grip_mm": 38.1, "receivers": ["wood"]}
    receivers = {("paired", "wood"): {"finished_full_wall_intervals_from_axis_point_mm": [[0., 38.1]]}}
    result = demand.standard_thread_window(axis, receivers)
    assert result["NDS_diameter_window_scenario"] == "Dr_required"
    wood, near, far = result["all_bearing_members"]
    assert wood["maximum_possible_thread_bearing_from_Lbmin_mm"] == pytest.approx(12.28725)
    assert near["fullD_exception_guaranteed_by_standard_window"] is True
    assert far["minimum_thread_bearing_from_Lgmax_mm"] == pytest.approx(5.55625)
    axis = dict(axis, id="original", nominal_under_head_length_mm=203.2, before_plate_mm=0.,
                after_plate_mm=0., grip_mm=177.8, receivers=["first", "second"])
    receivers = {("original", "first"): {"finished_full_wall_intervals_from_axis_point_mm": [[0., 88.9]]},
                 ("original", "second"): {"finished_full_wall_intervals_from_axis_point_mm": [[88.9, 177.8]]}}
    current = demand.standard_thread_window(axis, receivers)
    proposed = demand.standard_thread_window(axis, receivers, 215.9)
    assert current["NDS_diameter_window_scenario"] == "delivered_transition_dependent_D_or_Dr"
    assert proposed["NDS_diameter_window_scenario"] == "fullD_exception_within_standard_window"
    assert proposed["all_bearing_members"][1]["maximum_possible_thread_bearing_from_Lbmin_mm"] == pytest.approx(12.827)
    assert proposed["actual_NDS_diameter_or_material_adopted"] is False


def test_existing_sections_use_simultaneous_cut_wrench_without_geometry_queries():
    field = {"attachment_actions": [], "retained_bolt_actions": [], "panel_screw_actions": [],
             "contact_actions": [], "floor_actions": [],
             "body_applied_loads": [{"id": "self-weight/method-coupon", "body": "coupon",
                                     "point_xyz_mm": [50., 10., 0.], "force_xyz_n": [-20., 0., 0.]}],
             "member_element_actions": [{"member": "coupon", "start_xyz_mm": [0., 0., 0.],
                 "end_xyz_mm": [100., 0., 0.], "basis_grain_u_v_xyz": [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]}]}
    geometry = {"finished_member_sections": [{"member": "coupon", "grain_axis_xyz": [1., 0., 0.],
        "sampled_sections": [{"station_global_grain_projection_mm": 25., "finished_area_mm2": 100.},
                             {"station_global_grain_projection_mm": 75., "finished_area_mm2": 50.}]}]}
    result = demand.net_section_checks(field, geometry)[0]
    witness = result["maximum_tension_area_component_witness"]
    assert witness["cut_grain_station_mm"] == 75.
    assert witness["axial_tension_positive_n"] == pytest.approx(15.)
    assert witness["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx([0., 0., -150.])
    assert witness["positive_tension_over_base_area_reference"] == pytest.approx(15. / (50. * 575. * demand.unit.N_PER_LBF / 25.4**2))
    assert result["complete_net_section_utilization"] is None


def test_actual_duty_group_deduplicates_shared_shafts_and_refuses_steel_Cg(method_field):
    field, layout, _native, packet = method_field
    detail = json.loads((demand.ROOT / packet["reproducible_detail_artifact"]["path"]).read_text())
    full = detail["finished_geometry_queries"]
    receivers = {(r["axis_id"], r["member"]): r for r in full["receiver_boundary_geometry"]}
    for row in field["attachment_actions"]:
        receiver = receivers[(row["axis_id"], row["receiver"])]
        row["force_on_receiver_xyz_n"] = demand.scale(receiver["grain_axis_xyz"], 100.)
    rows = demand.connected_duty_group_diagnostics(field, layout, receivers, full, "a" * 64)
    assert len(rows) == 48
    paired_beam = next(row for row in rows if row["flange"] == "beam" and row["attachment_count"] == 2)
    assert paired_beam["physical_fastener_count"] == 1
    paired_post = next(row for row in rows if row["flange"] == "post" and row["physical_fastener_count"] == 2)
    assert paired_post["conditional_raw_two_bolt_row_reference_n"] > 0.
    assert "unsupported_nonwood_member" in paired_post["maintained_group_method_applicability"]["reason_codes"]
    assert paired_post["actual_Cg"] is None


def test_finished_support_rejects_raw_seat_ghost_and_accepts_boundary():
    polygon = [[38.1, 0., 0.], [88.9, 0., 0.], [88.9, 10., 0.], [38.1, 10., 0.]]
    assert demand.support_audit.inside_rectangle([38.1, 0., 0.], polygon)
    assert demand.support_audit.inside_rectangle([60., 5., 0.], polygon)
    assert not demand.support_audit.inside_rectangle([0., 0., 0.], polygon)
    assert not demand.support_audit.inside_rectangle([60., 5., 1.], polygon)


def test_shared_finished_gate_consumes_released_state_and_rejects_action_tampering():
    path = demand.unit.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json"
    assert demand.unit.sha(path) == "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d"
    field = json.loads(path.read_text())
    packet, native, layout = demand.read_unit()
    receipt = demand.validate_field(field, layout, native, packet)
    assert receipt["independent_finished_support_and_equilibrium_checks_pass"] is True
    assert receipt["equilibrium"]["body_count"] == 62
    assert receipt["equilibrium"]["flange_contacts"] == 288
    assert receipt["support"]["finished_host_count"] == 8
    assert receipt["support"]["normal_port_count"] == 32
    assert receipt["invoked_support_audit_sha256"] == demand.SUPPORT_AUDIT_SHA
    changed = copy.deepcopy(field)
    row = changed["attachment_actions"][0]
    row["force_on_first_xyz_n"][0] += 1.
    row["force_on_receiver_xyz_n"][0] += 1.
    with pytest.raises(ValueError):
        demand.validate_field(changed, layout, native, packet)


def test_shared_gate_cannot_be_bypassed_by_reported_convergence(method_field, monkeypatch):
    field, layout, native, packet = method_field
    monkeypatch.setattr(demand.support_audit, "audit_finished_state", lambda value: {
        "independent_finished_support_and_equilibrium_checks_pass": False})
    with pytest.raises(ValueError, match="independent finished-support/equilibrium gate fails"):
        demand.validate_field(field, layout, native, packet)


def test_duration_hypothesis_requires_an_explicit_live_case():
    live = demand.duration_component_sensitivity(100., 160., case_id="a12-rear", live_load_present=True)
    assert live["CD1_same_state_component_ratio"] == 1.6
    assert live["conditional_CD1p6_same_state_component_ratio"] == 1.
    assert live["complete_adjusted_NDS_resistance_n"] is None
    permanent = demand.duration_component_sensitivity(100., 90., case_id="gravity-only", live_load_present=False)
    assert permanent["conditional_CD1p6_reference_n"] is None
    assert permanent["conditional_CD1p6_same_state_component_ratio"] is None
    assert permanent["permanent_only_case_and_CD0p9_comparison"]["same_state_component_ratio"] == 1.
