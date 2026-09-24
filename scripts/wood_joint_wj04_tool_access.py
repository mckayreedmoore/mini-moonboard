"""WJ-04 catalog-wrench access and removal screen.

Uses source-bound trial geometry and intentionally broad FACOM external
envelopes. This checks nominal occupied space only. It does not model open-jaw
fit, torque transfer, delivered tool/wood tolerances, or a fabrication-ready
fastener installation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL, validate_wj04_trial

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = ROOT / "docs/wood-joints-mvp/wj04-tool-access.json"
ROOT_SCHEMA = "wood_joint_wj04_tool_access/v1"
HIT_TOLERANCE_MM3 = 1e-6
FLAT_STROKE_DEGREES = 30.0
REINDEX_DEGREES = 60.0
FULL_TURN_DEGREES = 360.0
DEFAULT_PRODUCER_COMMAND = "uv run python -m scripts.wood_joint_wj04_tool_access --write"
DEPENDENCY_PATHS = (
    "mini_moonboard/wood_joint_wj04_config.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_geometry.py",
    "mini_moonboard/floor_flush_width.py",
    "scripts/wood_joint_wj04_probe.py",
    "scripts/wood_joint_clearance.py",
)


def _vector(value: Any, name: str) -> cq.Vector:
    try:
        result = cq.Vector(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a three-component vector") from error
    if not all(math.isfinite(component) for component in result.toTuple()):
        raise ValueError(f"{name} must be finite")
    if result.Length <= 1e-9:
        raise ValueError(f"{name} must be nonzero")
    return result.normalized()


def _positive(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return result


def _tool_frame(
    outward_axis_xyz: Any,
    face_reference_xyz: Any,
    offset_degrees: float,
) -> tuple[cq.Vector, cq.Vector, cq.Vector]:
    """Return handle, width, and thickness axes for one in-plane offset case."""
    outward = _vector(outward_axis_xyz, "outward_axis_xyz")
    reference = cq.Vector(face_reference_xyz)
    reference = reference - outward * reference.dot(outward)
    if reference.Length <= 1e-9:
        raise ValueError("face_reference_xyz must not be parallel to outward axis")
    reference = reference.normalized()
    side = outward.cross(reference).normalized()
    angle = math.radians(float(offset_degrees))
    if not math.isfinite(angle):
        raise ValueError("offset_degrees must be finite")
    handle = (reference * math.cos(angle) + side * math.sin(angle)).normalized()
    width = outward.cross(handle).normalized()
    thickness = outward
    return handle, width, thickness


def build_catalog_wrench_envelope(
    center_xyz_mm: Any,
    outward_axis_xyz: Any,
    face_reference_xyz: Any,
    tool_candidate: Any,
    *,
    offset_degrees: float,
) -> cq.Shape:
    """Build conservative external envelope for one seated FACOM wrench.

    Catalog ``head_width_mm`` is modeled as circular head diameter and as a
    conservative full handle width. The double-ended tool's full overall
    length includes both head envelopes. Head and handle are flat in the
    fastener-face plane. Catalog head-offset values are recorded in the result
    but do not define a global wrench heading in this envelope.

    The supplied angle is a synthetic planar heading for a finite sweep
    sample. It is not the catalog jaw-to-handle offset: exact jaw orientation
    is unavailable. Circular heads and the full-width handle deliberately
    bound external occupancy. They are not exact wrench CAD or evidence that
    the 7/16-in jaw fits the bolt head/nut.
    """
    center = cq.Vector(center_xyz_mm)
    if not all(math.isfinite(component) for component in center.toTuple()):
        raise ValueError("center_xyz_mm must be finite")
    outward = _vector(outward_axis_xyz, "outward_axis_xyz")
    diameter = _positive(tool_candidate.head_width_mm, "head_width_mm")
    thickness = _positive(tool_candidate.head_thickness_mm, "head_thickness_mm")
    overall_length = _positive(tool_candidate.overall_length_mm, "overall_length_mm")
    if overall_length < diameter:
        raise ValueError("overall tool length cannot be shorter than head width")

    handle_axis, _width_axis, thickness_axis = _tool_frame(
        outward, face_reference_xyz, offset_degrees
    )
    radius = diameter / 2
    head_spacing = overall_length - diameter
    local_handle = (
        cq.Workplane(
            cq.Plane(
                origin=center,
                xDir=handle_axis,
                normal=thickness_axis,
            )
        )
        .box(
            head_spacing,
            diameter,
            thickness,
            centered=(False, True, True),
        )
        .val()
    )
    heads = [
        cq.Solid.makeCylinder(
            radius,
            thickness,
            center - thickness_axis * (thickness / 2),
            thickness_axis,
        ),
        cq.Solid.makeCylinder(
            radius,
            thickness,
            center
            + handle_axis * head_spacing
            - thickness_axis * (thickness / 2),
            thickness_axis,
        ),
    ]
    result = cq.Compound.makeCompound([*heads, local_handle])
    if not result.isValid() or not result.Solids():
        raise ValueError("catalog wrench external envelope must be valid solid geometry")
    return result


def rotational_sweep(
    shape: cq.Shape,
    center_xyz_mm: Any,
    axis_xyz: Any,
    angle_degrees: float,
) -> cq.Shape:
    """Return conservative AABB enclosing continuous rotation over angle.

    The source shape first expands to its axis-aligned bounding box. Each of
    that box's eight corners follows an analytic sinusoid around the requested
    axis. Endpoints and every interior coordinate extremum are evaluated, so
    this encloses all intermediate orientations without replacing a short
    stroke with a full-turn sweep. It may still report clashes from the AABB.
    """
    center = cq.Vector(center_xyz_mm)
    axis = _vector(axis_xyz, "axis_xyz")
    angle = float(angle_degrees)
    if not math.isfinite(angle):
        raise ValueError("angle_degrees must be finite")
    if abs(angle) <= 1e-12:
        return shape
    corners = _bbox_corners(shape.BoundingBox())
    if not corners:
        raise ValueError("rotational envelope requires a bounded solid")

    angle_range = sorted((0.0, math.radians(angle)))
    bounds_min = [math.inf, math.inf, math.inf]
    bounds_max = [-math.inf, -math.inf, -math.inf]
    for point in corners:
        delta = point - center
        axial = axis * delta.dot(axis)
        radial = delta - axial
        tangent = axis.cross(radial)
        base = center + axial
        for coordinate in range(3):
            base_value = base.toTuple()[coordinate]
            cosine_value = radial.toTuple()[coordinate]
            sine_value = tangent.toTuple()[coordinate]
            minimum, maximum = _sinusoid_extrema(
                cosine_value, sine_value, angle_range[0], angle_range[1]
            )
            bounds_min[coordinate] = min(bounds_min[coordinate], base_value + minimum)
            bounds_max[coordinate] = max(bounds_max[coordinate], base_value + maximum)

    sizes = [high - low for low, high in zip(bounds_min, bounds_max)]
    if min(sizes) <= 1e-12:
        raise ValueError("rotational envelope has zero axial or planar extent")
    result = cq.Solid.makeBox(
        sizes[0],
        sizes[1],
        sizes[2],
        cq.Vector(*bounds_min),
    )
    if not result.isValid() or not result.Solids():
        raise ValueError("continuous angular envelope did not produce valid geometry")
    return result


def _sinusoid_extrema(
    cosine_coefficient: float,
    sine_coefficient: float,
    angle_low: float,
    angle_high: float,
) -> tuple[float, float]:
    """Return extrema of ``a*cos(t) + b*sin(t)`` on a closed interval."""
    amplitude = math.hypot(cosine_coefficient, sine_coefficient)
    if amplitude <= 1e-15:
        return 0.0, 0.0
    if angle_high - angle_low >= math.tau - 1e-12:
        return -amplitude, amplitude

    def evaluate(angle: float) -> float:
        return cosine_coefficient * math.cos(angle) + sine_coefficient * math.sin(angle)

    values = [evaluate(angle_low), evaluate(angle_high)]
    stationary = math.atan2(sine_coefficient, cosine_coefficient)
    first = math.ceil((angle_low - stationary) / math.pi)
    last = math.floor((angle_high - stationary) / math.pi)
    values.extend(
        evaluate(stationary + index * math.pi)
        for index in range(first, last + 1)
    )
    return min(values), max(values)


def translation_sweep(shape: cq.Shape, displacement_xyz_mm: Any) -> cq.Shape:
    """Return a conservative oriented box enclosing a linear swept path."""
    displacement = cq.Vector(displacement_xyz_mm)
    if not all(math.isfinite(component) for component in displacement.toTuple()):
        raise ValueError("displacement_xyz_mm must be finite")
    if displacement.Length <= 1e-12:
        return shape
    path_axis = displacement.normalized()
    reference = min(
        (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1)),
        key=lambda candidate: abs(candidate.dot(path_axis)),
    )
    x_axis = (reference - path_axis * reference.dot(path_axis)).normalized()
    y_axis = path_axis.cross(x_axis).normalized()
    corners = _bbox_corners(shape.BoundingBox())
    x_values = [point.dot(x_axis) for point in corners]
    y_values = [point.dot(y_axis) for point in corners]
    z_values = [point.dot(path_axis) for point in corners]
    z_min = min(z_values)
    z_max = max(z_values) + displacement.Length
    origin = (
        x_axis * min(x_values)
        + y_axis * min(y_values)
        + path_axis * z_min
    )
    plane = cq.Plane(origin=origin, xDir=x_axis, normal=path_axis)
    result = (
        cq.Workplane(plane)
        .box(
            max(x_values) - min(x_values),
            max(y_values) - min(y_values),
            z_max - z_min,
            centered=(False, False, False),
        )
        .val()
    )
    if not result.isValid() or not result.Solids():
        raise ValueError("translation sweep did not produce valid solid geometry")
    return result


def _bbox_corners(bounds: cq.BoundBox) -> list[cq.Vector]:
    return [
        cq.Vector(x, y, z)
        for x in (bounds.xmin, bounds.xmax)
        for y in (bounds.ymin, bounds.ymax)
        for z in (bounds.zmin, bounds.zmax)
    ]


def _rotate_shape(
    shape: cq.Shape, center_xyz_mm: Any, axis_xyz: Any, angle_degrees: float
) -> cq.Shape:
    center = cq.Vector(center_xyz_mm)
    axis = _vector(axis_xyz, "axis_xyz")
    return shape.rotate(center, center + axis, float(angle_degrees))


def _rotate_vector(vector: cq.Vector, axis: cq.Vector, angle_degrees: float) -> cq.Vector:
    """Rotate vector by Rodrigues' formula without constructing CAD geometry."""
    angle = math.radians(angle_degrees)
    return (
        vector * math.cos(angle)
        + axis.cross(vector) * math.sin(angle)
        + axis * axis.dot(vector) * (1.0 - math.cos(angle))
    )


