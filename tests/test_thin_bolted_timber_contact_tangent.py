"""New admission seam over frozen known-matrix/chart methods only.

Admission is explicitly stubbed for a synthetic70-shaft map. The real frozen
quotient and isotropic roll-generator methods run on a geometry-only facade;
no 132-body candidate gate, CAD, K/response preparation or coupled solve runs.
"""

import copy
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import eye

from scripts import thin_bolted_timber_contact_tangent as wrapper


def fixture(monkeypatch, *, mutate_field=None, mutate_receipt=None, mutate_current=None):
    ndof = 840
    mapping = {"ndof": ndof, "mechanical_bodies": {}, "panels": {}}
    shafts = {}
    for i in range(70):
        name = f"shaft/coupon-{i}"; index = np.arange(12*i, 12*(i+1)).reshape(2, 6)
        mapping["mechanical_bodies"][name] = {"kind": "shaft", "node_dof_indices": index.tolist(),
                                             "storage_basis_columns_xyz": np.eye(3).tolist()}
        shafts[name] = {"index": index, "storage_basis": np.eye(3), "appended_first_twist_dof": int(index[0, 3])}
    # __new__ installs only the map required by frozen roll generators: no
    # constructor, material energy, beam assembly or response is evaluated.
    adapter = wrapper.admission.original.finite.isotropic.IsotropicShaftAdapter.__new__(
        wrapper.admission.original.finite.isotropic.IsotropicShaftAdapter)
    adapter.ndof = ndof; adapter.mechanics = SimpleNamespace(shafts=shafts)
    quotient = wrapper.methods.numerical.CircularShaftQuotient(adapter)
    q, gradient = np.zeros(ndof), np.zeros(ndof)
    sources = {path: wrapper.methods.numerical.FROZEN_SOURCES[path] for path in
               ("scripts/thin_bolted_finite_frame.py", "scripts/thin_bolted_isotropic_shaft.py")}
    sources[wrapper.admission.METHOD] = wrapper.admission.METHOD_SHA256
    floor_ids = [f"floor/{i}" for i in range(32)]
    cells = [{"id": f"timber-face/coupon/cell-{i}", "kind": "timber_face_contact",
        "axial_stiffness_n_mm": 10., "axial_tension_only": True, "signed_axial_extension_mm": 0. if i == 0 else .001,
        "lateral_stiffness_n_mm": 0., "radial_gap_mm": 0., "radial_distance_mm": 0.} for i in range(272)]
    field = {"schema": "thin_bolted_finite_frame_response/v1", "state_id": "synthetic-only", "case_id": "coupon",
        "accessory_placement": "coupon", "release": {"candidate_accepted": False, "climbing_released": False},
        "finite_kinematic_map": mapping, "source_sha256": sources, "finite_interaction_actions": cells,
        "response": {"q": q.tolist(), "gradient_n": gradient.tolist(), "potential_energy_nmm": -10.,
            "disabled_floor_support_ids": floor_ids[:1], "floor_xy_enabled_support_ids": floor_ids[1:],
            "floor_normal_reactions_n": {name: 0. if i == 0 else 1. for i, name in enumerate(floor_ids)}}}
    if mutate_field:
        mutate_field(field)
    payload = json.dumps(field).encode()

    def receipt():
        return {"schema": wrapper.admission.SCHEMA, wrapper.admission.SUCCESS: True,
            **{key: field[key] for key in wrapper.IDENTITY_KEYS},
            "field_sha256": hashlib.sha256(payload).hexdigest(),
            "field_canonical_sha256": wrapper.admission.original.canonical_sha(field),
            "source_sha256": {**field["source_sha256"], wrapper.GATE: wrapper.GATE_SHA256},
            "timber_contact_geometry": {"contact_cell_count": 272}, "release": copy.deepcopy(field["release"])}

    supplied = receipt()
    if mutate_receipt:
        mutate_receipt(supplied)
    receipt_payload = json.dumps(supplied).encode()
    seen = []
    def audit(data):
        assert isinstance(data, bytes) and data == payload
        seen.append(data)
        result = receipt()
        if mutate_current:
            mutate_current(result)
        return result
    monkeypatch.setattr(wrapper.admission, "audit_timber_contact_state", audit)
    fields = {**wrapper.FLAGS, "source_sha256": copy.deepcopy(field["source_sha256"]),
        "gradient_n": gradient.copy(), "energy_nmm": -10., "hessian_csr": 2.*eye(ndof, format="csr"),
        "disabled_floor_support_ids": floor_ids[:1], "floor_xy_enabled_support_ids": floor_ids[1:]}
    args = {"admission_receipt_sha256": hashlib.sha256(receipt_payload).hexdigest(), "quotient": quotient,
            "options": wrapper.methods.DirectionOptions(count=2)}
    return fields, q, payload, receipt_payload, args, seen


