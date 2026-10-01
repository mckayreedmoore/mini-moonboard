#!/usr/bin/env python3
"""Build source-bound proposed stock envelopes for the current 44 wood pieces.

The rectangular solids created here are analytical proposal boxes. They are
not source hosts, delivered lumber, a cut list, or release evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.gp import gp_Trsf

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
OUTPUT = OUT_DIR / "envelopes.json"
PINS_OUTPUT = OUT_DIR / "source-pins.json"
BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
INPUTS = {
    "source_inventory": Path("docs/wood-joints-mvp/source-inventory.json"),
    "timber_source_yield": BASE
    / "current-timber-source-yield-attempt01/current-timber-source-yield.json",
    "cut_inventory": BASE / "current-timber-cut-inventory-attempt01/inventory.json",
    "cut_yield_scenario": BASE
    / "current-timber-cut-yield-scenario-attempt02/current-timber-cut-yield-scenarios.json",
    "frame_material_map": BASE
    / "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json",
    "block_material_map": BASE
    / "current-block-material-frame-map-attempt02/material-frame-map.json",
    "grade_disposition": BASE
    / "current-timber-grade-disposition-attempt01/grade-disposition.json",
    "current_manifest": BASE
    / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
    "member_solids": BASE
    / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json",
}
PRODUCERS = {
    "source_inventory": Path("scripts/wood_joint_inventory.py"),
    "timber_source_yield": BASE / "current-timber-source-yield-attempt01/produce.py",
    "cut_inventory": BASE / "current-timber-cut-inventory-attempt01/produce.py",
    "cut_yield_scenario": Path(
        "scripts/build_current_timber_cut_yield_scenario_attempt02.py"
    ),
    "frame_material_map": BASE
    / "current-frame-timber-material-frame-map-attempt01/produce.py",
    "block_material_map": BASE
    / "current-block-material-frame-map-attempt02/produce.py",
    "grade_disposition_verifier": BASE
    / "current-timber-grade-disposition-attempt01/verify.py",
    "current_manifest": BASE / "current-full-frame-input-manifest-attempt04/produce.py",
    "member_solids": BASE / "current-full-frame-member-solids-attempt01/produce.py",
}
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_SELECTED = "compact-floor-flush-development"
EXPECTED_FRAME_SOURCE_ONLY = {
    "base_floor_left",
    "base_floor_right",
    "lumber_leg_left",
    "lumber_leg_right",
}
STATUS_CONTAINED = "CONTAINED"
STATUS_INCOMPATIBLE = "INCOMPATIBLE"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_VALUES = {STATUS_CONTAINED, STATUS_INCOMPATIBLE, STATUS_AMBIGUOUS}
LINEAR_TOLERANCE_MM = 1e-5
VOLUME_TOLERANCE_MM3 = 1e-3
DIRECTION_TOLERANCE = 1e-6
EXPECTED_CADQUERY = "2.8.0"
EXPECTED_OCP = "7.9.3.1.1"


class EnvelopeError(ValueError):
    """Raised when pinned source evidence is internally inconsistent."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_json(root: Path, relative: Path) -> tuple[dict[str, Any], bytes]:
    raw = (root / relative).read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise EnvelopeError(f"expected JSON object: {relative.as_posix()}")
    return value, raw


def _unit(vector: Iterable[float], context: str) -> tuple[float, float, float]:
    values = tuple(float(component) for component in vector)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise EnvelopeError(f"{context}: expected three finite vector components")
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 1e-12:
        raise EnvelopeError(f"{context}: zero vector")
    return tuple(value / norm for value in values)  # type: ignore[return-value]


