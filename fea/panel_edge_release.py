"""Pure-mesh zero-gap panel-edge release, retaining the ideal rim connection."""
import math
from collections import Counter

from fea.floor_contact import FACES
from fea.floor_contact_results import cross
from fea.solve_bearing_frame import straight_mesh_volume

LIMITS = ("Zero-gap traction-free leg/panel interface; no unilateral contact. "
          "Interpenetration is possible; this is not a conservative bound. "
          "N=0 common-edge nodes and the nonzero-area rim bond remain shared. "
          "No individual bolt-force or joint-capacity qualification.")


def release(nodes, elements, legs, interface_x, origin, normal, *,
            panel_thickness=18.25625, floor_nodes=(), load_nodes=(), tolerance=1e-5):
    """Return (nodes, elements, metadata); input dictionaries remain untouched.

    ``legs`` maps a side name to the complete element-ID set of BOTH leg plies.
    N is signed distance from ``origin`` along the unit board-back ``normal``.
    Only matching six-node C3D10 interface faces are accepted; a face straddling
    N=0 requires a conforming partition, not an increased classification tolerance.
    """
    if (len(origin) != 3 or len(normal) != 3 or not all(map(math.isfinite, (*origin, *normal, panel_thickness, tolerance)))
            or panel_thickness <= 0 or not 0 < tolerance <= 1e-4
            or not math.isclose(math.sqrt(sum(v*v for v in normal)), 1., abs_tol=1e-10, rel_tol=0)
            or not legs or set(legs) != set(interface_x)
            or not all(map(math.isfinite, interface_x.values()))):
        raise ValueError("Invalid release geometry or ownership inputs")
    if any(not isinstance(n, int) or n <= 0 for n in nodes):
        raise ValueError("Positive integer node IDs required")
    volume, _ = straight_mesh_volume(nodes, elements)
    if any(not set(ids) or not set(ids) <= elements.keys() for ids in legs.values()):
        raise ValueError("Missing leg-owned elements")
    counts = Counter(e for ids in legs.values() for e in ids)
    if any(count != 1 for count in counts.values()):
        raise ValueError("Leg ownership overlaps or duplicates")
    protected = set(floor_nodes) | set(load_nodes)
    if not protected <= nodes.keys():
        raise ValueError("Unknown protected load/floor node")
    ncoord = {n: sum((p[i]-origin[i])*normal[i] for i in range(3)) for n, p in nodes.items()}
    all_faces = {}
    for e, ids in elements.items():
        for indices in FACES:
            face = tuple(ids[i] for i in indices)
            all_faces.setdefault(frozenset(face), []).append((e, face))
    if any(len(owners) > 2 for owners in all_faces.values()):
        raise ValueError("Non-manifold mesh face")
    revised_nodes, revised_elements = dict(nodes), dict(elements)
    next_id, metadata = max(nodes)+1, {}
    for side in sorted(legs):
        owned = set(legs[side])
        leg_nodes = {n for e in owned for n in elements[e]}
        other_nodes = {n for e, ids in elements.items() if e not in owned for n in ids}
        shared = leg_nodes & other_nodes
        if not shared or any(abs(nodes[n][0]-interface_x[side]) > tolerance for n in shared):
            raise ValueError("Unexpected shared leg interface")
        if any(ncoord[n] < -panel_thickness-tolerance for n in shared):
            raise ValueError("Shared node outside panel/rim band")
        detached = sorted(n for n in shared if ncoord[n] < -tolerance)
        if not detached or set(detached) & protected:
            raise ValueError("Missing release nodes or protected node would be duplicated")
        panel_faces, rim_faces = [], []
        for owners in all_faces.values():
            if len(owners) != 2 or sum(e in owned for e, _ in owners) != 1:
                continue
            e, face = next((e, face) for e, face in owners if e in owned)
            if any(abs(nodes[n][0]-interface_x[side]) > tolerance for n in face):
                raise ValueError("Interface face outside declared plane")
            values = [ncoord[n] for n in face]
            a, b, c = [nodes[n] for n in face[:3]]
            area = math.sqrt(sum(v*v for v in cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])))/2
            if area <= 0:
                raise ValueError("Degenerate interface face")
            if min(values) < -tolerance and max(values) <= tolerance:
                panel_faces.append((e, face, area))
            elif min(values) >= -tolerance:
                rim_faces.append((e, face, area))
            else:
                raise ValueError("Interface face straddles N=0; conforming partition required")
        if not panel_faces or not rim_faces:
            raise ValueError("Both finite-area panel and rim interfaces required")
        mapping = {n: next_id+i for i, n in enumerate(detached)}
        next_id += len(mapping)
        for old, new in mapping.items():
            revised_nodes[new] = nodes[old]
        for e in owned:
            revised_elements[e] = tuple(mapping.get(n, n) for n in elements[e])
        if any(all(mapping.get(n, n) in other_nodes for n in face) for _, face, _ in panel_faces):
            raise ValueError("Finite-area panel face remains fully tied")
        if any(any(n in mapping for n in face) for _, face, _ in rim_faces):
            raise ValueError("Rim interface was detached")
        metadata[side] = {"node_map": mapping, "released_panel_face_count": len(panel_faces),
            "released_panel_area_mm2": sum(a for _, _, a in panel_faces),
            "retained_rim_face_count": len(rim_faces), "retained_rim_area_mm2": sum(a for _, _, a in rim_faces),
            "retained_common_edge_nodes": sorted(n for n in shared if abs(ncoord[n]) <= tolerance)}
    if any(tuple(revised_nodes[n] for n in revised_elements[e]) != tuple(nodes[n] for n in ids)
           for e, ids in elements.items()):
        raise ValueError("Release changed physical element coordinates")
    new_volume, _ = straight_mesh_volume(revised_nodes, revised_elements)
    if new_volume != volume:
        raise ValueError("Release changed material volume")
    return revised_nodes, revised_elements, {"limits": LIMITS, "legs": metadata,
        "volume_mm3": volume, "tolerance_mm": tolerance, "added_node_count": len(revised_nodes)-len(nodes)}