def run(data):
    fields, q, payload, receipt, args, _ = data
    return wrapper.diagnose_timber_contact_tangent(fields, q, payload, receipt, **args)


def test_positive_original_matrix_new_admission_and_all272_branch_margins(monkeypatch):
    data = fixture(monkeypatch)
    fields, q, payload, _, args, seen = data
    before = fields["hessian_csr"].copy()
    args["quotient"].canonicalize = lambda _q: (_ for _ in ()).throw(AssertionError("canonicalization forbidden"))
    report = run(data)
    assert seen == [payload]
    assert report["Ritz_directions"][0]["original_Rayleigh_quotient_n_per_mm"] == pytest.approx(2.)
    assert len(report["omitted_indices"]) == len(report["original_material_roll_work_by_shaft"]) == 70
    context = report["fixed_contact_context"]
    assert len(context["timber_face_branch_margins"]) == context["timber_face_cell_count"] == 272
    assert "timber-face/coupon/cell-0" in context["exact_axial_kink_ids"]
    assert report["stability_acceptance"] is False
    assert report["global_minimum_eigenvalue_lower_bound"] is None
    assert report["obsolete_admitted_tangent_wrapper_called"] is False
    assert not report["candidate_response_K_tangent_or_native_execution_performed"]
    assert not any(report["release"].values())
    np.testing.assert_array_equal(fields["hessian_csr"].toarray(), before.toarray())
    np.testing.assert_array_equal(q, 0.)


def test_negative_and_skew_original_work_reuses_frozen_method_without_modification(monkeypatch):
    data = fixture(monkeypatch)
    H = data[0]["hessian_csr"].tolil()
    H[0, 0] = -4.; H[0, 1] = 3.; H[1, 0] = -3.
    data[0]["hessian_csr"] = H.tocsr()
    before = data[0]["hessian_csr"].copy()
    direction = np.zeros(840); direction[0] = 2.
    data[4]["directions"] = [{"id": "known-negative", "direction_full_storage_coordinates": direction.tolist()}]
    report = run(data)
    assert report["Ritz_directions"][0]["original_Rayleigh_quotient_n_per_mm"] == pytest.approx(-4.)
    assert report["explicit_direction_work"][0]["original_quadratic_work_dHd_nmm"] == -16.
    assert report["symmetry"]["relative_Frobenius_asymmetry"] > 0.
    assert report["Ritz_directions"][0]["physical_negative_curvature_or_stability_proven"] is False
    np.testing.assert_array_equal(data[0]["hessian_csr"].toarray(), before.toarray())


@pytest.mark.parametrize("mutation", ["old_schema", "missing", "raw", "canonical", "state", "case", "source", "release"])
def test_wrong_already_issued_receipt_rejects(monkeypatch, mutation):
    def changed(receipt):
        if mutation == "old_schema":
            receipt["schema"] = "thin_bolted_independent_finite_admission/v1"
        elif mutation == "missing":
            receipt.pop(wrapper.admission.SUCCESS)
        elif mutation in ("raw", "canonical"):
            receipt["field_sha256" if mutation == "raw" else "field_canonical_sha256"] = "0"*64
        elif mutation in ("state", "case"):
            receipt["state_id" if mutation == "state" else "case_id"] = "other"
        elif mutation == "source":
            receipt["source_sha256"].pop(wrapper.admission.METHOD)
        else:
            receipt["release"]["climbing_released"] = True
    with pytest.raises(ValueError):
        run(fixture(monkeypatch, mutate_receipt=changed))


def test_explicit_receipt_sha_and_immutable_bytes_are_required(monkeypatch):
    data = fixture(monkeypatch); data[4]["admission_receipt_sha256"] = "0"*64
    with pytest.raises(ValueError, match="receipt SHA"):
        run(data)
    data = list(fixture(monkeypatch)); data[2] = bytearray(data[2])
    with pytest.raises(ValueError, match="immutable"):
        run(data)


@pytest.mark.parametrize("mutation", ["q", "gradient", "large_gradient", "energy", "disabled", "enabled",
    "tangent_flag", "placeholder", "twist_support", "double_count", "physical_source", "missing_method",
    "H_dimension", "H_nan", "H_complex", "field_release"])
