"""Resolve lower-joint conflicts in a separate HL35 v3 geometry experiment.

Changes are proposals for an unadopted candidate. No source model or frozen
failure is rewritten, and catalog or full-joint resistance is not supplied.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as base
from scripts import hl35_revised_candidate as previous

REVISION = "hl35-lower-fit-and-screw-clearance-v3"
PACKET = base.PACKET / "lower-fit-v3"
T, N, X = previous.T, previous.N, previous.X


def geometry(source: dict) -> tuple[dict, dict]:
    wood, dims = previous.revised_wood(source)
    dims["toe_t_mm"] = base.projected_extent(source["main_lower_left"], T)[0] + 31.7
    nmin, nmax = dims["n_mm"]
    toe = dims["toe_t_mm"]
    for name in ("base_side_left", "base_side_right", "hl35_center_principal"):
        b = wood[name].BoundingBox()
        hi = dims["top_t_mm"][0] if name == "hl35_center_principal" else dims["top_t_mm"][1]
        wood[name] = previous.prism(b.xmin, b.xmax, toe, hi, nmin, nmax)
    for side in ("left", "right"):
        name = f"base_rail_bottom_{side}"
        b = wood[name].BoundingBox()
        lo, _ = base.projected_extent(source[name], T)
        wood[name] = previous.prism(b.xmin, b.xmax, lo, lo + 139.7, nmin, nmax)
    front, back, underside = -36.0, -175.7, 238.9
    kink_z = (nmin + front * math.cos(math.radians(40))) / math.sin(math.radians(40))
    front_top = T.multiply(toe) + N.multiply(nmin)
    back_top_z = (toe - back * T.y) / T.z
    points = [(back, underside), (front, underside), (front, kink_z),
              (front_top.y, front_top.z), (back, back_top_z)]
    wood["base_header"] = previous.yz_prism(*dims["header_x_mm"], points)
    dims["header_yz_profile_mm"] = points
    dims["header_underside_z_mm"] = underside
    post_changes = []
    for side in ("left", "right"):
        for kind in ("outer", "center"):
            name = f"base_post_{kind}_{side}"
            b = wood[name].BoundingBox()
            center = (b.xmin + b.xmax) / 2
            if kind == "outer":
                center += -19.05 if side == "left" else 19.05
            shape = cq.Solid.makeBox(88.9, 139.7, underside,
                                     cq.Vector(center - 44.45, back, 0))
            if kind == "outer":
                # Fit over the existing runner without occupying it or adding a floor pad.
                runner = source[f"base_floor_{side}"]
                shape = shape.cut(runner).clean()
            wood[name] = shape
            post_changes.append({"member": name, "x_center_mm": center,
                                 "x_outboard_offset_mm": 19.05 if kind == "outer" else 0,
                                 "runner_housing_present": kind == "outer"})
    seam = -1.5875
    backer = cq.Solid.makeBox(88.9, 88.9, underside - 25.4,
                              cq.Vector(seam - 44.45, -124.9, 25.4))
    neck_center, neck_half, relief = -.68, 33.0, 5.5
    b = backer.BoundingBox()
    for left, right in ((b.xmin - 1, neck_center - neck_half),
                        (neck_center + neck_half, b.xmax + 1)):
        backer = backer.cut(cq.Solid.makeBox(right - left, b.ylen + 2, relief + 1,
                           cq.Vector(left, b.ymin - 1, underside - relief))).clean()
    wood["hl35_kicker_seam_backer"] = backer
    ties = []
    for index, x in enumerate((neck_center - 15.875, neck_center + 15.875), 1):
        y = -80.45
        local_top = (toe - y * T.y) / T.z
        head_top = local_top - 19.05 * math.tan(math.radians(40)) - 3
        seat = head_top - 11.6
        counterbore = cq.Solid.makeCylinder(19.05, local_top - seat + 30,
                                           cq.Vector(x, y, seat), cq.Vector(0, 0, 1))
        wood["base_header"] = wood["base_header"].cut(counterbore).clean()
        ties.append({"id": f"hl35_seam_backer_tie_{index}", "axis_kind": "auxiliary_through_tie",
                     "point": cq.Vector(x, y, seat), "direction": cq.Vector(0, 0, -1),
                     "grip_mm": seat - 25.4, "diameter_mm": 7.9375,
                     "receivers": ["base_header", "hl35_kicker_seam_backer"],
                     "attachments": [], "spotface_head_seat_z_mm": seat,
                     "catalog_hardware_selected": False})
    dims["seam_backer_neck"] = {"center_x_mm": neck_center, "width_x_mm": neck_half * 2,
                               "top_relief_depth_mm": relief, "tie_pitch_mm": 31.75}
    dims["seam_backer_ties"] = [{k: base.xyz(v) if isinstance(v, cq.Vector) else v
                                for k, v in row.items()} for row in ties]
    dims["kicker_post_changes"] = post_changes
    return wood, dims


def angles(wood: dict, dims: dict) -> list[base.Angle]:
    result = previous.revised_angles(wood, dims)
    final = []
    nmid = sum(dims["n_mm"]) / 2
    for a in result:
        origin, v = a.origin, a.v
        if a.duty.startswith("principal_header_"):
            origin += N.multiply(6.35)  # restore centered bend at the now-deeper upper seat
        if a.duty.startswith("kicker_header_"):
            origin += cq.Vector(0, 0, 50.8)
        if a.duty.startswith("rail_bottom_"):
            _, hi = base.projected_extent(wood[a.beam], T)
            origin = X.multiply(a.origin.x) + T.multiply(hi) + N.multiply(nmid)
            v = T
        final.append(previous.placed_angle(a.duty, a.id.rsplit("_", 1)[1], a.beam, a.post, origin, a.u, v))
    return final


def remap(snapshot: dict, inventory: dict) -> tuple[dict, dict, list[dict], list[dict]]:
    snapshot, inventory, changes = previous.remap_receivers(snapshot, inventory)
    # Raising the header underside retains the old upper kicker receivers.
    originals = {r["axis_id"]: r for r in base.load_sources()[1]["fixed_panel_kicker_screws"]}
    original_moves = {r["axis_id"]: r for r in base.load_sources()[0]["panel_screws"]}
    moves = {r["axis_id"]: r for r in snapshot["panel_screws"]}
    changes = [r for r in changes if not r["old_receiver"].startswith("base_post_")]
    proposed = []
    for row in inventory["fixed_panel_kicker_screws"]:
        name = row["axis_id"]
        old_move = original_moves.get(name)
        old_receiver = old_move["receiver_member"] if old_move else originals[name]["candidate_finished_receiver_member"]
        if old_receiver.startswith("base_post_"):
            row["candidate_finished_receiver_member"] = old_receiver
            if name in moves:
                moves[name]["receiver_member"] = old_receiver
        if name.startswith("round_kicker_") and name.endswith("_2") and ("_rim_" in name or "_center_" in name):
            old_point = old_move["new_start_global_xyz_mm"] if old_move else originals[name]["origin_global_xyz_mm"]
            new_point = [old_point[0], old_point[1], 173.05]
            move = moves.get(name, {"axis_id": name, "receiver_member": old_receiver})
            move["new_start_global_xyz_mm"] = new_point
            if name not in moves:
                snapshot["panel_screws"].append(move)
            moves[name] = move
            proposed.append({"axis_id": name, "old_point_xyz_mm": old_point, "new_point_xyz_mm": new_point,
                             "translation_xyz_mm": [0, 0, 173.05 - old_point[2]], "new_receiver": old_receiver,
                             "reason": "Clear the 1/2-inch HL35 post bolt at Z188.1; purchased count and screw length retained",
                             "physical_move_authorized_or_performed": False})
    return snapshot, inventory, changes, proposed


def raw_line_span(shape: cq.Shape, point: cq.Vector, direction: cq.Vector) -> tuple[float, float]:
    lo, hi = base.projected_extent(shape, direction)
    start = point + direction.multiply(lo - point.dot(direction) - 1)
    probe = cq.Solid.makeCylinder(.05, hi - lo + 2, start, direction)
    material = shape.intersect(probe)
    if not material.Solids():
        raise ValueError("planned axis misses its receiver")
    return base.projected_extent(material, direction)


def prepare_axis_grips(wood: dict, axes: list[dict]) -> tuple[dict, list[dict]]:
    wood = dict(wood)
    spotfaces = []
    for axis in axes:
        p, d = axis["point"], axis["direction"]
        name = axis["receiver"]
        axis["receivers"] = [name]
        axis["diameter_mm"] = 12.7
        axis["axis_kind"] = "hl35_through_bolt"
        lo, hi = raw_line_span(wood[name], p, d)
        axis["point"] = p + d.multiply(lo - p.dot(d))
        exit_point = p + d.multiply(hi - p.dot(d))
        if name == "base_header":
            # Inclined exit surfaces require a real washer seat, not a floating washer.
            depth = 25.4
            seat = exit_point - d.multiply(depth)
            cutter = cq.Solid.makeCylinder(19.05, 1000, seat, d)
            wood[name] = wood[name].cut(cutter).clean()
            hi -= depth
            spotfaces.append({"axis_id": axis["id"], "receiver": name,
                              "seat_point_xyz_mm": base.xyz(seat), "direction_xyz": base.xyz(d),
                              "conditional_diameter_mm": 38.1, "center_depth_mm": depth,
                              "actual_tool_or_cut_released": False})
        axis["grip_mm"] = hi - lo
        axis["point_xyz_mm"] = base.xyz(axis["point"])
        if axis["grip_mm"] < 88.9 - .05:
            axis["minimum_grip_failed"] = True
    return wood, spotfaces


def starting_axes(inventory: dict) -> list[dict]:
    axes = []
    for row in inventory["starting_frame_bolts"]:
        p, d = cq.Vector(*row["origin_global_xyz_mm"]), cq.Vector(*row["axis_global_xyz"])
        front = p + d.multiply(2.032 if row["axis_id"].startswith("rail_") else 3.175)
        grip = row["source_grip_mm"]
        if row["axis_id"].startswith("rail_front_"):
            grip += 31.75
            front -= d.multiply(31.75)
        axes.append({"id": row["axis_id"], "point": front, "direction": d, "grip_mm": grip,
                     "diameter_mm": row["source_occupied_diameter_mm"], "receivers": row["members"],
                     "attachments": [], "axis_kind": "starting_frame_bolt",
                     "old_grip_mm": row["source_grip_mm"], "source_head_origin_xyz_mm": row["origin_global_xyz_mm"]})
    return axes


def metal(axis: dict) -> list[tuple[str, cq.Shape]]:
    d, p, grip = cq.Vector(0, 0, 1), cq.Vector(0, 0, 0), axis["grip_mm"]
    diameter = axis["diameter_mm"]
    before = base.PLATE if axis["attachments"] else 0
    after = base.PLATE if len(axis["attachments"]) > 1 else 0
    washer = 3.0
    head_h, nut_h = (8.6, 11.2) if diameter >= 12.7 else (6.0, 8.6)
    head_r = (22.225 if diameter >= 12.7 else 14.2875) / math.sqrt(3)
    start = -before - washer
    # A quarter-inch length allowance is display only, not a selected retail SKU.
    length = math.ceil((grip + before + after + 2 * washer + nut_h + 4) / 6.35) * 6.35
    axis["conditional_under_head_length_mm"] = length
    def cylinder(radius: float, height: float, z: float) -> cq.Shape:
        return cq.Solid.makeCylinder(radius, height, p + d.multiply(z), d)
    def annulus(z: float) -> cq.Shape:
        return cylinder(19.05, washer, z).cut(cylinder(diameter / 2 + .4, washer, z))
    return [("shaft", cylinder(diameter / 2, length, start)),
            ("head", cylinder(head_r, head_h, start - head_h)),
            ("head_washer", annulus(start)), ("nut_washer", annulus(grip + after)),
            ("nut", cylinder(head_r, nut_h, grip + after + washer).cut(
                cylinder(diameter / 2, nut_h, grip + after + washer)))]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=base.ROOT / "site/hl35-fit-v3-scene.json")
    args = parser.parse_args()
    original_snapshot, original_inventory, parent = base.load_sources()
    source, shifts = base.reconstructed_wood(original_snapshot)
    wood, dims = geometry(source)
    aa = angles(wood, dims)
    snapshot, inventory, receiver_changes, screw_moves = remap(original_snapshot, original_inventory)
    print(f"Auditing {len(aa)} angles and four proposed screw moves", flush=True)
    report, axes = base.audit(wood, aa, snapshot, inventory)
    report["revision"] = REVISION
    report["counts"]["duties"] = len(report["duties"])
    report["counts"]["auxiliary_seam_backer_tie_axes"] = 2
    report["counts"]["new_proposed_screw_axis_moves"] = len(screw_moves)
    report["proposed_screw_moves"] = screw_moves
    report["changed_screw_receiver_identities"] = receiver_changes
    report["layout_parameters"] = dims
    receiving_ids = set(shifts) - {"base_principal_center_left", "base_principal_center_right"}
    receiving_ids.update({"hl35_center_principal", "hl35_kicker_seam_backer"})
    member_clashes = [{"first": a, "second": b, "intersection_mm3": round(volume, 3)}
                      for i, a in enumerate(sorted(receiving_ids)) for b in sorted(receiving_ids)[i + 1:]
                      if (volume := base.overlaps(wood[a], wood[b])) > .01]
    report["new_raw_member_intersections"] = member_clashes
    report["counts"]["raw_member_intersections"] = len(member_clashes)
    report["counts"]["panel_screw_axes_without_raw_receiver"] = sum(r["raw_receiver_intersection_mm3"] < .01 for r in report["panel_screw_axes"])
    finished, spotfaces = prepare_axis_grips(wood, axes)
    report["washer_spotfaces"] = spotfaces
    report["counts"]["hl35_axis_grips_below_88_9_mm"] = sum(axis.get("minimum_grip_failed", False) for axis in axes)
    frame_axes = starting_axes(original_inventory)
    tie_axes = [{**row, "point": cq.Vector(*row["point"]), "direction": cq.Vector(*row["direction"])}
                for row in dims["seam_backer_ties"]]
    all_axes = axes + frame_axes + tie_axes
    report["counts"]["total_proposed_structural_bolt_axes"] = len(all_axes)
    report["installed_axes"] = []
    for axis in all_axes:
        metal(axis)
        report["installed_axes"].append({k: base.xyz(v) if isinstance(v, cq.Vector) else v
                                          for k, v in axis.items() if k != "attachments"})
    report["status"] = "REVISE"
    report["joint_architecture"] = {
        "pair_rule_qualified": False,
        "single_angle_scope": "Beam-end compression is a separate proposed wood contact path. A single angle does not receive bidirectional catalog lateral credit; transverse and moment transfer remain unqualified.",
        "complete_joint_resistance_qualified": False,
        "seam_backer_ties": "Two 5/16-inch occupied through-tie axes; end-grain transfer and real hardware selection remain open.",
    }
    report["retained_frame_bolt_changes"] = [
        {"axis_id": a["id"], "old_grip_mm": a["old_grip_mm"], "new_grip_mm": a["grip_mm"],
         "new_wood_face_xyz_mm": base.xyz(a["point"]), "diameter_mm": a["diameter_mm"],
         "new_nominal_length_allowance_mm": a["conditional_under_head_length_mm"], "line_moved": False,
         "delivered_thread_window_qualified": False} for a in frame_axes]
    args.out.mkdir(parents=True, exist_ok=True)
    print(json.dumps(report["counts"], sort_keys=True), flush=True)
    # Shared mesh encoder/template structure; rebuild the metal using actual local grip lengths.
    scene = base.export_scene(report, finished, {name: cq.Vector() for name in sorted(receiving_ids)}, aa, [])
    templates = scene["mesh_templates"]
    solids = scene["solids"]
    def add_mesh(name: str, shape: cq.Shape, kind: str, description: str, **extra) -> None:
        solids.append({"id": name, "name": name, "mesh": base._shape_mesh(shape),
                       "fabrication": {"kind": kind, "description": description, **extra}})
    for axis in all_axes:
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        transform = [*base.xyz(plane.xDir), 0, *base.xyz(plane.yDir), 0, *base.xyz(plane.zDir), 0, *base.xyz(plane.origin), 1]
        for role, shape in metal(axis):
            key = f'hardware_{axis["diameter_mm"]}_{axis["grip_mm"]:.6f}_{len(axis["attachments"])}_{role}'
            if key not in templates:
                mesh = base._shape_mesh(shape)
                index = base._deduplicate_triangle_topologies([{"mesh": mesh}])
                scene["triangle_topologies"].update(index)
                templates[key] = {"id": key, "mesh": mesh}
            name = f'{axis["id"]}_{role}'
            solids.append({"id": name, "name": name, "template_id": key, "transform": transform,
                           "fabrication": {"kind": "bolt", "description": "Conditional metal occupancy; root/thread/product/strength and access unqualified",
                               "connection_name": axis["id"], "hardware_role": role,
                               "stack_roles": ["shaft", "head", "head_washer", "nut_washer", "nut"]}})
    # Source kicker raw panels have no mounting bores; cut only this candidate's nine axes per panel.
    for panel in ("kicker_left", "kicker_right"):
        shape = source[panel]
        for row in report["panel_screw_axes"]:
            if original_inventory["fixed_panel_kicker_screws"][0].get("panel_member") is None:
                raise ValueError("source panel identities missing")
            source_row = next(r for r in inventory["fixed_panel_kicker_screws"] if r["axis_id"] == row["axis_id"])
            if source_row["panel_member"] != panel:
                continue
            p, d = cq.Vector(*row["origin_global_xyz_mm"]), cq.Vector(*row["axis_global_xyz"])
            shape = shape.cut(cq.Solid.makeCylinder(2.0701, 65, p - d, d)).clean()
        add_mesh(panel, shape, "panel", "Kerf-right kicker; current/proposed nine screw axes; analysis bores, not drill sizes")
    for row in screw_moves:
        p = cq.Vector(*row["new_point_xyz_mm"])
        d = cq.Vector(0, -1, 0)
        shape = cq.Solid.makeCone(4.5, 2.0701, 3, p, d).fuse(
            cq.Solid.makeCylinder(2.0701, 60.5, p + d.multiply(3), d)).clean()
        add_mesh("fastener_" + row["axis_id"], shape, "screw", "Purchased Hillman policy; measured 9 mm head diameter with unmeasured 3 mm head-height envelope")
    # New direct meshes need topology records, without re-deduplicating existing templates.
    new_meshes = [r for r in solids if "mesh" in r and "triangle_indices_base64" in r["mesh"]]
    scene["triangle_topologies"].update(base._deduplicate_triangle_topologies(new_meshes))
    scene["revision"] = REVISION
    scene["replaced_host_names"] = sorted(shifts)
    scene["removed_parent_visual_names"] = ["kicker_left", "kicker_right", *["fastener_" + r["axis_id"] for r in screw_moves]]
    scene["removed_parent_bolt_axes"] = [a["id"] for a in frame_axes]
    scene["census"] = {"timber": 16, "brackets": len(aa), "new_screw_displays": 4, "new_panel_displays": 2,
                       "displayed_structural_bolt_axes": len(all_axes), "kept_starting_metal_axes": 0,
                       "panel_kicker_screws": 66}
    scene["design"]["key"] = "hl35-fit-development"
    scene["design"]["documents"][0] = {"label": "HL35 fit revision and limits", "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/lower-fit-v3/README.md"}
    scene["changed_screw_axis_ids"] = [r["axis_id"] for r in screw_moves]
    report_path = args.out / "fit-assessment.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {"schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
                "command": ".venv/bin/python -m scripts.hl35_fit_revision", "versions": {"cadquery": cq.__version__},
                "source_sha256": {**base.SOURCE_PINS, "scripts/hl35_candidate.py": base.sha(Path(base.__file__)),
                    "scripts/hl35_revised_candidate.py": base.sha(Path(previous.__file__)),
                    "scripts/hl35_fit_revision.py": base.sha(Path(__file__))},
                "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, args.scene)},
                "release": base.RELEASE}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Fit revision scene: {args.scene.stat().st_size} bytes; SHA256 {base.sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