def wrench_reindex_path(
    seated_wrench: cq.Shape,
    center_xyz_mm: Any,
    outward_axis_xyz: Any,
    handle_axis_xyz: Any,
    *,
    flat_stroke_degrees: float = FLAT_STROKE_DEGREES,
    head_width_mm: float,
) -> dict[str, Any]:
    """Return wrench sweep, lateral exit, one-flat reindex, and reseat volumes.

    The wrench leaves the fastener by translating along its modeled handle axis
    in the head plane. Distance uses one catalog head width. This is a bounded
    open-end exit proxy only; actual jaw direction and release motion are
    unmodeled. No socket-like stud clearance is imposed.
    """
    center = cq.Vector(center_xyz_mm)
    outward = _vector(outward_axis_xyz, "outward_axis_xyz")
    handle_axis = _vector(handle_axis_xyz, "handle_axis_xyz")
    if abs(handle_axis.dot(outward)) > 1e-8:
        raise ValueError("open-end wrench handle axis must stay in fastener-face plane")
    stroke = float(flat_stroke_degrees)
    if not math.isfinite(stroke) or stroke <= 0 or stroke >= 60:
        raise ValueError("flat_stroke_degrees must be positive and below one hex flat")
    lift_mm = _positive(head_width_mm, "head_width_mm")
    reindex = -2.0 * stroke
    post_stroke = _rotate_shape(seated_wrench, center, outward, stroke)
    post_stroke_handle = _rotate_vector(handle_axis, outward, stroke).normalized()
    lift_vector = post_stroke_handle * lift_mm
    lift_sweep = translation_sweep(post_stroke, lift_vector)
    lifted = post_stroke.translate(lift_vector)
    reindex_sweep = rotational_sweep(lifted, center, outward, reindex)
    reindexed = _rotate_shape(lifted, center, outward, reindex)
    reindexed_handle = _rotate_vector(post_stroke_handle, outward, reindex).normalized()
    reseat_sweep = translation_sweep(reindexed, -reindexed_handle * lift_mm)
    stroke_sweep = rotational_sweep(seated_wrench, center, outward, stroke)
    return {
        "stroke_sweep": stroke_sweep,
        "lateral_unseat_sweep": lift_sweep,
        "detached_reindex_sweep": reindex_sweep,
        "lateral_reseat_sweep": reseat_sweep,
        "stroke_degrees": stroke,
        "stroke_sweep_rotation_bound_degrees": abs(stroke),
        "stroke_sweep_is_full_rotation_bound": False,
        "reindex_degrees": reindex,
        "open_end_exit_distance_mm": lift_mm,
        "open_end_exit_motion_is_unverified_proxy": True,
        "reindexed_handle_axis_xyz": [
            round(value, 9) for value in reindexed_handle.toTuple()
        ],
    }