def test_original_response_or_matrix_mutations_reject(monkeypatch, mutation):
    data = fixture(monkeypatch)
    fields, q, payload, receipt, args, _ = data
    if mutation == "q":
        q[0] = .1
    elif mutation == "gradient":
        fields["gradient_n"][0] = 1e-8
    elif mutation == "large_gradient":
        fields["gradient_n"][0] = 2e-5
    elif mutation == "energy":
        fields["energy_nmm"] += 1e-6
    elif mutation in ("disabled", "enabled"):
        fields["disabled_floor_support_ids" if mutation == "disabled" else "floor_xy_enabled_support_ids"] = []
    elif mutation in ("tangent_flag", "placeholder", "twist_support", "double_count"):
        key = {"tangent_flag": "tangent_requested", "placeholder": "zero_jet_h_placeholders_are_a_physical_tangent",
               "twist_support": "physical_or_numerical_shaft_twist_support_added", "double_count": "shaft_elasticity_replaced_without_double_count"}[mutation]
        fields[key] = not fields[key]
    elif mutation == "physical_source":
        fields["source_sha256"][wrapper.admission.METHOD] = "0"*64
    elif mutation == "missing_method":
        fields["source_sha256"].pop(wrapper.admission.METHOD)
    elif mutation == "H_dimension":
        fields["hessian_csr"] = eye(839, format="csr")
    elif mutation == "H_nan":
        fields["hessian_csr"].data[0] = np.nan
    elif mutation == "H_complex":
        fields["hessian_csr"] = fields["hessian_csr"].astype(complex)
    else:
        field = json.loads(payload); field["release"]["climbing_released"] = True
        payload = json.dumps(field).encode()
    with pytest.raises(ValueError):
        wrapper.diagnose_timber_contact_tangent(fields, q, payload, receipt, **args)


@pytest.mark.parametrize("mutation", ["missing_object", "indices", "omitted", "work_ids", "budget_ids", "work_nan",
                                      "budget_nan", "budget_negative", "over_budget"])
def test_actual70_shaft_quotient_and_full_roll_work_contract(monkeypatch, mutation):
    data = fixture(monkeypatch); quotient = data[4]["quotient"]
    if mutation == "missing_object":
        data[4]["quotient"] = None
    elif mutation == "indices":
        quotient.indices = quotient.indices[::-1]
    elif mutation == "omitted":
        quotient.omitted_indices = quotient.omitted_indices[:-1]
    elif mutation in ("work_ids", "work_nan", "over_budget"):
        original = quotient.gauge_work
        def work(q, g):
            rows = original(q, g)
            if mutation == "work_ids":
                rows.pop(next(iter(rows)))
            else:
                rows[next(iter(rows))] = np.nan if mutation == "work_nan" else 1.
            return rows
        quotient.gauge_work = work
    else:
        original = quotient.gauge_work_budgets
        def budgets(q, g):
            rows = original(q, g)
            if mutation == "budget_ids":
                rows["shaft/foreign"] = rows.pop(next(iter(rows)))
            else:
                rows[next(iter(rows))] = np.nan if mutation == "budget_nan" else -1.
            return rows
        quotient.gauge_work_budgets = budgets
    with pytest.raises(ValueError):
        run(data)


@pytest.mark.parametrize("mutation", ["interior_indices", "storage_basis", "shaft_id", "adapter_ndof",
                                      "first_twist", "roll_generator", "state"])
def test_complete_adapter_map_and_frozen_roll_binding_reject_same_chart_tampering(monkeypatch, mutation):
    data = fixture(monkeypatch)
    fields, q, payload, _, args, _ = data
    mapping = json.loads(payload)["finite_kinematic_map"]
    chart = wrapper.methods.quotient_indices(mapping, q)
    quotient = args["quotient"]; adapter = quotient.shaft_adapter
    row = adapter.mechanics.shafts["shaft/coupon-0"]
    if mutation == "interior_indices":
        row["index"][1, [3, 4]] = row["index"][1, [4, 3]]
    elif mutation == "storage_basis":
        row["storage_basis"] = np.array([[1., 0., 0.], [0., 0., -1.], [0., 1., 0.]])
    elif mutation == "shaft_id":
        adapter.mechanics.shafts["shaft/foreign"] = adapter.mechanics.shafts.pop("shaft/coupon-0")
    elif mutation == "adapter_ndof":
        adapter.ndof -= 1
    elif mutation == "first_twist":
        row["appended_first_twist_dof"] += 1
    elif mutation == "roll_generator":
        adapter.material_roll_generators = lambda _q: {name: np.zeros(840) for name in adapter.mechanics.shafts}
    else:
        adapter.state = lambda _q: np.zeros(840)
    # The omitted/retained indices alone are unchanged in every mutation.
    np.testing.assert_array_equal(quotient.indices, chart["retained_indices"])
    np.testing.assert_array_equal(quotient.omitted_indices, chart["omitted_indices"])
    with pytest.raises(ValueError):
        wrapper.verify_quotient(quotient, chart, mapping, q, fields["gradient_n"])


