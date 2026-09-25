"""Full-scene static diagnostic for the provisional WJ24 composition.

The report checks exact source-bound identities, nominal positive-volume
intersections, fixed receivers, and the twelve preserved frame bolts. It does
not promote local contact/tool screens to acceptance or prove movement,
capacity, installation, fabrication, or release.
"""

from __future__ import annotations

from typing import Any

from scripts import wood_joint_bottom_center_integration as bottom_center
from scripts import wood_joint_bottom_outer_integration as bottom_outer
from scripts import wood_joint_top_center_integration as top_center
from scripts import wood_joint_wj12_diagnostic as shared_diagnostic
from scripts import wood_joint_wj18_diagnostic as wj18_diagnostic
from scripts.wood_joint_wj24_compositor import (
    BOTTOM_OUTER_AXIS_STATION_IDS,
    EXPECTED_CANDIDATE_AXIS_IDS,
    EXPECTED_CANDIDATE_AXIS_STATION_IDS,
    EXPECTED_CANDIDATE_PART_IDS,
    EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
    EXPECTED_SOURCE_HOST_IDS,
    EXPECTED_TARGET_DUTY_IDS,
    LAYOUT_ID,
    PRODUCER_HASH_PATHS,
    TRIAL_ID,
)

SCHEMA = "wood_joint_wj24_diagnostic/v1"

_family_producers = dict(wj18_diagnostic.WJ18_LAYOUT.family_producer_paths)
_family_producers.update(
    {
        "top_center": top_center.PRODUCER_HASH_PATHS["top_center_producer"],
        "bottom_outer": bottom_outer.PRODUCER_HASH_PATHS["bottom_outer_producer"],
        "bottom_center": bottom_center.PRODUCER_HASH_PATHS["bottom_center_producer"],
    }
)

_extra_producers = dict(wj18_diagnostic.WJ18_LAYOUT.extra_producer_hash_paths)
for _label, _path in PRODUCER_HASH_PATHS.items():
    _extra_producers[_label] = _path
for _family, _module in (
    ("top_center", top_center),
    ("bottom_outer", bottom_outer),
    ("bottom_center", bottom_center),
):
    for _label, _path in _module.PRODUCER_HASH_PATHS.items():
        _extra_producers[f"{_family}_input/{_label}"] = _path

_station_ids = dict(
    wj18_diagnostic.WJ18_LAYOUT.expected_candidate_axis_station_ids
)
_station_ids.update(top_center.TOP_AXIS_STATION_IDS)
_station_ids.update(BOTTOM_OUTER_AXIS_STATION_IDS)
_station_ids.update(bottom_center.BOTTOM_AXIS_STATION_IDS)
if _station_ids != EXPECTED_CANDIDATE_AXIS_STATION_IDS:
    raise RuntimeError("WJ24 diagnostic station bindings differ from the fixed compositor contract")

WJ24_LAYOUT = shared_diagnostic.DiagnosticLayout(
    layout_id=LAYOUT_ID,
    trial_id=TRIAL_ID,
    schema=SCHEMA,
    expected_target_duty_ids=EXPECTED_TARGET_DUTY_IDS,
    expected_source_host_ids=EXPECTED_SOURCE_HOST_IDS,
    expected_candidate_axis_ids=EXPECTED_CANDIDATE_AXIS_IDS,
    expected_candidate_part_ids=EXPECTED_CANDIDATE_PART_IDS,
    expected_candidate_installed_component_count=520,
    expected_replaced_source_axis_count=EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
    expected_retained_legacy_clip_count=0,
    expected_retained_legacy_sds_axis_count=0,
    expected_additional_overlay_axis_counts=(),
    family_producer_paths=tuple(sorted(_family_producers.items())),
    compositor_path=PRODUCER_HASH_PATHS["wj24_compositor"],
    diagnostic_path=PRODUCER_HASH_PATHS["wj24_diagnostic"],
    extra_producer_hash_paths=tuple(sorted(_extra_producers.items())),
    expected_candidate_axis_station_ids=tuple(sorted(_station_ids.items())),
)


