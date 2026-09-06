import itertools
import json
from copy import deepcopy

import pytest

from fea import tied_base_envelope as study


def test_saved_exact_inventory_screen_replays():
    saved = json.loads(study.OUTPUT.read_text())
    assert json.loads(json.dumps(study.build_report(), allow_nan=False)) == saved
    assert "NO CONNECTION, CONTACT OR STRUCTURAL ACCEPTANCE" in saved["status"]
    reference = saved["candidates"]["2x8-foot100-timber-only"]
    assert reference["state"]["mass_kg"] == pytest.approx(183.96328718899005)
    for name, candidate in saved["candidates"].items():
        cases = candidate["cases"]
        assert len(cases) == 96
        expected = set(itertools.product((150, 200, 250, 300), (1, 2), (.8, 1.), (0, 50, 100), (0, 300)))
        actual = {(row["climber_lb"], row["weight_multiplier"], row["mass_scale"], row["hold_standoff_mm"], row["horizontal_n"]) for row in cases}
        assert actual == expected
        assert candidate["summary"]["minimum_factor"] == min(row["governing"]["factor"] for row in cases if row["governing"]["factor"] is not None)
        assert candidate["summary"]["minimum_net_restoring_nmm"] == min(row["minimum_net_restoring_nmm"] for row in cases)
        for weight in study.WEIGHTS_LB:
            selected = [row for row in cases if row["climber_lb"] == weight]
            assert candidate["by_weight_lb"][str(weight)] == study.case_summary(selected)
            assert len(selected) == 24
        assert len(candidate["legacy_row12_cases"]) == 6
        assert [row["load"]["name"] for row in candidate["legacy_row12_cases"]] == [load.name for load in study.load_cases()]
        assert [row["status"] for row in candidate["legacy_row12_cases"][-2:]] == ["UPLIFT", "UPLIFT"]
        assert all(row["status"] == "MEETS MOMENT SCREEN ONLY" for row in cases)
        assert candidate["state"]["support_polygon_mm"] == reference["state"]["support_polygon_mm"]
        if name != "2x8-foot100-timber-only":
            assert candidate["state"]["mass_kg"] == pytest.approx(191.2812939344746)
            # In this rigid-body model only planar CG and added mass matter;
            # increased tie height is not credited as stiffness or anchoring.
            assert candidate["summary"]["minimum_factor"] > reference["summary"]["minimum_factor"]
    low = saved["candidates"]["2x8-foot100-tied-base-z100"]
    high = saved["candidates"]["2x8-foot100-tied-base-z275"]
    assert low["summary"]["minimum_factor"] == pytest.approx(high["summary"]["minimum_factor"], abs=1e-12)


@pytest.mark.parametrize("mutation,match", [
    ("height", "candidate"), ("source", "source changed"),
    ("artifact", "STEP changed"), ("nan", "Finite positive"),
    ("density", "density"), ("floor", "floor polygon"),
])
def test_changed_or_invalid_published_input_is_rejected(tmp_path, mutation, match):
    original = study.SUMMARIES[0]
    value = deepcopy(json.loads(original.read_text()))
    (tmp_path/"candidate.step").symlink_to((original.parent/"candidate.step").resolve())
    if mutation == "height":
        value["height_mm"] = 275
    elif mutation == "source":
        value["source_sha256"]["mini_moonboard/tied_base.py"] = "wrong"
    elif mutation == "artifact":
        value["artifact_sha256"]["candidate.step"] = "wrong"
    elif mutation == "nan":
        value["candidate_state"]["centre_mm"][0] = float("nan")
    elif mutation == "density":
        value["candidate_state"]["mass_kg"] = 195.573
    else:
        value["candidate_state"]["support_polygon_mm"] = [[x+1, y] for x, y in value["candidate_state"]["support_polygon_mm"]]
    path = tmp_path/"summary.json"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match=match):
        study.checked_states((path, study.SUMMARIES[1]))


def test_publication_preserves_existing_result(tmp_path):
    path = tmp_path/"previous.json"
    path.write_text("frozen")
    with pytest.raises(ValueError, match="overwritten"):
        study.publish(path)
    assert path.read_text() == "frozen"
