"""PB04 active geometry adapter; no solve, resistance, or release."""

import hashlib
import json
import math
from dataclasses import replace

from scripts import simple_pb03_outer_counterbore_revision as counterbore
from scripts import simple_pb03_upper_outer_edge_revision as upper_revision
from scripts.simple_center_pb02_native import PB02Native
from scripts.simple_pb03_lower_center_pair import TARGET_STATIONS as CENTER_STATIONS
from scripts.simple_pb03_native import (
    BLOCK_NAMES,
    REPLACED_STATIONS,
    PB03Native,
    _block_part,
)

SOURCE_ID = "pb04-upper-edge-plus-outer-counterbores-v1"
MINIMUM_COMBINED_CLEARANCE_MM = 3.0
SELECTED_OFFSET_MM = (
    upper_revision.lower.UPRIGHT_N_OFFSETS_MM[0]
    - counterbore.FORSTNER_DIAMETER_MM / 2
    - upper_revision.BORE_DIAMETER_MM / 2
    - MINIMUM_COMBINED_CLEARANCE_MM
)


def _same_shape(first, second):
    return first.distance(second) <= 1.0e-8 and math.isclose(
        first.Volume(), second.Volume(), abs_tol=1.0e-5
    )


def _box_signature(shape):
    bounds = shape.BoundingBox()
    return [
        round(value, 6)
        for value in (
            bounds.xmin,
            bounds.xmax,
            bounds.ymin,
            bounds.ymax,
            bounds.zmin,
            bounds.zmax,
        )
    ]


class PB04Native(PB03Native):
    """PB03 with the selected upper edge offset and twelve nut-side pockets."""

    KEY = SOURCE_ID

    def __init__(self):
        super().__init__()
        revised = upper_revision._build(SELECTED_OFFSET_MM)
        if tuple(revised) != REPLACED_STATIONS:
            raise ValueError("PB04 eight-station source inventory changed")
        _, counterbored = counterbore.build_counterbored_blocks(revised)
        self._pb03_geometries = revised
        self._pb04_uncut_blocks = tuple(
            _block_part(geometry) for geometry in revised.values()
        )
        self._blocks = tuple(
            _block_part(
                replace(
                    geometry,
                    block=counterbored.get(station, geometry.block),
                )
            )
            for station, geometry in revised.items()
        )
        self._pb03_bolts = tuple(
            bolt for geometry in revised.values() for bolt in geometry.bolts
        )
        self._pb03_bolt_points = self._build_pb03_bolt_interface_points()

    def uncut_wood_parts(self):
        """Use gross external blocks for beam records; machined solids stay visible."""
        uncut = getattr(self, "_pb04_uncut_blocks", None)
        if uncut is None:
            return super().uncut_wood_parts()
        return (*PB02Native.uncut_wood_parts(self), *uncut)

    def block_part_names(self):
        return tuple(part.name for part in self._blocks)

    def validate_prepared_case(self, structure, metadata):
        """Retain PB03 preparation gates and bind them to the PB04 source."""
        super().validate_prepared_case(structure, metadata)
        metadata.update(
            pb04_candidate=SOURCE_ID,
            pb04_preparation_validated=True,
            qualified_for_design=False,
            acceptance=False,
            drilling_released=False,
            fabrication_released=False,
            preparation_only=True,
            developmental_only=True,
        )


