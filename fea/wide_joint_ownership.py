"""CAD-audited ownership on the current wide mesh, never historical node IDs."""
import json
import math

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks, cross
from fea.solve_bearing_frame import straight_mesh_volume
from fea.timber_base_demand import partition_floor
from fea.timber_joint_demand import TOL, ownership, select_leg

KEY = "wide-principal-development"
LIMITS = (
    "Current wide-mesh ownership only. Ideal-bonded legs transfer through rim AND "
    "upper-panel edge, not isolated bolts. Base contains header, six posts, both "
    "kickers and gussets; fixed floor includes kicker. No joint resistance or approval."
)
SOURCE_FILES = ("fea/wide_joint_ownership.py", "fea/timber_joint_demand.py",
                "fea/timber_base_demand.py", "fea/solve_bearing_frame.py",
                "fea/floor_contact.py", "fea/floor_contact_results.py",
                "mini_moonboard/box_exports.py")


def mesh_moments(nodes, elements):
    volume, midpoint = straight_mesh_volume(nodes, elements)
    moments = [[], [], []]
    for ids in elements.values():
        points = [nodes[n] for n in ids[:4]]
        a, b, c = [[p[i]-points[0][i] for i in range(3)] for p in points[1:]]
        v = sum(x*y for x, y in zip(a, cross(b, c), strict=True))/6
        for i in range(3):
            moments[i].append(v*sum(p[i] for p in points)/4)
    return volume, [math.fsum(values)/volume for values in moments], midpoint


def base_member_names():
    return {"base_header", "kicker_left", "kicker_right", "timber_base_gusset_left", "timber_base_gusset_right",
            "base_post_outer_left", "base_post_outer_right", *{
                f"base_post_center_{side}_{end}" for side in ("left", "right") for end in ("front", "rear")}}


def recover_geometry(nodes, elements, feet, load_nodes):
    """Inspect current CAD against complete mesh elements and all applied nodes."""
    import cadquery as cq

    from mini_moonboard import box_frame as b
    from mini_moonboard import wide_frame as frame
    from mini_moonboard.box_exports import exact_bounds

    if frame.KEY != KEY or not set(load_nodes) <= nodes.keys():
        raise ValueError("Wrong candidate or unknown load nodes")
    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    axes = ((1., 0., 0.), (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized().toTuple(), b.normal().toTuple())
    legs = {}
    for side, sign in (("left", -1), ("right", 1)):
        plies = [raw[f"leg_{side}_{layer}"] for layer in ("inner", "outer")]
        bounds = exact_bounds(cq.Compound.makeCompound(plies))
        box = [getattr(bounds, axis+end) for end in ("min", "max") for axis in "xyz"]
        cached = {}

        def contains(point, cached=cached, plies=plies):
            key = tuple(point)
            if key not in cached:
                cached[key] = any(p.isInside(cq.Vector(*point), TOL) for p in plies)
            return cached[key]

        chosen = select_leg(nodes, elements, box, contains)
        members = {name: raw[name] for name in (f"base_side_{side}", f"main_upper_{side}")}
        ids, shared, supports = ownership(nodes, elements, chosen, feet, load_nodes,
            lambda p, sign=sign, members=members: abs(p[0]-sign*b.HALF) < TOL and
            any(s.isInside(cq.Vector(*p), TOL) for s in members.values()), contains)
        groups = {name: sorted(n for n in shared if shape.isInside(cq.Vector(*nodes[n]), TOL))
                  for name, shape in members.items()}
        if any(not ns for ns in groups.values()):
            raise ValueError("Expected both rim and upper-panel edge interfaces")
        volume, centre, midpoint = mesh_moments({n: nodes[n] for n in ids}, chosen)
        cad_volume = sum(p.Volume() for p in plies)
        cad_centre = [sum(p.Volume()*p.Center().toTuple()[i] for p in plies)/cad_volume for i in range(3)]
        if abs(volume/cad_volume-1) > .001 or math.dist(centre, cad_centre) > 1.:
            raise ValueError("Selected wide leg differs from physical volume or centroid")
        bolts = [c for c in frame.connections() if c.name.startswith(f"analysis_leg_wall_bolt_{side}_")]
        if len(bolts) != 4:
            raise ValueError("Expected four current leg-to-rim bolt axes")
        reference = [sign*b.HALF, *[sum(c.start.toTuple()[i] for c in bolts)/4 for i in (1, 2)]]
        legs[side] = {"reference_world_mm": reference, "element_ids": sorted(chosen),
            "element_count": len(chosen), "node_count": len(ids), "floor_nodes": sorted(supports),
            "shared_interface_node_count": len(shared), "shared_nodes_by_board_member": groups,
            "mesh_volume_mm3": volume, "cad_volume_mm3": cad_volume,
            "mesh_centroid_mm": centre, "cad_centroid_mm": cad_centre,
            "maximum_midpoint_error_mm": midpoint,
            "interface_note": "Aggregate rim plus upper-panel edge transfer; no bolt or interface split."}
    selected_names = {n for n in raw if n == "base_header" or n.startswith(("base_post_", "kicker_", "timber_base_gusset_"))}
    if selected_names != base_member_names():
        raise ValueError("Expected exact eleven-member wide base")
    group = {n: raw[n] for n in selected_names}
    contact = {n: s for n, s in group.items() if n.startswith(("base_post_", "kicker_"))}
    contains = lambda shape: lambda p: shape.isInside(cq.Vector(*p), TOL)
    supports, by_member = partition_floor(nodes, feet,
        {s: legs[s]["floor_nodes"] for s in legs}, {n: contains(s) for n, s in contact.items()})
    if any(contains(s)(nodes[n]) for n in load_nodes for s in group.values()):
        raise ValueError("Climbing load belongs to base free body")
    base = {"members": sorted(group), "reference_world_mm": raw["base_header"].Center().toTuple(),
            "floor_nodes": sorted(supports), "floor_nodes_by_member": by_member,
            "floor_note": "Unique union includes kicker and six posts; boundary nodes may occur in multiple member lists.",
            "cad_member_volume_mm3": {n: s.Volume() for n, s in group.items()}}
    return {"candidate": KEY, "limits": LIMITS, "local_axes_world": axes, "legs": legs, "base": base}


def recover(extra_load_nodes=()):
    """Authenticate current wide evidence and return metadata, nodes, DAT, sources."""
    from fea.solve_easy_frame import digest
    from fea.wide_asymmetric import authenticated_inputs, unchanged

    accepted, deck, dat, sources = authenticated_inputs()
    for path in SOURCE_FILES:
        current = digest(path)
        if path in sources and sources[path] != current:
            raise ValueError("Conflicting ownership source")
        sources[path] = current
    nodes, elements = mesh(deck)
    parsed = blocks(dat)
    metadata = recover_geometry(nodes, elements, set(parsed["forces", "FEET", 1.]),
                                set(accepted["load_nodes"]) | set(extra_load_nodes))
    unchanged(sources)
    return json.loads(json.dumps(metadata, allow_nan=False)), nodes, parsed, sources
