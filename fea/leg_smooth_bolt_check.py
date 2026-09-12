"""Specified smooth-shank leg bolt comparisons, not an installed joint rating.

The caller supplies sagittal moment. Prying is an explicit amplification screen,
not a prediction of the unilateral wood contact distribution.
"""
import math

from fea.dowel_yield import single_shear
from fea.leg_attachment_check import LEG, RIM
from fea.reinforced_timber_resistance import group_factor


def smooth_bolt_group(points, compression_n, moment_x_nmm=0.):
    if len(points) != 4 or not math.isfinite(compression_n) or compression_n < 0:
        raise ValueError('Require four bolts and nonnegative compression')
    cy, cz = (sum(p[k] for p in points)/4 for k in (1, 2))
    polar = sum((p[1]-cy)**2+(p[2]-cz)**2 for p in points)
    ea = 1600000*1.5*5.5
    cg = group_factor(4, 70/25.4, ea, ea, False)
    rows = []
    for p in points:
        force = (0., compression_n*LEG[1]/4-moment_x_nmm*(p[2]-cz)/polar,
                 compression_n*LEG[2]/4+moment_x_nmm*(p[1]-cy)/polar)
        demand = math.hypot(force[1], force[2])
        strengths = []
        for grain in (RIM, LEG):
            cos2 = min(1., sum(a*b for a,b in zip(force, grain, strict=True))**2/demand**2) if demand else 0.
            strengths.append(5600*3650/(5600*(1-cos2)+3650*cos2))
        d = .375
        reference = single_shear(main_length_in=1.5, side_length_in=1.5,
            main_bearing_lb_in=strengths[0]*d, side_bearing_lb_in=strengths[1]*d,
            main_yield_moment_lb_in=45000*d**3/6,
            side_yield_moment_lb_in=45000*d**3/6, gap_in=0.,
            reduction_terms={'Im':5.,'Is':5.,'II':4.5,'IIIm':4.,'IIIs':4.,'IV':4.})
        capacity = reference['reference_lateral_lbf']*4.4482216152605*cg
        rows.append({'force_xyz_n':force,'lateral_n':demand,'reference_n':capacity,
                     'ratio':demand/capacity,'mode':reference['governing_mode']})
    return {'bolts':rows,'peak_lateral_ratio':max(r['ratio'] for r in rows)}


def moment_interval(points, compression_n):
    if smooth_bolt_group(points,compression_n)['peak_lateral_ratio'] > 1:
        return None
    values = []
    for sign in (-1,1):
        low, high = 0., 1e6
        for _ in range(60):
            mid = (low+high)/2
            if smooth_bolt_group(points,compression_n,sign*mid)['peak_lateral_ratio'] <= 1:
                low = mid
            else:
                high = mid
        values.append(sign*low)
    return values


def prying_screen(points, compression_n, *, amplification=2., washer_side_mm=32.,
                   washer_hole_mm=11.1125, eccentricity_mm=38.1):
    """Envelope allocation: full member-centroid separation times compression.

    Signed elastic axial group balances that couple. Compression half is wood
    face contact; positive bolt forces are amplified by the explicit factor.
    This is a design screen, not a solved nonlinear contact/prying response.
    """
    centroid = [sum(p[k] for p in points)/4 for k in range(3)]
    offsets = [(p[1]-centroid[1], p[2]-centroid[2]) for p in points]
    yy = sum(y*y for y,z in offsets)
    yz = sum(y*z for y,z in offsets)
    zz = sum(z*z for y,z in offsets)
    determinant = yy*zz-yz*yz
    if determinant <= 0:
        raise ValueError('Axial couple requires a noncollinear bolt group')
    moment = compression_n*eccentricity_mm
    # e_x cross F = (0, -e*F_z, e*F_y). For axial bolt force T,
    # r cross (T,0,0) = (0,z*T,-y*T). Resolve BOTH moment components;
    # projection onto the grain axis alone misses covariance of the skew group.
    target_y, target_z = -moment*LEG[1], -moment*LEG[2]
    coefficient_y = (target_y*zz-target_z*yz)/determinant
    coefficient_z = (target_z*yy-target_y*yz)/determinant
    signed = [coefficient_y*y+coefficient_z*z for y,z in offsets]
    forces = [amplification*max(0.,force) for force in signed]
    area = washer_side_mm**2-math.pi*washer_hole_mm**2/4
    capacity = 625*0.006894757293168361*area
    return {'eccentricity_mm':eccentricity_mm,'amplification_assumed':amplification,
            'couple_nmm':moment,'bolt_tension_n':forces,
            'target_couple_xyz_nmm':[0., target_z, -target_y],
            'unamplified_signed_axial_force_n':signed,
            'washer_bearing_reference_n':capacity,
            'washer_bearing_ratio':max(forces)/capacity,
            'plate_bending_and_bolt_tension_not_checked':True,
            'prying_factor_not_an_established_physical_upper_bound':True}


def round_plate_screen(tension_n, *, outside_mm=38.1, hole_mm=11.1125,
                       thickness_mm=6.35, bearing_diameter_mm=14.2875):
    """Circular A36 plate, uniform wood pressure and radial cantilever strips.

    Ignore beneficial circumferential plate action. Treat each radial wedge as
    fixed at the minimum head/nut bearing circle. Service stress limit Fy/1.67.
    This includes force-induced pressure only; no installation preload credit.
    """
    area = math.pi*(outside_mm**2-hole_mm**2)/4
    pressure = tension_n/area
    a = bearing_diameter_mm/2
    c = outside_mm/2-a
    moment_per_inner_width = pressure*(c*c/2+c**3/(3*a))
    stress = 6*moment_per_inner_width/thickness_mm**2
    steel_allowable = 36000*.006894757293168361/1.67
    wood_allowable = 625*.006894757293168361
    return {'washer_tension_n':tension_n,'net_area_mm2':area,
            'wood_pressure_mpa':pressure,'wood_bearing_ratio':pressure/wood_allowable,
            'radial_strip_bending_stress_mpa':stress,
            'A36_bending_allowable_mpa':steel_allowable,
            'plate_bending_ratio':stress/steel_allowable}