def full_nut_removal_envelope(
    center_xyz_mm: Any,
    outward_axis_xyz: Any,
    tool_candidate: Any,
    axial_travel_mm: float,
) -> cq.Shape:
    """Bound every wrench orientation while nut and wrench advance off bolt.

    Full 360-degree in-plane turning plus axial translation is enclosed by one
    cylinder. Its radius is the published overall tool length: it covers the
    full 100 mm tool length once, without adding head length a second time.
    """
    center = cq.Vector(center_xyz_mm)
    outward = _vector(outward_axis_xyz, "outward_axis_xyz")
    radius = _positive(tool_candidate.overall_length_mm, "overall_length_mm")
    thickness = _positive(tool_candidate.head_thickness_mm, "head_thickness_mm")
    travel = float(axial_travel_mm)
    if not math.isfinite(travel) or travel < 0:
        raise ValueError("axial_travel_mm must be finite and nonnegative")
    return cq.Solid.makeCylinder(
        radius,
        thickness + travel,
        center - outward * (thickness / 2),
        outward,
    )


def _intersection_volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax <= b.xmin
        or b.xmax <= a.xmin
        or a.ymax <= b.ymin
        or b.ymax <= a.ymin
        or a.zmax <= b.zmin
        or b.zmax <= a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def collision_report(
    candidate_shapes: Mapping[str, cq.Shape],
    obstacles: Mapping[str, cq.Shape],
    *,
    excluded_target_ids: tuple[str, ...] = (),
    exclusion_scope: str = (
        "The active bolt's complete hex head or nut and its own shaft are "
        "excluded from tool-envelope clashes. This represents intended contact "
        "and open-end clearance only; jaw fit and actual contact remain "
        "unmodeled. Washers remain obstacles."
    ),
) -> dict[str, Any]:
    """Report envelope clashes after explicitly documented exclusions."""
    excluded = set(excluded_target_ids)
    unknown_exclusions = excluded - set(obstacles)
    if unknown_exclusions:
        raise ValueError(f"excluded target IDs missing from obstacles: {sorted(unknown_exclusions)}")
    remaining = {name: shape for name, shape in obstacles.items() if name not in excluded}
    hits: dict[str, dict[str, float]] = {}
    for candidate_name, candidate_shape in candidate_shapes.items():
        candidate_hits = {}
        for obstacle_name, obstacle_shape in remaining.items():
            volume = _intersection_volume(candidate_shape, obstacle_shape)
            if volume > HIT_TOLERANCE_MM3:
                candidate_hits[obstacle_name] = round(volume, 6)
        if candidate_hits:
            hits[candidate_name] = candidate_hits
    return {
        "external_envelope_hits_mm3": hits,
        "external_envelope_clear": not hits,
        "excluded_target_obstacle_ids": sorted(excluded),
        "exclusion_scope": exclusion_scope,
        "bounds_are_conservative": True,
        "envelope_clash_proves_physical_blockage": False,
        "clear_envelope_proves_actual_tool_access": False,
        "physical_access_established": False,
        "real_tool_impossibility_proven": False,
    }


def moving_part_translation_report(
    candidate_name: str,
    moving_part_id: str,
    moving_part: cq.Shape,
    displacement_xyz_mm: Any,
    obstacles: Mapping[str, cq.Shape],
    *,
    related_excluded_ids: tuple[str, ...] = (),
    exclusion_scope: str,
) -> dict[str, Any]:
    """Check a moving part's translation without colliding it with itself."""
    return collision_report(
        {
            candidate_name: translation_sweep(moving_part, displacement_xyz_mm),
        },
        obstacles,
        excluded_target_ids=(moving_part_id, *related_excluded_ids),
        exclusion_scope=exclusion_scope,
    )


def trial_binding(config=WJ04_TRIAL) -> dict[str, Any]:
    """Return immutable trial and tool provenance for integration artifacts."""
    validate_wj04_trial(config)
    tool = config.fasteners.tools[0]
    trial_sha = getattr(config, "canonical_sha256", None)
    if trial_sha is None:
        encoded = json.dumps(config.as_dict(), sort_keys=True, separators=(",", ":")).encode()
        trial_sha = hashlib.sha256(encoded).hexdigest()
    return {
        "schema": ROOT_SCHEMA,
        "trial_id": config.trial_id,
        "station_id": config.station_id,
        "source_variant": config.source_variant,
        "source_inventory_sha256": config.source_inventory_sha256,
        "trial_config_sha256": trial_sha,
        "fastener_candidates": {
            "bolts": [
                _json_safe(candidate) for candidate in config.fasteners.bolts
            ],
            "hex_head_bounds": _json_safe(config.fasteners.head),
            "nut": _json_safe(config.fasteners.nut),
            "washer": _json_safe(config.fasteners.washer),
            "washers_per_stack": config.fasteners.washers_per_stack,
            "purchase_approved": False,
            "status": "catalog candidates for geometry screening only",
        },
        "tool_candidate": {
            "candidate_id": tool.candidate_id,
            "manufacturer": tool.manufacturer,
            "description": tool.description,
            "wrench_size_in": tool.wrench_size_in,
            "head_width_mm": tool.head_width_mm,
            "modeled_head_diameter_mm": tool.head_width_mm,
            "modeled_head_radius_mm": tool.head_width_mm / 2,
            "head_thickness_mm": tool.head_thickness_mm,
            "overall_length_mm": tool.overall_length_mm,
            "catalog_head_offsets_degrees": list(tool.head_offsets_degrees),
            "catalog_offset_mapping_verified": False,
            "source_urls": list(tool.source_urls),
            "published_dimension_tolerances": tool.published_dimension_tolerances,
            "handle_sweep_verified": tool.handle_sweep_verified,
        },
        "operation_screen": {
            "flat_stroke_degrees": FLAT_STROKE_DEGREES,
            "reindex_degrees": REINDEX_DEGREES,
            "full_turn_degrees": FULL_TURN_DEGREES,
            "synthetic_heading_cases_degrees": list(tool.head_offsets_degrees),
            "partial_rotation_enclosure": (
                "An axis-aligned box encloses continuous rotation of the modeled "
                "tool bounding box. Each corner's coordinate extrema are found "
                "analytically on the requested angle interval."
            ),
            "interpretation": (
                "Two bounded synthetic planar heading cases use the catalog's "
                "15-degree and 75-degree values as sampling angles only. They "
                "do not model the wrench's actual jaw-to-handle offset. Each "
                "case uses a 30-degree turning stroke, an unverified open-end "
                "exit proxy, a detached 60-degree reindex, and reseating. This "
                "is not a torque, fit, or wrench-engagement claim."
            ),
        },
        "unmodeled_limits": [
            "Exact open-jaw outline, opening tolerance, fit, and contact patch",
            "Delivered tool dimensions, handle section/profile, and handle sweep",
            "Delivered wood dimensions, cut variation, and assembly tolerance",
            "Required installation torque and human hand clearance",
            "Physical nut/head rotation phase and contact force",
            "Actual swept width and clearance of the human-held handle",
            "Exact catalog drawing interpretation and three-dimensional jaw orientation",
            "Two simultaneously available wrenches and their human-hand placement",
        ],
        "release_claims": {
            "purchase_approved": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "physical_access_established": False,
        },
    }


