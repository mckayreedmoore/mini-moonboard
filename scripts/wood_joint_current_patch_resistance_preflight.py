"""Source-bound, pre-demand resistance preparation for the four-bolt patch.

This is a deliberately narrow current-artifact calculation. It reports the
ideal DF-L No. 2 wood-bearing reference under each washer and center-to-center
bolt-group geometry. It does not infer member loads, bolt sharing, wood grade,
bolt yield strength, or complete-joint resistance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from mini_moonboard.wood_joint_bolt_resistance import (
    wood_washer_annulus_reference_lbf,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
INPUT_PATHS = {
    "inventory": EVALUATION_ROOT / "ordinary-patch-inputs-attempt01/inventory.json",
    "contact_classification": EVALUATION_ROOT
    / "ordinary-patch-contact-classification-attempt01/classification.json",
    "material_map": EVALUATION_ROOT
    / "ordinary-patch-materials-attempt01/material-map.json",
}
EXPECTED_INPUT_SHA256 = {
    "inventory": "70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3",
    "contact_classification": "18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13",
    "material_map": "9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4",
}
OUTPUT_PATH = (
    EVALUATION_ROOT
    / "ordinary-patch-resistance-preflight-attempt01/resistance-preflight.json"
)

EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_WOOD_IDS = {
    "bottom_center_right_cleat",
    "base_rail_bottom_right",
    "base_principal_center_right",
}
EXPECTED_BOLTED_INTERFACES = {
    "bottom_center_right_cleat_to_base_rail_bottom_right": {
        "members": ["bottom_center_right_cleat", "base_rail_bottom_right"],
        "bolts": [
            "bottom_center/clip_horizontal_bottom_right_1/rail_1",
            "bottom_center/clip_horizontal_bottom_right_1/rail_2",
        ],
    },
    "bottom_center_right_cleat_to_base_principal_center_right": {
        "members": [
            "bottom_center_right_cleat",
            "base_principal_center_right",
        ],
        "bolts": [
            "bottom_center/clip_horizontal_bottom_right_1/principal_1",
            "bottom_center/clip_horizontal_bottom_right_1/principal_2",
        ],
    },
}
EXPECTED_WOOD_SEAT_KINDS = {
    "head_washer_to_first_receiver",
    "nut_washer_to_last_receiver",
}

MM_PER_INCH = 25.4
NEWTONS_PER_POUND_FORCE = 4.4482216152605
MODELED_SHAFT_DIAMETER_MM = 6.35
WOOD_BORE_DIAMETER_MM = 7.5
WASHER_ID_MIN_MM = 7.7978
WASHER_ID_MAX_MM = 8.3058
WASHER_OD_MIN_MM = 18.4658
WASHER_OD_MAX_MM = 19.0246
GEOMETRY_TOLERANCE = 1e-6


class InputContractError(ValueError):
    """Raised when a source manifest does not match the frozen patch scope."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frozen_inputs(
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Load only the three pinned current-patch source manifests."""
    inputs: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for input_id, relative_path in INPUT_PATHS.items():
        path = repo_root / relative_path
        observed_hash = _sha256(path)
        expected_hash = EXPECTED_INPUT_SHA256[input_id]
        if observed_hash != expected_hash:
            raise InputContractError(
                f"{input_id} hash changed: expected {expected_hash}, "
                f"observed {observed_hash}"
            )
        inputs[input_id] = json.loads(path.read_text(encoding="utf-8"))
        hashes[input_id] = observed_hash
    return inputs, hashes


def _finite_vector(values: Any, *, size: int, label: str) -> tuple[float, ...]:
    if not isinstance(values, list) or len(values) != size:
        raise InputContractError(f"{label} must be a {size}-vector")
    result = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in result):
        raise InputContractError(f"{label} must contain finite values")
    return result


def _unit(vector: tuple[float, ...], *, label: str) -> tuple[float, ...]:
    length = math.sqrt(sum(value * value for value in vector))
    if length <= 0 or not math.isfinite(length):
        raise InputContractError(f"{label} must be nonzero and finite")
    return tuple(value / length for value in vector)


def _dot(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def _subtract(first: tuple[float, ...], second: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(first, second, strict=True))


def _norm(vector: tuple[float, ...]) -> float:
    return math.sqrt(_dot(vector, vector))


def _validate_frozen_scope(
    inventory: dict[str, Any],
    classification: dict[str, Any],
    material_map: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    candidate = inventory.get("candidate", {})
    if candidate.get("revision_id") != EXPECTED_REVISION:
        raise InputContractError("inventory is not the owner-reviewed current revision")
    scope = inventory.get("scope", {})
    if (
        scope.get("physical_bolts") != 4
        or scope.get("finished_wood_bodies") != 3
        or scope.get("wood_interfaces") != 3
        or scope.get("strength_or_joint_acceptance_claim") is not False
    ):
        raise InputContractError("inventory no longer describes the frozen 3/4 patch")

    wood_rows = inventory.get("wood_bodies", [])
    wood_by_id = {row.get("part_id"): row for row in wood_rows}
    if set(wood_by_id) != EXPECTED_WOOD_IDS:
        raise InputContractError("wood member inventory differs from the frozen patch")
    bolts = inventory.get("physical_bolts", [])
    bolt_by_id = {row.get("physical_bolt_id"): row for row in bolts}
    expected_bolt_ids = {
        bolt_id
        for interface in EXPECTED_BOLTED_INTERFACES.values()
        for bolt_id in interface["bolts"]
    }
    if len(bolts) != 4 or set(bolt_by_id) != expected_bolt_ids:
        raise InputContractError(
            "physical bolt inventory differs from the frozen patch"
        )

    interface_by_id = {
        row.get("interface_id"): row for row in inventory.get("wood_interfaces", [])
    }
    if len(interface_by_id) != 3:
        raise InputContractError(
            "expected two bolted interfaces and one butt interface"
        )
    for interface_id, expected in EXPECTED_BOLTED_INTERFACES.items():
        row = interface_by_id.get(interface_id)
        if row is None:
            raise InputContractError(f"missing current interface {interface_id}")
        if row.get("members") != expected["members"]:
            raise InputContractError(f"member order changed for {interface_id}")
        if row.get("bolt_axis_ids") != expected["bolts"]:
            raise InputContractError(f"bolt membership changed for {interface_id}")

    if classification.get("status") != (
        "CURRENT_PATCH_CONTACT_GEOMETRY_INCOMPLETE_RESPONSE_UNREADY"
    ):
        raise InputContractError(
            "contact classification status differs from frozen input"
        )
    if (
        classification.get("contact_laws_assigned") is not False
        or classification.get("response_ready") is not False
        or classification.get("native_solve_ready") is not False
        or classification.get("scope", {}).get("washer_wood_seats") != 8
    ):
        raise InputContractError(
            "contact classification crosses the geometry-only boundary"
        )

    if material_map.get("status") != "proposal_only_current_patch_material_map":
        raise InputContractError("material map is not the current proposal-only map")
    if (
        material_map.get("scope", {}).get("strength_or_capacity_claim") is not False
        or material_map.get("scope", {}).get("delivered_wood_properties_verified")
        is not False
        or material_map.get("scope", {}).get("delivered_metal_properties_verified")
        is not False
    ):
        raise InputContractError(
            "material map is not a proposal-only material assignment"
        )

    expected_grains = {
        part_id: _unit(
            _finite_vector(
                row.get("grain", {}).get("grain_axis_global_xyz"),
                size=3,
                label=f"{part_id} grain axis",
            ),
            label=f"{part_id} grain axis",
        )
        for part_id, row in wood_by_id.items()
    }
    alternatives = material_map.get("wood_orientation_alternatives", [])
    if len(alternatives) != 2:
        raise InputContractError(
            "current wood orientation proposal must keep both R/T cases"
        )
    for alternative in alternatives:
        orientations = {
            row.get("part_id"): row for row in alternative.get("body_orientations", [])
        }
        if set(orientations) != EXPECTED_WOOD_IDS:
            raise InputContractError("material map wood-body inventory is incomplete")
        for part_id, row in orientations.items():
            material_grain = _unit(
                _finite_vector(
                    row.get("grain_axis_global_xyz"),
                    size=3,
                    label=f"{part_id} material grain axis",
                ),
                label=f"{part_id} material grain axis",
            )
            if abs(abs(_dot(expected_grains[part_id], material_grain)) - 1.0) > 1e-7:
                raise InputContractError(
                    f"material orientation grain conflicts for {part_id}"
                )
            if row.get("delivered_stock_observed") is not False:
                raise InputContractError("material orientation must remain a scenario")

    return wood_by_id, bolt_by_id


def _washer_reference_bounds() -> dict[str, Any]:
    lower = wood_washer_annulus_reference_lbf(
        washer_outer_diameter_in=WASHER_OD_MIN_MM / MM_PER_INCH,
        washer_inner_diameter_in=WASHER_ID_MAX_MM / MM_PER_INCH,
        wood_bore_diameter_in=WOOD_BORE_DIAMETER_MM / MM_PER_INCH,
    )
    upper = wood_washer_annulus_reference_lbf(
        washer_outer_diameter_in=WASHER_OD_MAX_MM / MM_PER_INCH,
        washer_inner_diameter_in=WASHER_ID_MIN_MM / MM_PER_INCH,
        wood_bore_diameter_in=WOOD_BORE_DIAMETER_MM / MM_PER_INCH,
    )

    def area_for(outer_mm: float, washer_id_mm: float) -> float:
        unsupported_diameter_mm = max(WOOD_BORE_DIAMETER_MM, washer_id_mm)
        return math.pi / 4 * (outer_mm**2 - unsupported_diameter_mm**2)

    return {
        "status": "conditional_per_seat_wood_reference_only",
        "wood_property_basis": "dry DF-L No. 2 Fc-perp = 625 psi per 2024 NDS Supplement Table 4A",
        "wood_species_grade_verified_for_delivered_stock": False,
        "washer_product_selected_or_received": False,
        "washer_dimensional_basis": "1/4-in Type A Wide plain washer dimensional envelope",
        "washer_dimensions_mm": {
            "inner_diameter": {"min": WASHER_ID_MIN_MM, "max": WASHER_ID_MAX_MM},
            "outer_diameter": {"min": WASHER_OD_MIN_MM, "max": WASHER_OD_MAX_MM},
        },
        "wood_bore_diameter_mm": {
            "value": WOOD_BORE_DIAMETER_MM,
            "meaning": "current CAD occupancy geometry, not a drilling instruction",
        },
        "calculation": "625 psi × π/4 × (washer OD² − max(wood bore, washer ID)²); no bearing-area increase",
        "lower_per_seat": {
            "annulus_area_mm2": area_for(WASHER_OD_MIN_MM, WASHER_ID_MAX_MM),
            "reference_lbf": lower["wood_bearing_reference_lbf"],
            "reference_N": lower["wood_bearing_reference_lbf"]
            * NEWTONS_PER_POUND_FORCE,
        },
        "upper_per_seat": {
            "annulus_area_mm2": area_for(WASHER_OD_MAX_MM, WASHER_ID_MIN_MM),
            "reference_lbf": upper["wood_bearing_reference_lbf"],
            "reference_N": upper["wood_bearing_reference_lbf"]
            * NEWTONS_PER_POUND_FORCE,
        },
        "limitations": [
            "Conditional on delivered wood meeting dry DF-L No. 2 applicability; current stock is unobserved.",
            "Ideal uniform compression over a complete annulus, full washer footprint on sound wood, no preload, and no bearing-area-factor increase.",
            "Not actual contact pressure, per-bolt force, adjusted design resistance, washer steel resistance, or joint capacity.",
            "Bounds apply per washer seat and are not summed across the eight seats.",
        ],
    }


def _washer_seat_rows(
    classification: dict[str, Any],
    wood_by_id: dict[str, dict[str, Any]],
    material_map: dict[str, Any],
    bolt_by_id: dict[str, dict[str, Any]],
    reference_bounds: dict[str, Any],
) -> list[dict[str, Any]]:
    source_id_by_wood_elset = {
        row.get("mesh_body_id"): row.get("source_body_id")
        for row in material_map.get("elset_body_map", [])
        if row.get("owner_kind") == "wood_member"
    }
    if set(source_id_by_wood_elset.values()) != EXPECTED_WOOD_IDS:
        raise InputContractError(
            "material map does not bind all three source wood members"
        )
    rows: list[dict[str, Any]] = []
    for seat in classification.get("hardware_seats", []):
        if seat.get("seat_kind") not in EXPECTED_WOOD_SEAT_KINDS:
            continue
        bolt_id = seat.get("physical_bolt_id")
        bolt = bolt_by_id.get(bolt_id)
        if bolt is None:
            raise InputContractError(f"washer seat references unknown bolt {bolt_id}")
        if seat.get("status") != "FINITE_OPPOSED_PLANAR_SEAT_GEOMETRY_VERIFIED":
            raise InputContractError(
                f"washer-to-wood geometry is not verified: {seat.get('seat_id')}"
            )
        if (
            seat.get("preload_or_active_pressure_claim") is not False
            or seat.get("load_transfer_law_assigned") is not False
        ):
            raise InputContractError(
                "washer geometry input contains a pressure/load claim"
            )
        pair = seat.get("owner_pair", [])
        if len(pair) != 2:
            raise InputContractError("washer seat owner pair is malformed")
        wood_elsets = [owner for owner in pair if owner in source_id_by_wood_elset]
        if len(wood_elsets) != 1:
            raise InputContractError(
                f"washer seat lacks one wood ELSET owner: {seat.get('seat_id')}"
            )
        receiver_id = source_id_by_wood_elset[wood_elsets[0]]
        expected_receiver = (
            bolt["receivers_head_to_nut"][0]
            if seat["seat_kind"] == "head_washer_to_first_receiver"
            else bolt["receivers_head_to_nut"][-1]
        )
        if receiver_id != expected_receiver or receiver_id not in wood_by_id:
            raise InputContractError(
                f"washer seat receiver order mismatch: {seat.get('seat_id')}"
            )
        overlay_area = float(seat.get("mesh_overlay", {}).get("area_mm2", math.nan))
        if not math.isfinite(overlay_area) or overlay_area <= 0:
            raise InputContractError(
                "washer wood-seat geometry must have a finite positive overlay"
            )
        rows.append(
            {
                "seat_id": seat["seat_id"],
                "physical_bolt_id": bolt_id,
                "seat_kind": seat["seat_kind"],
                "wood_receiver_id": receiver_id,
                "geometry_status": seat["status"],
                "mesh_overlay_area_mm2": overlay_area,
                "pressure_or_preload_established": False,
                "per_seat_reference_range_N": [
                    reference_bounds["lower_per_seat"]["reference_N"],
                    reference_bounds["upper_per_seat"]["reference_N"],
                ],
                "result_state": "CONDITIONAL_WOOD_BEARING_REFERENCE_ONLY",
            }
        )
    if len(rows) != 8:
        raise InputContractError(
            f"expected eight washer-to-wood seats, found {len(rows)}"
        )
    seen = {row["seat_id"] for row in rows}
    if len(seen) != 8:
        raise InputContractError("duplicate washer-to-wood seat identity")
    return sorted(rows, key=lambda row: row["seat_id"])


def _group_geometry(
    inventory: dict[str, Any],
    wood_by_id: dict[str, dict[str, Any]],
    bolt_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    interface_by_id = {
        row["interface_id"]: row for row in inventory.get("wood_interfaces", [])
    }
    results: list[dict[str, Any]] = []
    for interface_id, expected in EXPECTED_BOLTED_INTERFACES.items():
        interface = interface_by_id[interface_id]
        bolt_ids = interface["bolt_axis_ids"]
        first = bolt_by_id[bolt_ids[0]]
        second = bolt_by_id[bolt_ids[1]]
        direction = _unit(
            _finite_vector(
                first.get("axis_direction_head_to_nut_global_xyz"),
                size=3,
                label=f"{bolt_ids[0]} axis",
            ),
            label=f"{bolt_ids[0]} axis",
        )
        second_direction = _unit(
            _finite_vector(
                second.get("axis_direction_head_to_nut_global_xyz"),
                size=3,
                label=f"{bolt_ids[1]} axis",
            ),
            label=f"{bolt_ids[1]} axis",
        )
        if abs(abs(_dot(direction, second_direction)) - 1.0) > 1e-8:
            raise InputContractError(f"bolt axes are not parallel at {interface_id}")
        origins = [
            _finite_vector(
                bolt_by_id[bolt_id].get("axis_origin_global_xyz_mm"),
                size=3,
                label=f"{bolt_id} axis origin",
            )
            for bolt_id in bolt_ids
        ]
        delta = _subtract(origins[1], origins[0])
        axial_offset = _dot(delta, direction)
        pitch_vector = tuple(
            delta[index] - axial_offset * direction[index] for index in range(3)
        )
        pitch = _norm(pitch_vector)
        if pitch <= 0 or abs(axial_offset) > GEOMETRY_TOLERANCE:
            raise InputContractError(
                f"bolt pair does not have a planar group pitch at {interface_id}"
            )
        pitch_direction = _unit(pitch_vector, label=f"{interface_id} pitch direction")
        receiver_angles: list[dict[str, Any]] = []
        for member_id in expected["members"]:
            grain = _unit(
                _finite_vector(
                    wood_by_id[member_id].get("grain", {}).get("grain_axis_global_xyz"),
                    size=3,
                    label=f"{member_id} grain axis",
                ),
                label=f"{member_id} grain axis",
            )
            angle = math.degrees(
                math.acos(min(1.0, max(0.0, abs(_dot(direction, grain)))))
            )
            receiver_angles.append(
                {
                    "wood_member_id": member_id,
                    "bolt_axis_to_declared_grain_angle_degrees": angle,
                    "bolt_group_pitch_to_declared_grain_angle_degrees": math.degrees(
                        math.acos(
                            min(
                                1.0,
                                max(0.0, abs(_dot(pitch_direction, grain))),
                            )
                        )
                    ),
                    "meaning": "geometry orientation of bolt axes and pair line only; not a wood load-to-grain angle or NDS spacing disposition",
                }
            )
        results.append(
            {
                "interface_id": interface_id,
                "physical_bolt_ids": bolt_ids,
                "bolt_center_pitch_mm": pitch,
                "axial_datum_offset_mm": axial_offset,
                "modeled_shaft_diameter_mm": MODELED_SHAFT_DIAMETER_MM,
                "pitch_over_modeled_shaft_diameter": pitch / MODELED_SHAFT_DIAMETER_MM,
                "diameter_basis": "6.35 mm unthreaded CAD occupancy envelope; not delivered bolt D",
                "receiver_axis_grain_geometry": receiver_angles,
                "classification": "GEOMETRY_ONLY_NO_NDS_SPACING_OR_GROUP_PASS",
            }
        )
    return results


def _thread_fraction_limits(bolt_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Calculate current member-specific NDS 1/4 thread-bearing screens."""
    rows: list[dict[str, Any]] = []
    for bolt_id, bolt in sorted(bolt_by_id.items()):
        receiver_rows = bolt.get("raw_receiver_projected_intervals", [])
        if len(receiver_rows) != 2:
            raise InputContractError(
                f"expected two source-projected receiver intervals for {bolt_id}"
            )
        member_rows = []
        for receiver in receiver_rows:
            if (
                receiver.get("current_shaft_covers_raw_receiver") is not True
                or receiver.get("projection_gaps_mm") != []
            ):
                raise InputContractError(
                    f"bolt shaft does not continuously span receiver {receiver.get('member_id')}"
                )
            bearing_length_mm = float(
                receiver.get("projected_material_length_mm", math.nan)
            )
            if not math.isfinite(bearing_length_mm) or bearing_length_mm <= 0:
                raise InputContractError(
                    "receiver bearing length must be finite and positive"
                )
            member_rows.append(
                {
                    "wood_member_id": receiver["member_id"],
                    "projected_bearing_length_mm": bearing_length_mm,
                    "maximum_thread_bearing_length_for_full_body_D_mm": (
                        bearing_length_mm / 4
                    ),
                    "delivered_thread_bearing_length_mm": None,
                    "thread_fraction_status": "unverified_no_delivered_thread_location",
                }
            )
        rows.append({"physical_bolt_id": bolt_id, "members": member_rows})

    return {
        "status": "NDS_THREAD_FRACTION_LIMITS_COMPUTED_OCCUPANCY_UNVERIFIED",
        "method": "NDS-2024 §§12.3.7.1–12.3.7.2: full-body D exception only if thread bearing is at most one-quarter of the complete bearing length in each member holding threads; otherwise use Dr unless detailed analysis is supplied.",
        "per_bolt_member_limits": rows,
        "limits": "These are thresholds, not evidence that the delivered threads satisfy them; bolt nominal length or the 6.35 mm CAD shaft does not locate thread bearing.",
    }


