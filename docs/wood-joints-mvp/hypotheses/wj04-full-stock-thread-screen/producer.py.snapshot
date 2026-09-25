"""Screen WJ-04 full-stock member thread-bearing fractions from archived inputs.

This is a bounded dimensional check, not a capacity calculation or a delivered
bolt fit result. It treats the recorded minimum smooth-body length as a screen
boundary and keeps the actual thread transition, nut fit, and NDS diameter
decision open.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_RELATIVE = Path(
    "docs/wood-joints-mvp/hypotheses/wj16-full-stock-mechanics-inputs"
)
INPUT_REPORT_RELATIVE = ARCHIVE_RELATIVE / "mechanics-inputs.json"
MANIFEST_RELATIVE = ARCHIVE_RELATIVE / "sha256.json"
EXECUTION_RELATIVE = ARCHIVE_RELATIVE / "execution.json"
OUTPUT_RELATIVE = Path(
    "docs/wood-joints-mvp/hypotheses/wj04-full-stock-thread-screen/thread-screen.json"
)
SCHEMA = "wood_joint_wj04_full_stock_thread_bearing_screen/v1"

# This binds the analysis to the already reviewed eight-axis mechanics input.
MECHANICS_INPUTS_SHA256 = (
    "f21e99f55da92ea60c950eecc6707fe98ca5df47f4d019f344c16fa06b52caf9"
)
EXPECTED_SOURCE_INVENTORY_SHA256 = (
    "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78"
)
EXPECTED_COMPOSITION_SHA256 = (
    "c0bc37fdbc364deafcbc86dc04e710d2f5b6809436e560717a97593951f8ebcb"
)
EXPECTED_STATIC_DIAGNOSTIC_SHA256 = (
    "2133e1e329e1f868af6faa1ee27d7093d7c16ed9708bc75ea05c90a4dbdefb43"
)

WJ16_TRIAL_ID = "wj16-wj12-plus-left-service-four-duty-v1"
RIGHT_TRIAL_ID = "upper_g7_clearance_n86p9_reversed_rail_hypothesis"
WOOD_LAYER_TOLERANCE_MM = 0.5
THREAD_BEARING_LIMIT = 0.25
EXPECTED_LB_MM = 127.0
EXPECTED_LG_MM = 133.35
EXPECTED_WASHER_THICKNESS_RANGE_MM = (1.2954, 2.032)

CLEAT_LOWER = "wj04_lower_full_stock_cleat"
CLEAT_UPPER = "wj04_upper_g7_crosscut_full_stock_cleat"
EXPECTED_RECEIVERS_BY_STACK = {
    "lower_rail_1": (CLEAT_LOWER, "base_rail_service_lower_right"),
    "lower_rail_2": (CLEAT_LOWER, "base_rail_service_lower_right"),
    "lower_principal_1": (CLEAT_LOWER, "base_principal_center_right"),
    "lower_principal_2": (CLEAT_LOWER, "base_principal_center_right"),
    "upper_rail_1": ("base_rail_service_upper_right", CLEAT_UPPER),
    "upper_rail_2": ("base_rail_service_upper_right", CLEAT_UPPER),
    "upper_principal_1": (CLEAT_UPPER, "base_principal_center_right"),
    "upper_principal_2": (CLEAT_UPPER, "base_principal_center_right"),
}
EXPECTED_LAYER_THICKNESSES_MM = {
    CLEAT_LOWER: 88.9,
    CLEAT_UPPER: 88.9,
    "base_rail_service_lower_right": 38.1,
    "base_rail_service_upper_right": 38.1,
    "base_principal_center_right": 38.1,
}

SOURCE_CORRECTION_NOTE = "docs/wood-joints-mvp/bolt-dimension-source-correction.md"
ASME_SOURCE_URL = (
    "https://www.asme.org/codes-standards/find-codes-standards/"
    "b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-"
    "lobed-head-lag-screws"
)
AWC_NDS_2024_CHAPTER_12_URL = (
    "https://awc.org/wp-content/uploads/2026/08/"
    "AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf"
)
AWC_NDS_2024_CHAPTER_12_SHA256 = (
    "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
)
ASME_B18_2_1_2012_PDF_SHA256 = (
    "4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return value


def load_archived_mechanics_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the immutable WJ16-derived report after checking archive pins."""
    manifest_path = ROOT / MANIFEST_RELATIVE
    manifest = _read_json(manifest_path)
    if manifest.get("mechanics-inputs.json") != MECHANICS_INPUTS_SHA256:
        raise ValueError("archived mechanics-input manifest pin changed")
    report_path = ROOT / INPUT_REPORT_RELATIVE
    observed_report_hash = _sha256(report_path)
    if observed_report_hash != MECHANICS_INPUTS_SHA256:
        raise ValueError("archived mechanics-input report hash changed")

    for filename, expected_hash in manifest.items():
        archive_path = ROOT / ARCHIVE_RELATIVE / filename
        if not archive_path.is_file() or _sha256(archive_path) != expected_hash:
            raise ValueError(f"archived input hash differs from manifest: {filename}")
    execution = _read_json(ROOT / EXECUTION_RELATIVE)
    expected_archives = {
        "wj16_composition": (
            "docs/wood-joints-mvp/hypotheses/wj16-integrated-static/composition.json",
            EXPECTED_COMPOSITION_SHA256,
        ),
        "wj16_static_diagnostic": (
            "docs/wood-joints-mvp/hypotheses/wj16-integrated-static/diagnostic.json",
            EXPECTED_STATIC_DIAGNOSTIC_SHA256,
        ),
    }
    input_archives = execution.get("input_archives", {})
    if set(input_archives) != set(expected_archives):
        raise ValueError("mechanics-input execution archive identities changed")
    for archive_id, (relative_path, expected_hash) in expected_archives.items():
        record = input_archives[archive_id]
        if (
            record.get("path") != relative_path
            or record.get("sha256") != expected_hash
            or _sha256(ROOT / relative_path) != expected_hash
        ):
            raise ValueError(f"archived WJ16 {archive_id} input changed")

    document = _read_json(report_path)
    if document.get("composition", {}).get("source_inventory_sha256") != (
        EXPECTED_SOURCE_INVENTORY_SHA256
    ) or _sha256(ROOT / "docs/wood-joints-mvp/source-inventory.json") != (
        EXPECTED_SOURCE_INVENTORY_SHA256
    ):
        raise ValueError("mechanics input is not bound to the pinned source inventory")
    return document, {
        "mechanics_inputs_sha256": observed_report_hash,
        "archive_manifest_sha256": _sha256(manifest_path),
        "execution_sha256": _sha256(ROOT / EXECUTION_RELATIVE),
        "execution": execution,
    }


