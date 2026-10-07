"""Compare separated header rows and shallow, removable wire channels.

The frozen raw/occupied failures remain unchanged. All modified routing is a
new proposal at retained LED endpoints. This reuses existing CAD/clearance
helpers and preserves stock sizes, screw count and starting frame axes.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard import no_shoes_frame, round_structural_wiring
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import hl35_candidate as shared
from scripts import hl35_full_fit_candidate as geometry_tools
from scripts import hl35_nominal_service_candidate as service_tools
from scripts import hl35_service_clearance as retained_services
from scripts import thin_bolted_candidate as thin
from scripts import thin_bolted_fitting_screen as screen
from scripts import thin_bolted_occupied as occupied

HEADER_DUTIES = {
    "clip_timber_header_outer_left", "clip_timber_header_outer_right",
    "clip_angle_base_left", "clip_angle_base_right",
}
SAE_WASHER = {"od_mm": 1.092 * 25.4, "id_mm": .546 * 25.4,
              "thickness_mm": .121 * 25.4,
              "source": "https://boltdepot.com/Product-Details?product=3051",
              "price_usd_each": .25,
              "minimum_published_thickness_mm_for_resistance": .074 * 25.4}


def simplify_route(route: list) -> list:
    """Remove redundant straight-line controls without changing the endpoints."""
    result = []
    for point in route:
        if result and (cq.Vector(*point) - cq.Vector(*result[-1])).Length < 1e-8:
            continue
        result.append(list(point))
        while len(result) >= 3:
            first, middle, last = [cq.Vector(*p) for p in result[-3:]]
            a, b = middle - first, last - middle
            if a.dot(b) > 0 and a.cross(b).Length <= 1e-9 * a.Length * b.Length:
                result.pop(-2)
            else:
                break
    if len(result) < 2:
        raise ValueError("routing requires two distinct endpoints")
    return result


def front_open_cutter(route: list, placement: list, radius: float) -> cq.Shape:
    """Circular sweep union covering the complete forward lifting corridor.

    For a planar route at depth d, the circle at the front has radius
    sqrt(d²+r²). It covers the whole rectangle |side|<=r, 0<=N<=d;
    the circle around the wire covers its remaining rear cap.
    """
    depths = [p[2] for p in route]
    if max(depths) - min(depths) > 1e-6 or min(depths) < 0:
        raise ValueError("front-open method requires a planar route at nonnegative depth")
    depth = depths[0]
    body, _ = service_tools.sweep(route, radius, placement)
    front_route = [[p[0], p[1], 0.] for p in route]
    front, _ = service_tools.sweep(front_route, math.hypot(depth, radius), placement)
    return body.fuse(front).clean()


def routed_services(depth: float) -> tuple[list, dict, list, list]:
    original, authentication = retained_services.service_parts()
    _, _, parent = shared.load_sources()
    replacements, records, cutters = {}, [], []
    for source in round_structural_wiring.segments():
        name = source["name"]
        prior = parent["revision_report"]["wire_endpoint_revisions"].get(name)
        route = copy.deepcopy(prior["route_local_mm"] if prior else source["route_local_mm"])
        placement = prior["source_placement_xyz_mm"] if prior else list(no_shoes_frame.SHIFT.toTuple())
        endpoints = [copy.deepcopy(route[0]), copy.deepcopy(route[-1])]
        for point in route[1:-1]:
            point[2] = depth
        if any(abs(p[2] - depth) > 1e-6 for p in (route[0], route[-1])):
            raise ValueError("shallow planar proposal must retain the existing endpoint depth")
        controls = copy.deepcopy(route)
        route = simplify_route(route)
        shape, length = service_tools.sweep(route, round_structural_wiring.CABLE_DIAMETER_MM / 2, placement)
        cutter = front_open_cutter(route, placement, 6.35)
        if source["string_connector_envelope"]:
            first, last = [round_structural_wiring.b.point(*p) for p in controls[1:3]]
            direction, midpoint = (last - first).normalized(), (first + last) * .5
            size = round_structural_wiring.GEOMETRY["connector_length"]
            body = cq.Solid.makeCylinder(round_structural_wiring.MEASURED_MAXIMUM_DIAMETER_MM / 2,
                                         size, midpoint - direction.multiply(size / 2), direction)
            shape = shape.fuse(body.translate(cq.Vector(*placement))).clean()
            for offset, radius in ((0., 9.35), (-depth, math.hypot(depth, 9.35))):
                clearance = cq.Solid.makeCylinder(radius, size + 6, midpoint - direction.multiply((size + 6) / 2), direction)
                cutter = cutter.fuse(clearance.translate(cq.Vector(*placement) + screen.N.multiply(offset))).clean()
        replacements[name] = shape
        records.append({"name": name, "route_local_mm": route, "control_route_local_mm": controls,
                        "placement_xyz_mm": placement,
                        "source_endpoints_local_mm": endpoints,
                        "endpoints_retained": [route[0], route[-1]] == endpoints,
                        "routed_length_mm": length,
                        "approximate_budget_mm": round_structural_wiring.APPROXIMATE_PATH_BUDGET_MM,
                        "within_approximate_budget": length <= round_structural_wiring.APPROXIMATE_PATH_BUDGET_MM,
                        "actual_slack_bend_radius_or_feed_verified": False})
        cutters.append((name, "wire", cutter))
    nonwire = occupied.service_cutters(original, parent, occupied.DEFAULT_SETTINGS)
    cutters.extend(row for row in nonwire if row[1] != "wire")
    parts = [(name, kind, replacements.get(name, shape)) for name, kind, shape in original]
    return parts, authentication, records, cutters


def row_layout(row_shift: float, bottom_extra_shift: float) -> tuple[dict, list, dict, dict, list]:
    raw, fitted, context = thin.geometry()
    for member in ("base_rail_bottom_left", "base_rail_bottom_right"):
        raw[member] = raw[member].translate(thin.T.multiply(bottom_extra_shift))
    source = json.loads(occupied.RAW_REPORT.read_text())
    for name, expected in {**source["source_pins"], **source["additional_source_sha256"]}.items():
        if shared.sha(shared.ROOT / name) != expected:
            raise ValueError(f"raw comparison binding differs: {name}")
    stations = {row[0]: row for row in variant(KERF_RIGHT).stations()}
    changed, installed, grouped = [], [], {}
    for old, fitting in fitted:
        shift = row_shift if old.duty in HEADER_DUTIES else 0.
        angle = screen.pose(fitting, raw, stations[old.duty], shift, old.id.endswith("_opposite"))
        changed.append((angle, fitting))
        record = screen.audit_pose(angle, fitting, raw, [])
        installed.append(record)
        for hole in record["holes"]:
            grouped.setdefault(tuple(hole["key"]), []).append({
                "angle_id": angle.id, "duty_id": angle.duty, **hole,
            })
    source["physical_axes"] = [{"axis_id": f"thin_factory_bolt_{i:03d}", "receiver": rows[0]["receiver"],
                                "attachments": rows} for i, rows in enumerate(grouped.values(), 1)]
    return raw, changed, context, source, installed


def metal_with_washers(axes: list) -> tuple[list, list]:
    metal, changes = [], []
    for axis in axes:
        before, after = axis["before_plate_mm"], axis["after_plate_mm"]
        h = axis["hardware_scenario"]
        parts = dict(occupied.local_hardware(axis))
        small_head = any(a["angle_id"].startswith("B103ZN_") and a["flange"] == "post"
                         for a in axis["attachments"])
        small_nut = any(a["duty_id"].startswith("clip_timber_header_outer_") and a["flange"] == "beam"
                        for a in axis["attachments"])
        for role, selected in (("head_washer", small_head), ("nut_washer", small_nut)):
            if not selected:
                continue
            old_t, new_t = h["washer_thickness_mm"], SAE_WASHER["thickness_mm"]
            station = -before - new_t if role == "head_washer" else axis["grip_mm"] + after
            point = cq.Vector(0, 0, station)
            pieces = cq.Solid.makeCylinder(SAE_WASHER["od_mm"] / 2, new_t, point).cut(
                cq.Solid.makeCylinder(SAE_WASHER["id_mm"] / 2, new_t, point))
            parts[role] = pieces
            if role == "head_washer":
                shift = old_t - new_t
                parts["head"] = parts["head"].translate((0, 0, shift))
                parts["shaft"] = parts["shaft"].translate((0, 0, shift))
                axis["tip_projection_beyond_nut_mm"] += shift
            else:
                parts["nut"] = parts["nut"].translate((0, 0, new_t - old_t))
                axis["tip_projection_beyond_nut_mm"] += old_t - new_t
            changes.append({"axis_id": axis["id"], "role": role, **SAE_WASHER,
                            "resistance_and_hole_bridging_checked": False})
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        metal.extend((axis["id"], role, shape.moved(plane.location)) for role, shape in parts.items())
    return metal, changes


def pair_hits(first: list, second: list) -> list[dict]:
    return [{"first": name, "first_role": role, "second": other_name,
             "second_role": other_role, "intersection_mm3": round(volume, 6)}
            for name, role, body in first for other_name, other_role, other in second
            if (volume := shared.overlaps(body, other)) > .01]


def grain_ray_ends(raw: dict, axes: list) -> list[dict]:
    """Mid-shaft grain-ray diagnostic; oblique NDS end classification is open."""
    rows = []
    for axis in axes:
        if not axis["attachments"]:
            continue
        member = axis["receivers"][0]
        grain = (cq.Vector(1, 0, 0) if member.startswith("base_rail_") or member == "base_header"
                 else cq.Vector(0, 0, 1) if member.startswith("base_post_") else thin.T)
        midpoint = axis["point"] + axis["direction"].multiply(axis["grip_mm"] / 2)
        low, high = geometry_tools.line_span(raw[member], midpoint, grain)
        end = min(-low, high)
        rows.append({"axis_id": axis["id"], "member": member,
                     "grain_axis_xyz": shared.xyz(grain), "midpoint_xyz_mm": shared.xyz(midpoint),
                     "grain_ray_end_distances_mm": [-low, high],
                     "minimum_grain_ray_end_mm": end,
                     "conditional_softwood_tension_3p5d_mm": 3.5 * axis["diameter_mm"],
                     "conditional_softwood_tension_7d_mm": 7 * axis["diameter_mm"],
                     "at_least_3p5d_on_this_ray": end >= 3.5 * axis["diameter_mm"] - 1e-6,
                     "formal_end_distance_classified_or_force_applicable": False})
    return rows


def annular_backing(outer: float, inner: float, point: cq.Vector, inward: cq.Vector,
                    targets: list) -> float:
    skin = cq.Solid.makeCylinder(outer / 2, .05, point, inward).cut(
        cq.Solid.makeCylinder(inner / 2, .05, point, inward))
    return min(1., sum(shared.overlaps(skin, body) for body in targets) / skin.Volume())


def actual_washer_seats(axes: list, changes: list, wood: dict, angles: list) -> list[dict]:
    """Separate intentional opening bridging from missing outer backing."""
    by_change = {(r["axis_id"], r["role"]): r for r in changes}
    by_angle = {a.id: a.shape for a in angles}
    rows = []
    for axis in axes:
        h, p, d = axis["hardware_scenario"], axis["point"], axis["direction"]
        for role, plate, station, inward in (
            ("head_washer", axis["before_plate_mm"], -axis["before_plate_mm"], d),
            ("nut_washer", axis["after_plate_mm"], axis["grip_mm"] + axis["after_plate_mm"], -d),
        ):
            change = by_change.get((axis["id"], role))
            od = change["od_mm"] if change else h["washer_od_mm"]
            id_ = change["id_mm"] if change else h["washer_id_mm"]
            opening = screen.BORE if plate else axis["bore_diameter_mm"]
            targets = ([by_angle[a["angle_id"]] for a in axis["attachments"]]
                       if plate else [wood[n] for n in axis["receivers"]])
            point = p + d.multiply(station)
            rows.append({"axis_id": axis["id"], "role": role,
                         "support_material": "steel" if plate else "wood",
                         "od_mm": od, "id_mm": id_, "planned_support_opening_mm": opening,
                         "actual_annulus_backed_fraction": annular_backing(od, id_, point, inward, targets),
                         "annulus_outside_intentional_opening_backed_fraction": annular_backing(od, max(id_, opening), point, inward, targets),
                         "bridge_bending_and_bearing_resistance_checked": False})
    return rows


def evaluate(row_shift: float, bottom_extra_shift: float, wire_depth: float, revision: str) -> dict:
    raw, fitted, context, source, raw_installed = row_layout(row_shift, bottom_extra_shift)
    axes = occupied.prepare_axes(raw, source, context["inventory"], occupied.DEFAULT_SETTINGS)
    metal, small_washers = metal_with_washers(axes)
    end_rays = grain_ray_ends(raw, axes)
    angles = [a for a, _ in fitted]
    services, authentication, wire_rows, cutters = routed_services(wire_depth)
    pre_bore, cut_rows = dict(raw), []
    for name, operation, kind, cutter in variant(KERF_RIGHT).additional_machining_cutters():
        if name.endswith("_right"):
            cutter = cutter.translate((-3.175, 0, 0))
        before = pre_bore[name].Volume()
        pre_bore[name] = pre_bore[name].cut(cutter).clean()
        cut_rows.append({"receiver": name, "operation": operation, "kind": kind,
                         "removed_volume_mm3": before - pre_bore[name].Volume()})
    receivers = {n for n in raw if n.startswith(("base_", "lumber_leg_"))}
    pre_bore, service_cuts = service_tools.cut_services(pre_bore, receivers, cutters)
    installed = [screen.audit_pose(a, f, pre_bore, []) for a, f in fitted]
    finished = occupied.bore_wood(pre_bore, axes)
    washer_rows = actual_washer_seats(axes, small_washers, finished, angles)
    steel = metal + [(a.id, "angle", a.shape) for a in angles]
    pairs = geometry_tools.collision_pairs(steel)
    wood_hits = pair_hits(metal, [(n, "wood", body) for n, body in finished.items()])
    screw_rows = copy.deepcopy(json.loads(occupied.RAW_REPORT.read_text())["panel_screw_backing"]["axes"])
    support, screw_parts = [], []
    for row in screw_rows:
        if row["receiver"].startswith("base_rail_bottom"):
            point = cq.Vector(*row["origin_xyz_mm"]) + thin.T.multiply(bottom_extra_shift)
            row["origin_xyz_mm"] = shared.xyz(point)
        point, direction = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
        body = cq.Solid.makeCylinder(2.5, 44.45, point + direction.multiply(19.05), direction)
        support.append({"axis_id": row["axis_id"], "fraction": min(1., shared.overlaps(body, finished[row["receiver"]]) / body.Volume())})
        screw_parts.extend((row["axis_id"], role, shape) for role, shape in occupied.screw_shapes(row))
    screw_hits = pair_hits(screw_parts, steel)
    service_wood, service_metal = service_tools.service_hits(services, finished, metal, angles)
    holes = [h for r in installed for h in r["holes"]]
    flange_seats = [s for r in installed for s in r["seats"]]
    return {
        "schema": "thin_bolted_layout_revision/v1", "candidate": source["candidate"],
        "revision": revision, "disposition": "REVISE_UNQUALIFIED_PROPOSAL",
        "question": "Can separated header rows, selected SAE washers and shallow open wire channels resolve the occupied-fit failures without enlarging timber?",
        "inputs": {"header_row_shift_mm": row_shift, "bottom_extra_shift_mm": bottom_extra_shift,
                   "wire_depth_mm": wire_depth, "old_centered_service_passages_cut": False,
                   "new_machining_physical_release": False},
        "source_sha256": {
            **shared.SOURCE_PINS, **source["additional_source_sha256"],
            str(occupied.RAW_REPORT.relative_to(shared.ROOT)): shared.sha(occupied.RAW_REPORT),
            **{str(Path(module.__file__).relative_to(shared.ROOT)): shared.sha(Path(module.__file__))
               for module in (occupied, shared, geometry_tools, service_tools, retained_services,
                              no_shoes_frame, round_structural_wiring)},
            str(Path(__file__).relative_to(shared.ROOT)): shared.sha(Path(__file__)),
        },
        "counts": {
            "fittings": len(angles), "physical_bolt_axes": len(axes), "new_axes": len(source["physical_axes"]),
            "steel_roles": len(metal), "small_washers": len(small_washers), "hillman_axes": len(screw_rows),
            "full_post_service_bore_attachments": sum(h["raw_full_bore_fraction"] >= .99999 for h in holes),
            "full_post_service_rectangular_flange_seats": sum(s["ideal_rectangular_seat_fraction"] >= .99999 for s in flange_seats),
            "steel_steel_intersections": len(pairs), "steel_finished_wood_intersections": len(wood_hits),
            "steel_screw_intersections": len(screw_hits),
            "full_screw_receiver_bodies": sum(s["fraction"] >= .99999 for s in support),
            "washers_with_full_backing_outside_intentional_opening": sum(w["annulus_outside_intentional_opening_backed_fraction"] >= .99999 for w in washer_rows),
            "service_wood_intersections": len(service_wood), "service_steel_intersections": len(service_metal),
            "routed_wires": len(wire_rows), "over_approximate_wire_budgets": sum(not w["within_approximate_budget"] for w in wire_rows),
            "split_frame_members": sum(len(finished[n].Solids()) != 1 for n in receivers),
            "grain_rays_shorter_than_conditional_3p5d": sum(not e["at_least_3p5d_on_this_ray"] for e in end_rays),
        },
        "raw_fittings": raw_installed, "post_service_fittings": installed,
        "installed_axes": [{k: shared.xyz(v) if isinstance(v, cq.Vector) else v for k, v in a.items()} for a in axes],
        "small_washer_changes": small_washers, "screw_axes": screw_rows, "screw_support": support,
        "grain_ray_end_diagnostic": end_rays,
        "washer_seats": washer_rows,
        "wire_proposals": wire_rows, "recess_cuts": cut_rows, "service_cuts": service_cuts,
        "steel_steel_intersections": pairs, "steel_wood_intersections": wood_hits,
        "steel_screw_intersections": screw_hits,
        "service_clearance": {"original_service_authentication": authentication,
                              "modified_wire_bodies": len(wire_rows),
                              "wood_intersections": service_wood, "steel_intersections": service_metal},
        "release": shared.RELEASE, "mechanics_ready": False,
        "limits": [
            "Factory bend datums, actual fitting identity/dimensions and tolerances remain conditional.",
            "This proposes shallow front-open channels in fresh hidden timber; it does not alter the selected/reviewed candidates or approve any cut.",
            "Wire endpoints and LED/T-nut bodies remain source-bound; cable slack, real bend radii, feeding/lifting access and panel-removal sequence are unverified.",
            "Small SAE washers need bearing, bending and normal hole-bridging calculations; their outside diameter alone establishes no capacity.",
            "Actual hardware/shanks, timber end/edge classification, installation and disassembly remain open.",
            "No fresh whole-frame or joint/member/panel strength calculation, native solve or climbing release is included.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header-row-shift-mm", type=float, default=18.)
    parser.add_argument("--bottom-extra-shift-mm", type=float, default=0.)
    parser.add_argument("--wire-depth-mm", type=float, default=8.)
    parser.add_argument("--revision", default="thin-offset-header-rows-shallow-wires-v4")
    parser.add_argument("--out", type=Path, default=thin.PACKET / "mixed-offset-rows-shallow-wires-v4.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"preserve prior experiment: {args.out}")
    print("Checking separated rows, fourteen SAE washer proposals and shallow wire channels", flush=True)
    report = evaluate(args.header_row_shift_mm, args.bottom_extra_shift_mm, args.wire_depth_mm, args.revision)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": str(args.out), "counts": report["counts"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
