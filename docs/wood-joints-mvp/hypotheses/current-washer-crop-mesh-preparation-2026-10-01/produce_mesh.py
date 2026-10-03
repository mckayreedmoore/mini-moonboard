"""Parent-gated producer for one R75/H1 C3D10 mesh-only attempt.

This file is source preparation only in this checkout. It has no default run,
no retry, no Docker call, no solver path and no material/contact/load cards.
It refuses to build geometry or a mesh without an exact parent freeze, a fresh
parent runtime preflight receipt and the one-run reservation. No such freeze or
receipt is included here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mesh_oracles
import prepare

from fea import wood_joint_patch_mesh as wood_mesh
from fea.stitch_joint_mesh import (
    GMSH_TO_CCX,
    append_body,
    external_faces,
    surface_faces,
    validate_and_remap_surface_coverage,
    validate_ownership,
)

BRANCH = "R75_H1_R_T_A_K12_catalog_nominal_frictionless_mesh_only"
FREEZE_SCHEMA = "conditional_washer_crop_mesh_parent_freeze/v1"
PREFLIGHT_SCHEMA = "conditional_washer_crop_mesh_runtime_preflight/v1"
REPORT_SCHEMA = "conditional_washer_crop_mesh_report/v1"
REPORT_STATUS = "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER"
BODY_IDS = mesh_oracles.BODY_IDS
EXPECTED_RUNTIME = {"python": "3.12.3", "numpy": "1.26.4", "gmsh": "4.12.1"}
EXPECTED_SOURCE_STEP_SHA256 = "9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58"
EXPECTED_SOURCE_STEP = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-member-solids-attempt01/bundle/members/"
    "base_principal_center_right.step"
)
LIMITS = {
    "launch_limit": 1,
    "retry_budget": 0,
    "timeout_seconds": 300,
    "cpus": 2,
    "memory_bytes": 4_294_967_296,
    "scratch_bytes": 536_870_912,
    "network": "none",
    "source_mount_read_only": True,
    "mesh_only": True,
}
LOCAL_MESH = {"global_max_size_mm": 40.0, "local_min_size_mm": 0.8, "refinement_band_mm": 12.0}
OD_MM, ID_MM, WASHER_T_MM = 18.653125, 7.9248, 1.5875
NUT_HEIGHT_MM = 5.55625
LOAD_FACE_X_MM = -7.14375
WASHER_NUT_X_MM = -1.5875


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_object(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} is unavailable or invalid JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a JSON object")
    return value


def _require_parent_authorization(freeze_path: Path, preflight_path: Path) -> tuple[dict, dict, dict]:
    freeze_bytes = freeze_path.read_bytes()
    preflight_bytes = preflight_path.read_bytes()
    freeze = _read_object(freeze_path, "parent freeze")
    preflight = _read_object(preflight_path, "runtime preflight receipt")
    if freeze.get("schema") != FREEZE_SCHEMA or freeze.get("status") != "PARENT_FROZEN_ONE_RUN_AUTHORIZED":
        raise ValueError("an exact parent-owned one-run freeze is required")
    if freeze.get("branch") != BRANCH or freeze.get("candidate") != "compact-floor-flush-wood-joints-development" or freeze.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("parent freeze does not bind the reviewed R75/H1 branch")
    prep = prepare.build_record()
    if freeze.get("source_preparation_record_sha256") != prep["record_sha256"]:
        raise ValueError("source-preparation record drifted from the parent freeze")
    if freeze.get("source_pins_sha256") != prep["source_pins_sha256"]:
        raise ValueError("source pins drifted from the parent freeze")
    if freeze.get("source_preparation_code_sha256") != prep["source_preparation_code_sha256"]:
        raise ValueError("source preparation code drifted from the parent freeze")
    reservation = freeze.get("one_run_reservation")
    if not isinstance(reservation, dict) or reservation.get("status") != "RESERVED" or reservation.get("retry_budget") != 0 or reservation.get("launch_limit") != 1 or reservation.get("timeout_seconds") != 300 or not reservation.get("reservation_id"):
        raise ValueError("parent has not reserved exactly one zero-retry mesh launch")
    if freeze.get("preflight_receipt_sha256") != hashlib.sha256(preflight_bytes).hexdigest():
        raise ValueError("runtime preflight receipt bytes differ from the parent freeze")
    if preflight.get("schema") != PREFLIGHT_SCHEMA or preflight.get("status") != "PASS_PARENT_RUNTIME_PREFLIGHT":
        raise ValueError("parent runtime preflight did not pass")
    observed = preflight.get("observed_unix_seconds")
    if isinstance(observed, bool) or not isinstance(observed, (int, float)) or time.time() - float(observed) > 300 or float(observed) > time.time() + 2:
        raise ValueError("parent runtime preflight receipt is stale or future-dated")
    if preflight.get("runtime") != EXPECTED_RUNTIME or preflight.get("image_id") != freeze.get("image_id"):
        raise ValueError("preflight runtime/image differs from the frozen toolchain")
    resources = preflight.get("resources")
    if not isinstance(resources, dict) or any(resources.get(key) != value for key, value in LIMITS.items() if key not in {"launch_limit", "retry_budget", "timeout_seconds"}) or resources.get("timeout_seconds") != 300 or resources.get("output_mount_writable") is not True:
        raise ValueError("preflight resources differ from the hard one-run budget")
    readiness = freeze.get("qualified_methods")
    required_qualifications = (
        "gmsh_occ_intersect_face_ancestry_known_answer_passed",
        "gmsh_occ_supported_surface_signature_known_answer_passed",
        "gmsh_high_order_surface_element_api_verified",
        "gmsh_high_order_jacobian_api_verified",
    )
    if not isinstance(readiness, dict) or any(readiness.get(key) is not True for key in required_qualifications):
        raise ValueError("required Gmsh Boolean/mesh API method qualification is absent")
    if freeze.get("mechanics_cards_authorized") is not False or freeze.get("solver_launch_authorized") is not False or freeze.get("candidate_acceptance_authorized") is not False:
        raise ValueError("parent freeze exceeds the mesh-only task scope")
    if len(freeze_bytes) == 0:
        raise ValueError("empty parent freeze")
    return freeze, preflight, prep


def _check_gmsh_runtime(gmsh: Any, numpy: Any) -> None:
    observed = {
        "python": platform.python_version(),
        "numpy": str(numpy.__version__),
        "gmsh": str(gmsh.__version__),
    }
    if observed != EXPECTED_RUNTIME:
        raise ValueError(f"runtime version drift: {observed}")
    if gmsh.isInitialized():
        raise ValueError("producer requires a fresh Gmsh session")
    for owner, name in ((gmsh.model.occ, "intersect"), (gmsh.model.occ, "copy"), (gmsh.model.occ, "addCone"), (gmsh.model, "getNormal"), (gmsh.model, "getParametrizationBounds"), (gmsh.model.mesh, "getJacobians")):
        if not callable(getattr(owner, name, None)):
            raise ValueError(f"pinned Gmsh API is missing {name}")


def _output_directory(path: Path, freeze: dict[str, Any]) -> Path:
    requested = Path(os.path.abspath(path))
    frozen = Path(os.path.abspath(freeze.get("output_directory", "")))
    if requested != frozen:
        raise ValueError("mesh output path differs from the parent freeze")
    if requested.exists() or requested.is_symlink() or not requested.parent.is_dir() or requested.parent.is_symlink():
        raise FileExistsError("mesh output must be a new directory under a real precreated parent")
    resolved = requested.resolve(strict=False)
    if resolved.is_relative_to(ROOT) or resolved == Path("/"):
        raise ValueError("mesh output must be isolated outside the source tree")
    if not os.access(resolved.parent, os.W_OK):
        raise PermissionError("isolated mesh output parent is not writable")
    return resolved


def _write_new(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def _write_json(path: Path, value: Any) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    _write_new(path, payload)


def _global_from_local(frame: dict[str, Any], xyz: Iterable[float]) -> tuple[float, float, float]:
    local = tuple(float(value) for value in xyz)
    matrix = frame["local_to_global_transform"]
    return tuple(
        matrix[row][3] + math.fsum(matrix[row][column] * local[column] for column in range(3))
        for row in range(3)
    )


def _vector_to_local(frame: dict[str, Any], vector: Iterable[float]) -> tuple[float, float, float]:
    raw = tuple(float(value) for value in vector)
    matrix = frame["local_to_global_transform"]
    return tuple(math.fsum(matrix[row][column] * raw[row] for row in range(3)) for column in range(3))


def _canonical_sign(vector: Iterable[float]) -> tuple[float, float, float]:
    values = tuple(float(value) for value in vector)
    for value in values:
        if abs(value) > 1e-12:
            return tuple(-item for item in values) if value < 0 else values
    raise ValueError("degenerate analytic surface direction")


def _unit(vector: Iterable[float]) -> tuple[float, float, float]:
    values = tuple(float(value) for value in vector)
    length = math.sqrt(math.fsum(value * value for value in values))
    if len(values) != 3 or not math.isfinite(length) or length <= 1e-12:
        raise ValueError("invalid analytic surface vector")
    return tuple(value / length for value in values)


def _surface_samples(gmsh: Any, tag: int, frame: dict[str, Any] | None) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    low, high = gmsh.model.getParametrizationBounds(2, tag)
    u0, v0 = (float(value) for value in low)
    u1, v1 = (float(value) for value in high)
    points: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    for fu in (0.13, 0.31, 0.5, 0.69, 0.87):
        for fv in (0.13, 0.31, 0.5, 0.69, 0.87):
            uv = [u0 + fu * (u1 - u0), v0 + fv * (v1 - v0)]
            xyz = tuple(float(value) for value in gmsh.model.getValue(2, tag, uv))
            normal = tuple(float(value) for value in gmsh.model.getNormal(tag, uv))
            if frame is not None:
                xyz = prepare.source_to_local(list(xyz), frame["local_to_global_transform"])
                normal = _vector_to_local(frame, normal)
            points.append(xyz)
            normals.append(_unit(normal))
    return points, normals


def _axis_basis(axis: Iterable[float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    a = _unit(axis)
    seeds = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    seed = min(seeds, key=lambda item: abs(math.fsum(a[i] * item[i] for i in range(3))))
    u = _unit((a[1] * seed[2] - a[2] * seed[1], a[2] * seed[0] - a[0] * seed[2], a[0] * seed[1] - a[1] * seed[0]))
    v = (a[1] * u[2] - a[2] * u[1], a[2] * u[0] - a[0] * u[2], a[0] * u[1] - a[1] * u[0])
    return u, v


def _analytic_surface_signature(gmsh: Any, tag: int, frame: dict[str, Any] | None, numpy: Any) -> dict[str, Any]:
    surface_type = str(gmsh.model.getType(2, tag))
    if surface_type not in mesh_oracles.SUPPORTED_SOURCE_SURFACE_TYPES:
        raise ValueError(f"unsupported analytic face type: {surface_type}")
    points, normals = _surface_samples(gmsh, tag, frame)
    matrix_n = numpy.asarray(normals, dtype=float)
    mean_point = numpy.mean(numpy.asarray(points, dtype=float), axis=0)
    support: dict[str, Any]
    if surface_type == "Plane":
        normal = _canonical_sign(_unit(numpy.mean(matrix_n, axis=0)))
        offset = math.fsum(normal[i] * float(mean_point[i]) for i in range(3))
        residual = max(abs(math.fsum(normal[i] * point[i] for i in range(3)) - offset) for point in points)
        if residual > 1e-7:
            raise ValueError("plane analytic signature sample residual exceeds tolerance")
        support = {"unit_normal": normal, "signed_offset_mm": offset}
    else:
        centered_normals = matrix_n - numpy.mean(matrix_n, axis=0)
        _u, singular, vt = numpy.linalg.svd(centered_normals, full_matrices=False)
        if len(singular) < 3 or singular[-1] > max(1e-7, singular[0] * 1e-6):
            raise ValueError(f"{surface_type}: sampled normals do not define a unique revolution axis")
        axis = _canonical_sign(vt[-1, :])
        axis_u, axis_v = _axis_basis(axis)
        projected = numpy.asarray(
            [[math.fsum(float(point[i]) * axis_u[i] for i in range(3)), math.fsum(float(point[i]) * axis_v[i] for i in range(3))] for point in points],
            dtype=float,
        )
        if surface_type == "Cylinder":
            normal_uv = numpy.asarray(
                [[math.fsum(float(normal[i]) * axis_u[i] for i in range(3)), math.fsum(float(normal[i]) * axis_v[i] for i in range(3))] for normal in normals],
                dtype=float,
            )
            design = numpy.column_stack((2 * projected[:, 0], 2 * projected[:, 1], numpy.ones(len(points))))
            cx, cy, constant = numpy.linalg.lstsq(design, numpy.sum(projected * projected, axis=1), rcond=None)[0]
            radius = math.sqrt(max(0.0, float(constant + cx * cx + cy * cy)))
            axis_point = tuple(float(cx * axis_u[i] + cy * axis_v[i]) for i in range(3))
            radial_residuals = []
            for point in points:
                delta = tuple(point[i] - axis_point[i] for i in range(3))
                axial = math.fsum(delta[i] * axis[i] for i in range(3))
                radial_residuals.append(abs(math.sqrt(max(0.0, math.fsum((delta[i] - axial * axis[i]) ** 2 for i in range(3)))) - radius))
            if radius <= 0 or max(radial_residuals) > 1e-6:
                raise ValueError("cylinder analytic signature does not fit its sampled BREP")
            support = {"axis_unit": axis, "axis_point_closest_to_local_origin_mm": axis_point, "radius_mm": radius}
        else:
            mean_normal = numpy.mean(matrix_n, axis=0)
            axial_normal = float(numpy.dot(mean_normal, numpy.asarray(axis)))
            sin_angle = min(1.0, abs(axial_normal))
            semi_angle = math.asin(sin_angle)
            cos_angle = math.sqrt(max(0.0, 1 - sin_angle * sin_angle))
            if cos_angle <= 1e-8 or semi_angle <= 1e-8:
                raise ValueError("cone analytic signature has a degenerate semi-angle")
            radial_directions = []
            axial_coordinates = []
            for point, normal in zip(points, normals, strict=True):
                radial = tuple((normal[i] - axial_normal * axis[i]) / cos_angle for i in range(3))
                radial_directions.append(_unit(radial))
                axial_coordinates.append(math.fsum(point[i] * axis[i] for i in range(3)))
            constraints = []
            rhs = []
            for point, radial in zip(points, radial_directions, strict=True):
                projected_point = tuple(point[i] - math.fsum(point[j] * axis[j] for j in range(3)) * axis[i] for i in range(3))
                # The apex axis offset is found from the common center of the
                # radial normal lines; an axial component is fixed to zero.
                for basis in (axis_u, axis_v):
                    constraints.append([basis[i] - math.fsum(basis[j] * radial[j] for j in range(3)) * radial[i] for i in range(3)])
                    rhs.append(math.fsum(basis[i] * projected_point[i] for i in range(3)) - math.fsum(basis[i] * radial[i] for i in range(3)) * math.fsum(projected_point[i] * radial[i] for i in range(3)))
            constraints.append(list(axis))
            rhs.append(0.0)
            axis_origin = numpy.linalg.lstsq(numpy.asarray(constraints), numpy.asarray(rhs), rcond=None)[0]
            radii = [abs(math.fsum((point[i] - axis_origin[i]) * radial[i] for i in range(3))) for point, radial in zip(points, radial_directions, strict=True)]
            apex_axial = [axial - radius / math.tan(semi_angle) for axial, radius in zip(axial_coordinates, radii, strict=True)]
            apex = tuple(float(axis_origin[i] + (sum(apex_axial) / len(apex_axial)) * axis[i]) for i in range(3))
            expected_radii = [abs(axial - (sum(apex_axial) / len(apex_axial))) * math.tan(semi_angle) for axial in axial_coordinates]
            if max(abs(a - b) for a, b in zip(radii, expected_radii, strict=True)) > 1e-5:
                raise ValueError("cone apex/angle signature does not fit its sampled BREP")
            support = {"axis_unit": axis, "apex_mm": apex, "semi_angle_rad": semi_angle}

    boundary_signatures = []
    for dim, signed_tag in gmsh.model.getBoundary([(2, tag)], combined=False, oriented=True):
        if dim != 1:
            raise ValueError("surface boundary contains a noncurve entity")
        curve_tag = abs(int(signed_tag))
        curve_type = str(gmsh.model.getType(1, curve_tag))
        low, high = gmsh.model.getParametrizationBounds(1, curve_tag)
        a, b = float(low[0]), float(high[0])
        samples = [
            tuple(float(value) for value in gmsh.model.getValue(1, curve_tag, [a + f * (b - a)]))
            for f in ((0.2, 0.5, 0.8) if signed_tag > 0 else (0.8, 0.5, 0.2))
        ]
        if frame is not None:
            samples = [prepare.source_to_local(list(point), frame["local_to_global_transform"]) for point in samples]
        center = tuple(float(value) for value in gmsh.model.occ.getCenterOfMass(1, curve_tag))
        if frame is not None:
            center = prepare.source_to_local(list(center), frame["local_to_global_transform"])
        boundary_signatures.append(
            {
                "curve_type": curve_type,
                "length_mm": float(gmsh.model.occ.getMass(1, curve_tag)),
                "center": center,
                "sample_points": samples,
            }
        )
    if frame is not None:
        center = tuple(float(value) for value in gmsh.model.occ.getCenterOfMass(2, tag))
        center = prepare.source_to_local(list(center), frame["local_to_global_transform"])
        raw_bounds = tuple(float(value) for value in gmsh.model.getBoundingBox(2, tag))
        local_corners = [
            prepare.source_to_local([x, y, z], frame["local_to_global_transform"])
            for x in (raw_bounds[0], raw_bounds[1])
            for y in (raw_bounds[2], raw_bounds[3])
            for z in (raw_bounds[4], raw_bounds[5])
        ]
        trim_bounds = [min(point[axis] for point in local_corners) for axis in range(3)] + [max(point[axis] for point in local_corners) for axis in range(3)]
    else:
        center = tuple(float(value) for value in gmsh.model.occ.getCenterOfMass(2, tag))
        trim_bounds = list(float(value) for value in gmsh.model.getBoundingBox(2, tag))
    boundary_signatures.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    signature_payload = {
        "surface_type": surface_type,
        "analytic_support": support,
        "trim_area_mm2": float(gmsh.model.occ.getMass(2, tag)),
        "trim_centroid": center,
        "trim_bounds_local_order": trim_bounds,
        "trim_boundary_curves": boundary_signatures,
    }
    signature_bytes = json.dumps(signature_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {
        "surface_type": surface_type,
        "analytic_support": support,
        "signature_payload": signature_payload,
        "signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
        "area_mm2": float(gmsh.model.occ.getMass(2, tag)),
        "center": center,
    }


def _surface_signatures_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    def close_value(a: Any, b: Any, tolerance: float = 1e-7) -> bool:
        if isinstance(a, bool) or isinstance(b, bool):
            return a is b
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) <= tolerance
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            return len(a) == len(b) and all(close_value(x, y, tolerance) for x, y in zip(a, b, strict=True))
        if isinstance(a, dict) and isinstance(b, dict):
            return set(a) == set(b) and all(close_value(a[key], b[key], tolerance) for key in a)
        return a == b

    if left["surface_type"] != right["surface_type"]:
        return False
    if left["signature_sha256"] == right["signature_sha256"]:
        return True
    if abs(left["area_mm2"] - right["area_mm2"]) > max(1e-8, left["area_mm2"] * 1e-9):
        return False
    if any(abs(left["center"][i] - right["center"][i]) > 1e-7 for i in range(3)):
        return False
    a, b = left["analytic_support"], right["analytic_support"]
    if set(a) != set(b):
        return False
    if not close_value(a, b, 1e-8):
        return False
    if not close_value(
        left["signature_payload"]["trim_bounds_local_order"],
        right["signature_payload"]["trim_bounds_local_order"],
        1e-7,
    ):
        return False
    left_curves = left["signature_payload"]["trim_boundary_curves"]
    right_curves = list(right["signature_payload"]["trim_boundary_curves"])
    if len(left_curves) != len(right_curves):
        return False
    for curve in left_curves:
        candidates = [
            index
            for index, other in enumerate(right_curves)
            if curve["curve_type"] == other["curve_type"]
            and abs(curve["length_mm"] - other["length_mm"]) <= max(1e-8, curve["length_mm"] * 1e-9)
            and close_value(curve["center"], other["center"], 1e-7)
            and (
                close_value(curve["sample_points"], other["sample_points"], 1e-7)
                or close_value(curve["sample_points"], list(reversed(other["sample_points"])), 1e-7)
            )
        ]
        if len(candidates) != 1:
            return False
        right_curves.pop(candidates[0])
    return not right_curves


def _is_r75_cylinder(signature: dict[str, Any], frame: dict[str, Any], target_tn: tuple[float, float]) -> bool:
    if signature["surface_type"] != "Cylinder":
        return False
    support = signature["analytic_support"]
    axis = support["axis_unit"]
    point = support["axis_point_closest_to_local_origin_mm"]
    if abs(abs(axis[0]) - 1) > 1e-8 or abs(axis[1]) > 1e-8 or abs(axis[2]) > 1e-8 or abs(support["radius_mm"] - 75.0) > 1e-7:
        return False
    bounds = signature["signature_payload"]["trim_bounds_local_order"]
    return math.dist(point[1:], target_tn) <= 1e-6 and abs(bounds[0]) <= 1e-6 and abs(bounds[3] - 38.1) <= 1e-6


def _normal_local(gmsh: Any, tag: int, frame: dict[str, Any], uv: list[float]) -> tuple[float, float, float]:
    return _unit(_vector_to_local(frame, gmsh.model.getNormal(tag, uv)))


def _surface_param_samples(gmsh: Any, tag: int, frame: dict[str, Any]) -> list[tuple[float, float, float]]:
    low, high = gmsh.model.getParametrizationBounds(2, tag)
    u0, v0 = (float(value) for value in low)
    u1, v1 = (float(value) for value in high)
    return [
        prepare.source_to_local(
            list(gmsh.model.getValue(2, tag, [u0 + fu * (u1 - u0), v0 + fv * (v1 - v0)])),
            frame["local_to_global_transform"],
        )
        for fu in (0.2, 0.5, 0.8)
        for fv in (0.2, 0.5, 0.8)
    ]


def _classify_hardware_face(
    gmsh: Any,
    tag: int,
    body_id: str,
    frame: dict[str, Any],
    center_tn: tuple[float, float],
    nut_profile: dict[str, Any] | None,
    numpy: Any,
) -> str:
    signature = _analytic_surface_signature(gmsh, tag, frame, numpy)
    points = _surface_param_samples(gmsh, tag, frame)
    area = signature["area_mm2"]
    if nut_profile is None:
        if signature["surface_type"] == "Plane":
            x_values = [point[0] for point in points]
            if max(x_values) - min(x_values) <= 1e-7:
                if abs(sum(x_values) / len(x_values)) <= 1e-7:
                    return f"{body_id}.wood_bearing_annulus"
                if abs(sum(x_values) / len(x_values) - WASHER_NUT_X_MM) <= 1e-7:
                    return f"{body_id}.nut_bearing_annulus"
        if signature["surface_type"] == "Cylinder":
            radius = float(signature["analytic_support"]["radius_mm"])
            if abs(radius - OD_MM / 2) <= 1e-7:
                return f"{body_id}.washer_outer_cylindrical_edge"
            if abs(radius - ID_MM / 2) <= 1e-7:
                return f"{body_id}.washer_bore_cylindrical_edge"
        raise ValueError(f"{body_id}: washer face did not match one exact analytic semantic signature")

    local_bounds = [point[0] for point in points]
    radial = [math.dist(point[1:], center_tn) for point in points]
    x_bar = math.fsum(local_bounds) / len(local_bounds)
    if signature["surface_type"] == "Plane":
        normal = signature["analytic_support"]["unit_normal"]
        if max(local_bounds) - min(local_bounds) <= 1e-7:
            if abs(x_bar - LOAD_FACE_X_MM) <= 1e-7 and abs(area - 75.51784511932227) <= 1e-6:
                return f"{body_id}.outward_hex_load_face"
            if abs(x_bar - WASHER_NUT_X_MM) <= 1e-7 and abs(area - 57.48292325873653) <= 1e-6:
                return f"{body_id}.washer_bearing_land"
        if abs(normal[0]) <= 1e-7:
            offset = float(signature["analytic_support"]["signed_offset_mm"])
            relative_offset = offset - normal[1] * center_tn[0] - normal[2] * center_tn[1]
            outward = normal if relative_offset >= 0 else tuple(-value for value in normal)
            angle = math.degrees(math.atan2(outward[2], outward[1])) % 360
            face_index = min(range(6), key=lambda index: abs(((angle - 60 * index + 180) % 360) - 180))
            if abs(((angle - 60 * face_index + 180) % 360) - 180) <= 1e-6:
                return f"{body_id}.hex_flat_normal_{60 * face_index:03d}deg"
    if signature["surface_type"] == "Cylinder":
        radius = float(signature["analytic_support"]["radius_mm"])
        if abs(radius - 6.4135) <= 1e-6:
            return f"{body_id}.coaxial_corner_clip_cylinder"
        if abs(radius - 3.175) <= 1e-6:
            return f"{body_id}.smooth_through_bore"
    if signature["surface_type"] == "Cone":
        support = signature["analytic_support"]
        if abs(math.degrees(support["semi_angle_rad"]) - 45) > 1e-5:
            raise ValueError(f"{body_id}: unsupported nut cone semi-angle")
        outer_radii = [profile_radius(nut_profile, "outer", point[0]) for point in points]
        inner_radii = [profile_radius(nut_profile, "inner", point[0]) for point in points]
        outer_error = max(abs(a - b) for a, b in zip(radial, outer_radii, strict=True))
        inner_error = max(abs(a - b) for a, b in zip(radial, inner_radii, strict=True))
        if outer_error <= 2e-6:
            return f"{body_id}.bearing_side_outer_conical_relief"
        if inner_error <= 2e-6:
            return f"{body_id}.bearing_side_inner_conical_relief"
    raise ValueError(f"{body_id}: unclassified nut face; unsupported/ambiguous analytic signature")


def profile_radius(profile: dict[str, Any], side: str, source_x: float) -> float:
    u = -1.5875 - source_x
    if side == "outer":
        land = float(profile["bearing_side_outer_relief"]["H1_land_outer_radius"])
        return min(float(profile["silhouette"]["coaxial_corner_clip_diameter"]) / 2, land + u)
    if side == "inner":
        return max(float(profile["bearing_side_inner_relief"]["smooth_through_bore_radius"]), float(profile["bearing_side_inner_relief"]["land_inner_radius"]) - u)
    raise ValueError("unknown radial profile side")


def _source_crop_semantics(
    gmsh: Any,
    imported: tuple[int, int],
    cylinder_tag: int,
    frame: dict[str, Any],
    target_tn: tuple[float, float],
    numpy: Any,
) -> tuple[dict[int, str], list[dict[str, Any]], list[int]]:
    source_faces = [(dim, int(tag)) for dim, tag in gmsh.model.getBoundary([imported], combined=False, oriented=False) if dim == 2]
    if not source_faces:
        raise ValueError("receiver STEP has no natural source faces")
    originals = []
    for _dim, tag in source_faces:
        signature = _analytic_surface_signature(gmsh, tag, frame, numpy)
        originals.append({"tag": tag, "signature": signature})
    source_summary = record["receiver"]["source_solid_summary"]
    if len(originals) != source_summary["source_face_count"]:
        raise ValueError("receiver BREP source-face count differs from the pinned exact STEP round-trip")
    source_area_by_type: dict[str, float] = defaultdict(float)
    for source in originals:
        source_area_by_type[source["signature"]["surface_type"].upper()] += source["signature"]["area_mm2"]
    expected_type_areas = source_summary["surface_area_by_type_mm2"]
    if set(source_area_by_type) != set(expected_type_areas):
        raise ValueError("receiver BREP analytic surface type inventory differs from the pinned source summary")
    for surface_type, area in expected_type_areas.items():
        actual_area = source_area_by_type[surface_type]
        if abs(actual_area / area - 1) > 1e-6:
            raise ValueError(f"receiver BREP {surface_type} face area differs from the pinned source summary")
    copies = gmsh.model.occ.copy(source_faces)
    clipped, ancestry_map = gmsh.model.occ.intersect(copies, [(3, cylinder_tag)], removeObject=True, removeTool=False)
    gmsh.model.occ.synchronize()
    if len(ancestry_map) != len(copies) + 1:
        raise ValueError("Gmsh OCC face-clip ancestry map has the wrong input cardinality")
    descendants: list[dict[str, Any]] = []
    copied_surface_tags: list[int] = []
    for index, source in enumerate(originals):
        mapped = [(int(dim), int(tag)) for dim, tag in ancestry_map[index] if dim == 2]
        for _dim, tag in mapped:
            copied_surface_tags.append(tag)
            desc = _analytic_surface_signature(gmsh, tag, frame, numpy)
            descendants.append(
                {
                    "source_face_signature_sha256": source["signature"]["signature_sha256"],
                    "source_face_area_mm2": source["signature"]["area_mm2"],
                    "source_surface_type": source["signature"]["surface_type"],
                    "clipped_signature": desc,
                    "clipped_face_area_mm2": desc["area_mm2"],
                }
            )
    # The copied descendants are an independent exact ancestry witness. They
    # must be removed before meshing so only the cropped receiver solid remains.
    if copied_surface_tags:
        gmsh.model.occ.remove([(2, tag) for tag in copied_surface_tags], recursive=True)
        gmsh.model.occ.synchronize()
    return {}, descendants, [tag for _dim, tag in source_faces]


def _crop_receiver_model(
    gmsh: Any,
    numpy: Any,
    record: dict[str, Any],
    step_path: Path,
    output_geometry: Path,
) -> tuple[int, dict[int, str], list[dict[str, Any]], dict[str, Any]]:
    frame = record["receiver"]["source_frame"]
    target = record["receiver"]["local_seat_centers_X_T_N_mm"]["center_principal_right_2"]
    global_origin = _global_from_local(frame, (0.0, target[1], target[2]))
    source_model = "receiver_R75_crop"
    gmsh.model.add(source_model)
    if not step_path.is_file() or _sha256(step_path) != EXPECTED_SOURCE_STEP_SHA256:
        raise ValueError("receiver STEP is not the exact parent-pinned source body")
    imported = gmsh.model.occ.importShapes(str(step_path))
    gmsh.model.occ.synchronize()
    if len(imported) != 1 or imported[0][0] != 3 or len(gmsh.model.getEntities(3)) != 1:
        raise ValueError("pinned receiver STEP must import as one source solid")
    source_volume = float(gmsh.model.occ.getMass(*imported[0]))
    source_row = record["receiver"]["source_solid_summary"]
    if abs(source_volume / source_row["finished_volume_mm3"] - 1) > 1e-7:
        raise ValueError("receiver STEP import mass differs from the pinned source solid summary")
    cylinder = gmsh.model.occ.addCylinder(*global_origin, 38.1, 0.0, 0.0, 75.0)
    surface_map, natural_descendants, _source_faces = _source_crop_semantics(
        gmsh, imported[0], cylinder, frame, (target[1], target[2]), numpy
    )
    cropped, crop_map = gmsh.model.occ.intersect([imported[0]], [(3, cylinder)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    volumes = [int(tag) for dim, tag in cropped if dim == 3]
    if len(volumes) != 1 or len(gmsh.model.getEntities(3)) != 1:
        raise ValueError("R75 exact BREP intersection must yield one connected receiver solid")
    volume_tag = volumes[0]
    boundary = [(dim, int(tag)) for dim, tag in gmsh.model.getBoundary([(3, volume_tag)], combined=False, oriented=False)]
    if not boundary or any(dim != 2 for dim, _tag in boundary):
        raise ValueError("cropped receiver boundary includes missing or non-face entities")
    signatures = {tag: _analytic_surface_signature(gmsh, tag, frame, numpy) for _dim, tag in boundary}
    unmatched_descendants = list(range(len(natural_descendants)))
    source_rows: list[dict[str, Any]] = []
    geometry_signature_rows: list[dict[str, Any]] = []
    crop_faces: list[int] = []
    semantic_by_tag: dict[int, str] = {}
    for tag, signature in signatures.items():
        matches = [index for index in unmatched_descendants if _surface_signatures_match(signature, natural_descendants[index]["clipped_signature"])]
        if len(matches) == 1:
            index = matches[0]
            descendant = natural_descendants[index]
            source_key = descendant["source_face_signature_sha256"]
            semantic_id = f"receiver.source_face.{source_key[:16]}.{signature['signature_sha256'][:16]}"
            semantic_by_tag[tag] = semantic_id
            source_rows.append(
                {
                    "semantic_surface_id": semantic_id,
                    "source_surface_type": descendant["source_surface_type"],
                    "source_surface_signature_sha256": source_key,
                    "clipped_surface_signature_sha256": signature["signature_sha256"],
                    "source_step_sha256": EXPECTED_SOURCE_STEP_SHA256,
                    "source_face_ancestry_verified": True,
                    "source_face_area_mm2": descendant["source_face_area_mm2"],
                    "clipped_face_area_mm2": signature["area_mm2"],
                }
            )
            unmatched_descendants.remove(index)
        elif matches:
            raise ValueError("ambiguous one-to-many natural source face ancestry")
        elif _is_r75_cylinder(signature, frame, (target[1], target[2])):
            semantic_by_tag[tag] = "receiver.crop_cylinder_R75"
            crop_faces.append(tag)
        else:
            raise ValueError(f"receiver face {tag}: unsupported/unknown source ancestry or crop surface")
        geometry_signature_rows.append(
            {
                "semantic_surface_id": semantic_by_tag[tag],
                "surface_type": signature["surface_type"],
                "surface_signature_sha256": signature["signature_sha256"],
                "analytic_support": signature["analytic_support"],
                "trim_area_mm2": signature["area_mm2"],
                "trim_centroid_source_X_T_N_mm": list(signature["center"]),
                "trim_bounds_source_X_T_N_order": signature["signature_payload"]["trim_bounds_local_order"],
            }
        )
    if unmatched_descendants:
        raise ValueError("not every source-face/cylinder clipped descendant belongs to the final crop")
    if not crop_faces:
        raise ValueError("R75 crop did not retain its analytic cylindrical side face")
    natural_ids = [name for name in semantic_by_tag.values() if name != "receiver.crop_cylinder_R75"]
    if len(natural_ids) != len(set(natural_ids)):
        raise ValueError("two natural source faces share one semantic identity")
    if len(set(semantic_by_tag.values())) != len(semantic_by_tag):
        # Multiple geometric pieces from one source face are given individual
        # signature-derived IDs; only the R75 cylinder may be aggregated.
        crop_tags = [tag for tag, name in semantic_by_tag.items() if name == "receiver.crop_cylinder_R75"]
        if len(crop_tags) != len(crop_faces) or len(crop_tags) == len(semantic_by_tag):
            raise ValueError("duplicate receiver semantic face identity")
    volume = float(gmsh.model.occ.getMass(3, volume_tag))
    centroid = tuple(float(value) for value in gmsh.model.occ.getCenterOfMass(3, volume_tag))
    bounds = tuple(float(value) for value in gmsh.model.getBoundingBox(3, volume_tag))
    gmsh.write(str(output_geometry))
    return volume_tag, semantic_by_tag, source_rows, {
        "source_cad_volume_mm3": volume,
        "source_cad_centroid_global_mm": list(centroid),
        "source_cad_bounds_global_mm": list(bounds),
        "source_step_sha256": EXPECTED_SOURCE_STEP_SHA256,
        "source_face_ancestry_method": "source-face OCC intersection descendants matched to exact analytic support, trim boundary, area and centroid; transient tags are not identities",
        "source_natural_face_ids": sorted(name for name in semantic_by_tag.values() if name != "receiver.crop_cylinder_R75"),
        "crop_generated_surface_ids": ["receiver.crop_cylinder_R75"],
        "geometry_surface_signature_rows": geometry_signature_rows,
    }


def _add_hex_prism(gmsh: Any, frame: dict[str, Any], center_tn: tuple[float, float], outer_x: float, height: float, apothem: float) -> int:
    circumradius = apothem / math.cos(math.pi / 6)
    points = []
    for index in range(6):
        angle = math.pi / 6 + index * math.pi / 3
        local = (outer_x, center_tn[0] + circumradius * math.cos(angle), center_tn[1] + circumradius * math.sin(angle))
        points.append(gmsh.model.occ.addPoint(*_global_from_local(frame, local)))
    edges = [gmsh.model.occ.addLine(points[index], points[(index + 1) % 6]) for index in range(6)]
    loop = gmsh.model.occ.addCurveLoop(edges)
    face = gmsh.model.occ.addPlaneSurface([loop])
    prism = gmsh.model.occ.extrude([(2, face)], height, 0.0, 0.0)
    volumes = [int(tag) for dim, tag in prism if dim == 3]
    if len(volumes) != 1:
        raise ValueError("clipped hex prism extrusion did not produce exactly one solid")
    return volumes[0]


def _build_washer(gmsh: Any, body_id: str, frame: dict[str, Any], center_tn: tuple[float, float]) -> int:
    base = _global_from_local(frame, (WASHER_NUT_X_MM, center_tn[0], center_tn[1]))
    outer = gmsh.model.occ.addCylinder(*base, WASHER_T_MM, 0.0, 0.0, OD_MM / 2)
    bore_base = _global_from_local(frame, (WASHER_NUT_X_MM - 0.1, center_tn[0], center_tn[1]))
    bore = gmsh.model.occ.addCylinder(*bore_base, WASHER_T_MM + 0.2, 0.0, 0.0, ID_MM / 2)
    result, _map = gmsh.model.occ.cut([(3, outer)], [(3, bore)], removeObject=True, removeTool=True)
    volumes = [int(tag) for dim, tag in result if dim == 3]
    if len(volumes) != 1:
        raise ValueError(f"{body_id}: catalog washer annulus did not produce one solid")
    return volumes[0]


def _build_h1_nut(gmsh: Any, body_id: str, frame: dict[str, Any], center_tn: tuple[float, float], profile: dict[str, Any]) -> int:
    outer_x = LOAD_FACE_X_MM
    inner_x = WASHER_NUT_X_MM
    height = NUT_HEIGHT_MM
    apothem = float(profile["silhouette"]["regular_hex_across_flats"]) / 2
    clip_radius = float(profile["silhouette"]["coaxial_corner_clip_diameter"]) / 2
    land_radius = float(profile["bearing_side_outer_relief"]["H1_land_outer_radius"])
    relief_height = clip_radius - land_radius
    cone_start_x = inner_x - relief_height
    hex_volume = _add_hex_prism(gmsh, frame, center_tn, outer_x, height, apothem)
    clip_origin = _global_from_local(frame, (outer_x, center_tn[0], center_tn[1]))
    clip = gmsh.model.occ.addCylinder(*clip_origin, height, 0.0, 0.0, clip_radius)
    silhouette, _map = gmsh.model.occ.intersect([(3, hex_volume)], [(3, clip)], removeObject=True, removeTool=True)
    silhouette_volumes = [int(tag) for dim, tag in silhouette if dim == 3]
    if len(silhouette_volumes) != 1:
        raise ValueError(f"{body_id}: clipped regular-hex silhouette is not one solid")

    outer_cylinder_origin = _global_from_local(frame, (outer_x, center_tn[0], center_tn[1]))
    outer_cylinder = gmsh.model.occ.addCylinder(*outer_cylinder_origin, cone_start_x - outer_x, 0.0, 0.0, clip_radius)
    cone_origin = _global_from_local(frame, (cone_start_x, center_tn[0], center_tn[1]))
    outer_cone = gmsh.model.occ.addCone(*cone_origin, relief_height, 0.0, 0.0, clip_radius, land_radius)
    envelope, _map = gmsh.model.occ.fuse([(3, outer_cylinder)], [(3, outer_cone)], removeObject=True, removeTool=True)
    envelope_volumes = [int(tag) for dim, tag in envelope if dim == 3]
    if len(envelope_volumes) != 1:
        raise ValueError(f"{body_id}: outer cone/cylinder union is not one solid")
    shaped, _map = gmsh.model.occ.intersect([(3, silhouette_volumes[0])], [(3, envelope_volumes[0])], removeObject=True, removeTool=True)
    shaped_volumes = [int(tag) for dim, tag in shaped if dim == 3]
    if len(shaped_volumes) != 1:
        raise ValueError(f"{body_id}: outer relief clipping did not produce one solid")

    through_radius = float(profile["bearing_side_inner_relief"]["smooth_through_bore_radius"])
    inner_land_radius = float(profile["bearing_side_inner_relief"]["land_inner_radius"])
    inner_relief_depth = inner_land_radius - through_radius
    inner_relief_outer_x = inner_x - inner_relief_depth
    through_origin = _global_from_local(frame, (outer_x - 0.1, center_tn[0], center_tn[1]))
    through = gmsh.model.occ.addCylinder(*through_origin, height + 0.2, 0.0, 0.0, through_radius)
    relief_origin = _global_from_local(frame, (inner_relief_outer_x, center_tn[0], center_tn[1]))
    relief = gmsh.model.occ.addCone(*relief_origin, inner_relief_depth, 0.0, 0.0, through_radius, inner_land_radius)
    hole, _map = gmsh.model.occ.fuse([(3, through)], [(3, relief)], removeObject=True, removeTool=True)
    hole_volumes = [int(tag) for dim, tag in hole if dim == 3]
    if len(hole_volumes) != 1:
        raise ValueError(f"{body_id}: inner relief/bore union is not one solid")
    nut, _map = gmsh.model.occ.cut([(3, shaped_volumes[0])], [(3, hole_volumes[0])], removeObject=True, removeTool=True)
    nut_volumes = [int(tag) for dim, tag in nut if dim == 3]
    if len(nut_volumes) != 1:
        raise ValueError(f"{body_id}: complete H1 nut profile is not one solid")
    return nut_volumes[0]


def _build_hardware_model(gmsh: Any, numpy: Any, body_id: str, role: str, frame: dict[str, Any], center_tn: tuple[float, float], profile: dict[str, Any] | None, step_path: Path) -> tuple[int, dict[int, str], dict[str, Any]]:
    gmsh.model.add(body_id)
    if role == "washer":
        volume_tag = _build_washer(gmsh, body_id, frame, center_tn)
    elif role == "nut_H1":
        if profile is None:
            raise ValueError("H1 nut geometry requires the additive pinned profile")
        volume_tag = _build_h1_nut(gmsh, body_id, frame, center_tn, profile)
    else:
        raise ValueError(f"unsupported conditional hardware role: {role}")
    gmsh.model.occ.synchronize()
    volumes = gmsh.model.getEntities(3)
    if len(volumes) != 1 or volumes[0][1] != volume_tag:
        raise ValueError(f"{body_id}: hardware geometry inventory is not exactly one solid")
    boundary = [(dim, int(tag)) for dim, tag in gmsh.model.getBoundary([(3, volume_tag)], combined=False, oriented=False)]
    if not boundary or any(dim != 2 for dim, _tag in boundary):
        raise ValueError(f"{body_id}: hardware BREP has invalid boundary entities")
    surface_map: dict[int, str] = {}
    semantic_area: dict[str, float] = defaultdict(float)
    geometry_signature_rows = []
    for _dim, tag in boundary:
        semantic_id = _classify_hardware_face(gmsh, tag, body_id, frame, center_tn, profile, numpy)
        surface_map[tag] = semantic_id
        semantic_area[semantic_id] += float(gmsh.model.occ.getMass(2, tag))
        signature = _analytic_surface_signature(gmsh, tag, frame, numpy)
        geometry_signature_rows.append(
            {
                "semantic_surface_id": semantic_id,
                "surface_type": signature["surface_type"],
                "surface_signature_sha256": signature["signature_sha256"],
                "analytic_support": signature["analytic_support"],
                "trim_area_mm2": signature["area_mm2"],
                "trim_centroid_source_X_T_N_mm": list(signature["center"]),
                "trim_bounds_source_X_T_N_order": signature["signature_payload"]["trim_bounds_local_order"],
            }
        )
    if role == "washer":
        expected_area = math.pi / 4 * (OD_MM**2 - ID_MM**2)
        for semantic_suffix in ("wood_bearing_annulus", "nut_bearing_annulus"):
            actual = semantic_area.get(f"{body_id}.{semantic_suffix}", 0.0)
            if abs(actual - expected_area) > 1e-7:
                raise ValueError(f"{body_id}: {semantic_suffix} face area differs from catalog annulus")
        for suffix, radius in (("washer_outer_cylindrical_edge", OD_MM / 2), ("washer_bore_cylindrical_edge", ID_MM / 2)):
            actual = semantic_area.get(f"{body_id}.{suffix}", 0.0)
            expected = 2 * math.pi * radius * WASHER_T_MM
            if abs(actual - expected) > 1e-7:
                raise ValueError(f"{body_id}: {suffix} lateral area differs from catalog annulus")
    else:
        if abs(semantic_area.get(f"{body_id}.outward_hex_load_face", 0.0) - 75.51784511932227) > 1e-6:
            raise ValueError(f"{body_id}: complete outward load face differs from the pinned clipped-hex profile")
        if abs(semantic_area.get(f"{body_id}.washer_bearing_land", 0.0) - 57.48292325873653) > 1e-6:
            raise ValueError(f"{body_id}: complete H1 initial land differs from the pinned profile")
        hex_faces = [name for name in semantic_area if name.startswith(f"{body_id}.hex_flat_normal_")]
        required = {
            f"{body_id}.outward_hex_load_face",
            f"{body_id}.washer_bearing_land",
            f"{body_id}.coaxial_corner_clip_cylinder",
            f"{body_id}.smooth_through_bore",
            f"{body_id}.bearing_side_outer_conical_relief",
            f"{body_id}.bearing_side_inner_conical_relief",
        }
        if set(semantic_area) != required | set(hex_faces) or len(hex_faces) != 6:
            raise ValueError(f"{body_id}: H1 nut semantic surface inventory is incomplete or unsupported")
    volume = float(gmsh.model.occ.getMass(3, volume_tag))
    centroid = tuple(float(value) for value in gmsh.model.occ.getCenterOfMass(3, volume_tag))
    bounds = tuple(float(value) for value in gmsh.model.getBoundingBox(3, volume_tag))
    if role == "washer" and abs(volume - 355.5139185846077) > 1e-7:
        raise ValueError(f"{body_id}: catalog nominal washer BREP differs from independent annulus volume")
    if role == "nut_H1" and abs(volume - 415.50205345278425) > 1e-6:
        raise ValueError(f"{body_id}: H1 nut BREP differs from independent sectional volume")
    gmsh.write(str(step_path))
    return volume_tag, surface_map, {
        "source_cad_volume_mm3": volume,
        "source_cad_centroid_global_mm": list(centroid),
        "source_cad_bounds_global_mm": list(bounds),
        "role": role,
        "semantic_surface_ids": sorted(set(surface_map.values())),
        "geometry_surface_signature_rows": geometry_signature_rows,
    }


def _mesh_current_model(
    gmsh: Any,
    volume_tag: int,
    body_id: str,
    surface_map: dict[int, str],
    body_geometry: dict[str, Any],
    all_nodes: dict[int, tuple[float, float, float]],
    all_elements: dict[int, tuple[int, ...]],
    topology_bodies: dict[str, Any],
) -> dict[str, Any]:
    boundary = [(dim, int(tag)) for dim, tag in gmsh.model.getBoundary([(3, volume_tag)], combined=False, oriented=False)]
    if not boundary or any(dim != 2 for dim, _tag in boundary):
        raise ValueError(f"{body_id}: final mesh boundary is incomplete")
    if set(surface_map) != {tag for _dim, tag in boundary}:
        raise ValueError(f"{body_id}: semantic face map does not cover every BREP boundary face")
    features = []
    for _dim, tag in boundary:
        surface_type = str(gmsh.model.getType(2, tag))
        if surface_type not in mesh_oracles.SUPPORTED_SOURCE_SURFACE_TYPES:
            raise ValueError(f"{body_id}: unsupported surface type before mesh: {surface_type}")
        if surface_type in {"Cylinder", "Cone"} and surface_map[tag] != "receiver.crop_cylinder_R75":
            features.append(tag)
    for name, value in (
        ("Mesh.MeshSizeMax", LOCAL_MESH["global_max_size_mm"]),
        ("Mesh.MeshSizeMin", LOCAL_MESH["local_min_size_mm"]),
        ("Mesh.MeshSizeFromCurvature", 32),
        ("Mesh.MeshSizeExtendFromBoundary", 0),
        ("Mesh.MeshSizeFromPoints", 0),
        ("Mesh.ElementOrder", 2),
        ("Mesh.SecondOrderLinear", 0),
    ):
        gmsh.option.setNumber(name, value)
    if features:
        distance_field = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(distance_field, "FacesList", features)
        threshold = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(threshold, "InField", distance_field)
        gmsh.model.mesh.field.setNumber(threshold, "SizeMin", LOCAL_MESH["local_min_size_mm"])
        gmsh.model.mesh.field.setNumber(threshold, "SizeMax", LOCAL_MESH["global_max_size_mm"])
        gmsh.model.mesh.field.setNumber(threshold, "DistMin", 0.0)
        gmsh.model.mesh.field.setNumber(threshold, "DistMax", LOCAL_MESH["refinement_band_mm"])
        gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("HighOrder")

    element_types, element_tags_by_type, flat_connectivity = gmsh.model.mesh.getElements(3, volume_tag)
    if list(map(int, element_types)) != [11] or len(element_tags_by_type) != 1:
        raise ValueError(f"{body_id}: audited worker expected Gmsh quadratic tetrahedra only")
    local_elements = wood_mesh.c3d10_elements(element_tags_by_type[0], flat_connectivity[0])
    used_nodes = {node for row in local_elements.values() for node in row}
    node_tags, coordinates, _parametric = gmsh.model.mesh.getNodes()
    all_local_nodes = {
        int(node): tuple(float(value) for value in coordinates[3 * index : 3 * index + 3])
        for index, node in enumerate(node_tags)
    }
    if not used_nodes <= set(all_local_nodes):
        raise ValueError(f"{body_id}: C3D10 connectivity references absent nodes")
    local_nodes = {node: all_local_nodes[node] for node in used_nodes}
    if any(not all(math.isfinite(value) for value in point) for point in local_nodes.values()):
        raise ValueError(f"{body_id}: nonfinite C3D10 node coordinates")
    exterior = external_faces(local_elements)
    element_tags = element_tags_by_type[0]
    sampled = tuple(float(value) for value in gmsh.model.mesh.getElementQualities(element_tags, "minDetJac"))
    gauss_points, gauss_weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss5")
    _jacobians, determinants, _physical = gmsh.model.mesh.getJacobians(11, gauss_points, volume_tag)
    volume_audit = wood_mesh.audit_mesh_volume(
        float(body_geometry["source_cad_volume_mm3"]),
        tuple(float(value) for value in determinants),
        tuple(float(value) for value in gauss_weights),
        sampled,
        len(local_elements),
    )
    if not all(math.isfinite(value) and value > 0 for value in sampled) or not all(math.isfinite(float(value)) and float(value) > 0 for value in determinants):
        raise ValueError(f"{body_id}: nonpositive sampled or Gauss5 C3D10 Jacobian")
    node_map, element_map = append_body(all_nodes, all_elements, local_nodes, local_elements)

    surface_triangles: dict[str, list[tuple[int, ...]]] = defaultdict(list)
    local_faces: dict[str, list[list[int]]] = {}
    surface_records = []
    feature_elements: set[int] = set()
    for _dim, tag in boundary:
        types, _tags, flat = gmsh.model.mesh.getElements(2, tag)
        if list(map(int, types)) != [9] or len(flat) != 1 or len(flat[0]) % 6:
            raise ValueError(f"{body_id} surface {tag}: expected TRI6 only")
        rows = [tuple(int(value) for value in flat[0][index : index + 6]) for index in range(0, len(flat[0]), 6)]
        matched = surface_faces(rows, exterior)
        semantic_id = surface_map[tag]
        if str(gmsh.model.getType(2, tag)) in {"Cylinder", "Cone"} and semantic_id != "receiver.crop_cylinder_R75":
            feature_elements.update(element for element, _face in matched["faces"])
        if body_id.startswith(("washer_", "nut_H1_")):
            feature_elements.update(element for element, _face in matched["faces"])
        if semantic_id not in local_faces:
            local_faces[semantic_id] = []
        local_faces[semantic_id].extend(matched["faces"])
        surface_triangles[semantic_id].extend(tuple(node_map[node] for node in row) for row in rows)
        surface_records.append(
            {
                "semantic_surface_id": semantic_id,
                "transient_gmsh_tag": tag,
                "transient_tag_scope": "this independent Gmsh model only; never an interface identity",
                "surface_type": str(gmsh.model.getType(2, tag)),
                "cad_area_mm2": float(gmsh.model.occ.getMass(2, tag)),
                "tri6_count": len(rows),
                "tri6_exterior_face_refs": [[element_map[element], face] for element, face in matched["faces"]],
            }
        )
    validate_and_remap_surface_coverage(exterior, local_faces, element_map)
    topology_elements = {element_map[element]: tuple(node_map[node] for node in row) for element, row in local_elements.items()}
    topology = {"elements": topology_elements, "surface_triangles": dict(surface_triangles)}
    independent_topology = mesh_oracles.audit_c3d10_surface_ownership(topology_elements, topology["surface_triangles"])
    if independent_topology["connected_component_count"] != 1:
        raise ValueError(f"{body_id}: C3D10 mesh has disconnected volume components")
    edge_patterns = ((0, 4, 1), (1, 5, 2), (2, 6, 0), (0, 7, 3), (1, 8, 3), (2, 9, 3))
    local_edge_max = 0.0
    for element_id in feature_elements:
        row = local_elements[element_id]
        for left, middle, right in edge_patterns:
            xyz_left, xyz_mid, xyz_right = (local_nodes[row[index]] for index in (left, middle, right))
            for start, end in ((xyz_left, xyz_mid), (xyz_mid, xyz_right)):
                local_edge_max = max(local_edge_max, math.dist(start, end))
    if not feature_elements:
        raise ValueError(f"{body_id}: no locally refined feature faces were mapped")
    if local_edge_max > LOCAL_MESH["local_min_size_mm"] + 1e-8:
        raise ValueError(f"{body_id}: locally refined high-order edge segment exceeds 0.8 mm")
    washer_layers = None
    if body_id.startswith("washer_"):
        maximum_element_x_span = max(
            max(local_nodes[node][0] for node in row) - min(local_nodes[node][0] for node in row)
            for row in local_elements.values()
        )
        if maximum_element_x_span <= 0:
            raise ValueError(f"{body_id}: washer C3D10 elements have zero source-X span")
        washer_layers = math.floor(WASHER_T_MM / maximum_element_x_span + 1e-12)
        if washer_layers < 2:
            raise ValueError(f"{body_id}: mesh misses the minimum two-layer washer thickness target")
    body_record = {
        **body_geometry,
        "solid_count": 1,
        "connected_component_count": independent_topology["connected_component_count"],
        "element_type": "C3D10",
        "node_ids": sorted(node_map.values()),
        "element_ids": sorted(element_map.values()),
        "minimum_sampled_jacobian": min(sampled),
        "minimum_gauss5_jacobian": min(float(value) for value in determinants),
        "mesh_integrated_volume_mm3": float(volume_audit["integrated_volume_mm3"]),
        "integrated_mesh_audit": volume_audit,
        "surface_rows": surface_records,
        "semantic_surface_ids": sorted(surface_triangles),
        "maximum_locally_refined_edge_mm": local_edge_max,
        "achieved_washer_through_thickness_layers": washer_layers,
    }
    topology_bodies[body_id] = topology
    return body_record


def _write_mesh_deck(path: Path, nodes: dict[int, tuple[float, float, float]], elements: dict[int, tuple[int, ...]], bodies: dict[str, Any]) -> None:
    lines = ["*HEADING", "Conditional washer crop mesh only; no solver cards", "*NODE"]
    lines.extend(f"{node}," + ",".join(map(repr, xyz)) for node, xyz in sorted(nodes.items()))
    for body_id in BODY_IDS:
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={body_id.upper()}")
        lines.extend(f"{element}," + ",".join(map(str, elements[element])) for element in bodies[body_id]["element_ids"])
    text = "\n".join(lines) + "\n"
    mesh_oracles.validate_mesh_deck_keywords(text)
    _write_new(path, text.encode())


def _record_failure(output: Path, record: dict[str, Any], error: BaseException) -> None:
    failure = {
        **record,
        "status": "FAILED_MESH_PREPARATION_NO_SOLVER_NO_RETRY",
        "failure": f"{type(error).__name__}: {error}",
        "solver_cards": False,
        "mechanics_cards_authorized": False,
        "candidate_acceptance_authorized": False,
    }
    path = output / "failure.json"
    if not path.exists():
        _write_new(path, json.dumps(failure, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n")


def _nut_load_face_audits(
    record: dict[str, Any],
    bodies: dict[str, Any],
    topology: dict[str, Any],
    nodes: dict[int, tuple[float, float, float]],
) -> dict[str, Any]:
    audits: dict[str, Any] = {}
    direction = tuple(record["receiver"]["source_frame"]["axes_global_xyz"]["X"])
    for axis_id, nut_body in (
        ("center_principal_right_2", "nut_H1_center_principal_right_2"),
        ("center_principal_right_1", "nut_H1_center_principal_right_1"),
    ):
        semantic_id = f"{nut_body}.outward_hex_load_face"
        triangles = topology[nut_body]["surface_triangles"].get(semantic_id)
        if not triangles:
            raise ValueError(f"{nut_body}: exact outward nut load face is missing from semantic TRI6 map")
        cad_area = math.fsum(
            row["cad_area_mm2"]
            for row in bodies[nut_body]["surface_rows"]
            if row["semantic_surface_id"] == semantic_id
        )
        if abs(cad_area - 75.51784511932227) > 1e-6:
            raise ValueError(f"{nut_body}: outward load-face area differs from independent H1 profile")
        action = record["stack_loads"][axis_id]
        axis_origin = tuple(action["source_global_point_xyz_mm"])
        face_x = axis_origin[0] + LOAD_FACE_X_MM
        audit = mesh_oracles.integrate_uniform_axial_face(
            triangles,
            nodes,
            cad_area_mm2=cad_area,
            force_n=float(action["signed_inward_resultant_N"]),
            force_direction=direction,
            axis_origin_global_mm=axis_origin,
            plane_x_global_mm=face_x,
        )
        if audit["force_residual_N"] > 0.02 or audit["moment_residual_N_mm"] > 0.05:
            raise ValueError(f"{nut_body}: outward load-face TRI6 force/moment quadrature misses its tolerance")
        audits[axis_id] = {
            **audit,
            "semantic_surface_id": semantic_id,
            "load_face_cad_area_mm2": cad_area,
            "signed_inward_resultant_N": action["signed_inward_resultant_N"],
            "direction_receiver_local": [1.0, 0.0, 0.0],
            "diagnostic_only_no_load_card": True,
        }
    return audits


def _surface_ownership_record(
    preparation_record: dict[str, Any],
    bodies: dict[str, Any],
    topology: dict[str, Any],
    source_face_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    categories_by_body: dict[str, Any] = {}
    semantic_ids_by_body: dict[str, list[str]] = {}
    exterior_count = 0
    tri6_count = 0
    for body_id in BODY_IDS:
        body_topology = topology[body_id]
        audit = mesh_oracles.audit_c3d10_surface_ownership(
            body_topology["elements"], body_topology["surface_triangles"]
        )
        exterior_count += audit["exterior_c3d10_face_count"]
        tri6_count += audit["tri6_face_count"]
        ids = audit["semantic_surface_ids"]
        semantic_ids_by_body[body_id] = ids
        if body_id == BODY_IDS[0]:
            categories_by_body[body_id] = {
                "source_natural": sorted(row["semantic_surface_id"] for row in source_face_rows),
                "crop_generated": ["receiver.crop_cylinder_R75"],
                "conditional_hardware": [],
            }
        else:
            categories_by_body[body_id] = {
                "source_natural": [],
                "crop_generated": [],
                "conditional_hardware": ids,
            }
        flattened = [value for values in categories_by_body[body_id].values() for value in values]
        if sorted(flattened) != ids or len(flattened) != len(set(flattened)):
            raise ValueError(f"{body_id}: semantic surface category inventory is incomplete or duplicated")
    if exterior_count != tri6_count:
        raise ValueError("C3D10 exterior faces and actual TRI6 faces are not one-to-one")
    source_types = sorted({row["source_surface_type"] for row in source_face_rows})
    target = preparation_record["receiver"]["local_seat_centers_X_T_N_mm"]["center_principal_right_2"]
    return {
        "source_ancestry_verified": True,
        "source_face_ownership_complete": True,
        "source_face_descendant_coverage_complete": True,
        "bbox_only_identity_used": False,
        "unclassified_source_face_count": 0,
        "ambiguous_semantic_face_count": 0,
        "unmapped_intersecting_source_face_count": 0,
        "source_signature_family_allowlist": list(mesh_oracles.SUPPORTED_SOURCE_SURFACE_TYPES),
        "source_signature_families_seen": source_types,
        "unsupported_source_surface_types": [],
        "source_natural_face_signature_rows": source_face_rows,
        "source_step_sha256": EXPECTED_SOURCE_STEP_SHA256,
        "crop_geometry": {
            "shape": "finite source-X cylinder",
            "radius_mm": 75.0,
            "source_X_interval_mm": [0.0, 38.1],
            "center_axis_source_TN_mm": list(target[1:]),
            "natural_source_faces_retained": True,
        },
        "crop_generated_surface_ids": ["receiver.crop_cylinder_R75"],
        "semantic_surface_ids_by_body": semantic_ids_by_body,
        "surface_categories_by_body": categories_by_body,
        "exterior_c3d10_face_count": exterior_count,
        "tri6_face_count": tri6_count,
        "uncovered_exterior_face_count": 0,
        "duplicate_exterior_face_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--runtime-preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight-only", action="store_true")
    action.add_argument("--run-reserved-mesh", action="store_true")
    args = parser.parse_args()
    freeze, preflight, prep_record = _require_parent_authorization(args.freeze, args.runtime_preflight)
    output = _output_directory(args.output, freeze)

    import gmsh
    import numpy

    _check_gmsh_runtime(gmsh, numpy)
    if args.preflight_only:
        print(json.dumps({"status": "RUNTIME_PREFLIGHT_RECHECKED_NO_GEOMETRY_NO_MESH", "source_preparation_record_sha256": prep_record["record_sha256"], "image_id": preflight["image_id"], "runtime": EXPECTED_RUNTIME}, sort_keys=True))
        return
    if not args.run_reserved_mesh:
        raise AssertionError("unreachable action")

    output.mkdir(parents=True, exist_ok=False)
    reservation_claim = {
        "status": "ONE_RUN_CONSUMED_BEFORE_GEOMETRY",
        "reservation_id": freeze["one_run_reservation"]["reservation_id"],
        "freeze_sha256": _sha256(args.freeze),
        "preflight_sha256": _sha256(args.runtime_preflight),
        "retry_budget": 0,
    }
    _write_json(output / "reservation-claim.json", reservation_claim)
    run_record: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": "PREPARING_R75_H1_MESH_ONLY_NO_SOLVER",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "branch": BRANCH,
        "source_pins_sha256": prep_record["source_pins_sha256"],
        "source_preparation_record_sha256": prep_record["record_sha256"],
        "source_preparation_code_sha256": prep_record["source_preparation_code_sha256"],
        "freeze_sha256": reservation_claim["freeze_sha256"],
        "preflight_sha256": reservation_claim["preflight_sha256"],
        "runtime": EXPECTED_RUNTIME,
        "image_id": preflight["image_id"],
        "resources": preflight["resources"],
        "mesh_configuration": LOCAL_MESH,
        "body_ids": list(BODY_IDS),
        "body_count": 5,
        "accepted": False,
        "solved": False,
        "material_cards": False,
        "contact_cards": False,
        "tie_cards": False,
        "load_cards": False,
        "restraint_cards": False,
        "preload_cards": False,
        "solver_cards": False,
        "mechanics_cards_authorized": False,
        "candidate_acceptance_authorized": False,
    }
    _write_json(output / "mesh-preparation-start.json", run_record)
    geometry_directory = output / "geometry"
    geometry_directory.mkdir()
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    bodies: dict[str, Any] = {}
    topology_bodies: dict[str, Any] = {}
    source_face_rows: list[dict[str, Any]] = []
    gmsh_initialized = False
    try:
        profile_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/conditional-nut-profile.json"
        profile = _read_object(profile_path, "pinned H1 nut profile")
        if _sha256(profile_path) != prep_record["sources"][str(profile_path.relative_to(ROOT))]:
            raise ValueError("conditional H1 profile changed after source preparation")
        if gmsh.isInitialized():
            raise ValueError("reserved producer requires a fresh Gmsh process")
        gmsh.initialize()
        gmsh_initialized = True
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("General.Verbosity", 2)

        receiver_step = geometry_directory / f"{BODY_IDS[0]}.step"
        volume_tag, receiver_surfaces, source_face_rows, receiver_geometry = _crop_receiver_model(
            gmsh,
            numpy,
            prep_record,
            ROOT / EXPECTED_SOURCE_STEP,
            receiver_step,
        )
        receiver_geometry["geometry_step_path"] = receiver_step.name
        receiver_geometry["geometry_step_sha256"] = _sha256(receiver_step)
        receiver_mesh = _mesh_current_model(
            gmsh,
            volume_tag,
            BODY_IDS[0],
            receiver_surfaces,
            receiver_geometry,
            nodes,
            elements,
            topology_bodies,
        )
        receiver_mesh["geometry_step_path"] = receiver_step.name
        receiver_mesh["geometry_step_sha256"] = _sha256(receiver_step)
        bodies[BODY_IDS[0]] = receiver_mesh
        gmsh.model.remove()

        seat_centers = prep_record["receiver"]["local_seat_centers_X_T_N_mm"]
        for axis_id in ("center_principal_right_2", "center_principal_right_1"):
            local_center = seat_centers[axis_id]
            center_tn = (float(local_center[1]), float(local_center[2]))
            for body_id, role, nut_profile in (
                (f"washer_{axis_id}", "washer", None),
                (f"nut_H1_{axis_id}", "nut_H1", profile),
            ):
                if body_id not in BODY_IDS:
                    raise ValueError(f"unexpected hardware body identity: {body_id}")
                step_path = geometry_directory / f"{body_id}.step"
                hardware_volume, hardware_surfaces, hardware_geometry = _build_hardware_model(
                    gmsh,
                    numpy,
                    body_id,
                    role,
                    prep_record["receiver"]["source_frame"],
                    center_tn,
                    nut_profile,
                    step_path,
                )
                hardware_geometry["geometry_step_path"] = step_path.name
                hardware_geometry["geometry_step_sha256"] = _sha256(step_path)
                hardware_mesh = _mesh_current_model(
                    gmsh,
                    hardware_volume,
                    body_id,
                    hardware_surfaces,
                    hardware_geometry,
                    nodes,
                    elements,
                    topology_bodies,
                )
                hardware_mesh["geometry_step_path"] = step_path.name
                hardware_mesh["geometry_step_sha256"] = _sha256(step_path)
                bodies[body_id] = hardware_mesh
                gmsh.model.remove()
        if tuple(bodies) != BODY_IDS:
            raise ValueError("producer body order differs from the exact five-solid R75/H1 contract")
        gmsh.finalize()
        gmsh_initialized = False

        validate_ownership(
            nodes,
            elements,
            {
                body_id: {"nodes": bodies[body_id]["node_ids"], "elements": bodies[body_id]["element_ids"]}
                for body_id in BODY_IDS
            },
        )
        post_run_prep = prepare.build_record()
        if post_run_prep["record_sha256"] != prep_record["record_sha256"]:
            raise ValueError("pinned source inputs or preparation code changed during the reserved run")
        deck_path = output / "mesh.inp"
        _write_mesh_deck(deck_path, nodes, elements, bodies)
        surface_ownership = _surface_ownership_record(prep_record, bodies, topology_bodies, source_face_rows)
        load_face_audits = _nut_load_face_audits(prep_record, bodies, topology_bodies, nodes)
        washer_layers = [
            bodies[body_id]["achieved_washer_through_thickness_layers"]
            for body_id in BODY_IDS
            if body_id.startswith("washer_")
        ]
        report = {
            **run_record,
            "status": REPORT_STATUS,
            "body_count": len(bodies),
            "node_count": len(nodes),
            "element_count": len(elements),
            "bodies": bodies,
            "surface_ownership": surface_ownership,
            "nut_outward_face_quadrature_diagnostics": load_face_audits,
            "achieved_minimum_washer_through_thickness_layers": min(washer_layers),
            "maximum_local_edge_mm": max(body["maximum_locally_refined_edge_mm"] for body in bodies.values()),
            "source_geometry": prep_record["receiver"],
            "conditional_hardware_geometry": prep_record["hardware"],
            "geometry_step_sha256": {body_id: bodies[body_id]["geometry_step_sha256"] for body_id in BODY_IDS},
            "mesh_input_sha256": _sha256(deck_path),
            "mesh_topology_file": "mesh-topology.json",
            "output_contains_material_contact_tie_load_restraint_preload_or_solver_cards": False,
            "actual_hardware_or_wood_inspection": False,
            "product_strength_or_candidate_acceptance_claim": False,
            "native_run_count": 0,
            "external_oracle_scope": "analytic conditional geometry only; not product shape, CAD acceptance, material, contact, resistance or candidate qualification",
        }
        if report["maximum_local_edge_mm"] > LOCAL_MESH["local_min_size_mm"] + 1e-8:
            raise ValueError("global maximum over all mapped local feature edges exceeds 0.8 mm")
        topology_path = output / "mesh-topology.json"
        _write_json(topology_path, topology_bodies)
        report["mesh_topology_sha256"] = _sha256(topology_path)
        mesh_oracles.validate_mesh_report(
            report,
            prep_record["source_pins_sha256"],
            topology_bodies=topology_bodies,
        )
        report["record_sha256"] = hashlib.sha256(
            json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        _write_json(output / "mesh.json", report)
    except BaseException as error:
        if gmsh_initialized:
            try:
                gmsh.finalize()
            except Exception:
                pass
        _record_failure(output, run_record, error)
        raise


if __name__ == "__main__":
    main()
