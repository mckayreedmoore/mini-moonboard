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
    assert len(module.current_response_wood_parts()) == 26
    uncut = {part.name: part for part in module.uncut_wood_parts()}
    cut = {part.name: part for part in module.current_response_wood_parts()}
    for name in ("lumber_leg_left", "lumber_leg_right", "base_header"):
        assert cut[name].shape.Volume() < uncut[name].shape.Volume()
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


def test_one_signed_case_prepares_without_legacy_connectors(module):
    structure, metadata, summary = native.prepare_case("a12-rear", module=module)
    names = {row["name"] for row in structure.springs}
    assert summary["case"] == "a12-rear"
    assert summary["barrel_pairs"] == 46
    assert summary["face_contact_cells"] == 120
    assert summary["retained_face_contact_cells"] == 72
    assert summary["implicit_header_bearings"] is False
    assert len(summary["analysis_only_full_bevel_members"]) == 4
    assert summary["native_solve"] is False
    assert summary["structural_released"] is False
    assert metadata["diagnostic_only"] is True
    assert metadata["bolted_joint_demands"] is False
    assert metadata["acceptance"] is False
    assert metadata["header_bearing_assumption"].startswith("No implicit")
    assert not names & {row.name for row in module.assembly["removed_legacy_sds"]}
    assert not any(name.startswith("bearing_") for name in names)
    for bolt in module.barrel_bolt_names:
        springs = [spring for spring in structure.springs if spring["name"] == bolt]
        assert len(springs) == 3
        axial = next(spring for spring in springs if spring["dof"] == 1)
        assert axial["tension_only_assumption"] is True
    assert metadata["connection_ownership"]
