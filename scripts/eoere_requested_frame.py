"""Build the owner's retained frame without the rejected outboard returns.

Reuse current finished timber, suppressed-bore geometry and mesh exporters.
This is a fresh-stock design revision, never instructions to fill old holes.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from scripts.eoere_paired_frame_basis import ROOT, RAW, read, ref, sha

PACKET = Path("docs/bolted-frame-development/paired-frame-v2")
REVISION = "eoere-retained-frame-trimmed-three-quarter-v3"


def build(out: Path, thickness: float = 19.05):
    assert not out.exists() and 0 < thickness <= 28.575
    pins = {ref(Path(__file__))["path"]: sha(Path(__file__))}
    receipt = read(PACKET / "geometry.json", pins)
    parent_path = Path(receipt["checked_geometry"]["path"])
    parent = read(parent_path, pins, receipt["checked_geometry"]["sha256"])
    previous = read(Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/"
                         "thin-frame-comparison/eoere-successor-v1/leg-header-v3/"
                         "current_profiles.json"), pins)
    field = read(RAW / "frame-completion-v1/retained-2x6-A574-cases-v2/nominal/"
                 "three-pin-shift-corner-floor-a12-forward-v1/field.json", pins)
    g = copy.deepcopy(parent)
    profiles = g["profiles"]
    changed = {r["id"]: r for r in g["changed_finished_solids"]}
    original = copy.deepcopy(changed)
    removed_axes = {a["id"] for a in g["axes"] if a["id"].startswith("outboard_")}
    removed_wood = {f"outboard_{k}_{s}" for k in ("knee", "leg_packer")
                    for s in ("left", "right")}
    removed_angles = {f"outboard_knee_angle_{s}" for s in ("left", "right")}
    assert len(removed_axes) == 10
    removed = removed_wood | removed_angles | {
        n for n in changed if any(n.startswith(a + "_") for a in removed_axes)}
    for n in removed:
        changed.pop(n, None)
        profiles.pop(n, None)
    g["axes"] = [a for a in g["axes"] if a["id"] not in removed_axes]
    g["fitting_poses"] = [p for p in g["fitting_poses"] if p["id"] not in removed_angles]
    g["unbolted_factory_contact_receivers"] = [r for r in g["unbolted_factory_contact_receivers"]
                                              if r["angle_id"] not in removed_angles]
    out.mkdir(parents=True)

    def load(row):
        assert sha(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        return cq.Shape.importBrep(str(ROOT / row["path"]))

    def save(name, shape, kind="timber"):
        assert shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0, name
        path = out / (name + ".brep")
        assert shape.exportBrep(str(path))
        box = shape.BoundingBox()
        row = {"id": name, "kind": kind, "path": str(path.relative_to(ROOT)),
               "sha256": sha(path), "bytes": path.stat().st_size,
               "volume_mm3": shape.Volume(),
               "center_of_mass_xyz_mm": list(shape.Center().toTuple()),
               "bounds_xyz_mm": [getattr(box, a + end) for a in "xyz" for end in ("min", "max")]}
        changed[name] = row
        if name in profiles:
            profiles[name]["finished"] = row
        return row

    # Restore the original cap and its holes. The lower header is untouched.
    name = "base_rail_top"
    profiles[name] = copy.deepcopy(previous[name])
    save(name, load(previous[name]["finished"]))
    restorations = []
    shaft_rows = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
    for side in ("left", "right"):
        name = "base_side_" + side
        before = load(profiles[name]["finished"])
        old = load(previous[name]["finished"])
        cap_region = cq.Solid.makeBox(4000, 4000, 1000, cq.Vector(-2000, -1000, 2050))
        # Only the upper cap is restored; current lower and +15 mm leg bores survive.
        extra = old.intersect(cap_region).cut(before)
        after = before.fuse(extra).clean()
        restorations.append({"member": name, "restored_top_cap_mm3": after.Volume() - before.Volume()})
        profiles[name]["vertices_luv_mm"] = copy.deepcopy(previous[name]["vertices_luv_mm"])
        save(name, after)
        name = "lumber_leg_" + side
        before = load(profiles[name]["finished"])
        after = before
        for a in parent["axes"]:
            if not a["id"].startswith("outboard_leg_lap_" + side):
                continue
            shaft = shaft_rows[a["id"]]
            wall = next(r for r in shaft["surfaces"] if r["host"] == name)
            lo, hi = wall["interval_mm"]
            p, d = cq.Vector(*a["point_xyz_mm"]), cq.Vector(*a["direction_xyz"])
            # The existing recess is 12.7 deep with a 31.75 mm diameter.
            stock_end = lo - 12.7
            plugs = [cq.Solid.makeCylinder(a["bore_diameter_mm"] / 2, hi - stock_end,
                                          p + d * stock_end, d),
                     cq.Solid.makeCylinder(31.75 / 2, 12.7, p + d * stock_end, d)]
            for plug in plugs:
                after = after.fuse(plug).clean()
        save(name, after)
        restorations.append({"member": name, "suppressed_return_holes_mm3": after.Volume() - before.Volume(),
                             "fresh_stock_only_not_a_repair_instruction": True})

    # Project the surrounding header/post/rim outline onto each cleat plane.
    # This preserves the actual perimeter instead of a rectangular bounding box.
    def projection(profile, x, t):
        world = (np.asarray(profile["datum_xyz_mm"]) +
                 np.asarray(profile["vertices_luv_mm"]) @ np.asarray(profile["basis_grain_u_v_xyz"]))
        points = np.unique(np.round(world[:, 1:], 8), axis=0)
        polygon = points[ConvexHull(points).vertices]
        plane = cq.Plane(origin=(x, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
        return cq.Workplane(plane).polyline(polygon.tolist()).close().extrude(t).val()

    cleat_axes = [a for a in g["axes"] if any(n.startswith("eoere_cleat_") for n in a["receivers"])]
    outline_rows = []
    for side in ("left", "right"):
        interface = -1219.2 if side == "left" else 1216.025
        for i, suffix in enumerate(("", "_outer")):
            name = "eoere_cleat_" + side + suffix
            x = interface - (i + 1) * thickness if side == "left" else interface + i * thickness
            perimeter = projection(profiles["base_post_outer_" + side], x, thickness)
            for host in ("base_header", "base_side_" + side):
                perimeter = perimeter.fuse(projection(profiles[host], x, thickness)).clean()
            window = cq.Solid.makeBox(thickness, 203.2, 609.6, cq.Vector(x, -213.8, 139.7))
            blank = perimeter.intersect(window).clean()
            assert len(blank.Solids()) == 1
            polygon = sorted({(round(v.Y, 8), round(v.Z, 8)) for v in blank.Vertices()})
            profile = profiles[name]
            profile.update(blank_mm=[609.6, 203.2, thickness], datum_xyz_mm=[x, -213.8, 139.7],
                           vertices_luv_mm=[[v.Z - 139.7, v.X - x, v.Y + 213.8] for v in blank.Vertices()],
                           material="Two independent nominal3/4in structural plywood leaves per corner; unqualified revision")
            body = blank
            holes = []
            for a in cleat_axes:
                if name not in a["receivers"]:
                    continue
                p, d = cq.Vector(*a["point_xyz_mm"]), cq.Vector(*a["direction_xyz"])
                hole = cq.Solid.makeCylinder(a["bore_diameter_mm"] / 2, 250, p - d, d)
                before = body.Volume()
                body = body.cut(hole).clean()
                assert before - body.Volume() > 1, (name, a["id"])
                holes.append({"axis_id": a["id"], "center_yz_mm": [p.y, p.z]})
            assert len(holes) == 3
            save(name, body)
            outline_rows.append({"member": name, "outline_vertices_yz_mm": polygon,
                                 "nominal_leaf_thickness_mm": thickness, "holes": holes})
    # Move only the nut-side hardware to the thinner stack. Three existing
    # factory spacers keep nominal nuts past the A574 shank; delivered-window
    # qualification remains a separate, explicitly required check.
    metal_moves = []
    selected = copy.deepcopy(parent["selected_stack_overrides"])
    for a in cleat_axes:
        old_grip = a["grip_mm"]
        a["grip_mm"] = 88.9 + 2 * thickness
        a["nut_side_spacer_mm"] = 38.1
        delta_grip = a["grip_mm"] - old_grip
        direction = cq.Vector(*a["direction_xyz"])
        for role, along in [("nut_washer", delta_grip), ("spacer", delta_grip),
                            ("spacer_2", delta_grip), ("nut", delta_grip + 12.7)]:
            name = a["id"] + "_" + role
            save(name, load(changed[name]).translate(direction * along), "bolt")
            metal_moves.append({"id": name, "along_axis_mm": along})
        name = a["id"] + "_spacer_3"
        save(name, load(changed[a["id"] + "_spacer_2"]).translate(direction * 12.7), "bolt")
        for r in selected:
            if r["axis_id"] == a["id"]:
                r.update(nut_side_spacer_mm=38.1, spacer_piece_count=3,
                         delivered_part_or_thread_window_verified=False)
    selected = [r for r in selected if r["axis_id"] not in removed_axes]
    assert len(g["axes"]) == 92 and len(g["fitting_poses"]) == 24 and len(profiles) == 30
    delta_ids = sorted(n for n, r in changed.items() if n not in original or r["sha256"] != original[n]["sha256"])
    g.update(revision=REVISION, current_bolt_count=92, current_angle_count=24,
             changed_finished_solids=list(changed.values()), selected_stack_overrides=selected,
             removed_axes=list(dict.fromkeys([*g["removed_axes"], *sorted(removed_axes)])),
             geometry_adopted=False, new_response_computed=False, complete_joint_qualified=False,
             owner_requested_revision={"parent": ref(parent_path), "removed_member_ids": sorted(removed_wood),
                                       "removed_angle_ids": sorted(removed_angles), "removed_axis_ids": sorted(removed_axes),
                                       "removed_part_ids": sorted(removed), "replacement_part_ids": delta_ids,
                                       "top_rail_length_before_mm": 2765.425, "top_rail_length_after_mm": 2257.425,
                                       "restorations": restorations, "cleats": outline_rows, "nut_hardware_moves": metal_moves,
                                       "two_leaves_are_adjacent_outside_each_corner": True,
                                       "no_glue_friction_or_composite_action_credit": True},
             checks_pending=["Own revised geometry and installed hardware windows", "Own revised actions and plywood/joint checks"],
             scope="Owner-directed removal of both outboard knees/packers and rail extension; four trimmed3/4in plywood leaves at lower header corners. No inherited frame pass.",
             engineering_question="Does the requested simpler current frame and two3/4in cleats per corner work without the rejected outboard return?",
             source_sha256={**g["source_sha256"], **pins})
    path = out / "geometry.json"
    path.write_text(json.dumps(g, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"geometry": ref(path), "changed_parts": len(delta_ids), "removed_parts": len(removed),
                      "axes": len(g["axes"]), "angles": len(g["fitting_poses"]), "cleat_thickness_mm": thickness}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--thickness-mm", type=float, default=19.05)
    args = parser.parse_args()
    build(args.output.resolve(), args.thickness_mm)
