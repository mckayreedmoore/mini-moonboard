"""Physical-law checks for PB02 contact and tension-only spring directions."""

import numpy as np
import pytest

from fea.current_response_run import (
    axial_tension_state,
    next_axial_tension_names,
    physical_forces,
)
from fea.horizontal_panel_frame import Structure, next_bearing_set
from fea.round_insert_frame import normal_contact
from scripts.simple_center_connected_kinematics import EDGES
from scripts.simple_center_pb02_native import (
    PB02Native,
    _shifted_post_header_contacts,
    add_native_paths,
    native_row_inventory,
)


class PointStructure(Structure):
    """Use real Structure springs/equations with prescribed point-body motion."""

    def __init__(self):
        super().__init__()
        self.source_part = {}

    def attachment(self, member_name, point):
        tag = self.node(point)
        self.source_part[tag] = member_name
        return tag


@pytest.fixture(scope="module")
def native_paths():
    structure = PointStructure()
    metadata = {}
    add_native_paths(
        structure,
        metadata,
        bolt_axial_n_per_mm=700.0,
        bolt_lateral_n_per_mm=1200.0,
        face_normal_total_n_per_mm=2400.0,
    )
    return structure, metadata


def _spring(structure, name, dof=None):
    matches = [
        row
        for row in structure.springs
        if row["name"] == name and (dof is None or row["dof"] == dof)
    ]
    assert len(matches) == 1
    return matches[0]


def _projected_spring_displacements(structure, spring, movements):
    """Resolve helper-created MPC equations under prescribed body translations."""
    result = {}
    for auxiliary in spring["nodes"]:
        equation = next(
            terms
            for terms in structure.equations
            if terms[0][:2] == (auxiliary, spring["dof"])
        )
        leading_node, leading_dof, leading_coefficient = equation[0]
        assert leading_node == auxiliary
        assert leading_dof == spring["dof"]
        value = 0.0
        for source, dof, coefficient in equation[1:]:
            part = structure.source_part[source]
            value -= coefficient * movements.get(part, np.zeros(3))[dof - 1]
        displacement = np.zeros(3)
        displacement[spring["dof"] - 1] = value / leading_coefficient
        result[auxiliary] = displacement
    return result


@pytest.mark.parametrize("edge", tuple(EDGES))
def test_canonical_contact_opening_releases_and_closing_pushes_apart(
    native_paths, edge
):
    structure, metadata = native_paths
    row = next(
        item
        for item in native_row_inventory()
        if item["edge"] == edge and item["kind"] == "contact_compression"
    )
    spring = _spring(structure, row["name"], dof=1)
    owner = metadata["connection_ownership"][row["name"]]
    first_to_second = np.asarray(EDGES[edge][2], dtype=float)
    inward_into_first = -first_to_second

    assert owner["first"] == row["first_part"]
    assert owner["second"] == row["second_part"]
    np.testing.assert_allclose(row["direction"], first_to_second)
    np.testing.assert_allclose(owner["scalar_normal"], inward_into_first)

    opening_motion = {owner["second"]: -0.1 * inward_into_first}
    opening_u = _projected_spring_displacements(structure, spring, opening_motion)
    first_node, second_node = spring["nodes"]
    opening_mm = -(opening_u[second_node][0] - opening_u[first_node][0])
    assert opening_mm == pytest.approx(0.1)
    assert row["name"] not in next_bearing_set(
        [{"name": row["name"], "active": True, "opening_mm": opening_mm}]
    )

    closing_motion = {owner["second"]: 0.1 * inward_into_first}
    closing_u = _projected_spring_displacements(structure, spring, closing_motion)
    closing_delta = closing_u[second_node][0] - closing_u[first_node][0]
    closing_mm = -closing_delta
    assert closing_mm == pytest.approx(-0.1)
    assert row["name"] in next_bearing_set(
        [{"name": row["name"], "active": False, "opening_mm": closing_mm}]
    )

    force_n = spring["stiffness_n_per_mm"] * closing_delta
    physical = physical_forces(
        {"connection_ownership": {row["name"]: owner}},
        {
            "connector_forces": {
                row["name"]: {"force_on_first_xyz_n": [force_n, 0.0, 0.0]}
            }
        },
    )[row["name"]]
    on_first = np.asarray(physical["force_on_first_xyz_n"])
    on_second = np.asarray(physical["force_on_second_xyz_n"])
    assert np.dot(on_first, first_to_second) < 0.0
    assert np.dot(on_second, first_to_second) > 0.0
    np.testing.assert_allclose(on_first + on_second, 0.0)


