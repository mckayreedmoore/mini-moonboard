"""Prepare and solve the current 96-bolt frame with the existing declared laws.

Use its own cached geometry and gravity, four horizontal floor hosts and
perfectly bonded plywood pairs. The full-width plywood beam is an explicit
approximation; no actual bond, floor or complete-joint qualification follows.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import inspect
import json
import sys
from pathlib import Path
from unittest.mock import patch

import cadquery as cq
import numpy as np

from scripts import eoere_leg_header_mechanics as mechanics
from scripts.eoere_load_parameters import LoadParameters, parameterize_inputs
from scripts.eoere_paired_frame_basis import RAW, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
WORK = ROOT / RAW / "frame-completion-v1"
BASE = WORK / "owner-principal-pairs-v6/analysis-v1"
PHYSICAL = WORK / "owner-principal-pairs-v6/geometry/geometry.json"
RECEIPT = Path("docs/bolted-frame-development/owner-frame-v6/geometry.json")
GEOMETRY = BASE / "geometry/geometry.json"
MATERIAL = BASE / "material.json"
RUN = BASE / "four-hosts"
INPUTS = RUN / "preparation/inputs.json"
REVISION = "eoere-v6-perfect-bond-four-host-analysis-v1"
HOSTS = ("lumber_leg_left", "lumber_leg_right", "base_post_center_left", "base_post_center_right")


def rectangle_torsion(width, thickness):
    return width * thickness**3 * (1 / 3 - .21 * thickness / width *
                                  (1 - thickness**4 / (12 * width**4)))


def plywood_properties(width=139.7, thickness=19.05):
    """The existing APA24oc inputs, with the current actual envelope width."""
    if not 0 < thickness <= width:
        raise ValueError("positive rectangle dimensions required")
    lbf, inch = 4.4482216152605, 25.4
    ea = 5850000 * lbf * width / 304.8
    flat_ei = 330000 * lbf * inch**2 * width / 304.8
    gvtv = 45000 * lbf / inch
    return {"EA_N": 2 * ea, "EI_y_Nmm2": 2 * ea * width**2 / 12,
            "EI_z_Nmm2": 2 * flat_ei + 2 * ea * (thickness / 2)**2,
            "GA_u_N": 2e12 * width / 203.2, "GA_v_N": 2 * gvtv * width,
            "GJ_Nmm2": gvtv / thickness * rectangle_torsion(width, 2 * thickness),
            "shear_factor": 5 / 6}


def edited(source, before, after):
    assert source.count(before) == 1, (before, source.count(before))
    return source.replace(before, after)


def floor_method():
    if str(WORK) not in sys.path:
        sys.path.insert(0, str(WORK))
    with patch.object(sys, "argv", [str(OWN), "shared", "prepare"]):
        floor = mechanics.module(WORK / "owner_laminated_floor.py", "current_v6_fixed_floor")
    floor.OUT = RUN
    floor.laminated.MATERIAL = MATERIAL
    assert tuple(floor.HOSTS) == HOSTS
    # The source-bound force auditor is unchanged except for the explicit body census.
    source = edited(inspect.getsource(floor.read), "physical_body_count']==144", "physical_body_count']==148")
    namespace = {**vars(floor), "OWN": OWN}
    exec(compile(source, str(OWN), "exec"), namespace)  # noqa: S102 -- frozen auditor with the current inventory only
    floor.read = namespace["read"]
    return floor


def prepare():
    assert not BASE.exists(), "fresh analysis packet required"
    pins = {ref(OWN)["path"]: sha(OWN)}
    receipt = read(RECEIPT, pins, "d2849e0bb7e3751396854556fa0bb411d83f3cf94dec55ec157a582f4f5b6e80")
    g = read(PHYSICAL, pins, receipt["checked_geometry"]["sha256"])
    physical_clearance = read(receipt["checked_clearance"]["path"], pins,
                              receipt["checked_clearance"]["sha256"])
    assert physical_clearance["nominal_geometry_clear"] and len(g["axes"]) == 96
    assert g["revision"] == "eoere-flat-cleats-principal-upper-pairs-v6" and len(g["screw_axes"]) == 66
    GEOMETRY.parent.mkdir(parents=True)
    (BASE / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    unions = []
    for side in ("left", "right"):
        name, outer = "eoere_cleat_" + side, "eoere_cleat_" + side + "_outer"
        inner_profile, outer_profile = g["profiles"][name], g["profiles"][outer]
        old = [inner_profile["finished"], outer_profile["finished"]]
        shapes = []
        for row in old:
            assert sha(row["path"]) == row["sha256"]
            shapes.append(cq.Shape.importBrep(str(ROOT / row["path"])))
            pins[row["path"]] = row["sha256"]
        body = shapes[0].fuse(shapes[1]).clean()
        assert body.isValid() and len(body.Solids()) == 1
        assert abs(body.Volume() - sum(s.Volume() for s in shapes)) < .001
        path = GEOMETRY.parent / (name + ".brep")
        assert body.exportBrep(str(path))
        box = body.BoundingBox()
        source = {"id": name, "kind": "timber", **ref(path), "bytes": path.stat().st_size,
                  "volume_mm3": body.Volume(), "center_of_mass_xyz_mm": list(body.Center().toTuple()),
                  "bounds_xyz_mm": [getattr(box, a + b) for a in "xyz" for b in ("min", "max")]}
        frame = np.asarray(inner_profile["basis_grain_u_v_xyz"])
        datum = np.asarray([box.xmin, inner_profile["datum_xyz_mm"][1], inner_profile["datum_xyz_mm"][2]])
        vertices = []
        for p in (inner_profile, outer_profile):
            for v in p["vertices_luv_mm"]:
                vertices.append((frame @ (np.asarray(p["datum_xyz_mm"]) + frame.T @ v - datum)).tolist())
        inner_profile.update(finished=source, datum_xyz_mm=datum.tolist(),
                             vertices_luv_mm=np.unique(np.round(vertices, 8), axis=0).tolist(),
                             blank_mm=[500.8860828293809 - 139.7, 139.7, 38.1],
                             material="APA24oc pair; perfect-bond analytical body; actual bond unqualified")
        del g["profiles"][outer]
        for axis in g["axes"]:
            if outer in axis["receivers"]:
                axis["receivers"].remove(outer)
        unions.append({"analysis_body": source, "physical_leaves": old,
                       "volume_equals_sum": True, "physical_outline_or_holes_changed": False})
    g.update(revision=REVISION, parent_owner_geometry=ref(PHYSICAL), perfect_bond_analysis=True,
             physical_plywood_leaves=4, analytical_laminated_bodies=2,
             lamination_union_proof=unions, actual_bond_qualified=False)
    g["source_sha256"].update(pins)
    mechanics.write(GEOMETRY, g)
    c = copy.deepcopy(physical_clearance)
    c.update(geometry=ref(GEOMETRY), analytical_unions_only=True,
             physical_occupied_clearance_reused=receipt["checked_clearance"], union_proof=unions)
    mechanics.write(GEOMETRY.parent / "clearance.json", c)
    old_material = WORK / "owner-bolt-moves-v4/analysis/material.json"
    material = read(old_material, pins)
    material["properties"] = plywood_properties()
    material.update(material="Two aligned APA24oc nominal19.05mm plywood leaves; perfect bond; 139.7mm full-width beam approximation",
                    current_envelope_width_mm=139.7, nominal_combined_thickness_mm=38.1,
                    physical_qualification=False,
                    sizing_limits=["Current 139.7mm full-width beam approximation for the actual trapezoidal perimeter; not a variable-width plate or physical force bound.",
                                   "Perfect compatibility between layers, no actual adhesive qualification; independent published EA and apparent flatwise EI retained."])
    material["source_sha256"].update({ref(OWN)["path"]: sha(OWN), ref(old_material)["path"]: sha(old_material)})
    mechanics.write(MATERIAL, material)
    # Inventory and current-geometry routing only; the preparation kernels stay pinned.
    source = inspect.getsource(mechanics.prepare)
    source = edited(source, "geometry['revision'] == 'eoere-single-leg-bolts-header-angles-v3'",
                    "geometry['revision'] == " + repr(REVISION))
    source = edited(source, "if name.startswith(('base_post_outer_', 'eoere_cleat_')) or returned:",
                    "if True:  # refresh every current gross timber row")
    source = edited(source, "holes = [] if three_pin else copy.deepcopy(old['all_factory_holes'])", "holes = []")
    namespace = dict(vars(mechanics))
    exec(compile(source, str(OWN), "exec"), namespace)  # noqa: S102 -- exact source-bound preparation with current geometry/pose routing
    namespace["prepare"](GEOMETRY, BASE / "preparation", MATERIAL)
    data = json.loads((BASE / "preparation/inputs.json").read_bytes())
    assert len(data["timber_rows"]) == 22 and len(data["shafts"]) == 96
    assert len(data["finished_receiver_wall_queries"]) == 112
    floor = floor_method()
    data["scenario"]["declared_fixed_floor_support"] = floor.contract()
    data["scenario"]["numerical_stopping_tolerance_N"] = 1e-5
    data["scenario"]["perfect_bond_analysis"] = {"physical_parent": ref(PHYSICAL),
                                               "analysis_geometry": ref(GEOMETRY), "actual_bond_qualified": False}
    data = parameterize_inputs(data, LoadParameters(weight=250, unit="lb"))
    for p in [OWN, WORK / "owner_laminated_floor.py", BASE / "preparation/inputs.json",
              Path(floor.law.__file__), WORK / "owner-requested-lamination-v1/shared-floor-known-answer-v1.json"]:
        data["source_sha256"][ref(p)["path"]] = sha(p)
    INPUTS.parent.mkdir(parents=True)
    (INPUTS.parent / "producer-snapshot.py").write_bytes(mechanics.OWN.read_bytes())
    mechanics.write(INPUTS, data)
    mechanics.write(BASE / "readiness.json", {"physical_geometry": ref(PHYSICAL), "analysis_geometry": ref(GEOMETRY),
        "material": ref(MATERIAL), "inputs": ref(INPUTS), "bodies": 148, "shafts": 96,
        "wood_walls": 112, "fitting_ports": 96, "screws": 66, "cases": len(data["cases"]),
        "new_force_response_computed": False, "complete_joint_or_frame_qualified": False,
        "source_snapshot": ref(BASE / "producer-snapshot.py")})
    print("PREPARED current96 / 148bodies / 112walls / 96ports / six250lb cases", flush=True)


def run(case):
    floor = floor_method()
    b = mechanics.response.load("bridge").frozen()
    folder = RUN / case
    assert not folder.exists(), "fresh case output required"
    with patch.object(b, "compile_execute", floor.compiler), patch.object(floor.law, "RESTRAINED_HOSTS", HOSTS):
        result = mechanics.run(INPUTS, MATERIAL, case, folder)
    assert result["converged"], "current case not admitted"
    floor.replay(folder / "field.json", folder / "independent-replay.json")
    print("ADMITTED current96", case, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "a12-forward", "a12-left", "a12-rear", "k12-right", "k12-rear", "a1-rear"))
    args = parser.parse_args()
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (prepare if args.action == "prepare" else lambda: run(args.action))()
