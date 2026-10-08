"""Honor the frozen member writer's enclosing case/placement identity."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BRIDGE = OWN.parent.parent / "component_reductions.py"
BRIDGE_SHA = "3f2682226fd6836360785a68e158a15a65a06292444547e08a1e77d9e0d9a98d"
if hashlib.sha256(BRIDGE.read_bytes()).hexdigest() != BRIDGE_SHA:
    raise ValueError("preserve the frozen observer-isolation component bridge")
_spec = importlib.util.spec_from_file_location("observer_component_bridge_for_member_schema", BRIDGE)
bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bridge)
pure = bridge.frozen.pure


def verify_alias_state_labels(demand):
    """Strict aggregate/cut labels; members carry own state plus enclosure."""
    keys = pure.IDENTITIES
    identity = tuple(demand[key] for key in keys)
    enclosing = {key: demand[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    pure.unit.require(demand["schema"] == "thin_bolted_common_shaft_frame/v1"
        and demand["state_id"] == "thin-v4-" + pure.references.canonical_sha(enclosing)[:24],
        "member enclosing state/case/placement identity differs")
    for table in ("common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions", "common_shaft_section_cut_actions"):
        for row in demand[table]:
            for labeled in (row, *row.get("cuts", [])):
                pure.unit.require(tuple(labeled.get(key) for key in keys) == identity,
                                  "aggregate/cut alias mixes or omits admitted identity")
    for row in demand["member_element_actions"]:
        pure.unit.require(row.get("state_id") == demand["state_id"]
            and all(key not in row or row[key] == demand[key] for key in ("case_id", "accessory_placement")),
            "member own state or optional case/placement differs from admitted enclosure")


def consume(field_path, admission, *, expected_field_sha256, admission_sha256, samples=41, caller_sections=None):
    """Change only the alias validator; bytes, row labels and receipt stay intact."""
    pins = {str(BRIDGE.relative_to(ROOT)): BRIDGE_SHA, str(OWN.relative_to(ROOT)): LOADED_SHA}
    pure.verify_pins(pins)
    original = pure.timber.verify_alias_state_labels
    try:
        pure.timber.verify_alias_state_labels = verify_alias_state_labels
        result = bridge.consume(field_path, admission, expected_field_sha256=expected_field_sha256,
            admission_sha256=admission_sha256, samples=samples, caller_sections=caller_sections)
    finally:
        pure.timber.verify_alias_state_labels = original
    for path, digest in pins.items():
        pure.unit.require(path not in result["source_sha256"] or result["source_sha256"][path] == digest,
                          "member-schema adapter contradicts result source")
        result["source_sha256"][path] = digest
    pure.verify_pins(result["source_sha256"])
    result["enclosing_member_identity_schema_bridge"] = {
        "source": {"path": str(OWN.relative_to(ROOT)), "sha256": LOADED_SHA},
        "unchanged_component_bridge": {"path": str(BRIDGE.relative_to(ROOT)), "sha256": BRIDGE_SHA},
        "aggregate_and_shaft_cut_complete_identity_required": True,
        "member_own_state_required_optional_case_placement_must_match_enclosure": True,
        "member_labels_payload_or_receipt_modified": False,
        "original_validator_restored": pure.timber.verify_alias_state_labels is original,
    }
    return result
