"""Physical-law checks for the bounded PB03 eight-station mechanics adapter."""

import copy

import numpy as np
import pytest

from fea import current_response_model as response
from fea import round_insert_frame as shared
from fea.current_response_run import (
    axial_tension_state,
    next_axial_tension_names,
    physical_forces,
)
from fea.horizontal_panel_frame import Structure, next_bearing_set
from scripts import simple_rail_joint_comparison as pb01
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_pb03_native import BLOCK_NAMES, REPLACED_STATIONS, SOURCE_ID
from scripts.simple_pb03_native_mechanics import (
    MECHANICS_SOURCE_ID,
    PB03MechanicsNative,
    activate_existing_paths,
    native_member_contacts,
    native_row_inventory,
)


class PointStructure(Structure):
    """Exercise real connector helpers under prescribed body translations."""

    def __init__(self):
        super().__init__()
        self.source_part = {}

    def attachment(self, member_name, point):
        tag = self.node(point)
        self.source_part[tag] = member_name
        return tag


def _spring(structure, name, dof):
    matches = [
        row for row in structure.springs if row["name"] == name and row["dof"] == dof
    ]
    assert len(matches) == 1
    return matches[0]


def _projected_displacements(structure, spring, movements):
    result = {}
    for auxiliary in spring["nodes"]:
        equation = next(
            terms
            for terms in structure.equations
            if terms[0][:2] == (auxiliary, spring["dof"])
        )
        value = 0.0
        for source, dof, coefficient in equation[1:]:
            value -= (
                coefficient
                * movements.get(structure.source_part[source], np.zeros(3))[dof - 1]
            )
        displacement = np.zeros(3)
        displacement[spring["dof"] - 1] = value / equation[0][2]
        result[auxiliary] = displacement
    return result


@pytest.fixture(scope="module")
def module():
    return PB03MechanicsNative()


@pytest.fixture(scope="module")
def inventory(module):
    return native_row_inventory(module)


