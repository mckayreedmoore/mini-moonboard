"""Handedness-aware panel marker observer around the immutable v3 consumer.

A world isometry facade gives the frozen panel-only derivative routine a
proper chart. Its point/vector/tangent outputs return to the actual world;
the admitted maps, q, planes, actions and local coefficients never change.
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

import numpy as np

OWN = Path(__file__).resolve()
ROOT = OWN.parents[4]
TEST = OWN.with_name("test_mapped_diagnostic_v4.py")
PREFIX = str(OWN.parent.relative_to(ROOT)) + "/"
REUSED = {
    "mapped_diagnostic_v3.py": "951dcdb9fd8c886474bc4bfa9041c8bf013c40d808a81e4bbac68dc5b36406ad",
    "test_mapped_diagnostic_v3.py": "4f946ebf4b5404811d33df0888a402b3a48c1e84b60359c7336814645662c864",
    "mapped-diagnostic-coupon-v3.json": "6b5a6ddebc2413a10ca1cb6f8288461636c8d516c0a8c5be27cb1a94de2dc22e",
    "independent-mapped-review-v3.json": "55fa761b14dac5f90942f5cca73f2a0c37e5cc49887e9b32588a7eef1f76de0b",
    "independent_mapped_review_v3.py": "8b085fe77d3b48659b6a39b8b13bbf6c2946d70273bee02fb1b3d81848e2bd35",
    "current-mapped-markers-v3.json": "22fa9eb024b0dafae0985014eedf78e6a9eecfd4eee9d3e7148f139daa4477d5",
    "independent-v3-execution-semantic-failure.json": "10e656d2330a8ef8af1a3192b40fbe02cbb4f945d7ccc3d4004949c6adf2017c",
    "audit_v3_semantic_failure.py": "5d9efdc740a1a42f2eb147c4c83b4fec44b95bd9746c350bee3ee2fda98cad64",
}
CHART_SOURCES = {
    "fea/generated/thin-bolted-panel/operators-intervals8.json": "aeeb9b6ccd2c521896b32012ccbf9712fd67cdb7d0744e06d88afa4fd3f441d4",
    "fea/generated/thin-bolted-joint-wrench-review/review-v4.py": "c86cb3e84c0d16648e6a3d115da686afc6e2c97272cd06c4cbe3bfb93a15be55",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for _name, _expected in REUSED.items():
    if sha(OWN.with_name(_name)) != _expected:
        raise ValueError("issued v3 evidence changed: " + _name)
_spec = importlib.util.spec_from_file_location("private_reviewed_backing_marker_v3", OWN.with_name("mapped_diagnostic_v3.py"))
v3 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v3
_spec.loader.exec_module(v3)
query, core, reuse, finite, panels = v3.query, v3.core, v3.reuse, v3.finite, v3.panels
ORIGINAL_PANEL = v3.v2.ORIGINAL_PANEL
LOADED_SHA, TEST_SHA = sha(OWN), sha(TEST)
SCHEMA = "thin_bolted_admitted_current_panel_backing_mapped_markers/v4"
COUPON_SCHEMA = "thin_bolted_panel_backing_mapped_diagnostic_coupon/v4"


def own_pins():
    query.require(sha(OWN) == LOADED_SHA and sha(TEST) == TEST_SHA, "loaded handedness method/test changed")
    pins = query.join(v3.own_pins(), {PREFIX + name: value for name, value in REUSED.items()}, CHART_SOURCES,
        {str(OWN.relative_to(ROOT)): LOADED_SHA, str(TEST.relative_to(ROOT)): TEST_SHA})
    query.verify(pins)
    return pins


def handed_base_marker(mapping, q, panel, point):
    """Reuse frozen local derivatives in a proper world chart; pull back vectors."""
    row = mapping["panels"][panel]
    axes, origin, point = (np.asarray(value, dtype=float) for value in
        (row["axes_columns_xyz"], row["origin_xyz_mm"], point))
    reference = float(np.linalg.det(axes))
    query.require(np.isfinite(reference) and reference != 0., "singular/nonfinite source panel chart")
    reflection = reference < 0.
    isometry = np.diag([-1., 1., 1.]) if reflection else np.eye(3)
    local = (point - origin) @ axes
    facade_row = {**row, "axes_columns_xyz": (isometry @ axes).tolist(),
        "origin_xyz_mm": (isometry @ origin).tolist()}
    facade = {**mapping, "panels": {**mapping["panels"], panel: facade_row}}
    result = ORIGINAL_PANEL(facade, q, panel, isometry @ point)
    query.require(np.array_equal(result["reference_panel_local_xyz_mm"], local),
        "isometry facade changed source panel local coordinates")
    for key in ("current_rear_point_xyz_mm", "current_rear_outward_geometric_normal_xyz",
                "frozen_midsurface_front_normal_vector_xyz"):
        result[key] = (isometry @ np.asarray(result[key])).tolist()
    tangent = isometry @ np.asarray(result["rear_tangent_wrt_panel_local_xy"])
    result["rear_tangent_wrt_panel_local_xy"] = tangent.tolist()
    raw = (-1. if reflection else 1.) * result["rear_offset_chart_determinant"]
    relative = raw / reference
    query.require(np.isfinite(relative) and relative > 0., "inverted relative panel normal-offset marker chart")
    cross = np.cross(tangent[:, 0], tangent[:, 1])
    front = np.sign(reference) * cross / np.linalg.norm(cross)
    director = np.asarray(result["frozen_midsurface_front_normal_vector_xyz"])
    result.update({"current_rear_outward_geometric_normal_xyz": (-front).tolist(),
        "current_front_geometric_normal_xyz": front.tolist(),
        "rear_geometric_vs_frozen_normal_angle_rad": float(np.arctan2(np.linalg.norm(np.cross(front, director)), front @ director)),
        "rear_offset_chart_determinant": raw,
        "source_axes_determinant": reference, "reference_normal_offset_chart_determinant": reference,
        "relative_rear_offset_chart_determinant": relative,
        "world_isometry_facade_used_only_for_panel_marker": reflection,
        "world_isometry_facade_matrix": isometry.tolist(), "admitted_mapping_or_q_mutated": False,
        "source_axes_reorthonormalized": False, "normal_orientation_basis": "source chart handedness; rear opposite front"})
    return result


@contextmanager
def handed_callbacks():
    """Patch only the v2 frozen-marker callback, beneath its existing edge wrapper."""
    own_pins()
    before = v3.v2.ORIGINAL_PANEL
    query.require(before is ORIGINAL_PANEL, "unexpected or nested panel marker facade")
    context = {"panel_marker_attempt_count": 0}

    def observed(*args, **kwargs):
        context["panel_marker_attempt_count"] += 1
        return handed_base_marker(*args, **kwargs)

    try:
        v3.v2.ORIGINAL_PANEL = observed
        yield context
    finally:
        v3.v2.ORIGINAL_PANEL = before
        own_pins()


def panel_marker(mapping, q, panel, point):
    with handed_callbacks():
        return v3.v2.panel_marker(mapping, q, panel, point)


def method_contract():
    return {"method": "source-handedness-aware-panel-marker-world-isometry-facade",
        "reused_v3_consumer_sha256": REUSED["mapped_diagnostic_v3.py"],
        "preserved_v3_semantic_failure_sha256": REUSED["current-mapped-markers-v3.json"],
        "scoped_new_callback": "private v2.ORIGINAL_PANEL beneath original-coordinate edge metadata",
        "source_chart_determinant_and_current_over_reference_determinant_explicit": True,
        "world_isometry_facade_only": True, "q_local_coefficients_and_original_map_unchanged": True,
        "only_selected_panel_pose_called_in_facade": True, "source_Gram_error_preserved": True,
        "outward_rear_normal_is_minus_source_handedness_times_world_tangent_cross": True,
        "true_relative_fold_or_singularity_rejected": True, "physical_axes_planes_or_state_reflected": False,
        "force_area_response_or_tolerance_changed": False, "old_readiness_pass_transferred": False,
        "source_sha256": CHART_SOURCES}


def consume(coupon_path, coupon_sha256, *, progress=None):
    pins = own_pins()
    query.require(sha(coupon_path) == coupon_sha256, "exact new handedness coupon required")
    coupon = json.loads(Path(coupon_path).read_bytes())
    query.require(coupon["schema"] == COUPON_SCHEMA and coupon["method_checks_pass"] is True
        and coupon["candidate_q_or_forces_consumed"] is False and coupon["method_contract"] == method_contract()
        and all(coupon["source_sha256"].get(path) == value for path, value in pins.items()),
        "new source-bound handedness checks required")
    pins = query.join(pins, coupon["source_sha256"], {str(Path(coupon_path).resolve().relative_to(ROOT)): coupon_sha256})
    query.verify(pins)
    with handed_callbacks() as context:
        result = v3.consume(OWN.with_name("mapped-diagnostic-coupon-v3.json"), REUSED["mapped-diagnostic-coupon-v3.json"], progress=progress)
    query.require(result["schema"] == v3.SCHEMA and context["panel_marker_attempt_count"] == 530,
        "truthful complete v3 consumer and 530 marker attempts required")
    result["reused_v3_consumer_schema"], result["reused_v3_method_contract"] = result["schema"], result["method_contract"]
    result["schema"], result["method_contract"] = SCHEMA, method_contract()
    result["handedness_method_coupon_sha256"] = coupon_sha256
    result["handedness_marker_attempt_count"] = context["panel_marker_attempt_count"]
    result["source_sha256"] = query.join(result["source_sha256"], pins)
    query.verify(result["source_sha256"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coupon", type=Path, required=True)
    parser.add_argument("--coupon-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    query.require(not args.out.exists(), "preserve existing v4 marker output")
    result = consume(args.coupon, args.coupon_sha256,
        progress=lambda event: print(json.dumps(event), flush=True) if event["completed_ports"] % 50 == 0 else None)
    result.update({"invocation_argv": list(sys.orig_argv), "working_directory": str(Path.cwd()),
        "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS")},
        "toolchain": query.toolchain()})
    query.write_exclusive(args.out, result)
    print(json.dumps({"output": str(args.out), "sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
