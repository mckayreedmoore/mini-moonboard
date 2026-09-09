"""Actual complete compact member extraction; hardware envelopes are NOT contact-qualified."""
import argparse
import hashlib
import json
from itertools import pairwise
from pathlib import Path

import cadquery as cq

from fea.stitch_joint_geometry import validate_disjoint
from mini_moonboard import leg_hardware_trial as model
from mini_moonboard.box_exports import exact_bounds

PARENT = Path("site/hybrid/lumber-leg-hardware-2x6-e0/manifest.json")
LIMITS = ("Geometry preparation only. Complete drilled rim and leg; no crop, mesh, material law, "
          "load, restraint, preload, friction or strength assignment. Hardware retains the trial's "
          "clearance-envelope shaft/head/nut, unresolved fillets and threads. Smooth nut bore does "
          "not provide axial thread retention. Not ready for a physical hardware contact solve.")
ROLES = ("bolt", "head_washer_1", "head_washer_2", "nut_washer_1", "nut_washer_2", "nut")


def sources():
    parent = json.loads(PARENT.read_text())
    for path, sha in parent["sources"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError("Parent hardware geometry source changed")
    names = set(parent["sources"]) | {str(PARENT), "fea/compact_leg_joint_geometry.py",
                                     "fea/stitch_joint_geometry.py"}
    return {name: Path(name).read_bytes() for name in sorted(names)}


def common_planar_faces(first, second):
    """Actual common planar area; indices address source CAD faces, not mesh labels."""
    rows = []
    for i, a in enumerate(first.Faces()):
        if a.geomType() != "PLANE":
            continue
        aa = exact_bounds(a)
        for j, b in enumerate(second.Faces()):
            if b.geomType() != "PLANE":
                continue
            bb = exact_bounds(b)
            if aa.xlen > 1e-6 or bb.xlen > 1e-6 or abs(aa.xmin-bb.xmin) > 1e-6:
                continue
            intersection = a.intersect(b)
            if intersection.Area() > 1e-5:
                rows.append({"first_source_face": i, "second_source_face": j,
                    "area_mm2": intersection.Area(), "centroid_xyz_mm": intersection.Center().toTuple()})
    return rows


def prepare(side="left"):
    if side not in ("left", "right"):
        raise ValueError("Select left or right")
    before = sources()
    names = (f"base_side_{side}", f"lumber_leg_{side}")
    parts = {p.name: p for p in model.parts(extension=0.) if p.name in names}
    bolts = [c for c in model.connections(extension=0.) if c.name.startswith(f"lumber_leg_bolt_{side}_")]
    if len(parts) != 2 or len(bolts) != 4 or any(tuple(c.members) != names for c in bolts):
        raise ValueError("Require actual four-bolt two-member ownership")
    bodies = {name: p.shape for name,p in parts.items()}
    connections = []
    for bolt in bolts:
        shaft, w1, w2, w3, w4, head, nut = bolt.components()
        # Integral bolt head/shaft is one body. No washer or nut is fused to it.
        hardware = (shaft.fuse(head).clean(), w1, w2, w3, w4, nut)
        bodies.update({bolt.name+"_"+role: shape for role,shape in zip(ROLES, hardware, strict=True)})
        bore = cq.Solid.makeCylinder(11.1125/2, bolt.length, bolt.start, bolt.direction)
        collar = cq.Solid.makeCylinder(11.3125/2, bolt.length, bolt.start, bolt.direction)
        for name, part in parts.items():
            if part.shape.intersect(bore).Volume() > .001 or part.shape.intersect(collar).Volume() <= .01:
                raise ValueError(f"Missing actual bore or surrounding wood: {name}/{bolt.name}")
        connections.append({"name": bolt.name, "start_xyz_mm": bolt.start.toTuple(),
            "axis_xyz": bolt.direction.toTuple(), "length_mm": bolt.length,
            "nominal_diameter_mm": bolt.diameter, "wood_bore_diameter_mm": 11.1125,
            "grip_mm": bolt.grip, "washer_thickness_mm": bolt.washer_thickness,
            "members": names, "hardware_bodies": [bolt.name+"_"+role for role in ROLES]})
    maximum_overlap = validate_disjoint(bodies)
    wood_contact = common_planar_faces(bodies[names[0]], bodies[names[1]])
    if not wood_contact:
        raise ValueError("Missing actual wood interface")
    _, _, along, across = model.base.geometry("2x6", 0.)
    rim_grain = (model.base.original.b.point(0.,1.,0.)-model.base.original.b.point(0.,0.,0.)).normalized()
    interfaces = [{"bodies": list(names), "source_faces": wood_contact}]
    for bolt in bolts:
        prefix = bolt.name+"_"
        chain = [prefix+"bolt", prefix+"head_washer_1", prefix+"head_washer_2", names[0]]
        chain += [names[1], prefix+"nut_washer_1", prefix+"nut_washer_2", prefix+"nut"]
        for first, second in pairwise(chain):
            if (first,second) == names:
                continue
            faces = common_planar_faces(bodies[first], bodies[second])
            if not faces:
                raise ValueError(f"Missing stack face adjacency: {first}/{second}")
            interfaces.append({"bodies": [first,second], "source_faces": faces})
    report = {"side": side, "stock": "2x6", "extension_mm": 0., "limits": LIMITS,
        "qualified_for_design": False, "hardware_contact_geometry_verified": False,
        "cropped": False, "cut_planes": [], "boundary_conditions": [], "loads": [],
        "coordinates": "Original assembly global XYZ, mm; no transforms",
        "local_axes": {"thickness": [1.,0.,0.], "leg_grain": along.toTuple(),
                       "leg_across_grain": across.toTuple(), "rim_grain": rim_grain.toTuple()},
        "wood_members": list(names), "connections": connections, "planar_adjacencies": interfaces,
        "maximum_overlap_mm3": maximum_overlap,
        "body_count": len(bodies), "hardware_sources": model.SOURCES,
        "required_contact_geometry_replacements": [
            "Replace enlarged clearance-envelope shaft with catalog-bounded bolt body diameter and hole clearance",
            "Resolve full-body length, thread runout and root-bearing extent through the actual washer/wood stack; do not assume full shank through all wood",
            "Replace cylindrical head/nut envelopes with stated hex, bearing-face, chamfer and fillet idealizations",
            "Define explicit nut/bolt axial retention without bonding washers or assuming tightening/preload",
            "Select washer dimensional case and independently resolve each washer bearing/flexure/contact surface",
            "Specify material axes/properties, contact laws, loading and physical remote boundary conditions before meshing/solving"],
        "bodies": {name: {"volume_mm3": shape.Volume(), "centroid_xyz_mm": shape.Center().toTuple(),
            "source_part_name": name if name in parts else None,
            "bounds_mm": [[getattr(exact_bounds(shape),a+end) for a in "xyz"] for end in ("min","max")]}
            for name,shape in bodies.items()}}
    if sources() != before:
        raise ValueError("Source changed during preparation")
    report["source_sha256"] = {name: hashlib.sha256(data).hexdigest() for name,data in before.items()}
    return bodies, report


def export(directory, side="left"):
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError("Refusing to overwrite local joint geometry")
    bodies, report = prepare(side)
    before = sources()
    if {n: hashlib.sha256(v).hexdigest() for n,v in before.items()} != report["source_sha256"]:
        raise ValueError("Source changed before export")
    directory.mkdir(parents=True, exist_ok=False)
    for name, shape in bodies.items():
        cq.exporters.export(shape, str(directory/(name+".step")))
    for name, data in before.items():
        path = directory/"launch_sources"/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if sources() != before:
        raise ValueError("Source changed during export")
    report["step_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob("*.step")}
    report["original_part_step_sha256"] = {n: report["step_sha256"][n+".step"] for n in report["wood_members"]}
    (directory/"geometry.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--side", choices=("left", "right"), default="left")
    args = parser.parse_args()
    print(export(args.output, args.side))
