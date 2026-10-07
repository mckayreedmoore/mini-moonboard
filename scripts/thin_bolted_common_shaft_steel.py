"""Physical common-shaft steel-port, own-washer and circular-section diagnostics.

This consumer performs no solve or CAD query. It preserves every signed point
arm/free couple and never assigns one shared shaft's reactions equally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
METHODS = PACKET / "steel-resistance-methods-v4.json"
METHODS_SHA = "d00ff10eb875c0d093f6c0e811a7b1e2ef850f6d3ec846b6b910eb2c4cdabf19"
HEAD = PACKET / "cap-head-face-reference-v4.json"
HEAD_SHA = "0cba6f3c9e36506807fe4d353eb970534f92a52c3ed35d91a8076d83c73cc7d4"
AUDIT_SHA = "a236900e59a3d5984598df56d4243408ce12801d4ab6fcc7f765f6a420de01ba"
GRADE5_SOURCE = "https://www.fastenal.com/content/merch_rules/images/fcom/content-library/Fastener%20Reference%20Guide.pdf"
GRADE5_FY_MPA = 92000 * .006894757293168


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector(value, size=3) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.isfinite(result).all():
        raise ValueError(f"finite {size}-component vector required")
    return result


def transport_wrench(force, free_moment, point, reference) -> tuple[np.ndarray, np.ndarray]:
    force = vector(force)
    return force, vector(free_moment) + np.cross(vector(point) - vector(reference), force)


def aggregate_steel_ports(layout: dict, bearings: list[dict], captures: list[dict]) -> list[dict]:
    """Reduce physical actions ON STEEL to each own authenticated hole entry."""
    ports = {(axis["id"], port["angle_id"], port["flange"]): port
             for axis in layout["installed_axes"] for port in axis["attachments"]}
    by_host = {(axis, angle): (axis, angle, flange) for axis, angle, flange in ports}
    if len(by_host) != len(ports):
        raise ValueError("one physical shaft cannot ambiguously identify two ports on one fitting")
    grouped = {key: [] for key in ports}
    used = set()
    for table, rows in (("bearing", bearings), ("capture", captures)):
        for row in rows:
            host = row["second"]
            identity = (row["axis_id"], host)
            if identity not in by_host:
                if table == "bearing" and row.get("surface_material") == "steel":
                    raise ValueError("steel bearing leaves the occupied flange ports")
                continue
            key = by_host[identity]
            if row["id"] in used:
                raise ValueError("duplicate physical steel action")
            used.add(row["id"])
            if table == "bearing" and row.get("flange") != key[2]:
                raise ValueError("steel bore flange identity differs")
            if table == "capture" and row["end"].get("flange") != key[2]:
                raise ValueError("steel capture flange identity differs")
            point = row["host_support_point_xyz_mm"] if table == "capture" else row["point_xyz_mm"]
            force = vector(row["force_on_second_xyz_n"])
            moment = vector(row["moment_on_second_at_point_xyz_nmm"])
            grouped[key].append({"id": row["id"], "kind": table, "point_xyz_mm": point,
                                 "force_on_steel_xyz_n": force.tolist(),
                                 "moment_on_steel_at_point_xyz_nmm": moment.tolist()})
    result = []
    for key, actions in sorted(grouped.items()):
        if sum(a["kind"] == "bearing" for a in actions) != 2 or sum(a["kind"] == "capture" for a in actions) != 1:
            raise ValueError("each occupied steel port needs its two Gauss bearings and own end capture")
        port = ports[key]
        force, moment = np.zeros(3), np.zeros(3)
        for row in actions:
            f, m = transport_wrench(row["force_on_steel_xyz_n"], row["moment_on_steel_at_point_xyz_nmm"],
                                    row["point_xyz_mm"], port["entry_xyz_mm"])
            force += f
            moment += m
        result.append({"axis_id": key[0], "angle_id": key[1], "flange": key[2],
                       "receiver_metadata_only": port["receiver"], "point_xyz_mm": port["entry_xyz_mm"],
                       "force_on_steel_xyz_n": force.tolist(), "moment_on_steel_at_point_xyz_nmm": moment.tolist(),
                       "physical_action_ids": [r["id"] for r in actions],
                       "opposed_wood_or_angle_action_inferred": False})
    return result


def api_counterwrenches(ports: list[dict], state: dict) -> list[dict]:
    """Negated steel wrenches are API notation, not inferred wood reactions."""
    return [{"case_id": state["case_id"], "accessory_placement": state["accessory_placement"],
             "state_id": state["state_id"], "axis_id": row["axis_id"], "angle_id": row["angle_id"],
             "flange": row["flange"], "point_xyz_mm": row["point_xyz_mm"],
             "force_on_receiver_xyz_n": (-vector(row["force_on_steel_xyz_n"])).tolist(),
             "moment_on_receiver_at_point_xyz_nmm": (-vector(row["moment_on_steel_at_point_xyz_nmm"])).tolist(),
             "counterwrench_representation_only": True, "equals_actual_wood_receiver_reaction": False}
            for row in ports]


def own_washer_states(methods: dict, head: dict, captures: list[dict]) -> list[dict]:
    """Each washer takes its own capture force, never its opposite end's force."""
    references = {(r["axis_id"], r["role"]): r for r in methods["washer_reference_inputs"]}
    head_refs = {(r["axis_id"], r["role"]): r for r in head["ends"]}
    result, used = [], set()
    for capture in captures:
        end = capture["end"]
        role = {"head": "head_washer", "nut": "nut_washer"}[end["end"]]
        key = (capture["axis_id"], role)
        if key in used or key not in references:
            raise ValueError("duplicate or foreign own washer capture")
        used.add(key)
        reference = references[key]
        force = vector(capture["force_on_first_xyz_n"])
        direction = vector(end["direction_on_shaft_xyz"])
        if abs(np.linalg.norm(direction) - 1.) > 1e-10:
            raise ValueError("own washer direction must be a unit shaft axis")
        magnitude = float(force @ direction / np.linalg.norm(direction))
        scalar = capture["compression_n"]
        if not isinstance(scalar, (float, int)) or not math.isfinite(scalar) or scalar < 0 or abs(magnitude - scalar) > 1e-7:
            raise ValueError("own washer force contradicts its unilateral capture scalar")
        if np.linalg.norm(force - scalar * direction) > 1e-7:
            raise ValueError("washer capture includes unsupported transverse force")
        sensitivities = []
        for profile_id in reference["bearing_circle_sensitivity_profile_ids"]:
            profile = methods["washer_bending_profiles"][profile_id]
            coefficient = profile["unit_axial_two_face_bending"]["required_fy_mpa_at_sampled_bending_first_yield"]
            sensitivities.append({"profile_id": profile_id,
                                  "assumed_circular_bearing_diameter_mm": profile["assumed_circular_bearing_diameter_mm"],
                                  "required_fy_mpa_own_capture_axial_component": scalar * coefficient})
        if key in head_refs:
            profile_id = head_refs[key]["profile_id"]
            coefficient = head["profiles"][profile_id]["unit_axial_two_face_bending"]["required_fy_mpa_at_sampled_bending_first_yield"]
            sensitivities.append({"profile_id": profile_id, "assumed_circular_bearing_diameter_mm": 17.145,
                                  "required_fy_mpa_own_capture_axial_component": scalar * coefficient})
        wood = reference["nominal_wood_annulus_reference"]
        result.append({"state_id": capture.get("state_id"), "axis_id": key[0], "role": key[1],
                       "host": capture["second"], "support_material": reference["support_material"],
                       "shaft_pressure_face_point_xyz_mm": capture["point_xyz_mm"],
                       "host_support_point_xyz_mm": capture["host_support_point_xyz_mm"],
                       "own_capture_model_axial_force_n": scalar,
                       "reused_unit_plate_sensitivities": sensitivities,
                       "nominal_occupied_full_wood_annulus_axial_reference_index": scalar / (wood["wood_bearing_reference_lbf"] * 4.4482216152605) if wood else None,
                       "own_end_moments_prying_and_actual_pressure_verified": False,
                       "unknown_own_end_moments_zero_filled": False, "combined_washer_index": None,
                       "actual_head_or_nut_circle_and_fillet_seating_verified": False,
                       "actual_material_capacity_verified": False, "complete_joint_acceptance": False})
    if used != set(references):
        raise ValueError("all 140 own washer captures must be present")
    return result


