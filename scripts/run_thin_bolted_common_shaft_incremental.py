"""Reuse the frozen retry driver with stable energy arithmetic and a warm guess."""

from __future__ import annotations

import argparse
import builtins
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from scripts import run_thin_bolted_common_shaft_continuation as previous
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as incremental

PREVIOUS_DRIVER_SHA = "716b87b48709fab850e4b3bda31281b28364bef5f90d9aa8d9a1069bfb257c99"
CERTIFICATE = frame.PACKET / "incremental-step-method-coupons-v4.json"
CERTIFICATE_SHA = "91fb76f9dfba34a81836d24a664b54e9a70055d4e6a24b89b4527bd5e614201e"
INCREMENTAL_SHA = "3a3c794bb38352f1cc34d4c736a0812c14a53021d484549dc61d0a634cf83489"
STRATEGY = "adaptive-scaled-Levenberg-stable-original-potential-increments"


def read_warm(path: Path, expected_sha: str) -> tuple[np.ndarray, dict]:
    if frame.sha(path) != expected_sha:
        raise ValueError("saved failed-iterate source differs")
    report = json.loads(path.read_text())
    if (report["schema"] != "thin_bolted_common_shaft_frame/v1"
            or report["geometry_cache_sha256"] != frame.GEOMETRY_CACHE_SHA
            or report["response"]["converged"] or report["usable_conditional_actions"]
            or not report["failed_response_without_recovered_actions"]
            or "q" in report["response"]):
        raise ValueError("warm initialization must be the preserved failed common-shaft experiment")
    for name, digest in report["source_sha256"].items():
        if frame.sha(frame.ROOT / name) != digest:
            raise ValueError("saved warm experiment dependency differs: " + name)
    q = np.asarray(report["response"]["diagnostic_last_q"], dtype=float)
    if q.shape != (report["counts"]["dofs"],) or not np.isfinite(q).all():
        raise ValueError("finite source-bound failed coefficient vector required")
    metadata = {"path": str(path.resolve().relative_to(frame.ROOT)), "sha256": expected_sha,
                "source_state_id": report["state_id"], "case_id": report["case_id"],
                "accessory_placement": report["accessory_placement"], "dofs": len(q),
                "saved_gradient_inf_n": report["response"]["gradient_inf_n"],
                "reference_discretization": {key: report["parameters"][key]
                                             for key in ("panel_intervals", "beam_size_mm", "shaft_max_segment_mm")},
                "initialization_only": True, "accepted_forces_or_resistance_transferred": False}
    return q, metadata


def concise_common_print(value, **kwargs):
    """Keep failed diagnostic arrays in their artifact rather than the console."""
    if isinstance(value, str) and value.startswith("{"):
        payload = json.loads(value)
        failure = payload.get("failure")
        if failure:
            payload["failure"] = {key: item for key, item in failure.items()
                                  if key not in ("diagnostic_last_q", "iteration_history")}
            payload["failure"]["diagnostic_last_q_count"] = len(failure.get("diagnostic_last_q") or [])
            payload["failure"]["iteration_history_count"] = len(failure.get("iteration_history") or [])
            value = json.dumps(payload)
    builtins.print(value, **kwargs)


def enabled_floor_hosts(linear, material, tangents):
    """Observe the existing pattern without changing its energy or supports."""
    difference = linear.diagonal() - material.diagonal()
    contributions = {}
    for row in tangents:
        diagonal = row["stiffness"] * np.asarray(row["B"].power(2).sum(axis=0)).ravel()
        contributions[row["first"]] = contributions.get(row["first"], 0.) + diagonal
    enabled = []
    reconstructed = np.zeros_like(difference)
    for name, diagonal in contributions.items():
        index = int(np.argmax(diagonal))
        if diagonal[index] <= 0.:
            raise ValueError("floor pattern requires a nonzero tangent row")
        tolerance = max(1e-6, 1e-9 * diagonal[index])
        if abs(difference[index] - diagonal[index]) <= tolerance:
            enabled.append(name)
            reconstructed += diagonal
        elif abs(difference[index]) > tolerance:
            raise ValueError("floor tangent support is not an original on/off pattern")
    if not np.allclose(difference, reconstructed, rtol=1e-9, atol=1e-5):
        raise ValueError("observed floor pattern does not reproduce the linear diagonal")
    return sorted(enabled)


