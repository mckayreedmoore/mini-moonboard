"""Fresh-candidate admission controls without CAD or a response solve."""

import copy

import pytest

from scripts.eoere_v8_bracing_review import admit_field


@pytest.fixture
def admission():
    binding = {"path": "current-v8-field", "sha256": "1" * 64}
    geometry = {"path": "current-v8-geometry", "sha256": "2" * 64}
    material = {"path": "current-v8-material", "sha256": "3" * 64}
    field = {"trial_parent_geometry": geometry,
             "source_inputs": {"plywood_material": material, "scenario": {"climber_load_parameters": {
                 "input_weight": 250, "input_unit": "lb", "downward_multiplier": 2., "horizontal_force_n": 300.}}},
             "counts": {"physical_bodies": 148, "shaft": 96, "fitting": 24},
             "panel_screw_actions": [{}] * 66, "execution": {"historical_q_used": False},
             "native_FEA_performed": False, "response": {"converged": True}}
    replay = {"field": binding, "false_screw_and_floor_forces_rejected": True,
              "same_state_declared_fixed_floor_replayed": True, "all_credited_hosts_in_bearing": True,
              "equilibrium": {"gradient_inf_n": 1e-6, "physical_body_count": 148}}
    plywood = {"field": binding, "raw_operator_checks": [{}, {}]}
    return field, replay, plywood, binding, geometry, material


def test_current_admitted_response_passes_the_bracing_intake(admission):
    admit_field(*admission)


@pytest.mark.parametrize("mutation", [
    lambda f, r, p: f.update(trial_parent_geometry={"path": "v6", "sha256": "0" * 64}),
    lambda f, r, p: r.update(field={"path": "other-field", "sha256": "0" * 64}),
    lambda f, r, p: f["execution"].update(historical_q_used=True),
    lambda f, r, p: r["equilibrium"].update(gradient_inf_n=1e-4),
    lambda f, r, p: r.update(all_credited_hosts_in_bearing=False),
    lambda f, r, p: p.update(raw_operator_checks=[{}]),
    lambda f, r, p: f["source_inputs"]["scenario"]["climber_load_parameters"].update(downward_multiplier=3.),
])
def test_old_or_incomplete_inputs_cannot_supply_a_current_bracing_gain(admission, mutation):
    args = copy.deepcopy(admission)
    mutation(*args[:3])
    with pytest.raises(ValueError):
        admit_field(*args)
