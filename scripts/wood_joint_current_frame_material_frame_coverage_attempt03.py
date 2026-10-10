#!/usr/bin/env python3
"""Bind each block transverse scenario to its complementary tangential axis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

if __package__:
    from scripts import (
        wood_joint_current_frame_material_frame_coverage_attempt02 as attempt02,
    )
else:  # Direct CLI execution places this script's directory on sys.path.
    import wood_joint_current_frame_material_frame_coverage_attempt02 as attempt02

ATTEMPT_ID = "current-frame-material-frame-coverage-attempt03"
SCHEMA = "wood_joint_current_frame_material_frame_coverage/v3"
ATTEMPT02_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-material-frame-coverage-attempt02"
)
REVIEW01_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-material-frame-coverage-attempt01-independent-review-2026-09-28/report.md"
)
REVIEW02_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-material-frame-coverage-attempt02-independent-review-2026-09-28/report.md"
)
ATTEMPT02_RECORD_SHA256 = "a47a447f47f95ffbf71be47112cbfffdcb6accf5446d67c4d96d03deee713a71"
ATTEMPT02_REVIEW_SHA256 = "a84586a9dbfd38cea10701fa68e158acc8675c261d436c9d8fdf45fec895d1fd"
ATTEMPT01_REVIEW_SHA256 = "254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405"
ATTEMPT02_ARTIFACTS = (
    (
        Path("scripts/wood_joint_current_frame_material_frame_coverage_attempt02.py"),
        "3ad8c5f7d940c342b62b53087b33b5249419e3fcda4edfa3d3893dccfa4e3100",
        "attempt02 producer",
    ),
    (
        Path("tests/test_wood_joint_current_frame_material_frame_coverage_attempt02.py"),
        "fdb799a31c18b0a4e4d367a7776d2be81369c7dda67a08f03ec90600e17ee3da",
        "attempt02 tests",
    ),
    (
        ATTEMPT02_DIR / "README.md",
        "20088780d4ad0ca2fb852966f3623c4858f2061871d266e23f9cb7cb3e739ae6",
        "attempt02 packet README",
    ),
    (
        ATTEMPT02_DIR / "coverage.json",
        "3cad6ee9ff8d86e80dbf6d73e642ce3982f83a04f6b0df62be8fcd750a868cb7",
        "attempt02 coverage record",
    ),
    (
        ATTEMPT02_DIR / "source-pins.json",
        "35aae532028563457d114cff1a1d402df2480ca82c1d799df430d89c20eed47d",
        "attempt02 source lineage pins",
    ),
    (
        ATTEMPT02_DIR / "SHA256SUMS",
        "a8698e4bc5766b67f810d4a3c2fffa001b8413f3d669495fceea45379fd28950",
        "attempt02 packet checksums",
    ),
    (
        REVIEW02_PATH,
        ATTEMPT02_REVIEW_SHA256,
        "attempt02 independent review finding",
    ),
)
ATTEMPT02_SUMS = {
    "scripts/wood_joint_current_frame_material_frame_coverage_attempt02.py":
        "3ad8c5f7d940c342b62b53087b33b5249419e3fcda4edfa3d3893dccfa4e3100",
    "tests/test_wood_joint_current_frame_material_frame_coverage_attempt02.py":
        "fdb799a31c18b0a4e4d367a7776d2be81369c7dda67a08f03ec90600e17ee3da",
    (
        ATTEMPT02_DIR / "README.md"
    ).as_posix(): "20088780d4ad0ca2fb852966f3623c4858f2061871d266e23f9cb7cb3e739ae6",
    (
        ATTEMPT02_DIR / "coverage.json"
    ).as_posix(): "3cad6ee9ff8d86e80dbf6d73e642ce3982f83a04f6b0df62be8fcd750a868cb7",
    (
        ATTEMPT02_DIR / "source-pins.json"
    ).as_posix(): "35aae532028563457d114cff1a1d402df2480ca82c1d799df430d89c20eed47d",
}
SCENARIO_TANGENTIAL_AXIS = {
    "ring_R_on_X": "T",
    "ring_R_on_T": "X",
}
SCENARIO_ORDER = ("ring_R_on_X", "ring_R_on_T")
TOLERANCE = 1e-8


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record_digest(record: dict[str, Any]) -> str:
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    return _sha256(_canonical_bytes(unsigned))


def _vector_matches(left: Any, right: Any, *, tolerance: float = TOLERANCE) -> bool:
    if not isinstance(left, (list, tuple)) or not isinstance(right, (list, tuple)):
        return False
    if len(left) != 3 or len(right) != 3:
        return False
    try:
        values = [(float(a), float(b)) for a, b in zip(left, right)]
    except (TypeError, ValueError):
        return False
    return all(math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance for a, b in values)


def _cross_product(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _index_unique(rows: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError(f"{label} must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError(f"{label} rows must be objects")
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} has a missing {key}")
        if value in indexed:
            raise ValueError(f"duplicate {label}: {value}")
        indexed[value] = row
    return indexed


def build_coverage(
    manifest: dict[str, Any],
    descriptor: dict[str, Any],
    timber_map: dict[str, Any],
    block_map: dict[str, Any],
) -> dict[str, Any]:
    """Rebuild attempt02 coverage and bind each tangential label to its axis."""
    coverage = attempt02.build_coverage(manifest, descriptor, timber_map, block_map)
    block_rows = _index_unique(
        block_map.get("members", []), "part_id", "candidate-block frame identities"
    )
    checked_tangents: dict[str, dict[str, tuple[str, list[float]]]] = {}
    for block_id, source in block_rows.items():
        source_axes = source.get("source_frame_axes_global_xyz")
        if not isinstance(source_axes, dict):
            raise TypeError(f"source frame axes are missing for {block_id}")
        source_cases = _index_unique(
            source.get("transverse_assignment_cases", []),
            "scenario_id",
            f"transverse scenarios for {block_id}",
        )
        if set(source_cases) != set(SCENARIO_TANGENTIAL_AXIS):
            raise ValueError(f"block transverse scenario IDs are incomplete for {block_id}")

        checked_tangents[block_id] = {}
        for scenario_id in SCENARIO_ORDER:
            source_case = source_cases[scenario_id]
            expected_axis = SCENARIO_TANGENTIAL_AXIS[scenario_id]
            if source_case.get("tangential_axis_local_name") != expected_axis:
                raise ValueError(
                    f"tangential axis label disagrees with scenario ID for {block_id}/{scenario_id}"
                )

            expected_global = source_axes.get(expected_axis)
            material_axes = source_case.get("material_axes_global_xyz")
            if not isinstance(material_axes, dict) or not all(
                axis in material_axes for axis in ("L", "R", "T")
            ):
                raise TypeError(f"material T axis is missing for {block_id}/{scenario_id}")
            tangent = material_axes["T"]
            opposite_global = [-float(value) for value in expected_global]
            if not (
                _vector_matches(tangent, expected_global)
                or _vector_matches(tangent, opposite_global)
            ):
                raise ValueError(
                    f"material T axis is not sign-equivalent to complementary source axis for {block_id}/{scenario_id}"
                )
            right_handed_tangent = _cross_product(material_axes["L"], material_axes["R"])
            if not _vector_matches(tangent, right_handed_tangent):
                raise ValueError(f"material L/R/T frame is not right-handed for {block_id}/{scenario_id}")
            checked_tangents[block_id][scenario_id] = (
                expected_axis,
                [float(value) for value in expected_global],
            )

    for member in coverage["members"]:
        if member["coverage_class"] != "candidate_block":
            continue
        block_id = member["member_id"]
        cases = member["conditional_material_frame_scenarios"]["transverse_assignments"]
        for case in cases:
            axis_name, source_axis = checked_tangents[block_id][case["scenario_id"]]
            case["tangential_axis_local_name"] = axis_name
            case["source_tangential_axis_global_xyz"] = source_axis
            case["material_T_global_xyz"] = list(case["tangential_T_global_xyz"])

    coverage["schema"] = SCHEMA
    coverage["attempt_id"] = ATTEMPT_ID
    coverage["source_scope"]["attempt02_record_sha256"] = ATTEMPT02_RECORD_SHA256
    coverage["source_scope"]["attempt02_review_path"] = REVIEW02_PATH.as_posix()
    coverage["source_scope"]["attempt02_review_sha256"] = ATTEMPT02_REVIEW_SHA256
    coverage["limits"] = list(coverage["limits"]) + [
        "Attempt03 binds each block tangential-axis label and material T vector to the complementary source axis named by the scenario ID."
    ]
    coverage["record_sha256"] = _record_digest(coverage)
    return coverage


def _authenticate_attempt02(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path, expected_sha256, role in ATTEMPT02_ARTIFACTS:
        path = repo_root / relative_path
        if not path.is_file():
            raise ValueError(f"missing pinned attempt02 artifact: {relative_path.as_posix()}")
        data = path.read_bytes()
        observed_sha256 = _sha256(data)
        if observed_sha256 != expected_sha256:
            raise ValueError(f"attempt02 artifact hash mismatch: {relative_path.as_posix()}")
        rows.append(
            {
                "path": relative_path.as_posix(),
                "sha256": observed_sha256,
                "size_bytes": len(data),
                "role": role,
            }
        )

    sums_content = (repo_root / ATTEMPT02_DIR / "SHA256SUMS").read_text(encoding="utf-8")
    observed_sums: dict[str, str] = {}
    for line in sums_content.splitlines():
        digest, separator, relative_path = line.partition("  ")
        if not separator or len(digest) != 64 or relative_path in observed_sums:
            raise ValueError("attempt02 checksum file is malformed")
        observed_sums[relative_path] = digest
    if observed_sums != ATTEMPT02_SUMS:
        raise ValueError("attempt02 checksum inventory does not match its pinned packet files")
    return rows


def _verify_source_rows(repo_root: Path, rows: list[dict[str, Any]]) -> None:
    seen_paths: set[str] = set()
    for row in rows:
        relative_path = row.get("path")
        if not isinstance(relative_path, str) or relative_path in seen_paths:
            raise ValueError("attempt02 source lineage has a missing or duplicate path")
        seen_paths.add(relative_path)
        path = repo_root / relative_path
        if not path.is_file():
            raise ValueError(f"missing inherited source file: {relative_path}")
        data = path.read_bytes()
        if len(data) != row.get("size_bytes") or _sha256(data) != row.get("sha256"):
            raise ValueError(f"inherited source hash/size mismatch: {relative_path}")


def load_pinned_sources(repo_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Authenticate both reviews, attempt02, and its full original source lineage."""
    repo_root = repo_root.resolve()
    attempt02_artifacts = _authenticate_attempt02(repo_root)
    inherited_pins, original_documents = attempt02.load_pinned_sources(repo_root)

    expected_attempt02_files = {
        "coverage.json": _canonical_bytes(original_documents["coverage"]),
        "source-pins.json": _canonical_bytes(inherited_pins),
    }
    for name, expected in expected_attempt02_files.items():
        observed = (repo_root / ATTEMPT02_DIR / name).read_bytes()
        if observed != expected:
            raise ValueError(f"attempt02 output does not reproduce from pinned sources: {name}")

    inherited_rows = list(inherited_pins["attempt01_artifacts"]) + list(
        inherited_pins["attempt01_original_sources"]
    )
    _verify_source_rows(repo_root, inherited_rows)
    complete_lineage = attempt02_artifacts + inherited_rows
    if len({row["path"] for row in complete_lineage}) != len(complete_lineage):
        raise ValueError("attempt02 and inherited source lineage paths overlap")

    coverage = build_coverage(
        original_documents["manifest"],
        original_documents["descriptor"],
        original_documents["timber_map"],
        original_documents["block_map"],
    )
    attempt01_review = next(
        row for row in inherited_pins["attempt01_artifacts"] if row["sha256"] == ATTEMPT01_REVIEW_SHA256
    )
    attempt02_review = next(
        row for row in attempt02_artifacts if row["sha256"] == ATTEMPT02_REVIEW_SHA256
    )
    source_pins: dict[str, Any] = {
        "schema": "wood_joint_current_frame_material_frame_coverage_attempt03_source_pins/v1",
        "attempt_id": ATTEMPT_ID,
        "attempt02_artifact_count": len(attempt02_artifacts),
        "inherited_source_file_count": len(inherited_rows),
        "authenticated_file_count": len(complete_lineage),
        "attempt02_artifacts": attempt02_artifacts,
        "attempt02_source_pin_sha256": _sha256(_canonical_bytes(inherited_pins)),
        "attempt02_record_sha256": ATTEMPT02_RECORD_SHA256,
        "attempt01_review": attempt01_review,
        "attempt02_review": attempt02_review,
        "inherited_source_lineage_files": inherited_rows,
        "source_lineage_files": complete_lineage,
    }
    source_pins["record_sha256"] = _record_digest(source_pins)
    return source_pins, {**original_documents, "coverage": coverage}


