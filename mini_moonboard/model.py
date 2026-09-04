import math

import cadquery as cq

MAIN_PANEL_SIZE_MM = 1220.0
PANEL_THICKNESS_MM = 18.0
OFFICIAL_KICKER_HEIGHT_MM = 150.0
ANGLE_FROM_VERTICAL_DEG = 40.0


def _validate_kicker_height(kicker_height_mm: float) -> None:
    if not math.isfinite(kicker_height_mm) or kicker_height_mm <= 0:
        raise ValueError("kicker_height_mm must be a positive finite number")


def reference_envelope(
    kicker_height_mm: float = OFFICIAL_KICKER_HEIGHT_MM,
) -> tuple[float, float, float]:
    _validate_kicker_height(kicker_height_mm)
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    main_surface = 2 * MAIN_PANEL_SIZE_MM
    return (
        main_surface,
        main_surface * math.sin(angle),
        kicker_height_mm + main_surface * math.cos(angle),
    )


def _panel(width: float, height: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(width, PANEL_THICKNESS_MM, height, centered=(True, False, False))
        .translate((0, -PANEL_THICKNESS_MM, 0))
    )


def build_reference_board(
    kicker_height_mm: float = OFFICIAL_KICKER_HEIGHT_MM,
) -> cq.Assembly:
    _validate_kicker_height(kicker_height_mm)
    board = cq.Assembly(name="mini_moonboard_reference")
    half_panel = MAIN_PANEL_SIZE_MM / 2

    for side, x in (("left", -half_panel), ("right", half_panel)):
        board.add(
            _panel(MAIN_PANEL_SIZE_MM, kicker_height_mm).translate((x, 0, 0)),
            name=f"kicker_{side}",
            color=cq.Color("gray"),
        )

    for row, z in (("lower", 0.0), ("upper", MAIN_PANEL_SIZE_MM)):
        for side, x in (("left", -half_panel), ("right", half_panel)):
            panel = (
                _panel(MAIN_PANEL_SIZE_MM, MAIN_PANEL_SIZE_MM)
                .translate((x, 0, z))
                .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
                .translate((0, 0, kicker_height_mm))
            )
            board.add(panel, name=f"main_{row}_{side}", color=cq.Color("black"))

    return board
