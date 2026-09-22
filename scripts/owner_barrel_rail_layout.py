"""Source-distinct ten-duty direct cross-dowel viewer geometry; no release."""

import cadquery as cq

from mini_moonboard.box_frame import Connection
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as continuation
from scripts import simple_pb01_cross_dowel_trial as cd01
from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_center_pair as upper_center
from scripts import simple_pb03_upper_outer_pair as upper_outer
from scripts import simple_pb07_outer_rail_native as pb07

SOURCE_ID = "owner-barrel-direct-ten-rail-v1"
STATIONS = (
    *lower.TARGET_STATIONS,
    *lower.LOWER_OUTER_STATIONS,
    *upper_outer.TARGET_STATIONS,
    *upper_center.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)
CENTER_STATIONS = (*lower.TARGET_STATIONS, *upper_center.TARGET_STATIONS)
SPECS = {
    **lower.STATION_SPECS,
    **upper_outer.STATION_SPECS,
    **upper_center.STATION_SPECS,
    **bottom.STATION_SPECS,
}
ROW_N_FROM_FRONT_MM = (60.0, 92.25)
BARREL_X_FROM_BUTT_MM = cd01.BARREL_X_FROM_BUTT_MM
BARREL_AXIS_OFFSET_MM = continuation.BARREL_LENGTH_MM / 2
BARREL_RECESS_MM = (continuation.SECTION_MM[0] - continuation.BARREL_LENGTH_MM) / 2
MACHINE_BORE_DIAMETER_MM = cd01.MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM
ACCESS_DIAMETER_MM = cd01.ACCESS_DIAMETER_MM
ACCESS_LENGTH_MM = cd01.ACCESS_LENGTH_MM
TOL_MM3 = 1.0
ALTERNATE_X_MM = 76.2
ALTERNATE_T_MM = 38.1


def _box_bounds(shape):
    return cd01._local_bounds(shape)


def _cylinder(point, direction, length, diameter):
    return cq.Solid.makeCylinder(diameter / 2, length, point, direction)


def _xyz(x, t, n):
    return cq.Vector(*cd01._xyz(x, t, n))


def _axis(row):
    return _cylinder(row.start, row.direction.normalized(), row.length, row.diameter)


def _hits(shape, others):
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := protected._volume(shape, other)) > TOL_MM3
    }


def _owner_wood(source):
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    for side, sign in (("left", -1), ("right", 1)):
        name = f"base_post_center_{side}"
        bounds = wood[name].BoundingBox()
        center = (bounds.xmin + bounds.xmax) / 2
        wood[name] = wood[name].translate(
            cq.Vector(sign * posts.POST_CENTER_X_MM - center, 0, 0)
        )
    return wood


