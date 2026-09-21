"""Four direct center-header corner duties in the approved post pose; layout only."""

import json
import math
from functools import lru_cache

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as owner
from scripts import owner_layout_protected as protected
from scripts import simple_pb03_lower_center_pair as joints

STATIONS = (
    "clip_split_header_center_left",
    "clip_split_header_center_right",
    "clip_split_base_center_left",
    "clip_split_base_center_right",
)
POST_BLOCK_Y = (-150.3, -61.4)
POST_BLOCK_Z = (99.2, 238.9)
PRINCIPAL_BLOCK_Y = (-175.7, -114.0)
PRINCIPAL_BLOCK_Z = (277.0, 416.7)
BLOCK_X_MM = 139.7
BORE_RADIUS_MM = joints.BORE_DIAMETER_MM / 2
SOURCE = variant(KERF_RIGHT)


def _box(x0, x1, y, z):
    return cq.Solid.makeBox(
        x1 - x0, y[1] - y[0], z[1] - z[0], cq.Vector(x0, y[0], z[0])
    )


def _hits(shape, obstacles):
    return {
        name: round(volume, 6)
        for name, other in obstacles.items()
        if (volume := protected._volume(shape, other)) > protected.HIT_TOL_MM3
    }


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _candidate(side, family, wood):
    """Use the old bracket side of each member and a direct header face."""
    host_name = f"base_{'post' if family == 'post' else 'principal'}_center_{side}"
    host = wood[host_name]
    header = wood["base_header"]
    hb, bb = host.BoundingBox(), header.BoundingBox()
    lower = family == "post"
    y_range = POST_BLOCK_Y if lower else PRINCIPAL_BLOCK_Y
    z_range = POST_BLOCK_Z if lower else PRINCIPAL_BLOCK_Z
    if abs((hb.zmax if lower else hb.zmin) - (bb.zmin if lower else bb.zmax)) > 1e-6:
        raise ValueError(f"{host_name}: direct header meeting face changed")
    outward = 1 if side == "right" else -1
    contact_x = hb.xmax if outward == 1 else hb.xmin
    x0 = contact_x if outward == 1 else contact_x - BLOCK_X_MM
    block_name = f"owner_center_{family}_{side}_block"
    block = _box(x0, x0 + BLOCK_X_MM, y_range, z_range)
    specs = []
    if lower:
        cross_yz = ((-125.0, 150.0), (-125.0, 200.0))
        vertical_xy = tuple(
            (contact_x + outward * offset, -100.0) for offset in (60.0, 95.0)
        )
    else:
        # Rearward of the fixed bottom rail; do not remove or notch that rail.
        cross_yz = ((-150.0, 300.0), (-126.8, 332.0))
        vertical_xy = (
            (outward * 116.0, -162.0),
            (outward * 136.0, -135.0),
        )
    start_x = hb.xmin if outward == 1 else hb.xmax
    for number, (y, z) in enumerate(cross_yz, 1):
        specs.append(
            (
                f"owner_center_{family}_{side}_cross_{number}",
                (start_x, y, z),
                (outward, 0, 0),
                hb.xlen + BLOCK_X_MM,
                (host_name, block_name),
            )
        )
    for number, (x, y) in enumerate(vertical_xy, 1):
        start_z = z_range[0] if lower else bb.zmin
        specs.append(
            (
                f"owner_center_{family}_{side}_header_{number}",
                (x, y, start_z),
                (0, 0, 1),
                z_range[1] - z_range[0] + bb.zlen,
                (block_name, "base_header") if lower else ("base_header", block_name),
            )
        )
    bolts, bores, stacks, tools, coverage = [], {}, {}, {}, {}
    hosts = {host_name: host, "base_header": header, block_name: block}
    for name, start, direction, grip, members in specs:
        bolt, stack, bore, access = joints._stack(name, start, direction, grip, members)
        bolts.append(bolt)
        bores[name], stacks[name], tools[name] = bore, stack, access
        core = cq.Solid.makeCylinder(
            BORE_RADIUS_MM,
            grip,
            bolt.start + bolt.direction.normalized() * joints.END_ALLOWANCE_MM,
            bolt.direction,
        )
        coverage[name] = {
            member: round(protected._volume(core, hosts[member]) / core.Volume(), 7)
            for member in members
        }
    contact = {
        "host": joints._contact_area(block, host, (-outward, 0, 0)),
        "header": joints._contact_area(block, header, (0, 0, 1 if lower else -1)),
    }
    return {
        "host_name": host_name,
        "block_name": block_name,
        "block": block,
        "bolts": tuple(bolts),
        "bores": bores,
        "stacks": stacks,
        "tools": tools,
        "coverage": coverage,
        "contact": contact,
        "bounds": [x0, x0 + BLOCK_X_MM, *y_range, *z_range],
    }


