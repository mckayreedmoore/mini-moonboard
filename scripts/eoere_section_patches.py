"""Certified section tractions on disjoint rectangular material patches.

An LP selects bilinear tractions. Exact six-resultant integration, a polynomial
balance correction and the existing Bernstein method certify the field. Outer
rectangle support integrals give independent necessary bounds. A cubic convex
combination of fields can cover an entire source-load interval. This does not
establish volume equilibrium, elastic compatibility or fracture resistance.
"""
from __future__ import annotations

import hashlib
import itertools
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from scripts import eoere_cleat_section_traction as traction

dual, section = traction.dual, traction.previous
require = traction.current.require
OWN = Path(__file__).resolve()
with OWN.open('rb') as _stream:
    LOADED_SHA = hashlib.file_digest(_stream, 'sha256').hexdigest()
CORNERS = tuple(itertools.product((-1, 1), repeat=2))


def rational(value):
    require(not isinstance(value, bool), 'real scalar required')
    if isinstance(value, (float, np.floating)):
        require(math.isfinite(float(value)), 'finite binary scalar required')
        return F.from_float(float(value))
    return F(value)


def dot(a, b):
    return sum((x*y for x, y in zip(a, b, strict=True)), F(0))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def frame(half_tangent):
    t = rational(half_tangent)
    c, s = (1-t*t)/(1+t*t), 2*t/(1+t*t)
    return [[F(1), F(0), F(0)], [F(0), c, s], [F(0), -s, c]]


def rectangle(box):
    require(len(box) == 4, 'two complete rectangle intervals required')
    p0, p1, q0, q1 = map(rational, box)
    require(p0 < p1 and q0 < q1, 'positive rectangular patch required')
    return p0, p1, q0, q1


def disjoint(boxes):
    boxes = list(map(rectangle, boxes))
    require(boxes and all(a[1] <= b[0] or b[1] <= a[0] or a[3] <= b[2] or b[3] <= a[2]
                         for a, b in itertools.combinations(boxes, 2)), 'nonempty disjoint patch interiors required')
    return boxes


def robust_boxes(polygon, envelope, inset):
    """Inner/outer rectangles for a convex polygon's vertex-error envelope.

    Requiring inner_rectangle + [-e,e]^2 inside the nominal convex polygon
    makes it a subset of every convex vertex perturbation bounded by e.
    The adapter must separately justify that geometric uncertainty premise.
    """
    polygon = [tuple(map(rational, point)) for point in polygon]
    envelope, inset = rational(envelope), rational(inset)
    require(len(polygon) >= 3 and all(len(point) == 2 for point in polygon)
            and 0 < envelope < inset, 'convex polygon and positive geometric margins required')
    require(all((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]) > 0
                for a, b, c in zip(polygon, polygon[1:]+polygon[:1], polygon[2:]+polygon[:2], strict=True)),
            'strict counterclockwise convex polygon required')
    low = [min(point[i] for point in polygon) for i in range(2)]
    high = [max(point[i] for point in polygon) for i in range(2)]
    center = [(a+b)/2 for a, b in zip(low, high, strict=True)]
    half = [(b-a)/2-inset for a, b in zip(low, high, strict=True)]
    require(min(half) > 0, 'geometric inset consumes patch')
    scale = F(1)
    edges = list(zip(polygon, polygon[1:]+polygon[:1], strict=True))
    for a, b in edges:
        dx, dy = b[0]-a[0], b[1]-a[1]
        room = dx*(center[1]-a[1])-dy*(center[0]-a[0])-envelope*(abs(dx)+abs(dy))
        require(room > 0, 'bounding-box center outside the robust polygon interior')
        scale = min(scale, room/(abs(dx)*half[1]+abs(dy)*half[0]))
    half = [scale*value for value in half]
    inner = rectangle([center[0]-half[0], center[0]+half[0], center[1]-half[1], center[1]+half[1]])
    for p, q in itertools.product(inner[:2], inner[2:]):
        require(all((b[0]-a[0])*(q-a[1])-(b[1]-a[1])*(p-a[0])
                    >= envelope*(abs(b[0]-a[0])+abs(b[1]-a[1])) for a, b in edges),
                'exact expanded inner-corner containment failed')
    outer = rectangle([low[0]-envelope, high[0]+envelope, low[1]-envelope, high[1]+envelope])
    return inner, outer


