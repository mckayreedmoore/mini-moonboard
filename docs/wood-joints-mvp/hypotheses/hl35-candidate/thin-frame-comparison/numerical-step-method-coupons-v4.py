"""Record three tiny validated fixtures using their pinned input constructors."""

import importlib.util
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_numerical_step as step


def main():
    test_path = frame.ROOT / "tests/test_thin_bolted_numerical_step.py"
    spec = importlib.util.spec_from_file_location("numerical_coupons", test_path)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    rows = []
    for name, inputs, expected in (
        ("loaded_inactive_radial_and_axial_modes", fixtures.inactive_fixture(), {"q": [1.02, -1., 1.04, .63, .84]}),
        ("unloaded_floating_translations", fixtures.inactive_fixture(0., (0., 0.)), {"host_translations_mm": [1., -1.], "capture_forces_n": [0., 0.]}),
        ("unequal_two_support_circular_shaft", fixtures.unequal_supported_shaft()[:4], {"radial_reactions_n": [7.5, 2.5]}),
    ):
        response = step.compatible_contact_solve(*inputs, [])
        if not response["converged"] or response["gradient_inf_n"] >= 1e-5:
            raise ValueError("known-answer fixture does not converge under original laws")
        rows.append({"name": name, "hand_equilibrium_reference": expected, "response": response})
    source = Path(__file__).resolve()
    failed = frame.PACKET / "compatible-common-shaft-a12-rear-v4.json"
    output = frame.PACKET / "numerical-step-method-coupons-v4.json"
    if output.exists():
        raise FileExistsError("preserve numerical method coupons")
    pins = step.source_pins()
    pins.update({str(source.relative_to(frame.ROOT)): frame.sha(source), str(test_path.relative_to(frame.ROOT)): frame.sha(test_path),
                 str(failed.relative_to(frame.ROOT)): frame.sha(failed)})
    result = {"schema": "thin_bolted_numerical_step_method_coupons/v1", "source_sha256": pins,
        "command": "OPENBLAS_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/numerical-step-method-coupons-v4.py",
        "known_answer_coupons": rows,
        "validation": {"tests": 6, "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_numerical_step.py",
            "lint_command": ".venv/bin/ruff check scripts/thin_bolted_numerical_step.py tests/test_thin_bolted_numerical_step.py",
            "physical_gradient_tolerance_n": 1e-5, "body_force_tolerance_n": frame.BODY_FORCE_TOLERANCE_N,
            "body_moment_tolerance_nmm": frame.BODY_MOMENT_TOLERANCE_NMM,
            "physical_energy_gradient_hessian_derivative_coupon": True, "failed_actual_iterate_is_separate_from_actions": True},
        "limits": ["The preserved first common-shaft candidate state stopped at100iterations and21.828543799365463N residual; it supplies no valid force actions.",
            "Open inactive contact modes do not alone establish a physical mechanism. The continuation changes numerical steps only and adds no physical spring, clamp or gauge.",
            "These small fixtures do not guarantee convergence of the candidate. A fresh candidate state must retain the original laws/tolerances and independently close all132 body and global force/moment balances.",
            "First-order beam/plate/port applicability, unmeasured stiffness and clearances, delivered product geometry/material and component resistance remain separate conditional requirements."],
        "release": frame.RELEASE, "candidate_strength_or_release_established": False}

    def scalar(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)

    output.write_text(json.dumps(result, indent=2, allow_nan=False, default=scalar) + "\n")
    print(json.dumps({"output": str(output), "sha256": frame.sha(output), "producer_sha256": step.LOADED_PRODUCER_SHA256}))


if __name__ == "__main__":
    main()
