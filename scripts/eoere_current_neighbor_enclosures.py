"""Current source-bound piece enclosures for possible additional timber neighbors.

Rigidly re-express each genuine closed solid in its own straight chart. A union
of station-interval boxes covers its mapped material, including both endpoint
extensions. Only strict separation of every covering-piece pair excludes a
whole-body pair. Overlap supplies no contact or collision conclusion.
"""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from itertools import pairwise, product
from pathlib import Path

import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Trsf

from scripts import eoere_current_contact_inverse as inverse

current, scope = inverse.current, inverse.scope
canonical_sha = inverse.canonical_sha
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
DOCUMENTATION = [
    "https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_9_3/src/BRepBndLib/BRepBndLib.hxx",
    "https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.Shape.transformShape",
    "https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_9_3/src/BRepExtrema/BRepExtrema_DistShapeShape.hxx",
]
TOOL_VERSIONS = {"cadquery": "2.8.0", "cadquery-ocp": "7.9.3.1.1", "numpy": "2.5.2", "scipy": "1.18.1"}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded current neighbor producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def chart_basis(chart):
    axis = np.asarray(chart["reference_axis_xyz"], dtype=float)
    start = np.asarray(chart["reference_start_xyz_mm"], dtype=float)
    current.require(axis.shape == start.shape == (3,) and np.isfinite(np.r_[axis, start]).all()
                    and abs(np.linalg.norm(axis)-1.) < 1e-8, "finite proper source axis required")
    axis = axis/np.linalg.norm(axis)
    anchor = np.eye(3)[int(np.argmin(abs(axis)))]
    second = np.cross(anchor, axis)
    second /= np.linalg.norm(second)
    basis = np.column_stack((axis, second, np.cross(axis, second)))
    current.require(np.max(abs(basis.T@basis-np.eye(3))) < 1e-12 and abs(np.linalg.det(basis)-1.) < 1e-12,
                    "proper rigid chart re-expression required")
    return start, basis


def local_reference_box(owner, chart, extent, geometry, smooth, *, numerical_padding_mm=1e-6):
    """Query a copy of the original source; no tessellation supplies its bounds."""
    reference = smooth.reference
    current.require(isinstance(geometry, reference.ReferenceSolidDistance) and geometry.owner_id == owner == extent["owner_id"]
                    and extent["source_identity"]["topology_sha256"] == geometry.topology_sha256
                    and all(extent["source_identity"].get(k) == v for k, v in geometry.source_identity.items()),
                    "exact own chart-domain and genuine boundary source required")
    current.require(np.isfinite(numerical_padding_mm) and numerical_padding_mm >= 1e-6,
                    "at least the declared numerical source-box padding required")
    start, basis = chart_basis(chart)
    transform = np.eye(4)
    transform[:3, :3], transform[:3, 3] = basis.T, -basis.T@start
    rigid = gp_Trsf()
    rigid.SetValues(*transform[:3].ravel().tolist())
    native_transform = np.array([[rigid.Value(i, j) for j in range(1, 5)] for i in range(1, 4)])
    source_box = np.asarray(extent["source_identity"]["genuine_cached_solid_bounds_xyz_mm"])
    coordinate_error = abs(native_transform-transform[:3])@np.r_[abs(source_box).max(axis=1), 1.]
    local = geometry.shape.transformShape(reference.cq.Matrix(rigid))
    current.require(local.isValid() and len(local.Solids()) == 1
                    and abs(local.Volume()-geometry.shape.Volume()) <= max(1e-5, 1e-8*geometry.shape.Volume()),
                    "rigidly re-expressed own solid changed validity or volume")
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(local.wrapped, box, False, True)
    values = np.asarray(box.Get(), dtype=float)
    bounds = np.column_stack((values[:3], values[3:]))
    current.require(bounds.shape == (3, 2) and np.isfinite(bounds).all() and np.all(bounds[:, 0] < bounds[:, 1]),
                    "finite full-source local bounding box required")
    current.require(reference.brep_sha(geometry.shape) == geometry.shape_sha256
                    and canonical_sha(geometry.topology) == geometry.topology_sha256,
                    "original owned source changed during rigid query")
    record = {"owner_id": owner, "row_canonical_sha256": canonical_sha(chart),
        "extent_canonical_sha256": canonical_sha(extent), "source_identity": dict(geometry.source_identity),
        "topology_sha256": geometry.topology_sha256, "original_canonical_solid_sha256": geometry.shape_sha256,
        "local_canonical_solid_sha256": reference.brep_sha(local), "world_to_local_matrix": transform.tolist(),
        "native_world_to_local_matrix": native_transform.tolist(), "coordinate_reexpression_error_bound_mm": coordinate_error.tolist(),
        "chart_basis_columns_xyz": basis.tolist(), "native_local_bounds_mm": bounds.tolist(),
        "padded_local_bounds_mm": (bounds+np.column_stack((-coordinate_error-numerical_padding_mm, coordinate_error+numerical_padding_mm))).tolist(),
        "native_use_triangulation": False, "native_use_shape_tolerance": True,
        "numerical_padding_mm": numerical_padding_mm, "formal_interval_certificate": False}
    return {**record, "record_canonical_sha256": canonical_sha(record)}


