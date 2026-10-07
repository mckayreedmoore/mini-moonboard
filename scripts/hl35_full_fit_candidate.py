"""Finish the HL35 pose experiment and inspect complete planning hardware.

This reuses the preserved v1-v3 geometry methods. Successful occupied fit does
not establish a manufacturer-qualified joint, wood resistance or release.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cadquery as cq
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt

from scripts import hl35_candidate as base
from scripts import hl35_fit_revision as v3
from scripts import hl35_revised_candidate as v2

REVISION = "hl35-full-hardware-and-header-fit-v4"
PACKET = base.PACKET / "full-fit-v4"


def geometry(source: dict) -> tuple[dict, dict]:
    wood, dims = v3.geometry(source)
    left, right = dims["header_x_mm"]
    for lo, hi in ((left - 19.05, left), (right, right + 19.05)):
        wood["base_header"] = wood["base_header"].fuse(
            v2.yz_prism(lo, hi, dims["header_yz_profile_mm"])).clean()
    dims["header_x_mm"] = [left - 19.05, right + 19.05]
    dims["header_end_extension_each_mm"] = 19.05
    return wood, dims


def line_span(shape: cq.Shape, point: cq.Vector, direction: cq.Vector) -> tuple[float, float]:
    """Exact line/surface crossings, rather than a global thickness projection."""
    query = IntCurvesFace_ShapeIntersector()
    query.Load(shape.wrapped, 1e-7)
    query.Perform(gp_Lin(gp_Pnt(*point.toTuple()), gp_Dir(*direction.toTuple())), -10000, 10000)
    parameters = [query.WParameter(i) for i in range(1, query.NbPnt() + 1)]
    if len(parameters) < 2:
        raise ValueError("planned axis misses its receiver or has no finite wood span")
    return min(parameters), max(parameters)


def prepare_axes(wood: dict, axes: list[dict]) -> tuple[dict, list[dict]]:
    finished, spotfaces = dict(wood), []
    # Determine every span on the same raw shape before making any spotface.
    for axis in axes:
        p, d, name = axis["point"], axis["direction"], axis["receiver"]
        near, far = line_span(wood[name], p, d)
        axis.update({"point": p + d.multiply(near), "grip_mm": far - near,
                     "receivers": [name], "diameter_mm": 12.7, "axis_kind": "hl35_through_bolt"})
        if name == "base_header":
            seat = p + d.multiply(far - 25.4)
            finished[name] = finished[name].cut(cq.Solid.makeCylinder(19.05, 1000, seat, d)).clean()
            axis["grip_mm"] -= 25.4
            spotfaces.append({"axis_id": axis["id"], "receiver": name, "seat_point_xyz_mm": base.xyz(seat),
                              "direction_xyz": base.xyz(d), "conditional_diameter_mm": 38.1,
                              "center_depth_mm": 25.4, "actual_tool_or_cut_released": False})
        axis["point_xyz_mm"] = base.xyz(axis["point"])
        axis["minimum_grip_failed"] = axis["grip_mm"] < 88.9 - 1e-5
    return finished, spotfaces


def hardware(axes: list[dict]) -> list[tuple[str, str, cq.Shape]]:
    result = []
    for axis in axes:
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        for role, shape in v3.metal(axis):
            result.append((axis["id"], role, shape.moved(plane.location)))
    return result


def collision_pairs(parts: list[tuple[str, str, cq.Shape]]) -> list[dict]:
    bounds = [shape.BoundingBox() for _, _, shape in parts]
    clashes = []
    for i, (first, role, shape) in enumerate(parts):
        for j in range(i + 1, len(parts)):
            second, other_role, other = parts[j]
            if first == second:
                continue
            a, b = bounds[i], bounds[j]
            if any(min(getattr(a, x + "max"), getattr(b, x + "max")) -
                   max(getattr(a, x + "min"), getattr(b, x + "min")) < 1e-6 for x in "xyz"):
                continue
            volume = max(0.0, shape.intersect(other).Volume())
            if volume > .01:
                clashes.append({"first": first, "first_role": role, "second": second,
                                "second_role": other_role, "intersection_mm3": round(volume, 4)})
    return clashes


def candidate_machining(wood: dict, axes: list[dict], screw_rows: list[dict]) -> tuple[dict, list[dict]]:
    result, bores = dict(wood), []
    for axis in axes:
        p, d = axis["point"], axis["direction"]
        diameter = axis["diameter_mm"] + 1.5875
        cutter = cq.Solid.makeCylinder(diameter / 2, axis["grip_mm"] + 10, p - d.multiply(5), d)
        for name in axis["receivers"]:
            if name not in result:
                raise ValueError(f"missing receiver {name}")
            result[name] = result[name].cut(cutter).clean()
        bores.append({"axis_id": axis["id"], "receivers": axis["receivers"],
                      "conditional_diameter_mm": diameter, "drill_size_selected": False})
    for row in screw_rows:
        p, d = cq.Vector(*row["origin_global_xyz_mm"]), cq.Vector(*row["axis_global_xyz"])
        cutter = cq.Solid.makeCylinder(2.0701, 65, p - d, d)
        result[row["receiver"]] = result[row["receiver"]].cut(cutter).clean()
    return result, bores


def make_scene(report: dict, source: dict, wood: dict, receiving: set[str], angles: list,
               axes: list[dict], screw_moves: list[dict], inventory: dict) -> dict:
    scene = base.export_scene(report, wood, {name: cq.Vector() for name in sorted(receiving)}, angles, [])
    solids, templates = scene["solids"], scene["mesh_templates"]
    for axis in axes:
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        transform = [*base.xyz(plane.xDir), 0, *base.xyz(plane.yDir), 0,
                     *base.xyz(plane.zDir), 0, *base.xyz(plane.origin), 1]
        for role, shape in v3.metal(axis):
            key = f'hardware_{axis["diameter_mm"]}_{axis["grip_mm"]:.6f}_{len(axis["attachments"])}_{role}'
            if key not in templates:
                mesh = base._shape_mesh(shape)
                scene["triangle_topologies"].update(base._deduplicate_triangle_topologies([{"mesh": mesh}]))
                templates[key] = {"id": key, "mesh": mesh}
            name = f'{axis["id"]}_{role}'
            solids.append({"id": name, "name": name, "template_id": key, "transform": transform,
                           "fabrication": {"kind": "bolt", "description": "Conditional metal occupancy; product, threads and strength unqualified",
                               "connection_name": axis["id"], "hardware_role": role,
                               "stack_roles": ["shaft", "head", "head_washer", "nut_washer", "nut"]}})
    def add(name: str, shape: cq.Shape, kind: str, description: str) -> None:
        solids.append({"id": name, "name": name, "mesh": base._shape_mesh(shape),
                       "fabrication": {"kind": kind, "description": description}})
    by_id = {r["axis_id"]: r for r in inventory["fixed_panel_kicker_screws"]}
    for panel in ("kicker_left", "kicker_right"):
        shape = source[panel]
        for row in report["panel_screw_axes"]:
            if by_id[row["axis_id"]]["panel_member"] == panel:
                p, d = cq.Vector(*row["origin_global_xyz_mm"]), cq.Vector(*row["axis_global_xyz"])
                shape = shape.cut(cq.Solid.makeCylinder(2.0701, 65, p - d, d)).clean()
        add(panel, shape, "panel", "Preserved kerf-right kicker and hold/LED bores; nine candidate mounting axes")
    for row in screw_moves:
        p, d = cq.Vector(*row["new_point_xyz_mm"]), cq.Vector(0, -1, 0)
        shape = cq.Solid.makeCone(4.5, 2.0701, 3, p, d).fuse(
            cq.Solid.makeCylinder(2.0701, 60.5, p + d.multiply(3), d)).clean()
        add("fastener_" + row["axis_id"], shape, "screw", "Hillman 42605 policy; measured 9 mm head and unmeasured 3 mm height envelope")
    scene["triangle_topologies"].update(base._deduplicate_triangle_topologies(
        [r for r in solids if "mesh" in r and "triangle_indices_base64" in r["mesh"]]))
    scene.update({"revision": REVISION, "replaced_host_names": sorted(receiving),
                  "removed_parent_visual_names": ["kicker_left", "kicker_right",
                       *["fastener_" + r["axis_id"] for r in screw_moves]],
                  "removed_parent_bolt_axes": [a["id"] for a in axes if a["axis_kind"] == "starting_frame_bolt"],
                  "changed_screw_axis_ids": [r["axis_id"] for r in screw_moves],
                  "census": {"timber": 16, "brackets": len(angles), "new_screw_displays": 4,
                      "new_panel_displays": 2, "displayed_structural_bolt_axes": len(axes),
                      "kept_starting_metal_axes": 0, "panel_kicker_screws": 66}})
    # Two center members become one common principal plus the kicker seam backer.
    scene["replaced_host_names"] = sorted((receiving - {"hl35_center_principal", "hl35_kicker_seam_backer"}) |
                                         {"base_principal_center_left", "base_principal_center_right"})
    scene["design"]["key"] = "hl35-fit-development"
    scene["design"]["documents"][0] = {"label": "HL35 complete fit assessment and limits",
        "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/full-fit-v4/README.md"}
    for row in solids:
        if row["fabrication"]["kind"] == "timber":
            row["fabrication"]["description"] = "New candidate receiving wood with planning bolt and screw bores; LED/wire/T-nut passages and net resistance unqualified"
        if row["fabrication"]["kind"] == "bracket":
            row["fabrication"]["clearance_status"] = "Conditional flange pose checked; complete occupied and structural fit require assessment"
    return scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=base.ROOT / "site/hl35-full-fit-scene.json")
    args = parser.parse_args()
    snapshot, inventory, _ = base.load_sources()
    source, shifts = base.reconstructed_wood(snapshot)
    wood, dims = geometry(source)
    angles = v3.angles(wood, dims)
    changed_snapshot, changed_inventory, receiver_changes, screw_moves = v3.remap(snapshot, inventory)
    print("Checking 30 angle poses, then complete hardware occupancy", flush=True)
    report, axes = base.audit(wood, angles, changed_snapshot, changed_inventory)
    report["revision"] = REVISION
    report["counts"]["duties"] = len(report["duties"])
    moved, prior_moved = {r["axis_id"] for r in screw_moves}, {r["axis_id"] for r in snapshot["panel_screws"]}
    for row in report["panel_screw_axes"]:
        row["new_candidate_axis_moved"] = row["axis_id"] in moved
        row["prior_owner_move_retained"] = row["axis_id"] in prior_moved and row["axis_id"] not in moved
    report.update({"proposed_screw_moves": screw_moves, "changed_screw_receiver_identities": receiver_changes,
                   "layout_parameters": dims})
    receiving = (set(shifts) - {"base_principal_center_left", "base_principal_center_right"}) | {
        "hl35_center_principal", "hl35_kicker_seam_backer"}
    finished, spotfaces = prepare_axes(wood, axes)
    frame_axes = v3.starting_axes(inventory)
    ties = [{**a, "point": cq.Vector(*a["point"]), "direction": cq.Vector(*a["direction"])}
            for a in dims["seam_backer_ties"]]
    all_axes = axes + frame_axes + ties
    metal = hardware(all_axes)
    finished, bores = candidate_machining(finished, all_axes, report["panel_screw_axes"])
    report["planning_hardware_intersections"] = collision_pairs(metal)
    print(f"Complete metal pair conflicts: {len(report['planning_hardware_intersections'])}", flush=True)
    unintended = []
    for axis_id, role, shape in metal:
        if role == "shaft":
            continue
        for name, body in finished.items():
            volume = base.overlaps(shape, body)
            if volume > .01:
                unintended.append({"axis_id": axis_id, "role": role, "member": name,
                                   "intersection_mm3": round(volume, 4)})
    report["planning_nonshaft_hardware_timber_intersections"] = unintended
    screw_clashes = []
    for row in report["panel_screw_axes"]:
        p, d = cq.Vector(*row["origin_global_xyz_mm"]), cq.Vector(*row["axis_global_xyz"])
        screw = cq.Solid.makeCylinder(2.0701, 63.5, p, d)
        for axis_id, role, shape in metal:
            if (volume := base.overlaps(screw, shape)) > .01:
                screw_clashes.append({"screw_axis_id": row["axis_id"], "bolt_axis_id": axis_id,
                                       "role": role, "intersection_mm3": round(volume, 4)})
    report["planning_hardware_screw_intersections"] = screw_clashes
    report["washer_spotfaces"], report["candidate_bores"] = spotfaces, bores
    report["installed_axes"] = [{k: base.xyz(v) if isinstance(v, cq.Vector) else v
                                 for k, v in a.items() if k != "attachments"} for a in all_axes]
    counts = report["counts"]
    counts.update({"auxiliary_seam_backer_tie_axes": len(ties), "new_proposed_screw_axis_moves": len(screw_moves),
                   "total_proposed_structural_bolt_axes": len(all_axes),
                   "hl35_axis_grips_below_88_9_mm": sum(a["minimum_grip_failed"] for a in axes),
                   "planning_hardware_pair_intersections": len(report["planning_hardware_intersections"]),
                   "planning_nonshaft_hardware_timber_intersections": len(unintended),
                   "planning_hardware_screw_intersections": len(screw_clashes),
                   "receiving_members_split_by_planning_machining": sum(len(finished[n].Solids()) != 1 for n in receiving)})
    report["retained_frame_bolt_changes"] = [{"axis_id": a["id"], "old_grip_mm": a["old_grip_mm"],
        "new_grip_mm": a["grip_mm"], "line_moved": False, "delivered_thread_window_qualified": False} for a in frame_axes]
    report["joint_architecture"] = {"pair_rule_qualified": False,
        "paired_angle_duties": sorted(d for d in {a.duty for a in angles} if sum(b.duty == d for b in angles) == 2),
        "single_angle_and_compression_duties": sorted(a.duty for a in angles if sum(b.duty == a.duty for b in angles) == 1),
        "complete_joint_resistance_qualified": False,
        "limits": "A single angle has no bidirectional lateral catalog credit; wood compression, transverse force, moments and auxiliary tie behavior require separate evidence."}
    report["limits"] = [s for s in report["limits"] if "initial fit" not in s and "Raw host profiles preserve" not in s]
    report["limits"].append("Receiving wood has only conditional structural/screw bores and washer seats. LED/wire/T-nut passages, net sections, tool/removal access and complete joint mechanics remain open.")
    report["mechanics_gates"]["conditional_angle_pose"] = counts["duties_requiring_geometry_revision"] == 0
    report["mechanics_gates"]["geometry_fit"] = False
    print(json.dumps(counts, sort_keys=True), flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    scene = make_scene(report, source, finished, receiving, angles, all_axes, screw_moves, changed_inventory)
    report_path = args.out / "fit-assessment.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {"schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_full_fit_candidate", "versions": {"cadquery": cq.__version__},
        "source_sha256": {**base.SOURCE_PINS, **{str(Path(m.__file__).relative_to(base.ROOT)): base.sha(Path(m.__file__))
            for m in (base, v2, v3)}, "scripts/hl35_full_fit_candidate.py": base.sha(Path(__file__))},
        "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, args.scene)}, "release": base.RELEASE}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Scene bytes {args.scene.stat().st_size}; SHA256 {base.sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
