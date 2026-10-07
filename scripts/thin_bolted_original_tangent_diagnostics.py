"""Diagnostic quadratic directions of a caller-supplied original finite tangent.

No candidate preparation, response evaluation or solve occurs here. The parent
supplies the unchanged physical tangent at an independently admitted state.
Only known small matrices are evaluated by this module's receipt command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import scipy
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import ArpackError, ArpackNoConvergence, LinearOperator, eigsh

from scripts import thin_bolted_finite_newton as numerical

ROOT = Path(__file__).resolve().parents[1]
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
GATE = "scripts/thin_bolted_finite_state_audit.py"
FROZEN_SOURCES = {
    **numerical.FROZEN_SOURCES,
    "scripts/thin_bolted_finite_newton.py": "039282fa1c06d90b5e899c1c69c2920c003b42db1a8600e390a7a2d9aca75afe",
}
PRIMARY_SOURCES = [
    {"url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigsh.html",
     "use": "Real symmetric operator, which=SA for smallest algebraic Ritz values, k<N; ARPACK returns numerical approximations, not a certified global lower bound."},
    {"url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.ArpackNoConvergence.html",
     "use": "Preserve partial converged eigenpairs and an unresolved-search disposition after a convergence exception."},
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_pins():
    pins = {**FROZEN_SOURCES, OWN: LOADED_SHA256}
    require(all(digest(ROOT / path) == value for path, value in pins.items()),
            "original-tangent diagnostic or frozen quotient source changed")
    return pins


def finite_vector(value, size):
    value = np.asarray(value, dtype=float)
    require(value.shape == (size,) and np.isfinite(value).all(), "complete finite coordinate vector required")
    return value


@dataclass(frozen=True)
class DirectionOptions:
    count: int = 6
    maximum_iterations: int = 2000
    numerical_relative_tolerance: float = 1e-9
    dense_coupon_limit: int = 48
    random_seed: int = 61532

    def __post_init__(self):
        require(all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in
                    (self.count, self.maximum_iterations, self.dense_coupon_limit)), "positive numerical iteration counts required")
        require(isinstance(self.random_seed, int) and not isinstance(self.random_seed, bool)
                and self.random_seed >= 0, "nonnegative numerical random seed required")
        require(np.isfinite(self.numerical_relative_tolerance) and self.numerical_relative_tolerance >= 0,
                "nonnegative finite eigensolver tolerance required")


def quotient_indices(mapping, q, *, expected_shafts=70):
    """Reuse the frozen exact chart constructor with a geometry-only facade."""
    source_pins()
    ndof = mapping["ndof"]
    require(isinstance(ndof, int) and ndof > 0, "positive mapped coordinate count required")
    q = finite_vector(q, ndof)
    shafts = {}
    occupied = []
    for body, row in mapping["mechanical_bodies"].items():
        if row["kind"] != "shaft":
            continue
        indices = np.asarray(row["node_dof_indices"])
        require(indices.ndim == 2 and indices.shape[0] >= 2 and indices.shape[1] == 6
                and np.issubdtype(indices.dtype, np.integer) and not np.issubdtype(indices.dtype, np.bool_)
                and indices.min() >= 0 and indices.max() < ndof, "complete full local shaft node indices required")
        occupied.extend(indices.ravel().tolist())
        shafts[body] = {"appended_first_twist_dof": int(indices[0, 3])}
    require(len(shafts) == expected_shafts and len(occupied) == len(set(occupied)),
            "exact distinct source shaft count and coordinate ownership required")
    facade = SimpleNamespace(ndof=ndof, mechanics=SimpleNamespace(shafts=shafts))
    chart = numerical.CircularShaftQuotient(facade)
    require(np.max(abs(q[chart.omitted_indices]), initial=0.) <= 1e-8,
            "current admitted q must already be in the unchanged minimal local shaft chart")
    return {"retained_indices": chart.indices, "omitted_indices": chart.omitted_indices,
            "shaft_first_local_twist_index_by_body": {body: row["appended_first_twist_dof"] for body, row in shafts.items()},
            "chart": "frozen CircularShaftQuotient: first LOCAL scaled theta_x=0; principal restriction only",
            "physical_twist_support_added": False}


def matrix_digest(matrix):
    h = hashlib.sha256(np.asarray(matrix.shape, dtype="<i8").tobytes())
    for array, dtype in ((matrix.indptr, "<i8"), (matrix.indices, "<i8"), (matrix.data, "<f8")):
        h.update(np.asarray(array, dtype=dtype).tobytes())
    return h.hexdigest()


def direction_work(matrix, direction, gradient=None):
    """Recompute d.H.d against the original matrix; no symmetrized replacement."""
    direction = finite_vector(direction, matrix.shape[0])
    norm = float(np.linalg.norm(direction))
    require(norm > 0., "nonzero explicit direction required")
    action = matrix @ direction
    work = float(direction @ action)
    require(np.isfinite(action).all() and np.isfinite(work), "finite original directional tangent action required")
    return {"direction_squared_storage_norm": norm * norm,
            "original_quadratic_work_dHd_nmm": work,
            "half_second_order_potential_term_nmm": .5 * work,
            "original_Rayleigh_quotient_n_per_mm": work / (norm * norm),
            "first_order_gradient_work_nmm": None if gradient is None else float(finite_vector(gradient, len(direction)) @ direction),
            "quadratic_work_negative_in_supplied_matrix": work < 0.,
            "physical_negative_curvature_or_stability_proven": False}


def diagnose_matrix(hessian, retained_indices, *, gradient=None, options=None, directions=None):
    """Sparse fixed-chart quadratic diagnostics; no stiffness pass threshold."""
    source_pins()
    options = options or DirectionOptions()
    require(not np.iscomplexobj(hessian), "real original physical tangent required")
    original = csr_matrix(hessian, dtype=float, copy=True)
    require(original.shape[0] > 0 and original.shape[0] == original.shape[1]
            and np.isfinite(original.data).all(), "finite square original tangent required")
    original.sum_duplicates()
    original.sort_indices()
    before_sha = matrix_digest(original)
    index = np.asarray(retained_indices)
    require(index.ndim == 1 and len(index) > 0 and np.issubdtype(index.dtype, np.integer)
            and not np.issubdtype(index.dtype, np.bool_) and index.min() >= 0
            and index.max() < original.shape[0] and len(set(index.tolist())) == len(index),
            "distinct in-range retained chart indices required")
    if gradient is not None:
        gradient = finite_vector(gradient, original.shape[0])
    reduced = original[index][:, index]
    skew = original - original.T
    norm = float(np.linalg.norm(original.data))
    symmetry = {"original_Frobenius_norm_n_per_mm": norm,
                "skew_H_minus_HT_Frobenius_norm_n_per_mm": float(np.linalg.norm(skew.data)),
                "relative_Frobenius_asymmetry": None if norm == 0. else float(np.linalg.norm(skew.data) / norm),
                "half_skew_operator_norm_upper_bound_n_per_mm": .5 * float(np.max(np.asarray(abs(skew).sum(axis=1)).ravel(), initial=0.)),
                "original_matrix_modified_or_damped": False}
    size = reduced.shape[0]
    requested = min(options.count, size)
    # This explicit quadratic-form operator satisfies d.S.d=d.H.d. It is not
    # substituted into the physical potential, gradient, tangent or solver.
    symmetric = LinearOperator(reduced.shape, matvec=lambda v: .5 * (reduced @ v + reduced.T @ v), dtype=float)
    search = {"operator": "S=(Hq+Hq.T)/2 solely for real quadratic-form Ritz search",
              "which": "SA (smallest algebraic), without shift/invert", "requested_directions": requested,
              "options": asdict(options), "positive_Ritz_values_are_global_lower_bounds": False}
    if size <= options.dense_coupon_limit:
        values, vectors = np.linalg.eigh(.5 * (reduced.toarray() + reduced.T.toarray()))
        values, vectors = values[:requested], vectors[:, :requested]
        search.update(method="dense symmetric eigh for small matrix only", requested_search_converged=True)
    else:
        require(requested < size, "sparse eigsh requires requested count smaller than chart size")
        try:
            values, vectors = eigsh(symmetric, k=requested, which="SA", tol=options.numerical_relative_tolerance,
                                    maxiter=options.maximum_iterations,
                                    v0=np.random.default_rng(options.random_seed).normal(size=size))
            search.update(method="sparse ARPACK eigsh", requested_search_converged=True)
        except ArpackNoConvergence as error:
            values, vectors = error.eigenvalues, error.eigenvectors
            search.update(method="sparse ARPACK eigsh", requested_search_converged=False, numerical_search_message=str(error))
        except ArpackError as error:
            values, vectors = np.empty(0), np.empty((size, 0))
            search.update(method="sparse ARPACK eigsh", requested_search_converged=False, numerical_search_message=str(error))
    pairs = []
    if values is not None and vectors is not None:
        for col in np.argsort(values):
            v = np.asarray(vectors[:, col], dtype=float)
            require(np.isfinite(v).all() and np.linalg.norm(v) > 0., "finite nonzero Ritz direction required")
            v /= np.linalg.norm(v)
            action = symmetric @ v
            rayleigh = float(v @ action)
            residual = float(np.linalg.norm(action - rayleigh * v))
            full = np.zeros(original.shape[0])
            full[index] = v
            entries = np.argsort(abs(full))[-min(12, len(index)):][::-1]
            pairs.append({"reported_solver_Ritz_value_n_per_mm": float(values[col]),
                **direction_work(original, full, gradient),
                "symmetric_quadratic_operator_residual_L2_n_per_mm": residual,
                "original_restricted_operator_residual_L2_n_per_mm": float(np.linalg.norm(reduced @ v - rayleigh * v)),
                "nearest_some_eigenvalue_interval_of_represented_S_n_per_mm": [rayleigh - residual, rayleigh + residual],
                "interval_is_a_lower_bound_on_smallest_eigenvalue": False,
                "numerical_residual_interval_has_certified_roundoff_or_tangent_error_bound": False,
                "largest_storage_direction_components": [{"global_dof_index": int(i), "component": float(full[i])} for i in entries],
                "direction_full_storage_coordinates": full.tolist()})
    explicit = []
    omitted = np.setdiff1d(np.arange(original.shape[0]), index)
    for row in directions or []:
        d = finite_vector(row["direction_full_storage_coordinates"], original.shape[0])
        explicit.append({"id": row["id"], **direction_work(original, d, gradient),
                         "direction_is_in_current_retained_chart": bool(np.all(d[omitted] == 0.))})
    require(matrix_digest(original) == before_sha, "original diagnostic tangent changed")
    source_pins()
    return {"schema": "thin_bolted_original_tangent_directions/v1", "original_CSR_value_sha256": before_sha,
            "full_coordinate_count": original.shape[0], "retained_coordinate_count": len(index),
            "retained_indices": index.tolist(), "omitted_indices": omitted.tolist(),
            "coordinate_metric": "Euclidean supplied stored coordinates (u_mm,1000theta and panel coefficients); magnitudes depend on this metric",
            "symmetry": symmetry, "direction_search": search, "Ritz_directions": pairs,
            "explicit_direction_work": explicit, "physical_tangent_approximation_error_bound": None,
            "global_minimum_eigenvalue_lower_bound": None, "stability_acceptance": False,
            "limits": ["No damping, physical support, stiffness threshold, candidate assembly or response solve is added.",
                       "A negative Rayleigh direction is a witness for this supplied represented quadratic form only; approximate tangent, roundoff and contact/chart applicability need separate checks.",
                       "Positive or partial Ritz output cannot prove no unsearched negative direction or a global physical stability bound.",
                       "This is a fixed-contact-pattern second-variation diagnostic; contact switching and nonvariational corner activation remain separate."]}


def contact_context(field):
    rows = field["finite_interaction_actions"]
    axial = [{"id": r["id"], "signed_extension_mm": float(r["signed_axial_extension_mm"])} for r in rows
             if r["axial_stiffness_n_mm"] > 0 and r["axial_tension_only"]]
    radial = [{"id": r["id"], "distance_minus_gap_mm": float(r["radial_distance_mm"] - r["radial_gap_mm"])} for r in rows
              if r["lateral_stiffness_n_mm"] > 0 and r["radial_gap_mm"] > 0]
    normals = field["response"]["floor_normal_reactions_n"]
    return {"disabled_floor_support_ids": field["response"]["disabled_floor_support_ids"],
            "floor_xy_enabled_support_ids": field["response"]["floor_xy_enabled_support_ids"],
            "closest_axial_branch_margins": sorted(axial, key=lambda r: abs(r["signed_extension_mm"]))[:12],
            "closest_radial_branch_margins": sorted(radial, key=lambda r: abs(r["distance_minus_gap_mm"]))[:12],
            "exact_axial_kink_ids": [r["id"] for r in axial if r["signed_extension_mm"] == 0.],
            "exact_radial_kink_ids": [r["id"] for r in radial if r["distance_minus_gap_mm"] == 0.],
            "floor_normal_forces_n": normals, "floor_activation_threshold_n": numerical.FLOOR_BEARING_THRESHOLD_N,
            "branch_neighborhood_or_contact_pattern_stability_proven": False}


def diagnose_admitted_tangent(original_fields, original_q, field_payload, admission_payload, *, admission_sha256,
                              admission_receipt_sha256, options=None, directions=None, quotient=None):
    """Parent-only API: supply one original tangent at an admitted current q.

    The receipt is already independently issued; it is checked and reused.
    Origin of H cannot be reconstructed without another response evaluation,
    so the parent remains responsible for supplying H from the original call.
    """
    pins = source_pins()
    require(isinstance(field_payload, bytes), "one immutable released field byte payload required")
    require(isinstance(admission_payload, bytes)
            and hashlib.sha256(admission_payload).hexdigest() == admission_receipt_sha256,
            "one explicitly authenticated immutable admission receipt payload required")
    admission = json.loads(admission_payload)
    require(isinstance(admission_sha256, str) and len(admission_sha256) == 64
            and all(c in "0123456789abcdef" for c in admission_sha256)
            and digest(ROOT / GATE) == admission_sha256, "explicit reviewed finite admission source digest required")
    field = json.loads(field_payload)
    require(field["schema"] == "thin_bolted_finite_frame_response/v1"
            and admission.get("schema") == "thin_bolted_independent_finite_admission/v1"
            and admission.get("independent_finite_current_support_load_and_equilibrium_checks_pass") is True
            and admission.get("field_sha256") == hashlib.sha256(field_payload).hexdigest()
            and admission.get("source_sha256", {}).get(GATE) == admission_sha256
            and all(admission.get(k) == field[k] for k in ("state_id", "case_id", "accessory_placement")),
            "new exact raw-byte current finite admission required")
    q = finite_vector(original_q, field["finite_kinematic_map"]["ndof"])
    require(np.array_equal(q, finite_vector(field["response"]["q"], len(q))), "original tangent q differs from admitted coordinates")
    require(original_fields.get("tangent_requested") is True
            and original_fields.get("zero_jet_h_placeholders_are_a_physical_tangent") is False
            and original_fields.get("physical_or_numerical_shaft_twist_support_added") is False
            and original_fields.get("shaft_elasticity_replaced_without_double_count") is True,
            "caller must supply the unchanged original finite physical tangent response")
    for path, value in original_fields["source_sha256"].items():
        require(field["source_sha256"].get(path) == value and digest(ROOT / path) == value,
                "original tangent physical source differs from admitted source")
    require(all(original_fields["source_sha256"].get(p) == v for p, v in numerical.FROZEN_SOURCES.items()
                if p in ("scripts/thin_bolted_finite_frame.py", "scripts/thin_bolted_isotropic_shaft.py")),
            "original tangent frozen finite methods missing")
    g = finite_vector(original_fields["gradient_n"], len(q))
    require(np.allclose(g, finite_vector(field["response"]["gradient_n"], len(q)), rtol=1e-10, atol=1e-10),
            "original tangent physical gradient differs from admitted residual")
    before_energy, source_energy = float(original_fields["energy_nmm"]), float(field["response"]["potential_energy_nmm"])
    require(np.isfinite([before_energy, source_energy]).all()
            and abs(before_energy-source_energy) <= 32*np.finfo(float).eps*(abs(before_energy)+abs(source_energy)) + 1e-12,
            "original tangent potential differs from admitted potential")
    require(original_fields["disabled_floor_support_ids"] == field["response"]["disabled_floor_support_ids"]
            and original_fields["floor_xy_enabled_support_ids"] == field["response"]["floor_xy_enabled_support_ids"],
            "original tangent fixed floor branch differs from admitted branch")
    chart = quotient_indices(field["finite_kinematic_map"], q)
    if quotient is not None:
        require(np.array_equal(quotient.indices, chart["retained_indices"])
                and np.array_equal(quotient.omitted_indices, chart["omitted_indices"]),
                "parent quotient differs from exact admitted current shaft chart")
    result = diagnose_matrix(original_fields["hessian_csr"], chart["retained_indices"], gradient=g,
                             options=options, directions=directions)
    result.update(field_sha256=admission["field_sha256"], admission_receipt_sha256=admission_receipt_sha256,
                  source_sha256={**pins, GATE: admission_sha256},
                  **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
                  shaft_quotient={key: value for key, value in chart.items() if not isinstance(value, np.ndarray)},
                  fixed_contact_context=contact_context(field),
                  supplied_H_origin_is_parent_responsibility_not_independently_reassembled=True,
                  all_release_and_complete_joint_acceptance_flags=False)
    source_pins()
    require(digest(ROOT / GATE) == admission_sha256, "finite admission source changed during diagnostics")
    return result


def small_method_coupons():
    """Three matrices with exact positive, negative and removable-gauge spectra."""
    positive = diagnose_matrix(csr_matrix(np.diag([2., 3., 5.])), np.arange(3))
    negative = diagnose_matrix(csr_matrix(np.diag([-4., 2., 7.])), np.arange(3))
    full = np.diag(np.arange(1., 13.))
    full[3, 3] = 0.
    mapping = {"ndof": 12, "mechanical_bodies": {"shaft/coupon": {
        "kind": "shaft", "node_dof_indices": np.arange(12).reshape(2, 6).tolist()}}}
    chart = quotient_indices(mapping, np.zeros(12), expected_shafts=1)
    gauge = diagnose_matrix(csr_matrix(full), chart["retained_indices"])
    observed = {"positive_smallest": positive["Ritz_directions"][0]["original_Rayleigh_quotient_n_per_mm"],
                "negative_smallest": negative["Ritz_directions"][0]["original_Rayleigh_quotient_n_per_mm"],
                "gauged_smallest": gauge["Ritz_directions"][0]["original_Rayleigh_quotient_n_per_mm"],
                "gauged_omitted_indices": gauge["omitted_indices"]}
    require(observed == {"positive_smallest": 2., "negative_smallest": -4., "gauged_smallest": 1.,
                         "gauged_omitted_indices": [3]}, "known matrix diagnostic failed")
    return {"known_answers": observed, "positive": positive, "negative": negative, "gauge": gauge,
            "small_known_matrix_coupons_pass": True, "candidate_matrix_prepared_or_evaluated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method-out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.method_out.exists(), "preserve issued method receipt; select a new output path")
    pins = source_pins()
    test = "tests/test_thin_bolted_original_tangent_diagnostics.py"
    pins[test] = digest(ROOT / test)
    report = {"schema": "thin_bolted_original_tangent_diagnostic_method/v1", "source_sha256": pins,
              "observed_coupons": small_method_coupons(), "primary_sources": PRIMARY_SOURCES,
              "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "scope": "Known matrix methods only; caller-supplied original tangent diagnostic API ready for parent-only post-admission use",
              "candidate_field_consumed": False, "candidate_matrix_prepared_or_eigensolved": False,
              "stability_or_strength_acceptance": False, "physical_tangent_error_bound": None,
              "commands": ["OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q " + test,
                           ".venv/bin/ruff check " + OWN + " " + test,
                           "OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.thin_bolted_original_tangent_diagnostics --method-out NEW_UNUSED_PATH.json"]}
    source_pins()
    require(digest(ROOT / test) == pins[test], "diagnostic fixtures changed while issuing receipt")
    args.method_out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
