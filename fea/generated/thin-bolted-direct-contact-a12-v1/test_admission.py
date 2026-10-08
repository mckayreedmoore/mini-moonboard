"""Small source/map/law coupons; never prepare or solve the candidate."""

import copy
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix, diags

ROOT = Path(__file__).resolve().parents[3]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("fea/generated/thin-bolted-direct-contact-a12-v1/admission.py", "complete_contact_gate_coupon")
adapter = load("fea/generated/thin-bolted-complete-timber-contact-v1/adapter.py", "complete_contact_adapter_coupon")


@pytest.fixture(scope="module")
def geometry():
    return gate.read_complete_geometry()


@pytest.fixture(scope="module")
def prepared(geometry):
    assembly = adapter.geometry_only_coupon_assembly(geometry["grain_geometry"])
    return adapter.prepare_complete_timber_faces(assembly)


def face_field(prepared, q):
    recovered = {"contact_actions": []}
    for contact in prepared["contacts"]:
        compression = contact["stiffness"] * max(float((contact["B"] @ q)[0]), 0.)
        recovered["contact_actions"].append({k: contact[k] for k in ("id", "kind", "first", "second", "point_xyz_mm")}
                                          | {"compression_n": compression,
                                             "force_on_first_xyz_n": (compression * np.asarray(contact["direction_xyz"])).tolist()})
    field = adapter.stamp_complete_recovered_actions(recovered, prepared, q)
    field.update(state_id="method-coupon", case_id="a12-rear", accessory_placement="retained-original-top-hold",
                 parameters=copy.deepcopy(prepared["metadata"]["parameters"]),
                 release=copy.deepcopy(adapter.frame.RELEASE))
    for table in (field["contact_actions"], field["timber_face_contact_actions"]):
        for row in table:
            row.update({key: field[key] for key in ("state_id", "case_id", "accessory_placement")})
    return field


def test_independent_source_union_and_descriptor_identity(geometry):
    receipt = json.loads((ROOT / "fea/generated/thin-bolted-complete-timber-contact-v1/preparation.json").read_bytes())
    descriptors = gate.expected_complete_descriptors(geometry)
    assert len(descriptors) == 584 and geometry["pair_count"] == 30 and geometry["source_unordered_pair_count"] == 190
    assert gate.canonical_sha(descriptors) == receipt["metadata"]["signature_inputs"]["descriptor_sha256"]
    assert gate.canonical_sha(geometry["grain_geometry"]) == receipt["metadata"]["signature_inputs"]["grain_geometry_sha256"]
    assert {row["source_descriptor"]["geometry_proof_path"] for row in descriptors} == {gate.OLD, gate.DIRECT, gate.ATLAS}


@pytest.mark.parametrize("zero", [True, False])
def test_all_complete_face_laws_and_aliases_at_current_coupon_q(geometry, prepared, zero):
    q = np.zeros(240) if zero else np.random.default_rng(19).normal(0., 1e-4, 240)
    field = face_field(prepared, q)
    before = gate.canonical_sha(field)
    result = gate.verify_complete_face_actions(field, geometry, prepared["coordinate_map"], q,
                                               adapter_sha256=adapter.LOADED_SHA256)
    assert result["face_cell_count"] == 584 and result["retained_pair_count"] == 30
    assert gate.canonical_sha(field) == before
    if zero:
        assert result["face_potential_energy_nmm"] == 0.


@pytest.mark.parametrize("mutation", ["omit", "alias", "old_basis", "old_signature", "area", "normal", "owner",
                                      "grain", "proof", "stiffness", "closure", "force", "free_couple", "state"])
