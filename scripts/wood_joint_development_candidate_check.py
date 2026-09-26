"""Rebuild and round-trip export the owner-reviewed WJ24 development candidate.

This is a source/geometry integration check. It does not run mechanics or
change candidate authority, selection, or release status. STEP files are
written only to a temporary directory.
"""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_CANDIDATE = "compact-floor-flush-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CONTRACT_COUNTS = {
    "candidate_blocks": 24,
    "candidate_bolt_axes": 92,
    "panel_kicker_screw_axes": 66,
    "starting_frame_bolts": 12,
}
EXPECTED_GEOMETRY_COUNTS = {
    "candidate_parts": 24,
    "candidate_bolt_axes": 92,
    "panel_kicker_screw_axes": 66,
    "retained_frame_bolts": 12,
}
SCENE_AND_BUILD_FALSE_FLAGS = {
    "candidate_accepted",
    "source_cutting_released",
    "drilling_released",
    "fabrication_released",
    "structural_accepted",
    "assembly_proven",
}


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_false_flags(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} must contain exactly {sorted(expected)}")
    if any(flag is not False for flag in value.values()):
        raise ValueError(f"{label} must remain false for this development candidate")


def validate_candidate_package(root: Path = ROOT) -> dict[str, Any]:
    """Verify owner-reviewed revision identity, source hashes, and open gates."""
    root = Path(root)
    contract = _read_json(root, "wood-joints-candidate.json")
    selected = _read_json(root, "current-candidate.json")
    if contract.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("wood-joints-candidate.json names an unexpected candidate")
    if selected.get("candidate") != EXPECTED_SELECTED_CANDIDATE:
        raise ValueError("selected-candidate authority changed unexpectedly")
    if contract.get("authority", {}).get("selected_candidate") != selected["candidate"]:
        raise ValueError("development candidate no longer identifies the selected authority")

    revision = contract.get("current_development_revision")
    if not isinstance(revision, dict) or revision.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("candidate contract does not bind the owner-reviewed revision")
    if revision.get("release") is not False:
        raise ValueError("owner-reviewed development revision must remain unreleased")
    for field, expected in EXPECTED_CONTRACT_COUNTS.items():
        if revision.get(field) != expected:
            raise ValueError(f"candidate contract has an unexpected {field} count")

    report_path = revision.get("report")
    if not isinstance(report_path, str):
        raise TypeError("candidate contract must identify its reviewed geometry report")
    report = _read_json(root, report_path)
    if report.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("review report describes a different geometry revision")
    if report.get("status") != "unaccepted_viewer_geometry_revision":
        raise ValueError("review report status changed unexpectedly")

    scene_path = "site/owner-wood-joints-wj24-scene.json"
    scene = _read_json(root, scene_path)
    source_binding = scene.get("source_binding")
    counts = scene.get("counts")
    if not isinstance(source_binding, dict) or not isinstance(counts, dict):
        raise TypeError("review scene lacks source-binding or quantity records")
    if scene.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("review scene candidate identity differs from its contract")
    if scene.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("review scene revision differs from its contract")
    if source_binding.get("revision_report_sha256") != _sha256(root / report_path):
        raise ValueError("review scene report fingerprint is stale")
    inventory_path = "docs/wood-joints-mvp/source-inventory.json"
    if source_binding.get("source_inventory_sha256") != _sha256(root / inventory_path):
        raise ValueError("review scene source-inventory fingerprint is stale")

    expected_scene_counts = {
        "candidate_parts": EXPECTED_CONTRACT_COUNTS["candidate_blocks"],
        "candidate_bores": EXPECTED_CONTRACT_COUNTS["candidate_bolt_axes"],
        "candidate_installed_hardware_axes": EXPECTED_CONTRACT_COUNTS["candidate_bolt_axes"],
        "panel_screw_axes_total": EXPECTED_CONTRACT_COUNTS["panel_kicker_screw_axes"],
        "retained_frame_bolts": EXPECTED_CONTRACT_COUNTS["starting_frame_bolts"],
        "fixed_panel_axes": 58,
        "moved_panel_axes": 8,
    }
    for field, expected in expected_scene_counts.items():
        if counts.get(field) != expected:
            raise ValueError(f"review scene has an unexpected {field} count")

    candidate_false_flags = {
        "layout_complete",
        "engineering_mvp_complete",
        "physical_prototype_complete",
        "geometry_accepted",
        "drilling_released",
        "fabrication_released",
        "structural_released",
        "climbing_released",
    }
    _require_false_flags(
        contract.get("release_flags"), candidate_false_flags, "candidate release flags"
    )
    _require_false_flags(
        scene.get("release"), SCENE_AND_BUILD_FALSE_FLAGS, "scene release flags"
    )
    return {
        "candidate": EXPECTED_CANDIDATE,
        "selected_candidate_preserved": EXPECTED_SELECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "review_report_sha256": _sha256(root / report_path),
        "source_inventory_sha256": _sha256(root / inventory_path),
        "counts": expected_scene_counts,
        "release_flags_false": True,
    }


