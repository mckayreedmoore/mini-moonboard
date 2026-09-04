import math

import pytest

from mini_moonboard import build_reference_board, build_v1_concept, reference_envelope
from mini_moonboard.model import (
    V1_LEG_UPPER_DISTANCE_MM,
    V1_STRUCTURAL_BOLT_DISTANCES_MM,
)


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


def test_v1_concept_adds_two_exterior_hockey_stick_legs() -> None:
    board = build_v1_concept()

    names = [part.name for part in board.children]

    assert names[6:8] == ["leg_left", "leg_right"]
    assert names[8:18] == [
        "face_rail_1_lower",
        "face_rail_1_upper",
        "face_rail_2_lower",
        "face_rail_2_upper",
        "face_rail_3_lower",
        "face_rail_3_upper",
        "face_rail_4_lower",
        "face_rail_4_upper",
        "face_rail_center_seam_lower",
        "face_rail_center_seam_upper",
    ]
    assert "kicker_center_seam_backing" in names
    assert {"kicker_bottom_backing_left", "kicker_bottom_backing_right"} <= set(names)
    assert {
        "rear_tie_low_left",
        "rear_tie_low_right",
        "rear_tie_mid_left",
        "rear_tie_mid_right",
        "rear_tie_top_left",
        "rear_tie_top_right",
    } <= set(names)
    assert len(board.children) == 46
    for part in board.children[6:8]:
        shape = part.obj if not hasattr(part.obj, "val") else part.obj.val()
        assert shape.BoundingBox().zmin == pytest.approx(0, abs=0.001)
    assert max(V1_STRUCTURAL_BOLT_DISTANCES_MM) < V1_LEG_UPPER_DISTANCE_MM
    assert {"leg_bolt_left_1", "leg_bolt_right_4", "led_controller_envelope"} <= set(names)
    assert sum(name.startswith("led_string_envelope_") for name in names) == 4
