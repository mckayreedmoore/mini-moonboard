"""PB05 mechanics preparation stays bound to its own eight-station geometry."""

import pytest

from scripts.simple_pb05_native import OUTER_STATIONS, SOURCE_ID, screen
from scripts.simple_pb05_native_mechanics import (
    MECHANICS_SOURCE_ID,
    PB05MechanicsNative,
    activate_existing_paths,
    native_member_contacts,
    native_row_inventory,
)


@pytest.fixture(scope="module")
def prepared():
    module = PB05MechanicsNative()
    rows, identity = native_row_inventory(module)
    return module, rows, identity


def test_source_bound_rows_and_exact_faces(prepared):
    module, rows, identity = prepared
    geometry = module.pb03_geometries()
    assert identity["mechanics_source_id"] == MECHANICS_SOURCE_ID
    assert identity["pb05_source_id"] == SOURCE_ID
    assert (
        identity["source_fingerprint_sha256"]
        == screen(module)["source_fingerprint_sha256"]
    )
    assert identity["outer_stations"] == list(OUTER_STATIONS)
    assert identity["legacy_proxy_stations"] == 14
    assert identity["fixed_panel_kicker_axes"] == 66
    assert len(rows) == len({row["name"] for row in rows}) == 96
    assert sum(row["kind"] == "bolt" for row in rows) == 32
    assert sum(row["kind"] == "contact_compression" for row in rows) == 64
    for station, block in geometry.items():
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
                block.report["contact_area_mm2"][interface], abs=1e-4
            )
    points = {row["name"]: row["point_mm"] for row in rows if row["kind"] == "bolt"}
    for bolt in module.connections():
        if bolt.name in points:
            assert module.bolt_interface_point(bolt).toTuple() == pytest.approx(
                points[bolt.name]
            )
    contacts, scope = native_member_contacts(2400.0, module, (rows, identity))
    assert len(contacts) == 64
    assert scope["identity"] == identity


def test_invalid_contact_stiffness_rejected(prepared):
    module, rows, identity = prepared
    with pytest.raises(ValueError, match="positive and finite"):
        native_member_contacts(0.0, module, (rows, identity))


def test_activation_marks_existing_paths_without_release(prepared):
    module, rows, identity = prepared
    ownership = {}
    springs = []
    for row in rows:
        owner = {
            "first": row["first_part"],
            "second": row["second_part"],
            "point": row["point_mm"],
        }
        if row["kind"] == "bolt":
            owner["axis"] = row["direction"]
            springs.extend({"name": row["name"], "dof": dof} for dof in (1, 2, 3))
        else:
            owner["scalar_normal"] = row["direction"]
            springs.append(
                {"name": row["name"], "dof": 1, "bearing_closed_assumption": True}
            )
        ownership[row["name"]] = owner
    structure = type("Prepared", (), {"springs": springs})()
    metadata = {"connection_ownership": ownership}
    assert (
        activate_existing_paths(structure, metadata, module, (rows, identity))
        == identity
    )
    assert len(structure.springs) == 160
    assert sum(spring.get("tension_only_assumption", False) for spring in springs) == 32
    assert metadata["pb05_native_row_counts"] == {
        "existing_bolt_axes": 32,
        "bolt_tension_only": 32,
        "existing_bolt_lateral": 64,
        "contact_compression_cells": 64,
    }
    assert metadata["pb05_mechanics_identity"] == identity
    assert "pb03_mechanics_identity" not in metadata
    assert not metadata["acceptance"]
    assert not metadata["drilling_released"]
    assert not metadata["fabrication_released"]
