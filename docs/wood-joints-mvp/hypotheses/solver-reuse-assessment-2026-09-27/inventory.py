"""Read-only inventory of the frozen A09 inputs; no solver or model edits."""

import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-port-motion-attempt09-common-map"


def main():
    names = ["mesh.json", "mesh.inp", "contact-manifest.json", "contact-fragment.inc",
             "nut-coupling.json", "nut-coupling.inp", "rigid-carriers.inp",
             "materials.inp", "external-ports.json", "port-motion-controls.inp",
             "port_motion_n_plus.inp"]
    data = {name: (SOURCE / name).read_bytes() for name in names}
    mesh = json.loads(data["mesh.json"])
    contact = json.loads(data["contact-manifest.json"])
    coupling = json.loads(data["nut-coupling.json"])
    sets = {}
    current = None
    for line in data["contact-fragment.inc"].decode().splitlines():
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            current = None
            fields = line.upper().split(",")
            if fields[0] == "*NSET":
                assert "GENERATE" not in fields
                current = next(f.split("=", 1)[1] for f in fields[1:] if f.startswith("NSET="))
                assert current not in sets
                sets[current] = set()
        elif current:
            sets[current].update(int(x) for x in line.split(",") if x.strip())
    slaves = {k: v for k, v in sets.items() if k.endswith("_S")}
    assert len(slaves) == len(contact["pairs"]) == 35
    overlaps = []
    for (a, na), (b, nb) in itertools.combinations(sorted(slaves.items()), 2):
        common = na & nb
        if common:
            overlaps.append({"slave_a": a, "slave_b": b, "shared_node_count": len(common),
                             "shared_node_ids": sorted(common)})
    alternative = dict(slaves)
    alternative["WJCP_N_002_S"] = sets["WJCP_N_002_M"]
    alternative_overlaps = [
        {"slave_a": a, "slave_b": b, "shared_node_count": len(na & nb)}
        for (a, na), (b, nb) in itertools.combinations(sorted(alternative.items()), 2)
        if na & nb
    ]
    result = {
        "scope": "A09 source inventory only; no native solve or acceptance",
        "source_directory": str(SOURCE.relative_to(ROOT)),
        "sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in data.items()},
        "candidate": contact["candidate"],
        "node_count": mesh["node_count"], "element_count": mesh["element_count"],
        "body_count": mesh["body_count"], "wood_body_count": mesh["wood_body_count"],
        "physical_metal_body_count": mesh["physical_metal_body_count"],
        "contact_pair_count": len(contact["pairs"]),
        "contact_pair_category_counts": contact["pair_category_counts"],
        "nut_equation_count": len(coupling["equation_cards"]),
        "existing_slave_set_overlap_pair_count": len(overlaps),
        "existing_slave_set_overlaps": overlaps,
        "hypothetical_pair_002_reversal": {
            "model_changed": False,
            "slave_set_overlap_pair_count": len(alternative_overlaps),
            "slave_set_overlaps": alternative_overlaps,
            "interpretation": "Node-set screen only; not validated contact orientation or mechanics."
        },
        "limits": ["Node memberships are read from the contact producer's NSETs.",
                   "This is not an independent face-connectivity or geometry audit.",
                   "Alternative orientation is assessed only for slave node-set intersections, not face connectivity, pairing, normals, gaps, or mechanical response.",
                   "Code_Aster has not been installed, imported, or executed."]
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
