"""Current STEP-bound C3D20 members for the reduced wood-joint model.

The retained timber is meshed with the native C3D20 generator. Most members
use the descriptor's rectangular envelope; the two inclined legs use the
actual 1:12 foot-recess profile derived from their pinned STEP solids. STEP
bores stay filled in the mesh and are recorded as omitted geometry. This is
an analysis adapter, not an accepted stiffness or capacity model.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from fea import floor_recess_mesh, floor_taper_mesh
from fea.current_response_model import CurrentStructure

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
LEG_NAMES = frozenset(("lumber_leg_left", "lumber_leg_right"))
LENGTH_TOL_MM = 1e-5
GEOMETRY_TOL_MM = 1e-5
VOLUME_TOL_MM3 = 0.05


class ReducedMemberError(ValueError):
    """Raised when a reduced member cannot be tied to the pinned geometry."""


def _vector(value: Any, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ReducedMemberError(f"{label} must be a finite XYZ vector")
    return result


def _unit(value: np.ndarray, label: str) -> np.ndarray:
    length = float(np.linalg.norm(value))
    if not math.isfinite(length) or length <= 1e-12:
        raise ReducedMemberError(f"{label} must have positive finite length")
    return value / length


def _close(actual: float, expected: float, *, tol: float = GEOMETRY_TOL_MM) -> bool:
    return math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=tol)


def _safe_step_path(relative: Any) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ReducedMemberError("Each member requires a repository-relative STEP path")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ReducedMemberError(f"STEP path escapes repository root: {relative}") from exc
    if not path.is_file():
        raise ReducedMemberError(f"Pinned STEP file does not exist: {relative}")
    return path


def _verify_step_pin(descriptor: Mapping[str, Any]) -> Path:
    path = _safe_step_path(descriptor.get("step_path"))
    expected = descriptor.get("step_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ReducedMemberError(f"{descriptor.get('name')} has no STEP SHA-256 pin")
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        raise ReducedMemberError(
            f"STEP hash mismatch for {descriptor.get('name')}: "
            f"expected {expected}, got {observed}"
        )
    return path


def _descriptor_rows(descriptors: Any) -> list[Mapping[str, Any]]:
    if isinstance(descriptors, Mapping):
        if "members" in descriptors:
            rows = descriptors["members"]
        else:
            rows = list(descriptors.values())
    else:
        rows = descriptors
    if not isinstance(rows, Iterable) or isinstance(rows, (str, bytes, Mapping)):
        raise ReducedMemberError("Member descriptors must be a sequence of records")
    result = list(rows)
    if any(not isinstance(row, Mapping) for row in result):
        raise ReducedMemberError("Every member descriptor must be an object")
    return result


def _member_record(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    name = descriptor.get("name")
    if not isinstance(name, str) or not name:
        raise ReducedMemberError("Member descriptor has no name")
    if descriptor.get("member_kind", "timber") not in ("timber", "block", "candidate_block"):
        raise ReducedMemberError(f"{name} is not a timber or solid-wood block")
    start = _vector(descriptor.get("start"), f"{name}.start")
    end = _vector(descriptor.get("end"), f"{name}.end")
    axis = _unit(_vector(descriptor.get("axis"), f"{name}.axis"), f"{name}.axis")
    u = _unit(_vector(descriptor.get("section_u"), f"{name}.section_u"), f"{name}.section_u")
    v = _unit(_vector(descriptor.get("section_v"), f"{name}.section_v"), f"{name}.section_v")
    delta = end - start
    length = float(np.linalg.norm(delta))
    if length <= 1e-8 or not math.isclose(length, float(descriptor.get("length_mm", length)),
                                         rel_tol=1e-9, abs_tol=LENGTH_TOL_MM):
        raise ReducedMemberError(f"{name} endpoints disagree with its recorded length")
    if not np.allclose(delta / length, axis, atol=1e-8, rtol=0):
        raise ReducedMemberError(f"{name} endpoints disagree with its grain axis")
    if abs(float(axis @ u)) > 1e-8 or not np.allclose(np.cross(axis, u), v, atol=1e-8, rtol=0):
        raise ReducedMemberError(f"{name} section axes are not right-handed")
    width = float(descriptor.get("width_mm", math.nan))
    depth = float(descriptor.get("depth_mm", math.nan))
    if not math.isfinite(width + depth) or min(width, depth) <= 0:
        raise ReducedMemberError(f"{name} requires positive finite section dimensions")
    envelope = float(descriptor.get("rectangular_envelope_volume_mm3", math.nan))
    actual = float(descriptor.get("actual_volume_mm3", math.nan))
    if not math.isfinite(envelope + actual) or min(envelope, actual) <= 0:
        raise ReducedMemberError(f"{name} requires positive actual and envelope volumes")
    if not math.isclose(envelope, length * width * depth, rel_tol=2e-8, abs_tol=0.1):
        raise ReducedMemberError(f"{name} rectangular envelope volume is inconsistent")
    exceptions = descriptor.get("gross_geometry_exceptions", [])
    if not isinstance(exceptions, list):
        raise ReducedMemberError(f"{name} gross geometry exceptions must be a list")
    diagnostics = {
        "native_member_mesh": "GROSS_RECTANGULAR_C3D20",
        "geometry_source": descriptor.get("step_path"),
        "geometry_sha256": descriptor.get("step_sha256"),
        "actual_step_volume_mm3": actual,
        "rectangular_envelope_volume_mm3": envelope,
        "actual_to_envelope_volume_ratio": actual / envelope,
        "gross_geometry_exceptions": [dict(item) for item in exceptions],
        "gross_cut_and_bore_stiffness_modeled": False,
        "qualified_for_design": False,
    }
    return {
        "name": name,
        "start": start,
        "end": end,
        "axis": axis,
        "section_u": u,
        "section_v": v,
        "width_mm": width,
        "depth_mm": depth,
        "gross_width_mm": width,
        "gross_depth_mm": depth,
        "area_mm2": width * depth,
        "retained_area_fraction": actual / envelope,
        "source_descriptor": dict(descriptor),
        "geometry_diagnostics": diagnostics,
        "qualified_for_design": False,
    }


def _cylinder_omission(
    shape: cq.Shape, descriptor: Mapping[str, Any]
) -> tuple[float, np.ndarray, list[dict[str, Any]]]:
    """Return exact full-bore volume/first moment for axial STEP cylinders."""
    xmin = min(point.Center().x for point in shape.Vertices())
    xmax = max(point.Center().x for point in shape.Vertices())
    rows: list[dict[str, Any]] = []
    volume = 0.0
    first_moment = np.zeros(3)
    centres: list[tuple[float, float, float, float, float, float]] = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        surface = face._geomAdaptor()
        direction = np.asarray(surface.Axis().Direction().Coord(), dtype=float)
        if not np.allclose(np.abs(direction), [1.0, 0.0, 0.0], atol=1e-8, rtol=0):
            raise ReducedMemberError("Inclined-leg bore is not parallel to the X section axis")
        radius = float(surface.Radius())
        bounds = face.BoundingBox()
        length = float(bounds.xlen)
        if radius <= 0 or length <= 0 or not _close(bounds.ylen, 2 * radius) or not _close(bounds.zlen, 2 * radius):
            raise ReducedMemberError("Inclined-leg cylindrical opening is not a full axial bore")
        if not _close(face.Area(), 2 * math.pi * radius * length, tol=0.02):
            raise ReducedMemberError("Inclined-leg cylindrical face is not a complete through-bore")
        if bounds.xmin < xmin - GEOMETRY_TOL_MM or bounds.xmax > xmax + GEOMETRY_TOL_MM:
            raise ReducedMemberError("Inclined-leg bore extends outside its pinned STEP member")
        location = surface.Location().Coord()
        centre = np.array([(bounds.xmin + bounds.xmax) / 2, location[1], location[2]])
        bore_volume = math.pi * radius**2 * length
        rows.append({
            "center_xyz_mm": centre.tolist(),
            "x_bounds_mm": [float(bounds.xmin), float(bounds.xmax)],
            "radius_mm": radius,
            "length_mm": length,
            "volume_mm3": bore_volume,
        })
        centres.append((centre[1], centre[2], radius, bounds.xmin, bounds.xmax, bore_volume))
        volume += bore_volume
        first_moment += centre * bore_volume
    for i, first in enumerate(centres):
        for second in centres[i + 1 :]:
            overlaps_x = min(first[4], second[4]) - max(first[3], second[3]) > GEOMETRY_TOL_MM
            separation = math.hypot(first[0] - second[0], first[1] - second[1])
            if overlaps_x and separation <= first[2] + second[2] + GEOMETRY_TOL_MM:
                raise ReducedMemberError("Intersecting STEP bores need a non-cylindrical omission model")
    declared = sum(
        float(item.get("cylindrical_face_count", 0))
        for item in descriptor.get("gross_geometry_exceptions", [])
    )
    declared_count = round(declared)
    if declared_count != len(rows):
        raise ReducedMemberError("Inclined-leg STEP bore count disagrees with its descriptor")
    return volume, first_moment, rows


def _leg_recess_record(base: dict[str, Any], step_path: Path) -> dict[str, Any]:
    """Build the taper mesh profile only from the pinned STEP boundary faces."""
    name = base["name"]
    descriptor = base["source_descriptor"]
    step_shape = cq.importers.importStep(str(step_path)).val()
    solids = step_shape.Solids()
    if len(solids) != 1:
        raise ReducedMemberError(f"{name} STEP must contain one solid")
    actual_volume = float(step_shape.Volume())
    if not math.isclose(actual_volume, descriptor["actual_volume_mm3"], rel_tol=1e-9, abs_tol=VOLUME_TOL_MM3):
        raise ReducedMemberError(f"{name} imported STEP volume disagrees with the verified descriptor")

    axis = np.asarray(base["axis"], dtype=float)
    u = np.asarray(base["section_u"], dtype=float)
    v = np.cross(axis, u)
    if abs(axis[0]) > 1e-8 or axis[2] <= 0 or not np.allclose(u, [1.0, 0.0, 0.0], atol=1e-8, rtol=0):
        raise ReducedMemberError("Actual leg taper adapter requires positive-Z grain in the YZ plane")
    vertices = [np.asarray(vertex.Center().toTuple(), dtype=float) for vertex in step_shape.Vertices()]
    projected = np.asarray([[point[1], point[2]] for point in vertices])
    hull = ConvexHull(projected)
    side_profile = projected[hull.vertices]
    q_values = np.asarray([point @ v for point in vertices])
    q_min, q_max = float(q_values.min()), float(q_values.max())
    if not math.isclose(q_max - q_min, base["depth_mm"], rel_tol=1e-8, abs_tol=0.02):
        raise ReducedMemberError(f"{name} broad-face STEP profile disagrees with its section depth")

    candidates: list[tuple[cq.Face, np.ndarray, np.ndarray, np.ndarray]] = []
    for face in step_shape.Faces():
        if face.geomType() != "PLANE" or len(face.Vertices()) != 4:
            continue
        points = np.asarray([vertex.Center().toTuple() for vertex in face.Vertices()], dtype=float)
        stations = points @ axis
        q = points @ v
        x = points[:, 0]
        if (
            len(np.unique(np.round(stations, 6))) == 2
            and len(np.unique(np.round(q, 6))) == 2
            and len(np.unique(np.round(x, 6))) == 2
            and _close(float(q.max() - q.min()), base["depth_mm"], tol=0.02)
            and 1e-4 < float(x.max() - x.min()) < base["width_mm"] - GEOMETRY_TOL_MM
            and float(stations.max() - stations.min()) > 12 * float(x.max() - x.min()) - 0.02
        ):
            candidates.append((face, points, stations, q))
    if len(candidates) != 1:
        raise ReducedMemberError(f"{name} STEP must expose one exact four-corner 1:12 runout face")
    _, points, stations, q = candidates[0]
    start_station, end_station = float(stations.min()), float(stations.max())
    start_points = points[np.abs(stations - start_station) <= 0.02]
    end_points = points[np.abs(stations - end_station) <= 0.02]
    if len(start_points) != 2 or len(end_points) != 2:
        raise ReducedMemberError(f"{name} taper face does not have two full-depth endpoints")
    if not np.allclose(np.sort(start_points @ v), [q_min, q_max], atol=0.02, rtol=0):
        raise ReducedMemberError(f"{name} taper start does not span the full leg section")
    if not np.allclose(np.sort(end_points @ v), [q_min, q_max], atol=0.02, rtol=0):
        raise ReducedMemberError(f"{name} taper end does not span the full leg section")
    start_x = float(np.mean(start_points[:, 0]))
    end_x = float(np.mean(end_points[:, 0]))
    recess_depth = abs(start_x - end_x)
    taper_run = end_station - start_station
    if recess_depth <= 0 or not math.isclose(taper_run / recess_depth, 12.0, rel_tol=2e-5, abs_tol=2e-5):
        raise ReducedMemberError(f"{name} STEP recess is not an observed 1:12 runout")
    xmin, xmax = min(point[0] for point in vertices), max(point[0] for point in vertices)
    outer_left = _close(end_x, xmax, tol=0.02)
    if not outer_left and not _close(end_x, xmin, tol=0.02):
        raise ReducedMemberError(f"{name} taper end does not meet a pinned STEP outside face")
    if outer_left:
        retained_band = [xmin, start_x]
    else:
        retained_band = [start_x, xmax]
    cut_band = sorted((start_x, end_x))
    if not math.isclose(retained_band[1] - retained_band[0] + recess_depth,
                        base["width_mm"], rel_tol=1e-8, abs_tol=0.02):
        raise ReducedMemberError(f"{name} retained and recess bands do not fill the STEP section")

    bore_volume, bore_first_moment, bore_rows = _cylinder_omission(step_shape, descriptor)
    filled_volume = actual_volume + bore_volume
    actual_centre = np.asarray(step_shape.Center().toTuple(), dtype=float)
    filled_centre = (actual_centre * actual_volume + bore_first_moment) / filled_volume
    geometry = {
        "side_profile_yz_mm": side_profile.tolist(),
        "grain_axis_xyz": axis.tolist(),
        "normal_axis_xyz": v.tolist(),
        "cross_grain_bounds_mm": [q_min, q_max],
        "grain_bounds_mm": [float(min(point @ axis for point in vertices)),
                             float(max(point @ axis for point in vertices))],
        "taper_start_station_mm": start_station,
        "taper_end_station_mm": end_station,
        "taper_run_mm": taper_run,
        "max_recess_depth_mm": recess_depth,
        "cut_inner_x_band_mm": cut_band,
        "retained_x_band_mm": retained_band,
        "inner_face_x_mm": end_x,
        "outward_sign": -1.0 if outer_left else 1.0,
        "expected_retained_volume_mm3": filled_volume,
        "expected_retained_centroid_xyz_mm": filled_centre.tolist(),
        "step_drilled_volume_mm3": actual_volume,
        "filled_bore_omission_volume_mm3": bore_volume,
        "filled_bore_count": len(bore_rows),
        "filled_bores": bore_rows,
        "profile_source": "pinned STEP planar runout face and broad-face convex envelope",
    }
    base["floor_recess_geometry"] = geometry
    base["geometry_diagnostics"].update(
        native_member_mesh="ACTUAL_STEP_DERIVED_1_TO_12_LEG_RECESS_C3D20",
        actual_step_volume_mm3=actual_volume,
        filled_bore_omission_volume_mm3=bore_volume,
        filled_bore_count=len(bore_rows),
        expected_filled_bore_volume_mm3=filled_volume,
        exact_profile_source=geometry["profile_source"],
        gross_cut_and_bore_stiffness_modeled=False,
    )
    return base


def add_current_members(
    structure: CurrentStructure,
    descriptors: Any,
    size_mm: float,
) -> dict[str, dict[str, Any]]:
    """Add the 44 current timber/block solids from verified STEP descriptors.

    No attachment stations are imprinted. Arbitrary member attachments are
    added later with :func:`attach_member` by inverse C3D20 interpolation.
    Returns the member records with their mesh diagnostics.
    """
    if not math.isfinite(size_mm) or size_mm <= 0:
        raise ReducedMemberError("Member element size must be positive and finite")
    if isinstance(descriptors, Mapping):
        candidate = descriptors.get("candidate")
        revision = descriptors.get("geometry_revision_id")
        if candidate is not None and candidate != EXPECTED_CANDIDATE:
            raise ReducedMemberError(f"Wrong current candidate: {candidate}")
        if revision is not None and revision != EXPECTED_REVISION:
            raise ReducedMemberError(f"Wrong current geometry revision: {revision}")
    rows = _descriptor_rows(descriptors)
    indexed: dict[str, Mapping[str, Any]] = {}
    for descriptor in rows:
        name = descriptor.get("name")
        if not isinstance(name, str) or not name or name in indexed:
            raise ReducedMemberError(f"Member name is missing or duplicated: {name!r}")
        indexed[name] = descriptor
    if len(indexed) != 44:
        raise ReducedMemberError(f"Expected all 44 current timber/block descriptors, got {len(indexed)}")
    if LEG_NAMES - set(indexed):
        raise ReducedMemberError(f"Both pinned inclined legs are required: missing {sorted(LEG_NAMES - set(indexed))}")
    if set(indexed) & set(structure.members):
        raise ReducedMemberError("Current members have already been added to this structure")

    records: dict[str, dict[str, Any]] = {}
    pins: dict[str, Path] = {}
    for name, descriptor in indexed.items():
        pins[name] = _verify_step_pin(descriptor)
        record = _member_record(descriptor)
        if name in LEG_NAMES:
            record = _leg_recess_record(record, pins[name])
        records[name] = record

    for name, record in records.items():
        if name in LEG_NAMES:
            floor_taper_mesh.mesh_member(structure, record, attachment_points=(), size=size_mm)
        else:
            structure.member(record, attachment_points=(), size=size_mm)
        structure.members[name]["geometry_diagnostics"] = record["geometry_diagnostics"]
    return records


def shape20_derivatives(point: Sequence[float]) -> np.ndarray:
    """Natural-coordinate derivatives for ``floor_recess_mesh.shape20``."""
    natural = np.asarray(point, dtype=float)
    if natural.shape != (3,) or not np.isfinite(natural).all():
        raise ReducedMemberError("C3D20 natural coordinates must be a finite triplet")
    corners = floor_recess_mesh.CORNERS
    edges = floor_recess_mesh.EDGES
    derivatives: list[list[float]] = []
    for signs in corners:
        factors = 1.0 + signs * natural
        product = float(np.prod(factors))
        linear = float(np.dot(signs, natural) - 2.0)
        derivatives.append([
            signs[k] * float(np.prod(np.delete(factors, k))) * linear / 8.0
            + product * signs[k] / 8.0
            for k in range(3)
        ])
    for signs in edges:
        along = int(np.flatnonzero(signs == 0)[0])
        factors = 1.0 + signs * natural
        product = float(np.prod(factors))
        row = []
        for k in range(3):
            if k == along:
                row.append(-2.0 * natural[k] * product / 4.0)
            else:
                remaining = [j for j in range(3) if j != along and j != k]
                row.append((1.0 - natural[along] ** 2) * signs[k]
                           * float(np.prod(factors[remaining])) / 4.0)
        derivatives.append(row)
    return np.asarray(derivatives, dtype=float)


def _inverse_shape20(point: np.ndarray, node_coordinates: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    natural = np.zeros(3, dtype=float)
    for _ in range(30):
        weights = floor_recess_mesh.shape20(natural)
        mapped = weights @ node_coordinates
        residual = mapped - point
        if float(np.linalg.norm(residual, ord=np.inf)) <= 2e-8:
            break
        jacobian = node_coordinates.T @ shape20_derivatives(natural)
        try:
            update = np.linalg.solve(jacobian, residual)
        except np.linalg.LinAlgError:
            return None
        if not np.isfinite(update).all() or float(np.linalg.norm(update)) > 1e6:
            return None
        natural -= update
    else:
        return None
    weights = floor_recess_mesh.shape20(natural)
    if (np.max(np.abs(natural)) > 1.0 + 1e-7
            or np.linalg.norm(weights @ node_coordinates - point) > 1e-6
            or abs(float(weights.sum()) - 1.0) > 1e-10):
        return None
    return natural, weights


def _generic_cell_attachment(
    structure: CurrentStructure,
    name: str,
    point: np.ndarray,
) -> tuple[list[int], np.ndarray]:
    for element_id in structure.groups.get(name, []):
        kind, node_ids, _ = structure.elements[element_id]
        if kind != "C3D20":
            continue
        coordinates = np.asarray([structure.nodes[node] for node in node_ids], dtype=float)
        if (np.any(point < coordinates.min(axis=0) - GEOMETRY_TOL_MM)
                or np.any(point > coordinates.max(axis=0) + GEOMETRY_TOL_MM)):
            continue
        inverse = _inverse_shape20(point, coordinates)
        if inverse is not None:
            return node_ids, inverse[1]
    raise ReducedMemberError(f"Attachment lies outside the retained {name} C3D20 cells")


def attach_member(
    structure: CurrentStructure,
    name: str,
    point: Sequence[float],
) -> int:
    """Add an arbitrary rigid-motion-preserving attachment to a current member.

    For taper-meshed legs, existing recess-cell location rejects points in the
    physically removed foot region. Other members use exact inverse C3D20
    interpolation on the gross solid, so declared bore omissions remain
    visible diagnostics rather than fabricated local bore geometry.
    """
    if name not in structure.members:
        raise ReducedMemberError(f"Unknown current member {name}")
    xyz = _vector(point, "attachment point")
    member = structure.members[name]
    if "floor_taper_cells" in member:
        ids, weights = floor_taper_mesh.locate(structure, name, xyz)
    elif "floor_recess_cells" in member:
        ids, weights = floor_recess_mesh.locate(structure, name, xyz)
    else:
        ids, weights = _generic_cell_attachment(structure, name, xyz)
    reconstructed = weights @ np.asarray([structure.nodes[node] for node in ids], dtype=float)
    if (np.linalg.norm(reconstructed - xyz) > 1e-6
            or abs(float(np.sum(weights)) - 1.0) > 1e-10):
        raise ReducedMemberError("C3D20 attachment interpolation lost affine geometry")
    tag = structure.node(xyz)
    for dof in (1, 2, 3):
        structure.equations.append(
            [(tag, dof, 1.0)]
            + [(node, dof, -float(weight)) for node, weight in zip(ids, weights, strict=True)
               if abs(weight) > 1e-13]
        )
    return tag
