"""PB02 upright/link component screen stays authenticated and bounded."""

import pytest

from scripts.simple_center_pb02_individual_component_screen import screen


def test_current_a12_forward_upright_and_link_component_screen():
    result = screen()

    assert result["authentication"] == {
        "candidate": "pb02-kerf-right-native-development-only",
        "case": "a12-forward",
        "active_geometry_fingerprint": (
            "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
        ),
        "report_sha256": (
            "4e8f9c193c225fe3d28002ab93ed3258d7560558ed089f27a49752adeea36023"
        ),
        "model_identity": (
            "6ff81b19cd60be0e2241af7350534de26b3fb68214de6d73fa80433221468b6f"
        ),
        "diagnostic_scope_fingerprint": (
            "ce354d1ed95456b07e3c04cfe857f064d3987106124425391736c361d46dd773"
        ),
        "numerically_accepted": True,
        "actual_joint_demands_qualified": False,
    }
    upright = result["connections"]["principal_upright_block/bolt_1"]
    link = result["connections"]["upright_rear_block/bolt_1"]

    assert upright["demand"] == pytest.approx(
        {"axial_n": 9.970499999999994, "lateral_n": 46.36259486348288}
    )
    assert upright["load_to_grain_degrees"] == pytest.approx(
        {
            "base_principal_center_right": 60.00281746030071,
            "upright_side_cleat": 20.002817460300474,
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
        {"axial_n": 0.0, "lateral_n": 39.986125545245265}
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
