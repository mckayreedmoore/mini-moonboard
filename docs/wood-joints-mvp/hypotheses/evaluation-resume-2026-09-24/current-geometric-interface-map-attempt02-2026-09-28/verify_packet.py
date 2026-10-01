#!/usr/bin/env python3
"""Verify the source-pinned nominal BRep graph and receiver-screen packet."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-map-attempt02-2026-09-28"
)
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_REPORT_FILE_SHA = "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695"
EXPECTED_REPORT_CANONICAL_SHA = "adc7c1df49fcb231d705a3b40556a6b06f95aee48f16b0f91acbc77c7325a40d"
EXPECTED_BUILD_REPORT_CANONICAL_SHA = "06a4e848a3066d7e990bf146f11e513b128567b4d23c388d6a1d6ad8d980b4e0"
EXPECTED_GRAPH_BODY_CANONICAL_SHA = "8c1a792df9102b89a36060fb092edffc9843c224a55e64480e2a42af6afbbfa0"
EXPECTED_RECEIVER_CANONICAL_SHA = "39c5e14b85bc48d8ef9ed9fbc838f27254b3acf2d22c9258fe8d996807f3eeb2"

ROOT_FILES = [
    (
        "frozen_revision_report",
        "site/owner-wood-joints-review-report.json",
        "exact frozen review report passed to both geometry collectors",
    ),
    (
        "upstream_complete_contact_graph",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json",
        "prior live full graph; exact collector body comparator (parent_run is wrapper metadata)",
    ),
    (
        "upstream_receiver_screen",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json",
        "prior receiver-screen output; exact collector comparator",
    ),
    (
        "current_input_manifest",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
        "current revision and 50 finished member/92 candidate/12 retained/66 screw identity cross-check",
    ),
    (
        "member_solids_manifest",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json",
        "exact current STEP member identities and descriptors",
    ),
]

PRODUCER_MODULES = [
    "scripts/wood_joint_current_geometry.py",
    "scripts/wood_joint_current_contact_graph.py",
    "scripts/wood_joint_current_receiver_screen.py",
    "scripts/wood_joint_wj12_diagnostic.py",
    "scripts/wood_joint_wj12_compositor.py",
    "scripts/wood_joint_wj16_compositor.py",
    "scripts/wood_joint_wj18_compositor.py",
    "scripts/wood_joint_wj24_compositor.py",
    "scripts/wood_joint_bottom_center_integration.py",
    "scripts/wood_joint_bottom_outer_integration.py",
    "scripts/wood_joint_left_rail_integration.py",
    "scripts/wood_joint_right_rail_integration.py",
    "scripts/wood_joint_top_center_integration.py",
    "scripts/wood_joint_top_outer_integration.py",
    "scripts/wood_joint_wj24_2x6_outer_blocks.py",
    "scripts/wood_joint_wj24_bolt_orientation.py",
    "scripts/wood_joint_wj24_bottom_support_above_tnuts.py",
    "scripts/wood_joint_wj24_bottom_support_up_one_row.py",
    "scripts/wood_joint_wj24_center_header_blocks.py",
    "scripts/wood_joint_wj24_common_blocks.py",
    "scripts/wood_joint_wj24_inner_frame_blocks.py",
    "scripts/wood_joint_wj24_kicker_posts_outside_tnuts.py",
    "scripts/wood_joint_wj24_led_clearance.py",
    "scripts/wood_joint_wj24_lower_blocks_below.py",
    "scripts/wood_joint_wj24_remove_outer_links.py",
    "scripts/wood_joint_wj24_second_inner_bolts.py",
]

OTHER_GEOMETRY_INPUTS = [
    "docs/wood-joints-mvp/hypotheses/consolidated-blocks-two-inner-bolts-2026-09-24/orientation-audit.json",
    "docs/wood-joints-mvp/hypotheses/outer-links-removed-2026-09-24/revision.json",
    "docs/wood-joints-mvp/hypotheses/outer-links-removed-2026-09-24/verification.json",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any, *, pretty: bool = True) -> bytes:
    if pretty:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value, pretty=False))


def root_from_script() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "current-candidate.json").is_file() and (parent / ".git").is_dir():
            return parent
    raise RuntimeError("could not locate repository root")


def load_json(root: Path, relative: str) -> Any:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def add_pin(pin_map: dict[str, dict[str, Any]], root: Path, path: str, use: str, expected: str | None = None) -> None:
    target = root / path
    if not target.is_file():
        raise FileNotFoundError(path)
    digest = sha256_file(target)
    if expected is not None and digest != expected:
        raise ValueError(f"source hash mismatch for {path}: expected {expected}, found {digest}")
    row = pin_map.setdefault(path, {"path": path, "sha256": digest, "size_bytes": target.stat().st_size, "uses": []})
    if row["sha256"] != digest or row["size_bytes"] != target.stat().st_size:
        raise ValueError(f"inconsistent source pin record: {path}")
    if use not in row["uses"]:
        row["uses"].append(use)


def make_source_pins(root: Path) -> dict[str, Any]:
    base = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    graph_rel = base + "complete-contact-graph-attempt02.json"
    receiver_rel = base + "receiver-screen-attempt04.json"
    manifest_rel = base + "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    solids_rel = base + "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
    report = load_json(root, ROOT_FILES[0][1])
    graph = load_json(root, graph_rel)
    receiver = load_json(root, receiver_rel)
    manifest = load_json(root, manifest_rel)
    solids = load_json(root, solids_rel)
    if canonical_sha(report) != EXPECTED_REPORT_CANONICAL_SHA:
        raise ValueError("frozen site review report canonical hash is not the parent-pinned report")
    if graph["revision_id"] != REVISION or receiver["revision_id"] != REVISION or manifest["geometry_revision_id"] != REVISION:
        raise ValueError("a pinned source names a different geometry revision")
    if graph["source_sha256"]["frozen_revision_report_canonical_json_sha256"] != EXPECTED_REPORT_CANONICAL_SHA:
        raise ValueError("upstream graph is not bound to the exact frozen review report")

    pin_map: dict[str, dict[str, Any]] = {}
    for key, path, use in ROOT_FILES:
        add_pin(pin_map, root, path, use)
    for path in PRODUCER_MODULES:
        add_pin(pin_map, root, path, "source code for exact geometry reconstruction/collectors")
    for path in OTHER_GEOMETRY_INPUTS:
        add_pin(pin_map, root, path, "additional direct input read by build_current_geometry")
    for path, expected in sorted(graph["source_sha256"]["geometry_source_inputs_sha256"].items()):
        add_pin(pin_map, root, path, "geometry object's source_input SHA-256 inventory", expected)

    solids_root = Path(solids_rel).parent.parent
    physical = {row["member_id"]: row for row in manifest["physical_members"]}
    finished = {row["member_id"]: row for row in manifest["finished_member_step_bindings"]}
    if len(solids["members"]) != 50 or set(physical) != set(finished):
        raise ValueError("current input manifest member inventories do not reconcile")
    for item in solids["members"]:
        member_id = item["member_id"]
        step_rel = (solids_root / item["step_file"]).as_posix()
        physical_binding = physical[member_id]["current_finished_step_binding"]
        finished_binding = finished[member_id]
        if (
            item["member_kind"] != finished_binding["member_kind"]
            or physical_binding["path"] != step_rel
            or physical_binding["file_sha256"] != item["step_sha256"]
            or finished_binding["path"] != step_rel
            or finished_binding["file_sha256"] != item["step_sha256"]
            or finished_binding["size_bytes"] != item["step_size_bytes"]
            or finished_binding["source_shape_fingerprint_sha256"] != item["source_shape_fingerprint_sha256"]
        ):
            raise ValueError(f"manifest/member STEP join failed for {member_id}")
        add_pin(pin_map, root, step_rel, f"exact current member STEP geometry: {member_id}", item["step_sha256"])

    rows = sorted(pin_map.values(), key=lambda row: row["path"])
    for row in rows:
        row["uses"].sort()
    return {
        "schema": "wood_joint_current_geometric_interface_map_source_pins/v1",
        "attempt_id": PACKET_REL.name,
        "geometry_revision_id": REVISION,
        "current_contact_graph_source_input_sha256": graph["source_sha256"]["geometry_source_inputs_sha256"],
        "source_inventory_sha256": graph["source_sha256"]["source_inventory_sha256"],
        "frozen_review_report_file_sha256": sha256_file(root / ROOT_FILES[0][1]),
        "frozen_review_report_canonical_json_sha256": canonical_sha(report),
        "current_member_step_count": len(solids["members"]),
        "source_count": len(rows),
        "runtime_for_full_rebuild": {
            "python": "3.12.3",
            "cadquery": "2.8.0",
            "cadquery_ocp": "7.9.3.1.1",
            "verified_command": ".venv/bin/python verify_packet.py --rebuild",
        },
        "sources": rows,
        "scope_notes": [
            "All 68 geometry source-input hashes reported by the full graph were rehashed against the current repository.",
            "Producer modules and direct revision-report/orientation inputs are separately pinned.",
            "All 50 current STEP hashes match both the member-solids descriptor and attempt04 finished-member bindings.",
            "The upstream graph/receiver files are pinned comparators; their collector result content is preserved in this attempt.",
        ],
    }


def expected_summary(graph: dict[str, Any], receiver: dict[str, Any], pins: dict[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(graph)
    parent_run = body.pop("parent_run", None)
    state_counts: dict[str, int] = {}
    unresolved = []
    for row in body["edges"]:
        state = row["geometry_state"]
        state_counts[state] = state_counts.get(state, 0) + 1
        if state == "zero_area_touch_or_unresolved":
            unresolved.append(
                {
                    "pair_id": "pair:" + "|".join(sorted(row["member_ids"])),
                    "member_ids": row["member_ids"],
                    "geometry_state": row["geometry_state"],
                    "interface_geometry_state": row["interface_geometry_state"],
                    "finite_shared_planar_face_area_mm2": row["finite_shared_planar_face_area_mm2"],
                    "minimum_separation_mm": row["minimum_separation_mm"],
                    "contact_measurement_basis": row["contact_measurement_basis"],
                }
            )
    unresolved.sort(key=lambda item: item["pair_id"])
    graph_bytes = (root_from_script() / PACKET_REL / "complete-contact-graph.json").read_bytes()
    receiver_bytes = (root_from_script() / PACKET_REL / "receiver-screen.json").read_bytes()
    return {
        "schema": "wood_joint_current_geometric_interface_map_summary/v1",
        "geometry_revision_id": REVISION,
        "result_scope": "nominal BRep/CAD geometry observations only",
        "source_derived_counts": {
            "physical_member_nodes": body["counts"]["physical_member_nodes"],
            "unique_member_pairs": body["counts"]["unique_member_pairs"],
            "aabb_broadphase_candidates": body["counts"]["aabb_broadphase_candidates"],
            "exact_brep_pairs_evaluated": body["counts"]["exact_brep_pairs_evaluated"],
            "aabb_separated_pairs_not_exactly_evaluated": body["counts"]["aabb_separated_pairs_not_exactly_evaluated"],
            "geometry_state_counts": dict(sorted(state_counts.items())),
            "candidate_bolt_axes": body["counts"]["candidate_bolt_axes"],
            "retained_frame_bolt_axes": body["counts"]["retained_frame_bolt_axes"],
            "hillman_panel_kicker_axes": body["counts"]["current_panel_screw_axes"],
            "hillman_unchanged_axes": receiver["counts"]["unchanged_source_station_axes"],
            "hillman_moved_axes": receiver["counts"]["moved_axes"],
        },
        "six_zero_area_or_unresolved_pairs": unresolved,
        "receiver_screen_counts": receiver["counts"],
        "center_kicker_receiver_check": receiver["four_moved_kicker_center_receiver_check"],
        "frozen_report_binding": {
            "file_sha256": pins["frozen_review_report_file_sha256"],
            "canonical_json_sha256": pins["frozen_review_report_canonical_json_sha256"],
            "construction_report_canonical_json_sha256_diagnostic_only": EXPECTED_BUILD_REPORT_CANONICAL_SHA,
            "collector_report_source": "site/owner-wood-joints-review-report.json",
        },
        "reconstruction_comparison": {
            "exact_pinned_report_rerun_matches_upstream_graph_body": True,
            "graph_comparison_rule": "current collect_current_contact_graph result equals attempt02 JSON after removing only wrapper parent_run metadata",
            "exact_pinned_report_rerun_matches_upstream_receiver_json": True,
            "prior_wrong_report_diagnostic_graph_canonical_sha256": "9d2d9a8dc9cb2b0832d6f0e7a75c7b6d9651dfdc4e75fe635e4d9ed370dafd8b",
            "prior_wrong_report_diagnostic_delta": "only source_sha256.frozen_revision_report_canonical_json_sha256 differed (construction report 06a4… vs pinned review report adc7…); all other graph fields and receiver JSON matched; rejected in favor of exact pinned-report rerun",
            "exact_collector_graph_body_canonical_sha256": EXPECTED_GRAPH_BODY_CANONICAL_SHA,
            "exact_receiver_json_canonical_sha256": EXPECTED_RECEIVER_CANONICAL_SHA,
            "upstream_parent_run_metadata_preserved_in_graph_file": parent_run,
        },
        "artifact_sha256": {
            "complete-contact-graph.json": sha256_bytes(graph_bytes),
            "receiver-screen.json": sha256_bytes(receiver_bytes),
            "source-pins.json": sha256_bytes(canonical_bytes(pins)),
        },
        "geometry_and_mechanics_limits": [
            "147 pairs were evaluated using exact BRep; 1,078 pairs were AABB-separated and were not evaluated exactly.",
            "115 finite opposed planar touches are nominal geometry, not proof of active bearing, face ownership, or force transfer.",
            "The six zero-area/unresolved pairs are listed individually; their classification is not repaired or promoted to contact.",
            "The 66 axis-envelope/receiver checks do not establish physical screw engagement; 92/12 bolt inventories are axis/membership records only.",
            "No load transfer, stiffness, engagement, resistance, response, mechanical equivalence, capacity, acceptance, fabrication release, or climbing release is claimed.",
        ],
    }


def expected_readme(summary: dict[str, Any]) -> str:
    counts = summary["source_derived_counts"]
    out = summary["artifact_sha256"]
    unresolved = "\n".join(
        f"- `{row['pair_id']}`: `{', '.join(row['member_ids'])}`"
        for row in summary["six_zero_area_or_unresolved_pairs"]
    )
    return f"""# Current geometric interface map — attempt 02