def _validate_mechanics_input(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("schema") != "wood_joint_wj04_full_stock_mechanics_contract/v1":
        raise ValueError("unexpected archived WJ04 mechanics-input schema")
    if document.get("status") != "bounded_mechanics_inputs_only":
        raise ValueError("WJ04 input must remain an unaccepted bounded report")
    composition = document.get("composition", {})
    if (
        composition.get("trial_id") != WJ16_TRIAL_ID
        or composition.get("right_rail_family_trial_id") != RIGHT_TRIAL_ID
        or composition.get("source_inventory_sha256")
        != EXPECTED_SOURCE_INVENTORY_SHA256
    ):
        raise ValueError("archived WJ04 composition identity changed")
    if document.get("physical_inventory", {}).get("ordinary_physical_bolts") != 8:
        raise ValueError("WJ04 thread screen requires the exact eight-bolt input")

    rows = document.get("physical_bolts")
    expected_ids = {
        f"wj04_g7/{RIGHT_TRIAL_ID}/{stack_id}"
        for stack_id in EXPECTED_RECEIVERS_BY_STACK
    }
    if not isinstance(rows, list) or {row.get("physical_bolt_id") for row in rows} != expected_ids:
        raise ValueError("WJ04 input physical bolt IDs differ from eight pinned axes")
    if len(rows) != len(expected_ids):
        raise ValueError("WJ04 input has duplicate physical bolt IDs")

    by_stack = {row["stack_spec_id"]: row for row in rows}
    if set(by_stack) != set(EXPECTED_RECEIVERS_BY_STACK):
        raise ValueError("WJ04 stack spec identities changed")
    for stack_id, expected_receivers in EXPECTED_RECEIVERS_BY_STACK.items():
        row = by_stack[stack_id]
        receiver_rows = row.get("receivers_head_to_nut", ())
        if tuple(receiver.get("member_id") for receiver in receiver_rows) != expected_receivers:
            raise ValueError(f"{stack_id} ordered member receivers changed")
        for receiver in receiver_rows:
            expected_thickness = EXPECTED_LAYER_THICKNESSES_MM[receiver["member_id"]]
            if not math.isclose(
                float(receiver.get("wood_thickness_mm", math.nan)),
                expected_thickness,
                abs_tol=1e-9,
            ):
                raise ValueError(f"{stack_id} nominal member thickness changed")
        if not math.isclose(float(row.get("wood_grip_mm", math.nan)), 127.0, abs_tol=1e-9):
            raise ValueError(f"{stack_id} nominal ordered wood grip changed")

        hardware = row.get("hardware", {})
        bolt = hardware.get("bolt", {})
        washer = hardware.get("washers", {})
        if (
            bolt.get("candidate_id") != "kl_jack_25c600hcs5z"
            or bolt.get("sku") != "25C600HCS5Z"
            or bolt.get("thread") != "1/4-20 UNC"
            or bolt.get("dimensional_standard") != "ASME B18.2.1"
            or not math.isclose(
                float(bolt.get("minimum_smooth_body_Lb_mm", math.nan)),
                EXPECTED_LB_MM,
                abs_tol=1e-9,
            )
            or not math.isclose(
                float(bolt.get("maximum_grip_gage_Lg_mm", math.nan)),
                EXPECTED_LG_MM,
                abs_tol=1e-9,
            )
            or not math.isclose(
                float(bolt.get("nominal_length_mm", math.nan)), 152.4, abs_tol=1e-9
            )
            or washer.get("quantity") != 2
        ):
            raise ValueError(f"{stack_id} bolt or washer dimensional basis changed")
        washer_range = tuple(float(value) for value in washer.get("thickness_range_mm", ()))
        bolt_head_range = tuple(
            float(value)
            for value in bolt.get("head_side_washer_thickness_range_mm", ())
        )
        if (
            washer_range != EXPECTED_WASHER_THICKNESS_RANGE_MM
            or bolt_head_range != EXPECTED_WASHER_THICKNESS_RANGE_MM
        ):
            raise ValueError(f"{stack_id} washer catalog thickness bounds changed")
    return [by_stack[name] for name in sorted(by_stack)]


def _layer_thickness_corners(nominal_layers: tuple[float, ...]) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(corner)
        for corner in itertools.product(
            *(
                (thickness - WOOD_LAYER_TOLERANCE_MM, thickness + WOOD_LAYER_TOLERANCE_MM)
                for thickness in nominal_layers
            )
        )
    )


