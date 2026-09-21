"""Detached four-duty top corner-block layout; no native solve or release."""

import json
import math
from functools import lru_cache

import cadquery as cq

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_rail_joint_comparison as pb01
from scripts.simple_center_pb02_native import PB02Native

TARGET_STATIONS = (
    "clip_single_top_left_1",
    "clip_single_top_right_2",
    "clip_split_top_center_left",
    "clip_split_top_center_right",
)
MEMBERS = {
    TARGET_STATIONS[0]: ("base_side_left", "right"),
    TARGET_STATIONS[1]: ("base_side_right", "left"),
    TARGET_STATIONS[2]: ("base_principal_center_left", "left"),
    TARGET_STATIONS[3]: ("base_principal_center_right", "right"),
}
RAIL = "base_rail_top"
BLOCK_X_MM = 139.7
BLOCK_T_MM = 57.15
BLOCK_N_MM = 139.7
UPRIGHT_N_MM = (35.0, 104.7)
RAIL_X_MM = (40.0, 100.0)
RAIL_N_MM = 69.85


def _local_range(shape, axis):
    vector = pb01.T if axis == "t" else pb01.N
    values = [v.Y * vector[0] + v.Z * vector[1] for v in shape.Vertices()]
    return min(values), max(values)


def _hits(shape, obstacles):
    return {
        name: round(volume, 6)
        for name, other in obstacles.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _station(name, wood):
    """Put one block behind the top rail, flush with its actual rear face."""
    upright_name, extension = MEMBERS[name]
    upright, rail = wood[upright_name], wood[RAIL]
    ub = upright.BoundingBox()
    t_rear, t_front = _local_range(rail, "t")
    n_low, n_high = _local_range(rail, "n")
    if (
        abs(n_high - n_low - BLOCK_N_MM) > 1e-6
        or abs(_local_range(upright, "n")[0] - n_low) > 1e-6
        or abs(_local_range(upright, "n")[1] - n_high) > 1e-6
        or (
            "principal" in upright_name
            and abs(_local_range(upright, "t")[1] - t_rear) > 1e-6
        )
    ):
        raise ValueError(f"{name}: original top member faces changed")
    butt = ub.xmax if extension == "right" else ub.xmin
    x0 = butt if extension == "right" else butt - BLOCK_X_MM
    y0, z0 = pb01._yz(t_rear - BLOCK_T_MM, n_low)
    block = (
        cq.Solid.makeBox(BLOCK_X_MM, BLOCK_T_MM, BLOCK_N_MM, cq.Vector(x0, 0, 0))
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, y0, z0))
    )
    prefix = f"top_same_side_{name.removeprefix('clip_')}"
    specs = []
    direction = (1.0, 0.0, 0.0) if extension == "right" else (-1.0, 0.0, 0.0)
    for index, offset in enumerate(UPRIGHT_N_MM, 1):
        y, z = pb01._yz(t_rear - BLOCK_T_MM / 2, n_low + offset)
        x = ub.xmin if extension == "right" else ub.xmax
        specs.append(
            (
                f"{prefix}_upright_{index}",
                (x, y, z),
                direction,
                ub.xlen + BLOCK_X_MM,
                (upright_name, f"{prefix}_block"),
                {upright_name: ub.xlen, f"{prefix}_block": BLOCK_X_MM},
            )
        )
    for index, offset in enumerate(RAIL_X_MM, 1):
        x = butt + offset if extension == "right" else butt - offset
        y, z = pb01._yz(t_front, n_low + RAIL_N_MM)
        specs.append(
            (
                f"{prefix}_rail_{index}",
                (x, y, z),
                (0.0, -pb01.T[0], -pb01.T[1]),
                t_front - t_rear + BLOCK_T_MM,
                (RAIL, f"{prefix}_block"),
                {RAIL: t_front - t_rear, f"{prefix}_block": BLOCK_T_MM},
            )
        )
    bolts, bores, stacks, tools, complete = [], {}, {}, {}, {}
    for bolt_name, start, axis, grip, members, lengths in specs:
        bolt, stack, bore, access = lower._stack(bolt_name, start, axis, grip, members)
        bolts.append(bolt)
        bores[bolt_name], stacks[bolt_name], tools[bolt_name] = bore, stack, access
        hosts = {upright_name: upright, RAIL: rail, f"{prefix}_block": block}
        complete[bolt_name] = all(
            abs(
                bore.intersect(hosts[host]).Volume()
                - math.pi * (lower.BORE_DIAMETER_MM / 2) ** 2 * length
            )
            <= lower.TOL_MM3
            for host, length in lengths.items()
        )
    return {
        "block_name": f"{prefix}_block",
        "block": block,
        "upright": upright_name,
        "bolts": bolts,
        "bores": bores,
        "stacks": stacks,
        "tools": tools,
        "complete": complete,
        "contact": {
            "upright": lower._contact_area(block, upright, (-direction[0], 0, 0)),
            "rail": lower._contact_area(block, rail, (0, *pb01.T)),
        },
        "local_t_range_mm": [t_rear - BLOCK_T_MM, t_rear],
        "local_n_range_mm": [n_low, n_high],
    }


