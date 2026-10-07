"""Known matrix and admission contracts; no candidate tangent is prepared."""

import hashlib
import json

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import ArpackNoConvergence

from scripts import thin_bolted_original_tangent_diagnostics as diagnostics


def observed_values(result):
    return [row["original_Rayleigh_quotient_n_per_mm"] for row in result["Ritz_directions"]]


def shaft_map():
    return {"ndof": 12, "mechanical_bodies": {"shaft/coupon": {
        "kind": "shaft", "node_dof_indices": np.arange(12).reshape(2, 6).tolist()}}}


def test_positive_matrix_spectrum_is_not_a_stability_acceptance():
    result = diagnostics.diagnose_matrix(csr_matrix(np.diag([2., 3., 5.])), np.arange(3))
    assert observed_values(result) == pytest.approx([2., 3., 5.])
    assert result["symmetry"]["relative_Frobenius_asymmetry"] == 0.
    assert result["global_minimum_eigenvalue_lower_bound"] is None
    assert result["stability_acceptance"] is False


def test_negative_direction_retains_original_work_and_eigen_residual():
    result = diagnostics.diagnose_matrix(csr_matrix([[-2., 1.], [1., 1.]]), np.arange(2))
    expected = np.linalg.eigvalsh([[-2., 1.], [1., 1.]])
    assert observed_values(result) == pytest.approx(expected)
    witness = result["Ritz_directions"][0]
    assert witness["quadratic_work_negative_in_supplied_matrix"] is True
    assert witness["symmetric_quadratic_operator_residual_L2_n_per_mm"] < 1e-14
    assert witness["physical_negative_curvature_or_stability_proven"] is False


def test_exact_frozen_quotient_omits_one_local_first_twist_and_no_bending():
    chart = diagnostics.quotient_indices(shaft_map(), np.zeros(12), expected_shafts=1)
    np.testing.assert_array_equal(chart["omitted_indices"], [3])
    assert 4 in chart["retained_indices"] and 5 in chart["retained_indices"]
    matrix = np.diag(np.arange(1., 13.))
    matrix[3, 3] = 0.
    result = diagnostics.diagnose_matrix(csr_matrix(matrix), chart["retained_indices"])
    assert min(observed_values(result)) == pytest.approx(1.)
    assert chart["physical_twist_support_added"] is False


def test_noncanonical_current_chart_and_duplicate_shaft_coordinates_reject():
    q = np.zeros(12)
    q[3] = .01
    with pytest.raises(ValueError, match="already"):
        diagnostics.quotient_indices(shaft_map(), q, expected_shafts=1)
    mapping = shaft_map()
    mapping["mechanical_bodies"]["shaft/duplicate"] = mapping["mechanical_bodies"]["shaft/coupon"]
    with pytest.raises(ValueError, match="ownership"):
        diagnostics.quotient_indices(mapping, np.zeros(12), expected_shafts=2)


def test_sparse_smallest_algebraic_search_finds_negative_value_not_small_magnitude():
    matrix = csr_matrix(np.diag([-4., .001, 2., 7., 9., 11.]))
    result = diagnostics.diagnose_matrix(matrix, np.arange(6), options=diagnostics.DirectionOptions(count=2, dense_coupon_limit=2))
    assert observed_values(result) == pytest.approx([-4., .001], abs=1e-12)
    assert result["direction_search"]["requested_search_converged"] is True
    assert result["direction_search"]["positive_Ritz_values_are_global_lower_bounds"] is False


def test_partial_arpack_result_remains_numerically_unresolved(monkeypatch):
    def unfinished(*args, **kwargs):
        raise ArpackNoConvergence("fixture iteration limit", np.array([1.]), np.eye(6)[:, :1])
    monkeypatch.setattr(diagnostics, "eigsh", unfinished)
    result = diagnostics.diagnose_matrix(csr_matrix(np.diag(np.arange(1., 7.))), np.arange(6),
                                         options=diagnostics.DirectionOptions(count=2, dense_coupon_limit=2))
    assert observed_values(result) == [1.]
    assert result["direction_search"]["requested_search_converged"] is False
    assert result["stability_acceptance"] is False


def test_skew_is_disclosed_and_original_matrix_and_work_are_preserved():
    matrix = csr_matrix([[2., 4.], [-4., 3.]])
    before = matrix.copy()
    result = diagnostics.diagnose_matrix(matrix, np.arange(2), directions=[{
        "id": "hand", "direction_full_storage_coordinates": [2., 3.]}], gradient=[5., 7.])
    assert observed_values(result) == pytest.approx([2., 3.])
    np.testing.assert_array_equal(matrix.toarray(), before.toarray())
    assert result["symmetry"]["skew_H_minus_HT_Frobenius_norm_n_per_mm"] == pytest.approx(np.sqrt(128))
    assert result["symmetry"]["half_skew_operator_norm_upper_bound_n_per_mm"] == 4.
    assert result["Ritz_directions"][0]["original_restricted_operator_residual_L2_n_per_mm"] == 4.
    explicit = result["explicit_direction_work"][0]
    assert explicit["original_quadratic_work_dHd_nmm"] == 35.
    assert explicit["half_second_order_potential_term_nmm"] == 17.5
    assert explicit["first_order_gradient_work_nmm"] == 31.


