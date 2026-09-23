"""Actual mapped geometry for integrated barrel bevel-end members."""

import numpy as np
import pytest

from fea.current_response_model import gross_member_record
from fea.floor_taper_mesh import locate
from fea.horizontal_frame_members import axes
from scripts import owner_barrel_native_preparation as native


@pytest.fixture(scope="module")
def module():
    return native.IntegratedBarrelNative()


def _record(module, part):
    grain, section_u = module.MEMBER_AXES.get(part.name) or axes(module, part.name)
    return native._bevel_record(
        part,
        gross_member_record(part, grain, section_u),
    )


def test_all_former_projection_members_have_actual_source_bound_prisms(module):
    parts = {part.name: part for part in module.uncut_wood_parts()}

    assert module.FULL_BEVEL_PROJECTION_MEMBERS == ()
    assert module.ACTUAL_BEVEL_MEMBERS == native.ACTUAL_BEVEL_MEMBERS
    for name in module.ACTUAL_BEVEL_MEMBERS:
        part = parts[name]
        record = _record(module, part)
        geometry = record["uncut_prism_geometry"]

        assert record["owner_barrel_bevel_geometry"]["mode"] == (
            "actual_constant_x_cad_prism_c3d20"
        )
        assert geometry["expected_volume_mm3"] == pytest.approx(part.shape.Volume())
        assert geometry["expected_centroid_xyz_mm"] == pytest.approx(
            part.shape.Center().toTuple()
        )
        assert len(geometry["side_profile_yz_mm"]) == 5
        assert "bevel_projection" not in record


def test_actual_prism_mesh_contains_real_contact_and_bolt_points(module):
    parts = {part.name: part for part in module.uncut_wood_parts()}
    contacts = (
        *native.member_contacts(module, stiffness_per_area=100.0),
        *native.retained_face_contacts(module, stiffness_per_area=100.0),
    )
    points = {name: [] for name in module.ACTUAL_BEVEL_MEMBERS}
    for connection in module.connections():
        if connection.kind != "bolt":
            continue
        point = np.asarray(module.bolt_interface_point(connection).toTuple())
        for name in connection.members:
            if name in points:
                points[name].append(point)
    for contact in contacts:
        point = np.asarray(contact["point_xyz_mm"])
        for role in ("first", "second"):
            if contact[role] in points:
                points[contact[role]].append(point)

    structure = native.IntegratedBarrelStructure({})
    for name in module.ACTUAL_BEVEL_MEMBERS:
        part = parts[name]
        record = _record(module, part)
        assert points[name], name
        structure.member(record, points[name], size=150.0)
        member = structure.members[name]
        assert member["record"]["native_section_geometry"] == (
            "ACTUAL_UNCUT_PRISM_C3D20"
        )
        assert member["retained_mesh_volume_mm3"] == pytest.approx(
            part.shape.Volume(), abs=0.03
        )
        assert member["retained_mesh_centroid_xyz_mm"] == pytest.approx(
            part.shape.Center().toTuple(), abs=1.0e-6
        )
        for point in points[name]:
            node_ids, weights = locate(structure, name, point)
            mapped = weights @ np.asarray([structure.nodes[node] for node in node_ids])
            assert mapped == pytest.approx(point, abs=1.0e-6)