def build_geometry(wood=None):
    """Expose cut wood, intersecting bores, trial solids, and access per duty."""
    source = variant(KERF_RIGHT)
    panel = tuple(source.panel_connections())
    frame = tuple(row for row in source.connections() if row.kind == "bolt")
    if len(panel) != 66 or len(frame) != 12 or len(STATIONS) != 10:
        raise ValueError("Fixed kerf-right axis or rail-duty inventory changed")
    wood = _owner_wood(source) if wood is None else wood
    geometry = {}
    for station in STATIONS:
        spec = SPECS[station]
        upright, rail = wood[spec.upright_name], wood[spec.rail_name]
        ub, rb = _box_bounds(upright), _box_bounds(rail)
        sign = 1 if spec.rail_extension_direction == "right" else -1
        rail_butt_x = rb["x"][0] if sign == 1 else rb["x"][1]
        upright_butt_x = ub["x"][1] if sign == 1 else ub["x"][0]
        upright_outer_x = ub["x"][0] if sign == 1 else ub["x"][1]
        butt_mismatch = rail_butt_x - upright_butt_x
        direct_butt = abs(butt_mismatch) < 1e-5
        t_min, t_max = rb["t"]
        n_min, n_max = rb["n"]
        if abs((t_max - t_min) - continuation.SECTION_MM[0]) > 1e-4:
            raise ValueError(f"{station}: rail T section changed")
        if abs((n_max - n_min) - continuation.SECTION_MM[1]) > 1e-4:
            raise ValueError(f"{station}: rail rearward N envelope changed")
        barrel_x = rail_butt_x + sign * BARREL_X_FROM_BUTT_MM
        rows = []
        for index, n_offset in enumerate(ROW_N_FROM_FRONT_MM, 1):
            n = n_min + n_offset
            entry_from_minus_t = index == 1
            entry_t = t_min if entry_from_minus_t else t_max
            barrel_direction = cq.Vector(0, *cd01.T) * (1 if entry_from_minus_t else -1)
            bolt_direction = cq.Vector(sign, 0, 0)
            body_start = _xyz(
                barrel_x,
                entry_t
                + (BARREL_RECESS_MM if entry_from_minus_t else -BARREL_RECESS_MM),
                n,
            )
            barrel_entry = _xyz(barrel_x, entry_t, n)
            thread_center = body_start + barrel_direction * BARREL_AXIS_OFFSET_MM
            wood_seat = _xyz(upright_outer_x, (t_min + t_max) / 2, n)
            path_to_thread = abs(barrel_x - upright_outer_x)
            bore_start = wood_seat - bolt_direction * 2.0
            machine_bore = _cylinder(
                bore_start,
                bolt_direction,
                path_to_thread + continuation.BARREL_OD_MM / 2 + 4.0,
                MACHINE_BORE_DIAMETER_MM,
            )
            barrel_bore = _cylinder(
                barrel_entry,
                barrel_direction,
                BARREL_RECESS_MM + continuation.BARREL_LENGTH_MM,
                continuation.BARREL_OD_MM,
            )
            barrel = _cylinder(
                body_start,
                barrel_direction,
                continuation.BARREL_LENGTH_MM,
                continuation.BARREL_OD_MM,
            )
            bolt = _cylinder(
                wood_seat
                - bolt_direction * continuation.WASHER_THICKNESS_SENSITIVITY_MM,
                bolt_direction,
                continuation.BOLT_LENGTH_MM,
                continuation.THREAD_MAJOR_MM,
            )
            bolt_access = _cylinder(
                wood_seat,
                -bolt_direction,
                ACCESS_LENGTH_MM,
                ACCESS_DIAMETER_MM,
            )
            barrel_access = _cylinder(
                barrel_entry,
                -barrel_direction,
                ACCESS_LENGTH_MM,
                ACCESS_DIAMETER_MM,
            )
            rows.append(
                {
                    "name": f"{station}_barrel_{index}",
                    "entry_face": "minus_t" if entry_from_minus_t else "plus_t",
                    "n_offset_mm": n_offset,
                    "thread_center": thread_center,
                    "wood_seat": wood_seat,
                    "bolt_direction": bolt_direction,
                    "machine_bore": machine_bore,
                    "barrel_bore": barrel_bore,
                    "barrel": barrel,
                    "bolt": bolt,
                    "bolt_access": bolt_access,
                    "barrel_access": barrel_access,
                    "wood_path_to_thread_mm": path_to_thread,
                }
            )
        rail_bores = [row["machine_bore"] for row in rows] + [
            row["barrel_bore"] for row in rows
        ]
        upright_bores = [row["machine_bore"] for row in rows]
        cut_rail, cut_upright = rail, upright
        for bore in rail_bores:
            cut_rail = cut_rail.cut(bore)
        for bore in upright_bores:
            cut_upright = cut_upright.cut(bore)
        # ponytail: this is only a visible fallback volume, not a proven joint.
        alternate_x0 = rail_butt_x if sign == 1 else rail_butt_x - ALTERNATE_X_MM
        alternate = (
            cq.Solid.makeBox(
                ALTERNATE_X_MM,
                ALTERNATE_T_MM,
                n_max - n_min,
                cq.Vector(alternate_x0, 0, 0),
            )
            .rotate((0, 0, 0), (1, 0, 0), 50)
            .translate(_xyz(0, t_max, n_min))
        )
        geometry[station] = {
            "station": station,
            "spec": spec,
            "rail": rail,
            "upright": upright,
            "cut_rail": cut_rail.clean(),
            "cut_upright": cut_upright.clean(),
            "alternate_block": alternate,
            "rows": tuple(rows),
            "rail_n_depth_mm": n_max - n_min,
            "butt_mismatch_mm": butt_mismatch,
            "direct_butt_available": direct_butt,
        }
    return {"wood": wood, "stations": geometry, "panel": panel, "frame": frame}


