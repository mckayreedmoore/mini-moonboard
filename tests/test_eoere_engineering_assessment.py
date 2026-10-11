"""Portable known answers for the saved-state engineering diagnostics."""

import copy
import json
import math

import numpy as np
import pytest

from scripts import eoere_engineering_assessment as review
from scripts.thin_bolted_corotational_methods import so3_exp


def load_field(case_id):
    label, fx, fy = review.EXPECTED_LOADS[case_id]
    force = [fx, fy, -2224.11080763025]
    point, midplane = [1., 12., 3.], [1., 2., 3.]
    loads = [
        {"id": "permanent", "body": "wood", "point_xyz_mm": [5., 6., 7.], "force_xyz_n": [0., 0., -2000.]},
        {"id": "climber/" + label, "body": "panel", "point_xyz_mm": point, "force_xyz_n": force},
    ]
    case = {"loads": loads,
            "hold": {"label": label, "panel": "panel", "force_xyz_n": force, "load_point_xyz_mm": point,
                     "panel_midplane_xyz_mm": midplane,
                     "moment_about_panel_midplane_xyz_nmm": [-22241.1080763025, 0., -10.*fx]},
            "applied_force_xyz_n": [fx, fy, -4224.11080763025],
            "applied_moment_about_global_origin_xyz_nmm": [-12000.+12.*force[2]-3.*fy,
                                                         10000.+3.*fx-force[2], fy-12.*fx]}
    return {"case_id": case_id, "state_id": case_id+"-state", "source_inputs": {"case": case},
            "body_applied_loads": copy.deepcopy(loads)}


def contact_fixture(translation=.002, theta=.1):
    point = [1., 0., 5.]
    q = np.zeros(24)
    q[[0, 6]] = translation
    q[[5, 11]] = theta*1000.
    chart = {"rotation_scale": 1000., "final_ndof": 24, "four_port_fittings": {}, "timber": {
        "a": {"axis": [0., 0., 1.], "start": [0., 0., 0.], "stations": [0., 10.],
              "index": [list(range(6)), list(range(6, 12))]},
        "b": {"axis": [0., 0., 1.], "start": [2., 0., 0.], "stations": [0., 10.],
              "index": [list(range(12, 18)), list(range(18, 24))]},
    }}
    field = {"case_id": "case", "state_id": "state", "response": {
        "q": q.tolist(), "q_canonical_sha256": review.canonical_sha(q.tolist())},
        "reference_interaction_descriptors": [{"id": "face", "kind": "timber_face_contact", "first": "a", "second": "b",
                                               "point_xyz_mm": point, "direction_xyz": [1., 0., 0.], "stiffness": 1000.}],
        "contact_actions": [{"id": "face", "first": "a", "second": "b", "point_xyz_mm": point,
                             "force_on_first_xyz_n": [max(0., -translation)*1000., 0., 0.],
                             "compression_n": max(0., -translation)*1000.}]}
    return field, chart


@pytest.mark.parametrize("case_id", review.SEQUENCE)
def test_load_units_eccentric_couple_and_global_wrench(case_id):
    checked = review.load_check(load_field(case_id))
    assert checked["climber_force_xyz_n"][2] == pytest.approx(-2224.11080763025)
    assert checked["permanent_and_accessory_weight_n"] == 2000.
    assert checked["whole_moment_about_origin_xyz_nmm"] == pytest.approx(
        load_field(case_id)["source_inputs"]["case"]["applied_moment_about_global_origin_xyz_nmm"])


@pytest.mark.parametrize("mutation", ["force", "couple", "owner", "duplicate", "whole_moment"])
def test_reject_changed_load_basis(mutation):
    field = load_field("a12-left")
    if mutation == "force":
        field["source_inputs"]["case"]["hold"]["force_xyz_n"][0] *= -1
    elif mutation == "couple":
        field["source_inputs"]["case"]["hold"]["moment_about_panel_midplane_xyz_nmm"][2] *= -1
    elif mutation == "owner":
        field["body_applied_loads"][1]["body"] = "other-panel"
    elif mutation == "duplicate":
        field["body_applied_loads"].append(field["body_applied_loads"][0])
    else:
        field["source_inputs"]["case"]["applied_moment_about_global_origin_xyz_nmm"][1] += 1.
    with pytest.raises(ValueError):
        review.load_check(field)


