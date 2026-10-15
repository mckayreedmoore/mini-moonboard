"""Guarded reference closed-boundary distance jets; synthetic method scope only.

This geometry API does not turn reference distance into deformed Euclidean gap
or pressure. A caller must separately authenticate a solid's source and inverse
map, physical surface ownership, quadrature and branch-transition mechanics.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import OCP
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepExtrema import (
    BRepExtrema_DistShapeShape,
    BRepExtrema_IsInFace,
    BRepExtrema_IsOnEdge,
    BRepExtrema_IsVertex,
)
from OCP.GeomLProp import GeomLProp_SLProps
from OCP.gp import gp_Pnt, gp_Pnt2d
from OCP.TopAbs import TopAbs_FORWARD, TopAbs_IN, TopAbs_ON, TopAbs_OUT, TopAbs_REVERSED

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
LOADED_SOURCE_SHA256 = hashlib.sha256(OWN.read_bytes()).hexdigest()
SCHEMA = "thin_bolted_reference_closed_solid_distance/v1"
METHOD = "own-boundary-compound-distance-with-separate-solid-classification"
PINNED_TOOLS = {"ocp": "7.9.3.1", "cadquery": "2.8.0", "cadquery-ocp": "7.9.3.1.1"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def xyz(value):
    return np.array([value.X(), value.Y(), value.Z()], dtype=float)


def tools():
    values = {"ocp": OCP.__version__, "cadquery": cq.__version__,
              "cadquery-ocp": importlib.metadata.version("cadquery-ocp")}
    require(values == PINNED_TOOLS, "pinned OCCT/CadQuery toolchain required")
    return values


def source_pins():
    paths = [OWN, OWN.with_name("test_distance.py"), OWN.with_name("input.json"),
             ROOT/"mini_moonboard/connection_geometry.py", ROOT/"pyproject.toml", ROOT/"uv.lock"]
    pins = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    require(pins[str(OWN.relative_to(ROOT))] == LOADED_SOURCE_SHA256, "loaded distance source changed")
    return pins


def brep_sha(shape):
    stream = io.BytesIO()
    require(shape.exportBrep(stream), "reference BREP serialization failed")
    return hashlib.sha256(stream.getvalue()).hexdigest()


def distance_tool(vertex, target, tolerance):
    result = BRepExtrema_DistShapeShape(vertex.wrapped, target.wrapped, tolerance)
    require(result.IsDone() and result.NbSolution() > 0, "boundary extrema did not complete")
    require(np.isfinite(result.Value()) and result.Value() >= 0., "invalid boundary distance")
    return result


class ReferenceSolidDistance:
    """One valid, outward, closed solid; all its own faces remain in the search.

    Feature IDs bind actual BREP face bytes and ordinal in the source solid.
    Tolerance guard bands reject ordinary jets; they do not snap geometry or
    create an activation threshold. No mesh approximation supplies distance.
    """

    def __init__(self, shape, *, owner_id, source_identity,
                 linear_tolerance_mm=1e-7, tie_tolerance_mm=1e-6):
        tools()
        require(isinstance(shape, cq.Shape) and shape.isValid(), "valid own solid required")
        require(len(shape.Solids()) == 1 and len(shape.Shells()) == 1,
                "one solid with one closed shell required in this method scope")
        require(shape.wrapped.ShapeType() == shape.Solids()[0].wrapped.ShapeType(),
                "a solid, rather than a compound carrying extra geometry, is required")
        require(all(BRep_Tool.IsClosed_s(shell.wrapped) for shell in shape.Shells()),
                "reference shell has free boundaries")
        require(isinstance(owner_id, str) and owner_id and isinstance(source_identity, dict) and source_identity,
                "explicit own identity and source description required")
        self.owner_id, self.source_identity = owner_id, json.loads(json.dumps(source_identity, allow_nan=False))
        self.linear_tolerance = float(linear_tolerance_mm)
        self.tie_tolerance = float(tie_tolerance_mm)
        require(np.isfinite([self.linear_tolerance, self.tie_tolerance]).all()
                and 0. < self.linear_tolerance <= self.tie_tolerance, "positive ordered distance tolerances required")
        self.shape, self.faces = shape, shape.Faces()
        self.classifier = BRepClass3d_SolidClassifier(shape.wrapped)
        self.classifier.PerformInfinitePoint(self.linear_tolerance)
        require(self.classifier.State() == TopAbs_OUT, "solid's infinite-point orientation must be OUT")
        require(all(face.wrapped.Orientation() in (TopAbs_FORWARD, TopAbs_REVERSED) for face in self.faces),
                "internal/external face orientation is outside this method scope")
        self.boundary = cq.Compound.makeCompound(self.faces)
        require(not self.boundary.Solids() and len(self.boundary.Faces()) == len(self.faces),
                "boundary distance must contain every own face and no solid")
        self.shape_sha256, self.boundary_sha256 = brep_sha(shape), brep_sha(self.boundary)
        self.edges, self.vertices = shape.Edges(), shape.Vertices()
        self.support_records = {}
        for kind, shapes in (("EDGE", self.edges), ("VERTEX", self.vertices)):
            self.support_records[kind] = []
            for ordinal, item in enumerate(shapes, 1):
                digest = brep_sha(item)
                self.support_records[kind].append({"feature_id": f"{owner_id}/{kind.lower()}-{ordinal:04d}-{digest[:16]}",
                    "source_ordinal_1_based": ordinal, "support_brep_sha256": digest})
        self.face_records = []
        for ordinal, face in enumerate(self.faces, 1):
            digest = brep_sha(face)
            self.face_records.append({"feature_id": f"{owner_id}/face-{ordinal:04d}-{digest[:16]}",
                "face_ordinal_1_based": ordinal, "face_brep_sha256": digest,
                "surface_type": face.geomType(), "topological_orientation": str(face.wrapped.Orientation()),
                "face_area_mm2": float(face.Area()), "topological_face_tolerance_mm": BRep_Tool.Tolerance_s(face.wrapped)})
        self.topology = {"owner_id": owner_id, "source_identity": self.source_identity,
            "solid_brep_sha256": self.shape_sha256, "boundary_compound_brep_sha256": self.boundary_sha256,
            "valid_solid": True, "closed_shell_without_free_boundaries": True, "infinite_point_classification": "OUT",
            "counts": {"solids": 1, "shells": 1, "faces": len(self.faces), "edges": len(shape.Edges()),
                       "vertices": len(shape.Vertices())}, "volume_mm3": float(shape.Volume()),
            "boundary_area_mm2": float(shape.Area()), "own_faces": self.face_records,
            "own_edge_and_vertex_features": self.support_records,
            "mesh_used": False, "candidate_source_authentication_established": False}
        self.topology_sha256 = canonical(self.topology)

    def _feature(self, result, index, face_index):
        support = result.SupportTypeShape2(index)
        support_name = {BRepExtrema_IsInFace: "FACE_INTERIOR", BRepExtrema_IsOnEdge: "EDGE",
                        BRepExtrema_IsVertex: "VERTEX"}.get(support, "UNSUPPORTED")
        point = xyz(result.PointOnShape2(index))
        face = self.faces[face_index]
        entry = {**self.face_records[face_index], "support_type": support_name,
                 "closest_point_xyz_mm": point.tolist(), "distance_mm": float(result.Value())}
        support_shape = result.SupportOnShape2(index)
        if support == BRepExtrema_IsInFace:
            require(support_shape.IsSame(face.wrapped), "closest face differs from searched own face")
            support_id = entry["feature_id"]
        else:
            members = self.edges if support_name == "EDGE" else self.vertices if support_name == "VERTEX" else []
            matches = [i for i, item in enumerate(members) if support_shape.IsSame(item.wrapped)]
            require(len(matches) == 1, "closest edge/vertex does not match a unique own topological feature")
            support_id = self.support_records[support_name][matches[0]]["feature_id"]
        entry["own_face_feature_id"] = entry["feature_id"]
        entry["closest_support_feature_id"] = support_id
        if support == BRepExtrema_IsInFace:
            u, v = result.ParOnFaceS2(index)
            state = BRepClass_FaceClassifier(face.wrapped, gp_Pnt2d(u, v), self.linear_tolerance).State()
            entry["surface_parameters_uv"] = [u, v]
            entry["trim_classification"] = {TopAbs_IN: "IN", TopAbs_ON: "ON", TopAbs_OUT: "OUT"}.get(state, "UNKNOWN")
        return entry

    def _smooth_jet(self, point, rho, entry):
        face = self.faces[entry["face_ordinal_1_based"]-1]
        kind = entry["surface_type"]
        require(kind in ("PLANE", "CYLINDER"), "unsupported surface curvature")
        u, v = entry["surface_parameters_uv"]
        properties = GeomLProp_SLProps(BRep_Tool.Surface_s(face.wrapped), u, v, 2, self.linear_tolerance)
        require(properties.IsNormalDefined() and properties.IsCurvatureDefined(), "undefined surface differential properties")
        natural_normal = xyz(properties.Normal())
        orientation = 1. if face.wrapped.Orientation() == TopAbs_FORWARD else -1.
        normal = orientation*natural_normal
        closest = np.asarray(entry["closest_point_xyz_mm"])
        require(np.max(abs(xyz(properties.Value())-closest)) <= 10*self.linear_tolerance,
                "surface UV reconstruction differs from own closest point")
        require(np.max(abs(point-closest-rho*normal)) <= 10*self.linear_tolerance,
                "oriented face normal is inconsistent with signed boundary distance")
        adaptor = BRepAdaptor_Surface(face.wrapped)
        if kind == "PLANE":
            gradient, hessian = normal, np.zeros((3, 3))
            analytic = {"surface": "PLANE", "oriented_normal_xyz": normal.tolist()}
            require(max(abs(properties.MinCurvature()), abs(properties.MaxCurvature())) < 1e-10,
                    "plane curvature differs from zero")
        else:
            cylinder = adaptor.Cylinder()
            axis, origin, radius = xyz(cylinder.Axis().Direction()), xyz(cylinder.Location()), float(cylinder.Radius())
            projector = np.eye(3)-np.outer(axis, axis)
            radial = projector @ (point-origin)
            r = float(np.linalg.norm(radial))
            require(r > self.tie_tolerance, "cylinder axis has no unique radial distance jet")
            er = radial/r
            sign = float(normal @ er)
            require(abs(abs(sign)-1.) < 1e-10, "cylinder normal is not radial")
            sign = 1. if sign > 0 else -1.
            gradient = sign*er
            hessian = sign*(projector-np.outer(er, er))/r
            require(abs(sign*(r-radius)-rho) <= 10*self.linear_tolerance,
                    "cylinder signed radial distance differs from boundary distance")
            require(np.max(abs(np.sort(np.abs([properties.MinCurvature(), properties.MaxCurvature()]))-
                                      [0., 1./radius])) < 1e-9, "cylinder curvature magnitudes differ")
            analytic = {"surface": "CYLINDER", "axis_origin_xyz_mm": origin.tolist(), "axis_direction_xyz": axis.tolist(),
                        "radius_mm": radius, "query_axis_radius_mm": r, "oriented_radial_sign": sign,
                        "hessian_evaluated_at_query_radius_not_surface_radius": True}
        return {"gradient_rho_xyz": gradient.tolist(), "hessian_rho_per_mm": hessian.tolist(),
                "oriented_outward_normal_at_closest_xyz": normal.tolist(),
                "geom_lprop_natural_normal_xyz": natural_normal.tolist(),
                "geom_lprop_natural_principal_curvatures_per_mm": [properties.MinCurvature(), properties.MaxCurvature()],
                "analytic_feature_geometry": analytic}

    def query(self, point_xyz_mm):
        point = np.asarray(point_xyz_mm, dtype=float)
        require(point.shape == (3,) and np.isfinite(point).all(), "finite 3D reference query point required")
        require(brep_sha(self.shape) == self.shape_sha256 and brep_sha(self.boundary) == self.boundary_sha256,
                "reference solid or boundary changed")
        require(canonical(self.topology) == self.topology_sha256, "bound topology or source identity changed")
        require(all(a.wrapped.IsSame(b.wrapped) for a, b in zip(self.faces, self.shape.Faces(), strict=True)),
                "own face map differs from bound source solid")
        self.classifier.Perform(gp_Pnt(*point), self.linear_tolerance)
        state = self.classifier.State()
        require(state in (TopAbs_IN, TopAbs_OUT, TopAbs_ON), "unknown solid classification")
        classification = {TopAbs_IN: "IN", TopAbs_OUT: "OUT", TopAbs_ON: "ON"}[state]
        vertex = cq.Vertex.makeVertex(*point)
        boundary = distance_tool(vertex, self.boundary, self.linear_tolerance)
        require(not boundary.InnerSolution(), "boundary compound unexpectedly received solid inside shortcut")
        minimum = float(boundary.Value())
        candidates = []
        # Per-face replay guards ties that a single minimum result may coalesce.
        for face_index, face in enumerate(self.faces):
            distance = distance_tool(vertex, face, self.linear_tolerance)
            if distance.Value() <= minimum+self.tie_tolerance:
                candidates.extend(self._feature(distance, i, face_index) for i in range(1, distance.NbSolution()+1))
        require(candidates, "complete own face search omitted minimum")
        require(abs(min(entry["distance_mm"] for entry in candidates)-minimum) <= self.linear_tolerance,
                "own face minimum differs from boundary compound")
        distinct_points = []
        for entry in candidates:
            p = np.asarray(entry["closest_point_xyz_mm"])
            if all(np.linalg.norm(p-q) > self.tie_tolerance for q in distinct_points):
                distinct_points.append(p)
        rho = -minimum if state == TopAbs_IN else minimum
        if state == TopAbs_ON:
            require(minimum <= self.tie_tolerance, "ON classifier differs from boundary distance")
            # ON is tolerance based: retain the exact unsigned computation,
            # but do not invent a material side or snap a signed distance.
            rho = None
        flags = {"ON_or_touch_guard": state == TopAbs_ON or minimum <= self.linear_tolerance,
                 "multiple_own_minimizing_faces": len({x["feature_id"] for x in candidates}) > 1,
                 "multiple_minimizing_points": len(distinct_points) > 1,
                 "nonzero_penetration_medial_tie": state == TopAbs_IN and len(distinct_points) > 1,
                 "edge_support": any(x["support_type"] == "EDGE" for x in candidates),
                 "vertex_support": any(x["support_type"] == "VERTEX" for x in candidates),
                 "unsupported_surface_curvature": any(x["surface_type"] not in ("PLANE", "CYLINDER") for x in candidates),
                 "trim_not_strict_interior": any(x.get("trim_classification") != "IN" for x in candidates)}
        qualified = not any(flags.values()) and len(candidates) == 1
        jet = {"gradient_rho_xyz": None, "hessian_rho_per_mm": None,
               "oriented_outward_normal_at_closest_xyz": None}
        reason = "guarded tie/edge/vertex/touch/trim/unsupported-curvature branch"
        if qualified:
            try:
                jet = self._smooth_jet(point, rho, candidates[0])
                reason = None
            except ValueError as error:
                qualified, reason = False, str(error)
        result = {"schema": SCHEMA, "method": METHOD, "owner_id": self.owner_id,
            "reference_point_xyz_mm": point.tolist(), "reference_signed_distance_rho_mm": rho,
            "solid_classification": classification, "boundary_unsigned_distance_mm": minimum,
            "boundary_compound_contains_solid": False, "boundary_inner_solution": False,
            "boundary_global_solution_count": boundary.NbSolution(), "complete_near_minimum_own_features": candidates,
            "near_minimum_face_distance_spread_mm": max(x["distance_mm"] for x in candidates)-minimum,
            "ordinary_smooth_feature_jet_qualified": qualified, "jet_rejection_reason": reason,
            "branch_flags": flags, **jet, "topology_sha256": self.topology_sha256,
            "tolerances_mm": {"classifier_and_extrema": self.linear_tolerance, "tie_guard": self.tie_tolerance},
            "distance_units": "mm", "gradient_units": "dimensionless", "hessian_units": "1/mm",
            "candidate_topology_or_current_pressure_admitted": False,
            "release": {"capacity": False, "fabrication": False, "climbing": False}}
        require(brep_sha(self.shape) == self.shape_sha256 and brep_sha(self.boundary) == self.boundary_sha256,
                "geometry changed during reference distance query")
        require(canonical(self.topology) == self.topology_sha256, "bound topology changed during query")
        return result


def box_fixture(*, through_hole=False):
    shape = cq.Solid.makeBox(4., 4., 1., cq.Vector(-2., -2., -1.))
    if through_hole:
        cutter = cq.Solid.makeCylinder(.75, 1.5, cq.Vector(0., 0., -1.25), cq.Vector(0., 0., 1.))
        shape = shape.cut(cutter).Solids()[0]
    return ReferenceSolidDistance(shape, owner_id="synthetic-box-hole" if through_hole else "synthetic-box",
        source_identity={"kind": "synthetic-known-answer", "box_bounds_mm": [[-2., 2.], [-2., 2.], [-1., 0.]],
                         "through_hole_radius_mm": .75 if through_hole else None})


def known_answers():
    """Small exact-kernel coupons only; never load a candidate BREP or state."""
    before = source_pins()
    inputs = json.loads(OWN.with_name("input.json").read_bytes())
    require(inputs["pinned_toolchain"] == tools() and inputs["box_bounds_mm"] == [[-2., 2.], [-2., 2.], [-1., 0.]]
            and inputs["through_hole_radius_mm"] == .75 and inputs["linear_tolerance_mm"] == 1e-7
            and inputs["near_tie_guard_tolerance_mm"] == 1e-6, "matching frozen toy inputs required")
    box, hole = box_fixture(), box_fixture(through_hole=True)
    cases = [("box-top-in", box, [1.3, .2, -.25], -.25, True),
             ("box-top-out", box, [1.3, .2, .3], .3, True),
             ("box-side-in", box, [1.9, .2, -.25], -.1, True),
             ("box-edge-out", box, [2.1, 0., .2], np.hypot(.1, .2), False),
             ("box-vertex-out", box, [2.1, 2.2, .3], np.sqrt(.14), False),
             ("box-ON", box, [1.3, .2, 0.], None, False),
             ("box-medial-tie", box, [1.75, .2, -.25], -.25, False),
             ("hole-cylinder-in", hole, [1., .2, -.5], .75-np.hypot(1., .2), True),
             ("hole-cylinder-out", hole, [.5, .1, -.5], .75-np.hypot(.5, .1), True),
             ("hole-axis", hole, [0., 0., -.5], .75, False),
             ("hole-rim", hole, [.5, .1, .2], np.hypot(.75-np.hypot(.5, .1), .2), False)]
    rows = []
    for name, geometry, point, expected_rho, expected_jet in cases:
        row = geometry.query(point)
        if expected_rho is None:
            require(row["reference_signed_distance_rho_mm"] is None, "ON signed side was guessed")
            error = None
        else:
            error = abs(row["reference_signed_distance_rho_mm"]-expected_rho)
            require(error < 1e-12, "toy closed-boundary signed distance differs from hand answer")
        require(row["ordinary_smooth_feature_jet_qualified"] == expected_jet, "feature jet guard differs")
        rows.append({"case_id": name, "expected_reference_rho_mm": expected_rho,
                     "rho_error_mm": error, "response": row})
    fd = []
    for name, geometry, point in (("plane", box, [1.3, .2, -.25]),
                                 ("hole-in", hole, [1., .2, -.5]), ("hole-out", hole, [.5, .1, -.5])):
        q, h = np.array(point), 1e-5
        row = geometry.query(q)
        columns, derivatives = [], []
        for direction in np.eye(3)*h:
            plus, minus = geometry.query(q+direction), geometry.query(q-direction)
            require(plus["ordinary_smooth_feature_jet_qualified"] and minus["ordinary_smooth_feature_jet_qualified"],
                    "finite difference left the qualified feature branch")
            derivatives.append((plus["reference_signed_distance_rho_mm"]-minus["reference_signed_distance_rho_mm"])/(2*h))
            columns.append((np.array(plus["gradient_rho_xyz"])-minus["gradient_rho_xyz"])/(2*h))
        eg = float(np.max(abs(np.array(derivatives)-row["gradient_rho_xyz"])))
        gh = float(np.max(abs(np.array(columns).T-row["hessian_rho_per_mm"])))
        require(max(eg, gh) < 1e-8, "known-answer rho differential replay failed")
        fd.append({"case_id": name, "step_mm": h, "rho_to_gradient_max_abs": eg,
                   "gradient_to_hessian_max_abs_per_mm": gh})
    inside_solid = distance_tool(cq.Vertex.makeVertex(1.3, .2, -.25), box.shape, 1e-7)
    require(inside_solid.InnerSolution() and inside_solid.Value() == 0., "solid inside shortcut coupon changed")
    require(source_pins() == before, "method sources changed during toy replay")
    return {"schema": "thin_bolted_reference_closed_solid_distance_method_coupon/v1",
            "method": METHOD, "method_checks_pass": True, "source_sha256": before,
            "source_pins_before_after_unchanged": True, "input_sha256": before[str(OWN.with_name("input.json").relative_to(ROOT))],
            "fixture_topology": {"box": box.topology, "through-hole-box": hole.topology},
            "known_answers": rows, "finite_difference_checks": fd,
            "point_to_solid_inside_demonstration": {"value_mm": inside_solid.Value(), "inner_solution": True,
                                                   "correct_boundary_distance_mm": .25},
            "synthetic_geometry_queries_only": True, "candidate_BREP_q_K_or_action_consumed": False,
            "reference_rho_adopted_as_current_Euclidean_gap_or_pressure": False,
            "mesh_used": False, "limits": inputs["limits"], "primary_documentation": inputs["primary_documentation"],
            "toolchain": {**tools(), "python": platform.python_version(), "numpy": np.__version__},
            "release": {"candidate_method_ready": False, "candidate_admission": False,
                        "capacity": False, "fabrication": False, "climbing": False}}


def main():
    invocation = {"actual_sys_argv_from_start": sys.argv.copy(), "actual_sys_orig_argv_from_start": sys.orig_argv.copy(),
                  "pythonpath_from_start": os.environ.get("PYTHONPATH"), "cwd_from_start": str(Path.cwd()),
                  "loaded_driver_sha256": LOADED_SOURCE_SHA256,
                  "loaded_source_path": str(OWN.relative_to(ROOT))}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing reference distance evidence")
    result = {**known_answers(), "execution": invocation}
    with options.out.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"path": str(options.out), "sha256": hashlib.sha256(options.out.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