def verify_shaft_cuts(demand: dict, geometry: list[dict]) -> dict:
    """Replay every signed cut from authenticated actual point loads/couples.

    This is an equilibrium replay, not a beam solve. It includes head gravity
    outside the nominal under-head beam interval and both sides of every load.
    """
    rows = demand["common_shaft_section_cut_actions"]
    saved = {row["axis_id"]: row for row in rows}
    specs = {row["axis_id"]: row for row in geometry}
    if len(saved) != len(rows) or set(saved) != set(specs):
        raise ValueError("all unique physical shaft cut tables are required")
    actions = [*demand["common_shaft_bearing_actions"], *demand["shaft_end_capture_actions"]]
    maximum_force_error, maximum_moment_error, cut_count = 0., 0., 0
    for axis_id, spec in specs.items():
        row = saved[axis_id]
        point, expected_basis = vector(spec["point"]), np.asarray(spec["basis"], dtype=float)
        basis = np.asarray(row["basis_axis_tangent1_tangent2_xyz"], dtype=float)
        if (basis.shape != (3, 3) or not np.isfinite(basis).all()
                or np.linalg.norm(basis @ basis.T - np.eye(3)) > 1e-10
                or np.linalg.det(basis) < .9999999999
                or np.linalg.norm(basis - expected_basis) > 1e-10
                or np.linalg.norm(vector(row["axis_point_xyz_mm"]) - point) > 1e-5
                or np.linalg.norm(vector(row["axis_direction_xyz"]) - expected_basis[0]) > 1e-10
                or row["body"] != spec["body"]):
            raise ValueError("shaft cut basis/axis/body differs from frozen geometry")
        interval = vector(row["shaft_interval_from_axis_point_mm"], 2)
        if np.linalg.norm(interval - vector(spec["shaft_interval_mm"], 2)) > 1e-5:
            raise ValueError("shaft cut interval differs from frozen pressure-face/tip geometry")
        diameter = spec["diameter_mm"] * demand["parameters"]["shaft_diameter_scale"]
        if (abs(row["elastic_section_diameter_mm"] - diameter) > 1e-10
                or abs(row["bearing_contact_major_diameter_mm"] - spec["diameter_mm"]) > 1e-10):
            raise ValueError("shaft cut circle differs from the declared elastic/major diameter scenario")
        events = set(spec["shaft_interval_mm"])
        for surface in spec["surfaces"]:
            low, high = surface["interval_mm"]
            events.update((low, .5 * (low + high), high))
        for end in spec["ends"]:
            events.update((end["support_s_mm"], end["pressure_face_s_mm"]))
        coarse = []
        for event in sorted(events):
            if not coarse or event - coarse[-1] > 1e-6:
                coarse.append(event)
        segment = demand["parameters"]["shaft_max_segment_mm"]
        if not isinstance(segment, (int, float)) or not math.isfinite(segment) or segment <= 0:
            raise ValueError("positive finite shaft mesh segment required")
        mesh = []
        for low, high in pairwise(coarse):
            mesh.extend(np.linspace(low, high, max(1, math.ceil((high - low) / segment)) + 1)[:-1])
        mesh.append(coarse[-1])
        declared_mesh = np.asarray(row["mesh_stations_from_axis_point_mm"], dtype=float)
        if declared_mesh.shape != (len(mesh),) or not np.allclose(declared_mesh, mesh, atol=1e-9, rtol=0):
            raise ValueError("shaft cut mesh stations differ from source-bound geometry/scenario")
        loads = [(vector(load["point_xyz_mm"]), vector(load["force_xyz_n"]),
                  vector(load.get("moment_at_point_xyz_nmm", [0., 0., 0.])))
                 for load in demand["body_applied_loads"] if load["body"] == spec["body"]]
        loads += [(vector(action["point_xyz_mm"]), vector(action["force_on_first_xyz_n"]),
                   vector(action["moment_on_first_at_point_xyz_nmm"]))
                  for action in actions if action["first"] == spec["body"]]
        low, high = interval
        stations = list(np.linspace(low, high, 33)) + mesh
        for load_point, _, _ in loads:
            station = float((load_point - point) @ basis[0])
            stations.extend((float(np.clip(station - 1e-7, low, high)),
                             float(np.clip(station + 1e-7, low, high))))
        stations = sorted(set(stations))
        cuts = row["cuts"]
        declared_stations = np.asarray([cut["station_from_axis_point_mm"] for cut in cuts], dtype=float)
        if declared_stations.shape != (len(stations),) or not np.allclose(declared_stations, stations, atol=1e-9, rtol=0):
            raise ValueError("shaft cut census omits/changes a load-side, uniform or mesh sample")
        for cut in cuts:
            cut_point = point + basis[0] * cut["station_from_axis_point_mm"]
            if np.linalg.norm(vector(cut["point_xyz_mm"]) - cut_point) > 1e-5:
                raise ValueError("shaft cut point differs from its own axis station")
            force, moment = np.zeros(3), np.zeros(3)
            for load_point, load_force, free_moment in loads:
                if float((load_point - point) @ basis[0]) < cut["station_from_axis_point_mm"]:
                    force -= load_force
                    moment -= free_moment + np.cross(load_point - cut_point, load_force)
            expected = np.r_[basis @ force, basis @ moment]
            actual = vector(cut["local_N_V1_V2_T_M1_M2_n_nmm"], 6)
            force_error, moment_error = float(np.linalg.norm(actual[:3] - expected[:3])), float(np.linalg.norm(actual[3:] - expected[3:]))
            if force_error > 1e-7 or moment_error > 1e-4:
                raise ValueError("shaft section cut differs from independent physical point/couple equilibrium")
            maximum_force_error = max(maximum_force_error, force_error)
            maximum_moment_error = max(maximum_moment_error, moment_error)
            cut_count += 1
    return {"independent_same_cut_equilibrium_replay_pass": True, "physical_shafts": len(specs),
            "cut_samples_reconstructed": cut_count, "maximum_force_difference_n": maximum_force_error,
            "maximum_free_moment_difference_nmm": maximum_moment_error,
            "both_sides_of_every_load_and_all_mesh_uniform_samples_present": True,
            "native_or_CAD_execution": False}


