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
# The selected T-nut barrel is 10 mm long.  A 36 mm support-side service space
# leaves room for its flange and LED wiring while using the same two-ply stock
# thickness specified for every frame member.
V1_HARDWARE_GAP_MM = 36.0
V1_STANDOFF_WIDTH_MM = 60.0
V1_STANDOFF_LENGTH_MM = 80.0
V1_STANDOFF_CLEARANCE_MM = 20.0
V1_STRUCTURAL_BOLT_DIAMETER_MM = 9.525
V1_LEG_BEND_DISTANCE_MM = 1480.0
V1_LEG_UPPER_DISTANCE_MM = 1880.0
V1_STRUCTURAL_BOLT_DISTANCES_MM = (1520.0, 1600.0, 1680.0, 1760.0)
V1_SELECTED_TNUT_HOLE_DIAMETER_MM = 11.112
V1_LED_HOLE_DIAMETER_MM = 13.0
# The climber is below the overhanging panel. The board's opposite side carries
# rails, bearing blocks, wiring, and legs; it is the support side, never the climbing face.


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
    """Return a main panel with its climbing surface on local +Y (underside)."""
    return (
        cq.Workplane("XY")
        .box(width, PANEL_THICKNESS_MM, height, centered=(True, False, False))
    )


def _kicker_panel(width: float, height: float) -> cq.Workplane:
    """Return the vertical kicker with its climbing face forward on local -Y."""
    return _panel(width, height).translate((0, -PANEL_THICKNESS_MM, 0))


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


def _kicker_panel_with_holes(
    width: float, height: float, holes: list[tuple[float, float, float]]
) -> cq.Workplane:
    """Drill a vertical kicker while retaining its forward-facing convention."""
    return _panel_with_holes(width, height, holes).translate((0, -PANEL_THICKNESS_MM, 0))


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
            _kicker_panel(panel_size_mm, kicker_height_mm).translate((x, 0, 0)),
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


def _trim_to_finished_floor(member: cq.Workplane) -> cq.Workplane:
    """Mitre-trim a member to a full bearing face on the CAD floor plane."""
    above_floor = cq.Workplane("XY").box(10_000.0, 10_000.0, 10_000.0, centered=(True, True, False))
    return member.intersect(above_floor)


def v1_support_side_point(distance: float, normal_offset: float = V1_HARDWARE_GAP_MM) -> tuple[float, float]:
    """Return the Y/Z point at a board distance and support-side normal offset.

    The board tangent is 40 degrees from vertical.  Its support-side normal is
    local -Y (forward/upward); the climber sees local +Y below the board.  The
    offset must therefore be transformed in both Y and Z; a global-Y shift is
    not a valid board-normal gap.
    """
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    return (
        distance * math.sin(angle) - normal_offset * math.cos(angle),
        V1_KICKER_HEIGHT_MM + distance * math.cos(angle) + normal_offset * math.sin(angle),
    )


def _sloped_face_member(x: float, distance: float, length: float) -> cq.Workplane:
    """Return a board-parallel rail on the far side of the service space."""
    y, z = v1_support_side_point(distance, V1_HARDWARE_GAP_MM + V1_SUPPORT_THICKNESS_MM)
    return (
        cq.Workplane("XY")
        .box(V1_SUPPORT_WIDTH_MM, V1_SUPPORT_THICKNESS_MM, length, centered=(True, False, False))
        .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
        .translate(
            (
                x,
                y,
                z,
            )
        )
    )


def _panel_standoff(x: float, distance: float) -> cq.Workplane:
    """Return one laminated block touching panel and rail across the service gap.

    ``distance`` is measured along the board from the main-surface/kicker seam.
    The fixed placements from :func:`v1_rail_standoff_placements` are checked
    against every modelled bore in the panel plane.
    """
    y, z = v1_support_side_point(distance, V1_HARDWARE_GAP_MM / 2)
    return (
        cq.Workplane("XY")
        .box(
            V1_STANDOFF_WIDTH_MM,
            V1_HARDWARE_GAP_MM,
            V1_STANDOFF_LENGTH_MM,
            centered=(True, True, False),
        )
        .rotate((0, 0, 0), (1, 0, 0), -ANGLE_FROM_VERTICAL_DEG)
        .translate(
            (
                x,
                y,
                z,
            )
        )
    )


