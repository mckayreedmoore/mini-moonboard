"""Source-list cut recovery ordering around immutable bfb/e61 admission.

The producer recovers shaft cuts in authenticated source_inputs.shafts order.
JSON sorts the saved coordinate-map dictionary. This adapter restores only
that internal iteration order; values, input field tables and tolerances remain
unchanged. All genuine corrected-gate mechanics and source checks are reused.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

OWN = Path(__file__).resolve()
REUSED = OWN.with_name("first_order_admission_v2.py")
REUSED_SHA = "bfb984c47372d20387883d11d1d49f8a12d9debda1b0c78f1c024ace01bc2821"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
if hashlib.sha256(REUSED.read_bytes()).hexdigest() != REUSED_SHA:
    raise ValueError("preserve frozen bfb corrected admission")
SPEC = importlib.util.spec_from_file_location("eoere_genuine_bfb_recovery_reuse", REUSED)
corrected = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(corrected)
base, frame, core = corrected.base, corrected.frame, corrected.core
SCHEMA, SUCCESS, require = corrected.SCHEMA, corrected.SUCCESS, corrected.require


def source_pins(extra=None):
    pins = corrected.source_pins(extra)
    require(frame.sha(REUSED) == REUSED_SHA and frame.sha(OWN) == LOADED_SHA,
            "loaded order adapter or reused admission source changed")
    path = str(OWN.relative_to(frame.ROOT))
    require(path not in pins or pins[path] == LOADED_SHA, "order adapter source join conflict")
    pins[path] = LOADED_SHA
    return base.verify_pins(pins)


def source_ordered_maps(field, maps):
    """Keep original map objects; validate exact body/axis union before ordering."""
    sources = field["source_inputs"]["shafts"]
    require(isinstance(sources, list) and len(sources) == len(maps.shafts), "source shaft order has missing/extra owners")
    bodies = [row["body"] for row in sources]
    axes = [row["axis_id"] for row in sources]
    require(len(set(bodies)) == len(bodies) and len(set(axes)) == len(axes)
            and set(bodies) == set(maps.shafts)
            and all(maps.shafts[row["body"]]["axis_id"] == row["axis_id"] for row in sources),
            "source order has duplicate, foreign or mismatched owned shaft axes")
    view = copy.copy(maps)
    view.shafts = {body: maps.shafts[body] for body in bodies}
    return view


def verify_fitting_and_alias_recovery(field, snapshot, maps, q):
    return corrected.verify_fitting_and_alias_recovery(field, snapshot, source_ordered_maps(field, maps), q)


# Reuse the exact reviewed compatibility transformation in an independent
# context bound to the genuine new contract. No original globals are patched.
CONTEXT = {**corrected.CONTEXT, "OWN": OWN, "LOADED_SHA": LOADED_SHA, "source_pins": source_pins,
           "verify_fitting_and_alias_recovery": verify_fitting_and_alias_recovery}
AUDIT = corrected.corrected_function("audit_first_order_state", CONTEXT)
CONSUMER = corrected.corrected_function("require_admitted_payload", CONTEXT)


def compatibility_provenance():
    return {"reused_source_path": str(corrected.ORIGINAL.relative_to(frame.ROOT)),
        "reused_source_sha256": corrected.ORIGINAL_SHA,
        "removed_absent_historical_flag_guards": list(corrected.CORRECTED_FUNCTIONS),
        "exact_own_alias_metadata_and_table_membership_verified": True,
        "physical_laws_or_algorithms_changed": False, "field_bytes_or_action_aliases_modified": False}


def order_provenance():
    return {"reused_corrected_gate_path": str(REUSED.relative_to(frame.ROOT)), "reused_corrected_gate_sha256": REUSED_SHA,
        "order_source_path": "source_inputs.shafts", "exact_owned_body_and_axis_union_verified": True,
        "only_internal_recovery_map_iteration_order_changed": True, "field_tables_reordered_or_modified": False,
        "cut_values_or_force_tolerances_changed": False}


def audit_first_order_state(path_or_bytes):
    before = source_pins()
    receipt = AUDIT(path_or_bytes)
    require(source_pins() == before, "order-adapter/reused sources changed during audit")
    receipt["admission_compatibility_correction"] = compatibility_provenance()
    receipt["admission_recovery_order_correction"] = order_provenance()
    return receipt


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    require(receipt.get("admission_compatibility_correction") == compatibility_provenance()
            and receipt.get("admission_recovery_order_correction") == order_provenance(),
            "actual source-order corrected admission provenance required")
    return CONSUMER(field_bytes, receipt, admission_sha256=admission_sha256)
