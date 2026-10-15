"""Equilibrated ideal steel-bend stresses and outward-rounded interval checks.

The construction supports six end resultants and uniform body force. It is
statically admissible, not an elastic or complete holed-fitting solution.
"""
from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction as F
from functools import cache
from pathlib import Path

LOADED_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def body_free(r, z, c, s, *, a, t, w, force, moment):
    """Promote the six-wrench construction from its frozen method controls.

    Cylindrical slots rr, tt, zz, rt, rz, tz; moments are about the curve center.
    All arguments may be numbers, arrays, or intervals.
    """
    h = w/2
    inertia = 2*h**3/3
    x = (r-a)/t
    d, dd = 6*x*(1-x)/t, 6*(1-2*x)/t**2
    fx, fy, fz = force
    mx, my, mz = moment
    normal = (-fx*s+fy*c)/w-z*(mx*c+my*s)/inertia
    shear = (fx*c+fy*s)/w+z*(-mx*s+my*c)/inertia
    rr = d*normal-mz*d/(w*r)
    tt = (2*d+r*dd)*normal-mz*dd/w
    rt = d*shear+3*fz*r*d*z/(4*h**3)
    tz = 3*fz*(3*d+r*dd)*(h*h-z*z)/(8*h**3)
    return rr, tt, r*0, rt, r*0, tz


def gravity(r, z, theta, c, s, *, a, t, w, density):
    """Particular stress with div(sigma)=-density, free radial/width sides.

    Density is a Cartesian force per volume, not a mass density. The theta=0
    end has zero force and moment (w*R2*gz, 0, -w*R2*gx), R2=(b^3-a^3)/3.
    """
    b, h = a+t, w/2
    gx, gy, gz = density
    gr, gt = gx*c+gy*s, -gx*s+gy*c
    factor = 3*(a+b)/t**2
    p = factor*(r-a)*(r-b)
    dp = factor*(2*r-a-b)
    integral = factor*((r**3-a**3)/3-(a+b)*(r*r-a*a)/2+a*b*(r-a))
    radial = -p-(2*integral+r*r-a*a)/r
    hoop = r*dp+2*p
    rr, rt = theta*gt*p+gr*radial, theta*gr*p
    tt = theta*gt*hoop-gr*(hoop+r)
    k = 3*gz/(2*h*h)
    factor_z = -3*k*(a*a+b*b)/t**2
    pz = factor_z*(r-a)*(r-b)
    dpz = factor_z*(2*r-a-b)
    integral_z = factor_z*((r**4-a**4)/4-(a+b)*(r**3-a**3)/3+a*b*(r*r-a*a)/2)
    shear_z = -2*pz+(-k*(r**4-a**4)/2+2*integral_z)/(r*r)
    hoop_z = r*dpz+pz
    return (rr+z*theta*theta*pz, tt+z*(theta*theta*hoop_z+shear_z),
            gz*z*(1-z*z/(h*h))/2, rt+z*theta*shear_z, r*0,
            -k*r*theta*(h*h-z*z))


def equivalent_squared(stress):
    rr, tt, zz, rt, rz, tz = stress
    return ((rr-tt)**2+(tt-zz)**2+(zz-rr)**2)/2+3*(rt**2+rz**2+tz**2)


