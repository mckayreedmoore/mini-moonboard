"""Bounded inward-axis alternatives for the two outer-base barrel duties.

Only diagnostic solids move. The integrated viewer, source wood, fixed screws,
and retained frame bolts are not edited or cut by this probe.
"""

import json
from functools import lru_cache
from itertools import combinations

import cadquery as cq

from scripts import owner_barrel_outer_top_layout as outer
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger
from scripts.owner_barrel_layout_assembly import build_assembly

SOURCE_ID = "owner-barrel-outer-base-clearance-probe-v1"
STATIONS = ("clip_angle_base_left", "clip_angle_base_right")
OFFSETS_INWARD_MM = (0.0, 5.0, 10.0, 15.0)
WASHER_OD_MM = 25.4  # Provisional clearance envelope, not a verified retail OD.
HEAD_OD_MM = 11.0
HEAD_HEIGHT_MM = 4.0
TOOL_OD_MM = 20.0
TOOL_REACH_MM = 40.0
HIT_TOL_MM3 = 1.0


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > HIT_TOL_MM3
    }


def _other_shapes(assembly):
    physical = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] not in STATIONS
    }
    physical.update(
        {
            f"bolt/{name}/{role}": shape
            for name, roles in assembly["stacks"].items()
            if assembly["bolt_station"][name] not in STATIONS
            for role, shape in roles.items()
        }
    )
    paths = {
        f"drill/{name}": shape
        for name, shape in assembly["drilling_paths"].items()
        if not any(name.startswith(f"barrel_trial_{station}_") for station in STATIONS)
    }
    paths.update(
        {
            f"access/{name}": shape
            for name, shape in assembly["access_paths"].items()
            if not any(
                name.startswith(f"barrel_trial_{station}_") for station in STATIONS
            )
        }
    )
    return physical, paths