def test_known_finite_arm_cosine_closes_a_linear_open_gap():
    field, chart = contact_fixture()
    result, rows = review.contact_probe(field, chart, so3_exp)
    row = rows[0]
    assert row["linear_gap_mm"] == pytest.approx(-.002)
    assert row["fixed_director_finite_arm_gap_mm"] == pytest.approx(1.-math.cos(.1)-.002)
    assert row["gap_change_mm"] == pytest.approx(1.-math.cos(.1))
    assert result["open_to_compressed"] == 1
    assert result["compressed_to_open"] == 0
    assert result["physical_error_bound_or_response"] is False


def test_nonuniform_timber_stations_interpolate_unequal_poses_at_nonmidpoint():
    field, chart = contact_fixture()
    point = [1., 0., 5.5]
    q = np.zeros(36)
    q[:18] = [.001, -10., 4., 0., 0., 10.,
              .003, 2., 1., 0., 0., 20.,
              .007, 10., -3., 0., 0., 100.]
    for i, member in enumerate(chart["timber"].values()):
        member["stations"] = [0., 4., 10.]
        member["index"] = [list(range(18*i+6*j, 18*i+6*j+6)) for j in range(3)]
    chart["final_ndof"] = len(q)
    field["response"] = {"q": q.tolist(), "q_canonical_sha256": review.canonical_sha(q.tolist())}
    for table in ["reference_interaction_descriptors", "contact_actions"]:
        field[table][0]["point_xyz_mm"] = point
    # 5.5 is one quarter of the way from stations 4 to 10.
    anchor, translation, rotation = review.timber_pose(chart["timber"]["a"], point, q, 1000.)
    assert anchor == pytest.approx([0., 0., 5.5])
    assert translation == pytest.approx([.004, 4., 0.])
    assert rotation == pytest.approx([0., 0., .04])
    result, rows = review.contact_probe(field, chart, so3_exp)
    assert rows[0]["linear_gap_mm"] == pytest.approx(-.004)
    assert rows[0]["fixed_director_finite_arm_gap_mm"] == pytest.approx(1.-math.cos(.04)-.004)
    assert result["all_contact_scalars"][0] == pytest.approx([-.004, 1.-math.cos(.04)-.004, .04])


def test_multicontact_census_covers_both_switch_directions_near_zero_and_whole_extrema():
    field, chart = contact_fixture()
    field["reference_interaction_descriptors"], field["contact_actions"] = [], []
    specifications = [("open-to-compressed", 1., 0., [1., 0., 0.]),
                      ("compressed-to-open", 1., 0., [-1., 0., 0.]),
                      ("stays-open", 0., 0., [1., 0., 0.]),
                      ("near-zero", 0., 0., [0., 1., 0.]),
                      ("largest-change-stays-open", -3., 0., [1., 0., 0.]),
                      ("near-zero-to-compressed", 1., .02, [1., 0., 0.])]
    expected = []
    for name, x, y, direction in specifications:
        point = [x, y, 5.]
        linear = -((.002-.1*y)*direction[0]+.1*x*direction[1])
        finite = -((.002+(math.cos(.1)-1.)*x-math.sin(.1)*y)*direction[0]
                   +(math.sin(.1)*x+(math.cos(.1)-1.)*y)*direction[1])
        expected.append([linear, finite, .1])
        field["reference_interaction_descriptors"].append({"id": name, "kind": "timber_face_contact",
            "first": "a", "second": "b", "point_xyz_mm": point, "direction_xyz": direction, "stiffness": 1000.})
        field["contact_actions"].append({"id": name, "first": "a", "second": "b", "point_xyz_mm": point,
                                         "compression_n": max(0., linear)*1000.})
    result, rows = review.contact_probe(field, chart, so3_exp)
    assert result["contacts"] == result["timber_face_contacts"] == 6
    assert result["flange_contacts"] == 0
    assert np.asarray(result["all_contact_scalars"]) == pytest.approx(np.asarray(expected), abs=1e-14)
    assert result["strict_open_compressed_class_changes"] == 2
    assert result["open_to_compressed"] == result["compressed_to_open"] == 1
    assert [(r["linear_class"], r["surrogate_class"]) for r in rows] == [(-1, 1), (1, -1), (-1, -1), (0, 0), (-1, -1), (0, 1)]
    assert result["maximum_absolute_gap_change"] == rows[4]
    assert result["maximum_relative_linear_rotation"] == rows[0]
    assert result["largest_gap_change_class_switch"] == rows[0]


