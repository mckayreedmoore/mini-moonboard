"""Source-bound preparation of the integrated 46-pair barrel frame."""

import pytest

from scripts import owner_barrel_native_preparation as native


@pytest.fixture(scope="module")
def module():
    return native.IntegratedBarrelNative()


def test_integrated_module_has_only_current_connection_topology(module):
    connections = module.connections()
    names = {row.name for row in connections}
    assert len(connections) == len(names) == 124
    assert sum(row.kind == "bolt" for row in connections) == 58
    assert len(module.panel_connections()) == 66
    assert len(module.barrel_bolt_names) == 46
    assert len(module.uncut_wood_parts()) == 26
    assert not names & {row.name for row in module.assembly["removed_legacy_sds"]}
    assert not any(name.startswith("inner_kicker_backer_") for name in module.assembly["wood"])
    assert module.KEY == native.SOURCE_ID


def test_barrel_mass_envelopes_and_contact_normals_are_not_legacy_angles(module):
    barrels = [row for row in module.connections() if row.name in module.barrel_bolt_names]
    assert all(len(row.components()) == 4 for row in barrels)
    assert all(row.kind == "bolt" for row in barrels)
    assert not any(part.name.startswith("clip_") for part in module.parts())
    contacts = native.member_contacts(module, stiffness_per_area=100.0)
    assert len(contacts) == 120
    assert all(row["stiffness_n_per_mm"] > 0 for row in contacts)
    assert sum(row["name"].startswith("clip_split_base_center_") for row in contacts) == 32
    assert all(row["conditional_only"] for row in contacts)
    for station, face in module.faces["stations"].items():
        first = next(row for row in contacts if row["station"] == station)
        outward = face["normal_outward_from_first_xyz"]
        assert sum(a * b for a, b in zip(first["normal_xyz"], outward, strict=True)) == (
            pytest.approx(-1, abs=1e-6)
        )