def piece_enclosures(chart, q, extent, bound, local_box, *, numerical_padding_mm=1e-6):
    """Cover phi(X)=X+u(t)+(R(t)-I)(X-C(t)) on every source interval."""
    current.require(np.isfinite(numerical_padding_mm) and numerical_padding_mm >= 1e-6,
                    "at least the declared numerical piece padding required")
    current.require(local_box["record_canonical_sha256"] == canonical_sha({k: v for k, v in local_box.items() if k != "record_canonical_sha256"}),
                    "own native reference-box record changed")
    coarse = scope.containing_deformed_box(chart, q, extent, bound, numerical_padding_mm=numerical_padding_mm)
    current.require(local_box["owner_id"] == extent["owner_id"]
                    and local_box["row_canonical_sha256"] == canonical_sha(chart)
                    and local_box["extent_canonical_sha256"] == canonical_sha(extent), "own source local box required")
    start, basis = chart_basis(chart)
    current.require(np.array_equal(local_box["chart_basis_columns_xyz"], basis), "own rigid source basis differs")
    box = np.asarray(local_box["padded_local_bounds_mm"], dtype=float)
    current.require(box.shape == (3, 2) and np.isfinite(box).all() and np.all(box[:, 0] < box[:, 1]),
                    "finite complete own local source box required")
    stations = np.asarray(chart["reference_stations_mm"])
    q = np.asarray(q, dtype=float)
    indices, storage = np.asarray(chart["node_dof_indices"]), np.asarray(chart["storage_basis_columns_xyz"])
    translations = q[indices[:, :3]]@storage.T
    intervals = []
    if box[0, 0] < stations[0]: intervals.append((box[0, 0], min(box[0, 1], stations[0]), "first", 0))
    for i, (lo, hi) in enumerate(pairwise(stations)):
        intervals.append((max(box[0, 0], lo), min(box[0, 1], hi), "segment", i))
    if box[0, 1] > stations[-1]: intervals.append((max(box[0, 0], stations[-1]), box[0, 1], "last", len(stations)-1))
    intervals = [row for row in intervals if row[0] < row[1]]
    current.require(intervals and intervals[0][0] == box[0, 0] and intervals[-1][1] == box[0, 1]
                    and all(a[1] == b[0] for a, b in pairwise(intervals)),
                    "all source axial coordinates must be covered without gaps")
    pieces = []
    for ordinal, (lo, hi, kind, index) in enumerate(intervals):
        piece_box = box.copy()
        piece_box[0] = [lo, hi]
        local_corners = np.asarray(list(product(*piece_box.tolist())))
        world_corners = start+local_corners@basis.T
        source_world_box = np.asarray(extent["source_identity"]["genuine_cached_solid_bounds_xyz_mm"])+[-numerical_padding_mm, numerical_padding_mm]
        reference_world_box = np.column_stack((np.maximum(world_corners.min(axis=0), source_world_box[:, 0]),
                                               np.minimum(world_corners.max(axis=0), source_world_box[:, 1])))
        current.require(np.all(reference_world_box[:, 0] < reference_world_box[:, 1]),
                        "nonempty intersection of containing source boxes required")
        if kind == "segment":
            fractions = (np.asarray([lo, hi])-stations[index])/(stations[index+1]-stations[index])
            u = translations[index]+fractions[:, None]*(translations[index+1]-translations[index])
            arm_radius = float(np.linalg.norm(local_corners[:, 1:], axis=1).max())
            angle = bound["segments"][index]["absolute_geodesic_angle_upper_rad"]
            factor = float(2.*np.sin(angle/2.))
        else:
            endpoint = 0 if kind == "first" else -1
            u = translations[index][None, :]
            arms = local_corners.copy()
            arms[:, 0] -= stations[index]
            arm_radius = float(np.linalg.norm(arms, axis=1).max())
            factor = bound["rigid_endpoint_extensions"][endpoint]["rigid_endpoint_extension_L"]
        padding = factor*arm_radius+numerical_padding_mm
        bounds = reference_world_box+np.column_stack((u.min(axis=0)-padding, u.max(axis=0)+padding))
        pieces.append({"piece_index": ordinal, "branch": kind, "source_node_or_segment_index": index,
            "source_axial_interval_mm": [float(lo), float(hi)], "source_local_piece_bounds_mm": piece_box.tolist(),
            "reference_piece_world_bounds_xyz_mm": reference_world_box.tolist(),
            "translation_component_min_mm": u.min(axis=0).tolist(), "translation_component_max_mm": u.max(axis=0).tolist(),
            "reference_arm_radius_bound_mm": arm_radius, "rotation_factor_bound": factor,
            "rotation_displacement_norm_bound_mm": factor*arm_radius, "numerical_padding_mm": numerical_padding_mm,
            "bounds_xyz_mm": bounds.tolist()})
    return {"owner_id": extent["owner_id"], "q_canonical_sha256": bound["q_canonical_sha256"],
        "row_canonical_sha256": canonical_sha(chart), "extent_canonical_sha256": canonical_sha(extent),
        "local_reference_box_canonical_sha256": canonical_sha(local_box), "coarse_enclosure": coarse,
        "complete_reference_axial_box_covered": True, "pieces": pieces,
        "formal_interval_certificate_or_physical_contact_qualification": False}