def main():
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--warm-start", type=Path)
    parser.add_argument("--warm-start-sha256")
    custom, remainder = parser.parse_known_args(arguments)
    if bool(custom.warm_start) != bool(custom.warm_start_sha256):
        parser.error("warm path and expected source SHA must be supplied together")
    if frame.sha(Path(previous.__file__)) != PREVIOUS_DRIVER_SHA:
        raise ValueError("preserve the preceding numerical retry driver")
    if frame.sha(CERTIFICATE) != CERTIFICATE_SHA or frame.sha(Path(incremental.__file__)) != INCREMENTAL_SHA:
        raise ValueError("preserve the reviewed incremental method and certificate")
    warm_q, warm = (None, None) if custom.warm_start is None else read_warm(custom.warm_start, custom.warm_start_sha256)
    if warm:
        mapping_parser = argparse.ArgumentParser(add_help=False)
        mapping_parser.add_argument("--intervals", type=int, default=8)
        mapping_parser.add_argument("--beam-size", type=float, default=150.)
        mapping_parser.add_argument("--shaft-segment", type=float, default=25.)
        mapping, _ = mapping_parser.parse_known_args(remainder)
        if warm["reference_discretization"] != {"panel_intervals": mapping.intervals,
                                               "beam_size_mm": mapping.beam_size,
                                               "shaft_max_segment_mm": mapping.shaft_segment}:
            raise ValueError("warm reuse requires the unchanged reference degree-of-freedom mapping")
        warm["reference_discretization_matches_requested"] = True
    pins = incremental.source_pins()
    certificate_sha = frame.sha(CERTIFICATE)
    pins[str(CERTIFICATE.relative_to(frame.ROOT))] = certificate_sha
    for name, expected in json.loads(CERTIFICATE.read_text())["source_sha256"].items():
        if frame.sha(frame.ROOT / name) != expected:
            raise ValueError("incremental method certificate source differs: " + name)
    if warm:
        pins[warm["path"]] = warm["sha256"]
    driver = Path(__file__)
    driver_sha = frame.sha(driver)
    pins[str(driver.relative_to(frame.ROOT))] = driver_sha
    original_evaluate = frame.evaluate_elastic

    def solve(*args, **kwargs):
        material, _, _, contacts, tangents = args
        original_fields = incremental.ORIGINAL_FIELDS
        patterns = []
        latest_linear = None

        def fields(linear, *inputs, **options):
            nonlocal latest_linear
            result = original_fields(linear, *inputs, **options)
            if options.get("tangent"):
                if linear is not latest_linear:
                    patterns.append({"pattern_index": len(patterns),
                                     "enabled_centroid_xy_hosts": enabled_floor_hosts(linear, material, tangents)})
                    latest_linear = linear
                normals = {}
                for row, force in zip(contacts, result[4], strict=True):
                    if row["kind"] == "floor_normal":
                        normals[row["first"]] = normals.get(row["first"], 0.) + float(force)
                patterns[-1].update(last_gradient_inf_n=float(abs(result[0]).max()),
                                    last_floor_normal_force_n_by_host=normals)
            return result

        with patch.object(incremental, "ORIGINAL_FIELDS", fields):
            result = incremental.compatible_contact_solve(*args, **kwargs, warm_q=warm_q)
        result["floor_pattern_diagnostics"] = patterns
        result["floor_pattern_observer_changes_physical_fields"] = False
        return result

    def evaluate(*args, **kwargs):
        report = original_evaluate(*args, **kwargs)
        if frame.sha(driver) != driver_sha or frame.sha(CERTIFICATE) != certificate_sha:
            raise ValueError("incremental driver or method certificate changed during evaluation")
        if warm and frame.sha(frame.ROOT / warm["path"]) != warm["sha256"]:
            raise ValueError("warm experiment changed during evaluation")
        report["source_sha256"].update(pins)
        report["incremental_continuation_execution"] = {
            "command": [sys.executable, "-m", "scripts.run_thin_bolted_common_shaft_incremental", *arguments],
            "reused_driver_sha256": PREVIOUS_DRIVER_SHA,
            "numerical_method_module": "scripts.thin_bolted_incremental_step",
            "method_certificate_sha256": certificate_sha, "warm_initialization": warm,
            "published_energy_forces_and_tolerance_are_original": True,
            "new_energy_arithmetic_only": True,
        }
        return report

    facade = SimpleNamespace(__file__=incremental.__file__, source_pins=incremental.source_pins,
                             compatible_contact_solve=solve)
    old_argv = copy.copy(sys.argv)
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(previous, "numerical", facade),
              patch.object(previous, "NUMERICAL_SHA", pins["scripts/thin_bolted_incremental_step.py"]),
              patch.object(previous, "CERTIFICATE", CERTIFICATE),
              patch.object(previous, "CERTIFICATE_SHA", certificate_sha),
              patch.object(previous, "STRATEGY", STRATEGY),
              patch.object(frame, "evaluate_elastic", evaluate),
              patch.object(previous.common, "print", concise_common_print, create=True)):
            previous.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
