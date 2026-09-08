import math

import pytest

from fea.leg_demand_checkpoint import build


def test_climber_mass_and_simultaneous_components():
    result = build()
    assert len(result["rows"]) == 12
    assert {(r["stiffness"], r["climber_lb"]) for r in result["rows"]} == {
        (k, w) for k in ("k100", "k1000", "k10000") for w in (150, 200, 250, 300)}
    for row in result["rows"]:
        assert row["case"]["climber_lb"] == row["climber_lb"]
        assert row["simultaneous_signed_axial_n"] == row["force_on_leg_n"][0]
        assert row["lateral_n"] == math.hypot(*row["force_on_leg_n"][1:])
        assert row["numerical_reference_ratio"] == pytest.approx(row["lateral_n"]/797.6155904451)
        assert row["case"]["hold"] == "A12"
        assert row["case"]["weight_factor"] == 2
        assert row["case"]["horizontal_direction_deg"] == 90
    stiffest = [r for r in result["rows"] if r["stiffness"] == "k10000"]
    assert [r["lateral_n"] for r in stiffest] == pytest.approx(
        [506.4315692742, 638.6645083943, 770.8983838194, 903.1327842771])
    assert [r["simultaneous_signed_axial_n"] for r in stiffest] == pytest.approx(
        [-14.0773234745, -17.7713046327, -21.4652857909, -25.1592669491])
