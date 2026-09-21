"""PB02 upright/link component screen stays authenticated and bounded."""

import pytest

from scripts.simple_center_pb02_individual_component_screen import screen


def test_current_a12_forward_upright_and_link_component_screen():
    result = screen()

    assert result["authentication"] == {
        "candidate": "pb02-kerf-right-native-development-only",
        "case": "a12-forward",
        "active_geometry_fingerprint": (
            "06f0cd1a1754d26fb2ff74cc2eb7da8eed80fbbea5cc84d7627ae8ff07d61387"
        ),
        "report_sha256": (
            "6e5fe950f796e86c17fc575899c4e5b3a3314166e1fc3fafc81c96e530f1c7df"
        ),
        "model_identity": (
            "c6981acec1a15913cd792189f5bb2d7081d0b2afe9a7509503e974d0aca94cc3"
        ),
        "diagnostic_scope_fingerprint": (
            "c90bfe845d12bfed4a2d4a4b657cb26f34ba0e6b95af43fb8800596a723020d3"
        ),
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }
    upright = result["connections"]["principal_upright_block/bolt_1"]
    link = result["connections"]["upright_rear_block/bolt_1"]

    assert upright["demand"] == pytest.approx(
        {"axial_n": 20.0775, "lateral_n": 32.49687528774047}
    )
    assert upright["load_to_grain_degrees"] == pytest.approx(
        {
            "base_principal_center_right": 38.4584581337,
            "upright_side_cleat": 78.4584581337,
        }
    )
    principal_edges = upright["placement"]["base_principal_center_right"][
        "transverse_edges"
    ]
    assert principal_edges["loaded"]["distance_mm"] == pytest.approx(129.685)
    assert principal_edges["loaded"]["minimum_mm"] == pytest.approx(25.4)
    assert principal_edges["unloaded"]["distance_mm"] == pytest.approx(10.015)
    assert principal_edges["unloaded"]["minimum_mm"] == pytest.approx(9.525)
    assert principal_edges["unloaded"]["reserve_mm"] == pytest.approx(0.49)
    assert principal_edges["ten_mm_edge_is_loaded"] is False

    assert link["demand"] == pytest.approx(
        {"axial_n": 0.0, "lateral_n": 18.494207934978693}
    )
    assert link["washer"]["demand_n"] == 0
    assert link["washer"]["qualified"] is False

    for connection in (upright, link):
        assert connection["fastener_group"] == {
            "fastener_count": 1,
            "group_factor": 1.0,
            "group_action_applicable": False,
        }
        for root in ("root_0p189_in", "root_0p180_in"):
            case = connection["root_sensitivities"][root]
            assert set(case["reference_values_lbf"]) == {
                "Im",
                "Is",
                "II",
                "IIIm",
                "IIIs",
                "IV",
            }
            assert case["adjusted_reference_n"] > connection["demand"]["lateral_n"]
            assert case["demand_ratio"] < 0.1

    assert result["rating_or_drilling_release"] is False
    assert "local_crossed_bore_splitting" in result["unqualified"]
    assert "other_five_load_cases" in result["unqualified"]
