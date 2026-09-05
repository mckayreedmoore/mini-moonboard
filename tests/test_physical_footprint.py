"""Regenerate published physical support cases, not just their summary labels."""
import hashlib
import json
import math
from pathlib import Path

import pytest

from fea.physical_footprint import (
    EXTENSIONS_MM,
    OUTPUT,
    WEIGHTS_LB,
    cad_state,
    evaluate,
)


def test_sources_and_selection():
    report = json.loads(OUTPUT.read_text())
    for name, digest in report["source_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    assert report["climber_weights_lb"] == list(WEIGHTS_LB)
    assert report["extensions_mm"] == list(EXTENSIONS_MM)
    passing = [int(k) for k, item in report["candidates"].items() if item["below_screen_count"] == 0]
    assert report["minimum_tested_extension_meeting_all_96_cases_mm"] == (min(passing) if passing else None)


def test_zero_extension_retains_published_shallow_screen():
    zero = json.loads(OUTPUT.read_text())["candidates"]["0"]
    old = json.loads(Path("fea/results/hybrid/shallow_user_load_envelope.json").read_text())["candidates"]["2x8-shallow"]
    for key in ("mass_kg", "centre_xy_mm", "support_polygon_mm"):
        assert zero["state"][key] == old["state"][key]
    assert [{k: v for k, v in case.items() if not k.startswith("global_floor")} for case in zero["cases"]] == old["cases"]


@pytest.mark.parametrize("extension", EXTENSIONS_MM)
def test_physical_cad_and_report(extension):
    saved = json.loads(OUTPUT.read_text())["candidates"][str(extension)]
    state = cad_state(extension)
    assert state["mass_kg"] == pytest.approx(saved["state"]["mass_kg"], abs=1e-6)
    assert state["centre_xyz_mm"] == pytest.approx(saved["state"]["centre_xyz_mm"], abs=1e-6)
    assert state["part_count"] == saved["state"]["part_count"]
    for point, old in zip(state["support_polygon_mm"], saved["state"]["support_polygon_mm"], strict=True):
        assert point == pytest.approx(old, abs=1e-6)
    # Re-evaluate from published finite CAD state for deterministic exact comparison.
    assert json.loads(json.dumps(evaluate(saved["state"]), allow_nan=False)) == saved
    assert len(saved["cases"]) == 96
    assert len(saved["legacy_2d_cases"]) == 6
    assert {c["climber_lb"] for c in saved["cases"]} == set(WEIGHTS_LB)
    for case in saved["cases"]:
        assert math.hypot(*case["global_floor_force_n"]) == pytest.approx(case["global_floor_resultant_n"])
    for case in saved["legacy_2d_cases"]:
        total = state["mass_kg"]*9.80665-case["force_yz_n"][1]
        assert case["kicker_reaction_n"]+case["leg_reaction_n"] == pytest.approx(total)
