"""Conditional aggregate leg/board actions from fixed-floor bulk evidence."""
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks, cross
from fea.leg_joint_demand import local_components
from fea.publish_bearing_structural import validate_metadata
from fea.solve_bearing_frame import straight_mesh_volume
from fea.solve_easy_frame import audit, digest

DIRECTORY = Path("fea/results/timber-base")
SOURCE = DIRECTORY/"mesh40.json"
OUTPUT = Path("fea/results/timber-joint-demand.json")
TOL = 1e-5
LIMITS = (
    "Conditional aggregate leg-on-board resultants from fixed-XYZ-floor, isotropic "
    "ideal-bonded timber; zero gravity in these load cases. Both leg plies are "
    "one free body. The inset legs touch both rim and upper-panel edges, all "
    "ideally bonded in this mesh; this is not an isolated rim/bolt demand. "
    "Not actual unanchored demand, per-bolt/ply sharing, joint "
    "resistance, strength or approval. Original coordinates apply to this linear "
    "small-displacement solve; force N and moment Nmm."
)


def select_leg(nodes, elements, bounds, contains):
    """Select whole elements in a leg slab/profile, excluding low base gussets."""
    if len(bounds) != 6 or not all(map(math.isfinite, bounds)):
        raise ValueError("Finite leg bounds required")
    lower, upper = bounds[:3], bounds[3:]
    chosen = {}
    for tag, ids in elements.items():
        if len(ids) != 10 or len(set(ids)) != 10 or not set(ids) <= nodes.keys():
            raise ValueError("Invalid ten-node element connectivity")
        points = [nodes[n] for n in ids]
        # The centroid avoids admitting rim elements that only share a face.
        centre = [sum(p[i] for p in points[:4])/4 for i in range(3)]
        if not all(lower[i]-TOL <= centre[i] <= upper[i]+TOL for i in range(3)):
            continue
        if not all(all(lower[i]-TOL <= p[i] <= upper[i]+TOL for i in range(3))
                   and contains(p) for p in points):
            raise ValueError("Candidate element crosses the leg boundary or leaves its profile")
        chosen[tag] = ids
    if not chosen:
        raise ValueError("Missing leg elements")
    return chosen


def ownership(nodes, elements, chosen, feet, top, interface, floor_contains):
    ids = {n for row in chosen.values() for n in row}
    others = {n for tag, row in elements.items() if tag not in chosen for n in row}
    shared = ids & others
    supports = ids & set(feet)
    expected = {n for n in feet if floor_contains(nodes[n])}
    if not shared or any(not interface(nodes[n]) for n in shared):
        raise ValueError("Leg shares nodes outside its declared board interface")
    if not supports or supports != expected or ids & set(top):
        raise ValueError("Leg floor/load ownership differs")
    return ids, shared, supports


def resultant(nodes, reaction, reference):
    """Floor reaction equals leg-on-board action with no leg gravity/applied load."""
    if (not nodes or nodes.keys() != reaction.keys() or len(reference) != 3
            or not all(math.isfinite(v) for row in [reference, *nodes.values(), *reaction.values()]
                       for v in row)
            or any(len(row) != 3 for row in [*nodes.values(), *reaction.values()])):
        raise ValueError("Finite complete three-component free-body inputs required")
    force = [math.fsum(v[i] for v in reaction.values()) for i in range(3)]
    moments = [cross([p[i]-reference[i] for i in range(3)], reaction[n]) for n, p in nodes.items()]
    return force+[math.fsum(m[i] for m in moments) for i in range(3)]


def authenticated_inputs():
    row = json.loads(SOURCE.read_text())
    if (row.get("candidate") != "timber-base-development" or row.get("mesh_size_mm") != 40
            or not row.get("source_sha256")):
        raise ValueError("Require source-bound current timber evidence")
    sources = dict(row["source_sha256"])
    sources.update(row["publisher_source_sha256"])
    if any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Frozen source changed")
    if set(row["replay_archives"]) != {"mesh40"+suffix+".gz" for suffix in
                                       (".inp", ".dat", ".context.json", ".log", ".sta")}:
        raise ValueError("Incomplete expected mesh40 archives")
    decoded = {}
    for name, hashes in row["replay_archives"].items():
        path = DIRECTORY/name
        payload = path.read_bytes()
        data = gzip.decompress(payload)
        if (digest(path) != hashes["gzip_sha256"]
                or hashlib.sha256(data).hexdigest() != hashes["uncompressed_sha256"]
                or hashes["uncompressed_sha256"] != row["evidence_sha256"][hashes["original_name"]]):
            raise ValueError("Archived solver evidence changed")
        decoded[name.removesuffix(".gz")] = data.decode()
        sources[str(path)] = digest(path)
    deck, dat = decoded["mesh40.inp"], decoded["mesh40.dat"]
    validate_metadata(row, deck, json.loads(decoded["mesh40.context.json"]))
    replay = audit(deck, dat, row["frozen_geometry"])
    if any(json.loads(json.dumps(value)) != row[key] for key, value in replay.items()):
        raise ValueError("Published global equilibrium replay differs")
    for name in (str(SOURCE), "fea/timber_joint_demand.py", "fea/leg_joint_demand.py"):
        sources[name] = digest(name)
    return row, deck, dat, sources


