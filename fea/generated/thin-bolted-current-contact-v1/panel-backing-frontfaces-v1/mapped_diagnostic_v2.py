"""Narrow tri-state/edge-metadata correction around frozen mapped markers.

Original projection, plane, force, source and current-admission code is reused
unchanged. Only two callbacks in a private loaded module are scoped here.
The original failed-readiness source/coupon/review remain at their issued paths.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[4]
TEST = OWN.with_name("test_mapped_diagnostic_v2.py")
PREFIX = str(OWN.parent.relative_to(ROOT)) + "/"
ORIGINAL = {
    "mapped_diagnostic.py": "6159a748ee1640771243dbe7bd3f0747bc0fcb66e05516934b98b6a7759a2c85",
    "test_mapped_diagnostic.py": "5577ed9f7ba8e7707861219f2daf5e23f260e072fce948867b81252d07427743",
    "mapped-diagnostic-coupon.json": "92983c9125b1521fe56303de5263e6797b0bbbc030921dd022b8e0deaa14ef46",
    "independent-mapped-review-attempt01.json": "f679d6779ea2ac70f5499b82193d57b5f3523d6ad9d23794488be33c739f6dc2",
    "independent_mapped_review.py": "cd5170a97296020bc52750847224e16538cf7418f3f1da7c7bf019420261517b",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for _name, _expected in ORIGINAL.items():
    if sha(OWN.with_name(_name)) != _expected:
        raise ValueError("issued original bytes changed: " + _name)
_spec = importlib.util.spec_from_file_location("private_frozen_backing_marker_v1", OWN.with_name("mapped_diagnostic.py"))
frozen = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = frozen
_spec.loader.exec_module(frozen)
query, reuse, surface, finite, panels = frozen.query, frozen.reuse, frozen.surface, frozen.finite, frozen.panels
ORIGINAL_UNION, ORIGINAL_PANEL = frozen.union_summary, frozen.panel_marker
LOADED_SHA, TEST_SHA = sha(OWN), sha(TEST)
SCHEMA = "thin_bolted_admitted_current_panel_backing_mapped_markers/v2"
COUPON_SCHEMA = "thin_bolted_panel_backing_mapped_diagnostic_coupon/v2"


def own_pins():
    query.require(sha(OWN) == LOADED_SHA and sha(TEST) == TEST_SHA, "loaded corrected method/test bytes changed")
    pins = query.join({PREFIX + name: value for name, value in ORIGINAL.items()}, frozen.own_pins(),
                     {str(OWN.relative_to(ROOT)): LOADED_SHA, str(TEST.relative_to(ROOT)): TEST_SHA})
    query.verify(pins)
    return pins


def union_summary(rows):
    """False requires every owned piece proved exterior; other failure is NULL."""
    result = ORIGINAL_UNION(rows)
    all_exterior = bool(rows) and all(row["projection_error"] is None
        and row["current_reference_trim"] is not None
        and row["current_reference_trim"]["definitely_exterior"] is True for row in rows)
    result["some_smooth_local_owned_piece_projection_available"] = (
        True if result["certified_interior_opposed_piece_ids"] else False if all_exterior else None)
    result["all_owned_pieces_proved_exterior"] = all_exterior
    result["false_requires_all_owned_pieces_exterior"] = True
    return result


def panel_marker(mapping, q, panel, point):
    """Leave computed derivatives intact; label their original-coordinate branch."""
    result = ORIGINAL_PANEL(mapping, q, panel, point)
    row = mapping["panels"][panel]
    local = result["reference_panel_local_xyz_mm"]
    branches = []
    for coordinate, limit in zip(local[:2], (row["basis_width_mm"], row["basis_height_mm"]), strict=True):
        branches.append("tolerance_extrapolation" if coordinate < 0. or coordinate > limit else
                        "material_interior_side_at_boundary" if coordinate == 0. or coordinate == limit else
                        "material_interior")
    result["panel_xy_derivative_branch_by_axis"] = branches
    result["panel_xy_derivative_from_material_interior_side_at_boundary"] = "material_interior_side_at_boundary" in branches
    return result


@contextmanager
def corrected_callbacks():
    """Scope two callbacks only; restore even if the reused consumer raises."""
    own_pins()
    before = {"union_summary": frozen.union_summary, "panel_marker": frozen.panel_marker}
    try:
        frozen.union_summary, frozen.panel_marker = union_summary, panel_marker
        yield frozen
    finally:
        for key, value in before.items():
            setattr(frozen, key, value)
        own_pins()


def method_contract():
    return {"method": "mapped-marker-tristate-and-original-coordinate-edge-metadata-correction",
        "reused_geometry_engine_sha256": ORIGINAL["mapped_diagnostic.py"],
        "original_failed_readiness_review_sha256": ORIGINAL["independent-mapped-review-attempt01.json"],
        "scoped_reused_callbacks": ["union_summary", "panel_marker"],
        "projection_or_geometry_derivatives_changed": False, "force_q_or_area_changed": False,
        "old_readiness_pass_transferred": False, "false_only_all_pieces_proved_exterior": True,
        "edge_branch_flags_use_original_local_coordinates": True}


def consume(coupon_path, coupon_sha256, *, progress=None):
    """New source-bound contract; original coupon remains a truthful prerequisite."""
    pins = own_pins()
    query.require(sha(coupon_path) == coupon_sha256, "exact corrected method coupon required")
    coupon = json.loads(Path(coupon_path).read_bytes())
    query.require(coupon["schema"] == COUPON_SCHEMA and coupon["method_checks_pass"] is True
        and coupon["candidate_q_or_forces_consumed"] is False and coupon["method_contract"] == method_contract()
        and all(coupon["source_sha256"].get(path) == value for path, value in pins.items()),
        "corrected source-bound method checks required")
    pins = query.join(pins, coupon["source_sha256"], {str(Path(coupon_path).resolve().relative_to(ROOT)): coupon_sha256})
    query.verify(pins)
    with corrected_callbacks():
        result = frozen.consume(OWN.with_name("mapped-diagnostic-coupon.json"), ORIGINAL["mapped-diagnostic-coupon.json"],
                                progress=progress)
    query.require(result["schema"] == "thin_bolted_admitted_current_panel_backing_mapped_markers/v1",
                  "truthful reused internal consumer schema required")
    result["reused_internal_consumer_schema"] = result["schema"]
    result["schema"] = SCHEMA
    result["method_contract"] = method_contract()
    result["corrected_method_coupon_sha256"] = coupon_sha256
    result["source_sha256"] = query.join(result["source_sha256"], pins)
    query.verify(result["source_sha256"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coupon", type=Path, required=True)
    parser.add_argument("--coupon-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    query.require(not args.out.exists(), "preserve existing corrected marker output")
    result = consume(args.coupon, args.coupon_sha256,
        progress=lambda event: print(json.dumps(event), flush=True) if event["completed_ports"] % 50 == 0 else None)
    result.update({"invocation_argv": list(sys.orig_argv), "working_directory": str(Path.cwd()),
        "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS")},
        "toolchain": query.toolchain()})
    query.write_exclusive(args.out, result)
    print(json.dumps({"output": str(args.out), "sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