def test_budget_override_cannot_hide_real_interior_roll_work(monkeypatch):
    data = fixture(monkeypatch)
    fields, q, payload, _, args, _ = data
    mapping = json.loads(payload)["finite_kinematic_map"]
    chart = wrapper.methods.quotient_indices(mapping, q)
    gradient = fields["gradient_n"].copy(); gradient[9] = 2e-9
    quotient = args["quotient"]
    work = quotient.gauge_work(q, gradient)
    assert work["shaft/coupon-0"] == pytest.approx(2e-6)
    quotient.gauge_work_budgets = lambda _q, _g: {name: 1e-5 for name in work}
    with pytest.raises(ValueError, match="cannot be overridden"):
        wrapper.verify_quotient(quotient, chart, mapping, q, gradient)


def test_adapter_map_mutation_during_search_rejects(monkeypatch):
    data = fixture(monkeypatch); original = wrapper.methods.diagnose_matrix
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        data[4]["quotient"].shaft_adapter.mechanics.shafts["shaft/coupon-0"]["index"][1, [3, 4]] = [10, 9]
        return result
    monkeypatch.setattr(wrapper.methods, "diagnose_matrix", changed)
    with pytest.raises(ValueError, match="node indices/storage basis"):
        run(data)


def test_original_matrix_mutation_during_pure_diagnostics_is_rejected(monkeypatch):
    data = fixture(monkeypatch); original = wrapper.methods.diagnose_matrix
    def changed(H, *args, **kwargs):
        result = original(H, *args, **kwargs)
        H.data[0] += 1.
        return result
    monkeypatch.setattr(wrapper.methods, "diagnose_matrix", changed)
    with pytest.raises(ValueError, match="original H changed"):
        run(data)


def test_original_q_mutation_during_pure_diagnostics_is_rejected(monkeypatch):
    data = fixture(monkeypatch); original = wrapper.methods.diagnose_matrix
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        data[1][0] += .1
        return result
    monkeypatch.setattr(wrapper.methods, "diagnose_matrix", changed)
    with pytest.raises(ValueError, match="original q"):
        run(data)


def test_all272_zero_timber_rows_survive_branch_context(monkeypatch):
    data = fixture(monkeypatch, mutate_field=lambda field: [row.update(signed_axial_extension_mm=0.)
                                                          for row in field["finite_interaction_actions"]])
    report = run(data)
    assert len(report["fixed_contact_context"]["exact_axial_kink_ids"]) == 272


def test_missing_timber_branch_row_rejects_even_stubbed_receipt(monkeypatch):
    data = fixture(monkeypatch, mutate_field=lambda field: field["finite_interaction_actions"].pop())
    with pytest.raises(ValueError, match="complete272"):
        run(data)


def test_matching_saved_and_original_full_gradient_still_must_meet_residual_limit(monkeypatch):
    data = fixture(monkeypatch, mutate_field=lambda field: field["response"]["gradient_n"].__setitem__(0, 2e-5))
    data[0]["gradient_n"][0] = 2e-5
    with pytest.raises(ValueError, match="exceeds residual"):
        run(data)


def test_actual_roll_work_retains_omitted_full_gradient_component(monkeypatch):
    data = fixture(monkeypatch, mutate_field=lambda field: field["response"]["gradient_n"].__setitem__(3, 2e-9))
    data[0]["gradient_n"][3] = 2e-9
    # Full residual is below1e-5; frozen material-roll work1000*g is2e-6,
    # exceeding its1e-6 budget. Deleting the omitted dual would conceal this.
    with pytest.raises(ValueError, match="material-roll work exceeds"):
        run(data)


def test_fresh_current_gate_failure_cannot_reuse_old_issued_success(monkeypatch):
    data = fixture(monkeypatch, mutate_current=lambda receipt: receipt.update({wrapper.admission.SUCCESS: False}))
    with pytest.raises(ValueError, match="current timber-contact admission"):
        run(data)


def test_consumed_original_response_source_mutation_during_search_rejects(monkeypatch):
    data = fixture(monkeypatch); original = wrapper.methods.diagnose_matrix
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        data[0]["source_sha256"].pop(wrapper.admission.METHOD)
        return result
    monkeypatch.setattr(wrapper.methods, "diagnose_matrix", changed)
    with pytest.raises(ValueError, match="response changed"):
        run(data)