def separate_piece_covers(first, second):
    current.require(first["owner_id"] != second["owner_id"]
                    and first["q_canonical_sha256"] == second["q_canonical_sha256"]
                    and first["complete_reference_axial_box_covered"] is second["complete_reference_axial_box_covered"] is True,
                    "distinct complete own covers at the same exact trial state required")
    arrays = []
    for record in [first, second]:
        boxes = np.asarray([r["bounds_xyz_mm"] for r in record["pieces"]], dtype=float)
        current.require(boxes.ndim == 3 and boxes.shape[1:] == (3, 2) and len(boxes) > 0
                        and np.isfinite(boxes).all() and np.all(boxes[:, :, 0] < boxes[:, :, 1]),
                        "nonempty finite own piece cover required")
        arrays.append(boxes)
    a, b = arrays
    gaps = np.maximum(a[:, None, :, 0]-b[None, :, :, 1], b[None, :, :, 0]-a[:, None, :, 1])
    scores = gaps.max(axis=2)
    i, j = (int(v) for v in np.unravel_index(np.argmin(scores), scores.shape))
    return {"first": first["owner_id"], "second": second["owner_id"], "cover_piece_pair_count": int(scores.size),
        "excluded_by_strict_separation_of_every_covering_piece_pair": bool(np.all(scores > 0.)),
        "minimum_over_piece_pairs_of_maximum_axis_separation_mm": float(scores[i, j]),
        "nonseparated_piece_pair_count": int(np.count_nonzero(scores <= 0.)),
        "minimum_witness_piece_indices": [i, j], "minimum_witness_axis_separation_mm": gaps[i, j].tolist(),
        "overlap_is_not_detected_contact_or_collision": True}


def reference_pair_distance(first, second, smooth, *, numerical_padding_mm=1e-6):
    """Native reference minimum with explicit numerical, non-interval limits."""
    reference = smooth.reference
    current.require(all(isinstance(g, reference.ReferenceSolidDistance) for g in [first, second])
                    and first.owner_id != second.owner_id and np.isfinite(numerical_padding_mm) and numerical_padding_mm >= 1e-6,
                    "distinct genuine reference solids and declared distance padding required")
    def source(geometry):
        current.require(reference.brep_sha(geometry.shape) == geometry.shape_sha256
                        and canonical_sha(geometry.topology) == geometry.topology_sha256, "own reference geometry changed")
        return {**geometry.source_identity, "topology_sha256": geometry.topology_sha256}
    first_source, second_source = source(first), source(second)
    query = BRepExtrema_DistShapeShape(first.shape.wrapped, second.shape.wrapped, 1e-7)
    current.require(query.IsDone() and query.NbSolution() > 0, "native reference minimum-distance query failed")
    distance = float(query.Value())
    current.require(np.isfinite(distance) and distance >= 0., "finite nonnegative native minimum required")
    witnesses = []
    for index in range(1, query.NbSolution()+1):
        a, b = query.PointOnShape1(index), query.PointOnShape2(index)
        a, b = np.array([a.X(), a.Y(), a.Z()]), np.array([b.X(), b.Y(), b.Z()])
        current.require(np.isfinite(np.r_[a, b]).all() and abs(np.linalg.norm(a-b)-distance) <= numerical_padding_mm,
                        "native minimum witness differs from returned distance")
        witnesses.append({"first_point_xyz_mm": a.tolist(), "second_point_xyz_mm": b.tolist()})
    current.require(source(first) == first_source and source(second) == second_source,
                    "original pair sources changed during distance query")
    record = {"first": first.owner_id, "second": second.owner_id,
        "first_source_geometry": first_source, "second_source_geometry": second_source,
        "minimum_reference_distance_mm": distance, "native_deflection_mm": 1e-7,
        "numerical_padding_mm": numerical_padding_mm, "native_inner_solution": bool(query.InnerSolution()),
        "minimum_witnesses": witnesses, "formal_interval_or_roundoff_certificate": False}
    return {**record, "record_canonical_sha256": canonical_sha(record)}


