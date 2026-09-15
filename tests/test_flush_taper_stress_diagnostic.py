"""Mechanics checks independent of the current CAD and solved-case values."""
import math

import pytest

from scripts.flush_taper_stress_diagnostic import corner_extrema


def test_variable_section_has_interior_stress_extremum():
    # sigma=t/(1+2t)^2: zero endpoint moment and growing section move the peak
    # away from either endpoint. Direct derivative gives t=1/2 and sigma=1/8.
    rows = corner_extrema(1.,3.,6.,0.,(0.,0.),(0.,1.),-1,1)
    peak = max(rows,key=lambda row:row['longitudinal_stress_mpa'])
    assert peak['fraction'] == pytest.approx(.5)
    assert peak['longitudinal_stress_mpa'] == pytest.approx(.125)


def test_stress_sign_matches_right_handed_section_resultants():
    # Positive Mv comes from tensile traction at negative u since u x grain=-v.
    plus = corner_extrema(2.,2.,4.,0.,(0.,0.),(8.,8.),1,1)
    minus = corner_extrema(2.,2.,4.,0.,(0.,0.),(8.,8.),-1,1)
    assert plus[0]['longitudinal_stress_mpa'] == -3.
    assert minus[0]['longitudinal_stress_mpa'] == 3.
    # Positive Mu comes from tensile traction at positive v.
    assert corner_extrema(2.,2.,4.,0.,(8.,8.),(0.,0.),1,1)[0]['longitudinal_stress_mpa'] == 1.5


def test_analytic_extrema_enclose_direct_corner_equation():
    width_start,width_end,depth,axial = 50.8,88.9,139.7,-2400.
    mus,mvs = (73000.,-41000.),(-38000.,61000.)
    for u in (-1,1):
        for v in (-1,1):
            rows = corner_extrema(width_start,width_end,depth,axial,mus,mvs,u,v)
            lo = min(row['longitudinal_stress_mpa'] for row in rows)
            hi = max(row['longitudinal_stress_mpa'] for row in rows)
            for j in range(1001):
                t = j/1000
                w = width_start*(1-t)+width_end*t
                mu,mv = (pair[0]*(1-t)+pair[1]*t for pair in (mus,mvs))
                direct = axial/(w*depth)-mv*(u*w/2)/(depth*w**3/12)+mu*(v*depth/2)/(w*depth**3/12)
                assert lo-1e-12<=direct<=hi+1e-12
                assert math.isfinite(direct)
