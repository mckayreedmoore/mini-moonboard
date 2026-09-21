"""PB03 upper-service outer mirrored pair; geometry only, no release."""

from scripts import simple_pb03_cross_family as cross_family
from scripts import simple_pb03_lower_center_pair as lower

TARGET_STATIONS = (
    "clip_horizontal_upper_left_1",
    "clip_horizontal_upper_right_2",
)
BLOCK_NAMES = {
    TARGET_STATIONS[0]: "pb03_upper_outer_left_block",
    TARGET_STATIONS[1]: "pb03_upper_outer_right_block",
}
STATION_SPECS = {
    TARGET_STATIONS[0]: lower.StationSpec(
        TARGET_STATIONS[0],
        "left",
        "right",
        "left",
        "base_side_left",
        "base_rail_service_upper_left",
        BLOCK_NAMES[TARGET_STATIONS[0]],
        "pb03_upper_outer_left",
    ),
    TARGET_STATIONS[1]: lower.StationSpec(
        TARGET_STATIONS[1],
        "right",
        "left",
        "right",
        "base_side_right",
        "base_rail_service_upper_right",
        BLOCK_NAMES[TARGET_STATIONS[1]],
        "pb03_upper_outer_right",
    ),
}
SAME_SIDE_LOWER_STATIONS = {
    "left": lower.LOWER_OUTER_STATIONS[0],
    "right": lower.LOWER_OUTER_STATIONS[1],
}
UPPER_RAIL_N_OFFSET_MM = 125.0


def _source_inventory():
    """Expose the authenticated PB02 source inventory for bounded test injection."""
    return lower._source_inventory()


def build_pair(
    *,
    parts=None,
    finished_parts=None,
    panel_connections=None,
    stations=None,
    connections=None,
):
    """Build both upper outer stations from the actual kerf-right members."""
    supplied = (
        parts,
        finished_parts,
        panel_connections,
        stations,
        connections,
    )
    if any(value is None for value in supplied):
        if not all(value is None for value in supplied):
            raise ValueError("PB03 upper source inventory must be supplied completely")
        parts, finished_parts, panel_connections, stations, connections = (
            _source_inventory()
        )
    if lower.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT:
        raise ValueError("PB02 geometry fingerprint changed before PB03 upper pair")
    if set(parts) != set(finished_parts):
        raise ValueError("PB03 upper uncut and finished inventories differ")
    if (
        len([name for name in finished_parts if name.startswith(("main_", "kicker_"))])
        != 6
    ):
        raise ValueError("PB03 upper requires six explicit finished panel solids")
    station_names = {row[0] for row in stations}
    if len(station_names) != 22 or not set(TARGET_STATIONS) <= station_names:
        raise ValueError("PB03 upper requires the exact 22-station PB02 inventory")
    target_sds = [
        row
        for row in connections
        if any(row.name.startswith(f"{name}_") for name in TARGET_STATIONS)
    ]
    if len(target_sds) != 12 or any(row.kind != "screw" for row in target_sds):
        raise ValueError("PB03 upper target stations must own exactly 12 SDS axes")
    required = {
        member
        for spec in STATION_SPECS.values()
        for member in (spec.upright_name, spec.rail_name)
    }
    if not required <= set(parts):
        raise ValueError("PB03 upper target member inventory changed")
    fixed_axes = lower._fixed_axis_solids(panel_connections)
    # Stagger the upper rail bores within the actual 139.7-mm rail depth. The
    # lower pair uses 80.159 mm; repeating it blocks the 40-mm service paths.
    return {
        name: lower._build_station(
            STATION_SPECS[name],
            parts,
            finished_parts,
            fixed_axes,
            rail_n_offset_mm=UPPER_RAIL_N_OFFSET_MM,
        )
        for name in TARGET_STATIONS
    }


def build_lower_reference():
    """Build the existing four lower-service stations for collision screening."""
    return lower.build_core_slice()


def screen(pair=None, *, lower_reference=None):
    """Fail closed on local geometry and every upper/lower family interaction."""
    pair = build_pair() if pair is None else pair
    lower_reference = (
        build_lower_reference() if lower_reference is None else lower_reference
    )
    local = lower._screen_targets(
        pair, TARGET_STATIONS, "simple_pb03_upper_outer_pair/v1"
    )
    cross = cross_family.screen_cross_family(pair, lower_reference)
    clearances = {
        side: pair[TARGET_STATIONS[index]].block.distance(
            lower_reference[SAME_SIDE_LOWER_STATIONS[side]].block
        )
        for index, side in enumerate(("left", "right"))
    }
    lower_clear = cross["all_cross_family_collision_gates_pass"]
    legacy_tool_hits = {
        **cross["cross_family_tool_block_hits_mm3"],
        **cross["cross_family_tool_stack_hits_mm3"],
        **cross["cross_family_tool_tool_hits_mm3"],
    }
    result = {
        **local,
        **cross,
        # Compatibility aliases for the composed adapter and existing reports.
        "lower_family_bore_hits_mm3": cross["cross_family_bore_hits_mm3"],
        "lower_family_block_hits_mm3": cross["cross_family_block_hits_mm3"],
        "lower_family_stack_block_hits_mm3": cross["cross_family_stack_block_hits_mm3"],
        "lower_family_stack_component_hits_mm3": cross[
            "cross_family_stack_component_hits_mm3"
        ],
        "lower_family_tool_hits_mm3": legacy_tool_hits,
        "same_side_lower_block_clearance_mm": clearances,
        "all_upper_pair_geometry_gates_pass": local["all_geometry_gates_pass"],
        "all_lower_family_collision_gates_pass": lower_clear,
        "qualified_for_design": False,
        "exact_retail_hardware_selected": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    result["all_geometry_gates_pass"] = (
        result["all_upper_pair_geometry_gates_pass"] and lower_clear
    )
    return result
