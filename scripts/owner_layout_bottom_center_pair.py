"""Detached same-side bottom-center pair; owner layout only, no release."""

import json
import math
from functools import lru_cache

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import owner_layout_protected as protected
from scripts import simple_pb03_lower_center_pair as joints
from scripts import simple_rail_joint_comparison as basis
from scripts.simple_center_pb02_geometry import FRONT_Y as PB02_SIDE_FRONT_Y
from scripts.simple_center_side_depth_y_probe import SIDE_REAR_Y

STATIONS = (
    "clip_horizontal_bottom_left_2",
    "clip_horizontal_bottom_right_1",
)
SOURCE_ID = "owner-bottom-center-pair-x180-139p7-layout-v1"
BLOCK_X_MM = 139.7
BLOCK_T_MM = 57.15
BLOCK_N_MM = 139.7
UPRIGHT_N_MM = (50.0, 89.7)
RAIL_X_MM = (50.0, 85.0)
RAIL_N_MM = 69.85
PROTECTED_3D_GATES = (
    "delivered_hold_bolt_length",
    "wiring_bend_radius_and_routing",
    "purchased_66_panel_screw_full_lengths",
    "panel_screw_heads_and_driver_access",
    "frame_bolt_heads_nuts_and_tool_access",
    "candidate_delivered_bolt_lengths_and_tools",
    "retained_brackets_and_sds_installed_solids",
    "whole_frame_corner_block_interactions",
)


def _local_range(shape, axis):
    vector = basis.T if axis == "t" else basis.N
    values = [v.Y * vector[0] + v.Z * vector[1] for v in shape.Vertices()]
    return min(values), max(values)


def _hits(shape, obstacles):
    return {
        name: round(volume, 6)
        for name, other in obstacles.items()
        if (volume := joints._intersection_volume(shape, other)) > joints.TOL_MM3
    }