@lru_cache(maxsize=1)
def screen():
    """Report exact nominal fit and all stop gates without changing source CAD."""
    layout = owner.build_layout()
    if (
        layout["post_bounds_x_mm"]
        != {"left": [-199.05, -160.95], "right": [160.95, 199.05]}
        or layout["backer_frame_attachment_qualified"]
    ):
        raise ValueError("Approved ±180 mm post/backer source changed")
    wood = {part.name: part.shape for part in SOURCE.uncut_wood_parts()}
    original = dict(wood)
    for side in ("left", "right"):
        name = f"base_post_center_{side}"
        wood[name] = original[name].translate(
            cq.Vector(layout["post_shift_x_mm"][side], 0, 0)
        )
        x0, x1 = layout["backer_bounds_x_mm"][side]
        wood[f"inner_kicker_backer_{side}"] = _box(
            x0,
            x1,
            (owner.BACKER_REAR_Y_MM, owner.BACKER_FRONT_Y_MM),
            (0.0, owner.BACKER_TOP_Z_MM),
        )
    rows = {
        f"clip_split_{'header' if family == 'post' else 'base'}_center_{side}": _candidate(
            side, family, wood
        )
        for side in ("left", "right")
        for family in ("post", "principal")
    }
    if set(rows) != set(STATIONS):
        raise ValueError("Four center-header duty identities changed")
    old_stations = {row[0]: row for row in SOURCE.stations()}
    for station, row in rows.items():
        side = station.rsplit("_", 1)[1]
        old = old_stations.get(station)
        if (
            old is None
            or old[4:] != ("base_header", row["host_name"])
            or old[2].x != (1.0 if side == "right" else -1.0)
        ):
            raise ValueError(f"{station}: original bracket-duty side changed")
    source_connections = tuple(SOURCE.connections())
    target_prefixes = tuple(f"{station}_" for station in STATIONS)
    removed = tuple(
        row for row in source_connections if row.name.startswith(target_prefixes)
    )
    retained = tuple(row for row in source_connections if row not in removed)
    source_panels = tuple(
        row for row in source_connections if row.name in layout["fixed_panel_axes"]
    )
    frame = tuple(row for row in source_connections if row.kind == "bolt")
    new_bolts = tuple(bolt for row in rows.values() for bolt in row["bolts"])
    proposed = (*retained, *new_bolts)
    if len(removed) != 24 or len(source_panels) != 66 or len(frame) != 12:
        raise ValueError("Original target or fixed connection inventory changed")
    source_preserved = (
        all(row.kind == "screw" for row in removed)
        and tuple(row for row in proposed if row.name in layout["fixed_panel_axes"])
        == source_panels
        and tuple(
            row
            for row in proposed
            if row.kind == "bolt" and row.name in {f.name for f in frame}
        )
        == frame
        and not any(row.name.startswith(target_prefixes) for row in proposed)
        and all(
            original[name].distance(wood[name]) <= 1e-8
            for name in original
            if not name.startswith("base_post_center_")
        )
    )
    all_parts = {part.name: part.shape for part in SOURCE.parts()}
    retained_angles = {
        name: shape
        for name, shape in all_parts.items()
        if name.startswith("clip_") and name not in STATIONS
    }
    retained_sds = {
        row.name: _axis(row) for row in retained if row.name.startswith("clip_")
    }
    service = protected.inventory()
    if (
        service["counts"]["panel_screws"] != 66
        or service["counts"]["frame_bolts"] != 12
    ):
        raise ValueError("Protected fixed hardware inventory changed")
    reports, obstructions = {}, {}
    for station, row in rows.items():
        intended = {row["host_name"], "base_header", row["block_name"]}
        other_wood = {
            name: shape for name, shape in wood.items() if name not in intended
        }
        other_blocks = {
            trial["block_name"]: trial["block"]
            for name, trial in rows.items()
            if name != station
        }
        fixed = {**other_wood, **other_blocks, **retained_angles, **retained_sds}
        block_hits = _hits(row["block"], fixed)
        features = {f"block/{station}": row["block"]}
        hits = {"block_to_unrelated": block_hits}
        for bolt in row["bolts"]:
            name = bolt.name
            nonhost = {
                key: shape for key, shape in fixed.items() if key not in bolt.members
            }
            other_installed = {
                f"{other}/{role}": shape
                for other, stack in row["stacks"].items()
                if other != name
                for role, shape in stack.items()
                if role != "shaft"
            }
            hits[f"bore/{name}"] = _hits(row["bores"][name], nonhost)
            features[f"bore/{name}"] = row["bores"][name]
            for role, shape in row["stacks"][name].items():
                if role != "shaft":
                    hits[f"stack/{name}/{role}"] = _hits(shape, nonhost)
                    hits[f"stack_to_other_installed/{name}/{role}"] = _hits(
                        shape, other_installed
                    )
                    features[f"stack/{name}/{role}"] = shape
            for end, shape in row["tools"][name].items():
                hits[f"tool/{name}/{end}"] = _hits(shape, nonhost)
                hits[f"tool_to_other_installed/{name}/{end}"] = _hits(
                    shape, other_installed
                )
                hits[f"tool_host/{name}/{end}"] = _hits(
                    shape,
                    {
                        key: wood[key] if key in wood else row["block"]
                        for key in intended
                    },
                )
                features[f"tool/{name}/{end}"] = shape
        hits["same_station_bores"] = joints._bore_pair_hits(row["bores"])
        protected_hits = {
            name: families
            for name, families in protected.hits(features, service).items()
            if families
        }
        hits["protected_3d"] = protected_hits
        incomplete = {
            name: fractions
            for name, fractions in row["coverage"].items()
            if not all(value > 0 for value in fractions.values())
            or abs(sum(fractions.values()) - 1.0) > 1e-5
        }
        if incomplete:
            hits["incomplete_core_bores"] = incomplete
        if not all(value > 0 for value in row["contact"].values()):
            hits["missing_contact"] = row["contact"]
        blocking = {kind: value for kind, value in hits.items() if value}
        if blocking:
            obstructions[station] = blocking
        reports[station] = {
            "members": ["base_header", row["host_name"]],
            "block_bounds_xyz_mm": row["bounds"],
            "post_or_principal_contact_mm2": round(row["contact"]["host"], 6),
            "header_contact_mm2": round(row["contact"]["header"], 6),
            "bore_coverage": row["coverage"],
            "bolt_grips_mm": {bolt.name: bolt.grip for bolt in row["bolts"]},
        }
    # The two backers are receivers only. A header touch cannot be credited as fastening.
    decision = "REVISE_LAYOUT" if obstructions else "LAYOUT_ONLY_CLEAR"
    bottom_rail_ymin = min(
        wood[f"base_rail_bottom_{side}"].BoundingBox().ymin
        for side in ("left", "right")
    )
    nominal_reserves = {
        "principal_block_to_bottom_rail_y_envelope_mm": bottom_rail_ymin
        - PRINCIPAL_BLOCK_Y[1],
        "principal_cross_bore_to_header_tool_mm": 300.0
        - joints.TOOL_DIAMETER_MM / 2
        - wood["base_header"].BoundingBox().zmax,
        "principal_cross_to_vertical_bore_wall_mm": abs(-126.8 - -135.0)
        - joints.BORE_DIAMETER_MM,
        "principal_vertical_tool_to_other_washer_mm": math.hypot(20.0, 27.0)
        - (joints.TOOL_DIAMETER_MM + joints.WASHER_DIAMETER_MM) / 2,
        "principal_vertical_rear_washer_edge_mm": -162.0
        - joints.WASHER_DIAMETER_MM / 2
        - PRINCIPAL_BLOCK_Y[0],
    }
    return {
        "schema": "owner_layout_center_header_four/v1",
        "post_centers_x_mm": {"left": -180.0, "right": 180.0},
        "stations": reports,
        "inventory": {
            "candidate_blocks": 4,
            "candidate_bolts": len(new_bolts),
            "removed_target_sds_axes": len(removed),
            "retained_legacy_sds_axes": len(retained_sds),
            "fixed_panel_kicker_axes": len(source_panels),
            "retained_frame_bolt_axes": len(frame),
            **service["counts"],
        },
        "direct_paths": {
            f"header_to_{family}_{side}": [
                "base_header",
                f"base_{'post' if family == 'post' else 'principal'}_center_{side}",
            ]
            for side in ("left", "right")
            for family in ("post", "principal")
        },
        "source_preserved": source_preserved,
        "backers_receive_four_fixed_kicker_screws": len(layout["center_kicker_screws"])
        == 4
        and all(
            row["full_shaft_received"]
            for row in layout["center_kicker_screws"].values()
        ),
        "backer_frame_attachment_qualified": False,
        "pb02_rear_return_chain_used": False,
        "exact_obstructions": obstructions,
        "selected_nominal_reserves_mm": {
            name: round(value, 6) for name, value in nominal_reserves.items()
        },
        "needed_owner_exception": (
            "One or more listed original-member or protected-envelope collisions require owner layout direction; no member was changed."
            if obstructions
            else None
        ),
        "protected_limits": {
            "trial_hold_projection_mm": service["hold_rear_projection_mm"],
            "delivered_hold_bolt_lengths_verified": False,
            "wiring_bend_and_clearance_verified": False,
            "fastener_head_and_driver_clearance_verified": False,
        },
        "decision": decision,
        "native_solve": False,
        "strength_checked": False,
        "drilling_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    result = screen()
    print(json.dumps(result, indent=2, sort_keys=True))
