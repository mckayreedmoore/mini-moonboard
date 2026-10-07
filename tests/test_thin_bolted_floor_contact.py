"""Small known answers and export mutations for corner-local floor sticking."""

from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_floor_contact as floor
from scripts import thin_bolted_frame_mechanics as frame


def fixture():
    points = [[x, y, 0.] for x in (-50., 50.) for y in (-50., 50.)]
    return floor.rigid_block_fixture(points)


def test_known_answer_method_coupons():
    assert len(floor.method_coupons()) == 8


def test_corner_allocation_preserves_translation_and_adds_actual_yaw_levers():
    contacts, tangents = fixture()
    stiffness = sum((row["stiffness"] * (row["B"].T @ row["B"]) for row in tangents), csr_matrix((6, 6))).toarray()
    assert len(contacts) == 4 and len(tangents) == 8
    np.testing.assert_allclose(stiffness[:2, :2], np.eye(2) * 100.)
    assert stiffness[5, 5] == pytest.approx(.5)
    assert all(row["first"] == row["physical_first"] == "coupon-block" for row in tangents)
    assert all(row["normal_contact_id"] == row["floor_support_id"] for row in tangents)


@pytest.mark.parametrize("mutation", ["point", "host", "normal", "duplicate"])
def test_invalid_corner_routing_is_rejected(mutation):
    contacts, tangents = fixture()
    if mutation == "point":
        tangents[0]["point_xyz_mm"] = [0., 0., 0.]
    elif mutation == "host":
        tangents[0]["physical_first"] = "invented-support-body"
    elif mutation == "normal":
        tangents[0]["normal_contact_id"] = contacts[1]["id"]
    else:
        tangents[-1] = tangents[0]
    with pytest.raises(ValueError):
        floor.compatible_contact_solve(csr_matrix((6, 6)), np.zeros(6), [], contacts, tangents)


def test_solver_does_not_mutate_physical_rows_or_contact_operators():
    contacts, tangents = fixture()
    old_contacts, old_tangents = deepcopy(contacts), deepcopy(tangents)
    response = floor.compatible_contact_solve(csr_matrix((6, 6)), np.array([10., 0., -100., 0., 0., 0.]),
                                             [], contacts, tangents)
    assert response["converged"]
    for before, after in zip([*old_contacts, *old_tangents], [*contacts, *tangents], strict=True):
        assert before["first"] == after["first"] == "coupon-block"
        assert before["point_xyz_mm"] == after["point_xyz_mm"]
        np.testing.assert_array_equal(before["B"].toarray(), after["B"].toarray())
    assert not response["virtual_support_ids_are_physical_bodies"]
    assert not response["near_threshold_diagnostic_is_a_normal_reaction_error_bound"]
    assert response["floor_support_distribution_changed_from_centroid"]
    assert response["original_force_tolerance_or_physical_laws_changed"]


def test_failed_pattern_cannot_recover_actions():
    contacts, tangents = fixture()
    with pytest.raises(ValueError, match="no recovered actions"):
        floor.compatible_actions(None, {}, {"converged": False}, [], contacts, tangents)


def test_recovery_rejects_mismatched_same_state_activation():
    contacts, tangents = fixture()
    response = floor.compatible_contact_solve(csr_matrix((6, 6)), np.array([0., 0., -100., 0., 0., 0.]),
                                             [], contacts, tangents)
    response["disabled_floor_support_ids"] = [contacts[0]["id"]]
    with pytest.raises(ValueError, match="activation differ"):
        floor.compatible_actions(None, {}, response, [], contacts, tangents)


def test_same_state_zero_normal_recovery_carries_no_floor_shear():
    contacts, tangents = fixture()
    zero = csr_matrix((6, 6))
    response = floor.compatible_contact_solve(zero, np.zeros(6), [], contacts, tangents)
    assert response["converged"]
    assembly = SimpleNamespace(geo={"bodies": [{"id": "coupon-block"}], "members": []}, members={})
    case = {"case_id": "zero", "accessory_placement": "coupon", "loads": [],
            "applied_force_xyz_n": [0., 0., 0.], "applied_moment_about_global_origin_xyz_nmm": [0., 0., 0.]}
    recovered = floor.compatible_actions(lambda *args: floor.rigid_block_recovery(assembly, *args),
                                        case, response, [], contacts, tangents)
    assert len(recovered["floor_actions"]) == 12
    assert all(row["first"] == "coupon-block" for row in recovered["floor_actions"])
    assert all(not row["interaction_enabled"] for row in recovered["floor_actions"])
    assert all(not np.any(row["force_on_first_xyz_n"]) for row in recovered["floor_actions"])
    assert recovered["equilibrium_verification"]["all_body_and_global_checks_pass"]
    assert "maximum_centroid_xy_penalty_motion_mm" not in recovered["floor_support_summary"]
    for normal in [row for row in recovered["floor_actions"] if row["kind"] == "floor_normal"]:
        for tangent in [row for row in recovered["floor_actions"] if row["kind"] == "floor_tangent"
                        and row["floor_support_id"] == normal["id"]]:
            assert tangent["reference_point_xyz_mm"] == normal["reference_point_xyz_mm"]
            assert tangent["current_point_xyz_mm"] == normal["current_point_xyz_mm"]
            assert tangent["action_wrench_uses_reference_point_first_order"]


def test_new_method_preserves_frozen_sources():
    pins = floor.source_pins()
    assert pins["scripts/thin_bolted_incremental_step.py"] == floor.INCREMENTAL_SHA
    assert pins["scripts/thin_bolted_frame_mechanics.py"] == "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448"
    assert pins[str(floor.CONTACT_PATH.relative_to(frame.ROOT))] == floor.CONTACT_SHA
