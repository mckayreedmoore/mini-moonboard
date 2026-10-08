"""Small source/intake and hand section coupons; no candidate response exists."""
import copy
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("eoere_conditional_comparison", Path(__file__).with_name("comparison.py"))
unit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit)


def strip_coupon(Q=None):
    Q = np.eye(3) if Q is None else Q
    data = json.loads((unit.ROOT / unit.INPUT).read_bytes())
    data["fitting_basis_columns_xyz"] = Q.tolist()
    sources = {p: unit.DIRECT[p] for p in (unit.GUARDED, unit.INPUT)}
    descriptor = {"schema": "eoere_first_order_four_port_assembly_descriptor/v1", "body": "synthetic-fitting",
        "gravity_route": unit.ROUTE, "source_sha256": sources, "immutable_operator_snapshot_sha256": "f"*64,
        "own_fitting_scenario": data, "scenario_canonical_sha256": unit.canonical(data), "ports": []}
    response = {"schema": "eoere_four_port_assembly_seam_response/v1", "body": "synthetic-fitting",
        "root_recovery_uses_loaded_heel": True, "frozen_unloaded_model_response_used_for_gravity": False,
        "source_sha256": sources.copy(), "immutable_operator_snapshot_sha256": "f"*64,
        "port_actions": [], "strip_root_actions": [], "load_projection": {"route": unit.ROUTE},
        "per_flange_applied_strip_root_wrench_about_heel_n_nmm": {}}
    flange = {arm: np.zeros(6) for arm in ("arm-x", "arm-z")}
    for i, identifier in enumerate(unit.PORTS):
        arm, side = identifier.split("/")
        sign = -1 if side == "far-minus" else 1
        x = np.array([1., 0., 0.]) if arm == "arm-x" else np.array([0., 0., 1.])
        y = np.array([0., 1., 0.])
        B = Q @ np.column_stack([x, y, np.cross(x, y)])
        root, tip, point = Q @ (sign*22.225*y), Q @ (65.0875*x+sign*22.225*y), Q @ (65.0875*x+sign*25.4*y)
        F = B @ np.array([7.*sign, 2.*(i+1), -3.])
        M = B @ np.array([13.*(i+1), 17.*sign, -19.*(i+1)])
        fp, mp = -F, -M+np.cross(point-root, F)
        response["strip_root_actions"].append({"body": "synthetic-fitting", "port_id": identifier, "flange": arm,
            "point_xyz_mm": root.tolist(), "applied_to_strip_force_xyz_n": F.tolist(),
            "applied_to_strip_couple_at_root_xyz_nmm": M.tolist()})
        response["port_actions"].append({"body": "synthetic-fitting", "port_id": identifier, "point_xyz_mm": point.tolist(),
            "external_force_required_at_port_xyz_n": fp.tolist(), "external_couple_required_at_port_xyz_nmm": mp.tolist()})
        descriptor["ports"].append({"id": identifier, "flange": arm, "strip_root_xyz_mm": root.tolist(),
            "strip_tip_neutral_xyz_mm": tip.tolist(), "point_reference_xyz_mm": point.tolist()})
        flange[arm] += np.r_[F, M+np.cross(root, F)]
    response["per_flange_applied_strip_root_wrench_about_heel_n_nmm"] = {k: v.tolist() for k, v in flange.items()}
    response["load_projection"]["heel_wrench_n_nmm"] = sum(flange.values(), np.zeros(6)).tolist()
    response["loaded_root_wrench_minus_source_body_wrench_n_nmm"] = [0.]*6
    return response, descriptor


def circle_coupon(diameter=9.525):
    axis = {"id": "synthetic-axis", "diameter_mm": diameter, "point_xyz_mm": [1., 2., 3.], "direction_xyz": [1., 0., 0.]}
    row = {"axis_id": axis["id"], "body": "shaft/"+axis["id"], "elastic_section_diameter_mm": diameter,
        "bearing_contact_major_diameter_mm": diameter, "axis_point_xyz_mm": axis["point_xyz_mm"],
        "axis_direction_xyz": axis["direction_xyz"], "basis_axis_tangent1_tangent2_xyz": np.eye(3).tolist(),
        "body_root_and_delivered_shank_exposure_adopted": False, "shaft_interval_from_axis_point_mm": [0., 10.],
        "cuts": [{"station_from_axis_point_mm": 0., "point_xyz_mm": [1., 2., 3.],
                  "local_N_V1_V2_T_M1_M2_n_nmm": [11., -13., 17., -19., 23., -29.]}]}
    return row, axis


def test_source_only_current_census_and_pins():
    data = unit.source_contract()
    assert len(data["geometry"]["axes"]) == 100
    assert len(data["fitting_ids"]) == 22
    assert data["inputs"]["steel_fy_mpa"] is None
    unit.verify(data["source_sha256"])


def test_four_own_roots_hand_nvm_torsion_and_transport():
    result = unit.fitting_strip_comparisons(*strip_coupon())
    strip = result["strips"][0]
    a, b = strip["same_strip_endpoint_witnesses"]
    assert a["same_section_force_N_V1_V2_n"] == [-7., 2., -3.]
    assert a["same_section_moment_T_M1_M2_nmm"] == [13., -17., -19.]
    assert b["same_section_moment_T_M1_M2_nmm"] == pytest.approx([13., -17.-65.0875*3., -19.-65.0875*2.])
    A, Zy, Zz = 44.45*6.35, 44.45*6.35**2/6, 6.35*44.45**2/6
    sigma = 7/A+17/Zy+19/Zz
    tau = 1.5*math.hypot(2, 3)/A+13*6.35/a["torsion_rectangle"]["J_lower_mm4"]
    assert a["simultaneous_nominal_vm_bound_mpa"] == pytest.approx(math.hypot(sigma, math.sqrt(3)*tau), abs=1e-14)
    assert a["simultaneous_nominal_first_yield_bound_index"] is None
    assert result["full_flange_aggregate_stress_comparison"] is None


