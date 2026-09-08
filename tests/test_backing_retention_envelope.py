import json

import numpy as np
import pytest

from fea import backing_retention_envelope as model


def test_hand_solved_lever_and_direct_load():
    assert model.ceiling([(0, 0)], [(-1, 0)], (1, 0), [100])["conditional_load_ceiling_n"] == pytest.approx(50)
    assert model.ceiling([(0, 0)], [(-1, 0)], (0, 0), [100])["conditional_load_ceiling_n"] == pytest.approx(100)
    assert model.ceiling([(0, 1), (1, 1)], [(-1, 0), (-1, 2)], (3, 1), [100, 100])["conditional_load_ceiling_n"] == pytest.approx(75)


def test_current_geometry_replay_and_independent_certificates():
    report = model.build()
    assert report == json.loads(model.OUTPUT.read_text())
    bolts, corners = report["bolt_x_s_mm"], report["contact_corners_x_s_mm"]
    for case in report["cases"].values():
        caps = case["per_bolt_caps_n"]
        assert len(case["rows"]) == 6
        for row in case["rows"]:
            p = row["conditional_load_ceiling_n"]
            ts, cs = row["bolt_forces_n"], row["compression_forces_n"]
            assert p > 0 and min(ts+cs) >= -1e-8
            assert all(t <= cap+1e-7 for t, cap in zip(ts, caps, strict=True))
            assert sum(ts)-sum(cs) == pytest.approx(p)
            for axis in (0, 1):
                assert (sum(t*b[axis] for t, b in zip(ts, bolts, strict=True))
                        -sum(c*b[axis] for c, b in zip(cs, corners, strict=True))) == pytest.approx(p*row["load_x_s_mm"][axis], abs=1e-6)
            points = bolts+corners+[row["load_x_s_mm"]]
            upper, lower = row["upper_bound_dual"], row["lower_bound_dual"]
            assert min(lower) >= -1e-8 and max(upper) <= 1e-8
            assert upper[len(bolts):] == pytest.approx([0.]*(len(corners)+1))
            for i, point in enumerate(points):
                sign = 1 if i < len(bolts) else -1
                objective = -1 if i == len(points)-1 else 0
                assert sign*np.dot([1., *point], row["equilibrium_dual"])+upper[i]+lower[i] == pytest.approx(objective, abs=1e-8)
            assert sum(cap*u for cap, u in zip(caps, upper[:len(bolts)], strict=True)) == pytest.approx(-p)
    dry = report["cases"]["dry"]["rows"]
    for name, factor in (("wet", .67), ("dry_002in", .73)):
        for a, b in zip(dry, report["cases"][name]["rows"], strict=True):
            assert b["conditional_load_ceiling_n"] == pytest.approx(factor*a["conditional_load_ceiling_n"])


@pytest.mark.parametrize("caps", [[0], [-1], [float("nan")], [1, 2]])
def test_invalid_caps(caps):
    with pytest.raises(ValueError):
        model.ceiling([(0, 0)], [(-1, 0)], (1, 0), caps)
