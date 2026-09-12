import math

from fea.leg_attachment_check import LEG
from fea.wider_leg_six_bolt_screen import build


def test_six_bolt_candidate_preserves_force_and_moment_and_has_screen_margin():
    report = build()
    best = report['best']
    assert .7 < best['ratio'] < .9
    assert best['margin'] >= 2
    assert not report['qualified_for_construction']
    points = best['points']
    centre = [sum(p[k] for p in points)/6 for k in range(3)]
    for forces, load, target in zip(best['forces'], best['loads'], best['moments'], strict=True):
        for k in (1, 2):
            assert math.isclose(sum(f[k] for f in forces), load['compression_n']*LEG[k])
        recovered = sum((p[1]-centre[1])*f[2]-(p[2]-centre[2])*f[1]
                        for p, f in zip(points, forces, strict=True))
        assert math.isclose(recovered, target)