class Interval:
    """Finite IEEE-754 binary64 intervals; round each basic operation outward."""

    def __init__(self, low, high=None):
        self.low = low
        self.high = low if high is None else high
        if not (math.isfinite(self.low) and math.isfinite(self.high) and self.low <= self.high):
            raise ValueError('finite ordered interval required')

    @staticmethod
    def point(value):
        if isinstance(value, Interval):
            return value
        exact = value if isinstance(value, F) else F(str(value))
        rounded = float(exact)
        lo = math.nextafter(rounded, -math.inf) if F.from_float(rounded) > exact else rounded
        hi = math.nextafter(rounded, math.inf) if F.from_float(rounded) < exact else rounded
        return Interval(lo, hi)

    def __neg__(self):
        return Interval(-self.high, -self.low)

    def __add__(self, other):
        other = self.point(other)
        return Interval(math.nextafter(self.low+other.low, -math.inf),
                        math.nextafter(self.high+other.high, math.inf))

    __radd__ = __add__

    def __sub__(self, other):
        return self+-self.point(other)

    def __rsub__(self, other):
        return self.point(other)+-self

    def __mul__(self, other):
        other = self.point(other)
        products = [x*y for x in (self.low, self.high) for y in (other.low, other.high)]
        return Interval(math.nextafter(min(products), -math.inf),
                        math.nextafter(max(products), math.inf))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = self.point(other)
        if other.low <= 0 <= other.high:
            raise ValueError('interval divisor contains zero')
        inverse = Interval(math.nextafter(1/other.high, -math.inf),
                           math.nextafter(1/other.low, math.inf))
        return self*inverse

    def __rtruediv__(self, other):
        return self.point(other)/self

    def __pow__(self, exponent):
        if not isinstance(exponent, int) or exponent < 0:
            raise ValueError('nonnegative integer power required')
        if exponent == 0:
            return Interval(1.)
        if exponent == 1:
            return self
        if exponent == 2:
            squared = (self.low*self.low, self.high*self.high)
            lo = 0. if self.low <= 0 <= self.high else math.nextafter(min(squared), -math.inf)
            return Interval(lo, math.nextafter(max(squared), math.inf))
        return self**(exponent//2)*self**(exponent-exponent//2)


def atan_series(value, terms=32):
    """Exact alternating-series enclosure for |value|<=1/2."""
    value = F(value)
    if abs(value) > F(1, 2):
        raise ValueError('small inverse-tangent argument required')
    if value < 0:
        lo, hi = atan_series(-value, terms)
        return -hi, -lo
    total = sum(((-1)**n*value**(2*n+1)/F(2*n+1) for n in range(terms)), F(0))
    next_term = (-1)**terms*value**(2*terms+1)/F(2*terms+1)
    return min(total, total+next_term), max(total, total+next_term)


@cache
def pi_bounds():
    first, second = atan_series(F(1, 5)), atan_series(F(1, 239))
    return 16*first[0]-4*second[1], 16*first[1]-4*second[0]


@cache
def angle_at(value):
    """theta=2*atan(q), with rational Pythagorean c,s; 0<=q<=1."""
    q = F.from_float(value)
    if not 0 <= q <= 1:
        raise ValueError('quarter-circle half-angle argument required')
    if q <= F(1, 2):
        lo, hi = atan_series(q)
    else:
        lo, hi = atan_series((q-1)/(q+1))
        lower_pi, upper_pi = pi_bounds()
        lo, hi = lo+lower_pi/4, hi+upper_pi/4
    c, s = (1-q*q)/(1+q*q), 2*q/(1+q*q)
    return Interval(Interval.point(2*lo).low, Interval.point(2*hi).high), Interval.point(c), Interval.point(s)


def angle(box):
    first, last = angle_at(box.low), angle_at(box.high)
    return (Interval(first[0].low, last[0].high), Interval(last[1].low, first[1].high),
            Interval(first[2].low, last[2].high))


def total_stress(r, z, theta, c, s, params):
    own = {key: params[key] for key in ('a', 't', 'w', 'force', 'moment')}
    body = {key: params[key] for key in ('a', 't', 'w', 'density')}
    return tuple(x+y for x, y in zip(body_free(r, z, c, s, **own),
                                   gravity(r, z, theta, c, s, **body), strict=True))


def enclose(params, *, ceiling=1., cell_budget=10000):
    """Certify an everywhere-yield ceiling on the entire ideal quarter bend.

    Every accepted box covers material. A finite budget without a covering
    certificate is inconclusive. Squared indices are authoritative; square
    roots in the receipt are display values, not the acceptance predicate.
    """
    if not 0 < ceiling <= 1 or not isinstance(cell_budget, int) or cell_budget < 1:
        raise ValueError('positive reference ceiling and cell budget required')
    required = {'a', 't', 'w', 'force', 'moment', 'density'}
    if set(params) != required or min(params[key] for key in ('a', 't', 'w')) <= 0:
        raise ValueError('complete positive bend dimensions and own wrench required')
    constants = {key: (tuple(map(Interval.point, value)) if key in ('force', 'moment', 'density')
                       else Interval.point(value)) for key, value in params.items()}
    if any(len(constants[key]) != 3 for key in ('force', 'moment', 'density')):
        raise ValueError('three Cartesian force, moment and density components required')
    pending = [((0., 1., -1., 1., 0., 1.), 0)]
    visited, accepted, maximum, maximum_depth = 0, 0, 0., 0
    digest = hashlib.sha256()
    scale = Interval.point(F('1.67'))/235
    ceiling_squared = Interval.point(ceiling)**2
    while pending and visited < cell_budget:
        box, depth = pending.pop()
        visited += 1
        maximum_depth = max(maximum_depth, depth)
        u0, u1, z0, z1, q0, q1 = box
        r = constants['a']+constants['t']*Interval(u0, u1)
        z = constants['w']/2*Interval(z0, z1)
        theta, c, s = angle(Interval(q0, q1))
        squared = equivalent_squared(total_stress(r, z, theta, c, s, constants))*scale**2
        if squared.high <= ceiling_squared.low:
            accepted += 1
            maximum = max(maximum, squared.high)
            digest.update(json.dumps([box, squared.high.hex()], separators=(',', ':')).encode()+b'\n')
            continue
        axis = depth % 3
        lo, hi = box[2*axis:2*axis+2]
        mid = (lo+hi)/2
        if mid in (lo, hi):
            raise ValueError('interval subdivision stagnated')
        left, right = list(box), list(box)
        left[2*axis+1], right[2*axis] = mid, mid
        pending.extend(((tuple(right), depth+1), (tuple(left), depth+1)))
    passed = not pending
    return {'status': 'EVERYWHERE_CONSTRUCTION_WITHIN_REFERENCE' if passed else 'INTERVAL_BUDGET_INCONCLUSIVE',
            'all_material_boxes_covered': passed, 'visited_boxes': visited, 'accepted_boxes': accepted,
            'remaining_boxes': len(pending), 'maximum_depth': maximum_depth,
            'covering_upper_index_squared': maximum if passed else None,
            'covering_upper_index_squared_hex': maximum.hex() if passed else None,
            'covering_upper_index_display': math.nextafter(math.sqrt(maximum), math.inf) if passed else None,
            'accepted_partition_sha256': digest.hexdigest(), 'reference_ceiling': ceiling,
            'yield_reference_mpa': 235., 'reference_factor': 1.67,
            'elastic_first_yield_or_complete_fitting_proved': False}
