#!/usr/bin/env python3
"""Replay upper-block washer-seat geometry and signed axial seat references."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUTPUT = HERE / "seats.json"

UPPER_INPUTS = {
    "uppermost": (
        Path(
            "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json"
        ),
        "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6",
    ),
    "service": (
        Path(
            "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/upper-joints.json"
        ),
        "f4c92d874dcb0f40e5e900971deaff9580e99063b453e1984e9b1ba660a2be9f",
    ),
}

SUPPORT_HELPER = Path(
    "docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01/check_support.py"
)
MEMBER_BUNDLE = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-full-frame-member-solids-attempt01/bundle"
    "/current-full-frame-member-solids.json"
)
FASTENER_INPUTS = Path(
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30"
    "/fastener-inputs.json"
)

SOURCE_PINS: dict[str, tuple[Path, str]] = {
    "DF-L material specification": (
        Path(
            "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/materials.md"
        ),
        "943e5ecb26a5bb9e49e55e4c510bbbf697b08a6b9415c26bbcb41c48db70a2d6",
    ),
    "NDS Supplement Table 4A": (
        Path(
            "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/materials-source/"
            "AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf"
        ),
        "1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b",
    ),
    "existing washer-seat support implementation": (
        SUPPORT_HELPER,
        "9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57",
    ),
    "washer support geometry module": (
        Path("mini_moonboard/wood_joint_geometry.py"),
        "e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e",
    ),
    "CAD washer dimensions": (
        Path("mini_moonboard/wood_joint_frame.py"),
        "77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545",
    ),
    "fastener catalog input": (
        FASTENER_INPUTS,
        "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    ),
    "hardware specification": (
        Path(
            "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fasteners.md"
        ),
        "aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6",
    ),
    "hardware requirements": (
        Path(
            "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/requirements.json"
        ),
        "15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100",
    ),
    "finished-member bundle manifest": (
        MEMBER_BUNDLE,
        "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    ),
}

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CASES = ("a1-rear", "a12-rear", "k12-rear")
EXPECTED_INCREMENT_INDICES = tuple(range(7))
EXPECTED_AXES_PER_PACKET = 16
EXPECTED_BOLTS = 32
EXPECTED_GEOMETRY_SEATS = 64
EXPECTED_SOURCE_STATES = 672
EXPECTED_SEAT_STATES = 1344

INCH_MM = 25.4
PSI_TO_N_PER_MM2 = 0.006894757293168361
AXIS_TOLERANCE = 1e-8
FACE_COORDINATE_TOLERANCE_MM = 1e-5
SUPPORT_TOLERANCE = 1e-8
READBACK_TOLERANCE_MM = 1e-4
READBACK_AREA_TOLERANCE_MM2 = 1e-3
READBACK_VOLUME_TOLERANCE_MM3 = 0.001
AXIAL_ABSOLUTE_TOLERANCE_N = 1e-5


class SourceEvidenceError(RuntimeError):
    """A frozen source, readback, or source-bound field failed validation."""


def sha256(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    except OSError as error:
        raise SourceEvidenceError(f"cannot read source {path}: {error}") from error


def require_source(condition: bool, message: str) -> None:
    if not condition:
        raise SourceEvidenceError(message)


def finite_vector(value: Any, label: str) -> tuple[float, float, float]:
    require_source(
        isinstance(value, (list, tuple)) and len(value) == 3,
        f"invalid source vector: {label}",
    )
    vector = tuple(float(component) for component in value)
    require_source(
        all(math.isfinite(component) for component in vector),
        f"nonfinite source vector: {label}",
    )
    return vector


def dot(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(dot(vector, vector))


def subtract(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(first, second, strict=True))


def scale(
    vector: tuple[float, float, float], factor: float
) -> tuple[float, float, float]:
    return tuple(value * factor for value in vector)


def normalized(
    vector: tuple[float, float, float], label: str
) -> tuple[float, float, float]:
    length = norm(vector)
    require_source(length > 1e-12, f"zero source vector: {label}")
    return scale(vector, 1.0 / length)


def verify_hash(relative: Path, expected: str, label: str) -> str:
    path = ROOT / relative
    require_source(path.is_file(), f"missing pinned input: {relative}")
    actual = sha256(path)
    require_source(actual == expected, f"{label} SHA-256 changed: {relative}")
    return actual


def read_json(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    require_source(path.is_file(), f"missing JSON source: {relative}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SourceEvidenceError(
            f"cannot read source JSON {relative}: {error}"
        ) from error
    require_source(isinstance(value, dict), f"expected JSON object: {relative}")
    return value


def source_number(source: str, variable: str) -> float:
    import ast

    try:
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == variable
                for target in node.targets
            ):
                value = float(ast.literal_eval(node.value))
                require_source(
                    math.isfinite(value), f"nonfinite CAD constant: {variable}"
                )
                return value
    except (SyntaxError, ValueError) as error:
        raise SourceEvidenceError(
            f"cannot read pinned CAD constant {variable}: {error}"
        ) from error
    raise SourceEvidenceError(f"missing literal {variable} in pinned CAD source")


def load_support_helper() -> Any:
    helper_path = ROOT / SUPPORT_HELPER
    module_name = "upper_block_pinned_washer_support_helper"
    spec = importlib.util.spec_from_file_location(module_name, helper_path)
    require_source(
        spec is not None and spec.loader is not None,
        "cannot load pinned washer-support helper",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        raise SourceEvidenceError(
            f"cannot import pinned washer-support helper: {error}"
        ) from error
    require_source(
        module.ROOT.resolve() == ROOT,
        "washer-support helper resolved a different repository root",
    )
    return module


def bind_outer_seats(geometry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Derive head/nut seat owners from signed axis and member-face coordinates."""
    axis_raw = finite_vector(
        geometry.get("head_to_nut_axis_xyz"), "head_to_nut_axis_xyz"
    )
    axis_length = norm(axis_raw)
    require_source(
        abs(axis_length - 1.0) <= 1e-7, "frozen head-to-nut axis is not unit length"
    )
    axis = normalized(axis_raw, "head_to_nut_axis_xyz")
    endpoints = geometry.get("outer_seat_endpoints_xyz_mm")
    require_source(
        isinstance(endpoints, list) and len(endpoints) == 2,
        "expected two frozen outer seat endpoints",
    )
    points = [finite_vector(point, "outer_seat_endpoint_xyz_mm") for point in endpoints]
    origin = finite_vector(geometry.get("lateral_plane_xyz_mm"), "lateral_plane_xyz_mm")
    projections = [dot(subtract(point, origin), axis) for point in points]
    require_source(
        abs(projections[0] - projections[1]) > FACE_COORDINATE_TOLERANCE_MM,
        "outer seat endpoints have no signed axial order",
    )
    ordered = sorted(zip(projections, points, strict=True), key=lambda row: row[0])

    members = geometry.get("members")
    require_source(
        isinstance(members, dict) and set(members) == {"block", "host"},
        "expected exact block and host member geometry",
    )
    seat_rows: dict[str, dict[str, Any]] = {}
    for seat_role, (endpoint_projection, point) in zip(
        ("head", "nut"), ordered, strict=True
    ):
        matches = []
        for member_role, member_geometry in members.items():
            center = finite_vector(
                member_geometry.get("bolt_line_mid_bearing_xyz_mm"),
                f"{member_role} bolt-line midpoint",
            )
            bearing_length = float(member_geometry.get("bearing_length_mm"))
            require_source(
                math.isfinite(bearing_length) and bearing_length > 0,
                f"invalid {member_role} bearing length",
            )
            delta = subtract(point, center)
            axial_offset = dot(delta, axis)
            transverse = subtract(delta, scale(axis, axial_offset))
            face_sign = -1.0 if axial_offset < 0 else 1.0
            face_error = abs(abs(axial_offset) - bearing_length / 2)
            transverse_error = norm(transverse)
            if (
                face_error <= FACE_COORDINATE_TOLERANCE_MM
                and transverse_error <= FACE_COORDINATE_TOLERANCE_MM
            ):
                matches.append(
                    {
                        "member_role": member_role,
                        "member_id": str(member_geometry.get("member")),
                        "face_sign": face_sign,
                        "face_coordinate_error_mm": face_error,
                        "transverse_error_mm": transverse_error,
                        "bearing_length_mm": bearing_length,
                    }
                )
        require_source(
            len(matches) == 1,
            f"{seat_role} endpoint maps to {len(matches)} member faces",
        )
        match = matches[0]
        expected_sign = -1.0 if seat_role == "head" else 1.0
        require_source(
            match["face_sign"] == expected_sign,
            f"{seat_role} endpoint is on the wrong signed face",
        )
        member_geometry = members[match["member_role"]]
        grain = normalized(
            finite_vector(
                member_geometry.get("conditional_grain_xyz"),
                f"{match['member_id']} conditional grain",
            ),
            f"{match['member_id']} conditional grain",
        )
        grain_axis_alignment = abs(dot(grain, axis))
        if grain_axis_alignment <= AXIS_TOLERANCE:
            grain_relation = "perpendicular_to_bolt_axis"
        elif 1.0 - grain_axis_alignment <= AXIS_TOLERANCE:
            grain_relation = "parallel_to_bolt_axis"
        else:
            grain_relation = "oblique_to_bolt_axis_unresolved"
        seat_rows[seat_role] = {
            "seat_role": seat_role,
            "owner_role": match["member_role"],
            "owner_member_id": match["member_id"],
            "seat_point_xyz_mm": list(point),
            "seat_inward_normal_global_xyz": list(
                axis if seat_role == "head" else scale(axis, -1.0)
            ),
            "member_face_sign_along_head_to_nut_axis": int(match["face_sign"]),
            "face_coordinate_error_mm": match["face_coordinate_error_mm"],
            "transverse_error_mm": match["transverse_error_mm"],
            "bearing_length_mm": match["bearing_length_mm"],
            "conditional_grain_global_xyz": list(grain),
            "absolute_grain_axis_alignment": grain_axis_alignment,
            "grain_relation": grain_relation,
            "member_source_geometry": {
                "finished_step": member_geometry.get("finished_step"),
                "finished_step_sha256": member_geometry.get("finished_step_sha256"),
                "conditional_grain_xyz": member_geometry.get("conditional_grain_xyz"),
                "bolt_line_mid_bearing_xyz_mm": member_geometry.get(
                    "bolt_line_mid_bearing_xyz_mm"
                ),
            },
            "head_to_nut_projection_mm": endpoint_projection,
        }
    require_source(
        {row["owner_role"] for row in seat_rows.values()} == {"block", "host"},
        "outer washer seats do not bind one endpoint to each physical receiver",
    )
    return seat_rows