def _shape(value: Any) -> Any:
    shape = getattr(value, "shape", value)
    if hasattr(shape, "val"):
        shape = shape.val()
    return shape


def check_candidate_exports(root: Path = ROOT) -> dict[str, Any]:
    """Rebuild current geometry and verify temporary STEP round trips."""
    print("checking reviewed candidate identity and source fingerprints", flush=True)
    package = validate_candidate_package(root)
    from cadquery import exporters, importers

    from scripts.wood_joint_current_geometry import build_current_geometry

    print("rebuilding owner-reviewed current geometry", flush=True)
    geometry, report = build_current_geometry(
        progress=lambda step: print(f"rebuilding {step}", flush=True)
    )
    print("geometry rebuild complete; checking STEP round trips", flush=True)
    if getattr(geometry, "layout_id", None) != EXPECTED_REVISION:
        raise ValueError("geometry builder returned a different candidate revision")
    if report.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("geometry construction report describes a different revision")

    parts = getattr(geometry, "finished_candidate_parts", None)
    if not isinstance(parts, Mapping) or len(parts) != EXPECTED_GEOMETRY_COUNTS["candidate_parts"]:
        raise ValueError("rebuilt geometry does not contain the 24 reviewed candidate parts")
    actual_counts = {
        "candidate_parts": len(parts),
        "candidate_bolt_axes": len(getattr(geometry, "candidate_bores", {})),
        "panel_kicker_screw_axes": len(getattr(geometry, "fixed_axes", {})),
        "retained_frame_bolts": len(getattr(geometry, "frame_bolt_records", [])),
    }
    if actual_counts != EXPECTED_GEOMETRY_COUNTS:
        raise ValueError(f"rebuilt geometry counts differ from the reviewed revision: {actual_counts}")
    release = report.get("release")
    _require_false_flags(
        release,
        SCENE_AND_BUILD_FALSE_FLAGS,
        "rebuilt geometry report release flags",
    )

    exports = []
    with tempfile.TemporaryDirectory(prefix="wood-joint-candidate-step-") as directory:
        temp_root = Path(directory)
        for index, (part_id, value) in enumerate(sorted(parts.items()), start=1):
            print(f"STEP round trip {index}/{len(parts)}: {part_id}", flush=True)
            source_shape = _shape(value)
            if not source_shape.isValid() or source_shape.Volume() <= 0:
                raise ValueError(f"candidate part {part_id} is invalid or has no volume")
            token = hashlib.sha256(str(part_id).encode()).hexdigest()[:16]
            destination = temp_root / f"{token}.step"
            exporters.export(source_shape, str(destination))
            if not destination.is_file() or destination.stat().st_size == 0:
                raise ValueError(f"candidate part {part_id} did not produce a STEP export")
            imported_shape = importers.importStep(str(destination)).val()
            if (
                not imported_shape.isValid()
                or len(source_shape.Solids()) != len(imported_shape.Solids())
            ):
                raise ValueError(f"candidate part {part_id} topology changed in STEP round trip")
            source_bounds = source_shape.BoundingBox()
            exported_bounds = imported_shape.BoundingBox()
            source_dimensions = (source_bounds.xlen, source_bounds.ylen, source_bounds.zlen)
            exported_dimensions = (exported_bounds.xlen, exported_bounds.ylen, exported_bounds.zlen)
            if not math.isclose(
                source_shape.Volume(), imported_shape.Volume(), rel_tol=1e-8, abs_tol=1e-4
            ):
                raise ValueError(f"candidate part {part_id} volume changed in STEP round trip")
            if any(
                abs(source - exported) > 1e-5
                for source, exported in zip(source_dimensions, exported_dimensions, strict=True)
            ):
                raise ValueError(f"candidate part {part_id} bounds changed in STEP round trip")
            exports.append(
                {
                    "part_id": part_id,
                    "step_sha256": _sha256(destination),
                    "volume_mm3": source_shape.Volume(),
                    "solid_count": len(source_shape.Solids()),
                }
            )
    return {
        **package,
        "rebuilt_geometry_counts": actual_counts,
        "round_trip_step_parts": len(exports),
        "step_exports": exports,
        "claim_limit": (
            "Source-bound development geometry and STEP round-trip integrity only; "
            "no capacity, assembly, fabrication, or release is established."
        ),
    }


def main() -> None:
    result = check_candidate_exports()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
