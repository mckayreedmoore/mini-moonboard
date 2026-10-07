"""Tiny cancellation and initialization evidence; no candidate assembly or solve."""

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as method

WARM_SHA = "b892159b631b1a125c959d5e08cd86a0603b9eaf122a1fc87b9b44a3598af1ab"


def main():
    warm_path = frame.PACKET / "compatible-common-shaft-a12-rear-continuation-v4.json"
    if frame.sha(warm_path) != WARM_SHA:
        raise ValueError("preserve the failed source field")
    warm = json.loads(warm_path.read_text())
    test_path = frame.ROOT / "tests/test_thin_bolted_incremental_step.py"
    spec = importlib.util.spec_from_file_location("incremental_coupons", test_path)
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    old = tests.old_fixture_module()
    K, applied, q = csr_matrix([[1.]]), np.array([1e8 + 1e-4]), np.array([1e8])
    C, ck, candidate = csr_matrix((1, 1)), np.ones(1), q + 1e-4
    before, after = method.stable_fields(K, applied, [], C, ck, q), method.stable_fields(K, applied, [], C, ck, candidate)
    h = candidate - q
    hand = float((q - applied) @ h + .5 * h @ h)
    answer = method.compatible_contact_solve(K, applied, [], tests.dummy_contact(1), [], warm_q=q)
    rows = []
    for name, inputs in (("loaded_inactive_modes", old.inactive_fixture()),
                         ("unloaded_inactive_modes", old.inactive_fixture(0., (0., 0.))),
                         ("unequal_two_support_circular_shaft", old.unequal_supported_shaft()[:4])):
        response = method.compatible_contact_solve(*inputs, [])
        if not response["converged"] or response["gradient_inf_n"] >= 1e-5:
            raise ValueError("unchanged-law known answer failed")
        rows.append({"name": name, "response": response})
    source = Path(__file__).resolve()
    old_test = frame.ROOT / "tests/test_thin_bolted_numerical_step.py"
    pins = method.source_pins()
    pins.update({str(source.relative_to(frame.ROOT)): frame.sha(source), str(test_path.relative_to(frame.ROOT)): frame.sha(test_path),
                 str(old_test.relative_to(frame.ROOT)): frame.sha(old_test), str(warm_path.relative_to(frame.ROOT)): WARM_SHA})
    result = {"schema": "thin_bolted_incremental_step_method_coupons/v1", "source_sha256": pins,
        "command": "OPENBLAS_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/incremental-step-method-coupons-v4.py",
        "linear_cancellation_coupon": {"old_total_potential_nmm": float(before[1]), "new_total_potential_nmm": float(after[1]),
            "direct_total_difference_nmm": float(after[1]) - float(before[1]), "hand_increment_nmm": hand,
            "stable_increment_nmm": -(before[1] - after[1]), "warm_response": answer},
        "reused_known_answer_coupons": rows,
        "validation": {"tests": 15, "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_incremental_step.py",
            "lint_command": ".venv/bin/ruff check scripts/thin_bolted_incremental_step.py tests/test_thin_bolted_incremental_step.py",
            "additional_coverage": ["factorized unilateral quadratic remainder across activation", "circular remainder across gap and reversed direction",
                "radial transverse curvature beneath total-energy roundoff", "ordinary-scale equality to original potential differences",
                "actual warm initialization rebalanced to original force tolerance", "unmapped/nonfinite warm arrays rejected"],
            "physical_force_tolerance_n": 1e-5, "body_force_tolerance_n": frame.BODY_FORCE_TOLERANCE_N,
            "body_moment_tolerance_nmm": frame.BODY_MOMENT_TOLERANCE_NMM},
        "candidate_warm_source": {"path": str(warm_path.relative_to(frame.ROOT)), "sha256": WARM_SHA, "state_id": warm["state_id"],
            "diagnostic_dof_count": len(warm["response"]["diagnostic_last_q"]), "original_gradient_inf_n": warm["response"]["gradient_inf_n"],
            "source_is_a_converged_force_field": False, "candidate_q_used_in_this_coupon_execution": False},
        "limits": ["Stable increments change numerical energy arithmetic only; all forces, gradients, Hessians, published scalar energy, contact laws and tolerances retain the frozen definitions.",
            "Saved candidate diagnostic q is only an initialization. Its parameters/DOF map and complete source identity must match the new solve; no prior force field or acceptance transfers.",
            "These small coupon results do not establish candidate convergence, first-order applicability, actual stiffness bounds or strength. A recovered state must independently close all132 bodies and global force/moment equilibrium."],
        "release": frame.RELEASE, "candidate_strength_or_release_established": False}

    def scalar(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)

    output = frame.PACKET / "incremental-step-method-coupons-v4.json"
    if output.exists():
        raise FileExistsError("preserve incremental method evidence")
    output.write_text(json.dumps(result, indent=2, allow_nan=False, default=scalar) + "\n")
    print(json.dumps({"output": str(output), "sha256": frame.sha(output), "producer_sha256": method.LOADED_PRODUCER_SHA256}))


if __name__ == "__main__":
    main()
