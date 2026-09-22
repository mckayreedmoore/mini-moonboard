"""Detached direct-barrel replan for the two integrated 4x6 center posts.

Nominal source geometry only. Angled header-face pockets are a machining trial,
not a drill schedule, hardware qualification, or structural release.
"""

from itertools import combinations

import cadquery as cq

from mini_moonboard.box_frame import Connection
from mini_moonboard.floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    TRANSLATE_NAMES,
    variant,
)
from scripts import owner_barrel_center_layout as center
from scripts import owner_barrel_center_post_replacement as replacement
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly

SIDES = ("left", "right")
STATIONS = tuple(
    f"clip_split_{joint}_center_{side}"
    for joint in ("header", "base")
    for side in SIDES
)
OD = center.BARREL_OD_MM
LENGTH = center.BARREL_LENGTH_MM
OFFSET = center.THREAD_AXIS_OFFSET_MM
WASHER_T = center.WASHER_THICKNESS_MM
BORE_TIP_CLEARANCE_MM = 4.0
TOL = 1.0
RELEASE_FLAGS = {
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _cylinder(point, axis, length, diameter):
    return center._cylinder(point, axis, length, diameter)


def _add(point, axis, distance):
    return center._add(point, axis, distance)


def _hits(shape, targets):
    box = shape.BoundingBox()
    return {
        name: round(volume, 6)
        for name, other in targets.items()
        if (volume := protected._volume(shape, other, box, other.BoundingBox())) > TOL
    }


def _pose(
    station,
    index,
    *,
    seat,
    axis,
    entry,
    barrel_axis,
    axis_depth,
    first,
    second,
    barrel_host,
    first_depth,
    thread_depth,
    bolt_length,
    entry_face,
    bore_length=None,
    pocket=False,
    washer_od=center.WASHER_DIAMETER_MM,
):
    """Build a crossing bolt/barrel and its complete finite access envelopes."""
    name = f"barrel_center_{station}_{index}"
    recess = axis_depth - OFFSET
    receiver_width = barrel_host.BoundingBox().xlen
    if recess < 0 or recess + LENGTH > receiver_width:
        raise ValueError(f"{name}: barrel cannot fit the receiver width")
    thread = _add(seat, axis, thread_depth)
    barrel_thread = _add(entry, barrel_axis, axis_depth)
    if max(abs(a - b) for a, b in zip(thread, barrel_thread, strict=True)) > 1e-5:
        raise ValueError(f"{name}: bolt and barrel axes miss")
    barrel = _cylinder(_add(entry, barrel_axis, recess), barrel_axis, LENGTH, OD)
    cross_bore = _cylinder(entry, barrel_axis, recess + LENGTH, OD)
    shaft_start = _add(seat, axis, -WASHER_T)
    bore_length = bolt_length if bore_length is None else bore_length
    tip_extension = _cylinder(
        _add(seat, axis, bolt_length - WASHER_T),
        axis,
        BORE_TIP_CLEARANCE_MM,
        center.BORE_DIAMETER_MM,
    )
    solids = {
        "bolt_bore": _cylinder(
            seat,
            axis,
            bore_length - WASHER_T + BORE_TIP_CLEARANCE_MM,
            center.BORE_DIAMETER_MM,
        ),
        "barrel_cross_bore": cross_bore,
        "shaft": _cylinder(
            shaft_start, axis, bolt_length, center.hardware.THREAD_MAJOR_MM
        ),
        "barrel": barrel,
        "washer": _cylinder(shaft_start, axis, WASHER_T, washer_od),
        "head": _cylinder(
            _add(shaft_start, axis, -4), axis, 4, center.HEAD_DIAMETER_MM
        ),
        "bolt_tool": _cylinder(
            seat,
            tuple(-v for v in axis),
            center.TOOL_LENGTH_MM,
            center.TOOL_DIAMETER_MM,
        ),
        "barrel_tool": _cylinder(
            entry,
            tuple(-v for v in barrel_axis),
            center.TOOL_LENGTH_MM,
            center.TOOL_DIAMETER_MM,
        ),
    }
    if pocket:
        # ponytail: one 15 mm flat seat is enough to screen the angled washer;
        # a delivered counterbore and edge tolerance require separate design.
        solids["head_pocket"] = _cylinder(_add(seat, axis, -15), axis, 15, washer_od)
    first_bore = _cylinder(seat, axis, first_depth, center.BORE_DIAMETER_MM)
    second_bore = _cylinder(
        _add(seat, axis, first_depth),
        axis,
        thread_depth - first_depth,
        center.BORE_DIAMETER_MM,
    )
    full_core = _cylinder(seat, axis, thread_depth, center.BORE_DIAMETER_MM)
    return (
        name,
        solids,
        {
            "entry_face": entry_face,
            "bolt_seat_xyz_mm": [round(v, 6) for v in seat],
            "bolt_axis_xyz": list(axis),
            "barrel_entry_xyz_mm": [round(v, 6) for v in entry],
            "barrel_axis_xyz": list(barrel_axis),
            "thread_axis_xyz_mm": [round(v, 6) for v in thread],
            "bolt_length_mm": bolt_length,
            "washer_diameter_mm": washer_od,
            "barrel_axis_depth_mm": axis_depth,
            "barrel_receiver_width_mm": receiver_width,
            "barrel_recess_mm": round(recess, 6),
            "wood_beyond_barrel_mm": round(receiver_width - recess - LENGTH, 6),
            "barrel_cross_bore_depth_mm": round(recess + LENGTH, 6),
            "nominal_tip_beyond_thread_axis_mm": round(
                bolt_length - WASHER_T - thread_depth, 6
            ),
            "modeled_bore_depth_past_nominal_tip_mm": round(
                bore_length - bolt_length + BORE_TIP_CLEARANCE_MM, 6
            ),
            "tip_extension_in_receiver_fraction": round(
                protected._volume(tip_extension, second) / tip_extension.Volume(), 7
            ),
            "bolt_barrel_intersection_mm3": round(
                protected._volume(solids["bolt_bore"], cross_bore), 6
            ),
            "intended_bore_core_fraction": {
                "first": round(
                    protected._volume(first_bore, first) / first_bore.Volume(), 7
                ),
                "second": round(
                    protected._volume(second_bore, second) / second_bore.Volume(), 7
                ),
            },
            "joined_wood_bore_core_fraction": round(
                (
                    protected._volume(full_core, first)
                    + protected._volume(full_core, second)
                )
                / full_core.Volume(),
                7,
            ),
            "barrel_body_in_host_fraction": round(
                protected._volume(barrel, barrel_host) / barrel.Volume(), 7
            ),
            "barrel_cross_bore_in_host_fraction": round(
                protected._volume(cross_bore, barrel_host) / cross_bore.Volume(), 7
            ),
            "screened_roles": sorted(solids),
            "complete_thread_engagement_verified": False,
        },
    )


def build(*, assembly=None, wood=None, post_bolt_length_mm=4 * 25.4):
    """Source-build four revised stations and report every detected nominal clash."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    proof = replacement.build_model(assembly=assembly)
    source_wood = proof["wood"]
    wood = source_wood if wood is None else wood
    if (
        proof["report"]["stock_name"] != "4x6_depth"
        or proof["report"]["fixed_geometry_disposition"] != "CLEAR"
        or any(name.startswith("inner_kicker_backer_") for name in wood)
    ):
        raise ValueError("Expected source-bound, backer-free 4x6 post proof")
    for name in ("base_header", *replacement.POSTS):
        a, b = wood[name].BoundingBox(), source_wood[name].BoundingBox()
        if any(
            abs(getattr(a, field) - getattr(b, field)) > 1e-5
            for field in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
        ):
            raise ValueError(f"{name}: supplied wood differs from detached proof")
    header = wood["base_header"]
    hb = header.BoundingBox()
    fixed = protected.inventory()
    if fixed["counts"]["panel_screws"] != 66 or fixed["counts"]["frame_bolts"] != 12:
        raise ValueError("Fixed axes changed")
    service_voids = {}
    for member, cutter_name, cutter in variant(KERF_RIGHT).service_cutters():
        if member not in wood:
            continue
        if member in TRANSLATE_NAMES:
            cutter = cutter.translate(cq.Vector(-KERF_RIGHT_MM, 0, 0))
        void = cutter.intersect(wood[member])
        if void.Volume() > TOL:
            service_voids[f"{member}/{cutter_name}"] = void
    installed, checks, reports, host_map = {}, {}, {}, {}
    for side in SIDES:
        post_name = f"base_post_center_{side}"
        principal_name = f"base_principal_center_{side}"
        post, principal = wood[post_name], wood[principal_name]
        pb, qb = post.BoundingBox(), principal.BoundingBox()
        if abs(pb.zmax - hb.zmin) > 1e-5 or abs(qb.zmin - hb.zmax) > 1e-5:
            raise ValueError(f"{side}: direct butt planes changed")
        post_station = f"clip_split_header_center_{side}"
        principal_station = f"clip_split_base_center_{side}"
        reports[post_station] = {"family": "post_header", "bolts": {}}
        reports[principal_station] = {"family": "principal_header", "bolts": {}}
        # Pull both seats clear of the principal footprint above the header.
        post_center_x = pb.xmax - 28.4 if side == "left" else pb.xmin + 28.4
        outer_x = pb.xmin if side == "left" else pb.xmax
        post_barrel_axis = (1.0 if side == "left" else -1.0, 0.0, 0.0)
        post_depth = abs(post_center_x - outer_x)
        for index, y in enumerate((-145.0, -110.0), 1):
            name, solids, row = _pose(
                post_station,
                index,
                seat=(post_center_x, y, hb.zmax),
                axis=(0.0, 0.0, -1.0),
                entry=(outer_x, y, 200.0),
                barrel_axis=post_barrel_axis,
                axis_depth=post_depth,
                first=header,
                second=post,
                barrel_host=post,
                first_depth=hb.zlen,
                thread_depth=hb.zmax - 200.0,
                bolt_length=post_bolt_length_mm,
                entry_face="post_outer_side",
                bore_length=4 * 25.4,
            )
            reports[post_station]["bolts"][name] = row
            checks[name] = solids
            host_map[name] = ("base_header", post_name)
        principal_x = (qb.xmin + qb.xmax) / 2
        for index, (x_offset, entry_z, bolt_length) in enumerate(
            ((-10.0, 252.0, 5 * 25.4), (10.0, 259.0, 4.5 * 25.4)), 1
        ):
            axis = (0.0, -center.N[0], center.N[1])
            x = principal_x + x_offset
            outer_x = qb.xmin if index == 1 else qb.xmax
            barrel_axis = (1.0 if index == 1 else -1.0, 0.0, 0.0)
            face_point = (x, hb.ymin, entry_z)
            seat = _add(face_point, axis, 15.0)
            thread_depth = 100.0
            thread = _add(seat, axis, thread_depth)
            first_depth = (hb.zmax - seat[2]) / axis[2]
            name, solids, row = _pose(
                principal_station,
                index,
                seat=seat,
                axis=axis,
                entry=(outer_x, thread[1], thread[2]),
                barrel_axis=barrel_axis,
                axis_depth=abs(x - outer_x),
                first=header,
                second=principal,
                barrel_host=principal,
                first_depth=first_depth,
                thread_depth=thread_depth,
                bolt_length=bolt_length,
                entry_face="header_rear_recess",
                pocket=True,
                washer_od=19.05,
            )
            reports[principal_station]["bolts"][name] = row
            checks[name] = solids
            host_map[name] = ("base_header", principal_name)

    retired = set(STATIONS)
    retained = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] not in retired
    }
    retained.update(
        {
            f"stack/{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            if assembly["bolt_station"][name] not in retired
            for role, shape in stack.items()
        }
    )
    candidate_to_retained = {}
    post_hits, pair_hits, access_hits, tool_pair_hits = {}, {}, {}, {}
    service_hits, driver_pocket_hits = {}, {}
    for name, roles in checks.items():
        station = next(s for s in STATIONS if name.startswith(f"barrel_center_{s}_"))
        row = reports[station]["bolts"][name]
        allowed = set(host_map[name])
        unrelated = {n: s for n, s in wood.items() if n not in allowed}
        row["protected_hits_mm3"] = {
            role: hits for role, hits in protected.hits(roles, fixed).items() if hits
        }
        row["unrelated_wood_hits_mm3"] = {
            role: hits
            for role, shape in roles.items()
            if (hits := _hits(shape, unrelated))
        }
        for role in ("barrel", "barrel_cross_bore", "bolt_bore", "shaft"):
            if hits := _hits(roles[role], service_voids):
                service_hits[f"{name}/{role}"] = hits
        if "head_pocket" in roles:
            residual_header = header.cut(roles["head_pocket"])
            if hits := _hits(
                roles["bolt_tool"], {"header_after_head_pocket": residual_header}
            ):
                driver_pocket_hits[f"{name}/bolt_tool"] = hits
        seat, axis = row["bolt_seat_xyz_mm"], row["bolt_axis_xyz"]
        tip_extension = _cylinder(
            _add(seat, axis, row["bolt_length_mm"] - WASHER_T),
            axis,
            BORE_TIP_CLEARANCE_MM,
            center.BORE_DIAMETER_MM,
        )
        row["tip_extension_unrelated_wood_hits_mm3"] = _hits(tip_extension, unrelated)
        row["tip_extension_protected_hits_mm3"] = {
            role: hits
            for role, hits in protected.hits(
                {"tip_extension": tip_extension}, fixed
            ).items()
            if hits
        }
        row["head_washer_inside_header_fraction"] = (
            {
                role: round(
                    protected._volume(roles[role], header) / roles[role].Volume(), 7
                )
                for role in ("head", "washer")
            }
            if row["entry_face"].startswith("header_")
            else None
        )
        for role, shape in roles.items():
            key = f"{name}/{role}"
            if role in ("shaft", "barrel", "washer", "head"):
                installed[key] = shape
                if hits := _hits(
                    shape, {n: wood[n] for n in replacement.POSTS if n not in allowed}
                ):
                    post_hits[key] = hits
            if hits := _hits(shape, retained):
                candidate_to_retained[key] = hits
    for (name_a, shape_a), (name_b, shape_b) in combinations(installed.items(), 2):
        if name_a.rsplit("/", 1)[0] == name_b.rsplit("/", 1)[0]:
            continue
        if (volume := protected._volume(shape_a, shape_b)) > TOL:
            pair_hits[f"{name_a}|{name_b}"] = round(volume, 6)
    for name, roles in checks.items():
        for role in ("bolt_tool", "barrel_tool"):
            if hits := _hits(
                roles[role],
                {
                    key: shape
                    for key, shape in installed.items()
                    if not key.startswith(name + "/")
                },
            ):
                access_hits[f"{name}/{role}"] = hits
    tools = {
        f"{name}/{role}": shapes[role]
        for name, shapes in checks.items()
        for role in ("bolt_tool", "barrel_tool")
    }
    for (name_a, shape_a), (name_b, shape_b) in combinations(tools.items(), 2):
        if name_a.rsplit("/", 1)[0] == name_b.rsplit("/", 1)[0]:
            continue
        if (volume := protected._volume(shape_a, shape_b)) > TOL:
            tool_pair_hits[f"{name_a}|{name_b}"] = round(volume, 6)
    all_clashes = bool(
        post_hits
        or pair_hits
        or access_hits
        or tool_pair_hits
        or candidate_to_retained
        or service_hits
        or driver_pocket_hits
    )
    all_clashes |= any(
        bolt["protected_hits_mm3"]
        or bolt["unrelated_wood_hits_mm3"]
        or bolt["joined_wood_bore_core_fraction"] < 0.999
        or bolt["tip_extension_in_receiver_fraction"] < 0.999
        or bolt["tip_extension_unrelated_wood_hits_mm3"]
        or bolt["tip_extension_protected_hits_mm3"]
        or bolt["barrel_body_in_host_fraction"] < 0.999
        or (
            bolt["head_washer_inside_header_fraction"] is not None
            and min(bolt["head_washer_inside_header_fraction"].values()) < 0.999
        )
        for station in reports.values()
        for bolt in station["bolts"].values()
    )
    return {
        "wood": wood,
        "service_voids": service_voids,
        "solids": checks,
        "report": {
            "schema": "owner_barrel_center_post_joint_replan/v1",
            "source": "kerf-right model, detached 4x6 proof, current barrel assembly",
            "stations": reports,
            "protected_counts": fixed["counts"],
            "fixed_center_kicker_screws_received": len(
                proof["report"]["center_kicker_screws"]
            ),
            "hardware_to_new_post_hits_mm3": post_hits,
            "installed_hardware_pair_hits_mm3": pair_hits,
            "tool_to_other_hardware_hits_mm3": access_hits,
            "tool_pair_hits_mm3": tool_pair_hits,
            "candidate_to_retained_hardware_hits_mm3": candidate_to_retained,
            "candidate_to_inherited_service_void_hits_mm3": service_hits,
            "driver_to_header_after_pocket_hits_mm3": driver_pocket_hits,
            "nominal_geometry_disposition": "CLASH"
            if all_clashes
            else "CLEAR_OCCUPANCY",
            "native_solve": False,
            "structural_capacity_verified": False,
            "release_flags": dict(RELEASE_FLAGS),
            "limits": "Nominal CAD only; angled counterbores, 19.05 mm washer lead, barrel thread/wood resistance, tolerances, tool withdrawal and assembly remain unqualified.",
        },
    }


def build_layout(wood):
    """Four-row adapter; the parent owns the unchanged two bottom-center rows."""
    trial = build(wood=wood)
    report, solids = trial["report"], trial["solids"]
    stations = {}
    for station, station_report in report["stations"].items():
        bolts, barrels, stacks, drilling, access = {}, {}, {}, {}, {}
        for name, row in station_report["bolts"].items():
            shapes = solids[name]
            bolt_name = f"{name}_bolt"
            seat, axis = tuple(row["bolt_seat_xyz_mm"]), tuple(row["bolt_axis_xyz"])
            hosts = (
                "base_header",
                f"base_post_center_{station.rsplit('_', 1)[1]}"
                if station_report["family"] == "post_header"
                else f"base_principal_center_{station.rsplit('_', 1)[1]}",
            )
            bolts[bolt_name] = Connection(
                bolt_name,
                cq.Vector(*_add(seat, axis, -WASHER_T)),
                cq.Vector(*axis),
                row["bolt_length_mm"],
                center.hardware.THREAD_MAJOR_MM,
                hosts,
                "bolt",
            )
            barrels[name] = shapes["barrel"]
            stacks[bolt_name] = {
                role: shapes[role] for role in ("shaft", "washer", "head")
            }
            drilling[f"{name}/bolt_bore"] = shapes["bolt_bore"]
            drilling[f"{name}/barrel_cross_bore"] = shapes["barrel_cross_bore"]
            if "head_pocket" in shapes:
                drilling[f"{name}/head_pocket"] = shapes["head_pocket"]
            access[f"{name}/bolt_tool"] = shapes["bolt_tool"]
            access[f"{name}/barrel_tool"] = shapes["barrel_tool"]
        stations[station] = {
            "mode": "direct",
            "axis_offset_mm": OFFSET,
            "disposition": "REVISE"
            if report["nominal_geometry_disposition"] == "CLASH"
            else "VIEWER_ONLY_UNVERIFIED",
            "bolts": bolts,
            "barrels": barrels,
            "stacks": stacks,
            "drilling_paths": drilling,
            "access_paths": access,
        }
    return {"stations": stations, "diagnostics": report}