def _dot(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _canonical_sign(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    for component in vector:
        if abs(component) > DIRECTION_TOLERANCE:
            if component < 0:
                return tuple(-value for value in vector)  # type: ignore[return-value]
            break
    return vector


def _matrix(rows: list[list[float]]) -> cq.Matrix:
    transform = gp_Trsf()
    transform.SetValues(
        rows[0][0],
        rows[0][1],
        rows[0][2],
        rows[0][3],
        rows[1][0],
        rows[1][1],
        rows[1][2],
        rows[1][3],
        rows[2][0],
        rows[2][1],
        rows[2][2],
        rows[2][3],
    )
    return cq.Matrix(transform)


def _basis_matrices(
    grain: tuple[float, float, float],
    section_q: tuple[float, float, float],
    section_r: tuple[float, float, float],
) -> tuple[cq.Matrix, cq.Matrix]:
    # Local columns map to global axes; transpose maps global coordinates to
    # local stock coordinates because the basis is orthonormal and right handed.
    to_global = _matrix(
        [
            [grain[0], section_q[0], section_r[0], 0.0],
            [grain[1], section_q[1], section_r[1], 0.0],
            [grain[2], section_q[2], section_r[2], 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    to_local = _matrix(
        [
            [grain[0], grain[1], grain[2], 0.0],
            [section_q[0], section_q[1], section_q[2], 0.0],
            [section_r[0], section_r[1], section_r[2], 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    return to_local, to_global


def _plane_normal_directions(
    shape: cq.Shape, grain: tuple[float, float, float]
) -> list[tuple[float, float, float]]:
    """Find section directions from saved planar STEP faces.

    Projecting each planar normal perpendicular to the conditional grain axis
    removes its along-grain component. This handles oblique grain directions
    and taper planes without treating assembly X/T/N transforms as stock frames.
    """
    directions: list[tuple[float, float, float]] = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        normal = _unit(face.normalAt().toTuple(), "STEP planar face normal")
        along = _dot(normal, grain)
        projected = tuple(normal[i] - along * grain[i] for i in range(3))
        norm = math.sqrt(_dot(projected, projected))
        if norm <= DIRECTION_TOLERANCE:
            continue
        direction = _canonical_sign(_unit(projected, "projected STEP planar normal"))
        if not any(
            abs(_dot(direction, prior)) >= 1.0 - DIRECTION_TOLERANCE
            for prior in directions
        ):
            directions.append(direction)
    return sorted(directions)


def section_basis_from_step(
    shape: cq.Shape, grain_axis_global_xyz: Iterable[float]
) -> dict[str, Any]:
    """Return one unambiguous right-handed grain/section basis or a reason."""
    grain = _unit(grain_axis_global_xyz, "conditional grain axis")
    dirs = _plane_normal_directions(shape, grain)
    if len(dirs) != 2:
        return {
            "status": STATUS_AMBIGUOUS,
            "reason": f"expected two perpendicular planar section directions; found {len(dirs)}",
            "candidate_section_directions_global_xyz": [list(row) for row in dirs],
        }
    if abs(_dot(dirs[0], dirs[1])) > DIRECTION_TOLERANCE:
        return {
            "status": STATUS_AMBIGUOUS,
            "reason": "the two geometry-derived section directions are not perpendicular",
            "candidate_section_directions_global_xyz": [list(row) for row in dirs],
        }
    q = dirs[0]
    r = _unit(_cross(grain, q), "grain cross section-q")
    if abs(_dot(r, dirs[1])) < 1.0 - 10 * DIRECTION_TOLERANCE:
        # The canonical sign of q is deterministic; the second candidate is
        # an unoriented line and may have either sign.
        return {
            "status": STATUS_AMBIGUOUS,
            "reason": "grain and section directions do not form a right-handed orthonormal frame",
            "candidate_section_directions_global_xyz": [list(row) for row in dirs],
        }
    return {
        "status": STATUS_CONTAINED,
        "grain_axis_global_xyz": list(grain),
        "section_q_axis_global_xyz": list(q),
        "section_r_axis_global_xyz": list(r),
        "basis_rule": "q is the lexicographically first canonical unoriented projected planar normal; r = grain × q",
        "candidate_section_directions_global_xyz": [list(row) for row in dirs],
    }


def _oriented_bounds(shape: cq.Shape, to_local: cq.Matrix) -> list[list[float]]:
    local = shape.transformShape(to_local)
    bounds = local.BoundingBox()
    return [
        [float(bounds.xmin), float(bounds.xmax)],
        [float(bounds.ymin), float(bounds.ymax)],
        [float(bounds.zmin), float(bounds.zmax)],
    ]


def _global_bounds(shape: cq.Shape) -> list[float]:
    bounds = shape.BoundingBox()
    return [
        float(bounds.xmin),
        float(bounds.xmax),
        float(bounds.ymin),
        float(bounds.ymax),
        float(bounds.zmin),
        float(bounds.zmax),
    ]


def _volume_sum(shape: cq.Shape) -> float:
    solids = shape.Solids()
    if solids:
        return sum(float(solid.Volume()) for solid in solids)
    return float(shape.Volume())


def _fit_check(
    shape: cq.Shape,
    grain: tuple[float, float, float],
    q: tuple[float, float, float],
    r: tuple[float, float, float],
    stock_length_mm: float,
    section_mm: list[float],
) -> dict[str, Any]:
    """Fit a proposed rectangular envelope and check exact BRep booleans."""
    length = float(stock_length_mm)
    section_values = [float(value) for value in section_mm]
    if (
        not math.isfinite(length)
        or length <= 0
        or len(section_values) != 2
        or any(not math.isfinite(value) or value <= 0 for value in section_values)
    ):
        return {
            "status": STATUS_AMBIGUOUS,
            "reason": "blank length and both stock section dimensions must be positive finite values",
        }
    to_local, to_global = _basis_matrices(grain, q, r)
    finished_bounds = _oriented_bounds(shape, to_local)
    spans = [pair[1] - pair[0] for pair in finished_bounds]
    # Both rotations about the grain axis are enumerated. Choose the feasible
    # one with least total section surplus; exact ties use the listed source
    # dimension order and canonical q/r basis.
    choices = []
    for swapped in (False, True):
        dims = section_values[::-1] if swapped else section_values[:]
        deficits = [dims[i] - spans[i + 1] for i in range(2)]
        violation = sum(max(0.0, -value) for value in deficits)
        surplus = sum(max(0.0, value) for value in deficits)
        choices.append((violation, surplus, int(swapped), dims, deficits))
    violation, _, swapped, dims, section_deltas = min(choices, key=lambda row: row[:3])
    length_delta = length - spans[0]
    # Grain datum: the finished piece's minimum grain station is the stock
    # datum, so all length surplus remains at +grain. Section surplus is split
    # equally across opposing faces. Negative surplus stays exposed at +axis.
    stock_bounds = [[0.0, 0.0] for _ in range(3)]
    stock_bounds[0] = [finished_bounds[0][0], finished_bounds[0][0] + length]
    for index, dim in ((1, dims[0]), (2, dims[1])):
        span = spans[index]
        surplus = dim - span
        lower = finished_bounds[index][0] - max(0.0, surplus) / 2.0
        stock_bounds[index] = [lower, lower + dim]

    outside_volume = math.inf
    intersection_volume = 0.0
    volume_delta = math.inf
    bool_error = None
    try:
        lower = [stock_bounds[index][0] for index in range(3)]
        local_box = cq.Solid.makeBox(
            length,
            dims[0],
            dims[1],
            cq.Vector(lower[0], lower[1], lower[2]),
        )
        stock = local_box.transformShape(to_global)
        outside_volume = _volume_sum(shape.cut(stock))
        intersection_volume = _volume_sum(shape.intersect(stock))
        volume_delta = abs(float(shape.Volume()) - intersection_volume)
    except Exception as error:  # noqa: BLE001 - CAD/OCC boolean failures vary by kernel operation.
        bool_error = f"{type(error).__name__}: {error}"

    within_bounds = all(
        finished_bounds[index][0] >= stock_bounds[index][0] - LINEAR_TOLERANCE_MM
        and finished_bounds[index][1] <= stock_bounds[index][1] + LINEAR_TOLERANCE_MM
        for index in range(3)
    )
    if bool_error is not None:
        status = STATUS_AMBIGUOUS
    elif (
        violation > LINEAR_TOLERANCE_MM
        or length_delta < -LINEAR_TOLERANCE_MM
        or not within_bounds
        or outside_volume > VOLUME_TOLERANCE_MM3
        or volume_delta > VOLUME_TOLERANCE_MM3
    ):
        status = STATUS_INCOMPATIBLE
    else:
        status = STATUS_CONTAINED
    mapping = {
        "source_dimension_0_to_basis_axis": "r" if swapped else "q",
        "source_dimension_1_to_basis_axis": "q" if swapped else "r",
        "swapped": bool(swapped),
        "dimensions_in_q_r_order_mm": dims,
    }
    return {
        "status": status,
        "reason": bool_error,
        "stock_length_mm": length,
        "stock_section_mm_in_source_order": section_values,
        "section_axis_mapping": mapping,
        "finished_oriented_bounds_g_q_r_mm": finished_bounds,
        "finished_oriented_spans_g_q_r_mm": spans,
        "proposed_stock_bounds_g_q_r_mm": stock_bounds,
        "length_surplus_mm": length_delta,
        "section_surplus_q_r_mm": section_deltas,
        "datum_and_surplus_rule": "finished minimum-grain station is stock datum; length surplus at +grain; transverse surplus centered equally",
        "finished_volume_mm3": float(shape.Volume()),
        "stock_minus_finished_outside_volume_mm3": outside_volume,
        "stock_intersection_volume_mm3": intersection_volume,
        "finished_minus_intersection_volume_mm3": volume_delta,
        "linear_tolerance_mm": LINEAR_TOLERANCE_MM,
        "volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
    }


def _load_shape(root: Path, step_path: str, expected_sha256: str) -> cq.Shape:
    relative = Path(step_path)
    raw = (root / relative).read_bytes()
    actual = sha256_bytes(raw)
    if actual != expected_sha256:
        raise EnvelopeError(
            f"STEP digest changed for {relative.as_posix()}: expected {expected_sha256}, got {actual}"
        )
    imported = cq.importers.importStep(str(root / relative))
    solids = imported.solids().vals()
    if len(solids) != 1:
        raise EnvelopeError(
            f"{relative.as_posix()}: expected one STEP solid, found {len(solids)}"
        )
    shape = solids[0]
    if not shape.isValid():
        raise EnvelopeError(f"{relative.as_posix()}: imported STEP solid is invalid")
    return shape


def _input_pin_doc(
    root: Path,
    source_raw: dict[str, bytes],
    step_bindings: dict[str, dict[str, Any]],
    identity_digest: str,
) -> dict[str, Any]:
    pins: dict[str, Any] = {}
    for name, raw in sorted(source_raw.items()):
        pins[name] = {
            "path": INPUTS[name].as_posix(),
            "sha256": sha256_bytes(raw),
            "size_bytes": len(raw),
        }
    for name, relative in sorted(PRODUCERS.items()):
        raw = (root / relative).read_bytes()
        pins[f"producer:{name}"] = {
            "path": relative.as_posix(),
            "sha256": sha256_bytes(raw),
            "size_bytes": len(raw),
        }
    for role, path in (
        ("producer:stock_envelopes", Path(__file__).resolve()),
        (
            "test:stock_envelopes",
            Path(__file__).with_name("test_envelopes.py").resolve(),
        ),
    ):
        relative = path.relative_to(root)
        raw = path.read_bytes()
        pins[role] = {
            "path": relative.as_posix(),
            "sha256": sha256_bytes(raw),
            "size_bytes": len(raw),
        }
    for member_id, binding in sorted(step_bindings.items()):
        pins[f"step:{member_id}"] = {
            "path": binding["path"],
            "sha256": binding["file_sha256"],
            "size_bytes": int(binding["size_bytes"]),
        }
    return {
        "schema": "wood_joint_proposed_stock_envelope_source_pins/v1",
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "piece_identity_sha256": identity_digest,
        "pins": pins,
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    """Build all 44 source-bound proposals and current STEP containment checks."""
    root = Path(root).resolve()
    try:
        cadquery_version = cq.__version__
        ocp_version = importlib.metadata.version("cadquery-ocp")
    except importlib.metadata.PackageNotFoundError as error:
        raise EnvelopeError(
            f"pinned CadQuery/OCP runtime unavailable: {error}"
        ) from error
    if cadquery_version != EXPECTED_CADQUERY or ocp_version != EXPECTED_OCP:
        raise EnvelopeError(
            f"expected CadQuery/OCP {EXPECTED_CADQUERY}/{EXPECTED_OCP}; "
            f"found {cadquery_version}/{ocp_version}"
        )

    loaded: dict[str, dict[str, Any]] = {}
    source_raw: dict[str, bytes] = {}
    for name, relative in INPUTS.items():
        loaded[name], source_raw[name] = _read_json(root, relative)

    inventory = loaded["source_inventory"]
    source_yield = loaded["timber_source_yield"]
    cut_inventory = loaded["cut_inventory"]
    cut_yield = loaded["cut_yield_scenario"]
    frame_map = loaded["frame_material_map"]
    block_map = loaded["block_material_map"]
    grade_disposition = loaded["grade_disposition"]
    manifest = loaded["current_manifest"]
    solids_manifest = loaded["member_solids"]
    for name, source in (
        ("source inventory", inventory),
        ("source yield", source_yield),
        ("cut inventory", cut_inventory),
        ("cut yield", cut_yield),
        ("frame map", frame_map),
        ("block map", block_map),
        ("grade disposition", grade_disposition),
        ("current manifest", manifest),
        ("member solids", solids_manifest),
    ):
        if source.get("candidate") not in (EXPECTED_CANDIDATE, None):
            raise EnvelopeError(f"{name} candidate identity changed")
        if source.get("geometry_revision_id") not in (EXPECTED_REVISION, None):
            raise EnvelopeError(f"{name} geometry revision changed")
    if manifest.get("selected_candidate_authority_preserved") != EXPECTED_SELECTED:
        raise EnvelopeError("selected-candidate authority changed")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04":
        raise EnvelopeError("expected current full-frame input manifest attempt04")

    source_parts = {
        row["part_id"]: row for row in inventory["parts"] if row.get("kind") == "timber"
    }
    source_frame_rows = {
        row["part_id"]: row for row in source_yield["frame_member_records"]
    }
    cut_rows = {row["member_id"]: row for row in cut_inventory["members"]}
    if len(source_parts) != 20 or len(source_frame_rows) != 20 or len(cut_rows) != 44:
        raise EnvelopeError(
            "expected 20 frame source rows and 44 unique cut-inventory pieces"
        )
    if set(source_parts) != set(source_frame_rows):
        raise EnvelopeError(
            "frame source inventory and timber source-yield identities differ"
        )

    block_source_rows = {
        row["part_id"]: row for row in source_yield["candidate_block_records"]
    }
    if len(block_source_rows) != 24:
        raise EnvelopeError("expected exactly 24 proposed block rows")
    if set(cut_rows) != set(source_parts) | set(block_source_rows):
        raise EnvelopeError(
            "cut-inventory semantic identity differs from 20 frame + 24 blocks"
        )

    frame_grain = {row["member_id"]: row for row in frame_map["members"]}
    block_grain = {row["part_id"]: row for row in block_map["members"]}
    if set(frame_grain) != set(source_parts) or set(block_grain) != set(
        block_source_rows
    ):
        raise EnvelopeError(
            "conditional material maps do not match the 20 frame + 24 block identities"
        )

    physical = {row["member_id"]: row for row in manifest["physical_members"]}
    step_bindings = {
        row["member_id"]: row for row in manifest["finished_member_step_bindings"]
    }
    solid_rows = {row["member_id"]: row for row in solids_manifest["members"]}
    wood_ids = set(source_parts) | set(block_source_rows)
    if (
        not wood_ids.issubset(physical)
        or not wood_ids.issubset(step_bindings)
        or not wood_ids.issubset(solid_rows)
    ):
        raise EnvelopeError("current manifest or solids bundle is missing a wood piece")

    # The 30 scenario rows repeat the 24 proposals. Enforce semantic agreement
    # so a length/section cannot drift between the yield and envelope inputs.
    yield_proposals: dict[str, dict[str, Any]] = {}
    for scenario in cut_yield["scenarios"]:
        for blank in scenario["proposed_blanks"]:
            proposal = {
                "stock_class": blank["stock_class"],
                "length_mm": float(blank["proposed_blank_length_mm"]),
                "prepared_section_mm": [
                    float(value) for value in blank["proposed_blank_cross_section_mm"]
                ],
                "grade_assigned": blank["grade_assigned"],
                "post_rip_grade_status": blank["post_rip_grade_status"],
            }
            member_id = blank["part_id"]
            prior = yield_proposals.setdefault(member_id, proposal)
            if prior != proposal:
                raise EnvelopeError(f"cut-yield scenarios disagree for {member_id}")
    if set(yield_proposals) != set(block_source_rows):
        raise EnvelopeError(
            "cut-yield scenario identity differs from the 24 proposed blocks"
        )

    ripped = source_yield["ripped_4x6_blocks"]
    ripped_ids = set(ripped["part_ids"])
    expected_ripped_ids = {
        "center_principal_cleat_left",
        "center_principal_cleat_right",
        "knee_outer_left_inner_frame_block",
        "knee_outer_right_inner_frame_block",
    }
    if ripped_ids != expected_ripped_ids or int(ripped["count"]) != 4:
        raise EnvelopeError("the four grade-unassigned 4x6 rip identities changed")
    if (
        grade_disposition.get("candidate") != EXPECTED_CANDIDATE
        or grade_disposition.get("geometry_revision_id") != EXPECTED_REVISION
        or grade_disposition.get("selected_candidate_authority_preserved")
        != EXPECTED_SELECTED
        or grade_disposition.get("status")
        != "source_bound_preliminary_disposition_no_grade_assigned"
    ):
        raise EnvelopeError("four-rip grade disposition identity or status changed")
    grade_rip_by_id: dict[str, dict[str, Any]] = {}
    for group in grade_disposition["proposed_ripped_blocks"]:
        if group["source_stock_class"] != "4x6":
            raise EnvelopeError(
                "a proposed ripped block is no longer identified as starting from 4x6 stock"
            )
        if any(
            group[field] is not None
            for field in (
                "source_proposed_grade",
                "delivered_grade",
                "post_rip_grade_or_inspection_basis",
            )
        ):
            raise EnvelopeError(
                "a ripped block now has a source, delivered, or post-rip grade assignment"
            )
        for member_id in group["part_ids"]:
            if member_id in grade_rip_by_id:
                raise EnvelopeError(
                    f"duplicate grade-disposition rip identity: {member_id}"
                )
            grade_rip_by_id[member_id] = group
    if set(grade_rip_by_id) != ripped_ids:
        raise EnvelopeError("grade-disposition and source-yield rip identities differ")
    raw_rip_sections = {
        tuple(float(value) for value in row["to_mm"]): tuple(
            float(value) for value in row["from_cross_section_mm"]
        )
        for row in ripped["proposed_section_rips"]
    }

    expected_member_ids = sorted(wood_ids)
    step_pin_rows: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for member_id in expected_member_ids:
        binding = step_bindings[member_id]
        solid_row = solid_rows[member_id]
        cut_row = cut_rows[member_id]
        cut_step = cut_row["step"]
        step_path = binding["path"]
        if (
            binding["member_id"] != member_id
            or binding["one_solid_valid_roundtrip"] is not True
        ):
            raise EnvelopeError(
                f"current STEP binding is not one-solid for {member_id}"
            )
        if not step_path.endswith(solid_row["step_file"]):
            raise EnvelopeError(
                f"manifest and solids-bundle STEP paths differ for {member_id}"
            )
        if binding["file_sha256"] != solid_row["step_sha256"]:
            raise EnvelopeError(
                f"manifest and solids-bundle STEP hashes differ for {member_id}"
            )
        if (
            cut_step["path"] != step_path
            or cut_step["sha256"] != binding["file_sha256"]
        ):
            raise EnvelopeError(
                f"cut inventory and attempt04 STEP identity differ for {member_id}"
            )
        if (
            cut_row["source_shape_fingerprint_sha256"]
            != solid_row["source_shape_fingerprint_sha256"]
        ):
            raise EnvelopeError(
                f"cut inventory and solids-bundle source shape identity differ for {member_id}"
            )
        step_pin_rows[member_id] = binding

        is_frame = member_id in source_parts
        if is_frame:
            source_part = source_parts[member_id]
            length_mm = float(source_part["source_blank_dimensions_mm"][0])
            section_mm = [
                float(value) for value in source_part["actual_source_section_mm"]
            ]
            source_dims = [
                float(value) for value in source_part["source_blank_dimensions_mm"]
            ]
            source_yield_row = source_frame_rows[member_id]
            if abs(
                float(source_yield_row["source_blank_dimensions_mm_recorded"][0])
                - length_mm
            ) > 1e-9 or sorted(source_dims[1:]) != sorted(section_mm):
                raise EnvelopeError(
                    f"source blank dimensions and source section disagree for {member_id}"
                )
            stock_class = source_frame_rows[member_id][
                "nominal_stock_class_inferred_from_source_section"
            ]
            roles = physical[member_id]["composition_roles"]
            if roles == ["source_inventory_member"]:
                frame_status = "source_only"
            elif "current_rebuilt_host" in roles:
                frame_status = "rebuilt"
            else:
                frame_status = "ambiguous"
            if (
                member_id in EXPECTED_FRAME_SOURCE_ONLY
                and frame_status != "source_only"
            ):
                raise EnvelopeError(
                    f"expected source-only geometry identity changed for {member_id}"
                )
            if (
                member_id not in EXPECTED_FRAME_SOURCE_ONLY
                and frame_status != "rebuilt"
            ):
                raise EnvelopeError(
                    f"expected rebuilt frame identity changed for {member_id}"
                )
            grain = frame_grain[member_id]["conditional_grain_assignment"][
                "proposed_global_xyz"
            ]
            grade_status = "conditional_DF-L_No._2_basis_not_received_stock_grade"
            original_section = section_mm
            prepared_section = None
            proposal_source = "source-inventory source_blank_dimensions_mm and actual_source_section_mm"
            grain = frame_grain[member_id]["conditional_grain_assignment"][
                "proposed_global_xyz"
            ]
            cut_grain = cut_rows[member_id]["grain_frame_reference"][
                "conditional_grain_axis_global_xyz"
            ]
            if (
                max(
                    abs(float(a) - float(b))
                    for a, b in zip(grain, cut_grain, strict=True)
                )
                > 1e-9
            ):
                raise EnvelopeError(
                    f"conditional frame grain differs across pinned sources for {member_id}"
                )
        else:
            block_row = block_source_rows[member_id]
            yield_row = yield_proposals[member_id]
            length_mm = float(block_row["proposed_blank_stock_length_mm"])
            prepared_section = [
                float(value) for value in block_row["proposed_blank_cross_section_mm"]
            ]
            if (
                abs(length_mm - yield_row["length_mm"]) > 1e-9
                or prepared_section != yield_row["prepared_section_mm"]
            ):
                raise EnvelopeError(
                    f"source-yield and cut-yield proposal changed for {member_id}"
                )
            stock_class = block_row["proposed_stock_class"]
            grain = block_grain[member_id]["conditional_grain_assignment"][
                "grain_direction_global_xyz"
            ]
            if member_id in ripped_ids:
                if (
                    yield_row["grade_assigned"] is not False
                    or yield_row["post_rip_grade_status"]
                    != "unresolved_after_cross_section_remanufacture"
                ):
                    raise EnvelopeError(
                        f"post-rip grade status changed for {member_id}"
                    )
                prepared_key = tuple(prepared_section)
                original_section = list(raw_rip_sections.get(prepared_key, ()))
                if not original_section:
                    raise EnvelopeError(
                        f"missing original 4x6 rip section for {member_id}"
                    )
                disposition = grade_rip_by_id[member_id]
                if (
                    [float(value) for value in disposition["source_cross_section_mm"]]
                    != original_section
                    or [
                        float(value)
                        for value in disposition["proposed_blank_cross_section_mm"]
                    ]
                    != prepared_section
                    or abs(float(disposition["proposed_blank_length_mm"]) - length_mm)
                    > 1e-9
                ):
                    raise EnvelopeError(
                        f"grade-disposition stock/rip dimensions changed for {member_id}"
                    )
                grade_status = "unassigned_after_cross_section_rip"
            else:
                if yield_row["grade_assigned"] is not False:
                    raise EnvelopeError(
                        f"block source grade assignment changed for {member_id}"
                    )
                original_section = prepared_section[:]
                grade_status = "not_assigned"
            frame_status = None
            proposal_source = "current timber source-yield proposed blank schedule"
            grain = block_grain[member_id]["conditional_grain_assignment"][
                "grain_direction_global_xyz"
            ]
            cut_grain = cut_rows[member_id]["grain_frame_reference"][
                "conditional_grain_axis_global_xyz"
            ]
            if (
                max(
                    abs(float(a) - float(b))
                    for a, b in zip(grain, cut_grain, strict=True)
                )
                > 1e-9
            ):
                raise EnvelopeError(
                    f"conditional block grain differs across pinned sources for {member_id}"
                )

        if len(original_section) != 2:
            raise EnvelopeError(
                f"expected two original stock section dimensions for {member_id}"
            )
        shape = _load_shape(root, step_path, binding["file_sha256"])
        summary = solid_row["shape_summary"]
        if (
            abs(float(shape.Volume()) - float(summary["volume_mm3"]))
            > VOLUME_TOLERANCE_MM3
            or max(
                abs(actual - float(expected))
                for actual, expected in zip(
                    _global_bounds(shape), summary["bounds_xyz_mm"], strict=True
                )
            )
            > LINEAR_TOLERANCE_MM
        ):
            raise EnvelopeError(
                f"current STEP BRep differs from the pinned solids summary for {member_id}"
            )
        basis = section_basis_from_step(shape, grain)
        if basis["status"] != STATUS_CONTAINED:
            original_result = {
                "status": STATUS_AMBIGUOUS,
                "reason": basis["reason"],
                "linear_tolerance_mm": LINEAR_TOLERANCE_MM,
                "volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
            }
            prepared_result = None
        else:
            g = tuple(basis["grain_axis_global_xyz"])
            q = tuple(basis["section_q_axis_global_xyz"])
            r = tuple(basis["section_r_axis_global_xyz"])
            original_result = _fit_check(shape, g, q, r, length_mm, original_section)
            prepared_result = (
                _fit_check(shape, g, q, r, length_mm, prepared_section)
                if prepared_section is not None
                else None
            )
        statuses = [original_result["status"]]
        if prepared_result is not None:
            statuses.append(prepared_result["status"])
        if STATUS_AMBIGUOUS in statuses:
            overall = STATUS_AMBIGUOUS
        elif STATUS_INCOMPATIBLE in statuses:
            overall = STATUS_INCOMPATIBLE
        else:
            overall = STATUS_CONTAINED
        record = {
            "member_id": member_id,
            "member_kind": "frame_timber" if is_frame else "candidate_block",
            "stock_class": stock_class,
            "frame_status": frame_status,
            "stock_blank_length_mm": length_mm,
            "original_stock_section_mm": original_section,
            "prepared_section_mm": prepared_section,
            "prepared_section_required": prepared_section is not None,
            "grade_assignment_status": grade_status,
            "proposal_source": proposal_source,
            "current_finished_step_path": step_path,
            "current_finished_step_sha256": binding["file_sha256"],
            "current_finished_step_size_bytes": int(binding["size_bytes"]),
            "current_finished_solid_count": 1,
            "current_finished_volume_mm3": float(shape.Volume()),
            "source_shape_fingerprint_sha256": solid_row[
                "source_shape_fingerprint_sha256"
            ],
            "conditional_grain_axis_global_xyz": list(
                _unit(grain, f"{member_id} grain")
            ),
            "proposed_frame": basis,
            "original_stock_containment": original_result,
            "prepared_section_containment": prepared_result,
            "containment_status": overall,
            "proposal_limits": [
                "PROPOSED analytical rectangular starting-stock envelope; no raw-host, received-stock, cut-yield, or physical-inspection proof.",
                "Containment is geometric only; species, grade, treatment, moisture, defects, material assignment, and acceptance remain unresolved.",
            ],
        }
        records.append(record)

    if len(records) != 44 or len({record["member_id"] for record in records}) != 44:
        raise EnvelopeError("expected 44 unique output records")
    if sum(row["member_kind"] == "frame_timber" for row in records) != 20:
        raise EnvelopeError("expected exactly 20 frame timber records")
    if sum(row["member_kind"] == "candidate_block" for row in records) != 24:
        raise EnvelopeError("expected exactly 24 candidate block records")
    identity = [
        {
            "member_id": row["member_id"],
            "member_kind": row["member_kind"],
            "current_finished_step_path": row["current_finished_step_path"],
            "current_finished_step_sha256": row["current_finished_step_sha256"],
        }
        for row in records
    ]
    identity_digest = sha256_bytes(canonical_bytes(identity))
    pins_doc = _input_pin_doc(root, source_raw, step_pin_rows, identity_digest)
    pins_digest = sha256_bytes(canonical_bytes(pins_doc))
    return {
        "schema": "wood_joint_proposed_starting_stock_envelopes/v1",
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "source_manifest_id": manifest["manifest_id"],
        "source_manifest_sha256": sha256_bytes(source_raw["current_manifest"]),
        "member_solids_bundle_sha256": sha256_bytes(source_raw["member_solids"]),
        "selected_candidate_authority_preserved": EXPECTED_SELECTED,
        "record_count": len(records),
        "semantic_piece_identity_sha256": identity_digest,
        "source_pins_sha256": pins_digest,
        "producer_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "geometry_runtime": {
            "cadquery": cadquery_version,
            "cadquery_ocp": ocp_version,
            "linear_tolerance_mm": LINEAR_TOLERANCE_MM,
            "volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
        },
        "claims": {
            "status": "proposal_only_geometry_containment_screen",
            "containment_status_values": sorted(STATUS_VALUES),
            "one_solid_step_count": 44,
            "native_solver_executed": False,
            "cut_or_fabrication_authorized": False,
            "physical_stock_or_grade_observed": False,
            "purchasing_or_build_acceptance": False,
            "nesting_or_material_yield_proved": False,
        },
        "records": records,
    }, pins_doc


def verify_pin_document(root: Path, pins: dict[str, Any]) -> None:
    """Fail closed if any pinned source, producer, or STEP bytes have changed."""
    root = Path(root).resolve()
    for name, pin in pins["pins"].items():
        relative = Path(pin["path"])
        path = root / relative
        if not path.is_file():
            raise EnvelopeError(f"pinned file is missing: {relative.as_posix()}")
        raw = path.read_bytes()
        observed = sha256_bytes(raw)
        if observed != pin["sha256"] or len(raw) != int(pin["size_bytes"]):
            raise EnvelopeError(f"pinned bytes changed: {relative.as_posix()} ({name})")


def verify_canonical_file(path: Path, value: Any, label: str) -> None:
    if path.read_bytes() != canonical_bytes(value):
        raise EnvelopeError(f"{label} is not the exact canonical JSON byte sequence")


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise EnvelopeError(f"refusing to overwrite existing output: {path}") from error


def _verify_outputs(root: Path) -> dict[str, Any]:
    report, pins = build_report(root)
    expected_pins = canonical_bytes(pins)
    stored_pins = json.loads(PINS_OUTPUT.read_text(encoding="utf-8"))
    verify_pin_document(root, stored_pins)
    verify_canonical_file(PINS_OUTPUT, stored_pins, "source-pins.json")
    if canonical_bytes(stored_pins) != expected_pins:
        raise EnvelopeError(
            "source-pins.json does not match the current source inventory"
        )
    verify_canonical_file(OUTPUT, report, "envelopes.json")
    return {
        "status": "verified",
        "record_count": report["record_count"],
        "contained_count": sum(
            row["containment_status"] == STATUS_CONTAINED for row in report["records"]
        ),
        "incompatible_count": sum(
            row["containment_status"] == STATUS_INCOMPATIBLE
            for row in report["records"]
        ),
        "ambiguous_count": sum(
            row["containment_status"] == STATUS_AMBIGUOUS for row in report["records"]
        ),
        "envelopes_sha256": sha256_bytes(canonical_bytes(report)),
        "source_pins_sha256": sha256_bytes(expected_pins),
        "producer_sha256": sha256_bytes(Path(__file__).read_bytes()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", action="store_true", help="write ignored raw JSON outputs once"
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="replay exact source pins and canonical outputs",
    )
    args = parser.parse_args(argv)
    if args.write:
        report, pins = build_report(ROOT)
        if OUTPUT.exists() or PINS_OUTPUT.exists():
            raise EnvelopeError(
                "raw outputs already exist; remove only these ignored outputs before --write"
            )
        _write_exclusive(OUTPUT, canonical_bytes(report))
        try:
            _write_exclusive(PINS_OUTPUT, canonical_bytes(pins))
        except Exception:
            OUTPUT.unlink(missing_ok=True)
            raise
        result = {
            "status": "written",
            "record_count": report["record_count"],
            "contained_count": sum(
                row["containment_status"] == STATUS_CONTAINED
                for row in report["records"]
            ),
            "incompatible_count": sum(
                row["containment_status"] == STATUS_INCOMPATIBLE
                for row in report["records"]
            ),
            "ambiguous_count": sum(
                row["containment_status"] == STATUS_AMBIGUOUS
                for row in report["records"]
            ),
            "envelopes_sha256": sha256_bytes(canonical_bytes(report)),
            "source_pins_sha256": sha256_bytes(canonical_bytes(pins)),
            "producer_sha256": sha256_bytes(Path(__file__).read_bytes()),
        }
    else:
        result = _verify_outputs(ROOT)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
