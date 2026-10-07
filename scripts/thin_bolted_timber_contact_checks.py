"""Timber consumption through the distinct finite timber-face admission gate.

Recovery math comes from the frozen finite timber helper. Face-contact rows
remain in the one admitted interaction table and enter every own material-cut
inventory once, with current points and complete spatial couples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts import thin_bolted_timber_finite_checks as methods

ROOT, PACKET, unit = methods.ROOT, methods.PACKET, methods.unit
METHOD_SHA = "c22215fc4016aa618827ec17a78063d7344a01ce335207b9d650cc35b740de83"
GATE = "scripts/thin_bolted_timber_contact_admission.py"
GATE_SCHEMA = "thin_bolted_independent_timber_contact_admission/v1"
GATE_SUCCESS = "independent_finite_timber_contact_support_load_and_equilibrium_checks_pass"


def require_contact_receipt(receipt: dict, field: dict, field_sha: str, gate_sha: str) -> None:
    unit.require(receipt.get(GATE_SUCCESS) is True and receipt.get("schema") == GATE_SCHEMA,
                 "distinct finite timber-contact admission fails")
    unit.require(receipt.get("field_sha256") == field_sha
                 and receipt.get("source_sha256", {}).get(GATE) == gate_sha
                 and all(receipt.get(key) == field[key] for key in ("state_id", "case_id", "accessory_placement")),
                 "timber-contact receipt does not bind exact bytes/source/state")


def own_face_load_inventory(field: dict) -> dict:
    """Show that the generic frozen collector includes each own face side once."""
    faces = [row for row in field["finite_interaction_actions"] if row["kind"] == "timber_face_contact"]
    ids = {row["id"] for row in faces}
    unit.require(faces and len(ids) == len(faces), "unique corrected timber face-contact actions required")
    own = methods.own_current_actions(field)
    inventory = []
    for face in faces:
        for side in ("first", "second"):
            member = face[side]
            unit.require(field["finite_kinematic_map"]["mechanical_bodies"][member]["kind"] == "timber",
                         "face contact must connect its two actual timber members")
            entries = [row for row in own[member] if row.get("source_action_id") == face["id"]
                       and row.get("source_action_side") == side]
            unit.require(len(entries) == 1, "own corrected face side omitted or duplicated in material-cut inventory")
            inventory.append({"member": member, **entries[0]})
    return {"face_interaction_count": len(faces), "own_member_face_side_count": len(inventory),
            "own_member_face_loads": inventory,
            "source_tables_used_once": ["finite_interaction_actions", "finite_body_applied_loads"],
            "separate_face_alias_appended_or_old_force_used": False}


def consume(path: Path, field_sha256: str, *, admission_sha256: str) -> dict:
    unit.require(isinstance(admission_sha256, str) and len(admission_sha256) == 64
                 and all(char in "0123456789abcdef" for char in admission_sha256),
                 "mandatory reviewed timber-contact admission digest malformed")
    unit.require((ROOT / GATE).is_file(), "reviewed timber-contact gate must be issued")
    frozen = ((ROOT / GATE, admission_sha256), (Path(methods.__file__), METHOD_SHA),
                             (ROOT / methods.FINITE, methods.FINITE_SHA),
                             (Path(methods.references.__file__), methods.REFERENCES_SHA),
                             (Path(methods.sections.__file__), methods.SECTIONS_SHA))
    for source, expected in frozen:
        unit.require(unit.sha(source) == expected, "frozen timber-contact consumer source differs")
    payload = path.read_bytes()
    unit.require(hashlib.sha256(payload).hexdigest() == field_sha256, "released timber-contact field differs")
    field = json.loads(payload)
    from scripts.thin_bolted_timber_contact_admission import audit_timber_contact_state

    receipt = audit_timber_contact_state(payload)
    require_contact_receipt(receipt, field, field_sha256, admission_sha256)
    face_inventory = own_face_load_inventory(field)
    packet, _, layout = methods.references.read_unit()
    detail = packet["reproducible_detail_artifact"]
    detail_path = ROOT / detail["path"]
    detail_bytes = detail_path.read_bytes()
    unit.require(hashlib.sha256(detail_bytes).hexdigest() == detail["sha256"], "reused section inventory differs")
    full = json.loads(detail_bytes)["finished_geometry_queries"]
    property_bytes = methods.RECESS.read_bytes()
    unit.require(hashlib.sha256(property_bytes).hexdigest() == methods.RECESS_SHA, "queried net properties differ")
    properties = json.loads(property_bytes)
    unit.require(properties["state_id"] is None and properties["candidate"] == unit.CANDIDATE,
                 "only unchanged geometry-only net properties may be reused")
    for relative, expected in properties["source_sha256"].items():
        unit.require(unit.sha(ROOT / relative) == expected, "net property source differs")
    indexed = {(row["member"], row["station_global_grain_projection_mm"]): row for row in properties["finished_sections"]}
    # No table merge or face-kind filter: all admitted face actions enter the
    # unchanged generic collector called by this frozen same-cut recovery.
    cuts = methods.recover_saved_cuts(field, full, indexed)
    wood = methods.current_wood_bearing_wrenches(field, full, layout)
    captures = methods.current_capture_annuli(field, packet)
    receivers = {(row["axis_id"], row["member"]): row for row in full["receiver_boundary_geometry"]}
    windows = [methods.references.standard_thread_window(axis, receivers) for axis in layout["installed_axes"]]
    duration = methods.references.read_duration_sources()
    unit.require(len(wood) == 82 and len(captures) == 140 and len(windows) == 70, "complete actual timber shaft/capture census required")
    sources = [path, Path(__file__), Path(methods.__file__), ROOT / GATE, methods.references.UNIT,
               methods.references.NATIVE, detail_path, methods.RECESS,
               ROOT / "tests/test_thin_bolted_timber_contact_checks.py"]
    pins = {str(source.resolve().relative_to(ROOT)): unit.sha(source) for source in sources}
    pins.update({str(source.resolve().relative_to(ROOT)): expected for source, expected in frozen})
    pins[detail["path"]] = detail["sha256"]
    pins.update(properties["source_sha256"])
    pins.update({row["path"]: row["sha256"] for row in duration["authenticated_primary_sources"]})
    pins[duration["source_metadata_path"]] = duration["source_metadata_sha256"]
    unit.require(unit.sha(path) == field_sha256 and unit.sha(ROOT / GATE) == admission_sha256
                 and unit.sha(Path(methods.__file__)) == METHOD_SHA and unit.sha(methods.RECESS) == methods.RECESS_SHA,
                 "released timber-contact field/method/source changed during consumption")
    for relative, expected in pins.items():
        unit.require(unit.sha(ROOT / relative) == expected, "timber-contact source changed during consumption: " + relative)
    return {"schema": "thin_bolted_timber_contact_components/v1", "candidate": unit.CANDIDATE,
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement", "parameters")},
        "source_sha256": pins, "finite_contact_producer_source_sha256": field["source_sha256"],
        "distinct_timber_contact_admission": receipt, "own_face_load_inventory": face_inventory,
        "complete_current_cut_witnesses_including_timber_faces": cuts,
        "current82own_wood_bearing_wrenches": wood, "current140own_capture_and_annulus_references": captures,
        "current70reference_material_thread_windows": windows, "duration_source": duration,
        "counts": {"wood_bearing_hosts": len(wood), "own_captures": len(captures), "physical_shafts": len(windows),
            "saved_material_cuts_recovered": sum(row["saved_material_cut_count"] for row in cuts),
            "timber_face_interactions": face_inventory["face_interaction_count"]},
        "general_distributed_yield_group_splitting_shear_torsion_stability_resistance": None,
        "actual_face_bedding_pressure_bearing_and_cut_stiffness_acceptance": None,
        "CAD_query_or_solve_executed": False, "old_failed_force_or_admission_transferred": False,
        "all18_completion_gates_open": True, "complete_joint_acceptance": False, "release": unit.RELEASE,
        "limits": ["Every corrected timber face force/couple is included at its own current point in the complete material-cut balance. No separately exported face alias is appended.",
            "Only unchanged reference geometry/material/duration inputs are reused. Gross cut stiffness/bedding parameters, actual face pressure, complete yielding/fracture/shear/stability and physical demand bounds remain unqualified.",
            "Exact normal-stress extrema can use the existing frozen selected-section helper after admission; current centroid/I is known only at the two previously queried recess cuts."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--field-sha256", required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    unit.require(not args.out.exists(), "preserve distinct timber-contact evidence")
    result = consume(args.field, args.field_sha256, admission_sha256=args.admission_sha256)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
