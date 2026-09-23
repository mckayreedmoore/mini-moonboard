"""Source-CAD screen for owner-directed vertical center-principal barrels.

This detached probe moves two full 4x6 center posts outside KICK5/KICK6,
relocates only their four kicker screws, keeps shallow seam backing, and places
two vertical barrel bolts at each principal/header interface.  It does not
modify the selected candidate or either maintained barrel viewer.

Nominal clearance plus an explicit provisional tolerance stack is screened.
Delivered tolerances, wood/barrel resistance, stiffness, post/header attachment,
and native response remain evidence gates; no drilling or fabrication is released.
"""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

import cadquery as cq

from mini_moonboard import panel_grid_v2
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.model import V1_SELECTED_TNUT_FLANGE_DIAMETER_MM
from scripts import owner_barrel_candidate_service as service
from scripts import owner_barrel_selected_hardware as selected
from scripts import owner_layout_protected as protected
from scripts.owner_barrel_coordinates import local_bounds

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
SCHEMA = "owner_barrel_vertical_center_probe/v1"
SIDES = ("left", "right")
CENTER_SCREWS = frozenset(
    f"round_kicker_{side}_center_{index}" for side in SIDES for index in (1, 2)
)

# Geometry choices.  These are probe values, not shop tolerances.
POST_FACE_MM = 88.9
POST_TO_TNUT_NOMINAL_CLEARANCE_MM = 12.7
POST_CENTER_PLACEMENT_TOL_MM = 2.0
POST_HALF_WIDTH_GROWTH_TOL_MM = 1.5
TNUT_CENTER_PLACEMENT_TOL_MM = 1.0
TNUT_RADIUS_GROWTH_TOL_MM = 0.5
SCREW_AXIS_PLACEMENT_TOL_MM = 1.0
BACKER_EDGE_PLACEMENT_TOL_MM = 1.5
SCREW_EDGE_OFFSET_MM = 19.05
SEAM_BACKER_WIDTH_MM = 38.1
SEAM_BACKER_DEPTH_MM = 88.9

BOLT_BORE_DIAMETER_MM = 7.5
HEAD_DIAMETER_MM = 11.0
HEAD_HEIGHT_MM = 4.0
TOOL_DIAMETER_MM = 20.0
TOOL_LENGTH_MM = 40.0
BARREL_AXIS_DEPTH_MM = 19.05
BARREL_THREAD_Z_MM = 305.0
PRINCIPAL_ROWS_Y_MM = (-146.0, -66.0)
BORE_TIP_CLEARANCE_MM = 2.0
COMPLETE_THREAD_END_ALLOWANCE_MM = 2.54  # two 1/4-20 pitches; conservative screen
HIT_TOL_MM3 = 1.0
CONTAINMENT_TOL_MM3 = 0.01


def _round(value, digits=6):
    return round(float(value), digits)


def _bounds(shape):
    box = shape.BoundingBox()
    return [
        _round(getattr(box, field))
        for field in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
    ]


def _cylinder(start, direction, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(*start), cq.Vector(*direction)
    )


def _add(point, direction, distance):
    return tuple(point[i] + direction[i] * distance for i in range(3))


def _outside_volume(shape, hosts):
    return max(
        0.0,
        shape.Volume() - sum(protected._volume(shape, host) for host in hosts),
    )


def _hits(shape, targets, excluded=frozenset()):
    return {
        name: _round(volume)
        for name, target in targets.items()
        if name not in excluded
        and (volume := protected._volume(shape, target)) > HIT_TOL_MM3
    }


