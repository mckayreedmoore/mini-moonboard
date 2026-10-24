"""Publish the cumulative inward-bolt and inset-angle development geometry.

Reuse the checked v7 hardware meshes with translations. Only the thirteen
receivers with changed bores need replacement meshes; no mechanics is run.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts.eoere_inward_bolts import encode
from scripts.eoere_paired_frame_basis import RAW, ROOT, ref, sha
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)

REVISION = "eoere-inward-bolts-and-angles-v8"
BASE = RAW / "frame-completion-v1/owner-inward-angles-v8"
PACKET = Path("docs/bolted-frame-development/owner-frame-v8")
SCENE = Path("site/eoere-inward-angles-scene.json.gz")
INDEX = Path("docs/bolted-frame-development/development-revisions.json")


def publish(geometry_path):
    assert not (ROOT / PACKET).exists() and not (ROOT / SCENE).exists(), "fresh publication required"
    index_bytes = (ROOT / INDEX).read_bytes()
    previous = json.loads(index_bytes)
    assert previous["geometry"]["revision"] == "eoere-inward-exterior-bolts-v7"
    parent_receipt = json.loads((ROOT / previous["geometry"]["receipt"]["path"]).read_bytes())
    assert ref(previous["geometry"]["receipt"]["path"]) == previous["geometry"]["receipt"]
    parent = json.loads((ROOT / parent_receipt["checked_geometry"]["path"]).read_bytes())
    assert ref(parent_receipt["checked_geometry"]["path"]) == parent_receipt["checked_geometry"]
    g = json.loads(geometry_path.read_bytes())
    cpath = geometry_path.with_name("clearance.json")
    c = json.loads(cpath.read_bytes())
    assert g["revision"] == REVISION and c["geometry"] == ref(geometry_path)
    assert c["nominal_geometry_clear"] and c["occupied_part_count"] == 1037
    change = g["inward_angle_study"]
    assert change["parent_geometry"] == parent_receipt["checked_geometry"]
    assert change["world_translation_xyz_mm"] == [0., 6., 0.]
    moved_axes, moved_angles, timbers = (set(change[k]) for k in
        ("moved_axis_ids", "moved_angle_ids", "affected_wood_receivers"))
    assert (len(moved_axes), len(moved_angles), len(timbers)) == (24, 8, 13)
    assert g["screw_axes"] == parent["screw_axes"] and len(g["screw_axes"]) == 66
    assert len(g["axes"]) == 96 and len(g["fitting_poses"]) == 24
    assert all(a["direction_xyz"] == b["direction_xyz"] for a, b in zip(g["axes"], parent["axes"], strict=True))
    for a, b in zip(g["axes"], parent["axes"], strict=True):
        for key in ("diameter_mm", "nominal_under_head_length_mm", "hardware_scenario"):
            assert a.get(key) == b.get(key)
    assert g["selected_stack_overrides"] == parent["selected_stack_overrides"]
    for key in ("new_response_computed", "complete_joint_qualified", "release"):
        assert g[key] is False
    assert not change["panel_and_kicker_screws_changed"] and not change["member_outlines_changed"]
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    old_registry = {r["id"]: r for r in parent["changed_finished_solids"]}
    replacements, translations = [], []
    for name in sorted(timbers):
        row = registry[name]
        assert ref(row["path"])["sha256"] == row["sha256"]
        replacements.append({"id": name, "name": name,
                             "fabrication": {"kind": "timber", "owner_frame_revision": REVISION,
                                             "description": "Inset-angle bore positions; unchanged stock and outline; geometry review only"},
                             "mesh": _shape_mesh(cq.Shape.importBrep(str(ROOT / row["path"])))})
    for stack in change["complete_hardware_stack_moves"]:
        assert stack["axis_id"] in moved_axes and stack["complete_piece_count"] == len(stack["part_ids"])
        for name in stack["part_ids"]:
            translations.append({"name": name, "kind": "bolt", "axis_id": stack["axis_id"],
                                 "translation_xyz_mm": [0., 6., 0.]})
    for name in sorted(moved_angles):
        translations.append({"name": name, "kind": "angle", "translation_xyz_mm": [0., 6., 0.]})
    assert len(translations) == 160
    for row in translations:
        after = registry[row["name"]]
        assert sha(after["path"]) == after["sha256"]
        if row["kind"] == "angle":
            move = next(m for m in change["angle_moves"] if m["angle_id"] == row["name"])
            old_pose = next(p for p in parent["fitting_poses"] if p["id"] == row["name"])
            assert old_pose["origin_xyz_mm"] == move["before_origin_xyz_mm"]
            assert move["after_origin_xyz_mm"] == [v+d for v, d in zip(move["before_origin_xyz_mm"], [0, 6, 0], strict=True)]
            continue  # The source-bound CAD producer proves the factory shape's pure translation.
        before = old_registry[row["name"]]
        assert abs(before["volume_mm3"] - after["volume_mm3"]) < 1e-5
        for key, delta in (("center_of_mass_xyz_mm", [0., 6., 0.]), ("bounds_xyz_mm", [0., 0., 6., 6., 0., 0.])):
            assert max(abs(b + d - a) for b, d, a in zip(before[key], delta, after[key], strict=True)) < 1e-5
    changed_ids = set(c["newly_checked_part_ids"])
    assert changed_ids == timbers | {r["name"] for r in translations} and len(changed_ids) == 173
    assert {n for n, r in registry.items() if r != old_registry.get(n)} == changed_ids
    (ROOT / PACKET).mkdir()
    files = {}

    def put(name, value):
        path = ROOT / PACKET / name
        path.write_bytes(value if isinstance(value, bytes) else encode(value))
        files[name] = ref(path)

    put("axis-updates.json", {"parent_geometry": parent_receipt["checked_geometry"],
                              "axes": [a for a in g["axes"] if a["id"] in moved_axes],
                              "fitting_poses": [p for p in g["fitting_poses"] if p["id"] in moved_angles],
                              "screw_axes_changed": False, "inward_bolt_directions_preserved": True})
    put("member-updates.json", {name: g["profiles"][name] for name in sorted(timbers)})
    put("changes.json", {k: change[k] for k in ("parent_geometry", "prior_clearance", "world_translation_xyz_mm",
                         "seed_angle_ids", "moved_angle_ids", "moved_axis_ids", "angle_moves", "axis_moves",
                         "complete_hardware_stack_moves", "affected_wood_receivers", "flat_cleat_outline_preserved",
                         "panel_and_kicker_screws_changed", "member_outlines_changed",
                         "fresh_stock_only_not_a_physical_repair_instruction", "prior_force_results_transferred")})
    rows = []
    for proof in change["current_full_wall_reboring_proofs"]:
        name, profile = proof["receiver"], g["profiles"][proof["receiver"]]
        bounds = profile["finished"]["bounds_xyz_mm"]
        for bore in proof["new_bores"]:
            point, direction = np.asarray(bore["center_xyz_mm"]), np.asarray(bore["direction_xyz"])
            component = int(np.argmax(np.abs(direction)))
            low, high = bounds[2 * component:2 * component + 2]
            row = {"axis_id": bore["axis_id"], "receiver": name,
                   "modeled_bore_envelope_diameter_mm": bore["bore_diameter_mm"],
                   "full_wall_length_mm": bore["projected_wall_span_mm"], "Actual": "", "Disposition": ""}
            for end, station in (("entry", low if direction[component] > 0 else high),
                                 ("exit", high if direction[component] > 0 else low)):
                surface = point.copy(); surface[component] = station
                local = np.asarray(profile["basis_grain_u_v_xyz"]) @ (surface - profile["datum_xyz_mm"])
                for letter, value in zip("luv", local, strict=True):
                    row[end + "_in_receiver_" + letter + "_mm"] = float(value)
            rows.append(row)
    assert len(rows) == 78
    from scripts.eoere_paired_shop import csv_bytes
    put("receiver-updates.csv", csv_bytes(rows))
    put("layout.md", ("# Inset-angle geometry with inward-facing nuts\n\n"
        "Current development revision `" + REVISION + "` retains all 40 inward-facing exterior stacks from v7. "
        "Eight connected base/header angles and all 24 shared bolt axes move 6 mm in world Y, toward the frame interior. "
        "The [changes](changes.json), [axis updates](axis-updates.json), [13 receiver profiles](member-updates.json) and "
        "[78 full-wall bore rows](receiver-updates.csv) supersede their preceding poses and hole locations. "
        "The stock sections, member/cleat outlines, six panels, 66 Hillman axes, factory holes and hardware lengths/counts remain.\n\n"
        "This is a fresh-stock design revision: suppressed computational holes are not a physical hole-filling repair. "
        "The geometry and full occupied-part intersection check do not establish strength, complete edge/group factors, "
        "thread windows, washer seats or installation/tool access. No cutting, drilling, fabrication or climbing release. "
        "Actual/Disposition fields remain blank. The v6 forces and bracing study remain bound to v6; new matching results "
        "must identify this cumulative revision.\n").encode())
    report = {"schema": "eoere_inward_angles_revision/v1", "revision": REVISION,
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(geometry_path), "checked_clearance": ref(cpath),
              "counts": parent_receipt["counts"], "files": files, "producer": ref(Path(__file__)),
              "translation_xyz_mm": [0., 6., 0.], "moved_angles": 8, "moved_axes": 24,
              "changed_receivers": 13, "changed_parts": 173, "retained_inward_exterior_stacks": 40,
              "nominal_geometry_clear": True, "inward_bolt_directions_preserved": True,
              "stock_outlines_and_66_screws_preserved": True, "hardware_lengths_and_counts_preserved": True,
              "current_response_computed": False, "historical_capacity_transferred": False,
              "geometry_adopted": False,
              "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
              "fabrication_released": False, "climbing_released": False, "actual_observations": None}
    path = ROOT / PACKET / "geometry.json"
    path.write_bytes(encode(report))
    scene = {"schema": "eoere_inward_angles_patch/v1", "revision": REVISION, "key": previous["geometry"]["viewer"],
             "parent_scene": previous["geometry"]["scene"], "parent_layout": previous["geometry"]["receipt"],
             "layout_report": ref(path), "part_count": 1037, "counts": report["counts"],
             "replacements": replacements, "translations": translations, "removals": [],
             "current_response_computed": False, "historical_capacity_transferred": False,
             "complete_conditional_frame_evaluation": False, "panel_Hillman_resolution_deferred": True,
             "fabrication_released": False, "climbing_released": False}
    scene["triangle_topologies"] = _deduplicate_triangle_topologies(replacements)
    decoded = (json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n").encode()
    (ROOT / SCENE).write_bytes(gzip.compress(decoded, compresslevel=9, mtime=0))
    scene_ref = {**ref(SCENE), "decoded_sha256": hashlib.sha256(decoded).hexdigest()}
    index = copy.deepcopy(previous)
    index.update(schema="bolted_frame_development_revisions/v13", preceding_revision=previous,
                 geometry={"revision": REVISION, "viewer": scene["key"], "receipt": ref(path), "scene": scene_ref},
                 hardware_model={**index["hardware_model"], "revision": REVISION, "receipt": ref(path)},
                 shop={**index["shop"], "revision": REVISION, "geometry": ref(path), "result": ref(path)},
                 preserved_owner_v7_viewer="eoere-owner-frame-v7-development")
    assert (ROOT / INDEX).read_bytes() == index_bytes, "live index changed during publication"
    (ROOT / INDEX).write_bytes(encode(index))
    print(json.dumps({"geometry": ref(path), "scene": scene_ref, "changed_meshes": 13,
                      "translated_reused_meshes": 160, "counts": report["counts"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=ROOT / BASE / "geometry/geometry.json")
    args = parser.parse_args()
    publish(args.geometry.resolve())
