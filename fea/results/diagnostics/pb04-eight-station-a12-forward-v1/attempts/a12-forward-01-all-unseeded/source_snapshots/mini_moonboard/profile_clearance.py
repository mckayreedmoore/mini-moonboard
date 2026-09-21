"""Exact nominal planar bore ligament; no tearout or bearing capacity claim."""
import math

import cadquery as cq
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_UNKNOWN


def bore_ligament(face, center, radius, *, tolerance=1e-7):
    """Minimum distance to any face wire minus perpendicular bore radius, in mm.

    The center must be strictly inside a valid planar face, not in an inner hole
    or on an edge. Exact curved boundaries participate in the distance query.
    Negative ligament is retained when the circular bore crosses a boundary.
    This nominal geometry does not establish a permitted structural edge distance.
    """
    try:
        point = cq.Vector(center)
        radius, tolerance = float(radius), float(tolerance)
        if not all(math.isfinite(v) for v in (*point.toTuple(), radius, tolerance)):
            raise ValueError("Center, radius and tolerance must be finite")
        if radius < 0 or tolerance <= 0:
            raise ValueError("Radius must be nonnegative and tolerance positive")
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Invalid bore center, radius or tolerance") from error
    if not isinstance(face, cq.Face):
        raise TypeError("Profile must be a planar face")
    try:
        if not face.isValid() or face.geomType() != "PLANE":
            raise ValueError("Profile must be a valid planar face")
        if abs((point-face.Center()).dot(face.normalAt())) > tolerance:
            raise ValueError("Bore center must lie in the profile plane")
        classifier = BRepClass_FaceClassifier(face.wrapped, gp_Pnt(*point.toTuple()), tolerance)
        if classifier.State() == TopAbs_UNKNOWN:
            raise RuntimeError("Indeterminate profile classification")
        if classifier.State() != TopAbs_IN:
            raise ValueError("Bore center must be strictly inside profile material")
        vertex = cq.Vertex.makeVertex(*point.toTuple())
        distances = [vertex.distance(wire) for wire in face.Wires()]
        if not distances or not all(math.isfinite(v) and v >= 0 for v in distances):
            raise RuntimeError("Invalid boundary distance")
        return min(distances)-radius
    except ValueError:
        raise
    except Exception as error:
        raise RuntimeError("Profile ligament geometry evaluation failed") from error
