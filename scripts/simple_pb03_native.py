"""PB03 adapter for both lower-service pairs; no solve or release."""

from mini_moonboard.box_frame import Part
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_pb02_native import PB02Native
from scripts.simple_pb03_lower_center_pair import (
    ALL_BLOCK_NAMES,
    ALL_TARGET_STATIONS,
    BLOCK_LENGTH_MM,
    build_core_slice,
    screen_core_slice,
)


class PB03Native(PB02Native):
    """PB02 plus four blocks and sixteen unselected through-bolt stacks."""

    KEY = "pb03-lower-service-core-development-only"
    ACTIVE_FINGERPRINT = ACTIVE_FINGERPRINT

    def __init__(self):
        super().__init__()
        base_parts = tuple(PB02Native.uncut_wood_parts(self))
        base_finished_parts = tuple(PB02Native.wood_parts(self))
        base_connections = tuple(PB02Native.connections(self))
        base_stations = tuple(PB02Native.stations(self))
        panel_names = {row.name for row in self.raw.panel_connections()}
        base_panels = tuple(row for row in base_connections if row.name in panel_names)
        self._pair = build_core_slice(
            parts={part.name: part.shape for part in base_parts},
            finished_parts={part.name: part.shape for part in base_finished_parts},
            panel_connections=base_panels,
            stations=base_stations,
            connections=base_connections,
        )
        self._blocks = tuple(
            Part(
                geometry.block_name,
                geometry.block,
                (BLOCK_LENGTH_MM, 139.7, 57.15),
                "PB03 developmental solid timber corner block; exact stock, "
                "hardware, resistance, drilling, and fabrication are unselected",
                1,
            )
            for geometry in self._pair.values()
        )
        self._pb03_bolts = tuple(
            bolt for geometry in self._pair.values() for bolt in geometry.bolts
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
            if part.name not in ALL_TARGET_STATIONS
        )
        return (*retained, *self._blocks)

    def connections(self):
        retained = tuple(
            row
            for row in self._base_connections
            if not any(
                row.name.startswith(f"{station}_")
                for station in ALL_TARGET_STATIONS
            )
        )
        return (*retained, *self._pb03_bolts)

    def stations(self):
        return tuple(
            row for row in self._base_stations if row[0] not in ALL_TARGET_STATIONS
        )

    def legacy_proxy_stations(self):
        return tuple(row[0] for row in self.stations())


def screen(module=None):
    """Authenticate the exact bounded mutation and retain all no-release flags."""
    module = PB03Native() if module is None else module
    pair = screen_core_slice(module._pair)
    connections = module.connections()
    stations = module.stations()
    panels = module.panel_connections()
    legacy_sds = sum(row.name.startswith("clip_") for row in connections)
    new_bolts = [row for row in connections if row.name.startswith("pb03_")]
    blocks = {part.name for part in module.uncut_wood_parts()} & set(
        ALL_BLOCK_NAMES.values()
    )
    gates = (
        pair["all_geometry_gates_pass"]
        and len(stations) == 18
        and legacy_sds == 108
        and len(blocks) == 4
        and len(new_bolts) == 16
        and len(panels) == 66
        and len(connections) == 202
        and sum(row.kind == "bolt" for row in connections) == 28
        and not ({row[0] for row in stations} & set(ALL_TARGET_STATIONS))
    )
    if not gates:
        raise ValueError("PB03 lower-service inventory or geometry gate changed")
    return {
        "schema": "simple_pb03_native/v1",
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "legacy_proxy_stations": len(stations),
        "legacy_sds_axes": legacy_sds,
        "new_timber_blocks": len(blocks),
        "new_through_bolt_stacks": len(new_bolts),
        "fixed_panel_kicker_axes": len(panels),
        "total_connections": len(connections),
        "total_bolt_connections": sum(row.kind == "bolt" for row in connections),
        "geometry_gates_pass": True,
        "exact_retail_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
    }
