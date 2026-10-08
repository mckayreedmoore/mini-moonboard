"""New complete-union/binding/own-body operator checks; no field solve."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("complete_timber_adapter", Path(__file__).with_name("adapter.py"))
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


@pytest.fixture(scope="module")
def inputs():
    data, _ = A.read_inputs()
    grain = A.grain_geometry(data[A.FRAME_GEOMETRY], data[A.ATLAS])
    return data, grain


@pytest.fixture(scope="module")
def prepared(inputs):
    _, grain = inputs
    assembly = A.geometry_only_coupon_assembly(grain)
    return assembly, A.prepare_complete_timber_faces(assembly)


def test_complete_operator_known_answers(prepared):
    assembly, component = prepared
    result = A.known_answers(assembly, component)
    assert result["represented_cell_count"] == 584
    assert result["all584_actions_including_zeros_and_fresh_basis_stamped"]
    assert not result["K_prepared_or_global_field_solved"]


def test_all30_own_proof_and_grain_angle_metadata(prepared):
    _, component = prepared
    rows = component["descriptors"]
    assert len(rows) == len({r["id"] for r in rows}) == 584
    assert len({r["source_descriptor"]["patch_id"] for r in rows}) == 30
    assert {r["source_descriptor"]["geometry_proof_path"] for r in rows} == {A.OLD, A.DIRECT, A.ATLAS}
    header_post = next(r for r in rows if r["first"] == "base_header" and r["second"] == "base_post_center_left")
    assert header_post["source_descriptor"]["host_nominal_grain"]["first"]["normal_to_nominal_grain_angle_deg"] == 90.
    assert header_post["source_descriptor"]["host_nominal_grain"]["second"]["normal_to_nominal_grain_angle_deg"] == 0.
    assert not any(component["metadata"]["candidate_flags"].values())


@pytest.mark.parametrize("forgery", ["old_six_only", "missing_cell", "duplicate_cell", "wrong_owner", "nonfinite", "unoccupied", "area"])
def test_source_union_rejects_forgery(inputs, forgery):
    source, grain = inputs
    data = copy.deepcopy(source)
    patch = data[A.ATLAS]["new_positive_patches"][0]
    if forgery == "old_six_only":
        data[A.ATLAS]["new_positive_patches"] = []
    elif forgery == "missing_cell":
        patch["cells"].pop()
    elif forgery == "duplicate_cell":
        patch["cells"][1]["id"] = patch["cells"][0]["id"]
    elif forgery == "wrong_owner":
        patch["second"] = patch["first"]
    elif forgery == "nonfinite":
        patch["cells"][0]["point_xyz_mm"][0] = float("nan")
    elif forgery == "unoccupied":
        patch["cells"][0]["both_inward_material_probes_occupied"] = False
    elif forgery == "area":
        patch["cells"][0]["area_mm2"] *= 2.
    with pytest.raises(ValueError):
        A.describe_complete_contacts(data, grain)


def test_source_pin_mismatch(inputs):
    with pytest.raises(ValueError, match="source changed"):
        A.verify_pins({A.ATLAS: "0" * 64})


def test_grain_frame_forgery(inputs):
    data, _ = inputs
    saved = copy.deepcopy(data[A.FRAME_GEOMETRY])
    saved["member_element_actions"][0]["basis_grain_u_v_xyz"][1] = [0., 1., 0.]
    with pytest.raises(ValueError, match="grain frame"):
        A.grain_geometry(saved, data[A.ATLAS])


def test_different_bedding_or_old_scenario_rejected(inputs):
    data, grain = inputs
    for kwargs in ({"bedding_n_mm3": 2.}, {"scenario_id": A.faces.DEFAULT_SCENARIO_ID}):
        with pytest.raises(ValueError, match="scenario required"):
            A.describe_complete_contacts(data, grain, **kwargs)


def test_writer_keeps_new_basis_and_rejects_missing_zero_row(prepared):
    assembly, component = prepared
    q = np.zeros(assembly.ndof)
    actions = A.contact_response(component, q)["contact_actions"]
    stamped = A.stamp_complete_recovered_actions({"contact_actions": actions}, component, q)
    assert stamped["linear_timber_face_method"] == A.BASIS
    assert stamped["linear_timber_face_method"] != A.linear.METHOD_BASIS
    with pytest.raises(ValueError, match="all distinct"):
        A.stamp_complete_recovered_actions({"contact_actions": actions[:-1]}, component, q)


def test_nonfinite_component_q_and_descriptor_forgery(prepared):
    assembly, component = prepared
    q = np.zeros(assembly.ndof)
    q[0] = np.inf
    with pytest.raises(ValueError, match="finite"):
        A.contact_response(component, q)
    forged = copy.deepcopy(component)
    forged["descriptors"][0]["lateral_stiffness_n_mm"] = 1.
    with pytest.raises(ValueError, match="unchanged complete"):
        A.contact_response(forged, np.zeros(assembly.ndof))


@pytest.mark.parametrize("forgery", ["stiffness", "B", "coordinate", "basis", "release"])
def test_runtime_operator_binding_rejects_mutation(prepared, forgery):
    assembly, component = prepared
    forged = copy.deepcopy(component)
    if forgery == "stiffness":
        forged["contacts"][0]["stiffness"] *= 2.
    elif forgery == "B":
        forged["contacts"][0]["B"].data[0] *= 2.
    elif forgery == "coordinate":
        forged["coordinate_map"]["members"][0]["reference_start_xyz_mm"][0] += 1.
    elif forgery == "basis":
        forged["metadata"]["method"] = A.linear.METHOD_BASIS
    elif forgery == "release":
        forged["metadata"]["candidate_flags"]["capacity_established"] = True
    with pytest.raises(ValueError, match="unchanged complete"):
        A.contact_response(forged, np.zeros(assembly.ndof))