def _source_fingerprint(module):
    parts = {part.name: part.shape for part in module.wood_parts()}
    payload = {
        "source_id": SOURCE_ID,
        "parent_source_id": PB03Native.KEY,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "stations": list(module.pb03_geometries()),
        "blocks": {
            name: {
                "box_mm": _box_signature(parts[name]),
                "volume_mm3": round(parts[name].Volume(), 6),
            }
            for name in sorted(BLOCK_NAMES.values())
        },
        "bolts": [
            {
                "name": row.name,
                "start_mm": [round(value, 6) for value in row.start.toTuple()],
                "axis": [round(value, 9) for value in row.direction.toTuple()],
                "diameter_mm": row.diameter,
                "members": list(row.members),
            }
            for row in module.connections()
            if row.name.startswith("pb03_")
        ],
        "counterbore_depth_mm": counterbore._required_depth_mm(),
        "counterbore_diameter_mm": counterbore.FORSTNER_DIAMETER_MM,
        "upper_outer_rail_offset_mm": SELECTED_OFFSET_MM,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def screen(module=None):
    """Authenticate the combined PB04 geometry and retain every no-release gate."""
    module = PB04Native() if module is None else module
    if (
        module.KEY != SOURCE_ID
        or module.ACTIVE_FINGERPRINT != PB03Native.ACTIVE_FINGERPRINT
    ):
        raise ValueError("PB04 source identity changed")

    upper_result = upper_revision.analyze_revision()
    pocket_result = counterbore.screen(
        module=module,
        expected_source_id=SOURCE_ID,
    )
    parent = PB03Native()
    geometries = module.pb03_geometries()
    parent_geometries = parent.pb03_geometries()
    parts = {part.name: part.shape for part in module.wood_parts()}
    _, expected_blocks = counterbore.build_counterbored_blocks(geometries)
    local_geometry = upper_revision.lower._screen_targets(
        geometries, REPLACED_STATIONS, "simple_pb04_native/v1"
    )
    revised_pair = {
        name: geometries[name] for name in upper_revision.upper.TARGET_STATIONS
    }
    other_six = {
        name: geometry
        for name, geometry in geometries.items()
        if name not in revised_pair
    }
    cross_geometry = upper_revision.cross_family.screen_cross_family(
        revised_pair, other_six
    )

    center_unchanged = all(
        _same_shape(geometries[name].block, parent_geometries[name].block)
        and all(
            new == old
            for new, old in zip(
                geometries[name].bolts,
                parent_geometries[name].bolts,
                strict=True,
            )
        )
        for name in CENTER_STATIONS
    )
    actual_counterbores = all(
        _same_shape(parts[geometries[name].block_name], expected_blocks[name])
        for name in counterbore.TARGET_STATIONS
    )
    external_boxes_preserved = all(
        _box_signature(parts[geometry.block_name]) == _box_signature(geometry.block)
        for geometry in geometries.values()
    )
    connections = module.connections()
    inventory = {
        "pb03_stations": len(geometries),
        "counterbored_outer_blocks": len(counterbore.TARGET_STATIONS),
        "unchanged_lower_center_blocks": len(CENTER_STATIONS),
        "counterbores": 12,
        "through_bolt_axes": sum(row.name.startswith("pb03_") for row in connections),
        "legacy_proxy_stations": len(module.legacy_proxy_stations()),
        "legacy_sds_axes": sum(row.name.startswith("clip_") for row in connections),
        "fixed_panel_kicker_axes": len(module.panel_connections()),
        "total_connections": len(connections),
    }
    expected_inventory = {
        "pb03_stations": 8,
        "counterbored_outer_blocks": 6,
        "unchanged_lower_center_blocks": 2,
        "counterbores": 12,
        "through_bolt_axes": 32,
        "legacy_proxy_stations": 14,
        "legacy_sds_axes": 84,
        "fixed_panel_kicker_axes": 66,
        "total_connections": 194,
    }
    edge_rows = upper_revision._edge_rows(
        upper_revision._accepted_edge_forces(), SELECTED_OFFSET_MM
    )
    minimum_loaded_edge_reserve = min(
        row["loaded_edge_reserve_mm"] for row in edge_rows
    )
    minimum_bore_clearance = pocket_result["governing_ligaments_mm"][
        "pocket_to_unintended_bore"
    ]
    minimum_stack_clearance = pocket_result["governing_ligaments_mm"][
        "pocket_to_preserved_stack"
    ]
    intervals = upper_result["feasible_offset_intervals_mm"]
    expected_intervals = [[28.4, 51.159], [109.159, 111.3]]
    lower_passing_end = (
        upper_revision.lower.UPRIGHT_N_OFFSETS_MM[0]
        - counterbore.FORSTNER_DIAMETER_MM / 2
        - upper_revision.BORE_DIAMETER_MM / 2
        - MINIMUM_COMBINED_CLEARANCE_MM
    )
    upper_passing_start = (
        upper_revision.lower.UPRIGHT_N_OFFSETS_MM[1]
        + counterbore.FORSTNER_DIAMETER_MM / 2
        + upper_revision.BORE_DIAMETER_MM / 2
        + MINIMUM_COMBINED_CLEARANCE_MM
    )
    search = {
        "authenticated_edge_intervals_mm": intervals,
        "combined_clearance_requirement_mm": MINIMUM_COMBINED_CLEARANCE_MM,
        "passing_intervals_mm": [
            [intervals[0][0], round(min(intervals[0][1], lower_passing_end), 6)]
        ],
        "rejected_upper_interval_required_start_mm": upper_passing_start,
        "selected_offset_mm": SELECTED_OFFSET_MM,
        "selection_rule": (
            "closest to 125 mm among combined geometries retaining at least "
            "3.0 mm loaded-edge and counterbore clearance"
        ),
    }
    source_gates = (
        center_unchanged
        and actual_counterbores
        and external_boxes_preserved
        and inventory == expected_inventory
        and intervals == expected_intervals
        and math.isclose(SELECTED_OFFSET_MM, lower_passing_end, abs_tol=1.0e-9)
    )
    if not source_gates:
        raise ValueError("PB04 source inventory or composed solids changed")
    cross_interaction_hits = {
        "counterbore_to_unintended_bore_mm3": pocket_result[
            "pocket_unintended_bore_hits_mm3"
        ],
        "counterbore_to_preserved_stack_mm3": pocket_result[
            "pocket_preserved_stack_hits_mm3"
        ],
    }
    combined_geometry_passes = (
        pocket_result["all_geometry_checks_pass"]
        and local_geometry["all_geometry_gates_pass"]
        and cross_geometry["all_cross_family_collision_gates_pass"]
        and not any(cross_interaction_hits.values())
        and minimum_loaded_edge_reserve >= MINIMUM_COMBINED_CLEARANCE_MM - 1.0e-8
        and minimum_bore_clearance >= MINIMUM_COMBINED_CLEARANCE_MM - 1.0e-8
        and minimum_stack_clearance >= MINIMUM_COMBINED_CLEARANCE_MM - 1.0e-8
    )
    if not combined_geometry_passes:
        raise ValueError("PB04 has no viable combined-offset integration")
    return {
        "schema": "simple_pb04_native/v1",
        "pb04_source_id": SOURCE_ID,
        "parent_pb03_source_id": PB03Native.KEY,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "source_fingerprint_sha256": _source_fingerprint(module),
        "upper_revision_schema": upper_result["schema"],
        "counterbore_revision_schema": pocket_result["schema"],
        "upper_outer_rail_offset_mm": SELECTED_OFFSET_MM,
        "counterbore_depth_mm": counterbore._required_depth_mm(),
        "counterbore_diameter_mm": counterbore.FORSTNER_DIAMETER_MM,
        "inventory": inventory,
        "offset_search": search,
        "minimum_clearances_mm": {
            "loaded_edge_reserve": minimum_loaded_edge_reserve,
            "counterbore_to_unintended_bore": minimum_bore_clearance,
            "counterbore_to_preserved_stack": minimum_stack_clearance,
        },
        "unchanged_lower_center_blocks": center_unchanged,
        "actual_counterbored_block_solids_exposed": actual_counterbores,
        "external_block_boxes_preserved": external_boxes_preserved,
        "eight_station_cad_gates_pass": local_geometry["all_geometry_gates_pass"],
        "cross_family_cad_gates_pass": cross_geometry[
            "all_cross_family_collision_gates_pass"
        ],
        "cross_interaction_hits": cross_interaction_hits,
        "combined_geometry_gates_pass": combined_geometry_passes,
        "decision": "PASS_COMBINED_GEOMETRY_ONLY",
        "native_preparation_supported": True,
        "exact_retail_hardware_selected": False,
        "strength_checked": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
