"""Reconstruct CAD-audited leg ownership and check a release without solving."""
import json
import math
from collections import defaultdict
from pathlib import Path

from fea.floor_contact import mesh
from fea.floor_contact_results import cross
from fea.panel_edge_release import release
from fea.solve_bearing_frame import straight_mesh_volume
from fea.timber_asymmetric import unchanged
from fea.timber_joint_demand import authenticated_inputs
from fea.timber_structural import locations

REPORT = Path("fea/results/timber-joint-demand.json")


def recover(nodes, elements, leg):
    """Flood-fill from known feet without traversing the audited board interface."""
    shared = set().union(*map(set, leg["shared_nodes_by_board_member"].values()))
    floor = set(leg["floor_nodes"])
    if not shared or not floor or shared & floor or not (shared | floor) <= nodes.keys():
        raise ValueError("Invalid saved leg interface/floor inventory")
    adjacency = defaultdict(list)
    for e, ids in elements.items():
        for n in ids:
            if n not in shared:
                adjacency[n].append(e)
    pending = [e for n in floor for e in adjacency[n]]
    owned, visited = set(), set()
    while pending:
        e = pending.pop()
        if e in owned:
            continue
        owned.add(e)
        for n in elements[e]:
            if n not in shared and n not in visited:
                visited.add(n)
                pending.extend(adjacency[n])
    ids = {n for e in owned for n in elements[e]}
    others = {n for e, row in elements.items() if e not in owned for n in row}
    if (len(owned) != leg["element_count"] or len(ids) != leg["node_count"]
            or ids & others != shared or len(shared) != leg["shared_interface_node_count"]
            or {n for n in ids if abs(nodes[n][2]) < 1e-5} != floor):
        raise ValueError("Recovered ownership differs from CAD-audited report")
    subset = {e: elements[e] for e in owned}
    volume, _ = straight_mesh_volume({n: nodes[n] for n in ids}, subset)
    if not math.isclose(volume, leg["mesh_volume_mm3"], rel_tol=1e-10, abs_tol=.001):
        raise ValueError("Recovered volume differs")
    moments = [[], [], []]
    for row in subset.values():
        points = [nodes[n] for n in row[:4]]
        a, b, c = [[p[i]-points[0][i] for i in range(3)] for p in points[1:]]
        v = sum(x*y for x, y in zip(a, cross(b, c), strict=True))/6
        for i in range(3):
            moments[i].append(v*sum(p[i] for p in points)/4)
    centroid = [math.fsum(m)/volume for m in moments]
    if math.dist(centroid, leg["mesh_centroid_mm"]) > 1e-6:
        raise ValueError("Recovered centroid differs")
    return owned


def prove():
    accepted, deck, _, sources = authenticated_inputs()
    report = json.loads(REPORT.read_text())
    if report["candidate"] != accepted["candidate"]:
        raise ValueError("Different geometry")
    unchanged(report["source_sha256"])
    unchanged(sources)
    nodes, elements = mesh(deck)
    legs = {s: recover(nodes, elements, leg) for s, leg in report["legs"].items()}
    # Read-only vector construction; no CAD solid or topology operations.
    from mini_moonboard import box_frame as b

    floor = {n for n, p in nodes.items() if abs(p[2]) < 1e-5}
    loads = set(accepted["load_nodes"])
    from fea.timber_asymmetric import map_target

    for label, p, normal in locations():
        if label in ("A12", "K12", "F6"):
            loads.add(map_target(nodes, p, normal, floor)["node"])
    _, _, result = release(nodes, elements, legs, {"left": -b.HALF, "right": b.HALF},
        b.point(0, 0, 0).toTuple(), b.normal().toTuple(), floor_nodes=floor, load_nodes=loads)
    unchanged(report["source_sha256"])
    unchanged(sources)
    # Compact stdout proof only; no modified mesh or sensitivity result published.
    for side in result["legs"].values():
        side["duplicated_node_count"] = len(side.pop("node_map"))
    print(json.dumps(result, indent=2, allow_nan=False))
    return result


if __name__ == "__main__":
    prove()
