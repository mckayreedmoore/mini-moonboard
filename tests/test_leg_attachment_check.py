import pytest

from fea.leg_attachment_check import LEG, bolt_group, moment_limit

POINTS = [(0.,-25.,-35.),(0.,25.,-35.),(0.,-25.,35.),(0.,25.,35.)]


def test_group_force_and_moment_equilibrium():
    report = bolt_group(POINTS,3000.,17000.)
    forces = [r['force_on_rim_xyz_n'] for r in report['bolts']]
    assert [sum(f[k] for f in forces) for k in range(3)] == pytest.approx([3000*x for x in LEG])
    assert sum(p[1]*f[2]-p[2]*f[1] for p,f in zip(POINTS,forces,strict=True)) == pytest.approx(17000.)


def test_moment_boundary_and_overload():
    boundary = moment_limit(POINTS,2000.,1)
    assert boundary > 0
    assert bolt_group(POINTS,2000.,boundary*.999)['lateral_and_parallel_criteria_met']
    assert not bolt_group(POINTS,2000.,boundary*1.001)['lateral_and_parallel_criteria_met']
    assert moment_limit(POINTS,5000.,1) is None
