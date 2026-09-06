import math
import shutil
import subprocess
from pathlib import Path

import pytest

from fea.dynamic_momentum import (
    calculix_221_quadrature,
    consistent_mass,
    mass_block,
    momentum,
)


def tetra(offset=(0, 0, 0)):
    corners = [(0,0,0), (1,0,0), (0,1,0), (0,0,1)]
    xyz = corners + [tuple((corners[a][i]+corners[b][i])/2 for i in range(3))
                     for a,b in ((0,1),(1,2),(2,0),(0,3),(1,3),(2,3))]
    return {n: tuple(x+o for x,o in zip(point, offset)) for n,point in enumerate(xyz, 1)}


def exact_block(density=1):
    # Independent analytical integration of barycentric monomials on unit tetra.
    basis = []
    for i in range(4):
        powers = [0]*4
        powers[i] = 1
        linear = tuple(powers)
        powers[i] = 2
        basis.append({linear: -1, tuple(powers): 2})
    for i,j in ((0,1),(1,2),(2,0),(0,3),(1,3),(2,3)):
        powers = [0]*4
        powers[i] = powers[j] = 1
        basis.append({tuple(powers): 4})
    def entry(left, right):
        return density*math.fsum(c*d*math.prod(math.factorial(a+b) for a,b in zip(p,q)) /
                                 math.factorial(3+sum(p)+sum(q))
                                 for p,c in left.items() for q,d in right.items())
    return tuple(tuple(entry(left,right) for right in basis) for left in basis)


def native_unit_block():
    points, weights = calculix_221_quadrature()
    basis = []
    for x,y,z in points:
        bary = (1-x-y-z, x, y, z)
        basis.append([v*(2*v-1) for v in bary] +
                     [4*bary[i]*bary[j] for i,j in ((0,1),(1,2),(2,0),(0,3),(1,3),(2,3))])
    return mass_block(basis, weights, [1]*4, 1)


def test_native_four_point_corner_velocity_is_not_exact_mass():
    nodes = tetra()
    zero = dict.fromkeys(nodes, (0,0,0))
    velocity = {**zero, 1:(1,0,0)}
    native = momentum(nodes, {1:(tuple(nodes),native_unit_block())}, zero, velocity)
    exact = momentum(nodes, {1:(tuple(nodes),exact_block())}, zero, velocity)
    assert native["kinetic_energy"] == pytest.approx(1/1200, rel=1e-12)
    assert exact["kinetic_energy"] == pytest.approx(1/840, rel=1e-12)
    assert native["kinetic_energy"]/exact["kinetic_energy"] == pytest.approx(.7)


def test_translation_and_shared_nodes():
    nodes = tetra()
    zero = dict.fromkeys(nodes, (0,0,0))
    velocity = dict.fromkeys(nodes, (2,-3,4))
    block = exact_block(6)
    result = momentum(nodes, {1:(tuple(nodes), block)}, zero, velocity)
    assert result["mass"] == pytest.approx(1)
    assert result["linear_momentum"] == pytest.approx((2,-3,4))
    assert result["angular_momentum"] == pytest.approx((7/4,-2/4,-5/4))
    assert result["kinetic_energy"] == pytest.approx(29/2)
    # Assembly must sum both incident element contributions at shared nodes.
    doubled = momentum(nodes, {1:(tuple(nodes),block), 2:(tuple(nodes),block)}, zero, velocity)
    for key,value in result.items():
        assert doubled[key] == pytest.approx(tuple(2*v for v in value) if isinstance(value,tuple) else 2*value)
    assert block[0] and sum(block[0]) < 0  # Consistent C3D10 is not positive row-lumping.


@pytest.mark.parametrize("offset", [(0,0,0), (2,3,4)])
def test_rotation_and_deformed_angular_momentum(offset):
    nodes, rho, omega = tetra(offset), 6, 3
    zero = dict.fromkeys(nodes, (0,0,0))
    velocity = {n:(-omega*y, omega*x, 0) for n,(x,y,z) in nodes.items()}
    blocks = {1:(tuple(nodes), exact_block(rho))}
    ox,oy,oz = offset
    x2 = ox*ox/6+ox/12+1/60
    y2 = oy*oy/6+oy/12+1/60
    zx = oz*ox/6+(oz+ox)/24+1/120
    zy = oz*oy/6+(oz+oy)/24+1/120
    expected_p = (-omega*(oy+.25), omega*(ox+.25), 0)
    expected_h = (-rho*omega*zx, -rho*omega*zy, rho*omega*(x2+y2))
    result = momentum(nodes, blocks, zero, velocity)
    assert result["linear_momentum"] == pytest.approx(expected_p)
    assert result["angular_momentum"] == pytest.approx(expected_h)
    assert result["kinetic_energy"] == pytest.approx(.5*rho*omega**2*(x2+y2))
    # X+u = 2X + (0,0,5); velocity and reference mass are unchanged.
    displacement = {n:(x,y,z+5) for n,(x,y,z) in nodes.items()}
    moved = momentum(nodes, blocks, displacement, velocity)
    assert moved["angular_momentum"] == pytest.approx((2*expected_h[0]-5*expected_p[1],
                                                       2*expected_h[1]+5*expected_p[0], 2*expected_h[2]))
    assert moved["kinetic_energy"] == result["kinetic_energy"]