def _station(
    name,
    wood,
    block_x_mm=BLOCK_X_MM,
    rail_x_mm=RAIL_X_MM,
    *,
    block_side="front",
    block_n_min_mm=None,
    rail_n_offset_mm=RAIL_N_MM,
):
    side = "left" if "_left_" in name else "right"
    principal_name = f"base_principal_center_{side}"
    rail_name = f"base_rail_bottom_{side}"
    principal, rail = wood[principal_name], wood[rail_name]
    pb, rb = principal.BoundingBox(), rail.BoundingBox()
    extension = -1 if side == "left" else 1
    butt = pb.xmin if extension < 0 else pb.xmax
    rail_butt = rb.xmax if extension < 0 else rb.xmin
    if abs(butt - rail_butt) > 1e-6:
        raise ValueError(f"{name}: original same-side rail/principal butt changed")
    x0 = butt - block_x_mm if extension < 0 else butt
    t_rear, t_front = _local_range(rail, "t")
    n_low, n_high = _local_range(rail, "n")
    if abs(n_high - n_low - BLOCK_N_MM) > 1e-5:
        raise ValueError(f"{name}: original bottom rail N depth changed")
    if block_side not in ("front", "rear"):
        raise ValueError(f"{name}: unsupported block side {block_side}")
    block_t_start = t_front if block_side == "front" else t_rear - BLOCK_T_MM
    block_n_start = n_low if block_n_min_mm is None else block_n_min_mm
    y0, z0 = basis._yz(block_t_start, block_n_start)
    block = (
        cq.Solid.makeBox(block_x_mm, BLOCK_T_MM, BLOCK_N_MM, cq.Vector(x0, 0, 0))
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, y0, z0))
    )
    prefix = f"owner_bottom_{side}"
    specs = []
    for index, offset in enumerate(UPRIGHT_N_MM, 1):
        y, z = basis._yz(block_t_start + BLOCK_T_MM / 2, block_n_start + offset)
        specs.append(
            (
                f"{prefix}_principal_{index}",
                (pb.xmax if extension < 0 else pb.xmin, y, z),
                (float(extension), 0.0, 0.0),
                pb.xlen + block_x_mm,
                (principal_name, f"{prefix}_block"),
                {principal_name: pb.xlen, f"{prefix}_block": block_x_mm},
            )
        )
    for index, offset in enumerate(rail_x_mm, 1):
        x = rail_butt + extension * offset
        rail_start_t = t_rear if block_side == "front" else block_t_start
        y, z = basis._yz(rail_start_t, n_low + rail_n_offset_mm)
        rail_members = (
            (rail_name, f"{prefix}_block")
            if block_side == "front"
            else (f"{prefix}_block", rail_name)
        )
        specs.append(
            (
                f"{prefix}_rail_{index}",
                (x, y, z),
                (0.0, *basis.T),
                38.1 + BLOCK_T_MM,
                rail_members,
                {rail_name: 38.1, f"{prefix}_block": BLOCK_T_MM},
            )
        )
    bolts, bores, stacks, tools, complete, fractions = [], {}, {}, {}, {}, {}
    hosts = {principal_name: principal, rail_name: rail, f"{prefix}_block": block}
    for bolt_name, start, axis, grip, members, lengths in specs:
        bolt, stack, bore, access = joints._stack(bolt_name, start, axis, grip, members)
        bolts.append(bolt)
        bores[bolt_name], stacks[bolt_name], tools[bolt_name] = bore, stack, access
        fractions[bolt_name] = {
            member: bore.intersect(hosts[member]).Volume()
            / (math.pi * (joints.BORE_DIAMETER_MM / 2) ** 2 * length)
            for member, length in lengths.items()
        }
        complete[bolt_name] = all(
            abs(value - 1) < 0.001 for value in fractions[bolt_name].values()
        )
    return {
        "side": side,
        "principal_name": principal_name,
        "rail_name": rail_name,
        "block": block,
        "bolts": bolts,
        "bores": bores,
        "stacks": stacks,
        "tools": tools,
        "complete": complete,
        "fractions": fractions,
        "contact": {
            "principal": joints._contact_area(block, principal, (-extension, 0, 0)),
            "rail": joints._contact_area(
                block,
                rail,
                (0, -basis.T[0], -basis.T[1])
                if block_side == "front"
                else (0, basis.T[0], basis.T[1]),
            ),
        },
        "local_n_bounds": (block_n_start, block_n_start + BLOCK_N_MM),
        "local_t_bounds": (block_t_start, block_t_start + BLOCK_T_MM),
    }