def test_complete_face_source_and_law_mutations_rejected(geometry, prepared, mutation):
    q = np.random.default_rng(4).normal(0., 1e-4, 240)
    field = face_field(prepared, q)
    row = field["contact_actions"][0]
    if mutation == "omit":
        field["contact_actions"].pop()
    elif mutation == "alias":
        field["timber_face_contact_actions"].pop()
    elif mutation == "old_basis":
        field["linear_timber_face_method"] = gate.linear.BASIS
    elif mutation == "old_signature":
        field["parameters"]["complete_timber_face_contact_physical_signature_sha256"] = "0" * 64
    else:
        if mutation == "area": row["cell_area_mm2"] += 1.
        elif mutation == "normal": row["direction_xyz"] = (-np.asarray(row["direction_xyz"])).tolist()
        elif mutation == "owner": row["first"], row["second"] = row["second"], row["first"]
        elif mutation == "grain": row["source_descriptor"]["host_nominal_grain"]["first"]["normal_to_nominal_grain_angle_deg"] = 0.
        elif mutation == "proof": row["source_descriptor"]["geometry_proof_sha256"] = "0" * 64
        elif mutation == "stiffness": row["penalty_stiffness_n_mm"] += 1.
        elif mutation == "closure": row["relative_closure_mm"] += .01
        elif mutation == "force": row["force_on_first_xyz_n"][0] += 1.
        elif mutation == "free_couple": row["moment_on_first_at_point_xyz_nmm"] = [1., 0., 0.]
        elif mutation == "state": row["state_id"] = "other"
        field["timber_face_contact_actions"][0] = copy.deepcopy(row)
    with pytest.raises(ValueError):
        gate.verify_complete_face_actions(field, geometry, prepared["coordinate_map"], q,
                                         adapter_sha256=adapter.LOADED_SHA256)


def put_csr(arrays, prefix, matrix):
    matrix = csr_matrix(matrix)
    for key, value in (("data", matrix.data), ("indices", matrix.indices), ("indptr", matrix.indptr),
                        ("shape", np.asarray(matrix.shape, dtype=np.int64))):
        arrays[prefix + "_" + key] = value.copy()
    return {"prefix": prefix, "shape": list(matrix.shape)}


def small_operators():
    arrays = {"applied": np.array([200432.5, 0., 101030.]), "ck": np.full(4, 25000.)}
    material = diags([10., 20., 30.]).tocsr()
    groups = [{"id": "radial-gap", "ka": 1000., "kl": 1000., "clearance": 1.5875, "tension_only": True,
               "B": put_csr(arrays, "group0", [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]])}]
    tangents = [{"id": "foot/no-slip-" + str(i), "first": "foot", "stiffness": 100000.,
                 "B": put_csr(arrays, "tangent" + str(i), [np.eye(3)[i]])} for i in range(2)]
    inputs = {"schema": "thin_bolted_complete_timber_original_operator_inputs/v1", "ndof": 3,
              "material_K": put_csr(arrays, "K", material), "applied": {"key": "applied"},
              "groups": groups, "contacts": [{"id": "floor" + str(i), "kind": "floor_normal", "first": "foot",
                       "stiffness": 25000.} for i in range(4)],
              "C": put_csr(arrays, "C", [[0., 0., 1.]] * 4), "ck": {"key": "ck"}, "tangents": tangents}
    return inputs, arrays, material, material + diags([100000., 100000., 0.])


def test_fresh_original_gradient_known_answer_and_no_input_mutation():
    inputs, arrays, _, observed = small_operators()
    field = {"response": {"q": [2., 0., 1.], "nonbearing_no_slip_removed": []}}
    before = gate.canonical_sha(inputs), gate.canonical_sha(field)
    replay = gate.replay_original_gradient(field, inputs, arrays, observed_linear_K=observed)
    assert replay["observed_branch"]["gradient_inf_n"] < 2e-10
    assert replay["same_state_support_mask_consistent"] is True
    assert replay["floor_normal_force_n_by_host"] == {"foot": 100000.}
    assert replay["diagnostic_only"] is False and replay["current_action_admission_or_capacity_established"] is False
    assert before == (gate.canonical_sha(inputs), gate.canonical_sha(field))


def test_source_csr_order_is_preserved_for_exact_floating_replay():
    # The frozen face point ports have unsorted CSR rows. Reordering would
    # alter their representation digest and can change dot-product rounding.
    row = csr_matrix((np.array([1e16, 1., -1e16]), np.array([0, 2, 1]), np.array([0, 3])), shape=(1, 3))
    arrays = {}
    descriptor = put_csr(arrays, "raw", row)
    before = {k: v.copy() for k, v in arrays.items()}
    retained = gate.read_csr(arrays, descriptor)
    assert not retained.has_sorted_indices
    assert np.array_equal(retained.indices, row.indices) and np.array_equal(retained.data, row.data)
    assert np.array_equal(retained @ np.ones(3), row @ np.ones(3))
    for key, value in arrays.items():
        assert np.array_equal(value, before[key])


