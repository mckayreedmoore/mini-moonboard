"""Check conditional tool/removal envelopes and takeoff on frozen thin v4 CAD.

Uses the parent's exact BREP cache; this never rebuilds or changes the model.
Physical tools, delivered thread windows and full installed cost stay conditional.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
from collections import Counter
from decimal import Decimal
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from scripts import hl35_candidate as shared
from scripts import thin_bolted_model as model

PACKET = model.LAYOUT.parent
STOCK = shared.ROOT / "docs/floor-flush-construction-kerf-right/stock.csv"
GEOMETRY = PACKET / "native-geometry-v4.json"
OUT = PACKET / "access-takeoff-v4.json"
TOOL = {
    "status": "conditional maximum envelopes; no measured or selected tools",
    "half_inch": {"socket_od_mm": 32., "socket_length_mm": 80., "minimum_well_mm": 48.},
    "three_eighth_inch": {"socket_od_mm": 22., "socket_length_mm": 65., "minimum_well_mm": 36.},
    "approach_travel_mm": 100., "extension_od_mm": 20., "extension_length_mm": 150.,
    "remote_drive_head_od_mm": 50., "remote_drive_head_thickness_mm": 20.,
    "handle_outer_radius_mm": 215., "handle_thickness_mm": 12.,
    "handle_sector_deg": 40., "indexed_working_stroke_deg": 20.,
    "socket_to_seat_axial_gap_mm": .2,
    "note": "Remote sector contains a 20-degree stroke plus side-width allowance; torque, ratchet tooth pitch, grip and hand room are unqualified.",
    "manufacturer_research": [
        "https://www.tekton.com/1-2-inch-drive-x-7-8-inch-deep-6-point-socket-shd23022",
        "https://images.tekton.com/assets/SHD23022_spec.jpg",
        "https://www.tekton.com/3-8-inch-drive-x-9-16-inch-deep-6-point-socket-shd13014",
        "https://images.tekton.com/assets/SHD13014_spec.jpg",
    ],
    "research_limit": "Manufacturer pages identify suitable drive sizes, but their dimensional graphics were not decoded. The numerical envelopes above are explicit conditions, not asserted TEKTON dimensions.",
}


def axial_sweep(shape: cq.Shape, outward: cq.Vector, travel_mm: float) -> cq.Shape:
    """Exact continuous translation union for a constant-section axial solid.

    Includes the original pose. Validates the extrusion assumption, rejecting
    cones and other nonprismatic parts instead of silently using sampled poses.
    """
    if travel_mm < 0 or abs(outward.Length - 1.) > 1e-8:
        raise ValueError("sweep needs nonnegative travel and a unit direction")
    low, high = shared.projected_extent(shape, outward)
    faces = [f for f in shape.Faces() if f.geomType() == "PLANE"
             and abs(abs(f.normalAt().dot(outward)) - 1.) < 1e-7
             and abs(f.Center().dot(outward) - low) < 1e-6]
    if not faces:
        raise ValueError("no axial starting face")
    face = max(faces, key=lambda f: f.Area())
    if abs(face.Area() * (high - low) - shape.Volume()) > max(.01, 1e-7 * shape.Volume()):
        raise ValueError("constant-section sweep required")
    return cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(),
                                 outward.multiply(high - low + travel_mm))


def hits(shape: cq.Shape, obstacles: list[tuple[str, str, cq.Shape]]) -> list[dict]:
    return [{"obstacle": name, "role": role, "intersection_mm3": round(volume, 6)}
            for name, role, other in obstacles
            if (volume := shared.overlaps(shape, other)) > .01]


def convex_linear_sweep(shape: cq.Shape, direction: cq.Vector, travel: float) -> cq.Shape:
    """Continuous conservative Minkowski corridor for polyhedral stock.

    Convexification fills concave cuts and can create false blockers. It never
    asserts a clear path from endpoint-only sampling or omits curved extrema.
    """
    if travel < 0 or abs(direction.Length - 1.) > 1e-8:
        raise ValueError("sweep needs nonnegative travel and a unit direction")
    if any(e.geomType() != "LINE" for e in shape.Edges()):
        raise ValueError("polyhedral stock required")
    points = np.array([v.Center().toTuple() for v in shape.Vertices()])
    points = np.vstack((points, points + np.array(direction.toTuple()) * travel))
    hull = ConvexHull(points)
    faces = []
    for indices, equation in zip(hull.simplices, hull.equations):
        triangle = points[indices]
        if np.dot(np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0]), equation[:3]) < 0:
            triangle = triangle[::-1]
        wire = cq.Wire.makePolygon([cq.Vector(*p) for p in triangle], close=True)
        faces.append(cq.Face.makeFromWires(wire))
    result = cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    if not result.isValid() or shape.cut(result).Volume() > .01:
        raise ValueError("convex corridor failed containment")
    return result


def release_front(frozen: dict, cache: dict, shapes: list) -> dict:
    """Check nominal panel/retained-body release before exposing the frame."""
    originals = {name: body for name, _, body in shapes}
    obstacles = [(name, role, body) for name, role, body in shapes]
    screws = []
    for row in frozen["screw_axes"]:
        outward = -cq.Vector(*row["direction_xyz"])
        point = cq.Vector(*row["origin_xyz_mm"]) + outward.multiply(.2)
        body = cq.Solid.makeCylinder(5., 150., point, outward)
        blocked = hits(body, [r for r in obstacles if r[0] != "fastener_" + row["axis_id"]])
        screws.append({"axis_id": row["axis_id"], "conditional_front_driver_od_mm": 10.,
                       "axial_approach_length_mm": 150., "hits": blocked})
    tnut_owner = {r["name"]: r["panel"] for r in model.tnuts.datums(model.no_shoes_frame)}
    light_owner = {}
    for label, (x, slope) in model.panel_grid_v2.main_led_datums().items():
        light_owner["light_" + label] = f'main_{"lower" if slope < model.no_shoes_frame.b.HALF else "upper"}_{"left" if x < model.no_shoes_frame.b.HALF else "right"}'
    owners = {**tnut_owner, **light_owner}
    rows, removed = [], set()
    outlines = {r["member"]: cq.importers.importBrep(str(shared.ROOT / r["path"])).val()
                for r in cache["panel_outline_parts"]}
    order = ["main_upper_left", "main_upper_right", "main_lower_left", "main_lower_right", "kicker_left", "kicker_right"]
    for name in order:
        outward = -cq.Vector(*next(r["direction_xyz"] for r in frozen["screw_axes"] if r["panel"] == name))
        # Release the nominal lower/kicker miter before pulling normal to the face.
        pre_shift = model.revision.thin.T.multiply(.5) if name.startswith("main_lower_") else cq.Vector()
        moving = {name, *[n for n, owner in owners.items() if owner == name]}
        stationary = [r for r in obstacles if r[0] not in moving | removed
                      and r[1] not in {"screw", "wire"}]
        panel_corridor = (axial_sweep(outlines[name].translate(pre_shift), outward, 100.) if name.startswith("main_")
                          else convex_linear_sweep(outlines[name], outward, 100.))
        blockers = [{"moving": name, **r} for r in hits(panel_corridor, stationary)]
        if pre_shift.Length:
            corridor = convex_linear_sweep(outlines[name], pre_shift.normalized(), pre_shift.Length)
            blockers.extend({"moving": name, "phase": "upslope_seam_release", **r} for r in hits(corridor, stationary))
        for service in moving - {name}:
            body = originals[service]
            if service.startswith("light_"):
                corridor = axial_sweep(body.translate(pre_shift), outward, 100.)
            else:
                low, high = shared.projected_extent(body, outward)
                center = body.Center()
                point = center + outward.multiply(low - center.dot(outward)) + pre_shift
                corridor = cq.Solid.makeCylinder(model.tnuts.FLANGE_DIAMETER_MM / 2,
                                                 high - low + 100., point, outward)
            blockers.extend({"moving": service, **r} for r in hits(corridor, stationary))
            if pre_shift.Length:
                low, high = shared.projected_extent(body, outward)
                center = body.Center()
                point = center + outward.multiply(low - center.dot(outward))
                radius = (model.revision.round_structural_wiring.MEASURED_MAXIMUM_DIAMETER_MM / 2
                          if service.startswith("light_") else model.tnuts.FLANGE_DIAMETER_MM / 2)
                corridor = cq.Solid.makeCylinder(radius + pre_shift.Length, high - low, point, outward)
                blockers.extend({"moving": service, "phase": "upslope_seam_release", **r} for r in hits(corridor, stationary))
        rows.append({"panel": name, "outward_xyz": shared.xyz(outward), "travel_mm": 100.,
                     "first_upslope_translation_xyz_mm": shared.xyz(pre_shift),
                     "retained_bodies_carried": len(moving) - 1, "hits": blockers})
        if not blockers:
            removed.update(moving)
    return {"conditional_front_driver_rows": screws, "front_driver_axes_clear": sum(not r["hits"] for r in screws),
            "panel_and_retained_body_lift_rows": rows, "nominal_panel_assemblies_lift_clear": sum(not r["hits"] for r in rows),
            "wire_lift": "V4 front_open_cutter and its known-answer test bound the 8mm-depth-to-front timber lifting corridor. Actual connectors must first disconnect from panel LEDs; the harness is then lifted forward and removed. No connector unplugging stroke, full harness body path, bend/slack or handling check is supplied.",
            "conditions": ["Unloaded frame separately supported during disassembly; no assembly stability claim", "Holds/hold bolts removed first", "All 66 Hillman screws removed with front access", "Power off and LED/harness connectors detached before panel lift", "Panels carry their source T-nuts/LED bodies", "Harness lifted from front-open channels before structural-tool checks"],
            "limits": "Lower panels first shift0.5mmupslope after upper panels are removed, releasing the nominal miter before their100mm normal pull. Main-panel normal corridors are exact constant-section sweeps; kicker outlines and the tiny upslope stock sweeps are conservatively convexified. Retained service bodies use exact cylinders or full-flange cylinders, enlarged by0.5mm for the initial sideways motion. Driver recess/bit and actual unplugging/handling/tolerances remain unverified; this is conditional nominal release geometry, not demonstrated physical demountability."}


def socket_envelopes(axis: dict, side: str, metal: dict) -> tuple[list, cq.Plane, float]:
    direction = cq.Vector(*axis["direction"])
    outward = -direction if side == "head" else direction
    body = metal[(axis["id"], side)]
    low, _ = shared.projected_extent(body, outward)
    center = body.Center()
    origin = center + outward.multiply(low - center.dot(outward) + TOOL["socket_to_seat_axial_gap_mm"])
    spec = TOOL["half_inch" if axis["diameter_mm"] == 12.7 else "three_eighth_inch"]
    length = spec["socket_length_mm"]
    socket = cq.Solid.makeCylinder(spec["socket_od_mm"] / 2,
                                  length + TOOL["approach_travel_mm"], origin, outward)
    extension = cq.Solid.makeCylinder(TOOL["extension_od_mm"] / 2,
                                     TOOL["extension_length_mm"], origin + outward.multiply(length), outward)
    drive_origin = origin + outward.multiply(length + TOOL["extension_length_mm"])
    drive = cq.Solid.makeCylinder(TOOL["remote_drive_head_od_mm"] / 2,
                                 TOOL["remote_drive_head_thickness_mm"], drive_origin, outward)
    plane = cq.Plane(origin=drive_origin, normal=outward)
    # Frozen half-inch AF is deliberately larger than ordinary 3/4-inch SKU AF.
    well_required = axis["hardware_scenario"]["nut_height_mm"] + axis["tip_projection_beyond_nut_mm"] if side == "nut" else axis["hardware_scenario"]["head_height_mm"]
    return [("socket_approach", socket), ("extension", extension), ("remote_drive", drive)], plane, spec["minimum_well_mm"] - well_required


def handle_sector(plane: cq.Plane, azimuth_deg: float) -> cq.Shape:
    """Conservative continuous indexed-stroke envelope at the remote drive."""
    sector = cq.Solid.makeCylinder(TOOL["handle_outer_radius_mm"], TOOL["handle_thickness_mm"],
                                  angleDegrees=TOOL["handle_sector_deg"])
    inner = cq.Solid.makeCylinder(TOOL["remote_drive_head_od_mm"] / 2,
                                 TOOL["handle_thickness_mm"])
    return sector.cut(inner).rotate((0, 0, 0), (0, 0, 1), azimuth_deg).moved(plane.location)


def short_wrench_access(frozen: dict, shapes: list) -> dict:
    """Alternative bounded pass-through ring tool and near-head indexed stroke.

    This is an explicit outline condition, not a claim that any wrench fits.
    An open-ended wrench can be checked against the same outer footprint if
    its jaw/side-entry path and usable engagement are supplied separately.
    """
    metal = {(name.removesuffix("_" + role), role): body for name, role, body in shapes if role in model.ROLES}
    obstacles = [r for r in shapes if r[1] not in {"panel", "screw", "wire", "light", "tnut"}]
    rows = []
    for axis in frozen["installed_axes"]:
        own = axis["id"]
        stationary = [r for r in obstacles if not r[0].startswith(own + "_")]
        for side in ("head", "nut"):
            outward = cq.Vector(*axis["direction"]) * (-1 if side == "head" else 1)
            body = metal[(own, side)]
            low, _ = shared.projected_extent(body, outward)
            center = body.Center()
            origin = center + outward.multiply(low - center.dot(outward) + .2)
            radius, depth = (15., 12.) if axis["diameter_mm"] == 12.7 else (11., 10.)
            approach = cq.Solid.makeCylinder(radius, depth + 30., origin, outward)
            blockers = hits(approach, stationary)
            chosen = None
            if not blockers:
                plane = cq.Plane(origin=origin, normal=outward)
                for azimuth in range(0, 360, 15):
                    sector = cq.Solid.makeCylinder(215., depth, angleDegrees=40.).cut(
                        cq.Solid.makeCylinder(radius, depth))
                    sector = sector.rotate((0, 0, 0), (0, 0, 1), azimuth).moved(plane.location)
                    if not hits(sector, stationary) and sector.BoundingBox().zmin >= -.01:
                        chosen = azimuth
                        break
            rows.append({"axis_id": own, "side": side, "ring_body_od_mm": 2 * radius,
                         "axial_body_depth_mm": depth, "axial_entry_travel_mm": 30.,
                         "body_hits": blockers, "handle_sector_azimuth_deg": chosen,
                         "conditional_access_clear": not blockers and chosen is not None})
    return {"profile": "Pass-through ring body, nominal 7/8in or9/16inAF, OD<=30/22mm, axialdepth<=12/10mm; 30mm axialapproach; toolhandle liesinside continuous40-degree radialsector r=ringradius..215mm at the same axialdepth for a20-degree indexed stroke.",
            "tool_rows": rows, "clear_tool_sides": sum(r["conditional_access_clear"] for r in rows),
            "limits": "The outline is a conditional maximum envelope. No actual tool, side-entry jaw, torque capacity, hand/grip clearance or delivered-tool tolerance is verified. A long bolt tip requires a pass-through opening; a shallow blind socket cannot replace it."}


def bolt_release_sequence(removal: list[dict], axes: list[dict]) -> dict:
    """Resolve already-tested corridors by deleting preceding bolt stacks.

    Deleting obstacles cannot create an intersection. Nonmetal blockers or a
    cycle remain unresolved; a collision is never waived by ordering alone.
    """
    identifiers = {a["id"] for a in axes}
    dependencies = {name: set() for name in identifiers}
    nonmetal = []
    for row in removal:
        for clash in row["hits"]:
            other = clash["obstacle"].removesuffix("_" + clash["role"])
            if clash["role"] in model.ROLES and other in identifiers:
                dependencies[row["axis_id"]].add(other)
            else:
                nonmetal.append({"axis_id": row["axis_id"], "operation": row["operation"], **clash})
    pending, removed, stages = set(identifiers), set(), []
    while pending:
        ready = sorted(name for name in pending if dependencies[name] <= removed
                       and not any(r["axis_id"] == name for r in nonmetal))
        if not ready:
            break
        stages.append(ready)
        removed.update(ready)
        pending.difference_update(ready)
    return {"dependency_rows": [{"axis_id": name, "remove_first": sorted(required)}
                                for name, required in sorted(dependencies.items()) if required],
            "parallel_clear_stages": stages, "bolt_stacks_released": len(removed),
            "unresolved_axes": sorted(pending), "nonmetal_blockers": nonmetal,
            "operation_order_per_axis": ["remove nut", "remove nut washer", "withdraw bolt shaft/head toward head", "remove head washer"],
            "continuous_role_corridors_checked": len(removal),
            "limits": "Uses complete continuous corridors with the other joints present. Only previously removed physical stacks are deleted. This resolves nominal separation, not loaded disassembly or support stability."}


def fitting_corridors(row: dict, actual: cq.Shape) -> tuple[cq.Vector, list[cq.Shape]]:
    name = row["angle_id"]
    spec = (model.revision.thin.screen.FITTINGS["B104ZN"] if name.startswith("B104ZN")
            else model.revision.thin.B103)
    plane = cq.Plane(origin=cq.Vector(*row["origin_xyz_mm"]),
                     xDir=cq.Vector(*row["u_xyz"]), normal=cq.Vector(*row["w_xyz"]))
    w, t = spec.width_mm, spec.thickness_mm
    boxes = [cq.Solid.makeBox(spec.u_leg_mm, t, w, cq.Vector(0, 0, -w / 2)).moved(plane.location),
             cq.Solid.makeBox(t, spec.v_leg_mm, w, cq.Vector(0, 0, -w / 2)).moved(plane.location)]
    if actual.cut(boxes[0].fuse(boxes[1])).Volume() > .01:
        raise ValueError("bracket envelope failed containment")
    direction = (cq.Vector(*row["u_xyz"]) + cq.Vector(*row["v_xyz"])).normalized()
    return direction, [convex_linear_sweep(box, direction, 100.) for box in boxes]


def member_release(frozen: dict, cache: dict, shapes: list) -> dict:
    """Bound bracket and timber separation after all bolt stacks are removed."""
    exact = {name: body for name, _, body in shapes}
    stationary = [r for r in shapes if r[1] in {"timber", "bracket"}]
    rows = []
    for row in frozen["raw_fittings"]:
        name = row["angle_id"]
        direction, corridors = fitting_corridors(row, exact[name])
        obstacles = [r for r in stationary if r[0] != name]
        blockers = [{"moving_plate": i, **hit} for i, corridor in enumerate(corridors)
                    for hit in hits(corridor, obstacles)]
        blockers.extend({"moving_plate": i, "obstacle": "floor", "role": "floor"}
                        for i, corridor in enumerate(corridors) if corridor.BoundingBox().zmin < -.01)
        rows.append({"id": name, "direction_xyz": shared.xyz(direction), "travel_mm": 100., "hits": blockers})
        if not blockers:
            stationary = [r for r in stationary if r[0] != name]
    remaining_brackets = [r[0] for r in stationary if r[1] == "bracket"]
    timber = {r["member"]: cq.importers.importBrep(str(shared.ROOT / r["path"])).val()
              for r in cache["raw_parts"]}
    n, tangent = model.screen.N, model.revision.thin.T
    directions = [cq.Vector(1, 0, 0), cq.Vector(-1, 0, 0), -n, n, tangent, -tangent,
                  cq.Vector(0, 1, 0), cq.Vector(0, -1, 0), cq.Vector(0, 0, 1), cq.Vector(0, 0, -1)]
    pending, timber_rows = set(timber), []
    while pending:
        found = False
        for name in sorted(pending):
            if exact[name].cut(timber[name]).Volume() > .01:
                raise ValueError("timber stock envelope failed containment")
            obstacles = [r for r in stationary if r[0] != name]
            for direction in directions:
                corridor = convex_linear_sweep(timber[name], direction, 200.)
                if corridor.BoundingBox().zmin >= -.01 and not hits(corridor, obstacles):
                    timber_rows.append({"id": name, "direction_xyz": shared.xyz(direction),
                                        "travel_mm": 200., "hits": []})
                    stationary = [r for r in stationary if r[0] != name]
                    pending.remove(name)
                    found = True
                    break
            if found:
                break
        if not found:
            break
    last_rows = []
    for name in remaining_brackets:
        definition = next(r for r in frozen["raw_fittings"] if r["angle_id"] == name)
        direction, corridors = fitting_corridors(definition, exact[name])
        blockers = [{"moving_plate": i, **hit} for i, corridor in enumerate(corridors)
                    for hit in hits(corridor, [r for r in stationary if r[0] != name])]
        blockers.extend({"moving_plate": i, "obstacle": "floor", "role": "floor"}
                        for i, corridor in enumerate(corridors) if corridor.BoundingBox().zmin < -.01)
        last_rows.append({"id": name, "direction_xyz": shared.xyz(direction), "travel_mm": 100., "hits": blockers})
        if not blockers:
            stationary = [r for r in stationary if r[0] != name]
    unresolved = [r[0] for r in stationary if r[1] == "bracket"]
    return {"bracket_release_rows": rows, "brackets_released_before_timbers": len(rows) - len(remaining_brackets),
            "after_timber_bracket_release_rows": last_rows, "brackets_released": len(rows) - len(unresolved),
            "unresolved_brackets": unresolved, "individual_timber_release_rows": timber_rows,
            "individual_timbers_released": len(timber_rows), "unresolved_timbers": sorted(pending),
            "limits": "All panels/services/screws and70bolt stacks are absent. Brackets use containing unperforated rectangular flange corridors; each moves100mm diagonally away from its two seated faces. Timbers use containing convex raw-stock corridors over200mm, checked against the remaining exact timber/bracket bodies and the floor. Corridors may overstate concave stock occupancy. This proves a nominal initial separation route for individual-member transport; subsequent free handling, carried loads and support stability remain unverified."}


def pack_purchase(quantity: int, each_usd: float, pack_quantity: int,
                  pack_usd: float) -> dict:
    """Find the cheapest mixture of listed packs and individual pieces."""
    if quantity < 0 or pack_quantity <= 0 or min(each_usd, pack_usd) < 0:
        raise ValueError("invalid quantity or price")
    each, pack = Decimal(str(each_usd)), Decimal(str(pack_usd))
    choices = [(n * pack + max(0, quantity - n * pack_quantity) * each,
                n, max(0, quantity - n * pack_quantity))
               for n in range(math.ceil(quantity / pack_quantity) + 1)]
    cost, packs, singles = min(choices)
    return {"required": quantity, "packs": packs, "pack_quantity": pack_quantity,
            "singles": singles, "purchased": packs * pack_quantity + singles,
            "spares": packs * pack_quantity + singles - quantity, "cost_usd": float(cost)}


def stock_takeoff() -> dict:
    with STOCK.open() as stream:
        source = list(csv.DictReader(stream))
    blanks = {r["member"]: {"length_mm": float(r["blank_length_or_panel_width_mm"]),
                            "depth_mm": float(r["blank_depth_or_panel_height_mm"]),
                            "thickness_mm": float(r["thickness_mm"])} for r in source}
    plans = [
        ("4x6", 10, ["base_side_left"]), ("4x6", 10, ["base_side_right"]),
        ("4x6", 8, ["lumber_leg_left"]), ("4x6", 8, ["lumber_leg_right"]),
        ("2x6", 10, ["base_principal_center_left", "base_post_outer_left", "base_post_center_left"]),
        ("2x6", 10, ["base_principal_center_right", "base_post_outer_right", "base_post_center_right"]),
        ("2x6", 10, ["base_header"]), ("2x6", 8, ["base_rail_top"]),
        ("2x6", 8, ["base_floor_left"]), ("2x6", 8, ["base_floor_right"]),
        *[("2x6", 8, [f"base_rail_{label}_left", f"base_rail_{label}_right"])
          for label in ("bottom", "service_lower", "service_upper")],
    ]
    rows, used = [], []
    kerf, trim_each_end = 3.175, 12.7
    for section, feet, members in plans:
        consumed = sum(blanks[n]["length_mm"] for n in members) + len(members) * kerf + 2 * trim_each_end
        remaining = feet * 304.8 - consumed
        if remaining < 0:
            raise ValueError(f"stock yield fails: {members}")
        rows.append({"nominal_section": section, "length_ft": feet, "members": members,
                     "blank_lengths_mm": [blanks[n]["length_mm"] for n in members],
                     "consumed_with_kerf_and_trim_mm": consumed, "remaining_mm": remaining})
        used.extend(members)
    timber = {n for n in blanks if n.startswith(("base_", "lumber_leg_"))}
    if len(used) != 20 or set(used) != timber:
        raise ValueError("stock plan must place all twenty timbers exactly once")
    counts = Counter((r["nominal_section"], r["length_ft"]) for r in rows)
    return {"all_20_timbers_placed": True, "kerf_mm_per_output_piece": kerf,
            "end_trim_allowance_mm_each": trim_each_end, "sticks": rows,
            "purchase_quantities": [{"section": s, "length_ft": f, "quantity": n} for (s, f), n in sorted(counts.items())],
            "nominal_board_feet": sum((24 if r["nominal_section"] == "4x6" else 12) * r["length_ft"] / 12 for r in rows),
            "panel_blanks": [{"name": n, **v} for n, v in blanks.items() if n.startswith(("main_", "kicker_"))],
            "plywood_4x8_sheet_requirement": 3,
            "plywood_layout_condition": "Two nominal 1219.2x2438.4 mm sheets each yield two 1217.6125x1219.2 mm main blanks with one 3.175 mm middle kerf; a third sheet yields both 1217.6125x277 mm kicker blanks. Main panels consume full sheet width and length: no trimming allowance. Listed usable width conflicts with this; actual usable stock has not been inspected.",
            "limits": "Blank envelopes are reused, not finished saw settings. No new structural rip is used. DF-L No.2+ KD untreated solid S4S specification remains required. Stock prices, grade/seasoning, usable size and yield on delivered boards are unverified."}


def bolt_thread_fit(axis: dict, washers: dict) -> dict:
    """Required thread window from the actual frozen stack; no length inference."""
    h, length = axis["hardware_scenario"], axis["nominal_under_head_length_mm"]
    head_t = washers[(axis["id"], "head_washer")]["thickness_mm"]
    nut_t = washers[(axis["id"], "nut_washer")]["thickness_mm"]
    seat = axis["before_plate_mm"] + head_t + axis["grip_mm"] + axis["after_plate_mm"] + nut_t
    pitch = 25.4 / h["threads_per_inch"]
    tip = length - seat - h["nut_height_mm"]
    return {"axis_id": axis["id"], "nominal_length_mm": length,
            "nut_near_face_from_under_head_mm": seat,
            "maximum_smooth_shank_for_nut_to_reach_seat_mm": seat,
            "minimum_thread_length_to_reach_nut_near_face_mm": length - seat,
            "tip_projection_beyond_nut_mm": tip, "tip_threads": tip / pitch,
            "two_tip_threads_nominally_clear": tip >= 2 * pitch - 1e-6,
            "delivered_transition_and_engagement_verified": False,
            "nominal_head_washer_radial_shaft_clearance_mm": (washers[(axis["id"], "head_washer")]["id_mm"] - axis["diameter_mm"]) / 2,
            "nominal_nut_washer_radial_shaft_clearance_mm": (washers[(axis["id"], "nut_washer")]["id_mm"] - axis["diameter_mm"]) / 2,
            "note": "Published minimum full-thread length is a nominal nut-reach comparison; actual length, runout, seated nut height and each bearing/shear-plane thread position remain delivered-part inputs."}


def metal_gravity_rows(frozen: dict, shapes: list, raw: dict) -> list[dict]:
    """Conditional mass/centroid rows with local timber or panel owners.

    Bolt shafts and screw bodies are split by raw receiving stock, because
    their holes intentionally contain no finished wood. Exterior pieces use
    the closest receiver. Their exact compound centroid is retained.
    """
    axes = {a["id"]: a for a in frozen["installed_axes"]}
    screws = {"fastener_" + r["axis_id"]: r for r in frozen["screw_axes"]}
    tnut_panels = {r["name"]: r["panel"] for r in model.tnuts.datums(model.no_shoes_frame)}
    rows = []

    def append(name: str, role: str, owner: str, body: cq.Shape, method: str) -> None:
        volume = body.Volume()
        if volume > .001:
            rows.append({"id": name, "role": role, "owner": owner, "volume_mm3": volume,
                         "mass_kg": volume * 7.85e-6, "centroid_xyz_mm": shared.xyz(body.Center()),
                         "density_kg_m3": 7850., "material_or_mass_verified": False,
                         "ownership_method": method})

    for name, role, body in shapes:
        if role == "tnut":
            append(name, role, tnut_panels[name], body, "source T-nut panel datum")
            continue
        if role == "screw":
            receivers = [screws[name]["panel"], screws[name]["receiver"]]
        elif role in model.ROLES:
            axis_id = name.removesuffix("_" + role)
            receivers = axes[axis_id]["receivers"]
        else:
            continue
        remaining = body
        if role in {"shaft", "screw"}:
            for receiver in receivers:
                portion = remaining.intersect(raw[receiver])
                append(name, role, receiver, portion, "intersection with raw owned stock envelope")
                remaining = remaining.cut(raw[receiver])
        if remaining.Volume() > .001:
            point = cq.Vertex.makeVertex(*remaining.Center().toTuple())
            receiver = min(receivers, key=lambda n: raw[n].distance(point))
            append(name, role, receiver, remaining, "external piece closest to its actual receiver face")
    return rows


def takeoff(frozen: dict, cache: dict, shapes: list) -> dict:
    axes = frozen["installed_axes"]
    counts = Counter((a["source"], a["diameter_mm"], a["nominal_under_head_length_mm"]) for a in axes)
    washers = {}
    changed = {(r["axis_id"], r["role"]): r for r in frozen["small_washer_changes"]}
    for a in axes:
        for role in ("head_washer", "nut_washer"):
            c, h = changed.get((a["id"], role)), a["hardware_scenario"]
            washers[(a["id"], role)] = {"od_mm": c["od_mm"] if c else h["washer_od_mm"],
                                        "id_mm": c["id_mm"] if c else h["washer_id_mm"],
                                        "thickness_mm": c["thickness_mm"] if c else h["washer_thickness_mm"]}
    washer_counts = Counter(tuple(v[k] for k in ("od_mm", "id_mm", "thickness_mm")) for v in washers.values())
    wood_rows, metal_volume = [], 0.
    for name, role, shape in shapes:
        if role in {"timber", "panel"}:
            wood_rows.append({"name": name, "kind": role, "finished_volume_mm3": shape.Volume(),
                              "mass_kg_at_500kg_m3": shape.Volume() * 5e-7})
        elif role in model.ROLES:
            metal_volume += shape.Volume()
    raw = {r["member"]: cq.importers.importBrep(str(shared.ROOT / r["path"])).val()
           for r in cache["raw_parts"] + cache["panel_outline_parts"]}
    gravity = metal_gravity_rows(frozen, shapes, raw)
    owned_volume = sum(r["volume_mm3"] for r in gravity)
    source_volume = sum(body.Volume() for _, role, body in shapes if role in {*model.ROLES, "screw", "tnut"})
    if abs(owned_volume - source_volume) > .1:
        raise ValueError("local gravity ownership must conserve all modeled metal")
    wood_mass = sum(r["mass_kg_at_500kg_m3"] for r in wood_rows)
    bolt_mass = metal_volume * 7.85e-6
    small_metal_mass = sum(r["mass_kg"] for r in gravity if r["role"] in {"screw", "tnut"})
    # Catalog weight range records the B104 SKU/catalog conflict; do not add CAD angle volume.
    angle_low, angle_catalog = (24 * .64 + 12 * .56) * .45359237, (24 * .78 + 12 * .56) * .45359237
    prices = [
        ("new half x 3 in Grade5 hex bolts #397", 42, 1.23, 50, 43.98, 397),
        ("new half x 5 in Grade5 hex bolts #401", 16, 1.89, 25, 33.70, 401),
        ("retained half x 8 in Grade5 hex bolts #407", 4, 4.03, 25, 72.03, 407),
        ("retained three eighth x 4 in Grade5 hex bolts #367", 4, .81, 50, 29.10, 367),
        ("retained three eighth x 4.5 in Grade5 hex bolts #368", 4, .94, 50, 33.54, 368),
        ("half coarse Grade8 hex nuts #2586 comparison", 62, .24, 50, 8.07, 2586),
        ("three eighth coarse Grade5 hex nuts #2571 comparison", 8, .11, 100, 7.53, 2571),
        ("new large half USS Grade8 washers #3064 comparison", 102, .36, 50, 11.89, 3064),
        ("restricted half SAE Grade8 washers #3051", 14, .25, 50, 8.27, 3051),
    ]
    lines = [{"description": text, "url": f"https://boltdepot.com/Product-Details?product={sku}",
              "listed_each_usd": each, "listed_pack_usd": pack,
              **pack_purchase(qty, each, pq, pack), "actual_stack_compatible_or_selected": False}
             for text, qty, each, pq, pack, sku in prices]
    return {"bolts": [{"source": s, "diameter_mm": d, "nominal_length_mm": l, "quantity": n}
                       for (s, d, l), n in sorted(counts.items())],
            "hardware_counts": {"bolts": 70, "nuts": 70, "washers": 140, "angles_B104ZN": 24,
                                "angles_B103ZN": 12, "purchased_Hillman_42605": 66},
            "washer_envelopes": [{"od_mm": od, "id_mm": id_, "thickness_mm": t, "quantity": q}
                                  for (od, id_, t), q in sorted(washer_counts.items())],
            "stock": stock_takeoff(), "thread_fit": [bolt_thread_fit(a, washers) for a in axes],
            "conditional_metal_gravity_rows": gravity,
            "gravity_ownership_audit": {"source_volume_mm3": source_volume,
                                        "owned_volume_mm3": owned_volume,
                                        "difference_mm3": owned_volume - source_volume,
                                        "gravity_rows": len(gravity)},
            "mass": {"finished_wood": wood_rows, "wood_density_kg_m3": 500.,
                     "all_frame_and_panel_wood_kg": wood_mass, "conditional_bolt_metal_kg_at_7850": bolt_mass,
                     "angle_mass_kg_SKU_lower": angle_low, "angle_mass_kg_catalog_upper": angle_catalog,
                     "listed_modeled_mass_kg_range": [wood_mass + bolt_mass + angle_low, wood_mass + bolt_mass + angle_catalog],
                     "screw_and_tnut_conditional_CAD_mass_kg": small_metal_mass,
                     "dead_mass_with_original_25kg_accessory_allowance_range": [wood_mass + bolt_mass + angle_low + small_metal_mass + 25., wood_mass + bolt_mass + angle_catalog + small_metal_mass + 25.],
                     "original_25kg_allowance_covers": ["holds and hold bolts", "electrical equipment including LEDs/wires/connectors"],
                     "excluded": ["pads absent from CAD; no mass input", "accessories outside the original declared 25kg allowance"],
                     "complete_board_weight_established": False},
            "cost": {"observed_date": "2026-10-06", "currency": "USD", "configured_quote": False,
                     "boltdepot_comparison_lines": lines,
                     "angles": [{"model": name, "quantity": q, "each_usd": price, "extended_usd": q * price,
                                 "url": url} for name, q, price, url in (
                                     ("B104ZN", 24, 5.52, "https://www.platt.com/p/0151375/eaton-b-line/four-hole-corner-angle-steel-zinc-plated/781011500436/blib104zn"),
                                     ("B103ZN", 12, 3.53, "https://www.platt.com/p/0151547/eaton-b-line/three-hole-corner-angle-zinc-plated/781011500337/blib103zn"))],
                     "known_partial_comparison_subtotal_usd": 174.84 + sum(r["cost_usd"] for r in lines),
                     "58_new_axis_hardware_and_angles_comparison_usd": 174.84 + sum(lines[i]["cost_usd"] for i in (0, 1, 7, 8)) + pack_purchase(58, .24, 50, 8.07)["cost_usd"],
                     "missing": ["8 retained half-inch 38.1mm-OD washers", "16 retained three-eighth 25.4mm-OD washers within occupied tolerance", "specified lumber prices and availability for 2x4x6x10ft, 2x4x6x8ft, 3x2x6x10ft and 6x2x6x8ft", "purchased plywood/screw actual receipt cost; no extra purchase inferred", "hold/LED/T-nut/harness/pad/accessory receipts or quote", "shipping/tax", "required tools and machining cost"],
                     "complete_installed_cost_established": False,
                     "limits": "These supplier comparisons are not a purchase list. Grade, threads, tolerances and delivered fit remain unqualified. Cheapest listed pack/single mixture buys only needed packs and pieces; no shipping savings assumed."}}


def load_geometry() -> tuple[dict, list]:
    cache = json.loads(GEOMETRY.read_text())
    for name, expected in cache["source_sha256"].items():
        if shared.sha(shared.ROOT / name) != expected:
            raise ValueError(f"cache source changed: {name}")
    rows = cache["parts"]
    shapes = []
    for row in rows:
        path = shared.ROOT / row["path"]
        if shared.sha(path) != row["sha256"]:
            raise ValueError(f"cache part changed: {path}")
        shapes.append((row["id"], row["kind"], cq.importers.importBrep(str(path)).val()))
    for row in cache["raw_parts"] + cache["panel_outline_parts"]:
        if shared.sha(shared.ROOT / row["path"]) != row["sha256"]:
            raise ValueError(f"raw cache part changed: {row['id']}")
    if len([r for r in shapes if r[1] in model.ROLES]) != 350:
        raise ValueError("complete 350-role bolt cache required")
    return cache, shapes


def access(frozen: dict, shapes: list) -> dict:
    axes = frozen["installed_axes"]
    metal = {(name.removesuffix("_" + role), role): body for name, role, body in shapes if role in model.ROLES}
    # The cache loader is reconciled against the parent schema before use.
    all_obstacles = [(name, role, body) for name, role, body in shapes if role not in {"screw"}]
    exposed = [row for row in all_obstacles if row[1] not in {"panel", "wire", "light", "tnut"}]
    tool_rows, removal = [], []
    for axis in axes:
        own = axis["id"]
        obstacles = [r for r in exposed if not r[0].startswith(own + "_")]
        for side in ("head", "nut"):
            bodies, plane, well_margin = socket_envelopes(axis, side, metal)
            clashes = [{"operation": role, **hit} for role, shape in bodies for hit in hits(shape, obstacles)]
            chosen = None
            if not clashes:
                for azimuth in range(0, 360, 15):
                    sector = handle_sector(plane, azimuth)
                    if not hits(sector, obstacles) and sector.BoundingBox().zmin >= -.01:
                        chosen = azimuth
                        break
            tool_rows.append({"axis_id": own, "side": side, "tool_body_hits": clashes,
                              "remote_handle_sector_azimuth_deg": chosen,
                              "well_margin_mm": well_margin,
                              "conditional_access_clear": not clashes and chosen is not None and well_margin >= 0})
        d = cq.Vector(*axis["direction"])
        bolt_travel = axis["nominal_under_head_length_mm"] + 2.
        for role, outward, travel in (("nut", d, axis["tip_projection_beyond_nut_mm"] + axis["hardware_scenario"]["nut_height_mm"] + 2.),
                                       ("nut_washer", d, axis["tip_projection_beyond_nut_mm"] + axis["hardware_scenario"]["nut_height_mm"] + 4.),
                                       ("shaft", -d, bolt_travel), ("head", -d, bolt_travel),
                                       ("head_washer", -d, bolt_travel)):
            corridor = axial_sweep(metal[(own, role)], outward, travel)
            removal.append({"axis_id": own, "operation": role, "outward_xyz": shared.xyz(outward),
                            "travel_mm": travel, "hits": hits(corridor, obstacles)})
    return {"tool_envelopes": TOOL, "tool_rows": tool_rows, "continuous_axial_removal": removal,
            "clear_tool_sides": sum(r["conditional_access_clear"] for r in tool_rows),
            "tool_sides": len(tool_rows), "removal_operations_with_hits": sum(bool(r["hits"]) for r in removal),
            "limits": "Panels, screws and harness/service bodies are removed first for exposed-frame checks. Other joints remain in place. A blocked corridor is a sequence dependency, not proof of impossible individual-member transport. No physical handling, hand room, bolt release under load or delivered tool fit is asserted."}


def assemble_report(frozen: dict, checks: dict) -> dict:
    """Bind completed current-session checks without repeating unchanged CAD."""
    report = {"schema": "thin_bolted_access_takeoff/v1", "candidate": model.CANDIDATE,
              "source_sha256": {str(model.LAYOUT.relative_to(shared.ROOT)): model.LAYOUT_SHA,
                                str(model.EVIDENCE.relative_to(shared.ROOT)): shared.sha(model.EVIDENCE),
                                str(GEOMETRY.relative_to(shared.ROOT)): shared.sha(GEOMETRY),
                                str(STOCK.relative_to(shared.ROOT)): shared.sha(STOCK),
                                str(Path(__file__).relative_to(shared.ROOT)): shared.sha(Path(__file__))},
              "runtime": {"python": platform.python_version(), "cadquery": cq.__version__},
              **checks,
              "release": shared.RELEASE}
    report["bolt_release_sequence"] = bolt_release_sequence(report["access"]["continuous_axial_removal"], frozen["installed_axes"])
    report["reproduce"] = ".venv/bin/python -m scripts.thin_bolted_access_takeoff --out /tmp/thin-access-takeoff-reproduced.json"
    report["retention"] = "This compact report is retained in the existing comparison packet. The shared ignored BREP cache stays active for mechanics/access consumers; do not prune it. No CAD meshes or catalog documents are copied."
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve frozen access/takeoff evidence")
    frozen = model.source_layout()
    cache, shapes = load_geometry()
    report = assemble_report(frozen, {"front_release": release_front(frozen, cache, shapes),
                                     "compact_pass_through_tool": short_wrench_access(frozen, shapes),
                                     "access": access(frozen, shapes),
                                     "member_release": member_release(frozen, cache, shapes),
                                     "takeoff": takeoff(frozen, cache, shapes)})
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "clear_tool_sides": report["access"]["clear_tool_sides"],
                      "removal_operations_with_hits": report["access"]["removal_operations_with_hits"],
                      "compact_tool_sides_clear": report["compact_pass_through_tool"]["clear_tool_sides"],
                      "panel_assemblies_lift_clear": report["front_release"]["nominal_panel_assemblies_lift_clear"],
                      "individual_timbers_released": report["member_release"]["individual_timbers_released"],
                      "cost": report["takeoff"]["cost"]["known_partial_comparison_subtotal_usd"],
                      "mass": report["takeoff"]["mass"]["listed_modeled_mass_kg_range"]}, indent=2))


if __name__ == "__main__":
    main()