def report(
    config=WJ04_TRIAL,
    geometry=None,
    *,
    producer_command: str = DEFAULT_PRODUCER_COMMAND,
) -> dict[str, Any]:
    """Build source-bound tool, counterhold, nut-removal, and bolt-removal screen.

    `geometry` is supplied by the canonical WJ-04 probe adapter. Calling this
    function without it loads that adapter lazily; callers should run it only
    in the parent-approved CAD evidence slot.
    """
    validate_wj04_trial(config)
    if geometry is None:
        from scripts.wood_joint_wj04_probe import materialize_trial_geometry

        geometry = materialize_trial_geometry(config)

    geometry_config = getattr(geometry, "config", None)
    if geometry_config is None:
        raise ValueError("WJ-04 geometry must retain its canonical trial config")
    if geometry_config.canonical_sha256 != config.canonical_sha256:
        raise ValueError("WJ-04 geometry config fingerprint differs from requested trial")
    source_binding = getattr(geometry, "source_binding", None)
    if source_binding is None:
        raise ValueError("WJ-04 geometry must retain its source binding")
    bound_inventory_sha = (
        source_binding.get("inventory_sha256")
        if isinstance(source_binding, Mapping)
        else getattr(source_binding, "inventory_sha256", None)
    )
    if bound_inventory_sha != config.source_inventory_sha256:
        raise ValueError("WJ-04 geometry source inventory differs from canonical trial")

    file_bindings = _file_bindings(config)
    binding = trial_binding(config)
    report_data = {
        **binding,
        "candidate": config.development_candidate_id,
        "source_commit": config.source_commit,
        "producer_sha256": file_bindings["producer_sha256"],
        "producer_command": producer_command,
        "config_source_sha256": file_bindings["config_source_sha256"],
        "dependency_sha256": file_bindings["dependency_sha256"],
        "input_artifact_sha256": file_bindings["input_artifact_sha256"],
        "geometry_source_binding": _json_safe(source_binding),
        "stacks": {},
        "interpretation": (
            "No nominal envelope clash is evidence only for the modeled external "
            "tool envelope and supplied source-bound CAD. A modeled clash can be "
            "a false collision from the deliberately broad envelope; neither a "
            "clear envelope nor a clash proves actual tool access or physical "
            "impossibility. Jaw fit, tool orientation, delivered clearances, and "
            "thread engagement remain unverified."
        ),
    }
    from mini_moonboard.wood_joint_frame import bolt_axis_stroke_shapes

    if not isinstance(getattr(geometry, "stacks", None), Mapping):
        raise TypeError("WJ-04 adapter must expose source-bound BoltStack objects")
    installed_value = getattr(
        geometry,
        "installed_hardware",
        None,
    )
    if installed_value is None:
        installed_value = getattr(geometry, "installed", None)
    if installed_value is None:
        raise ValueError("WJ-04 adapter must expose installed hardware envelopes")

    obstacles = _geometry_obstacles(geometry)
    installed = _flatten_shapes(installed_value, "installed_hardware")
    obstacles.update(installed)
    reference_axes = _reference_axes(config)
    tool = config.fasteners.tools[0]

    for stack_config in config.stacks:
        stack_id = stack_config.stack_id
        if stack_id not in geometry.stacks:
            raise ValueError(f"WJ-04 adapter is missing stack {stack_id!r}")
        stack = geometry.stacks[stack_id]
        direction = _vector(stack.direction, f"{stack_id}.direction")
        expected_direction = _vector(
            config.frame.vector_to_global(stack_config.axis_direction_basis),
            f"{stack_id}.configured_direction",
        )
        if direction.dot(expected_direction) < 1.0 - 1e-7:
            raise ValueError(f"{stack_id} direction disagrees with canonical trial")
        expected_axis = cq.Vector(
            *config.frame.to_global(stack_config.axis_point_basis_mm)
        )
        if (cq.Vector(stack.head_seat.center) - expected_axis).Length > 1e-6:
            raise ValueError(f"{stack_id} axis point disagrees with canonical trial")
        if abs(stack.grip_mm - stack_config.grip_mm) > 1e-6:
            raise ValueError(f"{stack_id} grip disagrees with canonical trial")
        if tuple(layer.body_id for layer in stack.layers) != tuple(
            layer.member_id for layer in stack_config.layers
        ):
            raise ValueError(f"{stack_id} layer order disagrees with canonical trial")
        if (
            stack.hardware.candidate_sku != stack_config.hardware_candidate.sku
            or abs(
                stack.hardware.under_head_length_mm
                - stack_config.hardware_candidate.nominal_length_mm
            )
            > 1e-6
        ):
            raise ValueError(f"{stack_id} hardware disagrees with canonical candidate")

        target_keys = {
            role: _installed_key(installed, stack_id, role)
            for role in ("shaft", "head", "head_washer", "nut", "nut_washer")
        }
        target_shapes = {role: installed[key] for role, key in target_keys.items()}
        head_outward = -direction
        nut_outward = direction
        head_center = _seated_tool_center(
            stack.head_seat.center,
            head_outward,
            target_shapes["head"],
            tool.head_thickness_mm,
        )
        nut_center = _seated_tool_center(
            stack.nut_seat.center,
            nut_outward,
            target_shapes["nut"],
            tool.head_thickness_mm,
        )
        excluded_head = (target_keys["head"], target_keys["shaft"])
        excluded_nut = (target_keys["nut"], target_keys["shaft"])
        axis_reference = reference_axes[stack_id]
        heading_cases = []

        for heading in tool.head_offsets_degrees:
            head_wrench = build_catalog_wrench_envelope(
                head_center,
                head_outward.toTuple(),
                axis_reference,
                tool,
                offset_degrees=heading,
            )
            nut_wrench = build_catalog_wrench_envelope(
                nut_center,
                nut_outward.toTuple(),
                axis_reference,
                tool,
                offset_degrees=heading,
            )
            movement = wrench_reindex_path(
                nut_wrench,
                nut_center,
                nut_outward.toTuple(),
                _tool_frame(nut_outward, axis_reference, heading)[0],
                head_width_mm=tool.head_width_mm,
            )
            head_collision = collision_report(
                {"head_counterhold": head_wrench},
                obstacles,
                excluded_target_ids=excluded_head,
            )
            nut_collision = collision_report(
                {
                    "nut_turn_30deg": movement["stroke_sweep"],
                    "nut_open_end_exit": movement["lateral_unseat_sweep"],
                    "nut_detached_reindex_60deg": movement["detached_reindex_sweep"],
                    "nut_reseat": movement["lateral_reseat_sweep"],
                },
                obstacles,
                excluded_target_ids=excluded_nut,
            )
            paired_collision = collision_report(
                {
                    "nut_turn_30deg": movement["stroke_sweep"],
                    "nut_open_end_exit": movement["lateral_unseat_sweep"],
                    "nut_detached_reindex_60deg": movement["detached_reindex_sweep"],
                    "nut_reseat": movement["lateral_reseat_sweep"],
                },
                {"head_counterhold": head_wrench},
                exclusion_scope="No fastener or opposing tool is excluded.",
            )
            heading_cases.append(
                {
                    "synthetic_heading_proxy_degrees": heading,
                    "requires_two_wrench_units_for_simultaneous_counterhold": True,
                    "head_counterhold": head_collision,
                    "nut_turn_and_reindex": nut_collision,
                    "nut_tool_vs_head_counterhold": paired_collision,
                    "motion": {
                        "stroke_degrees": movement["stroke_degrees"],
                        "stroke_sweep_rotation_bound_degrees": movement[
                            "stroke_sweep_rotation_bound_degrees"
                        ],
                        "stroke_sweep_is_full_rotation_bound": movement[
                            "stroke_sweep_is_full_rotation_bound"
                        ],
                        "detached_reindex_degrees": movement["reindex_degrees"],
                        "open_end_exit_distance_mm": movement[
                            "open_end_exit_distance_mm"
                        ],
                        "open_end_exit_motion_is_unverified_proxy": True,
                    },
                }
            )

        nut_removal = _nut_removal_screen(
            stack,
            tool,
            obstacles,
            target_keys,
            target_shapes,
        )
        bolt_removal_shapes = bolt_axis_stroke_shapes(stack)
        bolt_removal = collision_report(
            bolt_removal_shapes,
            obstacles,
            excluded_target_ids=tuple(target_keys.values()),
            exclusion_scope=(
                "All same-stack installed hardware is treated as already removed. "
                "The active host and cleat remain obstacles; the shaft path must "
                "clear their modeled bores."
            ),
        )
        head_washer_travel = stack.hardware.washer_thickness_mm + 0.01
        head_washer_removal = moving_part_translation_report(
            "head_washer_after_bolt_withdrawal",
            target_keys["head_washer"],
            target_shapes["head_washer"],
            head_outward * head_washer_travel,
            obstacles,
            related_excluded_ids=tuple(
                key for role, key in target_keys.items() if role != "head_washer"
            ),
            exclusion_scope=(
                "The moving head washer's installed copy is excluded as the same "
                "physical part. The same-stack bolt and nut are already removed; "
                "source wood and all unrelated hardware and washers remain obstacles."
            ),
        )
        head_bounds = config.fasteners.head
        nut_bounds = config.fasteners.nut
        nominal_opening_mm = float(Fraction(tool.wrench_size_in) * 25.4)
        report_data["stacks"][stack_id] = {
            "hardware_candidate_id": stack_config.hardware_candidate.candidate_id,
            "bolt_nominal_length_mm": stack_config.hardware_candidate.nominal_length_mm,
            "grip_mm": stack_config.grip_mm,
            "axis_global_xyz_mm": [round(value, 9) for value in stack.head_seat.center.toTuple()],
            "axis_direction_global_xyz": [round(value, 9) for value in direction.toTuple()],
            "target_hardware_keys": target_keys,
            "tool_contact_screen": {
                "wrench_size_in": tool.wrench_size_in,
                "nominal_wrench_opening_mm": round(nominal_opening_mm, 6),
                "wrench_head_thickness_mm": tool.head_thickness_mm,
                "bolt_head_across_flats_range_mm": list(
                    head_bounds.across_flats_range_mm
                ),
                "bolt_head_height_range_mm": list(head_bounds.height_range_mm),
                "nut_across_flats_range_mm": list(nut_bounds.across_flats_range_mm),
                "nut_thickness_range_mm": list(nut_bounds.thickness_range_mm),
                "nominal_opening_inside_head_af_range": (
                    head_bounds.across_flats_range_mm[0]
                    <= nominal_opening_mm
                    <= head_bounds.across_flats_range_mm[1]
                ),
                "nominal_opening_inside_nut_af_range": (
                    nut_bounds.across_flats_range_mm[0]
                    <= nominal_opening_mm
                    <= nut_bounds.across_flats_range_mm[1]
                ),
                "minimum_head_axial_depth_minus_tool_thickness_mm": round(
                    head_bounds.height_range_mm[0] - tool.head_thickness_mm, 6
                ),
                "minimum_nut_axial_depth_minus_tool_thickness_mm": round(
                    nut_bounds.thickness_range_mm[0] - tool.head_thickness_mm, 6
                ),
                "nominal_opening_fit_verified": False,
                "fit_and_contact_verified": False,
                "interpretation": (
                    "The nominal 7/16-in opening lies within the source AF ranges, "
                    "and source bounds provide axial depth for a 3 mm nominal tool "
                    "envelope. The wrench opening tolerance and jaw profile are "
                    "unpublished; this does not establish actual jaw fit, contact "
                    "area, torque, or installed seating."
                ),
            },
            "heading_cases": heading_cases,
            "nut_full_removal": nut_removal,
            "full_bolt_withdrawal": {
                **bolt_removal,
                "modeled_shapes": sorted(bolt_removal_shapes),
                "same_stack_hardware_removed_first": True,
                "thread_end_and_thread_engagement_verified": False,
            },
            "head_washer_removal_after_bolt_withdrawal": {
                **head_washer_removal,
                "outward_travel_mm": round(head_washer_travel, 6),
                "same_stack_bolt_removed_first": True,
                "hand_pickup_clearance_verified": False,
            },
        }

    report_data["limiting_obstacles"] = _limiting_obstacles(report_data["stacks"])
    report_data["has_external_envelope_overlaps"] = bool(
        report_data["limiting_obstacles"]
    )
    report_data["envelope_screen_status"] = (
        "diagnostic_overlap_present"
        if report_data["has_external_envelope_overlaps"]
        else "no_overlap_in_modeled_envelopes"
    )
    report_data["real_tool_impossibility_proven"] = False
    report_data["physical_access_established"] = False
    if file_bindings != _file_bindings(config):
        raise RuntimeError(
            "WJ-04 tool screen source files changed during report generation"
        )
    return report_data


