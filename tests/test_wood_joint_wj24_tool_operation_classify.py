"""Focused tests for diagnostic-only WJ24 hit classification."""

from __future__ import annotations

import copy

from scripts.wood_joint_wj24_tool_operation_classify import (
    TEMPORAL_PREFIX,
    classify_wj24_tool_operation_report,
)


def _raw_report() -> dict:
    return {
        "schema": "wood_joint_wj24_tool_operation_probe/v1",
        "layout_id": "wj24-twenty-four-duty-integrated-static-v1",
        "trial_id": "wj24-wj18-plus-top-center-bottom-pairs-v1",
        "input_artifact_sha256": "source-input-sha",
        "method_contract": {
            "shaft_withdrawal": "all moving roles use one conservative oriented bounding sweep"
        },
        "axes": [
            {
                "axis_id": "axis_a",
                "operations": {
                    "installed_counterhold": {
                        "status": "sampled_seated_envelopes_only",
                        "head_pose_collision_screens": {
                            "15": {
                                "external_envelope_clear": False,
                                "external_envelope_hits_mm3": {
                                    "head_seated_pose": {
                                        "wood/beam": 0.25,
                                        f"{TEMPORAL_PREFIX}frame_bolt_1/head_tool": 1.5,
                                        "protected/future_family/proxy": 2.0,
                                    }
                                },
                                "physical_access_established": False,
                            }
                        },
                    },
                    "shaft_withdrawal": {
                        "status": "screened_continuous_translation_enclosure",
                        "method": "continuous translation with per-role enclosures",
                        "shaft_sweep_method": "exact_coaxial_cylinder_translation_sweep",
                        "head_and_washer_sweep_method": (
                            "separate conservative oriented-box translation enclosures"
                        ),
                        "terminal_clearance_margin_mm": 0.0,
                        "preconditions": [
                            "nut and nut_washer are fully unthreaded",
                            "nut and nut_washer are captured and absent from the moving phase",
                        ],
                        "sweep_collision_screen": {
                            "external_envelope_clear": True,
                            "external_envelope_hits_mm3": {},
                            "physical_removal_established": False,
                        },
                    },
                    "backer_operation": {
                        "status": "scope_not_modeled",
                        "required_state": "open frame and defined support transfer",
                    },
                },
            }
        ],
    }


def test_classification_preserves_raw_hits_and_splits_temporal_proxies() -> None:
    raw = _raw_report()
    original = copy.deepcopy(raw)
    raw_sha = "a" * 64

    classified = classify_wj24_tool_operation_report(raw, raw_report_sha256=raw_sha)

    assert raw == original
    assert classified["input_artifact_sha256"] == raw["input_artifact_sha256"]
    assert classified["classification_provenance"]["raw_report_sha256"] == raw_sha
    assert (
        classified["axes"][0]["operations"]["installed_counterhold"][
            "head_pose_collision_screens"
        ]["15"]["external_envelope_hits_mm3"]
        == original["axes"][0]["operations"]["installed_counterhold"][
            "head_pose_collision_screens"
        ]["15"]["external_envelope_hits_mm3"]
    )

    collision = classified["axes"][0]["operations"]["installed_counterhold"][
        "head_pose_collision_screens"
    ]["15"]
    hits = collision["hit_classification"]
    assert collision["external_envelope_clear"] is False
    assert hits["raw_external_envelope_clear"] is False
    assert hits["retained_geometry_envelope_hits"] == {
        "head_seated_pose": {
            "wood/beam": 0.25,
            "protected/future_family/proxy": 2.0,
        }
    }
    assert hits["temporal_operation_envelope_overlaps"] == {
        "head_seated_pose": {f"{TEMPORAL_PREFIX}frame_bolt_1/head_tool": 1.5}
    }
    assert hits["unknown_protected_families_retained"] == ["future_family"]
    assert hits["raw_hit_count"] == 3
    assert hits["retained_geometry_envelope_hit_count"] == 2
    assert hits["temporal_operation_envelope_overlap_count"] == 1
    assert hits["dropped_hit_count"] == 0
    assert hits["physical_access_established"] is False
    assert hits["operation_route_established"] is False

    operations = classified["axes"][0]["operations"]
    assert (
        operations["installed_counterhold"]["hit_classification_summary"][
            "retained_geometry_envelope_clear"
        ]
        is False
    )
    assert (
        operations["shaft_withdrawal"]["hit_classification_summary"][
            "temporal_operation_envelope_overlap_present"
        ]
        is False
    )
    assert (
        operations["backer_operation"]["hit_classification_summary"]["status"]
        == "scope_not_modeled"
    )
    assert (
        operations["backer_operation"]["hit_classification_summary"][
            "retained_geometry_envelope_clear"
        ]
        is None
    )

    inventory = classified["classification_inventory"]
    assert inventory["raw_hit_count"] == 3
    assert inventory["retained_geometry_envelope_hit_count"] == 2
    assert inventory["temporal_operation_envelope_overlap_count"] == 1
    assert inventory["dropped_hit_count"] == 0
    assert inventory["classification_changes_acceptance_or_access"] is False
    assert inventory["all_104_axis_rows_present"] is False


def test_method_refinement_summarizes_per_axis_method_without_rewriting_raw() -> None:
    raw = _raw_report()
    original_method_contract = copy.deepcopy(raw["method_contract"])

    classified = classify_wj24_tool_operation_report(raw)

    assert classified["method_contract"] == original_method_contract
    refinement = classified["method_refinement"]
    assert refinement["raw_method_contract_preserved_verbatim"] is True
    assert (
        refinement["raw_top_level_shaft_method_text"]
        == original_method_contract["shaft_withdrawal"]
    )
    summary = refinement["per_axis_method_summary"]
    assert summary["withdrawal_method_counts"] == {
        "continuous translation with per-role enclosures": 1
    }
    assert summary["shaft_sweep_method_counts"] == {
        "exact_coaxial_cylinder_translation_sweep": 1
    }
    assert summary["head_and_washer_sweep_method_counts"] == {
        "separate conservative oriented-box translation enclosures": 1
    }
    assert summary["terminal_clearance_margin_mm_counts"] == {"0.0": 1}
    assert summary["exact_coaxial_cylinder_shaft_sweep_count"] == 1
    assert summary["conservative_oriented_box_head_and_washer_sweep_count"] == 1
    assert refinement["classification_changes_acceptance_or_access"] is False
