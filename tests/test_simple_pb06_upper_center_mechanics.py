"""PB06 mechanics is source-bound preparation, not a solved load case."""

import pytest

from scripts import simple_pb06_upper_center_native as pb06
from scripts.simple_pb06_upper_center_mechanics import (
    activate_existing_paths,
    native_member_contacts,
    native_row_inventory,
)


@pytest.fixture(scope="module")
def prepared():
    module = pb06.PB06Native()
    return module, native_row_inventory(module)


def test_source_rows_faces_and_points(prepared):
    module, (rows, identity) = prepared
    source = pb06.screen(module)
    assert identity["pb06_source_id"] == pb06.SOURCE_ID
    assert identity["source_fingerprint_sha256"] == source["source_fingerprint_sha256"]
    assert len(rows) == len({row["name"] for row in rows}) == 120
    assert sum(row["kind"] == "bolt" for row in rows) == 40
    assert sum(row["kind"] == "contact_compression" for row in rows) == 80
    assert identity["fixed_panel_kicker_axes"] == 66
    assert identity["original_frame_bolt_axes"] == 12
    assert identity["legacy_sds_duties"] == 12
    assert identity["legacy_sds_axes"] == 72
    for station, geometry in module.pb03_geometries().items():
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
    points = {row["name"]: row["point_mm"] for row in rows if row["kind"] == "bolt"}
    for bolt in module.connections():
        if bolt.name in points:
            assert module.bolt_interface_point(bolt).toTuple() == pytest.approx(
                points[bolt.name], abs=1e-7
            )


def test_contact_law_and_no_release(prepared):
    module, inventory = prepared
    rows, identity = inventory
    contacts, scope = native_member_contacts(2400.0, module, inventory)
    assert len(contacts) == 80
    assert scope["identity"] == identity
    mean_area = sum(row["tributary_area_mm2"] for row in contacts) / 20
    assert scope["common_areal_density_n_per_mm3"] == pytest.approx(2400 / mean_area)
    assert sum(row["stiffness_n_per_mm"] for row in contacts) == pytest.approx(
        20 * 2400
    )
    with pytest.raises(ValueError, match="positive and finite"):
        native_member_contacts(0.0, module, inventory)

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
    assert activate_existing_paths(structure, metadata, module, inventory) == identity
    assert len(springs) == 200
    assert sum(spring.get("tension_only_assumption", False) for spring in springs) == 40
    assert metadata["pb06_native_row_counts"] == {
        "existing_bolt_axes": 40,
        "bolt_tension_only": 40,
        "existing_bolt_lateral": 80,
        "contact_compression_cells": 80,
    }
    assert metadata["pb06_mechanics_identity"] == identity
    assert "pb03_mechanics_identity" not in metadata
    assert all(
        metadata[flag] is False
        for flag in (
            "solved",
            "force_transfer",
            "qualified_for_design",
            "acceptance",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )
