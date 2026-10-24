"""Restore the reference cleat perimeter and two upper pins for geometry review.

Keep the current frame, two 19.05-mm leaves per corner and all 66 Hillman
axes. Reuse existing finished solids, complete hardware stacks and clearance
helpers; do not transfer earlier strength or issue fabrication instructions.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import inspect
import io
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import eoere_leg_header_clearance as clearance
from scripts import eoere_paired_shop as shop
from scripts.eoere_builder_layout import number, vector
from scripts.eoere_leg_header_revision import verify_attachment_axes
from scripts.eoere_paired_frame_basis import RAW, ROOT, read, ref, sha
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)

REVISION = "eoere-reference-cleat-upper-pair-v5"
PREVIOUS = Path("docs/bolted-frame-development/owner-frame-v4")
PACKET = Path("docs/bolted-frame-development/owner-frame-v5")
BASE = RAW / "frame-completion-v1/owner-reference-cleats-v5"
REFERENCE = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/"
                 "thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json")
INDEX = Path("docs/bolted-frame-development/development-revisions.json")
SCENE = Path("site/eoere-owner-frame-v5-scene.json.gz")
ADDED = {"left": "eoere_bolt_067", "right": "eoere_bolt_070"}
COUNTS = {"sawn_members": 20, "plywood_cleats": 4, "panels": 6, "angles": 24,
          "bolt_stacks": 94, "nuts": 94, "washers": 188, "spacer_pieces": 32,
          "Hillman_axes": 66, "receiver_occurrences": 118, "occupied_parts": 1027}


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def build(out: Path):
    """Create only the six changed timber bodies and two added bolt stacks."""
    assert not out.exists(), "fresh geometry output required"
    pins = {ref(Path(__file__))["path"]: sha(Path(__file__))}
    receipt = read(PREVIOUS / "geometry.json", pins)
    parent_path = Path(receipt["checked_geometry"]["path"])
    parent = read(parent_path, pins, receipt["checked_geometry"]["sha256"])
    reference = read(REFERENCE, pins, "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d")
    prior_clearance = read(receipt["checked_clearance"]["path"], pins,
                           receipt["checked_clearance"]["sha256"])
    assert parent["revision"] == "eoere-local-front-bolt-moves-v4"
    assert prior_clearance["nominal_geometry_clear"]
    g = copy.deepcopy(parent)
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    axes = {a["id"]: a for a in g["axes"]}
    profiles = g["profiles"]
    polygon = reference["new_cleat_YZ_polygon_mm"]
    assert len(polygon) == 4 and polygon[:2] == [[-175.7, 139.7], [-36.0, 139.7]]
    out.mkdir(parents=True)
    replacements, additions, wall_proofs = set(), [], []

    def load(row):
        assert sha(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        return cq.Shape.importBrep(str(ROOT / row["path"]))

    def save(name, body, kind="timber"):
        assert body.isValid() and len(body.Solids()) == 1 and body.Volume() > 0, name
        path = out / (name + ".brep")
        assert body.exportBrep(str(path))
        box = body.BoundingBox()
        row = {"id": name, "kind": kind, **ref(path), "bytes": path.stat().st_size,
               "volume_mm3": body.Volume(), "center_of_mass_xyz_mm": list(body.Center().toTuple()),
               "bounds_xyz_mm": [getattr(box, a + end) for a in "xyz" for end in ("min", "max")]}
        registry[name] = row
        replacements.add(name)
        if name in profiles:
            profiles[name]["finished"] = row

    for side, identity in ADDED.items():
        original_id = "eoere_bolt_071" if side == "left" else "eoere_bolt_074"
        original = axes[original_id]
        new = copy.deepcopy(original)
        new["id"] = identity
        new["point_xyz_mm"][1] -= 50.8
        for attachment in new["attachments"]:
            attachment["point"][1] -= 50.8
            attachment["transverse"] *= -1
            attachment["transverse_mm"] *= -1
            attachment["installed_bolt_axis_id"] = identity
        axes[identity] = new
        roles = sorted(n[len(original_id) + 1:] for n in registry if n.startswith(original_id + "_"))
        assert set(roles) == {"shaft", "head", "head_washer", "nut_washer", "nut",
                              "spacer", "spacer_2", "spacer_3"}
        for role in roles:
            save(identity + "_" + role,
                 load(registry[original_id + "_" + role]).translate((0, -50.8, 0)), "bolt")
        selected = copy.deepcopy(next(r for r in g["selected_stack_overrides"] if r["axis_id"] == original_id))
        selected.update(axis_id=identity, Actual="", Disposition="",
                        reason="Added upper pin uses the adjacent existing factory hole and the same nominal A574 stack; complete joint checks remain open.")
        g["selected_stack_overrides"].append(selected)
        additions.append({"axis_id": identity, "copied_stack_axis": original_id,
                          "translation_xyz_mm": [0, -50.8, 0], "roles": roles})

    for side in ADDED:
        for suffix in ("", "_outer"):
            name = "eoere_cleat_" + side + suffix
            p = profiles[name]
            x = p["datum_xyz_mm"][0]
            plane = cq.Plane(origin=(x, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
            blank = cq.Workplane(plane).polyline(polygon).close().extrude(19.05).val()
            own = [a for a in axes.values() if name in a["receivers"]]
            assert len(own) == 4
            body = blank
            for a in own:
                point, direction = cq.Vector(*a["point_xyz_mm"]), cq.Vector(*a["direction_xyz"])
                cutter = cq.Solid.makeCylinder(a["bore_diameter_mm"] / 2, 250, point - direction, direction)
                removed = body.intersect(cutter).Volume()
                expected = np.pi * (a["bore_diameter_mm"] / 2) ** 2 * 19.05
                assert abs(removed - expected) < .001, (name, a["id"], removed, expected)
                wall_proofs.append({"axis_id": a["id"], "receiver": name,
                                    "full_bore_wall_mm": 19.05, "removed_volume_mm3": removed})
                body = body.cut(cutter).clean()
            p.update(blank_mm=[max(z for _, z in polygon) - 139.7, 139.7, 19.05],
                     datum_xyz_mm=[x, -175.7, 139.7],
                     vertices_luv_mm=[[z - 139.7, u, y + 175.7] for y, z in polygon for u in (0., 19.05)],
                     end_planes=[],
                     material="Two nominal 19.05-mm plywood leaves per corner; reference perimeter; bond and strength unqualified")
            save(name, body)

        name = "base_side_" + side
        a = axes[ADDED[side]]
        before = load(profiles[name]["finished"])
        point, direction = cq.Vector(*a["point_xyz_mm"]), cq.Vector(*a["direction_xyz"])
        cutter = cq.Solid.makeCylinder(a["bore_diameter_mm"] / 2, 250, point - direction, direction)
        removed = before.intersect(cutter).Volume()
        expected = np.pi * (a["bore_diameter_mm"] / 2) ** 2 * 88.9
        assert abs(removed - expected) < .001, (name, removed, expected)
        wall_proofs.append({"axis_id": a["id"], "receiver": name,
                            "full_bore_wall_mm": 88.9, "removed_volume_mm3": removed})
        save(name, before.cut(cutter).clean())

    verify_attachment_axes(list(axes.values()), expected_ports=94)
    assert len(axes) == 94 and len(replacements) == 22
    assert g["screw_axes"] == parent["screw_axes"] and len(g["screw_axes"]) == 66
    assert all(axes[a["id"]] == a for a in parent["axes"])
    # Restoring the historical pair also restores its unresolved geometry duties.
    # These distances describe the actual factory pattern, never a capacity pass.
    pair_geometry = []
    for side, identity in ADDED.items():
        p = profiles["base_side_" + side]
        basis = np.asarray(p["basis_grain_u_v_xyz"])
        points = [basis @ (np.asarray(axes[i]["point_xyz_mm"]) - p["datum_xyz_mm"])
                  for i in (identity, "eoere_bolt_071" if side == "left" else "eoere_bolt_074")]
        vmax = max(v[2] for v in p["vertices_luv_mm"])
        pair_geometry.append({"side": side, "added_axis_id": identity,
                              "added_axis_near_edge_mm": float(vmax - points[0][2]),
                              "pair_grain_projection_mm": float(abs(points[1][0] - points[0][0])),
                              "perpendicular_loaded_edge_4D_marker_mm": 4 * 9.525,
                              "perpendicular_row_3p75D_marker_mm": 3.75 * 9.525,
                              "complete_oblique_pair_eligibility_established": False})
    g.update(revision=REVISION, current_bolt_count=94,
             axes=list(axes.values()), changed_finished_solids=list(registry.values()),
             removed_axes=[i for i in g["removed_axes"] if i not in ADDED.values()],
             omitted_cleat_axis_ids=[],
             retained_cleat_axis_ids=sorted(a["id"] for a in axes.values()
                                          if any(n.startswith("eoere_cleat_") for n in a["receivers"])),
             unbolted_factory_contact_receivers=[r for r in g["unbolted_factory_contact_receivers"]
                                                if r["angle_id"] not in {"eoere_clip_angle_base_left", "eoere_clip_angle_base_right"}],
             reference_cleat_revision={"parent": ref(parent_path), "outline_source": ref(REFERENCE),
                                       "outline_yz_mm": polygon, "leaf_thickness_mm": 19.05,
                                       "added_stacks": additions, "replacement_part_ids": sorted(replacements),
                                       "full_wall_proofs": wall_proofs, "upper_pair_geometry": pair_geometry,
                                       "fresh_stock_design_only": True},
             new_response_computed=False, geometry_adopted=False, complete_joint_qualified=False,
             scope="Restore reference trapezoid perimeter and two upper plus two lower cleat pins per corner; retain current frame and paired plywood thickness.",
             engineering_question="Does the requested reference cleat and complete four-pin pattern fit the current frame without unintended interference?",
             source_sha256={**g["source_sha256"], **pins})
    path = out / "geometry.json"
    path.write_bytes(encode(g))
    # Use the existing complete occupied registry and exact solid method.
    # The previous receipt covers unchanged pairs; only 22 bodies need querying.
    code = inspect.getsource(clearance.check)
    before = "    for first in sorted(changed):"
    assert code.count(before) == 1
    code = code.replace(before, "    for first in sorted(REPLACEMENT_IDS):")
    scope = {**vars(clearance), "REPLACEMENT_IDS": replacements}
    exec(compile(code, str(Path(__file__)), "exec"), scope)  # noqa: S102 -- reuse the source-bound incremental clearance method
    scope["check"](path, out / "clearance.json")
    result = json.loads((out / "clearance.json").read_text())
    assert result["nominal_geometry_clear"] and result["occupied_part_count"] == 1027
    assert all(sha(p) == h for p, h in pins.items()), "input changed during geometry build"
    print(json.dumps({"geometry": ref(path), "changed_parts": 22, "counts": COUNTS,
                      "upper_pair_geometry": pair_geometry}), flush=True)


def publish(out: Path):
    """Publish a small overlay and coordinated review records, preserving v4."""
    assert not (ROOT / PACKET).exists() and not (ROOT / SCENE).exists()
    previous = json.loads((ROOT / INDEX).read_bytes())
    assert previous["schema"] == "bolted_frame_development_revisions/v9"
    g = json.loads((out / "geometry.json").read_bytes())
    checked = json.loads((out / "clearance.json").read_bytes())
    assert g["revision"] == REVISION and checked["geometry"] == ref(out / "geometry.json")
    assert checked["nominal_geometry_clear"] and checked["occupied_part_count"] == 1027
    (ROOT / PACKET).mkdir()
    files = {}

    def put(name, value):
        path = ROOT / PACKET / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else encode(value))
        files[name] = ref(path)

    def rows(name):
        return list(csv.DictReader(io.StringIO((ROOT / PREVIOUS / name).read_text())))

    def table(values):
        keys = list(dict.fromkeys(k for row in values for k in row))
        return shop.csv_bytes([{k: row.get(k, "") for k in keys} for row in values])

    profiles, axes = g["profiles"], {a["id"]: a for a in g["axes"]}
    members = rows("members.csv")
    for row in members:
        p = profiles[row["member"]]
        for key, value in zip(("nominal_blank_length_mm", "nominal_blank_depth_mm", "nominal_blank_thickness_mm"), p["blank_mm"], strict=True):
            row[key] = value
        for c, value in zip("xyz", p["datum_xyz_mm"], strict=True):
            row["datum_" + c + "_mm"] = value
        row.update(current_finished_source_path=p["finished"]["path"], current_finished_source_sha256=p["finished"]["sha256"])
    holes = rows("receiver-holes.csv")
    for identity in ADDED.values():
        for name in axes[identity]["receivers"]:
            holes.append({"axis_id": identity, "receiver": name,
                          "nominal_shaft_diameter_mm": 9.525,
                          "modeled_bore_envelope_diameter_mm": 10.31875,
                          "Actual": "", "Disposition": ""})
    for row in holes:
        name, identity = row["receiver"], row["axis_id"]
        if not name.startswith("eoere_cleat_") and identity not in ADDED.values():
            continue
        a, p = axes[identity], profiles[name]
        box = p["finished"]["bounds_xyz_mm"]
        world = np.asarray(a["point_xyz_mm"])
        endpoints = sorted(((x - world[0]) / a["direction_xyz"][0], x) for x in box[:2])
        row["saved_full_wall_length_mm"] = endpoints[1][0] - endpoints[0][0]
        for prefix, (_, x) in zip(("entry", "exit"), endpoints, strict=True):
            q = world.copy()
            q[0] = x
            local = np.asarray(p["basis_grain_u_v_xyz"]) @ (q - p["datum_xyz_mm"])
            for c, value in zip("luv", local, strict=True):
                row[prefix + "_in_receiver_" + c + "_mm"] = float(value)
    assert len(members) == 30 and len(holes) == 118
    put("axes.json", {"axes": g["axes"], "screw_axes": g["screw_axes"], "fitting_poses": g["fitting_poses"]})
    put("current_profiles.json", profiles)
    put("members.csv", table(members))
    put("receiver-holes.csv", table(holes))
    put("hardware-additions.csv", table([r for r in g["selected_stack_overrides"] if r["axis_id"] in ADDED.values()]))
    lines = ["# Reference cleat and restored upper pair", "", "Applies to `" + REVISION + "`.", "",
             "The four plywood leaves use the preserved reference's straight sloping top and rectangular lower portion. Each corner now has two upper bolts and two lower bolts. Leaf thickness remains 19.05 mm; total nominal thickness remains 38.1 mm.", "",
             "These are geometry-review coordinates. Restoring the factory upper pair reopens loaded-edge and oblique-row eligibility; complete strength and bond checks remain open. No cutting or drilling instructions are issued. Actual/Disposition cells stay blank.", "",
             "The two added stacks are in [hardware additions](hardware-additions.csv); the preceding 92 proposed stacks retain their [hardware review](../owner-frame-v3/hardware-review.csv). The new cleat shapes supersede old cleat sheets and nesting; other members retain their preceding dimensions.", ""]
    for name in sorted(n for n in profiles if n.startswith("eoere_cleat_")):
        p = profiles[name]
        own = [r for r in holes if r["receiver"] == name]
        drawing = shop.drawing(name, p, own)
        drawing = drawing.replace(b"millimetre datum and drill sheet", b"millimetre geometry review")
        drawing = drawing.replace(b"Exact drilling coordinates appear below.", b"Review coordinates appear below; no cutting or drilling release.")
        put("drawings/" + name + ".svg", drawing)
        lines += ["## " + name, "", "Bounding blank L × depth × thickness: **" + " × ".join(map(number, p["blank_mm"])) + " mm**. [Review drawing](drawings/" + name + ".svg).", "",
                  "World datum XYZ: `" + vector(p["datum_xyz_mm"]) + "`.", "",
                  "| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |", "| --- | --- | --- |"]
        for row in own:
            lines.append("| `" + row["axis_id"] + "` | `" + vector(float(row["entry_in_receiver_" + c + "_mm"]) for c in "luv") + "` | `" + vector(float(row["exit_in_receiver_" + c + "_mm"]) for c in "luv") + "` |")
        lines.append("")
    put("layout.md", "\n".join(lines).encode())
    report = {"schema": "eoere_reference_cleat_revision/v1", "revision": REVISION,
              "candidate": previous["evidence_candidate"], "parent_geometry": previous["geometry"],
              "checked_geometry": ref(out / "geometry.json"), "checked_clearance": ref(out / "clearance.json"),
              "counts": COUNTS, "files": files, "reference_cleat_revision": g["reference_cleat_revision"],
              "nominal_geometry_clear": True, "development_model_integrated": True,
              "current_response_computed": False, "old_force_pass_transferred": False,
              "complete_conditional_frame_evaluation": False, "upper_pair_eligible": False,
              "panel_Hillman_resolution_deferred": True, "fabrication_released": False,
              "climbing_released": False, "actual_observations": None, "producer": ref(Path(__file__))}
    receipt_path = ROOT / PACKET / "geometry.json"
    receipt_path.write_bytes(encode(report))
    registry = {r["id"]: r for r in g["changed_finished_solids"]}
    changes = []
    for name in g["reference_cleat_revision"]["replacement_part_ids"]:
        row = registry[name]
        assert sha(row["path"]) == row["sha256"]
        fabrication = {"kind": row["kind"], "owner_frame_revision": REVISION,
                       "description": "Reference cleat perimeter and restored upper pin; geometry review with unresolved joint eligibility"}
        if row["kind"] == "bolt":
            a = next(a for a in g["axes"] if name.startswith(a["id"] + "_"))
            fabrication.update(connection_name=a["id"], hardware_role=name[len(a["id"]) + 1:],
                               diameter_mm=a["diameter_mm"], delivered_part_verified=False,
                               stack_roles=["shaft", "head", "head_washer", "nut_washer", "spacer", "spacer_2", "spacer_3", "nut"],
                               selected_underhead_length_mm=203.2, nut_side_spacer_mm=38.1,
                               spacer_piece_count=3)
        elif name.startswith("eoere_cleat_"):
            fabrication.update(blank_mm=profiles[name]["blank_mm"], nominal_leaf_thickness_mm=19.05,
                               upper_bolts_per_corner=2, lower_bolts_per_corner=2,
                               actual_bond_qualified=False)
        body = cq.Shape.importBrep(str(ROOT / row["path"]))
        changes.append({"id": name, "name": name, "mesh": _shape_mesh(body), "fabrication": fabrication,
                        **({"copy_metadata_from": "eoere_bolt_071" + name[len("eoere_bolt_067"):]} if name.startswith("eoere_bolt_067_") else
                           {"copy_metadata_from": "eoere_bolt_074" + name[len("eoere_bolt_070"):]} if name.startswith("eoere_bolt_070_") else {})})
    patch = {"schema": "eoere_reference_cleat_patch/v1", "revision": REVISION,
             "key": "eoere-current-frame-development", "parent_scene": previous["geometry"]["scene"],
             "parent_layout": previous["geometry"]["receipt"], "layout_report": ref(receipt_path),
             "part_count": 1027, "counts": COUNTS, "replacements": changes, "removals": [],
             "historical_capacity_transferred": False, "complete_conditional_frame_evaluation": False,
             "current_response_computed": False, "upper_pair_eligible": False,
             "panel_Hillman_resolution_deferred": True, "fabrication_released": False, "climbing_released": False}
    patch["triangle_topologies"] = _deduplicate_triangle_topologies(changes)
    decoded = (json.dumps(patch, separators=(",", ":"), allow_nan=False) + "\n").encode()
    (ROOT / SCENE).write_bytes(gzip.compress(decoded, compresslevel=9, mtime=0))
    scene_ref = {**ref(SCENE), "decoded_sha256": hashlib.sha256(decoded).hexdigest()}
    index = {"schema": "bolted_frame_development_revisions/v10", "candidate": previous["candidate"],
             "evidence_candidate": previous["evidence_candidate"],
             "geometry": {"revision": REVISION, "viewer": patch["key"], "receipt": ref(receipt_path), "scene": scene_ref},
             "hardware_model": {**copy.deepcopy(previous["hardware_model"]), "revision": REVISION, "receipt": ref(receipt_path)},
             "selected_baseline": copy.deepcopy(previous["selected_baseline"]),
             "shop": {"revision": REVISION, "geometry": ref(receipt_path), "result": ref(receipt_path),
                      "packet": "docs/bolted-frame-development/builder-plan.md", "shop_planning_only": True,
                      "instructions_current_for_fabrication": False},
             "conditional_frame_evaluation": None, "panel_Hillman_resolution_deferred": True,
             "fabrication_released": False, "climbing_released": False,
             "preserved_owner_v4_viewer": "eoere-owner-frame-v4-development", "preceding_revision": previous}
    (ROOT / INDEX).write_bytes(encode(index))
    print(json.dumps({"geometry": ref(receipt_path), "scene": scene_ref, "changed_parts": 22}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "publish"))
    parser.add_argument("--out", type=Path, default=ROOT / BASE / "geometry")
    args = parser.parse_args()
    (build if args.action == "build" else publish)(args.out.resolve())