def _hardware():
    data = selected.load_selection()
    barrel = data["barrel"]
    washer = data["washers"][0]
    bolt = next(row for row in data["bolts"] if row["product"] == "1456BHT5")
    if (
        barrel["product"] != "JCD14201606NL ZN"
        or barrel["nominal_body_od_mm"] != 10.0076
        or barrel["nominal_body_length_mm"] != 16.002
        or barrel["nominal_thread_axis_from_slotted_end_mm"] != 5.9944
        or washer["product"] != "33857"
        or washer["od_max_mm"] != 19.0246
        or washer["thickness_max_mm"] != 2.032
        or bolt["nominal_length_mm"] != 88.9
        or bolt["length_tolerance_mm"] != [-1.524, 1.016]
    ):
        raise ValueError("Selected center-joint hardware basis changed")
    return data, barrel, washer, bolt


def _source_geometry():
    source = variant(KERF_RIGHT)
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    required = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
        "kicker_left",
        "kicker_right",
    }
    if not required <= set(wood):
        raise ValueError("Kerf-right source members changed")
    header = wood["base_header"].BoundingBox()
    if (
        abs(header.ymin + 175.7) > 1e-6
        or abs(header.ymax + 36.0) > 1e-6
        or abs(header.zmin - 238.9) > 1e-6
        or abs(header.zmax - 277.0) > 1e-6
    ):
        raise ValueError("Kerf-right header bounds changed")
    seam = wood["kicker_left"].BoundingBox().xmax
    if abs(seam - wood["kicker_right"].BoundingBox().xmin) > 1e-6:
        raise ValueError("Kerf-right kicker seam changed")
    return source, wood, seam


def _post_and_backer_geometry(wood, seam):
    kickers = panel_grid_v2.kicker_foothold_datums()
    tnut_centers = {
        "left": kickers["5"][0] - panel_grid_v2.PANEL_HEIGHT_MM,
        "right": kickers["6"][0] - panel_grid_v2.PANEL_HEIGHT_MM,
    }
    tnut_radius = V1_SELECTED_TNUT_FLANGE_DIAMETER_MM / 2
    flange_bounds = {
        side: [center - tnut_radius, center + tnut_radius]
        for side, center in tnut_centers.items()
    }
    post_bounds_x = {
        "left": [
            flange_bounds["left"][0] - POST_TO_TNUT_NOMINAL_CLEARANCE_MM - POST_FACE_MM,
            flange_bounds["left"][0] - POST_TO_TNUT_NOMINAL_CLEARANCE_MM,
        ],
        "right": [
            flange_bounds["right"][1] + POST_TO_TNUT_NOMINAL_CLEARANCE_MM,
            flange_bounds["right"][1]
            + POST_TO_TNUT_NOMINAL_CLEARANCE_MM
            + POST_FACE_MM,
        ],
    }
    posts = {}
    for side in SIDES:
        original = wood[f"base_post_center_{side}"].BoundingBox()
        if (
            abs(original.ylen - 139.7) > 1e-6
            or abs(original.zmin) > 1e-6
            or abs(original.zmax - 238.9) > 1e-6
        ):
            raise ValueError(f"base_post_center_{side}: source bounds changed")
        x0, x1 = post_bounds_x[side]
        posts[f"base_post_center_{side}"] = cq.Solid.makeBox(
            x1 - x0,
            original.ylen,
            original.zlen,
            cq.Vector(x0, original.ymin, original.zmin),
        )

    backer_y0 = wood["base_header"].BoundingBox().ymax - SEAM_BACKER_DEPTH_MM
    backers = {
        "kicker_seam_backer_left": cq.Solid.makeBox(
            SEAM_BACKER_WIDTH_MM,
            SEAM_BACKER_DEPTH_MM,
            238.9,
            cq.Vector(seam - SEAM_BACKER_WIDTH_MM, backer_y0, 0),
        ),
        "kicker_seam_backer_right": cq.Solid.makeBox(
            SEAM_BACKER_WIDTH_MM,
            SEAM_BACKER_DEPTH_MM,
            238.9,
            cq.Vector(seam, backer_y0, 0),
        ),
    }
    tolerance_consumption = (
        POST_CENTER_PLACEMENT_TOL_MM
        + POST_HALF_WIDTH_GROWTH_TOL_MM
        + TNUT_CENTER_PLACEMENT_TOL_MM
        + TNUT_RADIUS_GROWTH_TOL_MM
    )
    return {
        "tnut_centers": tnut_centers,
        "flange_bounds": flange_bounds,
        "posts": posts,
        "backers": backers,
        "nominal_clearance_mm": POST_TO_TNUT_NOMINAL_CLEARANCE_MM,
        "provisional_tolerance_consumption_mm": tolerance_consumption,
        "adverse_provisional_clearance_mm": (
            POST_TO_TNUT_NOMINAL_CLEARANCE_MM - tolerance_consumption
        ),
    }


