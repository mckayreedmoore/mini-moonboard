"""Read source identities and replay the existing small gate fixtures only."""
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
    "first_order_admission_v2.py": "bfb984c47372d20387883d11d1d49f8a12d9debda1b0c78f1c024ace01bc2821",
    "test_first_order_admission_v2.py": "997e7771ffdba725d2a7b0bd18a1e5e7e1b82e9fd8098ccde4ff93ea8f0332c6",
    "first_order_admission.py": "e61ee415f0a8cd83f3ea4b0606064bceb128413eed4e66f1192955b1610ff66b",
    "test_first_order_admission.py": "2f39c367d3d3162b842156268206363064063a4cf5a7b8dcf3ad61b4e2d64bbe",
}
PRIOR = {
    "independent-original-gate-blocker-review.json": "4ff9b4a8f2e817f56ab0ddef8f11e6c8d9dd84870c141aaef765387fefe846fc",
    "independent-operator-v2-method-review.json": "56201ebf7d9d420bcf6f5271b5271c404643115b3441ac36cc87cd6e7e3106c5",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "source bytes changed")


def import_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hand_fields(snapshot, q, enabled):
    """Direct quadratic, radial-gap and positive-part arithmetic; no frozen force call."""
    applied = snapshot.applied
    gradient = np.asarray(snapshot.assembly.K @ q).ravel() - applied
    energy = .5 * float(q @ (snapshot.assembly.K @ q)) - float(q @ applied)
    for row in snapshot.tangents:
        if row["first"] in enabled:
            value = float((row["B"] @ q)[0])
            gradient += np.asarray(row["B"].T @ [row["stiffness"] * value]).ravel()
            energy += .5 * row["stiffness"] * value**2
    for row in snapshot.groups:
        value = np.asarray(row["B"] @ q).ravel()
        axial = max(float(value[0]), 0.) if row["tension_only"] else float(value[0])
        radius = float(np.hypot(value[1], value[2]))
        extension = max(radius - row["clearance"], 0.)
        force = np.array([row["ka"] * axial, 0., 0.])
        if radius > row["clearance"]:
            force[1:] = row["kl"] * extension / radius * value[1:]
        gradient += np.asarray(row["B"].T @ force).ravel()
        energy += .5 * row["ka"] * axial**2 + .5 * row["kl"] * extension**2
    for row in snapshot.contacts:
        closing = max(float((row["B"] @ q)[0]), 0.)
        gradient += np.asarray(row["B"].T @ [row["stiffness"] * closing]).ravel()
        energy += .5 * row["stiffness"] * closing**2
    return gradient, energy


def rejected(call):
    try:
        call()
    except ValueError:
        return True
    return False