def test_known_finite_arm_sine_and_exact_fitting_port_anchor():
    row = {"ports": [{"id": "chosen", "port_index": 1, "point_reference_xyz_mm": [4., 5., 6.]}],
           "dof_indices": list(range(24))}
    q = np.zeros(24)
    q[6:12] = [2., 3., 4., 0., 0., 1000.*.2]
    pose = review.fitting_pose(row, "chosen", q, 1000.)
    linear, finite = review.rigid_arm_displacements([5., 5., 6.], pose, so3_exp)
    assert linear == pytest.approx([2., 3.2, 4.])
    assert finite == pytest.approx([1.+math.cos(.2), 3.+math.sin(.2), 4.])
    with pytest.raises(ValueError, match="exact owned fitting"):
        review.fitting_pose(row, "unspecified", q, 1000.)


def test_mixed_timber_fitting_probe_uses_exact_port_and_both_finite_arms():
    field, chart = contact_fixture()
    del chart["timber"]["b"]
    chart["four_port_fittings"]["angle"] = {
        "ports": [{"id": "decoy", "port_index": 0, "point_reference_xyz_mm": [100., 100., 0.]},
                  {"id": "chosen", "port_index": 1, "point_reference_xyz_mm": [2., 0., 5.]}],
        "dof_indices": list(range(12, 24))}
    q = field["response"]["q"]
    q[12:18], q[18:24] = [3., 4., 5., 0., 0., 300.], [.001, .0002, -.002, 0., 0., 200.]
    field["response"]["q_canonical_sha256"] = review.canonical_sha(q)
    field["reference_interaction_descriptors"][0].update({"kind": "flange_contact", "second": "angle",
        "second_port_id": "chosen", "direction_xyz": [-1., 0., 0.]})
    field["contact_actions"][0].update({"second": "angle", "compression_n": 1., "force_on_first_xyz_n": [-1., 0., 0.]})
    result, rows = review.contact_probe(field, chart, so3_exp)
    # The two arms are +1 and -1 in X, rotating by 0.1 and 0.2 rad.
    finite_gap = .001-(1.-math.cos(.1))-(1.-math.cos(.2))
    assert result["timber_face_contacts"] == 0 and result["flange_contacts"] == 1
    assert rows[0]["linear_gap_mm"] == pytest.approx(.001)
    assert rows[0]["fixed_director_finite_arm_gap_mm"] == pytest.approx(finite_gap)
    assert result["all_contact_scalars"][0] == pytest.approx([.001, finite_gap, .1])
    assert result["compressed_to_open"] == result["strict_open_compressed_class_changes"] == 1
    assert result["open_to_compressed"] == 0
    assert result["largest_gap_change_class_switch"] == result["maximum_absolute_gap_change"] == rows[0]


