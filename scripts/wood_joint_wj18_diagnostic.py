"""Full-scene static diagnostic for the retained WJ16 plus top-outer layout.

The report checks nominal geometry and source identity only. It does not
establish movement, installation access, capacity, fabrication, or acceptance.
"""

from __future__ import annotations

from typing import Any

from scripts import wood_joint_top_outer_integration as top_outer
from scripts import wood_joint_wj12_diagnostic as shared_diagnostic
from scripts import wood_joint_wj16_diagnostic as wj16_diagnostic
from scripts.wood_joint_wj18_compositor import (
    EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS,
    EXPECTED_CANDIDATE_AXIS_IDS,
    EXPECTED_CANDIDATE_PART_IDS,
    EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
    EXPECTED_RETAINED_LEGACY_CLIP_COUNT,
    EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT,
    EXPECTED_SOURCE_HOST_IDS,
    EXPECTED_TARGET_DUTY_IDS,
    LAYOUT_ID,
    PRODUCER_HASH_PATHS,
    TOP_AXIS_STATION_IDS,
    TRIAL_ID,
)

SCHEMA = "wood_joint_wj18_diagnostic/v1"

_family_producers = dict(wj16_diagnostic.WJ16_LAYOUT.family_producer_paths)
_family_producers["top_outer"] = top_outer.PRODUCER_HASH_PATHS[
    "top_outer_producer"
]
_extra_producers = dict(wj16_diagnostic.WJ16_LAYOUT.extra_producer_hash_paths)
for _label, _path in top_outer.PRODUCER_HASH_PATHS.items():
    if _label != "top_outer_producer":
        _extra_producers[f"top_outer_input/{_label}"] = _path
_station_ids = dict(
    wj16_diagnostic.WJ16_LAYOUT.expected_candidate_axis_station_ids
)
_station_ids.update(TOP_AXIS_STATION_IDS)

WJ18_LAYOUT = shared_diagnostic.DiagnosticLayout(
    layout_id=LAYOUT_ID,
    trial_id=TRIAL_ID,
    schema=SCHEMA,
    expected_target_duty_ids=EXPECTED_TARGET_DUTY_IDS,
    expected_source_host_ids=EXPECTED_SOURCE_HOST_IDS,
    expected_candidate_axis_ids=EXPECTED_CANDIDATE_AXIS_IDS,
    expected_candidate_part_ids=EXPECTED_CANDIDATE_PART_IDS,
    expected_candidate_installed_component_count=400,
    expected_replaced_source_axis_count=EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
    expected_retained_legacy_clip_count=EXPECTED_RETAINED_LEGACY_CLIP_COUNT,
    expected_retained_legacy_sds_axis_count=EXPECTED_RETAINED_LEGACY_SDS_AXIS_COUNT,
    expected_additional_overlay_axis_counts=tuple(
        sorted(EXPECTED_ADDITIONAL_OVERLAY_AXIS_COUNTS.items())
    ),
    family_producer_paths=tuple(sorted(_family_producers.items())),
    compositor_path=PRODUCER_HASH_PATHS["wj18_compositor"],
    diagnostic_path=PRODUCER_HASH_PATHS["wj18_diagnostic"],
    extra_producer_hash_paths=tuple(sorted(_extra_producers.items())),
    expected_candidate_axis_station_ids=tuple(sorted(_station_ids.items())),
)


def build_wj18_diagnostic_report(
    geometry: Any,
    *,
    tolerance_mm3: float = shared_diagnostic.HIT_TOLERANCE_MM3,
) -> dict[str, Any]:
    """Run the shared nominal scene checks against the exact WJ18 identity."""
    if getattr(geometry, "layout_id", None) != LAYOUT_ID:
        raise ValueError("diagnostic requires the fixed eighteen-duty WJ18 layout")
    if getattr(geometry, "trial_id", None) != TRIAL_ID:
        raise ValueError("diagnostic requires the fixed WJ18 trial identity")
    report = shared_diagnostic.build_diagnostic_report(
        geometry,
        tolerance_mm3=tolerance_mm3,
        layout=WJ18_LAYOUT,
    )
    report["schema"] = SCHEMA
    report["status"] = "source_bound_eighteen_duty_static_geometry_diagnostic"
    report["integration_contract"] = {
        "composition_checks": dict(geometry.composition_checks),
        "absorbed_source_overlay_ids": list(geometry.absorbed_source_overlay_ids),
        "top_rail_purchase_overlay_is_a_regular_shared_host": {
            "host_in_finished_hosts": "base_rail_top" in geometry.finished_hosts,
            "host_in_additional_overlays": "base_rail_top"
            in geometry.additional_finished_source_parts,
            "purchase_cut_count": len(
                geometry.purchased_panel_cutters_by_host.get("base_rail_top", {})
            ),
        },
        "remaining_bottom_rail_overlay_ids": sorted(
            geometry.additional_finished_source_parts
        ),
        "source_native_and_panel_purchase_cut_maps_are_separate": True,
        "all_release_and_acceptance_flags_false": True,
    }
    report["claim_boundary"]["candidate_layout_identity_is_not_acceptance"] = True
    report["claim_boundary"]["complete_cross_family_scene_is_not_acceptance"] = True
    report["release"] = {
        "candidate_accepted": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_accepted": False,
        "assembly_proven": False,
    }
    return report
