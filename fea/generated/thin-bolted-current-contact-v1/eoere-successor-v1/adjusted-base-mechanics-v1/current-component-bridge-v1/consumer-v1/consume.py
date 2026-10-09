"""Admit exact current bytes before coarse component reductions.

The frozen equations retain their identities. Scoped callbacks supply current
schemas, axes and aperture metadata. No CAD, panel operator preparation, frame
construction or solve is called. The CLI reserves a fresh output before intake.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from threading import RLock
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PLAN = OWN.parent.parent / "component_plan.py"
PLAN_SHA = "caf5d1307d999843c3ea16f3536f5bdd25edb390ebbab6e624cf5f5a86dc727e"
GATE_SHA = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
FIELD_SCHEMA = "eoere_extended_cleat_fixed_floor_candidate/v1"
ADMISSION_SCHEMA = "eoere_extended_cleat_fixed_floor_independent_field_admission/v1"
SUCCESS = "current_extended_cleat_equilibrium_and_recovery_pass"
RELEASE = {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                                 "fabrication_released", "structural_released", "climbing_released")}
BOUNDARY_LOCK = RLock()
DESCRIPTOR_KEYS = {
    "timber_rows": "raw_gross_timber_rows", "physical_owner_gravity_rows": "physical_owner_gravity_rows",
    "fitting_poses": "fitting_poses", "fitting_port_bindings": "fitting_ports", "shafts": "shafts",
    "all_factory_holes": "all_factory_holes", "finished_receiver_wall_queries": "finished_receiver_wall_queries",
    "finished_body_observations": "finished_body_observations", "hillman_rows": "hillman_rows",
    "current_panel_machining_descriptors": "current_panel_machining_descriptors", "direct_contacts": "direct_contacts",
    "flange_domains": "flange_domains", "flange_shared_face_patches": "flange_shared_face_patches",
    "timber_and_panel_shared_face_patches": "timber_and_panel_shared_face_patches",
    "shared_pair_query_census": "shared_pair_query_census",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def name(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def checked(path, expected):
    raw = Path(path).read_bytes()
    require(digest(raw) == expected, "exact source/artifact bytes required: " + str(path))
    return raw


def verify(pins):
    for path, sha in pins.items():
        checked(ROOT / path, sha)


def load(path, expected, label):
    checked(path, expected)
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[label] = module
    spec.loader.exec_module(module)
    checked(path, expected)
    return module


def _load_plan():
    return load(PLAN, PLAN_SHA, "eoere_current_component_frozen_source_plan")


def _load_gate(plan):
    source = plan.ARTIFACTS["gate"]
    require(source["sha256"] == GATE_SHA, "exact corrected current gate required")
    return load(ROOT / source["path"], GATE_SHA, "eoere_current_component_genuine_gate")


def authenticate(field_path, receipt_path, expected_field_sha256, expected_receipt_sha256, admission_sha256):
    """No reducer import or callback is reachable before this returns."""
    require(admission_sha256 == GATE_SHA, "exact corrected current gate SHA required")
    checked(OWN, LOADED_SHA)
    raw = checked(field_path, expected_field_sha256)
    receipt_raw = checked(receipt_path, expected_receipt_sha256)
    raw_field, receipt = json.loads(raw), json.loads(receipt_raw)
    plan = _load_plan()
    require(raw_field.get("schema") == FIELD_SCHEMA and raw_field.get("release") == RELEASE,
            "current unreleased field schema required")
    expected_geometry = {"report": plan.ARTIFACTS["geometry"], "source_manifest": plan.ARTIFACTS["manifest"],
                         "cached_source_export": plan.ARTIFACTS["descriptors"]}
    require(raw_field["source_inputs"]["geometry"] == expected_geometry
            and raw_field["current_execution"]["geometry"] == plan.ARTIFACTS["geometry"], "exact current field geometry references required")
    require(receipt.get("schema") == ADMISSION_SCHEMA and receipt.get(SUCCESS) is True, "own current admission receipt required")
    gate = _load_gate(plan)
    field, pins = gate.require_admitted_payload(raw, receipt, admission_sha256=admission_sha256)
    require(canonical(field) == canonical(raw_field), "gate must return the identical raw field payload")
    pins = dict(pins)
    plan.merge(pins, {name(field_path): expected_field_sha256, name(receipt_path): expected_receipt_sha256,
                     name(OWN): LOADED_SHA, name(PLAN): PLAN_SHA,
                     plan.ARTIFACTS["gate"]["path"]: GATE_SHA})
    verify(pins)
    return field, pins, plan


def _current_contract(field, plan):
    """Only saved current metadata; no operator bank or force reducer call."""
    contract = plan.component_plan()
    exported = json.loads(plan.checked_bytes(plan.ARTIFACTS["descriptors"]))
    geometry = json.loads(plan.checked_bytes(plan.ARTIFACTS["geometry"]))
    source = field["source_inputs"]
    for key, exported_key in DESCRIPTOR_KEYS.items():
        require(source[key] == exported[exported_key], "current admitted descriptor join differs: " + key)
    require(source["parameters"] == exported["parameters"], "current admitted parameter join differs")
    panels = sorted({row["id"] for row in exported["finished_body_observations"]}
                    - {row["name"] for row in exported["raw_gross_timber_rows"]})
    require(sorted(source["panel_ids"]) == panels and len(source["panel_ids"]) == 6, "exact six current panel owners required")
    features = source["current_panel_machining_descriptors"]["features"]
    require(len(features) == len({(row["panel"], row["kind"], row["identity"]) for row in features}) == 340,
            "all 340 unique current aperture descriptors required")
    return contract, plan.indexed(geometry["axes"], "id")


def _reduce(field, axes, plan, pins, samples):
    """Reuse the genuine frozen functions with restored metadata boundaries."""
    def method(relative, label):
        sha = plan.METHODS[relative][0]
        return load(ROOT / plan.BASE / relative, sha, label)

    base = method("component-method-v1/assessment.py", "eoere_current_coarse_assessment")
    gross = method("component-method-v1/gross_members.py", "eoere_current_coarse_gross")
    steel = method("raised-rail-components-v1/comparisons.py", "eoere_current_coarse_centroidal_comparison")
    plan.merge(pins, base.PINS)
    plan.merge(pins, gross.source_pins())
    comparison_pins = {**steel.old.FROZEN, **steel.centroidal.source_pins(),
                       name(steel.ORIGINAL): steel.ORIGINAL_SHA, name(Path(steel.__file__)): steel.LOADED_SHA,
                       **{path: steel.old.DIRECT[path] for path in (steel.old.INPUT, steel.old.GUARDED)},
                       **{plan.ARTIFACTS[key]["path"]: plan.ARTIFACTS[key]["sha256"]
                          for key in ("geometry", "manifest", "descriptors")}}
    plan.merge(pins, comparison_pins)
    verify(pins)
    original_datums = base.panel.prepared_datums
    features = field["source_inputs"]["current_panel_machining_descriptors"]["features"]

    def current_datums(state, assessment, datums, integrated):
        del integrated
        result = original_datums(state, assessment, datums, {"panel_machining": {"features": features}})
        for row in result.values():
            row["support_bounds"] = []
            row["current_support_footprints_qualified"] = False
        return result

    def current_comparison_pins():
        verify(comparison_pins)
        return dict(comparison_pins)

    with BOUNDARY_LOCK, patch.object(base, "FIELD_SCHEMA", FIELD_SCHEMA), \
         patch.object(base.panel, "prepared_datums", current_datums), \
         patch.object(steel, "source_pins", current_comparison_pins):
        reductions, extra = base.reduce_field(field, steel, gross, axes, samples=samples)
    plan.merge(pins, extra)
    return reductions


def consume(field_path, receipt_path, *, expected_field_sha256, expected_receipt_sha256,
            admission_sha256=GATE_SHA, samples=41):
    """Exact current admission first; return own same-state coarse findings."""
    require(type(samples) is int and samples >= 3, "at least three spatial samples required")
    field, pins, plan = authenticate(field_path, receipt_path, expected_field_sha256, expected_receipt_sha256, admission_sha256)
    original = canonical(field)
    contract, axes = _current_contract(field, plan)
    plan.merge(pins, contract["source_sha256"])
    verify(pins)
    reductions = _reduce(field, axes, plan, pins, samples)
    require(canonical(field) == original, "component methods changed the admitted field")
    verify(pins)
    return {"schema": "eoere_extended_cleat_same_state_conditional_component_receipt/v1",
            **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
            "raw_field_sha256": expected_field_sha256, "field_admission_receipt_sha256": expected_receipt_sha256,
            "fresh_gate_sha256": admission_sha256, "current_geometry": plan.ARTIFACTS["geometry"],
            "current_saved_descriptors": plan.ARTIFACTS["descriptors"], "source_sha256": dict(sorted(pins.items())),
            "source_inputs_canonical_sha256": canonical(field["source_inputs"]), "component_reductions": reductions,
            "nominal_seat_geometry": copy.deepcopy(contract["nominal_seat_geometry"]),
            "current_callbacks": {"axes": 100, "panel_apertures": 340, "panel_screws": 66,
                "old_geometry_source_contract_called": False, "old_support_footprints_used": False,
                "scoped_boundaries_restored": True, "equations_or_tolerances_changed": False,
                "field_or_admission_payload_modified": False},
            "limits": [row["limit"] for row in contract["reuse"].values()],
            "execution": {"CAD_query_or_rebuild": False, "panel_bank_K_or_preparation": False,
                "frame_K_assembly_q_solve_native_or_browser": False, "existing_saved_field_spatial_equations_reused": True},
            "complete_joint_resistance": None, "disposition": "SAME_CURRENT_STATE_CONDITIONAL_COMPONENT_FINDINGS",
            "release": dict(RELEASE)}


def write_record(stream, record):
    stream.seek(0)
    stream.write(json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    stream.truncate()
    stream.flush()
    os.fsync(stream.fileno())


def consume_to_file(field_path, receipt_path, out, **kwargs):
    """Exclusive reservation precedes every input read and producer callback."""
    attempt = {"schema": "eoere_current_component_attempt/v1", "status": "STARTED", "output": str(out),
               "command": list(sys.orig_argv), "expected_source_sha256": {name(OWN): LOADED_SHA},
               "expected_inputs": {"field": {"path": str(field_path), "sha256": kwargs.get("expected_field_sha256")},
                                   "receipt": {"path": str(receipt_path), "sha256": kwargs.get("expected_receipt_sha256")},
                                   "gate_sha256": kwargs.get("admission_sha256", GATE_SHA)}, "release": dict(RELEASE)}
    with Path(out).open("x") as stream:
        write_record(stream, attempt)
        try:
            result = consume(field_path, receipt_path, **kwargs)
            result["execution"] = {**result.get("execution", {}), "command": list(sys.orig_argv),
                                   "cwd": str(Path.cwd()), "python": sys.version}
            result["output_reservation"] = {"method": "exclusive-create-before-intake", "failed_attempts_retained": True}
            write_record(stream, result)
        except BaseException as error:
            attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
            write_record(stream, attempt)
            raise
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected-field-sha256", required=True)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--admission-sha256", default=GATE_SHA)
    parser.add_argument("--samples", type=int, default=41)
    parser.add_argument("--out", type=Path, required=True)
    args = vars(parser.parse_args(argv))
    out, field, receipt = args.pop("out"), args.pop("field"), args.pop("receipt")
    result = consume_to_file(field, receipt, out, **args)
    print(json.dumps({"output": str(out), "schema": result["schema"], "sha256": digest(out.read_bytes())}))


if __name__ == "__main__":
    main()