This append-only packet preserves the nominal BRep contact graph and panel/kicker receiver screen for `{REVISION}`. It is a geometry observation only.

The full graph contains {counts['physical_member_nodes']} member nodes and {counts['unique_member_pairs']} unordered pairs. The collector evaluated {counts['exact_brep_pairs_evaluated']} pairs by exact BRep after a 147-pair AABB broadphase; {counts['aabb_separated_pairs_not_exactly_evaluated']} AABB-separated pairs were not evaluated exactly. Geometry states: {counts['geometry_state_counts']}.

Axis inventory joins: {counts['candidate_bolt_axes']} candidate bolt axes, {counts['retained_frame_bolt_axes']} retained frame-bolt axes, and {counts['hillman_panel_kicker_axes']} Hillman panel/kicker axes ({counts['hillman_unchanged_axes']} unchanged, {counts['hillman_moved_axes']} moved). The receiver screen is the current 66-axis map; it is not an installed-fastener result.

## Six unresolved exact-BRep pairs

These are preserved as `zero_area_touch_or_unresolved`; no contact is inferred:

{unresolved}

## Provenance and validation

The collectors were run on a rebuild from `build_current_geometry()` and were passed the exact pinned `site/owner-wood-joints-review-report.json` report. The returned contact-graph body matches `complete-contact-graph-attempt02.json` after excluding only that prior driver wrapper's `parent_run` metadata. The receiver-screen JSON matches `receiver-screen-attempt04.json` exactly. A diagnostic run passed the builder's construction report instead; its only graph difference was the report provenance hash. That run is rejected and retained only as a documented diagnostic in `scope-summary.json`.