def v1_face_rail_centres() -> tuple[float, ...]:
    """Return the five support-side rail centre planes in global X."""
    # The seam rail is shifted 30 mm left so its 60 mm bearing blocks can clear
    # the nearest central hold/LED column while the 180 mm rail still bridges X=0.
    return (-V1_PANEL_SIZE_MM, -360.0, 330.0, V1_PANEL_SIZE_MM, -85.0)


def v1_rail_standoff_placements() -> tuple[tuple[int, float, str, float], ...]:
    """Return (rail number, X, panel row, board distance) for bearing blocks.

    Each block is a two-ply 3/4-in offcut.  The placement intentionally keeps
    a 20 mm projected clearance beyond the edge of every CAD bore; it is not a
    substitute for confirming actual flange and LED hardware on an offcut.
    """
    rail_centres = v1_face_rail_centres()
    # Within each 180 mm rail, shift the bearing block away from the nearest
    # column of holds/LEDs.  130 and 630 mm land between successive 100 mm
    # T-nut/LED rows.
    block_centres = (-1165.0, -330.0, 300.0, 1165.0, -85.0)
    placements: list[tuple[int, float, str, float]] = []
    for rail_number, (rail_x, block_x) in enumerate(zip(rail_centres, block_centres), start=1):
        if abs(block_x - rail_x) + V1_STANDOFF_WIDTH_MM / 2 > V1_SUPPORT_WIDTH_MM / 2:
            raise ValueError("standoff must remain within its rail width")
        for row, row_distance in (("lower", 0.0), ("upper", V1_PANEL_SIZE_MM)):
            for local_distance in (130.0, 630.0):
                placements.append((rail_number, block_x, row, row_distance + local_distance))
    return tuple(placements)


def _rear_tie_half(side: int, y: float, z: float) -> cq.Workplane:
    """Return one transverse tie with its long section board-normal, not vertical."""
    # Each half ends at the interior face of an exterior 36 mm leg member.
    half_length = V1_PANEL_SIZE_MM + V1_SUPPORT_WIDTH_MM / 2
    # The board tangent is +40 degrees from vertical.  The board normal directed
    # rearward/downward is therefore +130 degrees from vertical in this signed
    # Y/Z plane, rather than the visually tempting but incorrect 50 degrees.
    normal_angle = 90.0 + ANGLE_FROM_VERTICAL_DEG
    return (
        cq.Workplane("XY")
        .box(
            half_length,
            V1_SUPPORT_THICKNESS_MM,
            V1_REAR_TIE_WIDTH_MM,
            centered=(True, True, True),
        )
        .rotate((0, 0, 0), (1, 0, 0), -normal_angle)
        .translate((side * half_length / 2, y, z))
    )


