"""Read-only A09 contact face/connectivity screen for prospective migration."""

import hashlib
import itertools
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-port-motion-attempt09-common-map"
# C3D10 face connectivity from the existing fea/floor_contact.py convention.
FACES = ((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
         (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6))


def cards(text):
    header, rows = None, []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if header:
                yield header, rows
            header, rows = line.upper().split(","), []
        else:
            rows.append(line.split(","))
    if header:
        yield header, rows


def main():
    mesh = (SOURCE / "mesh.inp").read_bytes()
    contact = (SOURCE / "contact-fragment.inc").read_bytes()
    nodes, elements = {}, {}
    for h, rows in cards(mesh.decode()):
        if h[0] == "*NODE":
            nodes.update({int(r[0]): tuple(map(float, r[1:])) for r in rows})
        elif h[0] == "*ELEMENT":
            assert "TYPE=C3D10" in h
            elements.update({int(r[0]): tuple(map(int, r[1:])) for r in rows})
    sets, surfaces, curvature = {}, {}, {}
    for h, rows in cards(contact.decode()):
        if h[0] == "*NSET":
            name = next(x[5:] for x in h if x.startswith("NSET="))
            sets[name] = {int(x) for r in rows for x in r if x}
        if h[0] == "*SURFACE":
            name = next(x[5:] for x in h if x.startswith("NAME="))
            owned, offsets, perpendicular = set(), [], []
            for r in rows:
                conn = elements[int(r[0])]
                face = [conn[k] for k in FACES[int(r[1][1:]) - 1]]
                owned.update(face)
                for a, b, mid in [(0, 1, 3), (1, 2, 4), (2, 0, 5)]:
                    offsets.append(math.dist(nodes[face[mid]], tuple(
                        (nodes[face[a]][k] + nodes[face[b]][k]) / 2 for k in range(3))))
                    edge = tuple(nodes[face[b]][k] - nodes[face[a]][k] for k in range(3))
                    delta = tuple(nodes[face[mid]][k] - nodes[face[a]][k] for k in range(3))
                    fraction = sum(x*y for x,y in zip(edge,delta)) / sum(x*x for x in edge)
                    perpendicular.append(math.sqrt(sum((delta[k] - fraction*edge[k])**2 for k in range(3))))
            expected_set = name.replace("WJCP_", "WJCP_N_", 1)
            assert owned == sets[expected_set], name
            surfaces[name] = owned
            curvature[name] = {"face_count": len(rows), "node_count": len(owned),
                               "maximum_midside_chord_offset_mm": max(offsets),
                               "maximum_midside_perpendicular_to_chord_mm": max(perpendicular),
                               "face_edge_occurrences_above_1e_7_mm": sum(x > 1e-7 for x in offsets)}
    slaves = {k: v for k, v in surfaces.items() if k.endswith("_S")}
    def overlaps(groups):
        return [{"a": a, "b": b, "node_ids": sorted(na & nb)}
                for (a, na), (b, nb) in itertools.combinations(sorted(groups.items()), 2) if na & nb]
    alternative = dict(slaves)
    alternative["WJCP_002_S"] = surfaces["WJCP_002_M"]
    result = {"scope": "Read-only contact connectivity screen; no solve or candidate acceptance",
              "source": str(SOURCE.relative_to(ROOT)),
              "sha256": {"mesh.inp": hashlib.sha256(mesh).hexdigest(),
                         "contact-fragment.inc": hashlib.sha256(contact).hexdigest()},
              "all_70_surface_memberships_equal_recorded_nsets": len(surfaces) == 70,
              "current_slave_overlaps": overlaps(slaves),
              "hypothetical_pair002_reversal_overlaps": overlaps(alternative),
              "surface_geometry": curvature,
              "limits": "No normals, projection, material, pairing-force equivalence, contact integration or Code_Aster mesh import checked. Midpoint and perpendicular chord offsets describe geometry; neither is a contact error or proof of a nonplanar face."}
    assert len(slaves) == 35 and len(surfaces) == 70
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
