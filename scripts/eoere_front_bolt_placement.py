"""Check current front runner/post bolt ends and outer edges on cached solids.

This resolves the end/outer-edge part of the governing two-wood reference.
Rows, oblique shear area, group action and local fracture stay separate.
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
INPUT = current.DOC / "selected-hardware-v1/current-response-v1/joint-closure-v1/front-bolt-placement-inputs-v1.json"
AXES = tuple(f"rail_front_bolt_{side}_{i}" for side in ("left", "right") for i in (1, 2))


def outer_planes(profile):
    """Six exterior planes of these extruded profiles, including the rear bevel."""
    basis = np.asarray(profile["basis_grain_u_v_xyz"], dtype=float)
    datum = np.asarray(profile["datum_xyz_mm"], dtype=float)
    vertices = np.asarray(profile["raw_profile_vertices_luv_mm"], dtype=float)
    current.require(basis.shape == (3, 3) and datum.shape == (3,) and vertices.ndim == 2
                    and vertices.shape[1] == 3 and np.isfinite(vertices).all()
                    and np.isfinite(basis).all() and np.isfinite(datum).all()
                    and np.linalg.norm(basis @ basis.T - np.eye(3)) < 1e-8
                    and np.linalg.det(basis) > 0., "finite orthonormal stock profile required")
    local = [(np.asarray(p["outward_normal_luv"], dtype=float), p["offset_from_datum_mm"])
             for p in profile["end_cut_planes"]]
    current.require(len(local) == 2 and {int(np.sign(n[0])) for n, _ in local} == {-1, 1},
                    "exactly two classified end planes required")
    for i in (1, 2):
        n = np.eye(3)[i]
        local.extend([(-n, -float(vertices[:, i].min())), (n, float(vertices[:, i].max()))])
    current.require(all(np.isfinite(n).all() and np.isfinite(d) and abs(np.linalg.norm(n)-1.) < 1e-8
                        and np.max(vertices @ n-d) < 1e-5 for n, d in local),
                    "profile vertices must lie inside their six outward planes")
    return [{"normal_xyz": (basis.T @ n).tolist(), "offset_mm": float(d+(basis.T @ n) @ datum)}
            for n, d in local]


def confirm_outer_faces(shape, planes):
    """Refuse changed exterior planes or additional non-cylindrical geometry."""
    found, cylinders = set(), 0
    for face in shape.Faces():
        kind = face.geomType()
        if kind == "CYLINDER":
            cylinders += 1
            continue
        current.require(kind == "PLANE", "unsupported finished boundary type")
        normal, point = np.asarray(face.normalAt().toTuple()), np.asarray(face.Center().toTuple())
        matches = [i for i, p in enumerate(planes)
                   if np.linalg.norm(normal-p["normal_xyz"]) < 1e-8
                   and abs(normal @ point-p["offset_mm"]) < 1e-5]
        current.require(len(matches) == 1, "finished exterior plane differs from source profile")
        found.add(matches[0])
    current.require(found == set(range(6)) and cylinders == 4,
                    "all six source exterior planes and four modeled bores required")
    return {"all_six_exterior_planes_match": True, "cylindrical_faces": cylinders}


def placement(profile, shaft, surface, end_method):
    outer_planes(profile)
    basis, datum = np.asarray(profile["basis_grain_u_v_xyz"]), np.asarray(profile["datum_xyz_mm"])
    direction, point = np.asarray(shaft["basis"][0]), np.asarray(shaft["point"])
    local_axis = basis @ direction
    current.require(np.linalg.norm(local_axis[[0, 2]]) < 1e-8 and abs(abs(local_axis[1])-1.) < 1e-8,
                    "shaft must traverse the stock thickness perpendicular to grain")
    interval = np.asarray(surface["interval_mm"], dtype=float)
    current.require(interval.shape == (2,) and np.isfinite(interval).all() and interval[1] > interval[0],
                    "positive finite own bearing interval required")
    points = np.asarray([basis @ (point+s*direction-datum) for s in interval])
    vertices = np.asarray(profile["raw_profile_vertices_luv_mm"])
    current.require(np.min(points[:, 1])-vertices[:, 1].min() >= -1e-5
                    and np.max(points[:, 1])-vertices[:, 1].max() <= 1e-5, "bearing interval outside stock")
    ends = []
    for plane in profile["end_cut_planes"]:
        n, offset = np.asarray(plane["outward_normal_luv"]), plane["offset_from_datum_mm"]
        distance = float(np.min((offset-points @ n)/abs(n[0])))
        current.require(np.isfinite(distance) and distance >= 0., "bearing axis outside end planes")
        ends.append({"end_sign": int(np.sign(n[0])), "minimum_axis_to_end_along_grain_mm": distance})
    edges = [float(np.min(points[:, 2])-vertices[:, 2].min()),
             float(vertices[:, 2].max()-np.max(points[:, 2]))]
    diameter = shaft["diameter_mm"]
    end = end_method(min(e["minimum_axis_to_end_along_grain_mm"] for e in ends), diameter,
                     "softwood_parallel_tension")
    return {"axis_id": shaft["axis_id"], "member": surface["host"], "diameter_mm": diameter,
            "own_bearing_interval_mm": interval.tolist(), "grain_end_distances": ends,
            "outer_edge_distances_mm": edges, "conservative_end_component": end,
            "minimum_outer_edge_4D_margin_mm": min(edges)-4.*diameter,
            "full_value_end_and_outer_edge_screen_pass": end["end_factor_only"] == 1. and min(edges) >= 4.*diameter-1e-6,
            "complete_Cdelta": None, "Cg": None, "complete_joint_resistance": None}


def run():
    inputs = json.loads(INPUT.read_bytes())
    current.require(inputs["schema"] == "eoere_front_bolt_placement_inputs/v1"
                    and inputs["axis_ids"] == list(AXES)
                    and inputs["producer"] == current.ref(OWN)
                    and current.sha(OWN) == LOADED_SHA, "frozen producer and exact four-axis scope required")
    cases, pins = intake_source.intake()
    refs = [current.ref(INPUT), inputs["producer"], current.ref(current.MANIFEST),
            *inputs["methods"].values(), inputs["test_source"], inputs["primary_source"]]
    pins = current.join(pins, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    end_method = component.load(inputs["methods"]["end_component"], "front_end_component").end_geometry_factor
    container = component.load(inputs["methods"]["container"], "front_container")
    reference = component.load(inputs["methods"]["distance"], "front_distance")
    reference.tools()
    known = container.known_answer(reference)
    first = cases[0][1]
    members = {r["name"]: r for r in first["source_inputs"]["timber_rows"]}
    observations = {r["id"]: r for r in first["source_inputs"]["finished_body_observations"]}
    shapes, geometry, bindings = {}, [], []
    for shaft in first["source_inputs"]["shafts"]:
        if shaft["axis_id"] not in AXES:
            continue
        current.require(shaft["diameter_mm"] == 9.525 and len(shaft["surfaces"]) == 2
                        and all(s["kind"] == "wood" for s in shaft["surfaces"]), "own two-wood front stack required")
        for surface in shaft["surfaces"]:
            host = surface["host"]
            profile = members[host]["raw_profile_source"]
            if host not in shapes:
                observation = observations[host]
                current.require(current.sha(current.ROOT/observation["source"]["path"]) == observation["source"]["sha256"],
                                "cached finished solid changed")
                shape = reference.cq.Shape.importBrep(str(current.ROOT/observation["source"]["path"]))
                solid, wrapper = container.strict_solid(shape, reference)
                current.require(wrapper == observation["strict_container"], "own strict container record differs")
                faces = confirm_outer_faces(solid, outer_planes(profile))
                shapes[host] = {"solid_source": observation["source"], "wrapper": wrapper, "exterior_faces": faces}
            geometry.append(placement(profile, shaft, surface, end_method))
    current.require(len(geometry) == 8 and len(shapes) == 4 and {r["axis_id"] for r in geometry} == set(AXES),
                    "all eight front bolt/wood occurrences on four members required")
    for binding, field, data in cases:
        current.require(field["source_inputs"]["shafts"] == first["source_inputs"]["shafts"]
                        and field["source_inputs"]["timber_rows"] == first["source_inputs"]["timber_rows"]
                        and field["source_inputs"]["finished_body_observations"] == first["source_inputs"]["finished_body_observations"],
                        "current front geometry differs between cases")
        rows = [r for r in data["findings"]["timber"]["shaft_components"] if r["axis_id"] in AXES]
        current.require(len(rows) == 4 and {r["axis_id"] for r in rows} == set(AXES)
                        and all(r["component"] is not None for r in rows), "four own front references required")
        bindings.append({"case_id": binding["case_id"], "state_id": binding["state_id"], "field": binding["field"],
                         "references": [{"axis_id": r["axis_id"], "unadjusted_reference_n": r["component"]["unadjusted_component_Z_n"],
                                         "lateral_demand_n": r["component"]["lateral_demand_n"],
                                         "unadjusted_ratio": r["component"]["V_over_unadjusted_component_Z"],
                                         "complete_Cdelta": None, "Cg": None} for r in rows]})
    for module in tuple(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file and Path(file).suffix == ".py" and Path(file).resolve().is_relative_to(current.ROOT):
            path = str(Path(file).resolve().relative_to(current.ROOT))
            current.require(path in pins and current.sha(current.ROOT/path) == pins[path],
                            "unbound repository execution source: "+path)
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, "loaded producer changed")
    return {"schema": "eoere_front_bolt_placement/v1", "producer": current.ref(OWN), "inputs": current.ref(INPUT),
            "source_sha256": pins, "sources_unchanged": True, "known_answer_container": known,
            "runtime": {n: importlib.metadata.version(n) for n in ("numpy", "cadquery", "cadquery-ocp")},
            "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
            "extra_grid": False, "axis_ids": list(AXES), "finished_members": shapes, "placement": geometry, "cases": bindings,
            "status": "CURRENT_FRONT_END_AND_OUTER_EDGE_COMPLETE_GROUP_PENDING",
            "all_full_value_end_and_outer_edge_screens_pass": all(r["full_value_end_and_outer_edge_screen_pass"] for r in geometry),
            "minimum_grain_end_distance_mm": min(e["minimum_axis_to_end_along_grain_mm"] for r in geometry for e in r["grain_end_distances"]),
            "minimum_outer_edge_distance_mm": min(min(r["outer_edge_distances_mm"]) for r in geometry),
            "maximum_unadjusted_reference_ratio": max(r["unadjusted_ratio"] for c in bindings for r in c["references"]),
            "complete_Cdelta": None, "complete_joint_resistance": None, "structural_acceptance": False,
            "native_solve_CAD_rebuild_geometry_change_or_actual_fit": False, "release": current.manifest()["release"],
            "limits": ["Full-value end and outer-edge checks use both end directions and both external cross-grain edges, conservatively against 7D and 4D. The rear floor bevel is included analytically over each complete bearing interval.",
                       "This is not the complete geometry factor: row/connected-group ownership, oblique shear area, interacting holes, local fracture and simultaneous force/couple resistance remain separate.",
                       "The 0.5-factor sensitivity is not established by these front end/outer-edge distances. Neither Cg=1 nor complete Cdelta=1 is adopted.",
                       "Current conditional first-order demands and purchased hardware assumptions are retained. No physical demand qualification or observed fit is supplied."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
