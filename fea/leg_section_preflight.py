"""Archived curved-leg cut topology and external references; no stress/solve."""
import hashlib
import json
import math
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

from fea.floor_contact import FACES, mesh
from fea.floor_contact_results import cross
from fea.independent_leg_response import deck
from fea.independent_ply_control import resultant

ARCHIVE = Path("fea/results/independent_leg_response/evidence.tar.gz")
ARCHIVE_SHA = "476283677930a59e8c0ed202f3455fa72b67880dbfcba3a8062dcb35522dfc5a"
CUT_Z = 1400.
REFERENCE = (1266.825, 900., CUT_Z)
LIMITS = ("Geometry/topology and external-load references only. Jagged conforming cut, not a planar section. "
          "No curved-face area/Jacobian qualification, native section output, stress extraction, "
          "contact, joint demand, resistance or construction approval.")


def serialized_loads(text):
    """Read actual per-step CLOAD fields through the native 20-column bound."""
    cases, loading, seen = [], False, set()
    for line in text.splitlines():
        if line.startswith("*"):
            loading = False
            if line == "*STEP":
                cases.append(None)
            elif line.startswith("*CLOAD"):
                if line != "*CLOAD,OP=NEW" or not cases or cases[-1] is not None:
                    raise ValueError("One replacement CLOAD per step required")
                cases[-1], seen, loading = {}, set(), True
        elif loading and line.strip():
            node, axis, token = line.split(",")
            node, axis = int(node), int(axis)
            if len(token) > 20 or axis not in (1, 2, 3) or (node, axis) in seen:
                raise ValueError("Invalid serialized load field")
            force = float(token[:20])
            if not math.isfinite(force):
                raise ValueError("Nonfinite serialized load")
            cases[-1].setdefault(node, [0., 0., 0.])[axis-1] = force
            seen.add((node, axis))
    if not cases or any(c is None for c in cases):
        raise ValueError("Missing serialized step loads")
    return [{n: tuple(v) for n, v in case.items()} for case in cases]


def connected(entities, pairs):
    graph = {e: set() for e in entities}
    for a, b in pairs:
        if a in graph and b in graph:
            graph[a].add(b)
            graph[b].add(a)
    if not graph:
        raise ValueError("Empty connected selection")
    visited, pending = set(), [next(iter(graph))]
    while pending:
        e = pending.pop()
        if e not in visited:
            visited.add(e)
            pending.extend(graph[e]-visited)
    if visited != set(graph):
        raise ValueError("Disconnected selection")


