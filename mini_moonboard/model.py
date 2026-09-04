import math

import cadquery as cq

MAIN_PANEL_SIZE_MM = 1220.0
PANEL_THICKNESS_MM = 18.0
OFFICIAL_KICKER_HEIGHT_MM = 150.0
V1_KICKER_HEIGHT_MM = 225.0
ANGLE_FROM_VERTICAL_DEG = 40.0
V1_SUPPORT_THICKNESS_MM = 36.0
V1_SUPPORT_WIDTH_MM = 180.0
V1_FACE_RAIL_COUNT = 4
V1_REAR_TIE_WIDTH_MM = 180.0


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


def _support_member(
    start_y: float, start_z: float, end_y: float, end_z: float
) -> cq.Workplane:
    """Return a provisional exterior support member between two side-view points."""
    delta_y, delta_z = end_y - start_y, end_z - start_z
    length = math.hypot(delta_y, delta_z)
    angle_from_vertical = math.degrees(math.atan2(delta_y, delta_z))
    return (
        cq.Workplane("XY")
        .box(V1_SUPPORT_THICKNESS_MM, V1_SUPPORT_WIDTH_MM, length, centered=(True, True, False))
        .rotate((0, 0, 0), (1, 0, 0), -angle_from_vertical)
        .translate((0, start_y, start_z))
    )


def _sloped_face_member(x: float, distance: float, length: float) -> cq.Workplane:
    """Return a rearward-offset, board-parallel support rail.

    The 54 mm local offset is a provisional clearance gap for T-nuts and LED
    wiring. It must be checked against the selected hardware before fabrication.
    """
    return (
        cq.Workplane("XY")
        .box(V1_SUPPORT_WIDTH_MM, V1_SUPPORT_THICKNESS_MM, length, centered=(True, False, False))
        .translate((x, 54.0, distance))
        .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
        .translate((0, 0, V1_KICKER_HEIGHT_MM))
    )


def _rear_tie(y: float, z: float) -> cq.Workplane:
    """Return a provisional full-width transverse tie between the exterior legs."""
    return cq.Workplane("XY").box(
        2 * MAIN_PANEL_SIZE_MM + 2 * V1_SUPPORT_THICKNESS_MM,
        V1_SUPPORT_THICKNESS_MM,
        V1_REAR_TIE_WIDTH_MM,
        centered=(True, True, True),
    ).translate((0, y, z))


def _panel_joint_brace(distance: float) -> cq.Workplane:
    """Return a full-width board-parallel brace at a panel-edge datum."""
    return (
        cq.Workplane("XY")
        .box(2 * MAIN_PANEL_SIZE_MM, V1_SUPPORT_THICKNESS_MM, V1_REAR_TIE_WIDTH_MM, centered=(True, False, True))
        .translate((0, 54.0, distance))
        .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
        .translate((0, 0, V1_KICKER_HEIGHT_MM))
    )


def build_v1_concept() -> cq.Assembly:
    """Build the provisional unanchored board and two exterior hockey-stick legs.

    The leg bend uses the fifth T-nut row down from the top (row 8); its upper
    section reaches two rows upward (row 10). The 60-degree lower-leg angle and
    36 mm support thickness are modeling assumptions, not structural approval.
    """
    board = build_reference_board(V1_KICKER_HEIGHT_MM)
    board.name = "mini_moonboard_v1_concept"
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    bend_distance = 1480.0  # Fifth T-nut row down from row 12.
    upper_distance = bend_distance + 400.0  # Two T-nut-row intervals.
    bend_y = bend_distance * math.sin(angle)
    bend_z = V1_KICKER_HEIGHT_MM + bend_distance * math.cos(angle)
    upper_y = upper_distance * math.sin(angle)
    upper_z = V1_KICKER_HEIGHT_MM + upper_distance * math.cos(angle)
    # The descending board line points -130 degrees from horizontal. Rotating
    # it 60 degrees gives the rearward, floor-reaching lower leg at -70 degrees.
    foot_y = bend_y + bend_z / math.tan(math.radians(70.0))

    for side, x in (("left", -MAIN_PANEL_SIZE_MM - V1_SUPPORT_THICKNESS_MM / 2),
                    ("right", MAIN_PANEL_SIZE_MM + V1_SUPPORT_THICKNESS_MM / 2)):
        upper = _support_member(bend_y, bend_z, upper_y, upper_z).translate((x, 0, 0))
        lower = _support_member(bend_y, bend_z, foot_y, 0.0).translate((x, 0, 0))
        board.add(cq.Compound.makeCompound([upper.val(), lower.val()]), name=f"leg_{side}", color=cq.Color("saddlebrown"))

    main_surface = 2 * MAIN_PANEL_SIZE_MM
    rail_spacing = main_surface / (V1_FACE_RAIL_COUNT - 1)
    for index in range(V1_FACE_RAIL_COUNT):
        board.add(
            _sloped_face_member(-MAIN_PANEL_SIZE_MM + index * rail_spacing, 0.0, main_surface),
            name=f"face_rail_{index + 1}",
            color=cq.Color("saddlebrown"),
        )

    for name, distance in (("kicker", 0.0), ("mid", MAIN_PANEL_SIZE_MM), ("top", main_surface)):
        board.add(
            _panel_joint_brace(distance),
            name=f"panel_joint_brace_{name}",
            color=cq.Color("saddlebrown"),
        )

    for name, fraction in (("low", 0.25), ("mid", 0.5), ("top", 0.75)):
        tie_distance = bend_distance * fraction
        tie_y = tie_distance * math.sin(angle) + 200.0
        tie_z = V1_KICKER_HEIGHT_MM + tie_distance * math.cos(angle)
        board.add(_rear_tie(tie_y, tie_z), name=f"rear_tie_{name}", color=cq.Color("saddlebrown"))

    return board