def screen(built=None):
    """One finite-solid screen; directness and service hits block layout approval."""
    built = build_geometry() if built is None else built
    fixed = protected.inventory()
    stations = {}
    for name, pose in built["stations"].items():
        rows = pose["rows"]
        unrelated = {
            part_name: shape
            for part_name, shape in built["wood"].items()
            if part_name not in (pose["spec"].upright_name, pose["spec"].rail_name)
        }
        solids = {
            f"{row['name']}/{kind}": row[kind]
            for row in rows
            for kind in (
                "machine_bore",
                "barrel_bore",
                "barrel",
                "bolt",
                "bolt_access",
                "barrel_access",
            )
        }
        service_hits = {
            solid: hits for solid, hits in protected.hits(solids, fixed).items() if hits
        }
        unrelated_hits = {
            solid: hits
            for solid, shape in solids.items()
            if (hits := _hits(shape, unrelated))
        }
        bore_intersections = tuple(
            round(protected._volume(row["machine_bore"], row["barrel_bore"]), 6)
            for row in rows
        )
        barrel_contained = tuple(
            abs(protected._volume(row["barrel"], pose["rail"]) - row["barrel"].Volume())
            <= TOL_MM3
            for row in rows
        )
        compact_alternate = None
        if not pose["direct_butt_available"]:
            compact_alternate = (
                "Trim the existing rail to the approved ±180-mm post side face; "
                "retain a separate explicit kicker/backer receiver, then rederive "
                "two direct end-to-side barrel rows. This is unmodeled and needs "
                "panel-screw/support and frame-bolt checks."
            )
        elif service_hits or unrelated_hits:
            compact_alternate = (
                "Short solid 139.7-mm-N timber corner cleat with two face-to-face "
                "interfaces and separate barrel pairs. Its visible trial block "
                "has not cleared the identified protected volume. This is not an "
                "old bracket; its bores, service space, and load path need new checks."
            )
        alternate_protected_hits = {
            key: value
            for key, value in protected.hits(
                {"block": pose["alternate_block"]}, fixed
            ).items()
            if value
        }
        alternate_wood_hits = _hits(pose["alternate_block"], unrelated)
        stations[name] = {
            "participants": [pose["spec"].upright_name, pose["spec"].rail_name],
            "rail_n_depth_mm": round(pose["rail_n_depth_mm"], 6),
            "butt_mismatch_mm": round(pose["butt_mismatch_mm"], 6),
            "direct_butt_available": pose["direct_butt_available"],
            "fastener_count": len(rows),
            "barrel_entry_faces": [row["entry_face"] for row in rows],
            "machine_bore_to_barrel_bore_mm3": bore_intersections,
            "machine_bore_meets_barrel_bore": all(
                v > TOL_MM3 for v in bore_intersections
            ),
            "barrels_contained_in_rail": all(barrel_contained),
            "wood_paths_to_thread_mm": [
                round(row["wood_path_to_thread_mm"], 6) for row in rows
            ],
            "nominal_5in_tip_past_axis_mm": [
                round(
                    continuation.BOLT_LENGTH_MM
                    - continuation.WASHER_THICKNESS_SENSITIVITY_MM
                    - row["wood_path_to_thread_mm"],
                    6,
                )
                for row in rows
            ],
            "protected_hits_mm3": service_hits,
            "unrelated_wood_hits_mm3": unrelated_hits,
            "compact_alternate": compact_alternate,
            "compact_alternate_protected_hits_mm3": alternate_protected_hits,
            "compact_alternate_unrelated_wood_hits_mm3": alternate_wood_hits,
            "geometry_status": (
                "DIRECT_TRIAL_BLOCKED"
                if not pose["direct_butt_available"]
                or service_hits
                or unrelated_hits
                or not all(barrel_contained)
                or not all(v > TOL_MM3 for v in bore_intersections)
                else "DIRECT_TRIAL_GEOMETRY_ONLY"
            ),
        }
    return {
        "schema": "owner_barrel_rail_layout/v1",
        "source_id": SOURCE_ID,
        "parent_source_id": pb07.SOURCE_ID,
        "inventory": {
            "rail_duties": len(stations),
            "panel_kicker_axes": len(built["panel"]),
            "retained_frame_bolt_axes": len(built["frame"]),
            "candidate_brackets": 0,
        },
        "trial_hardware": {
            "retail_identity": "Hillman 880543; Lowe's 3012559; Home Depot 202242356",
            "barrel_od_mm": continuation.BARREL_OD_MM,
            "barrel_length_mm": continuation.BARREL_LENGTH_MM,
            "thread_axis_from_end_mm_provisional": BARREL_AXIS_OFFSET_MM,
            "axis_offset_sensitivity_mm": list(continuation.AXIS_OFFSET_SENSITIVITY_MM),
            "bolt_length_mm_provisional": continuation.BOLT_LENGTH_MM,
            "washer_thickness_mm_provisional": continuation.WASHER_THICKNESS_SENSITIVITY_MM,
            "machine_bore_diameter_mm_trial_not_drill_size": MACHINE_BORE_DIAMETER_MM,
        },
        "protected_inventory_counts": fixed["counts"],
        "stations": stations,
        "disposition": "DEVELOPMENT_REVISE",
        "manufacturer_contacted": False,
        "fit_qualified": False,
        "strength_qualified": False,
        "native_solve": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


def _connection(row, spec):
    """Diagnostic installed axis only; length and thread fit stay provisional."""
    start = (
        row["wood_seat"]
        - row["bolt_direction"] * continuation.WASHER_THICKNESS_SENSITIVITY_MM
    )
    return Connection(
        f"{row['name']}_bolt",
        start,
        row["bolt_direction"],
        continuation.BOLT_LENGTH_MM,
        continuation.THREAD_MAJOR_MM,
        (spec.upright_name, spec.rail_name),
        "bolt",
    )


def build_layout(wood):
    """Assembly adapter: use its exact wood pose and retain REVISE dispositions."""
    built = build_geometry(wood=wood)
    report = screen(built)
    stations = {}
    for name, pose in built["stations"].items():
        bolts = {
            f"{row['name']}_bolt": _connection(row, pose["spec"])
            for row in pose["rows"]
        }
        blocked = report["stations"][name]["geometry_status"] == "DIRECT_TRIAL_BLOCKED"
        stations[name] = {
            "mode": "mixed" if blocked else "direct",
            "compact_alternate_block": pose["alternate_block"] if blocked else None,
            "axis_offset_mm": BARREL_AXIS_OFFSET_MM,
            "disposition": report["stations"][name]["geometry_status"],
            "bolts": bolts,
            "barrels": {row["name"]: row["barrel"] for row in pose["rows"]},
            "stacks": {
                f"{row['name']}_bolt": {"shaft": row["bolt"]} for row in pose["rows"]
            },
            "drilling_paths": {
                f"{row['name']}/{kind}": row[kind]
                for row in pose["rows"]
                for kind in ("machine_bore", "barrel_bore")
            },
            "access_paths": {
                f"{row['name']}/{kind}": row[kind]
                for row in pose["rows"]
                for kind in ("bolt_access", "barrel_access")
            },
        }
    return {
        "stations": stations,
        "diagnostics": {
            "source_id": SOURCE_ID,
            "disposition": report["disposition"],
            "station_screens": report["stations"],
            "limits": (
                "Shaft-only generic stacks; heads, washer seats, delivered thread "
                "fit, drilling sizes and tool insertion remain unverified"
            ),
        },
    }
