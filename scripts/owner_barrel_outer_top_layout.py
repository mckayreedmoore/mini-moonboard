"""Eight remaining owner duties: direct barrel bores or explicit open exceptions.

This detached viewer trial leaves original wood/66 panel axes/12 frame bolts
unchanged. Nominal retail dimensions are not a controlled drawing or strength.
"""

import json

import cadquery as cq

from mini_moonboard.box_frame import Connection
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger
from scripts.simple_rail_joint_comparison import N, T

SOURCE_ID = "owner-barrel-outer-top-kerf-right-v1"
FAMILIES = ("top_outer", "top_center", "header_outer_post", "base_outer_side")
MACHINE_BORE_D_MM = 7.5  # Provisional pilot/access screen, not drill release.
BARREL_BORE_D_MM = hardware.BARREL_OD_MM
TOL_MM3 = 1.0


def _point(x, t, n):
    return cq.Vector(x, t * T[0] + n * N[0], t * T[1] + n * N[1])


def _cylinder(start, direction, length, diameter):
    return cq.Solid.makeCylinder(diameter / 2, length, start, direction)


def _bounds(shape, direction):
    values = [v.Center().dot(direction) for v in shape.Vertices()]
    return min(values), max(values)


def _row(machine_start, machine_direction, axis, barrel_entry, barrel_direction, hosts):
    """A solid machine path must reach an actual intersecting barrel cross-bore."""
    axis_offset = hardware.BARREL_LENGTH_MM / 2
    from_entry = (axis - barrel_entry).dot(barrel_direction)
    recess = from_entry - axis_offset
    length = (axis - machine_start).dot(machine_direction)
    installed_reach = hardware.BOLT_LENGTH_MM - hardware.WASHER_THICKNESS_SENSITIVITY_MM
    machine = _cylinder(
        machine_start, machine_direction, installed_reach, MACHINE_BORE_D_MM
    )
    cross = _cylinder(
        barrel_entry,
        barrel_direction,
        recess + hardware.BARREL_LENGTH_MM,
        BARREL_BORE_D_MM,
    )
    body = _cylinder(
        barrel_entry + barrel_direction * recess,
        barrel_direction,
        hardware.BARREL_LENGTH_MM,
        BARREL_BORE_D_MM,
    )
    wood = [hosts[name] for name in hosts]
    machine_coverage = (
        sum(machine.intersect(part).Volume() for part in wood) / machine.Volume()
    )
    cross_coverage = (
        sum(cross.intersect(part).Volume() for part in wood) / cross.Volume()
    )
    return {
        "machine_bore_meets_barrel_bore": machine.intersect(body).Volume() > TOL_MM3,
        "source_wood_bore_coverage": round(min(machine_coverage, cross_coverage), 6),
        "machine_path_to_axis_mm": round(length, 4),
        "nominal_full_machine_bore_depth_mm": round(installed_reach, 4),
        "nominal_tip_beyond_axis_mm": round(installed_reach - length, 4),
        "barrel_recess_mm": round(recess, 4),
        "barrel_cross_bore_depth_mm": round(recess + hardware.BARREL_LENGTH_MM, 4),
        "axis_xyz_mm": [round(v, 4) for v in axis.toTuple()],
        "machine_start_xyz_mm": [round(v, 4) for v in machine_start.toTuple()],
        "barrel_entry_xyz_mm": [round(v, 4) for v in barrel_entry.toTuple()],
    }


def _top_outer(side, wood):
    left = side == "left"
    side_name = f"base_side_{side}"
    rail = wood["base_rail_top"]
    upright = wood[side_name]
    sb, rb = upright.BoundingBox(), rail.BoundingBox()
    butt = rb.xmin if left else rb.xmax
    outer = sb.xmin if left else sb.xmax
    direction = cq.Vector(1 if left else -1, 0, 0)
    t0, t1 = _bounds(rail, cq.Vector(0, *T))
    tmid = (t0 + t1) / 2
    # 30 mm receiver end distance keeps the 5-in trial bolt in range; its
    # grain-end/edge resistance and complete installed thread remain open.
    x = butt + (30 if left else -30)
    return [
        _row(
            _point(outer, tmid, n),
            direction,
            _point(x, tmid, n),
            _point(x, t0, n),
            cq.Vector(0, *T),
            {side_name: upright, "base_rail_top": rail},
        )
        for n in (265.0, 310.0)
    ]


