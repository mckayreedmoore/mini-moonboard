import math

import pytest

from mini_moonboard import build_reference_board, reference_envelope


def test_builds_six_named_panels() -> None:
    board = build_reference_board()

    assert [part.name for part in board.children] == [
        "kicker_left",
        "kicker_right",
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
    ]


def test_reports_official_surface_envelope() -> None:
    assert reference_envelope() == pytest.approx((2440.0, 1568.4, 2019.1), abs=0.1)


def test_kicker_height_must_be_positive_and_finite() -> None:
    for invalid_height in (0.0, -1.0, float("inf"), float("nan")):
        with pytest.raises(ValueError, match="positive finite"):
            build_reference_board(invalid_height)

        with pytest.raises(ValueError, match="positive finite"):
            reference_envelope(invalid_height)


def test_panels_have_nominal_dimensions_and_overhang() -> None:
    board = build_reference_board()
    parts = {part.name: part.obj.val() for part in board.children}

    assert parts["kicker_left"].Volume() == pytest.approx(1220 * 150 * 18)
    assert parts["main_lower_left"].Volume() == pytest.approx(1220 * 1220 * 18)

    lower_center = parts["main_lower_left"].Center()
    upper_center = parts["main_upper_left"].Center()
    row_offset_y = upper_center.y - lower_center.y
    row_offset_z = upper_center.z - lower_center.z

    assert math.degrees(math.atan2(row_offset_y, row_offset_z)) == pytest.approx(40)


def test_custom_kicker_moves_the_main_surface_up() -> None:
    official = build_reference_board()
    custom = build_reference_board(300)

    assert custom.children[0].obj.val().BoundingBox().zlen == pytest.approx(300)
    official_main_z = official.children[2].obj.val().Center().z
    custom_main_z = custom.children[2].obj.val().Center().z
    assert custom_main_z - official_main_z == pytest.approx(150)
