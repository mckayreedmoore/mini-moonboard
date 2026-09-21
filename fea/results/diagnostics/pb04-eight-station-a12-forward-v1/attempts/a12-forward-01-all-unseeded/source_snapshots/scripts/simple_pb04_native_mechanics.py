"""Source-bound PB04 eight-station native mechanics; no solve or release."""

import hashlib
import json

import cadquery as cq

from scripts import simple_pb03_native_mechanics as pb03
from scripts import simple_rail_joint_comparison as pb01
from scripts.simple_pb04_native import SOURCE_ID, PB04Native

MECHANICS_SOURCE_ID = "pb04-eight-station-native-mechanics-v1"


def _geometries(module):
    geometry_factory = getattr(module, "pb04_geometries", None)
    if geometry_factory is None:
        geometry_factory = module.pb03_geometries
    return geometry_factory()


class _PB03GeometryView:
    """Expose PB04 geometry through the one seam used by PB03 mechanics."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        return getattr(self._module, name)

    def pb03_geometries(self):
        return _geometries(self._module)


def _build_rows(module):
    return pb03._build_rows(_PB03GeometryView(module))


def _identity_payload(rows, module):
    geometries = _geometries(module)
    fingerprint = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "mechanics_source_id": MECHANICS_SOURCE_ID,
        "pb04_source_id": SOURCE_ID,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "replaced_stations": list(geometries),
        "legacy_proxy_stations": len(module.legacy_proxy_stations()),
        "fixed_panel_kicker_axes": len(module.panel_connections()),
        "contact_grid": [2, 2],
        "row_fingerprint_sha256": fingerprint,
    }


def native_row_inventory(module=None):
    """Return source-bound PB04 contact cells and existing bolt-axis rows."""
    module = PB04Native() if module is None else module
    geometries = _geometries(module)
    if module.KEY != SOURCE_ID or len(geometries) != 8:
        raise ValueError("PB04 mechanics source identity changed")
    if (
        len(module.legacy_proxy_stations()) != 14
        or len(module.panel_connections()) != 66
    ):
        raise ValueError("PB04 retained legacy or fixed-axis inventory changed")
    rows = _build_rows(module)
    names = [row["name"] for row in rows]
    if (
        len(rows) != 96
        or len(names) != len(set(names))
        or sum(row["kind"] == "contact_compression" for row in rows) != 64
        or sum(row["kind"] == "bolt" for row in rows) != 32
    ):
        raise ValueError("PB04 mechanics row inventory changed")
    return rows, _identity_payload(rows, module)


def native_member_contacts(face_normal_total_n_per_mm, module=None, row_inventory=None):
    """Build PB04 four-cell contacts with the established PB03 contact law."""
    module = PB04Native() if module is None else module
    rows = native_row_inventory(module) if row_inventory is None else row_inventory
    return pb03.native_member_contacts(
        face_normal_total_n_per_mm, module=module, row_inventory=rows
    )


def activate_existing_paths(structure, metadata, module=None, row_inventory=None):
    """Activate preparer-owned PB04 paths without retaining PB03 identity keys."""
    module = PB04Native() if module is None else module
    rows = native_row_inventory(module) if row_inventory is None else row_inventory
    identity = pb03.activate_existing_paths(
        structure, metadata, module=module, row_inventory=rows
    )
    counts = metadata.pop("pb03_native_row_counts")
    metadata.pop("pb03_candidate")
    metadata.pop("pb03_mechanics_identity")
    metadata.update(
        pb04_candidate=SOURCE_ID,
        pb04_mechanics_identity=identity,
        pb04_native_row_counts=counts,
    )
    return identity


class PB04MechanicsNative(PB04Native):
    """PB04 geometry with explicit block axes and exact interface points."""

    def __init__(self):
        super().__init__()
        block_names = tuple(
            geometry.block_name for geometry in _geometries(self).values()
        )
        block_grain = cq.Vector(0.0, *pb01.N)
        section_u = cq.Vector(1.0, 0.0, 0.0)
        self.MEMBER_AXES = {
            **self.MEMBER_AXES,
            **{name: (block_grain, section_u) for name in block_names},
        }
        self.NATIVE_SQUARE_END_MEMBERS = (*self.NATIVE_SQUARE_END_MEMBERS, *block_names)
        self._pb04_interface_points = {
            row["name"]: cq.Vector(*row["point_mm"])
            for row in _build_rows(self)
            if row["kind"] == "bolt"
        }

    def bolt_interface_point(self, connection):
        point = self._pb04_interface_points.get(connection.name)
        if point is not None:
            return point
        return connection.start + connection.direction * (2.032 + 38.1)
