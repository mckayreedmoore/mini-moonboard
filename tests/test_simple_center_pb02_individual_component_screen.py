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
            "a5e24552a90e4d6e27a987e381665bcc489a9021b61769c77fbbd0c5948e3631"
        ),
        "model_identity": (
            "876f860e709ab8a0d5fc6d3e755367adeb51e97f6aa63f28f3be0541c4c73d1a"
        ),
        "diagnostic_scope_fingerprint": (
            "9c019a17ebf5b2600e67b4686d55363be6f6b109861ef6db71ef13718cf9d930"
        ),
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }
    upright = result["connections"]["principal_upright_block/bolt_1"]
    link = result["connections"]["upright_rear_block/bolt_1"]

    assert upright["demand"] == pytest.approx(
        {"axial_n": 0.945499999999988, "lateral_n": 49.32286943116782}
    )
    assert upright["load_to_grain_degrees"] == pytest.approx(
        {
            "base_principal_center_right": 82.17788393463115,
            "upright_side_cleat": 42.17788393463091,
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
        {"axial_n": 0.0, "lateral_n": 43.061860344578655}
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
            assert case["demand_ratio"] < 0.12

    assert result["rating_or_drilling_release"] is False
    assert "local_crossed_bore_splitting" in result["unqualified"]
    assert "other_five_load_cases" in result["unqualified"]