def test_independent_point_ports_match_all584_raw_source_rows(geometry, prepared):
    mapping = prepared["coordinate_map"]
    for row in prepared["contacts"]:
        point, normal = row["point_xyz_mm"], row["direction_xyz"]
        expected = -gate._scalar_point_row(mapping, row["first"], point, normal)
        expected += gate._scalar_point_row(mapping, row["second"], point, normal)
        difference = row["B"] - expected
        assert not difference.nnz or abs(difference.data).max() < 1e-10


def test_failed_branch_remains_diagnostic_and_same_q_masks_are_separate():
    inputs, arrays, material, _ = small_operators()
    field = {"response": {"converged": False, "diagnostic_last_q": [2., 0., 1.]}}
    replay = gate.replay_original_gradient(field, inputs, arrays, observed_enabled_hosts=[], observed_linear_K=material)
    assert replay["diagnostic_only"] is True and "q" not in field["response"]
    assert replay["observed_enabled_centroid_xy_hosts"] == []
    assert replay["demanded_enabled_centroid_xy_hosts"] == ["foot"]
    assert replay["same_state_support_mask_consistent"] is False
    assert replay["observed_branch"]["gradient_inf_n"] == pytest.approx(200000.)
    assert replay["demanded_floor_law_branch"]["gradient_inf_n"] < 2e-10
    assert replay["observed_branch"]["gradient_canonical_sha256"] != replay["demanded_floor_law_branch"]["gradient_canonical_sha256"]


@pytest.mark.parametrize("mutation", ["q", "operator", "mask", "no_actual_K", "nan", "stiffness", "schema", "csr"])
def test_gradient_capture_mutations_rejected(mutation):
    inputs, arrays, material, _ = small_operators()
    field = {"response": {"diagnostic_last_q": [2., 0., 1.]}}
    kwargs = {"observed_enabled_hosts": [], "observed_linear_K": material}
    if mutation == "q": field["response"]["diagnostic_last_q"] = [2., 0.]
    elif mutation == "operator": kwargs["observed_linear_K"] = material + diags([1., 0., 0.])
    elif mutation == "mask": kwargs["observed_enabled_hosts"] = ["foreign"]
    elif mutation == "no_actual_K": kwargs.pop("observed_linear_K")
    elif mutation == "nan": arrays["applied"][0] = np.nan
    elif mutation == "stiffness": inputs["contacts"][0]["stiffness"] = -1.
    elif mutation == "schema": inputs["schema"] = "other"
    elif mutation == "csr": arrays["K_indptr"][-1] += 1
    with pytest.raises(ValueError):
        gate.replay_original_gradient(field, inputs, arrays, **kwargs)


def test_failed_full_field_is_rejected_without_original_operator_or_body_execution(monkeypatch):
    called = []
    monkeypatch.setattr(gate, "verify_execution", lambda *a, **k: called.append("execution"))
    monkeypatch.setattr(gate.linear.common_export, "audit_common_shaft_state", lambda *a: called.append("body"))
    field = {"schema": "thin_bolted_common_shaft_frame/v1", "case_id": "a12-rear",
        "candidate": "compact-floor-flush-thin-bolted-development",
        "layout_report_sha256": gate.original.arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"],
        "geometry_cache_sha256": gate.GEOMETRY_PINS[gate.CACHE],
        "accessory_placement": "retained-original-top-hold", "release": copy.deepcopy(adapter.frame.RELEASE),
        "complete_contact_admission_pending": True, "complete_joint_acceptance": False,
        "complete_joint_capacity_established": False, "compatible_numerical_mvp_complete": False,
        "response": {"converged": False, "diagnostic_last_q": [1.]}}
    with pytest.raises(ValueError, match="failed or unaccepted"):
        gate.audit_complete_timber_state(json.dumps(field).encode(), driver_sha256="0" * 64,
                                        method_receipt_path="unissued", method_receipt_sha256="0" * 64)
    assert called == []


