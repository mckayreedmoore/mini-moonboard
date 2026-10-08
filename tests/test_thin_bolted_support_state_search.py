"""Small exact support-mask fixtures; no candidate assembly or frame solve."""

import copy
import hashlib
import json
from unittest.mock import patch

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as incremental
from scripts import thin_bolted_support_state_search as search


def cycling_fixture():
    # Compression coordinates nA/nB and centroid horizontal coordinates xA/xB.
    # The SPD material block is a declared synthetic coupling, not a floor clamp.
    K = np.diag([0., 0., 0., 0., 5000., 5000.])
    K[:4, :4] = 5000. * np.array([[38., 26., -9., 8.], [26., 29., -12., -2.],
                                [-9., -12., 27., 17.], [8., -2., 17., 19.]])
    applied = 5000. * np.array([-16., -11., 18., -11., 0., 0.])
    contacts, tangents = [], []
    for i, host in enumerate(("foot-A", "foot-B")):
        for corner in range(4):
            B = np.zeros((1, 6)); B[0, i] = 1.
            contacts.append({"id": host + f"/floor-{corner}", "kind": "floor_normal",
                             "first": host, "second": "floor", "B": csr_matrix(B), "stiffness": 25000.})
        for component, index in enumerate((i + 2, i + 4)):
            B = np.zeros((1, 6)); B[0, index] = 1.
            tangents.append({"id": host + f"/no-slip-{component}", "kind": "floor_tangent",
                             "first": host, "B": csr_matrix(B), "stiffness": 100000.})
    return csr_matrix(K), applied, [], contacts, tangents


def hand_branch(K, applied, mask, normal_active):
    # Both floor hosts have four coincident compression coordinates, total100k.
    diagonal = [100000. * normal_active[0], 100000. * normal_active[1],
                100000. * mask[0], 100000. * mask[1],
                100000. * mask[0], 100000. * mask[1]]
    return np.linalg.solve(K.toarray() + np.diag(diagonal), applied)


