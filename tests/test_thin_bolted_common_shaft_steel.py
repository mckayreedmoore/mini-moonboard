"""Independent wrench, own-capture and simultaneous circular-stress coupons."""

import copy
import math

import numpy as np
import pytest

from scripts import thin_bolted_common_shaft_steel as consumer
from scripts import thin_bolted_steel_resistance as frozen


def steel_port_fixture():
    # Unequal ports on one physical shaft. Nonzero free couples are deliberate.
    layout = {"installed_axes": [{"id": "shared", "attachments": [
        {"angle_id": "left", "flange": "beam", "receiver": "wood-left", "entry_xyz_mm": [0., 0., 0.]},
        {"angle_id": "right", "flange": "post", "receiver": "wood-right", "entry_xyz_mm": [10., 0., 0.]},
    ]}]}
    bearings, captures = [], []
    for host, flange, points, forces, couples in (
        ("left", "beam", [[-2., 0., 0.], [-1., 0., 0.]], [[0., 4., 0.], [0., 6., 0.]], [[1., 0., 2.], [2., 0., 3.]]),
        ("right", "post", [[11., 0., 0.], [12., 0., 0.]], [[0., -3., 0.], [0., -4., 0.]], [[4., 0., 5.], [5., 0., 6.]]),
    ):
        for i, (point, force, couple) in enumerate(zip(points, forces, couples, strict=True)):
            bearings.append({"id": f"{host}-{i}", "axis_id": "shared", "second": host,
                "surface_material": "steel", "flange": flange, "point_xyz_mm": point,
                "force_on_second_xyz_n": force, "moment_on_second_at_point_xyz_nmm": couple})
        captures.append({"id": host + "-capture", "axis_id": "shared", "second": host,
            "end": {"flange": flange}, "host_support_point_xyz_mm": [-3., 0., 0.] if host == "left" else [13., 0., 0.],
            "force_on_second_xyz_n": [20., 0., 0.] if host == "left" else [-30., 0., 0.],
            "moment_on_second_at_point_xyz_nmm": [0., 7., 0.] if host == "left" else [0., 8., 0.]})
    return layout, bearings, captures


def test_transport_wrench_retains_arm_and_independent_free_couple():
    force, moment = consumer.transport_wrench([0., 3., 4.], [5., 6., 7.], [2., 0., 0.], [0., 0., 0.])
    assert force == pytest.approx([0., 3., 4.])
    assert moment == pytest.approx([5., -2., 13.])
    _, returned = consumer.transport_wrench(force, moment, [0., 0., 0.], [2., 0., 0.])
    assert returned == pytest.approx([5., 6., 7.])


def test_shared_ports_are_unequal_signed_wrenches_without_capacity_summing():
    ports = consumer.aggregate_steel_ports(*steel_port_fixture())
    assert ports[0]["force_on_steel_xyz_n"] == pytest.approx([20., 10., 0.])
    assert ports[0]["moment_on_steel_at_point_xyz_nmm"] == pytest.approx([3., 7., -9.])
    assert ports[1]["force_on_steel_xyz_n"] == pytest.approx([-30., -7., 0.])
    assert ports[1]["moment_on_steel_at_point_xyz_nmm"] == pytest.approx([9., 8., 0.])
    assert all(row["opposed_wood_or_angle_action_inferred"] is False for row in ports)
    translated = consumer.api_counterwrenches(ports, {"state_id": "one", "case_id": "load", "accessory_placement": "rear"})
    assert translated[0]["moment_on_receiver_at_point_xyz_nmm"] == pytest.approx([-3., -7., 9.])
    assert translated[0]["equals_actual_wood_receiver_reaction"] is False


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "flange", "foreign-steel"])
def test_reduction_rejects_incomplete_or_misidentified_physical_actions(mutation):
    layout, bearings, captures = steel_port_fixture()
    if mutation == "missing":
        bearings.pop()
    elif mutation == "duplicate":
        bearings.append(copy.deepcopy(bearings[0]))
    elif mutation == "flange":
        captures[0]["end"]["flange"] = "post"
    else:
        bearings[0]["second"] = "foreign-angle"
    with pytest.raises(ValueError):
        consumer.aggregate_steel_ports(layout, bearings, captures)


