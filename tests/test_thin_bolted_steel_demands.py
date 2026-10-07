"""Independent fixtures for fresh-state ownership and numerical validity gates."""

import copy
import hashlib
import json

import pytest

from scripts.thin_bolted_steel_demands import (
    small_washer_axial_references,
    validate_demand_state,
)


def state():
    identity = {"case_id": "fixture", "accessory_placement": "fixture-accessory",
                "parameters": {"clearance": 1.}, "geometry_cache_sha256": "fixture-geometry"}
    state_id = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True,
                                                      separators=(",", ":")).encode()).hexdigest()[:24]
    row = {"case_id": identity["case_id"], "accessory_placement": identity["accessory_placement"],
           "state_id": state_id, "point_xyz_mm": [0., 0., 0.], "force_on_receiver_xyz_n": [1., 2., 3.],
           "moment_on_receiver_at_point_xyz_nmm": [0., 0., 0.]}
    return {"schema": "thin_bolted_compatible_elastic_frame/v1", **identity, "state_id": state_id,
            "response": {"converged": True, "physical_residual_uses_unmodified_laws": True,
                         "gradient_inf_n": 1e-8, "generalized_residual_tolerance_n": 1e-5},
            "equilibrium_verification": {"all_bodies": 62, "force_tolerance_n": 1e-4,
                                         "moment_tolerance_nmm": .1, "all_body_and_global_checks_pass": True},
            "body_equilibrium_residuals": [{"body": str(i), "force_xyz_n": [0., 0., 0.],
                                            "moment_about_reference_xyz_nmm": [0., 0., 0.]} for i in range(62)],
            "global_equilibrium_residual_force_n": [0., 0., 0.],
            "global_equilibrium_residual_moment_nmm": [0., 0., 0.], "usable_conditional_actions": True,
            "attachment_actions": [{**row, "axis_id": str(i), "angle_id": str(i // 2),
                                    "flange": "beam" if i % 2 == 0 else "post"} for i in range(72)],
            "flange_contact_actions": [{**row, "id": "fixture-contact-" + str(i), "kind": "flange_contact",
                                        "angle_id": str(i // 8), "flange": "beam" if i % 8 < 4 else "post",
                                        "receiver": "fixture-receiver"} for i in range(288)]}


def test_complete_single_state_is_admissible_without_acceptance():
    result = validate_demand_state(state())
    assert result["attachment_count"] == 72
    assert result["flange_contact_count"] == 288
    assert "complete_joint_acceptance" not in result


@pytest.mark.parametrize("field,value", [("converged", False),
                                         ("physical_residual_uses_unmodified_laws", False),
                                         ("gradient_inf_n", 1.00001e-5), ("gradient_inf_n", float("nan"))])
def test_failed_or_regularized_field_is_not_consumed(field, value):
    demand = state()
    demand["response"][field] = value
    with pytest.raises(ValueError):
        validate_demand_state(demand)


def test_parameter_identity_change_is_rejected():
    demand = state()
    demand["parameters"]["clearance"] = 0.
    with pytest.raises(ValueError, match="declared parameters"):
        validate_demand_state(demand)


@pytest.mark.parametrize("table", ["attachment_actions", "flange_contact_actions"])
def test_action_from_other_state_is_rejected(table):
    demand = state()
    demand[table][0]["state_id"] = "other-state"
    with pytest.raises(ValueError, match="another parameter"):
        validate_demand_state(demand)


def test_missing_attachment_is_rejected():
    demand = state()
    demand["attachment_actions"].pop()
    with pytest.raises(ValueError, match="72-port"):
        validate_demand_state(demand)


def test_duplicate_attachment_is_rejected():
    demand = state()
    demand["attachment_actions"][1] = copy.deepcopy(demand["attachment_actions"][0])
    with pytest.raises(ValueError, match="duplicate attachment"):
        validate_demand_state(demand)


def test_duplicate_contact_is_rejected():
    demand = state()
    demand["flange_contact_actions"][1] = copy.deepcopy(demand["flange_contact_actions"][0])
    with pytest.raises(ValueError, match="duplicate or nonflange"):
        validate_demand_state(demand)


def test_nonfinite_action_is_rejected():
    demand = state()
    demand["attachment_actions"][0]["force_on_receiver_xyz_n"][1] = float("inf")
    with pytest.raises(ValueError, match="nonfinite"):
        validate_demand_state(demand)


def test_missing_contact_is_rejected_even_when_zero_force():
    demand = state()
    demand["flange_contact_actions"].pop()
    with pytest.raises(ValueError, match="288-corner"):
        validate_demand_state(demand)


def test_declared_bounded_residual_is_usable_only_with_physical_closure():
    demand = state()
    demand["response"]["gradient_inf_n"] = 9.64e-6
    assert validate_demand_state(demand)["physical_law_gradient_inf_n"] == 9.64e-6
    demand["body_equilibrium_residuals"][0]["force_xyz_n"] = [.0002, 0., 0.]
    with pytest.raises(ValueError, match="physical wrench closure failed"):
        validate_demand_state(demand)


@pytest.mark.parametrize("field,value", [("generalized_residual_tolerance_n", .0001),
                                         ("generalized_residual_tolerance_n", None)])
def test_requested_residual_tolerance_cannot_override_cap(field, value):
    demand = state()
    demand["response"][field] = value
    with pytest.raises(ValueError, match="generalized residual criterion"):
        validate_demand_state(demand)


@pytest.mark.parametrize("field,value", [("force_tolerance_n", .001), ("moment_tolerance_nmm", 1.)])
def test_requested_physical_tolerance_cannot_override_cap(field, value):
    demand = state()
    demand["equilibrium_verification"][field] = value
    with pytest.raises(ValueError, match="physical wrench closure criterion"):
        validate_demand_state(demand)


def test_body_census_cannot_omit_unloaded_body():
    demand = state()
    demand["body_equilibrium_residuals"].pop()
    with pytest.raises(ValueError, match="62 unique"):
        validate_demand_state(demand)


def test_global_moment_closure_is_independent_of_body_pass_boolean():
    demand = state()
    demand["global_equilibrium_residual_moment_nmm"] = [0., .101, 0.]
    with pytest.raises(ValueError, match="physical wrench closure failed"):
        validate_demand_state(demand)


def washer_fixture(force):
    methods = {"washer_reference_inputs": [{"axis_id": "one", "role": "nut_washer", "support_material": "wood",
               "small_washer_product": "fixture", "bearing_circle_sensitivity_profile_ids": ["a", "b", "c"],
               "nominal_wood_annulus_reference": {"wood_bearing_reference_lbf": 1.}}],
               "washer_bending_profiles": {key: {"assumed_circular_bearing_diameter_mm": diameter,
                    "unit_axial_two_face_bending": {"axial_n": 1., "required_fy_mpa_at_sampled_bending_first_yield": coefficient}}
                    for key, diameter, coefficient in (("a", 18., .2), ("b", 19., .3), ("c", 22., .4))}}
    layout = {"installed_axes": [{"id": "one", "attachments": [{"axis_xyz": [0., 0., 2.]}]}]}
    demand = {"state_id": "fixture-state", "attachment_actions": [{"axis_id": "one", "force_on_receiver_xyz_n": force}]}
    return methods, demand, layout


def test_washer_unit_response_reuse_preserves_signed_opening_and_same_end():
    result = small_washer_axial_references(*washer_fixture([3., 4., -5.]))[0]
    assert result["signed_force_on_receiver_along_flange_inward_axis_n"] == -5.
    assert result["opening_restraint_component_n"] == 5.
    assert result["closing_component_n"] == 0.
    assert [r["required_fy_mpa_opening_component_reference"] for r in
            result["reused_frozen_plate_sensitivities"]] == [1., 1.5, 2.]
    expected_n_per_lbf = .45359237 * 9.80665
    assert result["nominal_wood_full_annulus_opening_component_reference_index"] == pytest.approx(5. / expected_n_per_lbf)
    assert result["combined_axial_and_moment_washer_index"] is None
    assert result["unknown_own_end_moments_zero_filled"] is False


def test_closing_component_is_a_diagnostic_not_inferred_bolt_tension():
    result = small_washer_axial_references(*washer_fixture([3., 4., 5.]))[0]
    assert result["opening_restraint_component_n"] == 0.
    assert result["closing_component_n"] == 5.
    assert result["closing_shaft_force_capture_or_bilateral_spring_artifact_unresolved"] is True
    assert result["absolute_projection_inferred_as_physical_bolt_tension"] is False
    first = result["reused_frozen_plate_sensitivities"][0]
    assert first["required_fy_mpa_opening_component_reference"] == 0.
    assert first["required_fy_mpa_absolute_projection_diagnostic"] == 1.


def test_small_washer_reference_never_allocates_a_shared_shaft():
    methods, demand, layout = washer_fixture([0., 0., -5.])
    layout["installed_axes"][0]["attachments"].append({"axis_xyz": [0., 0., 2.]})
    with pytest.raises(ValueError, match="one authenticated physical-shaft"):
        small_washer_axial_references(methods, demand, layout)