def test_proper_world_rotation_preserves_own_strip_values():
    angle = .37
    Q = np.array([[math.cos(angle), -math.sin(angle), 0.], [math.sin(angle), math.cos(angle), 0.], [0., 0., 1.]])
    a = unit.fitting_strip_comparisons(*strip_coupon())
    b = unit.fitting_strip_comparisons(*strip_coupon(Q))
    for x, y in zip(a["strips"], b["strips"], strict=True):
        assert x["nominal_gross_prismatic_field_governing_endpoint"]["simultaneous_nominal_vm_bound_mpa"] == pytest.approx(
            y["nominal_gross_prismatic_field_governing_endpoint"]["simultaneous_nominal_vm_bound_mpa"], abs=1e-14)


def test_conditional_fy_is_explicit_not_product_property():
    result = unit.fitting_strip_comparisons(*strip_coupon(), fy_scenario={"fy_mpa": 250., "material_basis": "unqualified toy steel", "scenario_id": "toy"})
    cut = result["strips"][0]["same_strip_endpoint_witnesses"][0]
    assert cut["simultaneous_nominal_first_yield_bound_index"] == cut["simultaneous_nominal_vm_bound_mpa"]/250.
    assert result["physical_product_fy_mpa"] is None


@pytest.mark.parametrize("mutation,match", [
    ("unloaded", "loaded-heel"), ("missing", "four unique"), ("body", "own action"),
    ("force", "equilibrium"), ("aggregate", "flange root"), ("scenario", "permitted reference pose"),
    ("source", "operator/source"), ("nan", "finite complete"),
])
def test_strip_intake_rejects_invalid_contract(mutation, match):
    r, d = strip_coupon()
    if mutation == "unloaded":
        r["root_recovery_uses_loaded_heel"] = False
    elif mutation == "missing":
        r["port_actions"].pop()
    elif mutation == "body":
        r["strip_root_actions"][0]["body"] = "other"
    elif mutation == "force":
        r["port_actions"][0]["external_couple_required_at_port_xyz_nmm"][1] += 1.
    elif mutation == "aggregate":
        r["per_flange_applied_strip_root_wrench_about_heel_n_nmm"]["arm-x"][4] += 1.
    elif mutation == "scenario":
        d["own_fitting_scenario"]["elastic_modulus_mpa"] = 210000.
        d["scenario_canonical_sha256"] = unit.canonical(d["own_fitting_scenario"])
    elif mutation == "source":
        r["source_sha256"][unit.INPUT] = "0"*64
    elif mutation == "nan":
        r["strip_root_actions"][0]["applied_to_strip_force_xyz_n"][1] = math.nan
    with pytest.raises(ValueError, match=match):
        unit.fitting_strip_comparisons(r, d)


@pytest.mark.parametrize("d", [9.525, 12.7])
def test_solid_circle_hand_combined_same_cut(d):
    result = unit.shaft_circle_comparisons(*circle_coupon(d))
    cut = result["section_scenarios"][0]["sampled_governing_same_cut"]
    A = math.pi*d*d/4
    sigma = 11/A+32*math.hypot(23, 29)/(math.pi*d**3)
    tau = 4*math.hypot(13, 17)/(3*A)+16*19/(math.pi*d**3)
    assert cut["same_section_nominal_stress_envelope_mpa"] == pytest.approx(math.hypot(sigma, math.sqrt(3)*tau), abs=1e-14)
    assert cut["same_section_nominal_first_yield_index"] is None


def test_circle_governs_one_same_cut_and_explicit_reduced_scenario():
    row, axis = circle_coupon()
    row["cuts"] = [{"station_from_axis_point_mm": 0., "point_xyz_mm": [1., 2., 3.],
                    "local_N_V1_V2_T_M1_M2_n_nmm": [100., 0., 0., 0., 0., 0.]},
                   {"station_from_axis_point_mm": 10., "point_xyz_mm": [11., 2., 3.],
                    "local_N_V1_V2_T_M1_M2_n_nmm": [0., 0., 0., 20., 0., 0.]}]
    result = unit.shaft_circle_comparisons(row, axis, circle_scenarios=[{"id": "toy-reduced", "diameter_mm": 8., "section_basis": "caller toy; not delivered root"}])
    cut = result["section_scenarios"][0]["sampled_governing_same_cut"]
    assert cut["same_cut_N_V1_V2_T_M1_M2_n_nmm"] in [r["local_N_V1_V2_T_M1_M2_n_nmm"] for r in row["cuts"]]
    assert result["actual_thread_root_or_occupancy_adopted"] is False
    assert len(result["section_scenarios"]) == 2


def test_shaft_axis_cut_and_scenario_guards():
    row, axis = circle_coupon()
    forged = copy.deepcopy(row)
    forged["cuts"][0]["point_xyz_mm"][2] += 1.
    with pytest.raises(ValueError, match="same-cut point"):
        unit.shaft_circle_comparisons(forged, axis)
    with pytest.raises(ValueError, match="conditional material basis"):
        unit.shaft_circle_comparisons(row, axis, fy_scenario={"fy_mpa": 600., "material_basis": "", "scenario_id": "unqualified"})
    forged = copy.deepcopy(row)
    forged["cuts"].append(copy.deepcopy(forged["cuts"][0]))
    with pytest.raises(ValueError, match="unique cut station"):
        unit.shaft_circle_comparisons(forged, axis)
    forged["elastic_section_diameter_mm"] = 12.
    with pytest.raises(ValueError, match="identity/diameter"):
        unit.shaft_circle_comparisons(forged, axis)