def cut_topology(nodes, elements, owned, fixed, floor, selected=None):
    """Whole-element sub-body; six-node matching and oriented edge closure."""
    owned = set(owned)
    faces, edge_mids = defaultdict(list), {}
    for e in sorted(owned):
        ids = elements[e]
        if len(ids) != 10 or len(set(ids)) != 10:
            raise ValueError("Invalid quadratic element")
        for face, indices in enumerate(FACES, 1):
            ns = tuple(ids[i] for i in indices)
            for i, j, mid in ((0, 1, 3), (1, 2, 4), (2, 0, 5)):
                edge = tuple(sorted((ns[i], ns[j])))
                if edge in edge_mids and edge_mids[edge] != ns[mid]:
                    raise ValueError("Nonconforming quadratic edge")
                edge_mids[edge] = ns[mid]
            faces[tuple(sorted(ns))].append((e, face, ns))
    if any(len(v) not in (1, 2) for v in faces.values()):
        raise ValueError("Nonmanifold quadratic face")
    selected = ({e for e in owned if sum(nodes[n][2] for n in elements[e][:4])/4 < CUT_Z}
                if selected is None else set(selected))
    if not selected < owned:
        raise ValueError("Proper sub-body required")
    selected_nodes = {n for e in selected for n in elements[e]}
    if selected_nodes & set(fixed) or not set(floor) <= selected_nodes:
        raise ValueError("Cut includes fixture or omits floor")
    neighbours = [(v[0][0], v[1][0]) for v in faces.values() if len(v) == 2]
    connected(selected, neighbours)
    connected(owned-selected, neighbours)
    cut, boundary, deviations = [], [], []
    for entries in faces.values():
        lower = [v for v in entries if v[0] in selected]
        if len(lower) != 1:
            continue
        e, face, ns = lower[0]
        a, b, c = [nodes[n] for n in ns[:3]]
        normal = cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
        opposite = next(n for n in elements[e][:4] if n not in ns[:3])
        determinant = sum(normal[i]*(nodes[opposite][i]-a[i]) for i in range(3))
        if not math.isfinite(determinant) or determinant == 0:
            raise ValueError("Degenerate corner face orientation")
        # Outward winding of the corner skeleton; not curved-normal integration.
        outward = ns if determinant < 0 else tuple(ns[i] for i in (0, 2, 1, 5, 4, 3))
        boundary.append(outward)
        if len(entries) == 2:
            upper = next(v for v in entries if v[0] not in selected)
            ua, ub, uc = [nodes[n] for n in upper[2][:3]]
            upper_normal = cross([ub[i]-ua[i] for i in range(3)], [uc[i]-ua[i] for i in range(3)])
            if sum(normal[i]*upper_normal[i] for i in range(3)) >= 0:
                raise ValueError("Opposed cut winding differs")
            cut.append({"lower": [e, face], "upper": list(upper[:2]), "outward_nodes": outward})
            for i, j, mid in ((0, 1, 3), (1, 2, 4), (2, 0, 5)):
                deviations.append(math.dist(nodes[ns[mid]], [(nodes[ns[i]][k]+nodes[ns[j]][k])/2 for k in range(3)]))
    edges = Counter((ns[i], ns[j], ns[mid]) for ns in boundary for i, j, mid in ((0, 1, 3), (1, 2, 4), (2, 0, 5)))
    if not edges or any(n != 1 or edges[j, i, mid] != 1 for (i, j, mid), n in edges.items()):
        raise ValueError("Sub-body boundary is not closed")
    cut_edges = defaultdict(list)
    for i, item in enumerate(cut):
        ns = item["outward_nodes"]
        for a, b, mid in ((0, 1, 3), (1, 2, 4), (2, 0, 5)):
            cut_edges[tuple(sorted((ns[a], ns[b])))+(ns[mid],)].append(i)
    if any(len(v) not in (1, 2) for v in cut_edges.values()):
        raise ValueError("Nonmanifold cut edge")
    connected(range(len(cut)), [v for v in cut_edges.values() if len(v) == 2])
    if not deviations or max(deviations) < .1:
        raise ValueError("Cut does not sample genuinely curved midsides")
    return {"selected_elements": sorted(selected), "cut": cut, "boundary_face_count": len(boundary),
            "cut_face_count": len(cut), "maximum_cut_midside_deviation_mm": max(deviations),
            "selected_node_count": len(selected_nodes)}


def preflight(archive=ARCHIVE):
    with Path(archive).open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != ARCHIVE_SHA:
            raise ValueError("Selected actual-leg archive differs")
    rows = {}
    with tarfile.open(archive) as bundle:
        for size in (40, 25):
            source = bundle.extractfile(f"mesh{size}.inp").read().decode()
            metadata = json.load(bundle.extractfile(f"mesh{size}.json"))
            actual = bundle.extractfile(f"independent{size}.inp").read().decode()
            rebuilt, context = deck(source, metadata, True)
            if rebuilt != actual:
                raise ValueError("Actual serialized response deck differs")
            nodes, elements = mesh(actual)
            ply = context["plies"]["inner"]
            geometry = cut_topology(nodes, elements, metadata["part_elements"]["inner"],
                                    ply["fixed"], ply["weights_mm2"])
            shifted = {n: tuple(p[i]-REFERENCE[i] for i in range(3)) for n, p in nodes.items()}
            loads = []
            ply_nodes = set(ply["nodes"])
            for case, parsed in zip(context["cases"], serialized_loads(actual), strict=True):
                if parsed != case["loads"]:
                    raise ValueError("Serialized load vectors differ from declared context")
                applied = {n: f for n, f in parsed.items() if n in ply_nodes}
                if not set(applied) <= set(ply["weights_mm2"]):
                    raise ValueError("Applied load is not exclusively on retained floor")
                external = resultant(shifted, applied)
                loads.append({"sharing": case["sharing"], "axis": case["axis"],
                              "external_force_moment": external,
                              "expected_upper_on_lower_force_moment": [-v for v in external]})
            rows[str(size)] = {**geometry, "loads": loads,
                              "deck_sha256": hashlib.sha256(actual.encode()).hexdigest()}
    return {"limits": LIMITS, "qualified": False, "archive_sha256": ARCHIVE_SHA,
            "selection": "inner ply; mean corner Z < 1400 mm", "reference_mm": REFERENCE,
            "meshes": rows}


if __name__ == "__main__":
    print(json.dumps(preflight(), indent=2, allow_nan=False))
