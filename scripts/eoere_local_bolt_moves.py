"""Apply the two owner-approved local bolt moves to fresh-stock geometry.

Retain every timber section, plywood outline and hardware specification.
Historical holes are suppressed in this design model, never filled in a build.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import eoere_leg_header_clearance as clearance
from scripts.eoere_paired_frame_basis import RAW, ROOT, read, ref, sha

BASE = RAW / "frame-completion-v1"
PARENT = BASE / "owner-requested-geometry-v3/geometry.json"
PREPARATION = BASE / "owner-requested-cases-v3/geometry-preparation/inputs.json"
REVISION = "eoere-local-front-cleat-bolt-moves-v4"
OWN = Path(__file__).resolve()


def build(out: Path):
    assert not out.exists(), "fresh output required"
    pins = {ref(OWN)["path"]: sha(OWN)}
    g = read(PARENT, pins, "5ca7811d47646cd8d5839a76bbcdd7da509bbe3470dc21d2a7354d4b86a81257")
    previous_clearance = PARENT.parent / "clearance.json"
    assert read(previous_clearance, pins)["nominal_geometry_clear"]
    preparation = read(PREPARATION, pins)
    assert preparation["geometry"] == ref(PARENT)
    original = copy.deepcopy(g)
    changed = {r["id"]: r for r in g["changed_finished_solids"]}
    walls = preparation["finished_receiver_wall_queries"]
    targets = {f"rail_front_bolt_{side}_1" for side in ("left", "right")}
    targets |= {f"cleat_post_bolt_{side}_{i}" for side in ("left", "right") for i in (1, 2)}
    axes = {a["id"]: a for a in g["axes"]}
    wood, moves, replacement_ids = {}, [], set()
    out.mkdir(parents=True)

    def load(row):
        assert sha(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        return cq.Shape.importBrep(str(ROOT / row["path"]))

    def save(name, body, kind):
        assert body.isValid() and len(body.Solids()) == 1 and body.Volume() > 0, name
        path = out / (name + ".brep")
        assert body.exportBrep(str(path))
        box = body.BoundingBox()
        row = {"id": name, "kind": kind, "path": str(path.relative_to(ROOT)),
               "sha256": sha(path), "bytes": path.stat().st_size, "volume_mm3": body.Volume(),
               "center_of_mass_xyz_mm": list(body.Center().toTuple()),
               "bounds_xyz_mm": [getattr(box, c + end) for c in "xyz" for end in ("min", "max")]}
        changed[name] = row
        replacement_ids.add(name)
        if name in g["profiles"]:
            g["profiles"][name]["finished"] = row

    # Suppress all old holes before cutting any new ones, including holes
    # whose old/new envelopes overlap. Only the design for fresh stock changes.
    for identity in sorted(targets):
        axis = axes[identity]
        point, direction = np.asarray(axis["point_xyz_mm"]), np.asarray(axis["direction_xyz"])
        own_walls = [w for w in walls if w["axis_id"] == identity]
        assert {w["receiver"] for w in own_walls} == set(axis["receivers"])
        for wall in own_walls:
            name = wall["receiver"]
            body = wood[name] if name in wood else load(g["profiles"][name]["finished"])
            intervals = wall["finished_full_wall_intervals_from_axis_point_mm"]
            assert len(intervals) == 1
            lo, hi = intervals[0]
            tool = cq.Solid.makeCylinder(axis["bore_diameter_mm"] / 2, hi - lo,
                                        cq.Vector(*(point + lo * direction)), cq.Vector(*direction))
            wood[name] = body.fuse(tool).clean()

    for identity in sorted(targets):
        axis = axes[identity]
        old = np.asarray(axis["point_xyz_mm"])
        new, direction = old + [0, 0, 10.], np.asarray(axis["direction_xyz"])
        assert abs(old[2] - (50 if identity.startswith("rail_front") else 173.8125)) < 1e-6
        for wall in (w for w in walls if w["axis_id"] == identity):
            name = wall["receiver"]
            lo, hi = wall["finished_full_wall_intervals_from_axis_point_mm"][0]
            tool = cq.Solid.makeCylinder(axis["bore_diameter_mm"] / 2, hi - lo + 2,
                                        cq.Vector(*(new + (lo - 1) * direction)), cq.Vector(*direction))
            wood[name] = wood[name].cut(tool).clean()
        metals = [name for name in changed if name.startswith(identity + "_")]
        assert len(metals) == (5 if identity.startswith("rail_front") else 8)
        for name in metals:
            save(name, load(changed[name]).translate(cq.Vector(0, 0, 10)), "bolt")
        axis["point_xyz_mm"] = new.tolist()
        moves.append({"axis_id": identity, "before_xyz_mm": old.tolist(), "after_xyz_mm": new.tolist(),
                      "translation_xyz_mm": [0., 0., 10.], "receiver_member_ids": axis["receivers"]})
    for name, body in wood.items():
        save(name, body, "timber")

    assert len(replacement_ids) == 50 and len(wood) == 8
    assert len(g["axes"]) == 92 and g["screw_axes"] == original["screw_axes"]
    for axis in g["axes"]:
        old = next(a for a in original["axes"] if a["id"] == axis["id"])
        assert {k: v for k, v in axis.items() if k != "point_xyz_mm"} == {
            k: v for k, v in old.items() if k != "point_xyz_mm"}
        if axis["id"] not in targets:
            assert axis == old
    for name, profile in g["profiles"].items():
        assert {k: v for k, v in profile.items() if k != "finished"} == {
            k: v for k, v in original["profiles"][name].items() if k != "finished"}
    g.update(revision=REVISION, changed_finished_solids=list(changed.values()),
             local_bolt_moves={"parent": ref(PARENT), "axes": moves,
                               "replacement_part_ids": sorted(replacement_ids),
                               "fresh_stock_only_not_a_repair_instruction": True,
                               "upper_support_diameter_unchanged_mm": 12.7},
             new_response_computed=False, complete_joint_qualified=False,
             scope="Lower front pins Z50 to60mm; four cleat/post pins Z173.8125 to183.8125mm. All other axes, sections and hardware unchanged.",
             engineering_question="Do the two approved 10mm hole moves improve the own recalculated front and bonded-cleat references?",
             source_sha256={**g["source_sha256"], **pins})
    path = out / "geometry.json"
    path.write_text(json.dumps(g, indent=2, sort_keys=True) + "\n")

    # Reuse the complete occupied registry and exact solid intersection method.
    # The previous receipt covers unchanged pairs; check every revised part.
    code = inspect.getsource(clearance.check)
    replacements = {
        "    geometry = read(geometry_path)": "    geometry = read(geometry_path)\n    read(PRIOR_CLEARANCE, PRIOR_HASH)",
        "    for first in sorted(changed):": "    for first in sorted(REPLACEMENT_IDS):",
        "'occupied_part_count': len(bank),": "'reused_unchanged_pair_clearance': PRIOR_REF, 'newly_checked_part_ids': sorted(REPLACEMENT_IDS), 'occupied_part_count': len(bank),",
    }
    for before, after in replacements.items():
        assert code.count(before) == 1, before
        code = code.replace(before, after)
    scope = {**vars(clearance), "PRIOR_CLEARANCE": previous_clearance,
             "PRIOR_HASH": sha(previous_clearance), "PRIOR_REF": ref(previous_clearance),
             "REPLACEMENT_IDS": replacement_ids}
    exec(compile(code, str(OWN), "exec"), scope)  # noqa: S102 -- existing source-bound intersection method; explicit incremental part set only
    scope["check"](path, out / "clearance.json")
    print(json.dumps({"geometry": ref(path), "moved_axes": len(moves), "replacement_parts": len(replacement_ids)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    build(parser.parse_args().output.resolve())
