"""PB03 can use the PB02 preparer without adding its contact mechanics."""

import pytest

from fea.floor_flush_run import face_contacts
from scripts.simple_center_pb02_native import PB02Native, prepare_case
from scripts.simple_pb03_native import BLOCK_NAMES, PB03Native

AXIAL_STIFFNESS = 700.0
LATERAL_STIFFNESS = 1200.0
FACE_STIFFNESS = 2400.0


@pytest.fixture(scope="module")
def module():
    return PB03Native()


@pytest.fixture(scope="module")
def prepared(module):
    return prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=AXIAL_STIFFNESS,
        bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
        face_normal_total_n_per_mm=FACE_STIFFNESS,
        module=module,
        expected_candidate=module.KEY,
        member_contacts=face_contacts(PB02Native()),
        expected_legacy_station_count=14,
        post_prepare=module.validate_prepared_case,
    )


def test_pb03_prepares_exact_unsolved_inventory(module, prepared):
    structure, metadata = prepared
    connections = module.connections()
    pb03_bolts = [row for row in connections if row.name.startswith("pb03_")]
    legacy_sds = [row for row in connections if row.name.startswith("clip_")]

    assert len(module.legacy_proxy_stations()) == 14
    assert len(legacy_sds) == 84
    assert len(pb03_bolts) == 32
    assert len(module.panel_connections()) == 66
    assert set(BLOCK_NAMES.values()) <= set(structure.members)
    assert set(metadata["connection_ownership"]) >= {row.name for row in pb03_bolts}
    assert not any(
        name.startswith("pb03_") and name.endswith("_contact")
        for name in metadata["connection_ownership"]
    )


def test_pb03_block_axes_sections_and_exact_bolt_points(module, prepared):
    structure, _ = prepared
    points = module.pb03_bolt_interface_points()
    pb03_bolts = {
        row.name: row for row in module.connections() if row.name.startswith("pb03_")
    }

    assert set(points) == set(pb03_bolts)
    for name in BLOCK_NAMES.values():
        grain, section = module.MEMBER_AXES[name]
        assert grain.toTuple() == pytest.approx((0.0, -0.7660444431, 0.6427876097))
        assert section.toTuple() == pytest.approx((1.0, 0.0, 0.0))
        record = structure.members[name]["record"]
        assert record["axis"] == pytest.approx(grain.toTuple())
        assert record["section_u"] == pytest.approx(section.toTuple())
        assert name in module.NATIVE_SQUARE_END_MEMBERS

    for name, connection in pb03_bolts.items():
        assert module.bolt_interface_point(connection).toTuple() == pytest.approx(
            points[name].toTuple()
        )


def test_pb03_preparation_retains_pb02_center_paths_and_no_release(prepared):
    structure, metadata = prepared
    shifted = set(metadata["pb02_shifted_post_header_contacts"]["names"])
    spring_names = {spring["name"] for spring in structure.springs}

    assert len(shifted) == 4
    assert shifted <= spring_names
    assert metadata["pb02_native_row_counts"]["bolt_tension_only"] == 10
    assert metadata["pb03_preparation_validated"] is True
    assert metadata["solved"] is False
    assert metadata["qualified_for_design"] is False
    assert metadata["actual_joint_demands_qualified"] is False
    assert metadata["acceptance"] is False
    assert metadata["drilling_released"] is False
    assert metadata["fabrication_released"] is False
    assert metadata["preparation_only"] is True
    assert metadata["developmental_only"] is True