def _top_center(side, wood):
    name = f"base_principal_center_{side}"
    principal, rail = wood[name], wood["base_rail_top"]
    pb = principal.BoundingBox()
    xmid = (pb.xmin + pb.xmax) / 2
    t0, t1 = _bounds(rail, cq.Vector(0, *T))
    t_axis = t0 - 70.0
    entry_x = pb.xmin if side == "left" else pb.xmax
    cross_dir = cq.Vector(1 if side == "left" else -1, 0, 0)
    return [
        _row(
            _point(xmid, t1, n),
            cq.Vector(0, -T[0], -T[1]),
            _point(xmid, t_axis, n),
            _point(entry_x, t_axis, n),
            cross_dir,
            {"base_rail_top": rail, name: principal},
        )
        for n in (265.0, 310.0)
    ]


def _header_outer(side, wood):
    name = f"base_post_outer_{side}"
    post, header = wood[name], wood["base_header"]
    pb, hb = post.BoundingBox(), header.BoundingBox()
    xmid = (pb.xmin + pb.xmax) / 2
    entry_x = pb.xmin if side == "left" else pb.xmax
    cross_dir = cq.Vector(1 if side == "left" else -1, 0, 0)
    return [
        _row(
            cq.Vector(xmid, y, hb.zmax),
            cq.Vector(0, 0, -1),
            cq.Vector(xmid, y, pb.zmax - 70),
            cq.Vector(entry_x, y, pb.zmax - 70),
            cross_dir,
            {"base_header": header, name: post},
        )
        for y in (-135.0, -75.0)
    ]


def _base_outer(side, wood):
    name = f"base_side_{side}"
    rim, header = wood[name], wood["base_header"]
    rb, hb = rim.BoundingBox(), header.BoundingBox()
    xmid = (rb.xmin + rb.xmax) / 2
    entry_x = rb.xmin if side == "left" else rb.xmax
    cross_dir = cq.Vector(1 if side == "left" else -1, 0, 0)
    return [
        _row(
            cq.Vector(xmid, y, hb.zmin),
            cq.Vector(0, 0, 1),
            cq.Vector(xmid, y, rb.zmin + 70),
            cq.Vector(entry_x, y, rb.zmin + 70),
            cross_dir,
            {"base_header": header, name: rim},
        )
        for y in (-135.0, -75.0)
    ]


