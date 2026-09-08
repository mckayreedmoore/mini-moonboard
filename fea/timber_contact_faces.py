"""Explicit matched contact surfaces for the timber panel-edge diagnostic.

Geometry preparation only: no contact law, force recovery or capacity claim.
The N=0 common edge and ideal rim bond remain retained.
"""
import math

from fea.floor_contact import FACES
from fea.floor_contact_results import cross
from fea.panel_edge_release import release


def reconstruct(nodes, elements, legs, node_map, interface_x, origin, normal):
    """Return two matched outward-oriented face inventories from a proven release.

    Face labels are CalculiX S1..S4; normals are independently oriented away
    from the owning tetrahedron centroid, not inferred from face-node ordering.
    Both maps and the full release are checked before publishing face metadata.
    """
    revised_nodes, revised_elements, proof = release(
        nodes, elements, legs, interface_x, origin, normal)
    expected = {s: v["node_map"] for s, v in proof["legs"].items()}
    supplied = {s: {int(k): int(v) for k, v in values.items()} for s, values in node_map.items()}
    if supplied != expected:
        raise ValueError("Node map differs from complete proven release")
    owners = {}
    for e, ids in elements.items():
        for face, indices in enumerate(FACES, 1):
            key = frozenset(ids[i] for i in indices)
            owners.setdefault(key, []).append((e, face))

    def describe(e, face):
        ids = revised_elements[e]
        face_ids = [ids[i] for i in FACES[face-1]]
        points = [revised_nodes[n] for n in face_ids]
        a, b, c = points[:3]
        vector = cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
        length = math.sqrt(sum(v*v for v in vector))
        centre = [sum(revised_nodes[n][i] for n in ids[:4])/4 for i in range(3)]
        if sum(vector[i]*(centre[i]-a[i]) for i in range(3)) > 0:
            vector = [-v for v in vector]
        return {"element": e, "face": f"S{face}", "nodes": face_ids,
                "area_mm2": length/2, "outward_normal": [v/length for v in vector]}

    result = {}
    for side, sign in (("left", -1), ("right", 1)):
        owned, detached = set(legs[side]), set(expected[side])
        pairs, covered = [], set()
        for ids, adjacent in owners.items():
            if not ids & detached:
                continue
            if len(adjacent) != 2 or sum(e in owned for e, _ in adjacent) != 1:
                continue
            leg = next(item for item in adjacent if item[0] in owned)
            board = next(item for item in adjacent if item[0] not in owned)
            nvalues = [sum((nodes[n][i]-origin[i])*normal[i] for i in range(3)) for n in ids]
            if max(nvalues) > proof["tolerance_mm"]:
                raise ValueError("Contact inventory includes a rim face")
            first, second = describe(*board), describe(*leg)
            if ({tuple(revised_nodes[n]) for n in first["nodes"]} !=
                    {tuple(revised_nodes[n]) for n in second["nodes"]}):
                raise ValueError("Paired contact geometry differs")
            for entry, direction in ((first, sign), (second, -sign)):
                if math.dist(entry["outward_normal"], (direction, 0., 0.)) > 1e-10:
                    raise ValueError("Contact normals are not opposed outward X normals")
            if not math.isclose(first["area_mm2"], second["area_mm2"], rel_tol=1e-12):
                raise ValueError("Paired contact areas differ")
            covered.update(ids & detached)
            pairs.append({"panel": first, "leg": second})
        pairs.sort(key=lambda p: (p["panel"]["element"], p["panel"]["face"]))
        area = math.fsum(p["panel"]["area_mm2"] for p in pairs)
        if (covered != detached or len(pairs) != proof["legs"][side]["released_panel_face_count"]
                or not math.isclose(area, proof["legs"][side]["released_panel_area_mm2"], rel_tol=1e-12)):
            raise ValueError("Incomplete contact surface coverage")
        result[side] = {"pairs": pairs, "area_mm2": area,
                        "released_old_nodes": sorted(covered),
                        "retained_common_edge_nodes": proof["legs"][side]["retained_common_edge_nodes"]}
    return result