def member_step_bindings(
    sources: dict[str, dict[str, Any]], bundle: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    manifest_rows = bundle.get("members")
    require_source(
        isinstance(manifest_rows, list), "member bundle has no member inventory"
    )
    manifest = {row.get("member_id"): row for row in manifest_rows}
    require_source(
        len(manifest) == len(manifest_rows), "member bundle has duplicate member IDs"
    )
    bindings: dict[str, dict[str, Any]] = {}
    for packet, report in sources.items():
        geometry_rows = report.get("geometry_by_axis")
        require_source(
            isinstance(geometry_rows, dict),
            f"{packet} report has no geometry_by_axis map",
        )
        for geometry in geometry_rows.values():
            members = geometry.get("members")
            require_source(
                isinstance(members, dict) and set(members) == {"block", "host"},
                "expected exact block and host member geometry",
            )
            for source_geometry in members.values():
                member_id = str(source_geometry.get("member"))
                step_relative = Path(str(source_geometry["finished_step"]))
                step_hash = str(source_geometry["finished_step_sha256"])
                require_source(
                    not step_relative.is_absolute() and ".." not in step_relative.parts,
                    f"unsafe STEP path for {member_id}",
                )
                manifest_row = manifest.get(member_id)
                require_source(
                    manifest_row is not None,
                    f"member absent from pinned STEP manifest: {member_id}",
                )
                expected_path = step_relative.relative_to(
                    MEMBER_BUNDLE.parents[1]
                ).as_posix()
                require_source(
                    manifest_row.get("step_file") == expected_path,
                    f"STEP path differs from pinned manifest: {member_id}",
                )
                require_source(
                    manifest_row.get("step_sha256") == step_hash,
                    f"STEP hash differs from pinned manifest: {member_id}",
                )
                old = bindings.get(member_id)
                current = {
                    "member_id": member_id,
                    "path": step_relative.as_posix(),
                    "sha256": step_hash,
                    "manifest": manifest_row,
                }
                if old is not None:
                    require_source(
                        old["path"] == current["path"]
                        and old["sha256"] == current["sha256"],
                        f"inconsistent frozen STEP binding for {member_id}",
                    )
                else:
                    bindings[member_id] = current
    return bindings


def load_member_solids(
    bindings: dict[str, dict[str, Any]], helper: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    shapes: dict[str, Any] = {}
    summaries: dict[str, Any] = {}
    cq = helper.cq
    for member_id, binding in sorted(bindings.items()):
        relative = Path(binding["path"])
        verified_hash = verify_hash(
            relative, binding["sha256"], f"finished member STEP {member_id}"
        )
        try:
            imported = cq.importers.importStep(str(ROOT / relative)).val()
            solids = imported.Solids()
        except Exception as error:
            raise SourceEvidenceError(
                f"cannot read pinned STEP solid {member_id}: {error}"
            ) from error
        require_source(
            len(solids) == 1 and solids[0].isValid(),
            f"STEP is not one valid solid: {member_id}",
        )
        solid = solids[0]
        actual_faces = len(solid.Faces())
        actual_volume = float(solid.Volume())
        actual_box = solid.BoundingBox()
        actual_bounds = [
            float(actual_box.xmin),
            float(actual_box.xmax),
            float(actual_box.ymin),
            float(actual_box.ymax),
            float(actual_box.zmin),
            float(actual_box.zmax),
        ]
        face_types = Counter(face.geomType() for face in solid.Faces())
        actual_areas: dict[str, float] = {}
        for face in solid.Faces():
            kind = face.geomType()
            actual_areas[kind] = actual_areas.get(kind, 0.0) + float(face.Area())
        expected = binding["manifest"].get("step_roundtrip_summary", {})
        require_source(
            expected.get("valid") is True,
            f"manifest lacks valid STEP readback for {member_id}",
        )
        require_source(
            expected.get("solid_count") == 1,
            f"manifest solid count changed for {member_id}",
        )
        require_source(
            actual_faces == expected.get("face_count"),
            f"STEP readback face count changed for {member_id}",
        )
        require_source(
            abs(actual_volume - float(expected.get("volume_mm3")))
            <= READBACK_VOLUME_TOLERANCE_MM3,
            f"STEP readback volume changed for {member_id}",
        )
        expected_bounds = [float(value) for value in expected.get("bounds_xyz_mm", [])]
        require_source(
            len(expected_bounds) == 6, f"manifest bounds missing for {member_id}"
        )
        require_source(
            max(abs(a - b) for a, b in zip(actual_bounds, expected_bounds, strict=True))
            <= READBACK_TOLERANCE_MM,
            f"STEP readback bounds changed for {member_id}",
        )
        expected_areas = expected.get("surface_area_by_type_mm2", {})
        require_source(
            set(actual_areas) == set(expected_areas),
            f"STEP surface inventory changed for {member_id}",
        )
        require_source(
            all(
                abs(actual_areas[name] - float(expected_areas[name]))
                <= READBACK_AREA_TOLERANCE_MM2
                for name in actual_areas
            ),
            f"STEP surface areas changed for {member_id}",
        )
        shapes[member_id] = solid
        summaries[member_id] = {
            "path": binding["path"],
            "sha256": binding["sha256"],
            "verified_sha256": verified_hash,
            "valid": bool(solid.isValid()),
            "solid_count": len(solids),
            "face_count": actual_faces,
            "face_count_manifest": expected["face_count"],
            "volume_mm3": actual_volume,
            "volume_mm3_manifest": float(expected["volume_mm3"]),
            "bounds_xyz_mm": actual_bounds,
            "surface_face_count_by_type": dict(sorted(face_types.items())),
            "surface_area_by_type_mm2": dict(sorted(actual_areas.items())),
            "manifest_surface_area_by_type_mm2": expected_areas,
            "manifest_readback_status": "matched_within_pinned_tolerances",
        }
    return shapes, summaries


def catalog_scenarios(fasteners: dict[str, Any], helper: Any) -> list[dict[str, Any]]:
    dimensions = fasteners.get("dimension_inputs", {}).get("washer", {})
    id_bounds = [float(value) for value in dimensions.get("id_in", [])]
    od_bounds = [float(value) for value in dimensions.get("od_in", [])]
    require_source(
        len(id_bounds) == 2 and len(od_bounds) == 2,
        "catalog washer bounds must each have two limits",
    )
    id_min, id_max = (value * INCH_MM for value in id_bounds)
    od_min, od_max = (value * INCH_MM for value in od_bounds)
    require_source(
        0 < id_min <= id_max < od_min <= od_max, "invalid catalog washer annulus bounds"
    )
    frame_path = ROOT / Path("mini_moonboard/wood_joint_frame.py")
    try:
        frame_source = frame_path.read_text(encoding="utf-8")
    except OSError as error:
        raise SourceEvidenceError(
            f"cannot read pinned CAD washer source: {error}"
        ) from error
    cad_od = source_number(frame_source, "WASHER_OD_MM")
    cad_id = source_number(frame_source, "WASHER_ID_MM")
    raw = [
        {
            "scenario_id": "cad_modeled",
            "od_mm": cad_od,
            "id_mm": cad_id,
            "basis": "Pinned CAD washer annulus constants; geometry envelope only.",
            "dimensions_in": None,
        },
        {
            "scenario_id": "catalog_minimum_area",
            "od_mm": od_min,
            "id_mm": id_max,
            "basis": "Catalog Type A Wide bounds: minimum OD with maximum ID; minimum annulus area.",
            "dimensions_in": {"od": min(od_bounds), "id": max(id_bounds)},
        },
        {
            "scenario_id": "catalog_maximum_envelope",
            "od_mm": od_max,
            "id_mm": id_min,
            "basis": "Catalog Type A Wide bounds: maximum OD with minimum ID; maximum footprint envelope.",
            "dimensions_in": {"od": max(od_bounds), "id": min(id_bounds)},
        },
    ]
    scenarios = []
    for row in raw:
        od, inner = float(row["od_mm"]), float(row["id_mm"])
        require_source(
            math.isfinite(od) and math.isfinite(inner) and 0 < inner < od,
            f"invalid annulus dimensions: {row['scenario_id']}",
        )
        # hardware_for also checks that the hypothetical washer opening clears its declared steel shaft.
        helper.hardware_for(od, inner)
        area = math.pi * (od**2 - inner**2) / 4.0
        scenarios.append(
            {
                **row,
                "od_mm": od,
                "id_mm": inner,
                "annulus_area_mm2": area,
                "id_radius_mm": inner / 2,
                "od_radius_mm": od / 2,
            }
        )
    require_source(
        len({row["scenario_id"] for row in scenarios}) == 3,
        "washer scenario IDs are not unique",
    )
    return scenarios


def classify_support_helper_error(message: str) -> str | None:
    """Recognize only modeled geometry outcomes from the pinned helper."""
    if message == "washer datum has no matching planar wood boundary face":
        return "no_matching_planar_datum_face"
    if message.startswith("annulus is clipped by a bore or wood edge at "):
        return "inward_annulus_clipped_by_modeled_wood_boundary"
    if message.startswith("washer datum is embedded or outward normal is wrong at "):
        return "outward_probe_overlaps_modeled_wood_or_normal_is_incompatible"
    if message.startswith("nonfinite or out-of-range support fraction at "):
        return "modeled_support_fraction_invalid"
    return None


def seat_support_result(
    *,
    helper: Any,
    body: Any,
    seat: dict[str, Any],
    axis: tuple[float, float, float],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    member_id = str(seat["owner_member_id"])
    point = seat["seat_point_xyz_mm"]
    role = f"{seat['seat_role']}_washer_seat"
    od_mm, id_mm = scenario["od_mm"], scenario["id_mm"]
    planes = []
    datum_error = None
    try:
        planes = helper.matching_seat_planes(
            body,
            helper.cq.Vector(*point),
            helper.cq.Vector(*seat["seat_inward_normal_global_xyz"]),
        )
    except ValueError as error:
        datum_error = str(error)
    try:
        wrapped = helper.seat_support(body, member_id, point, axis, role, od_mm, id_mm)
        helper_error = None
    except ValueError as error:
        helper_error = str(error)
        geometry_error = classify_support_helper_error(helper_error)
        if geometry_error is None:
            raise SourceEvidenceError(
                f"pinned seat helper failed outside its modeled-support outcomes at {member_id}/{role}: {helper_error}"
            ) from error
        wrapped = None

    diagnostic_probe_count = 0
    if wrapped is not None:
        depth_keys = [f"{depth:g}" for depth in helper.DEPTHS_MM]
        inward_fractions = [
            float(wrapped["inward_support_fraction_by_depth"][key])
            for key in depth_keys
        ]
        outward_fractions = [
            float(wrapped["outward_support_fraction_by_depth"][key])
            for key in depth_keys
        ]
        unsupported_area = float(wrapped["unsupported_area_max_mm2"])
    else:
        hardware = helper.hardware_for(od_mm, id_mm)
        inward_seat = helper.WasherSeat(
            member_id,
            helper.cq.Vector(*point),
            helper.cq.Vector(*seat["seat_inward_normal_global_xyz"]),
        )
        outward_seat = helper.WasherSeat(
            member_id,
            helper.cq.Vector(*point),
            helper.cq.Vector(*seat["seat_inward_normal_global_xyz"]).multiply(-1),
        )
        inward, outward = [], []
        for depth in helper.DEPTHS_MM:
            inward.append(
                helper.washer_support_report(
                    inward_seat, body, hardware, probe_depth_mm=depth
                )
            )
            outward.append(
                helper.washer_support_report(
                    outward_seat, body, hardware, probe_depth_mm=depth
                )
            )
        inward_fractions = [float(report.support_fraction) for report in inward]
        outward_fractions = [float(report.support_fraction) for report in outward]
        unsupported_area = max(float(report.unsupported_area_mm2) for report in inward)
        # The wrapper has already run these probes for clipping/outward failures.
        # A missing datum face fails before probing, so its fallback is the base set.
        if helper_error != "washer datum has no matching planar wood boundary face":
            diagnostic_probe_count = 2 * len(helper.DEPTHS_MM)
    all_values = inward_fractions + outward_fractions
    numerical_support_valid = all(
        math.isfinite(value) and -SUPPORT_TOLERANCE <= value <= 1.0 + SUPPORT_TOLERANCE
        for value in all_values
    )
    inward_full = (
        numerical_support_valid and min(inward_fractions) >= 1.0 - SUPPORT_TOLERANCE
    )
    outward_clear = (
        numerical_support_valid and max(outward_fractions) <= SUPPORT_TOLERANCE
    )
    datum_valid = bool(planes) and datum_error is None
    modeled_support = (
        numerical_support_valid and inward_full and outward_clear and datum_valid
    )

    if wrapped is not None:
        require_source(
            modeled_support,
            f"seat helper returned support despite failing independent probe status at {member_id}/{role}",
        )
        helper_status = "full_support_returned"
        geometry_reasons: list[str] = []
    else:
        require_source(
            not modeled_support,
            f"seat helper reported modeled incompatibility despite complete direct support at {member_id}/{role}",
        )
        helper_status = "modeled_support_exception"
        geometry_reasons = []
        if datum_error:
            geometry_reasons.append("no_matching_planar_datum_face")
        if not numerical_support_valid:
            geometry_reasons.append("nonfinite_or_out_of_range_support_probe")
        if not inward_full:
            geometry_reasons.append("inward_annulus_clipped_by_modeled_wood_boundary")
        if not outward_clear:
            geometry_reasons.append("outward_probe_overlaps_modeled_wood")
        if not geometry_reasons and helper_error:
            geometry_reasons.append(
                classify_support_helper_error(helper_error)
                or "modeled_geometry_incompatibility"
            )

    return {
        "support_status": "full_modeled_support"
        if modeled_support
        else "conditional_incompatibility",
        "helper_status": helper_status,
        "geometry_incompatibility_reasons": geometry_reasons,
        "helper_exception": helper_error,
        "datum_face_status": "matched_coplanar_planar_face"
        if datum_valid
        else "no_matching_planar_datum_face",
        "matching_planar_face_count": len(planes),
        "maximum_plane_offset_mm": max(
            (float(row["plane_offset_mm"]) for row in planes), default=None
        ),
        "minimum_absolute_normal_alignment": min(
            (float(row["normal_alignment"]) for row in planes), default=None
        ),
        "depths_mm": [float(depth) for depth in helper.DEPTHS_MM],
        "inward_support_fraction_by_depth": {
            f"{depth:g}": value
            for depth, value in zip(helper.DEPTHS_MM, inward_fractions, strict=True)
        },
        "outward_overlap_fraction_by_depth": {
            f"{depth:g}": value
            for depth, value in zip(helper.DEPTHS_MM, outward_fractions, strict=True)
        },
        "minimum_inward_support_fraction": min(inward_fractions),
        "maximum_outward_overlap_fraction": max(outward_fractions),
        "maximum_inward_unsupported_area_mm2": unsupported_area,
        "additional_diagnostic_probe_count": diagnostic_probe_count,
        "inward_support_tolerance": SUPPORT_TOLERANCE,
        "outward_overlap_tolerance": SUPPORT_TOLERANCE,
    }


def axial_sign_and_pressure(
    *,
    action: dict[str, Any],
    seat: dict[str, Any],
    axis: tuple[float, float, float],
) -> dict[str, Any]:
    force_on_block = finite_vector(
        action.get("axial_force_on_block_n"), "axial_force_on_block_n"
    )
    receiver_force = (
        force_on_block if seat["owner_role"] == "block" else scale(force_on_block, -1.0)
    )
    inward = finite_vector(seat["seat_inward_normal_global_xyz"], "seat inward normal")
    signed_axial = dot(receiver_force, inward)
    reported_tension = float(action.get("axial_tension_n"))
    require_source(math.isfinite(reported_tension), "nonfinite frozen axial_tension_n")
    require_source(reported_tension >= 0.0, "source axial_tension_n is negative")
    block_projection = dot(force_on_block, axis)
    rounding = finite_vector(
        action.get("axial_force_rounding_radius_n"), "axial_force_rounding_radius_n"
    )
    allowed = AXIAL_ABSOLUTE_TOLERANCE_N + math.fsum(
        abs(axis[index]) * rounding[index] for index in range(3)
    )
    require_source(
        abs(abs(block_projection) - reported_tension) <= allowed,
        "signed source axial vector does not reproduce its nonnegative tension scalar",
    )
    transverse_force = subtract(force_on_block, scale(axis, block_projection))
    require_source(
        norm(transverse_force) <= allowed,
        "source axial tie force is not parallel to its signed bolt axis",
    )
    if signed_axial > allowed:
        physical_state = "tension_into_wood_seat"
        washer_pressure_demand = signed_axial
    elif signed_axial < -allowed:
        physical_state = "compression_unloading_wood_seat"
        washer_pressure_demand = 0.0
    else:
        physical_state = "unloaded"
        washer_pressure_demand = 0.0
    return {
        "force_on_receiver_member_n": list(receiver_force),
        "signed_axis_component_on_block_n": block_projection,
        "signed_axial_load_into_receiver_member_n": signed_axial,
        "reported_axial_tension_magnitude_n": reported_tension,
        "physical_axial_state": physical_state,
        "washer_pressure_demand_n": washer_pressure_demand,
        "pressure_is_counted_only_for_positive_tension": True,
        "source_rounding_allowance_n": allowed,
    }


def pressure_reference(
    *,
    signed: dict[str, Any],
    seat: dict[str, Any],
    support: dict[str, Any],
    scenario: dict[str, Any],
    fc_perp_psi: float,
) -> dict[str, Any]:
    demand = float(signed["washer_pressure_demand_n"])
    state = str(signed["physical_axial_state"])
    area = float(scenario["annulus_area_mm2"])
    fc_mpa = fc_perp_psi * PSI_TO_N_PER_MM2
    capacity = area * fc_mpa
    if state == "compression_unloading_wood_seat":
        status = "compression_not_counted_as_washer_pressure"
        pressure = ratio = None
    elif state == "unloaded":
        status = "unloaded_no_washer_pressure_demand"
        pressure = ratio = None
    elif support["support_status"] != "full_modeled_support":
        status = "conditional_incompatibility_no_full_annulus_pressure_comparison"
        pressure = ratio = None
    elif seat["grain_relation"] == "parallel_to_bolt_axis":
        status = "unresolved_grain_parallel_pressure_route"
        pressure = ratio = None
    elif seat["grain_relation"] == "oblique_to_bolt_axis_unresolved":
        status = "unresolved_oblique_grain_pressure_route"
        pressure = ratio = None
    elif seat["grain_relation"] == "perpendicular_to_bolt_axis":
        pressure = demand / area
        ratio = pressure / fc_mpa
        status = "conditional_fc_perp_ideal_annulus_reference_only"
    else:
        raise SourceEvidenceError(
            f"unknown conditional grain relation: {seat['grain_relation']}"
        )
    return {
        "scenario_id": scenario["scenario_id"],
        "modeled_support_status": support["support_status"],
        "physical_axial_state": state,
        "signed_axial_load_into_receiver_member_n": signed[
            "signed_axial_load_into_receiver_member_n"
        ],
        "washer_pressure_demand_n": demand,
        "grain_relation": seat["grain_relation"],
        "pressure_route_status": status,
        "annulus_area_mm2": area,
        "ideal_full_annulus_capacity_at_fc_perp_n": capacity,
        "fc_perp_psi": fc_perp_psi,
        "fc_perp_n_per_mm2": fc_mpa,
        "ideal_full_annulus_average_pressure_n_per_mm2": pressure,
        "fc_perp_reference_ratio": ratio,
        "reference_ratio_le_1": None if ratio is None else ratio <= 1.0,
    }


def input_sources() -> tuple[
    dict[str, dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    hashes: dict[str, dict[str, Any]] = {}
    for label, (relative, expected) in SOURCE_PINS.items():
        hashes[label] = {
            "path": relative.as_posix(),
            "sha256": verify_hash(relative, expected, label),
        }
    sources = {}
    for packet, (relative, expected) in UPPER_INPUTS.items():
        hashes[f"{packet} upper joint source"] = {
            "path": relative.as_posix(),
            "sha256": verify_hash(relative, expected, f"{packet} upper joint source"),
        }
        report = read_json(relative)
        require_source(
            report.get("candidate") == EXPECTED_CANDIDATE,
            f"{packet} candidate identity changed",
        )
        require_source(
            report.get("geometry_revision_id") == EXPECTED_REVISION,
            f"{packet} geometry revision changed",
        )
        for key in (
            "native_solve_executed_by_this_packet",
            "reviewed_geometry_changed",
            "complete_joint_resistance_established",
            "structural_released",
            "fabrication_released",
            "drilling_released",
            "six_case_envelope_established",
        ):
            require_source(
                report.get(key) is False,
                f"{packet} source has an unexpected {key} status",
            )
        sources[packet] = report
    fasteners = read_json(FASTENER_INPUTS)
    bundle = read_json(MEMBER_BUNDLE)
    require_source(
        bundle.get("candidate") == EXPECTED_CANDIDATE,
        "finished member bundle candidate changed",
    )
    require_source(
        bundle.get("geometry_revision_id") == EXPECTED_REVISION,
        "finished member bundle revision changed",
    )
    return sources, fasteners, bundle, hashes


def build_report() -> dict[str, Any]:
    source_reports, fasteners, bundle, verified_hashes = input_sources()
    helper = load_support_helper()
    require_source(
        tuple(float(value) for value in helper.DEPTHS_MM) == (0.01, 0.05, 0.1),
        "pinned washer probe depths changed",
    )
    require_source(
        float(helper.PLANE_TOLERANCE_MM) == 1e-5, "pinned seat datum tolerance changed"
    )
    require_source(
        float(helper.NORMAL_TOLERANCE) == 1e-8, "pinned seat normal tolerance changed"
    )
    require_source(
        float(helper.SUPPORT_TOLERANCE) == SUPPORT_TOLERANCE,
        "pinned support fraction tolerance changed",
    )
    scenarios = catalog_scenarios(fasteners, helper)
    fc_perp_values = [
        float(
            report.get("method_scenarios", {}).get("washer", {}).get("wood_fc_perp_psi")
        )
        for report in source_reports.values()
    ]
    require_source(
        fc_perp_values == [625.0, 625.0], "upper source Fc-perp reference changed"
    )
    for packet, report in source_reports.items():
        require_source(
            report.get("counts", {}).get("physical_bolts") == EXPECTED_AXES_PER_PACKET,
            f"{packet} physical bolt count changed",
        )
        require_source(
            report.get("counts", {}).get("bolt_action_records")
            == EXPECTED_AXES_PER_PACKET * 21,
            f"{packet} source action count changed",
        )
        require_source(
            len(report.get("geometry_by_axis", {})) == EXPECTED_AXES_PER_PACKET,
            f"{packet} geometry axis count changed",
        )

    bindings = member_step_bindings(source_reports, bundle)
    shapes, readbacks = load_member_solids(bindings, helper)
    cad_versions = {
        "cadquery": str(getattr(helper.cq, "__version__", "unknown")),
        "ocp": str(getattr(helper.OCP, "__version__", "unknown")),
    }

    geometry_seats = []
    support_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    source_actions: list[dict[str, Any]] = []
    axis_inventory: set[tuple[str, str]] = set()
    source_state_ids: set[str] = set()
    source_scalar_negative_count = 0
    source_scalar_zero_count = 0
    source_signed_projection_mismatches = 0

    for packet, report in source_reports.items():
        axes = report["geometry_by_axis"]
        action_rows = report["bolt_actions"]
        axis_inventory.update((packet, axis_id) for axis_id in axes)
        actions_by_axis: dict[str, list[dict[str, Any]]] = {}
        for action in action_rows:
            actions_by_axis.setdefault(str(action["axis_id"]), []).append(action)
        require_source(
            set(actions_by_axis) == set(axes),
            f"{packet} action and geometry axis inventories differ",
        )
        require_source(
            len(action_rows) == EXPECTED_AXES_PER_PACKET * 21,
            f"{packet} source action count changed",
        )

        for axis_id, geometry in sorted(axes.items()):
            axis = normalized(
                finite_vector(
                    geometry.get("head_to_nut_axis_xyz"), f"{axis_id} head-to-nut axis"
                ),
                f"{axis_id} head-to-nut axis",
            )
            seats = bind_outer_seats(geometry)
            geometry_block = str(geometry.get("block"))
            geometry_host = str(geometry.get("host"))
            require_source(
                geometry_block and geometry_host and geometry_block != geometry_host,
                f"invalid receiver identity for {axis_id}",
            )
            endpoint_span = norm(
                subtract(
                    finite_vector(
                        geometry["outer_seat_endpoints_xyz_mm"][1],
                        "outer seat endpoint",
                    ),
                    finite_vector(
                        geometry["outer_seat_endpoints_xyz_mm"][0],
                        "outer seat endpoint",
                    ),
                )
            )
            grip = math.fsum(
                float(row["bearing_length_mm"]) for row in geometry["members"].values()
            )
            require_source(
                abs(endpoint_span - grip) <= FACE_COORDINATE_TOLERANCE_MM,
                f"outer seat span differs from member stack at {axis_id}",
            )

            for seat_role, seat in seats.items():
                require_source(
                    seat["owner_member_id"] == str(geometry[seat["owner_role"]]),
                    f"{seat_role} member-role binding differs from axis geometry at {axis_id}",
                )
                member_id = seat["owner_member_id"]
                require_source(
                    member_id in shapes,
                    f"seat owner has no validated solid: {member_id}",
                )
                scenario_support = {}
                for scenario in scenarios:
                    support = seat_support_result(
                        helper=helper,
                        body=shapes[member_id],
                        seat=seat,
                        axis=axis,
                        scenario=scenario,
                    )
                    scenario_support[scenario["scenario_id"]] = support
                    support_by_key[
                        (packet, axis_id, seat_role, scenario["scenario_id"])
                    ] = support
                geometry_record = {
                    "source_packet": packet,
                    "axis_id": axis_id,
                    "block": geometry_block,
                    "host": geometry_host,
                    **seat,
                    "scenario_support": scenario_support,
                }
                geometry_seats.append(geometry_record)

            axis_actions = actions_by_axis[axis_id]
            state_keys = set()
            for action in axis_actions:
                require_source(
                    action.get("block") == geometry_block
                    and action.get("host") == geometry_host,
                    f"action receiver identity differs from signed geometry at {axis_id}",
                )
                require_source(
                    action.get("case") in EXPECTED_CASES,
                    f"unknown source case at {axis_id}",
                )
                require_source(
                    action.get("increment_index") in EXPECTED_INCREMENT_INDICES,
                    f"unknown increment index at {axis_id}",
                )
                state_key = (action["case"], int(action["increment_index"]))
                require_source(
                    state_key not in state_keys,
                    f"duplicate source state for {axis_id}: {state_key}",
                )
                state_keys.add(state_key)
                state_id = f"{packet}:{axis_id}:{action['case']}:i{int(action['increment_index']):02d}"
                require_source(
                    state_id not in source_state_ids,
                    f"duplicate source action identity: {state_id}",
                )
                source_state_ids.add(state_id)
                require_source(
                    str(action.get("axial_source_name", "")).endswith(
                        "/outer-seat-axial-tie"
                    ),
                    f"source action is not an outer-seat axial tie at {state_id}",
                )
                tension = float(action.get("axial_tension_n"))
                if tension < 0.0:
                    source_scalar_negative_count += 1
                if tension == 0.0:
                    source_scalar_zero_count += 1
                force_on_block = finite_vector(
                    action.get("axial_force_on_block_n"), f"{state_id} axial force"
                )
                projection = dot(force_on_block, axis)
                if (
                    abs(abs(projection) - max(0.0, tension))
                    > AXIAL_ABSOLUTE_TOLERANCE_N
                ):
                    source_signed_projection_mismatches += 1
                source_actions.append(
                    {
                        "source_packet": packet,
                        "state_id": state_id,
                        "axis_id": axis_id,
                        "action": action,
                        "axis": axis,
                        "seats": seats,
                    }
                )
            require_source(
                state_keys
                == {
                    (case, index)
                    for case in EXPECTED_CASES
                    for index in EXPECTED_INCREMENT_INDICES
                },
                f"state coverage incomplete for {axis_id}",
            )
        require_source(
            all(len(actions_by_axis[axis_id]) == 21 for axis_id in axes),
            f"not all axes have 21 source states in {packet}",
        )

    require_source(
        len(axis_inventory) == EXPECTED_BOLTS, "expected 32 unique physical upper bolts"
    )
    require_source(
        len(geometry_seats) == EXPECTED_GEOMETRY_SEATS,
        "expected 64 geometry-bound washer seats",
    )
    require_source(
        len(source_state_ids) == EXPECTED_SOURCE_STATES,
        "expected all 672 source states",
    )
    require_source(
        source_scalar_negative_count == 0,
        "frozen axial_tension_n contains a negative value",
    )
    require_source(
        source_signed_projection_mismatches == 0,
        "signed axial vector does not reproduce source tension scalar",
    )

    seat_states = []
    state_force_signs: dict[str, list[float]] = {}
    pressure_summary: dict[str, dict[str, Any]] = {
        scenario["scenario_id"]: {
            "eligible_supported_perpendicular_positive_tension_states": 0,
            "max_fc_perp_reference_ratio": 0.0,
            "governing_state_id": None,
            "conditional_geometry_incompatibility_state_count": 0,
            "parallel_or_oblique_route_unresolved_state_count": 0,
            "compression_states_not_counted_as_pressure": 0,
            "unloaded_states": 0,
        }
        for scenario in scenarios
    }
    for source in source_actions:
        packet = source["source_packet"]
        axis_id = source["axis_id"]
        action = source["action"]
        axis = source["axis"]
        for seat_role, seat in source["seats"].items():
            signed = axial_sign_and_pressure(action=action, seat=seat, axis=axis)
            state_force_signs.setdefault(source["state_id"], []).append(
                float(signed["signed_axial_load_into_receiver_member_n"])
            )
            scenario_results = []
            for scenario in scenarios:
                support = support_by_key[
                    (packet, axis_id, seat_role, scenario["scenario_id"])
                ]
                pressure = pressure_reference(
                    signed=signed,
                    seat=seat,
                    support=support,
                    scenario=scenario,
                    fc_perp_psi=625.0,
                )
                scenario_results.append(
                    {
                        "scenario_id": pressure["scenario_id"],
                        "pressure_route_status": pressure["pressure_route_status"],
                        "ideal_full_annulus_average_pressure_n_per_mm2": pressure[
                            "ideal_full_annulus_average_pressure_n_per_mm2"
                        ],
                        "fc_perp_reference_ratio": pressure["fc_perp_reference_ratio"],
                    }
                )
                summary = pressure_summary[scenario["scenario_id"]]
                if (
                    pressure["pressure_route_status"]
                    == "conditional_fc_perp_ideal_annulus_reference_only"
                ):
                    summary[
                        "eligible_supported_perpendicular_positive_tension_states"
                    ] += 1
                    ratio = float(pressure["fc_perp_reference_ratio"])
                    if ratio > summary["max_fc_perp_reference_ratio"]:
                        summary["max_fc_perp_reference_ratio"] = ratio
                        summary["governing_state_id"] = (
                            f"{source['state_id']}:{seat_role}"
                        )
                elif (
                    pressure["pressure_route_status"]
                    == "conditional_incompatibility_no_full_annulus_pressure_comparison"
                ):
                    summary["conditional_geometry_incompatibility_state_count"] += 1
                elif pressure["pressure_route_status"] in (
                    "unresolved_grain_parallel_pressure_route",
                    "unresolved_oblique_grain_pressure_route",
                ):
                    summary["parallel_or_oblique_route_unresolved_state_count"] += 1
                elif (
                    pressure["pressure_route_status"]
                    == "compression_not_counted_as_washer_pressure"
                ):
                    summary["compression_states_not_counted_as_pressure"] += 1
                elif (
                    pressure["pressure_route_status"]
                    == "unloaded_no_washer_pressure_demand"
                ):
                    summary["unloaded_states"] += 1
            seat_states.append(
                {
                    "source_packet": packet,
                    "source_state_id": source["state_id"],
                    "axis_id": axis_id,
                    "case": action["case"],
                    "increment_index": action["increment_index"],
                    "load_factor": action["load_factor"],
                    "axial_source_name": action["axial_source_name"],
                    "axial_source_row_ids": action["axial_source_row_ids"],
                    "seat_role": seat_role,
                    "seat_owner_role": seat["owner_role"],
                    "seat_owner_member_id": seat["owner_member_id"],
                    "grain_relation": seat["grain_relation"],
                    **signed,
                    "scenario_results": scenario_results,
                }
            )

    for state_id, signs in state_force_signs.items():
        require_source(
            len(signs) == 2,
            f"source state does not retain both outer seat identities: {state_id}",
        )
        require_source(
            abs(signs[0] - signs[1]) <= AXIAL_ABSOLUTE_TOLERANCE_N,
            f"outer seats have different physical axial signs: {state_id}",
        )
    require_source(
        len(seat_states) == EXPECTED_SEAT_STATES,
        "expected all 1,344 seat-state records",
    )
    require_source(
        all(len(row["scenario_results"]) == 3 for row in seat_states),
        "a seat state lost one or more annulus scenarios",
    )

    modeled_geometry_failures = sum(
        support["support_status"] != "full_modeled_support"
        for support in support_by_key.values()
    )
    geometry_status = (
        "full_modeled_support_at_all_tested_seats"
        if modeled_geometry_failures == 0
        else "conditional_incompatibility_detected"
    )
    support_base_probe_count = len(support_by_key) * len(helper.DEPTHS_MM) * 2
    diagnostic_probe_count = sum(
        int(support["additional_diagnostic_probe_count"])
        for support in support_by_key.values()
    )
    support_probe_count = support_base_probe_count + diagnostic_probe_count
    state_case_counts = Counter(
        (row["source_packet"], row["case"], row["increment_index"])
        for row in seat_states
    )
    require_source(
        len(state_case_counts) == 2 * 3 * 7,
        "unexpected case/increment/seat identity count",
    )

    return {
        "schema": "upper-block-washer-seat-axial-study/v1",
        "status": "bounded_conditional_seat_support_and_axial_reference_only",
        "source_integrity_status": "verified",
        "modeled_geometry_status": geometry_status,
        "modeled_geometry_incompatibility_count": int(modeled_geometry_failures),
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "target_scope": "32 physical bolts across the 16 uppermost and 16 service upper-block axes; both outer nominal washer seats per axis.",
        "source_pins": verified_hashes,
        "cad_readback_environment": cad_versions,
        "geometry_method": {
            "seat_owner_source": "Signed head_to_nut_axis_xyz orders the two outer endpoints; each endpoint is matched to a unique member face from the per-member bolt-line midpoint and half bearing length. The block is not presumed to carry the head.",
            "member_face_coordinate_tolerance_mm": FACE_COORDINATE_TOLERANCE_MM,
            "datum_plane_offset_tolerance_mm": float(helper.PLANE_TOLERANCE_MM),
            "datum_normal_alignment_tolerance": float(helper.NORMAL_TOLERANCE),
            "support_fraction_tolerance": float(helper.SUPPORT_TOLERANCE),
            "probe_depths_mm": [float(value) for value in helper.DEPTHS_MM],
            "base_support_probe_count": support_base_probe_count,
            "additional_failure_diagnostic_probe_count": diagnostic_probe_count,
            "readback_bounds_tolerance_mm": READBACK_TOLERANCE_MM,
            "readback_volume_tolerance_mm3": READBACK_VOLUME_TOLERANCE_MM3,
            "readback_surface_area_tolerance_mm2": READBACK_AREA_TOLERANCE_MM2,
            "annulus_test_directions": ["inward into wood", "outward from datum face"],
            "step_readback_basis": "Pinned current-finished-member bundle manifest plus per-member STEP SHA-256; imported solid count, validity, face count, volume, bounds, and surface areas are matched to manifest readbacks.",
        },
        "source_contract": {
            "source_action_state_count": len(source_state_ids),
            "source_state_identity_fields": [
                "source packet",
                "axis ID",
                "case",
                "increment index",
                "axial source name",
                "axial source row IDs",
            ],
            "geometry_seat_count": len(geometry_seats),
            "seat_state_count": len(seat_states),
            "seat_state_identity_fields": [
                "source packet",
                "source action state ID",
                "axis ID",
                "case",
                "increment index",
                "seat role",
                "seat owner member ID",
            ],
            "annulus_scenarios_per_seat_state": 3,
            "modeled_support_probe_count": support_probe_count,
            "all_source_states_retained": True,
            "all_two_seat_states_retained": True,
            "discarded_source_states": 0,
            "discarded_seat_states": 0,
            "discard_conditions": "none; retain zero and any signed negative axial state for classification",
        },
        "axial_source_check": {
            "reported_axial_tension_negative_value_count": source_scalar_negative_count,
            "reported_axial_tension_zero_or_within_tolerance_count": source_scalar_zero_count,
            "signed_axis_projection_mismatch_count": source_signed_projection_mismatches,
            "all_source_axial_tension_scalars_nonnegative": True,
            "source_force_vector_check": "signed block vector projected onto the signed head-to-nut axis reproduces the frozen nonnegative tension scalar in magnitude; each receiver seat's signed load is then projected into that member's inward face normal.",
            "two_outer_seats_same_signed_physical_state_per_source_state": True,
            "negative_signed_seat_load_pressure_rule": "physical compression/unloading is preserved with its sign and assigned zero washer pressure demand; it is never converted to positive pressure by absolute value.",
            "max_source_axial_rounding_allowance_n": max(
                float(row["source_rounding_allowance_n"]) for row in seat_states
            ),
        },
        "washer_annulus_scenarios": scenarios,
        "fc_perp_reference": {
            "value_psi": 625.0,
            "basis": "Pinned upper-review source: 2024 NDS Supplement Table 4A, DF-L No. 2 Fc-perp; ideal uniform pressure over a fully supported washer/wood annulus.",
            "application": "Only for conditional source grain perpendicular to the bolt axis, modeled full annulus support, and positive signed axial seat pressure.",
            "parallel_or_oblique_grain_route": "unresolved; no Fc-perp comparison is applied",
            "status": "conditional_reference_only_not_joint_acceptance",
        },
        "member_step_readbacks": [readbacks[key] for key in sorted(readbacks)],
        "geometry_seats": sorted(
            geometry_seats,
            key=lambda row: (row["source_packet"], row["axis_id"], row["seat_role"]),
        ),
        "seat_states": seat_states,
        "pressure_reference_summary": pressure_summary,
        "claim_limits": {
            "geometry_only": "BREP support is a modeled footprint check at saved seat poses. It does not prove actual flatness, contact, delivered washer fit, physical cuts, or the absence of unexported cuts.",
            "load_only": "The axial tie is a separate signed scalar/vector per source state and is not combined with a different state's lateral maximum or with group capacity.",
            "wood_pressure": "The 625 psi Fc-perp comparison is an ideal full-annulus reference. It does not establish washer bending/spreading, cap-head or nut bearing-face fit, splitting, load redistribution, adjustments, complete-joint capacity, or acceptance.",
            "hardware": "CAD washer dimensions and catalog Type A Wide dimensional extremes are conditional geometry scenarios. No washer, bolt, or nut is selected or verified as delivered.",
            "release": "No native solve was run. This packet does not authorize cutting, drilling, fabrication, structural release, or climbing.",
        },
        "joint_accepted": False,
        "six_case_envelope_established": False,
        "fabrication_released": False,
        "drilling_released": False,
        "native_solve_run": False,
        "producer_sha256": sha256(HERE / "seats.py"),
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="rebuild the source-bound report and compare exact bytes with ignored seats.json",
    )
    arguments = parser.parse_args(argv)
    try:
        report = build_report()
        payload = canonical_json(report)
        if arguments.verify:
            require_source(
                OUTPUT.is_file(),
                f"missing generated report: {OUTPUT.relative_to(ROOT)}",
            )
            require_source(
                OUTPUT.read_bytes() == payload.encode("utf-8"),
                "seats.json differs from the current source-bound replay",
            )
            print(
                f"verified: {len(report['geometry_seats'])} seats, "
                f"{len(report['seat_states'])} seat states, "
                f"{report['modeled_geometry_status']}"
            )
        else:
            OUTPUT.write_text(payload, encoding="utf-8")
            print(
                f"wrote {OUTPUT.relative_to(ROOT)}: {len(report['geometry_seats'])} seats, "
                f"{len(report['seat_states'])} seat states, "
                f"{report['modeled_geometry_status']}"
            )
    except (SourceEvidenceError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
