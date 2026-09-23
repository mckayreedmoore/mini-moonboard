"""Exact net-face cells for retained frame-bolt interfaces."""

from collections import defaultdict
from math import pi

import numpy as np
import pytest

from fea.floor_flush_run import face_contacts
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_native_preparation import IntegratedBarrelNative
from scripts.owner_barrel_retained_interfaces import (
    RetainedFacePose,
    retained_contact_rows,
    retained_interface_point,
)


def test_right_rim_leg_interfaces_follow_current_kerf_right_face():
    assembly = build_integrated_viewer_assembly()
    baseline = variant(KERF_RIGHT)
    rim = assembly["wood"]["base_side_right"].BoundingBox()
    leg = assembly["wood"]["lumber_leg_right"].BoundingBox()
    assert rim.xmax == pytest.approx(leg.xmin, abs=1e-6)
    for bolt in assembly["frame_connections"]:
        if bolt.name.startswith("lumber_leg_bolt_right_"):
            old = baseline.bolt_interface_point(bolt)
            current = retained_interface_point(assembly, baseline, bolt)
            assert old.x - current.x == pytest.approx(3.175, abs=1e-6)
            assert current.x == pytest.approx(rim.xmax, abs=1e-6)
        else:
            assert retained_interface_point(assembly, baseline, bolt).toTuple() == (
                pytest.approx(baseline.bolt_interface_point(bolt).toTuple())
            )


@pytest.fixture(scope="module")
def retained_faces():
    module = IntegratedBarrelNative()
    baseline = variant(KERF_RIGHT)
    rows = retained_contact_rows(module.assembly, baseline, stiffness_per_area=100.0)
    return module, baseline, rows


def test_retained_cells_keep_six_faces_and_twelve_exact_regions(retained_faces):
    _, _, rows = retained_faces
    groups = defaultdict(list)
    for row in rows:
        groups[(row["first"], row["second"])].append(row)

    assert len(rows) == 72
    assert len(groups) == 6
    assert {len(group) for group in groups.values()} == {12}
    assert all(row["exact_cut_cell_area_and_centroid"] for row in rows)
    assert all(row["tributary_area_mm2"] > 0 for row in rows)
    assert all(
        row["stiffness_n_per_mm"]
        == pytest.approx(100.0 * row["tributary_area_mm2"])
        for row in rows
    )


def test_retained_cells_preserve_exact_net_area_and_first_moments(retained_faces):
    module, baseline, rows = retained_faces
    exact_groups = defaultdict(list)
    for row in rows:
        exact_groups[(row["first"], row["second"])].append(row)

    # Legacy quadrature exactly integrates gross-face first moments, but its
    # uniform bore deduction does not.  Reconstruct gross moments, then deduct
    # each circular bore at its own centre as an independent expected value.
    old_rows = face_contacts(
        RetainedFacePose(module.assembly, baseline), stiffness_per_area=1.0
    )
    old_groups = defaultdict(list)
    for row in old_rows:
        old_groups[(row["first"], row["second"])].append(row)
    bolt_groups = defaultdict(list)
    for bolt in baseline.connections():
        if bolt.kind == "bolt":
            bolt_groups[bolt.members].append(bolt)

    for members, group in exact_groups.items():
        gross_area = sum(row["gross_tributary_area_mm2"] for row in group)
        bore_area = sum(
            pi * (baseline.bolt_dimensions(bolt)["hole_diameter_mm"] / 2) ** 2
            for bolt in bolt_groups[members]
        )
        net_area = sum(row["tributary_area_mm2"] for row in group)
        assert net_area == pytest.approx(gross_area - bore_area, abs=1.0e-5)

        legacy_net_area = sum(
            row["tributary_area_mm2"] for row in old_groups[members]
        )
        gross_scale = gross_area / legacy_net_area
        gross_moment = sum(
            (
                gross_scale
                * row["tributary_area_mm2"]
                * np.asarray(row["point_xyz_mm"])
                for row in old_groups[members]
            ),
            np.zeros(3),
        )
        bore_moment = np.zeros(3)
        for bolt in bolt_groups[members]:
            area = pi * (baseline.bolt_dimensions(bolt)["hole_diameter_mm"] / 2) ** 2
            interface_x = group[0]["point_xyz_mm"][0]
            bore_moment += area * np.asarray(
                [interface_x, bolt.start.y, bolt.start.z]
            )
        exact_moment = sum(
            (
                row["tributary_area_mm2"] * np.asarray(row["point_xyz_mm"])
                for row in group
            ),
            np.zeros(3),
        )
        np.testing.assert_allclose(exact_moment, gross_moment - bore_moment, atol=1.0e-4)


def test_retained_bore_deductions_are_local_and_centroids_avoid_bores(retained_faces):
    _, baseline, rows = retained_faces
    bolt_groups = defaultdict(list)
    for bolt in baseline.connections():
        if bolt.kind == "bolt":
            bolt_groups[bolt.members].append(bolt)

    deductions = []
    for row in rows:
        deductions.append(
            row["gross_tributary_area_mm2"] - row["tributary_area_mm2"]
        )
        point = np.asarray(row["point_xyz_mm"][1:])
        for bolt in bolt_groups[(row["first"], row["second"])]:
            radius = baseline.bolt_dimensions(bolt)["hole_diameter_mm"] / 2
            assert np.linalg.norm(point - [bolt.start.y, bolt.start.z]) > radius

    assert min(deductions) == pytest.approx(0.0, abs=1.0e-7)
    assert max(deductions) > 1.0


@pytest.mark.parametrize("stiffness", [0.0, -1.0, float("nan"), float("inf")])
def test_retained_cells_reject_invalid_stiffness(stiffness):
    with pytest.raises(ValueError, match="positive and finite"):
        retained_contact_rows(None, None, stiffness_per_area=stiffness)