def _shop_center_screws(source, post_geometry):
    model_rows = {row.name: row for row in source.panel_connections()}
    if len(model_rows) != 66 or not CENTER_SCREWS <= set(model_rows):
        raise ValueError("Panel/kicker screw inventory changed")
    with AXES.open(newline="") as stream:
        shop = {
            row["name"]: row
            for row in csv.DictReader(stream)
            if row["name"] in CENTER_SCREWS
        }
    if set(shop) != set(CENTER_SCREWS):
        raise ValueError("Four center kicker shop rows changed")

    relocated = {}
    rows = []
    for side in SIDES:
        receiver_name = f"kicker_seam_backer_{side}"
        receiver_shape = post_geometry["backers"][receiver_name]
        receiver = receiver_shape.BoundingBox()
        x = (receiver.xmin + receiver.xmax) / 2
        for index in (1, 2):
            name = f"round_kicker_{side}_center_{index}"
            old = model_rows[name]
            source_row = shop[name]
            purchased = float(source_row["shop_purchased_length_mm"])
            if (
                old.direction.normalized().toTuple() != (0.0, -1.0, 0.0)
                or abs(purchased - 63.5) > 1e-6
                or abs(old.start.z - (60.0 if index == 1 else 192.0)) > 1e-6
            ):
                raise ValueError(f"{name}: source screw changed")
            moved = replace(old, start=cq.Vector(x, old.start.y, old.start.z))
            solid = _cylinder(
                moved.start.toTuple(),
                moved.direction.normalized().toTuple(),
                purchased,
                moved.diameter,
            )
            outside = _outside_volume(solid, (receiver_shape,))
            # Shaft begins in plywood; only the part behind its rear face is in wood.
            panel_back_y = -36.0
            embedded = _cylinder(
                (x, panel_back_y, moved.start.z),
                (0.0, -1.0, 0.0),
                panel_back_y - (moved.start.y - purchased),
                moved.diameter,
            )
            embedded_outside = _outside_volume(embedded, (receiver_shape,))
            tnut_x = post_geometry["tnut_centers"][side]
            edge_margin = min(x - receiver.xmin, receiver.xmax - x)
            rows.append(
                {
                    "name": name,
                    "receiver": receiver_name,
                    "old_start_xyz_mm": list(old.start.toTuple()),
                    "new_start_xyz_mm": list(moved.start.toTuple()),
                    "purchased_length_mm": purchased,
                    "nominal_nearest_receiver_edge_mm": _round(edge_margin),
                    "adverse_provisional_receiver_edge_mm": _round(
                        edge_margin
                        - BACKER_EDGE_PLACEMENT_TOL_MM
                        - SCREW_AXIS_PLACEMENT_TOL_MM
                    ),
                    "axis_x_distance_from_kick_tnut_mm": _round(abs(x - tnut_x)),
                    "embedded_shaft_outside_receiver_mm3": _round(embedded_outside),
                    "whole_shaft_outside_receiver_mm3": _round(outside),
                    "structural_frame_credit": False,
                }
            )
            relocated[name] = {"connection": moved, "solid": solid}
    return model_rows, relocated, rows


