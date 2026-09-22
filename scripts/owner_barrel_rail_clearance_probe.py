"""Bounded right-center barrel trial against exact owner assembly wood; no release."""

import json
from itertools import product

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import owner_barrel_coordinates as coordinates
from scripts import owner_barrel_rail_layout as rail
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware

STATIONS = ("clip_horizontal_lower_right_1", "clip_horizontal_upper_right_1")
ROW_PAIRS_MM = (
    (50.0, 92.25),
    (55.0, 92.25),
    (60.0, 92.25),
    (65.0, 92.25),
    (65.0, 95.0),
)
SETBACKS_MM = (70.0, 75.0, 82.5)
SEVEN_D_MM = 7 * hardware.THREAD_MAJOR_MM
FOUR_D_MM = 4 * hardware.THREAD_MAJOR_MM
KINDS = (
    "machine_bore",
    "barrel_bore",
    "barrel",
    "bolt",
    "bolt_access",
    "barrel_access",
)


def owner_wood(source=None, placement=None):
    """Mirror the assembly's original timber, moved posts, and two screw backers."""
    source = variant(KERF_RIGHT) if source is None else source
    placement = posts.build_layout() if placement is None else placement
    if placement["post_bounds_x_mm"] != {
        "left": [-199.05, -160.95],
        "right": [160.95, 199.05],
    }:
        raise ValueError("Approved ±180 mm post pose changed")
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    for side, sign in (("left", -1), ("right", 1)):
        name = f"base_post_center_{side}"
        wood[name] = wood[name].translate(
            cq.Vector(placement["post_shift_x_mm"][side], 0, 0)
        )
        bounds = wood[name].BoundingBox()
        if abs((bounds.xmin + bounds.xmax) / 2 - sign * 180) > 1e-6:
            raise ValueError(f"{name}: changed center")
        x0, x1 = placement["backer_bounds_x_mm"][side]
        wood[f"inner_kicker_backer_{side}"] = cq.Solid.makeBox(
            x1 - x0,
            posts.BACKER_FRONT_Y_MM - posts.BACKER_REAR_Y_MM,
            posts.BACKER_TOP_Z_MM,
            cq.Vector(x0, posts.BACKER_REAR_Y_MM, 0),
        )
    return wood


def _hits(shape, others):
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := protected._volume(shape, other)) > protected.HIT_TOL_MM3
    }


