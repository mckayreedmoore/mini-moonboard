"""Necessary 3D strength bounds from compatible C3D20 virtual displacements.

The load functional must have the declared nodal virtual work. A strength
support integral bounds that work for every equilibrated stress field in the
stated six-component material domain. Saved elastic displacements only choose
trial functions; neither stress recovery nor solver convergence proves this
bound. Geometry support and load-transfer applicability remain explicit.
"""
from __future__ import annotations

import hashlib
import math
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from pathlib import Path

from fea.floor_recess_mesh import CORNERS, EDGES

NATURAL = tuple(tuple(map(int, row)) for bank in (CORNERS, EDGES) for row in bank)
ZERO = (0, 0, 0)
BASE_STRENGTHS = {'tension_parallel': F('8.5'), 'compression_parallel': F(17),
                  'tension_perpendicular': F('.4'), 'compression_perpendicular': F('2.2'),
                  'parallel_shear': F('2.144'), 'rolling_shear': F('.8')}
OWN = Path(__file__).resolve()
with OWN.open('rb') as _source:
    LOADED_SHA = hashlib.file_digest(_source, 'sha256').hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(value):
    """Binary floats remain their exact stored values; declared decimals use F."""
    if isinstance(value, F):
        return value
    if isinstance(value, float):
        require(math.isfinite(value), 'finite stored coordinate/value required')
        return F.from_float(value)
    return F(value)


def add(*polynomials):
    out = {}
    for polynomial in polynomials:
        for power, value in polynomial.items():
            out[power] = out.get(power, F(0))+value
    return {p: c for p, c in out.items() if c}


def scaled(polynomial, factor):
    return {p: v*factor for p, v in polynomial.items() if v*factor}


def multiply(first, second):
    out = {}
    for a, va in first.items():
        for b, vb in second.items():
            key = tuple(x+y for x, y in zip(a, b, strict=True))
            out[key] = out.get(key, F(0))+va*vb
    return {p: c for p, c in out.items() if c}


def derivative(polynomial, axis):
    out = {}
    for power, value in polynomial.items():
        if power[axis]:
            key = tuple(p-(i == axis) for i, p in enumerate(power))
            out[key] = value*power[axis]
    return out


def evaluate(polynomial, point):
    return sum(v*math.prod(number(x)**p for x, p in zip(point, key, strict=True))
               for key, v in polynomial.items())


def axis_polynomial(axis, constant, linear=0, quadratic=0):
    out = {ZERO: number(constant)}
    for power, value in ((1, linear), (2, quadratic)):
        if value:
            key = tuple(power if i == axis else 0 for i in range(3))
            out[key] = number(value)
    return {p: c for p, c in out.items() if c}


@lru_cache(maxsize=1)
def shape_polynomials():
    """Exact symbolic extension of the existing canonical C3D20 node ordering."""
    result = []
    for index, signs in enumerate(NATURAL):
        factors = [axis_polynomial(i, 1, sign) for i, sign in enumerate(signs)]
        value = {ZERO: F(1)}
        for factor in factors:
            value = multiply(value, factor)
        if index < 8:
            last = add({ZERO: F(-2)}, *(axis_polynomial(i, 0, sign) for i, sign in enumerate(signs)))
            value = scaled(multiply(value, last), F(1, 8))
        else:
            along = signs.index(0)
            value = scaled(multiply(value, axis_polynomial(along, 1, 0, -1)), F(1, 4))
        result.append(value)
    return tuple(result)


def separable_geometry(positions):
    """Exact monotone, possibly quadratic, maps for the stored tensor grid.

    No midpoint is snapped. Every stored component at a given natural axis
    coordinate must agree exactly, and each diagonal Jacobian stays positive.
    """
    require(len(positions) == 20 and all(len(p) == 3 for p in positions), 'twenty spatial nodes required')
    coordinates, jacobians, boxes, jacobian_bounds = [], [], [], []
    for axis in range(3):
        values = {}
        for natural, point in zip(NATURAL, positions, strict=True):
            at, value = natural[axis], number(point[axis])
            require(at not in values or values[at] == value, 'nonseparable stored geometry requires another map')
            values[at] = value
        low, middle, high = (values[k] for k in (-1, 0, 1))
        linear, quadratic = (high-low)/2, (high+low)/2-middle
        bounds = (linear-2*abs(quadratic), linear+2*abs(quadratic))
        require(bounds[0] > 0, 'nonpositive mapped-cell Jacobian')
        coordinates.append(axis_polynomial(axis, middle, linear, quadratic))
        jacobians.append(axis_polynomial(axis, linear, 2*quadratic))
        boxes.append((low, high))
        jacobian_bounds.append(bounds)
    return {'coordinates': coordinates, 'jacobians': jacobians,
            'boxes': boxes, 'jacobian_bounds': jacobian_bounds}


def sound_box(boxes, geometry):
    """Contain the complete mapped box in the finite profile outside all bores."""
    for plane in geometry['planes']:
        normal = tuple(map(number, plane['normal']))
        extreme = sum(n*(bounds[1] if n >= 0 else bounds[0])
                      for n, bounds in zip(normal, boxes, strict=True))
        if extreme > number(plane['offset']):
            return False
    for bore in geometry['bores']:
        require(bore['axis'] == [0., 1., 0.], 'current full-width U-axis bores required')
        start, end = (number(v)+number(bore['origin'][1]) for v in bore['interval_mm'])
        if boxes[1][1] <= start or boxes[1][0] >= end:
            continue
        radius = number(bore['radius_mm'])
        require(radius > 0 and start < end, 'positive finite cylinder required')
        distance = F(0)
        for axis in (0, 2):
            center = number(bore['origin'][axis])
            low, high = boxes[axis]
            nearest = max(low-center, center-high, F(0))
            distance += nearest**2
        if distance < radius**2:
            return False
    return True


