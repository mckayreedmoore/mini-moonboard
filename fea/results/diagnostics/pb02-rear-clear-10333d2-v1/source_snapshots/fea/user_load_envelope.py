"""Rigid-body support-polygon sensitivities, not contact FEA or a user rating."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

GRAVITY = 9.80665
LB_KG = 0.45359237
HISTORICAL_OUTPUT = Path("fea/results/hybrid/user_load_envelope.json")


def output_path(sizes, output):
    if "2x8-shallow" in sizes and (output is None or output.resolve() == HISTORICAL_OUTPUT.resolve()):
        raise ValueError("The shallow candidate requires --output to a separate, nonhistorical report")
    return HISTORICAL_OUTPUT if output is None else output


def hull(points):
    """Counterclockwise convex hull of actual coplanar floor-contact vertices."""
    points = sorted({tuple(p) for p in points})
    if len(points) < 3 or any(len(p) != 2 or not all(map(math.isfinite, p)) for p in points):
        raise ValueError("at least three finite floor points required")
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    def chain(items):
        result = []
        for p in items:
            while len(result) >= 2 and cross(result[-2], result[-1], p) <= 1e-6:
                result.pop()
            result.append(p)
        return result
    result = chain(points)[:-1]+chain(reversed(points))[:-1]
    if len(result) < 3:
        raise ValueError("floor polygon must have positive area")
    return result


def edge_screen(polygon, centre_xy, mass_kg, load_xyz, downward_n, horizontal_n, direction=None):
    """Evaluate every edge; None direction maximizes demand over ALL azimuths.

    For each CCW edge its left normal points inward. Live edge moment is
    D*distance(load) + z*dot(H,inward); weight moment is W*distance(CG).
    Worst horizontal force is exactly outward normal, not an angular sample.
    """
    values = (*centre_xy, mass_kg, *load_xyz, downward_n, horizontal_n)
    if not all(map(math.isfinite, values)) or mass_kg <= 0 or min(downward_n, horizontal_n, load_xyz[2]) < 0:
        raise ValueError("finite positive mass and nonnegative loads/height required")
    polygon = hull(polygon)
    if direction is not None:
        if len(direction) != 2 or not all(map(math.isfinite, direction)) or math.hypot(*direction) == 0:
            raise ValueError("finite nonzero horizontal direction required")
        norm = math.hypot(*direction)
        direction = tuple(v/norm for v in direction)
    rows = []
    for index, (a, b) in enumerate(zip(polygon, polygon[1:]+polygon[:1], strict=True)):
        length = math.dist(a, b)
        inward = ((a[1]-b[1])/length, (b[0]-a[0])/length)
        def distance(point, a=a, inward=inward):
            return sum((v-origin)*n for v, origin, n in zip(point[:2], a, inward, strict=True))
        dead = mass_kg*GRAVITY*distance(centre_xy)
        if dead <= 0:
            raise ValueError("unloaded centroid must lie strictly inside support polygon")
        force_direction = direction if direction is not None else tuple(-v for v in inward)
        live = downward_n*distance(load_xyz)+load_xyz[2]*horizontal_n*sum(
            d*n for d, n in zip(force_direction, inward, strict=True))
        rows.append({"edge": index, "vertices_mm": [a, b],
            "horizontal_direction_xy": force_direction, "dead_restoring_nmm": dead,
            "live_signed_restoring_nmm": live, "net_restoring_nmm": dead+live,
            "factor": dead/-live if live < 0 else None})
    return rows


def envelope(state, locations, weights=(250, 300)):
    """Accept an explicit CAD state, so no unbuilt candidate is fabricated."""
    if not weights or any(not math.isfinite(weight) or weight <= 0 for weight in weights):
        raise ValueError("At least one finite positive climber weight is required")
    rows = []
    for pounds, multiplier, mass_scale, offset, horizontal in itertools.product(
            weights, (1, 2), (0.8, 1.0), (0, 50, 100), (0, 300)):
        mass = state["mass_kg"]*mass_scale
        downward = pounds*LB_KG*GRAVITY*multiplier
        edges = {}
        for label, point, outward in locations:
            position = tuple(p+offset*n for p, n in zip(point, outward, strict=True))
            for item in edge_screen(state["support_polygon_mm"], state["centre_xy_mm"],
                                    mass, position, downward, horizontal):
                item = dict(item, hold=label, load_position_mm=position)
                old = edges.get(item["edge"])
                if old is None or item["net_restoring_nmm"] < old["net_restoring_nmm"]:
                    edges[item["edge"]] = item
        governing = min(edges.values(), key=lambda r: math.inf if r["factor"] is None else r["factor"])
        net = min(r["net_restoring_nmm"] for r in edges.values())
        rows.append({"climber_lb": pounds, "weight_multiplier": multiplier,
            "mass_scale": mass_scale, "hold_standoff_mm": offset, "horizontal_n": horizontal,
            "downward_n": downward, "governing": governing, "edges": list(edges.values()),
            "minimum_net_restoring_nmm": net,
            "translational_friction_demand": horizontal/(mass*GRAVITY+downward),
            "status": "TIP DEMAND" if net < 0 else "BELOW 1.5 SCREEN" if
                governing["factor"] is not None and governing["factor"] < 1.5 else "MEETS MOMENT SCREEN ONLY"})
    return rows


def cad_state(size):
    from fea.prepare_hybrid_frame import candidate_parts
    parts = [p for p in candidate_parts(size, size != "2x8") if size != "2x8" or not p.name.startswith("angle_")]
    masses = [p.shape.Volume()/1e9*(7850 if p.name.startswith("angle_") else 600) for p in parts]
    mass = sum(masses)
    centre = [sum(m*p.shape.centerOfMass(p.shape).toTuple()[i] for m, p in zip(masses, parts, strict=True))/mass for i in (0, 1)]
    points = [v.Center().toTuple()[:2] for p in parts for face in p.shape.Faces()
              if abs(face.BoundingBox().zmin) < 1e-5 and abs(face.BoundingBox().zmax) < 1e-5
              for v in face.Vertices()]
    source = Path(f"fea/results/hybrid/{size}/stability.json")
    baseline = None
    if source.exists():
        saved = json.loads(source.read_text())
        if abs(saved["mass_kg"]-mass) > 1e-5 or abs(saved["centre_y_mm"]-centre[1]) > 1e-5:
            raise ValueError("published baseline no longer matches CAD")
        mass, centre[1] = saved["mass_kg"], saved["centre_y_mm"]
        baseline = {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    return {"mass_kg": mass, "centre_xy_mm": centre, "support_polygon_mm": hull(points),
            "inventory_warning": "Undrilled timber only; incompatible angles and all hardware omitted. Hypothetical incomplete construction, not a complete 2x8 candidate." if size == "2x8" else "Drilled timber and custom angles; fasteners, holds, glue and LEDs omitted.",
            "baseline": baseline}


def hold_locations():
    from mini_moonboard import box_frame as b
    from mini_moonboard.panel_grid import kicker_foothold_datums, main_tnut_datums
    locations = [(label, b.point(x-b.HALF, s, -18).toTuple(), (-b.normal()).toTuple())
                 for label, (x, s) in main_tnut_datums().items()]
    locations += [("kicker_"+label, (x-b.HALF, -18, b.V1_KICKER_HEIGHT_MM+s), (0, 1, 0))
                  for label, (x, s) in kicker_foothold_datums().items()]
    return locations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", choices=("2x8", "2x8-shallow", "2x10", "2x12"), default=["2x8", "2x10", "2x12"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--weights", nargs="+", type=float, default=[250, 300])
    args = parser.parse_args()
    try:
        target = output_path(args.sizes, args.output)
    except ValueError as error:
        parser.error(str(error))
    sources = ("fea/user_load_envelope.py", "mini_moonboard/hybrid_frame.py",
               "mini_moonboard/hybrid.py", "mini_moonboard/box_frame.py", "mini_moonboard/panel_grid.py", "fea/prepare_hybrid_frame.py")
    if "2x8-shallow" in args.sizes:
        sources += ("mini_moonboard/shallow_frame.py",)
    report = {"assumptions": "One climber, 250 lb intended limit; 300 lb sensitivity, not a rating. Static and 2x gravity force; 300 N horizontal all azimuths illustrative, not prescribed dynamics. CAD floor support convex hull, rigid body; uniform mass scaling freezes CG. No joint flexibility, floor compliance, yaw equilibrium/friction distribution, anchors, ballast, strengths or approval.",
              "climber_weights_lb": args.weights,
              "source_sha256": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
              "candidates": {}}
    for size in args.sizes:
        state = cad_state(size)
        report["candidates"][size] = {"state": state, "cases": envelope(state, hold_locations(), args.weights)}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(target)


if __name__ == "__main__":
    main()
