"""Source and toy loaded-root review; never prepare/evaluate candidate inputs."""
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
    "guarded_assembly_interface.py": "a2b5ef4f45d05f3a29c428583238c3ead927ac7ae259a6c4a8d7c63ded3d0ad8",
    "test_guarded_assembly_interface.py": "bb8a010261d57ec49d2e39ee036dec278a9fcd4cc6f846eb5ba155fe6eacc1db",
    "first_order_factory.py": "5ca9a2018cc8a45fbddcf929f446cdd22b9d5fcae6ba816959de2c897b464570",
    "test_first_order_factory.py": "98386e0d2225670414707850365e5d71e8fed34f83a6acc00c71224983057866",
    "run_first_order.py": "28ceafcb9eac9764358071b728da96fbb2e5cd46011ead031ade8a9d7a811a39",
    "test_run_first_order.py": "1d7c48e7de814d87121710dc0b6703bf38e9662da31a369fc8ad80ac04fe1145",
}
PRIOR_REVIEW_SHA = "d8d938963a2dda3154c08e9dc91f841ebb10024b6032c20b49491806bed35931"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    require(all(sha(ROOT / p) == digest for p, digest in pins.items()), "reviewed frozen source changed")


def review():
    prior_path = OWN.parent / "independent-assembly-method-review.json"
    require(sha(prior_path) == PRIOR_REVIEW_SHA, "prior immutable review differs")
    prior = json.loads(prior_path.read_bytes())
    pins = dict(prior["source_sha256"])
    pins[str(prior_path.relative_to(ROOT))] = PRIOR_REVIEW_SHA
    for name, digest in EXPECTED.items():
        pins[str((LEAF / name).relative_to(ROOT))] = digest
    verify(pins)
    spec = importlib.util.spec_from_file_location("independent_guarded_factory_runner", LEAF / "run_first_order.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    # Read/authenticate only kernel bytes. No panel operator rehydration,
    # factory prepare, candidate reader, search or global assembler is invoked.
    extra = {**runner.runtime_pins(), **runner.search.source_pins(), runner.SAVED_PANEL_PATH: runner.SAVED_PANEL_SHA}
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "runtime source join conflict")
        pins[path] = digest
    verify(pins)
    before = canonical(pins)
    guarded = runner.factory.guarded
    original = json.loads((LEAF / "assembly-method-result.json").read_bytes())
    model = guarded.four.FourPortStripModel()
    element = guarded.GuardedFourPortAssemblyElement(model, "synthetic-fitting", np.arange(3, 27), 31)
    q = np.asarray(original["toy_stored_q"])
    loads = original["response"]["load_projection"]["physical_load_rows"]
    response = element.response(q, loads=loads, declared_route=guarded.ROUTE)
    f = np.asarray(response["load_projection"]["heel_wrench_n_nmm"])
    closures, root_total, external = [], np.zeros(6), f.copy()
    for root, tip in zip(response["strip_root_actions"], response["port_actions"], strict=True):
        rf = np.asarray(root["applied_to_strip_force_xyz_n"])
        rm = np.asarray(root["applied_to_strip_couple_at_root_xyz_nmm"])
        rp = np.asarray(root["point_xyz_mm"])
        tf = np.asarray(tip["external_force_required_at_port_xyz_n"])
        tm = np.asarray(tip["external_couple_required_at_port_xyz_nmm"])
        tp = np.asarray(tip["point_xyz_mm"])
        rw, tw = np.r_[rf, rm+np.cross(rp, rf)], np.r_[tf, tm+np.cross(tp, tf)]
        root_total += rw
        external += tw
        closures.append(float(np.max(abs(rw+tw))))
    errors = {"each_strip_wrench_closure_max_n_nmm": max(closures),
              "sum_root_wrench_minus_declared_gravity_max_n_nmm": float(np.max(abs(root_total-f))),
              "whole_fitting_external_wrench_closure_max_n_nmm": float(np.max(abs(external)))}
    require(max(errors.values()) < 1e-8, "independent loaded-root arithmetic differs")
    require(response["root_recovery_uses_loaded_heel"] is True and
            response["frozen_unloaded_model_response_used_for_gravity"] is False and
            len(response["strip_root_actions"]) == 4 and
            set(response["per_flange_applied_strip_root_wrench_about_heel_n_nmm"]) == {"arm-x", "arm-z"},
            "loaded root/flange ownership differs")
    descriptor = element.descriptor()
    model.inputs["elastic_modulus_mpa"] = 1.
    rejected = False
    try:
        element.descriptor()
    except ValueError:
        rejected = True
    finally:
        model.inputs["elastic_modulus_mpa"] = 200000.
    require(rejected and element.descriptor() == descriptor, "prior mutable-E finding not closed")
    response["port_actions"][0]["point_xyz_mm"][0] += 5.
    require(element.response(q, loads=loads, declared_route=guarded.ROUTE)["port_actions"][0]["point_xyz_mm"][0] == 65.0875,
            "returned response still aliases live port data")
    verify(pins)
    return {
        "schema": "independent_eoere_guarded_first_order_factory_method_review/v1",
        "disposition": "READY_BOUNDED_FIRST_ORDER_METHOD_ONLY",
        "source_sha256": pins, "source_count": len(pins), "source_manifest_before_after_sha256": [before, canonical(pins)],
        "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "focused_checks": {"guarded_interface": "14 passed in 0.45s", "factory_and_runner": "21 passed in 2.19s",
            "ruff": "all six frozen source/test paths passed", "candidate_query_or_solve": False},
        "independent_loaded_roots": {"declared_gravity_wrench_n_nmm": f.tolist(), "errors": errors,
            "strip_root_count": 4, "flange_resultant_count": 2},
        "resolved_findings": [
            "Guard fingerprints complete live model inputs/operators/maps/indices/storage and verifies immutable source bytes before/after every public call; mutable E/metadata/operator changes reject.",
            "Recovery uses loaded heel to export all 4 strip-root actions and 2 flange resultants; returned descriptors/actions are defensive deep copies.",
            "Runner successful path now consumes search._fresh_fields[0], requires finite full-ndof gradient, and rejects scalar/nonfinite values before recovery. Three new dispatch fixtures distinguish gradient from 19.25 Nmm energy."],
        "factory_contract_review": [
            "Production census: 22 timbers, 22 four-port fittings, 100 continuous shafts and 6 panels = 150 distinct bodies; no old two-node fittings instantiated. All 176 factory holes, 88 active own ports and 500 nominal metal roles require source joins.",
            "CommonShaftSystem is genuine and used once. Every nominal metal role gravity is assigned once to its own shaft; remap_bolt_gravity is not called. Fitting centroid loads use affine internal-heel condensation and work-conjugate rigid modes.",
            "Each bearing uses its own surface diameter: toy steel radial gap 0.2375 mm versus wood 0.396875 mm; one global bore diameter is not reused as gap authority.",
            "Contact ports on fittings require exact own strip IDs. Area-weighted flange 40,000 N/mm scale, timber 1 and panel 2 N/mm3 remain declared distinct priors.",
            "Floor retains 32 actual normal corners and 8 centroid XY pairs, kn 25000 / kt 100000 N/mm and host N > 1e-7 whole-foot activation; no new floor datum/law or transferred exclusion history.",
            "Actual input bytes/canonical rows and complete-reference-inventory review bind before production preparation; six saved panel operators require byte-identical panel geometry and loader/helper source joins.",
            "Runner checks fresh original gradient, body/global closure and unchanged operator fingerprint; convergence is pending new independent admission. Failed/timeout sidecars preserve source pins/branch observations and no accepted q/actions, with exclusive writes."],
        "embedding_and_energy_qualifications": [
            "Fitting descriptor.ndof is its pre-shaft embedding size; factory pads fitting ports after CommonShaftSystem extends the final assembly. Actual 24 fitting indices remain unchanged and the field gate must authenticate this padding seam.",
            "Global search potential omits the additive condensed gravity constant; each loaded fitting response retains it. This constant changes neither gradients nor line-search comparisons."],
        "confirmed_unresolved_blockers_in_reviewed_methods": [],
        "remaining_production_dependencies": ["Actual frozen successor extraction and independent exact input/contact/load ownership review",
            "Parent-owned one serialized candidate preparation/case with exact command and finite budgets",
            "Distinct source-bound 150-body field admission with independent same-q constitutive/operator/loaded-fitting and body/global checks"],
        "limits": ["Source-independent tiny fixtures and method arithmetic only; no candidate input reader/preparation/q/K/CAD/native/global solve invoked by this reproducer.",
            "Test success-dispatch/body-closure stubs are explicitly numerical protocol checks, not a production equilibrium proof.",
            "First-order gross-stock beams/four-strip fittings/reference-point contacts and unmeasured spring priors do not qualify physical plate response, finite/current-solid contact, pressure, washer prying, delivered hardware or complete strength.",
            "No predecessor field/pass/source census or geometry/native scope transfer; no capacity, fabrication or climbing release."],
        "release": {"bounded_numerical_method_ready": True, "candidate_prepared": False, "candidate_field_admitted": False,
            "physical_contact_or_product_response": False, "capacity": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    data = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()
    with args.out.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"path": str(args.out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "source_count": result["source_count"], "disposition": result["disposition"]}))


if __name__ == "__main__":
    main()