def cover_motion_bound(cover):
    """Bound sup |phi(X)-X| by translation norm plus rotation displacement."""
    current.require(cover["complete_reference_axial_box_covered"] is True and cover["pieces"], "complete own piece cover required")
    candidates = []
    for piece in cover["pieces"]:
        translation_box = np.column_stack((piece["translation_component_min_mm"], piece["translation_component_max_mm"]))
        padding, rotation = piece["numerical_padding_mm"], piece["rotation_displacement_norm_bound_mm"]
        current.require(translation_box.shape == (3, 2) and np.isfinite(translation_box).all()
                        and np.all(translation_box[:, 0] <= translation_box[:, 1])
                        and np.isfinite([padding, rotation]).all() and padding >= 1e-6 and rotation >= 0.,
                        "finite own piece motion bounds required")
        norm = float(np.linalg.norm(np.asarray(list(product(*translation_box.tolist()))), axis=1).max())
        candidates.append(norm+rotation+padding)
    index = int(np.argmax(candidates))
    return {"owner_id": cover["owner_id"], "q_canonical_sha256": cover["q_canonical_sha256"],
        "maximum_material_displacement_bound_mm": candidates[index], "witness_piece_index": index,
        "all_piece_displacement_bounds_mm": candidates}


def distance_motion_screen(distance, first, second):
    """Triangle inequality: dist(phi(A),psi(B)) >= dist(A,B)-deltaA-deltaB."""
    current.require(distance["record_canonical_sha256"] == canonical_sha({k: v for k, v in distance.items() if k != "record_canonical_sha256"})
                    and (distance["first"], distance["second"]) == (first["owner_id"], second["owner_id"])
                    and first["q_canonical_sha256"] == second["q_canonical_sha256"], "same own pair and trial state required")
    for side, cover in [("first", first), ("second", second)]:
        source = cover["coarse_enclosure"]["source_geometry"]
        current.require(all(distance[side+"_source_geometry"].get(k) == v for k, v in source.items()),
                        "reference distance and mapped cover sources differ")
    motion = [cover_motion_bound(c) for c in [first, second]]
    gap = distance["minimum_reference_distance_mm"]-distance["numerical_padding_mm"]-sum(m["maximum_material_displacement_bound_mm"] for m in motion)
    return {"reference_distance_record_canonical_sha256": canonical_sha(distance), "own_motion_bounds": motion,
        "minimum_reference_distance_minus_padding_and_both_motion_bounds_mm": gap,
        "excluded_by_strict_reference_distance_minus_motion": gap > 0.,
        "numerical_native_distance_not_interval_certificate": True}


