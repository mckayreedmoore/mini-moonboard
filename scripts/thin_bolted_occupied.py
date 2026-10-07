"""Inspect complete provisional hardware on the mixed thin-frame comparison.

This uses retained service passages or an explicitly requested clearance-void
scenario. Shaft/head/nut/washer envelopes are not purchased-part, threading,
installation, net-section or strength qualification. No native solve is run.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import platform
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

RAW_REPORT = thin.PACKET / "mixed-far-hole-raw-v2.json"
DEFAULT_SETTINGS = {
    "revision": "thin-mixed-retained-service-occupied-v3",
    "service_clearance_envelopes": False,
    "reverse_axis_ids": [],
    "service_void_scenario": {
        "wire_radius_mm": 6.35,
        "light_added_radius_mm": 3.0,
        "tnut_radius_mm": 15.875,
        "axial_margin_mm": 3.0,
    },
    "new_half_inch_hardware": {
        "washer_od_mm": 35.052,
        "washer_id_mm": 14.2875,
        "washer_thickness_mm": 3.3528,
        "head_height_mm": 9.0,
        "nut_height_mm": 11.5316,
        "hex_across_flats_mm": 22.225,
        "available_nominal_lengths_mm": [76.2, 127.0],
        "minimum_tip_threads": 2,
        "threads_per_inch": 13,
    },
}


def prepare_axes(wood: dict, raw_report: dict, inventory: dict, settings: dict) -> list[dict]:
    """Use actual raw line crossings and count shared holes exactly once."""
    axes = []
    reverse = set(settings["reverse_axis_ids"])
    for row in raw_report["physical_axes"]:
        attachments = row["attachments"]
        first = attachments[0]
        point = cq.Vector(*first["entry_xyz_mm"])
        direction = cq.Vector(*first["axis_xyz"])
        near, far = geometry_tools.line_span(wood[row["receiver"]], point, direction)
        point += direction.multiply(near)
        grip = far - near
        if row["axis_id"] in reverse:
            point += direction.multiply(grip)
            direction *= -1
        before = after = 0.0
        for attachment in attachments:
            source_point = cq.Vector(*attachment["entry_xyz_mm"])
            distance = (source_point - point).dot(direction)
            fitting = raw_report["fittings"][attachment["angle_id"].split("_", 1)[0]]
            thickness = fitting["thickness_mm"]
            if abs(distance) < 1e-5:
                before = max(before, thickness)
            elif abs(distance - grip) < 1e-5:
                after = max(after, thickness)
            else:
                raise ValueError(f"flange does not lie at a raw wood face: {row['axis_id']}")
        axes.append({
            "id": row["axis_id"], "point": point, "direction": direction,
            "grip_mm": grip, "diameter_mm": 12.7, "bore_diameter_mm": screen.BORE,
            "receivers": [row["receiver"]], "attachments": attachments,
            "before_plate_mm": before, "after_plate_mm": after,
            "hardware_scenario": copy.deepcopy(settings["new_half_inch_hardware"]),
            "source": "new_factory_fitting_axis", "delivered_stack_verified": False,
        })
    source_frame = variant(KERF_RIGHT)
    source_connections = {c.name: c for c in source_frame.connections() if c.kind == "bolt"}
    for row in inventory["starting_frame_bolts"]:
        dims = source_frame.bolt_dimensions(source_connections[row["axis_id"]])
        direction = cq.Vector(*row["axis_global_xyz"])
        point = cq.Vector(*row["origin_global_xyz_mm"]) + direction.multiply(dims["washer_thickness_mm"])
        diameter = row["source_occupied_diameter_mm"]
        axes.append({
            "id": row["axis_id"], "point": point, "direction": direction,
            "grip_mm": row["source_grip_mm"], "diameter_mm": diameter,
            "bore_diameter_mm": dims["hole_diameter_mm"], "receivers": row["members"],
            "attachments": [], "before_plate_mm": 0.0, "after_plate_mm": 0.0,
            "hardware_scenario": {
                "washer_od_mm": dims["washer_od_mm"], "washer_id_mm": dims["hole_diameter_mm"],
                "washer_thickness_mm": dims["washer_thickness_mm"],
                "head_height_mm": 9.0 if diameter == 12.7 else 6.0,
                "nut_height_mm": dims["nut_height_mm"],
                "hex_across_flats_mm": 22.225 if diameter == 12.7 else 14.2875,
                "available_nominal_lengths_mm": [dims["length_mm"]],
                "minimum_tip_threads": 2,
                "threads_per_inch": 13 if diameter == 12.7 else 16,
            },
            "source": "original_starting_frame_axis", "delivered_stack_verified": False,
        })
    if len(axes) != 70 or len({a["id"] for a in axes}) != 70:
        raise ValueError("expect 58 new physical axes and twelve starting axes")
    unknown = reverse - {a["id"] for a in axes}
    if unknown:
        raise ValueError(f"unknown reverse axes: {sorted(unknown)}")
    return axes


def local_hardware(axis: dict) -> list[tuple[str, cq.Shape]]:
    h = axis["hardware_scenario"]
    washer, before, after = h["washer_thickness_mm"], axis["before_plate_mm"], axis["after_plate_mm"]
    start = -before - washer
    nut_start = axis["grip_mm"] + after + washer
    minimum_length = nut_start - start + h["nut_height_mm"] + h["minimum_tip_threads"] * 25.4 / h["threads_per_inch"]
    length = next((v for v in h["available_nominal_lengths_mm"] if v >= minimum_length - 1e-6), None)
    if length is None:
        raise ValueError(f"no planning length meets tip allowance: {axis['id']}")
    axis["nominal_under_head_length_mm"] = length
    axis["tip_projection_beyond_nut_mm"] = length + start - nut_start - h["nut_height_mm"]
    axis["nominal_thread_window_qualified"] = False
    radius = h["hex_across_flats_mm"] / math.sqrt(3)

    def cylinder(r: float, z: float, height: float) -> cq.Shape:
        return cq.Solid.makeCylinder(r, height, cq.Vector(0, 0, z))

    def annulus(z: float) -> cq.Shape:
        return cylinder(h["washer_od_mm"] / 2, z, washer).cut(
            cylinder(h["washer_id_mm"] / 2, z, washer))

    def hexagon(z: float, height: float) -> cq.Shape:
        return cq.Workplane("XY").polygon(6, 2 * radius).extrude(height).val().translate((0, 0, z))

    return [
        ("shaft", cylinder(axis["diameter_mm"] / 2, start, length)),
        ("head", hexagon(start - h["head_height_mm"], h["head_height_mm"])),
        ("head_washer", annulus(start)),
        ("nut_washer", annulus(axis["grip_mm"] + after)),
        ("nut", hexagon(nut_start, h["nut_height_mm"]).cut(
            cylinder(axis["diameter_mm"] / 2, nut_start, h["nut_height_mm"]))),
    ]


def hardware(axes: list[dict]) -> list[tuple[str, str, cq.Shape]]:
    result = []
    for axis in axes:
        plane = cq.Plane(origin=axis["point"], normal=axis["direction"])
        result.extend((axis["id"], role, shape.moved(plane.location))
                      for role, shape in local_hardware(axis))
    return result


def service_cutters(parts: list, parent: dict, settings: dict) -> list:
    """Conditional voids at retained endpoints; no inherited dogleg proposal."""
    dims, cutters = settings["service_void_scenario"], []
    for record in round_structural_wiring.segments():
        route = record["route_local_mm"]
        placement = list(no_shoes_frame.SHIFT.toTuple())
        change = parent["revision_report"]["wire_endpoint_revisions"].get(record["name"])
        if change:
            route, placement = change["route_local_mm"], change["source_placement_xyz_mm"]
        cutter, _ = service_tools.sweep(route, dims["wire_radius_mm"], placement)
        if record["string_connector_envelope"]:
            first, last = [round_structural_wiring.b.point(*p) for p in route[1:3]]
            direction, midpoint = (last - first).normalized(), (first + last) * .5
            length = round_structural_wiring.GEOMETRY["connector_length"] + 6
            connector = cq.Solid.makeCylinder(12.7, length, midpoint - direction.multiply(length / 2), direction)
            cutter = cutter.fuse(connector.translate(cq.Vector(*placement))).clean()
        cutters.append((record["name"], "wire", cutter))
    for name, kind, shape in parts:
        if kind == "wire":
            continue
        if kind == "light":
            direction = screen.N
            radius = round_structural_wiring.MEASURED_MAXIMUM_DIAMETER_MM / 2 + dims["light_added_radius_mm"]
        else:
            direction = screen.N if name.startswith("hold_tnut_main_") else cq.Vector(0, -1, 0)
            radius = dims["tnut_radius_mm"]
        lo, hi = shared.projected_extent(shape, direction)
        point, margin = shape.Center(), dims["axial_margin_mm"]
        start = point + direction.multiply(lo - point.dot(direction) - margin)
        cutters.append((name, kind, cq.Solid.makeCylinder(radius, hi - lo + 2 * margin, start, direction)))
    return cutters


def pre_bore_wood(raw: dict, settings: dict, services: list) -> tuple[dict, list[dict]]:
    """Preserve rear recess; service voids stay explicit planning geometry."""
    frame, wood, cuts = variant(KERF_RIGHT), dict(raw), []
    for member, name, kind, cutter in frame.additional_machining_cutters():
        if member.endswith("_right"):
            cutter = cutter.translate((-3.175, 0, 0))
        before = wood[member].Volume()
        wood[member] = wood[member].cut(cutter).clean()
        cuts.append({"receiver": member, "operation": name, "kind": kind,
                     "removed_volume_mm3": before - wood[member].Volume()})
    for member, name, cutter in frame.service_cutters():
        before = wood[member].Volume()
        wood[member] = wood[member].cut(cutter).clean()
        cuts.append({"receiver": member, "operation": name, "kind": "retained_service_passage",
                     "removed_volume_mm3": before - wood[member].Volume()})
    if settings["service_clearance_envelopes"]:
        _, _, parent = shared.load_sources()
        receivers = {n for n in raw if n.startswith(("base_", "lumber_leg_"))}
        wood, added = service_tools.cut_services(wood, receivers, service_cutters(services, parent, settings))
        cuts.extend({**row, "operation": row["service"], "conditional_service_void": True}
                    for row in added)
    return wood, cuts


def washer_seats(axes: list, wood: dict, angles: list) -> list[dict]:
    """Check annular contact at the actual outer plate or wood face."""
    steel = {a.id: a.shape for a in angles}
    rows = []
    for axis in axes:
        h, d, p = axis["hardware_scenario"], axis["direction"], axis["point"]
        for side, plate, station, inward in (
            ("head", axis["before_plate_mm"], -axis["before_plate_mm"], d),
            ("nut", axis["after_plate_mm"], axis["grip_mm"] + axis["after_plate_mm"], -d),
        ):
            point = p + d.multiply(station)
            skin = cq.Solid.makeCylinder(h["washer_od_mm"] / 2, .05, point, inward).cut(
                cq.Solid.makeCylinder(h["washer_id_mm"] / 2, .05, point, inward))
            targets = ([steel[a["angle_id"]] for a in axis["attachments"]]
                       if plate else [wood[n] for n in axis["receivers"]])
            fraction = min(1., sum(shared.overlaps(skin, target) for target in targets) / skin.Volume())
            rows.append({"axis_id": axis["id"], "side": side,
                         "support_material": "steel" if plate else "wood",
                         "annular_seat_fraction": round(fraction, 6),
                         "bearing_or_bending_capacity_checked": False})
    return rows


def screw_shapes(row: dict) -> list[tuple[str, cq.Shape]]:
    point, direction = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
    return [
        ("head", cq.Solid.makeCone(4.5, 2.5, 3.0, point, direction)),
        ("body", cq.Solid.makeCylinder(2.5, 60.5, point + direction.multiply(3), direction)),
    ]


def bore_wood(wood: dict, axes: list[dict]) -> dict:
    result = dict(wood)
    for axis in axes:
        point, direction = axis["point"], axis["direction"]
        cutter = cq.Solid.makeCylinder(axis["bore_diameter_mm"] / 2, axis["grip_mm"] + 2,
                                      point - direction, direction)
        for member in axis["receivers"]:
            result[member] = result[member].cut(cutter).clean()
    return result


def audit(settings: dict) -> dict:
    raw_report = json.loads(RAW_REPORT.read_text())
    for name, expected in {**raw_report["source_pins"], **raw_report["additional_source_sha256"]}.items():
        if shared.sha(shared.ROOT / name) != expected:
            raise ValueError(f"raw comparison source changed: {name}")
    raw, fitted, context = thin.geometry()
    angles = [a for a, _ in fitted]
    services, authentication = retained_services.service_parts()
    pre_bore, cuts = pre_bore_wood(raw, settings, services)
    # Service subtraction must not shorten a stack or erase its physical axis.
    # Report lost receiving wood separately in the post-service audit below.
    axes = prepare_axes(raw, raw_report, context["inventory"], settings)
    metal = hardware(axes)
    installed = [screen.audit_pose(a, f, pre_bore, []) for a, f in fitted]
    finished = bore_wood(pre_bore, axes)
    seats_of_washers = washer_seats(axes, finished, angles)
    steel = metal + [(a.id, "angle", a.shape) for a in angles]
    pairs = geometry_tools.collision_pairs(steel)
    unintended = []
    for axis_id, role, shape in metal:
        for member, body in finished.items():
            volume = shared.overlaps(shape, body)
            if volume > .01:
                unintended.append({"axis_id": axis_id, "role": role, "member": member,
                                   "intersection_mm3": round(volume, 6)})
    screws = raw_report["panel_screw_backing"]["axes"]
    screw_hits, screw_support = [], []
    for row in screws:
        point, direction = cq.Vector(*row["origin_xyz_mm"]), cq.Vector(*row["direction_xyz"])
        probe = cq.Solid.makeCylinder(2.5, 44.45, point + direction.multiply(19.05), direction)
        fraction = min(1.0, shared.overlaps(probe, finished[row["receiver"]]) / probe.Volume())
        screw_support.append({"axis_id": row["axis_id"], "receiver": row["receiver"],
                              "post_other_bore_receiver_fraction": round(fraction, 6)})
        for screw_role, shape in screw_shapes(row):
            for identity, role, other in steel:
                if (volume := shared.overlaps(shape, other)) > .01:
                    screw_hits.append({"screw_axis_id": row["axis_id"], "screw_role": screw_role,
                                       "obstacle": identity, "obstacle_role": role,
                                       "intersection_mm3": round(volume, 6)})
    service_wood, service_metal = service_tools.service_hits(services, finished, metal, angles)
    receivers = [n for n in raw if n.startswith(("base_", "lumber_leg_"))]
    holes = [h for record in installed for h in record["holes"]]
    seats = [s for record in installed for s in record["seats"]]
    serialized_axes = [{k: shared.xyz(v) if isinstance(v, cq.Vector) else v
                        for k, v in a.items()} for a in axes]
    return {
        "schema": "thin_bolted_occupied_comparison/v1",
        "candidate": raw_report["candidate"], "revision": settings["revision"],
        "disposition": "REVISE_UNQUALIFIED_OCCUPIED_GEOMETRY",
        "question": "Do the mixed thin-member fittings clear complete nominal hardware, retained passages and services?",
        "settings": settings, "release": shared.RELEASE,
        "source_sha256": {
            **shared.SOURCE_PINS,
            **raw_report["additional_source_sha256"],
            str(RAW_REPORT.relative_to(shared.ROOT)): shared.sha(RAW_REPORT),
            **{str(Path(module.__file__).relative_to(shared.ROOT)): shared.sha(Path(module.__file__))
               for module in (shared, geometry_tools, service_tools, retained_services,
                              no_shoes_frame, round_structural_wiring)},
            str(Path(__file__).relative_to(shared.ROOT)): shared.sha(Path(__file__)),
        },
        "runtime": {"python": platform.python_version(), "cadquery": cq.__version__},
        "counts": {
            "physical_structural_bolt_axes": len(axes), "metal_roles": len(metal),
            "factory_angles": len(angles), "hillman_axes": len(screws),
            "full_pre_bore_receiver_attachments": sum(h["raw_full_bore_fraction"] >= .99999 for h in holes),
            "full_pre_bore_rectangular_flange_seats": sum(s["ideal_rectangular_seat_fraction"] >= .99999 for s in seats),
            "full_annular_washer_seats": sum(s["annular_seat_fraction"] >= .99999 for s in seats_of_washers),
            "steel_steel_intersections": len(pairs), "metal_finished_wood_intersections": len(unintended),
            "hardware_screw_intersections": len(screw_hits),
            "full_finished_screw_receiver_bodies": sum(s["post_other_bore_receiver_fraction"] >= .99999 for s in screw_support),
            "retained_service_wood_intersections": len(service_wood),
            "retained_service_steel_intersections": len(service_metal),
            "frame_wood_split_into_separate_solids": sum(len(finished[n].Solids()) != 1 for n in receivers),
        },
        "installed_axes": serialized_axes, "post_recess_and_service_fittings": installed,
        "wood_cuts": cuts, "steel_steel_intersections": pairs,
        "metal_finished_wood_intersections": unintended,
        "hardware_screw_intersections": screw_hits, "screw_receiver_support": screw_support,
        "washer_seats": seats_of_washers,
        "retained_service_clearance": {**authentication, "wood_intersections": service_wood,
                                       "steel_intersections": service_metal},
        "finished_frame_members": [{"member": n, "raw_volume_mm3": raw[n].Volume(),
                                    "post_passage_and_bolt_bore_volume_mm3": finished[n].Volume()}
                                   for n in receivers],
        "mechanics_ready": False, "installed_access_checked": False,
        "limits": [
            "Exact fitting bend/hole datums, thickness and tolerances remain conditional as recorded in the raw comparison.",
            "Heads/nuts are regular hexagonal planning envelopes. Actual SKUs, threads, tolerances, washer strength and seating still need their own check.",
            "New nominal bolt lengths are planning selections among 3 and 5 inches, not delivered smooth-shank qualification or a purchase list.",
            "The original twelve frame axes and nominal lengths are preserved; no resistance or installation pass is inherited.",
            "Hillman body diameter 5 mm and head height 3 mm are unverified scenarios; only nominal length and owner 9 mm head are known.",
            ("Retained service passages exclude new voids needed for G2 and moved rails; residual intersections are explicit failures."
             if not settings["service_clearance_envelopes"] else
             "Additional oversized service voids are explicit conditional envelopes, not verified drilling/routing or extraction corridors; their cut effects need resistance checks."),
            "Screw receivers are checked before their own occupancy subtraction; wood-thread engagement, pilot/countersink cuts and screw installation resistance remain separate.",
            "No bolt/washer/head extraction corridor, tool rotation, panel-edge load path, whole-frame stiffness or strength has been established.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--out", type=Path, default=thin.PACKET / "mixed-retained-service-occupied-v3.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"preserve prior input/result: {args.out}")
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    if args.config:
        settings.update(json.loads(args.config.read_text()))
    print("Checking retained machining and complete thin-frame metal", flush=True)
    report = audit(settings)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": str(args.out), "counts": report["counts"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