@pytest.fixture(scope="module")
def prepared_paths(module, inventory):
    rows, _ = inventory
    contacts, contact_scope = native_member_contacts(
        2400.0, module=module, row_inventory=inventory
    )
    structure = PointStructure()
    ownership = {}
    for row in (row for row in rows if row["kind"] == "bolt"):
        owner = {
            "first": row["first_part"],
            "second": row["second_part"],
            "point": row["point_mm"],
            "axis": row["direction"],
        }
        response.directional_connector(
            structure,
            structure.attachment(row["first_part"], row["point_mm"]),
            structure.attachment(row["second_part"], row["point_mm"]),
            {"axial_n_per_mm": 700.0, "lateral_n_per_mm": 1200.0},
            row["name"],
            owner,
        )
        ownership[row["name"]] = owner
    for contact in contacts:
        shared.normal_contact(
            structure,
            contact["name"],
            structure.attachment(contact["first"], contact["point_xyz_mm"]),
            [structure.attachment(contact["second"], contact["point_xyz_mm"])],
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
    metadata = {"connection_ownership": ownership}
    count_before = len(structure.springs)
    activate_existing_paths(structure, metadata, module=module, row_inventory=inventory)
    return structure, metadata, count_before, contact_scope


def test_inventory_is_source_bound_and_preserves_legacy_stations(inventory):
    rows, identity = inventory
    assert identity["mechanics_source_id"] == MECHANICS_SOURCE_ID
    assert identity["pb03_source_id"] == SOURCE_ID
    assert identity["pb02_source_fingerprint"] == ACTIVE_FINGERPRINT
    assert identity["replaced_stations"] == list(REPLACED_STATIONS)
    assert identity["legacy_proxy_stations"] == 14
    assert identity["fixed_panel_kicker_axes"] == 66
    assert identity["contact_grid"] == [2, 2]
    assert len(identity["row_fingerprint_sha256"]) == 64
    assert sum(row["kind"] == "contact_compression" for row in rows) == 64
    assert sum(row["kind"] == "bolt" for row in rows) == 32
    assert len(rows) == len({row["name"] for row in rows}) == 96


def test_four_cell_faces_preserve_area_normals_and_rocking_lever_arms(
    module, inventory
):
    rows, _ = inventory
    geometries = module.pb03_geometries()
    for station, geometry in geometries.items():
        for interface in ("upright", "rail"):
            cells = [
                row
                for row in rows
                if row["station"] == station
                and row["interface"] == interface
                and row["kind"] == "contact_compression"
            ]
            bolts = [
                row
                for row in rows
                if row["station"] == station
                and row["interface"] == interface
                and row["kind"] == "bolt"
            ]
            assert len(cells) == 4
            assert sum(row["tributary_area_mm2"] for row in cells) == pytest.approx(
                geometry.report["contact_area_mm2"][interface], abs=1e-4
            )
            normal = np.asarray(cells[0]["direction"])
            assert np.linalg.norm(normal) == pytest.approx(1.0)
            assert all(
                np.allclose(row["direction"], normal, atol=1e-9) for row in cells
            )
            assert all(
                np.allclose(row["direction"], normal, atol=1e-9) for row in bolts
            )
            centered = np.asarray([row["point_mm"] for row in cells])
            centered -= centered.mean(axis=0)
            assert np.linalg.matrix_rank(centered, tol=1e-7) == 2
            rotation_axis = centered[0] / np.linalg.norm(centered[0])
            opening = np.cross(rotation_axis, centered) @ normal
            assert opening.min() < 0.0 < opening.max()


def test_adapter_exposes_exact_points_and_explicit_block_member_axes(module, inventory):
    rows, _ = inventory
    bolt_points = {
        row["name"]: row["point_mm"] for row in rows if row["kind"] == "bolt"
    }
    for connection in module.connections():
        if connection.name not in bolt_points:
            continue
        assert module.bolt_interface_point(connection).toTuple() == pytest.approx(
            bolt_points[connection.name]
        )
    assert set(BLOCK_NAMES.values()) <= set(module.MEMBER_AXES)
    assert set(BLOCK_NAMES.values()) <= set(module.NATIVE_SQUARE_END_MEMBERS)
    for block_name in BLOCK_NAMES.values():
        grain, section = module.MEMBER_AXES[block_name]
        assert grain.toTuple() == pytest.approx((0.0, *pb01.N))
        assert section.toTuple() == pytest.approx((1.0, 0.0, 0.0))


def test_activation_marks_existing_paths_without_duplicate_connectors(
    prepared_paths,
):
    structure, metadata, count_before, contact_scope = prepared_paths
    assert count_before == 160
    assert len(structure.springs) == count_before
    assert (
        sum(
            spring.get("tension_only_assumption") is True
            for spring in structure.springs
        )
        == 32
    )
    assert metadata["pb03_native_row_counts"] == {
        "existing_bolt_axes": 32,
        "bolt_tension_only": 32,
        "existing_bolt_lateral": 64,
        "contact_compression_cells": 64,
    }
    assert contact_scope["rotation_and_partial_opening_resolved"] is True
    assert metadata["qualified_for_design"] is False
    assert metadata["acceptance"] is False
    assert metadata["drilling_released"] is False
    assert metadata["fabrication_released"] is False


def test_duplicate_existing_bolt_connector_fails_closed(
    prepared_paths, module, inventory
):
    structure, metadata, _, _ = prepared_paths
    duplicate_structure = copy.deepcopy(structure)
    duplicate_metadata = copy.deepcopy(metadata)
    bolt_name = next(row["name"] for row in inventory[0] if row["kind"] == "bolt")
    duplicate_structure.springs.append(
        copy.deepcopy(
            next(row for row in structure.springs if row["name"] == bolt_name)
        )
    )
    with pytest.raises(ValueError, match="exactly one existing directional"):
        activate_existing_paths(
            duplicate_structure,
            duplicate_metadata,
            module=module,
            row_inventory=inventory,
        )


def test_every_contact_opens_releases_closes_and_pushes_apart(
    prepared_paths, inventory
):
    structure, metadata, _, _ = prepared_paths
    for row in (row for row in inventory[0] if row["kind"] == "contact_compression"):
        spring = _spring(structure, row["name"], 1)
        owner = metadata["connection_ownership"][row["name"]]
        normal = np.asarray(owner["scalar_normal"])
        opening = _projected_displacements(
            structure, spring, {owner["second"]: -0.1 * normal}
        )
        first_node, second_node = spring["nodes"]
        opening_mm = -(opening[second_node][0] - opening[first_node][0])
        assert opening_mm == pytest.approx(0.1)
        assert row["name"] not in next_bearing_set(
            [{"name": row["name"], "active": True, "opening_mm": opening_mm}]
        )

        closing = _projected_displacements(
            structure, spring, {owner["second"]: 0.1 * normal}
        )
        delta = closing[second_node][0] - closing[first_node][0]
        assert -delta == pytest.approx(-0.1)
        force_n = spring["stiffness_n_per_mm"] * delta
        physical = physical_forces(
            {"connection_ownership": {row["name"]: owner}},
            {
                "connector_forces": {
                    row["name"]: {"force_on_first_xyz_n": [force_n, 0.0, 0.0]}
                }
            },
        )[row["name"]]
        assert np.dot(physical["force_on_first_xyz_n"], normal) > 0.0
        np.testing.assert_allclose(
            np.asarray(physical["force_on_first_xyz_n"])
            + physical["force_on_second_xyz_n"],
            0.0,
        )


def test_every_existing_bolt_slacks_and_tensions_with_equal_opposite_actions(
    prepared_paths, inventory
):
    structure, metadata, _, _ = prepared_paths
    for row in (row for row in inventory[0] if row["kind"] == "bolt"):
        spring = _spring(structure, row["name"], 1)
        owner = metadata["connection_ownership"][row["name"]]
        axis = np.asarray(owner["axis"])
        compressed = _projected_displacements(
            structure, spring, {owner["second"]: -0.1 * axis}
        )
        inactive = axial_tension_state(
            {"springs": [{**spring, "active": False}]}, compressed
        )[0]
        assert inactive["extension_mm"] == pytest.approx(-0.1)
        assert inactive["tension_force_n"] == 0.0
        assert inactive["tension_only_assumption_satisfied"] is True
        assert next_axial_tension_names([inactive]) == set()

        extended = _projected_displacements(
            structure, spring, {owner["second"]: 0.1 * axis}
        )
        active = axial_tension_state(
            {"springs": [{**spring, "active": True}]}, extended
        )[0]
        assert active["extension_mm"] == pytest.approx(0.1)
        assert active["tension_force_n"] == pytest.approx(70.0)
        assert next_axial_tension_names([active]) == {row["name"]}
        physical = physical_forces(
            {"connection_ownership": {row["name"]: owner}},
            {
                "connector_forces": {
                    row["name"]: {
                        "force_on_first_xyz_n": [
                            active["tension_force_n"],
                            0.0,
                            0.0,
                        ]
                    }
                }
            },
        )[row["name"]]
        np.testing.assert_allclose(physical["force_on_first_xyz_n"], 70.0 * axis)
        np.testing.assert_allclose(
            np.asarray(physical["force_on_first_xyz_n"])
            + physical["force_on_second_xyz_n"],
            0.0,
        )


def test_every_existing_bolt_retains_two_bilateral_lateral_directions(
    prepared_paths, inventory
):
    structure, metadata, _, _ = prepared_paths
    for row in (row for row in inventory[0] if row["kind"] == "bolt"):
        owner = metadata["connection_ownership"][row["name"]]
        axis = np.asarray(owner["axis"])
        tangent = np.asarray(owner["force_basis"])[1]
        spring = _spring(structure, row["name"], 2)
        displacements = _projected_displacements(
            structure, spring, {owner["second"]: 0.1 * tangent}
        )
        first_node, second_node = spring["nodes"]
        extension = displacements[second_node][1] - displacements[first_node][1]
        assert extension == pytest.approx(0.1)
        force_n = spring["stiffness_n_per_mm"] * extension
        physical = physical_forces(
            {"connection_ownership": {row["name"]: owner}},
            {
                "connector_forces": {
                    row["name"]: {"force_on_first_xyz_n": [0.0, force_n, 0.0]}
                }
            },
        )[row["name"]]
        on_first = np.asarray(physical["force_on_first_xyz_n"])
        assert np.dot(on_first, tangent) == pytest.approx(120.0)
        assert np.dot(on_first, axis) == pytest.approx(0.0, abs=1e-10)
        np.testing.assert_allclose(on_first + physical["force_on_second_xyz_n"], 0.0)


@pytest.mark.parametrize("value", (0.0, -1.0, np.inf, np.nan))
def test_contact_records_reject_invalid_trial_stiffness(value):
    with pytest.raises(ValueError, match="positive and finite"):
        native_member_contacts(value)