def build_report(
    inventory: dict[str, Any],
    classification: dict[str, Any],
    material_map: dict[str, Any],
    input_hashes: dict[str, str],
) -> dict[str, Any]:
    """Build the current ordinary-patch preflight from its frozen manifests."""
    if set(input_hashes) != set(INPUT_PATHS):
        raise InputContractError(
            "input hash set does not match the three frozen manifests"
        )
    for input_id, expected_hash in EXPECTED_INPUT_SHA256.items():
        if input_hashes[input_id] != expected_hash:
            raise InputContractError(f"unexpected hash for {input_id}")

    wood_by_id, bolt_by_id = _validate_frozen_scope(
        inventory, classification, material_map
    )
    reference_bounds = _washer_reference_bounds()
    washer_rows = _washer_seat_rows(
        classification,
        wood_by_id,
        material_map,
        bolt_by_id,
        reference_bounds,
    )
    group_rows = _group_geometry(inventory, wood_by_id, bolt_by_id)
    thread_fraction_limits = _thread_fraction_limits(bolt_by_id)

    fyb_gate = {
        "status": "unresolved",
        "missing_resistance_inputs": [
            "delivered bolt identity and measured/applicable D and Dr",
            "member-specific thread-bearing length in the 88.9 mm cleat and 38.1 mm host for each bolt",
            "ASTM F1575 bending-yield test or ASTM F606 tensile-yield evaluation with an applicable Fyb derivation for delivered bolts",
            "verified wood species/grade and applicable NDS design adjustments",
        ],
        "later_demand_and_response_inputs": [
            "fresh per-bolt lateral actions at each wood shear plane",
            "physically supported bolt/contact load-sharing response for the current complete joint",
        ],
        "prohibited_substitution": "Do not assign SAE J429 Grade 5 yield or an old bolt/angle capacity as Fyb.",
        "source_method": "NDS-2024 §§12.3.6.2, 12.3.7.1–12.3.7.2; see bolt-resistance-basis.md",
        "member_thread_fraction_limits": thread_fraction_limits,
    }
    end_edge_group = {
        "status": "unresolved_geometry_and_demand_classification",
        "available_geometry": "Two current two-bolt center pitches are computed from frozen bolt axes below.",
        "missing_geometry_and_classification_inputs": [
            "source-bound distances from each bolt center to actual finished member ends and edges, resolved in receiver grain/local axes rather than from overall bounds",
            "fresh signed per-bolt force direction to identify the loaded end/edge and the governing NDS spacing/end-distance cases",
            "member-specific splitting/group action and applicable NDS adjustment basis",
        ],
        "later_demand_and_response_inputs": [
            "fresh per-bolt force magnitudes and group/contact distribution to compare with applicable component/group references",
        ],
        "limits": "Center pitch alone is not a minimum-spacing, loaded-end, edge, tear-out, splitting, or group-resistance check.",
    }
    washer_steel = {
        "status": "unresolved",
        "missing": [
            "selected/delivered washer identity, material and dimensions",
            "applicable washer bending/spreading method for the actual wood support and load footprint",
            "fresh bolt force and supported contact/load distribution at each seat",
        ],
        "limits": "The conditional wood Fc-perp annulus reference does not bound washer steel response.",
    }
    return {
        "schema": "wood_joint_current_patch_resistance_preflight/v1",
        "status": "PRE_DEMAND_COMPONENT_REFERENCES_ONLY",
        "candidate": {
            "revision_id": EXPECTED_REVISION,
            "implementation_revision": inventory["candidate"][
                "implementation_revision"
            ],
            "wood_member_count": 3,
            "physical_bolt_count": 4,
            "bolted_interface_count": 2,
            "separate_unbolted_butt_interface": "base_rail_bottom_right_to_base_principal_center_right",
        },
        "inputs": {
            input_id: {
                "path": INPUT_PATHS[input_id].as_posix(),
                "sha256": input_hashes[input_id],
            }
            for input_id in INPUT_PATHS
        },
        "wood_washer_bearing": {
            **reference_bounds,
            "seat_count": len(washer_rows),
            "seats": washer_rows,
        },
        "two_bolt_group_geometry": group_rows,
        "resistance_gates": {
            "NDS_dowel_yield_and_member_bearing": fyb_gate,
            "NDS_end_edge_spacing_and_group_modes": end_edge_group,
            "washer_steel_bending_spreading": washer_steel,
            "bolt_tension_shear_and_nut_thread_resistance": {
                "status": "unresolved",
                "missing": [
                    "delivered bolt/nut product and grade evidence",
                    "controlling delivered tensile/shear sections and certified steel yield property",
                    "functional thread fit/engagement and applicable nut proof/strip basis",
                    "applicable tension/shear interaction method for the timber joint",
                ],
                "later_demand_inputs": ["fresh per-fastener force resultants"],
                "limits": "No Grade 5 property or resistance is inferred from a catalog candidate or generic steel elastic scenario.",
            },
        },
        "demand_and_acceptance": {
            "fresh_complete_joint_actions_present": False,
            "fastener_response_or_load_shares_present": False,
            "historical_demands_or_capacities_imported": False,
            "joint_adequacy_claim": False,
            "criteria_passed": [],
        },
        "claim_boundary": [
            "The washer result is a conditional per-seat wood-bearing reference, not an adjusted design resistance or acceptance check.",
            "Finite opposed seat geometry does not establish active pressure, preload, or load transfer.",
            "No per-seat references are summed and no equal bolt load share is assumed.",
            "The 3-member patch and its separate unbolted butt contact remain part of the complete load path; the two bolted interfaces are not an isolated accepted joint.",
            "No historical WJ04/WJ12/WJ24 demand or pass is inherited; no wood species/grade or delivered hardware is verified.",
        ],
    }


def run(repo_root: Path = REPO_ROOT) -> tuple[dict[str, Any], Path]:
    inputs, hashes = load_frozen_inputs(repo_root)
    report = build_report(
        inventory=inputs["inventory"],
        classification=inputs["contact_classification"],
        material_map=inputs["material_map"],
        input_hashes=hashes,
    )
    output_path = repo_root / OUTPUT_PATH
    return report, output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write JSON to this path")
    args = parser.parse_args()
    report, default_output = run()
    output_path = args.output or default_output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