def washer_fixture():
    methods = {"washer_reference_inputs": [], "washer_bending_profiles": {"old": {
        "assumed_circular_bearing_diameter_mm": 19.05,
        "unit_axial_two_face_bending": {"required_fy_mpa_at_sampled_bending_first_yield": .1}}}}
    captures = []
    for end, role, host, force, direction, support in (
        ("head", "head_washer", "angle", 2., [-1., 0., 0.], "steel"),
        ("nut", "nut_washer", "wood", 7., [1., 0., 0.], "wood"),
    ):
        methods["washer_reference_inputs"].append({"axis_id": "one", "role": role,
            "support_material": support, "bearing_circle_sensitivity_profile_ids": ["old"],
            "nominal_wood_annulus_reference": {"wood_bearing_reference_lbf": 10.} if support == "wood" else None})
        captures.append({"state_id": "fresh", "axis_id": "one", "second": host,
            "end": {"end": end, "direction_on_shaft_xyz": direction}, "compression_n": force,
            "force_on_first_xyz_n": (force * np.array(direction)).tolist(), "point_xyz_mm": [0., 0., 0.],
            "host_support_point_xyz_mm": [1., 0., 0.]})
    head = {"ends": [{"axis_id": "one", "role": "head_washer", "profile_id": "small-head"}],
        "profiles": {"small-head": {"unit_axial_two_face_bending": {"required_fy_mpa_at_sampled_bending_first_yield": .2}}}}
    return methods, head, captures


def test_each_washer_uses_own_capture_and_changed_head_circle_stays_head_only():
    head, nut = consumer.own_washer_states(*washer_fixture())
    assert head["own_capture_model_axial_force_n"] == 2.
    assert nut["own_capture_model_axial_force_n"] == 7.
    assert [row["required_fy_mpa_own_capture_axial_component"] for row in head["reused_unit_plate_sensitivities"]] == pytest.approx([.2, .4])
    assert [row["required_fy_mpa_own_capture_axial_component"] for row in nut["reused_unit_plate_sensitivities"]] == pytest.approx([.7])
    assert head["nominal_occupied_full_wood_annulus_axial_reference_index"] is None
    assert nut["nominal_occupied_full_wood_annulus_axial_reference_index"] == pytest.approx(7. / (10. * 4.4482216152605))
    assert head["combined_washer_index"] is None
    assert head["unknown_own_end_moments_zero_filled"] is False


@pytest.mark.parametrize("mutation", ["sign", "transverse", "missing", "duplicate", "nonunit"])
def test_own_capture_rejects_force_scalar_direction_and_census_errors(mutation):
    methods, head, captures = washer_fixture()
    if mutation == "sign":
        captures[0]["force_on_first_xyz_n"] = [2., 0., 0.]
    elif mutation == "transverse":
        captures[0]["force_on_first_xyz_n"][1] = 1.
    elif mutation == "missing":
        captures.pop()
    elif mutation == "duplicate":
        captures.append(copy.deepcopy(captures[0]))
    else:
        captures[0]["end"]["direction_on_shaft_xyz"] = [-2., 0., 0.]
    with pytest.raises(ValueError):
        consumer.own_washer_states(methods, head, captures)


def cut_fixture():
    return [{"axis_id": "shaft-one", "body": "shaft/shaft-one", "elastic_section_diameter_mm": 10., "cuts": [{
        "station_from_axis_point_mm": 20., "point_xyz_mm": [20., 0., 0.],
        "local_N_V1_V2_T_M1_M2_n_nmm": [100., 3., 4., 200., 300., 400.]}]}]


def test_circular_reference_uses_simultaneous_actions_and_explicit_root_scenario():
    rows = consumer.shaft_section_references(cut_fixture(), {"shaft-one": [{
        "id": "caller-root", "diameter_mm": 8., "section_basis": "unmeasured caller sensitivity, not actual ASME root"}]})
    scenarios = rows[0]["section_scenarios"]
    for scenario, d in zip(scenarios, [10., 8.], strict=True):
        area = math.pi * d**2 / 4.
        sigma = 100. / area + 32. * 500. / (math.pi * d**3)
        tau = 4. * 5. / (3. * area) + 16. * 200. / (math.pi * d**3)
        expected = math.sqrt(sigma**2 + 3. * tau**2)
        witness = scenario["sampled_governing_section"]
        assert witness["same_section_nominal_stress_envelope_mpa"] == pytest.approx(expected)
        assert witness["same_section_nominal_first_yield_index"] == pytest.approx(expected / consumer.GRADE5_FY_MPA)
    assert rows[0]["NDS_fyb_inferred_from_tensile_yield"] is False
    assert rows[0]["complete_joint_acceptance"] is False


@pytest.mark.parametrize("mutation", ["no-basis", "foreign", "duplicate-shaft", "duplicate-scenario"])
def test_circle_scenario_needs_unique_identity_and_explicit_geometric_basis(mutation):
    rows = cut_fixture()
    caller = {"shaft-one": [{"id": "root", "diameter_mm": 8., "section_basis": "caller sensitivity"}]}
    if mutation == "no-basis":
        caller["shaft-one"][0].pop("section_basis")
    elif mutation == "foreign":
        caller["foreign"] = []
    elif mutation == "duplicate-shaft":
        rows.append(copy.deepcopy(rows[0]))
    else:
        caller["shaft-one"][0]["id"] = "elastic_model_circle"
    with pytest.raises(ValueError):
        consumer.shaft_section_references(rows, caller)


