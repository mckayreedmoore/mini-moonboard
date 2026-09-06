"""Separate undrilled base-rail geometry; all new connections remain unresolved."""
import argparse
import hashlib
import json
import math
from functools import cache
from itertools import combinations
from pathlib import Path

import cadquery as cq

from fea.user_load_envelope import hull

from .box_exports import exact_bounds, overlap
from .box_frame import Part
from .export import _export_step
from .footprint_frame import parts as reference_parts

HEIGHTS_MM = (100, 275)
RAIL_WIDTH_MM = 38.1
RAIL_HEIGHT_MM = 88.9
DENSITY_KG_M3 = 600.0


def baseline():
    """Original timber objects, without inventing hardware for an undrilled model."""
    return tuple(p for p in reference_parts(100, False) if not p.name.startswith("angle_"))


@cache
def parts(height_mm=275):
    if not math.isfinite(height_mm) or height_mm not in HEIGHTS_MM:
        raise ValueError("Only the 100 mm and 275 mm geometry comparisons are defined")
    original = baseline()
    by_name = {p.name: p for p in original}
    added = []
    for side, sign in (("left", -1), ("right", 1)):
        cheek = by_name[f"kicker_cheek_{side}"].shape
        rim = by_name[f"box_side_{side}"].shape
        leg = by_name[f"leg_{side}"].shape
        cb, lb = exact_bounds(cheek), exact_bounds(leg)
        y0, y1 = cb.ymin, lb.ymax
        outer = lb.xmax if sign > 0 else lb.xmin
        rail = cq.Workplane("XY").box(RAIL_WIDTH_MM, y1-y0, RAIL_HEIGHT_MM).translate(
            (outer+sign*RAIL_WIDTH_MM/2, (y0+y1)/2, height_mm)).val()
        # Project the actual cheek/rim material into the lateral gap, then
        # retain only the rail band and the existing cheek's longitudinal span.
        receiver = cheek.fuse(rim).clean()
        gap_band = rail.translate((-sign*RAIL_WIDTH_MM, 0, 0))
        front_clip = cq.Workplane("XY").box(10000, cb.ylen, 10000).translate(
            (0, (cb.ymin+cb.ymax)/2, 0)).val()
        spacer = receiver.translate((sign*RAIL_WIDTH_MM, 0, 0)).intersect(gap_band).intersect(front_clip).clean()
        for name, shape, description in (
            (f"base_rail_{side}", rail, "Unfastened external rail envelope; section and joints not rated"),
            (f"base_spacer_{side}", spacer, "Fitted front gap spacer from actual cheek/rim profile; no connection or bond assumed"),
        ):
            if not shape.isValid() or len(shape.Solids()) != 1 or shape.Volume() <= 0:
                raise ValueError(f"Invalid/disconnected candidate solid: {name}")
            bounds = exact_bounds(shape)
            added.append(Part(name, shape, (bounds.ylen, bounds.zlen, bounds.xlen), description, 1))
    return original+tuple(added)


def face_contact_area(a, b):
    """Common planar X-normal face area; all intended new joints use this plane."""
    area = 0.0
    for first in a.Faces():
        aa = exact_bounds(first)
        if aa.xlen > 1e-5:
            continue
        for second in b.Faces():
            bb = exact_bounds(second)
            if bb.xlen < 1e-5 and abs(aa.xmin-bb.xmin) < 1e-5:
                area += first.intersect(second).Area()
    return area


