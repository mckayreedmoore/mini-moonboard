from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts.wood_joint_wj12_backer_statics import build_report
from scripts.wood_joint_wj12_compositor import TRIAL_ID, CandidateBore

ROOT = Path(__file__).resolve().parents[1]


def _fingerprint(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _cut_holes(shape: cq.Shape, points: tuple[tuple[float, float], ...]) -> cq.Shape:
    for x, y in points:
        shape = shape.cut(
            cq.Solid.makeCylinder(3.65, 10.0, cq.Vector(x, y, 0.0), cq.Vector(0, 0, 1))
        )
    return shape.clean()


def _geometry(
    *,
    missing_left_first_annulus: bool = False,
    with_irrelevant_counterbore_floor: bool = False,
):
    left_points = ((-35.0, -97.0), (-35.0, -63.0))
    right_points = ((41.0, -98.0), (25.0, -76.0))
    left_id = "inner_kicker_backer_left"
    right_id = "inner_kicker_backer_right"
    header = cq.Solid.makeBox(
        177.8,
        88.9,
        10.0,
        cq.Vector(-90.4875, -124.9, 10.0),
    )
    header = _cut_holes(header, (*left_points, *right_points)).clean()
    backers = {
        left_id: _cut_holes(
            cq.Solid.makeBox(
                88.9,
                88.9,
                10.0,
                cq.Vector(-90.4875, -124.9, 0.0),
            ),
            left_points,
        ),
        right_id: _cut_holes(
            cq.Solid.makeBox(
                88.9,
                88.9,
                10.0,
                cq.Vector(-1.5875, -124.9, 0.0),
            ),
            right_points,
        ),
    }
    if missing_left_first_annulus:
        x, y = left_points[0]
        backers[left_id] = backers[left_id].cut(
            cq.Solid.makeCylinder(7.0, 10.0, cq.Vector(x, y, 0.0), cq.Vector(0, 0, 1))
        ).clean()
    if with_irrelevant_counterbore_floor:
        x, y = left_points[0]
        backers[left_id] = backers[left_id].cut(
            cq.Solid.makeCylinder(8.0, 3.0, cq.Vector(x, y, 0.0), cq.Vector(0, 0, 1))
        ).clean()
    candidate_bores = {}
    installed = {}
    for side, points in (("left", left_points), ("right", right_points)):
        part_id = f"inner_kicker_backer_{side}"
        for index, (x, y) in enumerate(points, start=1):
            axis_id = f"backer_header_{side}_{index}"
            cylinder = cq.Solid.makeCylinder(
                3.65, 20.0, cq.Vector(x, y, 0.0), cq.Vector(0, 0, 1)
            )
            candidate_bores[axis_id] = CandidateBore(
                axis_id=axis_id,
                family="wj05_backer",
                trial_id="trial-wj05-backers",
                receiver_ids=(part_id, "base_header"),
                shape=cylinder,
                station_id=f"wj05_backer_{side}",
            )
            installed[axis_id] = {"shaft": cylinder}

    family_paths = {
        "wj03_compact_outer": "scripts/wood_joint_wj03_compact_outer_access.py",
        "right_rail_integration": "scripts/wood_joint_right_rail_integration.py",
        "wj04_upper_g7": "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
        "wj06_outer_pair": "scripts/wood_joint_wj06_outer_pair_probe.py",
        "center_x190": "scripts/wood_joint_wj05_center_post_x190_probe.py",
    }
    family_fingerprints = {
        name: {path: _fingerprint(path)} for name, path in family_paths.items()
    }
    inventory_hash = "a" * 64
    return SimpleNamespace(
        trial_id=TRIAL_ID,
        status="unaccepted_integrated_hypothesis",
        source_inventory={"source_commit": "synthetic-source", "candidate": "test"},
        source_inventory_sha256=inventory_hash,
        source_binding=SimpleNamespace(
            inventory_sha256=inventory_hash,
            runtime_module_sha256={"test_source_module.py": "b" * 64},
        ),
        family_source_fingerprints=family_fingerprints,
        family_trial_ids={
            **{name: f"trial-{name}" for name in family_paths},
            "wj05_backer": "trial-wj05-backers",
        },
        finished_candidate_parts=backers,
        finished_hosts={"base_header": header},
        candidate_bores=candidate_bores,
        candidate_installed_hardware=installed,
    )


def _cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _add(first, second):
    return tuple(a + b for a, b in zip(first, second, strict=True))


def _sub(first, second):
    return tuple(a - b for a, b in zip(first, second, strict=True))


def _dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def _norm(vector):
    return sum(item * item for item in vector) ** 0.5


def test_wj12_backer_report_derives_asymmetric_geometry_and_finite_patch_checks():
    report = build_report(_geometry())

    assert report["claim_boundary"]["historical_surrogate_backer_demand_used"] is False
    assert report["claim_boundary"]["fresh_native_solve_performed"] is False
    assert report["gates"]["release"] is False
    assert report["gates"]["real_backer_demands_available"] is False
    assert report["source_provenance"]["source_inventory_matches_binding"]
    assert report["source_provenance"]["all_family_producers_bound_and_current"]

    left = report["backers"]["left"]
    right = report["backers"]["right"]
    assert [
        item["axis_id"] for item in left["bolt_points_projected_to_actual_contact_plane"]
    ] == ["backer_header_left_1", "backer_header_left_2"]
    left_points = [
        item["point_global_xyz_mm"]
        for item in left["bolt_points_projected_to_actual_contact_plane"]
    ]
    assert left_points[0] == pytest.approx((-35.0, -97.0, 10.0))
    assert left_points[1] == pytest.approx((-35.0, -63.0, 10.0))
    assert [
        item["axis_id"] for item in right["bolt_points_projected_to_actual_contact_plane"]
    ] == ["backer_header_right_1", "backer_header_right_2"]
    right_points = [
        item["point_global_xyz_mm"]
        for item in right["bolt_points_projected_to_actual_contact_plane"]
    ]
    assert right_points[0] == pytest.approx((41.0, -98.0, 10.0))
    assert right_points[1] == pytest.approx((25.0, -76.0, 10.0))
    assert left["bolt_row_axis_global_xyz"] == pytest.approx((0.0, 1.0, 0.0))
    assert right["bolt_row_axis_global_xyz"] != pytest.approx(left["bolt_row_axis_global_xyz"])
    assert left["contact_face_geometry"]["ray_distance_method"].startswith(
        "intersection with actual backer contact-face outer-wire polygon"
    )
    assert all(
        item["fully_contained_in_both_finished_faces"]
        for side in report["backers"].values()
        for item in side["finite_contact_patch_checks"]["annular_bore_patches"]
    )


def test_unrelated_circular_counterbore_floor_does_not_block_contact_face_search():
    report = build_report(_geometry(with_irrelevant_counterbore_floor=True))

    assert report["backers"]["left"]["contact_face_geometry"][
        "opposed_coplanar_face_delta_mm"
    ] == pytest.approx(0.0)
    assert report["backers"]["left"]["finite_contact_patch_checks"][
        "all_annuli_inside_both_finished_faces"
    ]
    assert all(
        item["fully_contained_in_both_finished_faces"]
        for side in report["backers"].values()
        for item in side["finite_contact_patch_checks"]["edge_moment_patches"].values()
    )


@pytest.mark.parametrize("side_name", ("left", "right"))
def test_wj12_signed_unit_wrench_reactions_close_independently(side_name):
    row = build_report(_geometry())["backers"][side_name]
    points = tuple(
        point_row["point_global_xyz_mm"]
        for point_row in row["bolt_points_projected_to_actual_contact_plane"]
    )
    center = row["group_centroid_global_xyz_mm"]
    cases = row["unit_wrench_cases"]
    assert len(cases) == 12
    assert len({case["case_id"] for case in cases}) == 12

    for case in cases:
        witness = case["finite_contact_witness"]
        reactions = witness["bolt_reaction_resultants_global_xyz_n"]
        assert len(reactions) == 2
        force_sum = _add(*reactions)
        moment_sum = _add(
            _cross(_sub(points[0], center), reactions[0]),
            _cross(_sub(points[1], center), reactions[1]),
        )
        for contact in witness["contact_reaction_resultants"]:
            force = contact["reaction_global_xyz_n"]
            point = contact["point_global_xyz_mm"]
            force_sum = _add(force_sum, force)
            moment_sum = _add(moment_sum, _cross(_sub(point, center), force))
        external_force = case["load_force_global_xyz_n"]
        external_moment = case["load_moment_at_group_centroid_global_xyz_nmm"]
        assert _norm(_add(external_force, force_sum)) < 1.0e-8
        assert _norm(_add(external_moment, moment_sum)) < 1.0e-8
        assert witness["equilibrium_witness_closes"] is True
        assert witness["bolt_tension_capacity_established"] is False
        assert witness["idealized_bolt_bearing_support_established"] is False


def test_two_point_baseline_leaves_only_the_signed_moment_parallel_to_actual_row_unresolved():
    report = build_report(_geometry())
    for side in report["backers"].values():
        row_axis = side["bolt_row_axis_global_xyz"]
        for case in side["unit_wrench_cases"]:
            baseline = case["point_fastener_baseline"]
            moment_residual = baseline["moment_equilibrium_residual_global_xyz_nmm"]
            expected = tuple(
                component
                * _dot(case["load_moment_at_group_centroid_global_xyz_nmm"], row_axis)
                for component in row_axis
            )
            assert moment_residual == pytest.approx(expected)
            assert baseline["force_residual_norm_n"] < 1.0e-8
            assert _norm(_sub(moment_residual, expected)) < 1.0e-8


def test_missing_annulus_fails_finite_witness_even_when_point_force_sum_closes():
    report = build_report(_geometry(missing_left_first_annulus=True))
    left = report["backers"]["left"]
    case = next(
        row for row in left["unit_wrench_cases"] if row["case_id"] == "unit_force_Z_plus"
    )
    witness = case["finite_contact_witness"]

    assert witness["algebraic_equilibrium_closes"] is True
    assert witness["equilibrium_witness_closes"] is False
    assert witness["unilateral_bolt_tension_and_contact_compression_signs_valid"] is False
    assert witness["unresolved_support_components"] == (
        {
            "component": "bolt_1_axial_compression",
            "reason": "finite annular patch does not fit both finished contact faces",
        },
    )
    assert report["gates"]["all_finite_unit_wrench_equilibrium_witnesses_close"] is False
    assert report["gates"]["release"] is False


def test_wj12_backer_geometry_rejects_missing_bore_instead_of_mirroring_or_guessing():
    geometry = _geometry()
    del geometry.candidate_bores["backer_header_right_2"]

    with pytest.raises(ValueError, match="right backer must have exactly its two declared candidate bores"):
        build_report(geometry)
