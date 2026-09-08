import json

import numpy as np
import pytest

from fea import wide_backing_contact_bound as model


def test_exact_overhang_and_torsional_limits():
    corners = [(-1, 0), (-1, 2), (2, 0), (2, 2)]
    bolts = [(0, 1), (1, 1)]
    assert model.minimum_retention(bolts, corners, (3, 1))["minimum_total_retention_per_n"] == pytest.approx(2)
    assert model.minimum_retention(bolts, corners, (0, 1.5))["minimum_total_retention_per_n"] == pytest.approx(1.5)
    assert model.minimum_retention(bolts, corners, (-2, 1))["minimum_total_retention_per_n"] == pytest.approx(2)


def test_actual_three_component_balance_and_dual_bound():
    report = model.build()
    assert report == json.loads(model.OUTPUT.read_text())
    points = report["bolt_x_s_mm"]+report["contact_corners_x_s_mm"]
    for r in report["rows"]:
        assert min(r["bolt_reactions_per_n"]+r["contact_reactions_per_n"]) >= -1e-8
        assert sum(r["bolt_reactions_per_n"]) == pytest.approx(r["minimum_total_retention_per_n"])
        forces = r["bolt_reactions_per_n"]+[-c for c in r["contact_reactions_per_n"]]
        assert sum(forces) == pytest.approx(1)
        for axis in range(2):
            assert sum(f*p[axis] for f, p in zip(forces, points, strict=True)) == pytest.approx(r["load_x_s_mm"][axis])
        dual = np.array(r["dual"])
        for i, p in enumerate(points):
            column = np.array([1., *p])*(1 if i < 2 else -1)
            assert column@dual <= (1 if i < 2 else 0)+1e-8
        assert np.array([1., *r["load_x_s_mm"]])@dual == pytest.approx(r["minimum_total_retention_per_n"])
    assert max(r["minimum_total_retention_per_n"] for r in report["rows"]) == pytest.approx(936.45/171.45)


def test_invalid_and_infeasible_inputs():
    with pytest.raises(ValueError):
        model.minimum_retention([], [(0, 0)], (0, 0))
    with pytest.raises(ValueError, match="feasible"):
        model.minimum_retention([(0, 0)], [(0, 0)], (1, 0))
