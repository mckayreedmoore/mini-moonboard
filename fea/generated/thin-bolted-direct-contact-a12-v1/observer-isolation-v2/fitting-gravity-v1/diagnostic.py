"""Own fitting gravity as the frozen load operator's two port wrenches.

This preserves its half-port generalized work. It does not assign a physical
mass distribution to either formed leg or alter the admitted response.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_joint_post_admission as pure
from scripts import thin_bolted_steel_resistance as steel

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
TEST = OWN.with_name("test_diagnostic.py")
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
TEST_SHA = hashlib.sha256(TEST.read_bytes()).hexdigest()
PACKET = OWN.parent.parent
GATE = PACKET / "admission.py"
GATE_SHA = "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6"
FIELD_SHA = "29b25f11794a171a1364268ed676a24cee2882e47c3018b3648267d2707a0ddf"
COMPONENT_SHA = "650c0cf1225326506c91ff74b97205832f1ba73e3b67cfe8d73450d42237285e"
PINS = {
    "scripts/thin_bolted_frame_mechanics.py": "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448",
    "scripts/thin_bolted_joint_post_admission.py": "e63aa17cb56b71feb4c700d6bc0ffb4b801f7716753d350ae475409dc2470e5a",
    "scripts/thin_bolted_steel_resistance.py": "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602",
}
pure.verify_pins(PINS)


def source_pins():
    return {**PINS, str(GATE.relative_to(ROOT)): GATE_SHA,
            str(OWN.relative_to(ROOT)): LOADED_SHA, str(TEST.relative_to(ROOT)): TEST_SHA}


def authenticate(field_path, admission, component_path, *, expected_field_sha256, expected_component_sha256,
                 admission_sha256):
    """Exact current admission precedes any action or vector consumption."""
    pure.verify_pins(source_pins())
    pure.unit.require(expected_field_sha256 == FIELD_SHA and expected_component_sha256 == COMPONENT_SHA
                      and admission_sha256 == GATE_SHA, "reviewed exact current field/component/gate hashes required")
    field_path, component_path = Path(field_path), Path(component_path)
    payload, component_bytes = field_path.read_bytes(), component_path.read_bytes()
    pure.unit.require(hashlib.sha256(payload).hexdigest() == FIELD_SHA
                      and hashlib.sha256(component_bytes).hexdigest() == COMPONENT_SHA,
                      "exact admitted field and unchanged component bytes required")
    spec = importlib.util.spec_from_file_location("fitting_gravity_actual_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    field, pins = gate.require_admitted_payload(payload, admission, admission_sha256=admission_sha256)
    components = json.loads(component_bytes)
    pure.unit.require(components["independent_complete_timber_admission"] == admission
                      and components["field_sha256"] == FIELD_SHA
                      and components["field_canonical_sha256"] == pure.references.canonical_sha(field)
                      and all(components[k] == field[k] for k in pure.IDENTITIES)
                      and components["complete_joint_resistance"] is None
                      and components["complete_joint_acceptance"] is False
                      and components["release"] == field["release"], "same immutable current component/admission join required")
    pins = gate.linear.merge_pins(pins, components["source_sha256"], source_pins(),
        {str(field_path.resolve().relative_to(ROOT)): FIELD_SHA,
         str(component_path.resolve().relative_to(ROOT)): COMPONENT_SHA})
    pure.verify_pins(pins)
    return field, components, pins


def gravity_ports(points, centroid, force):
    """Call the genuine source port on a twelve-DOF chart, without its constructor."""
    centroid, force = np.asarray(centroid, dtype=float), np.asarray(force, dtype=float)
    pure.unit.require(centroid.shape == force.shape == (3,) and np.isfinite(centroid).all()
                      and np.isfinite(force).all() and set(points) == {"beam", "post"}, "finite source fitting points/force required")
    chart = object.__new__(frame.ElasticAssembly)
    chart.members, chart.panels, chart.ndof = {}, {}, 12
    chart.fittings = {"own": {"index": np.arange(12).reshape(2, 6),
        "points": {key: np.asarray(point, dtype=float) for key, point in points.items()}}}
    vector = np.asarray(chart.port("own", centroid).T @ force).ravel()
    rows = []
    for flange, offset in (("beam", 0), ("post", 6)):
        point = np.asarray(points[flange], dtype=float)
        half, moment = force / 2, np.cross(centroid - point, force / 2)
        pure.unit.require(np.max(abs(vector[offset:offset + 3] - half)) < 1e-12
                          and np.max(abs(vector[offset + 3:offset + 6] - moment / frame.ROTATION_SCALE)) < 1e-12,
                          "source half-port force/couple dual differs")
        rows.append({"flange": flange, "point_xyz_mm": point.tolist(),
                     "force_on_steel_xyz_n": half.tolist(), "moment_on_steel_at_point_xyz_nmm": moment.tolist()})
    return rows, vector, chart.port("own", centroid)


def project_current_gravity(field, layout):
    """Verify all own port loads against only the saved original applied vector."""
    record = field["complete_timber_original_operator_inputs"]
    manifest_path = ROOT / record["path"]
    pure.unit.require(pure.unit.sha(manifest_path) == record["sha256"], "original operator manifest differs")
    manifest = json.loads(manifest_path.read_bytes())
    bundle = manifest["array_bundle"]
    pure.unit.require(bundle == record["array_bundle"] and pure.unit.sha(ROOT / bundle["path"]) == bundle["sha256"]
                      and manifest["ndof"] == field["counts"]["dofs"] == 8018, "original RHS bundle/chart differs")
    # Access only this dense vector; no material K, group or contact array is read.
    with np.load(ROOT / bundle["path"], allow_pickle=False) as arrays:
        applied = np.array(arrays[manifest["applied"]["key"]], copy=True)
    start = 1 + max(i for row in field["linear_timber_coordinate_map"]["members"]
                    for node in row["node_dof_indices"] for i in node)
    pure.unit.require(start == 1350 and len(layout["raw_fittings"]) == 36
                      and min(r["global_dof_start"] for r in field["panel_generalized_coefficients"].values()) == start + 432,
                      "source fitting chart/order differs")
    names = {r["angle_id"] for r in layout["raw_fittings"]}
    loads = [r for r in field["body_applied_loads"] if r["body"] in names]
    indexed = {r["body"]: r for r in loads}
    pure.unit.require(len(loads) == len(indexed) == 36 and set(indexed) == names
                      and all(r["id"] == "self-weight/" + r["body"] and "moment_at_point_xyz_nmm" not in r for r in loads),
                      "all36 declared force-only fitting centroid gravity rows required")
    output, rhs_error, work_error, wrench_error = [], 0., 0., 0.
    for number, fitting in enumerate(layout["raw_fittings"]):
        load = indexed[fitting["angle_id"]]
        points = {r["flange"]: r["entry_xyz_mm"] for r in fitting["holes"]}
        rows, vector, port = gravity_ports(points, load["point_xyz_mm"], load["force_xyz_n"])
        slot = slice(start + 12 * number, start + 12 * (number + 1))
        rhs_error = max(rhs_error, float(np.max(abs(vector - applied[slot]))))
        q = np.asarray(field["response"]["q"][slot], dtype=float)
        hand = np.concatenate([np.r_[r["force_on_steel_xyz_n"],
                                    np.asarray(r["moment_on_steel_at_point_xyz_nmm"]) / frame.ROTATION_SCALE] for r in rows])
        work_error = max(work_error, abs(float(np.asarray(load["force_xyz_n"]) @ (port @ q)) - float(hand @ q)))
        total = sum((np.r_[r["force_on_steel_xyz_n"], np.cross(r["point_xyz_mm"], r["force_on_steel_xyz_n"])
                          + r["moment_on_steel_at_point_xyz_nmm"]] for r in rows), np.zeros(6))
        wanted = np.r_[load["force_xyz_n"], np.cross(load["point_xyz_mm"], load["force_xyz_n"])]
        wrench_error = max(wrench_error, float(np.max(abs(total - wanted))))
        output.extend({"angle_id": fitting["angle_id"], "source_body_gravity": copy.deepcopy(load), **row} for row in rows)
    pure.unit.require(rhs_error == 0. and work_error < 1e-10 and wrench_error < 1e-9,
                      "source fitting RHS/work/wrench gravity projection differs")
    return output, {"fitting_bodies": 36, "own_flange_port_loads": 72, "fitting_global_dof_interval": [start, start + 432],
                    "maximum_original_RHS_coefficient_error": rhs_error,
                    "maximum_current_q_virtual_work_error_nmm": work_error,
                    "maximum_global_wrench_error_n_nmm": wrench_error,
                    "original_operator_manifest": {k: record[k] for k in ("path", "sha256")},
                    "only_saved_applied_vector_read": True, "material_K_loaded": False}


def consume(field_path, admission, component_path, *, expected_field_sha256, expected_component_sha256, admission_sha256):
    """Additional same-state nominal diagnostic; preserve the issued component result."""
    field, components, pins = authenticate(field_path, admission, component_path,
        expected_field_sha256=expected_field_sha256, expected_component_sha256=expected_component_sha256,
        admission_sha256=admission_sha256)
    before = [pure.references.canonical_sha(v) for v in (field, components, admission)]
    layout = json.loads(steel.LAYOUT.read_bytes())
    added, projection = project_current_gravity(field, layout)
    indexed = {(r["angle_id"], r["flange"]): r for r in added}
    fittings = {r["angle_id"]: r for r in layout["raw_fittings"]}
    nominal, projected = [], []
    rows = components["steel"]["fresh_flange_component_comparison"]["flange_comparisons"]
    pure.unit.require(len(rows) == len({(r["angle_id"], r["flange"]) for r in rows}) == 72, "all72 unique current flange rows required")
    for row in rows:
        key = row["angle_id"], row["flange"]
        extra = {k: indexed[key][k] for k in ("point_xyz_mm", "force_on_steel_xyz_n", "moment_on_steel_at_point_xyz_nmm")}
        loads = copy.deepcopy(row["external_point_actions_on_steel"]) + [extra]
        result = steel.flange_reference(fittings[key[0]], key[1], loads)
        cuts = result.pop("sections")
        nominal.append({**{k: field[k] for k in pure.IDENTITIES}, **result, "section_count": len(cuts),
                        "sampled_stress_witness": max(cuts, key=lambda r: r["nominal_first_yield_index"]),
                        "without_explicit_port_gravity_nominal_index": row["sampled_maximum_nominal_first_yield_index"]})
        projected.append({**{k: field[k] for k in pure.IDENTITIES}, "angle_id": key[0], "flange": key[1],
                          "external_point_actions_on_steel": loads})
    # Explicit shape projection into the unchanged pure arithmetic API.
    torsion = pure.flange_torsion_reductions(field,
        {"fresh_flange_component_comparison": {"flange_comparisons": projected}}, layout)
    pure.unit.require(before == [pure.references.canonical_sha(v) for v in (field, components, admission)],
                      "admitted input changed during additional gravity diagnostic")
    pure.verify_pins(pins)
    pure.unit.require(pure.unit.sha(Path(field_path)) == FIELD_SHA and pure.unit.sha(Path(component_path)) == COMPONENT_SHA,
                      "issued immutable files changed")
    return {"schema": "thin_bolted_own_fitting_operator_gravity_cut_diagnostic/v1",
        **{k: field[k] for k in pure.IDENTITIES}, "field_sha256": FIELD_SHA, "unchanged_component_sha256": COMPONENT_SHA,
        "admission_canonical_sha256": pure.references.canonical_sha(admission), "actual_gate_sha256": GATE_SHA,
        "source_sha256": pins, "source_gravity_port_projection_checks": projection,
        "source_gravity_port_wrenches": added, "nominal_flange_diagnostics": nominal, "flange_torsion_diagnostics": torsion,
        "method": {"source_port_default_half_beam_half_post_used": True, "own_gravity_port_wrench_added_once": True,
                   "frozen_cut_and_torsion_APIs_reused": True, "old_component_result_modified": False,
                   "response_q_material_K_physics_or_receipt_changed": False},
        "limits": ["This is the frozen centroid-load operator's half-port generalized work, not an observed or continuous leg gravity distribution.",
                   "All loads retain the same admitted first-order state; no equilibrium, pose, pressure or demand is recomputed.",
                   "The nominal flat-leg, rectangle and equal-twist proxy references do not qualify actual sharp/formed heels, holes, warping, prying or joint resistance."],
        "complete_joint_resistance": None, "complete_joint_acceptance": False, "release": copy.deepcopy(field["release"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--components", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    if options.out.exists():
        raise FileExistsError("preserve existing gravity diagnostic")
    result = consume(options.field, json.loads(options.admission.read_bytes()), options.components,
        expected_field_sha256=FIELD_SHA, expected_component_sha256=COMPONENT_SHA, admission_sha256=GATE_SHA)
    result["command"] = [sys.executable, str(OWN), *sys.argv[1:]]
    with options.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
