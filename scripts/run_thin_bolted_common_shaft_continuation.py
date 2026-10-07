"""Retry the unchanged common-shaft problem with reviewed numerical steps.

The failed first experiment, its driver and every physical helper stay frozen.
This outer wrapper binds numerical provenance before the finished-floor state
identity is issued. It also preserves unsolved experiments through the existing
failure exporter without treating diagnostic coefficients as usable actions.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import run_thin_bolted_common_shaft_frame as common
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_numerical_step as numerical

COMMON_DRIVER_SHA = "d2f62c4cc7f98c48dcde5cd9f05b94cd3515eb9314497051a6322a64f2d2a7e8"
NUMERICAL_SHA = "82b7d5a8d9d9dc871ee6410fb4c5854093a998cfd9b331fdd986917b63ebbc28"
CERTIFICATE = frame.PACKET / "numerical-step-method-coupons-v4.json"
CERTIFICATE_SHA = "f3d8532dd38c85b82cb6252187aba46e0cc7219693dfca6c54d0a823c51df40c"
STRATEGY = "adaptive-scaled-Levenberg-original-potential"


def main():
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--newton-limit", type=int, default=500)
    custom, remainder = parser.parse_known_args(arguments)
    if custom.newton_limit < 1:
        parser.error("positive numerical iteration limit required")
    common_path, driver = Path(common.__file__), Path(__file__)
    if frame.sha(common_path) != COMMON_DRIVER_SHA:
        raise ValueError("preserve the frozen common-shaft experiment driver")
    if frame.sha(Path(numerical.__file__)) != NUMERICAL_SHA or frame.sha(CERTIFICATE) != CERTIFICATE_SHA:
        raise ValueError("preserve the reviewed numerical method and certificate")
    numerical_pins = numerical.source_pins()
    pins = dict(numerical_pins)
    pins[str(CERTIFICATE.relative_to(frame.ROOT))] = CERTIFICATE_SHA
    pins[str(common_path.relative_to(frame.ROOT))] = COMMON_DRIVER_SHA
    driver_sha = frame.sha(driver)
    pins[str(driver.relative_to(frame.ROOT))] = driver_sha
    original_evaluate = frame.evaluate_elastic

    def solve(K, applied, groups, contacts, tangents, max_iterations=100):
        return numerical.compatible_contact_solve(K, applied, groups, contacts, tangents,
                                                  max_iterations=custom.newton_limit)

    def evaluate(*args, **kwargs):
        report = original_evaluate(*args, **kwargs)
        if numerical.source_pins() != numerical_pins or frame.sha(CERTIFICATE) != CERTIFICATE_SHA:
            raise ValueError("numerical strategy changed during evaluation")
        if frame.sha(driver) != driver_sha or frame.sha(common_path) != COMMON_DRIVER_SHA:
            raise ValueError("numerical continuation driver changed during evaluation")
        report["parameters"].update({"numerical_continuation_method": STRATEGY,
                                      "numerical_newton_iteration_limit_per_floor_pattern": custom.newton_limit})
        report["source_sha256"].update(pins)
        report["numerical_continuation_execution"] = {
            "command": [sys.executable, "-m", "scripts.run_thin_bolted_common_shaft_continuation", *arguments],
            "physical_laws_changed": False, "physical_force_tolerance_changed": False,
            "numerical_damping_is_physical_stiffness": False,
            "failed_first_experiment_preserved": True,
            "newton_limit_per_floor_pattern": custom.newton_limit,
            "force_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
            "method_certificate_path": str(CERTIFICATE.relative_to(frame.ROOT)),
            "method_certificate_sha256": CERTIFICATE_SHA,
        }
        return report

    old_argv = copy.copy(sys.argv)
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(frame, "compatible_contact_solve", solve),
              patch.object(frame, "evaluate_elastic", evaluate)):
            common.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
