"""Source-bound PB06 ten-station mechanics preparation; no solve or release."""

import hashlib
import json

from scripts import simple_pb03_native_mechanics as pb03
from scripts.simple_pb06_upper_center_native import SOURCE_ID, PB06Native, screen

MECHANICS_SOURCE_ID = "pb06-ten-station-native-mechanics-v1"
_INVENTORY = {
    "blocks": 10,
    "original_frame_bolt_axes": 12,
    "panel_kicker_axes": 66,
    "legacy_sds_duties": 12,
    "legacy_sds_axes": 72,
    "pb05_bolt_axes": 32,
    "upper_center_bolt_axes": 8,
}
_NO_RELEASE = (
    "solved",
    "force_transfer",
    "qualified_for_design",
    "acceptance",
    "drilling_released",
    "fabrication_released",
    "structural_released",
)


def native_row_inventory(module=None):
    """Bind PB03 face cells and bolt rows to the authenticated PB06 source."""
    module = PB06Native() if module is None else module
    source = screen(module)
    geometries = module.pb03_geometries()
    connections = module.connections()
    if (
        module.KEY != SOURCE_ID
        or source["source_id"] != SOURCE_ID
        or source["inventory"] != _INVENTORY
        or any(
            source[flag] is not False
            for flag in (
                "native_solve",
                *_NO_RELEASE[1:],
            )
        )
        or len(geometries) != 10
        or len(module.panel_connections()) != 66
        or len(module.legacy_proxy_stations()) != 12
        or sum(row.name.startswith("clip_") for row in connections) != 72
        or sum(
            row.kind == "bolt" and not row.name.startswith("pb03_")
            for row in connections
        )
        != 12
    ):
        raise ValueError("PB06 mechanics source inventory changed")
    rows = pb03._build_rows(module)
    names = [row["name"] for row in rows]
    if (
        len(rows) != 120
        or len(names) != len(set(names))
        or sum(row["kind"] == "bolt" for row in rows) != 40
        or sum(row["kind"] == "contact_compression" for row in rows) != 80
    ):
        raise ValueError("PB06 mechanics row inventory changed")
    identity = {
        "mechanics_source_id": MECHANICS_SOURCE_ID,
        "pb06_source_id": SOURCE_ID,
        "source_fingerprint_sha256": source["source_fingerprint_sha256"],
        "pb05_source_fingerprint_sha256": source["pb05_source_fingerprint_sha256"],
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "replaced_stations": list(geometries),
        "fixed_panel_kicker_axes": 66,
        "original_frame_bolt_axes": 12,
        "legacy_sds_duties": 12,
        "legacy_sds_axes": 72,
        "contact_grid": [2, 2],
        "row_fingerprint_sha256": hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    return rows, identity


def native_member_contacts(face_normal_total_n_per_mm, module=None, row_inventory=None):
    """Use PB03's four-cell law with a ten-station mean interface area."""
    module = PB06Native() if module is None else module
    inventory = native_row_inventory(module) if row_inventory is None else row_inventory
    # ponytail: PB03 divides total face area by 16; PB06 has 20 interfaces.
    contacts, scope = pb03.native_member_contacts(
        face_normal_total_n_per_mm * 20 / 16, module=module, row_inventory=inventory
    )
    scope["input_mean_total_per_interface_n_per_mm"] = face_normal_total_n_per_mm
    return contacts, scope


def activate_existing_paths(structure, metadata, module=None, row_inventory=None):
    """Check and mark existing PB06 paths without creating or solving them."""
    module = PB06Native() if module is None else module
    inventory = native_row_inventory(module) if row_inventory is None else row_inventory
    identity = pb03.activate_existing_paths(
        structure, metadata, module=module, row_inventory=inventory
    )
    metadata.pop("pb03_candidate")
    metadata.pop("pb03_mechanics_identity")
    metadata.pop("pb03_native_row_counts")
    metadata.update(
        pb06_candidate=SOURCE_ID,
        pb06_mechanics_identity=identity,
        pb06_native_row_counts={
            "existing_bolt_axes": 40,
            "bolt_tension_only": 40,
            "existing_bolt_lateral": 80,
            "contact_compression_cells": 80,
        },
        preparation_only=True,
        developmental_only=True,
        **{flag: False for flag in _NO_RELEASE},
    )
    return identity