def _modified_inventory(base, relocated):
    solids = {family: dict(rows) for family, rows in base["solids"].items()}
    panel = solids["panel_screws"]
    for name, row in relocated.items():
        panel[name] = row["solid"]
    if len(panel) != 66 or set(relocated) != set(CENTER_SCREWS):
        raise ValueError("Relocated screw inventory is not exactly four of 66")
    return {
        **base,
        "solids": solids,
        "bounds": {
            family: {name: shape.BoundingBox() for name, shape in rows.items()}
            for family, rows in solids.items()
        },
    }


def _joint_geometry(wood, post_geometry, barrel, washer, bolt):
    rows_y = PRINCIPAL_ROWS_Y_MM
    header = wood["base_header"]
    hb = header.BoundingBox()
    max_washer_radius = washer["od_max_mm"] / 2
    washer_edge_reserve = min(
        rows_y[0] - max_washer_radius - hb.ymin,
        hb.ymax - rows_y[1] - max_washer_radius,
    )
    body_recess = (
        BARREL_AXIS_DEPTH_MM - barrel["nominal_thread_axis_from_slotted_end_mm"]
    )
    body_depth = body_recess + barrel["nominal_body_length_mm"]
    bolt_min = bolt["nominal_length_mm"] + bolt["length_tolerance_mm"][0]
    bolt_max = bolt["nominal_length_mm"] + bolt["length_tolerance_mm"][1]
    max_washer_t = washer["thickness_max_mm"]
    thread_depth = BARREL_THREAD_Z_MM - hb.zmin
    minimum_tip_past_axis = bolt_min - max_washer_t - thread_depth
    maximum_embedded_length = bolt_max - max_washer_t
    all_roles = {}
    records = []
    cut_roles = {"base_header": []}
    for side in SIDES:
        principal_name = f"base_principal_center_{side}"
        principal = wood[principal_name]
        pb = principal.BoundingBox()
        center_x = (pb.xmin + pb.xmax) / 2
        entry_x = pb.xmax if side == "left" else pb.xmin
        barrel_axis = (-1.0, 0.0, 0.0) if side == "left" else (1.0, 0.0, 0.0)
        cut_roles[principal_name] = []
        local = local_bounds(principal)
        for index, y in enumerate(rows_y, 1):
            name = f"vertical_principal_{side}_{index}"
            seat = (center_x, y, hb.zmin)
            bolt_axis = (0.0, 0.0, 1.0)
            thread = (center_x, y, BARREL_THREAD_Z_MM)
            entry = (entry_x, y, BARREL_THREAD_Z_MM)
            expected = _add(entry, barrel_axis, BARREL_AXIS_DEPTH_MM)
            if max(abs(a - b) for a, b in zip(expected, thread, strict=True)) > 1e-6:
                raise ValueError(f"{name}: bolt and selected barrel axes miss")
            shaft_start = _add(seat, bolt_axis, -max_washer_t)
            roles = {
                "bolt_bore": _cylinder(
                    seat,
                    bolt_axis,
                    maximum_embedded_length + BORE_TIP_CLEARANCE_MM,
                    BOLT_BORE_DIAMETER_MM,
                ),
                "shaft_max": _cylinder(shaft_start, bolt_axis, bolt_max, 6.35),
                "washer_max": _cylinder(
                    shaft_start,
                    bolt_axis,
                    max_washer_t,
                    washer["od_max_mm"],
                ),
                "head": _cylinder(
                    _add(shaft_start, bolt_axis, -HEAD_HEIGHT_MM),
                    bolt_axis,
                    HEAD_HEIGHT_MM,
                    HEAD_DIAMETER_MM,
                ),
                "driver_access": _cylinder(
                    seat,
                    (0.0, 0.0, -1.0),
                    TOOL_LENGTH_MM,
                    TOOL_DIAMETER_MM,
                ),
                "barrel_cross_bore": _cylinder(
                    entry, barrel_axis, body_depth, barrel["nominal_body_od_mm"]
                ),
                "selected_barrel": _cylinder(
                    _add(entry, barrel_axis, body_recess),
                    barrel_axis,
                    barrel["nominal_body_length_mm"],
                    barrel["nominal_body_od_mm"],
                ),
                "barrel_access": _cylinder(
                    entry,
                    tuple(-value for value in barrel_axis),
                    TOOL_LENGTH_MM,
                    TOOL_DIAMETER_MM,
                ),
            }
            for role, shape in roles.items():
                all_roles[f"{name}/{role}"] = shape
            cut_roles["base_header"].append(roles["bolt_bore"])
            cut_roles[principal_name].extend(
                (roles["bolt_bore"], roles["barrel_cross_bore"])
            )
            t = thread[1] * 0.6427876096865394 + thread[2] * 0.766044443118978
            n = thread[1] * -0.766044443118978 + thread[2] * 0.6427876096865394
            barrel_radius = barrel["nominal_body_od_mm"] / 2
            records.append(
                {
                    "name": name,
                    "station": f"clip_split_base_center_{side}",
                    "hosts": ["base_header", principal_name],
                    "bolt_seat_xyz_mm": list(seat),
                    "bolt_axis_xyz": list(bolt_axis),
                    "barrel_entry_xyz_mm": list(entry),
                    "barrel_axis_xyz": list(barrel_axis),
                    "thread_axis_xyz_mm": list(thread),
                    "selected_barrel_recess_mm": _round(body_recess),
                    "selected_barrel_bore_depth_mm": _round(body_depth),
                    "wood_beyond_barrel_bore_mm": _round(pb.xlen - body_depth),
                    "minimum_bolt_tip_past_thread_axis_mm": _round(
                        minimum_tip_past_axis
                    ),
                    "minimum_complete_thread_endpoint_past_axis_mm": _round(
                        minimum_tip_past_axis - COMPLETE_THREAD_END_ALLOWANCE_MM
                    ),
                    "barrel_x_edge_ligament_mm": _round(
                        min(center_x - pb.xmin, pb.xmax - center_x) - barrel_radius
                    ),
                    "barrel_local_tn_edge_ligament_mm": _round(
                        min(
                            t - local["t"][0],
                            local["t"][1] - t,
                            n - local["n"][0],
                            local["n"][1] - n,
                        )
                        - barrel_radius
                    ),
                    "role_bounds_xyz_mm": {
                        role: _bounds(shape) for role, shape in roles.items()
                    },
                }
            )
    pair_pitch = rows_y[1] - rows_y[0]
    return {
        "rows_y_mm": list(rows_y),
        "minimum_max_washer_header_edge_reserve_mm": washer_edge_reserve,
        "driver_edge_reserve_mm": min(
            rows_y[0] - TOOL_DIAMETER_MM / 2 - hb.ymin,
            hb.ymax - rows_y[1] - TOOL_DIAMETER_MM / 2,
        ),
        "barrel_pair_axis_pitch_mm": pair_pitch,
        "barrel_pair_clear_wood_between_bores_mm": (
            pair_pitch - barrel["nominal_body_od_mm"]
        ),
        "header_clear_wood_between_bolt_bores_mm": (pair_pitch - BOLT_BORE_DIAMETER_MM),
        "roles": all_roles,
        "records": records,
        "cuts": cut_roles,
        "hardware": {
            "barrel_product": barrel["product"],
            "barrel_od_mm": barrel["nominal_body_od_mm"],
            "barrel_length_mm": barrel["nominal_body_length_mm"],
            "barrel_axis_from_slotted_end_mm": barrel[
                "nominal_thread_axis_from_slotted_end_mm"
            ],
            "bolt_product": bolt["product"],
            "bolt_nominal_length_mm": bolt["nominal_length_mm"],
            "bolt_adverse_length_range_mm": [bolt_min, bolt_max],
            "washer_product": washer["product"],
            "washer_max_od_mm": washer["od_max_mm"],
            "washer_max_thickness_mm": max_washer_t,
        },
    }