def screen():
    module = variant(KERF_RIGHT)
    wood = {part.name: part.shape for part in module.uncut_wood_parts()}
    duties = ledger.selected_duties()
    target = {name: duty for name, duty in duties.items() if duty["family"] in FAMILIES}
    if len(target) != 8:
        raise ValueError("Eight selected outer/top duties changed")
    panel = module.panel_connections()
    frame = [row for row in module.connections() if row.kind == "bolt"]
    if len(panel) != 66 or len(frame) != 12:
        raise ValueError("Fixed source connection inventory changed")
    builders = {
        "top_outer": _top_outer,
        "top_center": _top_center,
        "header_outer_post": _header_outer,
        "base_outer_side": _base_outer,
    }
    grain = {
        "top_outer": "inclined side rim: N; top rail: X",
        "top_center": "inclined center principal: N; top rail: X",
        "header_outer_post": "outer post: Z; header: X",
        "base_outer_side": "inclined side rim: N; header: X",
    }
    stations = {}
    for name, duty in target.items():
        rows = builders[duty["family"]](duty["side"], wood)
        geometry = all(
            row["machine_bore_meets_barrel_bore"]
            and row["source_wood_bore_coverage"] >= 0.999
            and row["nominal_tip_beyond_axis_mm"] >= 0
            and row["barrel_recess_mm"] >= 0
            for row in rows
        )
        # Outer base also competes with the PB09 bottom-outer tools and the
        # outer header detail. Direct source wood coverage alone is insufficient.
        conflicting_family = duty["family"] == "base_outer_side"
        mode = "direct" if geometry and not conflicting_family else "exception"
        stations[name] = {
            "family": duty["family"],
            "side": duty["side"],
            "source_members": list(duty["timber"]),
            "grain": grain[duty["family"]],
            "mode": mode,
            "rows": rows,
            "machine_bore_meets_barrel_bore": all(
                row["machine_bore_meets_barrel_bore"] for row in rows
            ),
            "source_wood_bore_coverage": min(
                row["source_wood_bore_coverage"] for row in rows
            ),
            "complete_replacement": False,
            "blocker": (
                "PB09 bottom-outer tools / outer-header 3D compatibility unverified"
                if conflicting_family
                else "Nominal source timber coverage, bolt reach, or barrel recess fails"
                if not geometry
                else None
            ),
        }
    direct = sum(row["mode"] == "direct" for row in stations.values())
    return {
        "source_id": SOURCE_ID,
        "width_option": KERF_RIGHT,
        "source_axes": {"panel": len(panel), "frame_bolt": len(frame)},
        "provisional_hardware": {
            "barrel": "Hillman 880543 nominal retail identity only",
            "bolt": "Everbilt 800676 nominal 1/4-20 x 5 in",
            "barrel_length_mm": hardware.BARREL_LENGTH_MM,
            "barrel_od_mm": hardware.BARREL_OD_MM,
            "thread_major_mm": hardware.THREAD_MAJOR_MM,
            "axis_offset_mm": hardware.BARREL_LENGTH_MM / 2,
            "axis_offset_sensitivity_mm": list(hardware.AXIS_OFFSET_SENSITIVITY_MM),
            "bolt_length_mm": hardware.BOLT_LENGTH_MM,
            "washer_thickness_mm": hardware.WASHER_THICKNESS_SENSITIVITY_MM,
        },
        "stations": stations,
        "direct_count": direct,
        "exception_count": 8 - direct,
        "no_legacy_angle_placeholder": True,
        "protected_3d_checked": False,
        "nominal_tool_checked": False,
        "complete_thread_engagement_checked": False,
        "fit_qualified": False,
        "strength_qualified": False,
        "drilling_released": False,
    }


def viewer_solids(result=None):
    """Detached uncut nominal hardware and bore cutters for all eight trials.

    Exception shapes are diagnostic too; these are not installed fit evidence.
    """
    result = screen() if result is None else result
    hardware_solids, bore_cutters = {}, {}
    for station, data in result["stations"].items():
        for index, row in enumerate(data["rows"], 1):
            prefix = f"barrel_trial_{station}_{index}"
            start = cq.Vector(*row["machine_start_xyz_mm"])
            axis = cq.Vector(*row["axis_xyz_mm"])
            entry = cq.Vector(*row["barrel_entry_xyz_mm"])
            bolt_direction = (axis - start).normalized()
            barrel_direction = (axis - entry).normalized()
            body_start = entry + barrel_direction * row["barrel_recess_mm"]
            hardware_solids[f"{prefix}_bolt_shaft"] = _cylinder(
                start,
                bolt_direction,
                row["nominal_full_machine_bore_depth_mm"],
                hardware.THREAD_MAJOR_MM,
            )
            hardware_solids[f"{prefix}_barrel_body"] = _cylinder(
                body_start,
                barrel_direction,
                hardware.BARREL_LENGTH_MM,
                hardware.BARREL_OD_MM,
            )
            bore_cutters[f"{prefix}_machine_bore"] = _cylinder(
                start,
                bolt_direction,
                row["nominal_full_machine_bore_depth_mm"],
                MACHINE_BORE_D_MM,
            )
            bore_cutters[f"{prefix}_barrel_cross_bore"] = _cylinder(
                entry,
                barrel_direction,
                row["barrel_cross_bore_depth_mm"],
                BARREL_BORE_D_MM,
            )
    return {"hardware": hardware_solids, "bore_cutters": bore_cutters}


