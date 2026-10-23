"""Publish the compatible front-pin revision and its four changed drawings.

Unchanged drawings, hardware and stock allocation retain their frozen sources.
The viewer patch contains only fourteen changed parts and inherits the rest.
"""

from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import eoere_paired_shop as shop
from scripts.eoere_builder_layout import number, vector
from scripts.eoere_paired_frame_basis import RAW, ROOT, ref, sha
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)

BASE = RAW / "frame-completion-v1/owner-bolt-moves-v4"
GEOMETRY = BASE / "front-only-geometry/geometry.json"
PREPARATION = BASE / "analysis/preparation/inputs.json"
PACKET = Path("docs/bolted-frame-development/owner-frame-v4")
PREVIOUS = Path("docs/bolted-frame-development/owner-frame-v3")
SCENE = Path("site/eoere-owner-frame-v4-scene.json.gz")


def publish():
    index_path = Path("docs/bolted-frame-development/development-revisions.json")
    previous = json.loads((ROOT / index_path).read_bytes())
    assert previous["schema"] == "bolted_frame_development_revisions/v8"
    assert not (ROOT / PACKET).exists() and not (ROOT / SCENE).exists()
    g = json.loads((ROOT / GEOMETRY).read_bytes())
    prep = json.loads((ROOT / PREPARATION).read_bytes())
    clearance = json.loads((ROOT / GEOMETRY.parent / "clearance.json").read_bytes())
    assert clearance["geometry"] == ref(GEOMETRY) and clearance["nominal_geometry_clear"]
    assert prep["geometry"]["path"].endswith("owner-bolt-moves-v4/analysis/geometry/geometry.json")
    assert len(g["local_bolt_moves"]["axes"]) == 2
    (ROOT / PACKET).mkdir()
    files = {}

    def put(name, value):
        path = ROOT / PACKET / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not isinstance(value, bytes):
            value = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        path.write_bytes(value)
        files[name] = ref(path)

    def rows(name):
        return list(csv.DictReader(io.StringIO((ROOT / PREVIOUS / name).read_text())))

    def table(values):
        keys = list(dict.fromkeys(k for row in values for k in row))
        return shop.csv_bytes([{k: row.get(k, "") for k in keys} for row in values])

    profiles = g["profiles"]
    axes = {a["id"]: a for a in g["axes"]}
    members = rows("members.csv")
    for row in members:
        source = profiles[row["member"]]["finished"]
        row.update(current_finished_source_path=source["path"], current_finished_source_sha256=source["sha256"])
    holes = rows("receiver-holes.csv")
    walls = {(r["axis_id"], r["receiver"]): r for r in prep["finished_receiver_wall_queries"]}
    moved = {r["axis_id"] for r in g["local_bolt_moves"]["axes"]}
    for row in holes:
        identity, name = row["axis_id"], row["receiver"]
        if identity not in moved:
            continue
        axis, profile = axes[identity], profiles[name]
        intervals = walls[identity, name]["finished_full_wall_intervals_from_axis_point_mm"]
        assert len(intervals) == 1
        lo, hi = intervals[0]
        row["saved_full_wall_length_mm"] = hi - lo
        for prefix, station in (("entry", lo), ("exit", hi)):
            point = np.asarray(axis["point_xyz_mm"]) + station * np.asarray(axis["direction_xyz"])
            local = np.asarray(profile["basis_grain_u_v_xyz"]) @ (point - profile["datum_xyz_mm"])
            for c, value in zip("luv", local, strict=True):
                row[prefix + "_in_receiver_" + c + "_mm"] = float(value)
    assert len(members) == 30 and len(holes) == 112
    put("axes.json", {"axes": g["axes"], "screw_axes": g["screw_axes"], "fitting_poses": g["fitting_poses"]})
    put("current_profiles.json", profiles)
    put("members.csv", table(members))
    put("receiver-holes.csv", table(holes))
    names = sorted({r["receiver"] for r in holes if r["axis_id"] in moved})
    assert len(names) == 4
    lines = ["# Revised front-post and runner coordinates", "", "Applies to `" + g["revision"] + "`.", "",
             "The two lower front bolts move from50 to60mm above the floor. Upper bolts stay100mm; all four remain80mm from the common front end. Cleat/post bolts stay at173.8125mm in their factory angle holes. Upper long-support bolts stay1/2in at their existing axes.", "",
             "These four dimension sheets and the [complete receiver table](receiver-holes.csv) supersede the corresponding v3 coordinates. Other member drawings, dimensions, stock allocation and hardware remain in the [preserved packet](../owner-frame-v3/layout.md). Actual/Disposition cells stay blank. Design-review coordinates are not issued cutting/drilling instructions.", ""]
    for name in names:
        profile = profiles[name]
        own = [r for r in holes if r["receiver"] == name]
        put("drawings/" + name + ".svg", shop.drawing(name, profile, own))
        lines += ["## " + name, "", "Blank L × depth × thickness: **" + " × ".join(map(number, profile["blank_mm"])) + " mm**. [Dimension sheet](drawings/" + name + ".svg).", "",
                  "World datum XYZ: `" + vector(profile["datum_xyz_mm"]) + "`. Positive L/U/V: " + "; ".join("`" + vector(v) + "`" for v in profile["basis_grain_u_v_xyz"]) + ".", "",
                  "| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |", "| --- | --- | --- |"]
        for row in own:
            lines.append("| `" + row["axis_id"] + "` | `" + vector(float(row["entry_in_receiver_" + c + "_mm"]) for c in "luv") + "` | `" + vector(float(row["exit_in_receiver_" + c + "_mm"]) for c in "luv") + "` |")
        lines.append("")
    put("layout.md", "\n".join(lines).encode())
    for name in ("hardware-review.csv", "hardware-planning.csv", "hardware-totals.csv", "stock-nesting.csv", "hardware-length-windows.json"):
        files[name] = ref(PREVIOUS / name)
    counts = {"sawn_members": 20, "plywood_cleats": 4, "panels": 6, "angles": 24, "bolt_stacks": 92,
              "nuts": 92, "washers": 184, "spacer_pieces": 26, "Hillman_axes": 66,
              "receiver_occurrences": 112, "occupied_parts": 1011}
    report = {"schema": "eoere_owner_local_bolt_revision/v1", "revision": g["revision"],
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(GEOMETRY), "checked_clearance": ref(GEOMETRY.parent / "clearance.json"),
              "sizing_inputs": ref(PREPARATION), "counts": counts, "files": files,
              "local_bolt_moves": g["local_bolt_moves"], "nominal_geometry_clear": True,
              "rejected_cleat_move_clearance": ref(BASE / "geometry/clearance.json"),
              "cleat_move_adopted": False, "upper_support_diameter_increased": False,
              "development_model_integrated": True, "old_force_pass_transferred": False,
              "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
              "fabrication_released": False, "climbing_released": False, "actual_observations": None,
              "producer": ref(Path(__file__))}
    path = ROOT / PACKET / "geometry.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    receipt = ref(path)
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    replacements = []
    for name in g["local_bolt_moves"]["replacement_part_ids"]:
        row = registry[name]
        assert sha(row["path"]) == row["sha256"]
        body = cq.Shape.importBrep(str(ROOT / row["path"]))
        fabrication = {"kind": row["kind"], "owner_frame_revision": g["revision"],
                       "description": "Local lower-front-pin move; own conditional review; no inherited acceptance"}
        if row["kind"] == "bolt":
            axis = next(a for a in g["axes"] if name.startswith(a["id"] + "_"))
            fabrication.update(connection_name=axis["id"], hardware_role=name[len(axis["id"]) + 1:],
                               diameter_mm=axis["diameter_mm"], delivered_part_verified=False)
        replacements.append({"id": name, "name": name, "mesh": _shape_mesh(body), "fabrication": fabrication})
    scene = {"schema": "eoere_owner_requested_frame_patch/v1", "revision": g["revision"],
             "key": "eoere-current-frame-development", "parent_scene": previous["geometry"]["scene"],
             "parent_layout": previous["geometry"]["receipt"], "layout_report": receipt,
             "part_count": 1011, "counts": counts, "replacements": replacements, "removals": [],
             "historical_capacity_transferred": False, "complete_conditional_frame_evaluation": False,
             "panel_Hillman_resolution_deferred": True, "fabrication_released": False, "climbing_released": False}
    scene["triangle_topologies"] = _deduplicate_triangle_topologies(replacements)
    encoded = (json.dumps(scene, separators=(",", ":")) + "\n").encode()
    (ROOT / SCENE).write_bytes(gzip.compress(encoded, compresslevel=9, mtime=0))
    scene_ref = {**ref(SCENE), "decoded_sha256": hashlib.sha256(encoded).hexdigest()}
    current = {"schema": "bolted_frame_development_revisions/v9", "candidate": previous["candidate"],
               "evidence_candidate": previous["evidence_candidate"],
               "geometry": {"revision": g["revision"], "viewer": scene["key"], "receipt": receipt, "scene": scene_ref},
               "hardware_model": {**copy.deepcopy(previous["hardware_model"]), "revision": g["revision"], "receipt": receipt},
               "selected_baseline": copy.deepcopy(previous["selected_baseline"]),
               "shop": {"revision": g["revision"], "geometry": receipt, "result": receipt, "packet": "docs/bolted-frame-development/builder-plan.md",
                        "shop_planning_only": True, "instructions_current_for_fabrication": False},
               "conditional_frame_evaluation": None, "panel_Hillman_resolution_deferred": True,
               "fabrication_released": False, "climbing_released": False,
               "preserved_owner_v3_viewer": "eoere-owner-frame-v3-development", "preceding_revision": previous}
    (ROOT / index_path).write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"geometry": receipt, "scene": scene_ref, "changed_parts": len(replacements)}))


if __name__ == "__main__":
    publish()
