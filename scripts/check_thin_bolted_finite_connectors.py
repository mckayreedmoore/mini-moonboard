"""Record small objective spring coupons; no geometry or frame solve."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_connectors as method
from scripts import thin_bolted_frame_mechanics as frame


def main():
    test_path = frame.ROOT / "tests/test_thin_bolted_finite_connectors.py"
    spec = importlib.util.spec_from_file_location("finite_connector_fixtures", test_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    fixture.test_fixed_director_matches_the_frozen_axial_circular_gap_law()
    fixture.test_distinct_capture_datums_do_not_create_rigid_rotation_compression()
    fixture.test_zero_gap_at_zero_slip_keeps_the_reference_lateral_tangent()
    rows = []
    for degrees in (0., 20., 73.):
        angle = np.deg2rad(degrees)
        first = fixture.rotating_field(np.array([3., 2., 1.]), angle, 1, 0)
        second = fixture.rotating_field(np.array([1., 0., -.2]), angle, 1, 0)
        director = fixture.rotating_field(np.array([1., 0., 0.]), angle, 1, 0)
        r = method.connector_response(first, second, director, axial_stiffness_n_mm=13.,
                                      lateral_stiffness_n_mm=27., radial_gap_mm=.3)
        reference = .5 * 13 * 2**2 + .5 * 27 * (np.sqrt(2**2 + 1.2**2) - .3)**2
        rows.append({"common_rigid_rotation_deg": degrees, "energy_nmm": r["energy_nmm"],
                     "reference_energy_nmm": reference, "energy_error_nmm": abs(r["energy_nmm"] - reference),
                     "rigid_work_gradient_max_n": float(abs(r["gradient_n"]).max()),
                     "rigid_tangent_max_n_mm": float(abs(r["hessian_csr"].toarray()).max()),
                     "spatial_moment_residual_norm_nmm": float(np.linalg.norm(r["pair_spatial_moment_residual_nmm"]))})
    q = np.array([.1, -.05, .03, .02, -.04, -.1, .12])
    response = fixture.nonlinear_response(q)
    step = 1e-5
    perturbations = np.eye(len(q)) * step
    grad = np.array([(fixture.nonlinear_response(q + d)["energy_nmm"] - fixture.nonlinear_response(q - d)["energy_nmm"])
                     / (2 * step) for d in perturbations])
    tangent = np.column_stack([(fixture.nonlinear_response(q + d)["gradient_n"] - fixture.nonlinear_response(q - d)["gradient_n"])
                              / (2 * step) for d in perturbations])
    derivative = {"energy_gradient_max_abs_error": float(abs(grad - response["gradient_n"]).max()),
                  "gradient_tangent_max_abs_error": float(abs(tangent - response["hessian_csr"].toarray()).max()),
                  "director_spatial_couple_xyz_nmm": response["moment_on_director_owner_xyz_nmm"].tolist(),
                  "pair_spatial_moment_residual_nmm": response["pair_spatial_moment_residual_nmm"].tolist()}
    if any(row["energy_error_nmm"] > 1e-10 or row["rigid_work_gradient_max_n"] > 1e-10
           or row["rigid_tangent_max_n_mm"] > 1e-9 for row in rows):
        raise ValueError("objective known-answer spring coupon failed")
    if max(derivative["energy_gradient_max_abs_error"], derivative["gradient_tangent_max_abs_error"]) > 1e-8:
        raise ValueError("finite spring derivative coupon failed")
    paths = (Path(__file__), Path(method.__file__), Path(frame.__file__), test_path)
    result = {"schema": "thin_bolted_finite_connector_method/v1",
              "source_sha256": {str(p.resolve().relative_to(frame.ROOT)): frame.sha(p) for p in paths},
              "command": ".venv/bin/python -m scripts.check_thin_bolted_finite_connectors",
              "known_answer_rigid_coupons": rows, "finite_derivative_coupon": derivative,
              "reference_axial_radial_contact_laws_reused": True,
              "distinct_pressure_and_support_datums_do_not_create_rigid_compression": True,
              "validation": {"test_fixture_count": 8, "test_command": ".venv/bin/python -m pytest -q tests/test_thin_bolted_finite_connectors.py",
                             "lint_command": ".venv/bin/ruff check scripts/thin_bolted_finite_connectors.py scripts/check_thin_bolted_finite_connectors.py tests/test_thin_bolted_finite_connectors.py"},
              "limits": ["Caller must authenticate actual position/director jets and declare the director owner.",
                         "Spatial director couples must enter current-point body/global wrench recovery; they are not rotation-coordinate work duals.",
                         "Physical stiffness, local bearing pressure, own washer prying and component resistance are not qualified.",
                         "These isolated method coupons do not establish an integrated finite frame state or candidate acceptance."],
              "release": frame.RELEASE, "integrated_frame_or_candidate_acceptance_established": False}
    output = frame.PACKET / "finite-connector-method-v4.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": frame.sha(output),
                      "helper_sha256": frame.sha(Path(method.__file__)), "coupons": 8}))


if __name__ == "__main__":
    main()
