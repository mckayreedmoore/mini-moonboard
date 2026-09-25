"""Source-bound input manifest for the right inner full-stock G7 joint pair.

The adapter consumes a previously composed WJ12/WJ16 geometry object. It does
not materialize family CAD, run a native model, calculate resistance, or close
any release gate. In particular, geometric distances below are projected
finished-solid bounds, not loaded-edge checks or 4D/7D acceptance.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as g7_probe

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_wj04_full_stock_mechanics_contract/v1"
FAMILY = "wj04_g7"
GEOMETRY_TOLERANCE_MM = 1e-5
AXIS_BBOX_TOLERANCE_MM = 2e-5
AXIS_VOLUME_REL_TOLERANCE = 1e-8
CONTACT_PLANE_TOLERANCE_MM = 1e-5
G7_BORE_PROBE_MM = 0.1

CLEAT_DATUMS = {
    g7_probe.LOWER_CLEAT: {
        "origin_basis_x_t_n_mm": g7_probe.LOWER_CLEAT_ORIGIN_MM,
        "size_x_t_n_mm": g7_probe.CLEAT_SIZE_MM,
    },
    g7_probe.UPPER_CLEAT: {
        "origin_basis_x_t_n_mm": g7_probe.UPPER_CLEAT_ORIGIN_MM,
        "size_x_t_n_mm": g7_probe.UPPER_CLEAT_SIZE_MM,
    },
}

SOURCE_CONTACT_FACES = {
    "rail_to_cleat": {
        "planar_face_id": "planar_face_04",
        "normal_basis": "T",
    },
    "principal_to_cleat": {
        "planar_face_id": "planar_face_07",
        "normal_basis": "X",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _axis_id(stack_id: str) -> str:
    return f"{FAMILY}/{g7_probe.TRIAL_ID}/{stack_id}"


def _unit(vector: tuple[float, float, float] | list[float]) -> tuple[float, float, float]:
    values = tuple(float(value) for value in vector)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError("expected a finite three-component vector")
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 1e-12:
        raise ValueError("zero vector is not a valid axis")
    return tuple(value / norm for value in values)


def _dot(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _add(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(left, right, strict=True))


def _scale(
    vector: tuple[float, float, float], scalar: float
) -> tuple[float, float, float]:
    return tuple(value * scalar for value in vector)


def _vec(value: Any) -> tuple[float, float, float]:
    if isinstance(value, cq.Vector):
        result = tuple(float(component) for component in value.toTuple())
    else:
        result = tuple(float(component) for component in value)
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError("expected a finite three-component point/vector")
    return result


def _frame_axes() -> dict[str, tuple[float, float, float]]:
    frame = WJ04_TRIAL.frame
    axes = {
        "X": _unit(frame.x_global),
        "T": _unit(frame.t_global),
        "N": _unit(frame.n_global),
    }
    for first, second in (("X", "T"), ("X", "N"), ("T", "N")):
        if abs(_dot(axes[first], axes[second])) > 1e-8:
            raise ValueError("pinned WJ04 frame axes are not orthogonal")
    return axes


def _shape_is_valid(shape: Any, context: str) -> None:
    if not isinstance(shape, cq.Shape) or not shape.isValid() or shape.isNull():
        raise ValueError(f"{context} is missing valid composed CAD geometry")


def _current_fingerprint_map(fingerprints: Any) -> dict[str, str]:
    if not isinstance(fingerprints, dict) and not hasattr(fingerprints, "items"):
        raise ValueError("right G7 source fingerprint map is missing")
    result = {str(path): str(digest) for path, digest in fingerprints.items()}
    if not result:
        raise ValueError("right G7 source fingerprint map is empty")
    for path, digest in result.items():
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"{path}: invalid SHA-256 source pin")
        file_path = (ROOT / path).resolve()
        if not file_path.is_relative_to(ROOT.resolve()) or not file_path.is_file():
            raise ValueError(f"{path}: pinned source file is unavailable")
        if _sha256(file_path) != digest:
            raise ValueError(f"{path}: right G7 source changed after composition")
    return result


def _inventory_rows(inventory: Any) -> dict[str, dict[str, Any]]:
    if not hasattr(inventory, "get"):
        raise ValueError("composed source inventory is missing")
    rows = inventory.get("parts")
    if not isinstance(rows, (list, tuple)):
        raise TypeError("composed source inventory has no part rows")
    result = {
        str(row.get("part_id")): dict(row)
        for row in rows
        if isinstance(row, dict) and row.get("part_id")
    }
    if len(result) != len(rows):
        raise ValueError("source inventory has malformed or duplicate part IDs")
    return result


def _source_frame(row: dict[str, Any]) -> tuple[tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    transform = row.get("local_to_global_transform")
    axes_raw = row.get("local_axes")
    if (
        not isinstance(transform, (list, tuple))
        or len(transform) != 4
        or not isinstance(axes_raw, dict)
    ):
        raise ValueError(f"{row.get('part_id')}: source local frame is unavailable")
    try:
        origin = tuple(float(transform[index][3]) for index in range(3))
        axes = {str(name): _unit(axis) for name, axis in axes_raw.items()}
    except (IndexError, TypeError, ValueError) as error:
        raise ValueError(f"{row.get('part_id')}: malformed source local frame") from error
    for name in ("X", "T", "N"):
        if name not in axes:
            raise ValueError(f"{row.get('part_id')}: source frame lacks {name}")
    for first, second in (("X", "T"), ("X", "N"), ("T", "N")):
        if abs(_dot(axes[first], axes[second])) > 1e-8:
            raise ValueError(f"{row.get('part_id')}: source axes are not orthogonal")
    return origin, axes


def _finished_local_bounds(
    shape: cq.Shape,
    *,
    origin: tuple[float, float, float],
    axes: dict[str, tuple[float, float, float]],
    member_id: str,
) -> dict[str, tuple[float, float]]:
    frame = _frame_axes()
    for name in ("X", "T", "N"):
        if abs(_dot(axes[name], frame[name])) < 1 - 1e-8:
            raise ValueError(f"{member_id}: composed member frame differs from pinned X/T/N")
    angle_radians = math.atan2(frame["T"][2], frame["T"][1])
    angle_degrees = math.degrees(angle_radians)
    local_shape = shape.translate(tuple(-value for value in origin)).rotate(
        (0, 0, 0), (1, 0, 0), -angle_degrees
    )
    box = local_shape.BoundingBox()
    result = {
        "X": (float(box.xmin), float(box.xmax)),
        "T": (float(box.ymin), float(box.ymax)),
        "N": (float(box.zmin), float(box.zmax)),
    }
    if any(not math.isfinite(value) for bounds in result.values() for value in bounds):
        raise ValueError(f"{member_id}: finished-solid local bounds are not finite")
    return result


def _axis_coordinate_envelope(
    shape: cq.Shape,
    *,
    expected_start: tuple[float, float, float],
    direction: tuple[float, float, float],
    diameter_mm: float,
    length_mm: float,
) -> None:
    """Authenticate the composed full-grip cutter against the pinned axis."""
    box = shape.BoundingBox()
    radius = diameter_mm / 2
    end = _add(expected_start, _scale(direction, length_mm))
    expected_bounds = []
    for coordinate in range(3):
        transverse = radius * math.sqrt(max(0.0, 1.0 - direction[coordinate] ** 2))
        expected_bounds.extend(
            (
                min(expected_start[coordinate], end[coordinate]) - transverse,
                max(expected_start[coordinate], end[coordinate]) + transverse,
            )
        )
    actual_bounds = [box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax]
    if any(
        abs(actual - expected) > AXIS_BBOX_TOLERANCE_MM
        for actual, expected in zip(actual_bounds, expected_bounds, strict=True)
    ):
        raise ValueError("composed G7 bore geometry disagrees with its pinned axis")
    expected_volume = math.pi * radius**2 * length_mm
    if not math.isclose(
        shape.Volume(), expected_volume, rel_tol=AXIS_VOLUME_REL_TOLERANCE, abs_tol=1e-7
    ):
        raise ValueError("composed G7 bore is not the pinned full-grip cylindrical axis")


def _cleat_member_frame(cleat_id: str) -> tuple[tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    datum = CLEAT_DATUMS[cleat_id]
    return (
        _vec(WJ04_TRIAL.frame.to_global(datum["origin_basis_x_t_n_mm"])),
        _frame_axes(),
    )


def _member_boundary_distances(
    *,
    member_id: str,
    member_row: dict[str, Any] | None,
    shape: cq.Shape,
    bolt_midpoint: tuple[float, float, float],
    grain_global: tuple[float, float, float],
) -> dict[str, Any]:
    if member_row is None:
        origin, axes = _cleat_member_frame(member_id)
        basis_source = "pinned WJ04 X/T/N frame; exact G7 cleat datum"
    else:
        origin, axes = _source_frame(member_row)
        basis_source = "canonical source-inventory member transform and local_axes"
    bounds = _finished_local_bounds(
        shape, origin=origin, axes=axes, member_id=member_id
    )
    coords = {
        name: _dot(tuple(p - o for p, o in zip(bolt_midpoint, origin, strict=True)), axis)
        for name, axis in axes.items()
    }
    grain_name = max(axes, key=lambda name: abs(_dot(axes[name], grain_global)))
    if abs(_dot(axes[grain_name], grain_global)) < 1 - 1e-7:
        raise ValueError(f"{member_id}: explicit grain does not align with named local axis")
    distances = {}
    for name, (low, high) in bounds.items():
        value = coords[name]
        low_gap, high_gap = value - low, high - value
        if min(low_gap, high_gap) < -GEOMETRY_TOLERANCE_MM:
            raise ValueError(f"bolt axis lies outside composed receiver {member_id}")
        distances[name] = {
            "to_low_projected_boundary_mm": round(max(0.0, low_gap), 6),
            "to_high_projected_boundary_mm": round(max(0.0, high_gap), 6),
            "finished_solid_projected_bounds_mm": [round(low, 6), round(high, 6)],
            "axis_midpoint_local_coordinate_mm": round(value, 6),
        }
    grain_distance = distances[grain_name]
    direction_class = {
        "grain_local_axis": grain_name,
        "grain_end_distances_mm": [
            grain_distance["to_low_projected_boundary_mm"],
            grain_distance["to_high_projected_boundary_mm"],
        ],
        "cross_grain_boundary_distances_mm": {
            name: [
                row["to_low_projected_boundary_mm"],
                row["to_high_projected_boundary_mm"],
            ]
            for name, row in distances.items()
            if name != grain_name
        },
    }
    return {
        "member_id": member_id,
        "grain_axis_global_xyz": [round(value, 12) for value in grain_global],
        "grain_axis_source": (
            "explicit candidate cleat grain N from WJ04 full-stock G7 producer"
            if member_row is None
            else "canonical source inventory grain_axis_global_xyz"
        ),
        "basis_source": basis_source,
        "bolt_midpoint_boundary_distances_mm": distances,
        "grain_and_cross_grain_geometric_distances": direction_class,
        "interpretation_limit": (
            "Distances to the exact OCC projected bounding planes of the finished "
            "member in its explicit local frame. "
            "They do not identify a loaded edge/end or establish a conventional "
            "4D/7D screen; local cut transitions and signed actions remain separate."
        ),
    }


def _face_area_on_plane(
    shape: cq.Shape,
    *,
    point: tuple[float, float, float],
    normal: tuple[float, float, float],
) -> float | None:
    area = 0.0
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        center = _vec(face.Center())
        face_normal = _unit(_vec(face.normalAt()))
        separation = abs(_dot(tuple(a - b for a, b in zip(center, point, strict=True)), normal))
        if separation <= CONTACT_PLANE_TOLERANCE_MM and abs(_dot(face_normal, normal)) > 1 - 1e-7:
            area += float(face.Area())
    return round(area, 6) if area > 1e-8 else None


def _interface_record(
    *,
    spec: Any,
    stack_ids: list[str],
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    candidate_shape: cq.Shape,
    source_row: dict[str, Any],
) -> dict[str, Any]:
    first_member, first_thickness = spec.layers[0]
    interface_point = _add(origin, _scale(direction, float(first_thickness)))
    candidate_id = first_member if first_member in CLEAT_DATUMS else spec.layers[1][0]
    candidate_first = first_member == candidate_id
    candidate_normal = direction if candidate_first else _scale(direction, -1.0)
    source_face_spec = SOURCE_CONTACT_FACES[spec.interface_id]
    source_face = next(
        (
            face
            for face in source_row.get("actual_planar_faces", ())
            if face.get("face_id") == source_face_spec["planar_face_id"]
        ),
        None,
    )
    if source_face is None:
        raise ValueError(f"{spec.stack_id}: pinned source contact face is missing")
    expected_source_normal = _frame_axes()[source_face_spec["normal_basis"]]
    recorded_source_normal = _unit(source_face["normal_global_xyz"])
    if _dot(expected_source_normal, recorded_source_normal) < 1 - 1e-7:
        raise ValueError(f"{spec.stack_id}: source face normal differs from its pinned datum")
    source_face_center = _vec(source_face["center_global_xyz_mm"])
    source_plane_separation = abs(
        _dot(
            tuple(a - b for a, b in zip(source_face_center, interface_point, strict=True)),
            recorded_source_normal,
        )
    )
    if source_plane_separation > CONTACT_PLANE_TOLERANCE_MM:
        raise ValueError(
            f"{spec.stack_id}: source face plane misses the composed G7 shear-plane datum"
        )
    if _dot(recorded_source_normal, candidate_normal) > -1 + 1e-7:
        raise ValueError(f"{spec.stack_id}: paired host/cleat outward normals are not opposed")
    candidate_face_area = _face_area_on_plane(
        candidate_shape, point=interface_point, normal=candidate_normal
    )
    return {
        "interface_id": f"{spec.station_id}__{spec.interface_id}",
        "family_stack_ids": stack_ids,
        "members_head_to_nut": [member for member, _thickness in spec.layers],
        "source_host_face": {
            "part_id": spec.layers[0][0]
            if spec.layers[0][0] not in CLEAT_DATUMS
            else spec.layers[1][0],
            "source_inventory_planar_face_id": source_face_spec["planar_face_id"],
            "center_global_xyz_mm": [
                round(value, 6) for value in source_face["center_global_xyz_mm"]
            ],
            "normal_global_xyz": [round(value, 12) for value in recorded_source_normal],
            "shear_plane_separation_mm": round(source_plane_separation, 9),
        },
        "candidate_cleat_face": {
            "part_id": candidate_id,
            "plane_normal_global_xyz": [round(value, 12) for value in candidate_normal],
            "composed_finished_planar_area_mm2": candidate_face_area,
            "area_basis": (
                "sum of coplanar planar faces on the already-composed finished cleat; "
                "includes represented bore/crosscut removal if present"
                if candidate_face_area is not None
                else "no matching planar face was extracted from composed geometry"
            ),
        },
        "shear_plane_datum": {
            "origin_global_xyz_mm": [round(value, 9) for value in interface_point],
            "normal_head_to_nut_global_xyz": [round(value, 12) for value in direction],
            "location_basis": "axis origin plus first head-to-nut layer thickness",
        },
        "contact_geometry_status": (
            "finite composed cleat face measured; active contact overlap, gap/tolerance, "
            "opening, and load-bearing pressure remain unresolved"
            if candidate_face_area is not None
            else "exact finite contact face unavailable; nominal bounds only and active area unresolved"
        ),
        "capacity_or_bearing_credit": False,
    }


def _physical_bolt_record(
    *,
    geometry: Any,
    spec: Any,
    inventory_rows: dict[str, dict[str, Any]],
    candidate_shapes: dict[str, cq.Shape],
    source_shapes: dict[str, cq.Shape],
    bore_diameter_mm: float,
    bolt_candidate: Any,
) -> dict[str, Any]:
    axis_id = _axis_id(spec.stack_id)
    bore = geometry.candidate_bores.get(axis_id)
    if bore is None:
        raise ValueError(f"{axis_id}: composed physical bolt axis is missing")
    if (
        bore.axis_id != axis_id
        or bore.family != FAMILY
        or bore.trial_id != g7_probe.TRIAL_ID
        or tuple(bore.receiver_ids) != tuple(member for member, _ in spec.layers)
        or (
            getattr(bore, "station_id", None) is not None
            and bore.station_id != spec.station_id
        )
    ):
        raise ValueError(f"{axis_id}: composed axis identity/ordered receivers changed")
    _shape_is_valid(bore.shape, f"{axis_id} bore")
    direction = _unit(
        WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis)
    )
    axis_origin = _vec(WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
    grip = sum(float(thickness) for _member, thickness in spec.layers)
    if not math.isclose(grip, 127.0, abs_tol=1e-8):
        raise ValueError(f"{axis_id}: G7 stack no longer has 127 mm of wood grip")
    expected_start = _add(axis_origin, _scale(direction, -G7_BORE_PROBE_MM))
    _axis_coordinate_envelope(
        bore.shape,
        expected_start=expected_start,
        direction=direction,
        diameter_mm=bore_diameter_mm,
        length_mm=grip + 2 * G7_BORE_PROBE_MM,
    )
    components = geometry.candidate_installed_hardware.get(axis_id)
    required_roles = {"shaft", "head", "head_washer", "nut_washer", "nut"}
    if not hasattr(components, "keys") or set(components) != required_roles:
        raise ValueError(f"{axis_id}: expected exactly five modeled component roles")
    for role, shape in components.items():
        _shape_is_valid(shape, f"{axis_id}/{role}")

    washer = WJ04_TRIAL.fasteners.washer
    modeled_head_washer_thickness = WJ04_TRIAL.stacks[0].cad_envelope.washer_thickness_mm
    modeled_under_head_origin = _add(
        axis_origin, _scale(direction, -modeled_head_washer_thickness)
    )

    layer_midpoints = []
    axial_progress = 0.0
    member_sections = []
    for member_id, thickness_raw in spec.layers:
        thickness = float(thickness_raw)
        midpoint = _add(
            axis_origin,
            _scale(direction, axial_progress + thickness / 2),
        )
        layer_midpoints.append(midpoint)
        if member_id in CLEAT_DATUMS:
            member_row = None
            member_shape = candidate_shapes[member_id]
            grain_global = _frame_axes()["N"]
        else:
            member_row = inventory_rows.get(member_id)
            member_shape = source_shapes.get(member_id)
            if member_row is None or member_shape is None:
                raise ValueError(f"{axis_id}: receiver {member_id} is absent from composition")
            grain_global = _unit(member_row.get("grain_axis_global_xyz", ()))
        member_sections.append(
            _member_boundary_distances(
                member_id=member_id,
                member_row=member_row,
                shape=member_shape,
                bolt_midpoint=midpoint,
                grain_global=grain_global,
            )
        )
        axial_progress += thickness

    hardware = {
        "bolt": {
            "candidate_id": bolt_candidate.candidate_id,
            "sku": bolt_candidate.sku,
            "manufacturer": bolt_candidate.manufacturer,
            "thread": bolt_candidate.thread,
            "grade": bolt_candidate.grade,
            "nominal_length_mm": bolt_candidate.nominal_length_mm,
            "catalog_length_minus_tolerance_mm": bolt_candidate.length_minus_tolerance_mm,
            "minimum_smooth_body_Lb_mm": bolt_candidate.minimum_smooth_body_mm,
            "maximum_grip_gage_Lg_mm": bolt_candidate.maximum_full_thread_start_mm,
            "published_body_diameter_range_mm": list(bolt_candidate.body_diameter_range_mm),
            "dimensional_standard": bolt_candidate.dimensional_standard,
            "source_urls": list(bolt_candidate.source_urls),
            "raw_Lb_minus_nominal_wood_grip_mm_not_a_margin": round(
                bolt_candidate.minimum_smooth_body_mm - grip, 6
            ),
            "head_side_washer_thickness_range_mm": list(washer.thickness_range_mm),
            "modeled_head_side_washer_thickness_mm": modeled_head_washer_thickness,
            "underhead_to_far_wood_face_station_range_mm": [
                round(grip + washer.thickness_range_mm[0], 6),
                round(grip + washer.thickness_range_mm[1], 6),
            ],
            "underhead_to_far_wood_face_station_at_modeled_washer_mm": round(
                grip + modeled_head_washer_thickness, 6
            ),
            "smooth_shank_through_far_wood_face_proven": False,
            "thread_transition_gate": (
                "open: Lb is measured from the underhead plane; the head-side "
                "washer places the first wood face beyond that datum. The raw "
                "Lb-minus-wood-grip equality is not a shank-margin or adequacy result. "
                "Lg is a grip-gaging bound, not the delivered first full-form thread. "
                "Measure received bolts and verify the matched nut's functional thread engagement."
            ),
        },
        "nut": {
            "candidate_id": WJ04_TRIAL.fasteners.nut.candidate_id,
            "sku": WJ04_TRIAL.fasteners.nut.sku,
            "thread": WJ04_TRIAL.fasteners.nut.thread,
            "grade": WJ04_TRIAL.fasteners.nut.grade,
            "source_urls": list(WJ04_TRIAL.fasteners.nut.source_urls),
            "status": WJ04_TRIAL.fasteners.nut.status,
        },
        "washers": {
            "quantity": 2,
            "candidate_id": WJ04_TRIAL.fasteners.washer.candidate_id,
            "description": WJ04_TRIAL.fasteners.washer.description,
            "standard": WJ04_TRIAL.fasteners.washer.standard,
            "inside_diameter_range_mm": list(WJ04_TRIAL.fasteners.washer.inner_diameter_range_mm),
            "outside_diameter_range_mm": list(WJ04_TRIAL.fasteners.washer.outer_diameter_range_mm),
            "thickness_range_mm": list(WJ04_TRIAL.fasteners.washer.thickness_range_mm),
            "source_urls": list(WJ04_TRIAL.fasteners.washer.source_urls),
            "status": WJ04_TRIAL.fasteners.washer.status,
        },
        "selection_status": "provisional catalog candidates only; delivered product and strength not verified",
    }
    return {
        "physical_bolt_id": axis_id,
        "stack_spec_id": spec.stack_id,
        "station_id": spec.station_id,
        "interface_id": spec.interface_id,
        "world_axis_origin_xyz_mm": [round(value, 9) for value in axis_origin],
        "world_axis_origin_datum": (
            "wood-side head-seat centerline at the first wood layer plane; not the "
            "BoltStack.under_head_origin"
        ),
        "modeled_bolt_under_head_origin_xyz_mm": [
            round(value, 9) for value in modeled_under_head_origin
        ],
        "composed_occupancy_bore_start_xyz_mm": [round(value, 9) for value in expected_start],
        "world_axis_direction_head_to_nut": [round(value, 12) for value in direction],
        "axis_authentication": {
            "source": "pinned STACK_SPECS transformed by WJ04_TRIAL.frame",
            "composed_bore_bbox_and_volume_match": True,
            "axis_origin_datum": (
                "centerline at the first wood layer's head-side seat plane; this is "
                "BoltStack.head_seat.center, not BoltStack.under_head_origin"
            ),
            "composed_bore_extension_each_end_mm": G7_BORE_PROBE_MM,
            "optional_composed_station_tag": getattr(bore, "station_id", None),
            "resolved_station_from_pinned_stack_spec": spec.station_id,
            "bore_is_occupancy_geometry_not_selected_or_delivered_hardware": True,
        },
        "receivers_head_to_nut": [
            {"member_id": member_id, "wood_thickness_mm": float(thickness)}
            for member_id, thickness in spec.layers
        ],
        "wood_grip_mm": round(grip, 6),
        "single_wood_shear_plane_global_xyz_mm": [
            round(value, 9)
            for value in _add(axis_origin, _scale(direction, float(spec.layers[0][1])))
        ],
        "member_geometric_boundaries": member_sections,
        "hardware": hardware,
        "signed_end_edge_and_bolt_load_classification": "unresolved pending fresh signed six-component interface/bolt actions",
        "four_d_seven_d_status": "not evaluated; no geometric screen is an adequacy result",
    }


def build_mechanics_contract(geometry: Any) -> dict[str, Any]:
    """Build the bounded eight-bolt manifest from a composed WJ12/WJ16 object."""
    if getattr(geometry, "status", None) != "unaccepted_integrated_hypothesis":
        raise ValueError("mechanics contract requires an unaccepted composed WJ12/WJ16 object")
    if getattr(geometry, "source_inventory_sha256", None) != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("composed geometry inventory hash differs from the pinned WJ04 source")
    family_ids = getattr(geometry, "family_trial_ids", {})
    if family_ids.get(FAMILY) != g7_probe.TRIAL_ID:
        raise ValueError("composition does not contain the pinned full-stock G7 family trial")
    fingerprints = getattr(geometry, "family_source_fingerprints", {}).get("right_rail")
    current_fingerprints = _current_fingerprint_map(fingerprints)
    inventory_hash = _sha256(ROOT / INVENTORY_PATH)
    if inventory_hash != WJ04_TRIAL.source_inventory_sha256:
        raise ValueError("live source inventory differs from the canonical WJ04 pin")
    if dict(geometry.source_inventory) != json.loads(
        (ROOT / INVENTORY_PATH).read_text()
    ):
        raise ValueError("composed source inventory content differs from the canonical file")
    if current_fingerprints.get(INVENTORY_PATH) != inventory_hash:
        raise ValueError("composed right G7 source map does not pin the canonical inventory")
    if current_fingerprints.get("scripts/wood_joint_wj04_upper_g7_crosscut_probe.py") != _sha256(
        ROOT / "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"
    ):
        raise ValueError("composed right G7 source map lacks the pinned producer")

    inventory_rows = _inventory_rows(geometry.source_inventory)
    source_ids = {g7_probe.LOWER_RAIL, g7_probe.UPPER_RAIL, g7_probe.PRINCIPAL}
    candidate_ids = set(CLEAT_DATUMS)
    expected_receiver_ids = source_ids | candidate_ids
    if not expected_receiver_ids <= set(geometry.finished_hosts) | set(geometry.finished_candidate_parts):
        raise ValueError("composition omits a G7 receiver solid")
    for part_id in source_ids:
        if part_id not in inventory_rows:
            raise ValueError(f"canonical inventory omits G7 receiver {part_id}")
        grain = inventory_rows[part_id].get("grain_axis_global_xyz")
        if not grain or len(grain) != 3:
            raise ValueError(f"{part_id}: explicit source grain vector is unavailable")
        _shape_is_valid(geometry.finished_hosts.get(part_id), f"finished source host {part_id}")
    for part_id in candidate_ids:
        _shape_is_valid(
            geometry.finished_candidate_parts.get(part_id),
            f"finished candidate cleat {part_id}",
        )

    specs = tuple(g7_probe.STACK_SPECS)
    if len(specs) != 8 or len({spec.stack_id for spec in specs}) != 8:
        raise ValueError("pinned G7 producer must define eight unique physical bolt stacks")
    expected_axis_ids = {
        _axis_id(spec.stack_id)
        for spec in specs
    }
    actual_family_bores = {
        axis_id
        for axis_id, bore in geometry.candidate_bores.items()
        if getattr(bore, "family", None) == FAMILY
    }
    actual_family_hardware = {
        axis_id
        for axis_id in geometry.candidate_installed_hardware
        if axis_id.startswith(f"{FAMILY}/")
    }
    if actual_family_bores != expected_axis_ids:
        raise ValueError("composed geometry G7 bore identities differ from the exact eight-stack family")
    if actual_family_hardware != expected_axis_ids:
        raise ValueError("composed geometry G7 hardware-axis identities differ from the exact eight stacks")

    bolt_candidate = WJ04_TRIAL.fasteners.bolt_by_id("kl_jack_25c600hcs5z")
    bore_diameter_mm = WJ04_TRIAL.stacks[0].cad_envelope.bore_occupancy_diameter_mm
    physical_bolts = [
        _physical_bolt_record(
            geometry=geometry,
            spec=spec,
            inventory_rows=inventory_rows,
            candidate_shapes={
                part_id: geometry.finished_candidate_parts[part_id]
                for part_id in candidate_ids
            },
            source_shapes={part_id: geometry.finished_hosts[part_id] for part_id in source_ids},
            bore_diameter_mm=bore_diameter_mm,
            bolt_candidate=bolt_candidate,
        )
        for spec in specs
    ]

    specs_by_key: dict[tuple[str, str], list[Any]] = {}
    for spec in specs:
        specs_by_key.setdefault((spec.station_id, spec.interface_id), []).append(spec)
    interfaces = []
    for grouped_specs in specs_by_key.values():
        spec = grouped_specs[0]
        for peer in grouped_specs[1:]:
            if peer.layers != spec.layers:
                raise ValueError(f"{spec.interface_id}: paired bolts disagree on receiver order")
        stack_ids = [row.stack_id for row in grouped_specs]
        if len(stack_ids) != 2:
            raise ValueError(f"{spec.interface_id}: expected two physical bolts per interface")
        axis_origin = _vec(WJ04_TRIAL.frame.to_global(spec.axis_point_basis_mm))
        direction = _unit(WJ04_TRIAL.frame.vector_to_global(spec.axis_direction_basis))
        source_id = next(member for member, _thickness in spec.layers if member not in CLEAT_DATUMS)
        candidate_id = next(member for member, _thickness in spec.layers if member in CLEAT_DATUMS)
        interfaces.append(
            _interface_record(
                spec=spec,
                stack_ids=stack_ids,
                origin=axis_origin,
                direction=direction,
                candidate_shape=geometry.finished_candidate_parts[candidate_id],
                source_row=inventory_rows[source_id],
            )
        )

    # There are two axes at each interface; the manifest stores each physical
    # fastener once and each physical wood/wood interface once.
    if len(physical_bolts) != 8 or len(interfaces) != 4:
        raise ValueError("full-stock joint-pair manifest counts changed")
    unresolved_inputs = {
        "actual_six_case_signed_demands": "missing; WJ09 complete-frame cases required",
        "axial_slip_stiffness_and_bounds": "missing; no adopted value",
        "lateral_slip_stiffness_and_free_travel": "missing; no adopted value",
        "rotational_stiffness_and_bounds": "missing; no adopted value",
        "finite_area_unilateral_contact_law_and_opening": "missing; no adopted value",
        "material_resistance_and_adjustments": "missing; source DF-L No. 2 basis is not a received-stock inspection or resistance calculation",
        "bolt_steel_resistance_and_delivered_section": "missing; catalog candidate only and delivered thread/body not measured",
        "washer_and_nut_delivered_properties": "missing; catalog dimensional candidates only",
        "load_distribution_among_eight_bolts": "missing; no group/joint response model or fresh actions",
    }
    return {
        "schema": SCHEMA,
        "status": "bounded_mechanics_inputs_only",
        "scope": "right inner lower and upper full-stock G7 cleat pair; eight physical ordinary-bolt axes",
        "composition": {
            "trial_id": geometry.trial_id,
            "status": geometry.status,
            "source_inventory_sha256": inventory_hash,
            "right_rail_family_trial_id": g7_probe.TRIAL_ID,
            "right_rail_source_fingerprints_sha256": dict(sorted(current_fingerprints.items())),
            "canonical_wj04_config_sha256": WJ04_TRIAL.canonical_sha256,
        },
        "physical_inventory": {
            "ordinary_physical_bolts": len(physical_bolts),
            "modeled_component_shapes_for_these_bolts": 5 * len(physical_bolts),
            "physical_interfaces": len(interfaces),
            "scope_does_not_cover": "other WJ12/WJ16 duties, the whole frame, the 66 Hillman axes, or native-model readiness",
        },
        "physical_bolts": physical_bolts,
        "physical_interfaces": interfaces,
        "hardware_basis_note": (
            "All eight actual G7 stacks have 127 mm nominal wood grip and bind to "
            "the provisional 6-inch 25C600HCS5Z candidate. The 3-3/4-inch "
            "25C375HCS5Z rail entry in the ordinary-hardware note is for the old "
            "76.2 mm narrow-trial grip and does not apply here."
        ),
        "unresolved_mechanics_inputs": unresolved_inputs,
        "method_boundary": {
            "inherited_pb_or_angle_stiffness_or_resistance": False,
            "global_frame_actions": "not provided; WJ09 source-bound complete-frame cases remain required",
            "capacity_methods": "not evaluated by this input bridge",
            "criteria_map": "docs/wood-joints-mvp/criteria-method-map.md",
        },
        "claims": {
            "capacity_established": False,
            "4d_or_7d_adequacy_established": False,
            "native_analysis_ready": False,
            "whole_candidate_complete": False,
            "assembly_or_access_proven": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_release": False,
        },
    }
