#!/usr/bin/env python3
"""Read-only verification of the current timber grade disposition artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
OUT_DIR = Path(__file__).resolve().parent
DATA_PATH = OUT_DIR / "grade-disposition.json"
YIELD_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-timber-source-yield-attempt01/current-timber-source-yield.json"
)
MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json"
)
FRAME_MAP_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-timber-material-frame-map-attempt01/"
    "current-frame-timber-material-frame-map.json"
)
BLOCK_MAP_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-block-material-frame-map-attempt02/material-frame-map.json"
)

EXPECTED_HASHES = {
    YIELD_PATH: "2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c",
    "docs/wood-joints-mvp/source-inventory.json": "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json": "21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3",
    "docs/wood-joints-mvp/corner-block-stock-review-2026-09-24.md": "d7bdbb263e7e224fb911230c4aa5c7574d24be058634a2cf390ecf4bc72ed182",
    "docs/wood-joints-mvp/current-material-scenarios.md": "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4",
    "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json": "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695",
    "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    FRAME_MAP_PATH: "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    BLOCK_MAP_PATH: "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
}

EXPECTED_BLOCKS = {
    "center_principal_cleat_left": ([83.9, 139.7], 134.7, [83.9, 139.7, 134.7]),
    "center_principal_cleat_right": ([83.9, 139.7], 134.7, [83.9, 139.7, 134.7]),
    "knee_outer_left_inner_frame_block": (
        [88.9, 133.35],
        139.0,
        [88.9, 133.35, 139.0],
    ),
    "knee_outer_right_inner_frame_block": (
        [88.9, 133.35],
        139.0,
        [88.9, 133.35, 139.0],
    ),
}

EXPECTED_ARTIFACT_GROUPS = {
    frozenset({"center_principal_cleat_left", "center_principal_cleat_right"}): {
        "quantity": 2,
        "source_cross_section_mm": [88.9, 139.7],
        "proposed_rip_mm": 5.0,
        "proposed_blank_cross_section_mm": [83.9, 139.7],
        "proposed_blank_length_mm": 134.7,
        "source_geometry_bounds_xyz_mm": [83.9, 139.7, 134.7],
    },
    frozenset(
        {
            "knee_outer_left_inner_frame_block",
            "knee_outer_right_inner_frame_block",
        }
    ): {
        "quantity": 2,
        "source_cross_section_mm": [88.9, 139.7],
        "proposed_rip_mm": 6.35,
        "proposed_blank_cross_section_mm": [88.9, 133.35],
        "proposed_blank_length_mm": 139.0,
        "source_geometry_bounds_xyz_mm": [88.9, 133.35, 139.0],
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def verify_proposed_rips(disposition: dict[str, Any]) -> None:
    groups = disposition["proposed_ripped_blocks"]
    assert len(groups) == len(EXPECTED_ARTIFACT_GROUPS)
    found_ids: set[str] = set()
    found_groups: set[frozenset[str]] = set()

    for group in groups:
        part_ids = frozenset(group["part_ids"])
        assert part_ids not in found_groups
        found_groups.add(part_ids)
        found_ids.update(part_ids)
        expected = EXPECTED_ARTIFACT_GROUPS[part_ids]
        assert group["quantity"] == expected["quantity"]
        assert len(group["part_ids"]) == group["quantity"]
        assert group["source_stock_class"] == "4x6"
        for field, value in expected.items():
            assert group[field] == value, f"{field} differs for {sorted(part_ids)}"
        assert group["proposed_length_axis"] == "global_Z"
        assert group["source_proposed_grade"] is None
        assert group["delivered_grade"] is None
        assert group["post_rip_grade_or_inspection_basis"] is None

    assert found_groups == set(EXPECTED_ARTIFACT_GROUPS)
    assert found_ids == set(EXPECTED_BLOCKS)
    assert sum(group["quantity"] for group in groups) == 4


def verify() -> None:
    disposition = read_json(DATA_PATH)
    verify_proposed_rips(disposition)
    for relative_path, expected in EXPECTED_HASHES.items():
        actual = sha256(ROOT / relative_path)
        assert actual == expected, f"source hash changed: {relative_path}"

    binding = disposition["source_binding"]
    yield_pin = binding["primary_source_yield_attempt"]
    assert yield_pin["path"] == YIELD_PATH
    assert yield_pin["file_sha256"] == EXPECTED_HASHES[YIELD_PATH]
    assert sha256(ROOT / yield_pin["path"]) == yield_pin["file_sha256"]
    yield_data = read_json(ROOT / yield_pin["path"])
    assert yield_data["attempt_id"] == "current-timber-source-yield-attempt01"
    assert yield_data["candidate"] == disposition["candidate"]
    assert yield_data["geometry_revision_id"] == disposition["geometry_revision_id"]
    assert yield_data["reviewed_repository_commit"] == "b1e8707d"
    assert yield_data["attempt02_manifest_sha256"] == yield_pin["manifest_sha256_field"]
    assert yield_data["ripped_4x6_blocks"]["count"] == 4

    manifest_path = ROOT / MANIFEST_PATH
    manifest = read_json(manifest_path)
    manifest_payload = dict(manifest)
    manifest_digest = manifest_payload.pop("manifest_sha256")
    assert manifest_digest == yield_pin["manifest_sha256_field"]
    assert hashlib.sha256(canonical_json(manifest_payload)).hexdigest() == manifest_digest
    assert manifest["manifest_id"] == "current-full-frame-input-manifest-attempt02"
    assert manifest["selected_candidate_authority_preserved"] == disposition[
        "selected_candidate_authority_preserved"
    ]
    assert sha256(ROOT / "current-candidate.json") == EXPECTED_HASHES[
        "current-candidate.json"
    ]

    for source_pin in yield_data["source_artifacts"]:
        assert sha256(ROOT / source_pin["path"]) == source_pin["sha256"]

    for source_pin in binding["pinned_source_inputs"]:
        assert source_pin["path"] in EXPECTED_HASHES
        assert source_pin["sha256"] == EXPECTED_HASHES[source_pin["path"]]
    for map_pin in binding["material_frame_maps"]:
        assert map_pin["path"] in EXPECTED_HASHES
        assert map_pin["sha256"] == EXPECTED_HASHES[map_pin["path"]]

    records = {record["part_id"]: record for record in yield_data["candidate_block_records"]}
    assert set(records).intersection(EXPECTED_BLOCKS) == set(EXPECTED_BLOCKS)
    for part_id, (section, length, bounds) in EXPECTED_BLOCKS.items():
        record = records[part_id]
        assert record["proposed_blank_cross_section_mm"] == section
        assert record["proposed_blank_stock_length_mm"] == length
        assert record["finished_geometry_bounds_dimensions_xyz_mm"] == bounds
        assert record["proposed_stock_class"] == "4x6"
        assert record["proposed_delivered_grade"] is None
        assert record["inspector_or_regrade_basis"] is None

    frame_map = read_json(ROOT / binding["material_frame_maps"][0]["path"])
    block_map = read_json(ROOT / binding["material_frame_maps"][1]["path"])
    assert frame_map["scope"]["mapped_frame_timber_count"] == 20
    assert block_map["scope"]["mapped_connector_block_count"] == 24
    assert frame_map["geometry_revision_id"] == disposition["geometry_revision_id"]
    assert block_map["geometry_revision_id"] == disposition["geometry_revision_id"]
    assert frame_map["record_sha256"] == binding["material_frame_maps"][0][
        "record_sha256"
    ]
    assert block_map["record_sha256"] == binding["material_frame_maps"][1][
        "record_sha256"
    ]
    assert disposition["selected_candidate_authority_preserved"] == (
        "compact-floor-flush-development"
    )

    grade = disposition["grade_disposition"]
    assert grade["assigned_grade"] is None
    assert grade["grade_claimed"] is False
    assert grade["original_4x6_grade_transferred"] is False
    assert grade["original_4x6_design_values_transferred"] is False
    assert disposition["release"]["grade_assigned"] is False
    assert disposition["release"]["design_values_assigned"] is False

    print(
        "Verified pinned source hashes, revision, 20/24 maps, four rip targets, "
        "and no-grade limits."
    )


if __name__ == "__main__":
    verify()