def _geometry_checks(wood, post_geometry, joint, inventory, relocated):
    candidate_wood = {
        **wood,
        **post_geometry["posts"],
        **post_geometry["backers"],
    }
    fixed_hits = protected.hits(joint["roles"], inventory)
    protected_hits = {name: hits for name, hits in fixed_hits.items() if hits}

    unrelated_hits = {}
    service_cutters = service.candidate_service_cutters(variant(KERF_RIGHT), wood)
    service_voids = {
        f"{member}/{name}": cutter.intersect(wood[member])
        for member, name, cutter in service_cutters
        if member in wood and cutter.intersect(wood[member]).Volume() > HIT_TOL_MM3
    }
    service_hits = {}
    for record in joint["records"]:
        prefix = record["name"] + "/"
        allowed = set(record["hosts"])
        unrelated = {
            name: shape for name, shape in candidate_wood.items() if name not in allowed
        }
        for name, shape in joint["roles"].items():
            if not name.startswith(prefix):
                continue
            if hits := _hits(shape, unrelated):
                unrelated_hits[name] = hits
            if hits := _hits(
                shape,
                {
                    name: void
                    for name, void in service_voids.items()
                    if name.split("/", 1)[0] in allowed
                },
            ):
                service_hits[name] = hits

    role_items = list(joint["roles"].items())
    peer_hits = {}
    for index, (first_name, first) in enumerate(role_items):
        first_pair, first_role = first_name.rsplit("/", 1)
        for second_name, second in role_items[index + 1 :]:
            second_pair, second_role = second_name.rsplit("/", 1)
            if first_pair == second_pair:
                continue
            if first_role not in {
                "shaft_max",
                "washer_max",
                "head",
                "selected_barrel",
                "bolt_bore",
                "barrel_cross_bore",
                "driver_access",
                "barrel_access",
            } or second_role not in {
                "shaft_max",
                "washer_max",
                "head",
                "selected_barrel",
                "bolt_bore",
                "barrel_cross_bore",
                "driver_access",
                "barrel_access",
            }:
                continue
            volume = protected._volume(first, second)
            if volume > HIT_TOL_MM3:
                peer_hits[f"{first_name}|{second_name}"] = _round(volume)

    post_protected_hits = {}
    for post_name, post in post_geometry["posts"].items():
        families = {}
        for family, shapes in inventory["solids"].items():
            hits = _hits(post, shapes)
            if hits:
                families[family] = hits
        if families:
            post_protected_hits[post_name] = families

    backer_protected_hits = {}
    for name, backer in post_geometry["backers"].items():
        side = name.rsplit("_", 1)[1]
        own_screws = frozenset(
            screw for screw in relocated if f"_{side}_center_" in screw
        )
        families = {}
        for family, shapes in inventory["solids"].items():
            hits = _hits(
                backer,
                shapes,
                own_screws if family == "panel_screws" else frozenset(),
            )
            if hits:
                families[family] = hits
        if families:
            backer_protected_hits[name] = families

    combined = {}
    for member in (
        "base_header",
        "base_principal_center_left",
        "base_principal_center_right",
    ):
        uncut = wood[member]
        cutters = list(joint["cuts"][member])
        inherited = [
            cutter for host, _name, cutter in service_cutters if host == member
        ]
        cut = uncut
        for cutter in (*inherited, *cutters):
            cut = cut.cut(cutter)
        combined[member] = {
            "candidate_cut_count": len(cutters),
            "inherited_service_cut_count": len(inherited),
            "uncut_volume_mm3": _round(uncut.Volume()),
            "combined_cut_volume_mm3": _round(cut.Volume()),
            "removed_volume_mm3": _round(uncut.Volume() - cut.Volume()),
            "valid": cut.isValid(),
            "solid_count": len(cut.Solids()),
        }

    intended_outside = {}
    for record in joint["records"]:
        hosts = tuple(wood[name] for name in record["hosts"])
        principal = wood[record["hosts"][1]]
        prefix = record["name"] + "/"
        for name, shape in joint["roles"].items():
            if not name.startswith(prefix):
                continue
            role = name.rsplit("/", 1)[1]
            containment_shape = (
                _cylinder(
                    record["bolt_seat_xyz_mm"],
                    record["bolt_axis_xyz"],
                    joint["hardware"]["bolt_adverse_length_range_mm"][1]
                    - joint["hardware"]["washer_max_thickness_mm"],
                    6.35,
                )
                if role == "shaft_max"
                else shape
            )
            expected_hosts = (
                hosts
                if role in ("bolt_bore", "shaft_max")
                else (principal,)
                if role in ("barrel_cross_bore", "selected_barrel")
                else ()
            )
            if expected_hosts:
                outside = _outside_volume(containment_shape, expected_hosts)
                if outside > CONTAINMENT_TOL_MM3:
                    intended_outside[name] = _round(outside)

    seam = wood["kicker_left"].BoundingBox().xmax
    header = wood["base_header"]
    seam_samples = {}
    for side, sign in (("left", -1), ("right", 1)):
        backer = post_geometry["backers"][f"kicker_seam_backer_{side}"]
        x = seam + sign * 0.5
        seam_samples[side] = {
            "backer_full_height_samples": all(
                backer.isInside(cq.Vector(x, -36.1, z), 1e-5)
                for z in (0.5, 60.0, 119.45, 192.0, 238.4)
            ),
            "header_continuation_samples": all(
                header.isInside(cq.Vector(x, -36.1, z), 1e-5)
                for z in (239.4, 257.95, 276.5)
            ),
            "nominal_panel_contact_area_mm2": _round(SEAM_BACKER_WIDTH_MM * 238.9),
        }

    geometry_clear = not any(
        (
            protected_hits,
            unrelated_hits,
            service_hits,
            peer_hits,
            post_protected_hits,
            backer_protected_hits,
            intended_outside,
        )
    ) and all(row["valid"] and row["solid_count"] == 1 for row in combined.values())
    return {
        "protected_hardware_hits_mm3": protected_hits,
        "unrelated_wood_hits_mm3": unrelated_hits,
        "candidate_service_void_hits_mm3": service_hits,
        "peer_role_hits_mm3": peer_hits,
        "moved_post_protected_hits_mm3": post_protected_hits,
        "seam_backer_protected_hits_mm3": backer_protected_hits,
        "intended_path_outside_hosts_mm3": intended_outside,
        "combined_cut_members": combined,
        "seam_backing": seam_samples,
        "geometry_clear": geometry_clear,
    }


