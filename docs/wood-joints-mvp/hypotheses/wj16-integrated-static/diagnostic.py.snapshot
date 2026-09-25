"""Source-bound static checks for the sixteen-duty left-service composition.

This diagnostic consumes an already composed WJ16 object. It reports nominal
intersection and receiver evidence; it does not establish continuous motion,
installation, capacity, fabrication readiness, or acceptance.
"""

from __future__ import annotations

from typing import Any

from scripts import wood_joint_wj12_diagnostic as shared_diagnostic
from scripts.wood_joint_wj16_compositor import (
    EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS,
    EXPECTED_CANDIDATE_AXIS_IDS,
    EXPECTED_CANDIDATE_PART_IDS,
    EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
    EXPECTED_RETAINED_LEGACY_CLIP_COUNT,
    EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT,
    EXPECTED_SOURCE_HOST_IDS,
    EXPECTED_TARGET_DUTY_IDS,
    LAYOUT_ID,
    LEFT_AXIS_STATION_IDS,
    PRODUCER_HASH_PATHS,
    TRIAL_ID,
)

SCHEMA = "wood_joint_wj16_diagnostic/v1"

WJ16_LAYOUT = shared_diagnostic.DiagnosticLayout(
    layout_id=LAYOUT_ID,
    trial_id=TRIAL_ID,
    schema=SCHEMA,
    expected_target_duty_ids=EXPECTED_TARGET_DUTY_IDS,
    expected_source_host_ids=EXPECTED_SOURCE_HOST_IDS,
    expected_candidate_axis_ids=EXPECTED_CANDIDATE_AXIS_IDS,
    expected_candidate_part_ids=EXPECTED_CANDIDATE_PART_IDS,
    expected_candidate_installed_component_count=360,
    expected_replaced_source_axis_count=EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
    expected_retained_legacy_clip_count=EXPECTED_RETAINED_LEGACY_CLIP_COUNT,
    expected_retained_legacy_sds_axis_count=EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT,
    expected_additional_overlay_axis_counts=tuple(
        sorted(EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS.items())
    ),
    family_producer_paths=tuple(
        sorted(
            {
                **dict(shared_diagnostic.WJ12_LAYOUT.family_producer_paths),
                "left_service": "scripts/wood_joint_left_rail_integration.py",
            }.items()
        )
    ),
    compositor_path=PRODUCER_HASH_PATHS["wj16_compositor"],
    diagnostic_path=PRODUCER_HASH_PATHS["wj16_diagnostic"],
    extra_producer_hash_paths=tuple(
        sorted(
            (name, path)
            for name, path in PRODUCER_HASH_PATHS.items()
            if name not in {"wj16_compositor", "wj16_diagnostic"}
        )
    ),
    expected_candidate_axis_station_ids=tuple(sorted(LEFT_AXIS_STATION_IDS.items())),
)


def build_wj16_diagnostic_report(
    geometry: Any,
    *,
    tolerance_mm3: float = shared_diagnostic.HIT_TOLERANCE_MM3,
) -> dict[str, Any]:
    """Run shared geometry screens against the fixed WJ16 identity contract."""
    if getattr(geometry, "layout_id", None) != LAYOUT_ID:
        raise ValueError("diagnostic requires the fixed sixteen-duty WJ16 layout")
    report = shared_diagnostic.build_diagnostic_report(
        geometry,
        tolerance_mm3=tolerance_mm3,
        layout=WJ16_LAYOUT,
    )
    report["schema"] = SCHEMA
    report["status"] = "source_bound_sixteen_duty_static_geometry_diagnostic"
    report["claim_boundary"]["candidate_layout_identity_is_not_acceptance"] = True
    report["release"] = {
        "candidate_accepted": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_accepted": False,
        "assembly_proven": False,
    }
    return report
