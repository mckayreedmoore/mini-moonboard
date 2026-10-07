"""Own-face attribution and distinct-admission orchestration checks."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from scripts import thin_bolted_timber_contact_checks as contact


@pytest.fixture
def face_coupon():
    identity = {"state_id": "method-only", "case_id": "method-only", "accessory_placement": "method-only"}
    centers = [[0., 0., 0.], [100., 0., 0.]]
    mapping = {"ndof": 24, "panels": {}, "mechanical_bodies": {}}
    q = np.zeros(24)
    for index, (member, y) in enumerate((("first-wood", 10.), ("second-wood", 11.))):
        indices = np.arange(index * 12, index * 12 + 12).reshape(2, 6)
        q[indices[:, 1]] = y
        mapping["mechanical_bodies"][member] = {"kind": "timber", "node_reference_centers_xyz_mm": centers,
            "node_dof_indices": indices.tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
            "reference_start_xyz_mm": [0., 0., 0.], "reference_axis_xyz": [1., 0., 0.],
            "reference_stations_mm": [0., 100.]}
    face = {**identity, "id": "paired-face/quad0", "kind": "timber_face_contact",
        "first": "first-wood", "second": "second-wood",
        "reference_first_point_xyz_mm": [25., 0., 0.], "reference_second_point_xyz_mm": [25., 0., 0.],
        "point_on_first_xyz_mm": [25., 10., 0.], "point_on_second_xyz_mm": [25., 11., 0.],
        "force_on_first_xyz_n": [-100., 0., 20.], "force_on_second_xyz_n": [100., 0., -20.],
        "moment_on_first_at_current_point_xyz_nmm": [20., 0., 100.],
        "moment_on_second_at_current_point_xyz_nmm": [0., 0., 0.]}
    return {**identity, "finite_interaction_actions": [face], "finite_body_applied_loads": [],
            "finite_kinematic_map": mapping, "response": {"q": q.tolist()}}


def test_corrected_own_face_sides_enter_frozen_material_cut_collector_once(face_coupon):
    # A separately exported alias must never be appended by the wrapper.
    face_coupon["timber_face_contact_actions"] = copy.deepcopy(face_coupon["finite_interaction_actions"])
    result = contact.own_face_load_inventory(face_coupon)
    assert result["face_interaction_count"] == 1
    assert result["own_member_face_side_count"] == 2
    assert result["separate_face_alias_appended_or_old_force_used"] is False
    first, second = result["own_member_face_loads"]
    assert first["current_point_xyz_mm"] == [25., 10., 0.]
    assert second["current_point_xyz_mm"] == [25., 11., 0.]
    assert first["free_spatial_moment_xyz_nmm"] == [20., 0., 100.]
    assert second["free_spatial_moment_xyz_nmm"] == [0., 0., 0.]


def test_face_force_and_director_couple_change_each_own_complete_current_cut(face_coupon):
    methods = contact.methods
    own = methods.own_current_actions(face_coupon)
    cuts = []
    for member in ("first-wood", "second-wood"):
        frame = methods.current_cut_frame(face_coupon["finite_kinematic_map"], member,
            [50., 0., 0.], [1., 0., 0.], face_coupon["response"]["q"])
        cuts.append(methods.current_cut_wrench(own[member], [1., 0., 0.], 50., frame))
    assert cuts[0]["force_on_lower_material_portion_xyz_n"] == pytest.approx([100., 0., -20.])
    assert cuts[0]["moment_on_lower_material_portion_about_current_cut_xyz_nmm"] == pytest.approx([-20., -500., -100.])
    assert cuts[1]["force_on_lower_material_portion_xyz_n"] == pytest.approx([-100., 0., 20.])
    assert cuts[1]["moment_on_lower_material_portion_about_current_cut_xyz_nmm"] == pytest.approx([0., 500., 0.])
    assert cuts[0]["own_lower_material_action_ids"] == ["paired-face/quad0/first"]
    assert cuts[1]["own_lower_material_action_ids"] == ["paired-face/quad0/second"]
    # Complete current cut wrenches remain globally self-equilibrated after
    # transporting their distinct current cut datums to one reference point.
    total = sum((np.asarray(c["moment_on_lower_material_portion_about_current_cut_xyz_nmm"])
                 + np.cross(c["current_cut_point_xyz_mm"], c["force_on_lower_material_portion_xyz_n"]) for c in cuts), np.zeros(3))
    assert total == pytest.approx([0., 0., 0.])


@pytest.mark.parametrize("mutation", ["omitted", "duplicate", "state", "host"])
def test_missing_duplicate_or_misidentified_face_path_fails_closed(face_coupon, mutation):
    if mutation == "omitted":
        face_coupon["finite_interaction_actions"].clear()
    elif mutation == "duplicate":
        face_coupon["finite_interaction_actions"].append(copy.deepcopy(face_coupon["finite_interaction_actions"][0]))
    elif mutation == "state":
        face_coupon["finite_interaction_actions"][0]["state_id"] = "old-state"
    else:
        face_coupon["finite_kinematic_map"]["mechanical_bodies"]["first-wood"]["kind"] = "shaft"
    with pytest.raises(ValueError):
        contact.own_face_load_inventory(face_coupon)


@pytest.mark.parametrize("mutation", ["schema", "old_success", "bytes", "gate", "state"])
def test_distinct_contact_admission_cannot_relabel_an_old_receipt(mutation):
    identity = {"state_id": "S", "case_id": "C", "accessory_placement": "rear"}
    raw, gate = "a" * 64, "b" * 64
    receipt = {**identity, "schema": contact.GATE_SCHEMA, contact.GATE_SUCCESS: True,
        "field_sha256": raw, "source_sha256": {contact.GATE: gate}}
    contact.require_contact_receipt(receipt, identity, raw, gate)
    if mutation == "schema":
        receipt["schema"] = "thin_bolted_independent_finite_admission/v1"
    elif mutation == "old_success":
        del receipt[contact.GATE_SUCCESS]
        receipt["independent_finite_current_support_load_and_equilibrium_checks_pass"] = True
    elif mutation == "bytes":
        receipt["field_sha256"] = None
    elif mutation == "gate":
        receipt["source_sha256"][contact.GATE] = "c" * 64
    else:
        receipt["state_id"] = "old-state"
    with pytest.raises(ValueError, match="contact"):
        contact.require_contact_receipt(receipt, identity, raw, gate)


@pytest.mark.parametrize("wrong", [None, "UNISSUED", "A" * 64])
def test_reviewed_contact_gate_digest_is_mandatory(tmp_path, wrong):
    with pytest.raises(ValueError, match="admission digest"):
        contact.consume(tmp_path / "old-failed.json", "old-force-sha", admission_sha256=wrong)
    with pytest.raises(TypeError, match="admission_sha256"):
        contact.consume(tmp_path / "old-failed.json", "old-force-sha")