def test_cycle_escape_reuses_original_engine_and_finds_unvisited_hand_equilibrium():
    inputs = cycling_fixture()
    K, applied, _, contacts, tangents = inputs
    legacy = incremental.compatible_contact_solve(*inputs)
    assert not legacy["converged"]
    assert legacy["termination"] == "repeated floor-bearing pattern"
    events = []
    response = search.compatible_contact_solve(*inputs, mask_budget=4, branch_observer=events.append)
    assert response["converged"]
    diagnostic = response["support_state_search_v1"]
    assert [row["mask_id"] for row in diagnostic["tested_masks"]] == [
        "centroid-mask-11", "centroid-mask-00", "centroid-mask-10"]
    expected = hand_branch(K, applied, [True, False], [True, False])
    np.testing.assert_allclose(response["q"], expected, atol=2e-10)
    np.testing.assert_allclose(response["normal_contact_force_n"][:4], 25000. * expected[0], atol=1e-6)
    np.testing.assert_array_equal(response["normal_contact_force_n"][4:], np.zeros(4))
    assert response["nonbearing_no_slip_removed"] == ["foot-B"]
    assert response["gradient_inf_n"] < frame.GENERALIZED_RESIDUAL_TOLERANCE_N == 1e-5
    assert diagnostic["accepted_pattern_index"] == 2
    assert diagnostic["accepted_enabled_centroid_xy_hosts"] == ["foot-A"]
    assert diagnostic["final_mask_id"] == "centroid-mask-10"
    digest = hashlib.sha256(json.dumps(response["q"].tolist(), sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    assert diagnostic["final_q_canonical_sha256"] == digest
    assert not diagnostic["physical_laws_changed"]
    assert not diagnostic["old_field_initialization_used"]
    assert [event["phase"] for event in events] == ["branch_start", "branch_end"] * 3
    assert all(row["fixed_branch_converged"] for row in diagnostic["tested_masks"])
    assert all(row["disabled_xy_force_exactly_zero"] for row in diagnostic["tested_masks"])
    # The original caller rows survive unchanged, including shared B identities.
    assert all(row["kind"] == "floor_normal" for row in contacts)
    assert all(row["kind"] == "floor_tangent" for row in tangents)


@pytest.mark.parametrize("mask,normal_active", [([1, 1], [0, 0]), ([0, 0], [1, 1]),
                                                ([1, 0], [1, 0]), ([0, 1], [1, 1])])
def test_each_fixed_branch_preserves_requested_mask_and_full_original_fields(mask, normal_active):
    K, applied, groups, contacts, tangents = cycling_fixture()
    enabled = {host for host, on in zip(("foot-A", "foot-B"), mask, strict=True) if on}
    observed = []
    original_fields = incremental.ORIGINAL_FIELDS

    def observe(*args, **kwargs):
        observed.append(kwargs.get("tangent", False))
        return original_fields(*args, **kwargs)

    with patch.object(incremental, "ORIGINAL_FIELDS", observe):
        result = search._fixed_branch(K, applied, groups, contacts, tangents, enabled, 300, None)
        fresh = search._fresh_fields(K, applied, groups, contacts, tangents, enabled, result["q"])
    assert result["converged"]
    assert result["floor_pattern_iterations"] == 1
    assert result["nonbearing_no_slip_removed"] == []  # Internal engine does not choose the mask.
    np.testing.assert_allclose(result["q"], hand_branch(K, applied, mask, normal_active), atol=2e-10)
    np.testing.assert_allclose(fresh[0], 0., atol=1e-5)
    np.testing.assert_array_equal(result["normal_contact_force_n"], fresh[4])
    assert result["potential_energy_nmm"] == pytest.approx(fresh[1], abs=1e-8)
    assert any(observed)  # Existing original-fields instrumentation remains active.
    assert result["iteration_history"][-1]["active_floor_ports"] == 4 * sum(normal_active)


def test_budget_stop_exports_no_candidate_q_or_action_arrays():
    response = search.compatible_contact_solve(*cycling_fixture(), mask_budget=2)
    assert not response["converged"]
    assert response["termination"] == "support-mask search budget"
    assert "q" not in response and "normal_contact_force_n" not in response
    assert "connector_local_force_n" not in response
    assert response["diagnostic_last_q"] is not None
    assert not response["diagnostic_last_q_is_a_converged_or_accepted_force_field"]
    diagnostic = response["support_state_search_v1"]
    assert diagnostic["accepted_pattern_index"] is None
    assert diagnostic["final_q_canonical_sha256"] is None
    assert not diagnostic["complete_enumeration"] and not diagnostic["no_fixed_point_proven"]
    assert all(row["fixed_branch_converged"] and not row["self_consistent"]
               for row in diagnostic["tested_masks"])


def test_unresolved_fixed_branches_do_not_become_support_acceptance():
    response = search.compatible_contact_solve(*cycling_fixture(), max_iterations=1, mask_budget=4)
    assert not response["converged"]
    assert "q" not in response and "normal_contact_force_n" not in response
    diagnostic = response["support_state_search_v1"]
    assert diagnostic["all_masks_visited"] and not diagnostic["complete_enumeration"]
    assert not diagnostic["no_fixed_point_proven"]
    assert len({row["mask_id"] for row in diagnostic["tested_masks"]}) == 4
    assert not any(row["self_consistent"] for row in diagnostic["tested_masks"])


def test_resolved_two_mask_exhaustion_still_exports_no_accepted_force_field():
    K = csr_matrix(5000. * np.array([[1., .5, 0.], [.5, 1., 0.], [0., 0., 1.]]))
    applied = 5000. * np.array([-1., -4., 0.])
    contacts = [{"id": f"foot/floor-{i}", "kind": "floor_normal", "first": "foot", "second": "floor",
                 "B": csr_matrix([[1., 0., 0.]]), "stiffness": 25000.} for i in range(4)]
    tangents = [{"id": f"foot/no-slip-{i}", "kind": "floor_tangent", "first": "foot",
                 "B": csr_matrix([row]), "stiffness": 100000.}
                for i, row in enumerate(([0., 1., 0.], [0., 0., 1.]))]
    # Exact branch answers: on has n=-76/83<0; off has n=4/83>0.
    # Thus neither prescribed mask agrees with its own normal reaction.
    response = search.compatible_contact_solve(K, applied, [], contacts, tangents, mask_budget=2)
    assert not response["converged"] and response["termination"] == "support-mask search exhausted"
    assert "q" not in response and "normal_contact_force_n" not in response
    diagnostic = response["support_state_search_v1"]
    assert diagnostic["all_masks_visited"] and diagnostic["complete_enumeration"]
    assert all(row["fixed_branch_converged"] and not row["self_consistent"]
               for row in diagnostic["tested_masks"])
    assert not diagnostic["no_fixed_point_proven"]
    assert diagnostic["accepted_pattern_index"] is None
    np.testing.assert_allclose(response["diagnostic_last_q"], [4. / 83., -334. / 83., 0.], atol=2e-10)


def test_mutated_frozen_success_cannot_bypass_fresh_original_gradient():
    inputs = cycling_fixture()
    actual = search.FROZEN_INCREMENTAL_SOLVE

    def corrupt(*args, **kwargs):
        response = actual(*args, **kwargs)
        if response["converged"]:
            response["q"] = response["q"] + 1.
            response["gradient_inf_n"] = 0.
        return response

    with patch.object(search, "FROZEN_INCREMENTAL_SOLVE", corrupt):
        response = search.compatible_contact_solve(*inputs, mask_budget=4)
    assert not response["converged"]
    assert all(not row["fixed_branch_converged"] for row in response["support_state_search_v1"]["tested_masks"])
    assert "q" not in response


def test_search_rejects_external_q_and_detaches_observer_payload():
    inputs = cycling_fixture()
    with pytest.raises(ValueError, match="external q"):
        search.compatible_contact_solve(*inputs, mask_budget=4, warm_q=np.zeros(6))

    def observer(event):
        event["enabled_centroid_xy_hosts"].clear()
        event["phase"] = "corrupted-observer-copy"

    result = search.compatible_contact_solve(*inputs, mask_budget=4, branch_observer=observer)
    assert result["converged"]
    assert result["support_state_search_v1"]["accepted_enabled_centroid_xy_hosts"] == ["foot-A"]


def test_all_normal_rows_other_contact_kinds_and_original_inputs_survive_adapter():
    inputs = list(cycling_fixture())
    contacts = inputs[3]
    extra = {"id": "timber-pair", "kind": "timber_face_contact", "first": "foot-A", "second": "foot-B",
             "B": csr_matrix(np.zeros((1, 6))), "stiffness": 17.}
    contacts.append(extra)
    original = copy.deepcopy(contacts)
    seen = []
    actual = search.FROZEN_INCREMENTAL_SOLVE

    def capture(K, applied, groups, internal, tangents, **kwargs):
        seen.append(internal)
        assert len(internal) == len(contacts)
        for old, new in zip(contacts, internal, strict=True):
            assert new["B"] is old["B"]
            assert new["id"] == old["id"] and new["first"] == old["first"]
            assert new["second"] == old["second"] and new["stiffness"] == old["stiffness"]
        assert internal[-1] is extra
        return actual(K, applied, groups, internal, tangents, **kwargs)

    with patch.object(search, "FROZEN_INCREMENTAL_SOLVE", capture):
        result = search.compatible_contact_solve(*inputs, mask_budget=4)
    assert result["converged"] and seen
    assert len(result["normal_contact_force_n"]) == 9
    assert result["normal_contact_force_n"][-1] == 0.
    for old, new in zip(original, contacts, strict=True):
        assert old.keys() == new.keys() and old["kind"] == new["kind"]
        np.testing.assert_array_equal(old["B"].toarray(), new["B"].toarray())
