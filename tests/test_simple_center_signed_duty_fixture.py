"""The PB02 signed fixture remains source-bound and physically one-sided."""

from scripts.simple_center_connected_kinematics import EDGES
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_signed_duty_fixture import screen


def test_five_authenticated_cases_need_contact_and_tension_paths():
    result = screen()

    assert result["source_fingerprint"] == ACTIVE_FINGERPRINT
    assert [row["case"] for row in result["cases"]] == [
        "a1-rear",
        "a12-left",
        "a12-rear",
        "k12-rear",
        "k12-right",
    ]
    for case in result["cases"]:
        assert max(map(abs, case["self_equilibrium"]["net_force_n"])) < 1e-10
        assert (
            max(
                map(
                    abs,
                    case["self_equilibrium"]["net_moment_about_model_origin_nmm"],
                )
            )
            < 1e-9
        )
        states = case["reaction_models"]
        assert states["signed_contact_and_tension"]["feasible"] is True
        assert states["signed_contact_and_tension"]["max_force_residual_n"] < 1e-8
        assert states["signed_contact_and_tension"]["max_moment_residual_nmm"] < 1e-6
        assert states["tension_only_no_contact"]["feasible"] is False
        assert states["contact_only_no_tension"]["feasible"] is False
        assert states["shear_only"]["feasible"] is False
        omission = case["single_edge_omission"]
        assert set(omission["contact_edge_removal_feasible"]) == set(EDGES)
        assert omission["required_contact_edges_in_this_point_model"] == [
            "post_block",
            "upright_rear_block",
        ]
        assert omission["required_tension_edges_in_this_point_model"] == [
            "block_header",
            "header_principal_block",
            "principal_block_principal",
            "rear_block_post",
        ]
        assert all(
            duty["source_interface_residual_passed"]
            for duty in case["simultaneous_replacement_duties"]
        )

    assert result["strength_or_fabrication_release"] is False
