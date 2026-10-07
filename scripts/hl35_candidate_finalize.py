"""Resolve the last nominal center-foot service clash without changing bolts.

This changes one proposed wire dogleg from +16 to -16 mm along the slope. It
retains the v6 failed inputs and reuses its authenticated geometry and methods.
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
from scripts import hl35_nominal_service_candidate as v6

REVISION = "hl35-center-foot-wire-clearance-v7"
PACKET = base.PACKET / "final-fit-v7"


def services(parent: dict) -> tuple[list, dict, list, list]:
    parts, authentication, moves, cutters = v6.proposed_services(parent)
    name = "wire_072_F1_G1"
    row = next(r for r in moves if r["name"] == name)
    record = next(r for r in round_structural_wiring.segments() if r["name"] == name)
    first, last = record["route_local_mm"][0], record["route_local_mm"][-1]
    dx, dt = last[0] - first[0], last[1] - first[1]
    route = [first, [first[0] + dx / 3, first[1] + dt / 3 - 16, 8],
             [first[0] + 2 * dx / 3, first[1] + 2 * dt / 3 - 16, 8], last]
    placement = list(no_shoes_frame.SHIFT.toTuple())
    shape, length = v6.sweep(route, round_structural_wiring.CABLE_DIAMETER_MM / 2, placement)
    cutter, _ = v6.sweep(route, 6.35, placement)
    row.update({"route_local_mm": route, "routed_length_mm": length, "within_approximate_budget": length <= 304.8,
                "center_foot_avoidance": "16 mm dogleg below the LED endpoints along the slope"})
    parts = [(n, kind, shape if n == name else body) for n, kind, body in parts]
    cutters = [(n, kind, cutter if n == name else body) for n, kind, body in cutters]
    return parts, authentication, moves, cutters


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=base.ROOT / "site/hl35-final-scene.json")
    args = parser.parse_args()
    prior_manifest = json.loads((v6.PACKET / "manifest.json").read_text())
    for name, expected in {**prior_manifest["source_sha256"], **prior_manifest["outputs"]}.items():
        if base.sha(base.ROOT / name) != expected:
            raise ValueError(f"v6 evidence binding differs: {name}")
    prior_path = v6.PACKET / "fit-assessment.json"
    report = copy.deepcopy(json.loads(prior_path.read_text()))
    snapshot, inventory, parent = base.load_sources()
    source, shifts = base.reconstructed_wood(snapshot)
    wood, dims = v5.geometry(source)
    angles = v3.angles(wood, dims)
    changed_snapshot, changed_inventory, _, _ = v5.remap(snapshot, inventory)
    receivers = (set(shifts) - {"base_principal_center_left", "base_principal_center_right"}) | {
        "hl35_center_principal", "hl35_kicker_seam_backer"}
    print("Checking the downward center-foot dogleg and final receiving geometry", flush=True)
    parts, authentication, wire_moves, cutters = services(parent)
    serviced, cuts = v6.cut_services(wood, receivers, cutters)
    checked, axes = base.audit(serviced, angles, changed_snapshot, changed_inventory)
    finished, spotfaces = v4.prepare_axes(serviced, axes)
    ties = [{**a, "point": cq.Vector(*a["point"]), "direction": cq.Vector(*a["direction"])}
            for a in dims["seam_backer_ties"]]
    all_axes = axes + v3.starting_axes(inventory) + ties
    prior_axes = {a["id"]: a for a in report["installed_axes"]}
    for axis in all_axes:
        old = prior_axes[axis["id"]]
        if abs(axis["grip_mm"] - old["grip_mm"]) > 1e-5 or (axis["point"] - cq.Vector(*old["point"])).Length > 1e-5:
            raise ValueError(f"bolt seat or span changed: {axis['id']}")
    metal = v5.hardware(all_axes)
    finished, bores = v4.candidate_machining(finished, all_axes, report["panel_screw_axes"])
    timber_hits, steel_hits = v6.service_hits(parts, finished, metal, angles)
    for field in ("duties", "flange_seats", "flange_attachments", "physical_bolt_axes",
                  "angle_angle_intersections", "angle_wood_or_panel_intersections"):
        report[field] = checked[field]
    report["revision"] = REVISION
    report["counts"].update(checked["counts"])
    report["counts"]["duties"] = len(report["duties"])
    report["counts"].update({"retained_service_timber_intersections": len(timber_hits),
        "retained_service_metal_intersections": len(steel_hits),
        "hl35_axis_grips_below_88_9_mm": sum(a["minimum_grip_failed"] for a in axes),
        "panel_screw_axes_without_receiver": sum(r["raw_receiver_intersection_mm3"] < .01 for r in checked["panel_screw_axes"]),
        "receiving_members_split_by_planning_machining": sum(len(finished[n].Solids()) != 1 for n in receivers)})
    report.update({"service_clearance": {**authentication, "timber_intersections": timber_hits,
        "metal_intersections": steel_hits, "physical_service_access_qualified": False},
        "proposed_wire_routes": wire_moves, "service_voids": cuts, "washer_spotfaces": spotfaces,
        "candidate_bores": bores, "receiving_member_material": [{"member": n,
            "raw_volume_mm3": wood[n].Volume(), "finished_volume_mm3": finished[n].Volume(),
            "remaining_volume_fraction": finished[n].Volume() / wood[n].Volume(),
            "wood_resistance_qualified": False} for n in sorted(receivers)]})
    diagnostic_keys = ("duties_requiring_geometry_revision", "attachments_missing_minimum_receiving_wood",
        "flanges_without_full_nominal_bearing", "angle_angle_intersections", "angle_wood_or_panel_intersections",
        "panel_screw_axes_intersecting_angles", "panel_screw_axes_without_receiver", "hl35_axis_grips_below_88_9_mm",
        "receiving_members_split_by_planning_machining", "retained_service_timber_intersections", "retained_service_metal_intersections")
    report["mechanics_gates"]["conditional_occupied_geometry"] = all(report["counts"][k] == 0 for k in diagnostic_keys)
    # Preserve v6's unmodified 112 metal stacks, panels and eight screw moves.
    scene = json.loads((base.ROOT / "site/hl35-nominal-service-scene.json").read_text())
    for row in scene["solids"]:
        if row["fabrication"]["kind"] == "timber":
            row["mesh"] = base._shape_mesh(finished[row["name"]])
            row["fabrication"]["description"] = "Proposed receiving timber, conditional bores and service voids; machining method and net resistance unqualified"
        elif row["name"] == "wire_072_F1_G1":
            row["mesh"] = base._shape_mesh(next(body for name, _, body in parts if name == row["name"]))
        elif row["fabrication"]["kind"] == "bracket":
            row["fabrication"]["description"] = row["fabrication"]["description"].replace("REVISE", "UNQUALIFIED")
    scene["triangle_topologies"].update(base._deduplicate_triangle_topologies(
        [r for r in scene["solids"] if "mesh" in r and "triangle_indices_base64" in r["mesh"]]))
    used = {r["mesh"]["triangle_topology_sha256"] for r in scene["solids"] if "mesh" in r}
    used.update(r["mesh"]["triangle_topology_sha256"] for r in scene["mesh_templates"].values())
    scene["triangle_topologies"] = {k: value for k, value in scene["triangle_topologies"].items() if k in used}
    scene["revision"] = REVISION
    scene["counts"] = report["counts"]
    scene["design"]["documents"][0] = {"label": "HL35 final nominal fit and engineering gates",
        "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/final-fit-v7/README.md"}
    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / "fit-assessment.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {"schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_candidate_finalize", "versions": {"cadquery": cq.__version__},
        "source_sha256": {**prior_manifest["source_sha256"], str(prior_path.relative_to(base.ROOT)): base.sha(prior_path),
            "site/hl35-nominal-service-scene.json": base.sha(base.ROOT / "site/hl35-nominal-service-scene.json"),
            "scripts/hl35_candidate_finalize.py": base.sha(Path(__file__))},
        "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, args.scene)}, "release": base.RELEASE}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(report["counts"], sort_keys=True), flush=True)
    print(f"Scene bytes {args.scene.stat().st_size}; SHA256 {base.sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
