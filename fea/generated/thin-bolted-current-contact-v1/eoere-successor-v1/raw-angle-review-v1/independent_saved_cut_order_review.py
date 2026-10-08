"""Audit frozen saved shaft cuts by owner; never unpack K or evaluate a field."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import scipy

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
PACKET = OWN.parent.parent
RUN = PACKET / "a12-first-order-v2"
GATE = PACKET / "four-port-method-v1/first_order_admission_v2.py"
FIXED = {
    RUN / "field.json": "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598",
    RUN / "execution-plan.json": "b7e64565bc67f02a6a93ee1342f2de429a42da390d0852af620670275e4ceb4a",
    RUN / "admission-failure.json": "71d10f8c7c6b48a91661af76794dfd2000f9fbe5fbbf8eaa33ea80bffbe02071",
    RUN / "run_admission.py": "1409646b72ef2be201d170e2498694563acef3f965c3e2948b533b58da6ff6fd",
    GATE: "bfb984c47372d20387883d11d1d49f8a12d9debda1b0c78f1c024ace01bc2821",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "frozen source or output bytes changed")


def hand_cut(shaft, station, loads):
    """Explicit lower-part equilibrium; independent scalar cross products and fsum."""
    origin, basis = shaft["point"], shaft["basis"]
    point = [origin[i] + basis[0][i] * station for i in range(3)]
    lower = [(p, f) for p, f in loads if math.fsum((p[i] - origin[i]) * basis[0][i] for i in range(3)) < station]
    force = [-math.fsum(f[i] for _, f in lower) for i in range(3)]
    moment = []
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        moment.append(-math.fsum((p[j] - point[j]) * f[k] - (p[k] - point[k]) * f[j] for p, f in lower))
    return point, [math.fsum(basis[i][j] * value[j] for j in range(3)) for value in (force, moment) for i in range(3)]


def review():
    direct = {str(path.relative_to(ROOT)): digest for path, digest in FIXED.items()}
    verify(direct)
    field = json.loads((RUN / "field.json").read_bytes())
    plan = json.loads((RUN / "execution-plan.json").read_bytes())
    pins = dict(direct)
    for inherited in (plan["source_sha256"], field["source_sha256"]):
        for path, digest in inherited.items():
            require(path not in pins or pins[path] == digest, "source identity join conflict")
            pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    verify(pins)
    before = canonical(pins)
    pointer = field["operator_bundle"]["manifest"]
    require(sha(ROOT / pointer["path"]) == pointer["sha256"], "captured geometry chart changed")
    manifest = json.loads((ROOT / pointer["path"]).read_bytes())
    spec = importlib.util.spec_from_file_location("independent_saved_cut_order_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    source = {row["body"]: row for row in field["source_inputs"]["shafts"]}
    maps = {name: {**source[name], **row, "point": np.asarray(row["point"]),
        "basis": np.asarray(row["basis"]), "stations": np.asarray(row["stations"])}
        for name, row in manifest["coordinate_map"]["shafts"].items()}
    view = SimpleNamespace(shafts=maps, parameters={"shaft_diameter_scale":
        field["source_inputs"]["scenario"]["common_shaft_parameters"].get("diameter_scale", 1.)})
    expected = gate.base.factory.common.CommonShaftSystem.section_cut_actions(view, manifest["case"],
        field["common_shaft_bearing_actions"], field["shaft_end_capture_actions"])
    saved = field["common_shaft_section_cut_actions"]
    by_body = {row["body"]: row for row in saved}
    require(len(by_body) == len(saved) == len(expected) == len(source) == 100 and set(by_body) == set(source),
        "exact physical shaft/cut owner census differs")
    require([row["body"] for row in saved] == [row["body"] for row in field["source_inputs"]["shafts"]],
        "actual cut export must preserve authenticated source-list order")
    for row in expected:
        gate.base.compare_tree(by_body[row["body"]], row)
    require(saved[0]["body"] != expected[0]["body"], "original positional order defect no longer reproduced")
    witnesses = []
    for index in (0, 4, 88, 96, 99):
        row = saved[index]
        shaft = source[row["body"]]
        loads = [(value["point_xyz_mm"], value["force_xyz_n"]) for value in field["body_applied_loads"]
            if value["body"] == row["body"]]
        loads += [(value["point_xyz_mm"], value["force_on_first_xyz_n"])
            for value in [*field["common_shaft_bearing_actions"], *field["shaft_end_capture_actions"]]
            if value["first"] == row["body"]]
        cut = row["cuts"][len(row["cuts"]) // 2]
        point, action = hand_cut(shaft, cut["station_from_axis_point_mm"], loads)
        point_error = float(np.max(abs(np.asarray(point) - cut["point_xyz_mm"])))
        action_error = float(np.max(abs(np.asarray(action) - cut["local_N_V1_V2_T_M1_M2_n_nmm"])))
        require(point_error < 1e-9 and action_error < 1e-7, "independent lower-part equilibrium arithmetic differs")
        witnesses.append({"axis_id": row["axis_id"], "body": row["body"],
            "station_from_axis_point_mm": cut["station_from_axis_point_mm"],
            "hand_signed_N_V1_V2_T_M1_M2_n_nmm": action,
            "maximum_point_error_mm": point_error, "maximum_action_error_n_nmm": action_error})
    verify(pins)
    return {
        "schema": "independent_eoere_saved_shaft_cut_order_review/v1",
        "disposition": "PASS_SAVED_OWN_SHAFT_CUT_REPLAY_ONLY",
        "direct_source_sha256": direct,
        "inherited_source_binding": {"plan_source_count": len(plan["source_sha256"]),
            "plan_source_map_sha256": canonical(plan["source_sha256"]), "field_source_count": len(field["source_sha256"]),
            "field_source_map_sha256": canonical(field["source_sha256"]), "merged_source_count": len(pins),
            "merged_source_map_before_after_sha256": [before, canonical(pins)], "all_pinned_bytes_unchanged": True},
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "field_identity": {key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "field_canonical_sha256": canonical(field), "final_q_canonical_sha256": field["response"]["q_canonical_sha256"],
        "full_field_q_not_evaluated_in_this_cut_review": True,
        "saved_export_checks": {"owned_shaft_count": len(saved), "signed_cut_count": sum(len(row["cuts"]) for row in saved),
            "all_complete_records_pass_frozen_compare_tree_after_exact_body_join": True,
            "export_order_equals_authenticated_source_list": True,
            "saved_first_axis": saved[0]["axis_id"], "JSON_sorted_map_first_axis": expected[0]["axis_id"],
            "failure_is_positional_owner_order_only": True, "independent_hand_witnesses": witnesses},
        "smallest_compatible_correction": "A distinct gate recovery context uses authenticated source-list order for the same owned map rows. Do not change field, vectors, cut records, law or producer.",
        "limits": ["Only immutable JSON/source bytes and genuine external-load cut recovery were read. NPZ was hashed as inherited evidence; no K unpack/build, candidate preparation, q evaluation, solve, CAD or native execution.",
            "Full-field admission previously failed and remains separate. This verifies exported first-order signed shaft cuts, not physical demand bounds, shank/thread delivery, pressure, strength, finite contact or release."],
        "release": {"independent_field_admitted": False, "physical_applicability": False,
            "capacity": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"path": str(args.out), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "pins": result["inherited_source_binding"]["merged_source_count"]}))


if __name__ == "__main__":
    main()
