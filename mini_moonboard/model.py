import math

import cadquery as cq

from .panel_grid import kicker_foothold_datums, main_led_datums, main_tnut_datums

MAIN_PANEL_SIZE_MM = 1220.0
# Controlled v1 stock route: one factory-edge 48 in panel per 4 x 8 sheet.
# This is intentionally not rounded to the 1220 mm official nominal size.
V1_PANEL_SIZE_MM = 1219.2
PANEL_THICKNESS_MM = 18.0
OFFICIAL_KICKER_HEIGHT_MM = 150.0
V1_KICKER_HEIGHT_MM = 225.0
ANGLE_FROM_VERTICAL_DEG = 40.0
V1_SUPPORT_THICKNESS_MM = 36.0
V1_SUPPORT_WIDTH_MM = 180.0
V1_FACE_RAIL_COUNT = 4
V1_REAR_TIE_WIDTH_MM = 180.0
V1_HARDWARE_GAP_MM = 54.0
V1_STRUCTURAL_BOLT_DIAMETER_MM = 9.525
V1_LEG_BEND_DISTANCE_MM = 1480.0
V1_LEG_UPPER_DISTANCE_MM = 1880.0
V1_STRUCTURAL_BOLT_DISTANCES_MM = (1520.0, 1600.0, 1680.0, 1760.0)
V1_SELECTED_TNUT_HOLE_DIAMETER_MM = 11.112
V1_LED_HOLE_DIAMETER_MM = 13.0
# The climber is below the overhanging panel. The board's opposite side carries
# rails, braces, wiring, and legs; it is the support side, never the climbing face.


def _validate_kicker_height(kicker_height_mm: float) -> None:
    if not math.isfinite(kicker_height_mm) or kicker_height_mm <= 0:
        raise ValueError("kicker_height_mm must be a positive finite number")


def reference_envelope(
    kicker_height_mm: float = OFFICIAL_KICKER_HEIGHT_MM,
    panel_size_mm: float = MAIN_PANEL_SIZE_MM,
) -> tuple[float, float, float]:
    _validate_kicker_height(kicker_height_mm)
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    main_surface = 2 * panel_size_mm
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


def _panel_with_holes(
    width: float, height: float, holes: list[tuple[float, float, float]]
) -> cq.Workplane:
    """Cut provisional visual/drill bores through one local X/Z plywood panel."""
    panel = _panel(width, height)
    for x, z, diameter in holes:
        cutter = (
            cq.Workplane("XZ")
            .center(x, z)
            .circle(diameter / 2)
            .extrude(PANEL_THICKNESS_MM * 2, both=True)
        )
        panel = panel.cut(cutter)
    return panel


def _v1_main_panel_holes(column: int, row: int) -> list[tuple[float, float, float]]:
    """Map official centre data to one V1 stock-controlled main-panel quadrant."""
    x_min, y_min = column * V1_PANEL_SIZE_MM, row * V1_PANEL_SIZE_MM
    holes: list[tuple[float, float, float]] = []
    for x, y in main_tnut_datums().values():
        if x_min <= x < x_min + V1_PANEL_SIZE_MM and y_min <= y < y_min + V1_PANEL_SIZE_MM:
            holes.append((x - x_min - V1_PANEL_SIZE_MM / 2, y - y_min, V1_SELECTED_TNUT_HOLE_DIAMETER_MM))
    for x, y in main_led_datums().values():
        if x_min <= x < x_min + V1_PANEL_SIZE_MM and y_min <= y < y_min + V1_PANEL_SIZE_MM:
            holes.append((x - x_min - V1_PANEL_SIZE_MM / 2, y - y_min, V1_LED_HOLE_DIAMETER_MM))
    return holes