`source-pins.json` binds the frozen report, 68 geometry source-input hashes, producer modules, current attempt04 manifest, all 50 current STEP files, and upstream comparator outputs. `scope-summary.json` is deterministically reconstructed from the preserved JSON. Quick verification checks pins, joins, pair list, output hashes, and checksums:

```sh
python3 verify_packet.py --verify
sha256sum -c SHA256SUMS
```

Full nominal-BRep regeneration uses the repository CadQuery environment and takes about five minutes:

```sh
.venv/bin/python verify_packet.py --rebuild
```

## Limits

Every value is a nominal CAD/BRep observation. This packet establishes no active bearing, face ownership, load transfer, stiffness, fastener engagement, resistance, response, mechanical equivalence, capacity, acceptance, fabrication release, or climbing release. The 1,078 AABB-separated pairs remain unmeasured by exact BRep. The graph's preserved `parent_run.seconds` is metadata from the pinned prior live run; it is not a timing claim for the reconstruction performed for this packet.

Artifact hashes: graph `{out['complete-contact-graph.json']}`, receiver screen `{out['receiver-screen.json']}`, source pins `{out['source-pins.json']}`.
"""


def validate_content(root: Path, pins: dict[str, Any], graph: dict[str, Any], receiver: dict[str, Any]) -> dict[str, Any]:
    graph_body = copy.deepcopy(graph)
    parent_run = graph_body.pop("parent_run", None)
    if parent_run != {
        "collector_sha256": "8afed27a493719354c55b6c0deb5faeb1cd40068519d4578c365db120f293f7d",
        "seconds": parent_run.get("seconds") if isinstance(parent_run, dict) else None,
        "source_unchanged_after_run": True,
    }:
        raise ValueError("upstream graph parent_run wrapper is not the pinned expected form")
    if graph_body["revision_id"] != REVISION or receiver["revision_id"] != REVISION:
        raise ValueError("output artifact revision mismatch")
    if graph_body["source_sha256"]["frozen_revision_report_canonical_json_sha256"] != EXPECTED_REPORT_CANONICAL_SHA:
        raise ValueError("graph collector body uses an unexpected report provenance hash")
    if canonical_sha(graph_body) != EXPECTED_GRAPH_BODY_CANONICAL_SHA:
        raise ValueError("graph collector body canonical digest changed")
    if canonical_sha(receiver) != EXPECTED_RECEIVER_CANONICAL_SHA:
        raise ValueError("receiver screen canonical digest changed")
    expected_counts = {
        "physical_member_nodes": 50,
        "unique_member_pairs": 1225,
        "aabb_broadphase_candidates": 147,
        "exact_brep_pairs_evaluated": 147,
        "aabb_separated_pairs_not_exactly_evaluated": 1078,
        "candidate_bolt_axes": 92,
        "retained_frame_bolt_axes": 12,
        "current_panel_screw_axes": 66,
    }
    if graph_body["counts"] != expected_counts:
        raise ValueError(f"graph counts differ from parent-pinned reconstruction: {graph_body['counts']}")
    if receiver["counts"]["panel_kicker_axes_total"] != 66 or receiver["counts"]["unchanged_source_station_axes"] != 58 or receiver["counts"]["moved_axes"] != 8:
        raise ValueError("receiver-screen inventory counts changed")
    if pins["frozen_review_report_file_sha256"] != EXPECTED_REPORT_FILE_SHA or pins["frozen_review_report_canonical_json_sha256"] != EXPECTED_REPORT_CANONICAL_SHA:
        raise ValueError("source pins no longer identify exact frozen review report")

    manifest = load_json(root, ROOT_FILES[3][1])
    solids = load_json(root, ROOT_FILES[4][1])
    inventory = graph_body["inventories"]
    ids = {
        "physical_members": {row["member_id"] for row in inventory["physical_members"]},
        "candidate_bolt_axes": {row["axis_id"] for row in inventory["candidate_bolt_axes"]},
        "retained_frame_bolts": {row["axis_id"] for row in inventory["retained_frame_bolts"]},
        "current_panel_screw_axes": {row["axis_id"] for row in inventory["current_panel_screw_axes"]},
    }
    if ids["physical_members"] != {row["member_id"] for row in solids["members"]}:
        raise ValueError("graph and exact STEP member IDs differ")
    if ids["physical_members"] != {row["member_id"] for row in manifest["physical_members"]}:
        raise ValueError("graph and current manifest member IDs differ")
    for key, manifest_key in [
        ("candidate_bolt_axes", "candidate_bolt_axes"),
        ("retained_frame_bolts", "retained_frame_bolt_axes"),
        ("current_panel_screw_axes", "panel_kicker_screw_axes"),
    ]:
        if ids[key] != {row["axis_id"] for row in manifest[manifest_key]}:
            raise ValueError(f"graph and manifest axis IDs differ: {key}")

    pairs = []
    for row in graph_body["edges"]:
        if row["geometry_state"] == "zero_area_touch_or_unresolved":
            pairs.append(
                {
                    "pair_id": "pair:" + "|".join(sorted(row["member_ids"])),
                    "member_ids": row["member_ids"],
                    "geometry_state": row["geometry_state"],
                    "interface_geometry_state": row["interface_geometry_state"],
                    "finite_shared_planar_face_area_mm2": row["finite_shared_planar_face_area_mm2"],
                    "minimum_separation_mm": row["minimum_separation_mm"],
                    "contact_measurement_basis": row["contact_measurement_basis"],
                }
            )
    if len(pairs) != 6:
        raise ValueError(f"expected six unresolved exact-BRep pairs, found {len(pairs)}")
    states: dict[str, int] = {}
    for row in graph_body["edges"]:
        states[row["geometry_state"]] = states.get(row["geometry_state"], 0) + 1
    if states != {"finite_opposed_planar_touch": 115, "separated": 1104, "zero_area_touch_or_unresolved": 6}:
        raise ValueError(f"geometry state counts changed: {states}")
    return graph_body


def checksum_text(root: Path, names: list[str]) -> str:
    packet = root / PACKET_REL
    return "".join(f"{sha256_file(packet / name)}  {name}\n" for name in names)


def verify(root: Path) -> dict[str, Any]:
    packet = root / PACKET_REL
    pins = json.loads((packet / "source-pins.json").read_text(encoding="utf-8"))
    fresh_pins = make_source_pins(root)
    if canonical_bytes(pins) != canonical_bytes(fresh_pins):
        raise ValueError("source-pins.json differs from current exact source bytes")
    for source in pins["sources"]:
        actual = sha256_file(root / source["path"])
        if actual != source["sha256"]:
            raise ValueError(f"pinned source changed: {source['path']}")
    graph_path = packet / "complete-contact-graph.json"
    receiver_path = packet / "receiver-screen.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    receiver = json.loads(receiver_path.read_text(encoding="utf-8"))
    graph_body = validate_content(root, pins, graph, receiver)
    summary = json.loads((packet / "scope-summary.json").read_text(encoding="utf-8"))
    expected = expected_summary(graph, receiver, pins)
    if canonical_bytes(summary) != canonical_bytes(expected):
        raise ValueError("scope-summary.json is not the deterministic summary of preserved outputs")
    readme = expected_readme(summary)
    if (packet / "README.md").read_text(encoding="utf-8") != readme:
        raise ValueError("README.md differs from deterministic packet summary")
    files = ["README.md", "source-pins.json", "complete-contact-graph.json", "receiver-screen.json", "scope-summary.json", "verify_packet.py"]
    if (packet / "SHA256SUMS").read_text(encoding="utf-8") != checksum_text(root, files):
        raise ValueError("SHA256SUMS mismatch")
    return {
        "result": "PASS",
        "source_pins": len(pins["sources"]),
        "step_files": pins["current_member_step_count"],
        "graph_member_nodes": graph_body["counts"]["physical_member_nodes"],
        "graph_pairs": graph_body["counts"]["unique_member_pairs"],
        "exact_brep_pairs": graph_body["counts"]["exact_brep_pairs_evaluated"],
        "aabb_only_pairs": graph_body["counts"]["aabb_separated_pairs_not_exactly_evaluated"],
        "unresolved_pairs": len(summary["six_zero_area_or_unresolved_pairs"]),
        "axes": {key: summary["source_derived_counts"][key] for key in ["candidate_bolt_axes", "retained_frame_bolt_axes", "hillman_panel_kicker_axes"]},
        "checksum_files": len(files),
    }


def rebuild(root: Path) -> dict[str, Any]:
    verify(root)
    before = make_source_pins(root)
    # Imports remain inside the full-rebuild path; quick verification is CAD-free.
    from scripts.wood_joint_current_contact_graph import collect_current_contact_graph, _canonical_sha256
    from scripts.wood_joint_current_geometry import build_current_geometry
    from scripts.wood_joint_current_receiver_screen import collect_current_receiver_screen

    report_path = root / ROOT_FILES[0][1]
    frozen_report = json.loads(report_path.read_text(encoding="utf-8"))
    geometry, construction_report = build_current_geometry()
    construction_sha = _canonical_sha256(construction_report)
    if construction_sha != EXPECTED_BUILD_REPORT_CANONICAL_SHA:
        raise ValueError(f"construction report canonical hash changed: {construction_sha}")
    graph = collect_current_contact_graph(geometry, frozen_report)
    receiver = collect_current_receiver_screen(geometry, frozen_report)
    output_graph = json.loads((root / PACKET_REL / "complete-contact-graph.json").read_text(encoding="utf-8"))
    output_graph.pop("parent_run", None)
    if graph != output_graph:
        raise ValueError("full rebuild collector graph differs from preserved graph body")
    output_receiver = json.loads((root / PACKET_REL / "receiver-screen.json").read_text(encoding="utf-8"))
    if receiver != output_receiver:
        raise ValueError("full rebuild receiver screen differs from preserved JSON")
    if _canonical_sha256(graph) != EXPECTED_GRAPH_BODY_CANONICAL_SHA or _canonical_sha256(receiver) != EXPECTED_RECEIVER_CANONICAL_SHA:
        raise ValueError("full rebuild canonical collector digest mismatch")
    after = make_source_pins(root)
    if canonical_bytes(before) != canonical_bytes(after):
        raise ValueError("source inputs changed during full rebuild")
    return {"result": "PASS", "geometry_revision_id": geometry.layout_id, "construction_report_sha256": construction_sha, "collector_graph_sha256": _canonical_sha256(graph), "receiver_screen_sha256": _canonical_sha256(receiver)}


def freeze(root: Path) -> dict[str, Any]:
    packet = root / PACKET_REL
    packet.mkdir(parents=True, exist_ok=True)
    names = ["README.md", "source-pins.json", "complete-contact-graph.json", "receiver-screen.json", "scope-summary.json", "verify_packet.py", "SHA256SUMS"]
    # The verifier is authored first so it can define the freeze. Allow that
    # single bootstrap file, but never overwrite any generated packet content.
    existing = [name for name in names if name != "verify_packet.py" and (packet / name).exists()]
    if existing:
        raise FileExistsError(f"append-only attempt already contains files: {existing}")

    pins = make_source_pins(root)
    prior_graph_path = root / ROOT_FILES[1][1]
    prior_receiver_path = root / ROOT_FILES[2][1]
    graph = json.loads(prior_graph_path.read_text(encoding="utf-8"))
    receiver = json.loads(prior_receiver_path.read_text(encoding="utf-8"))
    validate_content(root, pins, graph, receiver)
    (packet / "source-pins.json").write_bytes(canonical_bytes(pins))
    (packet / "complete-contact-graph.json").write_bytes(prior_graph_path.read_bytes())
    (packet / "receiver-screen.json").write_bytes(prior_receiver_path.read_bytes())
    summary = expected_summary(graph, receiver, pins)
    (packet / "scope-summary.json").write_bytes(canonical_bytes(summary))
    (packet / "README.md").write_text(expected_readme(summary), encoding="utf-8")
    files = ["README.md", "source-pins.json", "complete-contact-graph.json", "receiver-screen.json", "scope-summary.json", "verify_packet.py"]
    (packet / "SHA256SUMS").write_text(checksum_text(root, files), encoding="utf-8")
    return verify(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true", help="create this new append-only packet from the exact validated upstream snapshot")
    group.add_argument("--verify", action="store_true", help="quickly verify pins, joins, summary, and checksums without loading CAD")
    group.add_argument("--rebuild", action="store_true", help="reconstruct current geometry and rerun both collectors; requires .venv CadQuery")
    args = parser.parse_args()
    root = root_from_script()
    try:
        result = freeze(root) if args.freeze else rebuild(root) if args.rebuild else verify(root)
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
