"""Saved-vector boundary tests only; no candidate field is consumed.

The admission API is explicitly mocked for synthetic complete-map payloads.
These payloads are not accepted by the production 132-body gate, and no seed
or candidate-admission report is issued by these fixtures.
"""

import copy
import hashlib
import json

import numpy as np
import pytest

from scripts import thin_bolted_finite_seed as seed


def coordinate_map():
    return {"ndof": 60,
        "mechanical_rotation_coordinates": "storage-basis rotation vector times1000; geodesic nodal interpolation",
        "mechanical_bodies": {"wood": {"kind": "timber", "node_reference_centers_xyz_mm": [[0., 0., 0.], [100., 0., 0.]],
            "node_dof_indices": np.arange(12).reshape(2, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
            "reference_start_xyz_mm": [0., 0., 0.], "reference_axis_xyz": [1., 0., 0.], "reference_stations_mm": [0., 100.]}},
        "panels": {"panel": {"kind": "panel", "global_dof_indices": list(range(12, 60)),
            "origin_xyz_mm": [0., 0., 0.], "axes_columns_xyz": np.eye(3).tolist(), "thickness_mm": 18.25625,
            "twist_scale": 1., "basis_width_mm": 100., "basis_height_mm": 100., "basis_order": 4,
            "basis_knots_normalized": [0., 0., 0., 0., 1., 1., 1., 1.],
            "coefficient_order": "u,v,outward_w;x-major tensor cubic spline",
            "mass_reference_xy_mm": [50., 50.], "mass_coefficient_row": [1./16.]*16}}}


def field_fixture():
    return {"schema": seed.FIELD_SCHEMA, "state_id": "synthetic-source-only", "case_id": "a12-rear",
        "accessory_placement": "retained-original-top-hold", "usable_conditional_actions": True,
        "response": {"converged": True, "q": (np.arange(60)/100.).tolist()}, "finite_kinematic_map": coordinate_map(),
        "body_identities": ["wood", "panel"], "source_sha256": {},
        "parameters": {"panel_intervals": 1, "beam_size_mm": 100., "shaft_max_segment_mm": 25.,
            "finite_kinematics_basis": "same declared coordinate kinematics", "finite_shaft_basis": "same shaft coordinate basis",
            "timber_face_contact_bedding_n_mm3": 1., "other_scenario": {"value": "source"}}}


def fixture(tmp_path, monkeypatch, *, field=None, mutate_receipt=None, after_admission=None):
    field = field_fixture() if field is None else field
    dependency = tmp_path/"existing-source.bin"; dependency.write_bytes(b"unchanged source")
    field["source_sha256"][str(dependency)] = hashlib.sha256(dependency.read_bytes()).hexdigest()
    payload = json.dumps(field, indent=2).encode()
    path = tmp_path/"synthetic-finite.json"; path.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    seen = []

    def audit(data):
        assert isinstance(data, bytes) and data == payload
        seen.append(data)
        parsed = json.loads(data)
        receipt = {"schema": seed.admission.SCHEMA, seed.admission.SUCCESS: True,
            **{key: parsed[key] for key in ("state_id", "case_id", "accessory_placement")},
            "field_sha256": hashlib.sha256(data).hexdigest(),
            "field_canonical_sha256": seed.admission.original.canonical_sha(parsed),
            "source_sha256": {**parsed["source_sha256"], seed.GATE: seed.GATE_SHA256}}
        if mutate_receipt:
            mutate_receipt(receipt)
        if after_admission:
            after_admission(path, dependency)
        return receipt

    monkeypatch.setattr(seed.admission, "audit_timber_contact_state", audit)
    target = {"target_map": copy.deepcopy(field.get("finite_kinematic_map", coordinate_map())),
              "target_ndof": 60, "target_body_identities": ["wood", "panel"],
              "target_parameters": copy.deepcopy(field["parameters"])}
    return path, expected, field, target, seen


def test_same_map_seed_uses_one_payload_and_returns_only_copied_initialization(tmp_path, monkeypatch):
    path, expected, field, target, seen = fixture(tmp_path, monkeypatch)
    q, provenance = seed.read_seed(path, expected, **target)
    np.testing.assert_array_equal(q, field["response"]["q"])
    assert seen == [path.read_bytes()]
    assert provenance["target_coordinate_map_sha256"] == seed.admission.original.canonical_sha(target["target_map"])
    assert provenance["source_state_id"] == field["state_id"] and "state_id" not in provenance
    assert provenance["initialization_only"]
    assert not provenance["target_admission_or_strength_transferred"]
    assert not provenance["source_forces_or_admission_receipt_returned"]
    assert not provenance["mesh_interpolation_projection_or_canonicalization_performed"]
    assert "finite_interaction_actions" not in provenance and "response" not in provenance
    q[0] = 999.
    provenance["target_parameters"]["other_scenario"]["value"] = "changed returned copy"
    q2, _ = seed.read_seed(path, expected, **target)
    assert q2[0] == field["response"]["q"][0]
    assert target["target_parameters"]["other_scenario"]["value"] == "source"


def test_source_case_and_noncoordinate_scenario_may_differ_without_identity_transfer(tmp_path, monkeypatch):
    field = field_fixture(); field["case_id"] = "k12-rear"
    path, expected, field, target, _ = fixture(tmp_path, monkeypatch, field=field)
    target["target_parameters"]["timber_face_contact_bedding_n_mm3"] = 2.
    _, provenance = seed.read_seed(path, expected, **target)
    assert provenance["source_case_id"] == "k12-rear"
    assert provenance["source_parameters"]["timber_face_contact_bedding_n_mm3"] == 1.
    assert provenance["target_parameters"]["timber_face_contact_bedding_n_mm3"] == 2.
    assert "case_id" not in provenance and "admission" not in provenance


@pytest.mark.parametrize("mutation", ["station", "center", "basis", "axis", "coordinate_indices", "rotation_label",
    "panel_axes", "panel_origin", "panel_knots", "panel_order", "panel_coefficient_order", "panel_mass",
    "panel_thickness", "body_order", "dimension"])
def test_same_size_changed_map_or_body_order_rejects(tmp_path, monkeypatch, mutation):
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch)
    mapping = target["target_map"]; wood = mapping["mechanical_bodies"]["wood"]; panel = mapping["panels"]["panel"]
    if mutation == "station":
        wood["reference_stations_mm"][1] += .001
    elif mutation == "center":
        wood["node_reference_centers_xyz_mm"][1][0] += .001
    elif mutation == "basis":
        wood["storage_basis_columns_xyz"][0][0] += 1e-10
    elif mutation == "axis":
        wood["reference_axis_xyz"][1] += 1e-10
    elif mutation == "coordinate_indices":
        wood["node_dof_indices"][0][0], wood["node_dof_indices"][0][1] = wood["node_dof_indices"][0][1], wood["node_dof_indices"][0][0]
    elif mutation == "rotation_label":
        mapping["mechanical_rotation_coordinates"] = "different rotation units"
    elif mutation == "panel_axes":
        panel["axes_columns_xyz"][1][1] += 1e-10
    elif mutation == "panel_origin":
        panel["origin_xyz_mm"][0] += .001
    elif mutation == "panel_knots":
        panel["basis_knots_normalized"][3] += 1e-10
    elif mutation == "panel_order":
        panel["basis_order"] += 1
    elif mutation == "panel_coefficient_order":
        panel["coefficient_order"] = "w,v,u"
    elif mutation == "panel_mass":
        panel["mass_coefficient_row"][0] += 1e-10
    elif mutation == "panel_thickness":
        panel["thickness_mm"] += 1e-10
    elif mutation == "body_order":
        target["target_body_identities"].reverse()
    else:
        target["target_ndof"] += 1; mapping["ndof"] += 1
    with pytest.raises(ValueError, match="complete prepared target map|body order"):
        seed.read_seed(path, expected, **target)


