"""Separate changed numerical hardware from frozen joint geometry/provenance."""

import copy

import pytest

from scripts.eoere_v9_analysis import (
    STACK_AXES,
    compare_prepared_inputs,
    verify_recipes,
)


def prepared():
    shaft = {
        "axis_id": "known",
        "body": "shaft/known",
        "point": [0.0, 0.0, 0.0],
        "basis": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "diameter_mm": 9.525,
        "bore_diameter_mm": 10.31875,
        "shaft_interval_mm": [-2.6416, 200.5584],
        "surfaces": [{"host": "wood", "kind": "wood", "interval_mm": [0.0, 127.0]}],
        "ends": [
            {
                "end": "nut",
                "host": "wood",
                "support_s_mm": 133.35,
                "pressure_face_s_mm": 174.0916,
                "own_spacer_length_mm": 38.1,
            }
        ],
        "metal_roles": [
            {
                "id": "known/nut",
                "kind": "nut",
                "mass_kg": 0.01,
                "center_of_mass_xyz_mm": [178.3715, 0.0, 0.0],
            }
        ],
    }
    return {
        "geometry": {"path": "before/geometry.json", "sha256": "before"},
        "source_sha256": {},
        "shafts": [shaft],
        "physical_owner_gravity_rows": [],
        "timber_rows": [],
        "fitting_poses": [],
        "fitting_port_bindings": [],
        "all_factory_holes": [],
        "direct_contacts": [],
        "flange_domains": [],
        "hillman_rows": [],
        "floor_footprints": {},
        "parameters": {"screw_stiffness_n_mm": 1000.0},
        "scenario": {
            "common_shaft_parameters": {"steel_E_mpa": 200000.0},
            "perfect_bond_analysis": {"physical_parent": {"path": "old"}},
        },
        "panel_ids": ["panel"],
        "current_panel_machining_descriptors": {"features": []},
        "cases": [
            {
                "case_id": "known",
                "loads": [
                    {
                        "id": "gravity",
                        "body": "shaft/known",
                        "force_xyz_n": [0.0, 0.0, -0.1],
                        "point_xyz_mm": [100.0, 0.0, 0.0],
                    }
                ],
            }
        ],
    }


MATERIAL = {"properties": {"EA_N": 100.0, "GJ_Nmm2": 500.0}, "source_sha256": {}}


def compare(first, last, old_material=MATERIAL, new_material=MATERIAL):
    return compare_prepared_inputs(first, last, old_material, new_material)


def test_source_path_changes_do_not_imply_numerical_change_or_force_equivalence():
    before = prepared()
    after = copy.deepcopy(before)
    after["geometry"] = {"path": "after/geometry.json", "sha256": "after"}
    after["source_sha256"] = {"new/input": "new"}
    after["scenario"]["perfect_bond_analysis"]["physical_parent"]["path"] = "new"
    material = {**MATERIAL, "source_sha256": {"new/material": "new"}}
    report = compare(before, after, MATERIAL, material)
    assert report["numerical_or_physical_descriptors_changed"] is False
    assert report["operator_or_response_equivalence_established"] is False
    assert report["historical_force_results_transferred"] is False


def test_shorter_unloaded_tip_changes_shaft_domain_without_moving_joint_surfaces():
    before = prepared()
    after = copy.deepcopy(before)
    after["shafts"][0]["shaft_interval_mm"][1] -= 12.7
    report = compare(before, after)
    assert report["families"]["shaft_domains_and_sections"]["changed"] is True
    assert report["families"]["bearing_surfaces"]["changed"] is False
    assert report["families"]["end_support_locations"]["changed"] is False


def test_shorter_spacer_keeps_support_seat_but_moves_inherited_capture_plane():
    before = prepared()
    after = copy.deepcopy(before)
    after["shafts"][0]["ends"][0]["own_spacer_length_mm"] = 25.4
    after["shafts"][0]["ends"][0]["pressure_face_s_mm"] -= 12.7
    report = compare(before, after)
    assert report["families"]["end_capture_pressure_locations"]["changed"] is True
    assert report["families"]["end_support_locations"]["changed"] is False