@pytest.fixture
def cheap_receipt(monkeypatch):
    with tempfile.TemporaryDirectory(prefix=".receipt-coupon-", dir=gate.PACKET) as temporary:
        packet = Path(temporary)
        monkeypatch.setattr(gate, "PACKET", packet)
        refs = []
        pins = {gate.OWN: gate.LOADED_PRODUCER_SHA256}
        for i in range(4):
            path = packet / f"record{i}.json"
            path.write_text('{"method_coupon":true}\n')
            ref = {"path": str(path.relative_to(gate.ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            refs.append(ref)
            pins[ref["path"]] = ref["sha256"]
        # This isolates the exact-byte receipt seam. Actual production source
        # checks are exercised separately; this is never a full field pass.
        monkeypatch.setattr(gate, "source_pins", lambda extra=None: {**pins, **(extra or {})})
        q, gradient = [2., 0., 1.], [0., 0., 0.]
        replay = {"q_kind": "q", "diagnostic_only": False, "final_q_canonical_sha256": gate.canonical_sha(q),
            "same_state_support_mask_consistent": True, "observed_branch": {"signed_gradient_n": gradient,
                "gradient_canonical_sha256": gate.canonical_sha(gradient), "gradient_inf_n": 0.},
            "operator_inputs": refs[0], "operator_array_bundle": refs[1], "original_closed_branch_capture": refs[2]}
        capture = {"array_bundle": refs[3]}
        field = {"schema": "thin_bolted_common_shaft_frame/v1", "linear_timber_face_method": gate.BASIS,
            "candidate": "compact-floor-flush-thin-bolted-development",
            "layout_report_sha256": gate.original.arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"],
            "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold",
            "parameters": {"complete_physics": True}, "geometry_cache_sha256": gate.GEOMETRY_PINS[gate.CACHE],
            "counts": {"dofs": 3}, "response": {"converged": True, "q": q, "gradient_inf_n": 0.,
                "original_gradient_replay_v1": replay, "original_closed_branch_capture_v1": capture},
            "usable_conditional_actions": True, "release": copy.deepcopy(adapter.frame.RELEASE), "source_sha256": pins}
        field["state_id"] = "thin-v4-" + gate.canonical_sha({k: field[k] for k in
                     ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")})[:24]
        payload = json.dumps(field, indent=2).encode()
        receipt = {"schema": gate.SCHEMA, gate.SUCCESS: True,
            **{k: field[k] for k in gate.linear.IDENTITIES}, "field_sha256": hashlib.sha256(payload).hexdigest(),
            "field_canonical_sha256": gate.canonical_sha(field), "source_sha256": pins,
            "original_gradient_checks": gate._gradient_record_summary(field),
            "support_search_checks": {"final_q_canonical_sha256": gate.canonical_sha(q)}, "release": field["release"]}
        yield payload, field, receipt, packet


def test_exact_receipt_bridge_does_not_replay_or_mutate(cheap_receipt, monkeypatch):
    payload, expected, receipt, _ = cheap_receipt
    monkeypatch.setattr(gate, "replay_original_gradient", lambda *a, **k: pytest.fail("no repeated operator replay"))
    before = gate.canonical_sha(receipt)
    field, pins = gate.require_admitted_payload(payload, receipt, admission_sha256=gate.LOADED_PRODUCER_SHA256)
    assert field == expected and pins[gate.OWN] == gate.LOADED_PRODUCER_SHA256
    assert gate.canonical_sha(receipt) == before


@pytest.mark.parametrize("mutation", ["raw", "schema", "success", "state", "q", "gate", "operator", "release", "gradient"])
def test_exact_receipt_bridge_mutations_rejected(cheap_receipt, mutation):
    payload, _field, receipt, _ = cheap_receipt
    if mutation == "raw": payload += b"\n"
    elif mutation == "schema": receipt["schema"] = gate.linear.SCHEMA
    elif mutation == "success": receipt[gate.SUCCESS] = False
    elif mutation == "state": receipt["state_id"] = "other"
    elif mutation == "q": receipt["support_search_checks"]["final_q_canonical_sha256"] = "0" * 64
    elif mutation == "gate": receipt["source_sha256"][gate.OWN] = "0" * 64
    elif mutation == "operator": (gate.ROOT / receipt["original_gradient_checks"]["operator_inputs"]["path"]).write_text("changed")
    elif mutation == "release": receipt["release"] = {"released": True}
    elif mutation == "gradient": receipt["original_gradient_checks"]["gradient_inf_n"] = 2e-5
    with pytest.raises(ValueError):
        gate.require_admitted_payload(payload, receipt, admission_sha256=gate.LOADED_PRODUCER_SHA256)
