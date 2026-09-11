"""Keep competing manufacturer patterns separate and map actual screw axes."""
import json

import cadquery as cq
import pytest

from fea import a34_base_fit as fit


def test_factory_pattern_variants_preserve_eight_axes_per_angle():
    data = json.loads(fit.DATA.read_text())
    variants = list(fit.patterns(data))
    assert len(variants) == 8
    station = ('angle', cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), cq.Vector(0, 0, 1), 'header', 'rim')
    for variant in variants:
        axes = fit.candidate_axes(station, variant)
        assert len(axes) == 8
        assert sum(row['receiver'] == 'header' for row in axes) == 4
        for row in axes:
            if row['receiver'] == 'header':
                assert row['start'].z == pytest.approx(variant['thickness_mm'])
                assert row['direction'].toTuple() == (0., 0., -1.)
            else:
                assert row['start'].x == pytest.approx(variant['thickness_mm'])
                assert row['direction'].toTuple() == (-1., 0., 0.)
    assert {v['family'] for v in variants} == {'dxf', 'sat'}
    assert data['disagreements']