@lru_cache(maxsize=1)
def screen():
    """Screen the detached proposal against original timber, panels and axes."""
    module = PB02Native()
    if module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT:
        raise ValueError("PB02 source fingerprint changed")
    wood = {part.name: part.shape for part in module.wood_parts()}
    parts = {part.name: part.shape for part in module.parts()}
    source_rows = tuple(module.connections())
    panel_rows = tuple(module.panel_connections())
    stations = {row[0]: row for row in module.stations()}
    target_prefixes = tuple(f"{name}_" for name in TARGET_STATIONS)
    target_sds = tuple(
        row for row in source_rows if row.name.startswith(target_prefixes)
    )
    retained = tuple(row for row in source_rows if row not in target_sds)
    frame_rows = tuple(row for row in source_rows if row.kind == "bolt")
    if (
        len(stations) != 22
        or any(
            stations[name][4:] != (RAIL, MEMBERS[name][0]) for name in TARGET_STATIONS
        )
        or len(target_sds) != 24
        or any(row.kind != "screw" for row in target_sds)
        or len(panel_rows) != 66
        or len(frame_rows) != 12
    ):
        raise ValueError("four top source duties or fixed axes changed")
    rows = {name: _station(name, wood) for name in TARGET_STATIONS}
    candidate_bolts = tuple(bolt for row in rows.values() for bolt in row["bolts"])
    candidate_connections = (*retained, *candidate_bolts)
    source_preserved = (
        tuple(
            row
            for row in candidate_connections
            if row.name in {p.name for p in panel_rows}
        )
        == panel_rows
        and tuple(
            row
            for row in candidate_connections
            if row.name in {p.name for p in frame_rows}
        )
        == frame_rows
        and all(
            name in wood for name in (RAIL, *(member for member, _ in MEMBERS.values()))
        )
        and not any(
            row.name.startswith(target_prefixes) for row in candidate_connections
        )
    )
    fixed_axes = {row.name: _axis(row) for row in panel_rows}
    frame_axes = {row.name: _axis(row) for row in frame_rows}
    retained_sds_axes = {
        row.name: _axis(row)
        for row in retained
        if row.kind == "screw" and row.name.startswith("clip_")
    }
    other_angles = {
        name: shape
        for name, shape in parts.items()
        if name.startswith("clip_") and name not in TARGET_STATIONS
    }
    obstructions = {}
    reports = {}
    for name, row in rows.items():
        unrelated = {
            part: shape
            for part, shape in wood.items()
            if part not in (row["upright"], RAIL)
            and not part.startswith(("main_", "kicker_"))
        }
        panels = {
            part: shape
            for part, shape in wood.items()
            if part.startswith(("main_", "kicker_"))
        }
        protected = {
            **unrelated,
            **panels,
            **fixed_axes,
            **frame_axes,
            **retained_sds_axes,
            **other_angles,
            **{other: trial["block"] for other, trial in rows.items() if other != name},
        }
        hits = {"block": _hits(row["block"], protected)}
        for bolt in row["bolts"]:
            name_bolt = bolt.name
            outside = {
                part: shape
                for part, shape in protected.items()
                if part not in bolt.members
            }
            hits[f"bore/{name_bolt}"] = _hits(row["bores"][name_bolt], outside)
            for role, shape in row["stacks"][name_bolt].items():
                hits[f"stack/{name_bolt}/{role}"] = _hits(shape, outside)
            for end, shape in row["tools"][name_bolt].items():
                hits[f"tool/{name_bolt}/{end}"] = _hits(shape, outside)
                hosts = {
                    RAIL: wood[RAIL],
                    row["upright"]: wood[row["upright"]],
                    row["block_name"]: row["block"],
                }
                hits[f"tool_host/{name_bolt}/{end}"] = _hits(shape, hosts)
        hits["same_station_bores"] = lower._bore_pair_hits(row["bores"])
        obstructions[name] = {family: found for family, found in hits.items() if found}
        reports[name] = {
            "members": [RAIL, row["upright"]],
            "block_name": row["block_name"],
            "block_local_t_range_mm": row["local_t_range_mm"],
            "block_local_n_range_mm": row["local_n_range_mm"],
            "contact_area_mm2": {
                key: round(value, 6) for key, value in row["contact"].items()
            },
            "complete_bores_by_bolt": row["complete"],
            "bolt_grips_mm": {bolt.name: bolt.grip for bolt in row["bolts"]},
        }
        if not all(row["complete"].values()):
            obstructions[name]["incomplete_bores"] = [
                key for key, value in row["complete"].items() if not value
            ]
        if not all(value > 0 for value in row["contact"].values()):
            obstructions[name]["missing_contact"] = [
                key for key, value in row["contact"].items() if value <= 0
            ]
    blocked = {name: found for name, found in obstructions.items() if found}
    return {
        "schema": "simple_top_same_side_four/v1",
        "target_stations": list(TARGET_STATIONS),
        "inventory": {
            "candidate_blocks": 4,
            "candidate_bolts": 16,
            "removed_target_sds_axes": len(target_sds),
            "retained_legacy_sds_axes": sum(
                row.kind == "screw" and row.name.startswith("clip_") for row in retained
            ),
            "original_frame_bolts": len(frame_rows),
            "fixed_panel_kicker_axes": len(panel_rows),
        },
        "block_local_n_mm": BLOCK_N_MM,
        "minimum_nominal_block_washer_edge_ligament_mm": min(
            *(offset - lower.WASHER_DIAMETER_MM / 2 for offset in UPRIGHT_N_MM),
            *(
                BLOCK_N_MM - offset - lower.WASHER_DIAMETER_MM / 2
                for offset in UPRIGHT_N_MM
            ),
            *(offset - lower.WASHER_DIAMETER_MM / 2 for offset in RAIL_X_MM),
            *(
                BLOCK_X_MM - offset - lower.WASHER_DIAMETER_MM / 2
                for offset in RAIL_X_MM
            ),
            RAIL_N_MM - lower.WASHER_DIAMETER_MM / 2,
            BLOCK_N_MM - RAIL_N_MM - lower.WASHER_DIAMETER_MM / 2,
        ),
        "protected_3d_gates": {
            "panel_screw_modeled_shaft_axes": "screened_66",
            "retained_frame_bolt_modeled_shaft_axes": "screened_12",
            "hold_bodies_and_tnuts": "unverified_no_solids",
            "unused_hold_holes": "unverified_no_solids",
            "hold_bolt_protrusions": "unverified_no_solids",
            "led_bodies_and_wiring": "unverified_no_solids",
            "panel_screw_heads_and_driver_access": "unverified_no_solids",
            "frame_bolt_heads_nuts_and_tool_access": "unverified_no_solids",
            "other_developmental_corner_blocks": "unverified_detached_pb02_source",
        },
        "stations": reports,
        "obstructions": blocked,
        "smallest_exception": "See exact blocked feature; common block not yet clear"
        if blocked
        else None,
        "decision": "REVISE" if blocked else "ADVANCE_GEOMETRY_ONLY",
        "source_preserved": source_preserved,
        "native_solve": False,
        "strength_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