def test_three_dimensional_probe_has_independent_quarter_and_sixth_turn_answers():
    # The oblique timber station is 3.5, one quarter of the way from 2 to 8.
    point, anchor_a, anchor_b = np.array([3.2, -1.3, 6.]), np.array([2., -.5, 6.]), np.array([4., -3., 5.])
    axis_a, axis_b = np.array([1., 2., 2.])/3., np.array([-2., 1., 2.])/3.
    theta_a, theta_b = axis_a*math.pi/2., axis_b*math.pi/3.
    translation_a, translation_b = np.array([.02, -.01, .02]), np.array([-.01, .03, .02])
    perturbation = np.array([.03, -.02, .01])
    q = np.zeros(24)
    q[:6] = [20., -40., 60., 700., -900., 400.]
    q[6:12] = np.r_[[.01, -.02, .03], (theta_a-perturbation)*1000.]
    q[12:18] = np.r_[[.05, .02, -.01], (theta_a+3.*perturbation)*1000.]
    q[18:24] = np.r_[translation_b, theta_b*1000.]
    chart = {"rotation_scale": 1000., "final_ndof": len(q), "timber": {
        "a": {"axis": (np.array([2., 3., 6.])/7.).tolist(), "start": [1., -2., 3.],
              "stations": [0., 2., 8.], "index": [list(range(6*i, 6*i+6)) for i in range(3)]}},
        "four_port_fittings": {"angle": {"ports": [{"id": "chosen", "port_index": 0,
            "point_reference_xyz_mm": anchor_b.tolist()}], "dof_indices": list(range(18, 24))}}}
    direction = np.array([2., -1., 3.])/math.sqrt(14.)
    arm_a, arm_b = point-anchor_a, point-anchor_b
    linear_a = translation_a+np.cross(theta_a, arm_a)
    linear_b = translation_b+np.cross(theta_b, arm_b)
    # Rodrigues' formula at 90 and 60 degrees gives these independent answers.
    finite_a = translation_a+np.cross(axis_a, arm_a)+axis_a*(axis_a @ arm_a)-arm_a
    finite_b = translation_b-.5*arm_b+math.sqrt(3.)/2.*np.cross(axis_b, arm_b)+.5*axis_b*(axis_b @ arm_b)
    linear_gap, finite_gap = float(-direction @ (linear_a-linear_b)), float(-direction @ (finite_a-finite_b))
    field = {"case_id": "3d", "state_id": "3d-state", "response": {
        "q": q.tolist(), "q_canonical_sha256": review.canonical_sha(q.tolist())},
        "reference_interaction_descriptors": [{"id": "oblique", "kind": "flange_contact", "first": "a", "second": "angle",
            "second_port_id": "chosen", "point_xyz_mm": point.tolist(), "direction_xyz": direction.tolist(), "stiffness": 1000.}],
        "contact_actions": [{"id": "oblique", "first": "a", "second": "angle", "point_xyz_mm": point.tolist(),
                             "compression_n": max(0., linear_gap)*1000.}]}
    anchor, translation, rotation = review.timber_pose(chart["timber"]["a"], point, q, 1000.)
    assert anchor == pytest.approx(anchor_a)
    assert translation == pytest.approx(translation_a)
    assert rotation == pytest.approx(theta_a)
    result, rows = review.contact_probe(field, chart, so3_exp)
    assert rows[0]["linear_gap_mm"] == pytest.approx(linear_gap, abs=1e-13)
    assert rows[0]["fixed_director_finite_arm_gap_mm"] == pytest.approx(finite_gap, abs=1e-13)
    assert result["all_contact_scalars"][0] == pytest.approx([linear_gap, finite_gap, np.linalg.norm(theta_a-theta_b)])


@pytest.mark.parametrize("gap,expected", [
    (-1.001e-8, -1), (-1e-8, 0), (-.999e-8, 0), (0., 0), (.999e-8, 0), (1e-8, 0), (1.001e-8, 1)])
def test_diagnostic_gap_classification_boundaries(gap, expected):
    assert review.gap_class(gap) == expected


def test_gap_probe_is_invariant_to_world_origin_and_recovers_signed_action():
    field, chart = contact_fixture(translation=-.002)
    original, rows = review.contact_probe(field, chart, so3_exp)
    assert rows[0]["linear_gap_mm"] == pytest.approx(.002)
    shift = np.array([20., -300., 4.])
    for row in chart["timber"].values():
        row["start"] = (np.asarray(row["start"])+shift).tolist()
    for table in ["reference_interaction_descriptors", "contact_actions"]:
        field[table][0]["point_xyz_mm"] = (np.asarray(field[table][0]["point_xyz_mm"])+shift).tolist()
    moved, moved_rows = review.contact_probe(field, chart, so3_exp)
    for key in ["linear_gap_mm", "fixed_director_finite_arm_gap_mm", "gap_change_mm"]:
        assert moved_rows[0][key] == pytest.approx(rows[0][key], abs=1e-12)
    assert moved["strict_open_compressed_class_changes"] == original["strict_open_compressed_class_changes"]


@pytest.mark.parametrize("mutation", ["q_digest", "force", "owner", "director", "indices"])
def test_probe_rejects_foreign_or_inconsistent_saved_state(mutation):
    field, chart = contact_fixture()
    if mutation == "q_digest":
        field["response"]["q"][0] += 1.
    elif mutation == "force":
        field["contact_actions"][0]["compression_n"] = 1.
    elif mutation == "owner":
        field["reference_interaction_descriptors"][0]["second"] = "panel"
    elif mutation == "director":
        field["reference_interaction_descriptors"][0]["direction_xyz"][0] = -2.
    else:
        chart["timber"]["a"]["index"][0][0] = -1
    with pytest.raises(ValueError):
        review.contact_probe(field, chart, so3_exp)