def test_tension_only_bolt_axis_and_slack_compression_follow_existing_law(
    native_paths,
):
    structure, metadata = native_paths
    row = next(
        item for item in native_row_inventory() if item["kind"] == "bolt_tension"
    )
    name = row["name"].removesuffix("/tension")
    spring = _spring(structure, name, dof=1)
    owner = metadata["connection_ownership"][name]
    axis = np.asarray(row["direction"], dtype=float)

    assert owner["first"] == row["first_part"]
    assert owner["second"] == row["second_part"]
    np.testing.assert_allclose(owner["axis"], axis)
    assert spring["tension_only_assumption"] is True

    compression_u = _projected_spring_displacements(
        structure, spring, {owner["second"]: -0.1 * axis}
    )
    inactive = axial_tension_state(
        {"springs": [{**spring, "active": False}]}, compression_u
    )[0]
    assert inactive["extension_mm"] == pytest.approx(-0.1)
    assert inactive["tension_force_n"] == 0.0
    assert inactive["tension_only_assumption_satisfied"] is True
    assert next_axial_tension_names([inactive]) == set()

    tension_u = _projected_spring_displacements(
        structure, spring, {owner["second"]: 0.1 * axis}
    )
    active = axial_tension_state({"springs": [{**spring, "active": True}]}, tension_u)[
        0
    ]
    assert active["extension_mm"] == pytest.approx(0.1)
    assert active["tension_force_n"] == pytest.approx(70.0)
    assert next_axial_tension_names([active]) == {name}

    physical = physical_forces(
        {"connection_ownership": {name: owner}},
        {
            "connector_forces": {
                name: {
                    "force_on_first_xyz_n": [
                        active["tension_force_n"],
                        0.0,
                        0.0,
                    ]
                }
            }
        },
    )[name]
    np.testing.assert_allclose(physical["force_on_first_xyz_n"], 70.0 * axis)
    np.testing.assert_allclose(physical["force_on_second_xyz_n"], -70.0 * axis)


def test_shifted_post_header_samples_keep_inward_z_and_total_face_stiffness():
    total_stiffness = 2400.0
    contacts = _shifted_post_header_contacts(PB02Native(), total_stiffness)

    assert len(contacts) == 4
    assert {tuple(contact["normal_xyz"]) for contact in contacts} == {(0.0, 0.0, -1.0)}
    assert sum(contact["stiffness_n_per_mm"] for contact in contacts) == pytest.approx(
        total_stiffness
    )

    structure = PointStructure()
    ownership = {}
    for contact in contacts:
        first = structure.attachment(contact["first"], contact["point_xyz_mm"])
        second = structure.attachment(contact["second"], contact["point_xyz_mm"])
        normal_contact(
            structure,
            contact["name"],
            first,
            [second],
            [1.0],
            contact["point_xyz_mm"],
            contact["normal_xyz"],
            contact["stiffness_n_per_mm"],
        )
        ownership[contact["name"]] = {
            "first": contact["first"],
            "second": contact["second"],
            "point": contact["point_xyz_mm"],
            "scalar_normal": contact["normal_xyz"],
        }

    for contact in contacts:
        spring = _spring(structure, contact["name"], dof=1)
        movement = {contact["second"]: np.array([0.0, 0.0, -0.1])}
        displacements = _projected_spring_displacements(structure, spring, movement)
        first_node, second_node = spring["nodes"]
        delta = displacements[second_node][0] - displacements[first_node][0]
        force_n = spring["stiffness_n_per_mm"] * delta
        physical = physical_forces(
            {"connection_ownership": {contact["name"]: ownership[contact["name"]]}},
            {
                "connector_forces": {
                    contact["name"]: {"force_on_first_xyz_n": [force_n, 0.0, 0.0]}
                }
            },
        )[contact["name"]]
        assert delta == pytest.approx(0.1)
        np.testing.assert_allclose(
            physical["force_on_first_xyz_n"], [0.0, 0.0, -force_n]
        )
        np.testing.assert_allclose(
            np.asarray(physical["force_on_first_xyz_n"])
            + physical["force_on_second_xyz_n"],
            0.0,
        )
