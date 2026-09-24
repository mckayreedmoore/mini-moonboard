"""Disposable WJ-03 compact outer-envelope geometry comparison.

This is a source-bound geometric diagnostic, not a structural, procurement,
fabrication, or build acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import (
    BRIDGE_LENGTH_MM,
    LINK_LENGTH_MM,
    LINK_Z0_MM,
    ORDINARY_REAR_ENVELOPE_MM,
    SIDES,
    SOURCE_HOST_IDS,
    SPINE_SECTION_MM,
    SPINE_Z0_MM,
    _connector_bores,
    _contact_geometry,
    _finished_source_hosts,
    _interfaces,
    _make_parts,
    _make_stacks,
    _stack,
    installed_stack_shapes,
    validate_source_binding,
)
from mini_moonboard.wood_joint_geometry import (
    CutRecord,
    FinishedPart,
    LocalFrame,
    bolt_stack_report,
    local_extrema,
    washer_support_report,
)
from mini_moonboard.wood_joint_panel_machining import (
    PANEL_NAMES,
    candidate_panel_replacements,
)
from scripts.wood_joint_clearance import (
    _protected_hits_exact,
    _wj03_protected_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
PANEL_HELPER = ROOT / "mini_moonboard/wood_joint_panel_machining.py"

SPINE_REAR_Y_MM = -182.05
SPINE_FRONT_Y_MM = -42.35
SPINE_DEPTH_MM = 139.7
SPINE_LENGTH_MM = 269.95
BRIDGE_FRONT_Y_MM = SPINE_REAR_Y_MM
BRIDGE_HEIGHT_MM = 88.9
UNDER_LINK_DEPTH_MM = SPINE_SECTION_MM
SIDE_BOLT_LOCAL_TN_MM = ((0.0, 84.5), (45.0, 84.5))
SIDE_BOLT_LENGTH_MM = 203.2
WASHER_THICKNESS_MM = 1.651
NUT_HEIGHT_MM = 5.7404
_GEOMETRY_TOLERANCE_MM = 1e-6
_VOLUME_TOLERANCE_MM3 = 1e-6


@dataclass(frozen=True)
class Hypothesis:
    id: str
    bridge_depth_mm: float
    bridge_rear_y_mm: float
    bevel_n_limit_mm: float
    bridge_bevel_n_limit_mm: float | None
    bridge_spine_length_mm: float
    bridge_link_length_mm: float
    bridge_stock: str

    @property
    def bridge_spine_grip_mm(self) -> float:
        return self.bridge_depth_mm + SPINE_DEPTH_MM

    @property
    def bridge_link_grip_mm(self) -> float:
        return self.bridge_depth_mm + UNDER_LINK_DEPTH_MM


HYPOTHESES = (
    Hypothesis(
        "full_bridge_4x6_spine_bevel_137",
        88.9,
        -270.95,
        137.0,
        None,
        254.0,
        203.2,
        "nominal 4x4 solid-sawn DF-L No. 2 cutoff",
    ),
    Hypothesis(
        "compact_bridge_4x6_spine_bevel_137_7",
        38.1,
        -220.15,
        137.7,
        None,
        203.2,
        152.4,
        "nominal 2x4 solid-sawn DF-L No. 2 cutoff",
    ),
    Hypothesis(
        "compact_bridge_rear_bevel_4x6_spine_137_7",
        38.1,
        -220.15,
        137.7,
        137.7,
        203.2,
        152.4,
        "nominal 2x4 solid-sawn DF-L No. 2 cutoff",
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rounded(value: float, digits: int = 6) -> float:
    result = round(value, digits)
    return 0.0 if abs(result) < 10 ** (-digits) else result


def _bounds(shape: cq.Shape) -> list[float]:
    box = shape.BoundingBox()
    return [
        _rounded(value)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _shape_record(shape: cq.Shape) -> dict[str, object]:
    return {
        "bounds_xyz_mm": _bounds(shape),
        "volume_mm3": _rounded(shape.Volume()),
    }


def _clip_polygon_half_plane(
    polygon: list[tuple[float, float]], signed, keep_positive: bool
) -> list[tuple[float, float]]:
    """Clip a Y/Z polygon by a signed linear plane equation."""
    result: list[tuple[float, float]] = []
    if not polygon:
        return result

    def inside(point: tuple[float, float]) -> bool:
        distance = signed(point)
        return distance >= 0.0 if keep_positive else distance <= 0.0

    previous = polygon[-1]
    previous_distance = signed(previous)
    previous_inside = inside(previous)
    for current in polygon:
        current_distance = signed(current)
        current_inside = inside(current)
        if current_inside != previous_inside:
            fraction = previous_distance / (previous_distance - current_distance)
            result.append(
                (
                    previous[0] + fraction * (current[0] - previous[0]),
                    previous[1] + fraction * (current[1] - previous[1]),
                )
            )
        if current_inside:
            result.append(current)
        previous, previous_distance, previous_inside = (
            current,
            current_distance,
            current_inside,
        )
    compact: list[tuple[float, float]] = []
    for point in result:
        if not compact or math.dist(point, compact[-1]) > _GEOMETRY_TOLERANCE_MM:
            compact.append(point)
    if len(compact) > 1 and math.dist(compact[0], compact[-1]) < _GEOMETRY_TOLERANCE_MM:
        compact.pop()
    return compact


def _clip_above_local_n(
    shape: cq.Shape, frame: LocalFrame, limit_mm: float
) -> cq.Shape:
    """Keep the solid half-space N <= limit in a global, named frame."""
    box = shape.BoundingBox()
    square = [
        (box.ymin - 1.0, box.zmin - 1.0),
        (box.ymax + 1.0, box.zmin - 1.0),
        (box.ymax + 1.0, box.zmax + 1.0),
        (box.ymin - 1.0, box.zmax + 1.0),
    ]

    def signed(point: tuple[float, float]) -> float:
        xyz = cq.Vector(box.xmin, point[0], point[1])
        return (xyz - frame.origin).dot(frame.n) - limit_mm

    removed_side = _clip_polygon_half_plane(square, signed, keep_positive=True)
    if len(removed_side) < 3:
        return shape
    wire = cq.Wire.makePolygon(
        [cq.Vector(box.xmin - 1.0, y, z) for y, z in removed_side], close=True
    )
    cutter = cq.Solid.extrudeLinear(wire, [], cq.Vector(box.xlen + 2.0, 0, 0))
    return shape.cut(cutter).clean()


def _source_frame(inventory: dict, part_id: str) -> LocalFrame:
    row = next(row for row in inventory["parts"] if row["part_id"] == part_id)
    transform = row["local_to_global_transform"]
    axes = row["local_axes"]
    return LocalFrame(
        tuple(transform[index][3] for index in range(3)),
        tuple(axes["X"]),
        tuple(axes["T"]),
        tuple(axes["N"]),
    )


def _world_tn(frame: LocalFrame, t_mm: float, n_mm: float) -> cq.Vector:
    return frame.origin + frame.t * t_mm + frame.n * n_mm


def _bridge_fabrication_method(spec: Hypothesis) -> str:
    if spec.bridge_bevel_n_limit_mm is not None:
        return "crosscuts, one rear bevel, and through-bores"
    return "crosscuts and through-bores"


def _canonical_frame(source_shapes: dict[str, cq.Shape], side: str) -> LocalFrame:
    header = source_shapes["base_header"].BoundingBox()
    post = source_shapes[f"base_post_outer_{side}"].BoundingBox()
    return LocalFrame(
        (
            post.xmin if side == "left" else post.xmax,
            header.ymax,
            header.zmin,
        ),
        (1.0, 0.0, 0.0),
        (0.0, math.cos(math.radians(50)), math.sin(math.radians(50))),
        (0.0, -math.sin(math.radians(50)), math.cos(math.radians(50))),
    )


def _raw_parts(
    side: str, wood: dict[str, cq.Shape], spec: Hypothesis
) -> dict[str, cq.Shape]:
    legacy = _make_parts(side, wood)
    spine_id = f"knee_outer_{side}_spine"
    bridge_id = f"knee_outer_{side}_rear_bridge"
    link_id = f"knee_outer_{side}_under_header_link"
    spine_box = legacy[spine_id].BoundingBox()
    bridge_box = legacy[bridge_id].BoundingBox()
    return {
        spine_id: cq.Solid.makeBox(
            SPINE_SECTION_MM,
            SPINE_DEPTH_MM,
            SPINE_LENGTH_MM,
            cq.Vector(spine_box.xmin, SPINE_REAR_Y_MM, SPINE_Z0_MM),
        ),
        bridge_id: cq.Solid.makeBox(
            BRIDGE_LENGTH_MM,
            spec.bridge_depth_mm,
            BRIDGE_HEIGHT_MM,
            cq.Vector(bridge_box.xmin, spec.bridge_rear_y_mm, LINK_Z0_MM),
        ),
        link_id: legacy[link_id],
    }


def _stacks(
    side: str,
    wood: dict[str, cq.Shape],
    spec: Hypothesis,
    ids: dict[str, str],
    side_frame: LocalFrame,
) -> dict:
    stacks = _make_stacks(side, wood, ids)
    spine_box = _raw_parts(side, wood, spec)[ids["spine"]].BoundingBox()
    bolt_x = spine_box.xmin if side == "left" else spine_box.xmax
    sign = 1.0 if side == "left" else -1.0
    for index, (t_mm, n_mm) in enumerate(((0.0, 84.5), (45.0, 84.5)), 1):
        point = _world_tn(side_frame, t_mm, n_mm)
        bolt_id = f"knee_outer_{side}_side_{index}"
        stacks[bolt_id] = _stack(
            bolt_id,
            (bolt_x, point.y, point.z),
            (sign, 0.0, 0.0),
            ((ids["spine"], SPINE_SECTION_MM), (f"base_side_{side}", 88.9)),
            SIDE_BOLT_LENGTH_MM,
        )
    for bolt_id, old in tuple(stacks.items()):
        if "_bridge_spine_" in bolt_id:
            stacks[bolt_id] = _stack(
                bolt_id,
                (old.head_seat.center.x, spec.bridge_rear_y_mm, old.head_seat.center.z),
                (0.0, 1.0, 0.0),
                (
                    (ids["bridge"], spec.bridge_depth_mm),
                    (ids["spine"], SPINE_DEPTH_MM),
                ),
                spec.bridge_spine_length_mm,
            )
        elif "_bridge_link_" in bolt_id:
            stacks[bolt_id] = _stack(
                bolt_id,
                (old.head_seat.center.x, spec.bridge_rear_y_mm, old.head_seat.center.z),
                (0.0, 1.0, 0.0),
                (
                    (ids["bridge"], spec.bridge_depth_mm),
                    (ids["under"], UNDER_LINK_DEPTH_MM),
                ),
                spec.bridge_link_length_mm,
            )
    return stacks


def _finished_candidate_parts(
    side: str,
    raw: dict[str, cq.Shape],
    stacks: dict,
    datum: LocalFrame,
    spec: Hypothesis,
    inventory_sha256: str,
) -> dict[str, FinishedPart]:
    ids = {
        "spine": f"knee_outer_{side}_spine",
        "bridge": f"knee_outer_{side}_rear_bridge",
        "under": f"knee_outer_{side}_under_header_link",
    }
    clipped = dict(raw)
    clipped[ids["spine"]] = _clip_above_local_n(
        raw[ids["spine"]], datum, spec.bevel_n_limit_mm
    )
    bevel = raw[ids["spine"]].cut(clipped[ids["spine"]]).clean()
    bridge_bevel = None
    if spec.bridge_bevel_n_limit_mm is not None:
        clipped[ids["bridge"]] = _clip_above_local_n(
            raw[ids["bridge"]], datum, spec.bridge_bevel_n_limit_mm
        )
        bridge_bevel = raw[ids["bridge"]].cut(clipped[ids["bridge"]]).clean()
    bore_cuts = _connector_bores(clipped, stacks)
    stock = {
        ids["spine"]: (
            "nominal 4x6 solid-sawn DF-L No. 2 cutoff",
            (SPINE_SECTION_MM, SPINE_DEPTH_MM, SPINE_LENGTH_MM),
            (0.0, 0.0, 1.0),
            "crosscuts, one rear bevel, and through-bores",
        ),
        ids["bridge"]: (
            spec.bridge_stock,
            (BRIDGE_LENGTH_MM, spec.bridge_depth_mm, BRIDGE_HEIGHT_MM),
            (1.0, 0.0, 0.0),
            _bridge_fabrication_method(spec),
        ),
        ids["under"]: (
            "nominal 4x4 solid-sawn DF-L No. 2 cutoff",
            (LINK_LENGTH_MM, 88.9, 88.9),
            (1.0, 0.0, 0.0),
            "crosscuts and through-bores",
        ),
    }
    parts = {}
    for part_id, uncut in raw.items():
        finished = clipped[part_id]
        records = []
        if part_id == ids["spine"]:
            records.append(
                CutRecord(
                    f"{part_id}/bevel_n_le_{spec.bevel_n_limit_mm:g}",
                    part_id,
                    "trim",
                    bevel,
                    "planar bevel cut in canonical local N frame",
                )
            )
        elif part_id == ids["bridge"] and bridge_bevel is not None:
            records.append(
                CutRecord(
                    f"{part_id}/bevel_n_le_{spec.bridge_bevel_n_limit_mm:g}",
                    part_id,
                    "trim",
                    bridge_bevel,
                    "planar bevel cut in canonical local N frame",
                )
            )
        for bolt_id, cutter in bore_cuts[part_id]:
            next_shape = finished.cut(cutter).clean()
            if finished.Volume() - next_shape.Volume() > _VOLUME_TOLERANCE_MM3:
                records.append(
                    CutRecord(
                        f"{part_id}/{bolt_id}",
                        part_id,
                        "bore",
                        cutter,
                        "candidate through-bore; jig and bit unselected",
                    )
                )
            finished = next_shape
        product, dimensions, grain, method = stock[part_id]
        box = uncut.BoundingBox()
        parts[part_id] = FinishedPart(
            id=part_id,
            stock_product=product,
            actual_dimensions_mm=dimensions,
            material="DF-L No. 2 assumed; delivered stock unobserved",
            grain_axis=grain,
            frame=LocalFrame(
                (box.xmin, box.ymin, box.zmin),
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1),
            ),
            transport_owner=f"knee_outer_{side}",
            uncut_shape=uncut,
            finished_shape=finished,
            modifications=tuple(records),
            source_sha256=inventory_sha256,
            fabrication_method=method,
        )
    return parts


def _intersection_hits(candidates: dict[str, cq.Shape], obstacles: dict[str, cq.Shape]):
    hits = []
    for candidate_id, shape in candidates.items():
        a = shape.BoundingBox()
        for obstacle_id, obstacle in obstacles.items():
            b = obstacle.BoundingBox()
            if (
                a.xmax <= b.xmin
                or b.xmax <= a.xmin
                or a.ymax <= b.ymin
                or b.ymax <= a.ymin
                or a.zmax <= b.zmin
                or b.zmax <= a.zmin
            ):
                continue
            volume = _intersection_volume(shape, obstacle)
            if volume > _VOLUME_TOLERANCE_MM3:
                hits.append(
                    {
                        "candidate_id": candidate_id,
                        "obstacle_id": obstacle_id,
                        "intersection_volume_mm3": _rounded(volume, 9),
                    }
                )
    return hits


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


def _body_timber_hits(
    candidate_bodies: dict[str, cq.Shape],
    finished_timber: dict[str, cq.Shape],
) -> list[dict[str, object]]:
    hits = []
    for body_id, body in candidate_bodies.items():
        for timber_id, timber in finished_timber.items():
            if body_id == timber_id:
                continue
            volume = _intersection_volume(body, timber)
            if volume > _VOLUME_TOLERANCE_MM3:
                hits.append(
                    {
                        "candidate_body_id": body_id,
                        "unintended_timber_id": timber_id,
                        "intersection_volume_mm3": _rounded(volume, 9),
                    }
                )
    return hits


def _stack_timber_hits(
    installed_by_side: dict[str, dict[str, dict[str, cq.Shape]]],
    finished_timber: dict[str, cq.Shape],
) -> list[dict[str, object]]:
    hits = []
    for side_components in installed_by_side.values():
        for bolt_id, roles in side_components.items():
            for role, component in roles.items():
                for timber_id, timber in finished_timber.items():
                    volume = _intersection_volume(component, timber)
                    if volume > _VOLUME_TOLERANCE_MM3:
                        hits.append(
                            {
                                "bolt_id": bolt_id,
                                "component": role,
                                "unintended_timber_id": timber_id,
                                "intersection_volume_mm3": _rounded(volume, 9),
                            }
                        )
    return hits


def _cross_stack_hits(
    installed_by_side: dict[str, dict[str, dict[str, cq.Shape]]]
) -> list[dict[str, object]]:
    components = [
        (bolt_id, role, shape)
        for side_components in installed_by_side.values()
        for bolt_id, roles in side_components.items()
        for role, shape in roles.items()
    ]
    hits = []
    for index, (first_bolt, first_role, first_shape) in enumerate(components):
        for second_bolt, second_role, second_shape in components[index + 1 :]:
            if first_bolt == second_bolt:
                continue
            volume = _intersection_volume(first_shape, second_shape)
            if volume > _VOLUME_TOLERANCE_MM3:
                hits.append(
                    {
                        "first": f"{first_bolt}/{first_role}",
                        "second": f"{second_bolt}/{second_role}",
                        "intersection_volume_mm3": _rounded(volume, 9),
                    }
                )
    return hits


def _stack_record(stack, physical: dict[str, cq.Shape]) -> dict[str, object]:
    length = bolt_stack_report(stack)
    head_support = washer_support_report(
        stack.head_seat,
        physical[stack.head_seat.body_id],
        stack.hardware,
    )
    nut_support = washer_support_report(
        stack.nut_seat,
        physical[stack.nut_seat.body_id],
        stack.hardware,
    )
    return {
        "candidate_specification": stack.hardware.candidate_sku,
        "catalog_length_provisional_mm": stack.hardware.under_head_length_mm,
        "grip_mm": stack.grip_mm,
        "nominal_required_under_head_length_mm": _rounded(
            length.required_under_head_length_mm
        ),
        "nominal_length_margin_mm": _rounded(length.length_margin_mm),
        "layers_head_to_nut": [
            {"body_id": layer.body_id, "thickness_mm": layer.thickness_mm}
            for layer in stack.layers
        ],
        "direction_global_xyz": list(stack.direction.toTuple()),
        "head_washer_seat_global_xyz_mm": list(stack.head_seat.center.toTuple()),
        "nut_washer_seat_global_xyz_mm": list(stack.nut_seat.center.toTuple()),
        "washer_support": {
            "head": {
                "fraction": _rounded(head_support.support_fraction, 9),
                "full_seat": head_support.full_seat,
                "unsupported_area_mm2": _rounded(head_support.unsupported_area_mm2),
            },
            "nut": {
                "fraction": _rounded(nut_support.support_fraction, 9),
                "full_seat": nut_support.full_seat,
                "unsupported_area_mm2": _rounded(nut_support.unsupported_area_mm2),
            },
        },
        "components": {
            role: _shape_record(shape)
            for role, shape in installed_stack_shapes(stack).items()
        },
    }


def _build(spec: Hypothesis, source=None) -> dict[str, object]:
    source = variant(KERF_RIGHT) if source is None else source
    binding = validate_source_binding(source)
    inventory = json.loads(SOURCE_INVENTORY.read_text())
    uncut_parts = tuple(source.uncut_wood_parts())
    current_parts = tuple(source.parts())
    wood = {part.name: part.shape for part in uncut_parts}
    current = {part.name: part.shape for part in current_parts}

    # Bind the raw source before using the local, candidate-only panel repair.
    replacements = candidate_panel_replacements(
        source, current_parts=current_parts, uncut_parts=uncut_parts
    )
    panels = {name: current[name] for name in PANEL_NAMES}
    panels.update({name: part.shape for name, part in replacements.items()})
    if set(panels) != PANEL_NAMES:
        raise ValueError("The remachined panel obstacle map must contain six panels")

    raw_by_side = {side: _raw_parts(side, wood, spec) for side in SIDES}
    ids_by_side = {
        side: {
            "spine": f"knee_outer_{side}_spine",
            "bridge": f"knee_outer_{side}_rear_bridge",
            "under": f"knee_outer_{side}_under_header_link",
        }
        for side in SIDES
    }
    stack_by_side = {
        side: _stacks(
            side,
            wood,
            spec,
            ids_by_side[side],
            _source_frame(inventory, f"base_side_{side}"),
        )
        for side in SIDES
    }
    all_stacks = {
        bolt_id: stack
        for side_stacks in stack_by_side.values()
        for bolt_id, stack in side_stacks.items()
    }
    source_hosts = _finished_source_hosts(
        wood,
        {part_id: current[part_id] for part_id in SOURCE_HOST_IDS},
        source.connections(),
        all_stacks,
        binding,
    )
    parts_by_side = {}
    for side in SIDES:
        datum = _canonical_frame(wood, side)
        parts_by_side[side] = _finished_candidate_parts(
            side,
            raw_by_side[side],
            stack_by_side[side],
            datum,
            spec,
            binding.inventory_sha256,
        )

    installed_by_side = {
        side: {
            bolt_id: installed_stack_shapes(stack)
            for bolt_id, stack in stack_by_side[side].items()
        }
        for side in SIDES
    }
    all_candidate_shapes = {
        **{
            part_id: part.finished_shape
            for rows in parts_by_side.values()
            for part_id, part in rows.items()
        },
        **{
            f"{bolt_id}/{role}": shape
            for rows in installed_by_side.values()
            for bolt_id, roles in rows.items()
            for role, shape in roles.items()
        },
    }
    protected = _wj03_protected_inventory(source)
    protected_hits = _protected_hits_exact(all_candidate_shapes, protected)
    panel_hits = _intersection_hits(all_candidate_shapes, panels)
    candidate_bodies = {
        part_id: part.finished_shape
        for rows in parts_by_side.values()
        for part_id, part in rows.items()
    }
    finished_timber = {name: current[name] for name in wood}
    finished_timber.update({name: part.shape for name, part in replacements.items()})
    finished_timber.update(
        {part_id: part.finished_shape for part_id, part in source_hosts.items()}
    )
    finished_timber.update(candidate_bodies)
    body_timber_hits = _body_timber_hits(candidate_bodies, finished_timber)
    stack_timber_hits = _stack_timber_hits(
        installed_by_side, finished_timber
    )
    cross_stack_hits = _cross_stack_hits(installed_by_side)

    node_reports = {}
    for side in SIDES:
        ids = ids_by_side[side]
        host_ids = ("base_header", f"base_post_outer_{side}", f"base_side_{side}")
        node_hosts = {part_id: source_hosts[part_id] for part_id in host_ids}
        physical = {
            **{
                part_id: part.finished_shape
                for part_id, part in parts_by_side[side].items()
            },
            **{part_id: part.finished_shape for part_id, part in node_hosts.items()},
        }
        sign = 1.0 if side == "left" else -1.0
        specs = {
            "spine_post": (
                physical[ids["spine"]],
                physical[f"base_post_outer_{side}"],
                (sign, 0, 0),
            ),
            "spine_side": (
                physical[ids["spine"]],
                physical[f"base_side_{side}"],
                (sign, 0, 0),
            ),
            "bridge_spine": (
                physical[ids["bridge"]],
                physical[ids["spine"]],
                (0, 1, 0),
            ),
            "bridge_link": (
                physical[ids["bridge"]],
                physical[ids["under"]],
                (0, 1, 0),
            ),
            "link_header": (
                physical[ids["under"]],
                physical["base_header"],
                (0, 0, 1),
            ),
            "spine_header_end": (
                physical[ids["spine"]],
                physical["base_header"],
                (sign, 0, 0),
            ),
        }
        contact_geometry = {
            name: _contact_geometry(*contact) for name, contact in specs.items()
        }
        areas = {name: row[0] for name, row in contact_geometry.items()}
        frames = {name: row[1] for name, row in contact_geometry.items()}
        interfaces = _interfaces(side, stack_by_side[side], ids, frames)

        datum = _canonical_frame(wood, side)
        permanent = [
            *(part.finished_shape for part in parts_by_side[side].values()),
            *(
                shape
                for roles in installed_by_side[side].values()
                for shape in roles.values()
            ),
        ]
        extrema = [local_extrema(shape, datum).n_mm for shape in permanent]
        n_min = min(row[0] for row in extrema)
        n_max = max(row[1] for row in extrema)
        node_reports[side] = {
            "part_bounds_and_volume": {
                part_id: {
                    "uncut": _shape_record(part.uncut_shape),
                    "finished": _shape_record(part.finished_shape),
                    "stock_product": part.stock_product,
                    "actual_dimensions_mm": list(part.actual_dimensions_mm),
                    "cuts": [cut.id for cut in part.modifications],
                    "cut_volumes_mm3": {
                        cut.id: _rounded(cut.removed_volume_mm3, 3)
                        for cut in part.modifications
                    },
                }
                for part_id, part in parts_by_side[side].items()
            },
            "contact_patches": {
                name: {
                    "measured_area_mm2": _rounded(area),
                    "measurement": "final-solid 0.1 mm translated intersection / depth",
                    "origin_global_xyz_mm": [
                        _rounded(value) for value in frames[name].origin.toTuple()
                    ],
                    "positive_computed_contact": area > 0,
                }
                for name, area in areas.items()
            },
            "interfaces": [
                {
                    "interface_id": row.id,
                    "body_ids": list(row.body_ids),
                    "bolt_group_ids": list(row.bolt_group_ids),
                    "bolt_penetration_order": list(row.bolt_penetration_order),
                    "behavior": row.behavior,
                }
                for row in interfaces
            ],
            "installed_stacks": {
                bolt_id: _stack_record(stack, physical)
                for bolt_id, stack in stack_by_side[side].items()
            },
            "canonical_rear_envelope": {
                "origin_global_xyz_mm": [
                    _rounded(value) for value in datum.origin.toTuple()
                ],
                "t_global_xyz": [_rounded(value) for value in datum.t.toTuple()],
                "n_global_xyz": [_rounded(value) for value in datum.n.toTuple()],
                "n_min_mm": _rounded(n_min),
                "n_max_mm": _rounded(n_max),
                "rearward_projection_mm": _rounded(n_max),
                "ordinary_limit_mm": ORDINARY_REAR_ENVELOPE_MM,
                "additional_over_ordinary_mm": _rounded(
                    n_max - ORDINARY_REAR_ENVELOPE_MM
                ),
            },
        }

    return {
        "schema": "wood_joint_wj03_compact_outer_probe/v1",
        "hypothesis": {
            "id": spec.id,
            "spine_y_bounds_mm": [SPINE_REAR_Y_MM, SPINE_FRONT_Y_MM],
            "spine_section_x_by_y_mm": [SPINE_SECTION_MM, SPINE_DEPTH_MM],
            "spine_bevel_local_n_limit_mm": spec.bevel_n_limit_mm,
            "bridge_bevel_local_n_limit_mm": spec.bridge_bevel_n_limit_mm,
            "bridge_y_bounds_mm": [spec.bridge_rear_y_mm, BRIDGE_FRONT_Y_MM],
            "bridge_depth_mm": spec.bridge_depth_mm,
            "bridge_spine_grip_mm": spec.bridge_spine_grip_mm,
            "bridge_link_grip_mm": spec.bridge_link_grip_mm,
            "side_bolt_source_local_TN_centers_mm": [
                list(row) for row in SIDE_BOLT_LOCAL_TN_MM
            ],
            "hardware_status": "provisional modeled lengths; no catalog fit acceptance",
            "structural_status": "not assessed",
        },
        "source_binding": {
            "source_commit": inventory["source_commit"],
            "source_inventory_sha256": binding.inventory_sha256,
            "runtime_module_sha256": binding.runtime_module_sha256,
            "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
            "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
            "panel_replacement_helper": (
                "mini_moonboard.wood_joint_panel_machining.candidate_panel_replacements"
            ),
            "panel_replacement_helper_sha256": _sha256(PANEL_HELPER),
            "panel_obstacle_part_ids": sorted(panels),
            "panel_obstacle_count": len(panels),
        },
        "source_host_openings": (
            "Built from selected source.parts() and uncut source hosts. Original "
            "openings remain; only replaced WJ-03 duty SDS axes are restored before "
            "candidate bores. No previous WJ-03 trial solids or bores are input."
        ),
        "protected_counts": {
            "candidate_panel_obstacles": len(panels),
            "fixed_purchased_panel_screw_envelopes": protected["counts"][
                "panel_screws"
            ],
            "starting_frame_bolt_axes": 12,
            "starting_frame_bolt_components": protected["counts"][
                "frame_bolt_components"
            ],
        },
        "nodes": node_reports,
        "protected_geometry_intersections": protected_hits,
        "candidate_vs_final_panel_intersections": panel_hits,
        "candidate_bodies_vs_unintended_finished_timber": body_timber_hits,
        "installed_stacks_vs_unintended_finished_timber": stack_timber_hits,
        "cross_stack_component_intersections": cross_stack_hits,
        "acceptance": "not assessed",
    }


def build_probe(hypothesis_id: str | None = None, source=None) -> dict[str, object]:
    selected = (
        HYPOTHESES
        if hypothesis_id is None
        else tuple(row for row in HYPOTHESES if row.id == hypothesis_id)
    )
    if not selected:
        raise ValueError(f"Unknown hypothesis: {hypothesis_id}")
    return {
        "schema": "wood_joint_wj03_compact_outer_probe_collection/v1",
        "probes": [_build(row, source=source) for row in selected],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypothesis", choices=[row.id for row in HYPOTHESES])
    args = parser.parse_args()
    print(json.dumps(build_probe(args.hypothesis), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