def shaft_section_references(rows: list[dict], caller_sections: dict | None = None) -> list[dict]:
    """Same-cut N/V/M/T circular envelopes; root dimensions require caller basis."""
    from scripts.thin_bolted_steel_resistance import bolt_section_reference

    caller_sections = caller_sections or {}
    identities = [row["axis_id"] for row in rows]
    if len(set(identities)) != len(identities) or set(caller_sections) - set(identities):
        raise ValueError("duplicate shaft or foreign caller section identity")
    result = []
    for shaft in rows:
        axis_id = shaft["axis_id"]
        scenarios = [{"id": "elastic_model_circle", "diameter_mm": shaft["elastic_section_diameter_mm"],
                      "section_basis": "source producer's unadopted uniform circular elastic shaft diameter"},
                     *caller_sections.get(axis_id, [])]
        own = []
        if len({scenario.get("id") for scenario in scenarios}) != len(scenarios):
            raise ValueError("duplicate circle section scenario identity")
        for scenario in scenarios:
            if not scenario.get("section_basis") or not scenario.get("id"):
                raise ValueError("root/body circle needs an explicit scenario and geometric basis")
            samples = []
            for cut in shaft["cuts"]:
                actions = vector(cut["local_N_V1_V2_T_M1_M2_n_nmm"], 6)
                stress = bolt_section_reference(force_n=actions[:3], moment_nmm=actions[3:],
                    diameter_mm=scenario["diameter_mm"], fy_mpa=GRADE5_FY_MPA,
                    material_basis="conditional conforming SAE J429 Grade5, quarter-to-one-inch primary vendor minimum yield; actual product unverified",
                    section_basis=scenario["section_basis"])
                samples.append({"station_from_axis_point_mm": cut["station_from_axis_point_mm"],
                                "point_xyz_mm": cut["point_xyz_mm"], "same_cut_N_V1_V2_T_M1_M2_n_nmm": actions.tolist(),
                                **stress})
            if not samples:
                raise ValueError("shaft cut samples are required")
            own.append({"section_scenario": scenario, "sample_count": len(samples),
                        "sampled_governing_section": max(samples, key=lambda r: r["same_section_nominal_stress_envelope_mpa"]),
                        "actual_root_body_thread_exposure_and_product_verified": False})
        result.append({"axis_id": axis_id, "body": shaft["body"], "section_scenarios": own,
                       "root_scenario_supplied": bool(caller_sections.get(axis_id)),
                       "NDS_fyb_inferred_from_tensile_yield": False,
                       "continuous_extrema_or_physical_first_yield_capacity_verified": False,
                       "complete_joint_acceptance": False})
    return result


