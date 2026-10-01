#!/usr/bin/env python3
"""Map the 20 current frame timbers to conditional source grain frames.

This reads the pinned source inventory, reviewed attempt02 manifest, and
already-exported current STEP solids. It does not rebuild CAD geometry, infer
grain from a display mesh, assign received-stock properties, or run mechanics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "current-frame-timber-material-frame-map.json"

INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt02/"
    "current-full-frame-input-manifest.json"
)
SOLID_ARTIFACT_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-member-solids-attempt01/bundle/"
    "current-full-frame-member-solids.json"
)
INVENTORY_RULE_PATH = "scripts/wood_joint_inventory.py"
SOURCE_FRAME_MODULE_PATH = "mini_moonboard/wood_joint_frame.py"
CURRENT_GEOMETRY_PATH = "scripts/wood_joint_current_geometry.py"

EXPECTED_SHA256 = {
    INVENTORY_PATH: "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    MANIFEST_PATH: "21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3",
    SOLID_ARTIFACT_PATH: "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    INVENTORY_RULE_PATH: "7e3cd529274eb61ada892fb0ad397ec7b9dcb26d3372f8df0b76c7bb06b4077e",
    SOURCE_FRAME_MODULE_PATH: "77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545",
    CURRENT_GEOMETRY_PATH: "b4ba3fdc917536d016932c356431e34ed63b9f174927d88d40e4ab6faa1686f8",
}

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_CANDIDATE = "compact-floor-flush-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_MANIFEST_ID = "current-full-frame-input-manifest-attempt02"
EXPECTED_MANIFEST_DIGEST = "1ad6b404c8658147e9d10f54daf4ebd393116c1934654f5521421dc96667e0a0"
EXPECTED_REVIEW_COMMIT = "b1e8707d"
EXPECTED_SOLID_ARTIFACT_DIGEST = "d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc"
EXPECTED_MEMBER_BUNDLE_DIGEST = "590e3d8ffc6a013ad10436def028b54b3c855688398c4bf9b30c460800fc987c"
MIN_INERTIA_AXIS_ALIGNMENT = 0.999
GEOMETRY_SUMMARY_TOLERANCE_MM = 1e-8
GEOMETRY_SUMMARY_TOLERANCE_MM3 = 1e-5


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"pinned source is missing: {relative_path}")
    return sha256_bytes(path.read_bytes())


def read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path}: expected a JSON object")
    return value


def dot(left: list[float], right: list[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def unit(vector: list[float], context: str) -> list[float]:
    if len(vector) != 3 or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"{context}: expected a finite three-vector")
    length = math.sqrt(dot(vector, vector))
    if length <= 0:
        raise ValueError(f"{context}: zero vector")
    return [value / length for value in vector]


def recorded_unit(vector: list[float], context: str) -> list[float]:
    """Validate an already-recorded unit vector without changing its values."""
    if len(vector) != 3 or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"{context}: expected a finite three-vector")
    length = math.sqrt(dot(vector, vector))
    if abs(length - 1.0) > 1e-8:
        raise ValueError(f"{context}: recorded direction is not unit length")
    return vector


def determinant(matrix: list[list[float]]) -> float:
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def source_frame(row: dict[str, Any], member_id: str) -> tuple[dict[str, list[float]], list[list[float]]]:
    axes_raw = row.get("local_axes")
    transform = row.get("local_to_global_transform")
    if not isinstance(axes_raw, dict) or set(axes_raw) != {"X", "T", "N"}:
        raise ValueError(f"{member_id}: source-local X/T/N axes are missing")
    if not isinstance(transform, list) or len(transform) != 4 or any(
        not isinstance(line, list) or len(line) != 4 for line in transform
    ):
        raise ValueError(f"{member_id}: malformed 4x4 local-to-global transform")

    axes = {
        name: recorded_unit(
            [float(value) for value in axes_raw[name]], f"{member_id} {name}"
        )
        for name in ("X", "T", "N")
    }
    matrix = [[float(value) for value in line] for line in transform]
    if any(not math.isfinite(value) for line in matrix for value in line):
        raise ValueError(f"{member_id}: non-finite source frame transform")
    if max(abs(matrix[3][i] - [0.0, 0.0, 0.0, 1.0][i]) for i in range(4)) > 1e-10:
        raise ValueError(f"{member_id}: transform is not affine homogeneous form")

    columns = [[matrix[row_index][column] for row_index in range(3)] for column in range(3)]
    for name, column in zip(("X", "T", "N"), columns, strict=True):
        if math.sqrt(math.fsum((axes[name][i] - column[i]) ** 2 for i in range(3))) > 1e-8:
            raise ValueError(f"{member_id}: local frame does not match transform columns")
    for index, first in enumerate(("X", "T", "N")):
        for second in ("X", "T", "N")[index + 1 :]:
            if abs(dot(axes[first], axes[second])) > 1e-8:
                raise ValueError(f"{member_id}: local frame axes are not orthogonal")
    if dot(cross(axes["X"], axes["T"]), axes["N"]) < 1.0 - 1e-8:
        raise ValueError(f"{member_id}: local frame is not right-handed")
    if abs(determinant([list(row) for row in zip(*columns, strict=True)]) - 1.0) > 1e-8:
        raise ValueError(f"{member_id}: local frame transform is not a proper rotation")
    return axes, matrix


def _jacobi_smallest_axis(matrix: list[list[float]]) -> list[float]:
    """Return a sign-canonical minimum-eigenvalue axis of a symmetric 3x3 matrix."""
    a = [[float(value) for value in row] for row in matrix]
    vectors = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(64):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda ij: abs(a[ij[0]][ij[1]]))
        if abs(a[p][q]) <= 1e-14 * max(1.0, *(abs(a[i][i]) for i in range(3))):
            break
        tau = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
        sign = 1.0 if tau >= 0.0 else -1.0
        t = sign / (abs(tau) + math.sqrt(1.0 + tau * tau))
        cosine = 1.0 / math.sqrt(1.0 + t * t)
        sine = t * cosine
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = a[q][p] = 0.0
        for r in range(3):
            if r in (p, q):
                continue
            arp, arq = a[r][p], a[r][q]
            a[r][p] = a[p][r] = cosine * arp - sine * arq
            a[r][q] = a[q][r] = sine * arp + cosine * arq
        for r in range(3):
            vrp, vrq = vectors[r][p], vectors[r][q]
            vectors[r][p] = cosine * vrp - sine * vrq
            vectors[r][q] = sine * vrp + cosine * vrq
    smallest = min(range(3), key=lambda index: a[index][index])
    axis = unit([vectors[row][smallest] for row in range(3)], "minimum-inertia axis")
    first_nonzero = next((value for value in axis if abs(value) > 1e-12), 1.0)
    if first_nonzero < 0.0:
        axis = [-value for value in axis]
    return axis


def step_geometry_crosscheck(
    member_id: str,
    step_relative: str,
    grain_axis: list[float],
    section_mm: list[float],
    expected_member: dict[str, Any],
) -> dict[str, Any]:
    """Check the proposed source axis against the exact exported STEP solid."""
    from cadquery import __version__ as cadquery_version
    from cadquery import importers

    if cadquery_version != "2.8.0":
        raise ValueError(f"CadQuery version changed: expected 2.8.0, got {cadquery_version}")
    imported = importers.importStep(str(ROOT / step_relative))
    shape = getattr(imported, "val", lambda: imported)()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError(f"{member_id}: current STEP must import as one valid solid")

    inertia = shape.matrixOfInertia(shape)
    principal_axis = _jacobi_smallest_axis(inertia)
    alignment = abs(dot(grain_axis, principal_axis))
    if alignment < MIN_INERTIA_AXIS_ALIGNMENT:
        raise ValueError(
            f"{member_id}: source grain proposal does not match current solid's long principal axis "
            f"(|dot|={alignment:.9f})"
        )
    points = [[float(value) for value in vertex.Center().toTuple()] for vertex in shape.Vertices()]
    if not points:
        raise ValueError(f"{member_id}: current STEP solid has no vertices")
    projections = [dot(point, grain_axis) for point in points]
    longitudinal_span = max(projections) - min(projections)
    if longitudinal_span <= max(section_mm):
        raise ValueError(f"{member_id}: proposed longitudinal span is not greater than its section")

    summary = expected_member.get("step_roundtrip_summary")
    if not isinstance(summary, dict):
        raise ValueError(f"{member_id}: current STEP artifact lacks its round-trip summary")
    bounds = shape.BoundingBox()
    actual_bounds = [
        float(bounds.xmin), float(bounds.xmax),
        float(bounds.ymin), float(bounds.ymax),
        float(bounds.zmin), float(bounds.zmax),
    ]
    expected_bounds = summary.get("bounds_xyz_mm")
    if not isinstance(expected_bounds, list) or len(expected_bounds) != 6:
        raise ValueError(f"{member_id}: malformed recorded STEP bounds")
    if max(abs(a - float(b)) for a, b in zip(actual_bounds, expected_bounds, strict=True)) > GEOMETRY_SUMMARY_TOLERANCE_MM:
        raise ValueError(f"{member_id}: imported STEP bounds differ from its recorded summary")
    if abs(float(shape.Volume()) - float(summary.get("volume_mm3", math.nan))) > GEOMETRY_SUMMARY_TOLERANCE_MM3:
        raise ValueError(f"{member_id}: imported STEP volume differs from its recorded summary")

    return {
        "method": "exact STEP BRep minimum principal inertia axis and vertex projection",
        "cadquery_version": cadquery_version,
        "solid_count": 1,
        "minimum_inertia_axis_global_xyz_sign_canonical": principal_axis,
        "absolute_dot_with_proposed_grain_axis": alignment,
        "sign_equivalent": True,
        "proposed_grain_projection_span_mm": longitudinal_span,
        "source_actual_section_mm": section_mm,
        "member_is_longer_than_its_largest_source_section_dimension": True,
        "bounds_and_volume_match_recorded_step_roundtrip_summary": True,
    }


def validate_bundle(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if (
        bundle.get("attempt_id") != "current-full-frame-member-solids-attempt01"
        or bundle.get("candidate") != EXPECTED_CANDIDATE
        or bundle.get("selected_candidate_preserved") != EXPECTED_SELECTED_CANDIDATE
        or bundle.get("geometry_revision_id") != EXPECTED_REVISION
        or bundle.get("reviewed_source_commit") != EXPECTED_REVIEW_COMMIT
        or bundle.get("artifact_sha256") != EXPECTED_SOLID_ARTIFACT_DIGEST
        or bundle.get("member_bundle_sha256") != EXPECTED_MEMBER_BUNDLE_DIGEST
    ):
        raise ValueError("current full-frame STEP artifact identity or digest changed")
    canonical = dict(bundle)
    artifact_digest = canonical.pop("artifact_sha256", None)
    if artifact_digest != sha256_bytes(canonical_json(canonical)):
        raise ValueError("current full-frame STEP artifact canonical digest mismatch")
    members = bundle.get("members")
    if not isinstance(members, list) or len(members) != 50:
        raise ValueError("current full-frame STEP artifact must contain 50 members")
    by_id = {row.get("member_id"): row for row in members if isinstance(row, dict)}
    if len(by_id) != 50 or any(not isinstance(member_id, str) for member_id in by_id):
        raise ValueError("current full-frame STEP artifact member IDs are duplicated or malformed")
    bundle_hash = sha256_bytes(canonical_json([
        {"member_id": row["member_id"], "step_sha256": row["step_sha256"]}
        for row in members
    ]))
    if bundle_hash != EXPECTED_MEMBER_BUNDLE_DIGEST:
        raise ValueError("current member STEP-set digest changed")
    readiness = bundle.get("readiness", {})
    if readiness.get("all_50_finished_member_solids_exported") is not True or readiness.get("step_roundtrip_checked") is not True:
        raise ValueError("current STEP bundle has not completed all-solid round-trip checks")
    if any(value is not False for value in bundle.get("release", {}).values()):
        raise ValueError("current STEP bundle release flags must remain false")
    return by_id


def build_record() -> dict[str, Any]:
    for relative_path, expected_hash in EXPECTED_SHA256.items():
        actual_hash = sha256_file(relative_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"pinned input hash changed for {relative_path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )

    inventory = read_json(INVENTORY_PATH)
    manifest = read_json(MANIFEST_PATH)
    bundle = read_json(SOLID_ARTIFACT_PATH)
    if (
        inventory.get("candidate") != EXPECTED_CANDIDATE
        or inventory.get("source_candidate") != EXPECTED_SELECTED_CANDIDATE
        or manifest.get("candidate") != EXPECTED_CANDIDATE
        or manifest.get("geometry_revision_id") != EXPECTED_REVISION
        or manifest.get("manifest_id") != EXPECTED_MANIFEST_ID
        or manifest.get("manifest_sha256") != EXPECTED_MANIFEST_DIGEST
        or manifest.get("reviewed_repository_commit") != EXPECTED_REVIEW_COMMIT
    ):
        raise ValueError("source inventory or attempt02 manifest identity changed")
    if manifest.get("authority_and_provenance", {}).get("selected_candidate") != EXPECTED_SELECTED_CANDIDATE:
        raise ValueError("attempt02 manifest no longer preserves selected-candidate authority")
    manifest_readiness = manifest.get("readiness", {})
    if manifest_readiness.get("inventory_complete") is not True or manifest_readiness.get("inputs_ready") is not False:
        raise ValueError("attempt02 manifest readiness state changed")
    if any(value is not False for value in manifest.get("release", {}).values()):
        raise ValueError("attempt02 manifest release flags must remain false")

    bundle_members = validate_bundle(bundle)
    inventory_rows = inventory.get("parts")
    manifest_rows = manifest.get("physical_members")
    if not isinstance(inventory_rows, list) or not isinstance(manifest_rows, list):
        raise ValueError("source inventory or attempt02 physical-member list is missing")
    source_parts = {row.get("part_id"): row for row in inventory_rows if isinstance(row, dict)}
    source_timber_ids = {
        row.get("part_id") for row in inventory_rows
        if isinstance(row, dict) and row.get("kind") == "timber"
    }
    if len(source_parts) != len(inventory_rows) or len(source_timber_ids) != 20:
        raise ValueError("source inventory must have unique IDs and exactly 20 timber records")
    manifest_rows_by_id = {
        row.get("member_id"): row for row in manifest_rows if isinstance(row, dict)
    }
    if len(manifest_rows_by_id) != len(manifest_rows) or len(manifest_rows) != 50:
        raise ValueError("attempt02 manifest must contain 50 unique physical-member IDs")
    candidate_rows = manifest.get("candidate_blocks")
    if not isinstance(candidate_rows, list) or len(candidate_rows) != 24:
        raise ValueError("attempt02 manifest must contain 24 candidate block IDs")
    candidate_ids = {
        row.get("part_id") for row in candidate_rows if isinstance(row, dict)
    }
    if len(candidate_ids) != 24 or not candidate_ids <= set(manifest_rows_by_id):
        raise ValueError("attempt02 candidate block IDs are duplicated or absent from members")
    if candidate_ids & source_timber_ids:
        raise ValueError("candidate block IDs must remain disjoint from frame timber IDs")
    frame_rows = {
        row.get("member_id"): row for row in manifest_rows
        if isinstance(row, dict)
        and row.get("member_kind") == "timber"
        and row.get("member_id") in source_timber_ids
    }
    if set(frame_rows) != source_timber_ids:
        raise ValueError("attempt02 current frame timber IDs do not match the 20 source timber IDs")
    if set(bundle_members) != set(manifest_rows_by_id):
        raise ValueError("current STEP IDs do not reconcile to the 50 attempt02 physical members")
    panel_ids = sorted(
        row["part_id"] for row in inventory_rows
        if isinstance(row, dict) and row.get("kind") == "plywood_panel"
    )
    if len(panel_ids) != 6 or set(panel_ids) & source_timber_ids:
        raise ValueError("source inventory panel scope changed")

    # The source inventory's code closure is rechecked before inheriting its
    # member-specific grain rules.
    source_pins = {path: {"sha256": digest} for path, digest in EXPECTED_SHA256.items()}
    for group_key in ("source_hashes_sha256", "source_runtime_module_hashes_sha256"):
        group = inventory.get(group_key)
        if not isinstance(group, dict):
            raise ValueError(f"source inventory is missing {group_key}")
        for relative_path, expected_hash in group.items():
            actual_hash = sha256_file(relative_path)
            if actual_hash != expected_hash:
                raise ValueError(f"source inventory dependency changed: {relative_path}")
            source_pins[relative_path] = {"sha256": expected_hash}
    source_pins[MANIFEST_PATH]["manifest_sha256_field"] = manifest["manifest_sha256"]
    source_pins[SOLID_ARTIFACT_PATH]["artifact_sha256_field"] = bundle["artifact_sha256"]

    member_records = []
    geometry_source_counts: dict[str, int] = {}
    for member_id in sorted(source_timber_ids):
        source = source_parts[member_id]
        manifest_row = frame_rows[member_id]
        solid = bundle_members[member_id]
        provenance = manifest_row.get("source_part_provenance", {})
        if source.get("kind") != "timber" or not isinstance(provenance, dict):
            raise ValueError(f"{member_id}: timber source provenance is malformed")
        if (
            provenance.get("source_shape_sha256") != source.get("source_shape_sha256")
            or provenance.get("source_shape_record_sha256") != source.get("source_shape_record_sha256")
            or solid.get("source_part_record_sha256") != sha256_bytes(canonical_json(source))
        ):
            raise ValueError(f"{member_id}: source inventory row/hash lineage does not reconcile")
        if solid.get("member_kind") != "timber" or solid.get("member_id") != member_id:
            raise ValueError(f"{member_id}: current STEP record has a mismatched identity")
        geometry_source = solid.get("geometry_source")
        if geometry_source not in {
            "current_composed_finished_host",
            "current_source_part_unchanged_in_composition",
        }:
            raise ValueError(f"{member_id}: unexpected current geometry source")
        geometry_source_counts[geometry_source] = geometry_source_counts.get(geometry_source, 0) + 1
        step_relative = (
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "current-full-frame-member-solids-attempt01/" + solid.get("step_file", "")
        )
        if solid.get("step_file") != f"bundle/members/{member_id}.step":
            raise ValueError(f"{member_id}: STEP path is not the expected named member file")
        if sha256_file(step_relative) != solid.get("step_sha256"):
            raise ValueError(f"{member_id}: current exact STEP file hash changed")
        if (ROOT / step_relative).stat().st_size != solid.get("step_size_bytes"):
            raise ValueError(f"{member_id}: current STEP file size changed")

        grain = recorded_unit(
            [float(value) for value in source.get("grain_axis_global_xyz", [])],
            f"{member_id} recorded grain",
        )
        section = [float(value) for value in source.get("actual_source_section_mm", [])]
        if len(section) != 2 or any(value <= 0.0 for value in section):
            raise ValueError(f"{member_id}: recorded source section is malformed")
        axes, transform = source_frame(source, member_id)
        grain_local = {name: dot(axes[name], grain) for name in ("X", "T", "N")}
        reconstructed = [
            math.fsum(axes[name][coordinate] * grain_local[name] for name in ("X", "T", "N"))
            for coordinate in range(3)
        ]
        if math.sqrt(math.fsum((reconstructed[i] - grain[i]) ** 2 for i in range(3))) > 1e-8:
            raise ValueError(f"{member_id}: source-local grain components do not reconstruct the recorded vector")

        summary = solid.get("shape_summary", {})
        manifest_summary = manifest_row.get("graph_finished_geometry_summary", {})
        if not isinstance(summary, dict) or not isinstance(manifest_summary, dict):
            raise ValueError(f"{member_id}: current finished geometry summary is missing")
        bounds = summary.get("bounds_xyz_mm")
        manifest_bounds = manifest_summary.get("bounds_xyz_mm")
        if not isinstance(bounds, list) or not isinstance(manifest_bounds, list) or len(bounds) != 6 or len(manifest_bounds) != 6:
            raise ValueError(f"{member_id}: current finished geometry bounds are malformed")
        if max(abs(float(a) - float(b)) for a, b in zip(bounds, manifest_bounds, strict=True)) > GEOMETRY_SUMMARY_TOLERANCE_MM:
            raise ValueError(f"{member_id}: current solid bounds do not match the reviewed manifest")
        if abs(float(summary.get("volume_mm3", math.nan)) - float(manifest_summary.get("volume_mm3", math.nan))) > GEOMETRY_SUMMARY_TOLERANCE_MM3:
            raise ValueError(f"{member_id}: current solid volume does not match the reviewed manifest")

        current_check = step_geometry_crosscheck(member_id, step_relative, grain, section, solid)
        member_records.append({
            "member_id": member_id,
            "current_geometry_source": geometry_source,
            "source_frame": {
                "basis_order": ["X", "T", "N"],
                "axes_global_xyz": axes,
                "local_to_global_transform": transform,
                "local_datum": source.get("local_datum"),
                "grain_components_in_source_frame": grain_local,
                "right_handed": True,
                "unit_axes": True,
            },
            "conditional_grain_assignment": {
                "longitudinal_material_axis": "L",
                "proposed_global_xyz": grain,
                "proposed_source_local_xyz": grain_local,
                "source_inventory_grain_rule": "grain_axis_global_xyz produced by the pinned source inventory _grain_axis rule",
                "source_blank_dimensions_mm_recorded_order": source.get("source_blank_dimensions_mm"),
                "actual_source_section_mm": section,
                "sign_equivalent": True,
                "delivered_stock_observed": False,
                "status": "conditional_source_orientation_scenario_not_observed_stock",
            },
            "source_inventory_lineage": {
                "source_part_record_sha256": sha256_bytes(canonical_json(source)),
                "source_shape_record_sha256": source.get("source_shape_record_sha256"),
                "source_shape_sha256": source.get("source_shape_sha256"),
                "species_grade_scenario_basis": source.get("species_grade_basis"),
                "delivered_species_group": None,
                "delivered_grade": None,
                "treatment": None,
                "moisture_content": None,
                "receiving_condition": None,
            },
            "current_geometry_lineage": {
                "attempt02_manifest_member_kind": manifest_row.get("member_kind"),
                "composition_roles": manifest_row.get("composition_roles"),
                "owner_report_finished_shape_sha256": manifest_row.get("owner_report_finished_shape_sha256"),
                "source_shape_fingerprint_sha256": solid.get("source_shape_fingerprint_sha256"),
                "shape_summary_sha256": solid.get("shape_summary_sha256"),
                "step_file": step_relative,
                "step_sha256": solid.get("step_sha256"),
                "step_size_bytes": solid.get("step_size_bytes"),
                "finished_bounds_xyz_mm": bounds,
                "finished_volume_mm3": summary.get("volume_mm3"),
                "step_roundtrip_summary": solid.get("step_roundtrip_summary"),
            },
            "exact_solid_axis_crosscheck": current_check,
            "transverse_ring_axes": {
                "status": "unresolved",
                "reason": "This map binds only the recorded longitudinal axis; received-board ring orientation is not observed.",
            },
        })

    if len(member_records) != 20 or geometry_source_counts != {
        "current_composed_finished_host": 16,
        "current_source_part_unchanged_in_composition": 4,
    }:
        raise ValueError(f"unexpected current timber geometry-source counts: {geometry_source_counts}")

    producer_relative = Path(__file__).resolve().relative_to(ROOT).as_posix()
    source_pins[producer_relative] = {"sha256": sha256_file(producer_relative)}
    record: dict[str, Any] = {
        "schema": "wood_joint_current_frame_timber_material_frame_map/v1",
        "attempt_id": "current-frame-timber-material-frame-map-attempt01",
        "status": "conditional_source_bound_current_timber_grain_map_geometry_crosschecked",
        "candidate": EXPECTED_CANDIDATE,
        "selected_candidate_preserved": EXPECTED_SELECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "reviewed_repository_commit": EXPECTED_REVIEW_COMMIT,
        "source_inventory_candidate": inventory.get("candidate"),
        "input_manifest_id": EXPECTED_MANIFEST_ID,
        "input_manifest_sha256": EXPECTED_MANIFEST_DIGEST,
        "current_geometry_artifact_id": bundle.get("attempt_id"),
        "current_geometry_artifact_sha256": bundle.get("artifact_sha256"),
        "scope": {
            "mapped_frame_timber_count": len(member_records),
            "mapped_part_ids": [row["member_id"] for row in member_records],
            "geometry_source_counts": geometry_source_counts,
            "excluded_unresolved_panel_ids": panel_ids,
            "panel_layups_resolved": False,
            "full_frame_material_mapping_complete": False,
        },
        "source_pins": dict(sorted(source_pins.items())),
        "frame_method": {
            "source_local_frame": "The source inventory's member-specific local_to_global_transform and X/T/N basis.",
            "grain_source": "The source inventory's per-member grain_axis_global_xyz, derived by its pinned _grain_axis rule from source geometry axes.",
            "current_geometry_transfer": "Member global coordinate frame is retained by the reviewed composition; each current exact STEP body and manifest summary is separately hash-bound.",
            "current_geometry_crosscheck": "CadQuery 2.8.0 exact STEP BRep minimum principal-inertia axis, sign-equivalent to proposed grain; no viewer mesh is read.",
            "member_geometry_rebuilt": "16 finished hosts; 4 source parts unchanged in composition.",
            "grain_assignment_observed": False,
            "member_geometry_replayed_here": False,
            "viewer_meshes_used": False,
            "candidate_geometry_changed": False,
        },
        "material_status": {
            "source_inventory_species_grade_scenario_basis": "DF-L No. 2; scenario basis only, not received-stock evidence.",
            "delivered_species_group": "unresolved",
            "delivered_grade": "unresolved",
            "grade_acceptance_after_any_remanufacture": "unresolved",
            "treatment": "unresolved",
            "moisture_content": "unresolved",
            "receiving_condition": "unresolved",
            "elastic_material_values": "unresolved; no values emitted by this map",
            "growth_ring_orientation": "unresolved per board",
            "all_six_panel_layups": "unresolved and excluded from this timber-only map",
        },
        "members": member_records,
        "readiness": {
            "full_frame_per_member_material_mapping_ready": False,
            "delivered_timber_properties_ready": False,
            "panel_layups_ready": False,
            "full_frame_inputs_ready": False,
            "native_solve_executed": False,
            "candidate_accepted": False,
        },
        "release": {
            "candidate_accepted": False,
            "engineering_mvp_complete": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "climbing_released": False,
        },
        "claim_limits": [
            "The 20 exact current timber IDs reconcile across source inventory, attempt02 manifest, and the current member STEP bundle.",
            "Each proposed longitudinal direction comes from the source inventory's pinned solid-geometry grain rule and blank/section record; the STEP inertia axis is a modeled-solid consistency check only.",
            "Grain vectors are conditional sign-equivalent stock scenarios, not observations of delivered lumber.",
            "The inventory's DF-L No. 2 field is a scenario basis; received species group, grade, grade disposition, treatment, moisture, and receiving condition remain unresolved.",
            "All six plywood panel layups, transverse ring orientations, steel properties, active connection behavior, demands, and acceptance remain unresolved.",
            "The map does not provide a material-value set, capacity, mechanics result, fabrication approval, or climbing release.",
        ],
    }
    record["record_sha256"] = sha256_bytes(canonical_json(record))
    return record


def verify() -> dict[str, Any]:
    expected = build_record()
    actual = read_json(OUTPUT.relative_to(ROOT).as_posix())
    record_digest = actual.pop("record_sha256", None)
    if record_digest != sha256_bytes(canonical_json(actual)):
        raise ValueError("map canonical record digest mismatch")
    if record_digest != expected["record_sha256"]:
        raise ValueError("map differs from its pinned source reconstruction")
    actual["record_sha256"] = record_digest
    return {
        "status": "verified",
        "candidate": actual["candidate"],
        "geometry_revision_id": actual["geometry_revision_id"],
        "mapped_timber_count": actual["scope"]["mapped_frame_timber_count"],
        "panel_layups_resolved": actual["scope"]["panel_layups_resolved"],
        "full_frame_inputs_ready": actual["readiness"]["full_frame_inputs_ready"],
        "record_sha256": record_digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write:
        if OUTPUT.exists():
            raise FileExistsError(f"refusing to overwrite existing attempt output: {OUTPUT}")
        record = build_record()
        OUTPUT.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "status": "written",
            "path": OUTPUT.relative_to(ROOT).as_posix(),
            "record_sha256": record["record_sha256"],
        }, sort_keys=True))
    else:
        print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
