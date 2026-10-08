"""Original paired-panel action metadata bridge around reviewed v2 markers.

The genuine current gate runs before this bridge observes any action. Its
first-only panel force export and paired body ledger justify second=-first.
Only a copied diagnostic action gains that field; admitted actions/q and all
geometry/projection/force laws remain unchanged.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np

OWN = Path(__file__).resolve()
ROOT = OWN.parents[4]
TEST = OWN.with_name("test_mapped_diagnostic_v3.py")
PREFIX = str(OWN.parent.relative_to(ROOT)) + "/"
REUSED = {
    "mapped_diagnostic_v2.py": "e256baedb843494eddcf40fe1db27f6c9fc3fb861bc258d05de845c8395e99a2",
    "test_mapped_diagnostic_v2.py": "a91c6a17e5a5dc539c57b567349b9cbf8403099bec1843c6c2517151d4fae632",
    "mapped-diagnostic-coupon-v2.json": "a439124e20c2861a8c4c81bb4c421355925dfffea360c36bcfd5ea3e4c501fb8",
    "independent-mapped-review-v2.json": "2748a26f317e214578e0dc9226a68bb67f1c83a17a917d6a0acf951987f49830",
    "independent_mapped_review_v2.py": "809dcf39bbf6e5455309f9522aa6cb7ebe1c110a7aa7abad3e99ceb8fd83644c",
    "mapped-v2-execution-failure-attempt01.json": "334e901e493a7e100be018bcf45199e382f67bcb6a168de5a5184b30effce7fc",
}
PAIR_SOURCES = {
    "scripts/thin_bolted_frame_mechanics.py": "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448",
    "scripts/thin_bolted_linear_timber_admission.py": "e6dcb38947bea00ca583cd9a9e8d37a0cf0720d1f3ca97f7013ba9f2def0c676",
    "scripts/thin_bolted_common_shaft_audit.py": "a236900e59a3d5984598df56d4243408ce12801d4ab6fcc7f765f6a420de01ba",
    "scripts/thin_bolted_equilibrium_audit.py": "748f637b918bf9b7faca673cb2e723c8dbb8f98bc4a2d3fd5b12987c20980b84",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for _name, _expected in REUSED.items():
    if sha(OWN.with_name(_name)) != _expected:
        raise ValueError("issued v2 bytes changed: " + _name)
_spec = importlib.util.spec_from_file_location("private_reviewed_backing_marker_v2", OWN.with_name("mapped_diagnostic_v2.py"))
v2 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v2
_spec.loader.exec_module(v2)
query, core = v2.query, v2.frozen
reuse, surface, finite, panels = v2.reuse, v2.surface, v2.finite, v2.panels
union_summary, panel_marker = v2.union_summary, v2.panel_marker
ORIGINAL_OBSERVE, ORIGINAL_LOAD = core.observe_port, core.load
LOADED_SHA, TEST_SHA = sha(OWN), sha(TEST)
SCHEMA = "thin_bolted_admitted_current_panel_backing_mapped_markers/v3"
COUPON_SCHEMA = "thin_bolted_panel_backing_mapped_diagnostic_coupon/v3"
IDENTITY_KEYS = ("state_id", "case_id", "accessory_placement")


def own_pins():
    query.require(sha(OWN) == LOADED_SHA and sha(TEST) == TEST_SHA, "loaded action-bridge/test bytes changed")
    pins = query.join(v2.own_pins(), {PREFIX + name: value for name, value in REUSED.items()}, PAIR_SOURCES,
                     {str(OWN.relative_to(ROOT)): LOADED_SHA, str(TEST.relative_to(ROOT)): TEST_SHA})
    query.verify(pins)
    return pins


def bridge_action(identity, source, action, state_identity):
    """Pure metadata formatting; the runtime caller supplies admitted identity."""
    query.require(action["id"] == identity and action["kind"] == "panel_contact"
        and (action["first"], action["second"], action["point_xyz_mm"]) ==
            (source["first"], source["second"], source["point_xyz_mm"])
        and all(action[key] == state_identity[key] for key in IDENTITY_KEYS),
        "original panel action identity/owners/reference point required")
    first = np.asarray(action["force_on_first_xyz_n"], dtype=float)
    query.require(first.shape == (3,) and np.isfinite(first).all(), "finite original first-body panel force required")
    second = -first
    supplied = "force_on_second_xyz_n" in action
    if supplied:
        given = np.asarray(action["force_on_second_xyz_n"], dtype=float)
        query.require(given.shape == (3,) and np.isfinite(given).all() and np.array_equal(given, second),
                      "supplied second-body panel force conflicts with original paired law")
    if "host_support_point_xyz_mm" in action:
        query.require(action["host_support_point_xyz_mm"] == source["point_xyz_mm"],
                      "panel paired force must retain the same original point")
    copied = copy.deepcopy(action)
    copied["force_on_second_xyz_n"] = second.tolist()
    provenance = {"schema": "thin_bolted_original_panel_pair_metadata_bridge/v1",
        "rule": "second=-original first at the same original point",
        "source_action_canonical_sha256": query.canonical(action), "original_second_field_present": supplied,
        "second_force_metadata_derived_from_original_paired_law": not supplied,
        "same_original_point_xyz_mm": source["point_xyz_mm"],
        "first": action["first"], "second": action["second"],
        "basis": {"writer": "scripts/thin_bolted_frame_mechanics.py:575",
            "paired_body_ledger": "scripts/thin_bolted_frame_mechanics.py:601",
            "current_common_body_ledger": "scripts/thin_bolted_common_shaft_audit.py:79",
            "original_first_force_check": "scripts/thin_bolted_linear_timber_admission.py:166"},
        "source_sha256": PAIR_SOURCES, "admitted_action_mutated": False,
        "new_force_or_physical_contact_couple_computed": False}
    return copied, provenance


class _AdmissionObserver:
    """Observe successful genuine gate return; expose its unchanged other APIs."""

    def __init__(self, module, context):
        self.module, self.context = module, context

    def __getattr__(self, name):
        return getattr(self.module, name)

    def require_admitted_payload(self, *args, **kwargs):
        field, pins = self.module.require_admitted_payload(*args, **kwargs)
        query.require(self.context["state_identity"] is None, "single actual admission observation required")
        actions = [row for row in field["contact_actions"] if row["kind"] == "panel_contact"]
        action_hashes = {row["id"]: query.canonical(row) for row in actions}
        query.require(len(actions) == len(action_hashes) == 530,
                      "actual gate must provide all original 530 panel actions")
        self.context["state_identity"] = {key: field[key] for key in IDENTITY_KEYS}
        self.context["action_hashes"] = action_hashes
        return field, pins


@contextmanager
def bridge_callbacks():
    """Scoped action-copy callback and observer of the original gate load only."""
    own_pins()
    before = {"observe_port": core.observe_port, "load": core.load}
    context = {"state_identity": None, "action_hashes": {}, "bridged_ids": []}

    def observed_load(path, expected, name):
        module = ORIGINAL_LOAD(path, expected, name)
        if Path(path).resolve() == (ROOT / query.GATE).resolve():
            query.require(expected == query.PINS[query.GATE], "exact actual current gate required")
            return _AdmissionObserver(module, context)
        return module

    def observed_port(mapping, q, identity, source, action, prepared_faces):
        query.require(context["state_identity"] is not None, "actual admission must precede action metadata bridge")
        query.require(context["action_hashes"].get(identity) == query.canonical(action),
                      "action metadata must equal the exact admitted original row")
        copied, provenance = bridge_action(identity, source, action, context["state_identity"])
        result = ORIGINAL_OBSERVE(mapping, q, identity, source, copied, prepared_faces)
        result["second_force_metadata_provenance"] = {**provenance, "genuine_current_gate_observed_before_bridge": True,
            "actual_gate_sha256": query.PINS[query.GATE], "original_field_sha256": query.PINS[query.FIELD]}
        context["bridged_ids"].append(identity)
        return result

    try:
        core.observe_port, core.load = observed_port, observed_load
        yield context
    finally:
        for key, value in before.items():
            setattr(core, key, value)
        own_pins()


def method_contract():
    return {"method": "original-paired-panel-force-metadata-schema-bridge",
        "reused_v2_geometry_method_sha256": REUSED["mapped_diagnostic_v2.py"],
        "preserved_actual_v2_execution_failure_sha256": REUSED["mapped-v2-execution-failure-attempt01.json"],
        "scoped_new_callbacks": ["observe_port", "load:actual-admission-observer-only"],
        "source_first_action_authenticated_before_bridge": True, "metadata_copy_only": True,
        "conflicting_explicit_second_force_rejected_exactly": True,
        "projection_force_q_area_law_or_tolerances_changed": False,
        "previous_geometry_checks_reused": True, "new_bridge_readiness_transferred_from_old_pass": False,
        "source_sha256": PAIR_SOURCES}


def consume(coupon_path, coupon_sha256, *, progress=None):
    pins = own_pins()
    query.require(sha(coupon_path) == coupon_sha256, "exact new action-schema coupon required")
    coupon = json.loads(Path(coupon_path).read_bytes())
    query.require(coupon["schema"] == COUPON_SCHEMA and coupon["method_checks_pass"] is True
        and coupon["candidate_q_or_forces_consumed"] is False and coupon["method_contract"] == method_contract()
        and all(coupon["source_sha256"].get(path) == value for path, value in pins.items()),
        "new source-bound action bridge checks required")
    pins = query.join(pins, coupon["source_sha256"], {str(Path(coupon_path).resolve().relative_to(ROOT)): coupon_sha256})
    query.verify(pins)
    with bridge_callbacks() as context:
        result = v2.consume(OWN.with_name("mapped-diagnostic-coupon-v2.json"), REUSED["mapped-diagnostic-coupon-v2.json"], progress=progress)
    query.require(result["schema"] == v2.SCHEMA and len(context["bridged_ids"]) == len(set(context["bridged_ids"])) == 530,
                  "truthful complete v2 consumer and 530 metadata bridges required")
    query.require(context["state_identity"] == {key: result[key] for key in IDENTITY_KEYS}, "bridge/current result identity differs")
    result["reused_v2_consumer_schema"] = result["schema"]
    result["reused_v2_method_contract"] = result["method_contract"]
    result["schema"], result["method_contract"] = SCHEMA, method_contract()
    result["action_schema_method_coupon_sha256"] = coupon_sha256
    result["second_force_metadata_bridge_count"] = len(context["bridged_ids"])
    result["source_sha256"] = query.join(result["source_sha256"], pins)
    query.verify(result["source_sha256"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coupon", type=Path, required=True)
    parser.add_argument("--coupon-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    query.require(not args.out.exists(), "preserve existing v3 marker output")
    result = consume(args.coupon, args.coupon_sha256,
        progress=lambda event: print(json.dumps(event), flush=True) if event["completed_ports"] % 50 == 0 else None)
    result.update({"invocation_argv": list(sys.orig_argv), "working_directory": str(Path.cwd()),
        "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS")},
        "toolchain": query.toolchain()})
    query.write_exclusive(args.out, result)
    print(json.dumps({"output": str(args.out), "sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
