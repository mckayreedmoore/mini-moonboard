#!/usr/bin/env python3
"""Build or verify a source-pinned, read-only T07 fit/transport register."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "AGENTS.md").is_file())
OUTPUT = HERE / "evidence-register.json"

PINNED = [
    ("docs/wood-joints-mvp/current-access-screen.md", "current 92-axis exact-component screen summary"),
    ("docs/wood-joints-mvp/current-retained-access.md", "current 12-axis retained hardware screen summary"),
    ("docs/wood-joints-mvp/current-retained-wire-sequence.md", "retained leg-bolt wire-service hypothesis and exact limits"),
    ("docs/wood-joints-mvp/current-hardware-schedule.md", "candidate and retained product/fit gaps"),
    ("docs/wood-joints-mvp/current-thread-fit-travel.md", "conditional thread class comparator and unmeasured-fit boundary"),
    ("docs/wood-joints-mvp/current-ordinary-nut-washer-property-basis.md", "conditional candidate nut/washer product boundary"),
    ("docs/wood-joints-mvp/transport-operations.md", "current high-level assembly/removal hypothesis"),
    ("docs/round-service-wiring-reference.json", "source lighting/string installation reference"),
    ("docs/led-wiring-reference.json", "modeled current wire and LED identity map"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json", "latest exact-component candidate-axis collision result"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-access-attempt03/access.json", "latest retained frame-bolt withdrawal/insertion result"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/captured-nut-motion-attempt02/motion.json", "captured local nut/washer alternate-motion result"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01/operation-coverage.json", "operation and entity coverage source"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json", "focused nut-slide, retained-wire, and tool-profile interpretation"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json", "current 50-member identity and geometry binding"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/brep-export/manifest.json", "D6 export identity, role, and removal dependency map"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/readback-validation.json", "211-file STEP summary/readback validation"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/independent-review.md", "independent D6 export review and state limits"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/parent-run-attempt02/report.json", "left leg bounded movement screen"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/independent-review.md", "left leg independent review"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/parent-run-attempt01/report.json", "right leg bounded movement screen"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/independent-review.md", "right leg independent review"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/parent-run-attempt01/report.json", "paired floor-rail minimal separation screens"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/independent-review.md", "paired floor-rail independent review"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/parent-run-attempt02/report.json", "left center-post bounded movement screen"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/independent-review.md", "left center-post independent review"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/parent-run-attempt02/report.json", "right center-post bounded movement screen"),
    ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/independent-review.md", "right center-post independent review"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def target_motion(relative: str) -> list[dict]:
    report = read_json(relative)
    cases = report.get("cases") or [report]
    rows = []
    for case in cases:
        target = case.get("target_member") or {}
        rows.append({
            "member_id": target.get("shape_id", target.get("member_id")),
            "translation_vector_xyz_mm": target.get("translation_vector_xyz_mm"),
            "travel_mm": target.get("travel_mm"),
            "status": case.get("status", report.get("status")),
            "operation_state_assumptions": case.get("operation_state_assumptions", report.get("operation_state_assumptions", [])),
        })
    return rows


def build_register() -> dict:
    pins = [{"path": path, "sha256": expected, "role": role}
            for path, role, expected in PIN_ROWS]
    tool_route_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json"
    full_manifest_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    access_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json"
    retained_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-access-attempt03/access.json"
    export_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/brep-export/manifest.json"

    tool = read_json(tool_route_path)
    full = read_json(full_manifest_path)
    access = read_json(access_path)
    retained = read_json(retained_path)
    export = read_json(export_path)
    members = full["physical_members"]
    original_timbers = sorted(
        row["member_id"] for row in members
        if row.get("member_kind") == "timber" and "source_inventory_member" in row.get("composition_roles", [])
    )
    panels = sorted(row["member_id"] for row in members if row.get("member_kind") == "panel")
    blocks = sorted(row["part_id"] for row in full["candidate_blocks"])

    expected_nut_axes = {
        "bottom_center/clip_horizontal_bottom_left_2/rail_2",
        "bottom_center/clip_horizontal_bottom_right_1/rail_2",
        "bottom_outer/clip_horizontal_bottom_left_1/rail_2",
        "bottom_outer/clip_horizontal_bottom_right_2/rail_2",
    }
    observed_nut_axes = {row["axis_id"] for row in tool["candidate_nut_slide_hits"]["hits"]}
    captured_axes = {row["axis_id"] for row in tool["candidate_captured_nut_local_route"]["rows"]}
    wire_rows = tool["retained_frame_bolt_wire_hits"]["rows"]
    if (len(original_timbers), len(blocks), len(panels)) != (20, 24, 6):
        raise ValueError("current full-frame identity counts changed")
    if (tool["candidate_nut_slide_hits"]["axis_count"], len(tool["candidate_nut_slide_hits"]["hits"])) != (4, 6):
        raise ValueError("candidate nut-slide hit count changed")
    if observed_nut_axes != expected_nut_axes or captured_axes != expected_nut_axes:
        raise ValueError("candidate slide/captured-route axis identities changed")
    if any(not row["clear_local_option"]["external_geometry_clear"] for row in tool["candidate_captured_nut_local_route"]["rows"]):
        raise ValueError("a captured local route no longer has its recorded CAD-clear flag")
    if (tool["retained_frame_bolt_wire_hits"]["axis_count"],
            tool["retained_frame_bolt_wire_hits"]["component_sweep_hit_count"], len(wire_rows)) != (4, 12, 4):
        raise ValueError("retained wire-conflict count changed")
    if any(row["physical_cable_blockage_established"] or row["reverse_insertion_physical_route_established"] for row in wire_rows):
        raise ValueError("retained wire evidence boundary changed")

    motion = {
        "lumber_legs": target_motion("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/parent-run-attempt02/report.json") + target_motion("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/parent-run-attempt01/report.json"),
        "base_floor_rails": target_motion("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/parent-run-attempt01/report.json"),
        "center_posts": target_motion("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/parent-run-attempt02/report.json") + target_motion("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/parent-run-attempt02/report.json"),
        "coverage_limit": "Six of 20 source timbers have bounded movement reports: four 62.468/140.7 mm translations and two 1 mm rail separations. No report supplies support, positive clearance margin, or stable staging; no other source timber, block-body, or panel movement is screened here.",
    }
    screened_source_timbers = sorted({
        row["member_id"]
        for family in ("lumber_legs", "base_floor_rails", "center_posts")
        for row in motion[family]
    })
    if len(screened_source_timbers) != 6 or not set(screened_source_timbers).issubset(original_timbers):
        raise ValueError("member-motion report target identity coverage changed")
    motion["screened_source_timber_ids"] = screened_source_timbers
    motion["unscanned_source_timber_ids"] = sorted(set(original_timbers) - set(screened_source_timbers))
    motion["unscanned_candidate_block_ids"] = blocks
    motion["unscanned_panel_ids"] = panels

    return {
        "schema": "current-fit-transport-closeout-source-register/v1",
        "status": "bounded_source_review_no_reversible_operation_clear",
        "geometry_revision_id": full["geometry_revision_id"],
        "source_authority": {
            "full_frame_manifest_path": full_manifest_path,
            "full_frame_manifest_file_sha256": dict((p, h) for p, _, h in PIN_ROWS)[full_manifest_path],
            "full_frame_manifest_internal_sha256": full.get("manifest_sha256"),
            "readiness": full.get("readiness"),
            "release": full.get("release"),
        },
        "source_pins": pins,
        "transport_identity_inventory": {
            "source_timbers": original_timbers,
            "candidate_block_bodies": blocks,
            "panels": panels,
            "source_timber_count": len(original_timbers),
            "candidate_block_count": len(blocks),
            "panel_count": len(panels),
            "total_individual_member_or_panel_identities": len(original_timbers) + len(blocks) + len(panels),
            "candidate_bolt_axis_count": len(full["candidate_bolt_axes"]),
            "retained_frame_bolt_axis_count": len(full["retained_frame_bolt_axes"]),
            "retained_frame_bolt_physical_role_count": export["exported_counts"]["retained_frame_bolt_physical_roles"],
            "panel_kicker_screw_axis_count": len(full["panel_kicker_screw_axes"]),
            "unchanged_panel_axes": full["inventory_counts"]["panel_axes_unchanged"],
            "owner_moved_panel_axes": full["inventory_counts"]["panel_axes_owner_moved"],
            "d6_export_counts": export["exported_counts"],
        },
        "candidate_access_screen": {
            "path": access_path,
            "status": access["status"],
            "axis_count": len(access["axis_operations"]),
            "geometry_revision_id": access["geometry_revision_id"],
            "scope_boundary": "Exact supplied source-component BReps and modeled scene only; hardware remains unselected/unverified.",
        },
        "candidate_nut_slide_findings": {
            "source_path": tool_route_path,
            "axis_count": tool["candidate_nut_slide_hits"]["axis_count"],
            "direct_axial_component_hit_count": tool["candidate_nut_slide_hits"]["direct_axial_hit_count"],
            "basis": tool["candidate_nut_slide_hits"]["basis"],
            "hits": tool["candidate_nut_slide_hits"]["hits"],
            "captured_local_route": tool["candidate_captured_nut_local_route"],
            "blocker_removal_alternative": tool["blocker_removal_alternative"],
            "status": "six source-CAD slide hits have a locally clear captured lateral alternative; no tool-fit, thread-release, capture, full staging, or reverse-assembly clearance is established",
        },
        "retained_leg_bolt_wire_findings": {
            "source_path": tool_route_path,
            "axis_count": tool["retained_frame_bolt_wire_hits"]["axis_count"],
            "component_sweep_hit_count": tool["retained_frame_bolt_wire_hits"]["component_sweep_hit_count"],
            "rows": tool["retained_frame_bolt_wire_hits"]["rows"],
            "service_sequence_status": tool["retained_frame_bolt_wire_hits"]["service_sequence_status"],
            "service_sequence_note": tool["retained_frame_bolt_wire_hits"]["service_sequence_note"],
            "minimum_missing_evidence": tool["minimum_missing_evidence"],
            "status": "modeled wire-solid hits are not proof of physical cable blockage; a reversible service state and reverse bolt path are unestablished",
        },
        "tool_profile_evidence": {
            "candidate_profiles": tool["tool_profile_candidates"],
            "synthetic_proxy_rows": tool["existing_synthetic_tool_proxy_rows"],
            "scope": "Manufacturer profile dimensions are comparators only. No actual tool is selected, jaw/counterhold/hand fit is proved, or torque method assigned.",
        },
        "retained_access_screen": {
            "path": retained_path,
            "sha256": dict((p, h) for p, _, h in PIN_ROWS)[retained_path],
            "axis_count": len(retained["axis_operations"]),
            "targeted_wire_conflict_ids": [row["axis_id"] for row in tool["retained_frame_bolt_wire_hits"]["rows"]],
            "modeled_withdrawal_mm": [row["modeled_withdrawal_mm"] for row in tool["retained_frame_bolt_wire_hits"]["rows"]],
            "physical_cable_blockage_established": any(row["physical_cable_blockage_established"] for row in tool["retained_frame_bolt_wire_hits"]["rows"]),
            "reverse_insertion_physical_route_established": any(row["reverse_insertion_physical_route_established"] for row in tool["retained_frame_bolt_wire_hits"]["rows"]),
        },
        "source_timbers_motion_evidence": motion,
        "operation_sequence": {
            "forward_hypothesis": ["support/stage members", "frame and retained bolts", "candidate blocks and bolt stacks", "six panels and 66 separate screw operations", "lighting/wires and lights"],
            "reverse_hypothesis": ["support/capture", "lights and service wiring by a documented reversible route", "panels and 66 separate screw operations", "candidate stacks and blocks", "retained frame bolts", "individual timber members"],
            "source_path": "docs/wood-joints-mvp/transport-operations.md",
            "accepted": False,
            "within_family_order_established": False,
        },
        "scope_boundary": [
            "No CAD or geometry edits, native solves, vendor outreach, product selection, or physical operation occurred.",
            "Solid-sweep intersections describe the pinned CAD BReps and fixed modeled wires, not delivered hardware or flexible-cable snag behavior.",
            "All movement screens assume prior removals and do not establish tool access, support transfer, human handling, positive tolerance margin, stable staging, or a full reversible sequence.",
            "No structural capacity, load-path acceptance, fabrication, assembly, transport, or climbing release is claimed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    failures = []
    for relative, role in PINNED:
        source = ROOT / relative
        if not source.is_file():
            failures.append(f"missing source: {relative}")
            continue
        actual = sha256(source)
        expected = EXPECTED_SHA256[relative]
        if actual != expected:
            failures.append(f"source hash mismatch: {relative}: expected {expected}, got {actual}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 2

    register = build_register()
    rendered = json.dumps(register, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return 0
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
        print("evidence-register.json differs from pinned-source reconstruction", file=sys.stderr)
        return 1
    print(f"PASS {OUTPUT.relative_to(ROOT)}; {len(PINNED)} source pins matched")
    return 0


EXPECTED_SHA256 = {
    "docs/wood-joints-mvp/current-access-screen.md": "8ea4253fd7d4ab2e3e6457e0547bdde0b7a249fa9413eb7c4649ed25e1b4d8a1",
    "docs/wood-joints-mvp/current-retained-access.md": "b9e7240e0a2b500ff0a71a1517c22c3a5b14576791e3ca691efe6efb426ce76c",
    "docs/wood-joints-mvp/current-retained-wire-sequence.md": "d4df2519c579c8f5d2865205f7c3e6dc03eb4136d7853530031ef90e56dd0559",
    "docs/wood-joints-mvp/current-hardware-schedule.md": "47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa",
    "docs/wood-joints-mvp/current-thread-fit-travel.md": "4046318d1fac274bc3a2bb654921d3eaa4bce9c33e2cc2c391b8b83f4ac8d50d",
    "docs/wood-joints-mvp/current-ordinary-nut-washer-property-basis.md": "98a151ae040232aa1f2485826ba4c29dc0e0d0fb1ce6ac87ddd9bf062eeb6bcf",
    "docs/wood-joints-mvp/transport-operations.md": "8484c1f6f307716ea3a81470d4fbc5c91aa0353afb63f3d8693e78b2d8482ca3",
    "docs/round-service-wiring-reference.json": "b335fe3732c89e66625bac0525e959ccc562e2c7cd0e1e1551a4720fc26497f8",
    "docs/led-wiring-reference.json": "b0f93c4f48139561c06491d3d1031b9e3ceb830f40e1fcf78bdf846146f3f1f0",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json": "bd2b97c0677b2e0ab5b09898ba7f2227758088744cd93f7e3c9b266bce5c5215",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-access-attempt03/access.json": "fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/captured-nut-motion-attempt02/motion.json": "83c905bec64010695c769a73d7b8923869ef1aef5bda9b8591cdad0d443b21a4",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01/operation-coverage.json": "1722ff0f0a438934df15e6285947bdbf3b34f8d99a1e94e30403d756ab33d7ae",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json": "f7848741b4e3edbc15b36084bc5a89f884cea38e1f39c8edfe26527e4eb1b292",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json": "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/brep-export/manifest.json": "d90a93440575b7871fc429c3f8cec621877f805a068b7ff09a60fddc4b1e538b",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/readback-validation.json": "b5ff31f6d50c15bdec692cf54bd964c8b5d44fee8fc1dc1aa87ac80a802142f3",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/independent-review.md": "b029c852443662751be7ee5bfd85069be3a9391b0e0032b37f2c57fec38d0f91",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/parent-run-attempt02/report.json": "01e42fce759ddb69f1e099fde55a5a24f7833b9982a4f99d5cab4c2ec3ab209f",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/independent-review.md": "fe2ca72d425f60f38e2b29f817ca6ef6d44482170bb379d7eec6674ad7bac449",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/parent-run-attempt01/report.json": "7e73a8105ede4c6d65a683fccd0c2f97ebbba35fd01be5280669576e594f0669",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/independent-review.md": "0d9d9c14bc0a04586c220e1ef2588c5066763fbe8cbbc7d2254141b558b951de",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/parent-run-attempt01/report.json": "2ce63b037951f06d5d524daae5bef906af5e0bb5b7358a324492d5a76296e715",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/independent-review.md": "a3a8a543398e863ca5b5262a19be0c798176deb3e3595e959d7c0ee170f4a0e7",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/parent-run-attempt02/report.json": "ba7d4ff4f20f68477b1e6cdcd1a183357104daa3f35e630eaa8f692fc783995d",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/independent-review.md": "07fcc720d93290afea0eaa1a2df1d257b5d2ba1f2523d97947ce64bba19d9094",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/parent-run-attempt02/report.json": "04bebd247a2b4a278403a5df4a697a5044682b93ccfe9c93b3be56c53cfd6899",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/independent-review.md": "a98969b374e840ebaf8c4bade641a2c93e0b3812ae09ae3f42f04840fbd38af9",
}

# Keep the pin metadata and digest table separate so the build emits concise
# source records without duplicating path literals in the generated payload.
PIN_ROWS = [(path, role, EXPECTED_SHA256[path]) for path, role in PINNED]


if __name__ == "__main__":
    raise SystemExit(main())