def consume(path: Path, sections_path: Path | None = None) -> dict:
    payload = path.read_bytes()
    input_sha = hashlib.sha256(payload).hexdigest()
    demand = json.loads(payload)
    from scripts.thin_bolted_common_shaft_audit import audit_common_shaft_state

    audit_path = ROOT / "scripts/thin_bolted_common_shaft_audit.py"
    audit_sha = sha(audit_path)
    if audit_sha != AUDIT_SHA:
        raise ValueError("preserve the issued independent physical common-shaft gate")
    audit = audit_common_shaft_state(demand)
    if audit.get("independent_common_shaft_support_load_and_equilibrium_checks_pass") is not True:
        raise ValueError("independent physical common-shaft gate failed")
    if sha(METHODS) != METHODS_SHA or sha(HEAD) != HEAD_SHA:
        raise ValueError("frozen component method/coefficient report changed")
    methods, head = [json.loads(p.read_text()) for p in (METHODS, HEAD)]
    for source in (methods, head):
        for relative, expected in source["source_sha256"].items():
            if sha(ROOT / relative) != expected:
                raise ValueError(f"frozen component dependency changed: {relative}")
    from scripts.thin_bolted_common_shaft import read_inputs
    from scripts.thin_bolted_steel_resistance import LAYOUT, compare_flange_actions

    layout = json.loads(LAYOUT.read_text())
    ports = aggregate_steel_ports(layout, demand["common_shaft_bearing_actions"], demand["shaft_end_capture_actions"])
    if len(ports) != 72:
        raise ValueError("all 72 physical steel ports are required")
    supplied = demand["common_shaft_steel_port_actions"]
    exported = {(r["axis_id"], r["angle_id"], r["flange"]): r for r in supplied}
    if len(exported) != 72 or len(supplied) != 72:
        raise ValueError("all 72 producer steel aggregate ports are required")
    for port in ports:
        saved = exported[(port["axis_id"], port["angle_id"], port["flange"])]
        for key, tolerance in (("point_xyz_mm", 1e-5), ("force_on_steel_xyz_n", 1e-7),
                               ("moment_on_steel_at_point_xyz_nmm", 1e-4)):
            if np.linalg.norm(vector(saved[key]) - vector(port[key])) > tolerance:
                raise ValueError("producer steel wrench differs from signed physical point/couple reduction")
    comparison = compare_flange_actions(api_counterwrenches(ports, demand), demand["flange_contact_actions"])
    for row in comparison["flange_comparisons"]:
        row["nominal_yield_index_covers_exported_torsion"] = row["steel_torsion_complete"]
        row["torsion_omitted_from_nominal_vm_envelope"] = not row["steel_torsion_complete"]
    washers = own_washer_states(methods, head, demand["shaft_end_capture_actions"])
    cut_replay = verify_shaft_cuts(demand, read_inputs())
    sections_payload = sections_path.read_bytes() if sections_path else None
    sections_sha = hashlib.sha256(sections_payload).hexdigest() if sections_payload is not None else None
    caller = json.loads(sections_payload) if sections_payload is not None else None
    shaft_refs = shaft_section_references(demand["common_shaft_section_cut_actions"], caller)
    if len(shaft_refs) != 70:
        raise ValueError("all 70 common physical shafts require section-cut references")
    if sha(path) != input_sha or sha(audit_path) != audit_sha:
        raise ValueError("demand/audit changed during component consumption")
    if sections_path and sha(sections_path) != sections_sha:
        raise ValueError("caller section source changed during component consumption")
    pins = {str(path.resolve().relative_to(ROOT)): input_sha, str(METHODS.relative_to(ROOT)): METHODS_SHA,
            str(HEAD.relative_to(ROOT)): HEAD_SHA, str(audit_path.relative_to(ROOT)): audit_sha,
            str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))}
    tests = ROOT / "tests/test_thin_bolted_common_shaft_steel.py"
    pins[str(tests.relative_to(ROOT))] = sha(tests)
    if sections_path:
        pins[str(sections_path.resolve().relative_to(ROOT))] = sections_sha
    return {"schema": "thin_bolted_common_shaft_steel/v1", "candidate": demand["candidate"],
            "state_id": demand["state_id"], "case_id": demand["case_id"],
            "accessory_placement": demand["accessory_placement"], "parameters": demand["parameters"],
            "source_sha256": pins, "producer_source_sha256": demand["source_sha256"],
            "independent_physical_common_shaft_audit": audit, "steel_port_wrenches": ports,
            "fresh_flange_component_comparison": comparison, "own_washer_capture_references": washers,
            "independent_shaft_cut_replay": cut_replay,
            "shaft_same_section_references": shaft_refs,
            "grade5_material_reference": {"source": GRADE5_SOURCE, "locator": "p0 inch-series SAEJ429Grade5 row, quarter-to-one-inch size range",
                                          "minimum_tensile_yield_psi": 92000, "minimum_tensile_yield_mpa": GRADE5_FY_MPA,
                                          "minimum_tensile_strength_psi": 120000, "proof_strength_psi_distinct_from_yield": 85000,
                                          "NDS_fyb_assigned": None, "actual_product_and_property_verified": False},
            "steel_torsion_unmodeled_flange_count": sum(not r["steel_torsion_complete"] for r in comparison["flange_comparisons"]),
            "method_validation": {"fixture_count": 27,
                "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_common_shaft_steel.py",
                "lint_command": ".venv/bin/ruff check scripts/thin_bolted_common_shaft_steel.py tests/test_thin_bolted_common_shaft_steel.py",
                "scope": "wrench arms/free couples, unequal shared sides, own140 washer force identity, same-cut circular stress and independent cut census/replay"},
            "limits": ["Steel-port counterwrenches are API notation only; actual wood reactions and unequal shared sides stay independent.",
                       "Full point arms and free couples are retained; the frozen flat-strip normal/bending/shear envelope omits torsion where flagged.",
                       "Each washer uses its own model axial capture. Actual pressure, head/nut/fillet seating, own-end moments/prying and washer yield remain unresolved.",
                       "Shaft stresses use same-cut equilibrium N/V/M/T and a conditional conforming Grade5 yield scenario. Actual root/shank, threads/notches/head/nut/stripping and second-order applicability are unverified.",
                       "Material/diameter scenarios are not ASD/LRFD design strengths or inspected delivered capacities."],
            "native_or_CAD_execution": False, "unchanged_unit_methods_recomputed": False,
            "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demands", type=Path, required=True)
    parser.add_argument("--sections", type=Path, help="Optional axis-keyed circle scenarios: id,diameter_mm,section_basis; no actual root is inferred")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued physical common-shaft component evidence")
    report = consume(args.demands, args.sections)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "state_id": report["state_id"],
                      "steel_ports": len(report["steel_port_wrenches"]), "own_washers": len(report["own_washer_capture_references"]),
                      "shafts": len(report["shaft_same_section_references"]),
                      "unmodeled_flange_torsion": report["steel_torsion_unmodeled_flange_count"]}, indent=2))


if __name__ == "__main__":
    main()