def _file_bindings(config: Any) -> dict[str, Any]:
    dependency_sha256 = {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for relative in DEPENDENCY_PATHS
    }
    producer_sha256 = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
    config_path = "mini_moonboard/wood_joint_wj04_config.py"
    return {
        "producer_sha256": producer_sha256,
        "config_source_sha256": dependency_sha256[config_path],
        "dependency_sha256": dependency_sha256,
        "input_artifact_sha256": {
            config.source_inventory_path: config.source_inventory_sha256,
        },
    }


def render_markdown(report_data: Mapping[str, Any]) -> str:
    """Render a concise human-readable summary from the exact JSON payload."""
    rows = []
    for stack_id, stack in report_data["stacks"].items():
        cases = stack["heading_cases"]
        head = _operation_status([case["head_counterhold"] for case in cases])
        turn = _operation_status([case["nut_turn_and_reindex"] for case in cases])
        pair = _operation_status(
            [case["nut_tool_vs_head_counterhold"] for case in cases]
        )
        removal = stack["nut_full_removal"]
        nut_out = _operation_status(
            [
                removal["wrench_full_turn_and_axial_sweep"],
                removal["nut_translation_sweep"],
                removal["nut_washer_translation_sweep"],
            ]
        )
        bolt_out = _operation_status([stack["full_bolt_withdrawal"]])
        head_washer_out = _operation_status(
            [stack["head_washer_removal_after_bolt_withdrawal"]]
        )
        rows.append(
            f"| {stack_id} | {head} | {turn} | {pair} | {nut_out} | "
            f"{bolt_out} | {head_washer_out} |"
        )
    limiting = report_data.get("limiting_obstacles", [])
    limiting_text = (
        ", ".join(
            f"{row['obstacle_id']} ({row['maximum_reported_intersection_mm3']} mm³)"
            for row in limiting[:8]
        )
        if limiting
        else "None in the modeled envelopes."
    )
    fasteners = report_data["fastener_candidates"]
    bolt_text = ", ".join(
        f"{row['manufacturer']} {row['sku']} ({row['nominal_length_mm']} mm)"
        for row in fasteners["bolts"]
    )
    tool = report_data["tool_candidate"]
    source_links = ", ".join(
        f"[{url}]({url})" for url in tool["source_urls"]
    )
    return (
        "# WJ-04 tool access and removal screen\n\n"
        f"Status: {report_data['envelope_screen_status']}. This is a "
        "conservative catalog-envelope screen, not a physical access pass or "
        "evidence that a real wrench path is impossible.\n\n"
        "## Trial and modeled candidates\n\n"
        f"- Trial: {report_data['trial_id']} at {report_data['station_id']} "
        f"({report_data['source_variant']}).\n"
        f"- Trial config SHA-256: {report_data['trial_config_sha256']}; "
        f"source inventory SHA-256: {report_data['source_inventory_sha256']}.\n"
        f"- Bolts: {bolt_text}. Nut: {fasteners['nut']['manufacturer']} "
        f"{fasteners['nut']['sku']}; washers: "
        f"{fasteners['washers_per_stack']} × {fasteners['washer']['description']} "
        "per stack.\n"
        f"- Wrench: {tool['manufacturer']} {tool['candidate_id']}, "
        f"{tool['wrench_size_in']} in, "
        f"{tool['modeled_head_diameter_mm']} mm nominal external head diameter, "
        f"{tool['head_thickness_mm']} mm thickness, "
        f"{tool['overall_length_mm']} mm overall length. Source: {source_links}.\n"
        "- These remain modeling candidates; purchase, drilling, fabrication, "
        "structural, and physical-access approvals are false.\n\n"
        "## Conservative envelope results\n\n"
        "| Stack | Head counterhold | Nut stroke and reindex | Two-wrench overlap | Nut and nut washer removal | Bolt withdrawal | Head washer removal |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n"
        "Clear means no intersections in this nominal, deliberately broad "
        "envelope. Overlap means that an envelope intersects a modeled "
        "obstacle; it does not prove that an actual open-end wrench cannot "
        "pass. Rotation paths use continuous-angle boxes computed from analytic "
        "corner extrema; translation paths use enclosing boxes. Exact jaw fit, "
        "handle profile, and human-hand clearance are not modeled. The 15°/75° "
        "values are synthetic planar heading samples, not a verified mapping "
        "of the catalog jaw offsets.\n\n"
        f"Limiting modeled obstacles: {limiting_text}\n\n"
        "## Removal sequence screened\n\n"
        f"The model screens a 30° nut-working stroke, an unverified open-end "
        f"exit proxy over one {tool['head_width_mm']} mm head width, detached "
        "60° reindex and "
        "reseating; a full-turn tool envelope while the nut advances to clear "
        "the nominal bolt tip; nut and nut-washer translation; full bolt-axis "
        "withdrawal; then head-washer detachment. The nut washer's source-bounded "
        "minimum ID exceeds the modeled shaft maximum, allowing this nominal axial "
        "slide screen; thread major diameter and received-part fit remain "
        "unverified. Nut/thread fit, full-form "
        "threads at the tip, delivered dimensions, tool tolerances, torque, "
        "installation sequence, and hand pickup are unverified.\n\n"
        "## Reproduction and provenance\n\n"
        f"Run {report_data['producer_command']}. Producer SHA-256: "
        f"{report_data['producer_sha256']}. JSON data: "
        "[wj04-tool-access.json](wj04-tool-access.json).\n"
    )


