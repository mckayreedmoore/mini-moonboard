"""Recover current cleat normal-force/couple demand on a finished transverse cut.

This is saved-action arithmetic and cached-solid querying, not a new frame
response or a perpendicular-tension/fracture capacity.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

import numpy as np

from scripts import eoere_current_washer_lands as intake_source

current, component = intake_source.current, intake_source.component
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
MEMBERS = ("eoere_cleat_left", "eoere_cleat_right")
CUT_Y_MM = -105.85
# Right-handed coordinates: normal Y, in-plane Z, in-plane X.
BASIS = np.asarray([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])
BOUNDARY_TOL_MM = 1e-7


def section_geometry(solid, cq, cut_y):
    """Measure the intact rectangular cut and both finished material portions."""
    bb = solid.BoundingBox()
    current.require(solid.isValid() and len(solid.Solids()) == 1
                    and bb.ymin < cut_y < bb.ymax, "valid one-solid interior cut required")
    span = 2.*max(bb.xlen, bb.ylen, bb.zlen)+2.
    face = solid.intersect(cq.Face.makePlane(span, span,
        cq.Vector((bb.xmin+bb.xmax)/2., cut_y, (bb.zmin+bb.zmax)/2.), cq.Vector(0., 1., 0.)))
    faces = face.Faces()
    current.require(len(faces) == 1 and faces[0].geomType() == "PLANE"
                    and len(faces[0].Edges()) == 4 and all(e.geomType() == "LINE" for e in faces[0].Edges()),
                    "one intact rectangular cut required; holes/notches are not a rectangle")
    sb, center = face.BoundingBox(), np.asarray(face.Center().toTuple())
    width, height, area = sb.xlen, sb.zlen, face.Area()
    current.require(width > 0. and height > 0. and abs(area-width*height) < 1e-5
                    and abs(center[1]-cut_y) < BOUNDARY_TOL_MM
                    and np.linalg.norm(center-np.asarray([(sb.xmin+sb.xmax)/2., cut_y, (sb.zmin+sb.zmax)/2.])) < 1e-6,
                    "cut must equal its rectangular hull")
    portions = {}
    for side, low, high in (("low", bb.ymin-1., cut_y), ("high", cut_y, bb.ymax+1.)):
        clip = cq.Solid.makeBox(bb.xlen+2., high-low, bb.zlen+2., cq.Vector(bb.xmin-1., low, bb.zmin-1.))
        piece = solid.intersect(clip)
        current.require(piece.isValid() and len(piece.Solids()) == 1 and piece.Volume() > 0.,
                        "connected positive-volume cut portions required")
        portions[side] = {"volume_mm3": piece.Volume(), "center_xyz_mm": list(piece.Center().toTuple())}
    total = solid.Volume()
    current.require(abs(sum(p["volume_mm3"] for p in portions.values())-total) < 1e-4,
                    "finished split volume does not conserve original material")
    mass_center = sum(np.asarray(p["center_xyz_mm"])*p["volume_mm3"] for p in portions.values())/total
    current.require(np.linalg.norm(mass_center-np.asarray(solid.Center().toTuple())) < 1e-6,
                    "finished split first moments do not conserve original material")
    return {"cut_y_mm": cut_y, "origin_xyz_mm": center.tolist(), "basis_normal_p_q_xyz": BASIS.tolist(),
            "width_x_mm": width, "height_z_mm": height, "area_mm2": area,
            "whole_volume_mm3": total, "whole_center_xyz_mm": list(solid.Center().toTuple()),
            "portions": portions}


def action_wrench(actions, origin, cut_y, include_boundary):
    """One-sided trace of the saved point-action law, retaining free couples."""
    origin = np.asarray(origin, dtype=float)
    current.require(origin.shape == (3,) and np.isfinite(origin).all(), "finite cut origin required")
    force, moment, selected = np.zeros(3), np.zeros(3), []
    for action in actions:
        point, own_force, couple = (np.asarray(action[k], dtype=float) for k in
                                  ("point_xyz_mm", "force_xyz_n", "free_couple_xyz_nmm"))
        current.require(all(a.shape == (3,) and np.isfinite(a).all() for a in (point, own_force, couple)),
                        "finite point force and free couple required")
        delta = point[1]-cut_y
        if delta > BOUNDARY_TOL_MM or (abs(delta) <= BOUNDARY_TOL_MM and include_boundary):
            force += own_force
            moment += np.cross(point-origin, own_force)+couple
            selected.append(action["id"])
    return force, moment, selected


def normal_components(q, width, height, normal_bound):
    """Normal equilibrium demand only; do not substitute a tensile allowable."""
    q = np.asarray(q, dtype=float)
    current.require(q.shape == (6,) and np.isfinite(q).all()
                    and np.isfinite([width, height]).all() and min(width, height) > 0.,
                    "finite wrench and positive rectangle required")
    bounds = [[-height/2., height/2.], [-width/2., width/2.]]
    lower = normal_bound(q.tolist(), bounds)
    area, ip, iq = width*height, width*height**3/12., height*width**3/12.
    corners = [{"p_z_mm": p, "q_x_mm": r,
                "normal_stress_mpa": float(q[0]/area+q[4]*r/iq-q[5]*p/ip)}
               for p in (-height/2., height/2.) for r in (-width/2., width/2.)]
    return {"normal_hull": lower, "affine_normal_equilibrium_field": {
                "corners": corners, "maximum_tension_mpa": max(0., max(r["normal_stress_mpa"] for r in corners)),
                "maximum_compression_mpa": max(0., -min(r["normal_stress_mpa"] for r in corners)),
                "constitutive_compatibility_or_local_fracture_qualified": False},
            "necessary_peak_tensile_stress_lower_bound_mpa": lower["minimum_tensile_normal_resultant_n"]/area,
            "perpendicular_tensile_allowable_mpa": None, "fracture_or_complete_resistance_n": None}


def member_actions(field, data, member, geometry):
    shafts = {r["axis_id"]: r for r in field["source_inputs"]["shafts"]}
    rows = [r for r in data["findings"]["timber"]["wood_surfaces"] if r["receiver"] == member]
    current.require(len(rows) == 4 and len({r["axis_id"] for r in rows}) == 4, "four own cleat bore actions required")
    actions = []
    for row in rows:
        shaft, point = shafts[row["axis_id"]], np.asarray(row["own_aggregate_point_xyz_mm"])
        current.require(abs(abs(shaft["basis"][0][0])-1.) < 1e-10
                        and abs(point[1]-CUT_Y_MM) > shaft["bore_diameter_mm"]/2.+BOUNDARY_TOL_MM,
                        "X-axis bore support must not cross the Y-normal cut")
        force, moment = np.zeros(3), np.zeros(3)
        for action in row["own_point_actions"]:
            own_force = np.asarray(action["signed_components"]["force_on_receiver_xyz_n"])
            force += own_force
            moment += np.cross(np.asarray(action["point_xyz_mm"])-point, own_force)+action["own_free_moment_nmm"]
        current.require(np.linalg.norm(force-row["own_force_xyz_n"], np.inf) < 1e-7
                        and np.linalg.norm(moment-row["own_moment_at_aggregate_xyz_nmm"], np.inf) < 1e-5,
                        "own point actions do not recover their complete bolt/wood wrench")
        actions.append({"id": row["axis_id"]+"/complete-wood-wrench", "point_xyz_mm": point.tolist(),
                        "force_xyz_n": force.tolist(), "free_couple_xyz_nmm": moment.tolist()})
    for row in field["contact_actions"]:
        if member in (row["first"], row["second"]):
            sign = 1. if row["first"] == member else -1.
            actions.append({"id": row["id"], "point_xyz_mm": row["point_xyz_mm"],
                            "force_xyz_n": (sign*np.asarray(row["force_on_first_xyz_n"])).tolist(),
                            "free_couple_xyz_nmm": (sign*np.asarray(row["moment_at_point_model_xyz_nmm"])).tolist()})
    current.require(all(member not in (r["first"], r["second"]) for r in field["panel_screw_actions"]),
                    "additional cleat screw actions must be included")
    gravity = [r for r in field["body_applied_loads"] if r["body"] == member]
    current.require(len(gravity) == 1 and gravity[0]["id"] == "self-weight/"+member
                    and np.linalg.norm(np.asarray(gravity[0]["point_xyz_mm"])-geometry["whole_center_xyz_mm"]) < 1e-6
                    and gravity[0]["force_xyz_n"][0:2] == [0., 0.] and gravity[0]["force_xyz_n"][2] < 0.,
                    "uniform finished-body gravity at its own mass center required")
    current.require(len({r["id"] for r in actions}) == len(actions), "duplicate cleat point-action identity")
    return actions, np.asarray(gravity[0]["force_xyz_n"])


def case_result(binding, field, data, member, geometry, normal_bound):
    actions, gravity = member_actions(field, data, member, geometry)
    origin = np.asarray(geometry["origin_xyz_mm"])
    full_force = gravity+sum((np.asarray(a["force_xyz_n"]) for a in actions), np.zeros(3))
    full_moment = np.cross(np.asarray(geometry["whole_center_xyz_mm"])-origin, gravity)+sum(
        (np.cross(np.asarray(a["point_xyz_mm"])-origin, a["force_xyz_n"])+a["free_couple_xyz_nmm"] for a in actions), np.zeros(3))
    current.require(np.linalg.norm(full_force, np.inf) < 1e-5 and np.linalg.norm(full_moment, np.inf) < 1e-5,
                    "whole-cleat force or moment balance fails unchanged numerical gates")
    high = geometry["portions"]["high"]
    high_gravity = gravity*high["volume_mm3"]/geometry["whole_volume_mm3"]
    traces = []
    for include in (False, True):
        force, moment, selected = action_wrench(actions, origin, CUT_Y_MM, include)
        force += high_gravity
        moment += np.cross(np.asarray(high["center_xyz_mm"])-origin, high_gravity)
        q = np.concatenate([BASIS @ force, BASIS @ moment])
        traces.append({"boundary_point_actions_in_high_trace": include, "high_point_action_ids": selected,
                       "required_cut_on_low_portion_n_nmm": q.tolist(),
                       **normal_components(q, geometry["width_x_mm"], geometry["height_z_mm"], normal_bound)})
    delta = np.asarray(traces[0]["required_cut_on_low_portion_n_nmm"])-traces[1]["required_cut_on_low_portion_n_nmm"]
    current.require(np.linalg.norm(delta[[0, 4, 5]], np.inf) < 1e-5,
                    "cut-coincident point-action allocation changes the normal demand")
    return {"case_id": binding["case_id"], "state_id": binding["state_id"], "field": binding["field"],
            "member": member, "complete_saved_exterior_point_actions": actions,
            "finished_high_portion_gravity_xyz_n": high_gravity.tolist(),
            "whole_body_force_residual_n": full_force.tolist(), "whole_body_moment_residual_nmm": full_moment.tolist(),
            "normal_trace_allocation_max_difference_n_nmm": float(np.linalg.norm(delta[[0, 4, 5]], np.inf)), "traces": traces}


def run(input_path):
    input_ref = current.ref(input_path)
    inputs = current.read(input_ref)
    current.require(inputs["schema"] == "eoere_cleat_transverse_wrench_inputs/v1"
                    and inputs["producer"] == current.ref(OWN) and current.sha(OWN) == LOADED_SHA,
                    "exact frozen producer required")
    execution = current.read(inputs["execution_sources"])
    cases, pins = intake_source.intake()
    refs = [input_ref, inputs["producer"], inputs["execution_sources"], inputs["test_source"],
            inputs["normal_hull_method"], *inputs["primary_and_scope_sources"], current.ref(current.MANIFEST),
            *execution["methods"].values()]
    pins = current.join(pins, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    bound = component.load(inputs["normal_hull_method"], "cleat_existing_normal_hull")
    known_bound = bound.coupon()
    reference = component.load(execution["methods"]["distance"], "cleat_distance")
    container = component.load(execution["methods"]["container"], "cleat_container")
    reference.tools()
    known_container = container.known_answer(reference)
    geometry, results = {}, []
    for binding, field, data in cases:
        for member in MEMBERS:
            observation = next(r for r in field["source_inputs"]["finished_body_observations"] if r["id"] == member)
            if member not in geometry:
                current.require(pins[observation["source"]["path"]] == observation["source"]["sha256"], "own cached solid must be bound")
                shape = reference.cq.Shape.importBrep(str(current.ROOT/observation["source"]["path"]))
                solid, wrapper = container.strict_solid(shape, reference)
                current.require(wrapper == observation["strict_container"] and abs(solid.Volume()-observation["volume_mm3"]) < .01,
                                "current finished solid or strict wrapper differs")
                geometry[member] = {**section_geometry(solid, reference.cq, CUT_Y_MM), "observation": observation}
            current.require(geometry[member]["observation"] == observation, "own current solid differs between cases")
            results.append(case_result(binding, field, data, member, geometry[member], bound.normal_bound))
    for module in tuple(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file and Path(file).suffix == ".py" and Path(file).resolve().is_relative_to(current.ROOT):
            path = str(Path(file).resolve().relative_to(current.ROOT))
            current.require(path in pins and current.sha(current.ROOT/path) == pins[path], "unbound repository execution source: "+path)
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA and len(results) == 12, "producer drift or incomplete own-case coverage")
    witness = max(results, key=lambda r: max(t["normal_hull"]["minimum_tensile_normal_resultant_n"] for t in r["traces"]))
    return {"schema": "eoere_cleat_transverse_wrench/v1", "producer": inputs["producer"], "inputs": input_ref,
            "source_sha256": pins, "all_sources_unchanged": True,
            "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1", "extra_grid": False,
            "known_answer_normal_hull": known_bound, "known_answer_container": known_container,
            "runtime": {n: importlib.metadata.version(n) for n in ("numpy", "cadquery", "cadquery-ocp")},
            "geometry": geometry, "cases": results, "maximum_tensile_resultant_witness": {k: witness[k] for k in ("case_id", "member", "traces")},
            "status": "CURRENT_CLEAT_NORMAL_FORCE_AND_COUPLE_DEMAND_COMPLETE_RESISTANCE_PENDING",
            "cleat_transverse_resistance": None, "complete_joint_resistance": None, "finished_member_capacity": None,
            "physical_demand_bounds_established": False, "structural_acceptance": False,
            "release": current.manifest()["release"], "native_solve_CAD_rebuild_geometry_change_or_actual_fit": False,
            "limits": ["Saved first-order point actions only, including source free couples and uniform gravity split over the actual finished solid. The two one-sided point traces have identical normal demand; their retained tangential actions can differ.",
                       "The rectangular-hull tensile resultant is a necessary normal equilibrium bound with unbounded point pressure. The affine normal field supplies only normal force and both normal-force moments, not physical compatibility, shear/torsion, bore stress or fracture resistance.",
                       "No generic NDS sawn-lumber perpendicular tensile allowable, EC5 design-format conversion, clear-wood capacity or historical candidate pass is adopted.",
                       "The broader complete-joint/member and physical stiffness/restraint qualifications remain unresolved. Deferred panel/screw remedies, excluded actual fit and no-slip assumption remain unchanged."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run(args.inputs))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
