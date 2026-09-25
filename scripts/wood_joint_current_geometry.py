"""Lazily rebuild the owner-reviewed WJ24 geometry input.

The module intentionally imports no CAD modules at import time. Call
``build_current_geometry`` with the historical composed WJ24 object to reuse
the parent's in-memory baseline, or omit it to run the recorded source-pinned
composition sequence first. This only constructs geometry and its cumulative
revision report; it does not run mechanics or establish acceptance.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
BASE_COMPOSITION_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json"
ORIENTATION_AUDIT_PATH = ROOT / (
    "docs/wood-joints-mvp/hypotheses/consolidated-blocks-two-inner-bolts-2026-09-24/"
    "orientation-audit.json"
)
OUTER_LINKS_REPORT_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/outer-links-removed-2026-09-24"
OUTER_LINKS_REPORT_PATH = OUTER_LINKS_REPORT_DIR / "revision.json"
OUTER_LINKS_VERIFICATION_PATH = OUTER_LINKS_REPORT_DIR / "verification.json"

# These operation outputs bind the saved outer-links report to the replayed
# geometry. Viewer-only annotations such as summary wording and findings are
# intentionally excluded from the comparison.
_OUTER_LINKS_GEOMETRY_FIELDS = (
    "schema",
    "status",
    "revision_id",
    "input_revision_id",
    "scope",
    "removed_candidate_part_ids",
    "removed_candidate_axis_ids",
    "removed_display_solid_ids",
    "moved_candidate_axis_ids",
    "moved_panel_axes",
    "baseline_display_translations_mm",
    "changed_display_solid_ids",
    "preserved_ids",
    "affected_receiver_ids",
    "host_replay",
    "candidate_part_replay",
    "preserved_counts",
    "checks",
)


def _verify_recovery_inputs() -> dict[str, Any]:
    """Keep a from-scratch reconstruction on the archived WJ24 inputs."""
    reference = json.loads(BASE_COMPOSITION_PATH.read_text())
    mismatches = []
    for relative_path, expected_sha256 in reference["source_input_hashes_sha256"].items():
        path = ROOT / relative_path
        actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha256 != expected_sha256:
            mismatches.append(relative_path)
    if mismatches:
        joined = ", ".join(sorted(mismatches))
        raise RuntimeError(
            "cannot reconstruct the historical WJ24 base: archived source inputs changed: "
            f"{joined}"
        )
    return reference


def _compose_baseline_geometry() -> Any:
    """Replay the exact parent-session baseline recovery sequence lazily."""
    reference = _verify_recovery_inputs()

    # Keep imports inside the callable: users with an existing parent-session
    # geometry should be able to import this module without loading CadQuery.
    from scripts import wood_joint_bottom_center_integration as bottom_center
    from scripts import wood_joint_bottom_outer_integration as bottom_outer
    from scripts import wood_joint_left_rail_integration as left
    from scripts import wood_joint_right_rail_integration as right
    from scripts import wood_joint_top_center_integration as top_center
    from scripts import wood_joint_top_outer_integration as top_outer
    from scripts import wood_joint_wj12_compositor as wj12
    from scripts import wood_joint_wj16_compositor as wj16
    from scripts import wood_joint_wj18_compositor as wj18
    from scripts import wood_joint_wj24_compositor as wj24

    inventory = json.loads(wj12.WJ03_SOURCE_INVENTORY.read_text())
    hosts = wj12.source_host_ids(inventory)
    right_geometry = right.materialize_right_rail_geometry()
    preflight = wj12.preflight_source_cutter_map(
        right_geometry.source,
        right.source_native_cutters_by_host(right_geometry.source, hosts),
        inventory,
    )
    compact = wj12.compact_access.materialize_geometry()
    center = wj12.center_x190_probe.materialize_geometry()
    g12 = wj12.compose_trial_geometry(
        preflight,
        compact,
        right_geometry,
        center,
        purchased_panel_cutters_by_host=right.candidate_panel_purchase_cutters_by_host(
            right_geometry.source, inventory, hosts
        ),
    )
    left_geometry = left.materialize_left_service_geometry(right_geometry)
    g16 = wj16.compose_wj16_geometry(g12, left_geometry)
    top_outer_geometry = top_outer.build_top_outer_integration(g16)
    g18 = wj18.compose_wj18_geometry(g16, top_outer_geometry)
    top_center_geometry = top_center.build_top_center_integration(g18)
    bottom_outer_geometry = bottom_outer.build_bottom_outer_integration(
        g18, context_variant="wj18"
    )
    bottom_center_geometry = bottom_center.build_bottom_center_integration(g18)
    baseline = wj24.compose_wj24_geometry(
        g18, top_center_geometry, bottom_outer_geometry, bottom_center_geometry
    )
    if wj24.composition_report(baseline) != reference:
        raise RuntimeError(
            "reconstructed historical WJ24 base does not match its archived composition report"
        )
    return baseline


def _load_revision_helpers() -> Any:
    """Load the incremental geometry builders only when a build is requested."""
    from types import SimpleNamespace

    from scripts import wood_joint_wj24_2x6_outer_blocks as outer_2x6
    from scripts import wood_joint_wj24_bolt_orientation as bolt_orientation
    from scripts import wood_joint_wj24_bottom_support_above_tnuts as above_tnuts
    from scripts import wood_joint_wj24_bottom_support_up_one_row as support_up
    from scripts import wood_joint_wj24_center_header_blocks as center_header
    from scripts import wood_joint_wj24_common_blocks as common_blocks
    from scripts import wood_joint_wj24_inner_frame_blocks as inner_frame
    from scripts import wood_joint_wj24_kicker_posts_outside_tnuts as kicker_posts
    from scripts import wood_joint_wj24_led_clearance as led_clearance
    from scripts import wood_joint_wj24_lower_blocks_below as lower_blocks
    from scripts import wood_joint_wj24_remove_outer_links as remove_outer_links
    from scripts import wood_joint_wj24_second_inner_bolts as second_inner_bolts

    return SimpleNamespace(
        above_tnuts=above_tnuts,
        bolt_orientation=bolt_orientation,
        center_header=center_header,
        common_blocks=common_blocks,
        inner_frame=inner_frame,
        kicker_posts=kicker_posts,
        led_clearance=led_clearance,
        lower_blocks=lower_blocks,
        outer_2x6=outer_2x6,
        remove_outer_links=remove_outer_links,
        second_inner_bolts=second_inner_bolts,
        support_up=support_up,
    )


def _load_orientation_audit() -> dict[str, Any]:
    return json.loads(ORIENTATION_AUDIT_PATH.read_text())


def _attach_archived_outer_links_findings(
    report: dict[str, Any],
    *,
    expected_revision_id: str,
    expected_input_revision_id: str,
) -> dict[str, Any]:
    """Restore the verified review findings consumed by common-block replay.

    The original viewer driver added findings after the geometry helper. The
    archived report is used only when its verification hash and replayed
    geometry fields match exactly; otherwise the replay stops rather than
    silently losing or borrowing findings from another revision.
    """
    report_bytes = OUTER_LINKS_REPORT_PATH.read_bytes()
    archived = json.loads(report_bytes)
    verification = json.loads(OUTER_LINKS_VERIFICATION_PATH.read_text())
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    if verification.get("report_sha256") != report_sha256:
        raise RuntimeError("archived outer-links report does not match its verification hash")
    if verification.get("revision_id") != expected_revision_id:
        raise RuntimeError("outer-links verification names a different geometry revision")
    if verification.get("joint_evaluations_run") is not False:
        raise RuntimeError("archived outer-links report is not a geometry-only checkpoint")
    if archived.get("revision_id") != expected_revision_id:
        raise RuntimeError("archived outer-links report names a different geometry revision")
    if archived.get("input_revision_id") != expected_input_revision_id:
        raise RuntimeError("archived outer-links report has a different input revision")
    archived_prior = archived.get("prior_revision_report")
    if not isinstance(archived_prior, dict) or archived_prior.get("revision_id") != expected_input_revision_id:
        raise RuntimeError("archived outer-links report has a mismatched prior-revision binding")
    if report.get("revision_id") != expected_revision_id:
        raise RuntimeError("replayed outer-links report names a different geometry revision")
    if report.get("input_revision_id") != expected_input_revision_id:
        raise RuntimeError("replayed outer-links report has a different input revision")

    mismatches = [
        key for key in _OUTER_LINKS_GEOMETRY_FIELDS
        if key not in archived
        or key not in report
        or report[key] != archived[key]
    ]
    if mismatches:
        raise RuntimeError(
            "archived outer-links findings are not bound to this geometry replay; "
            "mismatched fields: " + ", ".join(mismatches)
        )
    findings = archived.get("findings")
    if not isinstance(findings, list) or not findings:
        raise RuntimeError("verified outer-links report has no findings to preserve")
    if any(not isinstance(row, dict) or not row.get("title") or not row.get("detail") for row in findings):
        raise RuntimeError("verified outer-links findings are incomplete")

    existing_findings = report.get("findings", [])
    if not isinstance(existing_findings, list):
        raise TypeError("replayed outer-links findings must be a list")
    merged_findings = copy.deepcopy(findings)
    for row in existing_findings:
        if row not in merged_findings:
            merged_findings.append(copy.deepcopy(row))
    report["findings"] = merged_findings
    return {
        "revision_id": expected_revision_id,
        "report_path": str(OUTER_LINKS_REPORT_PATH.relative_to(ROOT)),
        "report_sha256": report_sha256,
        "archived_finding_count": len(findings),
        "finding_count": len(merged_findings),
    }


def build_current_geometry(
    base_geometry: Any | None = None,
    *,
    progress: Callable[[str], None] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Build and return ``(current_geometry, cumulative_revision_report)``.

    ``base_geometry`` is the already-composed historical WJ24 baseline used by
    the recorded incremental drivers. Supplying it avoids recomposition and
    leaves source/authority metadata outside this frozen geometry replay. If
    omitted, the original source-pinned composition sequence is rebuilt first.
    """
    baseline = base_geometry if base_geometry is not None else _compose_baseline_geometry()
    helpers = _load_revision_helpers()

    lower_geometry, lower_report = helpers.lower_blocks.build_wj24_lower_blocks_below(
        baseline, progress=progress
    )
    raised_geometry, _raised_report = helpers.support_up.build_wj24_bottom_support_up_one_row(
        lower_geometry, lower_report
    )
    above_geometry, above_report = helpers.above_tnuts.build_bottom_support_above_tnuts(
        lower_geometry, lower_report, raised_geometry
    )
    kicker_geometry, kicker_report = helpers.kicker_posts.build_kicker_posts_outside_tnuts(
        above_geometry, above_report
    )
    header_geometry, header_report = helpers.center_header.build_wj24_center_header_blocks(
        kicker_geometry, kicker_report
    )
    inner_geometry, inner_report = helpers.inner_frame.build_wj24_inner_frame_blocks(
        header_geometry, header_report
    )
    links_geometry, links_report = helpers.remove_outer_links.build_wj24_remove_outer_links(
        inner_geometry, inner_report
    )
    findings_source = _attach_archived_outer_links_findings(
        links_report,
        expected_revision_id=helpers.remove_outer_links.REVISION_ID,
        expected_input_revision_id=helpers.remove_outer_links.INPUT_REVISION_ID,
    )
    common_geometry, common_report = helpers.common_blocks.build_wj24_common_blocks(
        links_geometry, links_report
    )
    second_geometry, second_report = helpers.second_inner_bolts.build_wj24_second_inner_bolts(
        common_geometry, common_report
    )
    oriented_geometry, oriented_report = helpers.bolt_orientation.build_wj24_bolt_orientation(
        second_geometry, second_report, _load_orientation_audit()
    )
    led_geometry, led_report = helpers.led_clearance.build_wj24_led_clearance(
        oriented_geometry, oriented_report
    )
    current_geometry, current_report = helpers.outer_2x6.build_wj24_2x6_outer_blocks(
        led_geometry, led_report
    )

    if getattr(current_geometry, "layout_id", None) != CURRENT_REVISION_ID:
        raise RuntimeError(
            "incremental builders returned an unexpected current geometry revision: "
            f"{getattr(current_geometry, 'layout_id', None)!r}"
        )
    if current_report.get("revision_id") != CURRENT_REVISION_ID:
        raise RuntimeError("cumulative report does not describe the current geometry revision")
    current_report.update({
        "report_kind": "geometry_construction_report",
        "viewer_report_parity": False,
        "viewer_report_parity_note": (
            "This report records the reproducible geometry-helper chain. It does not include "
            "all manually assembled viewer annotations, focused checks, or weight summaries."
        ),
        "archived_findings_source": findings_source,
        "joint_evaluations_run": False,
        "release": {
            "candidate_accepted": False,
            "source_cutting_released": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_accepted": False,
            "assembly_proven": False,
        },
    })
    return current_geometry, current_report


# The longer spelling makes the review status explicit for downstream callers.
build_current_review_geometry = build_current_geometry
