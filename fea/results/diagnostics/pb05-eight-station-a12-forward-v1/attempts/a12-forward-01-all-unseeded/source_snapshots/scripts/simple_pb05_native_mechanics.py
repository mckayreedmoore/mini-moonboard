"""Source-bound PB05 contact and bolt preparation; no solve or release."""

import hashlib
import json

from scripts import simple_pb03_native_mechanics as pb03
from scripts.simple_pb05_native import OUTER_STATIONS, SOURCE_ID, PB05Native, screen

MECHANICS_SOURCE_ID = "pb05-eight-station-native-mechanics-v1"


def native_row_inventory(module=None):
    """Bind PB03 row construction to PB05's authenticated no-pocket geometry."""
    module = PB05MechanicsNative() if module is None else module
    source = screen(module)
    geometries = module.pb03_geometries()
    if (
        module.KEY != SOURCE_ID
        or source["source_id"] != SOURCE_ID
        or source["inventory"]
        != {
            "outer_blocks": 6,
            "unchanged_center_blocks": 2,
            "outer_pockets": 0,
            "panel_kicker_axes": 66,
            "frame_bolt_axes": 12,
            "legacy_sds_duties": 14,
            "legacy_sds_axes": 84,
            "new_bolt_axes": 32,
        }
        or len(geometries) != 8
        or set(OUTER_STATIONS) - set(geometries)
    ):
        raise ValueError("PB05 mechanics source inventory changed")
    rows = pb03._build_rows(module)
    names = [row["name"] for row in rows]
    if (
        len(rows) != 96
        or len(names) != len(set(names))
        or sum(row["kind"] == "bolt" for row in rows) != 32
        or sum(row["kind"] == "contact_compression" for row in rows) != 64
    ):
        raise ValueError("PB05 mechanics row inventory changed")
    identity = {
        "mechanics_source_id": MECHANICS_SOURCE_ID,
        "pb05_source_id": SOURCE_ID,
        "source_fingerprint_sha256": source["source_fingerprint_sha256"],
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "replaced_stations": list(geometries),
        "outer_stations": list(OUTER_STATIONS),
        "legacy_proxy_stations": len(module.legacy_proxy_stations()),
        "fixed_panel_kicker_axes": len(module.panel_connections()),
        "contact_grid": [2, 2],
        "row_fingerprint_sha256": hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    return rows, identity


def native_member_contacts(face_normal_total_n_per_mm, module=None, row_inventory=None):
    """Use the established four-cell unilateral contact law for PB05 faces."""
    module = PB05MechanicsNative() if module is None else module
    rows = native_row_inventory(module) if row_inventory is None else row_inventory
    return pb03.native_member_contacts(
        face_normal_total_n_per_mm, module=module, row_inventory=rows
    )


def activate_existing_paths(structure, metadata, module=None, row_inventory=None):
    """Mark existing PB05 bolts and contacts without adding connectors."""
    module = PB05MechanicsNative() if module is None else module
    rows = native_row_inventory(module) if row_inventory is None else row_inventory
    identity = pb03.activate_existing_paths(
        structure, metadata, module=module, row_inventory=rows
    )
    counts = metadata.pop("pb03_native_row_counts")
    metadata.pop("pb03_candidate")
    metadata.pop("pb03_mechanics_identity")
    metadata.update(
        pb05_candidate=SOURCE_ID,
        pb05_mechanics_identity=identity,
        pb05_native_row_counts=counts,
    )
    return identity


class PB05MechanicsNative(PB05Native):
    """PB05 geometry with the inherited explicit axes and face points."""