@lru_cache(maxsize=3)
def screen_variant(
    source_id=SOURCE_ID,
    block_x_mm=BLOCK_X_MM,
    rail_x_mm=RAIL_X_MM,
    *,
    block_side="front",
    block_n_min_mm=None,
    rail_n_offset_mm=RAIL_N_MM,
    include_pb02_side_cleat=True,
):
    """Screen two candidate corners without altering any historical source."""
    module = variant(KERF_RIGHT)
    wood_names = {part.name for part in module.uncut_wood_parts()}
    # Conservative maintained solids still carry old target SDS voids; do not
    # pass a new bore merely because an uncut rectangular blank covers it.
    wood = {part.name: part.shape for part in module.parts() if part.name in wood_names}
    if set(wood) != wood_names:
        raise ValueError("Kerf-right finished timber inventory changed")
    stations = {row[0]: row for row in module.stations()}
    connections = tuple(module.connections())
    panel = tuple(module.panel_connections())
    frame = tuple(row for row in connections if row.kind == "bolt")
    target = tuple(
        row
        for row in connections
        if row.name.startswith(tuple(name + "_" for name in STATIONS))
    )
    other = tuple(
        row for row in connections if row.name.startswith("clip_") and row not in target
    )
    if (
        len(panel) != 66
        or len(frame) != 12
        or len(target) != 12
        or len(other) != 132
        or any(
            stations[name][4:]
            != (f"base_rail_bottom_{side}", f"base_principal_center_{side}")
            for name, side in zip(STATIONS, ("left", "right"), strict=True)
        )
    ):
        raise ValueError("Original bottom-center duties or protected axes changed")
    for side, sign in (("left", -1), ("right", 1)):
        wood[f"base_post_center_{side}"] = wood[f"base_post_center_{side}"].translate(
            cq.Vector(sign * 110, 0, 0)
        )
    layout = posts.build_layout()
    if layout["post_bounds_x_mm"] != {
        "left": [-199.05, -160.95],
        "right": [160.95, 199.05],
    }:
        raise ValueError("Approved ±180 mm post context changed")
    for side, (x0, x1) in layout["backer_bounds_x_mm"].items():
        wood[f"inner_kicker_backer_{side}"] = cq.Solid.makeBox(
            x1 - x0,
            posts.BACKER_FRONT_Y_MM - posts.BACKER_REAR_Y_MM,
            posts.BACKER_TOP_Z_MM,
            cq.Vector(x0, posts.BACKER_REAR_Y_MM, 0),
        )
    right_side_cleat = None
    if include_pb02_side_cleat:
        # Historical partial candidate only; absent from the unified 24 duties.
        right_side_cleat = cq.Solid.makeBox(
            88.9,
            PB02_SIDE_FRONT_Y - SIDE_REAR_Y,
            183,
            cq.Vector(89.05, SIDE_REAR_Y, 277),
        )
        wood["upright_side_cleat"] = right_side_cleat
    pair = {
        name: _station(
            name,
            wood,
            block_x_mm,
            rail_x_mm,
            block_side=block_side,
            block_n_min_mm=block_n_min_mm,
            rail_n_offset_mm=rail_n_offset_mm,
        )
        for name in STATIONS
    }
    protected_inventory = protected.inventory()
    finite = protected_inventory["counts"]
    if finite["panel_screws"] != len(panel) or finite["frame_bolts"] != len(frame):
        raise ValueError("Finite protected source axes changed")
    reports = {}
    blocked = {}
    finite_hits = {}
    for name, row in pair.items():
        protected_wood = {
            part: shape
            for part, shape in wood.items()
            if part not in (row["principal_name"], row["rail_name"])
        }
        protected_wood.update(
            {
                f"other_block/{other}": other_row["block"]
                for other, other_row in pair.items()
                if other != name
            }
        )
        other_timber_hits = _hits(row["block"], protected_wood)
        features = {"block": row["block"]}
        for bolt in row["bolts"]:
            features[f"bore/{bolt.name}"] = row["bores"][bolt.name]
            features.update(
                {
                    f"stack/{bolt.name}/{role}": solid
                    for role, solid in row["stacks"][bolt.name].items()
                }
            )
            features.update(
                {
                    f"tool/{bolt.name}/{end}": solid
                    for end, solid in row["tools"][bolt.name].items()
                }
            )
        finite_hits[name] = {
            feature: collision
            for feature, collision in protected.hits(
                features, protected_inventory
            ).items()
            if collision
        }
        axis_hits = {
            f"{feature}/{family}/{member}": volume
            for feature, collisions in finite_hits[name].items()
            for family in ("panel_screws", "frame_bolts")
            for member, volume in collisions.get(family, {}).items()
        }
        same_bore_hits = joints._bore_pair_hits(row["bores"])
        hosts = {
            row["principal_name"]: wood[row["principal_name"]],
            row["rail_name"]: wood[row["rail_name"]],
            "candidate_block": row["block"],
        }
        tool_host_hits = {
            f"{bolt}/{end}/{member}": volume
            for bolt, ends in row["tools"].items()
            for end, shape in ends.items()
            for member, volume in _hits(shape, hosts).items()
        }
        blocker = {
            "incomplete_bores": [
                bolt for bolt, passed in row["complete"].items() if not passed
            ],
            "other_timber_hits_mm3": other_timber_hits,
            "protected_axis_hits_mm3": axis_hits,
            "finite_protected_hits": finite_hits[name],
            "same_station_bore_hits_mm3": same_bore_hits,
            "tool_host_hits_mm3": tool_host_hits,
            "missing_contacts": [
                host for host, area in row["contact"].items() if area <= 0
            ],
        }
        blocked[name] = {key: value for key, value in blocker.items() if value}
        reports[name] = {
            "block_local_n_bounds_mm": [round(v, 6) for v in row["local_n_bounds"]],
            "block_local_t_bounds_mm": [round(v, 6) for v in row["local_t_bounds"]],
            "block_dimensions_mm": [block_x_mm, BLOCK_T_MM, BLOCK_N_MM],
            "block_bounds_xyz_mm": [
                round(value, 6)
                for value in (
                    row["block"].BoundingBox().xmin,
                    row["block"].BoundingBox().xmax,
                    row["block"].BoundingBox().ymin,
                    row["block"].BoundingBox().ymax,
                    row["block"].BoundingBox().zmin,
                    row["block"].BoundingBox().zmax,
                )
            ],
            "contact_area_mm2": {key: round(v, 6) for key, v in row["contact"].items()},
            "complete_bores_by_bolt": row["complete"],
            "bore_host_volume_fraction": row["fractions"],
            "block_side_cleat_hit_mm3": (
                round(joints._intersection_volume(row["block"], right_side_cleat), 6)
                if right_side_cleat is not None
                else None
            ),
            "protected_axis_hits_mm3": axis_hits,
            "finite_protected_hits": finite_hits[name],
            "other_timber_hits_mm3": other_timber_hits,
            "bolt_grips_mm": {bolt.name: bolt.grip for bolt in row["bolts"]},
            "bolt_paths": {
                bolt.name: {
                    "bore_start_xyz_mm": list(bolt.start.toTuple()),
                    "direction_xyz": list(bolt.direction.toTuple()),
                    "bore_envelope_length_mm": bolt.length,
                    "wood_grip_mm": bolt.grip,
                    "trial_diameter_mm": bolt.diameter,
                }
                for bolt in row["bolts"]
            },
            "generic_tool_host_hits_mm3": tool_host_hits,
        }
    return {
        "source_id": source_id,
        "stations": list(STATIONS),
        "target_duty_members": {name: list(stations[name][4:]) for name in STATIONS},
        "approved_post_centers_x_mm": [-180.0, 180.0],
        "block_local_n_mm": BLOCK_N_MM,
        "block_side": block_side,
        "retained_pb02_side_cleat": include_pb02_side_cleat,
        "rail_n_offset_from_low_mm": rail_n_offset_mm,
        "rail_x_offsets_from_butt_mm": list(rail_x_mm),
        "inventory": {
            "candidate_blocks": 2,
            "candidate_through_bolts": 8,
            "target_legacy_sds": len(target),
            "other_legacy_sds": len(other),
            "retained_frame_bolts": len(frame),
            "fixed_panel_kicker_axes": len(panel),
        },
        "pairs": reports,
        "binding_constraints": {key: value for key, value in blocked.items() if value},
        "finite_protected_counts": finite,
        "protected_3d_gates": {
            name: {"status": "UNVERIFIED", "clearance_mm": None}
            for name in PROTECTED_3D_GATES
        },
        "backer_frame_attachment_qualified": False,
        "whole_frame_qualified": False,
        "decision": "REVISE"
        if any(blocked.values())
        else "ADVANCE_LAYOUT_GEOMETRY_ONLY",
        "native_solve": False,
        "drilling_released": False,
        "structural_released": False,
    }


def screen():
    """Retain the original detached layout diagnostic unchanged."""
    return screen_variant()


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
