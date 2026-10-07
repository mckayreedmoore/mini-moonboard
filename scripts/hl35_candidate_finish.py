"""Evaluate the next HL35 candidate revision including retained service bodies.

The two seam rails move apart, auxiliary washers shrink to conditional 1.25-in
envelopes, and four upper panel screws move along the slope. No release follows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as base
from scripts import hl35_fit_revision as v3
from scripts import hl35_full_fit_candidate as v4
from scripts import hl35_revised_candidate as v2
from scripts import hl35_service_clearance as service

REVISION = "hl35-separated-seam-rails-and-service-audit-v5"
PACKET = base.PACKET / "service-fit-v5"


def geometry(source: dict) -> tuple[dict, dict]:
    wood, dims = v4.geometry(source)
    changes = []
    for side in ("left", "right"):
        for level, shift in (("lower", -26.55), ("upper", 26.9)):
            name = f"base_rail_service_{level}_{side}"
            old = base.projected_extent(wood[name], v2.T)
            wood[name] = wood[name].translate(v2.T.multiply(shift))
            changes.append({"member": name, "shift_along_slope_mm": shift,
                            "old_t_mm": old, "new_t_mm": base.projected_extent(wood[name], v2.T)})
    dims["service_rail_shifts"] = changes
    dims["auxiliary_tie_washer_od_mm"] = 31.75
    dims["auxiliary_tie_counterbore_od_mm"] = 38.1
    return wood, dims


def remap(snapshot: dict, inventory: dict) -> tuple[dict, dict, list, list]:
    snapshot, inventory, receivers, proposed = v3.remap(snapshot, inventory)
    moves = {r["axis_id"]: r for r in snapshot["panel_screws"]}
    for row in inventory["fixed_panel_kicker_screws"]:
        name = row["axis_id"]
        if name.startswith("round_panel_upper_") and name.endswith("_4") and ("_rim_" in name or "_center_" in name):
            move = moves.get(name)
            old = move["new_start_global_xyz_mm"] if move else row["origin_global_xyz_mm"]
            point = cq.Vector(*old) + v2.T.multiply(19.05)
            receiver = move["receiver_member"] if move else row["candidate_finished_receiver_member"]
            new_move = {"axis_id": name, "receiver_member": receiver, "new_start_global_xyz_mm": base.xyz(point)}
            if move:
                move.update(new_move)
            else:
                snapshot["panel_screws"].append(new_move)
            proposed.append({"axis_id": name, "old_point_xyz_mm": old, "new_point_xyz_mm": base.xyz(point),
                             "translation_xyz_mm": base.xyz(v2.T.multiply(19.05)), "new_receiver": receiver,
                             "reason": "Clear the top HL35 post shaft; preserve purchased Hillman count and length",
                             "physical_move_authorized_or_performed": False})
    return snapshot, inventory, receivers, proposed


def local_metal(axis: dict) -> list[tuple[str, cq.Shape]]:
    parts = v3.metal(axis)
    if axis["axis_kind"] != "auxiliary_through_tie":
        return parts
    envelope = cq.Solid.makeCylinder(15.875, axis["grip_mm"] + 60, cq.Vector(0, 0, -30))
    return [(role, shape.intersect(envelope) if role.endswith("washer") else shape) for role, shape in parts]


def hardware(axes: list[dict]) -> list[tuple[str, str, cq.Shape]]:
    result = []
    for axis in axes:
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        result.extend((axis["id"], role, shape.moved(plane.location)) for role, shape in local_metal(axis))
    return result


def nonshaft_hits(metal: list, wood: dict) -> list[dict]:
    hits = []
    for axis, role, shape in metal:
        if role != "shaft":
            for name, body in wood.items():
                if (volume := base.overlaps(shape, body)) > .01:
                    hits.append({"axis_id": axis, "role": role, "member": name, "intersection_mm3": round(volume, 4)})
    return hits


def screw_hits(metal: list, screws: list) -> list[dict]:
    hits = []
    for row in screws:
        p, d = cq.Vector(*row["origin_global_xyz_mm"]), cq.Vector(*row["axis_global_xyz"])
        shape = cq.Solid.makeCylinder(2.0701, 63.5, p, d)
        for axis, role, body in metal:
            if (volume := base.overlaps(shape, body)) > .01:
                hits.append({"screw_axis_id": row["axis_id"], "bolt_axis_id": axis,
                             "role": role, "intersection_mm3": round(volume, 4)})
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=base.ROOT / "site/hl35-service-fit-scene.json")
    args = parser.parse_args()
    snapshot, inventory, _ = base.load_sources()
    source, shifts = base.reconstructed_wood(snapshot)
    wood, dims = geometry(source)
    angles = v3.angles(wood, dims)
    changed_snapshot, changed_inventory, receiver_changes, moves = remap(snapshot, inventory)
    print("Auditing the separated seam rails and eight proposed screw moves", flush=True)
    report, axes = base.audit(wood, angles, changed_snapshot, changed_inventory)
    report["revision"] = REVISION
    moved, original_moves = {r["axis_id"] for r in moves}, {r["axis_id"] for r in snapshot["panel_screws"]}
    for row in report["panel_screw_axes"]:
        row["new_candidate_axis_moved"] = row["axis_id"] in moved
        row["prior_owner_move_retained"] = row["axis_id"] in original_moves and row["axis_id"] not in moved
    finished, spotfaces = v4.prepare_axes(wood, axes)
    frame_axes = v3.starting_axes(inventory)
    ties = [{**a, "point": cq.Vector(*a["point"]), "direction": cq.Vector(*a["direction"])}
            for a in dims["seam_backer_ties"]]
    all_axes = axes + frame_axes + ties
    metal = hardware(all_axes)
    finished, bores = v4.candidate_machining(finished, all_axes, report["panel_screw_axes"])
    receiving = (set(shifts) - {"base_principal_center_left", "base_principal_center_right"}) | {
        "hl35_center_principal", "hl35_kicker_seam_backer"}
    report.update({"proposed_screw_moves": moves, "changed_screw_receiver_identities": receiver_changes,
                   "layout_parameters": dims, "washer_spotfaces": spotfaces, "candidate_bores": bores,
                   "planning_hardware_intersections": v4.collision_pairs(metal),
                   "planning_nonshaft_hardware_timber_intersections": nonshaft_hits(metal, finished),
                   "planning_hardware_screw_intersections": screw_hits(metal, report["panel_screw_axes"]),
                   "installed_axes": [{k: base.xyz(v) if isinstance(v, cq.Vector) else v
                       for k, v in a.items() if k != "attachments"} for a in all_axes]})
    report["counts"].update({"duties": len(report["duties"]), "auxiliary_seam_backer_tie_axes": len(ties),
        "new_proposed_screw_axis_moves": len(moves), "total_proposed_structural_bolt_axes": len(all_axes),
        "hl35_axis_grips_below_88_9_mm": sum(a["minimum_grip_failed"] for a in axes),
        "planning_hardware_pair_intersections": len(report["planning_hardware_intersections"]),
        "planning_nonshaft_hardware_timber_intersections": len(report["planning_nonshaft_hardware_timber_intersections"]),
        "planning_hardware_screw_intersections": len(report["planning_hardware_screw_intersections"]),
        "receiving_members_split_by_planning_machining": sum(len(finished[n].Solids()) != 1 for n in receiving),
        "panel_screw_axes_without_raw_receiver": sum(r["raw_receiver_intersection_mm3"] < .01 for r in report["panel_screw_axes"])})
    print(json.dumps(report["counts"], sort_keys=True), flush=True)
    print("Authenticating and checking the retained 405 light/wire/T-nut bodies", flush=True)
    service_report = service.inspect(finished, metal, angles)
    report["service_clearance"] = service_report
    report["counts"].update({"retained_service_timber_intersections": service_report["counts"]["timber_intersections"],
                             "retained_service_metal_intersections": service_report["counts"]["metal_intersections"]})
    report["joint_architecture"] = {"pair_rule_qualified": False,
        "paired_angle_duties": sorted(d for d in {a.duty for a in angles} if sum(b.duty == d for b in angles) == 2),
        "single_angle_and_compression_duties": sorted(a.duty for a in angles if sum(b.duty == a.duty for b in angles) == 1),
        "complete_joint_resistance_qualified": False,
        "limits": "A single angle has no bidirectional catalog lateral credit. Wood compression, transverse force, moments and auxiliary tie behavior need separate evidence."}
    report["retained_frame_bolt_changes"] = [{"axis_id": a["id"], "old_grip_mm": a["old_grip_mm"],
        "new_grip_mm": a["grip_mm"], "line_moved": False, "delivered_thread_window_qualified": False} for a in frame_axes]
    report["mechanics_gates"]["conditional_angle_pose"] = report["counts"]["duties_requiring_geometry_revision"] == 0
    report["mechanics_gates"]["geometry_fit"] = False
    report["limits"] = [s for s in report["limits"] if "initial fit" not in s and "Raw host profiles preserve" not in s]
    report["limits"].extend([
        "Occupied hardware and preserved service bodies are checked. Receiving wood still lacks service passages; native provisional-body findings do not establish physical access.",
        "All structural/screw bores, washer spotfaces and screw changes are unadopted planning geometry. Net sections, installation tools, hardware products and full joint mechanics remain unqualified."])
    scene = v4.make_scene(report, source, finished, receiving, angles, all_axes, moves, changed_inventory)
    scene["revision"] = REVISION
    scene["census"]["new_screw_displays"] = len(moves)
    scene["design"]["documents"][0] = {"label": "HL35 service-fit revision and limits",
        "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/service-fit-v5/README.md"}
    for axis in ties:
        for role, shape in local_metal(axis):
            if role.endswith("washer"):
                row = next(r for r in scene["solids"] if r["fabrication"].get("connection_name") == axis["id"]
                           and r["fabrication"].get("hardware_role") == role)
                mesh = base._shape_mesh(shape)
                scene["triangle_topologies"].update(base._deduplicate_triangle_topologies([{"mesh": mesh}]))
                scene["mesh_templates"][row["template_id"]] = {"id": row["template_id"], "mesh": mesh}
    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / "fit-assessment.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {"schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_candidate_finish", "versions": {"cadquery": cq.__version__},
        "source_sha256": {**base.SOURCE_PINS, **{str(Path(m.__file__).relative_to(base.ROOT)): base.sha(Path(m.__file__))
            for m in (base, v2, v3, v4, service)}, "scripts/hl35_candidate_finish.py": base.sha(Path(__file__))},
        "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, args.scene)}, "release": base.RELEASE}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Final counts: {json.dumps(report['counts'], sort_keys=True)}", flush=True)
    print(f"Scene bytes {args.scene.stat().st_size}; SHA256 {base.sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
