"""RV-2 keeps one authenticated scenario and an explicitly bounded verdict."""

import copy

import pytest

from scripts import simple_pb01_provisional_decision as decision
from scripts.simple_pb01_hybrid_local_actions import extract


def test_rv2_preserves_signed_serial_actions_and_conditional_checks():
    result = decision.decide()
    source = extract()
    assert result["case"] == "a12-left"
    assert result["archive_sha256"] == source["archive_sha256"]
    assert result["proxy_station_count"] == 23
    assert result["decision"] == "revise"
    assert result["decision_scope"] == "development_only"
    assert result["joint_utilization"] is None
    assert result["design_pass"] is None
    assert set(result["interfaces"]) == {"upright", "rail"}
    for family, face in result["interfaces"].items():
        original = source["interfaces"][family]
        assert face["resultant_on_host"] == original["resultant_on_host"]
        assert face["resultant_on_cleat"] == original["resultant_on_cleat"]
        assert face["bolts"] == original["bolts"]
        assert face["contacts"] == original["contacts"]
        assert len(face["bolts"]) == 2
        assert len(face["contacts"]) == 4
        assert sum(row["active"] for row in face["contacts"]) == 2
        assert face["checks"]["group_action"]["ratio"] is None
    bolts = result["bolt_checks"]
    assert bolts["pb01_upright_u2"]["lateral_yield"]["0.180"][
        "modeled_direction_ratio"
    ] == pytest.approx(0.06433648)
    assert bolts["pb01_rail_r1"]["positive_axial_wood_annulus_ratio"] == pytest.approx(
        0.03254374
    )
    assert bolts["pb01_rail_r2"]["positive_axial_wood_annulus_ratio"] is None
    assert bolts["pb01_rail_r1"]["axial_steel_nut_ratio"] is None
    assert result["member_checks"]["rail_host_row_toward_butt"][
        "reference_lbf"
    ] == pytest.approx(850.3937)
    assert result["member_checks"]["rail_host_row_toward_butt"]["utilization"] is None
    assert result["cleat_check"]["maxima"]["torsion_abs_nmm"]["value"] > 0
    assert result["cleat_check"]["utilization"] is None
    assert result["rail_stack"]["receiving_accepted"] is False


def test_rv2_fails_closed_if_case_or_interface_identity_changes(monkeypatch):
    changed = copy.deepcopy(extract())
    changed["case"] = "a12-rear"
    monkeypatch.setattr(decision, "extract", lambda: changed)
    with pytest.raises(ValueError, match="identity"):
        decision.decide()
    changed["case"] = "a12-left"
    changed["interfaces"]["rail"]["host"] = "other"
    with pytest.raises(ValueError, match="identity"):
        decision.decide()