def test_explicit_full_space_direction_is_not_silently_projected_into_chart():
    result = diagnostics.diagnose_matrix(csr_matrix(np.diag([2., -3., 5.])), np.array([0, 2]),
        directions=[{"id": "outside-chart", "direction_full_storage_coordinates": [0., 2., 0.]}])
    row = result["explicit_direction_work"][0]
    assert row["original_quadratic_work_dHd_nmm"] == -12.
    assert row["direction_is_in_current_retained_chart"] is False
    assert row["physical_negative_curvature_or_stability_proven"] is False


@pytest.mark.parametrize("matrix,index", [(np.eye(2)*np.nan, [0, 1]), (np.ones((2, 3)), [0, 1]),
    (np.eye(2), [0, 0]), (np.eye(2), [0., 1.]), (np.eye(2), [0, 2]), (np.eye(2)*1j, [0, 1])])
def test_bad_original_matrix_or_chart_rejects(matrix, index):
    with pytest.raises(ValueError):
        diagnostics.diagnose_matrix(matrix, np.asarray(index))


def admitted_coupon(monkeypatch):
    """Synthetic orchestration receipt only; never issued as candidate evidence."""
    mapping = shaft_map()
    q = np.zeros(12)
    field = {"schema": "thin_bolted_finite_frame_response/v1", "state_id": "coupon-only", "case_id": "coupon",
        "accessory_placement": "coupon", "finite_kinematic_map": mapping,
        "source_sha256": {p: v for p, v in diagnostics.numerical.FROZEN_SOURCES.items()
                           if p in ("scripts/thin_bolted_finite_frame.py", "scripts/thin_bolted_isotropic_shaft.py")},
        "finite_interaction_actions": [], "response": {"q": q.tolist(), "gradient_n": q.tolist(),
            "potential_energy_nmm": 0., "disabled_floor_support_ids": [], "floor_xy_enabled_support_ids": [],
            "floor_normal_reactions_n": {}}}
    field_payload = json.dumps(field).encode()
    gate_sha = diagnostics.digest(diagnostics.ROOT / diagnostics.GATE)
    receipt = {"schema": "thin_bolted_independent_finite_admission/v1",
        "independent_finite_current_support_load_and_equilibrium_checks_pass": True,
        "field_sha256": hashlib.sha256(field_payload).hexdigest(), "source_sha256": {diagnostics.GATE: gate_sha},
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")}}
    receipt_payload = json.dumps(receipt).encode()
    original = {"tangent_requested": True, "zero_jet_h_placeholders_are_a_physical_tangent": False,
        "physical_or_numerical_shaft_twist_support_added": False, "shaft_elasticity_replaced_without_double_count": True,
        "source_sha256": field["source_sha256"], "gradient_n": q, "energy_nmm": 0.,
        "hessian_csr": csr_matrix(np.diag(np.arange(1., 13.))),
        "disabled_floor_support_ids": [], "floor_xy_enabled_support_ids": []}
    actual_chart = diagnostics.quotient_indices
    monkeypatch.setattr(diagnostics, "quotient_indices", lambda m, state: actual_chart(m, state, expected_shafts=1))
    return original, q, field_payload, receipt_payload, {"admission_sha256": gate_sha,
        "admission_receipt_sha256": hashlib.sha256(receipt_payload).hexdigest()}


def test_parent_original_tangent_wrapper_binds_exact_payload_and_branch(monkeypatch):
    original, q, field, receipt, args = admitted_coupon(monkeypatch)
    result = diagnostics.diagnose_admitted_tangent(original, q, field, receipt, **args)
    assert result["state_id"] == "coupon-only"
    assert result["omitted_indices"] == [3]
    assert result["admission_receipt_sha256"] == args["admission_receipt_sha256"]
    assert result["supplied_H_origin_is_parent_responsibility_not_independently_reassembled"] is True
    assert result["stability_acceptance"] is False


@pytest.mark.parametrize("mutation", ["q", "gradient", "energy", "branch", "receipt", "field", "method-source", "fake-tangent"])
def test_parent_wrapper_rejects_changed_coordinate_field_or_original_response(monkeypatch, mutation):
    original, q, field, receipt, args = admitted_coupon(monkeypatch)
    if mutation == "q":
        q[0] = .1
    elif mutation == "gradient":
        original["gradient_n"] = np.ones(12)
    elif mutation == "energy":
        original["energy_nmm"] = 1.
    elif mutation == "branch":
        original["disabled_floor_support_ids"] = ["different"]
    elif mutation == "receipt":
        receipt += b" "
    elif mutation == "field":
        field += b" "
    elif mutation == "method-source":
        original["source_sha256"] = {}
    else:
        original["tangent_requested"] = False
    with pytest.raises(ValueError):
        diagnostics.diagnose_admitted_tangent(original, q, field, receipt, **args)


def test_known_matrix_method_receipt_coupons():
    assert diagnostics.small_method_coupons()["small_known_matrix_coupons_pass"] is True
