"""Pure conditional comparisons for the successor's declared gross sections.

No field reader, admission, stiffness, CAD, q or solve is provided. A future
caller must authenticate its new field and recover own same-cut actions first.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import thin_bolted_flange_torsion as torsion
from scripts import thin_bolted_steel_resistance as steel

OWN = Path(__file__).resolve()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
PRODUCT = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/product-inputs-final.json"
GEOMETRY = LEAF + "/occupied-geometry-v2-complete/geometry.json"
SCENE = LEAF + "/occupied-geometry-v2-complete/scene.json"
INPUT = LEAF + "/four-port-method-v1/inputs.json"
ROUTE = "source-point-wrench-through-internal-rigid-heel-v1"
GUARDED = LEAF + "/four-port-method-v1/guarded_assembly_interface.py"
FROZEN = {
    "scripts/thin_bolted_flange_torsion.py": "48e3181f65772cb2d21be6687a011eaeba6a35491b6299cd179759f66ffc6871",
    "scripts/thin_bolted_steel_resistance.py": "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602",
    "mini_moonboard/wood_joint_bolt_resistance.py": "488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166",
}
DIRECT = {**FROZEN,
    GEOMETRY: "05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd",
    SCENE: "8599fca392ccf2ec366ab4c39e4c1d74be89da50167edc7c760e5cb73c524c4a",
    PRODUCT: "dd662e681871576d0a76666e9370d4359f7e96e0a2ad5f9710553895f53a5309",
    INPUT: "a938b41e53f5708c74e30ec1f021e894513ab6be4b1c6df390bababcfeebbd8e",
    GUARDED: "a2b5ef4f45d05f3a29c428583238c3ead927ac7ae259a6c4a8d7c63ded3d0ad8",
    LEAF + "/four-port-method-v1/assembly_interface.py": "4103015c05405e930e10c90edb5e147dd9d1ec2fb0575f17e3e4efc01a6cb66b",
    LEAF + "/four-port-method-v1/four_port.py": "8482d5f3f1d01eee9141db2bbeef5237f87cb7d78f00619749604c0a23f57567",
    "scripts/thin_bolted_common_shaft.py": "0ff8c52a36f168cba0bd3fed2d592daa9e5d9de5facbc650b151f64c2f23f4eb",
    "uv.lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
}
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PORTS = ("arm-x/far-minus", "arm-x/far-plus", "arm-z/far-minus", "arm-z/far-plus")
LIMITS = [
    "Gross half-strip fields fill all near and far factory holes; no actual holed-plate stress bound.",
    "Four strips have independent longitudinal response; summed flange wrenches cannot replace their own comparisons.",
    "Actual formed heel radius, thinning, restrained warping, plate continuity, local load introduction, contact and prying are unresolved.",
    "Collector gravity is the declared point-wrench interpolation, not actual distributed fitting weight.",
    "Shaft nominal circles do not establish delivered shank, thread root/occupancy, notch, head, nut, stripping or seating resistance.",
    "Product Fy/Fu and bolt grade are unverified; nominal first-yield markers are not code-qualified allowable joint strengths.",
    "No complete joint, physical demand bound, pressure, floor, timber or fabrication acceptance.",
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source changed: " + path)


def array(value, shape):
    out = np.asarray(value, dtype=float)
    require(out.shape == shape and np.isfinite(out).all(), "finite complete vector/matrix required")
    return out


def proper(value):
    out = array(value, (3, 3))
    require(np.max(abs(out.T @ out - np.eye(3))) < 1e-10 and abs(np.linalg.det(out)-1.) < 1e-10,
            "proper supplied section basis required; no reorthogonalization")
    return out


def yield_scenario(value):
    if value is None:
        return None, None, None
    require(set(value) == {"fy_mpa", "material_basis", "scenario_id"}, "explicit conditional Fy scenario schema required")
    fy = steel.number(value["fy_mpa"], "conditional Fy", positive=True)
    require(all(isinstance(value[k], str) and value[k].strip() for k in ("material_basis", "scenario_id")),
            "conditional material basis and scenario ID required")
    return fy, value["material_basis"], value["scenario_id"]


def fitting_strip_comparisons(response, descriptor, *, fy_scenario=None):
    """Own root+neutral-tip envelopes for each unloaded prismatic half-strip.

    The nominal stress envelope is convex along this constant-section interval:
    force/torsion are constant, bending is affine. Its maximum occurs at an
    endpoint. This bounds this declared gross strip field, not an actual angle.
    """
    verify(FROZEN)
    own_sources = {path: DIRECT[path] for path in (GUARDED, INPUT)}
    verify(own_sources)
    fy, material, scenario_id = yield_scenario(fy_scenario)
    require(descriptor["schema"] == "eoere_first_order_four_port_assembly_descriptor/v1"
            and response["schema"] == "eoere_four_port_assembly_seam_response/v1", "own four-port schemas required")
    body = descriptor["body"]
    require(isinstance(body, str) and body and response["body"] == body, "own fitting body identity required")
    require(response["root_recovery_uses_loaded_heel"] is True
            and response["frozen_unloaded_model_response_used_for_gravity"] is False
            and descriptor["gravity_route"] == response["load_projection"]["route"] == ROUTE,
            "loaded-heel collector recovery required")
    require(response["immutable_operator_snapshot_sha256"] == descriptor["immutable_operator_snapshot_sha256"]
            and response["source_sha256"] == descriptor["source_sha256"]
            and all(response["source_sha256"].get(p) == h for p, h in own_sources.items()), "own immutable operator/source join required")
    data = descriptor["own_fitting_scenario"]
    require(descriptor["scenario_canonical_sha256"] == canonical(data), "own fitting scenario hash differs")
    declared = json.loads((ROOT / INPUT).read_bytes())
    require({k: v for k, v in data.items() if k not in ("heel_reference_xyz_mm", "fitting_basis_columns_xyz")} ==
            {k: v for k, v in declared.items() if k not in ("heel_reference_xyz_mm", "fitting_basis_columns_xyz")},
            "own fitting scenario differs beyond its permitted reference pose")
    require(tuple(data[k] for k in ("arm_length_mm", "width_mm", "thickness_mm", "far_station_mm", "transverse_half_pitch_mm"))
            == (88.9, 88.9, 6.35, 65.0875, 25.4) and data["steel_fy_mpa"] is None,
            "exact own inch-centered geometry and unknown product Fy required")
    Q, origin = proper(data["fitting_basis_columns_xyz"]), array(data["heel_reference_xyz_mm"], (3,))
    table = {}
    for key in ("port_actions", "strip_root_actions"):
        rows = response[key]
        require(len(rows) == 4 and {r["port_id"] for r in rows} == set(PORTS)
                and all(r["body"] == body for r in rows), "all four unique own action ports required")
        table[key] = {r["port_id"]: r for r in rows}
    require(len(descriptor["ports"]) == 4 and {r["id"] for r in descriptor["ports"]} == set(PORTS),
            "all four unique descriptor ports required")
    ports = {r["id"]: r for r in descriptor["ports"]}
    sums = {arm: np.zeros(6) for arm in ("arm-x", "arm-z")}
    results = []
    for identifier in PORTS:
        arm, side = identifier.split("/")
        sign = -1 if side == "far-minus" else 1
        along = np.array([1., 0., 0.]) if arm == "arm-x" else np.array([0., 0., 1.])
        across = np.array([0., 1., 0.])
        basis = proper(Q @ np.column_stack([along, across, np.cross(along, across)]))
        root = origin + Q @ (sign * 88.9/4 * across)
        neutral_tip = root + Q @ (65.0875 * along)
        point = origin + Q @ (65.0875 * along + sign * 25.4 * across)
        r, p, port = table["strip_root_actions"][identifier], table["port_actions"][identifier], ports[identifier]
        require(r["flange"] == arm and port["flange"] == arm, "own strip flange identity differs")
        for supplied, expected in ((r["point_xyz_mm"], root), (p["point_xyz_mm"], point),
                                   (port["strip_root_xyz_mm"], root), (port["point_reference_xyz_mm"], point),
                                   (port["strip_tip_neutral_xyz_mm"], neutral_tip)):
            require(np.max(abs(array(supplied, (3,))-expected)) < 1e-8, "own strip/port datum differs")
        F = array(r["applied_to_strip_force_xyz_n"], (3,))
        M = array(r["applied_to_strip_couple_at_root_xyz_nmm"], (3,))
        fp = array(p["external_force_required_at_port_xyz_n"], (3,))
        mp = array(p["external_couple_required_at_port_xyz_nmm"], (3,))
        require(np.max(abs(F+fp)) <= 1e-7 and np.max(abs(M+mp+np.cross(point-root, fp))) <= 1e-4,
                "own strip root/tip equilibrium differs")
        sums[arm] += np.r_[F, M+np.cross(root-origin, F)]
        samples = []
        for label, cut in (("root", root), ("neutral-tip", neutral_tip)):
            local_f, local_m = basis.T @ F, basis.T @ (M+np.cross(root-cut, F))
            stress = torsion.simultaneous_section_bound(width_mm=44.45, thickness_mm=6.35,
                removed_center_width_mm=0., force_local_n=local_f, moment_local_nmm=local_m,
                fy_mpa=fy, scenario="gross_rectangle")
            samples.append({"cut_id": label, "point_xyz_mm": cut.tolist(), **stress})
        results.append({"port_id": identifier, "flange": arm, "basis_columns_xyz": basis.tolist(),
            "strip_width_mm": 44.45, "thickness_mm": 6.35, "interval_length_mm": 65.0875,
            "same_strip_endpoint_witnesses": samples,
            "nominal_gross_prismatic_field_governing_endpoint": max(samples, key=lambda row: row["simultaneous_nominal_vm_bound_mpa"]),
            "all_factory_holes_filled_in_nominal_field": True, "actual_holed_strip_field_bound": False})
    supplied_flange = response["per_flange_applied_strip_root_wrench_about_heel_n_nmm"]
    require(set(supplied_flange) == set(sums), "both own flange resultants required")
    for key, value in sums.items():
        require(np.max(abs(value-array(supplied_flange[key], (6,)))) <= 1e-4, "flange root wrench transport differs")
    residual = sum(sums.values(), np.zeros(6))-array(response["load_projection"]["heel_wrench_n_nmm"], (6,))
    require(np.max(abs(residual)) <= 1e-4
            and np.max(abs(residual-array(response["loaded_root_wrench_minus_source_body_wrench_n_nmm"], (6,)))) <= 1e-4,
            "source collector body wrench differs from loaded roots")
    verify(FROZEN)
    verify(own_sources)
    return {"body": body, "strips": results, "conditional_fy_mpa": fy, "material_basis": material,
            "fy_scenario_id": scenario_id, "physical_product_fy_mpa": None,
            "flange_root_resultants_diagnostic_only_n_nmm": {k: v.tolist() for k, v in sums.items()},
            "full_flange_aggregate_stress_comparison": None, "limits": LIMITS,
            "source_field_admission_performed_here": False, "complete_joint_acceptance": False}


def shaft_circle_comparisons(shaft, expected_axis, *, fy_scenario=None, circle_scenarios=()):
    """Reuse signed same-cut circular envelopes; actual thread root is unknown."""
    verify(FROZEN)
    fy, material, scenario_id = yield_scenario(fy_scenario)
    identifier, diameter = expected_axis["id"], expected_axis["diameter_mm"]
    require(diameter in (9.525, 12.7) and shaft["axis_id"] == identifier and shaft["body"] == "shaft/"+identifier
            and shaft["elastic_section_diameter_mm"] == shaft["bearing_contact_major_diameter_mm"] == diameter,
            "own nominal shaft identity/diameter differs")
    point = array(expected_axis["point_xyz_mm"], (3,))
    direction = array(expected_axis["direction_xyz"], (3,))
    require(np.linalg.norm(direction) > 0., "nonzero source shaft direction required")
    direction /= np.linalg.norm(direction)
    basis = proper(array(shaft["basis_axis_tangent1_tangent2_xyz"], (3, 3)).T).T
    require(np.max(abs(array(shaft["axis_point_xyz_mm"], (3,))-point)) < 1e-8
            and np.max(abs(array(shaft["axis_direction_xyz"], (3,))-direction)) < 1e-10
            and np.max(abs(basis[0]-direction)) < 1e-10
            and shaft["body_root_and_delivered_shank_exposure_adopted"] is False,
            "source shaft axis/chart or delivered-section scope differs")
    low, high = array(shaft["shaft_interval_from_axis_point_mm"], (2,))
    require(low < high and shaft["cuts"], "own finite shaft interval and nonempty same-cut samples required")
    scenarios = [{"id": "nominal_model_circle", "diameter_mm": diameter,
                  "section_basis": "Unqualified uniform circular elastic model diameter; delivered section/threads unknown"}, *circle_scenarios]
    require(len({r["id"] for r in scenarios}) == len(scenarios), "unique explicit circle scenarios required")
    own = []
    for section in scenarios:
        require(isinstance(section["id"], str) and section["id"].strip()
                and isinstance(section["section_basis"], str) and section["section_basis"].strip(), "circle scenario ID and geometric basis required")
        d = steel.number(section["diameter_mm"], "conditional circle diameter", positive=True)
        require(d <= diameter, "conditional reduced circle cannot exceed source nominal model diameter")
        samples, stations = [], set()
        for cut in shaft["cuts"]:
            station = steel.number(cut["station_from_axis_point_mm"], "own cut station")
            require(low <= station <= high and station not in stations, "own in-interval unique cut station required")
            stations.add(station)
            cut_point = array(cut["point_xyz_mm"], (3,))
            require(np.max(abs(cut_point-(point+station*direction))) < 1e-7, "same-cut point/station differs")
            action = array(cut["local_N_V1_V2_T_M1_M2_n_nmm"], (6,))
            value = steel.bolt_section_reference(force_n=action[:3], moment_nmm=action[3:], diameter_mm=d,
                fy_mpa=fy, material_basis=material, section_basis=section["section_basis"])
            samples.append({"station_from_axis_point_mm": station, "point_xyz_mm": cut_point.tolist(),
                "same_cut_N_V1_V2_T_M1_M2_n_nmm": action.tolist(), **value})
        own.append({"section_scenario": section, "sample_count": len(samples),
            "sampled_governing_same_cut": max(samples, key=lambda row: row["same_section_nominal_stress_envelope_mpa"])})
    verify(FROZEN)
    return {"axis_id": identifier, "body": shaft["body"], "section_scenarios": own,
            "conditional_fy_mpa": fy, "material_basis": material, "fy_scenario_id": scenario_id,
            "actual_thread_root_or_occupancy_adopted": False, "continuous_station_extrema_checked_here": False,
            "same_cut_external_action_replay_or_field_admission_performed_here": False,
            "NDS_fyb_inferred_from_tensile_yield": False, "complete_joint_acceptance": False, "limits": LIMITS}


def source_contract():
    """Authenticate saved inputs only; return full pin union for caller reuse."""
    direct = {**DIRECT, str(OWN.relative_to(ROOT)): LOADED_SHA,
              str(OWN.with_name("test_comparison.py").relative_to(ROOT)): sha(OWN.with_name("test_comparison.py"))}
    verify(direct)
    geometry, scene, product, inputs = [json.loads((ROOT / p).read_bytes()) for p in (GEOMETRY, SCENE, PRODUCT, INPUT)]
    pins = dict(direct)
    for obj in (geometry, product):
        for path, digest in obj["source_sha256"].items():
            require(path not in pins or pins[path] == digest, "contradictory source pin")
            pins[path] = digest
    verify(pins)
    axes = geometry["axes"]
    ids = [r["id"] for r in axes]
    counts = Counter(r["diameter_mm"] for r in axes)
    require(len(ids) == len(set(ids)) == 100 and counts == {9.525: 96, 12.7: 4}, "exact successor shaft census required")
    fittings = [r["id"] for r in scene["solids"] if r["fabrication"]["kind"] == "bracket"]
    require(len(fittings) == len(set(fittings)) == geometry["counts"]["bracket"] == 22
            and geometry["counts"]["factory_holes"] == 176 and geometry["counts"]["installed_factory_holes"] == 88,
            "exact current fitting/hole census required")
    require(tuple(geometry["scenario"][k] for k in ("leg_mm", "width_mm", "thickness_mm")) == (88.9, 88.9, 6.35)
            and tuple(inputs[k] for k in ("arm_length_mm", "width_mm", "thickness_mm")) == (88.9, 88.9, 6.35)
            and inputs["steel_fy_mpa"] is None and inputs["elastic_modulus_mpa"] == 200000., "own scenario join differs")
    verify(pins)
    return {"direct_pins": direct, "source_sha256": pins, "geometry": geometry, "scene": scene, "inputs": inputs,
            "source_pin_union_canonical_sha256": canonical(pins), "fitting_ids": fittings}


def prepare():
    data = source_contract()
    pins = data["source_sha256"]
    report = {"schema": "eoere_conditional_steel_shaft_comparison_preparation/v1",
        "status": "PURE_METHOD_PREPARED_PENDING_INDEPENDENT_REVIEW", "source_sha256": data["direct_pins"],
        "referenced_source_map_paths": [GEOMETRY, PRODUCT], "source_pin_union_count": len(pins),
        "source_pin_union_canonical_sha256": canonical(pins), "source_pins_before_after_unchanged": True,
        "input_geometry_counts": data["geometry"]["counts"], "shaft_diameter_count": {"9.525_mm": 96, "12.7_mm": 4},
        "fitting_ids_canonical_sha256": canonical(data["fitting_ids"]), "own_strip_scenario_input": INPUT,
        "comparison_geometry": {"arm_length_mm": 88.9, "fitting_width_mm": 88.9, "thickness_mm": 6.35,
            "half_strip_width_mm": 44.45, "root_to_neutral_tip_mm": 65.0875,
            "near_unused_hole_station_mm": 23.8125, "far_used_hole_station_mm": 65.0875,
            "hole_diameter_mm": 10., "hole_to_half_strip_centroid_offset_mm": 3.175},
        "steel_elastic_analogy_mpa": 200000., "product_steel_fy_mpa": None, "product_steel_fu_mpa": None,
        "bolt_grade_or_fy_adopted": None, "optional_fy_contract": "Caller-only {fy_mpa, material_basis, scenario_id}; NULL by default; no blanket ASD factor or joint allowable",
        "future_consumer_contract": [
            "Actual distinct successor gate must return PASS on exact raw field bytes/state before any action vector is consumed; historical132/62-body gates are incompatible.",
            "Bind actual input/geometry/source/map/operator hashes and top-state table canonical hashes; common recovery does not supply per-cut state labels.",
            "Exactly22 source fitting descriptors plus22 loaded four-port responses: four unique own roots/tip ports each, loaded-heel recovery and same immutable operator/source snapshot.",
            "Use each of88 independent half-strip root+neutral-tip fields; preserve both heel-transported flange wrenches without substituting their sum for strip stresses.",
            "Exactly100 own shaft rows joined to actual physical axes:96 nominal9.525 and4 nominal12.7; fresh cuts retain station_from_axis_point_mm, point and all signed N/V/M/T at that same cut.",
            "New independent gate must replay source external shaft loads, captures/bearings/gravity, cut census and local basis; this pure helper cannot authenticate those loads.",
            "No old centered two-ligament proxy: each successor half-strip has an eccentric hole and multiple rows; actual holed stress field needs its own method.",
        ], "limits": LIMITS,
        "candidate_field_q_force_CAD_K_native_or_solve_executed": False,
        "production_consumer_or_candidate_readiness": False, "physical_or_fabrication_acceptance": False,
        "tools": {"python": platform.python_version(), "numpy": importlib.metadata.version("numpy")},
        "execution_orig_argv": sys.orig_argv,
        "reproduction_command": "uv run python fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/steel-shaft-comparison-v1/comparison.py --out /tmp/eoere-steel-shaft-plan-replay.json"}
    verify(pins)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = prepare()
    with args.out.open("xb") as stream:
        stream.write((json.dumps(result, indent=2, allow_nan=False)+"\n").encode())
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "source_pin_count": result["source_pin_union_count"]}))


if __name__ == "__main__":
    main()
