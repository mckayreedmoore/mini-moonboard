"""Replay one admitted saved field; never prepare, assemble or solve a candidate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
PACKET = OWN.parent.parent
RUN = PACKET / "a12-first-order-v2"
GATE = PACKET / "four-port-method-v1/first_order_admission_v3.py"
FIXED = {
    RUN / "field.json": "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598",
    RUN / "admission-v3.json": "383772d00e6f6c9207a833f5a9a067b6eaa1ca01279eb367c6ef518e41f77ee0",
    RUN / "execution-plan.json": "b7e64565bc67f02a6a93ee1342f2de429a42da390d0852af620670275e4ceb4a",
    RUN / "audit_field.py": "9869c1968b9a931cfef8c572281a32ebe3ad779f305893d7b4bb26b77e8cdb50",
    RUN / "admission-failure.json": "71d10f8c7c6b48a91661af76794dfd2000f9fbe5fbbf8eaa33ea80bffbe02071",
    GATE: "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008",
    OWN.parent / "independent-source-order-gate-method-review.json": "e3abe7cda2817972f31ed57c3c45cddd8529133488aa4ab69db3f1a2ab632fe0",
    OWN.parent / "independent-saved-cut-order-review.json": "f433839887b184ef16dcc4c55c789db26720421a06b1e369ac5fa031d5086632",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "frozen field/receipt/operator/source bytes changed")


def review():
    direct = {str(path.relative_to(ROOT)): digest for path, digest in FIXED.items()}
    verify(direct)
    raw = (RUN / "field.json").read_bytes()
    field = json.loads(raw)
    saved = json.loads((RUN / "admission-v3.json").read_bytes())
    plan = json.loads((RUN / "execution-plan.json").read_bytes())
    pins = dict(direct)
    for inherited in (plan["source_sha256"], field["source_sha256"], saved["source_sha256"]):
        for path, digest in inherited.items():
            require(path not in pins or pins[path] == digest, "source graph join conflict")
            pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    verify(pins)
    before = canonical(pins)
    spec = importlib.util.spec_from_file_location("independent_actual_v3_saved_field_gate", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    require(saved[gate.SUCCESS] is True and saved["source_path"] == str(GATE.relative_to(ROOT))
        and saved["admission_source_sha256"] == FIXED[GATE], "actual source-bound v3 success required")
    require(saved["input_raw_sha256"] == hashlib.sha256(raw).hexdigest()
        and saved["input_canonical_sha256"] == canonical(field), "receipt binds a different raw or canonical field")
    require(field["operator_bundle"] == saved["operator_bundle"]
        and field["original_operator_fingerprint_sha256"] == saved["original_operator_fingerprint_sha256"],
        "actual original artifact/operator identity differs")
    for record in saved["operator_bundle"].values():
        require(sha(ROOT / record["path"]) == record["sha256"], "raw operator artifact changed")

    start = time.monotonic()
    replay = gate.audit_first_order_state(raw)  # Exactly one saved-operator replay, no solve.
    elapsed = time.monotonic() - start
    require(canonical(replay) == canonical(saved), "full independent replay differs from issued saved receipt")
    consumed, consumer_pins = gate.require_admitted_payload(raw, saved, admission_sha256=FIXED[GATE])
    require(consumed == field and all(pins.get(path) == digest for path, digest in consumer_pins.items()),
        "actual exact-byte consumer returns changed field or source graph")
    require(saved["release"] == gate.core.RELEASE and all(value is False for value in saved["release"].values())
        and saved["physical_demand_bounds_established"] is False
        and saved["first_order_physical_applicability_established"] is False,
        "numerical admission was promoted to physical applicability or release")
    law = saved["original_law_checks"]
    global_residual = np.asarray(law["global_residual_n_nmm"])
    global_force = float(np.linalg.norm(global_residual[:3]))
    global_moment = float(np.linalg.norm(global_residual[3:]))
    require(law["physical_body_count"] == 150 and law["gradient_inf_n"] < 1e-5
        and law["maximum_body_force_norm_n"] < 1e-4 and law["maximum_body_moment_about_reference_norm_nmm"] < .1
        and global_force < 1e-4 and global_moment < .1, "original numerical closure criteria fail")
    require(saved["loaded_recovery_checks"]["loaded_root_recoveries_replayed"] == 22
        and saved["loaded_recovery_checks"]["own_surface_aggregate_recoveries_replayed"] == 208
        and saved["loaded_recovery_checks"]["own_signed_external_action_shaft_cut_recoveries_replayed"] == 100,
        "actual fitting/surface/cut recovery census differs")
    require(saved["applied_load_checks"]["distributed_panel_rhs_independently_regenerated"] is False
        and saved["applied_load_checks"]["distributed_panel_rhs_is_exact_source_authenticated_capture"] is True,
        "captured panel RHS limit was omitted")
    verify(pins)
    return {
        "schema": "independent_eoere_actual_saved_admission_review/v1",
        "disposition": "PASS_UNCHANGED_CONDITIONAL_FIRST_ORDER_NUMERICAL_FIELD_REPLAY",
        "direct_source_sha256": direct,
        "inherited_source_binding": {"plan_source_count": len(plan["source_sha256"]),
            "field_source_count": len(field["source_sha256"]), "admission_source_count": len(saved["source_sha256"]),
            "plan_source_map_sha256": canonical(plan["source_sha256"]), "field_source_map_sha256": canonical(field["source_sha256"]),
            "admission_source_map_sha256": canonical(saved["source_sha256"]), "merged_source_count": len(pins),
            "merged_map_before_after_sha256": [before, canonical(pins)], "all_pinned_bytes_unchanged": True},
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")},
            "saved_operator_replay_count": 1, "saved_operator_replay_seconds": elapsed},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "field_identity": {key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "field_bytes": len(raw), "field_canonical_sha256": canonical(field),
        "final_q_canonical_sha256": field["response"]["q_canonical_sha256"],
        "full_signed_gradient_canonical_sha256": field["response"]["gradient_canonical_sha256"],
        "issued_receipt_canonical_sha256": canonical(saved), "fresh_replay_receipt_canonical_sha256": canonical(replay),
        "full_receipt_replay_equal": True, "actual_cheap_same_byte_api_pass": True,
        "operator_bundle": saved["operator_bundle"], "original_operator_fingerprint_sha256": saved["original_operator_fingerprint_sha256"],
        "numerical_closure": {**law, "global_force_norm_n": global_force, "global_moment_norm_nmm": global_moment},
        "owned_port_checks": saved["owned_port_checks"], "applied_load_checks": saved["applied_load_checks"],
        "loaded_recovery_checks": saved["loaded_recovery_checks"], "support_search_checks": saved["support_search_checks"],
        "admission_compatibility_correction": saved["admission_compatibility_correction"],
        "admission_recovery_order_correction": saved["admission_recovery_order_correction"],
        "motion_marker_maxima": {key: value for key, value in saved["motion_diagnostics"].items()
            if key not in {"timber_node_translation_rows", "timber_node_rotation_rows"}},
        "confirmed_discrepancies": [],
        "limits": ["The immutable failed bfb admission remains preserved. The distinct v3 context fixes only authenticated source-list iteration order and prior absent-flag/source-label compatibility; original field tables and producer algorithms are unchanged.",
            "One saved original-operator replay and exact-byte consumer call executed. No candidate preparation, global material-K assembly, Newton/search step, CAD/native run, geometry change or new force field.",
            "Distributed panel RHS and material K are authenticated captured outputs rather than independently regenerated. Full ownership, nonpanel load work, same-q gradient/floor law, paired actions and body/global closure are checked.",
            "Linear motion markers do not establish finite geometry/contact/pressure or physical movement. Gross-stock/four-strip stiffness and material/end/heel/contact datums remain conditional; numerical admission supplies no strength or complete-joint release."],
        "release": {"conditional_numerical_field_replay_verified": True, "physical_applicability": False,
            "capacity": False, "complete_joint_acceptance": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve every prior review output; do not repeat replay on existing path")
    result = review()
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"path": str(args.out), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "pins": result["inherited_source_binding"]["merged_source_count"], "replay_seconds": result["execution"]["saved_operator_replay_seconds"]}))


if __name__ == "__main__":
    main()