def _station(pose, wood, fixed):
    rows = pose["rows"]
    spec = pose["spec"]
    rail_bounds = coordinates.local_bounds(pose["rail"])
    upright_bounds = coordinates.local_bounds(pose["upright"])
    offsets = [row["n_offset_mm"] for row in rows]
    n0 = rail_bounds["n"][0]
    n_values = [n0 + offset for offset in offsets]
    setback = abs(
        rows[0]["thread_center"].x
        - (
            rail_bounds["x"][0]
            if rows[0]["bolt_direction"].x > 0
            else rail_bounds["x"][1]
        )
    )
    reserves = {
        "rail_front_7d_mm": offsets[0] - SEVEN_D_MM,
        "rail_rear_7d_mm": rail_bounds["n"][1] - n_values[1] - SEVEN_D_MM,
        "upright_front_7d_mm": n_values[0] - upright_bounds["n"][0] - SEVEN_D_MM,
        "upright_rear_7d_mm": upright_bounds["n"][1] - n_values[1] - SEVEN_D_MM,
        "row_pitch_4d_mm": offsets[1] - offsets[0] - FOUR_D_MM,
        "rail_butt_7d_mm": setback - SEVEN_D_MM,
        "barrel_bore_far_t_wood_mm": rail.BARREL_RECESS_MM,
    }
    tip_paths = []
    for row in rows:
        direction = row["bolt_direction"]
        bore_box = row["machine_bore"].BoundingBox()
        bore_end_x = bore_box.xmax if direction.x > 0 else bore_box.xmin
        tip_from_seat = (
            hardware.BOLT_LENGTH_MM - hardware.WASHER_THICKNESS_SENSITIVITY_MM
        )
        tip_x = row["wood_seat"].x + direction.x * tip_from_seat
        bore_overrun = (tip_x - bore_end_x) * direction.x
        exterior_x = rail_bounds["x"][1] if direction.x > 0 else rail_bounds["x"][0]
        continuation = (
            cq.Solid.makeCylinder(
                rail.MACHINE_BORE_DIAMETER_MM / 2,
                bore_overrun,
                cq.Vector(bore_end_x, row["wood_seat"].y, row["wood_seat"].z),
                direction,
            )
            if bore_overrun > 0
            else None
        )
        tip_paths.append(
            {
                "past_barrel_mm": round(
                    tip_from_seat
                    - row["wood_path_to_thread_mm"]
                    - hardware.BARREL_OD_MM / 2,
                    6,
                ),
                "past_modeled_bore_mm": round(bore_overrun, 6),
                "to_rail_exterior_mm": round((exterior_x - tip_x) * direction.x, 6),
                "pilot_continuation": continuation,
            }
        )
    solids = {f"{row['name']}/{kind}": row[kind] for row in rows for kind in KINDS}
    solids.update(
        {
            f"{row['name']}/pilot_continuation_diagnostic": path["pilot_continuation"]
            for row, path in zip(rows, tip_paths)
            if path["pilot_continuation"] is not None
        }
    )
    protected_hits = {
        name: hits for name, hits in protected.hits(solids, fixed).items() if hits
    }
    unrelated = {
        name: shape
        for name, shape in wood.items()
        if name not in (spec.rail_name, spec.upright_name)
    }
    wood_hits = {
        name: hits
        for name, shape in solids.items()
        if (hits := _hits(shape, unrelated))
    }
    row_conflicts = {
        f"{a}/{b}": round(volume, 6)
        for a in KINDS
        for b in KINDS
        if (volume := protected._volume(rows[0][a], rows[1][b])) > protected.HIT_TOL_MM3
    }
    bore_meets = [
        round(protected._volume(row["machine_bore"], row["barrel_bore"]), 6)
        for row in rows
    ]
    body_contained = [
        abs(protected._volume(row["barrel"], pose["rail"]) - row["barrel"].Volume())
        <= protected.HIT_TOL_MM3
        for row in rows
    ]
    gates = {
        "direct_butt": pose["direct_butt_available"],
        "nominal_reserves": min(reserves.values()) >= -1e-6,
        "bores_meet": all(value > protected.HIT_TOL_MM3 for value in bore_meets),
        "barrels_contained": all(body_contained),
        "no_protected_hits": not protected_hits,
        "no_unrelated_wood_hits": not wood_hits,
        "no_inter_row_hits": not row_conflicts,
        "bolt_tip_inside_rail_exterior": all(
            path["to_rail_exterior_mm"] >= 0 for path in tip_paths
        ),
    }
    return {
        "reserves_mm": {key: round(value, 6) for key, value in reserves.items()},
        "bore_intersections_mm3": bore_meets,
        "body_contained": body_contained,
        "nominal_bolt_tip": [
            {key: value for key, value in path.items() if key != "pilot_continuation"}
            for path in tip_paths
        ],
        "protected_hits_mm3": protected_hits,
        "unrelated_wood_hits_mm3": wood_hits,
        "inter_row_hits_mm3": row_conflicts,
        "gates": gates,
        "failed_gates": [name for name, passed in gates.items() if not passed],
    }


def search():
    source = variant(KERF_RIGHT)
    wood = owner_wood(source)
    fixed = protected.inventory()
    if (
        len(tuple(source.panel_connections())) != 66
        or len(tuple(row for row in source.connections() if row.kind == "bolt")) != 12
    ):
        raise ValueError("Fixed panel/frame axes changed")
    candidates = []
    for rows, setback in product(ROW_PAIRS_MM, SETBACKS_MM):
        built = rail.build_geometry(
            wood=wood,
            row_n_mm=rows,
            barrel_setback_mm=setback,
            stations=STATIONS,
            cut_wood=False,
        )
        stations = {}
        for name, pose in built["stations"].items():
            stations[name] = _station(pose, wood, fixed)
        candidates.append(
            {
                "rows_n_from_front_mm": list(rows),
                "barrel_setback_mm": setback,
                "stations": stations,
                "geometry_gates_clear": all(
                    not row["failed_gates"] for row in stations.values()
                ),
            }
        )
    return {
        "schema": "owner_barrel_rail_clearance_probe/v1",
        "source": rail.SOURCE_ID,
        "stations": list(STATIONS),
        "wood_parts": len(wood),
        "protected_inventory_counts": fixed["counts"],
        "panel_screw_axes_preserved": 66,
        "retained_frame_bolt_axes_preserved": 12,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "fit_qualified": False,
        "strength_qualified": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(search(), indent=2))
