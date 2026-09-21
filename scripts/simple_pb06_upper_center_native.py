"""PB06 upper-center native geometry replacement; preparation only."""

import hashlib
from pathlib import Path

from mini_moonboard.box_frame import Part
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_center_pair as upper_center
from scripts import simple_pb05_native as pb05

SOURCE_ID = "pb06-upper-center-native-v1"
TARGET_STATIONS = upper_center.TARGET_STATIONS
_PREFIXES = tuple(f"{station}_" for station in TARGET_STATIONS)
_BLOCK_NOTE = "PB06 developmental solid timber block; hardware and drilling unselected"
_FALSE_FLAGS = {
    "solved": False,
    "force_transfer": False,
    "qualified_for_design": False,
    "acceptance": False,
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def _axis(row):
    return pb05._axis(row)


def _target_sds(rows):
    return tuple(row for row in rows if row.name.startswith(_PREFIXES))


class PB06Native(pb05.PB05Native):
    """Replace exactly two upper-center ML24Z/SDS proxies with timber and bolts."""

    KEY = SOURCE_ID

    def __init__(self):
        super().__init__()
        if self.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT:
            raise ValueError("PB06 PB02 geometry source changed")
        _, _, _, _, source_connections = lower._source_inventory()
        original = _target_sds(self._base_connections)
        if (
            len(original) != 12
            or any(row.kind != "screw" for row in original)
            or tuple(map(_axis, original))
            != tuple(map(_axis, _target_sds(source_connections)))
            or set(self.legacy_proxy_stations()) & set(TARGET_STATIONS)
            != set(TARGET_STATIONS)
        ):
            raise ValueError("PB06 original upper-center SDS axes changed")
        self._original_target_sds = tuple(map(_axis, original))
        pair = upper_center.build_pair()
        if set(pair) != set(TARGET_STATIONS) or any(
            len(row.bolts) != 4 for row in pair.values()
        ):
            raise ValueError("PB06 upper-center trial inventory changed")
        self._pb03_geometries.update(pair)
        self._blocks = (
            *self._blocks,
            *(
                Part(
                    row.block_name,
                    row.block,
                    (row.block_length_mm, *row.report["block_dimensions_mm"][:2]),
                    _BLOCK_NOTE,
                    1,
                )
                for row in pair.values()
            ),
        )
        self._pb03_bolts = (
            *self._pb03_bolts,
            *(bolt for row in pair.values() for bolt in row.bolts),
        )
        self.MEMBER_AXES = {
            **self.MEMBER_AXES,
            **{
                row.block_name: (
                    pb05.pb03.BLOCK_GRAIN_AXIS,
                    pb05.pb03.BLOCK_SECTION_AXIS,
                )
                for row in pair.values()
            },
        }
        self.NATIVE_SQUARE_END_MEMBERS = (
            *self.NATIVE_SQUARE_END_MEMBERS,
            *(row.block_name for row in pair.values()),
        )
        # ponytail: PB03's point builder requires exactly 32 axes; add the eight
        # new face points directly after its authenticated PB05 construction.
        uncut = {part.name: part.shape for part in self.uncut_wood_parts()}
        for row in pair.values():
            for bolt in row.bolts:
                direction = bolt.direction.normalized()
                host_face = max(
                    v.Center().dot(direction) for v in uncut[bolt.members[0]].Vertices()
                )
                block_face = min(
                    v.Center().dot(direction) for v in row.block.Vertices()
                )
                if (
                    abs(host_face - block_face) > 1e-6
                    or bolt.name in self._pb03_bolt_points
                ):
                    raise ValueError(f"{bolt.name}: PB06 host/block face changed")
                self._pb03_bolt_points[bolt.name] = bolt.start + direction * (
                    host_face - bolt.start.dot(direction)
                )
        self._pb06_ready = True

    def connections(self):
        rows = super().connections()
        if not getattr(self, "_pb06_ready", False):
            return rows
        return tuple(row for row in rows if not row.name.startswith(_PREFIXES))

    def stations(self):
        rows = super().stations()
        if not getattr(self, "_pb06_ready", False):
            return rows
        return tuple(row for row in rows if row[0] not in TARGET_STATIONS)

    def validate_prepared_case(self, structure, metadata):
        """Check PB06 ownership without inheriting PB03/PB05 count assumptions."""
        ownership = metadata.get("connection_ownership", {})
        new_names = {
            bolt.name for row in self._pb03_geometries.values() for bolt in row.bolts
        }
        block_names = {row.block_name for row in self._pb03_geometries.values()}
        if (
            len(self.legacy_proxy_stations()) != 12
            or len(_target_sds(self.connections())) != 0
            or sum(row.name.startswith("clip_") for row in self.connections()) != 72
            or len(new_names) != 40
            or len(self.panel_connections()) != 66
            or not block_names <= set(structure.members)
            or not new_names <= set(ownership)
        ):
            raise ValueError("PB06 prepared inventory changed")
        metadata.update(
            pb06_candidate=SOURCE_ID,
            pb06_preparation_validated=True,
            preparation_only=True,
            developmental_only=True,
            **_FALSE_FLAGS,
        )


def screen(module=None):
    """Fingerprint PB06 geometry and authenticate the retained PB05 inventory."""
    module = PB06Native() if module is None else module
    source = pb05.PB05Native()
    source_report = pb05.screen(source)
    source_rows = source.connections()
    rows = module.connections()
    expected = tuple(row for row in source_rows if not row.name.startswith(_PREFIXES))
    new_axes = tuple(
        _axis(bolt)
        for station in TARGET_STATIONS
        for bolt in module.pb03_geometries()[station].bolts
    )
    source_parts = {part.name: part.shape for part in source.wood_parts()}
    actual_parts = {part.name: part.shape for part in module.wood_parts()}
    source_pb03 = source.pb03_geometries()
    candidate_pb03 = module.pb03_geometries()
    if (
        module.KEY != SOURCE_ID
        or module._original_target_sds
        != tuple(map(_axis, _target_sds(source._base_connections)))
        or tuple(map(_axis, rows)) != (*tuple(map(_axis, expected)), *new_axes)
        or set(actual_parts)
        != set(source_parts)
        | {candidate_pb03[station].block_name for station in TARGET_STATIONS}
        or any(
            actual_parts[name].distance(shape) > 1e-8
            or abs(actual_parts[name].Volume() - shape.Volume()) > 1e-5
            for name, shape in source_parts.items()
        )
        or set(candidate_pb03) != set(source_pb03) | set(TARGET_STATIONS)
        or len(module.legacy_proxy_stations()) != 12
        or sum(row.name.startswith("clip_") for row in rows) != 72
        or tuple(map(_axis, module.panel_connections()))
        != tuple(map(_axis, source.panel_connections()))
        or len(new_axes) != 8
        or any(
            actual_parts[candidate_pb03[station].block_name].distance(
                candidate_pb03[station].block
            )
            > 1e-8
            for station in TARGET_STATIONS
        )
    ):
        raise ValueError("PB06 source or replacement inventory changed")
    shapes = {name: pb05._shape(shape) for name, shape in actual_parts.items()}
    identity = {
        "source_id": SOURCE_ID,
        "pb05_source_fingerprint": source_report["source_fingerprint_sha256"],
        "target_sds": module._original_target_sds,
        "connections": tuple(map(_axis, rows)),
        "wood": shapes,
    }
    fingerprint = pb05._digest(
        {
            "identity": identity,
            "pb06_source_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "upper_center_source_sha256": hashlib.sha256(
                Path(upper_center.__file__).read_bytes()
            ).hexdigest(),
        }
    )
    return {
        "schema": "simple_pb06_upper_center_native/v1",
        "source_id": SOURCE_ID,
        "pb05_source_fingerprint_sha256": source_report["source_fingerprint_sha256"],
        "source_fingerprint_sha256": fingerprint,
        "original_target_sds_authenticated": True,
        "inventory": {
            "blocks": 10,
            "original_frame_bolt_axes": 12,
            "panel_kicker_axes": 66,
            "legacy_sds_duties": 12,
            "legacy_sds_axes": 72,
            "pb05_bolt_axes": 32,
            "upper_center_bolt_axes": 8,
        },
        **{key: value for key, value in _FALSE_FLAGS.items() if key != "solved"},
        "native_solve": False,
    }