def run(*, progress=None):
    cases, record, _measure, domains, pins = inverse.authenticated_inputs()
    poses = inverse.diagnostic_poses(cases, record, domains)
    _bedding, injectivity, _adapter, smooth, container, method_pins = inverse.runtime_methods()
    pins = current.join(pins, method_pins, {own_ref()["path"]: LOADED_SHA})
    current.verify(pins)
    tool_versions = {name: version(name) for name in TOOL_VERSIONS}
    current.require(tool_versions == TOOL_VERSIONS, "pinned native geometry and numerical versions required")
    geometries = inverse.current_geometries(domains, smooth, container, pins)
    saved = domains["current_diagnostic_ambient_injectivity"]
    charts, extents = saved["charts"], saved["extents"]
    current.require(set(charts) == set(extents) == set(geometries), "complete own22 source joins required")
    boxes = {o: local_reference_box(o, charts[o], extents[o], g, smooth) for o, g in geometries.items()}
    possible_pairs = sorted({(s["first"], s["second"]) for case in record["cases"] for s in case["all231_pair_screens"]
                             if s["possible_new_neighbor_requiring_own_feature_coverage"]})
    distances = {(a, b): reference_pair_distance(geometries[a], geometries[b], smooth) for a, b in possible_pairs}
    guards = {o: inverse.TrialDomain(o, chart, extents[o], 9450, injectivity) for o, chart in charts.items()}
    results = []
    for binding, q, source_case, source_domain in poses:
        bounds = {o: guard.bound(q) for o, guard in guards.items()}
        current.require(list(bounds.values()) == source_domain["bounds"], "fresh own trial bounds differ from frozen records")
        covers = {o: piece_enclosures(charts[o], q, extents[o], bound, boxes[o]) for o, bound in bounds.items()}
        current.require([r["coarse_enclosure"] for r in covers.values()] == source_case["containing_deformed_boxes"],
                        "old own coarse enclosures differ from frozen scope")
        screens = []
        for old in source_case["all231_pair_screens"]:
            result = separate_piece_covers(covers[old["first"]], covers[old["second"]])
            distance = distances.get((old["first"], old["second"]))
            motion_screen = None if distance is None else distance_motion_screen(distance, covers[old["first"]], covers[old["second"]])
            excluded = (old["excluded_by_strict_containing_box_separation"] or result["excluded_by_strict_separation_of_every_covering_piece_pair"]
                        or motion_screen is not None and motion_screen["excluded_by_strict_reference_distance_minus_motion"])
            screens.append({**result, "registered_source_pair": old["registered_source_pair"],
                "old_coarse_exclusion": old["excluded_by_strict_containing_box_separation"],
                "old_possible_new_neighbor": old["possible_new_neighbor_requiring_own_feature_coverage"],
                "source_distance_motion_screen": motion_screen, "excluded_by_any_source_bound_screen": bool(excluded),
                "remaining_possible_new_neighbor": not excluded and not old["registered_source_pair"]})
        current.require(len(screens) == len({(r["first"], r["second"]) for r in screens}) == 231,
                        "all231 unique whole-body pair decisions required")
        result = {**binding, "full_diagnostic_q_canonical_sha256": canonical_sha(q.tolist()), "own_piece_covers": list(covers.values()),
            "all231_pair_screens": screens,
            "previous_possible_new_neighbor_count": sum(r["old_possible_new_neighbor"] for r in screens),
            "newly_excluded_possible_neighbor_count": sum(r["old_possible_new_neighbor"] and r["excluded_by_any_source_bound_screen"] for r in screens),
            "remaining_possible_new_neighbor_count": sum(r["remaining_possible_new_neighbor"] for r in screens)}
        results.append(result)
        if progress: progress({k: result[k] for k in ["case_id", "previous_possible_new_neighbor_count", "newly_excluded_possible_neighbor_count", "remaining_possible_new_neighbor_count"]})
    current.verify(pins)
    return {"schema": "eoere_current_source_bound_piece_neighbor_enclosures/v2", "producer": own_ref(), "source_sha256": pins,
        "all_sources_unchanged": True, "case_sequence": inverse.component.SEQUENCE, "cases": results,
        "current_contact_scope": inverse.CONTACT_SCOPE, "current_inverse_producer": inverse.own_ref(),
        "source_local_reference_boxes": list(boxes.values()), "fresh_current_bound_count": sum(g.bound_evaluation_count for g in guards.values()),
        "possible_pair_reference_distances": list(distances.values()),
        "tool_versions": tool_versions,
        "native_geometry_documentation": DOCUMENTATION,
        "geometry_revision": record["geometry_revision"], "hardware_revision": record["hardware_revision"], "extra_grid": False,
        "saved_poses_only_not_trial_state_neighbor_coverage": True,
        "contact_force_or_frame_equilibrium_or_native_FEA_performed": False,
        "physical_stiffness_or_demand_or_strength_qualified": False, "structural_acceptance": False, "release": current.manifest()["release"],
        "limits": ["Rigid re-expression and exact-surface native bounding queries retain source topology; numerical padding is not an interval or roundoff certificate.",
            "A union of closed station-interval boxes covers the same geodesic map, including both rigid endpoint extensions. Source chart orthogonality and native geometry retain their floating-point limitations.",
            "Every covering-piece pair must be strictly separated to exclude a whole-body pair. Any overlap remains a possibility, not detected contact or collision.",
            "Piece reference boxes intersect two containing source boxes. A separate triangle-inequality screen subtracts both whole-material displacement bounds from the native reference minimum with numerical padding; no interval certificate is claimed.",
            "Only six saved diagnostic poses are screened. Registered pairs stay in the contact plan; no face cell, force or later-state neighbor is silently removed.",
            "This is no physical pressure, stiffness, complete equilibrium, resistance, native FEA or structural acceptance result."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run(progress=lambda value: print(json.dumps(value), flush=True)))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
