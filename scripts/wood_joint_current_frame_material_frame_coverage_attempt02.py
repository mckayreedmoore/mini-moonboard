#!/usr/bin/env python3
"""Bind each block transverse scenario label to its named source radial axis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

if __package__:
    from scripts import (
        wood_joint_current_frame_material_frame_coverage_attempt01 as attempt01,
    )
else:  # Direct CLI execution places this script's directory on sys.path.
    import wood_joint_current_frame_material_frame_coverage_attempt01 as attempt01

ATTEMPT_ID = "current-frame-material-frame-coverage-attempt02"
SCHEMA = "wood_joint_current_frame_material_frame_coverage/v2"
ATTEMPT01_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-material-frame-coverage-attempt01"
)
REVIEW_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-material-frame-coverage-attempt01-independent-review-2026-09-28/report.md"
)
ATTEMPT01_ARTIFACTS = (
    (
        Path("scripts/wood_joint_current_frame_material_frame_coverage_attempt01.py"),
        "90672d9544c9ba29adaacbb32f4c00ed926e0e55b8038f51dddeee0fa3122865",
        "attempt01 producer",
    ),
    (
        Path("tests/test_wood_joint_current_frame_material_frame_coverage_attempt01.py"),
        "a97a3a42c306b47d3c07c664cf32fb58dc7742999e39b84ebba3bfd201e799fe",
        "attempt01 tests",
    ),
    (
        ATTEMPT01_DIR / "README.md",
        "56ad116ed9f9d3a25239b5dd71ea830c0eeca0cc00c90d1df8ee4889c582b511",
        "attempt01 packet README",
    ),
    (
        ATTEMPT01_DIR / "coverage.json",
        "569f7e61bcd402f97c85be63eb5457428e579b70f5e3b2f2abfe5e49aadb3265",
        "attempt01 coverage record",
    ),
    (
        ATTEMPT01_DIR / "source-pins.json",
        "50f82483f744df809b33e5317788d3aadb6896df1ce3b2ea070bbb3c5ef31ad3",
        "attempt01 original source pins",
    ),
    (
        ATTEMPT01_DIR / "SHA256SUMS",
        "56ec16ebbf5e6f319676fe348b477cdf9f40d05bf7628cb676bba0c07a02a29b",
        "attempt01 packet checksums",
    ),
    (
        REVIEW_PATH,
        "254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405",
        "attempt01 independent review finding",
    ),
)
SCENARIO_RADIAL_AXIS = {
    "ring_R_on_X": "X",
    "ring_R_on_T": "T",
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


def _index_unique(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} has a missing {key}")
        if value in indexed:
            raise ValueError(f"duplicate {label}: {value}")
        indexed[value] = row
    return indexed


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


def _validate_radial_case(
    block_id: str,
    source_axes: dict[str, Any],
    source_case: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = source_case.get("scenario_id")
    expected_axis = SCENARIO_RADIAL_AXIS.get(scenario_id)
    if expected_axis is None:
        raise ValueError(f"unsupported block transverse scenario ID for {block_id}: {scenario_id}")
    if source_case.get("radial_axis_local_name") != expected_axis:
        raise ValueError(f"radial axis label disagrees with scenario ID for {block_id}/{scenario_id}")

    material_axes = source_case.get("material_axes_global_xyz")
    if not isinstance(material_axes, dict) or not isinstance(material_axes.get("R"), list):
        raise TypeError(f"material R axis is missing for {block_id}/{scenario_id}")
    expected_global = source_axes.get(expected_axis)
    if not _vector_matches(material_axes["R"], expected_global):
        raise ValueError(f"radial R axis disagrees with scenario label for {block_id}/{scenario_id}")

    points = source_case.get("calculix_orientation_points_global_xyz")
    if not isinstance(points, list) or len(points) != 6:
        raise ValueError(f"CalculiX orientation points are invalid for {block_id}/{scenario_id}")
    radial_point = points[3:6]
    if not _vector_matches(radial_point, expected_global):
        raise ValueError(f"CalculiX radial point disagrees with source axis for {block_id}/{scenario_id}")
    if not _vector_matches(radial_point, material_axes["R"]):
        raise ValueError(f"CalculiX radial point disagrees with material R axis for {block_id}/{scenario_id}")

    checked_axes = {
        axis: list(material_axes[axis])
        for axis in ("L", "R", "T")
    }
    return {
        "scenario_id": scenario_id,
        "radial_axis_local_name": expected_axis,
        "source_radial_axis_global_xyz": list(expected_global),
        "longitudinal_L_global_xyz": checked_axes["L"],
        "material_R_global_xyz": checked_axes["R"],
        "tangential_T_global_xyz": checked_axes["T"],
        "tangential_axis_local_name": source_case.get("tangential_axis_local_name"),
        "calculix_orientation_points_global_xyz": [float(value) for value in points],
        "proposal_only": source_case.get("proposal_only") is True,
    }


def build_coverage(
    manifest: dict[str, Any],
    descriptor: dict[str, Any],
    timber_map: dict[str, Any],
    block_map: dict[str, Any],
) -> dict[str, Any]:
    """Rebuild attempt01 coverage and bind every block scenario to its radial label."""
    block_source_rows = _index_unique(
        block_map.get("members", []), "part_id", "candidate-block frame identities"
    )
    checked_cases_by_block: dict[str, list[dict[str, Any]]] = {}
    for block_id, source in block_source_rows.items():
        source_axes = source["source_frame_axes_global_xyz"]
        source_cases = source["transverse_assignment_cases"]
        by_id = _index_unique(source_cases, "scenario_id", f"transverse scenarios for {block_id}")
        if set(by_id) != set(SCENARIO_RADIAL_AXIS):
            raise ValueError(f"block transverse scenario IDs are incomplete for {block_id}")
        checked_cases_by_block[block_id] = [
            _validate_radial_case(block_id, source_axes, by_id[scenario_id])
            for scenario_id in SCENARIO_ORDER
        ]

    coverage = attempt01.build_coverage(manifest, descriptor, timber_map, block_map)
    for member in coverage["members"]:
        if member["coverage_class"] != "candidate_block":
            continue
        block_id = member["member_id"]
        member["conditional_material_frame_scenarios"]["transverse_assignments"] = (
            checked_cases_by_block[block_id]
        )

    coverage["schema"] = SCHEMA
    coverage["attempt_id"] = ATTEMPT_ID
    coverage["source_scope"]["attempt01_record_sha256"] = _record_digest(
        attempt01.build_coverage(manifest, descriptor, timber_map, block_map)
    )
    coverage["source_scope"]["attempt01_review_path"] = REVIEW_PATH.as_posix()
    coverage["source_scope"]["attempt01_review_sha256"] = ATTEMPT01_ARTIFACTS[-1][1]
    coverage["limits"] = list(coverage["limits"]) + [
        "Attempt02 binds each block case ID to its declared source radial axis, material R axis, and CalculiX radial orientation point."
    ]
    coverage["record_sha256"] = _record_digest(coverage)
    return coverage


def _authenticate_attempt01(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path, expected_sha256, role in ATTEMPT01_ARTIFACTS:
        path = repo_root / relative_path
        if not path.is_file():
            raise ValueError(f"missing pinned attempt01 artifact: {relative_path.as_posix()}")
        data = path.read_bytes()
        observed_sha256 = _sha256(data)
        if observed_sha256 != expected_sha256:
            raise ValueError(f"attempt01 artifact hash mismatch: {relative_path.as_posix()}")
        rows.append(
            {
                "path": relative_path.as_posix(),
                "sha256": observed_sha256,
                "size_bytes": len(data),
                "role": role,
            }
        )

    sums_path = repo_root / ATTEMPT01_DIR / "SHA256SUMS"
    expected_sums = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative_path = line.partition("  ")
        if not separator or len(digest) != 64 or relative_path in expected_sums:
            raise ValueError("attempt01 checksum file is malformed")
        expected_sums[relative_path] = digest
    pinned_sum_inputs = {
        relative_path.as_posix(): expected_sha256
        for relative_path, expected_sha256, _ in ATTEMPT01_ARTIFACTS
        if relative_path.as_posix() not in {ATTEMPT01_DIR.joinpath("SHA256SUMS").as_posix(), REVIEW_PATH.as_posix()}
    }
    if expected_sums != pinned_sum_inputs:
        raise ValueError("attempt01 checksum inventory does not match its pinned packet files")
    return rows


def load_pinned_sources(repo_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Authenticate attempt01 and its review, then recheck all original inputs."""
    repo_root = repo_root.resolve()
    attempt01_artifacts = _authenticate_attempt01(repo_root)
    original_pins, original_documents = attempt01.load_pinned_sources(repo_root)

    rebuilt_attempt01_coverage = attempt01.build_coverage(
        original_documents["manifest"],
        original_documents["descriptor"],
        original_documents["timber_map"],
        original_documents["block_map"],
    )
    expected_attempt01_files = {
        "coverage.json": _canonical_bytes(rebuilt_attempt01_coverage),
        "source-pins.json": _canonical_bytes(original_pins),
    }
    for name, expected in expected_attempt01_files.items():
        observed = (repo_root / ATTEMPT01_DIR / name).read_bytes()
        if observed != expected:
            raise ValueError(f"attempt01 output does not reproduce from pinned original sources: {name}")

    coverage = build_coverage(
        original_documents["manifest"],
        original_documents["descriptor"],
        original_documents["timber_map"],
        original_documents["block_map"],
    )
    original_files = list(original_pins["pinned_json_inputs"]) + list(
        original_pins["exact_current_step_files"]
    )
    source_pins: dict[str, Any] = {
        "schema": "wood_joint_current_frame_material_frame_coverage_attempt02_source_pins/v1",
        "attempt_id": ATTEMPT_ID,
        "attempt01_artifact_count": len(attempt01_artifacts),
        "original_source_file_count": len(original_files),
        "authenticated_file_count": len(attempt01_artifacts) + len(original_files),
        "attempt01_artifacts": attempt01_artifacts,
        "attempt01_original_source_pin_sha256": _sha256(
            _canonical_bytes(original_pins)
        ),
        "attempt01_original_sources": original_files,
        "attempt01_independent_review": {
            "path": REVIEW_PATH.as_posix(),
            "sha256": ATTEMPT01_ARTIFACTS[-1][1],
            "finding": "block transverse scenario IDs were not bound to their named source radial axes",
        },
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
            "current-frame-material-frame-coverage-attempt02"
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="create coverage.json and source-pins.json exclusively")
    mode.add_argument("--verify", action="store_true", help="rebuild in memory and compare frozen JSON outputs")
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
                "result": "PASS_AXIS_BOUND_CONDITIONAL_MATERIAL_FRAME_COVERAGE_ONLY",
                "authenticated_file_count": source_pins["authenticated_file_count"],
                "attempt01_artifact_count": source_pins["attempt01_artifact_count"],
                "original_source_file_count": source_pins["original_source_file_count"],
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
