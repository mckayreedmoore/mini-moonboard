import pytest

from mini_moonboard.stability import (
    SCREENING_DENSITY_KG_M3,
    evaluate_unanchored_stability,
    v1_stability_screen,
)


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


def test_general_stability_evaluator_reproduces_v1_baseline() -> None:
    screen = v1_stability_screen()

    cases = evaluate_unanchored_stability(
        mass_kg=screen.mass_kg,
        centre_y_mm=screen.centre_y_mm,
        front_toe_y_mm=screen.front_toe_y_mm,
        rear_toe_y_mm=screen.rear_toe_y_mm,
        load_y_mm=screen.load_y_mm,
        load_z_mm=screen.load_z_mm,
    )

    assert cases == screen.cases


@pytest.mark.parametrize(
    "kwargs",
    (
        {"mass_kg": 0, "front_toe_y_mm": 0, "rear_toe_y_mm": 1},
        {"mass_kg": 1, "front_toe_y_mm": 1, "rear_toe_y_mm": 1},
        {"mass_kg": 1, "front_toe_y_mm": 0, "rear_toe_y_mm": 1},
    ),
)
def test_general_stability_evaluator_rejects_invalid_inputs(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        evaluate_unanchored_stability(
            centre_y_mm=1 if kwargs["front_toe_y_mm"] == 0 else 0,
            load_y_mm=0,
            load_z_mm=1,
            **kwargs,
        )