@pytest.mark.parametrize("parameter", seed.COORDINATE_PARAMETERS)
def test_coordinate_scenario_parameter_must_match(tmp_path, monkeypatch, parameter):
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch)
    target["target_parameters"][parameter] = "different"
    with pytest.raises(ValueError, match="coordinate parameter differs"):
        seed.read_seed(path, expected, **target)


@pytest.mark.parametrize("mutation", ["failed", "missing_map", "diagnostic_only", "old_schema"])
def test_failed_or_unsupported_export_cannot_fall_back_to_diagnostic_vector(tmp_path, monkeypatch, mutation):
    field = field_fixture()
    if mutation == "failed":
        field["response"]["converged"] = False; field["usable_conditional_actions"] = False
    elif mutation == "missing_map":
        field.pop("finite_kinematic_map")
    elif mutation == "diagnostic_only":
        field["response"]["diagnostic_last_q"] = field["response"].pop("q")
    else:
        field["schema"] = "thin_bolted_common_shaft_frame/v1"
    path, expected, _, target, seen = fixture(tmp_path, monkeypatch, field=field)
    with pytest.raises(ValueError):
        seed.read_seed(path, expected, **target)
    assert seen == []


@pytest.mark.parametrize("mutation", ["missing", "schema", "state", "case", "raw", "canonical", "gate_pin"])
def test_missing_or_wrong_current_admission_rejects(tmp_path, monkeypatch, mutation):
    def changed(receipt):
        if mutation == "missing":
            receipt.pop(seed.admission.SUCCESS)
        elif mutation == "schema":
            receipt["schema"] = "previous finite gate"
        elif mutation in ("state", "case"):
            receipt["state_id" if mutation == "state" else "case_id"] = "other"
        elif mutation in ("raw", "canonical"):
            receipt["field_sha256" if mutation == "raw" else "field_canonical_sha256"] = "0"*64
        else:
            receipt["source_sha256"][seed.GATE] = "0"*64
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch, mutate_receipt=changed)
    with pytest.raises(ValueError):
        seed.read_seed(path, expected, **target)


