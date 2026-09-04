import pytest

from mini_moonboard.stability import SCREENING_DENSITY_KG_M3, v1_stability_screen


def test_unanchored_top_normal_load_requires_uplift_at_screening_density() -> None:
    screen = v1_stability_screen()

    assert screen.mass_kg == pytest.approx(192.5, abs=1)
    assert screen.front_toe_y_mm < screen.centre_y_mm < screen.rear_toe_y_mm
    assert any(case.front_reaction_n < 0 or case.rear_reaction_n < 0 for case in screen.cases)
    assert max(case.minimum_weight_n for case in screen.cases) / 9.80665 > screen.mass_kg


def test_stability_screen_rejects_nonpositive_density() -> None:
    with pytest.raises(ValueError):
        v1_stability_screen(0)

    assert SCREENING_DENSITY_KG_M3 == 600