def build_layout(wood):
    """Give the integrated viewer actual nominal geometry; every row is REVISE.

    The two outer-base rows are direct-bore *leads*, not approved fit: their
    competing PB09/header tools remain unresolved. There is no fake block.
    """
    duties = ledger.selected_duties()
    builders = {
        "top_outer": _top_outer,
        "top_center": _top_center,
        "header_outer_post": _header_outer,
        "base_outer_side": _base_outer,
    }
    stations = {}
    for station, duty in duties.items():
        if duty["family"] not in FAMILIES:
            continue
        for member in duty["timber"]:
            if member not in wood:
                raise ValueError(f"{station}: missing selected source timber {member}")
        rows = builders[duty["family"]](duty["side"], wood)
        bolts, barrels, stacks, drilling, access = {}, {}, {}, {}, {}
        for index, row in enumerate(rows, 1):
            if (
                not row["machine_bore_meets_barrel_bore"]
                or row["source_wood_bore_coverage"] < 0.999
                or row["barrel_recess_mm"] < 0
                or row["nominal_tip_beyond_axis_mm"] < 0
            ):
                raise ValueError(
                    f"{station}: direct source bore is geometrically blocked"
                )
            name = f"barrel_trial_{station}_{index}"
            bolt_name = f"{name}_bolt"
            start = cq.Vector(*row["machine_start_xyz_mm"])
            axis = cq.Vector(*row["axis_xyz_mm"])
            entry = cq.Vector(*row["barrel_entry_xyz_mm"])
            bolt_dir = (axis - start).normalized()
            barrel_dir = (axis - entry).normalized()
            shaft_start = start - bolt_dir * hardware.WASHER_THICKNESS_SENSITIVITY_MM
            bolts[bolt_name] = Connection(
                bolt_name,
                shaft_start,
                bolt_dir,
                hardware.BOLT_LENGTH_MM,
                hardware.THREAD_MAJOR_MM,
                duty["timber"],
                "bolt",
            )
            barrels[name] = _cylinder(
                entry + barrel_dir * row["barrel_recess_mm"],
                barrel_dir,
                hardware.BARREL_LENGTH_MM,
                hardware.BARREL_OD_MM,
            )
            stacks[bolt_name] = {
                "shaft": _cylinder(
                    shaft_start,
                    bolt_dir,
                    hardware.BOLT_LENGTH_MM,
                    hardware.THREAD_MAJOR_MM,
                )
            }
            drilling[f"{name}/machine_bore"] = _cylinder(
                start,
                bolt_dir,
                row["nominal_full_machine_bore_depth_mm"],
                MACHINE_BORE_D_MM,
            )
            drilling[f"{name}/barrel_bore"] = _cylinder(
                entry,
                barrel_dir,
                row["barrel_cross_bore_depth_mm"],
                BARREL_BORE_D_MM,
            )
            access[f"{name}/bolt_access"] = _cylinder(
                start,
                -bolt_dir,
                40.0,
                20.0,
            )
            access[f"{name}/barrel_access"] = _cylinder(
                entry,
                -barrel_dir,
                40.0,
                20.0,
            )
        stations[station] = {
            "mode": "direct",
            "compact_alternate_block": None,
            "axis_offset_mm": hardware.BARREL_LENGTH_MM / 2,
            "disposition": "REVISE",
            "bolts": bolts,
            "barrels": barrels,
            "stacks": stacks,
            "drilling_paths": drilling,
            "access_paths": access,
        }
    if len(stations) != 8:
        raise ValueError("Missing outer/top owner duty in viewer")
    return {
        "stations": stations,
        "diagnostics": {
            "source_id": SOURCE_ID,
            "disposition": "REVISE",
            "limits": (
                "All eight have diagnostic nominal direct-bore shapes. Outer-base "
                "pair is a held exception pending PB09/header clearance. Shaft-only "
                "stacks; washer/head, thread, tools, protected solids and strength open."
            ),
        },
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