def _row(side, index, inward_mm, wood):
    """Rebuild the original row with only its bolt/thread axis moved inward X."""
    rim_name = f"base_side_{side}"
    post_name = f"base_post_outer_{side}"
    rim, header, post = wood[rim_name], wood["base_header"], wood[post_name]
    rb, hb, pb = rim.BoundingBox(), header.BoundingBox(), post.BoundingBox()
    sign = 1 if side == "left" else -1
    x = (rb.xmin + rb.xmax) / 2 + sign * inward_mm
    entry_x = rb.xmin if side == "left" else rb.xmax
    y = (-135.0, -75.0)[index - 1]
    seat = cq.Vector(x, y, hb.zmin)
    axis = cq.Vector(x, y, rb.zmin + 70.0)
    entry = cq.Vector(entry_x, y, rb.zmin + 70.0)
    row = outer._row(
        seat,
        cq.Vector(0, 0, 1),
        axis,
        entry,
        cq.Vector(sign, 0, 0),
        {"base_header": header, rim_name: rim},
    )
    barrel_start = (
        cq.Vector(*row["barrel_entry_xyz_mm"])
        + cq.Vector(sign, 0, 0) * row["barrel_recess_mm"]
    )
    washer_start = seat - cq.Vector(0, 0, hardware.WASHER_THICKNESS_SENSITIVITY_MM)
    embedded_length = row["nominal_full_machine_bore_depth_mm"]
    name = f"{side}_{index}"
    physical = {
        f"{name}/shaft": outer._cylinder(
            washer_start,
            cq.Vector(0, 0, 1),
            hardware.BOLT_LENGTH_MM,
            hardware.THREAD_MAJOR_MM,
        ),
        f"{name}/barrel": outer._cylinder(
            barrel_start,
            cq.Vector(sign, 0, 0),
            hardware.BARREL_LENGTH_MM,
            hardware.BARREL_OD_MM,
        ),
        f"{name}/washer": outer._cylinder(
            washer_start,
            cq.Vector(0, 0, 1),
            hardware.WASHER_THICKNESS_SENSITIVITY_MM,
            WASHER_OD_MM,
        ),
        f"{name}/head": outer._cylinder(
            washer_start - cq.Vector(0, 0, HEAD_HEIGHT_MM),
            cq.Vector(0, 0, 1),
            HEAD_HEIGHT_MM,
            HEAD_OD_MM,
        ),
    }
    paths = {
        f"{name}/machine_bore": outer._cylinder(
            seat, cq.Vector(0, 0, 1), embedded_length, outer.MACHINE_BORE_D_MM
        ),
        f"{name}/barrel_bore": outer._cylinder(
            entry,
            cq.Vector(sign, 0, 0),
            row["barrel_cross_bore_depth_mm"],
            hardware.BARREL_OD_MM,
        ),
        f"{name}/bolt_access": outer._cylinder(
            seat, cq.Vector(0, 0, -1), TOOL_REACH_MM, TOOL_OD_MM
        ),
        f"{name}/barrel_access": outer._cylinder(
            entry, cq.Vector(-sign, 0, 0), TOOL_REACH_MM, TOOL_OD_MM
        ),
    }
    intended = {"base_header": header, rim_name: rim}
    contained = {
        "machine_bore": min(
            1.0,
            sum(
                protected._volume(paths[f"{name}/machine_bore"], part)
                for part in intended.values()
            )
            / paths[f"{name}/machine_bore"].Volume(),
        ),
        "barrel_bore": protected._volume(paths[f"{name}/barrel_bore"], rim)
        / paths[f"{name}/barrel_bore"].Volume(),
        "barrel_body": protected._volume(physical[f"{name}/barrel"], rim)
        / physical[f"{name}/barrel"].Volume(),
    }
    # A thin disk immediately inside the nominal header face checks whether
    # the assumed washer actually bears on that face, rather than over a void.
    seat_disk = outer._cylinder(seat, cq.Vector(0, 0, 1), 0.1, WASHER_OD_MM)
    seat_fraction = protected._volume(seat_disk, header) / seat_disk.Volume()
    post_access = _hits(paths[f"{name}/bolt_access"], {post_name: post})
    post_edge = pb.xmax if side == "left" else pb.xmin
    access_margin = sign * (x - post_edge) - TOOL_OD_MM / 2
    return {
        "datum": {
            "row": index,
            "y_mm": y,
            "axis_x_mm": round(x, 6),
            "access_to_outer_post_nominal_gap_mm": round(access_margin, 6),
            "source_wood_coverage_fraction": {
                key: round(value, 7) for key, value in contained.items()
            },
            "provisional_washer_header_seat_fraction": round(seat_fraction, 7),
            "nominal_bore_meets_barrel": row["machine_bore_meets_barrel_bore"],
            "tip_beyond_barrel_axis_mm": row["nominal_tip_beyond_axis_mm"],
            "outer_post_bolt_access_hits_mm3": post_access,
        },
        "physical": physical,
        "paths": paths,
    }


def _pair_hits(first, second):
    return {
        f"{name_a}|{name_b}": round(volume, 6)
        for name_a, shape_a in first.items()
        for name_b, shape_b in second.items()
        if (volume := protected._volume(shape_a, shape_b)) > HIT_TOL_MM3
    }


