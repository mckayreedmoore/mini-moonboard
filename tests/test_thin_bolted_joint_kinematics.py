"""Known revolute-joint mechanisms independent of the climbing-frame layout."""

import numpy as np

from scripts.thin_bolted_joint_kinematics import hinge_matrix, rank_diagnostic


def joint(a, b, point, axis):
    return {"first": a, "second": b, "point_mm": point, "axis": axis}


def test_one_hinge_releases_only_rotation_about_its_shaft():
    matrix = hinge_matrix(["beam"], [joint("beam", "ground", [20, 0, 0], [0, 0, 1])], "ground", [20, 0, 0])
    assert rank_diagnostic(matrix)["rank"] == 5
    assert np.linalg.norm(matrix @ np.array([0, 0, 0, 0, 0, 100.])) < 1e-10
    assert np.linalg.norm(matrix @ np.array([0, 0, 0, 100., 0, 0])) > 1


def test_two_parallel_noncollinear_ground_hinges_lock_the_body():
    hinges = [joint("beam", "ground", [0, 0, 0], [0, 0, 1]),
              joint("beam", "ground", [40, 0, 0], [0, 0, 1])]
    assert rank_diagnostic(hinge_matrix(["beam"], hinges, "ground", [0, 0, 0]))["rank"] == 6


def test_two_points_on_one_shaft_do_not_remove_its_free_rotation():
    hinges = [joint("beam", "ground", [0, 0, 0], [0, 0, 1]),
              joint("beam", "ground", [0, 0, 40], [0, 0, 1])]
    assert rank_diagnostic(hinge_matrix(["beam"], hinges, "ground", [0, 0, 0]))["rank"] == 5


def test_single_rigid_angle_between_two_hinges_has_two_free_motions():
    hinges = [joint("beam", "angle", [84, 0, 0], [0, 0, 1]),
              joint("angle", "ground", [0, 68, 0], [1, 0, 0])]
    result = rank_diagnostic(hinge_matrix(["beam", "angle"], hinges, "ground", [0, 0, 0]))
    assert result["moving_body_variables"] == 12
    assert result["rank"] == 10
    assert result["isolated_joint_free_motions"] == 2


def test_opposed_rigid_angles_sharing_a_beam_shaft_retain_one_free_motion():
    hinges = [joint("beam", "first", [84, 0, -5], [0, 0, 1]),
              joint("beam", "second", [84, 0, 5], [0, 0, 1]),
              joint("first", "ground", [0, 68, 0], [1, 0, 0]),
              joint("second", "ground", [0, -20, 0], [1, 0, 0])]
    for scale in (10., 100., 1000.):
        result = rank_diagnostic(hinge_matrix(["beam", "first", "second"], hinges, "ground", [0, 0, 0], scale))
        assert result["rank"] == 17
        assert result["isolated_joint_free_motions"] == 1
