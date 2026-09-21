"""Identity and geometry checks for the PB04 mechanics adapter."""

import numpy as np
import pytest

from scripts.simple_pb04_native import SOURCE_ID
from scripts.simple_pb04_native_mechanics import (
    MECHANICS_SOURCE_ID,
    PB04MechanicsNative,
    native_member_contacts,
    native_row_inventory,
)


@pytest.fixture(scope="module")
def module():
    return PB04MechanicsNative()


@pytest.fixture(scope="module")
def inventory(module):
    return native_row_inventory(module)


def test_inventory_has_new_pb04_identity_and_fixed_counts(inventory):
    rows, identity = inventory

    assert identity["mechanics_source_id"] == MECHANICS_SOURCE_ID
    assert identity["pb04_source_id"] == SOURCE_ID
    assert "pb03_source_id" not in identity
    assert identity["legacy_proxy_stations"] == 14
    assert identity["fixed_panel_kicker_axes"] == 66
    assert len(identity["replaced_stations"]) == 8
    assert len(identity["row_fingerprint_sha256"]) == 64
    assert sum(row["kind"] == "bolt" for row in rows) == 32
    assert sum(row["kind"] == "contact_compression" for row in rows) == 64
    assert len(rows) == len({row["name"] for row in rows}) == 96


def test_contact_cells_preserve_each_pb04_face(module, inventory):
    rows, _ = inventory
    geometry_factory = getattr(module, "pb04_geometries", module.pb03_geometries)
    for station, geometry in geometry_factory().items():
        for interface in ("upright", "rail"):
            cells = [
                row
                for row in rows
                if row["station"] == station
                and row["interface"] == interface
                and row["kind"] == "contact_compression"
            ]
            assert len(cells) == 4
            assert sum(row["tributary_area_mm2"] for row in cells) == pytest.approx(
                geometry.report["contact_area_mm2"][interface], abs=1e-4
            )
            points = np.asarray([row["point_mm"] for row in cells])
            assert np.linalg.matrix_rank(points - points.mean(axis=0), tol=1e-7) == 2


def test_exact_points_block_axes_and_contact_law_are_exposed(module, inventory):
    rows, identity = inventory
    bolt_points = {
        row["name"]: row["point_mm"] for row in rows if row["kind"] == "bolt"
    }
    for connection in module.connections():
        if connection.name in bolt_points:
            assert module.bolt_interface_point(connection).toTuple() == pytest.approx(
                bolt_points[connection.name]
            )
    block_names = {row["second_part"] for row in rows if row["kind"] == "bolt"}
    assert block_names <= set(module.MEMBER_AXES)
    assert block_names <= set(module.NATIVE_SQUARE_END_MEMBERS)
    contacts, scope = native_member_contacts(2400.0, module, inventory)
    assert len(contacts) == 64
    assert scope["identity"] == identity
    assert scope["rotation_and_partial_opening_resolved"] is True


@pytest.mark.parametrize("value", (0.0, -1.0, np.inf, np.nan))
def test_contact_records_reject_invalid_trial_stiffness(value):
    with pytest.raises(ValueError, match="positive and finite"):
        native_member_contacts(value)
