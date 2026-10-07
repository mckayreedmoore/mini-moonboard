"""Test deeper header seats after v7's bolt-tip coverage failure.

Check receiving wood and flange support after the washer recesses, before
intentional through holes. Removing a clash cannot qualify lost wood bearing.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as base
from scripts import hl35_candidate_finalize as v7
from scripts import hl35_candidate_finish as v5
from scripts import hl35_fit_revision as v3
from scripts import hl35_full_fit_candidate as v4
from scripts import hl35_nominal_service_candidate as v6

REVISION = "hl35-deeper-header-seat-and-bearing-audit-v8"
PACKET = base.PACKET / "counterbore-fit-v8"


def main() -> None:
    prior_path = v7.PACKET / "fit-assessment.json"
    prior_manifest = json.loads((v7.PACKET / "manifest.json").read_text())
    for name, expected in {**prior_manifest["source_sha256"], **prior_manifest["outputs"]}.items():
        if base.sha(base.ROOT / name) != expected:
            raise ValueError(f"v7 input binding differs: {name}")
    prior = json.loads(prior_path.read_text())
    snapshot, inventory, parent = base.load_sources()
    source, shifts = base.reconstructed_wood(snapshot)
    wood, dims = v5.geometry(source)
    angles = v3.angles(wood, dims)
    changed_snapshot, changed_inventory, _, screw_moves = v5.remap(snapshot, inventory)
    receivers = (set(shifts) - {"base_principal_center_left", "base_principal_center_right"}) | {
        "hl35_center_principal", "hl35_kicker_seam_backer"}
    print("Testing 31.75 mm header washer seats and their effect on neighboring flange bearing", flush=True)
    services, authentication, wire_moves, cutters = v7.services(parent)
    serviced, cuts = v6.cut_services(wood, receivers, cutters)
    raw_audit, axes = base.audit(serviced, angles, changed_snapshot, changed_inventory)
    recessed, spotfaces = v4.prepare_axes(serviced, axes)
    for row in spotfaces:
        axis = next(a for a in axes if a["id"] == row["axis_id"])
        seat = cq.Vector(*row["seat_point_xyz_mm"]) - axis["direction"].multiply(6.35)
        recessed["base_header"] = recessed["base_header"].cut(
            cq.Solid.makeCylinder(19.05, 1000, seat, axis["direction"])).clean()
        axis["grip_mm"] -= 6.35
        axis["minimum_grip_failed"] = axis["grip_mm"] < 88.9 - 1e-5
        row.update({"seat_point_xyz_mm": base.xyz(seat), "center_depth_mm": 31.75})
    # This audit includes every recess, while excluding only the intended
    # through-hole cutters. It does not mistake intentional bores for missing stock.
    print("Checking the recessed receiving wood", flush=True)
    audited, _ = base.audit(recessed, angles, changed_snapshot, changed_inventory)
    report = copy.deepcopy(prior)
    for field in ("duties", "flange_seats", "flange_attachments", "angle_angle_intersections", "angle_wood_or_panel_intersections"):
        report[field] = audited[field]
    report["counts"].update(audited["counts"])
    report["counts"]["duties"] = len(report["duties"])
    report["revision"] = REVISION
    report["before_washer_recesses"] = raw_audit["counts"]
    ties = [{**a, "point": cq.Vector(*a["point"]), "direction": cq.Vector(*a["direction"])}
            for a in dims["seam_backer_ties"]]
    all_axes = axes + v3.starting_axes(inventory) + ties
    metal = v5.hardware(all_axes)
    finished, bores = v4.candidate_machining(recessed, all_axes, report["panel_screw_axes"])
    complete_pairs = v4.collision_pairs(metal + [(a.id, "angle", a.shape) for a in angles])
    steel_pairs = [r for r in complete_pairs if "angle" in (r["first_role"], r["second_role"])]
    metal_pairs = [r for r in complete_pairs if "angle" not in (r["first_role"], r["second_role"])]
    unexpected = []
    axis_receivers = {a["id"]: set(a["receivers"]) for a in all_axes}
    for axis_id, role, shape in metal:
        if role == "shaft":
            for name, body in wood.items():
                if name not in axis_receivers[axis_id] and (volume := base.overlaps(shape, body)) > .01:
                    unexpected.append({"axis_id": axis_id, "member": name, "intersection_mm3": round(volume, 4)})
    timber_hits, service_metal = v6.service_hits(services, finished, metal, angles)
    nonshaft, screw_hits = v5.nonshaft_hits(metal, finished), v5.screw_hits(metal, report["panel_screw_axes"])
    report.update({"washer_spotfaces": spotfaces, "candidate_bores": bores, "service_voids": cuts,
        "service_clearance": {**authentication, "timber_intersections": timber_hits, "metal_intersections": service_metal,
                              "physical_service_access_qualified": False},
        "proposed_wire_routes": wire_moves, "planning_hardware_intersections": metal_pairs,
        "planning_hardware_angle_intersections": steel_pairs, "shaft_unrelated_raw_timber_intersections": unexpected,
        "planning_nonshaft_hardware_timber_intersections": nonshaft, "planning_hardware_screw_intersections": screw_hits,
        "installed_axes": [{k: base.xyz(v) if isinstance(v, cq.Vector) else v for k, v in a.items() if k != "attachments"}
                           for a in all_axes],
        "receiving_member_material": [{"member": n, "raw_volume_mm3": wood[n].Volume(),
            "finished_volume_mm3": finished[n].Volume(), "remaining_volume_fraction": finished[n].Volume() / wood[n].Volume(),
            "wood_resistance_qualified": False} for n in sorted(receivers)]})
    report["counts"].update({"planning_hardware_pair_intersections": len(metal_pairs),
        "planning_hardware_angle_intersections": len(steel_pairs), "shaft_unrelated_raw_timber_intersections": len(unexpected),
        "planning_nonshaft_hardware_timber_intersections": len(nonshaft), "planning_hardware_screw_intersections": len(screw_hits),
        "retained_service_timber_intersections": len(timber_hits), "retained_service_metal_intersections": len(service_metal),
        "hl35_axis_grips_below_88_9_mm": sum(a["minimum_grip_failed"] for a in axes),
        "receiving_members_split_by_planning_machining": sum(len(finished[n].Solids()) != 1 for n in receivers)})
    keys = ("duties_requiring_geometry_revision", "attachments_missing_minimum_receiving_wood", "flanges_without_full_nominal_bearing",
        "angle_angle_intersections", "angle_wood_or_panel_intersections", "planning_hardware_pair_intersections",
        "planning_hardware_angle_intersections", "shaft_unrelated_raw_timber_intersections", "planning_nonshaft_hardware_timber_intersections",
        "planning_hardware_screw_intersections", "retained_service_timber_intersections", "retained_service_metal_intersections",
        "hl35_axis_grips_below_88_9_mm", "receiving_members_split_by_planning_machining")
    report["mechanics_gates"]["conditional_occupied_geometry"] = all(report["counts"][k] == 0 for k in keys)
    report.pop("reused_v5_negative_hardware_checks", None)
    scene = v4.make_scene(report, source, finished, receivers, angles, all_axes, screw_moves, changed_inventory)
    scene["revision"] = REVISION
    scene["census"].update({"new_screw_displays": len(screw_moves), "new_wire_displays": len(wire_moves)})
    scene["removed_parent_visual_names"].extend(sorted(v6.WIRE_CHANGES))
    scene["changed_wire_ids"] = sorted(v6.WIRE_CHANGES)
    scene["design"]["documents"][0] = {"label": "HL35 counterbore and bearing assessment",
        "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/counterbore-fit-v8/README.md"}
    for axis in ties:
        for role, shape in v5.local_metal(axis):
            if role.endswith("washer"):
                row = next(r for r in scene["solids"] if r["fabrication"].get("connection_name") == axis["id"]
                           and r["fabrication"].get("hardware_role") == role)
                mesh = base._shape_mesh(shape)
                scene["triangle_topologies"].update(base._deduplicate_triangle_topologies([{"mesh": mesh}]))
                scene["mesh_templates"][row["template_id"]] = {"id": row["template_id"], "mesh": mesh}
    for name, kind, shape in services:
        if name in v6.WIRE_CHANGES:
            scene["solids"].append({"id": name, "name": name, "mesh": base._shape_mesh(shape),
                "fabrication": {"kind": kind, "description": "Proposed shallow wire dogleg; endpoints retained; physical routing unqualified"}})
    scene["triangle_topologies"].update(base._deduplicate_triangle_topologies(
        [r for r in scene["solids"] if "mesh" in r and "triangle_indices_base64" in r["mesh"]]))
    PACKET.mkdir(parents=True, exist_ok=True)
    report_path, scene_path = PACKET / "fit-assessment.json", base.ROOT / "site/hl35-counterbore-scene.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    scene_path.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {"schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_counterbore_candidate", "versions": {"cadquery": cq.__version__},
        "source_sha256": {**prior_manifest["source_sha256"], str(prior_path.relative_to(base.ROOT)): base.sha(prior_path),
            "scripts/hl35_counterbore_candidate.py": base.sha(Path(__file__))},
        "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, scene_path)}, "release": base.RELEASE}
    (PACKET / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(report["counts"], sort_keys=True), flush=True)
    print(f"Scene bytes {scene_path.stat().st_size}; SHA256 {base.sha(scene_path)}", flush=True)


if __name__ == "__main__":
    main()
