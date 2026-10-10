#!/usr/bin/env python3
"""Build a source-bound, conditional material-frame coverage record.

This offline adapter joins existing orientation scenarios to the current
attempt04 STEP inventory. It does not assign material properties or solver
identities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ATTEMPT_ID = "current-frame-material-frame-coverage-attempt01"
SCHEMA = "wood_joint_current_frame_material_frame_coverage/v1"
GEOMETRY_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
CANDIDATE = "compact-floor-flush-wood-joints-development"

BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
DESCRIPTOR_DIR = BASE / "current-full-frame-member-solids-attempt01"
INPUTS = {
    "manifest": (
        BASE / "current-full-frame-input-manifest-attempt04"
        / "current-full-frame-input-manifest.json",
        "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
        "Exact current-revision 50-body inventory and STEP bindings",
    ),
    "descriptor": (
        DESCRIPTOR_DIR / "bundle/current-full-frame-member-solids.json",
        "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
        "Exact 50-body STEP bundle descriptor",
    ),
    "timber_map": (
        BASE / "current-frame-timber-material-frame-map-attempt01"
        / "current-frame-timber-material-frame-map.json",
        "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
        "Conditional longitudinal orientation scenarios for 20 frame timbers",
    ),
    "block_map": (
        BASE / "current-block-material-frame-map-attempt02"
        / "material-frame-map.json",
        "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
        "Conditional grain and transverse scenarios for 24 connector blocks",
    ),
}

TOLERANCE = 1e-8
PANEL_UNRESOLVED_STATUS = "unresolved_product_and_sheet_axis"
BLOCK_FRAME_METHODS = {
    "source-axis frame plus saved exact-solid proper-rigid transform",
    "current geometry source builder's global-axis Solid.makeBox construction",
    "pinned WJ04 trial frame and source-bound upper-G7 builder datum",
}
FALSE_READINESS = {
    "candidate_accepted": False,
    "full_frame_material_mapping_ready": False,
    "inputs_ready": False,
    "launch_ready": False,
    "native_solve_ready": False,
}
FALSE_ACCEPTANCE = {
    "candidate_accepted": False,
    "criterion_resolved": False,
}
FALSE_NATIVE = {"executed": False}
FALSE_RELEASE = {
    "climbing_released": False,
    "drilling_released": False,
    "engineering_mvp_complete": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record_digest(record: dict[str, Any], digest_field: str) -> str:
    unsigned = dict(record)
    unsigned.pop(digest_field, None)
    return _sha256(_canonical_bytes(unsigned))


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


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


def _close(left: float, right: float, tolerance: float = TOLERANCE) -> bool:
    return math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance


def _vector(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"invalid three-vector in {label}")
    vector = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in vector):
        raise ValueError(f"non-finite three-vector in {label}")
    return vector  # type: ignore[return-value]


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _vector_matches(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
    *,
    sign_equivalent: bool = False,
) -> bool:
    direct = all(_close(a, b) for a, b in zip(left, right))
    if direct or not sign_equivalent:
        return direct
    return all(_close(a, -b) for a, b in zip(left, right))


def _basis(axes: dict[str, Any], label: str) -> dict[str, tuple[float, float, float]]:
    if set(axes) != {"X", "T", "N"}:
        raise ValueError(f"source frame has incomplete axes in {label}")
    vectors = {axis: _vector(axes[axis], f"{label}.{axis}") for axis in ("X", "T", "N")}
    for axis, vector in vectors.items():
        if not _close(_norm(vector), 1.0):
            raise ValueError(f"source frame is not orthonormal in {label}: {axis} is not unit length")
    for first, second in (("X", "T"), ("X", "N"), ("T", "N")):
        if not _close(_dot(vectors[first], vectors[second]), 0.0):
            raise ValueError(f"source frame is not orthonormal in {label}: {first}/{second}")
    if not _vector_matches(_cross(vectors["X"], vectors["T"]), vectors["N"]):
        raise ValueError(f"source frame is not right-handed in {label}")
    return vectors


def _check_timber_row(row: dict[str, Any]) -> dict[str, Any]:
    member_id = row["member_id"]
    label = f"frame timber {member_id}"
    frame = row.get("source_frame")
    assignment = row.get("conditional_grain_assignment")
    if not isinstance(frame, dict) or not isinstance(assignment, dict):
        raise TypeError(f"missing conditional source frame in {label}")
    if frame.get("basis_order") != ["X", "T", "N"]:
        raise ValueError(f"unexpected source frame basis order in {label}")
    axes = _basis(frame.get("axes_global_xyz", {}), label)
    if frame.get("right_handed") is not True or frame.get("unit_axes") is not True:
        raise ValueError(f"source frame flags do not certify a basis in {label}")

    transform = frame.get("local_to_global_transform")
    if not isinstance(transform, list) or len(transform) != 4 or any(
        not isinstance(line, list) or len(line) != 4 for line in transform
    ):
        raise ValueError(f"invalid local-to-global transform in {label}")
    for column, axis in enumerate(("X", "T", "N")):
        transformed_axis = tuple(float(transform[row_index][column]) for row_index in range(3))
        if not _vector_matches(transformed_axis, axes[axis]):
            raise ValueError(f"transform and source axes disagree in {label}")
    if not all(_close(float(transform[3][column]), target) for column, target in enumerate((0, 0, 0, 1))):
        raise ValueError(f"invalid homogeneous transform in {label}")

    local = assignment.get("proposed_source_local_xyz")
    if not isinstance(local, dict) or set(local) != {"X", "T", "N"}:
        raise ValueError(f"missing conditional grain components in {label}")
    local_vector = tuple(float(local[axis]) for axis in ("X", "T", "N"))
    if not all(math.isfinite(component) for component in local_vector) or not _close(_norm(local_vector), 1.0):
        raise ValueError(f"invalid conditional grain components in {label}")
    reconstructed = tuple(
        sum(axes[axis][component] * float(local[axis]) for axis in ("X", "T", "N"))
        for component in range(3)
    )
    proposed_global = _vector(assignment.get("proposed_global_xyz"), label + " grain")
    if not _vector_matches(reconstructed, proposed_global, sign_equivalent=assignment.get("sign_equivalent") is True):
        raise ValueError(f"conditional grain components do not reconstruct in {label}")
    if assignment.get("delivered_stock_observed") is not False:
        raise ValueError(f"conditional grain scenario is not marked unobserved in {label}")

    lineage = row.get("current_geometry_lineage")
    if not isinstance(lineage, dict):
        raise TypeError(f"missing current STEP lineage in {label}")
    return {
        "axes": axes,
        "grain_direction": proposed_global,
        "grain_axis": assignment.get("longitudinal_material_axis"),
        "grain_components": {axis: float(local[axis]) for axis in ("X", "T", "N")},
        "lineage": lineage,
        "orientation_status": assignment.get("status"),
        "transverse_ring_axes_status": row.get("transverse_ring_axes", {}).get("status"),
    }


def _check_block_row(row: dict[str, Any]) -> dict[str, Any]:
    part_id = row["part_id"]
    label = f"candidate block {part_id}"
    axes = _basis(row.get("source_frame_axes_global_xyz", {}), label)
    assignment = row.get("conditional_grain_assignment")
    if not isinstance(assignment, dict) or assignment.get("delivered_stock_observed") is not False:
        raise ValueError(f"block grain scenario is not marked unobserved in {label}")
    grain = _vector(assignment.get("grain_direction_global_xyz"), label + " grain")
    if assignment.get("source_axis_name") != "N" or not _vector_matches(grain, axes["N"], sign_equivalent=True):
        raise ValueError(f"block grain scenario disagrees with source N axis in {label}")
    scenarios = row.get("transverse_assignment_cases")
    if not isinstance(scenarios, list) or len(scenarios) != 2:
        raise ValueError(f"block must retain two transverse scenarios in {label}")
    scenario_ids: set[str] = set()
    checked_scenarios = []
    for scenario in scenarios:
        scenario_id = scenario.get("scenario_id")
        if scenario_id not in {"ring_R_on_X", "ring_R_on_T"} or scenario_id in scenario_ids:
            raise ValueError(f"unexpected or duplicate transverse scenario in {label}")
        scenario_ids.add(scenario_id)
        if scenario.get("proposal_only") is not True or scenario.get("right_handed") is not True:
            raise ValueError(f"block transverse scenario is not conditional in {label}")
        material_axes_raw = scenario.get("material_axes_global_xyz")
        if not isinstance(material_axes_raw, dict) or set(material_axes_raw) != {"L", "R", "T"}:
            raise ValueError(f"invalid material orientation scenario in {label}")
        material_axes = {
            name: _vector(material_axes_raw[name], f"{label}.{scenario_id}.{name}")
            for name in ("L", "R", "T")
        }
        for vector in material_axes.values():
            if not _close(_norm(vector), 1.0):
                raise ValueError(f"material orientation scenario is not orthonormal in {label}")
        for first, second in (("L", "R"), ("L", "T"), ("R", "T")):
            if not _close(_dot(material_axes[first], material_axes[second]), 0.0):
                raise ValueError(f"material orientation scenario is not orthonormal in {label}")
        if not _vector_matches(_cross(material_axes["L"], material_axes["R"]), material_axes["T"]):
            raise ValueError(f"material orientation scenario is not right-handed in {label}")
        if not _vector_matches(material_axes["L"], grain):
            raise ValueError(f"material L axis disagrees with conditional grain in {label}")
        orientation_points = scenario.get("calculix_orientation_points_global_xyz")
        if not isinstance(orientation_points, list) or len(orientation_points) != 6:
            raise ValueError(f"missing orientation points in {label}")
        if not _vector_matches(_vector(orientation_points[:3], label), material_axes["L"]):
            raise ValueError(f"orientation points disagree with L axis in {label}")
        if not _vector_matches(_vector(orientation_points[3:], label), material_axes["R"]):
            raise ValueError(f"orientation points disagree with R axis in {label}")
        checked_scenarios.append(
            {
                "scenario_id": scenario_id,
                "longitudinal_L_global_xyz": list(material_axes["L"]),
                "radial_R_global_xyz": list(material_axes["R"]),
                "tangential_T_global_xyz": list(material_axes["T"]),
                "proposal_only": True,
            }
        )
    if scenario_ids != {"ring_R_on_X", "ring_R_on_T"}:
        raise ValueError(f"block transverse scenario set is incomplete in {label}")
    frame_binding = row.get("frame_binding")
    if not isinstance(frame_binding, dict) or frame_binding.get("method") not in BLOCK_FRAME_METHODS:
        raise ValueError(f"block frame lineage is incomplete in {label}")
    return {
        "axes": axes,
        "grain_direction": grain,
        "grain_axis": assignment.get("longitudinal_material_axis"),
        "grain_source_axis_name": assignment.get("source_axis_name"),
        "frame_binding_method": frame_binding["method"],
        "orientation_status": "conditional_source_orientation_scenario_not_observed_stock",
        "scenarios": checked_scenarios,
    }


def _material_and_solver_nulls() -> tuple[dict[str, None], dict[str, None]]:
    return (
        {
            "density": None,
            "elastic_properties": None,
            "grade": None,
            "material_id": None,
            "species_group": None,
        },
        {"body_id": None, "dof_ids": None, "element_ids": None, "node_ids": None},
    )


def build_coverage(
    manifest: dict[str, Any],
    descriptor: dict[str, Any],
    timber_map: dict[str, Any],
    block_map: dict[str, Any],
) -> dict[str, Any]:
    """Validate source identities and compile their conditional frame scenarios."""
    if manifest.get("candidate") != CANDIDATE or any(
        document.get("geometry_revision_id") != GEOMETRY_REVISION_ID
        for document in (manifest, timber_map, block_map)
    ):
        raise ValueError("candidate or geometry revision mismatch")
    if any(document.get("candidate") != CANDIDATE for document in (timber_map, block_map)):
        raise ValueError("orientation map candidate mismatch")

    bindings = _index_unique(
        manifest.get("finished_member_step_bindings", []), "member_id", "attempt04 STEP identities"
    )
    descriptor_rows = _index_unique(descriptor.get("members", []), "member_id", "STEP descriptor identities")
    if set(bindings) != set(descriptor_rows):
        raise ValueError("attempt04 STEP identities do not match descriptor identities")
    if len(bindings) != 50 or len(descriptor_rows) != 50:
        raise ValueError("expected exact 50-body attempt04 inventory")

    descriptor_base = DESCRIPTOR_DIR.as_posix()
    for member_id, binding in bindings.items():
        descriptor_row = descriptor_rows[member_id]
        expected_path = f"{descriptor_base}/{descriptor_row.get('step_file')}"
        identity_pairs = (
            (binding.get("member_kind"), descriptor_row.get("member_kind")),
            (binding.get("path"), expected_path),
            (binding.get("file_sha256"), descriptor_row.get("step_sha256")),
            (binding.get("size_bytes"), descriptor_row.get("step_size_bytes")),
            (binding.get("shape_summary_sha256"), descriptor_row.get("shape_summary_sha256")),
            (binding.get("source_shape_fingerprint_sha256"), descriptor_row.get("source_shape_fingerprint_sha256")),
        )
        if any(left != right for left, right in identity_pairs):
            raise ValueError(f"STEP identity mismatch for {member_id}")

    expected_counts = {"timber": 20, "candidate_block": 24, "plywood_panel": 6}
    observed_counts: dict[str, int] = {}
    for row in bindings.values():
        kind = row.get("member_kind")
        observed_counts[kind] = observed_counts.get(kind, 0) + 1
    if observed_counts != expected_counts:
        raise ValueError(f"attempt04 STEP kind counts mismatch: {observed_counts}")

    physical = _index_unique(manifest.get("physical_members", []), "member_id", "physical member identities")
    if set(physical) != set(bindings) or len(physical) != 50:
        raise ValueError("physical member identities do not match attempt04 STEP identities")
    candidate_blocks = _index_unique(manifest.get("candidate_blocks", []), "part_id", "manifest candidate-block identities")
    block_ids = {member_id for member_id, row in bindings.items() if row["member_kind"] == "candidate_block"}
    timber_ids = {member_id for member_id, row in bindings.items() if row["member_kind"] == "timber"}
    panel_ids = {member_id for member_id, row in bindings.items() if row["member_kind"] == "plywood_panel"}
    if set(candidate_blocks) != block_ids or len(candidate_blocks) != 24:
        raise ValueError("manifest candidate-block identities do not match STEP identities")

    timber_rows = _index_unique(timber_map.get("members", []), "member_id", "frame-timber identities")
    block_rows = _index_unique(block_map.get("members", []), "part_id", "candidate-block frame identities")
    if set(timber_rows) != timber_ids:
        raise ValueError("frame-timber identities do not match attempt04 timber identities")
    if set(block_rows) != block_ids:
        raise ValueError("candidate-block frame identities do not match attempt04 block identities")

    materials_null, solver_null = _material_and_solver_nulls()
    entries: list[dict[str, Any]] = []
    for member_id in sorted(bindings):
        binding = bindings[member_id]
        member_kind = binding["member_kind"]
        base_entry: dict[str, Any] = {
            "member_id": member_id,
            "member_kind": member_kind,
            "current_step": {
                "path": binding["path"],
                "sha256": binding["file_sha256"],
                "size_bytes": binding["size_bytes"],
                "shape_summary_sha256": binding["shape_summary_sha256"],
                "source_shape_fingerprint_sha256": binding["source_shape_fingerprint_sha256"],
            },
            "material_assignment": dict(materials_null),
            "solver_mapping": dict(solver_null),
        }
        if member_kind == "timber":
            source = timber_rows[member_id]
            checked = _check_timber_row(source)
            lineage = checked["lineage"]
            if any(
                lineage.get(source_key) != binding.get(binding_key)
                for source_key, binding_key in (
                    ("step_file", "path"),
                    ("step_sha256", "file_sha256"),
                    ("step_size_bytes", "size_bytes"),
                    ("shape_summary_sha256", "shape_summary_sha256"),
                    ("source_shape_fingerprint_sha256", "source_shape_fingerprint_sha256"),
                )
            ):
                raise ValueError(f"frame-timber STEP lineage mismatch for {member_id}")
            base_entry.update(
                {
                    "coverage_class": "frame_timber",
                    "orientation_status": checked["orientation_status"],
                    "orientation_source": {
                        "path": INPUTS["timber_map"][0].as_posix(),
                        "sha256": INPUTS["timber_map"][1],
                    },
                    "conditional_material_frame_scenarios": {
                        "source_frame_axes_global_xyz": {
                            axis: list(checked["axes"][axis]) for axis in ("X", "T", "N")
                        },
                        "longitudinal_axis": checked["grain_axis"],
                        "longitudinal_direction_global_xyz": list(checked["grain_direction"]),
                        "longitudinal_components_in_source_frame_xyz": checked["grain_components"],
                        "transverse_ring_axes_status": checked["transverse_ring_axes_status"],
                    },
                }
            )
        elif member_kind == "candidate_block":
            source = block_rows[member_id]
            checked = _check_block_row(source)
            base_entry.update(
                {
                    "coverage_class": "candidate_block",
                    "orientation_status": checked["orientation_status"],
                    "orientation_source": {
                        "path": INPUTS["block_map"][0].as_posix(),
                        "sha256": INPUTS["block_map"][1],
                    },
                    "conditional_material_frame_scenarios": {
                        "source_frame_axes_global_xyz": {
                            axis: list(checked["axes"][axis]) for axis in ("X", "T", "N")
                        },
                        "longitudinal_axis": checked["grain_axis"],
                        "longitudinal_source_axis_name": checked["grain_source_axis_name"],
                        "longitudinal_direction_global_xyz": list(checked["grain_direction"]),
                        "source_frame_binding_method": checked["frame_binding_method"],
                        "transverse_assignments": checked["scenarios"],
                    },
                }
            )
        elif member_kind == "plywood_panel":
            base_entry.update(
                {
                    "coverage_class": "plywood_panel_unresolved",
                    "orientation_status": PANEL_UNRESOLVED_STATUS,
                    "orientation_source": None,
                    "conditional_material_frame_scenarios": None,
                }
            )
        else:
            raise ValueError(f"unsupported attempt04 member kind for {member_id}: {member_kind}")
        entries.append(base_entry)

    if {row["member_id"] for row in entries if row["coverage_class"] == "plywood_panel_unresolved"} != panel_ids:
        raise ValueError("unresolved panel identity set mismatch")
    block_frame_method_counts: dict[str, int] = {}
    for row in entries:
        if row["coverage_class"] != "candidate_block":
            continue
        method = row["conditional_material_frame_scenarios"]["source_frame_binding_method"]
        block_frame_method_counts[method] = block_frame_method_counts.get(method, 0) + 1

    coverage: dict[str, Any] = {
        "schema": SCHEMA,
        "attempt_id": ATTEMPT_ID,
        "candidate": CANDIDATE,
        "geometry_revision_id": GEOMETRY_REVISION_ID,
        "source_scope": {
            "attempt04_manifest_path": INPUTS["manifest"][0].as_posix(),
            "attempt04_manifest_sha256": INPUTS["manifest"][1],
            "exact_body_count": 50,
            "mapped_frame_timber_count": 20,
            "mapped_candidate_block_count": 24,
            "unresolved_plywood_panel_count": 6,
            "block_frame_method_counts": dict(sorted(block_frame_method_counts.items())),
            "selected_candidate_preserved": "compact-floor-flush-development",
        },
        "members": entries,
        "limits": [
            "Wood orientations are conditional source geometry/material scenarios, not observed delivered stock.",
            "The six plywood panels have no assigned layup, principal material axes, or properties.",
            "No material properties, density, product assignment, solver material, body, element, node, DOF, or load mapping is emitted.",
            "This orientation coverage does not make the full-frame model ready or establish a mechanics result.",
        ],
        "readiness": dict(FALSE_READINESS),
        "acceptance": dict(FALSE_ACCEPTANCE),
        "native_execution": dict(FALSE_NATIVE),
        "release": dict(FALSE_RELEASE),
    }
    coverage["record_sha256"] = _record_digest(coverage, "record_sha256")
    return coverage


def load_pinned_sources(repo_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Read pinned JSON inputs and authenticate every current STEP export."""
    repo_root = repo_root.resolve()
    documents: dict[str, dict[str, Any]] = {}
    pin_rows: list[dict[str, Any]] = []
    for role, (relative_path, expected_sha256, description) in INPUTS.items():
        absolute_path = repo_root / relative_path
        if not absolute_path.is_file():
            raise ValueError(f"missing pinned input: {relative_path.as_posix()}")
        data = absolute_path.read_bytes()
        observed_sha256 = _sha256(data)
        if observed_sha256 != expected_sha256:
            raise ValueError(f"pinned input hash mismatch: {relative_path.as_posix()}")
        try:
            document = json.loads(data)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid pinned JSON input: {relative_path.as_posix()}") from error
        if not isinstance(document, dict):
            raise TypeError(f"expected pinned JSON object: {relative_path.as_posix()}")
        documents[role] = document
        pin_rows.append(
            {
                "role": role,
                "path": relative_path.as_posix(),
                "sha256": observed_sha256,
                "size_bytes": len(data),
                "description": description,
            }
        )

    coverage = build_coverage(
        documents["manifest"], documents["descriptor"], documents["timber_map"], documents["block_map"]
    )
    manifest_rows = _index_unique(
        documents["manifest"]["finished_member_step_bindings"], "member_id", "attempt04 STEP identities"
    )
    step_rows: list[dict[str, Any]] = []
    for member_id in sorted(manifest_rows):
        binding = manifest_rows[member_id]
        relative_path = Path(binding["path"])
        absolute_path = (repo_root / relative_path).resolve()
        if not absolute_path.is_relative_to(repo_root):
            raise ValueError(f"STEP path leaves repository root: {relative_path.as_posix()}")
        if not absolute_path.is_file():
            raise ValueError(f"missing current STEP body: {relative_path.as_posix()}")
        data = absolute_path.read_bytes()
        observed_sha256 = _sha256(data)
        if observed_sha256 != binding["file_sha256"] or len(data) != binding["size_bytes"]:
            raise ValueError(f"STEP identity mismatch for {member_id}: file hash or size differs")
        step_rows.append(
            {
                "member_id": member_id,
                "path": relative_path.as_posix(),
                "sha256": observed_sha256,
                "size_bytes": len(data),
            }
        )

    source_pins: dict[str, Any] = {
        "schema": "wood_joint_current_frame_material_frame_coverage_source_pins/v1",
        "attempt_id": ATTEMPT_ID,
        "input_json_count": len(pin_rows),
        "current_step_count": len(step_rows),
        "authenticated_file_count": len(pin_rows) + len(step_rows),
        "pinned_json_inputs": pin_rows,
        "exact_current_step_files": step_rows,
    }
    source_pins["record_sha256"] = _record_digest(source_pins, "record_sha256")
    return source_pins, {**documents, "coverage": coverage}


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
        default=BASE / ATTEMPT_ID,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="create coverage.json and source-pins.json exclusively")
    mode.add_argument("--verify", action="store_true", help="rebuild in memory and compare frozen JSON outputs")
    arguments = parser.parse_args()
    try:
        source_pins, coverage = produce(
            arguments.repo_root.resolve(),
            arguments.attempt_dir if arguments.attempt_dir.is_absolute() else arguments.repo_root / arguments.attempt_dir,
            write=arguments.write,
        )
    except (OSError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "result": "PASS_CONDITIONAL_MATERIAL_FRAME_COVERAGE_ONLY",
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
