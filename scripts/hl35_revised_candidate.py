"""Revised HL35 layout with a common center, wider rails and explicit end bearing.

Catalog capacities are not adopted. The bidirectional single-angle beam-end
proposal requires separate compression/contact and complete joint evidence.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import cadquery as cq

from scripts import hl35_candidate as base

REVISION = "hl35-common-center-and-bearing-v2"
PACKET = base.PACKET / "common-center-and-bearing-v2"
T = cq.Vector(0, math.sin(math.radians(40)), math.cos(math.radians(40)))
N = cq.Vector(0, -math.cos(math.radians(40)), math.sin(math.radians(40)))
X = cq.Vector(1, 0, 0)


def prism(xmin: float, xmax: float, tmin: float, tmax: float,
          nmin: float, nmax: float) -> cq.Shape:
    local = cq.Solid.makeBox(xmax - xmin, tmax - tmin, nmax - nmin,
                             cq.Vector(xmin, tmin, nmin))
    return local.moved(cq.Plane(origin=(0, 0, 0), xDir=X, normal=N).location)


def yz_prism(xmin: float, xmax: float, points: list[tuple[float, float]]) -> cq.Shape:
    vertices = [cq.Vector(xmin, y, z) for y, z in points]
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([*vertices, vertices[0]]))
    return cq.Solid.extrudeLinear(face.outerWire(), [], cq.Vector(xmax - xmin, 0, 0))


def revised_wood(source: dict) -> tuple[dict, dict]:
    wood = dict(source)
    nmin, nmax = base.projected_extent(source["base_side_left"], N)
    xmin = source["base_side_left"].BoundingBox().xmin
    xmax = source["base_side_right"].BoundingBox().xmax
    seam_x = -1.5875
    bottom = base.projected_extent(source["main_lower_left"], T)[0]
    toe = bottom + 19.05
    top_min, _ = base.projected_extent(source["base_rail_top"], T)
    top_max = top_min + 88.9
    # A solid 6x8 timber envelope: 5.5 in in N, 7.5 in in X, not two glued ribs.
    core_xmin, core_xmax = seam_x - 190.5 / 2, seam_x + 190.5 / 2
    wood.pop("base_principal_center_left")
    wood.pop("base_principal_center_right")
    wood["hl35_center_principal"] = prism(core_xmin, core_xmax, toe, top_min, nmin, nmax)
    for side in ("left", "right"):
        name = f"base_side_{side}"
        b = source[name].BoundingBox()
        wood[name] = prism(b.xmin, b.xmax, toe, top_max, nmin, nmax)

    for name in [key for key in source if key.startswith("base_rail_")]:
        tmin, tmax = base.projected_extent(source[name], T)
        if name == "base_rail_top":
            lo, hi, left, right = tmin, tmin + 88.9, xmin + 88.9, xmax - 88.9
        else:
            side = "left" if name.endswith("_left") else "right"
            left, right = ((xmin + 88.9, core_xmin) if side == "left" else (core_xmax, xmax - 88.9))
            # Keep the source connector-side face. Reverse-face poses are tried separately.
            if "service_lower" in name:
                lo, hi = tmin, tmin + 88.9
            else:
                lo, hi = tmax - 88.9, tmax
        wood[name] = prism(left, right, lo, hi, nmin, nmax)

    header_xmin, header_xmax = xmin - 82.55, xmax + 82.55
    front, back, underside = -36.0, -175.7, 188.1
    kink_z = (nmin + front * math.cos(math.radians(40))) / math.sin(math.radians(40))
    front_top = T.multiply(toe) + N.multiply(nmin)
    back_top_z = (toe - back * T.y) / T.z
    points = [(back, underside), (front, underside), (front, kink_z),
              (front_top.y, front_top.z), (back, back_top_z)]
    wood["base_header"] = yz_prism(header_xmin, header_xmax, points)
    for side in ("left", "right"):
        for kind in ("outer", "center"):
            name = f"base_post_{kind}_{side}"
            old = source[name].BoundingBox()
            center = (old.xmin + old.xmax) / 2
            if kind == "outer":
                center = xmin + 44.45 if side == "left" else xmax - 44.45
            wood[name] = cq.Solid.makeBox(88.9, 139.7, underside,
                                          cq.Vector(center - 44.45, back, 0))
    # This backer receives the otherwise unsupported kicker seam, without new panel screws.
    wood["hl35_kicker_seam_backer"] = cq.Solid.makeBox(88.9, 88.9, underside - 25.4,
                                                      cq.Vector(seam_x - 44.45, -124.9, 25.4))
    # Two vertical through-bolts require their own end-grain/dowel and tool checks.
    backer_axes = []
    for index, x in enumerate((seam_x - 25.4, seam_x + 25.4), 1):
        y = -80.45
        local_top = (toe - y * T.y) / T.z
        # Recess the head below the lowest inclined-top point under a 38.1 mm washer.
        head_top = local_top - 19.05 * math.tan(math.radians(40)) - 3
        seat = head_top - 11.6
        counterbore = cq.Solid.makeCylinder(19.05, local_top - seat + 30,
                                           cq.Vector(x, y, seat), cq.Vector(0, 0, 1))
        wood["base_header"] = wood["base_header"].cut(counterbore).clean()
        backer_axes.append({"axis_id": f"hl35_seam_backer_tie_{index}",
                            "point_xyz_mm": [x, y, seat], "direction_xyz": [0, 0, -1],
                            "shaft_diameter_mm": 9.525, "conditional_wood_bore_diameter_mm": 11.1125,
                            "header_head_seat_z_mm": seat, "backer_lower_face_z_mm": 25.4,
                            "full_load_path_qualified": False,
                            "limits": "End-grain through-bolt load transfer, wood/washer bearing, root/body/thread windows and removal access remain unqualified."})
    dims = {"n_mm": [nmin, nmax], "toe_t_mm": toe, "top_t_mm": [top_min, top_max],
            "core_x_mm": [core_xmin, core_xmax], "header_x_mm": [header_xmin, header_xmax],
            "header_yz_profile_mm": points, "seam_backer_ties": backer_axes}
    return wood, dims


def placed_angle(duty: str, label: str, beam: str, post: str, origin: cq.Vector,
                 u: cq.Vector, v: cq.Vector) -> base.Angle:
    w = u.cross(v)
    angle = base.Angle(f"angle_hl35_{duty}_{label}", duty, beam, post, origin, u, v, w, base.angle_shape())
    angle.shape = angle.placed(angle.shape)
    return angle


def revised_angles(wood: dict, dims: dict) -> list[base.Angle]:
    angles = []
    nmid = sum(dims["n_mm"]) / 2
    # Pair at principal toes. The explicit forward offset keeps a full inward wood cylinder in the header.
    for label, post in (("outer_left", "base_side_left"), ("center", "hl35_center_principal"),
                         ("outer_right", "base_side_right")):
        b = wood[post].BoundingBox()
        for face, x, u in (("left", b.xmin, X.multiply(-1)), ("right", b.xmax, X)):
            origin = X.multiply(x) + T.multiply(dims["toe_t_mm"]) + N.multiply(nmid - 6.35)
            angles.append(placed_angle(f"principal_header_{label}", face, "base_header", post, origin, u, T))
    # Header-to-kicker-post joints retain genuinely opposed installations.
    for side in ("left", "right"):
        for kind in ("outer", "center"):
            post = f"base_post_{kind}_{side}"
            b = wood[post].BoundingBox()
            for face, x, u in (("left", b.xmin, X.multiply(-1)), ("right", b.xmax, X)):
                origin = cq.Vector(x, -105.85, 188.1)
                angles.append(placed_angle(f"kicker_header_{kind}_{side}", face, "base_header", post,
                                          origin, u, cq.Vector(0, 0, -1)))
    # Single angle at each terminated beam end; compression is a separate wood contact obligation.
    for side in ("left", "right"):
        for level in ("bottom", "service_lower", "service_upper"):
            beam = f"base_rail_{level}_{side}"
            lo, hi = base.projected_extent(wood[beam], T)
            # Below bottom/lower beams and above upper beams keeps the existing row separation.
            face_t, v = (lo, T.multiply(-1)) if level != "service_upper" else (hi, T)
            b = wood[beam].BoundingBox()
            if side == "left":
                endpoints = (("outer", b.xmin, X, "base_side_left"),
                             ("center", b.xmax, X.multiply(-1), "hl35_center_principal"))
            else:
                endpoints = (("center", b.xmin, X, "hl35_center_principal"),
                             ("outer", b.xmax, X.multiply(-1), "base_side_right"))
            for label, x, u, post in endpoints:
                origin = X.multiply(x) + T.multiply(face_t) + N.multiply(nmid)
                angles.append(placed_angle(f"rail_{level}_{side}_{label}", "single", beam, post, origin, u, v))
    beam = "base_rail_top"
    lo, _ = base.projected_extent(wood[beam], T)
    for side, post, u in (("left", "base_side_left", X), ("right", "base_side_right", X.multiply(-1))):
        b = wood[post].BoundingBox()
        x = b.xmax if side == "left" else b.xmin
        origin = X.multiply(x) + T.multiply(lo) + N.multiply(nmid)
        angles.append(placed_angle(f"rail_top_outer_{side}", "single", beam, post, origin, u, T.multiply(-1)))
    core = wood["hl35_center_principal"].BoundingBox()
    for face, x, u in (("left", core.xmin, X.multiply(-1)), ("right", core.xmax, X)):
        origin = X.multiply(x) + T.multiply(lo) + N.multiply(nmid)
        angles.append(placed_angle("rail_top_center", face, beam, "hl35_center_principal", origin, u, T.multiply(-1)))
    return angles


def remap_receivers(snapshot: dict, inventory: dict) -> tuple[dict, dict, list[dict]]:
    snapshot, inventory = copy.deepcopy(snapshot), copy.deepcopy(inventory)
    moves = {row["axis_id"]: row for row in snapshot["panel_screws"]}
    changes = []
    for row in inventory["fixed_panel_kicker_screws"]:
        move = moves.get(row["axis_id"])
        old = move["receiver_member"] if move else row["candidate_finished_receiver_member"]
        point = move["new_start_global_xyz_mm"] if move else row["origin_global_xyz_mm"]
        new = "hl35_center_principal" if old.startswith("base_principal_center_") else old
        if old.startswith("base_post_") and point[2] > 188.1:
            new = "base_header"
        row["candidate_finished_receiver_member"] = new
        if move:
            move["receiver_member"] = new
        if old != new:
            changes.append({"axis_id": row["axis_id"], "old_receiver": old, "new_receiver": new,
                            "axis_moved": False})
    return snapshot, inventory, changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET)
    parser.add_argument("--scene", type=Path, default=base.ROOT / "site/hl35-revised-scene.json")
    args = parser.parse_args()
    snapshot, inventory, _ = base.load_sources()
    source, shifts = base.reconstructed_wood(snapshot)
    wood, dims = revised_wood(source)
    angles = revised_angles(wood, dims)
    changed_snapshot, changed_inventory, receiver_changes = remap_receivers(snapshot, inventory)
    print(f"Built {len(angles)} revised HL35 envelopes; auditing", flush=True)
    report, axes = base.audit(wood, angles, changed_snapshot, changed_inventory)
    report["revision"] = REVISION
    report["counts"]["duties"] = len(report["duties"])
    report["counts"]["auxiliary_seam_backer_tie_axes"] = 2
    report["layout_parameters"] = dims
    report["changed_screw_receiver_identities"] = receiver_changes
    report["joint_architecture"] = {
        "paired_angle_duties": sorted(d for d in {a.duty for a in angles}
                                      if sum(a.duty == d for a in angles) == 2),
        "single_angle_and_compression_contact_duties": sorted(a.duty for a in angles
            if sum(b.duty == a.duty for b in angles) == 1),
        "catalog_pair_rule_qualified": False,
        "single_angle_scope": "No bidirectional catalog lateral credit. Separation and reverse-sign wood end bearing must be checked as independent signed paths; all moments/transverse demands remain unqualified.",
        "seam_backer": "Separate end-grain through-bolt joint; no HL capacity or old block pass assigned.",
    }
    receivers = set(shifts) - {"base_principal_center_left", "base_principal_center_right"}
    receivers.update({"hl35_center_principal", "hl35_kicker_seam_backer"})
    member_clashes = [
        {"first": a, "second": b, "intersection_mm3": round(volume, 3)}
        for i, a in enumerate(sorted(receivers)) for b in sorted(receivers)[i + 1:]
        if (volume := base.overlaps(wood[a], wood[b])) > .01
    ]
    report["new_raw_member_intersections"] = member_clashes
    report["counts"]["raw_member_intersections"] = len(member_clashes)
    report["counts"]["panel_screw_axes_without_raw_receiver"] = sum(r["raw_receiver_intersection_mm3"] < .01 for r in report["panel_screw_axes"])
    # Receiving depth at an old screw is compared to its reviewed raw geometry, not guessed from nominal length.
    source_snapshot, source_inventory, _ = base.load_sources()
    source_moves = {r["axis_id"]: r for r in source_snapshot["panel_screws"]}
    screw_receiving = []
    revised_screws = {r["axis_id"]: r for r in report["panel_screw_axes"]}
    for row in source_inventory["fixed_panel_kicker_screws"]:
        move = source_moves.get(row["axis_id"])
        old_receiver = move["receiver_member"] if move else row["candidate_finished_receiver_member"]
        new = revised_screws[row["axis_id"]]
        cylinder = cq.Solid.makeCylinder(row["source_occupied_diameter_mm"] / 2, 63.5,
                                         cq.Vector(*new["origin_global_xyz_mm"]), cq.Vector(*new["axis_global_xyz"]))
        old_volume = base.overlaps(cylinder, source[old_receiver])
        screw_receiving.append({"axis_id": row["axis_id"], "source_raw_receiving_mm3": round(old_volume, 3),
                                "new_raw_receiving_mm3": new["raw_receiver_intersection_mm3"],
                                "raw_receiving_reduced": new["raw_receiver_intersection_mm3"] + .02 < old_volume})
    report["screw_receiving_comparison"] = screw_receiving
    report["counts"]["panel_screw_raw_receiving_reductions"] = sum(r["raw_receiving_reduced"] for r in screw_receiving)
    report["counts"]["total_proposed_structural_bolt_axes"] = len(axes) + 12 + 2
    report["stock_envelopes"] = {
        "outer_principals": "4x6: X88.9 x N139.7 mm, square inclined toes and 50.8 mm extended upper end",
        "common_center": "solid 6x8 timber envelope: X190.5 x N139.7 mm; actual section and grade unverified",
        "rails": "4x6: T88.9 x N139.7 mm; retain front plane and source connector-side faces",
        "header": "solid 6x12 stock envelope; shaped wedge, 88.9 mm front depth below the kicker top, inclined upper seat and panel-bottom backing lip; not a built-up beam",
        "kicker_posts": "four solid 4x6: X88.9 x Y139.7, height188.1 mm",
        "kicker_seam": "solid 4x4 backer, X88.9 x Y88.9, Z25.4..188.1; two separate vertical 3/8-in planning ties",
    }
    report["retained_frame_bolt_changes"] = {
        "axes_moved": False,
        "outer_kicker_post_x_thickness_increase_mm": 50.8,
        "new_lengths_required_at_affected_front_bolts": True,
        "starting_frame_bolt_hardware_qualified": False,
        "display": "Starting frame metal remains source context until every affected grip, shaft and thread window is rebuilt and checked.",
    }
    report["limits"].extend([
        "The corrected current geometry is not replaced; all member/receiver changes occur only in this new revision.",
        "A single angle plus explicit wood compression is a proposed combined path, not a manufacturer-qualified pair replacement.",
        "The inclined header must be a realizable solid stock profile; cut/grade/net-section and cost remain unverified.",
        "The two seam-backers ties have not received end-grain resistance or access qualification.",
        "Service bores, T-nut/LED/wire clearances, frame hardware and tool/removal operations remain required before a finished model or native solve.",
    ])
    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / "fit-assessment.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["counts"], sort_keys=True), flush=True)
    new_shifts = {name: cq.Vector(0, 0, 0) for name in sorted(receivers)}
    scene = base.export_scene(report, wood, new_shifts, angles, axes)
    scene["revision"] = REVISION
    scene["replaced_host_names"] = sorted(shifts)
    scene["design"]["key"] = "hl35-revised-development"
    scene["design"]["documents"][0] = {"label": "Revised HL35 candidate and limits",
        "path": "docs/wood-joints-mvp/hypotheses/hl35-candidate/common-center-and-bearing-v2/README.md"}
    scene["auxiliary_tie_axes_not_displayed"] = dims["seam_backer_ties"]
    scene["retained_frame_hardware_status"] = "Source context; affected grip and metal lengths must be revised"
    args.scene.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    manifest = {
        "schema": "hl35_candidate_evidence_bindings/v1", "candidate": base.CANDIDATE, "revision": REVISION,
        "command": ".venv/bin/python -m scripts.hl35_revised_candidate", "versions": {"cadquery": cq.__version__},
        "source_sha256": {**base.SOURCE_PINS, "scripts/hl35_candidate.py": base.sha(Path(base.__file__)),
                          "scripts/hl35_revised_candidate.py": base.sha(Path(__file__))},
        "outputs": {str(p.relative_to(base.ROOT)): base.sha(p) for p in (report_path, args.scene)},
        "release": base.RELEASE,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Revised scene: {args.scene.stat().st_size} bytes; SHA256 {base.sha(args.scene)}", flush=True)


if __name__ == "__main__":
    main()