def _v1_kicker_holes(column: int) -> list[tuple[float, float, float]]:
    """Map official kicker and row-one LED centres to the active 150 mm V1 zone."""
    x_min = column * V1_PANEL_SIZE_MM
    holes: list[tuple[float, float, float]] = []
    for x, y in kicker_foothold_datums().values():
        if x_min <= x < x_min + V1_PANEL_SIZE_MM:
            holes.append((x - x_min - V1_PANEL_SIZE_MM / 2, V1_KICKER_HEIGHT_MM + y, V1_SELECTED_TNUT_HOLE_DIAMETER_MM))
    for x, y in main_led_datums().values():
        if x_min <= x < x_min + V1_PANEL_SIZE_MM and y < 0:
            holes.append((x - x_min - V1_PANEL_SIZE_MM / 2, V1_KICKER_HEIGHT_MM + y, V1_LED_HOLE_DIAMETER_MM))
    return holes


def build_reference_board(
    kicker_height_mm: float = OFFICIAL_KICKER_HEIGHT_MM,
    panel_size_mm: float = MAIN_PANEL_SIZE_MM,
) -> cq.Assembly:
    _validate_kicker_height(kicker_height_mm)
    board = cq.Assembly(name="mini_moonboard_reference")
    half_panel = panel_size_mm / 2

    for side, x in (("left", -half_panel), ("right", half_panel)):
        board.add(
            _panel(panel_size_mm, kicker_height_mm).translate((x, 0, 0)),
            name=f"kicker_{side}",
            color=cq.Color("gray"),
        )

    for row, z in (("lower", 0.0), ("upper", panel_size_mm)):
        for side, x in (("left", -half_panel), ("right", half_panel)):
            panel = (
                _panel(panel_size_mm, panel_size_mm)
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
    """Return a support-side-offset, board-parallel rail.

    The 54 mm local offset is a provisional clearance gap for T-nuts and LED
    wiring. It must be checked against the selected hardware before fabrication.
    """
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    return (
        cq.Workplane("XY")
        .box(V1_SUPPORT_WIDTH_MM, V1_SUPPORT_THICKNESS_MM, length, centered=(True, False, False))
        .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
        .translate(
            (
                x,
                V1_HARDWARE_GAP_MM + distance * math.sin(angle),
                V1_KICKER_HEIGHT_MM + distance * math.cos(angle),
            )
        )
    )


def _rear_tie_half(side: int, y: float, z: float) -> cq.Workplane:
    """Return one half of a support-side transverse tie; its splice needs review."""
    half_length = V1_PANEL_SIZE_MM + V1_SUPPORT_THICKNESS_MM
    return cq.Workplane("XY").box(
        half_length,
        V1_SUPPORT_THICKNESS_MM,
        V1_REAR_TIE_WIDTH_MM,
        centered=(True, True, True),
    ).translate((side * half_length / 2, y, z))


def _panel_joint_brace_half(side: int, distance: float) -> cq.Workplane:
    """Return one stock-cuttable half of a board-parallel panel-joint brace."""
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    return (
        cq.Workplane("XY")
        .box(V1_PANEL_SIZE_MM, V1_SUPPORT_THICKNESS_MM, V1_REAR_TIE_WIDTH_MM, centered=(True, False, True))
        .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
        .translate(
            (
                side * V1_PANEL_SIZE_MM / 2,
                V1_HARDWARE_GAP_MM + distance * math.sin(angle),
                V1_KICKER_HEIGHT_MM + distance * math.cos(angle),
            )
        )
    )


def _kicker_backing_member(x: float, width: float, height: float) -> cq.Workplane:
    """Return a vertical rear kicker backing member for the panel seam or bottom edge."""
    return (
        cq.Workplane("XY")
        .box(width, V1_SUPPORT_THICKNESS_MM, height, centered=(True, False, False))
        .translate((x, V1_HARDWARE_GAP_MM, 0.0))
    )


def _structural_bolt_envelope(side: int, distance: float) -> cq.Workplane:
    """Return a conservative X-axis envelope for a leg-to-outer-rail bolt."""
    x, y, z = v1_structural_bolt_position(side, distance)
    return cq.Workplane("XY").box(
        V1_SUPPORT_WIDTH_MM + V1_SUPPORT_THICKNESS_MM,
        V1_STRUCTURAL_BOLT_DIAMETER_MM,
        V1_STRUCTURAL_BOLT_DIAMETER_MM,
        centered=(True, True, True),
    ).translate(
        (x, y, z)
    )


def _led_string_envelope(x: float) -> cq.Workplane:
    """Return a conservative rear cable-routing envelope for one LED string."""
    return _sloped_face_member(x, 0.0, 2 * V1_PANEL_SIZE_MM).translate((0, -24.0, 0))


def v1_leg_geometry() -> dict[str, float]:
    """Return the shared provisional side-leg geometry in millimetres."""
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    bend_distance, upper_distance = V1_LEG_BEND_DISTANCE_MM, V1_LEG_UPPER_DISTANCE_MM
    bend_y = V1_HARDWARE_GAP_MM + bend_distance * math.sin(angle)
    bend_z = V1_KICKER_HEIGHT_MM + bend_distance * math.cos(angle)
    upper_y = V1_HARDWARE_GAP_MM + upper_distance * math.sin(angle)
    upper_z = V1_KICKER_HEIGHT_MM + upper_distance * math.cos(angle)
    foot_y = bend_y + bend_z / math.tan(math.radians(70.0))
    # Solve the endpoint-centre elevation which places the wood member's lower
    # edge on z=0. Finished feet remain a separate, reviewer-selected detail.
    foot_center_z = 0.0
    for _ in range(8):
        lower_length = math.hypot(foot_y - bend_y, foot_center_z - bend_z)
        foot_center_z = V1_SUPPORT_WIDTH_MM / 2 * (foot_y - bend_y) / lower_length
    return {
        "bend_distance": bend_distance,
        "bend_y": bend_y,
        "bend_z": bend_z,
        "upper_y": upper_y,
        "upper_z": upper_z,
        "foot_y": foot_y,
        "foot_center_z": foot_center_z,
        "lower_length": math.hypot(foot_y - bend_y, foot_center_z - bend_z),
    }


def v1_structural_bolt_position(side: int, distance: float) -> tuple[float, float, float]:
    """Return the X-axis bolt center on the 18 mm normal mid-plane of an outer rail."""
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    rail_midplane = V1_SUPPORT_THICKNESS_MM / 2
    return (
        side * (V1_PANEL_SIZE_MM + V1_SUPPORT_THICKNESS_MM / 2),
        V1_HARDWARE_GAP_MM + distance * math.sin(angle) + rail_midplane * math.cos(angle),
        V1_KICKER_HEIGHT_MM + distance * math.cos(angle) - rail_midplane * math.sin(angle),
    )


def build_v1_concept() -> cq.Assembly:
    """Build the provisional unanchored board and two exterior hockey-stick legs.

    The leg bend uses the fifth T-nut row down from the top (row 8); its upper
    section reaches two rows upward (row 10). The 60-degree lower-leg angle and
    36 mm support thickness are modeling assumptions, not structural approval.
    """
    board = cq.Assembly(name="mini_moonboard_v1_concept")
    half_panel = V1_PANEL_SIZE_MM / 2
    for column, (side, x) in enumerate((("left", -half_panel), ("right", half_panel))):
        board.add(
            _panel_with_holes(V1_PANEL_SIZE_MM, V1_KICKER_HEIGHT_MM, _v1_kicker_holes(column)).translate((x, 0, 0)),
            name=f"kicker_{side}",
            color=cq.Color("gray"),
        )
    for row, z in (("lower", 0.0), ("upper", V1_PANEL_SIZE_MM)):
        for column, (side, x) in enumerate((("left", -half_panel), ("right", half_panel))):
            panel = (
                _panel_with_holes(V1_PANEL_SIZE_MM, V1_PANEL_SIZE_MM, _v1_main_panel_holes(column, 0 if row == "lower" else 1))
                .translate((x, 0, z))
                .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
                .translate((0, 0, V1_KICKER_HEIGHT_MM))
            )
            board.add(panel, name=f"main_{row}_{side}", color=cq.Color("black"))
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    leg = v1_leg_geometry()
    bend_y, bend_z = leg["bend_y"], leg["bend_z"]
    upper_y, upper_z = leg["upper_y"], leg["upper_z"]
    foot_y, foot_center_z = leg["foot_y"], leg["foot_center_z"]

    for side, x in (
        ("left", -V1_PANEL_SIZE_MM - V1_SUPPORT_WIDTH_MM / 2 - V1_SUPPORT_THICKNESS_MM / 2),
        ("right", V1_PANEL_SIZE_MM + V1_SUPPORT_WIDTH_MM / 2 + V1_SUPPORT_THICKNESS_MM / 2),
    ):
        upper = _support_member(bend_y, bend_z, upper_y, upper_z).translate((x, 0, 0))
        lower = _support_member(bend_y, bend_z, foot_y, foot_center_z).translate((x, 0, 0))
        board.add(cq.Compound.makeCompound([upper.val(), lower.val()]), name=f"leg_{side}", color=cq.Color("saddlebrown"))

    main_surface = 2 * V1_PANEL_SIZE_MM
    rail_spacing = main_surface / (V1_FACE_RAIL_COUNT - 1)
    for index in range(V1_FACE_RAIL_COUNT):
        for row, distance in (("lower", 0.0), ("upper", V1_PANEL_SIZE_MM)):
            board.add(
                _sloped_face_member(-V1_PANEL_SIZE_MM + index * rail_spacing, distance, V1_PANEL_SIZE_MM),
                name=f"face_rail_{index + 1}_{row}",
                color=cq.Color("saddlebrown"),
            )
    for row, distance in (("lower", 0.0), ("upper", V1_PANEL_SIZE_MM)):
        board.add(
            _sloped_face_member(0.0, distance, V1_PANEL_SIZE_MM),
            name=f"face_rail_center_seam_{row}",
            color=cq.Color("saddlebrown"),
        )

    for name, distance in (("kicker", 0.0), ("mid", V1_PANEL_SIZE_MM), ("top", main_surface)):
        for side, label in ((-1, "left"), (1, "right")):
            board.add(
                _panel_joint_brace_half(side, distance),
                name=f"panel_joint_brace_{name}_{label}",
                color=cq.Color("saddlebrown"),
            )

    board.add(
        _kicker_backing_member(0.0, V1_SUPPORT_WIDTH_MM, V1_KICKER_HEIGHT_MM),
        name="kicker_center_seam_backing",
        color=cq.Color("saddlebrown"),
    )
    for side, label in ((-1, "left"), (1, "right")):
        board.add(
            _kicker_backing_member(side * V1_PANEL_SIZE_MM / 2, V1_PANEL_SIZE_MM, V1_REAR_TIE_WIDTH_MM),
            name=f"kicker_bottom_backing_{label}",
            color=cq.Color("saddlebrown"),
        )

    for name, fraction in (("low", 0.25), ("mid", 0.5), ("top", 0.75)):
        tie_distance = leg["bend_distance"] * fraction
        tie_y = tie_distance * math.sin(angle) + V1_HARDWARE_GAP_MM
        tie_z = V1_KICKER_HEIGHT_MM + tie_distance * math.cos(angle)
        for side, label in ((-1, "left"), (1, "right")):
            board.add(
                _rear_tie_half(side, tie_y, tie_z),
                name=f"rear_tie_{name}_{label}",
                color=cq.Color("saddlebrown"),
            )

    for side, label in ((-1, "left"), (1, "right")):
        for index, distance in enumerate(V1_STRUCTURAL_BOLT_DISTANCES_MM, start=1):
            board.add(
                _structural_bolt_envelope(side, distance),
                name=f"leg_bolt_{label}_{index}",
                color=cq.Color("lightgray"),
            )

    for index, x in enumerate((-900.0, -300.0, 300.0, 900.0), start=1):
        board.add(
            _led_string_envelope(x),
            name=f"led_string_envelope_{index}",
            color=cq.Color("blue"),
        )
    board.add(
        cq.Workplane("XY")
        .box(180.0, 60.0, 120.0, centered=(True, True, True))
        .translate((0, 900.0, 1050.0)),
        name="led_controller_envelope",
        color=cq.Color("blue"),
    )

    return board
