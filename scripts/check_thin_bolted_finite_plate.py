"""Small known-answer certificate for the objective finite plate API."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_plate as finite
from scripts import thin_bolted_panel_mechanics as retained


def coupons() -> dict:
    basis = retained.SheetBasis(12., 8., 1)
    plate = finite.FinitePlate(basis)
    greville = np.array([basis.knots[i + 1:i + 4].mean() for i in range(basis.order)])
    x, y = np.meshgrid(12 * greville, 8 * greville, indexing="ij")
    reference = np.c_[x.ravel(), y.ravel(), np.zeros(basis.size)]
    angle = math.radians(20.)
    rotation = np.array([[1., 0., 0.], [0., math.cos(angle), -math.sin(angle)],
                         [0., math.sin(angle), math.cos(angle)]])
    translation = np.array([7., -11., 13.])
    q = (reference @ (rotation - np.eye(3)).T + translation).T.ravel()
    point = np.array([4.3, 3.7])
    local = plate.point_energy(q, point)
    port = plate.point_port(q, point, 100 + retained.CAT / 2)
    rigid = {"rotation_deg": 20., "maximum_absolute_Green_strain": float(abs(local["strain"]).max()),
             "maximum_absolute_curvature_per_mm": float(abs(local["curvature"]).max()),
             "energy_density_n_per_mm": local["energy_per_reference_area_n_per_mm"],
             "offset_port_position_error_mm": float(np.linalg.norm(port["position_xyz_mm"]
                 - rotation @ np.r_[point, 100 + retained.CAT / 2] - translation))}
    values = np.array([[1.02, .01, .08], [-.02, .99, -.03], [.001, -.002, .004],
                       [.002, .003, -.001], [-.001, .002, .005]])
    base = plate.section.local_energy(values)
    step = 1e-6
    gradient, tangent = [], []
    for column in range(15):
        delta = np.zeros((5, 3)); delta.ravel()[column] = step
        plus, minus = plate.section.local_energy(values + delta), plate.section.local_energy(values - delta)
        gradient.append((plus["energy_per_reference_area_n_per_mm"] - minus["energy_per_reference_area_n_per_mm"]) / (2 * step))
        tangent.append((plus["local_gradient"] - minus["local_gradient"]) / (2 * step))
    gradient, tangent = np.asarray(gradient), np.asarray(tangent).T
    derivatives = {"central_difference_step": step,
                   "gradient_relative_L2_error": float(np.linalg.norm(gradient - base["local_gradient"]) / np.linalg.norm(base["local_gradient"])),
                   "full_Hessian_relative_Frobenius_error": float(np.linalg.norm(tangent - base["local_hessian"]) / np.linalg.norm(base["local_hessian"])),
                   "Hessian_relative_symmetry_error": float(np.linalg.norm(base["local_hessian"] - base["local_hessian"].T) / np.linalg.norm(base["local_hessian"]))}
    q = np.random.default_rng(109).normal(scale=.01, size=3 * basis.size)
    direction = np.random.default_rng(100).normal(size=len(q))
    step = 1e-5
    port = plate.point_port(q, point, 100 + retained.CAT / 2)
    plus, minus = plate.point_port(q + step * direction, point, 100 + retained.CAT / 2), plate.point_port(q - step * direction, point, 100 + retained.CAT / 2)
    jacobian = (plus["position_xyz_mm"] - minus["position_xyz_mm"]) / (2 * step)
    hessian = (plus["jacobian_xyz_per_coefficient"] - minus["jacobian_xyz_per_coefficient"]) / (2 * step)
    analytic_j = port["jacobian_xyz_per_coefficient"] @ direction
    analytic_h = np.einsum("ijk,k->ij", port["hessian_xyz_per_coefficient_squared"], direction)
    offset = {"z_mm": 100 + retained.CAT / 2, "central_difference_step_mm": step,
              "directional_Jacobian_relative_L2_error": float(np.linalg.norm(jacobian - analytic_j) / np.linalg.norm(analytic_j)),
              "directional_Hessian_relative_Frobenius_error": float(np.linalg.norm(hessian - analytic_h) / np.linalg.norm(analytic_h))}
    points, weights = basis.quadrature()
    tangent = plate.energy(np.zeros_like(q), points, weights)["hessian_n_per_mm"]
    original = retained.plate_matrix(basis, points, weights)
    linear = {"maximum_absolute_Hessian_difference_n_per_mm": float(abs(tangent - original).max()),
              "relative_Frobenius_difference": float(np.linalg.norm(tangent - original) / np.linalg.norm(original))}
    return {"rigid_rotation": rigid, "local_derivatives": derivatives,
            "offset_point_port": offset, "reference_linear_tangent": linear,
            "certificate_checks_pass": bool(rigid["maximum_absolute_Green_strain"] < 1e-13
                and rigid["maximum_absolute_curvature_per_mm"] < 1e-13
                and rigid["offset_port_position_error_mm"] < 1e-10
                and derivatives["gradient_relative_L2_error"] < 1e-7
                and derivatives["full_Hessian_relative_Frobenius_error"] < 1e-7
                and offset["directional_Jacobian_relative_L2_error"] < 1e-7
                and offset["directional_Hessian_relative_Frobenius_error"] < 1e-7
                and linear["relative_Frobenius_difference"] < 1e-12)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    paths = [Path(__file__), Path(finite.__file__), Path(retained.__file__),
             retained.ROOT / "fea/current_response_materials.py",
             retained.ROOT / "tests/test_thin_bolted_finite_plate.py"]
    pins = {str(path.resolve().relative_to(retained.ROOT)): retained.sha(path) for path in paths}
    observed = coupons()
    retained.require(observed["certificate_checks_pass"], "finite plate coupon certificate failed")
    result = {"schema": "thin_bolted_objective_finite_plate_method/v1", "source_sha256": pins,
              "scope": "standalone flat-reference objective geometry and conditional APA section-energy proxy",
              "parameters": {"thickness_mm": retained.CAT, "strength_axis": "reference physical x",
                             "twist_scale": 1., "reference_area_energy": True},
              "observed_coupons": observed, "pytest_tests_passed": 9, "ruff": "pass",
              "commands": ["UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline python -m pytest tests/test_thin_bolted_finite_plate.py -q",
                           "UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache uv run --offline ruff check scripts/thin_bolted_finite_plate.py scripts/check_thin_bolted_finite_plate.py tests/test_thin_bolted_finite_plate.py",
                           "UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline python -m scripts.check_thin_bolted_finite_plate --out NEW_UNUSED_PATH.json"],
              "primary_sources": ["https://arxiv.org/html/2008.05254v2",
                                  "https://portal.fis.tum.de/de/publications/isogeometric-shell-analysis-with-kirchhoff-love-elements/"],
              "limits": ["Objective midsurface metric/director geometry does not establish plywood laminate, product, nonlinear material or through-thickness constitutive qualification.",
                         "Quadratic reference-area section energy omits Poisson and membrane-bending coupling and higher thickness-metric terms; curvature/strain applicability must be assessed.",
                         "No candidate field, contact solve, native model, actual hold footprint, local hole/seat field or structural acceptance is computed."],
              "release": {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established", "fabrication_released", "structural_released", "climbing_released")}}
    for path, expected in pins.items():
        retained.require(retained.sha(retained.ROOT / path) == expected, "finite method source changed during certificate")
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      "coupon_checks_pass": observed["certificate_checks_pass"]}))


if __name__ == "__main__":
    main()
