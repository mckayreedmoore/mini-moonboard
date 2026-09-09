"""Catalog-dimension elastic geometry hypotheses, not physical resistance bounds."""
import argparse
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path

import cadquery as cq

from fea import compact_leg_joint_geometry as original

model = original.model
DIAMETER = 9.525
ROOT_REFERENCE = .298*25.4
BODY_LENGTH_REFERENCE = 74.6125
FLATS = .562*25.4
HEAD_HEIGHT = .243*25.4
NUT_HEIGHT = .337*25.4
VARIANTS = ("smooth", "root-reference")
LIMITS = ("Geometry-only elastic-contact hypotheses. Maximum listed head/nut flats and heights, "
          "minimum listed MCX thickness; nominal body diameter. Smooth and stepped root-reference "
          "variants are not proven physical bounds. Root .298in is not a manufacturer minimum. "
          "No helix, chamfer, fillet, preload, thread stripping or strength acceptance. "
          "Nut-shaft axial retention requires an explicit planned tied-engagement idealization; "
          "no ties, material, contact law, restraints or loads have been applied.")


def source_bytes():
    values = original.sources()
    for path in ("fea/compact_leg_joint_geometry.py", "fea/compact_joint_contact_geometry.py"):
        values[path] = Path(path).read_bytes()
    return values


def hex_prism(start, direction, height):
    plane = cq.Plane(origin=start, xDir=(0,1,0), normal=direction)
    return cq.Workplane(plane).polygon(6, FLATS/math.cos(math.pi/6)).extrude(height).val()


def prepare(side="left", variant="smooth"):
    if variant not in VARIANTS:
        raise ValueError("Select smooth or root-reference")
    before = source_bytes()
    previous, parent = original.prepare(side)
    wood = parent["wood_members"]
    bodies = {name: previous[name] for name in wood}
    bolts = [c for c in model.connections(model.WASHER_MIN, extension=0.)
             if c.name.startswith(f"lumber_leg_bolt_{side}_")]
    connections, interfaces = [], []
    for bolt in bolts:
        d, start = bolt.direction.normalized(), bolt.start
        nut_start = 4*model.WASHER_MIN+bolt.grip
        diameter = DIAMETER if variant == "smooth" else ROOT_REFERENCE
        shaft = cq.Solid.makeCylinder(DIAMETER/2,
            bolt.length if variant == "smooth" else BODY_LENGTH_REFERENCE, start, d)
        if variant == "root-reference":
            shaft = shaft.fuse(cq.Solid.makeCylinder(ROOT_REFERENCE/2,
                bolt.length-BODY_LENGTH_REFERENCE, start+d*BODY_LENGTH_REFERENCE, d)).clean()
        core = shaft.fuse(hex_prism(start, -d, HEAD_HEIGHT)).clean()
        nut = hex_prism(start+d*nut_start, d, NUT_HEIGHT).cut(
            cq.Solid.makeCylinder(diameter/2, NUT_HEIGHT, start+d*nut_start, d)).clean()
        _, w1, w2, w3, w4, _, _ = bolt.components()
        components = (core,w1,w2,w3,w4,nut)
        names = [bolt.name+"_"+role for role in original.ROLES]
        bodies.update(zip(names,components,strict=True))
        chain = [names[0],names[1],names[2],wood[0],wood[1],names[3],names[4],names[5]]
        for first, second in pairwise(chain):
            if any(row["bodies"] == [first,second] for row in interfaces):
                continue
            faces = original.common_planar_faces(bodies[first],bodies[second])
            if not faces:
                raise ValueError(f"Missing planar stack adjacency: {first}/{second}")
            interfaces.append({"bodies": [first,second], "source_faces": faces})
        connections.append({"name": bolt.name, "start_xyz_mm": start.toTuple(), "axis_xyz": d.toTuple(),
            "length_mm": bolt.length, "members": wood, "wood_bore_diameter_mm": 11.1125,
            "body_diameter_mm": DIAMETER, "distal_diameter_mm": diameter,
            "diameter_transition_underhead_mm": BODY_LENGTH_REFERENCE if variant == "root-reference" else None,
            "wood_intervals_underhead_mm": [[2*model.WASHER_MIN,2*model.WASHER_MIN+38.1],
                                             [2*model.WASHER_MIN+38.1,2*model.WASHER_MIN+76.2]],
            "hardware_bodies": names,
            "planned_tied_engagement": {"bodies": [names[0],names[5]],
                "underhead_interval_mm": [nut_start,nut_start+NUT_HEIGHT], "diameter_mm": diameter,
                "surface": "Coincident coaxial cylindrical patch within this axial interval, not entire shaft",
                "applied": False, "physical_thread_capacity_verified": False}})
    maximum = original.validate_disjoint(bodies)
    if len(bodies) != 26 or len(connections) != 4:
        raise ValueError("Require complete four-bolt joint")
    report = {"side": side,"variant": variant,"limits": LIMITS,"stock":"2x6","extension_mm":0.,
        "qualified_for_design":False,"physical_bounds_verified":False,"solved":False,
        "cropped":False,"wood_members":wood,"coordinates":parent["coordinates"],"local_axes":parent["local_axes"],
        "body_count":len(bodies),"connections":connections,"planar_adjacencies":interfaces,
        "maximum_overlap_mm3":maximum,"head_nut_flats_mm":FLATS,"head_height_mm":HEAD_HEIGHT,
        "nut_height_mm":NUT_HEIGHT,"washer_thickness_mm":model.WASHER_MIN,
        "dimension_case":"Maximum listed head/nut dimensions; minimum MCX thickness; nominal bolt body diameter",
        "hardware_sources":model.SOURCES,"boundary_conditions":[],"loads":[],"applied_ties":[],
        "bodies":{name:{"volume_mm3":shape.Volume(),"centroid_xyz_mm":shape.Center().toTuple()}
                  for name,shape in bodies.items()}}
    if before != source_bytes():
        raise ValueError("Source changed during geometry preparation")
    report["source_sha256"] = {n:hashlib.sha256(v).hexdigest() for n,v in before.items()}
    return bodies,report


def export(directory, side="left", variant="smooth"):
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError("Refusing to overwrite contact idealization")
    bodies,report = prepare(side,variant)
    before = source_bytes()
    if {n:hashlib.sha256(v).hexdigest() for n,v in before.items()} != report["source_sha256"]:
        raise ValueError("Source changed before export")
    directory.mkdir(parents=True,exist_ok=False)
    for name,shape in bodies.items():
        cq.exporters.export(shape,str(directory/(name+".step")))
    for name,data in before.items():
        path = directory/"launch_sources"/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    if before != source_bytes():
        raise ValueError("Source changed during export")
    report["step_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob("*.step")}
    report["original_part_step_sha256"] = {n:report["step_sha256"][n+".step"] for n in report["wood_members"]}
    (directory/"geometry.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--side",choices=("left","right"),default="left")
    parser.add_argument("--variant",choices=VARIANTS,default="smooth")
    args = parser.parse_args()
    print(export(args.output,args.side,args.variant))
