"""PB03 upper-service center mirrored pair; geometry only, no release."""

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross_family
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper

TARGET_STATIONS = (
    "clip_horizontal_upper_left_2",
    "clip_horizontal_upper_right_1",
)
BLOCK_NAMES = {
    TARGET_STATIONS[0]: "pb03_upper_center_left_block",
    TARGET_STATIONS[1]: "pb03_upper_center_right_block",
}
STATION_SPECS = {
    TARGET_STATIONS[0]: lower.StationSpec(
        TARGET_STATIONS[0],
        "left",
        "left",
        "right",
        "base_principal_center_left",
        "base_rail_service_upper_left",
        BLOCK_NAMES[TARGET_STATIONS[0]],
        "pb03_upper_center_left",
    ),
    TARGET_STATIONS[1]: lower.StationSpec(
        TARGET_STATIONS[1],
        "right",
        "right",
        "left",
        "base_principal_center_right",
        "base_rail_service_upper_right",
        BLOCK_NAMES[TARGET_STATIONS[1]],
        "pb03_upper_center_right",
    ),
}
RAIL_N_OFFSET_MM = 125.0


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
    """Build both upper-center stations from actual kerf-right PB02 members."""
    supplied = (parts, finished_parts, panel_connections, stations, connections)
    if any(value is None for value in supplied):
        if not all(value is None for value in supplied):
            raise ValueError(
                "PB03 upper-center source inventory must be supplied completely"
            )
        parts, finished_parts, panel_connections, stations, connections = (
            _source_inventory()
        )
    if lower.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT:
        raise ValueError(
            "PB02 geometry fingerprint changed before PB03 upper-center pair"
        )
    if set(parts) != set(finished_parts):
        raise ValueError("PB03 upper-center uncut and finished inventories differ")
    if (
        len([name for name in finished_parts if name.startswith(("main_", "kicker_"))])
        != 6
    ):
        raise ValueError(
            "PB03 upper-center requires six explicit finished panel solids"
        )
    station_names = {row[0] for row in stations}
    if len(station_names) != 22 or not set(TARGET_STATIONS) <= station_names:
        raise ValueError(
            "PB03 upper-center requires the exact 22-station PB02 inventory"
        )
    target_sds = [
        row
        for row in connections
        if any(row.name.startswith(f"{name}_") for name in TARGET_STATIONS)
    ]
    if len(target_sds) != 12 or any(row.kind != "screw" for row in target_sds):
        raise ValueError(
            "PB03 upper-center target stations must own exactly 12 SDS axes"
        )
    required = {
        member
        for spec in STATION_SPECS.values()
        for member in (spec.upright_name, spec.rail_name)
    }
    if not required <= set(parts):
        raise ValueError("PB03 upper-center target member inventory changed")
    fixed_axes = lower._fixed_axis_solids(panel_connections)
    return {
        name: lower._build_station(
            STATION_SPECS[name],
            parts,
            finished_parts,
            fixed_axes,
            rail_n_offset_mm=RAIL_N_OFFSET_MM,
        )
        for name in TARGET_STATIONS
    }


def build_existing_reference():
    """Build all eight PB03 geometries currently present in the native adapter."""
    return {
        **lower.build_core_slice(),
        **upper.build_pair(),
        **bottom.build_pair(),
    }


def screen(pair=None, *, existing_reference=None):
    """Fail closed on local geometry and interactions with all current PB03 work."""
    pair = build_pair() if pair is None else pair
    existing_reference = (
        build_existing_reference() if existing_reference is None else existing_reference
    )
    local = lower._screen_targets(
        pair, TARGET_STATIONS, "simple_pb03_upper_center_pair/v1"
    )
    cross = cross_family.screen_cross_family(pair, existing_reference)
    block_clearances = {
        name: min(
            item.block.distance(reference.block)
            for reference in existing_reference.values()
        )
        for name, item in pair.items()
    }
    result = {
        **local,
        **cross,
        "reference_station_count": len(existing_reference),
        "nearest_existing_block_clearance_mm": block_clearances,
        "all_upper_center_pair_geometry_gates_pass": local["all_geometry_gates_pass"],
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
    result["all_geometry_gates_pass"] = (
        result["all_upper_center_pair_geometry_gates_pass"]
        and result["all_cross_family_collision_gates_pass"]
        and result["reference_station_count"] == 8
    )
    return result
