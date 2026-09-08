"""Installed bracket axes and grain assumptions, without assigning capacities."""
import csv
import io
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard import box_frame as b
from mini_moonboard import wide_frame as frame
from scripts.wide_purchase_bom import build as authenticate_inventory

OUTPUT = Path("docs/wide-bracket-axes.csv")


def grain(member):
    """Intended stock grain, not an inspection of purchased lumber."""
    if member == "base_header" or member.startswith("base_rail_"):
        return cq.Vector(1, 0, 0)
    if member.startswith("base_post_"):
        return cq.Vector(0, 0, 1)
    if member.startswith(("base_side_", "base_principal_")):
        return (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    raise ValueError("Unclassified member grain: "+member)


def rows():
    authenticate_inventory()
    connections = frame.connections()
    result = []
    for name, origin, u, v, beam, upright in frame.stations():
        w = u.cross(v)
        screws = [c for c in connections if c.members[0] == name]
        if len(screws) != 6:
            raise ValueError("Bracket must have six assigned screws")
        for member, direction in ((beam, -v), (upright, -u)):
            assigned = [c for c in screws if c.members[1] == member]
            if len(assigned) != 3 or any((c.direction-direction).Length > 1e-8 for c in assigned):
                raise ValueError("Flange assignment or screw axis differs")
        result.append({
            "bracket": name, "beam_member": beam, "upright_member": upright,
            "origin_world_mm": origin.toTuple(),
            "origin_world_in": (origin/25.4).toTuple(),
            "u_world": u.toTuple(), "v_world": v.toTuple(),
            "bend_axis_world": w.toTuple(),
            "beam_grain_world_assumed": grain(beam).toTuple(),
            "upright_grain_world_assumed": grain(upright).toTuple(),
            "bend_dot_beam_grain_abs": abs(w.dot(grain(beam))),
            "bend_dot_upright_grain_abs": abs(w.dot(grain(upright))),
            "beam_screw_dot_grain_abs": abs(v.dot(grain(beam))),
            "upright_screw_dot_grain_abs": abs(u.dot(grain(upright))),
            "screws": tuple(c.name for c in screws),
            "qualification": "F1 axis only; F2/F3/F4 signs, installation, joint demand and resistance unresolved",
        })
    if len(result) != 18 or len({r["bracket"] for r in result}) != 18:
        raise ValueError("Expected eighteen unique brackets")
    return result


def build():
    records = rows()
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
    writer.writeheader()
    for row in records:
        writer.writerow({k: json.dumps(v) if isinstance(v, tuple) else v for k, v in row.items()})
    return stream.getvalue()


if __name__ == "__main__":
    OUTPUT.write_text(build())
