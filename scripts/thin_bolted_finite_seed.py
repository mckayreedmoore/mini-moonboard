"""Authenticate an admitted finite vector for exact-map initialization only.

No mesh interpolation, coordinate projection, force recovery, target admission,
CAD, stiffness preparation or solve occurs. The caller owns prepared target
maps and subsequent execution. This utility has no runner or gate override.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from scripts import thin_bolted_timber_contact_admission as admission

ROOT = admission.ROOT
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = admission.original.support.digest(Path(__file__))
GATE = "scripts/thin_bolted_timber_contact_admission.py"
GATE_SHA256 = "75011f4cfa042a46d8e45eb5716ae01df2edff3418b1439553afb04b14b14632"
FIELD_SCHEMA = "thin_bolted_finite_frame_response/v1"
COORDINATE_PARAMETERS = ("panel_intervals", "beam_size_mm", "shaft_max_segment_mm",
                         "finite_kinematics_basis", "finite_shaft_basis")


def source_pins():
    pins = {OWN: LOADED_PRODUCER_SHA256, GATE: GATE_SHA256}
    admission.original.require(Path(admission.__file__).resolve() == (ROOT/GATE).resolve()
                               and admission.LOADED_PRODUCER_SHA256 == GATE_SHA256,
                               "loaded seed admission is not the fixed reviewed timber-contact gate")
    verify_pins(pins)
    return pins


def verify_pins(pins):
    for path, expected in pins.items():
        admission.original.require(isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected) is not None
                                   and admission.original.support.digest(ROOT/path) == expected,
                                   "finite seed source changed: "+path)


def target_snapshot(target_map, target_ndof, target_body_identities, target_parameters):
    admission.original.require(type(target_ndof) is int and target_ndof > 0
                               and isinstance(target_map, dict) and target_map.get("ndof") == target_ndof
                               and isinstance(target_map.get("mechanical_bodies"), dict)
                               and isinstance(target_map.get("panels"), dict),
                               "prepared target map and finite dimension required")
    admission.original.require(isinstance(target_body_identities, (list, tuple))
                               and all(isinstance(name, str) for name in target_body_identities),
                               "explicit prepared target physical-body order required")
    names = list(target_body_identities)
    map_names = set(target_map["mechanical_bodies"]) | set(target_map["panels"])
    admission.original.require(len(names) == len(set(names)) == len(map_names) and set(names) == map_names,
                               "target physical-body list must cover the complete finite map once")
    admission.original.require(isinstance(target_parameters, dict)
                               and all(key in target_parameters for key in COORDINATE_PARAMETERS),
                               "explicit target coordinate-scenario parameters required")
    # Keyed-object insertion order is not a coordinate identity. Ordered node,
    # coefficient and physical-body arrays are preserved by this exact digest.
    return copy.deepcopy({"map": target_map, "ndof": target_ndof,
                          "body_identities": names, "parameters": target_parameters})


def read_seed(path, expected_field_sha256, *, target_map, target_ndof,
              target_body_identities, target_parameters):
    """Return ``(q.copy(), provenance)`` only after current source admission.

    Source case/accessory and other scenario parameters may differ. The five
    coordinate parameters and the entire coordinate map/body order must match.
    No source action table, admission receipt or target state identity returns.
    """
    pins = source_pins()
    admission.original.require(isinstance(expected_field_sha256, str)
                               and re.fullmatch("[0-9a-f]{64}", expected_field_sha256) is not None,
                               "exact released finite seed raw SHA256 required")
    target = target_snapshot(target_map, target_ndof, target_body_identities, target_parameters)
    target_digest = admission.original.canonical_sha(target)
    path = Path(path).resolve()
    payload = path.read_bytes()
    admission.original.require(hashlib.sha256(payload).hexdigest() == expected_field_sha256,
                               "released finite seed bytes differ")
    field = json.loads(payload)
    admission.original.require(field.get("schema") == FIELD_SCHEMA,
                               "current finite export schema required for a saved seed")
    admission.original.require(field.get("response", {}).get("converged") is True
                               and field.get("usable_conditional_actions") is True
                               and isinstance(field.get("finite_kinematic_map"), dict)
                               and "q" in field["response"],
                               "failed or missing-map finite exports cannot authenticate a seed")
    receipt = admission.audit_timber_contact_state(payload)
    admission.original.require(receipt.get("schema") == admission.SCHEMA and receipt.get(admission.SUCCESS) is True,
                               "current timber-contact admission required before vector reuse")
    admission.original.require(receipt.get("field_sha256") == expected_field_sha256
                               and receipt.get("field_canonical_sha256") == admission.original.canonical_sha(field)
                               and all(receipt.get(key) == field[key] for key in ("state_id", "case_id", "accessory_placement"))
                               and receipt.get("source_sha256", {}).get(GATE) == GATE_SHA256,
                               "seed admission does not bind exact source bytes/state/gate")
    pins = admission.merge_pins(pins, field["source_sha256"], receipt["source_sha256"])
    verify_pins(pins)
    mapping = field["finite_kinematic_map"]
    admission.original.require(admission.original.canonical_sha(mapping) == admission.original.canonical_sha(target["map"])
                               and field["body_identities"] == target["body_identities"],
                               "saved finite seed requires the exact complete prepared target map and body order")
    for key in COORDINATE_PARAMETERS:
        admission.original.require(key in field["parameters"]
                                   and admission.original.canonical_sha(field["parameters"][key])
                                   == admission.original.canonical_sha(target["parameters"][key]),
                                   "saved finite seed coordinate parameter differs: "+key)
    q = admission.original.array(field["response"]["q"], (target_ndof,)).copy()
    admission.original.require(mapping["ndof"] == target_ndof,
                               "saved finite seed dimension differs from prepared target")
    admission.original.require(path.read_bytes() == payload,
                               "released seed file changed during authentication")
    admission.original.require(admission.original.canonical_sha(target_snapshot(target_map, target_ndof,
                               target_body_identities, target_parameters)) == target_digest,
                               "prepared target map/scenario changed during seed authentication")
    verify_pins(pins)
    source_path = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return q, {"schema": "thin_bolted_exact_map_finite_seed/v1", "kind": "admitted finite vector as initialization only",
               "path": source_path, "sha256": expected_field_sha256,
               "source_state_id": field["state_id"], "source_case_id": field["case_id"],
               "source_accessory_placement": field["accessory_placement"], "dofs": target_ndof,
               "source_coordinate_map_sha256": admission.original.canonical_sha(mapping),
               "target_coordinate_map_sha256": admission.original.canonical_sha(target["map"]),
               "target_physical_body_order": target["body_identities"],
               "source_parameters": copy.deepcopy(field["parameters"]), "target_parameters": target["parameters"],
               "coordinate_parameters_compared": list(COORDINATE_PARAMETERS), "source_sha256": pins,
               "initialization_only": True, "target_admission_or_strength_transferred": False,
               "source_forces_or_admission_receipt_returned": False,
               "mesh_interpolation_projection_or_canonicalization_performed": False,
               "CAD_K_response_or_solve_executed": False}