def _write_exclusive(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)


def produce(repo_root: Path, attempt_dir: Path, *, write: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    source_pins, documents = load_pinned_sources(repo_root)
    expected = {
        "coverage.json": _canonical_bytes(documents["coverage"]),
        "source-pins.json": _canonical_bytes(source_pins),
    }
    if write:
        for name, content in expected.items():
            _write_exclusive(attempt_dir / name, content)
        return source_pins, documents["coverage"]
    for name, content in expected.items():
        path = attempt_dir / name
        if not path.is_file() or path.read_bytes() != content:
            raise ValueError(f"generated artifact differs from verified source inputs: {path}")
    return source_pins, documents["coverage"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--attempt-dir",
        type=Path,
        default=Path(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "current-frame-material-frame-coverage-attempt03"
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="create the frozen coverage and source pins")
    mode.add_argument("--verify", action="store_true", help="rebuild and compare frozen JSON outputs")
    arguments = parser.parse_args()
    attempt_dir = arguments.attempt_dir
    if not attempt_dir.is_absolute():
        attempt_dir = arguments.repo_root / attempt_dir
    try:
        source_pins, coverage = produce(arguments.repo_root.resolve(), attempt_dir, write=arguments.write)
    except (OSError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "result": "PASS_TANGENTIAL_AXIS_BOUND_CONDITIONAL_MATERIAL_FRAME_COVERAGE_ONLY",
                "attempt02_artifact_count": source_pins["attempt02_artifact_count"],
                "inherited_source_file_count": source_pins["inherited_source_file_count"],
                "authenticated_file_count": source_pins["authenticated_file_count"],
                "body_count": len(coverage["members"]),
                "record_sha256": coverage["record_sha256"],
                "readiness": coverage["readiness"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
