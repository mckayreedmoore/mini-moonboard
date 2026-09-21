"""Six-case PB02 component demands remain authenticated and developmental."""

import copy

import pytest

from scripts import simple_center_pb02_six_case_component_envelope as envelope


def test_envelope_reports_every_bolt_and_case_with_simultaneous_demands():
    result = envelope.screen()

    assert result["status"] == "authenticated_six_case_component_demand_envelope"
    assert result["authentication"]["accepted_case_count"] == 6
    assert result["case_order"] == [
        "a12-forward",
        "a12-rear",
        "a12-left",
        "k12-right",
        "k12-rear",
        "a1-rear",
    ]
    assert len(result["bolts"]) == 10
    for bolt in result["bolts"].values():
        assert list(bolt["demand_by_case"]) == result["case_order"]
        for demand in bolt["demand_by_case"].values():
            assert demand["axial_tension_n"] >= 0
            assert demand["lateral_n"] >= 0
            assert demand["combined_n"] == pytest.approx(
                (demand["axial_tension_n"] ** 2 + demand["lateral_n"] ** 2) ** 0.5
            )
            assert demand["simultaneous_from_same_solve"] is True

    governing = result["governing"]["bolt_combined_demand"]
    assert governing["name"] == "principal_block_principal/bolt_1"
    assert governing["case"] == "a12-rear"
    assert governing["combined_n"] == pytest.approx(196.3913426)
    axial = result["governing"]["bolt_axial_tension"]
    assert axial["name"] == "header_principal_block/bolt_1"
    assert axial["interface"] == "header_principal_block"
    assert axial["case"] == "a12-rear"
    assert axial["axial_tension_n"] == pytest.approx(75.57589)
    lateral = result["governing"]["bolt_lateral_demand"]
    assert lateral["name"] == "principal_block_principal/bolt_1"
    assert lateral["interface"] == "principal_block_principal"
    assert lateral["case"] == "a12-rear"
    assert lateral["lateral_n"] == pytest.approx(181.8491061)


def test_envelope_reports_interfaces_and_supported_conditional_ratios():
    result = envelope.screen()

    assert len(result["interfaces"]) == 7
    for interface in result["interfaces"].values():
        assert list(interface["demand_by_case"]) == result["case_order"]
        assert interface["resistance_ratio"] is None
        assert interface["resistance_qualified"] is False

    interface = result["governing"]["complete_interface_force_resultant"]
    assert interface["name"] == "principal_block_principal"
    assert interface["case"] == "a12-rear"
    assert interface["force_n"] == pytest.approx(195.7706110)
    moment = result["governing"]["complete_interface_moment_resultant"]
    assert moment["name"] == "header_principal_block"
    assert moment["case"] == "a12-rear"
    assert moment["moment_nmm"] == pytest.approx(5147.6998224)

    comparisons = result["conditional_comparisons"]
    assert comparisons["direct_shaft"]["applicable_bolt_count"] == 10
    assert comparisons["individual_wood_yield"]["applicable_bolt_count"] == 2
    assert comparisons["block_header_end_grain"]["applicable_bolt_count"] == 2
    assert comparisons["direct_shaft"]["governing"]["ratio"] < 1
    assert comparisons["individual_wood_yield"]["governing"]["ratio"] < 1
    assert comparisons["block_header_end_grain"]["governing"]["ratio"] < 1
    assert comparisons["all_supported_conditional_ratios_below_one"] is True
    assert comparisons["complete_joint_verdict"] is False


def test_envelope_advances_only_for_bounded_development():
    result = envelope.screen()

    assert result["disposition"]["decision"] == "ADVANCE"
    assert result["disposition"]["scope"] == "development_only"
    assert result["boundaries"]["factory_connectors_only"] is True
    assert result["boundaries"]["custom_steel_authorized"] is False
    assert result["boundaries"]["lap_joints_authorized"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert "reference-density" in " ".join(result["sensitivity_caveats"])
    assert "washer" in " ".join(result["sensitivity_caveats"]).lower()


def test_envelope_fails_closed_if_evidence_authentication_changes(monkeypatch):
    original = envelope.six_case_evidence.screen

    def changed():
        result = copy.deepcopy(original())
        result["qualified_for_design"] = True
        return result

    monkeypatch.setattr(envelope.six_case_evidence, "screen", changed)

    with pytest.raises(ValueError, match="six-case evidence boundary changed"):
        envelope.screen()


def test_envelope_rejects_changed_bolt_inventory(monkeypatch):
    original = envelope._load_reports

    def changed(authentication):
        reports = original(authentication)
        reports["a12-forward"]["physical_connection_forces"].pop("post_block/bolt_1")
        return reports

    monkeypatch.setattr(envelope, "_load_reports", changed)

    with pytest.raises(ValueError, match="ten-bolt inventory changed"):
        envelope.screen()
