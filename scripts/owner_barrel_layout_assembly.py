"""Whole-frame, kerf-right barrel-nut viewer composition; layout only.

Three independent producer families supply all 24 former clip duties. The
barrel/bolt envelopes are provisional and must not be used as drill dimensions.
"""

from importlib import import_module
from itertools import combinations
from math import isfinite

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger

_FAMILY_NAMES = {
    "rail10": frozenset(
        {"bottom_outer", "lower_outer", "lower_center", "upper_outer", "upper_center"}
    ),
    "center6": frozenset({"bottom_center", "header_center", "base_center"}),
    "outer_top8": frozenset(
        {"top_outer", "top_center", "header_outer_post", "base_outer_side"}
    ),
}
FAMILY_STATIONS = {
    family: tuple(
        station
        for name, left, right in ledger.PAIRS
        if name in names
        for station in (left, right)
    )
    for family, names in _FAMILY_NAMES.items()
}
PRODUCER_MODULES = {
    "rail10": "scripts.owner_barrel_rail_layout",
    "center6": "scripts.owner_barrel_center_layout",
    "outer_top8": "scripts.owner_barrel_outer_top_layout",
}
_NO_RELEASE = {
    "geometry_accepted": False,
    "retail_fit_approved": False,
    "thread_axis_controlled": False,
    "barrel_strength_qualified": False,
    "wood_strength_qualified": False,
    "backer_attachment_qualified": False,
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _default_builders():
    builders = {}
    missing = []
    for family, module_name in PRODUCER_MODULES.items():
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name != module_name:
                raise
            missing.append(module_name)
            continue
        builder = getattr(module, "build_layout", None)
        if not callable(builder):
            raise TypeError(f"{module_name} must expose build_layout(wood)")
        builders[family] = builder
    if missing:
        raise RuntimeError(f"Barrel producers not yet available: {', '.join(missing)}")
    return builders


def _overlap(first, second, first_box, second_box):
    if (
        min(first_box.xmax, second_box.xmax) - max(first_box.xmin, second_box.xmin) <= 0
        or min(first_box.ymax, second_box.ymax) - max(first_box.ymin, second_box.ymin)
        <= 0
        or min(first_box.zmax, second_box.zmax) - max(first_box.zmin, second_box.zmin)
        <= 0
    ):
        return 0.0
    volume = first.intersect(second).Volume()
    return round(volume, 6) if volume > 1.0 else 0.0


def _cross_family_hits(physical, paths):
    """Screen supplied finite solids; protected and same-family checks stay open."""
    boxes = {
        name: shape.BoundingBox() for name, (_, shape) in {**physical, **paths}.items()
    }
    physical_hits = {}
    for (first_name, (first_family, first)), (
        second_name,
        (second_family, second),
    ) in combinations(physical.items(), 2):
        if first_family == second_family:
            continue
        volume = _overlap(first, second, boxes[first_name], boxes[second_name])
        if volume:
            physical_hits[f"{first_name}|{second_name}"] = volume
    path_hits = {}
    for path_name, (path_family, path) in paths.items():
        for target_name, (target_family, target) in physical.items():
            if path_family == target_family:
                continue
            volume = _overlap(path, target, boxes[path_name], boxes[target_name])
            if volume:
                path_hits[f"{path_name}|{target_name}"] = volume
    return physical_hits, path_hits


def _add_unique(target, rows, label):
    if not isinstance(rows, dict):
        raise TypeError(f"{label} must be a name-to-object mapping")
    for name, item in rows.items():
        if name in target:
            raise ValueError(f"Duplicate {label} name: {name}")
        target[name] = item


def _validate_bolt(name, bolt):
    fields = ("start", "direction", "length", "diameter")
    if bolt.name != name or any(not hasattr(bolt, field) for field in fields):
        raise ValueError(f"{name}: bolt needs start/direction/length/diameter")
    try:
        start = bolt.start.toTuple()
        direction = bolt.direction.toTuple()
        length = float(bolt.length)
        diameter = float(bolt.diameter)
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(
            f"{name}: bolt needs start/direction/length/diameter"
        ) from error
    if (
        len(start) != 3
        or len(direction) != 3
        or not all(isfinite(value) for value in (*start, *direction, length, diameter))
        or sum(value * value for value in direction) <= 0
        or length <= 0
        or diameter <= 0
    ):
        raise ValueError(f"{name}: invalid diagnostic bolt axis")


def build_assembly(
    producers=None, *, source=None, placement=None, post_placement="outward"
):
    """Compose three producer poses without qualifying hardware or drilling."""
    producers = _default_builders() if producers is None else producers
    if set(producers) != set(FAMILY_STATIONS):
        raise ValueError(
            "Exactly rail10, center6, and outer_top8 producers are required"
        )
    source = variant(KERF_RIGHT) if source is None else source
    if post_placement not in ("outward", "original"):
        raise ValueError("Barrel post placement must be outward or original")
    placement = (
        posts.build_layout()
        if placement is None and post_placement == "outward"
        else placement
    )
    duties = ledger.selected_duties()
    expected = {station for names in FAMILY_STATIONS.values() for station in names}
    if len(expected) != 24 or set(duties) != expected:
        raise ValueError(
            "Three barrel families must partition the exact 24-duty ledger"
        )

    source_connections = tuple(source.connections())
    panel_connections = tuple(source.panel_connections())
    frame_connections = tuple(row for row in source_connections if row.kind == "bolt")
    legacy_names = {name for duty in duties.values() for name in duty["sds_axes"]}
    removed_legacy_sds = tuple(
        row for row in source_connections if row.name in legacy_names
    )
    all_names = [row.name for row in source_connections]
    if (
        len(panel_connections) != 66
        or len({row.name for row in panel_connections}) != 66
        or not {row.name for row in panel_connections} <= set(all_names)
        or len(frame_connections) != 12
        or len(legacy_names) != 144
        or len(removed_legacy_sds) != 144
        or len(set(all_names)) != len(all_names)
    ):
        raise ValueError("Kerf-right fixed and legacy connection inventory changed")

    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    for side, sign in (("left", -1), ("right", 1)):
        name = f"base_post_center_{side}"
        if post_placement == "outward":
            wood[name] = wood[name].translate(
                cq.Vector(placement["post_shift_x_mm"][side], 0, 0)
            )
        center = (wood[name].BoundingBox().xmin + wood[name].BoundingBox().xmax) / 2
        target = 180.0 if post_placement == "outward" else 70.0
        if abs(center - sign * target) > 1e-6:
            raise ValueError(
                f"Expected ±{target:g} mm center-post pose changed: {name}"
            )
        if post_placement == "outward":
            x0, x1 = placement["backer_bounds_x_mm"][side]
            wood[f"inner_kicker_backer_{side}"] = cq.Solid.makeBox(
                x1 - x0,
                posts.BACKER_FRONT_Y_MM - posts.BACKER_REAR_Y_MM,
                posts.BACKER_TOP_Z_MM,
                cq.Vector(x0, posts.BACKER_REAR_Y_MM, 0),
            )

    bolts, barrels, stacks, drilling, access = {}, {}, {}, {}, {}
    replacement_solids, station_modes, station_dispositions = {}, {}, {}
    bolt_station, barrel_station = {}, {}
    station_family, producer_diagnostics = {}, {}
    physical, paths = {}, {}
    provisional_offset = hardware.BARREL_LENGTH_MM / 2
    for family, names in FAMILY_STATIONS.items():
        report = producers[family](wood)
        rows = report["stations"]
        if set(rows) != set(names):
            raise ValueError(f"{family} does not cover its exact station duties")
        producer_diagnostics[family] = report.get("diagnostics", {})
        for station, row in rows.items():
            mode = row["mode"]
            block = row.get("compact_alternate_block")
            if mode != "direct":
                raise ValueError(f"{station}: barrel-only direct mode required")
            if block is not None:
                raise ValueError(f"{station}: barrel-only station contains a block")
            if abs(row["axis_offset_mm"] - provisional_offset) > 1e-6:
                raise ValueError(
                    f"{station}: barrel axis must use provisional 8.001 mm pose"
                )
            disposition = row["disposition"]
            if not isinstance(disposition, str) or not disposition:
                raise ValueError(f"{station}: missing layout disposition")
            row_bolts = row["bolts"]
            row_barrels = row["barrels"]
            row_stacks = row["stacks"]
            if not row_bolts or not row_barrels or set(row_stacks) != set(row_bolts):
                raise ValueError(f"{station}: incomplete bolt/barrel/stack inventory")
            for name, bolt in row_bolts.items():
                _validate_bolt(name, bolt)
            station_modes[station], station_family[station] = mode, family
            station_dispositions[station] = disposition
            replacement_solids[station] = (
                *row_barrels.values(),
                *(solid for roles in row_stacks.values() for solid in roles.values()),
            )
            _add_unique(bolts, row_bolts, "bolt")
            _add_unique(barrels, row_barrels, "barrel")
            bolt_station.update({name: station for name in row_bolts})
            barrel_station.update({name: station for name in row_barrels})
            _add_unique(stacks, row_stacks, "stack")
            _add_unique(drilling, row["drilling_paths"], "drilling path")
            _add_unique(access, row["access_paths"], "access path")
            for name, solid in row_barrels.items():
                physical[f"barrel/{name}"] = (family, solid)
            for name, roles in row_stacks.items():
                if not roles:
                    raise ValueError(f"{station}: empty bolt stack {name}")
                for role, solid in roles.items():
                    physical[f"bolt/{name}/{role}"] = (family, solid)
            for name, solid in row["drilling_paths"].items():
                paths[f"drill/{name}"] = (family, solid)
            for name, solid in row["access_paths"].items():
                paths[f"access/{name}"] = (family, solid)

    physical_hits, path_hits = _cross_family_hits(physical, paths)
    diagnostics = {
        "status": "REVISE",
        "wood_basis": (
            "Kerf-right uncut source members with "
            + (
                "approved ±180-mm posts and two kicker backers"
                if post_placement == "outward"
                else "original ±70-mm center posts and no added kicker backers"
            )
            + "; drill paths are envelopes, not cuts"
        ),
        "station_family": station_family,
        "producer_diagnostics": producer_diagnostics,
        "cross_family_physical_hits_mm3": physical_hits,
        "cross_family_drill_access_hits_mm3": path_hits,
        "cross_family_screen_scope": "Supplied physical solids and paths across producer families only",
        "unverified_gates": (
            "Same-family collisions and intended joint contacts",
            "Protected holds/T-nuts/unused holes and hold-bolt projection",
            "LED bodies, wire routing and bends",
            "66 panel screws and 12 retained frame bolts against all new solids",
            "Delivered barrel thread-axis, bore geometry, material and resistance",
            "Finished-wood complete bore coverage and drilling sequence",
            "Bolt thread engagement, nominal length, washer seats and driver access",
            "6-10 mm barrel-axis sensitivity, tolerances and wood net-section strength",
            (
                "Backer structural attachment and complete changed-topology load path"
                if post_placement == "outward"
                else "Original-post kicker screw support and complete load path"
            ),
        ),
    }
    return {
        "post_placement": post_placement,
        "wood": wood,
        "replacement_solids": replacement_solids,
        "barrels": barrels,
        "barrel_solids": barrels,
        "barrel_station": barrel_station,
        "bolts": bolts,
        "diagnostic_bolt_axes": bolts,
        "bolt_station": bolt_station,
        "stacks": stacks,
        "drilling_paths": drilling,
        "access_paths": access,
        "station_modes": station_modes,
        "station_dispositions": station_dispositions,
        "removed_legacy_stations": tuple(sorted(expected)),
        "removed_legacy_sds": removed_legacy_sds,
        "panel_connections": panel_connections,
        "frame_connections": frame_connections,
        "hardware_basis": {
            "status": "provisional_uncontrolled_retail_identity_only",
            "barrel_model": "Hillman 880543",
            "barrel_length_mm": hardware.BARREL_LENGTH_MM,
            "barrel_od_mm": hardware.BARREL_OD_MM,
            "thread_major_mm": hardware.THREAD_MAJOR_MM,
            "axis_offset_mm_provisional": provisional_offset,
            "axis_offset_sensitivity_mm": hardware.AXIS_OFFSET_SENSITIVITY_MM,
            "bolt_lengths_mm_nominal_trials": sorted(
                {round(float(bolt.length), 6) for bolt in bolts.values()}
            ),
            "washer_thickness_mm_unverified": hardware.WASHER_THICKNESS_SENSITIVITY_MM,
        },
        "diagnostics": diagnostics,
        "release_flags": dict(_NO_RELEASE),
    }