def transport(wrench, p, q, inverse=False):
    n, vp, vq, torque, mp, mq = map(rational, wrench)
    p, q = rational(p), rational(q)
    sign = -1 if inverse else 1
    return [n, vp, vq, torque+sign*(p*vq-q*vp), mp+sign*q*n, mq-sign*p*n]


def patch_wrench(fields, box):
    p0, p1, q0, q1 = rectangle(box)
    return transport(traction.polynomial_wrench(fields, q1-q0, p1-p0), (p0+p1)/2, (q0+q1)/2)


def bilinear(corners):
    require(len(corners) == 4, 'all four signed corners required')
    corners = list(map(rational, corners))
    return {(i, j): sum(value*p**i*q**j for value, (p, q) in zip(corners, CORNERS, strict=True))/4
            for i, j in itertools.product((0, 1), repeat=2)}


def wrench_matrix(boxes):
    boxes = disjoint(boxes)
    columns = []
    for box in boxes:
        for corner in range(4):
            for component in range(3):
                fields = [bilinear([F(j == corner and k == component) for j in range(4)]) for k in range(3)]
                columns.append(patch_wrench(fields, box))
    return [[column[i] for column in columns] for i in range(6)]


def candidate(wrench, boxes, strengths):
    """Select fields and a dual multiplier; floating success proves neither."""
    wrench = list(map(rational, wrench))
    require(len(wrench) == 6 and any(wrench), 'nonzero complete wrench required')
    matrix = np.asarray(wrench_matrix(boxes), dtype=float)
    _, _, strengths = dual.dimensions(F(1), F(1), strengths)
    n = matrix.shape[1]
    facets = []
    for normal, sp, sq in itertools.product((1/strengths['tension'], -1/strengths['compression']), (-1, 1), (-1, 1)):
        for start in range(0, n, 3):
            row = np.zeros(n+1)
            row[start:start+3] = [float(normal), float(sp/strengths['parallel_shear']), float(sq/strengths['rolling_shear'])]
            row[-1] = -1
            facets.append(row)
    scales = np.maximum(np.max(abs(matrix), axis=1), 1.)
    result = linprog(np.r_[np.zeros(n), 1.], A_eq=np.c_[matrix/scales[:, None], np.zeros(6)],
        b_eq=np.asarray(wrench, dtype=float)/scales, A_ub=np.asarray(facets), b_ub=np.zeros(len(facets)),
        bounds=[(None, None)]*n+[(0, None)], method='highs-ds',
        options={'primal_feasibility_tolerance': 1e-9, 'dual_feasibility_tolerance': 1e-9})
    require(result.success and np.isfinite(result.x).all(), 'section LP did not select a finite witness')
    values = result.x[:-1].reshape((len(boxes), 4, 3))
    return {'corner_tractions_n_mm2': values.tolist(), 'dual_multiplier': (result.eqlin.marginals/scales).tolist(),
            'LP_index': float(result.fun), 'LP_is_not_a_certificate': True}


def certify(wrench, boxes, strengths, corners, tolerance=F(1, 10**7)):
    boxes = disjoint(boxes)
    wrench = list(map(rational, wrench))
    require(len(wrench) == 6 and len(corners) == len(boxes), 'complete wrench and own patch census required')
    fields = []
    for points in corners:
        require(len(points) == 4 and all(len(row) == 3 for row in points), 'all four complete traction vectors required')
        fields.append([bilinear([points[i][component] for i in range(4)]) for component in range(3)])
    recovered = [sum(values, F(0)) for values in zip(*(patch_wrench(field, box) for field, box in zip(fields, boxes, strict=True)), strict=True)]
    residual = [a-b for a, b in zip(wrench, recovered, strict=True)]
    index = max(range(len(boxes)), key=lambda i: (boxes[i][1]-boxes[i][0])*(boxes[i][3]-boxes[i][2]))
    p0, p1, q0, q1 = boxes[index]
    correction = section.traction_coefficients(transport(residual, (p0+p1)/2, (q0+q1)/2, inverse=True), q1-q0, p1-p0)
    require(patch_wrench(correction, boxes[index]) == residual, 'polynomial correction does not recover the full residual')
    for field, added in zip(fields[index], correction, strict=True):
        for key, value in added.items():
            field[key] = field.get(key, F(0))+value
    recovered = [sum(values, F(0)) for values in zip(*(patch_wrench(field, box) for field, box in zip(fields, boxes, strict=True)), strict=True)]
    require(recovered == wrench, 'corrected field does not carry all six resultants exactly')
    enclosures = [section.enclosure(section.interaction_polynomials(field, strengths), tolerance, 100000) for field in fields]
    upper = max(F(item['exact_upper_fraction']) for item in enclosures)
    return {'exact_complete_wrench': list(map(str, wrench)), 'exact_residual_before_correction': list(map(str, residual)),
            'exact_recovered_wrench': list(map(str, recovered)), 'correction_patch': index,
            'exact_construction_upper': str(upper), 'construction_upper': float(upper), 'patch_enclosures': enclosures,
            'traction_polynomials': [[[[i, j, str(value)] for (i, j), value in sorted(field.items())] for field in patch] for patch in fields]}


