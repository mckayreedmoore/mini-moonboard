"""Current-wide leg/rim point mapping and complete bonded-interface inventory."""
import json
from collections import defaultdict
from pathlib import Path

from fea.floor_contact import FACES
from fea.gusset_connector_trial import point_weights
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import unchanged
from fea.wide_asymmetric import preparation
from fea.wide_joint_ownership import recover
from mini_moonboard import wide_frame as frame

OUTPUT = Path("fea/results/leg-connector-map.json")


def build():
    info, decks = preparation()
    ownership, nodes, _, sources = recover([v["node"] for v in info["mapping"].values()])
    from fea.floor_contact import mesh
    _, elements = mesh(decks["A12"])
    for name in ("fea/leg_connector_map.py", "fea/gusset_connector_trial.py"):
        sources[name] = digest(name)
    faces = defaultdict(list)
    for eid, ids in elements.items():
        for number, indices in enumerate(FACES, 1):
            face = tuple(ids[i] for i in indices)
            faces[tuple(sorted(face))].append((eid, number, face))
    if any(len(rows) > 2 for rows in faces.values()):
        raise ValueError("Nonmanifold parent mesh")
    result = {}
    bolts = {c.name: c for c in frame.connections()}
    for side, leg in ownership["legs"].items():
        chosen = set(leg["element_ids"])
        members = {n: set(ids) for n, ids in leg["shared_nodes_by_board_member"].items()}
        contacts = defaultdict(list)
        for rows in faces.values():
            inside = [r for r in rows if r[0] in chosen]
            if len(rows) != 2 or len(inside) != 1:
                continue
            eid, face, ids = inside[0]
            member = [n for n, ns in members.items() if set(ids) <= ns]
            if len(member) != 1:
                raise ValueError("Unclassified or ambiguous leg shared face")
            neighbor = next(r for r in rows if r[0] not in chosen)
            contacts[member[0]].append({"element": eid, "face": face, "nodes": list(ids),
                                       "neighbor_element": neighbor[0], "neighbor_face": neighbor[1]})
        shared = set().union(*members.values())
        if {n for fs in contacts.values() for f in fs for n in f["nodes"]} != shared:
            raise ValueError("Leg shared nodes lack classified shared faces")
        points = {}
        for i in range(1, 5):
            name = f"analysis_leg_wall_bolt_{side}_{i}"
            bolt = bolts[name]
            rim = f"base_side_{side}"
            if set(bolt.members) != {rim, f"leg_{side}_inner", f"leg_{side}_outer"}:
                raise ValueError("Unexpected leg bolt member stack")
            points[name] = {**point_weights(nodes, contacts[rim], (bolt.start.y, bolt.start.z)), "side": side, "member": rim}
        result[side] = {**leg, "shared_nodes": sorted(shared), "interfaces": dict(contacts), "points": points}
    unchanged(sources)
    return {"source_sha256": sources, "legs": result,
            "limits": "Geometry mapping only. Both leg plies remain bonded; no connector stiffness, capacity or release solve."}


if __name__ == "__main__":
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite leg map")
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