def _screen_stack(row: dict[str, Any]) -> dict[str, Any]:
    stack_id = row["stack_spec_id"]
    receivers = row["receivers_head_to_nut"]
    nominal_layers = tuple(float(receiver["wood_thickness_mm"]) for receiver in receivers)
    washer_min, washer_max = EXPECTED_WASHER_THICKNESS_RANGE_MM
    corner_results: list[dict[str, Any]] = []
    member_maxima = {
        receiver["member_id"]: {
            "max_fraction": -1.0,
            "max_thread_bearing_length_mm": 0.0,
            "governing_corner_index": None,
        }
        for receiver in receivers
    }
    index = 0
    for index, (head_washer, nut_washer, layer_corner) in enumerate(
        itertools.product(
            (washer_min, washer_max),
            (washer_min, washer_max),
            _layer_thickness_corners(nominal_layers),
        ),
        start=1,
    ):
        axial_station = head_washer
        member_results = []
        for receiver, thickness in zip(receivers, layer_corner, strict=True):
            member_id = receiver["member_id"]
            start = axial_station
            end = start + thickness
            threaded_length = min(
                thickness,
                max(0.0, end - max(start, EXPECTED_LB_MM)),
            )
            fraction = threaded_length / thickness
            within_limit = fraction <= THREAD_BEARING_LIMIT + 1e-12
            member_results.append(
                {
                    "member_id": member_id,
                    "nominal_thickness_mm": float(receiver["wood_thickness_mm"]),
                    "corner_thickness_mm": thickness,
                    "axial_start_from_underhead_mm": start,
                    "axial_end_from_underhead_mm": end,
                    "bearing_length_after_Lb_boundary_mm": threaded_length,
                    "fraction_after_Lb_boundary": fraction,
                    "within_recorded_one_quarter_limit_at_Lb_boundary": within_limit,
                }
            )
            maximum = member_maxima[member_id]
            if fraction > maximum["max_fraction"]:
                maximum.update(
                    {
                        "max_fraction": fraction,
                        "max_thread_bearing_length_mm": threaded_length,
                        "governing_corner_index": index,
                    }
                )
            axial_station = end
        corner_results.append(
            {
                "corner_index": index,
                "head_washer_thickness_mm": head_washer,
                "nut_washer_thickness_mm": nut_washer,
                "wood_layer_thicknesses_head_to_nut_mm": list(layer_corner),
                "receiving_member_results": member_results,
            }
        )

    if len(corner_results) != 16:
        raise ValueError(f"{stack_id} must evaluate all 16 independent input corners")
    members = []
    for receiver in receivers:
        member_id = receiver["member_id"]
        maximum = member_maxima[member_id]
        maximum_fraction = float(maximum["max_fraction"])
        members.append(
            {
                "member_id": member_id,
                "nominal_thickness_mm": float(receiver["wood_thickness_mm"]),
                "maximum_fraction_after_Lb_boundary": maximum_fraction,
                "maximum_bearing_length_after_Lb_boundary_mm": float(
                    maximum["max_thread_bearing_length_mm"]
                ),
                "governing_corner_index": maximum["governing_corner_index"],
                "all_corner_fractions_within_recorded_limit_at_Lb_boundary": (
                    maximum_fraction <= THREAD_BEARING_LIMIT + 1e-12
                ),
            }
        )
    return {
        "physical_bolt_id": row["physical_bolt_id"],
        "stack_spec_id": stack_id,
        "station_id": row["station_id"],
        "interface_id": row["interface_id"],
        "ordered_receivers_head_to_nut": [
            {
                "member_id": receiver["member_id"],
                "nominal_thickness_mm": float(receiver["wood_thickness_mm"]),
            }
            for receiver in receivers
        ],
        "wood_layer_corner_count": len(_layer_thickness_corners(nominal_layers)),
        "independent_washer_and_layer_corner_count": len(corner_results),
        "member_screens": members,
        "all_members_all_corners_within_recorded_limit_at_Lb_boundary": all(
            member["all_corner_fractions_within_recorded_limit_at_Lb_boundary"]
            for member in members
        ),
        "corner_results": corner_results,
    }


