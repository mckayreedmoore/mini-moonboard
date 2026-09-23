"""Build and validate the unresolved barrel-joint resistance ledger.

This module inventories required checks.  It does not run a native solve,
derive a capacity, qualify hardware, or release the candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts.owner_barrel_native_connector_inventory import build_inventory

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "owner_barrel_resistance_ledger/v1"
CASES = (
    "a12-rear",
    "a12-forward",
    "a12-left",
    "k12-right",
    "k12-rear",
    "a1-rear",
)
HARDWARE_PATH = ROOT / "docs/barrel-nut-hardware-evidence.json"

FASTENER_MODES = {
    "bn_bolt_steel_interaction": {
        "category": "steel",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "bolt_material_minimum_controlled",
            "bolt_thread_and_body_geometry_controlled",
        ),
        "repo_mechanics": (
            "No complete bolt tension/shear/bending interaction is implemented "
            "for the provisional 1/4-20 products."
        ),
    },
    "bn_male_thread_stripping": {
        "category": "thread",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "bolt_material_minimum_controlled",
            "bolt_complete_thread_interval_controlled",
            "minimum_usable_thread_overlap_calculable",
        ),
        "repo_mechanics": "No supported male-thread stripping resistance exists.",
    },
    "bn_female_thread_stripping": {
        "category": "thread",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "barrel_material_minimum_controlled",
            "barrel_complete_thread_interval_controlled",
            "minimum_usable_thread_overlap_calculable",
        ),
        "repo_mechanics": "No supported barrel-thread stripping resistance exists.",
    },
    "bn_barrel_wall_and_flexure": {
        "category": "steel",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "barrel_material_minimum_controlled",
            "barrel_net_geometry_controlled",
        ),
        "repo_mechanics": (
            "Nominal CAD barrel envelope is geometry only; no wall, net-section, "
            "local-thread, bending, or opening resistance is implemented."
        ),
    },
    "bn_head_washer_bending": {
        "category": "steel",
        "method_status": "UNRESOLVED",
        "required_evidence": ("head_washer_selected_and_controlled",),
        "repo_mechanics": "No washer SKU or supported washer bending check exists.",
    },
    "bn_head_washer_wood_bearing": {
        "category": "wood",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "head_washer_selected_and_controlled",
            "wood_reference_basis_documented",
            "wood_connection_adjustments_resolved",
        ),
        "repo_mechanics": (
            "Ideal full-contact Fc-perpendicular values are constituent scales, "
            "not washer-seat, pull-through, breakout, or joint resistance."
        ),
    },
    "bn_bolt_lateral_submodel": {
        "category": "wood",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "bolt_material_minimum_controlled",
            "bolt_thread_and_body_geometry_controlled",
            "wood_reference_basis_documented",
            "wood_connection_adjustments_resolved",
        ),
        "repo_mechanics": (
            "2024 NDS lateral-yield equations are identified only as a possible "
            "constituent submodel; applicability and inputs remain unresolved."
        ),
    },
    "bn_barrel_wood_bearing": {
        "category": "wood",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "barrel_net_geometry_controlled",
            "wood_reference_basis_documented",
            "wood_connection_adjustments_resolved",
        ),
        "repo_mechanics": (
            "No applicable barrel-body bearing or local-bore resistance method exists."
        ),
    },
}

STATION_MODES = {
    "bn_wood_splitting_breakout": {
        "category": "wood",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "wood_reference_basis_documented",
            "wood_connection_adjustments_resolved",
            "exact_cut_section_resistance_method_supported",
        ),
        "repo_mechanics": (
            "Nominal ligament and clearance screens do not establish splitting, "
            "edge/end breakout, shear-out, or pocket-fracture resistance."
        ),
    },
    "bn_local_net_section_interaction": {
        "category": "wood",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "wood_reference_basis_documented",
            "wood_connection_adjustments_resolved",
            "exact_cut_section_resistance_method_supported",
        ),
        "repo_mechanics": (
            "Existing full-slot section sensitivities are not actual blind-cut "
            "combined axial/flexural/shear/torsional checks."
        ),
    },
    "bn_group_eccentricity_and_sharing": {
        "category": "group",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "joint_stiffness_and_clearance_supported",
            "signed_individual_fastener_demands_qualified",
        ),
        "repo_mechanics": (
            "No supported unequal-stiffness, eccentricity, clearance, opening, "
            "or reversal sharing method exists."
        ),
    },
    "bn_contact_pressure_and_opening": {
        "category": "contact",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "contact_law_supported",
            "signed_station_demands_qualified",
            "wood_connection_adjustments_resolved",
        ),
        "repo_mechanics": (
            "Source-built face cells are geometry inputs only; no supported contact "
            "stiffness or pressure/opening resistance is accepted."
        ),
    },
    "bn_joint_slip_serviceability": {
        "category": "group",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "joint_stiffness_and_clearance_supported",
            "serviceability_limits_frozen",
            "signed_station_demands_qualified",
        ),
        "repo_mechanics": (
            "No supported assembled-joint stiffness, hole-play, seating, residual-set, "
            "or serviceability limit exists."
        ),
    },
    "bn_reassembly_durability": {
        "category": "group",
        "method_status": "UNRESOLVED",
        "required_evidence": ("reassembly_qualification_supported",),
        "repo_mechanics": "No physical or defensible analytical reassembly bound exists.",
    },
    "bn_kicker_backing_transfer": {
        "category": "group",
        "method_status": "UNRESOLVED",
        "required_evidence": (
            "kicker_screw_resistance_supported",
            "signed_station_demands_qualified",
        ),
        "repo_mechanics": (
            "Receiver traces exist, but four fixed kicker screws and post/header "
            "joints have no complete qualified transfer resistance."
        ),
        "applicable_families": ("header_center",),
    },
}

ALL_MODES = {**FASTENER_MODES, **STATION_MODES}
ALLOWED_STATUSES = {"UNRESOLVED", "NOT_APPLICABLE", "PASS", "FAIL"}
BLOCKERS = {
    "BLK-SIGNED-CASE-RESPONSE": {
        "finding": "No accepted six-case candidate response supplies joint demands.",
        "closure": "Complete and accept source-bound six-case solves and demand extraction.",
    },
    "BLK-BOLT-MATERIAL": {
        "finding": "No controlled minimum bolt material applies to every provisional product family.",
        "closure": "Supply exact-product controlled minimum properties or a valid qualification route.",
    },
    "BLK-BOLT-GEOMETRY": {
        "finding": "Bolt body, root, complete-thread, runout, head, and tolerance geometry is not controlled.",
        "closure": "Supply exact-product controlled geometry and tolerance limits.",
    },
    "BLK-THREAD-OVERLAP": {
        "finding": "Minimum overlap of complete male and female threads is not calculable.",
        "closure": "Control both thread intervals and full tolerance stack, then establish required engagement.",
    },
    "BLK-BARREL-STRENGTH": {
        "finding": "Barrel material, thread, wall, and flexural resistance are unsupported.",
        "closure": "Supply controlled exact-part properties and mechanics or qualify complete joints.",
    },
    "BLK-BARREL-DRAWING": {
        "finding": "Barrel axis, wall, thread opening, lead-in, and tolerance geometry lacks a controlled drawing.",
        "closure": "Supply SKU-linked controlled geometry or predeclared measured-lot limits.",
    },
    "BLK-WASHER": {
        "finding": "No controlled head-side washer schedule or bending/seating basis is selected.",
        "closure": "Select exact washer products and close fit, bending, seating, and wood-bearing checks.",
    },
    "BLK-WOOD-REFERENCE": {
        "finding": "Required wood reference basis is absent.",
        "closure": "Freeze supported species, grade, condition, and reference values.",
    },
    "BLK-WOOD-ADJUSTMENTS": {
        "finding": "Candidate-specific wood adjustments and connection-zone inputs are unresolved.",
        "closure": "Resolve applicable adjustments and verify required material/section inputs.",
    },
    "BLK-WOOD-METHOD": {
        "finding": "No supported exact-cut splitting, breakout, or combined net-section method is complete.",
        "closure": "Implement geometry-specific supported mechanics or a predeclared qualification route.",
    },
    "BLK-JOINT-STIFFNESS": {
        "finding": "Complete joint stiffness, clearance, seating, and reversal behavior are unsupported.",
        "closure": "Establish justified stiffness and clearance bounds for each critical family.",
    },
    "BLK-SIGNED-DEMANDS": {
        "finding": "Signed per-fastener or per-station actions are not qualified.",
        "closure": "Extract balanced signed actions from accepted candidate cases.",
    },
    "BLK-CONTACT-LAW": {
        "finding": "Contact-cell geometry exists, but accepted compression/opening law does not.",
        "closure": "Support contact law and verify pressure, opening, reclosure, and sensitivity.",
    },
    "BLK-SERVICEABILITY-LIMITS": {
        "finding": "Slip, rotation, opening, and residual-set limits are not frozen.",
        "closure": "Freeze limits before assessing response and qualify required stiffness behavior.",
    },
    "BLK-REASSEMBLY-EVIDENCE": {
        "finding": "No qualified reassembly fit, damage, set, or engagement-loss evidence exists.",
        "closure": "Define supported service scope and complete relevant qualification evidence.",
    },
    "BLK-KICKER-TRANSFER": {
        "finding": "Kicker screw-to-post-to-header transfer lacks complete resistance evidence.",
        "closure": "Close fixed screw, post/header joint, connected-frame, and signed-action checks.",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_hardware() -> dict:
    return json.loads(HARDWARE_PATH.read_text())


def _bolt_family_map(hardware: dict) -> dict[float, dict]:
    rows = hardware["common_new_stack_components"]["bolt_product_families"]
    result = {float(row["nominal_length_mm"]): row for row in rows}
    if set(result) != {88.9, 114.3, 127.0, 152.4}:
        raise ValueError("Barrel bolt product-family lengths changed")
    return result


def _evidence_state(hardware: dict, bolt_family: dict) -> dict[str, bool]:
    barrel = hardware["common_new_stack_components"]["barrel"]
    washer = hardware["common_new_stack_components"]["head_side_washer"]
    material = hardware["material_basis"]
    exit_row = hardware["bn1_exit_assessment"]
    # Values are deliberately strict. Retail descriptions and nominal CAD do not
    # become controlled properties.
    return {
        "bolt_material_minimum_controlled": bolt_family["status"]
        == "documented_controlled",
        "bolt_thread_and_body_geometry_controlled": not any(
            "controlled" in item or "tolerance" in item or "runout" in item
            for item in bolt_family["missing"]
        ),
        "bolt_complete_thread_interval_controlled": not any(
            "thread" in item or "runout" in item or "chamfer" in item
            for item in bolt_family["missing"]
        ),
        "barrel_material_minimum_controlled": not any(
            "material" in item for item in barrel["missing"]
        ),
        "barrel_complete_thread_interval_controlled": not any(
            "thread" in item or "lead-in" in item for item in barrel["missing"]
        ),
        "barrel_net_geometry_controlled": not any(
            token in item
            for item in barrel["missing"]
            for token in ("drawing", "tolerance", "diameter", "length", "axis")
        ),
        "minimum_usable_thread_overlap_calculable": bool(
            exit_row["calculable_minimum_thread_overlap_available"]
        ),
        "head_washer_selected_and_controlled": (
            washer["selected_product"] is not None
            and washer["selection_status"] == "documented_controlled"
            and not washer["missing"]
        ),
        "wood_reference_basis_documented": material["specified_species_grade"][
            "status"
        ]
        == "documented_repository",
        "wood_connection_adjustments_resolved": not material["missing"],
        "exact_cut_section_resistance_method_supported": False,
        "joint_stiffness_and_clearance_supported": False,
        "signed_individual_fastener_demands_qualified": False,
        "signed_station_demands_qualified": False,
        "contact_law_supported": False,
        "serviceability_limits_frozen": False,
        "reassembly_qualification_supported": False,
        "kicker_screw_resistance_supported": False,
    }


def _blocker_codes(mode: str, state: dict[str, bool]) -> list[str]:
    evidence_codes = {
        "bolt_material_minimum_controlled": "BLK-BOLT-MATERIAL",
        "bolt_thread_and_body_geometry_controlled": "BLK-BOLT-GEOMETRY",
        "bolt_complete_thread_interval_controlled": "BLK-THREAD-OVERLAP",
        "barrel_material_minimum_controlled": "BLK-BARREL-STRENGTH",
        "barrel_complete_thread_interval_controlled": "BLK-THREAD-OVERLAP",
        "barrel_net_geometry_controlled": "BLK-BARREL-DRAWING",
        "minimum_usable_thread_overlap_calculable": "BLK-THREAD-OVERLAP",
        "head_washer_selected_and_controlled": "BLK-WASHER",
        "wood_reference_basis_documented": "BLK-WOOD-REFERENCE",
        "wood_connection_adjustments_resolved": "BLK-WOOD-ADJUSTMENTS",
        "exact_cut_section_resistance_method_supported": "BLK-WOOD-METHOD",
        "joint_stiffness_and_clearance_supported": "BLK-JOINT-STIFFNESS",
        "signed_individual_fastener_demands_qualified": "BLK-SIGNED-DEMANDS",
        "signed_station_demands_qualified": "BLK-SIGNED-DEMANDS",
        "contact_law_supported": "BLK-CONTACT-LAW",
        "serviceability_limits_frozen": "BLK-SERVICEABILITY-LIMITS",
        "reassembly_qualification_supported": "BLK-REASSEMBLY-EVIDENCE",
        "kicker_screw_resistance_supported": "BLK-KICKER-TRANSFER",
    }
    missing = [
        evidence_codes[field]
        for field in ALL_MODES[mode]["required_evidence"]
        if not state[field]
    ]
    return sorted({"BLK-SIGNED-CASE-RESPONSE", *missing})


def _case_results(status: str, blockers: list[str], *, applicable: bool) -> dict:
    result = {}
    for case in CASES:
        result[case] = {
            "status": status,
            "applicable": applicable,
            "demand": None,
            "demand_units": None,
            "resistance": None,
            "resistance_basis": None,
            "utilization": None,
            "blocker_codes": blockers,
        }
    return result


def _assessment(
    *,
    target_kind: str,
    target: str,
    station: str,
    family: str,
    mode: str,
    state: dict[str, bool],
) -> dict:
    definition = ALL_MODES[mode]
    applicable = family in definition.get("applicable_families", (family,))
    if not applicable:
        status = "NOT_APPLICABLE"
        blockers: list[str] = []
        reason = f"Mode applies only to {list(definition['applicable_families'])}."
    else:
        status = "UNRESOLVED"
        blockers = _blocker_codes(mode, state)
        reason = (
            "No qualified signed candidate demand or complete supported resistance "
            "exists; missing controlled inputs remain unresolved."
        )
    return {
        "target_kind": target_kind,
        "target": target,
        "station": station,
        "family": family,
        "mode": mode,
        "category": definition["category"],
        "applicable": applicable,
        "status": status,
        "reason": reason,
        "required_evidence": list(definition["required_evidence"]),
        "evidence_state": {field: state[field] for field in definition["required_evidence"]},
        "repo_mechanics": definition["repo_mechanics"],
        "case_results": _case_results(status, blockers, applicable=applicable),
    }


def _validate_case_result(
    result: dict,
    *,
    required_missing: bool,
    method_supported: bool,
) -> None:
    status = result.get("status")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unknown resistance status: {status}")
    if required_missing and status != "UNRESOLVED":
        raise ValueError("Missing controlled properties must remain UNRESOLVED")
    numbers = (result.get("demand"), result.get("resistance"), result.get("utilization"))
    if status in {"UNRESOLVED", "NOT_APPLICABLE"}:
        if any(value is not None for value in numbers):
            raise ValueError(f"{status} result cannot carry numeric acceptance values")
        if status == "UNRESOLVED" and not result.get("blocker_codes"):
            raise ValueError("UNRESOLVED result requires an exact blocker")
        return
    demand, resistance, utilization = numbers
    if not method_supported:
        raise ValueError("PASS/FAIL requires a supported resistance method")
    if (
        not all(isinstance(value, (int, float)) and math.isfinite(value) for value in numbers)
        or demand < 0
        or resistance <= 0
        or not math.isclose(utilization, demand / resistance, rel_tol=1e-9, abs_tol=1e-12)
    ):
        raise ValueError("PASS/FAIL requires compatible finite demand and resistance")
    if (status == "PASS") != (utilization <= 1.0):
        raise ValueError("PASS/FAIL conflicts with utilization")
    if not result.get("resistance_basis"):
        raise ValueError("PASS/FAIL requires a resistance basis")


def validate_ledger(
    ledger: dict,
    *,
    inventory: dict | None = None,
    hardware: dict | None = None,
) -> None:
    """Fail closed on missing targets, modes, cases, evidence, or numeric bases."""
    if ledger.get("schema") != SCHEMA:
        raise ValueError("Unexpected barrel resistance ledger schema")
    if inventory is None:
        inventory = build_inventory()
    if hardware is None:
        hardware = _load_hardware()
    bolt_families = _bolt_family_map(hardware)
    if ledger.get("case_order") != list(CASES):
        raise ValueError("Barrel resistance case identity changed")
    if set(ledger.get("mode_registry", {})) != set(ALL_MODES):
        raise ValueError("Barrel resistance mode registry is incomplete")
    if set(ledger.get("blocker_registry", {})) != set(BLOCKERS):
        raise ValueError("Barrel resistance blocker registry is incomplete")
    source_identity = ledger.get("source_identity", {})
    if (
        source_identity.get("connector_inventory_fingerprint_sha256")
        != inventory["inventory_fingerprint_sha256"]
        or source_identity.get("hardware_evidence_sha256") != _sha256(HARDWARE_PATH)
        or source_identity.get("criteria_sha256")
        != _sha256(ROOT / "docs/barrel-nut-criteria.md")
    ):
        raise ValueError("Barrel resistance ledger source identity is stale")
    for mode, definition in ALL_MODES.items():
        row = ledger["mode_registry"][mode]
        if (
            row.get("scope")
            != ("fastener" if mode in FASTENER_MODES else "station")
            or row.get("category") != definition["category"]
            or row.get("required_evidence") != list(definition["required_evidence"])
            or row.get("method_status") != definition["method_status"]
        ):
            raise ValueError(f"{mode}: mode definition differs from checker")
    fasteners = ledger.get("fasteners", {})
    stations = ledger.get("stations", {})
    if set(fasteners) != set(inventory["bolts"]) or len(fasteners) != 46:
        raise ValueError("Barrel resistance ledger does not cover all 46 fasteners")
    if set(stations) != set(inventory["stations"]) or len(stations) != 24:
        raise ValueError("Barrel resistance ledger does not cover all 24 duties")
    for name, row in fasteners.items():
        if row["station"] != inventory["bolts"][name]["station"]:
            raise ValueError(f"{name}: station ownership changed")
        if set(row["assessments"]) != set(FASTENER_MODES):
            raise ValueError(f"{name}: fastener-mode coverage is incomplete")
        expected_state = _evidence_state(
            hardware,
            bolt_families[round(float(inventory["bolts"][name]["length_mm"]), 1)],
        )
        for mode, assessment in row["assessments"].items():
            expected = {
                field: expected_state[field]
                for field in FASTENER_MODES[mode]["required_evidence"]
            }
            if assessment["evidence_state"] != expected:
                raise ValueError(f"{name}: evidence state differs from hardware ledger")
    for name, row in stations.items():
        if set(row["fastener_names"]) != set(inventory["stations"][name]["bolt_names"]):
            raise ValueError(f"{name}: fastener membership changed")
        if set(row["assessments"]) != set(STATION_MODES):
            raise ValueError(f"{name}: station-mode coverage is incomplete")
    for target_rows in (fasteners, stations):
        for row in target_rows.values():
            for mode, assessment in row["assessments"].items():
                if set(assessment["case_results"]) != set(CASES):
                    raise ValueError("Every assessment must cover all six cases")
                if any(
                    code not in BLOCKERS
                    for result in assessment["case_results"].values()
                    for code in result.get("blocker_codes", ())
                ):
                    raise ValueError("Assessment cites an unknown blocker code")
                required_missing = any(
                    not assessment["evidence_state"][field]
                    for field in ALL_MODES[mode]["required_evidence"]
                )
                if required_missing and assessment["applicable"] and assessment["status"] != "UNRESOLVED":
                    raise ValueError("Missing controlled properties must remain UNRESOLVED")
                for result in assessment["case_results"].values():
                    _validate_case_result(
                        result,
                        required_missing=required_missing and assessment["applicable"],
                        method_supported=(
                            ledger["mode_registry"][mode]["method_status"]
                            == "SUPPORTED"
                        ),
                    )
    summary = ledger.get("summary", {})
    if (
        summary.get("station_count") != 24
        or summary.get("fastener_count") != 46
        or summary.get("status") != "UNRESOLVED"
        or summary.get("pass_count") != 0
        or ledger.get("structural_release") is not False
    ):
        raise ValueError("Barrel resistance summary or release boundary changed")


def build_ledger(*, inventory: dict | None = None, hardware: dict | None = None) -> dict:
    """Build complete unresolved assessment matrix from current source inventory."""
    if inventory is None:
        inventory = build_inventory()
    if hardware is None:
        hardware = _load_hardware()
    if len(inventory["stations"]) != 24 or len(inventory["bolts"]) != 46:
        raise ValueError("Resistance ledger requires current 24-duty/46-fastener pose")
    bolt_families = _bolt_family_map(hardware)
    fasteners = {}
    family_counts: dict[str, int] = {}
    for name, bolt in sorted(inventory["bolts"].items()):
        nominal_length = round(float(bolt["length_mm"]), 1)
        if nominal_length not in bolt_families:
            raise ValueError(f"{name}: no evidence family for {nominal_length} mm bolt")
        product_family = bolt_families[nominal_length]
        family_counts[product_family["id"]] = family_counts.get(product_family["id"], 0) + 1
        station = bolt["station"]
        family = inventory["stations"][station]["family"]
        state = _evidence_state(hardware, product_family)
        fasteners[name] = {
            "station": station,
            "family": family,
            "entry_member": bolt["entry_member"],
            "receiving_member": bolt["receiving_member"],
            "barrel_name": bolt["barrel_name"],
            "bolt_product_family": product_family["id"],
            "nominal_bolt_length_mm": nominal_length,
            "assessments": {
                mode: _assessment(
                    target_kind="fastener",
                    target=name,
                    station=station,
                    family=family,
                    mode=mode,
                    state=state,
                )
                for mode in FASTENER_MODES
            },
        }
    expected_family_counts = {
        row["id"]: row["required_quantity"]
        for row in hardware["common_new_stack_components"]["bolt_product_families"]
    }
    if family_counts != expected_family_counts:
        raise ValueError(
            f"Hardware evidence quantities differ from geometry: {family_counts}"
        )

    # Station modes use one conservative common evidence state. Bolt-family
    # fields are irrelevant to their declared evidence requirements.
    common_state = _evidence_state(hardware, next(iter(bolt_families.values())))
    stations = {}
    for name, source in sorted(inventory["stations"].items()):
        family = source["family"]
        stations[name] = {
            "family": family,
            "side": source["side"],
            "timber_members": source["timber_members"],
            "fastener_names": source["bolt_names"],
            "assessments": {
                mode: _assessment(
                    target_kind="station",
                    target=name,
                    station=name,
                    family=family,
                    mode=mode,
                    state=common_state,
                )
                for mode in STATION_MODES
            },
        }
    ledger = {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "status": "resistance_inputs_and_demands_unresolved",
        "purpose": (
            "Complete coverage ledger only; no capacity, demand acceptance, "
            "hardware qualification, fabrication release, or climber rating."
        ),
        "source_identity": {
            "connector_inventory_fingerprint_sha256": inventory[
                "inventory_fingerprint_sha256"
            ],
            "hardware_evidence_path": str(HARDWARE_PATH.relative_to(ROOT)),
            "hardware_evidence_sha256": _sha256(HARDWARE_PATH),
            "criteria_path": "docs/barrel-nut-criteria.md",
            "criteria_sha256": _sha256(ROOT / "docs/barrel-nut-criteria.md"),
            "generator_path": "scripts/owner_barrel_resistance_ledger.py",
        },
        "case_order": list(CASES),
        "mode_registry": {
            mode: {
                "scope": "fastener" if mode in FASTENER_MODES else "station",
                "category": row["category"],
                "required_evidence": list(row["required_evidence"]),
                "method_status": row["method_status"],
                "repo_mechanics": row["repo_mechanics"],
                **(
                    {"applicable_families": list(row["applicable_families"])}
                    if "applicable_families" in row
                    else {}
                ),
            }
            for mode, row in ALL_MODES.items()
        },
        "blocker_registry": BLOCKERS,
        "fasteners": fasteners,
        "stations": stations,
        "summary": {
            "status": "UNRESOLVED",
            "station_count": len(stations),
            "fastener_count": len(fasteners),
            "fastener_assessment_count": len(fasteners) * len(FASTENER_MODES),
            "station_assessment_count": len(stations) * len(STATION_MODES),
            "case_result_count": (
                len(fasteners) * len(FASTENER_MODES)
                + len(stations) * len(STATION_MODES)
            )
            * len(CASES),
            "pass_count": 0,
            "fail_count": 0,
            "unresolved_reason": (
                "Controlled bolt/thread/barrel/washer inputs, supported wood/contact/"
                "group methods, qualified stiffness, and signed candidate demands are missing."
            ),
        },
        "structural_release": False,
        "diy_ready": False,
    }
    validate_ledger(ledger, inventory=inventory, hardware=hardware)
    return ledger


def render(ledger: dict) -> str:
    return json.dumps(ledger, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ledger = build_ledger()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(ledger))


if __name__ == "__main__":
    main()