def strain_power(positions, virtual):
    """Return det(J) times six engineering strains, without an inverse map.

    The positive diagonal Jacobian makes the Piola numerator polynomial.
    Positive homogeneity gives h(epsilon)*det(J)=h(det(J)*epsilon).
    """
    require(len(virtual) == 20 and all(len(v) == 3 for v in virtual), 'twenty virtual spatial displacements required')
    geometry = separable_geometry(positions)
    displacements = [add(*(scaled(shape, number(v[component]))
                           for shape, v in zip(shape_polynomials(), virtual, strict=True)))
                     for component in range(3)]
    cofactors = [multiply(*(geometry['jacobians'][i] for i in range(3) if i != axis)) for axis in range(3)]
    gradients = [[multiply(derivative(v, axis), cofactors[axis]) for axis in range(3)]
                 for v in displacements]
    return [gradients[0][0], gradients[1][1], gradients[2][2],
            add(gradients[0][1], gradients[1][0]), add(gradients[0][2], gradients[2][0]),
            add(gradients[1][2], gradients[2][1])], geometry


@lru_cache(maxsize=1)
def bernstein_transform():
    """Power basis on [-1,1] to tensor degree-three Bernstein coefficients."""
    return tuple(tuple(sum((F(math.comb(power, j)*2**j*(-1)**(power-j)*math.comb(index, j), math.comb(3, j))
                            for j in range(min(index, power)+1)), F(0))
                       for power in range(4)) for index in range(4))


def bernstein(polynomial):
    require(all(len(p) == 3 and all(0 <= k <= 3 for k in p) for p in polynomial),
            'degree at most three per natural coordinate required')
    transform = bernstein_transform()
    return tuple(sum((c*math.prod(transform[i][p] for i, p in zip(index, power, strict=True))
                      for power, c in polynomial.items()), F(0)) for index in product(range(4), repeat=3))


def support(strain, strengths):
    """Support of the declared six-component positive linear stress gauge."""
    require(len(strain) == 6 and set(strengths) == set(BASE_STRENGTHS), 'six strains and complete strength hypothesis required')
    s = {k: number(v) for k, v in strengths.items()}
    require(min(s.values()) > 0, 'positive full-tensor reference strengths required')
    normal = [(s['tension_parallel'], s['compression_parallel']),
              (s['tension_perpendicular'], s['compression_perpendicular']),
              (s['tension_perpendicular'], s['compression_perpendicular'])]
    return max(*[factor*value for value, (ft, fc) in zip(strain[:3], normal, strict=True) for factor in (ft, -fc)],
               s['parallel_shear']*abs(strain[3]), s['parallel_shear']*abs(strain[4]),
               s['rolling_shear']*abs(strain[5]))


def element_bound(positions, virtual, strengths):
    fields, geometry = strain_power(positions, virtual)
    coefficients = [bernstein(p) for p in fields]
    mean = [sum(c, F(0))/64 for c in coefficients]
    lower = 8*support(mean, strengths)
    upper = F(8, 64)*sum((support(tuple(c[i] for c in coefficients), strengths) for i in range(64)), F(0))
    require(F(0) <= lower <= upper, 'exact convex volume-support enclosure failed')
    return {'lower': lower, 'upper': upper, 'coefficients': coefficients, 'geometry': geometry}


def necessary_index(work, support_upper):
    """One-sided virtual work; the asymmetric normal domain forbids abs(work)."""
    work, support_upper = number(work), number(support_upper)
    require(support_upper >= 0, 'nonnegative strength support required')
    if work <= 0:
        return F(0)
    require(support_upper > 0, 'positive rigid work requires an explicit load-balance treatment')
    return work/support_upper


def support_nodes(elements, selected):
    """Zero extension is compatible when all safe-submesh boundary nodes vanish."""
    faces = {}
    seen = set()
    inside, outside = set(), set()
    for cell, (element, chosen) in enumerate(zip(elements, selected, strict=True)):
        require(len(element) == 20 and len(set(element)) == 20, 'distinct canonical twenty-node connectivity required')
        ids = tuple(map(int, element))
        key = tuple(sorted(ids))
        require(key not in seen, 'duplicate cell connectivity refused')
        seen.add(key)
        if not chosen:
            outside.update(ids)
            continue
        inside.update(ids)
        for axis, side in product(range(3), (-1, 1)):
            face = tuple(sorted(ids[i] for i, natural in enumerate(NATURAL) if natural[axis] == side))
            require(len(face) == 8, 'complete C3D20 boundary face required')
            faces.setdefault(face, []).append((cell, axis, side))
    require(all(len(owners) in (1, 2) for owners in faces.values()), 'nonmanifold safe submesh refused')
    for owners in faces.values():
        if len(owners) == 2:
            first, second = owners
            require(first[0] != second[0] and first[1] == second[1] and first[2] == -second[2],
                    'internal face requires distinct cells on opposite canonical sides')
    boundary = {node for face, owners in faces.items() if len(owners) == 1 for node in face}
    return sorted(inside-boundary-outside), sorted(boundary)
