"""Synthetic finite-patch clipping and signed nodal-load checks."""

from dataclasses import replace

import pytest

from fea.wood_joint_patch_load_patch import (
    InterfacePatchBinding,
    MeshTopology,
    Tri6Surface,
    distribute_case_on_resolved_patch,
    resolve_interface_load_patch,
)
from fea.wood_joint_patch_unit_cases import (
    EXPECTED_OWNER_PAIRS,
    distribute_unit_case_to_nodes,
    load_wj16_unit_case_plan,
)
from fea.wood_joint_patch_wrench import is_equilibrated

PLAN = load_wj16_unit_case_plan()
INTERFACE_ID = next(iter(EXPECTED_OWNER_PAIRS))
OWNER_HOST, OWNER_CLEAT = EXPECTED_OWNER_PAIRS[INTERFACE_ID]
DATUM = next(
    row.point_xyz_mm
    for row in PLAN.interface_datums
    if row.interface_id == INTERFACE_ID
)


def _c3d10(start_node: int, corners):
    edge_pairs = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
    points = list(corners)
    points.extend(
        tuple((corners[first][axis] + corners[second][axis]) / 2.0 for axis in range(3))
        for first, second in edge_pairs
    )
    node_ids = tuple(range(start_node, start_node + 10))
    return dict(zip(node_ids, points, strict=True)), node_ids


def _synthetic_interface():
    ox, oy, oz = DATUM
    host_corners = (
        (ox, oy, oz),
        (ox + 4.0, oy, oz),
        (ox, oy + 4.0, oz),
        (ox, oy, oz + 1.0),
    )
    cleat_corners = (
        (ox + 0.5, oy + 0.5, oz),
        (ox + 2.5, oy + 0.5, oz),
        (ox + 0.5, oy + 2.5, oz),
        (ox + 1.0, oy + 1.0, oz - 1.0),
    )
    host_nodes, host_connectivity = _c3d10(1, host_corners)
    cleat_nodes, cleat_connectivity = _c3d10(11, cleat_corners)
    nodes = {**host_nodes, **cleat_nodes}
    mesh = MeshTopology(
        node_xyz_mm=nodes,
        elements_by_owner={
            OWNER_HOST: {1: host_connectivity},
            OWNER_CLEAT: {2: cleat_connectivity},
        },
        owner_node_ids={
            OWNER_HOST: host_connectivity,
            OWNER_CLEAT: cleat_connectivity,
        },
    )
    host_face_nodes = tuple(host_connectivity[index] for index in (0, 1, 2, 4, 5, 6))
    cleat_face_nodes = tuple(cleat_connectivity[index] for index in (0, 1, 2, 4, 5, 6))
    host = Tri6Surface(OWNER_HOST, ((1, 1),), host_face_nodes, (0.0, 0.0, -1.0), "host")
    cleat = Tri6Surface(
        OWNER_CLEAT, ((2, 1),), cleat_face_nodes, (0.0, 0.0, 1.0), "cleat"
    )
    binding = InterfacePatchBinding(
        INTERFACE_ID,
        DATUM,
        2.0,
        host,
        cleat,
        (("synthetic_mesh", "no-source-hash"),),
    )
    return mesh, binding


def _resolved_patch():
    mesh, binding = _synthetic_interface()
    return resolve_interface_load_patch(binding, mesh, subdivisions=4), mesh, binding


def test_synthetic_finite_overlap_retains_owned_area_weights_and_rank_six_patches():
    patch, _mesh, _binding = _resolved_patch()
    overlay = patch.overlay

    assert overlay.host_surface_area_mm2 == pytest.approx(8.0)
    assert overlay.candidate_surface_area_mm2 == pytest.approx(2.0)
    assert overlay.common_area_mm2 == pytest.approx(2.0)
    assert overlay.common_centroid_xyz_mm == pytest.approx(
        (DATUM[0] + 7.0 / 6.0, DATUM[1] + 7.0 / 6.0, DATUM[2])
    )
    for side in (overlay.host_patch, overlay.candidate_patch):
        assert len(side.node_weights) == 6
        assert len({row.node_id for row in side.node_weights}) == 6
        assert all(row.tributary_area_mm2 > 0.0 for row in side.node_weights)
        assert sum(
            row.tributary_area_mm2 for row in side.node_weights
        ) == pytest.approx(overlay.common_area_mm2)
        assert side.nodal_area_centroid_xyz_mm == pytest.approx(
            overlay.common_centroid_xyz_mm
        )
        assert side.scaled_gram_relative_pivot > 1e-12