def build_thread_screen_report() -> dict[str, Any]:
    """Build a source-bound thread-bearing fraction report from the pinned archive."""
    document, archive_evidence = load_archived_mechanics_inputs()
    input_rows = _validate_mechanics_input(document)
    stacks = [_screen_stack(row) for row in input_rows]
    if len(stacks) != 8:
        raise ValueError("thread-bearing screen must cover exactly eight physical bolts")
    return {
        "schema": SCHEMA,
        "status": "bounded_thread_bearing_geometry_screen_only",
        "claim_boundary": (
            "This report applies the recorded one-quarter threaded-bearing fraction "
            "screen to eight archived WJ-04 full-stock bolt stacks at independent "
            "wood-layer and washer dimensional corners. It establishes no capacity, "
            "delivered bolt fit, full-shank coverage, or NDS diameter selection."
        ),
        "source": {
            "mechanics_inputs_path": INPUT_REPORT_RELATIVE.as_posix(),
            "mechanics_inputs_sha256": archive_evidence["mechanics_inputs_sha256"],
            "archive_manifest_path": MANIFEST_RELATIVE.as_posix(),
            "archive_manifest_sha256": archive_evidence["archive_manifest_sha256"],
            "execution_path": EXECUTION_RELATIVE.as_posix(),
            "execution_sha256": archive_evidence["execution_sha256"],
            "wj16_composition_path": archive_evidence["execution"]["input_archives"][
                "wj16_composition"
            ]["path"],
            "wj16_composition_sha256": EXPECTED_COMPOSITION_SHA256,
            "wj16_static_diagnostic_path": archive_evidence["execution"][
                "input_archives"
            ]["wj16_static_diagnostic"]["path"],
            "wj16_static_diagnostic_sha256": EXPECTED_STATIC_DIAGNOSTIC_SHA256,
            "source_inventory_sha256": EXPECTED_SOURCE_INVENTORY_SHA256,
            "source_correction_note": SOURCE_CORRECTION_NOTE,
            "source_correction_note_sha256": _sha256(ROOT / SOURCE_CORRECTION_NOTE),
            "asme_b18_2_1_2012_pdf_sha256": ASME_B18_2_1_2012_PDF_SHA256,
            "nds_2024_chapter_12_pdf_sha256": AWC_NDS_2024_CHAPTER_12_SHA256,
            "producer_sha256": _sha256(Path(__file__)),
        },
        "method": {
            "receiving_member_layer_tolerance_mm_each_side": WOOD_LAYER_TOLERANCE_MM,
            "layer_tolerance_status": (
                "independent diagnostic corner input; not a stock or cut acceptance tolerance"
            ),
            "washer_thickness_range_mm": list(EXPECTED_WASHER_THICKNESS_RANGE_MM),
            "head_and_nut_washers_varied_independently": True,
            "wood_layers_varied_independently": True,
            "corner_count_per_bolt": 16,
            "smooth_body_screen_boundary_Lb_mm_from_underhead": EXPECTED_LB_MM,
            "Lg_mm_recorded_but_not_used_as_thread_boundary": EXPECTED_LG_MM,
            "Lg_semantics": "maximum grip-gaging inspection bound; not a thread-start location",
            "fraction_formula": (
                "For each receiver layer, overlap its head-to-nut axial interval with "
                "the interval beginning at the recorded Lb boundary; divide that length "
                "by the layer's corner thickness."
            ),
            "thread_boundary_assumption": (
                "The geometric split is placed at minimum smooth-body Lb=127 mm only "
                "for this dimensional screen. Actual delivered last-thread-scratch, "
                "thread runout, and first full-form thread locations are not measured; "
                "do not read this as an actual thread-transition guarantee."
            ),
            "threshold_fraction": THREAD_BEARING_LIMIT,
            "threshold_source": {
                "standard": "ANSI/AWC NDS-2024 §12.3.7.2",
                "source_url": AWC_NDS_2024_CHAPTER_12_URL,
                "local_pdf_sha256": AWC_NDS_2024_CHAPTER_12_SHA256,
                "application": (
                    "The one-quarter rule is only the member-specific geometry "
                    "condition for the full-body diameter option in NDS lateral-yield "
                    "calculations; it is not a resistance result. If the condition is "
                    "not met, NDS permits thread-root diameter or detailed analysis."
                ),
            },
            "bolt_dimension_basis": {
                "standard": "ASME B18.2.1-2012 Table 12, printed page 21",
                "source_url": ASME_SOURCE_URL,
                "local_pdf_sha256": ASME_B18_2_1_2012_PDF_SHA256,
                "correction_note": SOURCE_CORRECTION_NOTE,
                "lb_min_mm": EXPECTED_LB_MM,
                "lg_max_mm": EXPECTED_LG_MM,
                "source_attribution_note": (
                    "Use the ASME table ordering and derivation in the correction note. "
                    "The Nickel Systems partial-thread table prints the six-inch 1/4-in "
                    "cell as 5.25 / 5.00 under Lb min / Lg max; that reversed labeling "
                    "is not used as the dimension source here."
                ),
            },
        },
        "hardware_and_fit_status": {
            "bolt_candidate_id": "kl_jack_25c600hcs5z",
            "nominal_length_mm": 152.4,
            "actual_delivered_thread_transition_verified": False,
            "full_smooth_shank_through_every_wood_layer_proven": False,
            "nut_fit_or_functional_engagement_verified": False,
            "screen_uses_Lg_as_thread_boundary": False,
            "actual_NDS_full_body_diameter_exception_established": False,
            "capacity_established": False,
        },
        "physical_bolt_count": len(stacks),
        "member_screen_count": sum(len(stack["member_screens"]) for stack in stacks),
        "total_corner_evaluations": sum(
            stack["independent_washer_and_layer_corner_count"] for stack in stacks
        ),
        "total_member_corner_fractions": sum(
            stack["independent_washer_and_layer_corner_count"]
            * len(stack["member_screens"])
            for stack in stacks
        ),
        "all_evaluated_member_corners_within_recorded_limit_at_Lb_boundary": all(
            stack["all_members_all_corners_within_recorded_limit_at_Lb_boundary"]
            for stack in stacks
        ),
        "physical_bolts": stacks,
        "release": {
            "thread_screen_result": "conditional geometry screen only",
            "fastener_selected": False,
            "NDS_diameter_choice_released": False,
            "fit_or_installation_released": False,
            "capacity_established": False,
            "native_solve_run": False,
        },
    }


def write_report(output_path: Path | None = None) -> Path:
    """Write the deterministic JSON report and return its path."""
    destination = output_path or (ROOT / OUTPUT_RELATIVE)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_thread_screen_report(), indent=2, sort_keys=True) + "\n"
    )
    return destination


if __name__ == "__main__":
    print(write_report().relative_to(ROOT))