def test_effective_length_is_a_domain_requirement_without_bracing_credit():
    rows = review.stability_requirements([
        {"member": "long", "span_mm": 2500., "weak_column_domain_limit_mm": 1905.},
        {"member": "boundary", "span_mm": 1905., "weak_column_domain_limit_mm": 1905.},
    ])
    assert rows[0]["maximum_effective_length_factor_for_full_span"] == .762
    assert rows[0]["full_span_K1_outside_domain"] is True
    assert rows[1]["full_span_K1_outside_domain"] is False
    assert all(r["actual_effective_length_factor"] is None and not r["bracing_or_member_strength_qualified"] for r in rows)


def test_active_action_paths_exclude_zero_links_and_do_not_qualify_directional_restraint():
    field = {"case_id": "case", "state_id": "state", "body_identities": ["a", "b", "c"],
             **{k: [] for k in ["common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions", "floor_actions"]}}
    field["floor_actions"] = [{"first": "a", "second": "floor", "force_on_first_xyz_n": [0., 0., 10.]}]
    field["contact_actions"] = [
        {"first": "a", "second": "b", "force_on_first_xyz_n": [0., 0., 1.]},
        {"first": "b", "second": "c", "force_on_first_xyz_n": [0., 0., 0.]},
    ]
    result = review.load_path_screen(field)
    assert result["owners_without_active_action_path_to_floor"] == ["c"]
    field["contact_actions"][1]["moment_at_point_model_xyz_nmm"] = [0., 0., .001]
    result = review.load_path_screen(field)
    assert result["all_owners_have_active_action_path_to_floor"] is True
    assert result["directional_restraint_capacity_or_complete_joint_behavior_qualified"] is False
    field["common_shaft_bearing_actions"] = [{"first": "b", "second": "a", "force_on_first_xyz_n": [0., 1., 0.]}]
    result = review.load_path_screen(field)
    assert result["active_action_rows"] == 4
    assert result["active_edge_census"] == [[0, 1, 2], [0, 3, 1], [1, 2, 1]]


@pytest.mark.parametrize("force,moment,active", [
    (.999e-6, 0., False), (1e-6, 0., False), (1.001e-6, 0., True),
    (0., .999e-5, False), (0., 1e-5, False), (0., 1.001e-5, True),
    (1e-6, 1e-5, False), (.999e-6, 1.001e-5, True)])
def test_active_action_force_and_moment_cutoffs(force, moment, active):
    field = {"case_id": "boundary", "state_id": "state", "body_identities": ["body"],
        **{k: [] for k in ["common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions"]},
        "floor_actions": [{"first": "body", "second": "floor", "force_on_first_xyz_n": [force, 0., 0.],
                           "moment_at_point_model_xyz_nmm": [0., moment, 0.]}]}
    result = review.load_path_screen(field)
    assert result["force_threshold_n"] == 1e-6 and result["moment_threshold_nmm"] == 1e-5
    assert result["all_owners_have_active_action_path_to_floor"] is active
    assert result["active_action_rows"] == int(active)
    assert result["active_edge_census"] == ([[0, 1, 1]] if active else [])


@pytest.mark.parametrize("removed_table,disconnected", [
    ("floor_actions", ["base", "plate", "shaft", "timber", "panel"]),
    ("contact_actions", ["plate", "shaft", "timber", "panel"]),
    ("shaft_end_capture_actions", ["shaft", "timber", "panel"]),
    ("common_shaft_bearing_actions", ["timber", "panel"]),
    ("panel_screw_actions", ["panel"]),
])
def test_routing_chain_requires_each_physical_action_table(removed_table, disconnected):
    field = {"case_id": "case", "state_id": "state", "body_identities": ["base", "plate", "shaft", "timber", "panel"]}
    for table, first, second in [("floor_actions", "base", "floor"),
                                 ("contact_actions", "plate", "base"),
                                 ("shaft_end_capture_actions", "shaft", "plate"),
                                 ("common_shaft_bearing_actions", "timber", "shaft"),
                                 ("panel_screw_actions", "panel", "timber")]:
        field[table] = [{"first": first, "second": second, "force_on_first_xyz_n": [0., 0., 2.]}]
    result = review.load_path_screen(field)
    assert result["physical_owners"] == result["active_action_rows"] == 5
    assert result["physical_owner_ids"] == field["body_identities"]
    assert result["active_edge_census"] == [[0, 1, 1], [0, 5, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1]]
    assert result["owners_without_active_action_path_to_floor"] == []
    assert result["all_owners_have_active_action_path_to_floor"] is True
    field[removed_table][0]["force_on_first_xyz_n"] = [0., 0., 0.]
    result = review.load_path_screen(field)
    assert result["owners_without_active_action_path_to_floor"] == sorted(disconnected)
    assert result["active_action_rows"] == 4
    assert sum(r[2] for r in result["active_edge_census"]) == 4
    assert result["all_owners_have_active_action_path_to_floor"] is False


