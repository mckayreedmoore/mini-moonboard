"""Build and audit a separate, unadopted 24-duty HL35 replacement candidate.

This is an installed-pose experiment, not a manufacturer connection design.
Raw receiving profiles are reconstructed from the reviewed geometry snapshot.
No native solve, frozen wood-joint model or selected authority is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    TRANSLATE_NAMES,
    variant,
)
from scripts.export_wood_joint_wj24_scene import (
    _deduplicate_triangle_topologies,
    _shape_mesh,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate"
CANDIDATE = "compact-floor-flush-hl35-development"
REVISION = "hl35-all-duty-direct-replacement-v1"
SOURCE_PINS = {
    "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json": "0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187",
    "docs/wood-joints-mvp/source-inventory.json": "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    "site/owner-wood-joints-wj24-scene.json": "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf",
}
SNAPSHOT_PATH = next(p for p in SOURCE_PINS if p.endswith("geometry-snapshot.json"))
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
REACH = 82.55
BEND_LENGTH = 127.0
HOLE_OFFSET = 50.8  # horizontal flange coordinate remains unverified
HOLE_PITCH = 63.5
WOOD_MIN = 88.9
PLATE = 5.0  # conservative planning occupancy; not a delivered gauge
BORE = 14.2875  # conditional 9/16-in wood clearance, not a drilling instruction
BOLT = 12.7
RELEASE = {
    "candidate_accepted": False,
    "complete_joint_acceptance": False,
    "capacity_established": False,
    "fabrication_released": False,
    "structural_released": False,
    "climbing_released": False,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources() -> tuple[dict, dict, dict]:
    for path, expected in SOURCE_PINS.items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"frozen parent bytes differ: {path}")
    return tuple(json.loads((ROOT / p).read_text()) for p in (
        SNAPSHOT_PATH, INVENTORY_PATH, "site/owner-wood-joints-wj24-scene.json"
    ))


def xyz(vector: cq.Vector) -> list[float]:
    return [round(value, 9) for value in vector.toTuple()]


def projected_extent(shape: cq.Shape, direction: cq.Vector) -> tuple[float, float]:
    values = [vertex.Center().dot(direction) for vertex in shape.Vertices()]
    return min(values), max(values)


def line_key(member: str, point: cq.Vector, direction: cq.Vector) -> tuple:
    """Opposed flange attachments on one physical wood bore share an identity."""
    unit = direction.normalized()
    first = next(value for value in unit.toTuple() if abs(value) > 1e-8)
    if first < 0:
        unit = unit.multiply(-1)
    foot = point - unit.multiply(point.dot(unit))
    return (member, *(round(v, 6) for v in unit.toTuple()),
            *(round(v, 6) for v in foot.toTuple()))


def overlaps(a: cq.Shape, b: cq.Shape) -> float:
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(min(getattr(aa, f"{x}max"), getattr(bb, f"{x}max")) -
           max(getattr(aa, f"{x}min"), getattr(bb, f"{x}min")) < 1e-6 for x in "xyz"):
        return 0.0
    return max(0.0, a.intersect(b).Volume())


def reconstructed_wood(snapshot: dict) -> tuple[dict[str, cq.Shape], dict[str, cq.Vector]]:
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    shifts = {}
    for name, row in snapshot["members"].items():
        if name not in wood:
            continue  # old candidate blocks are deliberately absent
        shape, target = wood[name], row["raw"]
        bounds = shape.BoundingBox()
        shift = cq.Vector(*(target["min_xyz_mm"][i] - getattr(bounds, f"{a}min")
                            for i, a in enumerate("xyz")))
        shape = shape.translate(shift)
        b = shape.BoundingBox()
        if any(abs(getattr(b, f"{a}max") - target["max_xyz_mm"][i]) > 1e-5
               for i, a in enumerate("xyz")) or abs(shape.Volume() - target["volume_mm3"]) > 0.1:
            raise ValueError(f"current raw profile is not a rigid translation: {name}")
        wood[name], shifts[name] = shape, shift
    if len(shifts) != 16:
        raise ValueError("expected 16 authenticated receiving hosts")
    return wood, shifts


@dataclass
class Angle:
    id: str
    duty: str
    beam: str
    post: str
    origin: cq.Vector
    u: cq.Vector
    v: cq.Vector
    w: cq.Vector
    shape: cq.Shape

    def point(self, u: float, v: float, w: float) -> cq.Vector:
        return self.origin + self.u.multiply(u) + self.v.multiply(v) + self.w.multiply(w)

    def placed(self, shape: cq.Shape) -> cq.Shape:
        return shape.moved(cq.Plane(origin=self.origin, xDir=self.u, normal=self.w).location)


def angle_shape() -> cq.Shape:
    shape = cq.Solid.makeBox(REACH, PLATE, BEND_LENGTH, cq.Vector(0, 0, -BEND_LENGTH / 2))
    shape = shape.fuse(cq.Solid.makeBox(PLATE, REACH, BEND_LENGTH,
                                     cq.Vector(0, 0, -BEND_LENGTH / 2))).clean()
    for w in (-HOLE_PITCH / 2, HOLE_PITCH / 2):
        for point, direction in ((cq.Vector(HOLE_OFFSET, -1, w), cq.Vector(0, 1, 0)),
                                 (cq.Vector(-1, HOLE_OFFSET, w), cq.Vector(1, 0, 0))):
            shape = shape.cut(cq.Solid.makeCylinder(BORE / 2, PLATE + 2, point, direction))
    return shape.clean()


def build_angles(wood: dict, shifts: dict, *, align_changed_faces: bool = False) -> list[Angle]:
    template = angle_shape()
    angles = []
    for duty, origin, u, v, beam, post in variant(KERF_RIGHT).stations():
        if duty in TRANSLATE_NAMES:
            origin += cq.Vector(-KERF_RIGHT_MM, 0, 0)
        # Raised bottom rails and relocated kicker posts belong to the reviewed model.
        origin += shifts[beam] if "horizontal_bottom" in duty else shifts[post]
        pmin, pmax = projected_extent(wood[post], u)
        if align_changed_faces:
            origin += u.multiply(pmax - origin.dot(u))
            _, bmax = projected_extent(wood[beam], v)
            origin += v.multiply(bmax - origin.dot(v))
        if abs(origin.dot(u) - pmax) > 1e-5:
            raise ValueError(f"station does not start on the receiving face: {duty}")
        for face, o, reach in (("near", origin, u),
                                ("opposed", origin - u.multiply(pmax - pmin), u.multiply(-1))):
            w = reach.cross(v)
            angle = Angle(f"angle_hl35_{duty}_{face}", duty, beam, post, o, reach, v, w, template)
            angle.shape = angle.placed(template)
            angles.append(angle)
    if len(angles) != 48:
        raise ValueError("expected paired envelopes on each of 24 duties")
    return angles


def audit(wood: dict, angles: list[Angle], snapshot: dict, inventory: dict) -> tuple[dict, list[dict]]:
    attachments = []
    axes = {}
    seats = []
    for angle in angles:
        for flange, member, inward, along in (("beam", angle.beam, angle.v.multiply(-1), angle.u),
                                               ("post", angle.post, angle.u.multiply(-1), angle.v)):
            # A thin inward skin measures nominal full bearing independently of the bore tests.
            local_skin = (cq.Solid.makeBox(REACH, .05, BEND_LENGTH,
                                           cq.Vector(0, -.05, -BEND_LENGTH / 2)) if flange == "beam" else
                          cq.Solid.makeBox(.05, REACH, BEND_LENGTH,
                                           cq.Vector(-.05, 0, -BEND_LENGTH / 2)))
            skin = angle.placed(local_skin)
            supported = min(1.0, overlaps(skin, wood[member]) / skin.Volume())
            seats.append({"angle_id": angle.id, "duty_id": angle.duty, "flange": flange,
                          "receiver": member, "nominal_rectangular_bearing_fraction": round(supported, 6),
                          "full_nominal_bearing": supported > .99999})
            pmin, pmax = projected_extent(wood[member], inward)
            thickness = pmax - pmin
            for index, w in enumerate((-HOLE_PITCH / 2, HOLE_PITCH / 2), 1):
                point = angle.origin + along.multiply(HOLE_OFFSET) + angle.w.multiply(w)
                cylinder = cq.Solid.makeCylinder(BORE / 2, WOOD_MIN, point, inward)
                fraction = min(1.0, overlaps(cylinder, wood[member]) / cylinder.Volume())
                key = line_key(member, point, inward)
                if key not in axes:
                    axes[key] = {"id": f"hl35_bolt_{len(axes) + 1:03d}", "receiver": member,
                                 "point": point, "direction": inward, "grip_mm": thickness,
                                 "attachments": []}
                axis = axes[key]
                attachment = {"angle_id": angle.id, "duty_id": angle.duty, "flange": flange,
                              "hole_index": index, "physical_axis_id": axis["id"], "receiver": member,
                              "seat_point_xyz_mm": xyz(point), "inward_axis_xyz": xyz(inward),
                              "projected_raw_member_thickness_mm": round(thickness, 6),
                              "minimum_thickness_present_at_hole": fraction > .99999,
                              "minimum_88_9_mm_bore_wood_fraction": round(fraction, 6)}
                attachments.append(attachment)
                axis["attachments"].append(attachment)

    plate_clashes = []
    for i, a in enumerate(angles):
        for b in angles[i + 1:]:
            volume = overlaps(a.shape, b.shape)
            if volume > .01:
                plate_clashes.append({"first": a.id, "second": b.id, "intersection_mm3": round(volume, 3)})
    wood_clashes = []
    for angle in angles:
        for name, shape in wood.items():
            volume = overlaps(angle.shape, shape)
            if volume > .01:
                wood_clashes.append({"angle_id": angle.id, "member": name,
                                     "intersection_mm3": round(volume, 3)})

    moves = {row["axis_id"]: row for row in snapshot["panel_screws"]}
    screws = []
    for row in inventory["fixed_panel_kicker_screws"]:
        move = moves.get(row["axis_id"])
        point = cq.Vector(*(move["new_start_global_xyz_mm"] if move else row["origin_global_xyz_mm"]))
        direction = cq.Vector(*row["axis_global_xyz"])
        member = move["receiver_member"] if move else row["candidate_finished_receiver_member"]
        envelope = cq.Solid.makeCylinder(row["source_occupied_diameter_mm"] / 2, 63.5, point, direction)
        hits = [angle.id for angle in angles if overlaps(envelope, angle.shape) > .01]
        screws.append({"axis_id": row["axis_id"], "origin_global_xyz_mm": xyz(point),
                       "axis_global_xyz": xyz(direction), "receiver": member,
                       "prior_owner_move_retained": bool(move),
                       "new_candidate_axis_moved": False, "plate_clashes": hits,
                       "raw_receiver_intersection_mm3": round(overlaps(envelope, wood[member]), 3)})
    if len(screws) != 66 or len({row["axis_id"] for row in screws}) != 66:
        raise ValueError("expected exactly 66 unique preserved panel screws")

    duties = []
    for duty in sorted({a.duty for a in angles}):
        aa = [row for row in attachments if row["duty_id"] == duty]
        ss = [row for row in seats if row["duty_id"] == duty]
        ids = {a.id for a in angles if a.duty == duty}
        findings = []
        if any(not row["minimum_thickness_present_at_hole"] for row in aa):
            findings.append("catalog_minimum_receiving_wood_missing")
        if any(not row["full_nominal_bearing"] for row in ss):
            findings.append("nominal_full_flange_bearing_missing")
        if any(row["first"] in ids or row["second"] in ids for row in plate_clashes):
            findings.append("angle_envelopes_intersect")
        if any(row["angle_id"] in ids for row in wood_clashes):
            findings.append("angle_envelope_intersects_timber_or_panel")
        if any(ids.intersection(row["plate_clashes"]) for row in screws):
            findings.append("purchased_screw_envelope_intersects_angle")
        duties.append({"duty_id": duty, "angles": sorted(ids), "status": "REVISE" if findings else "UNQUALIFIED",
                       "fit_findings": findings, "physical_bolt_axes": sorted({row["physical_axis_id"] for row in aa}),
                       "catalog_resistance_utilization": None,
                       "load_path_status": "not_established_for_complete_joint_wrench"})
    axis_rows = [{**{k: v for k, v in axis.items() if k not in {"point", "direction", "attachments"}},
                  "point_xyz_mm": xyz(axis["point"]), "direction_xyz": xyz(axis["direction"]),
                  "attachment_ids": [f'{a["angle_id"]}:{a["flange"]}:{a["hole_index"]}' for a in axis["attachments"]]}
                 for axis in axes.values()]
    report = {
        "schema": "hl35_candidate_fit_assessment/v1", "candidate": CANDIDATE, "revision": REVISION,
        "status": "REVISE", "source_sha256": SOURCE_PINS,
        "counts": {"duties": 24, "hl35_angles": len(angles), "flange_hole_attachments": len(attachments),
                   "new_physical_bolt_axes": len(axes), "retained_frame_bolt_axes": 12,
                   "panel_kicker_screw_axes": len(screws), "removed_wood_blocks": 24,
                   "removed_wood_candidate_bolt_axes": 92,
                   "duties_requiring_geometry_revision": sum(row["status"] == "REVISE" for row in duties),
                   "flanges_without_full_nominal_bearing": sum(not row["full_nominal_bearing"] for row in seats),
                   "attachments_missing_minimum_receiving_wood": sum(not row["minimum_thickness_present_at_hole"] for row in attachments),
                   "angle_angle_intersections": len(plate_clashes), "angle_wood_or_panel_intersections": len(wood_clashes),
                   "panel_screw_axes_intersecting_angles": sum(bool(row["plate_clashes"]) for row in screws)},
        "parameters_mm": {"flange_reach": REACH, "bend_length": BEND_LENGTH, "hole_pitch": HOLE_PITCH,
                          "conditional_hole_offset": HOLE_OFFSET, "planning_plate_thickness": PLATE,
                          "conditional_wood_bore_diameter": BORE, "bolt_diameter": BOLT,
                          "catalog_minimum_receiver_thickness": WOOD_MIN},
        "duties": duties, "flange_seats": seats, "flange_attachments": attachments,
        "physical_bolt_axes": axis_rows, "panel_screw_axes": screws,
        "angle_angle_intersections": plate_clashes, "angle_wood_or_panel_intersections": wood_clashes,
        "load_basis": {"climber_weight_lb": 250, "downward_multiplier": 2,
                       "horizontal_force_N": 300, "hold_lever_mm": 100,
                       "fresh_frame_or_joint_force_fields": False,
                       "inherited_joint_passes": False, "floor_no_slip_verified": False},
        "mechanics_gates": {
            "geometry_fit": False, "current_catalog_and_factory_hole_geometry_verified": False,
            "direction_and_pair_installation_applicable": False, "complete_force_and_moment_load_path": False,
            "bolt_group_wood_resistance_and_edge_distance": False, "hardware_fit_and_assembly_access": False,
            "panel_resistance_reassessed": False, "native_solve_ready": False,
        },
        "limits": [
            "HL35 is the catalog model; HL35S has not been verified as a separate Simpson SKU.",
            "The 5 mm ideal flat-angle envelope is not measured steel, a bend-radius model or a material strength.",
            "Horizontal flange hole offset is assumed; neither factory holes nor wood drill sizes are selected.",
            "Raw host profiles preserve reviewed stock positions; old candidate bores are not carried into fresh stock.",
            "Receiving-host service passages and candidate machining are omitted in this initial fit experiment; net sections are unassessed.",
            "Bolt/nut/washer display envelopes are planning allowances, not catalog or delivered stack qualification.",
            "Only catalog-listed directions may be compared after orientation, duration and installation are established.",
            "Opposed connectors do not double the catalog lateral rating; no arbitrary moment or transverse capacity is supplied.",
            "Electrical solids, T-nuts, retained bolt hardware and tool sweeps need exact clearance checks after a viable pose exists.",
            "Failing nominal fit is sufficient to reject this pose; no structural, fabrication or climbing release is claimed.",
        ],
        "release": RELEASE,
    }
    return report, list(axes.values())


def hardware_shapes(axis: dict, wood: dict) -> list[tuple[str, cq.Shape]]:
    grip = axis["grip_mm"]
    direction, front = cq.Vector(0, 0, 1), cq.Vector(0, 0, 0)
    # Opposed post flanges share a shaft; beam flange shafts have one ideal steel plate.
    back_plate = PLATE if len(axis["attachments"]) > 1 else 0.0
    start = front - direction.multiply(PLATE + 3)
    length = math.ceil((grip + PLATE + back_plate + 6 + 11.2 + 4) / 6.35) * 6.35
    end = front + direction.multiply(grip + back_plate)
    def cylinder(radius: float, height: float, origin: cq.Vector) -> cq.Shape:
        return cq.Solid.makeCylinder(radius, height, origin, direction)
    washer = lambda origin: cylinder(19.05, 3, origin).cut(cylinder(7.15, 3, origin))
    return [
        ("shaft", cylinder(BOLT / 2, length, start)),
        ("head", cylinder(12.83, 8.6, start - direction.multiply(8.6))),
        ("head_washer", washer(start)),
        ("nut_washer", washer(end)),
        ("nut", cylinder(12.83, 11.2, end + direction.multiply(3)).cut(
            cylinder(BOLT / 2, 11.2, end + direction.multiply(3)))),
    ]


def export_scene(report: dict, wood: dict, shifts: dict, angles: list[Angle], axes: list[dict]) -> dict:
    solids = []
    templates = {}
    failed = {d["duty_id"] for d in report["duties"] if d["status"] == "REVISE"}
    def matrix(plane: cq.Plane) -> list[float]:
        return [*xyz(plane.xDir), 0, *xyz(plane.yDir), 0, *xyz(plane.zDir), 0, *xyz(plane.origin), 1]
    def add(name: str, shape: cq.Shape, kind: str, description: str,
            template_id: str | None = None, plane: cq.Plane | None = None, **fabrication) -> None:
        geometry = {"mesh": _shape_mesh(shape)} if template_id is None else {
            "template_id": template_id, "transform": matrix(plane)}
        if template_id is not None and template_id not in templates:
            templates[template_id] = {"id": template_id, "mesh": _shape_mesh(shape)}
        solids.append({"id": name, "name": name, **geometry,
                       "fabrication": {"kind": kind, "description": description,
                                       "clearance_status": "FAIL nominal fit; development pose" if kind == "bracket" else "Development envelope; unqualified",
                                       **fabrication}})
    for name in shifts:
        add(name, wood[name], "timber", "Reviewed raw profile; old corner blocks and old candidate bores removed; service machining unassessed")
    for angle in angles:
        add(angle.id, angle_shape(), "bracket", f"HL35 ideal 5 mm planning envelope; {angle.duty}; {'REVISE' if angle.duty in failed else 'UNQUALIFIED'}",
            template_id="hl35_flat_angle", plane=cq.Plane(origin=angle.origin, xDir=angle.u, normal=angle.w))
    for axis in axes:
        roles = ["shaft", "head", "head_washer", "nut_washer", "nut"]
        direction, point = axis["direction"], axis["point"]
        pmin, _ = projected_extent(wood[axis["receiver"]], direction)
        front = point + direction.multiply(pmin - point.dot(direction))
        plane = cq.Plane(origin=front, normal=direction)
        for role, shape in hardware_shapes(axis, wood):
            add(f'{axis["id"]}_{role}', shape, "bolt", "Conditional 1/2-inch planning hardware; unverified product and thread window",
                template_id=f'hardware_{role}_{axis["grip_mm"]:.5f}_{len(axis["attachments"])}', plane=plane,
                connection_name=axis["id"], hardware_role=role, stack_roles=roles)
    topologies = _deduplicate_triangle_topologies([row for row in solids if "mesh" in row] + list(templates.values()))
    return {
        "schema": "hl35_candidate_display_delta/v1", "candidate": CANDIDATE,
        "revision": REVISION, "status": "REVISE",
        "parent_scene": {"url": "owner-wood-joints-wj24-scene.json", "sha256": SOURCE_PINS["site/owner-wood-joints-wj24-scene.json"]},
        "keep_parent_classes": ["baseline", "panel_replacement", "electrical_replacement"],
        "keep_parent_panel_screws": True,
        "replaced_host_names": sorted(shifts),
        "counts": report["counts"], "solids": solids, "mesh_templates": templates, "triangle_topologies": topologies,
        "release": RELEASE,
        "design": {"key": "hl35-development", "status": "REVISE", "qualified_for_design": False,
                   "documents": [{"label": "HL35 candidate and fit assessment", "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/README.md"},
                                 {"label": "Current development ledger", "path": "docs/wood-joints-mvp/completion-ledger.md"}]},
    }


def thick_stock_trial(wood: dict) -> dict:
    """Isolate minimum thickness; this does not adopt altered stock or poses."""
    trial = dict(wood)
    slope = cq.Vector(0, math.sin(math.radians(40)), math.cos(math.radians(40)))
    for name in ("base_principal_center_left", "base_principal_center_right",
                 "base_post_center_left", "base_post_center_right"):
        trial[name] = wood[name].fuse(wood[name].translate((-25.4, 0, 0)),
                                      wood[name].translate((25.4, 0, 0))).clean()
    for side, shift in (("left", 50.8), ("right", -50.8)):
        name = f"base_post_outer_{side}"
        trial[name] = wood[name].fuse(wood[name].translate((shift, 0, 0)),
                                      wood[name].translate((shift / 2, 0, 0))).clean()
    for name in [key for key in wood if key.startswith("base_rail_")]:
        trial[name] = wood[name].fuse(wood[name].translate(slope.multiply(-25.4)),
                                     wood[name].translate(slope.multiply(25.4))).clean()
    header = wood["base_header"]
    trial["base_header"] = header.fuse(header.translate((0, 0, -25.4)),
                                        header.translate((0, 0, -50.8))).clean()
    hb = trial["base_header"].BoundingBox()
    for name in [key for key in trial if key.startswith("base_post_")]:
        b = trial[name].BoundingBox()
        keep = cq.Solid.makeBox(b.xlen + 2, b.ylen + 2, hb.zmin,
                                cq.Vector(b.xmin - 1, b.ymin - 1, 0))
        trial[name] = trial[name].intersect(keep).clean()
    return trial


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=ROOT / "site/hl35-candidate-scene.json")
    parser.add_argument("--thickness-trial", action="store_true", help="also audit an unadopted 3.5-inch-stock sensitivity")
    args = parser.parse_args()
    snapshot, inventory, _ = load_sources()
    wood, shifts = reconstructed_wood(snapshot)
    angles = build_angles(wood, shifts)
    print("Built 48 HL35 planning envelopes; auditing 24 duties", flush=True)
    report, axes = audit(wood, angles, snapshot, inventory)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "fit-assessment.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["counts"], sort_keys=True), flush=True)
    scene = export_scene(report, wood, shifts, angles, axes)
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    outputs = [args.out / "fit-assessment.json", args.scene]
    if args.thickness_trial:
        trial = thick_stock_trial(wood)
        trial_angles = build_angles(trial, shifts, align_changed_faces=True)
        trial_report, _ = audit(trial, trial_angles, snapshot, inventory)
        trial_report["revision"] = "hl35-3p5-stock-thickness-sensitivity-v1"
        trial_report["is_adopted_candidate_geometry"] = False
        trial_report["changed_raw_hosts"] = sorted(name for name in shifts if abs(trial[name].Volume() - wood[name].Volume()) > .1)
        trial_report["scope"] = "Thickness-only sensitivity; paired-angle bearing, complete layout and inherited member machining are not corrected. Original screw receiver identities are checked without automatic reassignment."
        trial_report["new_raw_member_intersections"] = [
            {"first": a, "second": b, "intersection_mm3": round(volume, 3)}
            for i, a in enumerate(shifts) for b in list(shifts)[i + 1:]
            if (volume := overlaps(trial[a], trial[b])) > .01
        ]
        path = args.out / "thickness-sensitivity.json"
        path.write_text(json.dumps(trial_report, indent=2, allow_nan=False) + "\n")
        outputs.append(path)
        print("Thickness sensitivity: " + json.dumps(trial_report["counts"], sort_keys=True), flush=True)
    manifest = {
        "schema": "hl35_candidate_evidence_bindings/v1", "candidate": CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_candidate" + (" --thickness-trial" if args.thickness_trial else ""),
        "versions": {"cadquery": cq.__version__},
        "source_sha256": {**SOURCE_PINS, "scripts/hl35_candidate.py": sha(Path(__file__))},
        "outputs": {str(p.relative_to(ROOT)): sha(p) for p in outputs},
        "release": RELEASE,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Scene: {args.scene.stat().st_size} bytes; SHA256 {sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