@lru_cache(maxsize=1)
def probe():
    """Screen four inward offsets on exact integrated kerf-right owner wood."""
    assembly = build_assembly()
    fixed = protected.inventory()
    duties = ledger.selected_duties()
    if (
        len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Fixed kerf-right connection inventory changed")
    if any(duties[name]["family"] != "base_outer_side" for name in STATIONS):
        raise ValueError("Outer-base duty ledger changed")
    other_physical, other_paths = _other_shapes(assembly)
    candidates = {}
    for inward_mm in OFFSETS_INWARD_MM:
        stations = {}
        candidate_physical, candidate_paths, rows_by_station = {}, {}, {}
        for station in STATIONS:
            side = duties[station]["side"]
            rows = [_row(side, index, inward_mm, assembly["wood"]) for index in (1, 2)]
            rows_by_station[station] = rows
            physical = {
                name: solid for row in rows for name, solid in row["physical"].items()
            }
            paths = {
                name: solid for row in rows for name, solid in row["paths"].items()
            }
            candidate_physical.update(physical)
            candidate_paths.update(paths)
            unrelated = {
                name: shape
                for name, shape in assembly["wood"].items()
                if name not in duties[station]["timber"]
            }
            wood_hits = {
                name: hits
                for name, shape in (physical | paths).items()
                if (hits := _hits(shape, unrelated))
            }
            protected_hits = {
                name: hits
                for name, hits in protected.hits(physical | paths, fixed).items()
                if hits
            }
            row_pair = rows[0]["physical"] | rows[0]["paths"]
            other_row = rows[1]["physical"] | rows[1]["paths"]
            row_hits = _pair_hits(row_pair, other_row)
            stations[station] = {
                "rows": [row["datum"] for row in rows],
                "outer_post_bolt_access_hits_mm3": {
                    str(index): row["datum"]["outer_post_bolt_access_hits_mm3"]
                    for index, row in enumerate(rows, 1)
                    if row["datum"]["outer_post_bolt_access_hits_mm3"]
                },
                "unrelated_wood_hits_mm3": wood_hits,
                "protected_hits_mm3": protected_hits,
                "inter_row_hits_mm3": row_hits,
            }
        # The only new candidate family has two duties; screen each against its
        # other side and all 22 unchanged barrel duties, including path conflicts.
        cross_station = {}
        for first, second in combinations(STATIONS, 2):
            first_rows, second_rows = rows_by_station[first], rows_by_station[second]
            first_physical = {
                n: s for r in first_rows for n, s in r["physical"].items()
            }
            second_physical = {
                n: s for r in second_rows for n, s in r["physical"].items()
            }
            first_paths = {n: s for r in first_rows for n, s in r["paths"].items()}
            second_paths = {n: s for r in second_rows for n, s in r["paths"].items()}
            cross_station.update(_pair_hits(first_physical, second_physical))
            cross_station.update(_pair_hits(first_paths, second_physical))
            cross_station.update(_pair_hits(second_paths, first_physical))
        neighbor_hits = {
            "physical_to_physical": _pair_hits(candidate_physical, other_physical),
            "new_paths_to_physical": _pair_hits(candidate_paths, other_physical),
            "other_paths_to_new_physical": _pair_hits(other_paths, candidate_physical),
            "other_base_station": cross_station,
        }
        clear = all(
            not row["outer_post_bolt_access_hits_mm3"]
            and not row["unrelated_wood_hits_mm3"]
            and not row["protected_hits_mm3"]
            and not row["inter_row_hits_mm3"]
            and all(
                datum["nominal_bore_meets_barrel"]
                and min(datum["source_wood_coverage_fraction"].values()) >= 0.999
                and datum["provisional_washer_header_seat_fraction"] >= 0.999
                and datum["tip_beyond_barrel_axis_mm"] >= 0
                for datum in row["rows"]
            )
            for row in stations.values()
        ) and not any(neighbor_hits.values())
        candidates[str(inward_mm)] = {
            "stations": stations,
            "neighbor_hits_mm3": neighbor_hits,
            "nominal_geometry_screen_clear": clear,
        }
    return {
        "source_id": SOURCE_ID,
        "basis": "exact integrated kerf-right owner assembly; uncut diagnostic geometry",
        "inventory": {
            "outer_base_stations": len(STATIONS),
            "fixed_panel_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
            "protected": fixed["counts"],
            "other_barrel_duties": 22,
        },
        "offsets_inward_mm": list(OFFSETS_INWARD_MM),
        "nominal_envelopes_mm": {
            "bolt_access_diameter": TOOL_OD_MM,
            "bolt_access_reach": TOOL_REACH_MM,
            "washer_od": WASHER_OD_MM,
            "head_od": HEAD_OD_MM,
            "head_height": HEAD_HEIGHT_MM,
            "bolt_nominal_length": hardware.BOLT_LENGTH_MM,
        },
        "candidates": candidates,
        "limits": (
            "Nominal finite solids only. Delivered barrel geometry/thread axis, bolt "
            "shank/thread engagement, actual head/washer/tool, tolerances, installation "
            "order, net sections, strength and six-case load path remain unqualified."
        ),
        "layout_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