def _kicker_backing_member(x: float, width: float, height: float) -> cq.Workplane:
    """Return a direct-contact backing in the blank lower kicker extension."""
    return (
        cq.Workplane("XY")
        .box(width, V1_SUPPORT_THICKNESS_MM, height, centered=(True, False, False))
        .translate((x, 0.0, 0.0))
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
    bend_distance, upper_distance = V1_LEG_BEND_DISTANCE_MM, V1_LEG_UPPER_DISTANCE_MM
    bend_y, bend_z = v1_support_side_point(bend_distance, V1_HARDWARE_GAP_MM + V1_SUPPORT_THICKNESS_MM / 2)
    upper_y, upper_z = v1_support_side_point(upper_distance, V1_HARDWARE_GAP_MM + V1_SUPPORT_THICKNESS_MM / 2)
    foot_y = bend_y + bend_z / math.tan(math.radians(70.0))
    # The untrimmed centreline intentionally reaches the floor plane.  The
    # member is then intersected with Z>=0 so its end is a full floor-parallel
    # bearing face rather than a single low corner.
    foot_center_z = 0.0
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
    rail_midplane = V1_SUPPORT_THICKNESS_MM / 2
    y, z = v1_support_side_point(distance, V1_HARDWARE_GAP_MM + rail_midplane)
    return (
        side * (V1_PANEL_SIZE_MM + V1_SUPPORT_THICKNESS_MM / 2),
        y,
        z,
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
            _kicker_panel_with_holes(V1_PANEL_SIZE_MM, V1_KICKER_HEIGHT_MM, _v1_kicker_holes(column)).translate((x, 0, 0)),
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
    leg = v1_leg_geometry()
    bend_y, bend_z = leg["bend_y"], leg["bend_z"]
    upper_y, upper_z = leg["upper_y"], leg["upper_z"]
    foot_y, foot_center_z = leg["foot_y"], leg["foot_center_z"]

    for side, x in (
        ("left", -V1_PANEL_SIZE_MM - V1_SUPPORT_WIDTH_MM / 2 - V1_SUPPORT_THICKNESS_MM / 2),
        ("right", V1_PANEL_SIZE_MM + V1_SUPPORT_WIDTH_MM / 2 + V1_SUPPORT_THICKNESS_MM / 2),
    ):
        upper = _support_member(bend_y, bend_z, upper_y, upper_z).translate((x, 0, 0))
        lower = _trim_to_finished_floor(
            _support_member(bend_y, bend_z, foot_y, foot_center_z).translate((x, 0, 0))
        )
        board.add(cq.Compound.makeCompound([upper.val(), lower.val()]), name=f"leg_{side}", color=cq.Color("saddlebrown"))

    rail_centres = v1_face_rail_centres()
    for index, rail_x in enumerate(rail_centres[:V1_FACE_RAIL_COUNT]):
        for row, distance in (("lower", 0.0), ("upper", V1_PANEL_SIZE_MM)):
            board.add(
                _sloped_face_member(rail_x, distance, V1_PANEL_SIZE_MM),
                name=f"face_rail_{index + 1}_{row}",
                color=cq.Color("saddlebrown"),
            )
    for row, distance in (("lower", 0.0), ("upper", V1_PANEL_SIZE_MM)):
        board.add(
            _sloped_face_member(rail_centres[-1], distance, V1_PANEL_SIZE_MM),
            name=f"face_rail_center_seam_{row}",
            color=cq.Color("saddlebrown"),
        )

    for rail_number, x, row, distance in v1_rail_standoff_placements():
        board.add(
            _panel_standoff(x, distance),
            name=f"rail_{rail_number}_standoff_{row}_{int(distance % V1_PANEL_SIZE_MM)}",
            color=cq.Color("peru"),
        )

    for side, label in ((-1, "left"), (1, "right")):
        board.add(
            _kicker_backing_member(side * V1_PANEL_SIZE_MM / 2, V1_PANEL_SIZE_MM, 75.0),
            name=f"kicker_blank_extension_backing_{label}",
            color=cq.Color("saddlebrown"),
        )

    for name, fraction in (("low", 0.25), ("mid", 0.5), ("top", 0.75)):
        tie_distance = leg["bend_distance"] * fraction
        tie_y, tie_z = v1_support_side_point(
            tie_distance, V1_HARDWARE_GAP_MM + V1_SUPPORT_THICKNESS_MM + V1_REAR_TIE_WIDTH_MM / 2
        )
        for side, label in ((-1, "left"), (1, "right")):
            board.add(
                _rear_tie_half(side, tie_y, tie_z),
                name=f"rear_tie_{name}_{label}",
                color=cq.Color("saddlebrown"),
            )

    return board