@pytest.mark.parametrize("density", [0,-1,math.nan,math.inf])
def test_invalid_density(density):
    with pytest.raises(ValueError, match="density"):
        consistent_mass({1:tuple(range(1,11))}, tetra(), density)


def test_invalid_mesh_state_and_quadrature():
    nodes = tetra()
    elements = {1:tuple(nodes)}
    zero = dict.fromkeys(nodes, (0,0,0))
    blocks = {1:(tuple(nodes),exact_block())}
    with pytest.raises(ValueError, match="Incomplete"):
        momentum(nodes, blocks, zero, {1:(0,0,0)})
    with pytest.raises(ValueError, match="Incomplete"):
        momentum(nodes, blocks, {1:(0,0,0)}, zero)
    with pytest.raises(ValueError, match="Finite"):
        momentum(nodes, blocks, zero, {**zero, 2:(math.nan,0,0)})
    with pytest.raises(ValueError, match="Finite"):
        momentum(nodes, blocks, {**zero, 2:(0,math.inf,0)}, zero)
    with pytest.raises(ValueError, match="coordinates"):
        consistent_mass(elements, {**nodes, 1:(math.inf,0,0)}, 1)
    for bad in ({}, {1:(1,)*10}, {1:tuple(range(2,12))}):
        with pytest.raises(ValueError, match="connectivity"):
            consistent_mass(bad, nodes, 1)
    for determinant in (0,-1,math.nan,math.inf):
        with pytest.raises(ValueError, match="Jacobian"):
            mass_block([[.1]*10], [1/6], [determinant], 1)


def test_gmsh_straight_and_curved_tetra_in_immutable_image():
    image = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
    if not shutil.which("docker") or subprocess.run(["docker","image","inspect",image],
                                                    capture_output=True, check=False, timeout=10).returncode:
        pytest.skip("Immutable local Gmsh image required")
    # The analytical polynomial helper remains independent of Gmsh quadrature.
    code = '''
import runpy
from fea.dynamic_momentum import calculix_221_mass, consistent_mass, momentum
helpers = runpy.run_path('/work/tests/test_dynamic_momentum.py')
nodes = helpers['tetra']()
elements = {1:tuple(nodes)}
ids, block = consistent_mass(elements,nodes,6)[1]
exact = helpers['exact_block'](6)
assert max(abs(block[i][j]-exact[ids[i]-1][ids[j]-1]) for i in range(10) for j in range(10)) < 1e-12
native_ids, native = calculix_221_mass(elements,nodes,1)[1]
analytical_native = helpers['native_unit_block']()
assert max(abs(native[i][j]-analytical_native[native_ids[i]-1][native_ids[j]-1]) for i in range(10) for j in range(10)) < 1e-12
zero = dict.fromkeys(nodes, (0,0,0))
velocity = {**zero, 1:(1,0,0)}
ke = momentum(nodes,{1:(native_ids,native)},zero,velocity)['kinetic_energy']
assert abs(ke-1/1200) < 1e-12
nodes[5] = (.5,-.04,.02)
nodes[9] = (.52,.01,.55)
eight = consistent_mass(elements,nodes,6)[1][1]
ten = consistent_mass(elements,nodes,6,'Gauss10')[1][1]
# Gmsh's tabulated high-order tetra rules differ at ~4e-12 here.
assert max(abs(eight[i][j]-ten[i][j]) for i in range(10) for j in range(10)) < 1e-10
nodes = helpers['tetra']()
nodes[9],nodes[10] = nodes[10],nodes[9]
try:
    consistent_mass(elements,nodes,6)
except ValueError as error:
    assert 'Jacobian' in str(error)
else:
    raise AssertionError('Swapped midside nodes accepted')
# Failure must release Gmsh so another valid integration can run.
consistent_mass(elements, helpers['tetra'](), 6)
'''
    import pytest as host_pytest
    site = str(Path(host_pytest.__file__).resolve().parent.parent)
    result = subprocess.run(["docker","run","--rm","--network=none","--memory=2g","--cpus=2",
                             "--read-only","--tmpfs","/tmp:size=128m",
                             "-e","PYTHONDONTWRITEBYTECODE=1","-v",f"{Path.cwd()}:/work:ro",
                             "-v",f"{site}:/host-packages:ro","-e","PYTHONPATH=/work:/host-packages",
                             image,"timeout","--kill-after=5s","45s","python3","-c",code],
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout+result.stderr