def state(items):
    volume = sum(p.shape.Volume() for p in items)
    centre = [sum(p.shape.Volume()*p.shape.Center().toTuple()[i] for p in items)/volume for i in range(3)]
    floor = [v.Center().toTuple()[:2] for p in items for face in p.shape.Faces()
             if abs(exact_bounds(face).zmin) < 1e-5 and abs(exact_bounds(face).zmax) < 1e-5
             for v in face.Vertices()]
    bounds = exact_bounds(cq.Compound.makeCompound([p.shape for p in items]))
    return {"part_count": len(items), "volume_mm3": volume, "mass_kg": volume*DENSITY_KG_M3/1e9,
            "centre_mm": centre, "centre_in": [v/25.4 for v in centre], "support_polygon_mm": hull(floor),
            "bounds_mm": [[getattr(bounds, axis+"min"), getattr(bounds, axis+"max")] for axis in "xyz"],
            "overall_dimensions_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "overall_dimensions_in": [v/25.4 for v in (bounds.xlen, bounds.ylen, bounds.zlen)]}


def inspect(height_mm=275):
    original, actual = baseline(), parts(height_mm)
    by_name = {p.name: p for p in actual}
    added = actual[len(original):]
    if any(p is not q for p, q in zip(original, actual[:len(original)], strict=True)):
        raise ValueError("Original timber was replaced")
    collisions = [(a.name, b.name, overlap(a.shape, b.shape)) for a, b in combinations(actual, 2)
                  if a in added or b in added]
    collisions = [row for row in collisions if row[2] > .01]
    if collisions:
        raise ValueError(f"New-part solid overlap: {collisions}")
    contacts = []
    for side in ("left", "right"):
        for first, second, required in (
            (f"base_rail_{side}", f"leg_{side}", True),
            (f"base_rail_{side}", f"base_spacer_{side}", True),
            (f"base_spacer_{side}", f"kicker_cheek_{side}", True),
            (f"base_spacer_{side}", f"box_side_{side}", height_mm == 275),
        ):
            area = face_contact_area(by_name[first].shape, by_name[second].shape)
            if required and area <= .01:
                raise ValueError(f"Missing intended face adjacency: {first}, {second}")
            contacts.append({"parts": [first, second], "area_mm2": area,
                             "status": "GEOMETRIC ADJACENCY ONLY; CONNECTION UNRESOLVED" if area > .01 else "NO CONTACT"})
    old_state, new_state = state(original), state(actual)
    if old_state["support_polygon_mm"] != new_state["support_polygon_mm"]:
        raise ValueError("Candidate changed the actual floor polygon")
    if any(exact_bounds(p.shape).zmin <= 0 for p in added):
        raise ValueError("A new rail/spacer reaches the floor")
    return {"candidate": f"2x8-foot100-tied-base-z{height_mm:g}", "height_mm": height_mm,
            "status": "GEOMETRY CHECKS ONLY; ALL NEW CONNECTIONS UNRESOLVED; NOT STRUCTURAL APPROVAL",
            "assumptions": "Unchanged undrilled timber from 2x8-foot100 plus two rails and two fitted spacers; all wood at comparison density600kg/m3; angles/fasteners/holds/glue/LEDs omitted; no holes/new fasteners/glue/bonded joint capacity; no floor anchors/pads/ballast/new floor contact",
            "baseline": old_state, "candidate_state": new_state,
            "added_mass_kg": new_state["mass_kg"]-old_state["mass_kg"], "density_kg_m3": DENSITY_KG_M3,
            "floor_polygon_unchanged": True, "new_part_overlap_mm3": collisions,
            "intended_face_contacts": contacts,
            "added_parts": [{"name": p.name, "volume_mm3": p.shape.Volume(),
                             "mass_kg": p.shape.Volume()*DENSITY_KG_M3/1e9,
                             "centre_mm": p.shape.Center().toTuple(),
                             "blank_dimensions_mm": p.blank, "blank_dimensions_in": [v/25.4 for v in p.blank],
                             "description": p.description} for p in added],
            "unresolved": ["All rail/spacer/frame attachments, fastener spacing and capacities",
                           "Existing cheek/rim and leg/rim connection demand after adding ties",
                           "Asymmetric/reversed loads, joint slip, rail buckling and lateral racking",
                           "Hardware, tool and actual climber/fall/access clearances",
                           "Global sliding/tipping and locally audited unilateral floor contact"]}


def export(directory, height_mm=275):
    directory = Path(directory)
    step, summary = directory/"candidate.step", directory/"summary.json"
    if step.exists() or summary.exists():
        raise ValueError("Existing candidate export must not be overwritten")
    report = inspect(height_mm)
    directory.mkdir(parents=True, exist_ok=True)
    assembly = cq.Assembly(name=report["candidate"]+"_UNFASTENED_GEOMETRY")
    for part in parts(height_mm):
        assembly.add(part.shape, name=part.name)
    _export_step(assembly, step)
    sources = ("tied_base.py", "footprint_frame.py", "shallow_frame.py", "hybrid_frame.py", "hybrid.py",
               "box_frame.py", "box_exports.py", "model.py", "panel_grid.py", "export.py")
    report["source_sha256"] = {"mini_moonboard/"+name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in sources}
    hull_source = Path(__file__).parents[1]/"fea/user_load_envelope.py"
    report["source_sha256"]["fea/user_load_envelope.py"] = hashlib.sha256(hull_source.read_bytes()).hexdigest()
    report["artifact_sha256"] = {step.name: hashlib.sha256(step.read_bytes()).hexdigest()}
    summary.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--height", type=int, choices=HEIGHTS_MM, default=275)
    args = parser.parse_args()
    print(export(Path("exports/tied-base")/f"z{args.height}", args.height))


if __name__ == "__main__":
    main()
