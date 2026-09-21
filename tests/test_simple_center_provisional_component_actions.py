"""PB02 provisional actions preserve physical signs, identity, and scope."""

import itertools

import numpy as np
import pytest

from scripts.simple_center_connected_kinematics import EDGES
from scripts.simple_center_provisional_component_actions import (
    FORCE_TOLERANCE_N,
    MOMENT_TOLERANCE_NMM,
    PATHS,
    screen,
)
from scripts.simple_center_stiffness_sensitivity import SCENARIOS

CASES = ("a1-rear", "a12-left", "a12-rear", "k12-rear", "k12-right")


@pytest.fixture(scope="module")
def report():
    return screen()


def test_report_has_exactly_fifty_unique_case_scenario_records(report):
    expected = set(itertools.product(CASES, (row[0] for row in SCENARIOS)))
    identities = [(record["case"], record["scenario"]) for record in report["records"]]

    assert report["record_count"] == 50
    assert len(identities) == len(set(identities)) == 50
    assert set(identities) == expected


def test_every_record_has_complete_edges_and_exact_path_groups(report):
    expected_edges = set(EDGES)
    expected_paths = {name: list(edge_names) for name, edge_names in PATHS.items()}

    assert expected_paths["header_to_post"] == ["post_block", "block_header"]
    assert expected_paths["header_to_principal"] == [
        "header_principal_block",
        "principal_block_principal",
    ]
    for record in report["records"]:
        assert set(record["edges"]) == expected_edges
        assert set(record["path_groups"]) == set(expected_paths)
        for name, expected_order in expected_paths.items():
            group = record["path_groups"][name]
            assert group["ordered_edges"] == expected_order
            assert list(group["interfaces"]) == expected_order
            assert group["wrenches_summed_as_capacity"] is False
            for edge in expected_order:
                assert group["interfaces"][edge] == record["edges"][edge]


def test_bolt_face_and_interface_actions_are_equal_and_opposite(report):
    for record in report["records"]:
        for edge_name, edge in record["edges"].items():
            assert len(edge["bolts"]) == len(EDGES[edge_name][3])
            assert edge["face_contact"]["sample_count"] == 4

            for bolt in edge["bolts"]:
                for action in ("shear", "axial_tension", "combined"):
                    on_first = np.asarray(bolt[action]["force_on_first_n"])
                    on_second = np.asarray(bolt[action]["force_on_second_n"])
                    np.testing.assert_allclose(on_first, -on_second, atol=1e-12)

                shear = np.asarray(bolt["shear"]["force_on_second_n"])
                axial = np.asarray(bolt["axial_tension"]["force_on_second_n"])
                combined = np.asarray(bolt["combined"]["force_on_second_n"])
                np.testing.assert_allclose(combined, shear + axial, atol=1e-12)
                assert bolt["shear"]["magnitude_n"] == pytest.approx(
                    np.linalg.norm(shear)
                )
                assert bolt["combined"]["magnitude_n"] == pytest.approx(
                    np.linalg.norm(combined)
                )
                assert bolt["axial_tension"]["tension_n"] == pytest.approx(
                    np.linalg.norm(axial)
                )

            contact = edge["face_contact"]
            np.testing.assert_allclose(
                contact["on_first"]["force_n"],
                -np.asarray(contact["on_second"]["force_n"]),
                atol=1e-12,
            )
            np.testing.assert_allclose(
                contact["on_first"]["moment_about_interface_center_nmm"],
                -np.asarray(contact["on_second"]["moment_about_interface_center_nmm"]),
                atol=1e-9,
            )

            complete = edge["complete_interface_action"]
            np.testing.assert_allclose(
                complete["on_first"]["force_n"],
                -np.asarray(complete["on_second"]["force_n"]),
                atol=FORCE_TOLERANCE_N,
            )
            np.testing.assert_allclose(
                complete["on_first"]["moment_about_interface_center_nmm"],
                -np.asarray(complete["on_second"]["moment_about_interface_center_nmm"]),
                atol=MOMENT_TOLERANCE_NMM,
            )
            assert edge["equal_and_opposite_check"]["passed"] is True


def test_all_reconstructed_body_equilibrium_passes(report):
    for record in report["records"]:
        equilibrium = record["body_equilibrium"]
        assert equilibrium["passed"] is True
        assert equilibrium["maximum_force_residual_n"] <= FORCE_TOLERANCE_N
        assert equilibrium["maximum_moment_residual_nmm"] <= MOMENT_TOLERANCE_NMM
        for body in equilibrium["bodies"].values():
            internal = body["internal_reaction_wrench_about_origin"]
            external = body["matching_external_load_wrench_about_origin"]
            np.testing.assert_allclose(
                np.asarray(internal["force_n"]) + external["force_n"],
                body["residual"]["force_n"],
                atol=1e-12,
            )
            np.testing.assert_allclose(
                np.asarray(internal["moment_nmm"]) + external["moment_nmm"],
                body["residual"]["moment_nmm"],
                atol=1e-9,
            )


def test_scope_limitations_forbid_demand_enveloping_and_release(report):
    limitations = " ".join(report["limitations"])

    assert report["strength_or_fabrication_release"] is False
    assert "historical-action provisional" in limitations
    assert "not current PB02 design demands" in limitations
    assert "no a12-forward" in limitations
    assert "no Frankenstein envelope" in limitations
    assert (
        "not a structural, drilling, fabrication, or construction release"
        in limitations
    )