def necessary(multiplier, wrench, outer_boxes, strengths):
    require(len(multiplier) == len(wrench) == 6, 'complete dual multiplier and wrench required')
    multiplier, wrench = list(map(rational, multiplier)), list(map(rational, wrench))
    work = dot(multiplier, wrench)
    if work < 0:
        multiplier, work = [-value for value in multiplier], -work
    certificates, support = [], F(0)
    for box in map(rectangle, outer_boxes):
        p0, p1, q0, q1 = box
        # Dual translation differs from primal wrench transport.
        n, vp, vq, torque, mp, mq = multiplier
        p, q = (p0+p1)/2, (q0+q1)/2
        shifted = [n+q*mp-p*mq, vp-q*torque, vq+p*torque, torque, mp, mq]
        value, certificate = dual.support(shifted, q1-q0, p1-p0, strengths)
        support += value
        certificates.append(certificate)
    require(support > 0 and work >= 0, 'nonzero continuous support required')
    lower = work/support
    return {'exact_multiplier': list(map(str, multiplier)), 'exact_work': str(work), 'exact_outer_support': str(support),
            'exact_necessary_lower': str(lower), 'necessary_lower': float(lower), 'outer_support_certificates': certificates}


def cut_wrench(station, cut_transverse_origin, low, high, center, gravity, actions):
    """Exact X-grain source affine selfweight and an explicit fixed point set."""
    station, low, high = map(rational, (station, low, high))
    center, gravity = list(map(rational, center)), list(map(rational, gravity))
    require(len(center) == len(gravity) == 3 and low <= station <= high and low < high,
            'own positive source span and complete gravity required')
    origin = [station, *map(rational, cut_transverse_origin)]
    require(len(origin) == 3, 'complete cut datum required')
    length, middle = high-low, (low+high)/2
    beta = 12*(center[0]-middle)/length**2
    require(min(1+beta*(low-middle), 1+beta*(high-middle)) >= 0, 'negative affine source gravity density')
    fraction = (station-low+beta*((station-middle)**2-(low-middle)**2)/2)/length
    first = ((station**2-low**2)/2+beta*((station**3-low**3)/3-middle*(station**2-low**2)/2))/length
    arm = [-station*fraction+first, (center[1]-origin[1])*fraction, (center[2]-origin[2])*fraction]
    force, moment = [value*fraction for value in gravity], cross(arm, gravity)
    for point, action, free in actions:
        point, action, free = [list(map(rational, values)) for values in (point, action, free)]
        require(len(point) == len(action) == len(free) == 3, 'complete own point action and free couple required')
        force = [a+b for a, b in zip(force, action, strict=True)]
        couple = cross([p-o for p, o in zip(point, origin, strict=True)], action)
        moment = [a+b+c for a, b, c in zip(moment, couple, free, strict=True)]
    return [-value for value in force], [-value for value in moment]


def cubic_controls(values):
    """Cubic Bernstein coefficients from exact samples at 0,1/3,2/3,1."""
    require(len(values) == 4 and all(len(row) == 6 for row in values), 'four exact complete cubic wrench samples required')
    first, one_third, two_thirds, last = [list(map(rational, row)) for row in values]
    a = [27*v-8*x-z for v, x, z in zip(one_third, first, last, strict=True)]
    b = [27*v-x-8*z for v, x, z in zip(two_thirds, first, last, strict=True)]
    return [first, [(2*x-y)/18 for x, y in zip(a, b, strict=True)],
            [(2*y-x)/18 for x, y in zip(a, b, strict=True)], last]


def evaluate_controls(controls, t):
    t = rational(t)
    require(0 <= t <= 1 and len(controls) == 4 and all(len(row) == 6 for row in controls), 'complete cubic field and unit interval required')
    weights = [(1-t)**3, 3*t*(1-t)**2, 3*t*t*(1-t), t**3]
    return [sum((weight*row[i] for weight, row in zip(weights, controls, strict=True)), F(0)) for i in range(6)]