def test_six_signed_force_and_moment_cases_reconstruct_on_both_finite_patches():
    patch, _mesh, _binding = _resolved_patch()
    cases = [case for case in PLAN.cases if case.interface_id == INTERFACE_ID]

    assert len(cases) == 12
    for case in cases:
        distributed = distribute_case_on_resolved_patch(case, patch)
        assert distributed.action_reaction_check.passed
        assert distributed.action_reaction_check.owner_bodies == case.owner_bodies
        assert len(distributed.owner_distributions) == 2
        for owner_distribution, side in zip(
            distributed.owner_distributions,
            (patch.overlay.host_patch, patch.overlay.candidate_patch),
            strict=True,
        ):
            assert owner_distribution.owner_body == side.owner_body
            assert len(owner_distribution.nodal_forces) == len(side.node_weights)
            assert [row.node_id for row in owner_distribution.nodal_forces] == [
                row.node_id for row in side.node_weights
            ]
            assert [
                row.tributary_area_mm2 for row in owner_distribution.nodal_forces
            ] == [row.tributary_area_mm2 for row in side.node_weights]
            assert (
                owner_distribution.reconstructed_wrench_global.force_n
                == pytest.approx(
                    owner_distribution.target_wrench_global.force_n, abs=1e-9
                )
            )
            assert (
                owner_distribution.reconstructed_wrench_global.moment_nmm
                == pytest.approx(
                    owner_distribution.target_wrench_global.moment_nmm, abs=1e-8
                )
            )
            assert is_equilibrated(owner_distribution.residual_global)
            assert owner_distribution.scaled_gram_relative_pivot > 1e-12


def test_patch_rejects_incomplete_surface_node_ownership():
    mesh, binding = _synthetic_interface()
    incomplete_surface = replace(
        binding.host_surface,
        tri6_node_ids=binding.host_surface.tri6_node_ids[:-1],
    )
    incomplete_binding = replace(binding, host_surface=incomplete_surface)

    with pytest.raises(ValueError, match="exact TRI6 face union"):
        resolve_interface_load_patch(incomplete_binding, mesh, subdivisions=4)


def test_case_adapter_rejects_foreign_or_incomplete_owner_patches():
    patch, _mesh, _binding = _resolved_patch()
    case = next(case for case in PLAN.cases if case.interface_id == INTERFACE_ID)
    wrong_owner_case = replace(case, cleat_body="unowned-cleat")

    with pytest.raises(ValueError, match="owner/moment references"):
        distribute_case_on_resolved_patch(wrong_owner_case, patch)

    with pytest.raises(ValueError, match="owners must match exactly"):
        distribute_unit_case_to_nodes(
            case,
            {OWNER_HOST: patch.overlay.host_patch.node_weights},
        )


def test_case_adapter_rejects_mislabeled_or_foreign_surface_nodes():
    patch, _mesh, _binding = _resolved_patch()
    case = next(case for case in PLAN.cases if case.interface_id == INTERFACE_ID)
    mislabeled_host = replace(patch.overlay.host_patch, owner_body=OWNER_CLEAT)
    mislabeled_overlay = replace(patch.overlay, host_patch=mislabeled_host)

    with pytest.raises(ValueError, match="owner labels"):
        distribute_case_on_resolved_patch(
            case, replace(patch, overlay=mislabeled_overlay)
        )

    foreign_node = patch.overlay.candidate_patch.node_weights[0]
    host_weights = (foreign_node, *patch.overlay.host_patch.node_weights[1:])
    foreign_node_host = replace(
        patch.overlay.host_patch,
        node_weights=host_weights,
    )
    foreign_node_overlay = replace(patch.overlay, host_patch=foreign_node_host)

    with pytest.raises(ValueError, match="source-surface ownership"):
        distribute_case_on_resolved_patch(
            case, replace(patch, overlay=foreign_node_overlay)
        )
