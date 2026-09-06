"""Actual right-leg stitch geometry preflight; no mesh, constraints or solver."""
import argparse
import hashlib
import json
import math
import sys
import tempfile
from itertools import combinations
from pathlib import Path

import cadquery as cq

from mini_moonboard import spacing_frame as frame
from mini_moonboard.box_exports import exact_bounds

LIMITS = (
    "Generic elastic geometry only; no material properties, bonding, constraints, "
    "preload, friction or capacity assigned. Real threads, contact laws and manufacturing "
    "tolerances remain unknown. Smooth nut and washer bores touch the nominal shank; "
    "this geometry does not supply threaded axial retention. No mesh or solver run."
)
VOLUME_TOLERANCE_MM3 = .001
DISTANCE_TOLERANCE_MM = 1e-5
REPOSITORY = Path(__file__).resolve().parents[1]


def stitches():
    return tuple(c for c in frame.connections() if c.name.startswith("leg_stitch_right_"))


def solids():
    """Four separate hardware bodies per stitch; only shaft/head are one body."""
    result = {p.name: p.shape for p in frame.parts(True)
              if p.name in ("leg_right_inner", "leg_right_outer")}
    for connection in stitches():
        shaft, washer_inner, washer_outer, head, nut = connection.components()
        result[connection.name + "_bolt"] = shaft.fuse(head).clean()
        for role, shape in (("washer_inner", washer_inner), ("washer_outer", washer_outer), ("nut", nut)):
            result[connection.name + "_" + role] = shape.cut(shaft).clean()
    return result


def validate_disjoint(bodies):
    """Allow contact, reject positive-volume overlap above CAD numerical tolerance."""
    maximum = 0.
    for name, shape in bodies.items():
        if (not shape.isValid() or len(shape.Solids()) != 1
                or not math.isfinite(shape.Volume()) or shape.Volume() <= 0):
            raise ValueError(f"Invalid single solid: {name}")
        bounds = exact_bounds(shape)
        if not all(math.isfinite(getattr(bounds, k + end)) for k in "xyz" for end in ("min", "max")):
            raise ValueError(f"Nonfinite solid bounds: {name}")
    for (name, shape), (other_name, other) in combinations(bodies.items(), 2):
        a, b = exact_bounds(shape), exact_bounds(other)
        if any(min(getattr(a, k + "max"), getattr(b, k + "max"))
               - max(getattr(a, k + "min"), getattr(b, k + "min")) <= 0 for k in "xyz"):
            continue
        volume = shape.intersect(other).Volume()
        maximum = max(maximum, volume)
        if not math.isfinite(volume) or volume < -VOLUME_TOLERANCE_MM3 or volume > VOLUME_TOLERANCE_MM3:
            raise ValueError(f"Positive-volume overlap: {name}, {other_name}: {volume} mm3")
    return maximum


