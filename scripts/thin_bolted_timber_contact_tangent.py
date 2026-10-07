"""New timber-contact admission over frozen original-tangent diagnostics.

The parent supplies the original physical response, matrix, state and actual
shaft quotient. Only admission/orchestration is new: no response evaluation,
matrix preparation, coordinate adjustment or physical acceptance occurs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, issparse

from scripts import thin_bolted_original_tangent_diagnostics as methods
from scripts import thin_bolted_timber_contact_admission as admission

ROOT = admission.ROOT
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = methods.digest(Path(__file__))
HELPER = "scripts/thin_bolted_original_tangent_diagnostics.py"
HELPER_SHA256 = "d5870a32dc6a993d9fa4a494f304e9db900e6a0a7d70e6cf748da98e856cf281"
GATE = "scripts/thin_bolted_timber_contact_admission.py"
GATE_SHA256 = "75011f4cfa042a46d8e45eb5716ae01df2edff3418b1439553afb04b14b14632"
IDENTITY_KEYS = ("state_id", "case_id", "accessory_placement")
FLAGS = {"tangent_requested": True, "zero_jet_h_placeholders_are_a_physical_tangent": False,
         "physical_or_numerical_shaft_twist_support_added": False,
         "shaft_elasticity_replaced_without_double_count": True}


def verify_pins(pins):
    for path, expected in pins.items():
        methods.require(isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected) is not None
                        and methods.digest(ROOT/path) == expected, "timber-contact tangent source changed: "+path)


def source_pins():
    methods.require(Path(admission.__file__).resolve() == (ROOT/GATE).resolve()
                    and admission.LOADED_PRODUCER_SHA256 == GATE_SHA256
                    and Path(methods.__file__).resolve() == (ROOT/HELPER).resolve()
                    and methods.LOADED_SHA256 == HELPER_SHA256, "fixed reviewed tangent/admission source required")
    pins = admission.merge_pins(methods.source_pins(),
        {OWN: LOADED_PRODUCER_SHA256, HELPER: HELPER_SHA256, GATE: GATE_SHA256})
    verify_pins(pins)
    return pins


def require_receipt(receipt, field, field_payload):
    methods.require(receipt.get("schema") == admission.SCHEMA and receipt.get(admission.SUCCESS) is True,
                    "distinct current timber-contact admission required")
    methods.require(receipt.get("field_sha256") == hashlib.sha256(field_payload).hexdigest()
                    and receipt.get("field_canonical_sha256") == admission.original.canonical_sha(field)
                    and all(receipt.get(key) == field[key] for key in IDENTITY_KEYS)
                    and receipt.get("source_sha256", {}).get(GATE) == GATE_SHA256,
                    "timber-contact tangent receipt differs from exact bytes/state/gate")
    methods.require(receipt.get("release") and not any(receipt["release"].values()),
                    "tangent admission cannot grant release")


def response_snapshot(fields):
    """Copy only consumed original-response values, without touching its H."""
    return {"flags": {key: fields.get(key) for key in FLAGS},
            "source_sha256": copy.deepcopy(fields["source_sha256"]),
            "gradient_n": np.asarray(fields["gradient_n"]).tolist(), "energy_nmm": float(fields["energy_nmm"]),
            "disabled_floor_support_ids": copy.deepcopy(fields["disabled_floor_support_ids"]),
            "floor_xy_enabled_support_ids": copy.deepcopy(fields["floor_xy_enabled_support_ids"])}


def matrix_snapshot(hessian, ndof):
    methods.require(not np.iscomplexobj(hessian), "real original physical tangent required")
    # The copy is solely a value fingerprint. It never replaces or modifies
    # the supplied H; frozen diagnose_matrix owns its separate search copy.
    matrix = csr_matrix(hessian, copy=True)
    methods.require(matrix.shape == (ndof, ndof) and np.isfinite(matrix.data).all()
                    and not np.iscomplexobj(matrix.data), "full finite square original tangent dimension required")
    return {"format": hessian.format if issparse(hessian) else "dense",
            "dtype": str(hessian.dtype) if hasattr(hessian, "dtype") else "array-like",
            "CSR_value_sha256": methods.matrix_digest(matrix)}


def verify_original_response(fields, original_q, field):
    ndof = field["finite_kinematic_map"]["ndof"]
    q = methods.finite_vector(original_q, ndof).copy()
    methods.require(np.array_equal(q, methods.finite_vector(field["response"]["q"], ndof)),
                    "original tangent q differs from admitted coordinates")
    methods.require(all(fields.get(key) is value for key, value in FLAGS.items()),
                    "unchanged original finite physical tangent response required")
    methods.require(fields.get("candidate_strength_or_release_established", False) is False
                    and not any(fields.get("release", {}).values()), "original tangent cannot assert release")
    sources = fields["source_sha256"]
    for path, value in sources.items():
        methods.require(field["source_sha256"].get(path) == value, "original physical source differs from admitted field")
    required = ("scripts/thin_bolted_finite_frame.py", "scripts/thin_bolted_isotropic_shaft.py",
                admission.METHOD)
    methods.require(all(sources.get(path) == field["source_sha256"].get(path) and path in sources for path in required),
                    "original tangent omits a frozen finite/isotropic/timber-contact producer")
    gradient = methods.finite_vector(fields["gradient_n"], ndof).copy()
    saved_gradient = methods.finite_vector(field["response"]["gradient_n"], ndof)
    methods.require(np.allclose(gradient, saved_gradient, rtol=1e-10, atol=1e-10)
                    and np.max(abs(gradient), initial=0.) <= 1e-5, "original full gradient differs or exceeds residual limit")
    energy, saved_energy = float(fields["energy_nmm"]), float(field["response"]["potential_energy_nmm"])
    budget = 32*np.finfo(float).eps*(abs(energy)+abs(saved_energy))+1e-12
    methods.require(np.isfinite([energy, saved_energy]).all() and abs(energy-saved_energy) <= budget,
                    "original tangent potential differs from admitted potential")
    methods.require(fields["disabled_floor_support_ids"] == field["response"]["disabled_floor_support_ids"]
                    and fields["floor_xy_enabled_support_ids"] == field["response"]["floor_xy_enabled_support_ids"],
                    "original tangent fixed floor branch differs")
    return q, gradient


def verify_quotient_binding(quotient, chart, mapping):
    """Authenticate every coordinate consumed by the frozen roll generators."""
    adapter_type = admission.original.finite.isotropic.IsotropicShaftAdapter
    quotient_type = methods.numerical.CircularShaftQuotient
    methods.require(type(quotient) is quotient_type and type(quotient.shaft_adapter) is adapter_type
                    and quotient.ndof == quotient.shaft_adapter.ndof == mapping["ndof"],
                    "parent actual frozen circular-shaft quotient required")
    methods.require(np.array_equal(quotient.indices, chart["retained_indices"])
                    and np.array_equal(quotient.omitted_indices, chart["omitted_indices"]),
                    "parent quotient differs from exact70 local shaft chart")
    adapter = quotient.shaft_adapter
    expected = {name: row for name, row in mapping["mechanical_bodies"].items() if row["kind"] == "shaft"}
    methods.require(set(adapter.mechanics.shafts) == set(expected), "parent quotient shaft map differs")
    for name, row in adapter.mechanics.shafts.items():
        indices, basis = np.asarray(row["index"]), np.asarray(row["storage_basis"])
        methods.require(indices.dtype.kind in "iu" and np.array_equal(indices, expected[name]["node_dof_indices"])
                        and basis.shape == (3, 3) and np.isfinite(basis).all()
                        and np.array_equal(basis, expected[name]["storage_basis_columns_xyz"])
                        and row["appended_first_twist_dof"] == chart["shaft_first_local_twist_index_by_body"][name],
                        "parent quotient node indices/storage basis differ from admitted map: "+name)
    for obj, implementation, names in ((quotient, quotient_type, ("gauge_work", "gauge_work_budgets")),
                                      (adapter, adapter_type, ("material_roll_generators", "state"))):
        methods.require(all(getattr(getattr(obj, name), "__func__", None) is getattr(implementation, name)
                            for name in names), "frozen material-roll methods/budgets cannot be overridden")


def verify_quotient(quotient, chart, mapping, q, gradient):
    verify_quotient_binding(quotient, chart, mapping)
    # Call the authenticated frozen implementations, including the complete
    # interior-node generators and their unchanged numerical work budgets.
    work = methods.numerical.CircularShaftQuotient.gauge_work(quotient, q, gradient)
    budgets = methods.numerical.CircularShaftQuotient.gauge_work_budgets(quotient, q, gradient)
    names = set(chart["shaft_first_local_twist_index_by_body"])
    methods.require(isinstance(work, dict) and isinstance(budgets, dict)
                    and len(names) == 70 and set(work) == set(budgets) == names,
                    "all70 own shaft material-roll work and budgets required")
    report = {}
    for name in names:
        value, budget = float(work[name]), float(budgets[name])
        methods.require(np.isfinite([value, budget]).all() and budget >= 0. and abs(value) <= budget,
                        "original potential material-roll work exceeds its own finite budget: "+name)
        report[name] = {"original_full_gradient_work_nmm_per_rad": value, "numerical_work_budget_nmm_per_rad": budget}
    return report


def diagnose_timber_contact_tangent(original_fields, original_q, field_payload, admission_payload, *,
                                     admission_receipt_sha256, quotient, options=None, directions=None):
    """Parent-only post-admission inspection of the supplied ORIGINAL H.

    H origin is the parent's responsibility. Reusing this wrapper never
    canonicalizes q, evaluates a response or calls the obsolete old admission
    wrapper. Positive/partial Ritz output remains a numerical diagnostic.
    """
    pins = source_pins()
    methods.require(isinstance(field_payload, bytes) and isinstance(admission_payload, bytes),
                    "immutable field and already-issued admission byte payloads required")
    methods.require(isinstance(admission_receipt_sha256, str)
                    and re.fullmatch("[0-9a-f]{64}", admission_receipt_sha256) is not None
                    and hashlib.sha256(admission_payload).hexdigest() == admission_receipt_sha256,
                    "explicit released timber-contact admission receipt SHA256 required")
    field = json.loads(field_payload)
    methods.require(field.get("schema") == "thin_bolted_finite_frame_response/v1"
                    and field.get("release") and not any(field["release"].values()), "current unreleased finite field required")
    supplied = json.loads(admission_payload)
    require_receipt(supplied, field, field_payload)
    current = admission.audit_timber_contact_state(field_payload)
    require_receipt(current, field, field_payload)
    methods.require(supplied["source_sha256"] == current["source_sha256"],
                    "issued admission source graph differs from current fixed admission")
    pins = admission.merge_pins(pins, field["source_sha256"], supplied["source_sha256"], original_fields["source_sha256"])
    verify_pins(pins)
    field_before = admission.original.canonical_sha(field)
    q, gradient = verify_original_response(original_fields, original_q, field)
    before_q, before_gradient = q.copy(), gradient.copy()
    response_before = admission.original.canonical_sha(response_snapshot(original_fields))
    hessian = original_fields["hessian_csr"]
    matrix_before = matrix_snapshot(hessian, len(q))
    chart = methods.quotient_indices(field["finite_kinematic_map"], q)
    roll_work = verify_quotient(quotient, chart, field["finite_kinematic_map"], q, gradient)
    methods.require(np.array_equal(q, before_q) and np.array_equal(gradient, before_gradient),
                    "material-roll checks changed supplied coordinates or full gradient")
    context = methods.contact_context(field)
    cells = [{"id": row["id"], "signed_extension_mm": float(row["signed_axial_extension_mm"])}
             for row in field["finite_interaction_actions"] if row["kind"] == "timber_face_contact"]
    methods.require(len(cells) == len({row["id"] for row in cells}) == 272
                    and current["timber_contact_geometry"]["contact_cell_count"] == 272,
                    "complete272 admitted timber-face branch margins required")
    context.update(timber_face_branch_margins=cells, timber_face_cell_count=len(cells))
    result = methods.diagnose_matrix(hessian, chart["retained_indices"], gradient=gradient,
                                     options=options, directions=directions)
    methods.require(np.array_equal(q, before_q) and np.array_equal(gradient, before_gradient)
                    and np.array_equal(methods.finite_vector(original_q, len(q)), before_q)
                    and admission.original.canonical_sha(response_snapshot(original_fields)) == response_before,
                    "original q/full gradient/response changed during tangent inspection")
    methods.require(original_fields["hessian_csr"] is hessian
                    and matrix_snapshot(hessian, len(q)) == matrix_before, "supplied original H changed during diagnostics")
    methods.require(admission.original.canonical_sha(field) == field_before,
                    "immutable parsed finite field changed during diagnostics")
    verify_quotient_binding(quotient, chart, field["finite_kinematic_map"])
    verify_pins(pins)
    source_pins()
    result.update(schema="thin_bolted_timber_contact_original_tangent/v1",
        **{key: field[key] for key in IDENTITY_KEYS}, field_sha256=hashlib.sha256(field_payload).hexdigest(),
        field_canonical_sha256=admission.original.canonical_sha(field), admission_receipt_sha256=admission_receipt_sha256,
        source_sha256=pins, original_input_matrix_snapshot=matrix_before,
        shaft_quotient={key: value for key, value in chart.items() if not isinstance(value, np.ndarray)},
        original_material_roll_work_by_shaft=roll_work, fixed_contact_context=context,
        frozen_pure_diagnostic_functions_reused=True, obsolete_admitted_tangent_wrapper_called=False,
        supplied_H_origin_is_parent_responsibility_not_independently_reassembled=True,
        candidate_response_K_tangent_or_native_execution_performed=False,
        stability_strength_complete_joint_or_release_accepted=False, release={key: False for key in field["release"]})
    return result
