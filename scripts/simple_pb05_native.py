"""PB05 narrow no-pocket native geometry; preparation only, no solve or release."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from mini_moonboard.box_frame import Part
from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_native as pb03
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb04_native as pb04
from scripts.simple_pb03_native import REPLACED_STATIONS, PB03Native

SOURCE_ID = "pb05-six-narrow-no-pocket-outer-v1"
OUTER_STATIONS = (
    *lower.LOWER_OUTER_STATIONS,
    *upper.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)
BLOCK_X_MM = 95.25
RAIL_X_OFFSETS_MM = (25.0, 70.0)


def _axis(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.members,
        row.kind,
        row.grip,
    )


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _shape(shape):
    box = shape.BoundingBox()
    return {
        "box_mm": [
            round(value, 6)
            for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
        ],
        "volume_mm3": round(shape.Volume(), 6),
    }


class PB05Native(PB03Native):
    """Replace six PB03 outers with narrow solids; keep PB04-identical centers."""

    KEY = SOURCE_ID
    OUTER_STATIONS = OUTER_STATIONS

    def __init__(self):
        super().__init__()
        if (
            self.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
            or set(self._pb03_geometries) != set(REPLACED_STATIONS)
            or len(self.legacy_proxy_stations()) != 14
        ):
            raise ValueError("PB05 source inventory changed")
        parts, finished, panels, _, _ = lower._source_inventory()
        if len(panels) != 66:
            raise ValueError("PB05 fixed panel axes changed")
        axes = lower._fixed_axis_solids(panels)
        specs = {**lower.STATION_SPECS, **upper.STATION_SPECS, **bottom.STATION_SPECS}
        # ponytail: producer constants are scoped to the six detached rebuilds.
        with (
            patch.object(lower, "BLOCK_X_MM", BLOCK_X_MM),
            patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_OFFSETS_MM),
        ):
            outer = {
                name: lower._build_station(
                    specs[name],
                    parts,
                    finished,
                    axes,
                    rail_n_offset_mm=(
                        pb04.SELECTED_OFFSET_MM
                        if name in upper.TARGET_STATIONS
                        else lower.RAIL_N_OFFSET_MM
                    ),
                )
                for name in OUTER_STATIONS
            }
        self._pb03_geometries = {**self._pb03_geometries, **outer}
        self._blocks = tuple(
            Part(
                row.block_name,
                row.block,
                (row.block_length_mm, *row.report["block_dimensions_mm"][:2]),
                "PB05 developmental solid timber block; hardware and drilling unselected",
                1,
            )
            for row in self._pb03_geometries.values()
        )
        self._pb03_bolts = tuple(
            bolt for row in self._pb03_geometries.values() for bolt in row.bolts
        )
        self._pb03_bolt_points = self._build_pb03_bolt_interface_points()

    def validate_prepared_case(self, structure, metadata):
        PB03Native.validate_prepared_case(self, structure, metadata)
        metadata.update(
            pb05_candidate=SOURCE_ID,
            pb05_preparation_validated=True,
            solved=False,
            force_transfer=False,
            qualified_for_design=False,
            acceptance=False,
            drilling_released=False,
            fabrication_released=False,
            structural_released=False,
            preparation_only=True,
            developmental_only=True,
        )


def screen(module=None):
    """Bind PB05 geometry and retained axes without importing case mechanics."""
    module = PB05Native() if module is None else module
    if (
        module.KEY != SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB05 source identity changed")
    geometries = module.pb03_geometries()
    parts = {part.name: part.shape for part in module.wood_parts()}
    connections = module.connections()
    base = module._base_connections
    panel = tuple(map(_axis, module.panel_connections()))
    fixed = tuple(
        _axis(row)
        for row in connections
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    base_fixed = tuple(_axis(row) for row in base if row.kind == "bolt")
    outer = {name: geometries[name] for name in OUTER_STATIONS}
    centers = set(REPLACED_STATIONS) - set(OUTER_STATIONS)
    if (
        set(geometries) != set(REPLACED_STATIONS)
        or len(centers) != 2
        or len(panel) != 66
        or panel
        != tuple(
            _axis(row)
            for row in base
            if row.name in {p.name for p in module.panel_connections()}
        )
        or len(fixed) != 12
        or fixed != base_fixed
        or len(module.legacy_proxy_stations()) != 14
        or sum(row.name.startswith("clip_") for row in connections) != 84
        or sum(row.name.startswith("pb03_") for row in connections) != 32
        or len(connections) != 194
    ):
        raise ValueError("PB05 fixed axis or legacy inventory changed")
    if any(
        row.report["block_dimensions_mm"] != [95.25, 57.15, 300.0]
        or _shape(parts[row.block_name]) != _shape(row.block)
        for row in outer.values()
    ):
        raise ValueError("PB05 narrow block geometry changed")
    block_axes = {
        name: [axis.toTuple() for axis in module.MEMBER_AXES[name]]
        for name in sorted(row.block_name for row in geometries.values())
    }
    identity = {
        "source_id": SOURCE_ID,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "outer_stations": OUTER_STATIONS,
        "upper_rail_offset_mm": pb04.SELECTED_OFFSET_MM,
        "blocks": {
            row.block_name: _shape(parts[row.block_name]) for row in geometries.values()
        },
        "block_axes": block_axes,
        "connections": [_axis(row) for row in connections],
    }
    sources = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in {
            "pb05_native": Path(__file__),
            "pb03_builder": Path(lower.__file__),
            "pb03_adapter": Path(pb03.__file__),
            "pb04_offset": Path(pb04.__file__),
        }.items()
    }
    return {
        "schema": "simple_pb05_native/v1",
        "source_id": SOURCE_ID,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "block_axis_fingerprint_sha256": _digest(identity),
        "source_fingerprint_sha256": _digest(
            {"identity": identity, "sources": sources}
        ),
        "source_sha256": sources,
        "inventory": {
            "outer_blocks": 6,
            "unchanged_center_blocks": 2,
            "outer_pockets": 0,
            "panel_kicker_axes": 66,
            "frame_bolt_axes": 12,
            "legacy_sds_duties": 14,
            "legacy_sds_axes": 84,
            "new_bolt_axes": 32,
        },
        "native_solve": False,
        "force_transfer": False,
        "qualified_for_design": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