def _operation_status(rows: list[Mapping[str, Any]]) -> str:
    return (
        "Overlap in bound"
        if any(not row.get("external_envelope_clear", False) for row in rows)
        else "Clear in bound"
    )


def write_report(
    report_data: Mapping[str, Any],
    json_path: Path = DEFAULT_JSON_OUTPUT,
) -> tuple[Path, Path]:
    """Write deterministic JSON and matching Markdown summary."""
    json_path = json_path.resolve()
    markdown_path = json_path.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report_data, indent=2, sort_keys=True) + "\n"
    json_path.write_text(encoded, encoding="utf-8")
    markdown_path.write_text(render_markdown(report_data), encoding="utf-8")
    return json_path, markdown_path


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _flatten_shapes(value: Any, prefix: str) -> dict[str, cq.Shape]:
    if isinstance(value, cq.Shape):
        return {prefix: value}
    if isinstance(value, cq.Workplane):
        return {prefix: value.val()}
    if isinstance(value, Mapping):
        result: dict[str, cq.Shape] = {}
        for key, item in value.items():
            result.update(_flatten_shapes(item, f"{prefix}/{key}"))
        return result
    if isinstance(value, (tuple, list)):
        result = {}
        for index, item in enumerate(value):
            result.update(_flatten_shapes(item, f"{prefix}/{index}"))
        return result
    if value is None:
        return {}
    raise TypeError(
        f"{prefix} contains unsupported geometry value {type(value).__name__}"
    )


