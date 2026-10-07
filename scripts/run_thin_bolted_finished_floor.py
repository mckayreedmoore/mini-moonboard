"""Reuse frozen mechanics with authenticated finished timber floor faces.

The preceding state used raw leg corners inside an existing recess. This
driver changes only those support footprints, gives the corrected method a
distinct identity, and preserves the earlier producer and numerical state.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import run_thin_bolted_mechanics as writer
from scripts import thin_bolted_frame_mechanics as frame

CONTACT_PATH = frame.PACKET / "frame-contact-geometry-v4.json"
CONTACT_SHA = "e6c7ac4548b943bef4580b7c58efd67c11e29ed3335ae4036998a70c346986fc"
FLOOR_BASIS = "authenticated-finished-timber-horizontal-faces"
FLOOR_HOSTS = {
    "base_floor_left", "base_floor_right", "base_post_center_left",
    "base_post_center_right", "base_post_outer_left", "base_post_outer_right",
    "lumber_leg_left", "lumber_leg_right",
}


def ordered_rectangle(points) -> list:
    """Validate a horizontal rectangle and order its vertices counterclockwise."""
    array = np.asarray(points, dtype=float)
    if array.shape != (4, 3) or not np.isfinite(array).all() or abs(array[:, 2]).max() > 1e-6:
        raise ValueError("four finite finished floor corners at z=0 required")
    low, high = array[:, :2].min(axis=0), array[:, :2].max(axis=0)
    if np.any(high - low <= 0.):
        raise ValueError("positive finished bearing area required")
    expected = np.array([(x, y) for x in (low[0], high[0]) for y in (low[1], high[1])])
    matches = np.all(abs(array[:, None, :2] - expected[None, :, :]) <= 1e-6, axis=2)
    if not np.all(matches.sum(axis=0) == 1) or not np.all(matches.sum(axis=1) == 1):
        raise ValueError("finished bearing corners must describe one rectangle")
    center = array[:, :2].mean(axis=0)
    angles = np.arctan2(array[:, 1] - center[1], array[:, 0] - center[0])
    return array[np.argsort(angles)].tolist()


def read_finished_footprints() -> tuple[dict, list, dict]:
    """Reuse the source-bound contact audit; no BREP import or CAD regeneration."""
    if frame.sha(CONTACT_PATH) != CONTACT_SHA:
        raise ValueError("preserve the authenticated finished contact packet")
    contact = json.loads(CONTACT_PATH.read_text())
    if (contact["geometry_cache_sha256"] != frame.GEOMETRY_CACHE_SHA
            or contact["layout_report_sha256"] != frame.LAYOUT_SHA
            or contact["unsupported_flange_contacts"]):
        raise ValueError("contact audit is incompatible with frozen candidate inputs")
    for name, expected in contact["source_sha256"].items():
        if frame.sha(frame.ROOT / name) != expected:
            raise ValueError(f"finished-contact source differs: {name}")
    cache = json.loads(frame.GEOMETRY_CACHE.read_text())
    timber = {row["id"]: row for row in cache["parts"] if row["kind"] == "timber"}
    footprints = contact["finished_floor_footprints"]
    if set(footprints) != FLOOR_HOSTS:
        raise ValueError("all eight finished floor hosts required")
    proof = []
    for name, points in sorted(footprints.items()):
        source = timber[name]
        if contact["source_sha256"].get(source["path"]) != source["sha256"]:
            raise ValueError(f"finished floor host lacks authenticated BREP: {name}")
        polygon = ordered_rectangle(points)
        low, high = np.asarray(polygon).min(axis=0), np.asarray(polygon).max(axis=0)
        proof.append({"member": name, "polygons_xyz_mm": [polygon],
                      "bearing_area_mm2": float(np.prod((high - low)[:2])),
                      "source_brep_path": source["path"],
                      "source_brep_sha256": source["sha256"]})
    pins = dict(contact["source_sha256"])
    pins[str(CONTACT_PATH.relative_to(frame.ROOT))] = CONTACT_SHA
    return copy.deepcopy(footprints), proof, pins


def bind_finished_state(report: dict, proof: list, pins: dict, driver_sha: str) -> dict:
    """Change state identity and every action alias together with floor provenance."""
    previous_id = report["state_id"]
    report["parameters"].update({"floor_support_basis": FLOOR_BASIS,
                                 "floor_contact_geometry_sha256": CONTACT_SHA})
    identity = {"case_id": report["case_id"], "accessory_placement": report["accessory_placement"],
                "parameters": report["parameters"], "geometry_cache_sha256": report["geometry_cache_sha256"]}
    corrected_id = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]

    visited = set()

    def replace_ids(value):
        if isinstance(value, (dict, list)):
            if id(value) in visited:
                return
            visited.add(id(value))
        if isinstance(value, dict):
            if "state_id" in value:
                if value["state_id"] != previous_id:
                    raise ValueError("mixed action identity before finished-support binding")
                value["state_id"] = corrected_id
            for nested in value.values():
                replace_ids(nested)
        elif isinstance(value, list):
            for nested in value:
                replace_ids(nested)

    replace_ids(report)
    report["finished_floor_footprints"] = copy.deepcopy(proof)
    report["source_sha256"].update(pins)
    report["source_sha256"][str(Path(__file__).relative_to(frame.ROOT))] = driver_sha
    report["finished_floor_execution"] = {
        "command": [sys.executable, "-m", "scripts.run_thin_bolted_finished_floor", *sys.argv[1:]],
        "environment": {"OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS")},
        "floor_support_basis": FLOOR_BASIS, "floor_contact_geometry_sha256": CONTACT_SHA,
        "finished_host_count": len(proof), "CAD_recreated": False,
        "new_constitutive_law": False,
        "preserved_frozen_producer": True,
        "independent_finished_support_audit_required": True,
    }
    report["limits"].append("Finished horizontal bearing footprints replace raw leg corners; distributed floor stiffness and actual no-slip support remain assumed.")
    return report


def main() -> None:
    footprints, proof, pins = read_finished_footprints()
    driver_sha = frame.sha(Path(__file__))
    original_geometry, original_evaluate = frame.geometry, frame.evaluate_elastic

    def geometry(*args, **kwargs):
        geo = dict(original_geometry(*args, **kwargs))
        if set(geo["floor_footprints"]) != set(footprints):
            raise ValueError("frozen mechanics floor-host census differs")
        geo["floor_footprints"] = copy.deepcopy(footprints)
        return geo

    def evaluate(*args, **kwargs):
        report = original_evaluate(*args, **kwargs)
        if frame.sha(Path(__file__)) != driver_sha or frame.sha(CONTACT_PATH) != CONTACT_SHA:
            raise ValueError("finished-support producer changed during evaluation")
        return bind_finished_state(report, proof, pins, driver_sha)

    with patch.object(frame, "geometry", geometry), patch.object(frame, "evaluate_elastic", evaluate):
        writer.main()


if __name__ == "__main__":
    main()
