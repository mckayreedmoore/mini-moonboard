"""Analytic curved geometry only: no Gmsh, Docker, solver or real-leg run."""
import copy

import numpy as np
import pytest

from fea import leg_section_geometry as geometry
from fea.mortar_geometry_diagnostic import triangle_weights


def rule(order=4):
    """Independent tensor Gauss rule on the Duffy reference triangle."""
    x, w = np.polynomial.legendre.leggauss(order)
    x, w = (x+1)/2, w/2
    coordinates, weights = [], []
    for i, r in enumerate(x):
        for j, t in enumerate(x):
            coordinates.append((r, (1-r)*t))
            weights.append(w[i]*w[j]*(1-r))
    basis, gradient = [], []
    for r, s in coordinates:
        a = 1-r-s
        basis.append([a*(2*a-1), r*(2*r-1), s*(2*s-1), 4*a*r, 4*r*s, 4*s*a])
        gradient.append([[1-4*a, 1-4*a, 0], [4*r-1, 0, 0], [0, 4*s-1, 0],
                         [4*(a-r), -4*r, 0], [4*s, 4*r, 0], [-4*s, 4*(a-s), 0]])
    return np.array(basis), np.array(gradient), np.array(weights)


def tetra(alpha=.05):
    corners = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.)]
    mids = [(np.array(corners[i])+corners[j])/2 for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
    # Exact quadratic shear map (r,s,t)->(r,s,t+alpha*r²), detJ=1.
    nodes = {i+1: (x, y, z+alpha*x*x) for i, (x, y, z) in enumerate(corners+mids)}
    elements = {1: tuple(nodes)}
    faces = geometry.boundary(nodes, elements, {1})
    return np.array([[nodes[n] for n in face] for face in faces])


@pytest.mark.parametrize("alpha", [0., .05])
def test_closed_curved_tetra_matches_exact_volume_and_centroid(alpha):
    patches = tetra(alpha)
    low, high = [geometry.surface_integrals(patches, *rule(order)) for order in (4, 6)]
    assert low["area_vector"] == pytest.approx([0, 0, 0], abs=1e-14)
    assert low["volume"] == pytest.approx(1/6, abs=1e-14)
    centroid = np.array([1/4, 1/4, 1/4+alpha/10])
    assert low["first_moment"] == pytest.approx(centroid/6, abs=1e-14)
    reverse = geometry.surface_integrals(patches[:, (0, 2, 1, 5, 4, 3)], *rule())
    assert reverse["volume"] == pytest.approx(-1/6, abs=1e-14)
    # Scalar area is nonpolynomial; Duffy quadrature is not symmetric under
    # reversal. Its tiny integration difference is not an orientation failure.
    assert reverse["area"] == pytest.approx(low["area"], abs=1e-12)
    assert reverse["first_moment"] == pytest.approx(-centroid/6, abs=1e-14)
    result = geometry.assess(low, high, 1/6, centroid/6, 2., 0.)
    assert result["geometric_comparisons_within_gates"] and result["failures"] == {}
    assert low["minimum_sampled_surface_jacobian"] > 0
    # Existing independent TRI6 sampling reproduces the sheared patch map at
    # all vertices/midsides without modifying any frozen geometry helper.
    bary, sampled = triangle_weights(2)
    assert np.max(abs(sampled.sum(axis=1)-1)) == 0
    assert np.allclose((sampled @ patches[0])[0], patches[0][2])
    assert len(bary) == 6


@pytest.mark.parametrize("quantity", list(geometry.GATES)+["opposed_cut_area_relative"])
def test_each_declared_gate_reports_failure_without_changing_limits(quantity):
    low = geometry.surface_integrals(tetra(), *rule())
    high = copy.deepcopy(low)
    volume, moment, opposed = 1/6, np.array([.25, .25, .255])/6, 0.
    if quantity == "closed_area_relative":
        low["area_vector"][0] = 1.
    elif quantity == "volume_relative":
        volume *= 1.01
        moment *= 1.01
    elif quantity == "centroid_over_length":
        moment[0] += .01
    elif quantity == "area_quadrature_relative":
        high["area"] *= 1.01
    else:
        opposed = .01
    result = geometry.assess(low, high, volume, moment, 2., opposed)
    assert not result["geometric_comparisons_within_gates"]
    assert set(result["failures"]) == {quantity}


@pytest.mark.parametrize("fault", ["collapsed", "nan", "folded"])
def test_surface_rejects_invalid_sampled_geometry(fault):
    patches = tetra()
    if fault == "collapsed":
        patches[:] = 0
    elif fault == "nan":
        patches[0, 0, 0] = np.nan
    else:
        patches[0, 3] = patches[0, 0] + 5*(patches[0, 0]-patches[0, 1])
    with pytest.raises(ValueError):
        geometry.surface_integrals(patches, *rule())


def test_native_rule_adapter_preserves_tri6_order():
    class Mesh:
        def getIntegrationPoints(self, kind, rule):
            assert (kind, rule) == (9, "Gauss8")
            return [0., 0., 0.], [.5]
        def getBasisFunctions(self, kind, points, label):
            assert kind == 9 and points == [0., 0., 0.]
            return (1, list(range(6)), 1) if label == "Lagrange" else (3, list(range(18)), 1)
    class Model:
        mesh = Mesh()
    class Gmsh:
        model = Model()
    basis, gradient, weights = geometry.native_rule(Gmsh(), 8)
    assert basis.tolist() == [[0, 1, 2, 3, 4, 5]]
    assert gradient.shape == (1, 6, 3) and gradient[0, 5].tolist() == [15, 16, 17]
    assert weights.tolist() == [.5]


@pytest.mark.parametrize("opposed", [float("nan"), float("inf"), -1.])
def test_invalid_opposed_residual_cannot_pass(opposed):
    surface = geometry.surface_integrals(tetra(), *rule())
    with pytest.raises(ValueError, match="opposed-cut residual"):
        geometry.assess(surface, surface, 1/6, np.array([.25, .25, .255])/6, 2., opposed)
