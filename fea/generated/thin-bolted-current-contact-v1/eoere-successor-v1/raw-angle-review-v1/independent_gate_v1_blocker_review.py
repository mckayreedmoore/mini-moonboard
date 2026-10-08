"""Reproduce two original gate contract defects on the existing five-owner toy."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import scipy

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent / "four-port-method-v1"
EXPECTED = {
    "first_order_admission.py": "e61ee415f0a8cd83f3ea4b0606064bceb128413eed4e66f1192955b1610ff66b",
    "test_first_order_admission.py": "2f39c367d3d3162b842156268206363064063a4cf5a7b8dcf3ad61b4e2d64bbe",
    "run_first_order.py": "28ceafcb9eac9764358071b728da96fbb2e5cd46011ead031ade8a9d7a811a39",
    "first_order_factory.py": "5ca9a2018cc8a45fbddcf929f446cdd22b9d5fcae6ba816959de2c897b464570",
    "test_first_order_factory.py": "98386e0d2225670414707850365e5d71e8fed34f83a6acc00c71224983057866",
}
MUTATIONS = (
    ("foreign-flange", "common_shaft_steel_port_actions", "flange", "foreign-port"),
    ("foreign-receiver", "common_shaft_steel_port_actions", "receiver", "foreign-wood"),
    ("foreign-angle", "common_shaft_steel_port_actions", "angle_id", "foreign-angle"),
    ("foreign-grain", "common_shaft_wood_bearing_actions", "grain_axis_xyz", [0., 1., 0.]),
    ("foreign-member", "common_shaft_wood_bearing_actions", "member", "foreign-wood"),
    ("foreign-interval", "common_shaft_steel_port_actions", "surface_interval_mm", [99., 100.]),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    if not all(sha(ROOT / path) == digest for path, digest in pins.items()):
        raise ValueError("reviewed source bytes changed")


def review():
    pins = {str((LEAF / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()}
    verify(pins)
    spec = importlib.util.spec_from_file_location("independent_original_gate_blockers", LEAF / "test_first_order_admission.py")
    toy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(toy)
    gate = toy.gate
    for path, digest in gate.source_pins().items():
        if path in pins and pins[path] != digest:
            raise ValueError("source join conflict")
        pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    verify(pins)
    before = canonical(pins)

    # Exactly the frozen factory fixture: five synthetic owners, not a
    # successor input or a physical equilibrium. No numerical step is taken.
    data, panels, integrated = toy.toy.toy()
    prepared = gate.factory.prepare_synthetic(data, panels, integrated)
    chart = gate.bundle.coordinate_map(prepared)
    snapshot = SimpleNamespace(assembly=prepared.assembly, applied=prepared.applied,
        groups=prepared.groups, contacts=prepared.contacts, tangents=prepared.tangents,
        case=prepared.case, coordinate_map=chart,
        manifest={"fitting_descriptors": [el.descriptor() for el in prepared.fittings.values()]})
    q = np.random.default_rng(13).normal(size=prepared.assembly.ndof) * .001
    fresh = gate.replay_original(snapshot, q, ["wood-a"])
    response = {"converged": True, "q": q, "connector_local_force_n": fresh[3],
        "normal_contact_force_n": fresh[4], "nonbearing_no_slip_removed": [],
        "support_state_search_v1": {"accepted_enabled_centroid_xy_hosts": ["wood-a"]}}
    recovered = gate.core.recover(prepared, response)
    recovered["source_inputs"] = data
    maps = gate.OwnedMaps(snapshot, data)
    baseline = gate.verify_fitting_and_alias_recovery(recovered, snapshot, maps, q)
    if "usable_conditional_actions" in recovered:
        raise ValueError("original missing-flag defect no longer reproduced")
    observed = []
    for name, table, key, value in MUTATIONS:
        changed = copy.deepcopy(recovered)
        original = copy.deepcopy(changed[table][0][key])
        changed[table][0][key] = value
        gate.verify_fitting_and_alias_recovery(changed, snapshot, maps, q)
        observed.append({"name": name, "table": table, "key": key,
            "original": original, "forged": value, "incorrectly_accepted_by_original_gate": True})
    verify(pins)
    return {
        "schema": "independent_eoere_original_field_gate_blocker_review/v1",
        "disposition": "BLOCKED_ORIGINAL_GATE_METHOD_BEFORE_PRODUCTION",
        "source_sha256": pins, "source_count": len(pins),
        "source_manifest_before_after_sha256": [before, canonical(pins)], "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "focused_verification": {"original_fixture_result": "34 passed in 2.87s", "ruff": "original gate and test paths passed",
            "command": [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                str((LEAF / "test_first_order_admission.py").relative_to(ROOT))]},
        "known_answer_scope": {"physical_owner_count": prepared.counts["physical_bodies"], "synthetic_only": True,
            "arbitrary_fixture_q_is_not_claimed_in_equilibrium": True, "numerical_step_taken": False,
            "loaded_recovery_baseline": baseline},
        "confirmed_blockers": [
            {"name": "incompatible_historical_usability_flag", "producer_recovery_emits_flag": False,
                "original_full_and_cheap_gate_require_true": True,
                "consequence": "A genuine converged frozen producer output is rejected before independent checks."},
            {"name": "unverified_source_alias_labels", "mutations": observed,
                "consequence": "Forces and signed cuts can pass while own flange, receiver, grain or interval labels are false."}],
        "correction_scope": "Parent directs a distinct gate correction only; original gate/test and frozen producer/model bytes remain preserved.",
        "limits": ["Only the existing five-owner factory fixture and its component recovery ran. No candidate input, candidate assembly, candidate q, global solve, CAD or native execution consumed.",
            "The observed mutation passes are component-gate defects; this receipt does not fabricate a full 150-owner field admission.",
            "Distributed panel RHS is captured/source-authenticated rather than independently regenerated; that accepted method limit is unchanged.",
            "No first-order physical applicability, pressure, resistance, fabrication or climbing release established."],
        "release": {"gate_method_ready": False, "candidate_evaluated": False, "field_admitted": False,
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
        "source_count": result["source_count"], "disposition": result["disposition"]}))


if __name__ == "__main__":
    main()
