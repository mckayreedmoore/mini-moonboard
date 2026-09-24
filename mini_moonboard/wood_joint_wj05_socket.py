"""WJ-05 seated Ko-ken socket outside-envelope geometry.

This is one catalog-tool collision proxy, not a fit or access qualification.
The modeled outer cylinder uses the product's largest listed diameter over its
full length. Its open end is seated at the engaged hex fastener's far face;
the intended nut/head overlap is part of that datum, not an obstacle clash.
The socket's internal 12-point profile, clearances, ratchet, and extension are
not modeled.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import cadquery as cq

KOKEN_3305A_7_16_PRODUCT = "Ko-ken 3305A-7/16"
KOKEN_PRODUCT_URL = (
    "https://kokenusa.com/products/deep-socket-3-8sq-dr-12-p-7-16"
)
KOKEN_SOCKET_OUTSIDE_DIAMETER_MM = 17.2  # D2, maximum listed outside diameter.
KOKEN_SOCKET_WORKING_END_DIAMETER_MM = 16.0  # D1.
KOKEN_SOCKET_LENGTH_MM = 55.0  # L.
KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM = 41.5  # H2.
KOKEN_SOCKET_H1_MM = 12.0


@dataclass(frozen=True)
class SeatedSocketEnvelope:
    """Catalog socket's conservative outside envelope and explicit seat datum.

    `engagement_face_z_mm` is far face of hex fastener at full seating:
    nut bearing face for top access, bolt underhead bearing face for bottom.
    `outward_z` points from that face toward the socket drive end.
    """

    external_envelope: cq.Solid
    approach_endpoint_envelope: cq.Solid
    approach_sweep_envelope: cq.Solid
    center_xy_mm: tuple[float, float]
    engagement_face_z_mm: float
    approach_face_z_mm: float
    target_bounds_z_mm: tuple[float, float]
    outward_z: Literal[-1, 1]
    length_mm: float = KOKEN_SOCKET_LENGTH_MM
    outside_diameter_mm: float = KOKEN_SOCKET_OUTSIDE_DIAMETER_MM
    stud_clearance_depth_mm: float = KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM

    @property
    def axial_bounds_mm(self) -> tuple[float, float]:
        box = self.external_envelope.BoundingBox()
        return box.zmin, box.zmax

    @property
    def approach_endpoint_bounds_mm(self) -> tuple[float, float]:
        box = self.approach_endpoint_envelope.BoundingBox()
        return box.zmin, box.zmax

    @property
    def approach_sweep_bounds_mm(self) -> tuple[float, float]:
        box = self.approach_sweep_envelope.BoundingBox()
        return box.zmin, box.zmax


def seated_koken_3305a_7_16_envelope(
    center_xy_mm: tuple[float, float],
    engagement_face_z_mm: float,
    outward_z: Literal[-1, 1],
    target_bounds_z_mm: tuple[float, float],
) -> SeatedSocketEnvelope:
    """Build one Ko-ken 3305A-7/16 outside-envelope proxy at seated datum.

    `target_bounds_z_mm` names engaged nut/head extent. The returned seated
    cylinder starts at the engaged hex's far face. The approach endpoint starts
    at its outward face, matching the prior WJ-05 approach-only placement. The
    sweep cylinder covers every coaxial position between these endpoints. All
    use D2 over the full axial extent as conservative external occupancy; D1
    and H1 do not define an unprovided stepped OD or internal profile here.
    """

    if len(center_xy_mm) != 2 or not all(
        math.isfinite(float(value)) for value in center_xy_mm
    ):
        raise ValueError("center_xy_mm must contain two finite coordinates")
    if not math.isfinite(float(engagement_face_z_mm)):
        raise ValueError("engagement_face_z_mm must be finite")
    if outward_z not in (-1, 1):
        raise ValueError("outward_z must be -1 or 1")
    if len(target_bounds_z_mm) != 2 or not all(
        math.isfinite(float(value)) for value in target_bounds_z_mm
    ):
        raise ValueError("target_bounds_z_mm must contain two finite bounds")
    target_z_min, target_z_max = sorted(float(value) for value in target_bounds_z_mm)
    if target_z_max <= target_z_min:
        raise ValueError("target_bounds_z_mm must have positive span")
    x_mm, y_mm = (float(value) for value in center_xy_mm)
    z_mm = float(engagement_face_z_mm)
    expected_engagement_face = target_z_min if outward_z == 1 else target_z_max
    if not math.isclose(z_mm, expected_engagement_face, abs_tol=1e-9):
        raise ValueError(
            "engagement_face_z_mm must be target's far face for outward_z"
        )
    approach_face_z_mm = target_z_max if outward_z == 1 else target_z_min
    direction = cq.Vector(0, 0, outward_z)

    def cylinder(start_z_mm: float, length_mm: float) -> cq.Solid:
        return cq.Solid.makeCylinder(
            KOKEN_SOCKET_OUTSIDE_DIAMETER_MM / 2,
            length_mm,
            cq.Vector(x_mm, y_mm, start_z_mm),
            direction,
        )

    external_envelope = cylinder(z_mm, KOKEN_SOCKET_LENGTH_MM)
    approach_endpoint_envelope = cylinder(
        approach_face_z_mm,
        KOKEN_SOCKET_LENGTH_MM,
    )
    approach_sweep_envelope = cylinder(
        z_mm,
        KOKEN_SOCKET_LENGTH_MM + target_z_max - target_z_min,
    )
    return SeatedSocketEnvelope(
        external_envelope=external_envelope,
        approach_endpoint_envelope=approach_endpoint_envelope,
        approach_sweep_envelope=approach_sweep_envelope,
        center_xy_mm=(x_mm, y_mm),
        engagement_face_z_mm=z_mm,
        approach_face_z_mm=approach_face_z_mm,
        target_bounds_z_mm=(target_z_min, target_z_max),
        outward_z=outward_z,
    )


def wj05_socket_occupancy_intent(
    socket: SeatedSocketEnvelope,
    *,
    target_component: str,
    target_bounds_z_mm: tuple[float, float],
    target_max_corner_diameter_mm: float,
) -> dict:
    """Describe expected socket/fastener envelope overlap, not tool fit.

    The WJ-05 collision proxy models only the socket's outside occupancy. Its
    overlap with the intended head or nut is recorded separately from obstacle
    clashes. No 12-point opening or engagement clearance is inferred.
    """

    if not target_component:
        raise ValueError("target_component must be named")
    if len(target_bounds_z_mm) != 2 or not all(
        math.isfinite(float(value)) for value in target_bounds_z_mm
    ):
        raise ValueError("target_bounds_z_mm must contain two finite bounds")
    target_z_min, target_z_max = sorted(float(value) for value in target_bounds_z_mm)
    if target_z_max <= target_z_min:
        raise ValueError("target_bounds_z_mm must have positive span")
    if any(
        not math.isclose(actual, expected, abs_tol=1e-9)
        for actual, expected in zip(
            (target_z_min, target_z_max), socket.target_bounds_z_mm
        )
    ):
        raise ValueError("target bounds must match the socket's built station")
    target_diameter_mm = float(target_max_corner_diameter_mm)
    if not math.isfinite(target_diameter_mm) or target_diameter_mm <= 0:
        raise ValueError("target_max_corner_diameter_mm must be positive and finite")

    socket_z_min, socket_z_max = socket.axial_bounds_mm
    overlap_mm = max(
        0.0,
        min(socket_z_max, target_z_max) - max(socket_z_min, target_z_min),
    )
    target_height_mm = target_z_max - target_z_min
    return {
        "classification": "intentional_socket_fastener_occupancy_not_obstacle_clash",
        "target_component": target_component,
        "target_bounds_z_mm": [target_z_min, target_z_max],
        "socket_engagement_face_z_mm": socket.engagement_face_z_mm,
        "socket_approach_face_z_mm": socket.approach_face_z_mm,
        "socket_outward_z": socket.outward_z,
        "socket_external_envelope_bounds_z_mm": [socket_z_min, socket_z_max],
        "approach_endpoint_envelope_bounds_z_mm": list(
            socket.approach_endpoint_bounds_mm
        ),
        "approach_sweep_envelope_bounds_z_mm": list(
            socket.approach_sweep_bounds_mm
        ),
        "target_axial_height_mm": target_height_mm,
        "external_envelope_axial_overlap_mm": overlap_mm,
        "socket_outer_envelope_spans_full_target_hex_height": (
            overlap_mm >= target_height_mm - 1e-9
        ),
        "socket_external_diameter_mm": socket.outside_diameter_mm,
        "target_max_corner_diameter_mm": target_diameter_mm,
        "external_diameter_margin_over_target_max_corner_diameter_mm": (
            socket.outside_diameter_mm - target_diameter_mm
        ),
        "internal_12_point_profile_and_engagement_fit": "not_modeled_or_assessed",
        "scope": "outside-envelope occupancy bookkeeping only; no tool-fit, tolerance, torque, reach, or swing claim",
    }