def test_frozen_flange_accepts_free_torsion_couple_and_marks_envelope_incomplete():
    # A pure free couple along the beam leg would vanish if transport omitted M.
    fitting = {"angle_id": "B104ZN_synthetic", "origin_xyz_mm": [0., 0., 0.],
        "u_xyz": [1., 0., 0.], "v_xyz": [0., 1., 0.], "w_xyz": [0., 0., 1.]}
    row = {"point_xyz_mm": [80., 0., 0.], "force_on_steel_xyz_n": [0., 0., 0.],
        "moment_on_steel_at_point_xyz_nmm": [100., 0., 0.]}
    result = frozen.flange_reference(fitting, "beam", [row])
    assert result["steel_torsion_complete"] is False
    assert any(abs(section["torsion_nmm"]) == 100. for section in result["sections"])
    assert result["complete_joint_acceptance"] is False


def cut_replay_fixture():
    # Hand answer: head gravity at x=-2, bore force/free torque at x=3.
    # At s<=3: Vz=1, My=s+2. At s>3: add Vy=-2, T=-5, Mz=2(s-3).
    geometry = [{"axis_id": "one", "body": "shaft/one", "point": [0., 0., 0.],
        "basis": np.eye(3).tolist(), "diameter_mm": 10., "shaft_interval_mm": [0., 10.],
        "surfaces": [], "ends": [{"support_s_mm": 0., "pressure_face_s_mm": 0.},
                                    {"support_s_mm": 10., "pressure_face_s_mm": 10.}]}]
    stations = sorted({*np.linspace(0., 10., 33), 0., 10., 3. - 1e-7, 3. + 1e-7, 10. - 1e-7})
    cuts = [{"station_from_axis_point_mm": float(s), "point_xyz_mm": [float(s), 0., 0.],
             "local_N_V1_V2_T_M1_M2_n_nmm": [0., -2. if s > 3. else 0., 1.,
                                            -5. if s > 3. else 0., float(s + 2.), 2. * (s - 3.) if s > 3. else 0.]}
            for s in stations]
    demand = {"parameters": {"shaft_diameter_scale": .9, "shaft_max_segment_mm": 25.},
        "body_applied_loads": [{"body": "shaft/one", "point_xyz_mm": [-2., 0., 0.], "force_xyz_n": [0., 0., -1.]}],
        "common_shaft_bearing_actions": [{"first": "shaft/one", "point_xyz_mm": [3., 0., 0.],
            "force_on_first_xyz_n": [0., 2., 0.], "moment_on_first_at_point_xyz_nmm": [5., 0., 0.]}],
        "shaft_end_capture_actions": [{"first": "shaft/one", "point_xyz_mm": [10., 0., 0.],
            "force_on_first_xyz_n": [4., 0., 0.], "moment_on_first_at_point_xyz_nmm": [0., 0., 0.]}],
        "common_shaft_section_cut_actions": [{"axis_id": "one", "body": "shaft/one",
            "axis_point_xyz_mm": [0., 0., 0.], "axis_direction_xyz": [1., 0., 0.],
            "basis_axis_tangent1_tangent2_xyz": np.eye(3).tolist(), "shaft_interval_from_axis_point_mm": [0., 10.],
            "mesh_stations_from_axis_point_mm": [0., 10.], "elastic_section_diameter_mm": 9.,
            "bearing_contact_major_diameter_mm": 10., "cuts": cuts}]}
    return demand, geometry


def test_cut_replay_keeps_outside_head_gravity_and_every_force_arm_free_couple():
    result = consumer.verify_shaft_cuts(*cut_replay_fixture())
    assert result["independent_same_cut_equilibrium_replay_pass"] is True
    assert result["maximum_force_difference_n"] == pytest.approx(0.)
    assert result["maximum_free_moment_difference_nmm"] < 1e-12


@pytest.mark.parametrize("mutation", ["moment", "force", "omit", "duplicate", "basis", "axis", "diameter", "mesh"])
def test_cut_replay_rejects_changed_or_omitted_sections_and_datums(mutation):
    demand, geometry = cut_replay_fixture()
    row = demand["common_shaft_section_cut_actions"][0]
    if mutation == "moment":
        row["cuts"][0]["local_N_V1_V2_T_M1_M2_n_nmm"][4] = 0.
    elif mutation == "force":
        row["cuts"][0]["local_N_V1_V2_T_M1_M2_n_nmm"][2] = 0.
    elif mutation == "omit":
        row["cuts"].pop()
    elif mutation == "duplicate":
        demand["common_shaft_section_cut_actions"].append(copy.deepcopy(row))
    elif mutation == "basis":
        row["basis_axis_tangent1_tangent2_xyz"][1] = [0., 0., 1.]
    elif mutation == "axis":
        row["axis_point_xyz_mm"][0] = 1.
    elif mutation == "diameter":
        row["elastic_section_diameter_mm"] = 10.
    else:
        row["mesh_stations_from_axis_point_mm"] = [0., 5., 10.]
    with pytest.raises(ValueError):
        consumer.verify_shaft_cuts(demand, geometry)
