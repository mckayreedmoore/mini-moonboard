"""Summary keeps separate maxima and their simultaneous force components."""
from pathlib import Path

import pytest

from fea.lumber_leg_summary import summarize


def test_summary_replays_existing_conditional_plywood_checkpoint():
    result = summarize(Path("fea/results/coupled-leg-release.tar.gz"))
    assert result["qualified_for_design"] is False
    assert len(result["rows"]) == 12
    row = next(r for r in result["rows"] if r["stiffness"] == "k10000" and r["climber_lb"] == 250)
    lateral = row["bolt_peaks"]["lateral_n"]
    assert lateral["value"] == pytest.approx(770.8983838, abs=.001)
    assert lateral["simultaneous_force_xyz_n"][0] == pytest.approx(-21.4652858, abs=.001)
    assert lateral["case"]["hold"] == "A12" and lateral["case"]["weight_factor"] == 2
    assert lateral["bolt"] == "analysis_leg_wall_bolt_left_1"
    axial = row["bolt_peaks"]["axial_n"]
    assert axial["value"] == abs(axial["simultaneous_force_xyz_n"][0])
    assert (axial["bolt"], axial["case"]) != (lateral["bolt"], lateral["case"])
