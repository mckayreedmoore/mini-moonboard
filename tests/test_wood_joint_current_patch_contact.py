"""Focused tests for the current-only C3D10 contact classifier."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from fea import wood_joint_current_patch_contact as contact
from fea.wood_joint_patch_load_patch import MeshTopology


def _tetra_topology() -> MeshTopology:
    nodes = {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (0.0, 1.0, 0.0),
        4: (0.0, 0.0, 1.0),
        5: (0.5, 0.0, 0.0),
        6: (0.5, 0.5, 0.0),
        7: (0.0, 0.5, 0.0),
        8: (0.0, 0.0, 0.5),
        9: (0.5, 0.0, 0.5),
        10: (0.0, 0.5, 0.5),
    }
    return MeshTopology(
        node_xyz_mm=nodes,
        elements_by_owner={"BODY": {1: tuple(range(1, 11))}},
        owner_node_ids={"BODY": tuple(nodes)},
    )


def _plane_row() -> dict[str, object]:
    return {
        "cad_type": "Plane",
        "cad_area_mm2": 0.5,
        "cad_centroid_global_xyz_mm": [1 / 3, 1 / 3, 0.0],
        "bounds_xyz_mm": [0.0, 1.0, 0.0, 1.0, 0.0, 0.0],
        "tri6_exterior_face_refs": [[1, 1]],
        "tri6_node_ids": [1, 2, 3, 5, 6, 7],
        "analytic_surface_parameters": {
            "surface_type": "Plane",
            "sample_point_global_xyz_mm": [0.0, 0.0, 0.0],
            # This is a parametric normal; its sign is not an outward claim.
            "sample_normal_global_xyz": [0.0, 0.0, 1.0],
        },
    }


def _source_face() -> dict[str, object]:
    return {
        "area_mm2": 0.5,
        "centroid_global_xyz_mm": [1 / 3, 1 / 3, 0.0],
        "bounds_xyz_mm": [0.0, 1.0, 0.0, 1.0, 0.0, 0.0],
        "normal_global_xyz": [0.0, 0.0, -1.0],
    }


def test_source_face_mapping_uses_full_bounds_and_not_common_patch_area() -> None:
    topology = _tetra_topology()
    row = {**_plane_row(), "_owner_mesh_id": "BODY"}
    source = _source_face()

    assert contact._face_surface_matches(row, source, topology)

    # A finite patch may occupy only part of its source face. The independent
    # patch area does not replace the full source-face metric used for binding.
    finite_overlap_area = 0.2
    assert finite_overlap_area < source["area_mm2"]
    row["bounds_xyz_mm"] = [0.0, 1.0, 0.0, 1.0, 0.1, 0.1]
    assert not contact._face_surface_matches(row, source, topology)


def test_c3d10_corner_order_reconstructs_outward_normal_and_checks_source_sign() -> (
    None
):
    topology = _tetra_topology()
    surface, audit = contact._tri6_surface(
        "BODY",
        "1",
        _plane_row(),
        topology,
        expected_normal=(0.0, 0.0, -1.0),
        expected_plane_point=(0.0, 0.0, 0.0),
    )

    assert surface.outward_normal_global_xyz == pytest.approx((0.0, 0.0, -1.0))
    assert audit["source_oriented_normal_alignment"] == pytest.approx(1.0)
    with pytest.raises(ValueError, match="oriented source face"):
        contact._tri6_surface(
            "BODY",
            "1",
            _plane_row(),
            topology,
            expected_normal=(0.0, 0.0, 1.0),
            expected_plane_point=(0.0, 0.0, 0.0),
        )


def test_cylinder_radial_direction_separates_internal_bore_from_solid_outer_wall(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    topology = MeshTopology(
        node_xyz_mm={node: (1.0, 0.0, float(node)) for node in range(1, 11)},
        elements_by_owner={"BODY": {1: tuple(range(1, 11))}},
        owner_node_ids={"BODY": tuple(range(1, 11))},
    )
    # Choose a radial point at +X on a cylinder parallel to global Z. The
    # reconstructed element-outward normal determines whether it is a hole.
    monkeypatch.setattr(
        contact,
        "_face_normal_and_points",
        lambda *_args, **_kwargs: (
            (1.0, 0.0, 0.0),
            (1, 2, 5, 8, 9, 10),
            (),
        ),
    )
    fit: Mapping[str, object] = {"point": (0.0, 0.0, 0.0)}
    row = {"tri6_exterior_face_refs": [[1, 1]]}

    outside_sign = contact._cylinder_radial_normal_sign(
        "BODY", row, fit, topology, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    )
    assert outside_sign == pytest.approx(1.0)

    monkeypatch.setattr(
        contact,
        "_face_normal_and_points",
        lambda *_args, **_kwargs: (
            (-1.0, 0.0, 0.0),
            (1, 2, 5, 8, 9, 10),
            (),
        ),
    )
    inside_sign = contact._cylinder_radial_normal_sign(
        "BODY", row, fit, topology, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    )
    assert inside_sign == pytest.approx(-1.0)


def test_overlay_payload_retains_nodal_centroid_residual_and_rank_checks() -> None:
    class PatchSide:
        class Weight:
            def __init__(self, area: float) -> None:
                self.tributary_area_mm2 = area

        node_weights = (Weight(6.0), Weight(6.0))
        nodal_centroid_error_mm = 0.00425031
        scaled_gram_relative_pivot = 1.0e-6

    class Overlay:
        common_area_mm2 = 12.0
        common_centroid_xyz_mm = (1.0, 2.0, 3.0)
        candidate_surface_area_mm2 = 15.0
        host_surface_area_mm2 = 18.0
        candidate_patch = PatchSide()
        host_patch = PatchSide()
        refinement_relative_change = 1e-5
        maximum_plane_residual_mm = 0.0
        maximum_normal_alignment_residual = 0.0

    payload = contact._overlay_payload(Overlay())
    assert payload["candidate_nodal_area_centroid_residual_mm"] == pytest.approx(
        0.00425031
    )
    assert payload["host_nodal_area_centroid_residual_mm"] == pytest.approx(0.00425031)
    assert payload["candidate_positive_area_sum_mm2"] == pytest.approx(12.0)
    assert payload["candidate_scaled_rank_six_pivot"] == pytest.approx(1e-6)
