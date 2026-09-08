import numpy as np
import pytest

from fea.three_member_connector import stiffness


def test_rigid_motion_equilibrium_and_energy():
    model = stiffness([38.1, 19.05, 19.05], [100, 80, 80], 3e7)
    k, centres = model["member_stiffness"], model["member_centres_mm"]
    assert np.max(abs(k-k.T)) < 1e-7
    translation = np.array([1, 0, 1, 0, 1, 0])
    rotation = np.column_stack((centres, np.ones(3))).ravel()
    assert np.max(abs(k@translation)) < 1e-6
    assert np.max(abs(k@rotation)) < 1e-5
    eigenvalues = np.linalg.eigvalsh(k)
    assert eigenvalues[0] > -1e-6 and eigenvalues[2] > 0
    motion = np.array([0., .002, .5, -.003, -.2, .004])
    force = k@motion
    assert abs(sum(force[::2])) < 1e-6
    assert abs(sum(force[1::2]+centres*force[::2])) < 1e-5
    bolt = model["bolt_recovery"]@motion
    full = np.r_[bolt, motion]
    assert np.max(abs((model["full_stiffness"]@full)[:len(bolt)])) < 1e-6
    assert full@model["full_stiffness"]@full == pytest.approx(motion@force, rel=1e-8)
    assert motion@force > 0


def test_rigid_bolt_limit_against_independent_integrals():
    # Independent affine-bolt least-squares energy, integrated in closed form.
    lengths, foundations = np.array([2., 1., 1.]), np.array([3., 4., 5.])
    centres = np.array([1., 2.5, 3.5])
    a, b, d = np.zeros((2, 2)), np.zeros((2, 6)), np.zeros((6, 6))
    for i, (length, foundation, centre) in enumerate(zip(lengths, foundations, centres, strict=True)):
        mass, moment = foundation*length, foundation*length**3/12
        a += np.array([[mass, mass*centre], [mass*centre, mass*centre**2+moment]])
        b[:, 2*i:2*i+2] = [[mass, 0], [mass*centre, moment]]
        d[2*i, 2*i], d[2*i+1, 2*i+1] = mass, moment
    expected = d-b.T@np.linalg.solve(a, b)
    actual = stiffness(lengths, foundations, 1e7, subdivisions=1)["member_stiffness"]
    assert np.max(abs(actual-expected)) < 2e-5


def test_mesh_refinement_and_invalid_inputs():
    matrices = [stiffness([38.1, 19.05, 19.05], [100, 80, 80], 3e7, n)["member_stiffness"]
                for n in (4, 8, 16)]
    assert np.linalg.norm(matrices[2]-matrices[1]) < np.linalg.norm(matrices[1]-matrices[0])
    assert np.linalg.norm(matrices[2]-matrices[1])/np.linalg.norm(matrices[2]) < 1e-5
    for lengths, foundation, ei, n in (([1, 1], [1, 1, 1], 1, 2),
        ([1, 0, 1], [1, 1, 1], 1, 2), ([1, 1, 1], [1, np.nan, 1], 1, 2),
        ([1, 1, 1], [1, 1, 1], 0, 2), ([1, 1, 1], [1, 1, 1], 1, True)):
        with pytest.raises(ValueError):
            stiffness(lengths, foundation, ei, n)