def test_changed_file_same_state_is_not_used_as_the_vector(tmp_path, monkeypatch):
    def changed(path, _dependency):
        field = json.loads(path.read_bytes()); field["response"]["q"][0] = 99.
        path.write_text(json.dumps(field))
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch, after_admission=changed)
    with pytest.raises(ValueError, match="file changed"):
        seed.read_seed(path, expected, **target)


def test_stale_source_dependency_rejects(tmp_path, monkeypatch):
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch,
        after_admission=lambda _path, dependency: dependency.write_bytes(b"changed source"))
    with pytest.raises(ValueError, match="source changed"):
        seed.read_seed(path, expected, **target)


def test_prepared_target_mutation_during_admission_rejects(tmp_path, monkeypatch):
    target = None
    def changed(_path, _dependency):
        target["target_map"]["mechanical_bodies"]["wood"]["reference_stations_mm"][1] += 1.
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch, after_admission=changed)
    with pytest.raises(ValueError, match="target map/scenario changed"):
        seed.read_seed(path, expected, **target)


def test_wrong_released_hash_rejects_before_admission(tmp_path, monkeypatch):
    path, _, _, target, seen = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="bytes differ"):
        seed.read_seed(path, "0"*64, **target)
    assert seen == []


@pytest.mark.parametrize("metadata", ["flange_node_map", "gravity_port"])
def test_complete_fitting_port_and_gravity_metadata_must_match(tmp_path, monkeypatch, metadata):
    field = field_fixture(); mapping = field["finite_kinematic_map"]
    mapping["ndof"] = 72
    mapping["mechanical_bodies"]["fitting"] = {"kind": "fitting", "node_reference_centers_xyz_mm": [[0., 0., 0.], [50., 50., 0.]],
        "node_dof_indices": np.arange(60, 72).reshape(2, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
        "flange_node_map": {"beam": 0, "post": 1}, "gravity_port": "mean of two exact flange rigid-arm ports"}
    field["response"]["q"] = (np.arange(72)/100.).tolist()
    field["body_identities"].append("fitting")
    path, expected, _, target, _ = fixture(tmp_path, monkeypatch, field=field)
    target["target_ndof"] = 72; target["target_body_identities"].append("fitting")
    target["target_map"]["mechanical_bodies"]["fitting"][metadata] = "other"
    with pytest.raises(ValueError, match="complete prepared target map"):
        seed.read_seed(path, expected, **target)


def test_missing_explicit_prepared_coordinate_parameters_rejects(tmp_path, monkeypatch):
    path, expected, _, target, seen = fixture(tmp_path, monkeypatch)
    target["target_parameters"].pop("shaft_max_segment_mm")
    with pytest.raises(ValueError, match="target coordinate-scenario"):
        seed.read_seed(path, expected, **target)
    assert seen == []


def test_loaded_gate_must_remain_the_fixed_reviewed_source(tmp_path, monkeypatch):
    path, expected, _, target, seen = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(seed.admission, "LOADED_PRODUCER_SHA256", "0"*64)
    with pytest.raises(ValueError, match="fixed reviewed"):
        seed.read_seed(path, expected, **target)
    assert seen == []
