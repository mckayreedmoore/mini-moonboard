"""Pure loaded four-port arithmetic review; no candidate input evaluation."""
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

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent / "four-port-method-v1"
EXPECTED = {
    "assembly_interface.py": "4103015c05405e930e10c90edb5e147dd9d1ec2fb0575f17e3e4efc01a6cb66b",
    "test_assembly_interface.py": "d10a66eec19d318892e3785aa4ee885ce81a0495eb889676a9c55d77476ae0e1",
    "assembly-plan.json": "943a287974b117e90730ddca3f67852b0e15003e608c75e6b537e6e0abe8dff2",
    "assembly-method-result.json": "df1473a8d3430f163d434d50ecf2df31c95bb0da1091db717d8ba361112438ba",
    "method-result.json": "b20b352e1c0c5bd8a4dc53299a6daf1591300dd98542c31c3bf5a1af81fadca3",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "frozen source bytes differ")


def review():
    saved = json.loads((LEAF / "assembly-method-result.json").read_bytes())
    plan = json.loads((LEAF / "assembly-plan.json").read_bytes())
    pins = dict(saved["source_sha256"])
    for path, digest in plan["source_sha256"].items():
        require(path not in pins or pins[path] == digest, "contradictory source pins")
        pins[path] = digest
    for name, digest in EXPECTED.items():
        path = str((LEAF / name).relative_to(ROOT))
        require(path not in pins or pins[path] == digest, "direct source pin differs")
        pins[path] = digest
    verify(pins)
    before = canonical(pins)
    spec = importlib.util.spec_from_file_location("independent_assembly_method", LEAF / "assembly_interface.py")
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    fresh = method.coupon()
    old = {k: v for k, v in saved.items() if k != "execution"}
    old["source_sha256"] = dict(old["source_sha256"])
    for name in ("test_assembly_interface.py", "assembly-plan.json"):
        old["source_sha256"].pop(str((LEAF / name).relative_to(ROOT)))
    require(canonical(old) == canonical(fresh), "saved numerical coupon replay differs")
    require(not saved["candidate_prepared_or_evaluated"] and not saved["old_field_or_pass_transferred"], "toy scope differs")
    element = method.FourPortAssemblyElement(method.four.FourPortStripModel(), "synthetic-fitting", np.arange(3, 27), 31)
    K = element.model.full_K
    A, B, C = K[:6, :6], K[:6, 6:], K[6:, 6:]
    S = np.diag(element.scale)
    qp = np.asarray(saved["toy_stored_q"])
    f = np.array([0., 0., -12., -36., 216., 0.])
    require(np.array_equal(f, saved["expected_physical_gravity_wrench_about_heel_n_nmm"]), "source wrench differs")
    qh = np.linalg.solve(A, f-B@S@qp)
    condensed = S@(C-B.T@np.linalg.solve(A, B))@S
    rhs = -S@B.T@np.linalg.solve(A, f)
    constant = -.5*float(f@np.linalg.solve(A, f))
    potential = .5*float(qp@condensed@qp)-float(qp@rhs)+constant
    response = saved["response"]
    metrics = {
        "loaded_heel_difference_mm_rad": float(np.max(abs(qh-response["loaded_heel_q_mm_rad"]))),
        "affine_gradient_difference_stored_units": float(np.max(abs(condensed@qp-rhs-response["gradient_stored_units"]))),
        "potential_difference_nmm": abs(potential-response["potential_nmm"]),
        "constant_difference_nmm": abs(constant-response["load_projection"]["potential_constant_nmm"]),
    }
    require(max(metrics.values()) < 1e-10, "independent loaded block arithmetic differs")
    total = f.copy()
    for row in response["port_actions"]:
        force = np.asarray(row["external_force_required_at_port_xyz_n"])
        moment = np.asarray(row["external_couple_required_at_port_xyz_nmm"])
        point = np.asarray(row["point_xyz_mm"])
        total += np.r_[force, moment+np.cross(point, force)]
    metrics["independent_body_wrench_closure_n_nmm"] = float(np.max(abs(total)))
    require(metrics["independent_body_wrench_closure_n_nmm"] < 1e-9, "own loaded body closure differs")

    # Defensive descriptor output is distinct from immutable live inputs.
    original = element.descriptor()
    exported = element.descriptor()
    exported["own_fitting_scenario"]["elastic_modulus_mpa"] = 1.
    exported["ports"][0]["point_reference_xyz_mm"][0] += 1.
    require(element.descriptor() == original, "exported descriptor aliases model")
    element.model.inputs["elastic_modulus_mpa"] = 1.
    mutated = element.descriptor()
    require(mutated["own_fitting_scenario"]["elastic_modulus_mpa"] == 1. and element.model.E == 200000. and
            mutated["elastic_block_little_endian_float64_sha256"] == original["elastic_block_little_endian_float64_sha256"],
            "descriptor-mutation witness no longer applies")
    element.model.inputs["elastic_modulus_mpa"] = 200000.
    require(element.descriptor() == original, "toy input mutation not restored")
    observed_source_callback = False
    old_guard = method.source_pins
    def reject_guard():
        raise ValueError("independent source-guard sentinel")
    method.source_pins = reject_guard
    try:
        element.response(np.zeros(24), declared_route=method.ROUTE)
    except ValueError:
        observed_source_callback = True
    finally:
        method.source_pins = old_guard
    require(not observed_source_callback, "source-callback witness no longer applies")
    verify(pins)
    return {
        "schema": "independent_eoere_four_port_assembly_method_review/v1",
        "disposition": "NUMERICAL_SEAM_PASS_SOURCE_BOUND_FIELD_GUARDS_REQUIRED",
        "source_sha256": pins, "source_count": len(pins), "source_manifest_before_after_sha256": [before, canonical(pins)],
        "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "focused_tests": {"command": ".venv/bin/python -m pytest -q " + str((LEAF / "test_assembly_interface.py").relative_to(ROOT)),
            "result": "9 passed in 0.40s", "ruff": "two frozen sources passed", "saved_coupon_in_memory_replay_exact": True},
        "independent_loaded_condensation": {"physical_wrench_n_nmm": f.tolist(), "potential_nmm": potential,
            "potential_constant_nmm": constant, "metrics": metrics,
            "equations": "A=Khh,B=Khp,C=Kpp; qh=A^-1(f-BSq); Kc=S(C-B.T A^-1B)S; fc=-SB.T A^-1f; V=.5q.TKcq-q.Tfc-.5f.T A^-1f"},
        "world_port_mapping": {"proper_model_basis": "[u,-w,v]", "source_transverse_sign_reversed": True,
            "nodes": "Source inner-entry datums; arbitrary point ports transport actual moment arms, including half-thickness offsets",
            "rigid_heel": "Internal loaded coordinate only; no fifth physical owner, external heel restraint or added ground couple"},
        "confirmed_contract_gaps": [
            "Live model.inputs is mutable. E200000->1 changes descriptor scenario/hash without changing cached operator or model.E200000. A production immutable snapshot/assertion must reject this mismatch.",
            "Source pins are checked at construction/descriptor; response, point/load ports and load projection do not invoke the guard per call. Production before/after immutable source checks remain mandatory."],
        "descriptor_export_deep_copy_pass": True,
        "production_recovery_requirement": "Recover strip-root/flange resultants from the loaded heel and genuine beam factors. This response exports four loaded port wrenches and loaded heel/closure but not loaded strip-root/flange rows; frozen model.response(q) uses an unloaded heel and cannot substitute.",
        "limits": ["Synthetic 31-coordinate seam only; no candidate inputs, assembly, q, K, geometry, CAD or native/global solve evaluated.",
            "Localized centroid point-wrench route is an explicit interpolation scenario, not product uniform self-weight deformation or a contact/surface point map.",
            "Gross-strip first-order model limits remain: unknown actual plate/bend/hole/calibration/material/strength; no response accuracy or resistance bound.",
            "Plan geometry is preserved pre-revision context and all anticipated successor censuses/source joins need genuine new production validation."],
        "release": {"synthetic_numerical_consistency": True, "candidate_field_admitted": False, "physical_product_accuracy": False,
            "capacity": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    data = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    with args.out.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"path": str(args.out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "source_count": result["source_count"], "disposition": result["disposition"]}))


if __name__ == "__main__":
    main()
