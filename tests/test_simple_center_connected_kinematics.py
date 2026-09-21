"""Connected point model keeps contact and boundary assumptions explicit."""

import copy

import numpy as np
import pytest

from scripts.simple_center_connected_kinematics import (
    CONTACT_CELLS,
    CONTACT_PARTITION,
    EDGES,
    NODE_PARTS,
    _partition_fingerprint,
    constraint_rows,
    contact_partition,
    current_edges,
    matrix,
    screen,
)
from scripts.simple_center_pb02_geometry import active_geometry


def test_current_trial_axes_are_used():
    assert EDGES == current_edges()
    assert EDGES["post_block"][3] == [
        (177.65, -145, 145),
        (177.65, -145, 176),
    ]
    assert EDGES["block_header"][3] == [
        (208.35, -130.5, 186),
        (236.0, -117.5, 186),
    ]
    assert EDGES["header_principal_block"][3] == [(15.475, -139, 291.45)]
    assert EDGES["principal_block_principal"][3] == [(34.525, -95, 312.5)]
    assert np.allclose(EDGES["principal_upright_block"][3], [(114.45, -144.5, 356)])
    assert np.allclose(EDGES["upright_rear_block"][3], [(133.5, -163.95, 328.5)])
    assert EDGES["rear_block_post"][3][1] == (140, -150.3, 202.0)
    assert EDGES["upright_rear_block"][2] == (0, -1, 0)
    assert EDGES["rear_block_post"][2] == (0, 1, 0)
    assert np.allclose(EDGES["post_block"][4], (177.65, -131.25, 166.95))
    assert np.allclose(EDGES["block_header"][4], (222.1, -131.25, 238.9))
    assert np.allclose(EDGES["header_principal_block"][4], (15.475, -110.35, 277))
    assert np.allclose(EDGES["principal_block_principal"][4], (50.95, -113.85, 310.5))
    assert np.allclose(EDGES["principal_upright_block"][4], (89.05, -144.9, 368.5))
    assert np.allclose(EDGES["upright_rear_block"][4], (133.5, -175.7, 368.5))
    assert np.allclose(EDGES["rear_block_post"][4], (133.35, -175.7, 121.95))


def test_connected_rank_depends_on_return_path_and_contacts():
    result = screen()
    anchored = result["post_anchored"]
    assert anchored["all_faces_closed_axial_on"]["relative_dof"] == 0
    assert anchored["all_faces_closed_axial_off"]["relative_dof"] == 0
    assert anchored["serial_only_closed_axial_on"]["relative_dof"] == 2
    assert anchored["principal_faces_open_axial_on"]["relative_dof"] == 2
    assert anchored["main_faces_closed_return_faces_open_axial_on"]["relative_dof"] == 3
    assert (
        anchored["main_faces_closed_return_faces_open_axial_off"]["relative_dof"] == 7
    )
    assert {
        row["relative_dof"] for row in anchored["one_face_open_axial_on"].values()
    } == {0}
    assert {
        row["relative_dof"] for row in anchored["one_face_open_axial_off"].values()
    } == {1}
    assert anchored["all_faces_open_axial_on"]["relative_dof"] == 9
    assert anchored["all_faces_open_axial_off"]["relative_dof"] == 19
    assert result["free_assembly_all_faces_closed_axial_on"]["relative_dof"] == 6
    assert result["strength_or_frame_verdict"] is False


def test_whole_body_translation_is_free_without_post_anchor():
    closed = matrix(closed=EDGES, anchor_post=False)
    translation = np.zeros(closed.shape[1])
    translation[::6] = 1.0
    assert np.linalg.norm(closed @ translation) < 1e-10


def test_contact_samples_lie_on_both_active_cad_faces():
    parts, _, _ = active_geometry()
    axes = ("x", "y", "z")
    for row in constraint_rows(closed=EDGES):
        if row["kind"] != "contact_compression":
            continue
        first, second, normal, _, _ = EDGES[row["edge"]]
        normal_index = next(index for index, value in enumerate(normal) if value)
        for node in (first, second):
            bounds = parts[NODE_PARTS[node]].BoundingBox()
            for index, (axis, coordinate) in enumerate(zip(axes, row["point_mm"])):
                low = getattr(bounds, f"{axis}min")
                high = getattr(bounds, f"{axis}max")
                assert low - 1e-6 <= coordinate <= high + 1e-6
                if index == normal_index:
                    assert min(abs(coordinate - low), abs(coordinate - high)) < 1e-6


def test_contact_cells_cover_exact_net_face_overlap_and_exclude_bores():
    for edge, cells in CONTACT_CELLS.items():
        assert len(cells) == 4
        assert sum(cell["tributary_area_mm2"] for cell in cells) == pytest.approx(
            cells[0]["net_overlap_area_mm2"], abs=1e-5
        )
        assert all(cell["inside_both_true_faces"] for cell in cells)
        assert all(cell["outside_all_bore_footprints"] for cell in cells)
        rows = [
            row
            for row in constraint_rows(closed=(edge,))
            if row["kind"] == "contact_compression"
        ]
        assert [row["point_mm"] for row in rows] == [cell["point_mm"] for cell in cells]
        assert [row["tributary_area_mm2"] for row in rows] == [
            cell["tributary_area_mm2"] for cell in cells
        ]


@pytest.mark.parametrize("resolution", [2, 4, 8])
def test_contact_partition_refines_deterministically_and_preserves_first_moments(
    resolution,
):
    first_cells, first = contact_partition(resolution)
    second_cells, second = contact_partition((resolution, resolution))

    assert first == second
    assert first_cells == second_cells
    assert first["grid_resolution"] == [resolution, resolution]
    assert len(first["fingerprint"]) == 64
    assert first["contact_row_count"] == sum(map(len, first_cells.values()))
    for edge, cells in first_cells.items():
        interface = first["interfaces"][edge]
        area = sum(cell["tributary_area_mm2"] for cell in cells)
        first_moment = sum(
            (
                cell["tributary_area_mm2"] * np.asarray(cell["point_mm"])
                for cell in cells
            ),
            np.zeros(3),
        )
        assert area == pytest.approx(interface["net_overlap_area_mm2"], abs=1e-5)
        np.testing.assert_allclose(
            first_moment,
            interface["net_first_moment_mm3"],
            atol=1e-4,
        )
        assert all(cell["inside_both_true_faces"] for cell in cells)
        assert all(cell["outside_all_bore_footprints"] for cell in cells)

    if resolution == 2:
        assert first == CONTACT_PARTITION
    else:
        assert first["fingerprint"] != CONTACT_PARTITION["fingerprint"]
        assert first["contact_row_count"] > CONTACT_PARTITION["contact_row_count"]


def test_contact_partition_fingerprint_binds_member_ownership_and_normal():
    interfaces = copy.deepcopy(CONTACT_PARTITION["interfaces"])
    interfaces["post_block"]["canonical_first_to_second_normal"] = [-1, 0, 0]

    changed = _partition_fingerprint((2, 2), CONTACT_CELLS, interfaces)

    assert changed != CONTACT_PARTITION["fingerprint"]