def test_changed_metal_gravity_and_its_load_arm_are_both_visible():
    before = prepared()
    after = copy.deepcopy(before)
    after["shafts"][0]["metal_roles"][0]["center_of_mass_xyz_mm"][0] -= 12.7
    after["cases"][0]["loads"][0]["point_xyz_mm"][0] -= 12.7
    report = compare(before, after)
    assert report["families"]["metal_gravity_roles"]["changed"] is True
    assert report["families"]["case_loads"]["changed"] is True
    assert report["families"]["timber_response_geometry"]["changed"] is False


def test_bound_material_operator_change_is_not_hidden_by_a_new_material_path():
    before = prepared()
    material = copy.deepcopy(MATERIAL)
    material["properties"]["GJ_Nmm2"] *= 2
    report = compare(before, copy.deepcopy(before), MATERIAL, material)
    assert report["families"]["plywood_material_operator"]["changed"] is True


def test_new_constitutive_parameter_is_not_dropped_as_provenance():
    before = prepared()
    after = copy.deepcopy(before)
    after["scenario"]["common_shaft_parameters"]["steel_E_mpa"] *= 0.9
    assert (
        compare(before, after)["families"]["constitutive_scenario"]["changed"] is True
    )


def test_nonfinite_input_cannot_receive_an_equivalence_record():
    data = prepared()
    data["shafts"][0]["diameter_mm"] = float("nan")
    with pytest.raises(ValueError):
        compare(data, copy.deepcopy(data))


def recipe_fixture():
    identities = sorted(STACK_AXES) + [f"retained_{i}" for i in range(88)]
    before = {
        "axes": [],
        "selected_stack_overrides": [],
        "profiles": {"wood": "retained"},
        "fitting_poses": [],
        "screw_axes": [],
        "inward_angle_study": {},
        "inward_bolt_revision": {},
    }
    for identity in identities:
        before["axes"].append(
            {
                "id": identity,
                "point_xyz_mm": [0.0, 0.0, 0.0],
                "direction_xyz": [1.0, 0.0, 0.0],
                "grip_mm": 127.0,
                "before_plate_mm": 0.0,
                "after_plate_mm": 6.35,
                "receivers": ["wood"],
                "attachments": [],
                "head_faces": "exterior",
                "nut_faces": "interior",
                "installation_orientation_revision": "v7",
                "nominal_under_head_length_mm": 203.2,
                "nut_side_spacer_mm": 38.1,
            }
        )
        before["selected_stack_overrides"].append(
            {"axis_id": identity, "minimum_body_mm": 163.5125, "spacer_piece_count": 3}
        )
    after = copy.deepcopy(before)
    updates = []
    for index, identity in enumerate(identities[:8]):
        after["axes"][index].update(
            nominal_under_head_length_mm=190.5, nut_side_spacer_mm=25.4
        )
        after["selected_stack_overrides"][index].update(
            minimum_body_mm=144.272, spacer_piece_count=1
        )
        updates.append(
            {
                "axis_id": identity,
                "before_axis": copy.deepcopy(before["axes"][index]),
                "before_selection": copy.deepcopy(
                    before["selected_stack_overrides"][index]
                ),
                "after_axis": copy.deepcopy(after["axes"][index]),
                "after_selection": copy.deepcopy(
                    after["selected_stack_overrides"][index]
                ),
            }
        )
    return before, after, {"axis_updates": updates}


def test_exact_eight_recipes_keep_all_other_stacks_and_wood():
    before, after, parameters = recipe_fixture()
    verify_recipes(after, before, parameters)


@pytest.mark.parametrize(
    "change", ["extra_stack", "recipe", "wood", "hidden_axis_move"]
)
def test_recipe_guard_rejects_unrecorded_cumulative_changes(change):
    before, after, parameters = recipe_fixture()
    if change == "extra_stack":
        after["axes"][-1]["nominal_under_head_length_mm"] -= 12.7
    elif change == "recipe":
        after["selected_stack_overrides"][0]["minimum_body_mm"] = 163.5125
    elif change == "wood":
        after["profiles"]["wood"] = "changed"
    else:
        after["axes"][0]["point_xyz_mm"][1] = 6.0
        parameters["axis_updates"][0]["after_axis"]["point_xyz_mm"][1] = 6.0
    with pytest.raises(ValueError):
        verify_recipes(after, before, parameters)
