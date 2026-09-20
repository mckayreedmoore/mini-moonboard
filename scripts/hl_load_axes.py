"""Catalog-figure HL axis registration for nominal installed poses only.

The C-C-2026 p. 315 HL55 installation shows F1 along the horizontal flange
reach (and beam), perpendicular to the bend. These frames transform a wrench;
they do not assign allowable loads, load sharing, or one-sided resistance.
"""

from dataclasses import dataclass

Vector = tuple[int, int, int]


@dataclass(frozen=True)
class HLFrame:
    reach: Vector  # Catalog F1 axis, oriented away from the upright leg.
    bend: Vector  # Unlisted horizontal transverse axis.
    uplift: Vector  # Catalog uplift axis for the horizontal-seat-up pose.


def _cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def frame_for_reach(reach: Vector, uplift: Vector = (0, 0, 1)) -> HLFrame:
    """Register axis-aligned reach and rotated catalog-uplift direction.

    An inverted seat has `uplift = -Z` as a *geometric transform only*; the
    catalog's seat-up allowable cannot be transferred to it by this helper.
    """
    if reach not in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
        raise ValueError("reach must be a horizontal signed coordinate axis")
    if uplift not in ((0, 0, 1), (0, 0, -1)):
        raise ValueError("uplift must be a signed vertical coordinate axis")
    return HLFrame(reach=reach, bend=_cross(uplift, reach), uplift=uplift)


def _dot(a: tuple[float, float, float], b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def local_wrench(
    frame: HLFrame,
    force: tuple[float, float, float],
    moment: tuple[float, float, float],
) -> dict[str, tuple[float, float, float]]:
    """Project a signed wrench at one unchanged reference point onto HL axes.

    The caller must first transfer moments to the chosen joint origin; this
    function does not add a lever-arm cross product or distribute joint load.
    """
    basis = (frame.reach, frame.bend, frame.uplift)
    return {
        "force": tuple(_dot(force, axis) for axis in basis),
        "moment": tuple(_dot(moment, axis) for axis in basis),
    }


# The reference frame records the physical manufacturer's typical figure, not
# the drawing's page-horizontal projection. Upper poses follow current ideal
# outward-X seats; lower follows the rearward-Y horizontal seat. Mirrored bend
# signs are coordinate bookkeeping, not separate catalog-rated load signs.
POSE_ORIENTATION: dict[str, tuple[Vector, Vector]] = {
    "catalog_typical_right": ((1, 0, 0), (0, 0, 1)),
    "upper_right_outward_x": ((1, 0, 0), (0, 0, 1)),
    "upper_left_outward_x": ((-1, 0, 0), (0, 0, 1)),
    "lower_rearward_y": ((0, -1, 0), (0, 0, 1)),
    "b_lower_right_front": ((1, 0, 0), (0, 0, -1)),
    "b_lower_right_rib": ((-1, 0, 0), (0, 0, -1)),
    "b_lower_left_front": ((-1, 0, 0), (0, 0, -1)),
    "b_lower_left_rib": ((1, 0, 0), (0, 0, -1)),
}


def pose_frames() -> dict[str, HLFrame]:
    return {
        name: frame_for_reach(reach, uplift)
        for name, (reach, uplift) in POSE_ORIENTATION.items()
    }