def _geometry_obstacles(geometry: Any) -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    finished = getattr(geometry, "finished_parts", None)
    if finished is None:
        finished = getattr(geometry, "finished", None)
    if finished:
        result.update(_flatten_shapes(finished, "finished_parts"))
    else:
        parts = getattr(geometry, "parts", None)
        if parts:
            result.update(_flatten_shapes(parts, "parts"))
        else:
            result.update(_flatten_shapes(getattr(geometry, "wood", {}), "wood"))
    for attr in ("other_wood", "panels", "protected"):
        result.update(_flatten_shapes(getattr(geometry, attr, {}), attr))
    if not result:
        raise ValueError("WJ-04 adapter supplied no source-bound obstruction solids")
    return result


def _installed_key(installed: Mapping[str, cq.Shape], stack_id: str, role: str) -> str:
    suffix = f"/{stack_id}/{role}"
    matches = [key for key in installed if key.endswith(suffix)]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"expected exactly one installed {role} envelope for {stack_id}")


def _seated_tool_center(
    axis_point_xyz: Any,
    outward_axis: cq.Vector,
    target_solid: cq.Shape,
    tool_thickness_mm: float,
) -> tuple[float, float, float]:
    """Seat the outer tool face on the modeled fastener's exterior face."""
    axis_point = cq.Vector(axis_point_xyz)
    projection = axis_point.dot(outward_axis)
    projected_extents = [vertex.Center().dot(outward_axis) for vertex in target_solid.Vertices()]
    if not projected_extents:
        raise ValueError("target hardware envelope has no vertices")
    outer_plane = max(projected_extents)
    thickness = _positive(tool_thickness_mm, "tool_thickness_mm")
    center = axis_point + outward_axis * (outer_plane - projection + thickness / 2)
    return tuple(center.toTuple())


def _reference_axes(config: Any) -> dict[str, tuple[float, float, float]]:
    result = {}
    for stack in config.stacks:
        axis = _vector(
            config.frame.vector_to_global(stack.axis_direction_basis),
            f"{stack.stack_id}.axis_direction_basis",
        )
        cardinal = min(
            (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1)),
            key=lambda candidate: abs(candidate.dot(axis)),
        )
        projected = (cardinal - axis * cardinal.dot(axis)).normalized()
        result[stack.stack_id] = tuple(projected.toTuple())
    return result


def nut_washer_axial_removal_report(
    moving_part_id: str,
    moving_part: cq.Shape,
    obstacles: Mapping[str, cq.Shape],
    *,
    removed_nut_id: str,
    shaft_id: str,
    outward_axis_xyz: Any,
    travel_mm: float,
    washer_min_inner_diameter_mm: float,
    shaft_max_diameter_mm: float,
) -> dict[str, Any]:
    """Screen axial washer travel with only source-supported clearances removed."""
    washer_min_id = _positive(
        washer_min_inner_diameter_mm, "washer_min_inner_diameter_mm"
    )
    shaft_max_diameter = _positive(shaft_max_diameter_mm, "shaft_max_diameter_mm")
    if washer_min_id <= shaft_max_diameter:
        raise ValueError(
        "source-bound washer minimum ID must exceed modeled shaft maximum "
        "diameter before shaft can be excluded from axial washer motion"
        )
    travel = float(travel_mm)
    if not math.isfinite(travel) or travel < 0:
        raise ValueError("travel_mm must be finite and nonnegative")
    axis = _vector(outward_axis_xyz, "outward_axis_xyz")
    report_data = moving_part_translation_report(
        "nut_washer_to_clear_bolt_tip",
        moving_part_id,
        moving_part,
        axis * travel,
        obstacles,
        related_excluded_ids=(removed_nut_id, shaft_id),
        exclusion_scope=(
            "The moving washer's installed copy and already-removed same-stack nut "
            "are excluded. Its same-stack shaft is excluded only for this axial "
            "slide: source-bounded minimum washer ID exceeds canonical modeled "
            "shaft diameter. Unrelated shafts, washers, hardware, and wood remain "
            "obstacles; thread major diameter, delivered-part fit, and assembly "
            "clearances are unverified."
        ),
    )
    report_data["axial_sliding_clearance"] = {
        "motion_is_along_fastener_axis": True,
        "washer_min_inner_diameter_mm": washer_min_id,
        "shaft_max_diameter_mm": shaft_max_diameter,
        "minimum_radial_clearance_mm": round(
            (washer_min_id - shaft_max_diameter) / 2, 6
        ),
        "source_bounds_allow_modeled_axial_slide": True,
        "thread_major_diameter_and_received_clearance_verified": False,
        "delivered_parts_and_assembly_clearance_verified": False,
    }
    return report_data