def review():
    pins = {str((LEAF / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()}
    for name, digest in PRIOR.items():
        path = OWN.parent / name
        require(sha(path) == digest, "prior evidence bytes changed")
        prior = json.loads(path.read_bytes())
        for key, value in prior["source_sha256"].items():
            require(key not in pins or pins[key] == value, "prior source join conflict")
            pins[key] = value
        pins[str(path.relative_to(ROOT))] = digest
    verify(pins)
    fixtures = import_path("independent_corrected_gate_small_fixtures", LEAF / "test_first_order_admission_v2.py")
    gate = fixtures.gate
    for path, digest in gate.source_pins().items():
        require(path not in pins or pins[path] == digest, "new source join conflict")
        pins[path] = digest
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    verify(pins)
    before = canonical(pins)
    identity = {key: gate.base.__dict__[key] for key in ("OWN", "LOADED_SHA", "__file__",
        "audit_first_order_state", "require_admitted_payload", "verify_fitting_and_alias_recovery")}

    # Genuine existing five-owner fixture only; one tiny construction. All
    # trial vectors below are prescribed arbitrary component markers, not
    # equilibrium states or successor inputs. No numerical solve is called.
    data, panels, integrated = fixtures.coupon.toy.toy()
    prepared = gate.base.factory.prepare_synthetic(data, panels, integrated)
    partitions = {name: [{**gate.core.descriptor(row), "B": row["B"].copy()} for row in getattr(prepared, name)]
        for name in ("groups", "contacts", "tangents")}
    snapshot = SimpleNamespace(assembly=prepared.assembly, applied=prepared.applied, case=prepared.case,
        **partitions, coordinate_map=gate.base.bundle.coordinate_map(prepared), rigid_modes=prepared.assembly.rigid_modes(),
        manifest={"fitting_descriptors": [el.descriptor() for el in prepared.fittings.values()]})
    rows = [*snapshot.groups, *snapshot.contacts, *snapshot.tangents]
    raw_before = [(row["B"].data.tobytes(), row["B"].indices.tobytes(), row["B"].indptr.tobytes()) for row in rows]
    maps = gate.base.OwnedMaps(snapshot, data)
    ports = gate.base.verify_ports(snapshot, maps, data)
    loads = gate.base.verify_load_work(snapshot, maps, data)
    trials, mutation_results = [], []
    vectors = [np.zeros(prepared.assembly.ndof), np.random.default_rng(13).normal(size=prepared.assembly.ndof) * .001]
    for q in vectors:
        fresh = gate.base.replay_original(snapshot, q, ["wood-a"])
        hand_gradient, hand_energy = hand_fields(snapshot, q, {"wood-a"})
        gradient_error = float(np.max(abs(hand_gradient - fresh[0])))
        energy_error = abs(hand_energy - fresh[1])
        require(gradient_error < 1e-7 and energy_error < 1e-8, "independent hand potential/gradient differs")
        response = {"converged": True, "q": q, "connector_local_force_n": fresh[3],
            "normal_contact_force_n": fresh[4], "nonbearing_no_slip_removed": [],
            "support_state_search_v1": {"accepted_enabled_centroid_xy_hosts": ["wood-a"]}}
        recovered = gate.core.recover(prepared, response)
        recovered["source_inputs"] = data
        require("usable_conditional_actions" not in recovered, "original producer flag contract differs")
        recovery = gate.verify_fitting_and_alias_recovery(recovered, snapshot, maps, q)
        trials.append({"q_kind": "zero" if not np.any(q) else "prescribed seed13 small component marker",
            "hand_gradient_max_error_n": gradient_error, "hand_potential_error_nmm": energy_error,
            "loaded_recovery": recovery, "claimed_in_equilibrium": False})
        for name, table, key, value in (
            ("flange", "common_shaft_steel_port_actions", "flange", "foreign-port"),
            ("receiver", "common_shaft_steel_port_actions", "receiver", "foreign-wood"),
            ("angle", "common_shaft_steel_port_actions", "angle_id", "foreign-angle"),
            ("interval", "common_shaft_steel_port_actions", "surface_interval_mm", [99., 100.]),
            ("member", "common_shaft_wood_bearing_actions", "member", "foreign-wood"),
            ("grain", "common_shaft_wood_bearing_actions", "grain_axis_xyz", [0., 1., 0.])):
            changed = copy.deepcopy(recovered)
            changed[table][0][key] = value
            require(rejected(lambda: gate.verify_fitting_and_alias_recovery(changed, snapshot, maps, q)),
                "reported source alias defect still accepted")
            mutation_results.append({"trial": trials[-1]["q_kind"], "source_label": name, "rejected": True})
    require(raw_before == [(row["B"].data.tobytes(), row["B"].indices.tobytes(), row["B"].indptr.tobytes()) for row in rows],
        "port or original gradient replay changed raw CSR rows")

    # Explicitly synthetic receipt-binding protocol, not a full field audit.
    field = fixtures.minimal_pending()
    raw = json.dumps(field).encode()
    receipt = fixtures.contract_receipt(field, raw)
    parsed, _ = gate.require_admitted_payload(raw, receipt, admission_sha256=gate.LOADED_SHA)
    require(parsed == field and "usable_conditional_actions" not in parsed, "new exact-byte consumer contract differs")
    require(rejected(lambda: gate.require_admitted_payload(raw + b" ", receipt, admission_sha256=gate.LOADED_SHA)),
        "same canonical field with changed raw bytes accepted")
    changed = copy.deepcopy(field)
    changed["response"]["q"][0] = .1
    changed_raw = json.dumps(changed).encode()
    changed_receipt = copy.deepcopy(receipt)
    changed_receipt.update(input_raw_sha256=hashlib.sha256(changed_raw).hexdigest(), input_canonical_sha256=canonical(changed))
    require(rejected(lambda: gate.require_admitted_payload(changed_raw, changed_receipt, admission_sha256=gate.LOADED_SHA)),
        "changed q accepted after repairing only outer byte/canonical digests")
    require(rejected(lambda: gate.require_admitted_payload(raw, receipt, admission_sha256=gate.base.LOADED_SHA)),
        "historical gate SHA accepted as actual new method")
    require({key: gate.base.__dict__[key] for key in identity} == identity, "original module identity/global changed")
    verify(pins)
    return {
        "schema": "independent_eoere_corrected_field_gate_method_review/v1",
        "disposition": "READY_BOUNDED_CORRECTED_GATE_METHOD_ONLY",
        "source_sha256": pins, "source_count": len(pins),
        "source_manifest_before_after_sha256": [before, canonical(pins)], "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "focused_verification": {"original": "34 passed in 2.87s", "distinct_correction": "27 passed in 3.60s",
            "ruff": "both corrected source/test paths passed; original source/test lint passed earlier",
            "command": [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                str((LEAF / "test_first_order_admission_v2.py").relative_to(ROOT))]},
        "independent_small_checks": {"physical_owner_count": prepared.counts["physical_bodies"], "full_dof_count": prepared.assembly.ndof,
            "port_checks": ports, "load_work_checks": loads, "prescribed_trials": trials,
            "original_reported_alias_mutations_rejected": mutation_results,
            "raw_CSR_bytes_preserved_after_owned_port_and_gradient_replay": True,
            "cheap_synthetic_binding_only": {"successful_exact_byte_contract": True,
                "changed_raw_whitespace_rejected": True, "changed_q_with_repaired_outer_digests_rejected": True,
                "old_gate_SHA_rejected": True, "full_field_audit_or_150_body_admission_asserted": False}},
        "reviewed_contract": [
            "Actual v2 raw exporter/driver, full coordinate charts, immutable source/review/raw artifacts and original state recipe are authenticated before accepting current coefficients.",
            "Original native CSR order and original K/RHS/B laws replay full same-q signed gradient, energy, connector forces, compression and strict whole-host N>1e-7 centroid activation; tolerance remains 1e-5N.",
            "Every physical owner, owned point port, full rigid-load work, nonpanel affine/point load and body/global wrench closure is checked. Actual 150-owner admission is deferred to the future field.",
            "Genuine loaded heel, four strip roots, two own flanges, exact wood/steel source aliases and signed shaft cuts are replayed. Zero-force raw paths still require exact source metadata.",
            "Two copied private function contexts remove only the absent historical flag clauses. Original module globals/__file__, producer, model and all physical algorithms remain unchanged.",
            "New gate receipts carry actual new path/SHA and explicit correction provenance. Cheap consumers require the exact same raw bytes, state/q/gradient, raw operators, all action-table digests and source closure.",
            "Motion diagnostics report own linear point/node/relative-strip markers without an adopted physical small-motion or contact threshold."],
        "confirmed_blockers": [],
        "limits": [
            "Distributed panel RHS is exact captured/source-authenticated output, not independently regenerated. Material K is authenticated saved output, not independently rebuilt by the gate.",
            "Only the prior five-owner tiny fixture, prescribed non-equilibrium component markers and synthetic cheap receipt protocol were consumed; no candidate inputs/q/K, global solve, CAD, native run or actual field admission.",
            "First-order gross-stock/four-strip/reference-point spring scenario and unmeasured stiffness/material/end/heel datums remain conditional; no pressure, physical demand bound, strength, finite contact or complete-joint acceptance."],
        "release": {"bounded_gate_method_ready": True, "candidate_evaluated": False, "independent_field_admitted": False,
            "physical_applicability": False, "capacity": False, "fabrication": False, "climbing": False},
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
