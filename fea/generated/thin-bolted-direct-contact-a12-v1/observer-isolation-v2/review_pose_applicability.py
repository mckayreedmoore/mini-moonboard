"""Exact saved pose replay and independent Rodrigues point arithmetic; no K."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PINS = {
    "a12-rear.json": "29b25f11794a171a1364268ed676a24cee2882e47c3018b3648267d2707a0ddf",
    "admission.json": "e5bbf8c0ad2947f42f71819d61b03fcd260a0926b5f5429481e5523ff8e122a5",
    "pose-applicability.json": "9918d4b93c8201f71d0621aff2b3fa2d2391b2eb148da8d4fbe389f712f3d077",
    "pose_applicability.py": "a31ab842ccbd6f6f66e1ca009b29c1e0ad67753e93477cda3f9c013e9878712a",
    "admission.py": "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def canonical(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def exp(vector):
    """Independent Rodrigues formula; no production rotation API."""
    x, y, z = vector
    skew = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    angle = float(np.linalg.norm(vector))
    if angle <= 1e-12:
        return np.eye(3) + skew + .5 * skew @ skew
    return np.eye(3) + np.sin(angle) / angle * skew + (1. - np.cos(angle)) / angle**2 * (skew @ skew)

def log(rotation):
    angle = float(np.arccos(np.clip((np.trace(rotation) - 1.) / 2., -1., 1.)))
    vector = np.array([rotation[2, 1] - rotation[1, 2], rotation[0, 2] - rotation[2, 0],
                       rotation[1, 0] - rotation[0, 1]])
    return .5 * vector if angle < 1e-10 else angle / (2. * np.sin(angle)) * vector

def angle(rotation):
    return float(np.arccos(np.clip((np.trace(rotation) - 1.) / 2., -1., 1.)))

def independent_markers(field, layout, duties):
    q = np.asarray(field["response"]["q"])
    members = {r["member"]: r for r in field["linear_timber_coordinate_map"]["members"]}
    require(len(members) == 20 and all(r["storage_basis_columns_xyz"] == np.eye(3).tolist()
                                    for r in members.values()), "twenty world-storage charts required")
    offset = max(i for r in members.values() for n in r["node_dof_indices"] for i in n) + 1
    fits = {r["angle_id"]: (r, offset + 12 * i) for i, r in enumerate(layout["raw_fittings"])}

    def pose(body, p, flange=None):
        if body in fits:
            r, start = fits[body]
            i = 0 if flange == "beam" else 1
            v = q[start + 6 * i:start + 6 * i + 6]
            c = np.asarray(next(x["entry_xyz_mm"] for x in r["holes"] if x["flange"] == flange))
            u, w, R = v[:3], v[3:] / 1000., exp(v[3:] / 1000.)
        else:
            r = members[body]
            z = np.asarray(r["reference_stations_mm"])
            s = (p - np.asarray(r["reference_start_xyz_mm"])) @ np.asarray(r["reference_axis_xyz"])
            i = int(np.clip(np.searchsorted(z, s) - 1, 0, len(z) - 2))
            t = float(np.clip((s - z[i]) / (z[i + 1] - z[i]), 0., 1.))
            v = q[np.asarray(r["node_dof_indices"])[i:i + 2]]
            c0, c1 = np.asarray(r["node_reference_centers_xyz_mm"])[i:i + 2]
            c, u = (1. - t) * c0 + t * c1, (1. - t) * v[0, :3] + t * v[1, :3]
            w = ((1. - t) * v[0, 3:] + t * v[1, 3:]) / 1000.
            R0, R1 = exp(v[0, 3:] / 1000.), exp(v[1, 3:] / 1000.)
            R = R0 @ exp(t * log(R0.T @ R1))
        return c + u + R @ (p - c), p + u + np.cross(w, p - c), R

    selected = {r["angle_id"] for r in layout["raw_fittings"] if r["duty_id"] in duties}
    groups = {"timber": [], "representative_flanges": []}
    for a in field["contact_actions"]:
        p = np.asarray(a["point_xyz_mm"])
        if a["kind"] == "timber_face_contact":
            group, n, x = "timber", np.asarray(a["direction_xyz"]), pose(a["first"], p)
        elif a["kind"] == "flange_contact" and a["first"] in selected:
            flange = a["id"].split("/")[-2]
            r = fits[a["first"]][0]
            group, n = "representative_flanges", np.asarray(r["v_xyz" if flange == "beam" else "u_xyz"])
            x = pose(a["first"], p, flange)
        else:
            continue
        n = n / np.linalg.norm(n)
        y = pose(a["second"], p)
        groups[group].append({"id": a["id"], "first": a["first"], "second": a["second"],
            "saved_N": a["compression_n"], "linear_mm": float(n @ (x[1] - y[1])),
            "fixed_mm": float(n @ (x[0] - y[0])), "updated_mm": float((y[2] @ n) @ (x[0] - y[0])),
            "material_rotation_rad": angle(y[2].T @ x[2])})
    summary = {}
    for name, rows in groups.items():
        changes = [r for r in rows if (r["linear_mm"] > 0.) != (r["updated_mm"] > 0.)]
        r = max(rows, key=lambda r: r["material_rotation_rad"])
        summary[name] = {"points": len(rows), "loaded": sum(r["saved_N"] > 0. for r in rows),
            "marker_side_changes": len(changes), "loaded_to_opening": sum(r["saved_N"] > 0. and
                r["updated_mm"] > 0. for r in rows), "unloaded_to_closing": sum(r["saved_N"] == 0. and
                r["updated_mm"] < 0. for r in rows),
            "minimum_abs_linear_mm_at_change": min(abs(r["linear_mm"]) for r in changes),
            "minimum_abs_updated_mm_at_change": min(abs(r["updated_mm"]) for r in changes),
            "material_rotation_maximum": {k: r[k] for k in ("id", "first", "second", "material_rotation_rad")}}
    require([list(summary[k].values())[:5] for k in groups] == [[584, 104, 13, 11, 2], [32, 15, 13, 13, 0]],
            "independent marker census differs")
    for name, expected in (("timber", .17325522019157685), ("representative_flanges", .23078771403554427)):
        require(abs(summary[name]["material_rotation_maximum"]["material_rotation_rad"] - expected) < 1e-12,
                "independent all-point material rotation maximum differs")
    cell17 = next(r for r in groups["timber"] if r["id"] ==
                  "timber-face/base_post_outer_left/base_floor_left/1-5-0/cell-17")
    require(abs(cell17["updated_mm"] - .0812907343700095) < 1e-10, "cell17 differs")
    name = "B104ZN_clip_angle_base_left_reference"
    ports = {r["flange"]: np.asarray(r["entry_xyz_mm"]) for r in fits[name][0]["holes"]}
    a, b = pose(name, ports["beam"], "beam"), pose(name, ports["post"], "post")
    internal = {"id": name + "/two-flange-port-pose", "rotation_rad": angle(a[2].T @ b[2]),
        "translation_norm_mm": float(np.linalg.norm(a[2].T @ (b[0] - a[0]) - (ports["post"] - ports["beam"])))}
    require(abs(internal["rotation_rad"] - .02406965033684583) < 1e-12, "internal witness differs")
    return summary, cell17, internal


def review():
    for name, digest in PINS.items():
        require(sha(PACKET / name) == digest, "input changed: " + name)
    spec = importlib.util.spec_from_file_location("reviewed_current_pose_route", PACKET / "pose_applicability.py")
    route = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(route)
    saved = json.loads((PACKET / "pose-applicability.json").read_bytes())
    receipt = json.loads((PACKET / "admission.json").read_bytes())
    require(len(saved["source_sha256"]) == 208, "208 pose source bindings required")
    route.verify(saved["source_sha256"])
    replay = route.consume(PACKET / "a12-rear.json", receipt, expected_field_sha256=PINS["a12-rear.json"],
                           admission_sha256=PINS["admission.py"])
    require(canonical(replay) == canonical(saved), "entire pose output differs on exact replay")
    field = json.loads((PACKET / "a12-rear.json").read_bytes())
    config = json.loads(route.CONFIG.read_bytes())
    layout = json.loads((ROOT / config["layout"]).read_bytes())
    counts, cell17, internal = independent_markers(field, layout, config["duties"])
    for group in ("bearings", "captures"):
        for row in saved["markers"]["representative_governing_markers"][group].values():
            require("gauge_independent_rotation_metric" not in row and
                row["finite_shaft_orientation_is_recorded_zero_linear_roll_lift_marker"] is True and
                row["objective_shaft_or_washer_orientation_recovered"] is False, "shaft qualification absent")
    route.verify(saved["source_sha256"])
    for name, digest in PINS.items():
        require(sha(PACKET / name) == digest, "input changed during arithmetic: " + name)
    return {"schema": "thin_bolted_admitted_pose_independent_numerical_review/v1", "numeric_review_pass": True,
        "inputs": PINS, "pose_source_union_entries": 208,
        "pose_source_union_canonical_sha256": canonical(saved["source_sha256"]),
        "source_bytes_unchanged_before_after": True,
        **{k: saved[k] for k in ("state_id", "field_canonical_sha256", "q_canonical_sha256",
                                "admission_receipt_canonical_sha256")},
        "entire_pose_output_exact_replay": True, "dofs": 8018, "timbers": 20, "patches": 30,
        "pose_only_zero_shaft_roll_gauges": 70, "independent_Rodrigues_results": counts,
        "hand_marker_units": "saved_N is saved first-order compression in N; linear/fixed/updated are opening-positive point projection markers in mm; rotations are radians.",
        "loaded_cell17_witness": cell17, "independent_internal_two_port_witness": internal,
        "timber_governing_values": {k: r[k] for k, r in saved["markers"]["all584_governing_markers"].items()},
        "qualification": [
            "Original-law first-order equilibrium is unchanged. Sliding/orientation and loaded marker side changes leave physical contact applicability unverified.",
            "Fixed-q markers are not actual motion, new forces, finite equilibrium/contact branch, current overlap, pressure or resistance criteria.",
            "Finite shaft/washer orientation remains a zero-roll-lift marker, not a recovered objective orientation.",
            "Internal two-port pose is not actual heel curvature, bending strain or prying strength."],
        "K_unpack_assembly_or_evaluation": False, "global_native_solve_or_CAD": False,
        "forces_branch_or_equilibrium_recomputed": False, "complete_joint_acceptance": False,
        "release": saved["release"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET / "pose-applicability-review.json")
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing numeric review receipt")
    producer_sha = sha(Path(__file__))
    result = review()
    require(sha(Path(__file__)) == producer_sha, "review producer changed during arithmetic")
    result["producer"] = {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": producer_sha}
    result["execution_command_argv"] = [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]]
    result["environment"] = {k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}
    result["tool_versions"] = {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}
    with options.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"producer_sha256": producer_sha, "result_sha256": sha(options.out),
                      "producer_bytes": Path(__file__).stat().st_size, "result_bytes": options.out.stat().st_size}))


if __name__ == "__main__":
    main()