def _nut_removal_screen(
    stack: Any,
    tool: Any,
    obstacles: Mapping[str, cq.Shape],
    target_keys: Mapping[str, str],
    target_shapes: Mapping[str, cq.Shape],
) -> dict[str, Any]:
    direction = _vector(stack.direction, f"{stack.id}.direction")
    nut_axis_point = cq.Vector(stack.nut_seat.center)
    tip = cq.Vector(stack.under_head_origin) + direction * stack.hardware.under_head_length_mm
    nut_start = nut_axis_point + direction * stack.hardware.washer_thickness_mm
    travel = max(0.0, (tip - nut_start).dot(direction) + 0.01)
    nut_wrench_center = _seated_tool_center(
        nut_axis_point,
        direction,
        target_shapes["nut"],
        tool.head_thickness_mm,
    )
    wrench_sweep = full_nut_removal_envelope(
        nut_wrench_center, direction.toTuple(), tool, travel
    )
    nut_key = target_keys["nut"]
    shaft_key = target_keys["shaft"]
    washer_key = target_keys["nut_washer"]
    wrench_report = collision_report(
        {"full_turn_and_axial_nut_wrench": wrench_sweep},
        obstacles,
        excluded_target_ids=(nut_key, shaft_key),
        exclusion_scope=(
            "The target nut and its own shaft are excluded for intended open-jaw "
            "contact and axial unthreading. Both washers and all other hardware "
            "remain obstacles."
        ),
    )
    nut_report = moving_part_translation_report(
        "nut_to_clear_bolt_tip",
        nut_key,
        target_shapes["nut"],
        direction * travel,
        obstacles,
        related_excluded_ids=(shaft_key,),
        exclusion_scope=(
            "The moving target nut and its own threaded shaft are excluded as "
            "intended contact during unthreading. Its washer and all other "
            "hardware remain obstacles."
        ),
    )
    washer_start = cq.Vector(stack.nut_seat.center)
    washer_travel = max(0.0, (tip - washer_start).dot(direction) + 0.01)
    washer_report = nut_washer_axial_removal_report(
        washer_key,
        target_shapes["nut_washer"],
        obstacles,
        removed_nut_id=nut_key,
        shaft_id=shaft_key,
        outward_axis_xyz=direction.toTuple(),
        travel_mm=washer_travel,
        washer_min_inner_diameter_mm=stack.hardware.washer_id_mm,
        shaft_max_diameter_mm=stack.hardware.steel_diameter_mm,
    )
    return {
        "nominal_axial_travel_to_clear_shaft_tip_mm": round(travel, 6),
        "nominal_nut_washer_travel_to_clear_shaft_tip_mm": round(washer_travel, 6),
        "travel_basis": (
            "Nominal tip plane less the modeled nut's inboard face, using the "
            "canonical stack's modeled washer thickness. Full-form thread at the "
            "tip and usable thread interval are not guaranteed."
        ),
        "wrench_full_turn_and_axial_sweep": wrench_report,
        "nut_translation_sweep": nut_report,
        "nut_washer_translation_sweep": washer_report,
        "tool_radius_mm": tool.overall_length_mm,
        "tool_radius_conservative_vs_overall_length": True,
        "full_nut_removal_verified": False,
        "thread_engagement_and_runout_verified": False,
    }


def _limiting_obstacles(stacks: Mapping[str, Any]) -> list[dict[str, Any]]:
    hits_by_obstacle: dict[str, list[dict[str, Any]]] = {}

    def collect(value: Any, stack_id: str, operation: str) -> None:
        if not isinstance(value, Mapping):
            return
        hits = value.get("external_envelope_hits_mm3", {})
        if not isinstance(hits, Mapping):
            return
        for candidate, rows in hits.items():
            if not isinstance(rows, Mapping):
                continue
            for obstacle, volume in rows.items():
                name = str(obstacle)
                hits_by_obstacle.setdefault(name, []).append(
                    {
                        "stack_id": stack_id,
                        "operation": operation,
                        "candidate_shape": str(candidate),
                        "intersection_mm3": round(float(volume), 6),
                    }
                )

    for stack_id, stack in stacks.items():
        for case in stack["heading_cases"]:
            for operation in ("head_counterhold", "nut_turn_and_reindex", "nut_tool_vs_head_counterhold"):
                collect(case[operation], stack_id, operation)
        for operation in (
            "wrench_full_turn_and_axial_sweep",
            "nut_translation_sweep",
            "nut_washer_translation_sweep",
        ):
            collect(stack["nut_full_removal"][operation], stack_id, operation)
        collect(stack["full_bolt_withdrawal"], stack_id, "full_bolt_withdrawal")
        collect(
            stack["head_washer_removal_after_bolt_withdrawal"],
            stack_id,
            "head_washer_removal_after_bolt_withdrawal",
        )
    return [
        {
            "obstacle_id": name,
            "maximum_reported_intersection_mm3": max(
                row["intersection_mm3"] for row in rows
            ),
            "screen_locations": sorted(
                rows,
                key=lambda row: (
                    -row["intersection_mm3"],
                    row["stack_id"],
                    row["operation"],
                    row["candidate_shape"],
                ),
            ),
        }
        for name, rows in sorted(
            hits_by_obstacle.items(),
            key=lambda item: (
                -max(row["intersection_mm3"] for row in item[1]),
                item[0],
            ),
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help="JSON path; Markdown is written beside it",
    )
    args = parser.parse_args()
    if not args.write and args.output.resolve() != DEFAULT_JSON_OUTPUT.resolve():
        parser.error("--output requires --write")
    command = DEFAULT_PRODUCER_COMMAND
    if args.output.resolve() != DEFAULT_JSON_OUTPUT.resolve():
        command = f"{DEFAULT_PRODUCER_COMMAND} --output {args.output}"
    data = report(producer_command=command)
    if args.write:
        json_path, markdown_path = write_report(data, args.output)
        print(f"Wrote {json_path} and {markdown_path}")
    else:
        print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
