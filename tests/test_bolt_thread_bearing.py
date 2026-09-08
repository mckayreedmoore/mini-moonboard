import json

import pytest

from fea import bolt_thread_bearing as model


def test_interval_overlap_boundaries():
    assert model.exposure(2, 20, 60, 25)["threaded_bearing_mm"] == 0
    assert model.exposure(40, 50, 60, 25)["threaded_bearing_mm"] == 10
    assert model.exposure(20, 40, 60, 25)["threaded_fraction"] == .25
    assert model.exposure(20, 40, 60, 25)["nominal_quarter_length_condition"]
    assert not model.exposure(20, 40.01, 60, 25)["nominal_quarter_length_condition"]


@pytest.mark.parametrize("args", [(-1, 20, 60, 25), (2, 61, 60, 25),
    (20, 20, 60, 25), (2, 20, 60, 61), (2, float("nan"), 60, 25)])
def test_invalid_intervals(args):
    with pytest.raises(ValueError):
        model.exposure(*args)


def test_actual_current_stacks_and_publication():
    report = model.build()
    assert report == json.loads(model.OUTPUT.read_text())
    assert len(report["rows"]) == 28
    failed = []
    for row in report["rows"]:
        if row["member"].startswith("timber_base_gusset_"):
            assert row["bearing_length_mm"] == pytest.approx(19.05)
            assert row["threaded_bearing_mm"] == pytest.approx(8.382)
            failed.append(row)
        elif row["connection"].startswith("leg_stitch_") and row["member"].endswith("outer"):
            assert row["bearing_length_mm"] == pytest.approx(19.05)
            assert row["threaded_bearing_mm"] == pytest.approx(2.032)
        else:
            assert row["threaded_bearing_mm"] == pytest.approx(0)
    assert len(failed) == 8
    assert [r for r in report["rows"] if not r["nominal_quarter_length_condition"]] == failed
