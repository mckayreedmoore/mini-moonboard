"""Correct inherited retained-bolt face points for the integrated kerf pose.

This only changes analysis coordinates. All twelve physical bolt axes remain
those of the maintained viewer and selected kerf-right source.
"""

from math import isclose

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT_MM


def retained_interface_point(assembly, baseline, connection):
    """Use the current shared rim/leg face for the two right upper bolts."""
    point = baseline.bolt_interface_point(connection)
    if not connection.name.startswith("lumber_leg_bolt_right_"):
        return point
    if (
        assembly.get("post_placement") != "integrated"
        or set(connection.members) != {"base_side_right", "lumber_leg_right"}
    ):
        raise ValueError("Require current integrated right rim/leg bolt pair")
    rim = assembly["wood"]["base_side_right"].BoundingBox()
    leg = assembly["wood"]["lumber_leg_right"].BoundingBox()
    if (
        not isclose(rim.xmax, leg.xmin, abs_tol=1e-6)
        or not isclose(point.x - rim.xmax, KERF_RIGHT_MM, abs_tol=1e-6)
    ):
        raise ValueError("Right kerf rim/leg interface no longer matches its source")
    return cq.Vector(rim.xmax, point.y, point.z)


class RetainedFacePose:
    """Expose baseline bolts and wood with current retained interface points."""

    def __init__(self, assembly, baseline):
        self.assembly = assembly
        self.baseline = baseline

    def __getattr__(self, name):
        return getattr(self.baseline, name)

    def bolt_interface_point(self, connection):
        return retained_interface_point(self.assembly, self.baseline, connection)


def retained_contact_rows(assembly, baseline, *, stiffness_per_area):
    """Rebuild the six inherited retained-bolt faces at current kerf points."""
    from fea.floor_flush_run import face_contacts

    rows = face_contacts(
        RetainedFacePose(assembly, baseline),
        stiffness_per_area=stiffness_per_area,
    )
    if len(rows) != 72:
        raise ValueError("Retained frame-bolt face-contact inventory changed")
    return tuple(rows)