def install_saved_evidence(monkeypatch):
    """Small complete six-case intake fixture, with genuinely evaluated gaps."""
    ref = lambda path: {"path": str(path.relative_to(review.current.ROOT)), "sha256": "a"*64}
    geometry, hardware = {"path": "geometry", "sha256": "b"*64}, {"path": "hardware", "sha256": "c"*64}
    release = {"candidate_accepted": False, "capacity_established": False}
    forces = {"schema": "eoere_selected_hardware_six_case_response/v1", "case_sequence": review.SEQUENCE,
              "geometry": geometry, "hardware_model": hardware, "geometry_revision": "geo", "hardware_revision": "hardware",
              "extra_grid": False, "release": release, "all_six_saved_field_admissions_pass": True,
              "complete_joint_resistance": None, "finished_member_capacity": None, "cases": []}
    components = {**copy.deepcopy(forces), "schema": "eoere_current_six_case_structural_references/v1",
                  "current_response": ref(review.PACKET/"result.json"), "cases": []}
    registry = {ref(review.PACKET/"result.json")["path"]: forces, ref(review.PACKET/"components.json")["path"]: components}
    for i, case_id in enumerate(review.SEQUENCE):
        field, chart = contact_fixture(translation=.001*(i+1), theta=.1+.01*i)
        field.update(load_field(case_id))
        field["schema"] = review.current.FIELD_SCHEMA
        field["response"]["converged"] = True
        field["body_identities"] = ["a", "b", *[f"unused-{j}" for j in range(148)]]
        for table in ["common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "floor_actions"]:
            field[table] = []
        for j in range(20):
            chart["timber"][f"unused-{j}"] = chart["timber"]["a"]
        chart["four_port_fittings"] = {f"unused-{j}": {} for j in range(22)}
        bundle = {"manifest": {"path": case_id+"-chart", "sha256": "d"*64}}
        field["operator_bundle"] = bundle
        binding = {"case_id": case_id, "state_id": field["state_id"],
                   "field": {"path": case_id+"-field", "sha256": "e"*64},
                   "admission": {"path": case_id+"-admission", "sha256": "f"*64}, "operator_bundle": bundle}
        registry[case_id+"-field"], registry[case_id+"-chart"] = field, {
            "coordinate_map": chart, "rigid_modes_reference_xyz_mm": [0., 750., 1100.]}
        registry[case_id+"-admission"] = {review.current.SUCCESS: True, "schema": "eoere_selected_hardware_field_admission/v1",
                                        "case_id": case_id, "state_id": field["state_id"], "input_raw_sha256": "e"*64,
                                        "q_canonical_sha256": field["response"]["q_canonical_sha256"], "operator_bundle": bundle}
        forces["cases"].append(binding)
        domains = [{"member": "member-"+str(j), "span_mm": 2000.+j, "weak_column_domain_limit_mm": 1905.} for j in range(22)]
        components["cases"].append({**binding, "gross_member_stability": {"all_member_witness_records": domains}})
    for name, record in [("force-map", forces), ("component-map", components)]:
        pins = {name+"-source": "9"*64}
        registry[name] = pins
        record["source_union"] = {"record": {"path": name, "sha256": "8"*64}, "count": len(pins),
                                  "canonical_sha256": review.canonical_sha(pins)}
    verifications = []
    monkeypatch.setattr(review.current, "ref", ref)
    monkeypatch.setattr(review.current, "read", lambda r: copy.deepcopy(registry[r["path"]]))
    monkeypatch.setattr(review.current, "verify", lambda pins: verifications.append(copy.deepcopy(pins)))
    monkeypatch.setattr(review.current, "manifest", lambda: {**forces, "cases": []})
    return registry, forces, components, verifications


def test_six_case_intake_evaluates_each_own_state_and_preserves_unknown_acceptance(monkeypatch):
    registry, forces, components, verifications = install_saved_evidence(monkeypatch)
    result, raw = review.run()
    references = [review.own_ref(), review.current.ref(review.PACKET/"result.json"),
                  review.current.ref(review.PACKET/"components.json"),
                  forces["source_union"]["record"], components["source_union"]["record"]]
    expected = {**registry["force-map"], **registry["component-map"], **{r["path"]: r["sha256"] for r in references}}
    assert len(expected) == 7
    assert verifications == [expected, expected]
    assert result["cases"] == forces["cases"]
    assert [r["case_id"] for r in result["load_checks"]] == review.SEQUENCE
    assert set(raw) == set(review.SEQUENCE)
    assert set(result["recorded_hold_geometry"]) == {"A12", "K12", "A1"}
    assert result["equilibrium_wrench_reference_xyz_mm"] == [0., 750., 1100.]
    gaps = [r["maximum_absolute_gap_change"]["gap_change_mm"] for r in result["finite_arm_contact_probe"]["cases"]]
    assert gaps == pytest.approx([1.-math.cos(.1+.01*i) for i in range(6)])
    assert result["structural_acceptance"] is False
    assert result["complete_joint_resistance"] is None and result["finished_member_capacity"] is None
    assert result["screw_panel_exceedance_resolution_deferred_by_owner"] is True
    assert result["screw_panel_load_path_removed_or_capacity_accepted"] is False


@pytest.mark.parametrize("drift_phase", ["none", "before", "after"])
def test_real_source_verification_surrounds_calculations(monkeypatch, tmp_path, drift_phase):
    original_source = review.OWN.read_bytes()
    real_ref, real_verify, probe = review.current.ref, review.current.verify, review.contact_probe
    producer = tmp_path/"scripts/eoere_engineering_assessment.py"
    producer.parent.mkdir()
    producer.write_bytes(original_source)
    monkeypatch.setattr(review.current, "ROOT", tmp_path)
    monkeypatch.setattr(review, "OWN", producer)
    monkeypatch.setattr(review, "PACKET", tmp_path/"packet")
    registry, forces, components, verifications = install_saved_evidence(monkeypatch)
    sources = {}
    for name, record in [("force-map", forces), ("component-map", components)]:
        source = tmp_path/(name+"-source")
        source.write_text(name+" bytes")
        sources[name] = source
        pins = registry[name]
        pins[name+"-source"] = review.current.sha(source)
        record["source_union"]["canonical_sha256"] = review.canonical_sha(pins)
        (tmp_path/name).write_text(json.dumps(pins))
        record["source_union"]["record"] = real_ref(tmp_path/name)
    review.PACKET.mkdir()
    (review.PACKET/"result.json").write_text(json.dumps(forces))
    components["current_response"] = real_ref(review.PACKET/"result.json")
    (review.PACKET/"components.json").write_text(json.dumps(components))
    monkeypatch.setattr(review.current, "ref", real_ref)
    calculations = []

    def verify(pins):
        verifications.append(copy.deepcopy(pins))
        return real_verify(pins)

    def calculate(*args):
        calculations.append(args[0]["case_id"])
        result = probe(*args)
        if drift_phase == "after" and len(calculations) == 1:
            sources["component-map"].write_text("changed after admission")
        return result

    monkeypatch.setattr(review.current, "verify", verify)
    monkeypatch.setattr(review, "contact_probe", calculate)
    if drift_phase == "before":
        sources["force-map"].write_text("changed before admission")
    if drift_phase == "none":
        report, _ = review.run()
        assert report["all_input_sources_unchanged"] is True
    else:
        with pytest.raises(ValueError, match="source drift"):
            review.run()
    assert len(verifications) == (1 if drift_phase == "before" else 2)
    assert calculations == ([] if drift_phase == "before" else review.SEQUENCE)


@pytest.mark.parametrize("mutation", ["state", "union", "revision", "capacity", "admission", "reference"])
def test_intake_rejects_incompatible_evidence(monkeypatch, mutation):
    registry, forces, components, _ = install_saved_evidence(monkeypatch)
    if mutation == "state":
        components["cases"][1]["state_id"] = components["cases"][0]["state_id"]
    elif mutation == "union":
        forces["source_union"]["count"] += 1
    elif mutation == "revision":
        components["geometry_revision"] = "other"
    elif mutation == "capacity":
        forces["complete_joint_resistance"] = 1000.
    elif mutation == "admission":
        registry[review.SEQUENCE[0]+"-admission"][review.current.SUCCESS] = False
    else:
        registry[review.SEQUENCE[0]+"-chart"]["rigid_modes_reference_xyz_mm"][1] += 1.
    with pytest.raises(ValueError):
        review.run()
