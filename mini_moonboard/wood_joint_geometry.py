"""Finished-solid and installed-hardware geometry for wood-joint development.

This module contains geometric screens only.  A successful result is not a
wood, bolt, washer, contact, or complete-joint strength result.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import Literal

import cadquery as cq

from .connection_geometry import material_intervals

VectorLike = cq.Vector | tuple[float, float, float]
EvidenceStatus = Literal[
    "unverified",
    "failed",
    "passed_under_recorded_assumptions",
    "not_applicable_with_reason",
]
_EVIDENCE_STATUSES = frozenset(
    {
        "unverified",
        "failed",
        "passed_under_recorded_assumptions",
        "not_applicable_with_reason",
    }
)

_GEOMETRY_TOLERANCE_MM = 1e-6
_INTERSECTION_VOLUME_TOLERANCE_MM3 = 1e-6


def _vector(value: VectorLike, name: str) -> cq.Vector:
    try:
        result = cq.Vector(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a three-component vector") from error
    if not all(math.isfinite(component) for component in result.toTuple()):
        raise ValueError(f"{name} must be finite")
    return result


def _unit(value: VectorLike, name: str) -> cq.Vector:
    result = _vector(value, name)
    if result.Length <= _GEOMETRY_TOLERANCE_MM:
        raise ValueError(f"{name} must be nonzero")
    return result.normalized()


def _shape(value: cq.Shape | cq.Workplane, name: str = "shape") -> cq.Shape:
    result = value.val() if isinstance(value, cq.Workplane) else value
    if not isinstance(result, cq.Shape) or not result.isValid() or not result.Solids():
        raise ValueError(f"{name} must contain valid solid geometry")
    return result


def _positive(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return result


def _point_tuple(value: VectorLike) -> tuple[float, float, float]:
    return tuple(round(component, 9) for component in _vector(value, "point").toTuple())


@dataclass(frozen=True)
class LocalFrame:
    """Named right-handed orthonormal part or interface frame."""

    origin: VectorLike
    x: VectorLike
    t: VectorLike
    n: VectorLike

    def __post_init__(self) -> None:
        origin = _vector(self.origin, "origin")
        x, t, n = (
            _unit(value, name)
            for value, name in ((self.x, "x"), (self.t, "t"), (self.n, "n"))
        )
        if any(abs(a.dot(b)) > 1e-8 for a, b in ((x, t), (x, n), (t, n))):
            raise ValueError("Local-frame axes must be orthogonal")
        if x.cross(t).dot(n) < 1.0 - 1e-8:
            raise ValueError("Local-frame axes must be right-handed")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "t", t)
        object.__setattr__(self, "n", n)

    def coordinates(self, point: VectorLike) -> tuple[float, float, float]:
        delta = _vector(point, "point") - self.origin
        return delta.dot(self.x), delta.dot(self.t), delta.dot(self.n)


@dataclass(frozen=True)
class CutRecord:
    id: str
    parent_part_id: str
    kind: Literal["bore", "recess", "relief", "trim", "other"]
    removed_shape: cq.Shape | cq.Workplane
    fabrication_method: str

    def __post_init__(self) -> None:
        if not self.id or not self.parent_part_id or not self.fabrication_method:
            raise ValueError("Cut IDs, parent and fabrication method are required")
        object.__setattr__(
            self, "removed_shape", _shape(self.removed_shape, "removed_shape")
        )

    @property
    def removed_volume_mm3(self) -> float:
        return self.removed_shape.Volume()


@dataclass(frozen=True)
class FinishedPart:
    """Physical part retaining both purchased stock and net finished solid."""

    id: str
    stock_product: str
    actual_dimensions_mm: tuple[float, float, float]
    material: str
    grain_axis: VectorLike
    frame: LocalFrame
    transport_owner: str
    uncut_shape: cq.Shape | cq.Workplane
    finished_shape: cq.Shape | cq.Workplane
    modifications: tuple[CutRecord, ...]
    source_sha256: str
    fabrication_method: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.id,
                self.stock_product,
                self.material,
                self.transport_owner,
                self.source_sha256,
                self.fabrication_method,
            )
        ):
            raise ValueError(
                "Finished-part identity and provenance fields are required"
            )
        if len(self.source_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.source_sha256
        ):
            raise ValueError("source_sha256 must be a lowercase SHA-256 digest")
        dimensions = tuple(
            _positive(value, "actual dimension") for value in self.actual_dimensions_mm
        )
        if len(dimensions) != 3:
            raise ValueError("actual_dimensions_mm must contain three dimensions")
        uncut, finished = (
            _shape(self.uncut_shape, "uncut_shape"),
            _shape(self.finished_shape, "finished_shape"),
        )
        grain = _unit(self.grain_axis, "grain_axis")
        if any(cut.parent_part_id != self.id for cut in self.modifications):
            raise ValueError("Every modification must name its parent part")
        if len({cut.id for cut in self.modifications}) != len(self.modifications):
            raise ValueError("Modification IDs must be unique within a part")
        volume_tolerance = max(1e-5, uncut.Volume() * 1e-9)
        if finished.cut(uncut).Volume() > volume_tolerance:
            raise ValueError("Finished shape must remain within uncut stock")
        expected = uncut
        for cut in self.modifications:
            next_expected = expected.cut(cut.removed_shape)
            if expected.Volume() - next_expected.Volume() <= volume_tolerance:
                raise ValueError(f"Modification {cut.id!r} removes no parent material")
            expected = next_expected
        mismatch = finished.cut(expected).Volume() + expected.cut(finished).Volume()
        if mismatch > volume_tolerance:
            raise ValueError(
                "Finished shape must equal uncut stock minus recorded modifications"
            )
        object.__setattr__(self, "actual_dimensions_mm", dimensions)
        object.__setattr__(self, "grain_axis", grain)
        object.__setattr__(self, "uncut_shape", uncut)
        object.__setattr__(self, "finished_shape", finished)

    @property
    def finished_fingerprint(self) -> str:
        payload = {
            "id": self.id,
            "source_sha256": self.source_sha256,
            "frame": _frame_signature(self.frame),
            "grain_axis": _point_tuple(self.grain_axis),
            "uncut": _shape_signature(self.uncut_shape),
            "finished": _shape_signature(self.finished_shape),
            "cuts": [
                {
                    "id": cut.id,
                    "parent": cut.parent_part_id,
                    "kind": cut.kind,
                    "method": cut.fabrication_method,
                    "shape": _shape_signature(cut.removed_shape),
                }
                for cut in sorted(self.modifications, key=lambda item: item.id)
            ],
        }
        return _canonical_sha256(payload)


@dataclass(frozen=True)
class InterfaceRecord:
    id: str
    body_ids: tuple[str, str]
    legacy_duties: tuple[str, ...]
    contact_face_ids: tuple[str, ...]
    frame: LocalFrame
    behavior: Literal["compression_only", "bonded", "fastened", "clearance"]
    bolt_group_ids: tuple[str, ...]
    bolt_penetration_order: tuple[str, ...]
    force_reference_point: VectorLike
    separates_for_move: bool
    access_sequence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id or len(set(self.body_ids)) != 2:
            raise ValueError("Interface must join two distinct physical bodies")
        if not all(self.body_ids) or not self.contact_face_ids:
            raise ValueError("Interface bodies and contact faces are required")
        if len(set(self.bolt_penetration_order)) != len(self.bolt_penetration_order):
            raise ValueError("Bolt penetration order cannot repeat a body")
        object.__setattr__(
            self,
            "force_reference_point",
            _vector(self.force_reference_point, "force_reference_point"),
        )


@dataclass(frozen=True)
class StackLayer:
    body_id: str
    thickness_mm: float

    def __post_init__(self) -> None:
        if not self.body_id:
            raise ValueError("Stack layer body ID is required")
        object.__setattr__(
            self, "thickness_mm", _positive(self.thickness_mm, "layer thickness")
        )


@dataclass(frozen=True)
class BoltHardware:
    candidate_sku: str
    under_head_length_mm: float
    steel_diameter_mm: float
    cad_occupied_diameter_mm: float
    drill_diameter_mm: float
    head_diameter_mm: float
    head_height_mm: float
    washer_od_mm: float
    washer_id_mm: float
    washer_thickness_mm: float
    nut_diameter_mm: float
    nut_height_mm: float
    usable_thread_start_mm: float
    usable_thread_end_mm: float

    def __post_init__(self) -> None:
        if not self.candidate_sku:
            raise ValueError("Bolt candidate specification is required")
        names = (
            "under_head_length_mm",
            "steel_diameter_mm",
            "cad_occupied_diameter_mm",
            "drill_diameter_mm",
            "head_diameter_mm",
            "head_height_mm",
            "washer_od_mm",
            "washer_id_mm",
            "washer_thickness_mm",
            "nut_diameter_mm",
            "nut_height_mm",
        )
        for name in names:
            object.__setattr__(self, name, _positive(getattr(self, name), name))
        start, end = (
            float(self.usable_thread_start_mm),
            float(self.usable_thread_end_mm),
        )
        if not (0 <= start < end <= self.under_head_length_mm):
            raise ValueError("Usable thread interval must lie along nominal shaft")
        if self.washer_id_mm < self.steel_diameter_mm:
            raise ValueError("Washer ID cannot be smaller than steel diameter")
        if self.drill_diameter_mm < self.steel_diameter_mm:
            raise ValueError("Drill diameter cannot be smaller than steel diameter")
        if self.cad_occupied_diameter_mm < self.steel_diameter_mm:
            raise ValueError(
                "CAD occupied diameter cannot be smaller than steel diameter"
            )
        object.__setattr__(self, "usable_thread_start_mm", start)
        object.__setattr__(self, "usable_thread_end_mm", end)


@dataclass(frozen=True)
class WasherSeat:
    body_id: str
    center: VectorLike
    inward_normal: VectorLike

    def __post_init__(self) -> None:
        if not self.body_id:
            raise ValueError("Washer support body is required")
        object.__setattr__(self, "center", _vector(self.center, "washer center"))
        object.__setattr__(
            self, "inward_normal", _unit(self.inward_normal, "washer inward normal")
        )


@dataclass(frozen=True)
class BoltStack:
    id: str
    hardware: BoltHardware
    under_head_origin: VectorLike
    direction: VectorLike
    layers: tuple[StackLayer, ...]
    head_seat: WasherSeat
    nut_seat: WasherSeat
    required_tip_projection_mm: float = 0.0

    def __post_init__(self) -> None:
        if not self.id or not self.layers:
            raise ValueError("Bolt stack ID and layers are required")
        if (
            self.layers[0].body_id != self.head_seat.body_id
            or self.layers[-1].body_id != self.nut_seat.body_id
        ):
            raise ValueError(
                "Washer support bodies must be first and last stack layers"
            )
        object.__setattr__(
            self,
            "under_head_origin",
            _vector(self.under_head_origin, "under_head_origin"),
        )
        object.__setattr__(self, "direction", _unit(self.direction, "bolt direction"))
        direction = self.direction
        if self.head_seat.inward_normal.dot(direction) < 1.0 - 1e-8:
            raise ValueError("Head washer inward normal must follow bolt direction")
        if self.nut_seat.inward_normal.dot(-direction) < 1.0 - 1e-8:
            raise ValueError("Nut washer inward normal must oppose bolt direction")
        expected_head_seat = (
            self.under_head_origin + direction * self.hardware.washer_thickness_mm
        )
        expected_nut_seat = expected_head_seat + direction * self.grip_mm
        if (self.head_seat.center - expected_head_seat).Length > _GEOMETRY_TOLERANCE_MM:
            raise ValueError("Head washer seat does not align with under-head datum")
        if (self.nut_seat.center - expected_nut_seat).Length > _GEOMETRY_TOLERANCE_MM:
            raise ValueError("Nut washer seat does not match declared stack grip")
        projection = float(self.required_tip_projection_mm)
        if not math.isfinite(projection) or projection < 0:
            raise ValueError("Required tip projection must be finite and nonnegative")
        object.__setattr__(self, "required_tip_projection_mm", projection)

    @property
    def grip_mm(self) -> float:
        return sum(layer.thickness_mm for layer in self.layers)

    def shaft_shape(self) -> cq.Shape:
        return cq.Solid.makeCylinder(
            self.hardware.cad_occupied_diameter_mm / 2,
            self.hardware.under_head_length_mm,
            self.under_head_origin,
            self.direction,
        )

    def installed_shapes(self) -> Mapping[str, cq.Shape]:
        """Return nominal installed collision envelopes for every stack component."""
        spec, origin, direction = self.hardware, self.under_head_origin, self.direction

        def ring(start: cq.Vector) -> cq.Shape:
            return cq.Solid.makeCylinder(
                spec.washer_od_mm / 2, spec.washer_thickness_mm, start, direction
            ).cut(
                cq.Solid.makeCylinder(
                    spec.washer_id_mm / 2,
                    spec.washer_thickness_mm,
                    start,
                    direction,
                )
            )

        head_washer_start = self.head_seat.center - direction * spec.washer_thickness_mm
        nut_washer_start = self.nut_seat.center
        nut_start = nut_washer_start + direction * spec.washer_thickness_mm
        return {
            "shaft": self.shaft_shape(),
            "head": cq.Solid.makeCylinder(
                spec.head_diameter_mm / 2,
                spec.head_height_mm,
                origin,
                -direction,
            ),
            "head_washer": ring(head_washer_start),
            "nut_washer": ring(nut_washer_start),
            "nut": cq.Solid.makeCylinder(
                spec.nut_diameter_mm / 2,
                spec.nut_height_mm,
                nut_start,
                direction,
            ),
        }


@dataclass(frozen=True)
class EvidenceRecord:
    candidate_fingerprint: str
    geometry_fingerprint: str
    source_fingerprints: tuple[tuple[str, str], ...]
    producer: str
    command: str
    artifact_sha256: str
    applicability: str
    status: EvidenceStatus
    governing_case: str | None
    result: str
    limits: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in _EVIDENCE_STATUSES:
            raise ValueError(f"Unknown evidence status {self.status!r}")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.producer, self.command, self.applicability, self.result)
        ):
            raise ValueError(
                "Evidence producer, command, applicability and result are required"
            )
        if not self.source_fingerprints or any(
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(digest, str)
            or not digest
            for name, digest in self.source_fingerprints
        ):
            raise ValueError("Evidence requires nonempty named source fingerprints")
        if len({name for name, _ in self.source_fingerprints}) != len(
            self.source_fingerprints
        ):
            raise ValueError("Evidence source fingerprint names must be unique")
        if self.status == "passed_under_recorded_assumptions" and not self.limits:
            raise ValueError("Conditional pass requires recorded limits")
        digests = (
            self.candidate_fingerprint,
            self.geometry_fingerprint,
            self.artifact_sha256,
            *(digest for _, digest in self.source_fingerprints),
        )
        if any(
            not isinstance(value, str)
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
            for value in digests
        ):
            raise ValueError("Evidence fingerprints must be lowercase SHA-256 digests")


@dataclass(frozen=True)
class LocalExtrema:
    x_mm: tuple[float, float]
    t_mm: tuple[float, float]
    n_mm: tuple[float, float]


def local_extrema(shape: cq.Shape | cq.Workplane, frame: LocalFrame) -> LocalExtrema:
    """Return exact-kernel bounds after rotating finished geometry into a local frame."""
    body = _shape(shape)
    origin = frame.origin
    matrix = cq.Matrix(
        [
            [*frame.x.toTuple(), -origin.dot(frame.x)],
            [*frame.t.toTuple(), -origin.dot(frame.t)],
            [*frame.n.toTuple(), -origin.dot(frame.n)],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    box = body.transformGeometry(matrix).BoundingBox()
    return LocalExtrema(
        (box.xmin, box.xmax), (box.ymin, box.ymax), (box.zmin, box.zmax)
    )


@dataclass(frozen=True)
class FaceLigamentReport:
    face_width_mm: float
    bore_centers_mm: tuple[float, ...]
    bore_diameter_mm: float
    center_edge_distances_mm: tuple[tuple[float, float], ...]
    clear_ligaments_mm: tuple[tuple[float, float], ...]
    symmetric_target_mm: float
    target_passes: bool


def face_ligament_report(
    face_width_mm: float,
    bore_centers_mm: Iterable[float],
    bore_diameter_mm: float,
    symmetric_target_mm: float,
) -> FaceLigamentReport:
    """Report distances to both edges of a one-dimensional presented face."""
    width = _positive(face_width_mm, "face width")
    diameter = _positive(bore_diameter_mm, "bore diameter")
    target = _positive(symmetric_target_mm, "symmetric target")
    centers = tuple(float(value) for value in bore_centers_mm)
    if not centers or any(
        not math.isfinite(value) or value < 0 or value > width for value in centers
    ):
        raise ValueError("Bore centers must lie on the presented face")
    edge = tuple((center, width - center) for center in centers)
    clear = tuple((near - diameter / 2, far - diameter / 2) for near, far in edge)
    return FaceLigamentReport(
        width,
        centers,
        diameter,
        edge,
        clear,
        target,
        all(min(pair) >= target for pair in edge),
    )


@dataclass(frozen=True)
class Bore:
    id: str
    host_part_id: str
    start: VectorLike
    direction: VectorLike
    length_mm: float
    drill_diameter_mm: float

    def __post_init__(self) -> None:
        if not self.id or not self.host_part_id:
            raise ValueError("Bore ID and host are required")
        object.__setattr__(self, "start", _vector(self.start, "bore start"))
        object.__setattr__(self, "direction", _unit(self.direction, "bore direction"))
        object.__setattr__(self, "length_mm", _positive(self.length_mm, "bore length"))
        object.__setattr__(
            self,
            "drill_diameter_mm",
            _positive(self.drill_diameter_mm, "drill diameter"),
        )

    def cutter(self) -> cq.Shape:
        return cq.Solid.makeCylinder(
            self.drill_diameter_mm / 2, self.length_mm, self.start, self.direction
        )


@dataclass(frozen=True)
class BoreHostReport:
    bore_id: str
    declared_host_id: str
    centerline_intervals_mm: tuple[tuple[float, float], ...]
    cutter_containment_fraction: float
    passes: bool


def validate_bore_host(bore: Bore, parts: Mapping[str, FinishedPart]) -> BoreHostReport:
    """Require full declared-host material along bore length and cutter radius."""
    if bore.host_part_id not in parts:
        raise ValueError(f"Unknown bore host {bore.host_part_id!r}")
    host = parts[bore.host_part_id].finished_shape
    intervals = tuple(
        material_intervals(
            host,
            bore.start,
            bore.direction,
            -_GEOMETRY_TOLERANCE_MM,
            bore.length_mm + _GEOMETRY_TOLERANCE_MM,
        )
    )
    cutter = bore.cutter()
    fraction = cutter.intersect(host).Volume() / cutter.Volume()
    centerline_pass = any(
        start <= _GEOMETRY_TOLERANCE_MM
        and end >= bore.length_mm - _GEOMETRY_TOLERANCE_MM
        for start, end in intervals
    )
    return BoreHostReport(
        bore.id,
        bore.host_part_id,
        intervals,
        fraction,
        centerline_pass and fraction >= 1.0 - 1e-7,
    )


@dataclass(frozen=True)
class BoltStackReport:
    bolt_id: str
    grip_mm: float
    required_under_head_length_mm: float
    available_under_head_length_mm: float
    length_margin_mm: float
    nut_on_usable_thread: bool
    passes: bool


def bolt_stack_report(stack: BoltStack) -> BoltStackReport:
    hardware = stack.hardware
    required = (
        2 * hardware.washer_thickness_mm
        + stack.grip_mm
        + hardware.nut_height_mm
        + stack.required_tip_projection_mm
    )
    nut_start = (
        hardware.washer_thickness_mm + stack.grip_mm + hardware.washer_thickness_mm
    )
    nut_end = nut_start + hardware.nut_height_mm
    threaded = (
        nut_start >= hardware.usable_thread_start_mm - _GEOMETRY_TOLERANCE_MM
        and nut_end <= hardware.usable_thread_end_mm + _GEOMETRY_TOLERANCE_MM
    )
    margin = hardware.under_head_length_mm - required
    return BoltStackReport(
        stack.id,
        stack.grip_mm,
        required,
        hardware.under_head_length_mm,
        margin,
        threaded,
        margin >= -_GEOMETRY_TOLERANCE_MM and threaded,
    )


@dataclass(frozen=True)
class WasherSupportReport:
    body_id: str
    support_fraction: float
    unsupported_area_mm2: float
    full_seat: bool


def washer_support_report(
    seat: WasherSeat,
    body: cq.Shape | cq.Workplane,
    hardware: BoltHardware,
    *,
    probe_depth_mm: float = 0.05,
) -> WasherSupportReport:
    """Probe annular support immediately below a modeled washer seat."""
    depth = _positive(probe_depth_mm, "probe depth")
    outer = cq.Solid.makeCylinder(
        hardware.washer_od_mm / 2, depth, seat.center, seat.inward_normal
    )
    inner = cq.Solid.makeCylinder(
        hardware.washer_id_mm / 2, depth, seat.center, seat.inward_normal
    )
    annulus = outer.cut(inner)
    supported = annulus.intersect(_shape(body)).Volume()
    fraction = supported / annulus.Volume()
    area = math.pi / 4 * (hardware.washer_od_mm**2 - hardware.washer_id_mm**2)
    return WasherSupportReport(
        seat.body_id,
        fraction,
        max(0.0, area * (1.0 - fraction)),
        fraction >= 1.0 - 1e-7,
    )


@dataclass(frozen=True)
class BoltPairSpacing:
    center_distance_mm: float
    steel_diameter_mm: float
    diameter_multiple: float


def bolt_pair_spacing(
    first: VectorLike, second: VectorLike, steel_diameter_mm: float
) -> BoltPairSpacing:
    diameter = _positive(steel_diameter_mm, "steel diameter")
    distance = (_vector(second, "second bolt") - _vector(first, "first bolt")).Length
    return BoltPairSpacing(distance, diameter, distance / diameter)


@dataclass(frozen=True)
class LinearBoltRowReport:
    member_length_mm: float
    centers_mm: tuple[float, ...]
    steel_diameter_mm: float
    required_end_distance_mm: float
    end_distances_mm: tuple[float, float]
    adjacent_spacings_mm: tuple[float, ...]
    end_distance_passes: bool


def linear_bolt_row_report(
    member_length_mm: float,
    centers_mm: Sequence[float],
    steel_diameter_mm: float,
    *,
    end_distance_multiple: float,
) -> LinearBoltRowReport:
    length = _positive(member_length_mm, "member length")
    diameter = _positive(steel_diameter_mm, "steel diameter")
    multiple = _positive(end_distance_multiple, "end-distance multiple")
    centers = tuple(sorted(float(center) for center in centers_mm))
    if not centers or any(
        not math.isfinite(center) or not 0 <= center <= length for center in centers
    ):
        raise ValueError("Bolt-row centers must lie within member length")
    ends = centers[0], length - centers[-1]
    spacings = tuple(b - a for a, b in pairwise(centers))
    required = multiple * diameter
    return LinearBoltRowReport(
        length, centers, diameter, required, ends, spacings, min(ends) >= required
    )


class ContactClass(StrEnum):
    UNRELATED = "unrelated"
    BOLT_IN_OWN_BORE = "bolt_in_own_bore"
    WASHER_ON_DECLARED_HOST = "washer_on_declared_host"
    INTENDED_WOOD_CONTACT = "intended_wood_contact"


@dataclass(frozen=True)
class ContactDeclaration:
    first_id: str
    second_id: str
    classification: ContactClass

    def key(self) -> frozenset[str]:
        if not self.first_id or not self.second_id or self.first_id == self.second_id:
            raise ValueError("Contact declaration needs two distinct body IDs")
        return frozenset((self.first_id, self.second_id))


def classify_contact(
    first_id: str,
    second_id: str,
    declarations: Iterable[ContactDeclaration],
) -> ContactClass:
    key = frozenset((first_id, second_id))
    matches = [item.classification for item in declarations if item.key() == key]
    if len(matches) > 1 and len(set(matches)) > 1:
        raise ValueError(f"Conflicting contact declarations for {sorted(key)}")
    return matches[0] if matches else ContactClass.UNRELATED


@dataclass(frozen=True)
class GeometryBody:
    id: str
    category: str
    shape: cq.Shape | cq.Workplane

    def __post_init__(self) -> None:
        if not self.id or not self.category:
            raise ValueError("Geometry body identity and category are required")
        object.__setattr__(self, "shape", _shape(self.shape))


@dataclass(frozen=True)
class Collision:
    first_id: str
    second_id: str
    classification: ContactClass
    intersection_volume_mm3: float
    clearance_mm: float
    failure: bool


def screen_clearance(
    bodies: Sequence[GeometryBody],
    declarations: Iterable[ContactDeclaration] = (),
) -> tuple[Collision, ...]:
    """Classify exact intersections and nearest separations for every body pair."""
    if len({body.id for body in bodies}) != len(bodies):
        raise ValueError("Geometry body IDs must be unique")
    declared = tuple(declarations)
    result: list[Collision] = []
    for index, first in enumerate(bodies):
        for second in bodies[index + 1 :]:
            classification = classify_contact(first.id, second.id, declared)
            if not _bounds_overlap(
                first.shape.BoundingBox(), second.shape.BoundingBox()
            ):
                intersection = 0.0
                clearance = first.shape.distance(second.shape)
            else:
                intersection = first.shape.intersect(second.shape).Volume()
                clearance = (
                    0.0
                    if intersection > _GEOMETRY_TOLERANCE_MM
                    else first.shape.distance(second.shape)
                )
            result.append(
                Collision(
                    first.id,
                    second.id,
                    classification,
                    intersection,
                    clearance,
                    intersection > _INTERSECTION_VOLUME_TOLERANCE_MM3
                    and classification
                    in (
                        ContactClass.UNRELATED,
                        ContactClass.WASHER_ON_DECLARED_HOST,
                        ContactClass.INTENDED_WOOD_CONTACT,
                    ),
                )
            )
    return tuple(result)


@dataclass(frozen=True)
class AccessSweep:
    id: str
    start: VectorLike
    direction: VectorLike
    tool_diameter_mm: float
    tool_length_mm: float
    insertion_stroke_mm: float

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Access sweep ID is required")
        object.__setattr__(self, "start", _vector(self.start, "access start"))
        object.__setattr__(self, "direction", _unit(self.direction, "access direction"))
        for name in ("tool_diameter_mm", "tool_length_mm", "insertion_stroke_mm"):
            object.__setattr__(self, name, _positive(getattr(self, name), name))

    def swept_shape(self) -> cq.Shape:
        return cq.Solid.makeCylinder(
            self.tool_diameter_mm / 2,
            self.tool_length_mm + self.insertion_stroke_mm,
            self.start,
            self.direction,
        )


@dataclass(frozen=True)
class AccessSweepReport:
    access_id: str
    collisions: tuple[Collision, ...]
    minimum_clearance_mm: float
    passes: bool


def access_sweep_report(
    sweep: AccessSweep,
    obstacles: Sequence[GeometryBody],
    *,
    allowed_contact_ids: Iterable[str] = (),
) -> AccessSweepReport:
    tool = GeometryBody(sweep.id, "tool_sweep", sweep.swept_shape())
    declarations = tuple(
        ContactDeclaration(sweep.id, body_id, ContactClass.INTENDED_WOOD_CONTACT)
        for body_id in allowed_contact_ids
    )
    collisions = tuple(
        row
        for row in screen_clearance((tool, *obstacles), declarations)
        if sweep.id in (row.first_id, row.second_id)
    )
    minimum = min((row.clearance_mm for row in collisions), default=math.inf)
    return AccessSweepReport(
        sweep.id, collisions, minimum, not any(row.failure for row in collisions)
    )


@dataclass(frozen=True)
class JointFixture:
    """Small mixed-body regression fixture, not a candidate joint design."""

    bodies: tuple[GeometryBody, ...]
    access: AccessSweep


def representative_worst_corner_fixture() -> JointFixture:
    """Return deterministic mixed-body fixture with one retained-bolt tool clash."""
    host = (
        cq.Workplane("XY").box(220.0, 139.7, 38.1, centered=(False, False, False)).val()
    )
    neighbor = (
        cq.Workplane("XY")
        .box(38.1, 139.7, 180.0, centered=(False, False, False))
        .translate((180, 0, 38.1))
        .val()
    )
    screw = cq.Solid.makeCylinder(
        2.5, 55.0, cq.Vector(60, 30, 38.1), cq.Vector(0, 0, 1)
    )
    tnut = cq.Solid.makeCylinder(
        12.7, 3.0, cq.Vector(100, 50, 38.1), cq.Vector(0, 0, 1)
    )
    light = cq.Solid.makeCylinder(
        6.5, 31.0, cq.Vector(130, 80, 38.1), cq.Vector(0, 0, 1)
    )
    wire = cq.Solid.makeCylinder(4.0, 100.0, cq.Vector(20, 120, 50), cq.Vector(1, 0, 0))
    retained_bolt = cq.Solid.makeCylinder(
        4.7625, 139.7, cq.Vector(190, 0, 100), cq.Vector(0, 1, 0)
    )
    bodies = tuple(
        GeometryBody(name, category, shape)
        for name, category, shape in (
            ("host", "finished_wood", host),
            ("neighbor", "neighboring_wood", neighbor),
            ("panel_screw", "retained_screw", screw),
            ("hold_tnut", "hold_tnut", tnut),
            ("light", "light", light),
            ("wire", "wire", wire),
            ("retained_bolt", "retained_bolt", retained_bolt),
        )
    )
    access = AccessSweep(
        "known_collision_tool", (190, 69.85, 200), (0, 0, -1), 30, 60, 80
    )
    return JointFixture(bodies, access)


def _frame_signature(frame: LocalFrame) -> dict[str, tuple[float, float, float]]:
    return {
        "origin": _point_tuple(frame.origin),
        "x": _point_tuple(frame.x),
        "t": _point_tuple(frame.t),
        "n": _point_tuple(frame.n),
    }


def _shape_signature(shape: cq.Shape) -> dict[str, object]:
    """Stable geometric summary used with explicit machining records."""
    box = shape.BoundingBox()
    center = shape.Center()
    faces = sorted(
        (round(face.Area(), 7), _point_tuple(face.Center())) for face in shape.Faces()
    )
    vertices = sorted(_point_tuple(vertex.Center()) for vertex in shape.Vertices())
    return {
        "volume_mm3": round(shape.Volume(), 7),
        "area_mm2": round(shape.Area(), 7),
        "center_mm": _point_tuple(center),
        "bounds_mm": tuple(
            round(value, 7)
            for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
        ),
        "faces": faces,
        "vertices": vertices,
    }


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _bounds_overlap(first: cq.BoundBox, second: cq.BoundBox) -> bool:
    return (
        first.xmin <= second.xmax
        and first.xmax >= second.xmin
        and first.ymin <= second.ymax
        and first.ymax >= second.ymin
        and first.zmin <= second.zmax
        and first.zmax >= second.zmin
    )
