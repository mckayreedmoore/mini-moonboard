"""Publish only the owner's requested geometry and honest review tables.

The preceding complete evaluation stays bound to its original model. The new
tables describe a sizing candidate; they do not issue cutting instructions.
"""

from __future__ import annotations

import copy
import csv
import gzip
import io
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts.eoere_current_shop_followup import csv_bytes
from scripts.eoere_paired_frame_basis import ROOT, RAW, ref, sha
from scripts.eoere_requested_frame import REVISION
from scripts.export_wood_joint_wj24_scene import _deduplicate_triangle_topologies, _shape_mesh

RAW_GEOMETRY = RAW / "frame-completion-v1/owner-requested-geometry-v3/geometry.json"
PREPARATION = RAW / "frame-completion-v1/owner-requested-cases-v3/geometry-preparation/inputs.json"
PACKET = Path("docs/bolted-frame-development/owner-frame-v3")
SCENE = Path("site/eoere-owner-frame-v3-scene.json.gz")
KEY = "eoere-current-frame-development"


def publish():
    # A failed topology export can leave unpublished review tables. Resume
    # those owned outputs only while the preserved v7 index is still current.
    assert not (ROOT / SCENE).exists()
    g = json.loads((ROOT / RAW_GEOMETRY).read_bytes())
    preparation = json.loads((ROOT / PREPARATION).read_bytes())
    clearance = json.loads((ROOT / RAW_GEOMETRY.parent / "clearance.json").read_bytes())
    index_path = Path("docs/bolted-frame-development/development-revisions.json")
    previous = json.loads((ROOT / index_path).read_bytes())
    assert previous["schema"] == "bolted_frame_development_revisions/v7"
    assert preparation["geometry"] == clearance["geometry"] == ref(RAW_GEOMETRY)
    assert clearance["nominal_geometry_clear"] and clearance["occupied_part_count"] == 1011
    (ROOT / PACKET).mkdir(exist_ok=True)
    files = {}

    def put(name, value):
        path = PACKET / name
        if not isinstance(value, bytes):
            value = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        (ROOT / path).write_bytes(value)
        files[name] = ref(path)
        return files[name]

    def rows(name):
        p = Path("docs/bolted-frame-development/paired-frame-v2") / name
        return list(csv.DictReader(io.StringIO((ROOT / p).read_text())))

    def table(values):
        keys = list(dict.fromkeys(k for row in values for k in row))
        return csv_bytes([{k: row.get(k, "") for k in keys} for row in values])

    profiles = g["profiles"]
    axes = {a["id"]: a for a in g["axes"]}
    selected = []
    for r in rows("hardware-selection.csv"):
        if r["axis_id"] not in axes:
            continue
        a = axes[r["axis_id"]]
        r.update(receiver_member_ids=";".join(a["receivers"]), nut_side_spacer_mm=a.get("nut_side_spacer_mm", 0),
                 spacer_piece_count=round(a.get("nut_side_spacer_mm", 0) / 12.7), Actual="", Disposition="",
                 review_status="Owner-requested sizing candidate; affected strength/installation checks required")
        if any(n.startswith("eoere_cleat_") for n in a["receivers"]):
            for k in ["minimum_two_pitch_margin_mm", "minimum_nut_seating_margin_mm",
                      "minimum_receiver_plus_plate_with_spacer_mm", "maximum_receiver_plus_plate_with_spacer_mm"]:
                r[k] = ""
            r["reason"] = "Two nominal19.05mm plywood leaves; three12.7mm factory spacers. Catalog seating on delivered panel thickness remains unresolved. No inherited window pass."
        selected.append(r)
    members = []
    for row in rows("members.csv"):
        name = row["member"]
        if name not in profiles:
            continue
        p = profiles[name]
        for k, v in zip(("nominal_blank_length_mm", "nominal_blank_depth_mm", "nominal_blank_thickness_mm"), p["blank_mm"]):
            row[k] = v
        for i, c in enumerate("xyz"):
            row["datum_" + c + "_mm"] = p["datum_xyz_mm"][i]
        row.update(current_finished_source_path=p["finished"]["path"], current_finished_source_sha256=p["finished"]["sha256"],
                   Actual="", Disposition="")
        members.append(row)
    holes = []
    for wall in preparation["finished_receiver_wall_queries"]:
        name, identity = wall["receiver"], wall["axis_id"]
        a, p = axes[identity], profiles[name]
        intervals = wall["finished_full_wall_intervals_from_axis_point_mm"]
        assert len(intervals) == 1
        lo, hi = intervals[0]
        point, direction = np.asarray(a["point_xyz_mm"]), np.asarray(a["direction_xyz"])
        row = {"axis_id": identity, "receiver": name, "nominal_shaft_diameter_mm": a["diameter_mm"],
               "modeled_bore_envelope_diameter_mm": a["bore_diameter_mm"], "saved_full_wall_length_mm": hi - lo,
               "Actual": "", "Disposition": ""}
        for prefix, q in [("entry", point + direction * lo), ("exit", point + direction * hi)]:
            local = np.asarray(p["basis_grain_u_v_xyz"]) @ (q - p["datum_xyz_mm"])
            for j, c in enumerate("luv"):
                row[prefix + "_in_receiver_" + c + "_mm"] = float(local[j])
        holes.append(row)
    assert len(selected) == 92 and len(holes) == 112 and len(members) == 30
    put("axes.json", {"axes": g["axes"], "screw_axes": g["screw_axes"], "fitting_poses": g["fitting_poses"]})
    put("current_profiles.json", profiles)
    put("members.csv", table(members))
    put("hardware-review.csv", table(selected))
    put("receiver-holes.csv", table(holes))
    requested = g["owner_requested_revision"]
    counts = {"sawn_members": 20, "plywood_cleats": 4, "panels": 6, "angles": 24,
              "bolt_stacks": 92, "nuts": 92, "washers": 184, "spacer_pieces": 26,
              "Hillman_axes": 66, "receiver_occurrences": 112, "occupied_parts": 1011}
    report = {"schema": "eoere_owner_requested_frame_revision/v1", "revision": REVISION,
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(RAW_GEOMETRY), "checked_clearance": ref(RAW_GEOMETRY.parent / "clearance.json"),
              "sizing_inputs": ref(PREPARATION), "counts": counts, "files": files,
              "owner_requested_revision": requested, "nominal_geometry_clear": True,
              "development_model_integrated": True, "old_force_pass_transferred": False,
              "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
              "fabrication_released": False, "climbing_released": False, "actual_observations": None,
              "producer": ref(Path(__file__)), "geometry_producer": ref("scripts/eoere_requested_frame.py")}
    receipt_path = PACKET / "geometry.json"
    (ROOT / receipt_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    receipt = ref(receipt_path)
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    replacements = []
    for name in requested["replacement_part_ids"]:
        row = registry[name]
        assert sha(row["path"]) == row["sha256"]
        shape = cq.Shape.importBrep(str(ROOT / row["path"]))
        fabrication = {"kind": row["kind"], "owner_frame_revision": REVISION,
                       "dimensions_mm": [row["bounds_xyz_mm"][2*i+1]-row["bounds_xyz_mm"][2*i] for i in range(3)],
                       "description": "Owner-requested frame; sizing and hardware unresolved; no inherited frame pass"}
        if name.startswith("eoere_cleat_"):
            fabrication.update(material="Proposed APA24oc PS1 plywood, >=5plies and Group1; strengthaxisworldZ",
                               nominal_independent_leaf_thickness_mm=19.05,
                               no_glue_friction_or_composite_action_credit=True,
                               minimum_credited_actual_thickness_mm=None)
        if row["kind"] == "bolt":
            a = next(a for identity, a in axes.items() if name.startswith(identity + "_"))
            role = name[len(a["id"]) + 1:]
            roles = ["shaft", "head", "head_washer", "nut_washer", "nut", "spacer", "spacer_2", "spacer_3"]
            fabrication.update(connection_name=a["id"], hardware_role=role, diameter_mm=a["diameter_mm"],
                               stack_roles=roles, nut_side_spacer_mm=38.1, spacer_piece_count=3,
                               selected_underhead_length_mm=a["nominal_under_head_length_mm"],
                               delivered_part_verified=False)
        replacements.append({"id": name, "name": name, "mesh": _shape_mesh(shape), "fabrication": fabrication})
    scene = {"schema": "eoere_owner_requested_frame_patch/v1", "revision": REVISION, "key": KEY,
             "parent_scene": previous["geometry"]["scene"], "parent_layout": previous["geometry"]["receipt"],
             "layout_report": receipt, "part_count": 1011, "counts": counts, "replacements": replacements,
             "removals": requested["removed_part_ids"], "historical_capacity_transferred": False,
             "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
             "fabrication_released": False, "climbing_released": False}
    scene["triangle_topologies"] = _deduplicate_triangle_topologies(replacements)
    encoded = (json.dumps(scene, separators=(",", ":")) + "\n").encode()
    (ROOT / SCENE).write_bytes(gzip.compress(encoded, compresslevel=9, mtime=0))
    import hashlib
    scene_ref = {**ref(SCENE), "decoded_sha256": hashlib.sha256(encoded).hexdigest()}
    geometry = {"revision": REVISION, "viewer": KEY, "receipt": receipt, "scene": scene_ref}
    current = {"schema": "bolted_frame_development_revisions/v8", "candidate": previous["candidate"],
               "evidence_candidate": previous["evidence_candidate"], "geometry": geometry,
               "hardware_model": {"revision": REVISION, "receipt": receipt, "actual_parts_verified": False,
                                   "analysis_pass_transferred": False, "selected_for_build": False},
               "selected_baseline": copy.deepcopy(previous["selected_baseline"]),
               "shop": {"revision": REVISION, "geometry": receipt, "result": receipt,
                        "packet": "docs/bolted-frame-development/builder-plan.md", "shop_planning_only": True,
                        "instructions_current_for_fabrication": False},
               "conditional_frame_evaluation": None, "panel_Hillman_resolution_deferred": True,
               "fabrication_released": False, "climbing_released": False, "preceding_revision": previous}
    (ROOT / index_path).write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"geometry": receipt, "scene": scene_ref, "parts": 1011, "replacements": len(replacements)}))


if __name__ == "__main__":
    publish()
