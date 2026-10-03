"""Assess saved proposal rank and bound its fixed-force rigid seating freedom.

This reuses the recorded clearance certificate. It changes no frame force,
contact branch, stiffness, geometry or acceptance threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/frame-stability"
FRAME = HERE / "rawlocal/knee-bridge-gravity/attempt01"
RESPONSE = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
PACKAGE = HERE / "rawlocal/knee-bridge-working-package/attempt02"
PINS = {
    FRAME / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    RESPONSE / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    PACKAGE / "receipt.json": "5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b",
    PACKET / "simple_frame.py": "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    PACKET / "bounded_clearance.py": "35c0ceb7609c7ff77118ddf0a8e9f0da681ae41ad3396e4a95a71792724a9c7b",
}
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def key(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "missing helper loader")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def outer_intervals(mapping, coordinate_intervals):
    """Bound a linear observable on the certified null-coordinate outer box."""
    low, high = coordinate_intervals.T
    lo = np.minimum(mapping * low, mapping * high).sum(axis=1)
    hi = np.maximum(mapping * low, mapping * high).sum(axis=1)
    return np.c_[lo, hi]


def build(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate output child required")
    pins = dict(PINS)
    authenticate(pins)
    receipt, assessment, comparison = (read(p) for p in (
        PACKAGE / "receipt.json", FRAME / "operator-assessment.json", RESPONSE / "comparison.json",
    ))
    for relative, digest in receipt["source_sha256"].items():
        path = ROOT / relative
        require(path not in pins or pins[path] == digest, "conflicting source binding")
        pins[path] = digest
    for name, digest in assessment["output_sha256"].items():
        path = FRAME / name
        require(path not in pins or pins[path] == digest, "conflicting operator output binding")
        pins[path] = digest
    pins[Path(__file__).resolve()] = sha(__file__)
    authenticate(pins)
    require(comparison["frame_operator_directory"] == key(FRAME), "frame/operator source mismatch")
    require(comparison["source_climber_weight_lb"] == 250 and comparison["climber_load_scale"] == 1, "changed climber envelope")
    require(comparison["comparison_horizontal_force_n"] == 300, "changed horizontal force")
    states = comparison["states"]
    require(len(states) == 12 and {(s["case_id"], s["gap_scale"]) for s in states} == {(c, g) for c in CASES for g in (0.0, 1.0)}, "twelve-state census mismatch")
    names = read(FRAME / "model.json")["body_names"]
    require(len(names) == len(set(names)) == 50, "body column inventory mismatch")
    rows = read(FRAME / "row-identities.json")
    sys.path.insert(0, str(PACKET))
    try:
        frame = module(PACKET / "simple_frame.py", "qualification_simple_frame")
        bounds = module(PACKET / "bounded_clearance.py", "qualification_bounded_clearance")
    finally:
        sys.path.remove(str(PACKET))
    with np.load(FRAME / "operators.npz", allow_pickle=False) as data:
        H, D, e, W, k, uni, normals, tangents, transform, footprints = frame.lump_floor(
            *(data[n] for n in ("H", "D", "e", "W")), rows,
        )
    H = (H + H.T) / 2
    require(footprints == comparison["floor_footprints"], "floor contract mismatch")
    require(D.shape == (1612, 300) and transform.shape == (1612, 1888), "operator layout mismatch")
    require(np.all(np.count_nonzero(transform, axis=0) <= 1), "force recovery needs disjoint floor rows")
    row_norm_squared = np.square(transform).sum(axis=1)
    require(np.all(row_norm_squared > 0), "empty lumped force row")
    retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    by_id = {}
    for i, row in enumerate(retained):
        by_id.setdefault(row["row_id"], []).append(i)
    pairs = [by_id[p["plane_id"]] for p in comparison["clearance_planes"]]
    require(len(pairs) == 88 and all(len(p) == 2 and p[1] == p[0] + 1 for p in pairs), "clearance component pairing mismatch")
    targets = np.array(pairs).ravel()
    gaps = np.array([p["relative_radial_gap_mm"] for p in comparison["clearance_planes"]])
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    result_states = []
    with np.load(RESPONSE / "response.npz", allow_pickle=False) as saved:
        for state in states:
            case, gap = state["case_id"], state["gap_scale"]
            tag = case + ("_gap" if gap else "_zero")
            raw, q, a = (saved[tag + suffix] for suffix in (
                "_raw_force_n", "_lumped_q_mm", "_rigid_coordinates",
            ))
            f = (transform @ raw) / row_norm_squared
            require(np.max(abs(transform.T @ f - raw)) < 1e-7, "lumped force recovery mismatch")
            index = CASES.index(case)
            factor = comparison["dead_load_factor"]
            work = factor * W[:, 2 * index] + W[:, 2 * index + 1]
            load_e = factor * e[:, 2 * index] + e[:, 2 * index + 1]
            require(np.max(abs(D @ a + load_e - H @ f - q)) < 1e-7, "saved pose/compliance mismatch")
            balance = (D.T @ f - work).reshape(-1, 6)
            require(np.max(abs(balance[:, :3])) < 0.1 and 1000 * np.max(abs(balance[:, 3:])) < 2, "saved force/moment imbalance")
            certificate = None
            if gap:
                certificate, arrays = bounds.finite_clearance_certificate(
                    D, q, f, k, uni, normals, tangents, targets, gap * gaps, work,
                )
                old = state["fixed_force_clearance_certificate"]
                require(certificate["bounded"] and certificate["nullity"] == old["nullity"], "saved seating classification mismatch")
                require(certificate["actual_active_tangent_svd"]["rank"] == old["actual_active_tangent_svd"]["rank"], "saved tangent-rank mismatch")
                coordinates = np.array([[b["minimum"], b["maximum"]] for b in certificate["null_coordinate_bounds"]])
                increments = outer_intervals(arrays["nullspace"], coordinates)
            else:
                require(state["audit"]["force_bearing_rigid_rank"] == 300, "original zero-gap rank gate failed")
                increments = np.zeros((300, 2))
            bodies = []
            for i, name in enumerate(names):
                inc = increments[6 * i:6 * i + 6]
                total = inc + a[6 * i:6 * i + 6, None]
                bodies.append({
                    "body": name,
                    "rigid_translation_increment_component_intervals_mm": inc[:3].tolist(),
                    "rigid_rotation_increment_component_intervals_rad": (inc[3:] / 1000).tolist(),
                    "representative_rigid_translation_mm": a[6 * i:6 * i + 3].tolist(),
                    "rigid_translation_norm_outer_bound_mm": float(np.linalg.norm(np.max(abs(total[:3]), axis=1))),
                    "rigid_rotation_norm_outer_bound_rad": float(np.linalg.norm(np.max(abs(total[3:]), axis=1)) / 1000),
                })
            result_states.append({
                "case_id": case, "gap_scale": gap,
                "force_bearing_rank": state["audit"]["force_bearing_rigid_rank"],
                "recorded_rank300_criterion_pass": state["audit"]["force_bearing_rigid_rank"] == 300,
                "fixed_force_seating_bounded": True,
                "certificate": certificate, "body_rigid_seating_bounds": bodies,
                "total_deformed_body_motion_bound_established": False,
                "dynamic_stability_established": False,
            })
            print(tag, "rank", state["audit"]["force_bearing_rigid_rank"], "bounded rigid seating", flush=True)
    authenticate(pins)
    result = {
        "schema": "current_proposal_saved_rank_and_rigid_seating_assessment/v1",
        "status": "COMPLETE_SAVED_RANK_AND_FIXED_FORCE_RIGID_SEATING_ASSESSMENT",
        "states": result_states,
        "rank300_exceedance_count": sum(not s["recorded_rank300_criterion_pass"] for s in result_states),
        "model_changes_required_by_rank_alone": None,
        "limits": [
            "The original strict rank300 criterion fails in six nominal-clearance states; this remains an explicit criterion outcome.",
            "Nominal seating is bounded at fixed force within the original numerical tolerances. Outer boxes enclose circular disks; their vertices are not accepted physical states.",
            "Rigid-coordinate bounds are not full elastic member/panel deflection bounds. No numerical serviceability threshold was invented.",
            "The first-order force model has no inertia, geometric stiffness or dynamic history. A 2x force envelope does not qualify those omitted behaviors.",
            "104 global bolt axes and four separate static internal proposal ties retain their original distinct model scope.",
        ],
        "frame_or_native_or_CAD_run": False,
        "source_forces_changed": False, "proposal_adopted": False,
        "complete_joint_acceptance": False, "physical_release": False,
    }
    write(output / "checks.json", result)
    authenticate(pins)
    artifacts = {n: sha(output / n) for n in (".gitignore", "checks.json", "producer.py.snapshot")}
    write(output / "receipt.json", {"source_sha256": {key(p): h for p, h in pins.items()}, "output_sha256": artifacts})
    return {"status": result["status"], "states": len(result_states), "rank300_exceedance_count": result["rank300_exceedance_count"], "receipt_sha256": sha(output / "receipt.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    print(json.dumps(build(parser.parse_args().output)))