def build_report():
    """Build one bounded nominal/adverse-tolerance geometry report."""
    _, barrel, washer, bolt = _hardware()
    source, wood, seam = _source_geometry()
    post_geometry = _post_and_backer_geometry(wood, seam)
    model_screws, relocated, screw_rows = _shop_center_screws(source, post_geometry)
    base_inventory = protected.inventory()
    inventory = _modified_inventory(base_inventory, relocated)
    joint = _joint_geometry(wood, post_geometry, barrel, washer, bolt)
    checks = _geometry_checks(wood, post_geometry, joint, inventory, relocated)
    if post_geometry["adverse_provisional_clearance_mm"] <= 0:
        raise ValueError("Provisional post/T-nut tolerance stack has no clearance")
    if len(model_screws) != 66 or len(relocated) != 4:
        raise ValueError("Panel screw preservation count changed")

    geometry_candidate = bool(
        checks["geometry_clear"]
        and all(
            row["minimum_complete_thread_endpoint_past_axis_mm"] > 0
            and row["barrel_x_edge_ligament_mm"] > 0
            and row["barrel_local_tn_edge_ligament_mm"] > 0
            and row["wood_beyond_barrel_bore_mm"] > 0
            for row in joint["records"]
        )
        and all(
            row["backer_full_height_samples"] and row["header_continuation_samples"]
            for row in checks["seam_backing"].values()
        )
    )
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "detached owner-directed center geometry; selected/current scenes unchanged",
        "source_candidate": source.KEY,
        "native_solve_run": False,
        "post_layout": {
            "kicker_seam_x_mm": _round(seam),
            "kick_tnut_centers_x_mm": {
                side: _round(value)
                for side, value in post_geometry["tnut_centers"].items()
            },
            "kick_tnut_flange_bounds_x_mm": {
                side: [_round(value) for value in bounds]
                for side, bounds in post_geometry["flange_bounds"].items()
            },
            "moved_post_bounds_xyz_mm": {
                name: _bounds(shape) for name, shape in post_geometry["posts"].items()
            },
            "seam_backer_bounds_xyz_mm": {
                name: _bounds(shape) for name, shape in post_geometry["backers"].items()
            },
            "nominal_post_to_tnut_flange_clearance_mm": post_geometry[
                "nominal_clearance_mm"
            ],
            "provisional_tolerance_stack_mm": {
                "post_center_placement": POST_CENTER_PLACEMENT_TOL_MM,
                "post_half_width_growth": POST_HALF_WIDTH_GROWTH_TOL_MM,
                "tnut_center_placement": TNUT_CENTER_PLACEMENT_TOL_MM,
                "tnut_radius_growth": TNUT_RADIUS_GROWTH_TOL_MM,
                "total_consumed": post_geometry["provisional_tolerance_consumption_mm"],
                "remaining_clearance": post_geometry[
                    "adverse_provisional_clearance_mm"
                ],
                "status": "PROVISIONAL_NOT_CONTROLLED",
            },
            "literal_tnut_centered_full_post": {
                "status": "REJECTED_NOMINAL_WITHOUT_RELIEF",
                "left_bounds_x_mm": [-169.41, -80.51],
                "right_bounds_x_mm": [79.15, 168.05],
                "right_driver_overlap_mm": 0.85,
                "right_selected_max_washer_overlap_mm": 0.3623,
                "reason": (
                    "Each T-nut and provisional hold path passes through its post; "
                    "the right post also overlaps the driver and selected maximum "
                    "washer envelope. The outside-flange pose avoids relief cuts."
                ),
            },
        },
        "panel_screws": {
            "source_count": len(model_screws),
            "unchanged_count": len(model_screws) - len(relocated),
            "relocated_count": len(relocated),
            "relocated_names": sorted(relocated),
            "rows": screw_rows,
            "receiver_role": "panel and kicker-seam support only",
            "structural_frame_credit": False,
        },
        "principal_header_joint": {
            key: value for key, value in joint.items() if key not in ("roles", "cuts")
        },
        "candidate_inventory_delta": {
            "barrel_pairs": {"current": 46, "proposed": 48},
            "JCD14201606NL ZN": {"current": 46, "proposed": 48},
            "Fastenal 33857": {"current": 46, "proposed": 48},
            "CDE 1456BHT5": {"current": 4, "proposed": 8},
            "CDE 1472BHT5": {"current": 26, "proposed": 24},
            "basis": (
                "Replace two current 4.5-in single angled principal/header bolts "
                "with four selected 3.5-in vertical bolts."
            ),
        },
        "checks": checks,
        "decision": {
            "nominal_and_provisional_tolerance_geometry": (
                "CANDIDATE" if geometry_candidate else "NO_GO"
            ),
            "complete_joint": "EVIDENCE_BLOCKED",
            "diy_ready": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "blocking_gates": [
                "controlled delivered post, T-nut, drill, barrel, washer, and bolt tolerances",
                "moved-post/header connection and shallow seam-backer attachment resistance",
                "selected barrel material, usable female thread, proof, wall, and stripping resistance",
                "combined-cut DF-L splitting, group action, reversal, and complete-joint resistance",
                "representative two-direction stiffness and reversed-twist test",
                "delivered driver, recessed barrel insertion/orientation, removal, and hold-bolt access",
            ],
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
