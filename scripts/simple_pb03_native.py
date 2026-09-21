"""PB03 adapter for six converted service-rail stations; no solve or release."""

from mini_moonboard.box_frame import Part
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_pb02_native import PB02Native
from scripts.simple_pb03_bottom_outer_pair import (
    BLOCK_NAMES as BOTTOM_BLOCK_NAMES,
)
from scripts.simple_pb03_bottom_outer_pair import (
    TARGET_STATIONS as BOTTOM_TARGET_STATIONS,
)
from scripts.simple_pb03_bottom_outer_pair import build_pair as build_bottom_outer_pair
from scripts.simple_pb03_bottom_outer_pair import screen as screen_bottom_outer_pair
from scripts.simple_pb03_lower_center_pair import (
    ALL_BLOCK_NAMES as LOWER_BLOCK_NAMES,
)
from scripts.simple_pb03_lower_center_pair import (
    ALL_TARGET_STATIONS as LOWER_TARGET_STATIONS,
)
from scripts.simple_pb03_lower_center_pair import (
    build_core_slice,
    screen_core_slice,
)
from scripts.simple_pb03_upper_outer_pair import (
    BLOCK_NAMES as UPPER_BLOCK_NAMES,
)
from scripts.simple_pb03_upper_outer_pair import (
    TARGET_STATIONS as UPPER_TARGET_STATIONS,
)
from scripts.simple_pb03_upper_outer_pair import build_pair as build_upper_outer_pair
from scripts.simple_pb03_upper_outer_pair import screen as screen_upper_outer_pair

REPLACED_STATIONS = (
    *LOWER_TARGET_STATIONS,
    *UPPER_TARGET_STATIONS,
    *BOTTOM_TARGET_STATIONS,
)
BLOCK_NAMES = {
    **LOWER_BLOCK_NAMES,
    **UPPER_BLOCK_NAMES,
    **BOTTOM_BLOCK_NAMES,
}
SOURCE_ID = "pb03-lower-service-plus-upper-and-bottom-outer-v1"


def _block_part(geometry):
    block_x, block_t, block_length = geometry.report["block_dimensions_mm"]
    return Part(
        geometry.block_name,
        geometry.block,
        (block_length, block_x, block_t),
        "PB03 developmental solid timber corner block; exact stock, hardware, "
        "resistance, drilling, and fabrication are unselected",
        1,
    )


class PB03Native(PB02Native):
    """PB02 plus eight blocks and thirty-two unselected through-bolt stacks."""

    KEY = SOURCE_ID
    ACTIVE_FINGERPRINT = ACTIVE_FINGERPRINT

    def __init__(self):
        super().__init__()
        base_parts = tuple(PB02Native.uncut_wood_parts(self))
        base_finished_parts = tuple(PB02Native.wood_parts(self))
        base_connections = tuple(PB02Native.connections(self))
        base_stations = tuple(PB02Native.stations(self))
        panel_names = {row.name for row in self.raw.panel_connections()}
        base_panels = tuple(row for row in base_connections if row.name in panel_names)
        source = {
            "parts": {part.name: part.shape for part in base_parts},
            "finished_parts": {part.name: part.shape for part in base_finished_parts},
            "panel_connections": base_panels,
            "stations": base_stations,
            "connections": base_connections,
        }
        self._lower_service = build_core_slice(**source)
        self._upper_outer = build_upper_outer_pair(**source)
        self._bottom_outer = build_bottom_outer_pair(**source)
        self._pb03_geometries = {
            **self._lower_service,
            **self._upper_outer,
            **self._bottom_outer,
        }
        self._blocks = tuple(
            _block_part(geometry) for geometry in self._pb03_geometries.values()
        )
        self._pb03_bolts = tuple(
            bolt
            for geometry in self._pb03_geometries.values()
            for bolt in geometry.bolts
        )
        self._base_connections = base_connections
        self._base_stations = base_stations

    def uncut_wood_parts(self):
        return (*PB02Native.uncut_wood_parts(self), *self._blocks)

    def wood_parts(self):
        return (*PB02Native.wood_parts(self), *self._blocks)

    def current_response_wood_parts(self):
        return (*PB02Native.current_response_wood_parts(self), *self._blocks)

    def parts(self):
        retained = tuple(
            part
            for part in PB02Native.parts(self)
            if part.name not in REPLACED_STATIONS
        )
        return (*retained, *self._blocks)

    def connections(self):
        retained = tuple(
            row
            for row in self._base_connections
            if not any(
                row.name.startswith(f"{station}_") for station in REPLACED_STATIONS
            )
        )
        return (*retained, *self._pb03_bolts)

    def stations(self):
        return tuple(
            row for row in self._base_stations if row[0] not in REPLACED_STATIONS
        )

    def legacy_proxy_stations(self):
        return tuple(row[0] for row in self.stations())

    def pb03_geometries(self):
        """Return the complete declared PB03 geometry without exposing internals."""
        return dict(self._pb03_geometries)


def screen(module=None):
    """Authenticate the exact bounded mutation and retain all no-release flags."""
    module = PB03Native() if module is None else module
    lower = screen_core_slice(module._lower_service)
    upper = screen_upper_outer_pair(
        module._upper_outer, lower_reference=module._lower_service
    )
    existing = {**module._lower_service, **module._upper_outer}
    bottom = screen_bottom_outer_pair(module._bottom_outer, existing_reference=existing)
    connections = module.connections()
    stations = module.stations()
    panels = module.panel_connections()
    legacy_sds = sum(row.name.startswith("clip_") for row in connections)
    new_bolts = [row for row in connections if row.name.startswith("pb03_")]
    blocks = {part.name for part in module.uncut_wood_parts()} & set(
        BLOCK_NAMES.values()
    )
    gates = (
        lower["all_geometry_gates_pass"]
        and upper["all_geometry_gates_pass"]
        and upper["all_lower_family_collision_gates_pass"]
        and bottom["all_geometry_gates_pass"]
        and bottom["all_cross_family_collision_gates_pass"]
        and len(stations) == 14
        and legacy_sds == 84
        and len(blocks) == 8
        and len(new_bolts) == 32
        and len(panels) == 66
        and len(connections) == 194
        and sum(row.kind == "bolt" for row in connections) == 44
        and not ({row[0] for row in stations} & set(REPLACED_STATIONS))
    )
    if not gates:
        raise ValueError("PB03 composed service inventory or geometry gate changed")
    return {
        "schema": "simple_pb03_native/v1",
        "pb03_source_id": SOURCE_ID,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "replaced_legacy_stations": list(REPLACED_STATIONS),
        "legacy_proxy_stations": len(stations),
        "legacy_sds_axes": legacy_sds,
        "new_timber_blocks": len(blocks),
        "new_through_bolt_stacks": len(new_bolts),
        "fixed_panel_kicker_axes": len(panels),
        "total_connections": len(connections),
        "total_bolt_connections": sum(row.kind == "bolt" for row in connections),
        "lower_service_geometry_gates_pass": lower["all_geometry_gates_pass"],
        "upper_outer_geometry_gates_pass": upper["all_upper_pair_geometry_gates_pass"],
        "bottom_outer_geometry_gates_pass": bottom[
            "all_bottom_pair_geometry_gates_pass"
        ],
        "cross_family_collision_gates_pass": upper[
            "all_lower_family_collision_gates_pass"
        ]
        and bottom["all_cross_family_collision_gates_pass"],
        "geometry_gates_pass": True,
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
