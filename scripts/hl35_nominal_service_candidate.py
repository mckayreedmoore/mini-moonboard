"""Close nominal service occupancy in the HL35 development candidate.

Clearance voids are proposed envelopes, not a qualified machining sequence.
Full wood/joint resistance, actual connector geometry and service access remain
separate gates even if every nominal occupied-body intersection is eliminated.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard import no_shoes_frame, round_structural_wiring
from scripts import hl35_candidate as base
from scripts import hl35_candidate_finish as v5
from scripts import hl35_fit_revision as v3
from scripts import hl35_full_fit_candidate as v4
from scripts import hl35_revised_candidate as v2
from scripts import hl35_service_clearance as service

REVISION = "hl35-nominal-service-passages-and-wire-routes-v6"
PACKET = base.PACKET / "nominal-service-v6"
WIRE_CHANGES = {"wire_048_D1_E1", "wire_066_F7_F6", "wire_072_F1_G1"}


def sweep(route: list, radius: float, placement: list) -> tuple[cq.Shape, float]:
    path = round_structural_wiring.wire_path({"route_local_mm": route})
    first, second = [round_structural_wiring.b.point(*p) for p in route[:2]]
    plane = cq.Plane(origin=first, normal=(second - first).normalized())
    shape = cq.Workplane(plane).circle(radius).sweep(cq.Workplane(obj=path), isFrenet=True).val()
    return shape.translate(cq.Vector(*placement)), path.Length()


def proposed_services(parent: dict) -> tuple[list, dict, list, list]:
    parts, authentication = service.service_parts()
    by_name = {name: (kind, shape) for name, kind, shape in parts}
    revisions, cutters = [], []
    for record in round_structural_wiring.segments():
        name = record["name"]
        route, placement = copy.deepcopy(record["route_local_mm"]), list(no_shoes_frame.SHIFT.toTuple())
        if name in parent["revision_report"]["wire_endpoint_revisions"]:
            change = parent["revision_report"]["wire_endpoint_revisions"][name]
            route, placement = change["route_local_mm"], change["source_placement_xyz_mm"]
        if name in WIRE_CHANGES:
            first, last = route[0], route[-1]
            dx, dt = last[0] - first[0], last[1] - first[1]
            # A shallow dogleg retains both LED endpoints and gives a modeled
            # curved route; unused real cable slack is a separate open input.
            side_x, side_t = (16, 0) if abs(dt) > abs(dx) else (0, 16)
            route = [first, [first[0] + dx / 3 + side_x, first[1] + dt / 3 + side_t, 8],
                     [first[0] + 2 * dx / 3 + side_x, first[1] + 2 * dt / 3 + side_t, 8], last]
            shape, length = sweep(route, round_structural_wiring.CABLE_DIAMETER_MM / 2, placement)
            by_name[name] = ("wire", shape)
            revisions.append({"name": name, "route_local_mm": route, "source_placement_xyz_mm": placement,
                              "routed_length_mm": length, "approximate_segment_budget_mm": 304.8,
                              "within_approximate_budget": length <= 304.8,
                              "unused_slack_accommodation_modeled": False,
                              "endpoints_retained": route[0] == record["route_local_mm"][0] and route[-1] == record["route_local_mm"][-1],
                              "physical_route_selected_or_installed": False})
        cutter, _ = sweep(route, 6.35, placement)
        if record["string_connector_envelope"]:
            first, last = [round_structural_wiring.b.point(*p) for p in route[1:3]]
            direction, midpoint = (last - first).normalized(), (first + last) * .5
            length = round_structural_wiring.GEOMETRY["connector_length"] + 6
            connector = cq.Solid.makeCylinder(12.7, length, midpoint - direction.multiply(length / 2), direction)
            cutter = cutter.fuse(connector.translate(cq.Vector(*placement))).clean()
        cutters.append((name, "wire", cutter))
    for name, (kind, shape) in by_name.items():
        if kind == "wire":
            continue
        if kind == "light":
            direction = v2.N
            radius = round_structural_wiring.MEASURED_MAXIMUM_DIAMETER_MM / 2 + 3
        else:
            direction = v2.N if name.startswith("hold_tnut_main_") else cq.Vector(0, -1, 0)
            radius = 15.875
        lo, hi = base.projected_extent(shape, direction)
        center = shape.Center()
        start = center + direction.multiply(lo - center.dot(direction) - 3)
        cutters.append((name, kind, cq.Solid.makeCylinder(radius, hi - lo + 6, start, direction)))
    return [(name, kind, shape) for name, (kind, shape) in by_name.items()], authentication, revisions, cutters


def cut_services(wood: dict, receivers: set[str], cutters: list) -> tuple[dict, list]:
    result, cuts = dict(wood), []
    for name, kind, cutter in cutters:
        for member in sorted(receivers):
            if base.overlaps(cutter, result[member]) > .01:
                before = result[member].Volume()
                result[member] = result[member].cut(cutter).clean()
                cuts.append({"service": name, "kind": kind, "receiver": member,
                             "removed_volume_mm3": round(before - result[member].Volume(), 4),
                             "machining_sequence_qualified": False})
    return result, cuts


def service_hits(parts: list, wood: dict, metal: list, angles: list) -> tuple[list, list]:
    obstacles = [({"member": name}, shape, shape.BoundingBox()) for name, shape in wood.items()
                 if not name.startswith(("main_", "kicker_"))]
    obstacles.extend(({"axis": name, "role": role}, shape, shape.BoundingBox()) for name, role, shape in metal)
    obstacles.extend(({"angle": angle.id}, angle.shape, angle.shape.BoundingBox()) for angle in angles)
    timber, steel = [], []
    for name, kind, shape in parts:
        a = shape.BoundingBox()
        for identity, other, b in obstacles:
            if any(min(getattr(a, x + "max"), getattr(b, x + "max")) -
                   max(getattr(a, x + "min"), getattr(b, x + "min")) < 1e-6 for x in "xyz"):
                continue
            volume = max(0.0, shape.intersect(other).Volume())
            if volume > .01:
                hits = timber if "member" in identity else steel
                hits.append({"service": name, "kind": kind, **identity, "intersection_mm3": round(volume, 4)})
    return timber, steel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=base.ROOT / "site/hl35-nominal-service-scene.json")
    args = parser.parse_args()
    previous_path = v5.PACKET / "fit-assessment.json"
    previous_manifest = json.loads((v5.PACKET / "manifest.json").read_text())
    for name, expected in {**previous_manifest["source_sha256"], **previous_manifest["outputs"]}.items():
        if base.sha(base.ROOT / name) != expected:
            raise ValueError(f"v5 evidence binding differs: {name}")
    prior_report = json.loads(previous_path.read_text())
    snapshot, inventory, parent = base.load_sources()
    source, shifts = base.reconstructed_wood(snapshot)
    wood, dims = v5.geometry(source)
    angles = v3.angles(wood, dims)
    changed_snapshot, changed_inventory, receiver_changes, screw_moves = v5.remap(snapshot, inventory)
    receivers = (set(shifts) - {"base_principal_center_left", "base_principal_center_right"}) | {
        "hl35_center_principal", "hl35_kicker_seam_backer"}
    print("Constructing service clearance envelopes and three shallow wire proposals", flush=True)
    services, authentication, wire_moves, cutters = proposed_services(parent)
    serviced, cuts = cut_services(wood, receivers, cutters)
    print(f"Cut {len(cuts)} nominal service void intersections; rechecking the connector seats", flush=True)
    report, axes = base.audit(serviced, angles, changed_snapshot, changed_inventory)
    report["revision"] = REVISION
    report["counts"]["duties"] = len(report["duties"])
    report["layout_parameters"] = dims
    report["proposed_wire_routes"] = wire_moves
    report["proposed_screw_moves"] = screw_moves
    report["changed_screw_receiver_identities"] = receiver_changes
    moved = {r["axis_id"] for r in screw_moves}
    original_moves = {r["axis_id"] for r in snapshot["panel_screws"]}
    for row in report["panel_screw_axes"]:
        row["new_candidate_axis_moved"] = row["axis_id"] in moved
        row["prior_owner_move_retained"] = row["axis_id"] in original_moves and row["axis_id"] not in moved
    # Hardware stays exactly at the authenticated v5 pose. New service voids
    # must not be used to shorten the bolts or hide loss of wood at their paths.
    finished, spotfaces = v4.prepare_axes(serviced, axes)
    frame_axes = v3.starting_axes(inventory)
    ties = [{**a, "point": cq.Vector(*a["point"]), "direction": cq.Vector(*a["direction"])}
            for a in dims["seam_backer_ties"]]
    all_axes = axes + frame_axes + ties
    prior_axes = {a["id"]: a for a in prior_report["installed_axes"]}
    for axis in all_axes:
        old = prior_axes[axis["id"]]
        if abs(axis["grip_mm"] - old["grip_mm"]) > 1e-5 or (axis["point"] - cq.Vector(*old["point"])).Length > 1e-5:
            raise ValueError(f"service void changed a bolt seat/span: {axis['id']}")
    metal = v5.hardware(all_axes)
    finished, bores = v4.candidate_machining(finished, all_axes, report["panel_screw_axes"])
    timber_hits, steel_hits = service_hits(services, finished, metal, angles)
    counts = report["counts"]
    counts.update({"auxiliary_seam_backer_tie_axes": 2, "new_proposed_screw_axis_moves": len(screw_moves),
        "new_proposed_wire_routes": len(wire_moves), "total_proposed_structural_bolt_axes": len(all_axes),
        "hl35_axis_grips_below_88_9_mm": sum(a["minimum_grip_failed"] for a in axes),
        "panel_screw_axes_without_receiver": sum(r["raw_receiver_intersection_mm3"] < .01 for r in report["panel_screw_axes"]),
        "receiving_members_split_by_planning_machining": sum(len(finished[n].Solids()) != 1 for n in receivers),
        "retained_service_timber_intersections": len(timber_hits), "retained_service_metal_intersections": len(steel_hits),
        **{k: prior_report["counts"][k] for k in ("planning_hardware_pair_intersections",
             "planning_hardware_screw_intersections", "planning_nonshaft_hardware_timber_intersections")}})
    report.update({"service_clearance": {**authentication, "timber_intersections": timber_hits,
        "metal_intersections": steel_hits, "physical_service_access_qualified": False},
        "service_voids": cuts, "washer_spotfaces": spotfaces, "candidate_bores": bores,
        "joint_architecture": prior_report["joint_architecture"], "installed_axes": prior_report["installed_axes"],
        "retained_frame_bolt_changes": prior_report["retained_frame_bolt_changes"],
        "reused_v5_negative_hardware_checks": {"path": str(previous_path.relative_to(base.ROOT)),
            "sha256": base.sha(previous_path), "basis": "Same hardware and screw poses; service subtraction cannot create a new solid-wood collision."},
        "receiving_member_material": [{"member": n, "raw_volume_mm3": wood[n].Volume(),
            "finished_volume_mm3": finished[n].Volume(), "remaining_volume_fraction": finished[n].Volume() / wood[n].Volume(),
            "wood_resistance_qualified": False} for n in sorted(receivers)]})
    checks = ("duties_requiring_geometry_revision", "attachments_missing_minimum_receiving_wood",
        "flanges_without_full_nominal_bearing", "angle_angle_intersections", "angle_wood_or_panel_intersections",
        "panel_screw_axes_intersecting_angles", "panel_screw_axes_without_receiver", "hl35_axis_grips_below_88_9_mm",
        "receiving_members_split_by_planning_machining", "retained_service_timber_intersections", "retained_service_metal_intersections")
    report["mechanics_gates"]["conditional_occupied_geometry"] = all(counts[k] == 0 for k in checks)
    report["limits"] = [s for s in prior_report["limits"] if "lacks service passages" not in s]
    report["limits"].append("Service voids are oversized geometric clearance envelopes, not a drilling/routing method. Curved passages, net sections, wire slack and feeding/removal access remain unqualified.")
    scene = v4.make_scene(report, source, finished, receivers, angles, all_axes, screw_moves, changed_inventory)
    scene["revision"] = REVISION
    scene["census"].update({"new_screw_displays": len(screw_moves), "new_wire_displays": len(wire_moves)})
    scene["removed_parent_visual_names"].extend(sorted(WIRE_CHANGES))
    scene["changed_wire_ids"] = sorted(WIRE_CHANGES)
    scene["design"]["documents"][0] = {"label": "HL35 nominal fit and remaining engineering gates",
        "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/nominal-service-v6/README.md"}
    # Keep the v5 smaller auxiliary washer envelopes in the shared templates.
    for axis in ties:
        for role, shape in v5.local_metal(axis):
            if role.endswith("washer"):
                row = next(r for r in scene["solids"] if r["fabrication"].get("connection_name") == axis["id"]
                           and r["fabrication"].get("hardware_role") == role)
                mesh = base._shape_mesh(shape)
                scene["triangle_topologies"].update(base._deduplicate_triangle_topologies([{"mesh": mesh}]))
                scene["mesh_templates"][row["template_id"]] = {"id": row["template_id"], "mesh": mesh}
    for name, kind, shape in services:
        if name in WIRE_CHANGES:
            scene["solids"].append({"id": name, "name": name, "mesh": base._shape_mesh(shape),
                "fabrication": {"kind": kind, "description": "Proposed shallow wire dogleg; existing LED endpoints; unused slack and physical routing unqualified"}})
    scene["triangle_topologies"].update(base._deduplicate_triangle_topologies(
        [r for r in scene["solids"] if "mesh" in r and "triangle_indices_base64" in r["mesh"]]))
    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / "fit-assessment.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {"schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_nominal_service_candidate", "versions": {"cadquery": cq.__version__},
        "source_sha256": {**previous_manifest["source_sha256"], str(previous_path.relative_to(base.ROOT)): base.sha(previous_path),
            "scripts/hl35_nominal_service_candidate.py": base.sha(Path(__file__))},
        "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, args.scene)}, "release": base.RELEASE}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(counts, sort_keys=True), flush=True)
    print(f"Scene bytes {args.scene.stat().st_size}; SHA256 {base.sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