def _resolve_empty_overlay_semantics(report: dict[str, Any], geometry: Any) -> None:
    """Treat the exact zero-overlay WJ24 contract as a vacuous pass.

    The shared diagnostic predates zero-overlay layouts and uses ``bool(rows)``
    for several overlay summaries. Preserve those raw values, then report the
    exact WJ24 meaning: no expected overlay hosts and no actual overlay maps.
    """
    raw = report["additional_source_purchase_overlays"]
    empty_contract = (
        not dict(WJ24_LAYOUT.expected_additional_overlay_axis_counts)
        and not geometry.additional_finished_source_parts
        and not geometry.additional_purchased_panel_cutters_by_host
        and raw["expected_host_count"] == 0
        and raw["overlay_host_ids"] == []
        and raw["cutter_map_host_ids"] == []
        and raw["host_ids_match_expected"] is True
    )
    if not empty_contract:
        return
    report["shared_helper_zero_overlay_raw_flags"] = {
        key: raw[key]
        for key in (
            "all_overlay_cutter_ids_match_fixed_axes",
            "all_purchase_cutters_intersect_source_finished_members",
            "all_overlays_replay_from_source_finished_members_and_cuts",
            "all_compositor_reconstruction_evidence_matches",
        )
    }
    for key in (
        "all_overlay_cutter_ids_match_fixed_axes",
        "all_purchase_cutters_intersect_source_finished_members",
        "all_overlays_replay_from_source_finished_members_and_cuts",
        "all_compositor_reconstruction_evidence_matches",
    ):
        raw[key] = True
    count_row = report["counts_and_ids"]["additional_source_purchase_overlays"]
    count_row["all_overlay_and_cutter_ids_match_inventory"] = True
    report["diagnostic_gates"]["untouched_source_receiver_overlays_reconcile"] = True
    report["zero_overlay_contract_is_vacuously_satisfied"] = True


def build_wj24_diagnostic_report(
    geometry: Any,
    *,
    tolerance_mm3: float = shared_diagnostic.HIT_TOLERANCE_MM3,
) -> dict[str, Any]:
    """Run fixed-layout full-scene checks without treating them as acceptance."""
    if getattr(geometry, "layout_id", None) != LAYOUT_ID:
        raise ValueError("diagnostic requires the fixed twenty-four-duty WJ24 layout")
    if getattr(geometry, "trial_id", None) != TRIAL_ID:
        raise ValueError("diagnostic requires the fixed WJ24 trial identity")
    report = shared_diagnostic.build_diagnostic_report(
        geometry,
        tolerance_mm3=tolerance_mm3,
        layout=WJ24_LAYOUT,
    )
    _resolve_empty_overlay_semantics(report, geometry)
    report["schema"] = SCHEMA
    report["status"] = "source_bound_twenty_four_duty_static_geometry_diagnostic"
    report["integration_contract"] = {
        "composition_checks": dict(geometry.composition_checks),
        "source_hosts_rebuilt_from_raw_and_complete_cut_union": len(
            geometry.finished_hosts
        )
        == 16,
        "all_144_source_sds_axes_removed": len(geometry.replaced_source_axis_ids)
        == EXPECTED_REPLACED_SOURCE_AXIS_COUNT,
        "all_104_candidate_axes_and_520_roles_preserved": len(
            geometry.candidate_bores
        )
        == 104
        and sum(map(len, geometry.candidate_installed_hardware.values())) == 520,
        "all_28_candidate_parts_preserved": len(geometry.finished_candidate_parts) == 28,
        "four_backer_fixed_panel_receiver_cuts_preserved": sum(
            len(cuts)
            for cuts in geometry.purchased_panel_cutters_by_candidate_part.values()
        )
        == 4,
        "absorbed_source_overlay_ids": list(geometry.absorbed_source_overlay_ids),
        "remaining_source_only_overlays": sorted(
            geometry.additional_finished_source_parts
        ),
        "all_66_fixed_axes_and_twelve_frame_bolts_retained": len(
            geometry.fixed_axes
        )
        == 66
        and len(geometry.frame_bolt_records) == 12
        and len(geometry.frame_bolt_shapes) == 72,
        "local_family_access_and_contact_findings_preserved": True,
        "tool_and_contact_screen_is_not_acceptance": True,
        "complete_joint_acceptance": False,
        "capacity_established": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    report["local_family_diagnostics"] = dict(geometry.local_delta_diagnostics)
    report["claim_boundary"].update(
        {
            "individual_family_tool_and_contact_screens_are_retained_as_conditional_findings": True,
            "raw_tool_envelope_overlaps_are_not_discarded_or_called_clear": True,
            "complete_access_or_assembly_sequence_established": False,
            "contact_support_or_capacity_established": False,
        }
    )
    report["release"] = {
        "candidate_accepted": False,
        "source_cutting_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_accepted": False,
        "assembly_proven": False,
    }
    return report