def main():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite joint-demand evidence")
    row, deck, dat, sources = authenticated_inputs()
    import cadquery as cq

    from mini_moonboard import box_frame as b
    from mini_moonboard import timber_frame as frame
    from mini_moonboard.box_exports import exact_bounds

    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    nodes, elements = mesh(deck)
    parsed = blocks(dat)
    axes = ((1., 0., 0.), (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized().toTuple(), b.normal().toTuple())
    legs = {}
    for side, sign in (("left", -1), ("right", 1)):
        plies = [raw[f"leg_{side}_{layer}"] for layer in ("inner", "outer")]
        shape = cq.Compound.makeCompound(plies)
        bounds = exact_bounds(shape)
        limits = [getattr(bounds, axis+end) for end in ("min", "max") for axis in "xyz"]
        cached = {}

        def contains(point, cached=cached, plies=plies):
            key = tuple(point)
            if key not in cached:
                cached[key] = any(p.isInside(cq.Vector(*point), TOL) for p in plies)
            return cached[key]

        selected = select_leg(nodes, elements, limits, contains)
        feet = set(parsed[("forces", "FEET", 1.)])
        interface_members = {name: raw[name] for name in
                             (f"base_side_{side}", f"main_upper_{side}")}
        ids, shared, supports = ownership(nodes, elements, selected, feet, row["load_nodes"],
            lambda p, sign=sign, members=interface_members: abs(p[0]-sign*b.HALF) < TOL and
            any(shape.isInside(cq.Vector(*p), TOL) for shape in members.values()),
            contains)
        interface_nodes = {name: sorted(n for n in shared if shape.isInside(cq.Vector(*nodes[n]), TOL))
                           for name, shape in interface_members.items()}
        if any(not group for group in interface_nodes.values()):
            raise ValueError("Expected both rim and upper-panel contacts for current inset leg")
        subset = {n: nodes[n] for n in ids}
        volume, midpoint = straight_mesh_volume(subset, selected)
        cad_volume = sum(p.Volume() for p in plies)
        if abs(volume/cad_volume-1) > .001:
            raise ValueError("Selected leg mesh volume differs from actual leg")
        first_moments = [[], [], []]
        for connectivity in selected.values():
            corners = [nodes[n] for n in connectivity[:4]]
            a, c, d = [[p[i]-corners[0][i] for i in range(3)] for p in corners[1:]]
            determinant = sum(x*y for x, y in zip(a, cross(c, d), strict=True))
            for i in range(3):
                first_moments[i].append(determinant/6*sum(p[i] for p in corners)/4)
        centre = [math.fsum(values)/volume for values in first_moments]
        cad_centre = [sum(p.Volume()*p.Center().toTuple()[i] for p in plies)/cad_volume for i in range(3)]
        if math.dist(centre, cad_centre) > 1.:
            raise ValueError("Selected leg mesh centroid differs from actual leg")
        bolts = [c for c in frame.connections() if c.name.startswith(f"analysis_leg_wall_bolt_{side}_")]
        if len(bolts) != 4:
            raise ValueError("Expected four actual leg-wall bolt axes")
        reference = [sign*b.HALF, *[sum(c.start.toTuple()[i] for c in bolts)/4 for i in (1, 2)]]
        cases = []
        for step, case in enumerate(row["frozen_geometry"]["audited_cases"], 1):
            reactions = parsed[("forces", "FEET", float(step))]
            if reactions.keys() != feet:
                raise ValueError("Reaction support inventory changes between cases")
            world = resultant({n: nodes[n] for n in supports}, {n: reactions[n] for n in supports}, reference)
            cases.append({"case": case["name"], "leg_on_board_world_n_nmm": world,
                "board_on_leg_world_n_nmm": [-v for v in world],
                "leg_on_board_local_xsn_n_nmm": local_components(world, axes)})
        legs[side] = {"reference_world_mm": reference, "element_count": len(selected),
            "node_count": len(ids), "shared_interface_node_count": len(shared),
            "shared_nodes_by_board_member": interface_nodes,
            "interface_note": "Rim and upper-panel edge share the transfer; boundary nodes may belong to both. No interface force split is recovered.",
            "floor_nodes": sorted(supports), "mesh_volume_mm3": volume,
            "cad_volume_mm3": cad_volume, "mesh_centroid_mm": centre, "cad_centroid_mm": cad_centre,
            "maximum_midpoint_error_mm": midpoint, "cases": cases}
    if set(legs["left"]["floor_nodes"]) & set(legs["right"]["floor_nodes"]):
        raise ValueError("Leg floor patches overlap")
    if any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Source changed during recovery")
    report = {"candidate": frame.KEY, "limits": LIMITS, "local_axes_world": axes,
              "source_sha256": sources, "legs": legs}
    with OUTPUT.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
