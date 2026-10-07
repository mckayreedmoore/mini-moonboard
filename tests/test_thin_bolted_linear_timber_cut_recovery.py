"""One synthetic face-table seam coupon; no candidate admission or solve."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from scripts import thin_bolted_timber_common_shaft_checks as common


def test_linear_face_contact_enters_both_own_cuts_once_without_alias_double_count():
    # A common reference face point lies off both grain-parallel centerlines.
    # Compression pushes the first timber toward -Y and the second toward +Y.
    # This first-order coupon has zero point couples and zero selfweight.
    face = {
        "id": "synthetic-paired-face/cell0",
        "kind": "timber_face_contact",
        "first": "first-timber",
        "second": "second-timber",
        "point_xyz_mm": [25., 20., 10.],
        "force_on_first_xyz_n": [0., -120., 0.],
        "moment_at_point_model_xyz_nmm": [0., 0., 0.],
    }
    field = {
        "common_shaft_bearing_actions": [],
        "shaft_end_capture_actions": [],
        "panel_screw_actions": [],
        "contact_actions": [face],
        "timber_face_contact_actions": [copy.deepcopy(face)],
        "floor_actions": [],
        "body_applied_loads": [],
    }
    own, gravity = common.member_point_inputs(field)
    assert gravity == {}
    assert set(own) == {"first-timber", "second-timber"}
    assert len(own["first-timber"]) == len(own["second-timber"]) == 1
    assert own["first-timber"] == [([25., 20., 10.], [0., -120., 0.], [0., 0., 0.])]
    assert own["second-timber"] == [([25., 20., 10.], [0., 120., 0.], [0., 0., 0.])]

    cuts = []
    for member, center, expected_force, expected_moment in (
        ("first-timber", [50., 0., 0.], [0., 120., 0.], [-1200., 0., -3000.]),
        ("second-timber", [50., 40., 0.], [0., -120., 0.], [1200., 0., 3000.]),
    ):
        # At x=20 the face at x=25 lies outside the lower-material portion.
        before = common.previous.member_cut_wrench(
            [1., 0., 0.], 0., 100., [20., center[1], 0.], center,
            [0., 0., 0.], own[member],
        )
        assert before["force_on_lower_portion_xyz_n"] == pytest.approx([0., 0., 0.])
        assert before["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx([0., 0., 0.])
        cut = common.previous.member_cut_wrench(
            [1., 0., 0.], 0., 100., center, center, [0., 0., 0.], own[member],
        )
        # Hand equilibrium: cut F=-Fface and cut M=-(pface-pcut) x Fface.
        assert cut["force_on_lower_portion_xyz_n"] == pytest.approx(expected_force)
        assert cut["moment_on_lower_portion_about_cut_xyz_nmm"] == pytest.approx(expected_moment)
        assert cut["axial_tension_positive_n"] == pytest.approx(0.)
        cuts.append(cut)

    assert np.sum([cut["force_on_lower_portion_xyz_n"] for cut in cuts], axis=0) == pytest.approx([0., 0., 0.])
    common_datum_moments = [
        np.asarray(cut["moment_on_lower_portion_about_cut_xyz_nmm"])
        + np.cross(cut["cut_point_xyz_mm"], cut["force_on_lower_portion_xyz_n"])
        for cut in cuts
    ]
    assert np.sum(common_datum_moments, axis=0) == pytest.approx([0., 0., 0.])
