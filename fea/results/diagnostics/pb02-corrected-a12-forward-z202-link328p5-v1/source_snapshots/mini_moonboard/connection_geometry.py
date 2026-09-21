"""Nominal axial material intervals, not annular support or thread capacity."""
import math

import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_UNKNOWN


def material_intervals(shape, start, direction, lower_mm, upper_mm, *, tolerance=1e-7):
    """Return sorted signed-mm intervals of strict interior along a finite axis.

    Direction is normalized. Boundary-only tangencies receive no material credit.
    Gaps no larger than ``tolerance`` are merged as numerical seams. The caller
    supplies the actual net receiver, including service reliefs; this helper does
    not restore bores or infer effective thread, bearing or structural resistance.
    Invalid inputs and kernel errors raise rather than masquerading as no material.
    """
    try:
        origin, axis = cq.Vector(start), cq.Vector(direction)
        lower, upper, tol = float(lower_mm), float(upper_mm), float(tolerance)
        values = (*origin.toTuple(), *axis.toTuple(), lower, upper, tol)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Axis and limits must be finite")
        if lower >= upper or tol <= 0 or not math.isfinite(axis.Length) or axis.Length == 0:
            raise ValueError("Require increasing limits, positive tolerance and nonzero direction")
        axis = axis.normalized()
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Invalid material-interval axis or limits") from error
    if not isinstance(shape, cq.Shape):
        raise TypeError("Receiver must be a valid solid shape")
    try:
        if not shape.isValid() or not shape.Solids():
            raise ValueError("Receiver must contain valid solids")
        solids = shape.Solids()
        line = cq.Edge.makeLine(origin+axis*lower, origin+axis*upper)
        intersection = line.intersect(shape)
        intervals = []
        for edge in intersection.Edges():
            a, z = sorted((p-origin).dot(axis) for p in (edge.startPoint(), edge.endPoint()))
            if not math.isfinite(a) or not math.isfinite(z):
                raise RuntimeError("Nonfinite intersection coordinates")
            if a < lower-tol or z > upper+tol:
                raise RuntimeError("Intersection escaped the requested segment")
            a, z = max(a, lower), min(z, upper)
            if z-a <= tol:
                continue
            midpoint = origin+axis*((a+z)/2)
            # CQ isInside includes ON faces; a tangent axis must not count as
            # interior engagement. Check constituent solids for compound input.
            interior = False
            for solid in solids:
                classifier = BRepClass3d_SolidClassifier(solid.wrapped)
                classifier.Perform(gp_Pnt(*midpoint.toTuple()), tol)
                if classifier.State() == TopAbs_UNKNOWN:
                    raise RuntimeError("Indeterminate material classification")
                interior |= classifier.State() == TopAbs_IN
            if interior:
                intervals.append((a, z))
        merged = []
        for a, z in sorted(intervals):
            if merged and a <= merged[-1][1]+tol:
                merged[-1] = (merged[-1][0], max(z, merged[-1][1]))
            else:
                merged.append((a, z))
        return merged
    except ValueError:
        raise
    except Exception as error:
        raise RuntimeError("Material-interval geometry evaluation failed") from error