def validate(bodies):
    connections = stitches()
    expected = {"leg_right_inner", "leg_right_outer"} | {
        c.name + "_" + role for c in connections
        for role in ("bolt", "washer_inner", "washer_outer", "nut")}
    if len(connections) != 3 or len(bodies) != 14 or set(bodies) != expected:
        raise ValueError("Expected two plies and twelve separate hardware bodies")
    maximum = validate_disjoint(bodies)
    records = {}
    for name, shape in bodies.items():
        bounds = exact_bounds(shape)
        records[name] = {"volume_mm3": shape.Volume(),
                         "bounds_mm": [bounds.xmin, bounds.ymin, bounds.zmin,
                                       bounds.xmax, bounds.ymax, bounds.zmax]}
    for name, x0 in (("leg_right_inner", 1257.3), ("leg_right_outer", 1276.35)):
        shape = bodies[name]
        bounds = exact_bounds(shape)
        if abs(bounds.xmin - x0) > 1e-5 or abs(bounds.xlen - 19.05) > 1e-5:
            raise ValueError("Wrong actual ply thickness/location")
        floors = [f for f in shape.Faces() if abs(exact_bounds(f).zmin) < 1e-5
                  and abs(exact_bounds(f).zmax) < 1e-5]
        holes = [c for c in frame.connections() if name in c.members]
        if len(floors) != 1 or len(holes) != 7 or sum(c.name.startswith("leg_stitch_") for c in holes) != 3:
            raise ValueError("Expected own floor and four upper plus three stitch bores")
        for hole in holes:
            origin = cq.Vector(x0, hole.start.y, hole.start.z)
            bore = cq.Solid.makeCylinder(5, 19.05, origin, cq.Vector(1, 0, 0))
            surround = cq.Solid.makeCylinder(6, 19.05, origin, cq.Vector(1, 0, 0))
            if (shape.intersect(bore).Volume() > VOLUME_TOLERANCE_MM3
                    or abs(shape.intersect(surround).Volume() - math.pi * 11 * 19.05) > .01):
                raise ValueError(f"Missing complete actual 10 mm bore: {name}/{hole.name}")
        records[name].update(floor_area_mm2=floors[0].Area(),
                             floor_centroid_mm=floors[0].Center().toTuple(),
                             bore_names=[c.name for c in holes])
    contact_pairs = [("leg_right_inner", "leg_right_outer")]
    stitch_records = []
    for c in connections:
        if (abs(c.diameter - 9.525) > 1e-8 or abs(c.grip - 38.1) > 1e-8
                or abs(c.length - 57.15) > 1e-8 or c.direction.toTuple() != (1., 0., 0.)):
            raise ValueError("Unexpected nominal stitch geometry")
        prefix = c.name + "_"
        contact_pairs += [(prefix + "bolt", prefix + "washer_inner"),
                          (prefix + "washer_inner", "leg_right_inner"),
                          ("leg_right_outer", prefix + "washer_outer"),
                          (prefix + "washer_outer", prefix + "nut"),
                          (prefix + "bolt", prefix + "washer_outer"),
                          (prefix + "bolt", prefix + "nut")]
        for ply in ("leg_right_inner", "leg_right_outer"):
            distance = bodies[prefix + "bolt"].distance(bodies[ply])
            if not math.isfinite(distance) or abs(distance - .2375) > 1e-5:
                raise ValueError("Incorrect actual bore/shank radial clearance")
        stitch_records.append({"name": c.name, "start_mm": c.start.toTuple(),
                               "axis": c.direction.toTuple(), "length_mm": c.length,
                               "grip_mm": c.grip, "bore_diameter_mm": 10.,
                               "shank_diameter_mm": c.diameter, "radial_clearance_mm": .2375,
                               "projection_past_nut_mm": c.length - (4 + c.grip + 9)})
    for first, second in contact_pairs:
        distance = bodies[first].distance(bodies[second])
        if not math.isfinite(distance) or distance < 0 or distance > DISTANCE_TOLERANCE_MM:
            raise ValueError(f"Missing nominal stack contact: {first}/{second}")
    return {"status": "VERIFIED GEOMETRY ONLY; NO MESH OR SOLVER", "limits": LIMITS,
            "candidate": frame.KEY, "body_count": len(bodies), "parts": records,
            "stitches": stitch_records, "nominal_touching_pairs": contact_pairs,
            "maximum_pair_overlap_mm3": maximum,
            "overlap_tolerance_mm3": VOLUME_TOLERANCE_MM3}


def source_snapshot():
    """Read repo-relative source bytes and reject imports from another checkout."""
    for name, module in tuple(sys.modules.items()):
        if name == "mini_moonboard" or name.startswith("mini_moonboard."):
            origin = Path(module.__file__).resolve()
            expected = REPOSITORY.joinpath(*name.split("."))
            expected = expected / "__init__.py" if origin.name == "__init__.py" else expected.with_suffix(".py")
            if origin != expected:
                raise ValueError(f"Imported source outside this checkout: {name}")
    paths = [Path(__file__).resolve(), *sorted((REPOSITORY / "mini_moonboard").glob("*.py"))]
    return {p.relative_to(REPOSITORY).as_posix(): p.read_bytes() for p in paths}


def export(bodies, parent=Path("fea/generated"), *, sources_before=None):
    """Export only to a new unique evidence directory, never published geometry."""
    initial_sources = source_snapshot()
    if sources_before is not None and sources_before != initial_sources:
        raise ValueError("Source drift during geometry preparation")
    summary = validate(bodies)
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="stitch-joint-geometry-", dir=parent))
    for name, shape in bodies.items():
        cq.exporters.export(shape, str(directory / f"{name}.step"))
    for name, contents in initial_sources.items():
        path = directory / "launch_sources" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    if source_snapshot() != initial_sources:
        raise ValueError("Source drift during geometry export; incomplete directory has no manifest")
    record = {**summary, "cadquery_version": cq.__version__,
              "source_binding": "before geometry through export" if sources_before is not None else "export interval only",
              "source_sha256": {name: hashlib.sha256(contents).hexdigest() for name, contents in initial_sources.items()},
              "step_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.step"))}}
    (directory / "geometry.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="write a unique fea/generated evidence directory")
    args = parser.parse_args()
    sources_before = source_snapshot()
    bodies = solids()
    if args.export:
        print(export(bodies, sources_before=sources_before))
    else:
        summary = validate(bodies)
        if source_snapshot() != sources_before:
            raise ValueError("Source drift during geometry preparation")
        print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
