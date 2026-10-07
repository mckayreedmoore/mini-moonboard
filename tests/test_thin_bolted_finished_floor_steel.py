"""Focused finished-support gate and changed head-scenario ownership fixtures."""

import pytest

from scripts import thin_bolted_finished_floor_steel as writer


def test_failed_support_gate_prevents_force_comparison(tmp_path, monkeypatch):
    from scripts import thin_bolted_finished_support_audit, thin_bolted_steel_demands

    monkeypatch.setattr(thin_bolted_finished_support_audit, "audit_finished_state", lambda _: {
        "independent_finished_support_and_equilibrium_checks_pass": False})
    calls = []
    monkeypatch.setattr(thin_bolted_steel_demands, "consume", lambda _: calls.append(True))
    source = tmp_path / "state.json"
    source.write_text("{}")
    with pytest.raises(ValueError, match="finished-support and equilibrium gate failed"):
        writer.consume_finished_state(source)
    assert calls == []


def head_fixture(closing=False, nut=False):
    role = "nut_washer" if nut else "head_washer"
    row = {"state_id": "fresh-state", "axis_id": "one", "role": role, "support_material": "steel",
           "signed_force_on_receiver_along_flange_inward_axis_n": 5. if closing else -5.,
           "opening_restraint_component_n": 0. if closing else 5.,
           "closing_component_n": 5. if closing else 0., "absolute_axial_projection_diagnostic_n": 5.}
    reference = {"ends": [{"axis_id": "one", "role": role, "profile_id": "head-profile"}],
                 "profiles": {"head-profile": {"unit_axial_two_face_bending": {
                     "axial_n": 1., "required_fy_mpa_at_sampled_bending_first_yield": .2}}}}
    return [row], reference


def test_changed_head_reference_keeps_fresh_opening_action_and_unknown_moment():
    result = writer.cap_head_same_state_references(*head_fixture())[0]
    assert result["state_id"] == "fresh-state"
    assert result["required_fy_mpa_opening_component_reference"] == 1.
    assert result["required_fy_mpa_absolute_projection_diagnostic"] == 1.
    assert result["assumed_circular_head_bearing_diameter_mm"] == 17.145
    assert result["combined_washer_index"] is None
    assert result["physical_bolt_tension_or_own_end_moments_verified"] is False


def test_closing_action_remains_diagnostic_and_head_circle_is_never_given_to_nut():
    result = writer.cap_head_same_state_references(*head_fixture(closing=True))[0]
    assert result["required_fy_mpa_opening_component_reference"] == 0.
    assert result["required_fy_mpa_absolute_projection_diagnostic"] == 1.
    with pytest.raises(ValueError, match="steel-supported head scenarios"):
        writer.cap_head_same_state_references(*head_fixture(nut=True))
