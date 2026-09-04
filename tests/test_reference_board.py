import math
from collections import deque
from itertools import combinations

import pytest

from mini_moonboard import build_reference_board, build_v1_concept, reference_envelope
from mini_moonboard.model import (
    PANEL_THICKNESS_MM,
    V1_HARDWARE_GAP_MM,
    V1_KICKER_MAIN_GUSSET_BLANK_HEIGHT_MM,
    V1_LEG_UPPER_DISTANCE_MM,
    V1_PANEL_FASTENER_DIAMETER_MM,
    V1_PANEL_FASTENER_LENGTH_MM,
    V1_PANEL_SIZE_MM,
    V1_REAR_TIE_LAG_LOCAL_OFFSETS_MM,
    V1_STANDOFF_CLEARANCE_MM,
    V1_STRUCTURAL_BOLT_DISTANCES_MM,
    _kicker_main_seam_gusset,
    _structural_bolt_envelope,
    _v1_kicker_holes,
    _v1_main_panel_holes,
    v1_face_rail_centres,
    v1_lower_leg_cut_profile,
    v1_main_support_origin,
    v1_panel_fastener_envelope,
    v1_panel_fastener_positions,
    v1_rail_standoff_placements,
    v1_rear_tie_lag_envelope,
    v1_seam_panel_fastener_positions,
    v1_seam_standoff_placements,
    v1_structural_bolt_position,
    v1_support_side_point,
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

    assert names[6:10] == ["leg_left", "leg_knee_gusset_left", "leg_right", "leg_knee_gusset_right"]
    assert names[10:20] == [
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
    assert {"kicker_blank_extension_backing_left", "kicker_blank_extension_backing_right"} <= set(names)
    assert "kicker_blank_extension_backing_seam_splice" in names
    assert {"kicker_main_seam_gusset_left", "kicker_main_seam_gusset_right"} <= set(names)
    assert {"leg_knee_gusset_left", "leg_knee_gusset_right"} <= set(names)
    assert {
        "rear_tie_low_left",
        "rear_tie_low_right",
        "rear_tie_mid_left",
        "rear_tie_mid_right",
        "rear_tie_top_left",
        "rear_tie_top_right",
    } <= set(names)
    assert len(board.children) == 73
    for part in (next(part for part in board.children if part.name == name) for name in ("leg_left", "leg_right")):
        shape = part.obj if not hasattr(part.obj, "val") else part.obj.val()
        assert shape.BoundingBox().zmin == pytest.approx(0, abs=0.001)
    assert max(V1_STRUCTURAL_BOLT_DISTANCES_MM) < V1_LEG_UPPER_DISTANCE_MM
    for distance in V1_STRUCTURAL_BOLT_DISTANCES_MM:
        x, y, z = v1_structural_bolt_position(1, distance)
        assert x == pytest.approx(V1_PANEL_SIZE_MM + 36 / 2)
        expected_y, expected_z = v1_support_side_point(distance, V1_HARDWARE_GAP_MM + 18)
        assert (y, z) == pytest.approx((expected_y, expected_z))


def _shape(child: object):
    obj = child.obj  # type: ignore[attr-defined]
    return obj.val() if hasattr(obj, "val") else obj


def test_v1_bores_are_mapped_inside_stock_controlled_panels() -> None:
    assert [len(_v1_main_panel_holes(column, row)) for row in range(2) for column in range(2)] == [72, 60, 66, 55]
    assert [len(_v1_kicker_holes(column)) for column in range(2)] == [11, 10]

    for row in range(2):
        for column in range(2):
            for x, z, diameter in _v1_main_panel_holes(column, row):
                assert abs(x) + diameter / 2 < V1_PANEL_SIZE_MM / 2
                assert diameter / 2 < z < V1_PANEL_SIZE_MM - diameter / 2


def test_v1_geometry_has_valid_solids_with_floor_bearing_faces() -> None:
    board = build_v1_concept()
    for child in board.children:
        shape = _shape(child)
        assert shape.isValid(), child.name
        assert shape.Solids(), child.name

    for child in (next(child for child in board.children if child.name == name) for name in ("leg_left", "leg_right")):
        floor_faces = [
            face
            for face in _shape(child).Faces()
            if face.BoundingBox().zmin == pytest.approx(0, abs=0.001)
            and face.BoundingBox().zmax == pytest.approx(0, abs=0.001)
        ]
        assert floor_faces
        trim_corner, floor_corner = v1_lower_leg_cut_profile()[:2]
        expected_bearing_width = math.dist(trim_corner, floor_corner)
        assert max(face.Area() for face in floor_faces) == pytest.approx(36 * expected_bearing_width, abs=1)


def test_v1_support_contacts_clear_all_bores_and_do_not_overlap() -> None:
    board = build_v1_concept()
    parts = {child.name: _shape(child) for child in board.children}
    assert parts["main_lower_left"].distance(parts["rail_1_standoff_lower_130"]) == pytest.approx(0)
    assert parts["rail_1_standoff_lower_130"].distance(parts["face_rail_1_lower"]) == pytest.approx(0)
    assert parts["main_lower_left"].distance(parts["face_rail_1_lower"]) == pytest.approx(V1_HARDWARE_GAP_MM)
    assert parts["kicker_main_seam_gusset_left"].distance(parts["kicker_left"]) == pytest.approx(0)
    assert parts["kicker_main_seam_gusset_left"].distance(parts["main_lower_left"]) == pytest.approx(0)
    seam_splice = parts["kicker_blank_extension_backing_seam_splice"]
    assert seam_splice.distance(parts["kicker_blank_extension_backing_left"]) == pytest.approx(0)
    assert seam_splice.distance(parts["kicker_blank_extension_backing_right"]) == pytest.approx(0)
    for side in ("left", "right"):
        assert parts[f"leg_knee_gusset_{side}"].distance(parts[f"leg_{side}"]) == pytest.approx(0)
    for index, rail in enumerate(("face_rail_1", "face_rail_2", "face_rail_3", "face_rail_4", "face_rail_center_seam"), start=1):
        splice = parts[f"face_rail_splice_{index}"]
        assert splice.distance(parts[f"{rail}_lower"]) == pytest.approx(0)
        assert splice.distance(parts[f"{rail}_upper"]) == pytest.approx(0)
    for row in ("low", "mid", "top"):
        for side in ("left", "right"):
            assert parts[f"rear_tie_{row}_{side}"].distance(parts[f"leg_{side}"]) == pytest.approx(0)
        assert parts[f"rear_tie_splice_{row}"].distance(parts[f"rear_tie_{row}_left"]) == pytest.approx(0)
        assert parts[f"rear_tie_splice_{row}"].distance(parts[f"rear_tie_{row}_right"]) == pytest.approx(0)
    for row in ("low", "mid", "top"):
        for side, rails in (("left", ("face_rail_1", "face_rail_2", "face_rail_center_seam")), ("right", ("face_rail_3", "face_rail_4", "face_rail_center_seam"))):
            cross_tie = parts[f"rail_cross_tie_{row}_{side}"]
            rail_row = "upper" if row == "top" else "lower"
            for rail in rails:
                assert cross_tie.distance(parts[f"{rail}_{rail_row}"]) == pytest.approx(0)
        assert parts[f"rail_cross_tie_splice_{row}"].distance(parts[f"rail_cross_tie_{row}_left"]) == pytest.approx(0)
        assert parts[f"rail_cross_tie_splice_{row}"].distance(parts[f"rail_cross_tie_{row}_right"]) == pytest.approx(0)

    for rail_number, _x, _distance in v1_seam_standoff_placements():
        block = parts[f"rail_{rail_number}_standoff_main_seam"]
        side = "left" if rail_number in (1, 2, 5) else "right"
        rail = f"face_rail_{rail_number}" if rail_number < 5 else "face_rail_center_seam"
        assert block.distance(parts[f"main_lower_{side}"]) == pytest.approx(0)
        assert block.distance(parts[f"main_upper_{side}"]) == pytest.approx(0)
        assert block.distance(parts[f"{rail}_lower"]) == pytest.approx(0)
        assert block.distance(parts[f"{rail}_upper"]) == pytest.approx(0)

    for row, fraction in (("low", 0.25), ("mid", 0.5), ("top", 0.75)):
        for sign, side in ((-1, "left"), (1, "right")):
            for offset in V1_REAR_TIE_LAG_LOCAL_OFFSETS_MM:
                envelope = v1_rear_tie_lag_envelope(sign, fraction, offset)
                assert envelope.intersect(parts[f"leg_{side}"]).Volume() > 1_000
                assert envelope.intersect(parts[f"rear_tie_{row}_{side}"]).Volume() > 10_000
    for sign, side, rail in ((-1, "left", "face_rail_1_upper"), (1, "right", "face_rail_4_upper")):
        for distance in V1_STRUCTURAL_BOLT_DISTANCES_MM:
            envelope = _structural_bolt_envelope(sign, distance).val()
            # The reference envelope is deliberately absent from the physical
            # STEP assembly, but its axis must traverse both the leg and rail.
            assert envelope.intersect(parts[f"leg_{side}"]).Volume() > 0
            assert envelope.intersect(parts[rail]).Volume() > 0

    expected_panel_embedment = V1_PANEL_FASTENER_LENGTH_MM - 2 * V1_HARDWARE_GAP_MM
    for placement, fastener_pair in zip(
        v1_rail_standoff_placements(),
        (v1_panel_fastener_positions()[index : index + 2] for index in range(0, 40, 2)),
        strict=True,
    ):
        rail_number, _block_x, row, block_distance = placement
        rail = f"face_rail_{rail_number}_{row}" if rail_number < 5 else f"face_rail_center_seam_{row}"
        block = f"rail_{rail_number}_standoff_{row}_{int(block_distance % V1_PANEL_SIZE_MM)}"
        panel = f"main_{row}_{'left' if rail_number in (1, 2, 5) else 'right'}"
        for _fastener_rail, screw_x, screw_distance in fastener_pair:
            envelope = v1_panel_fastener_envelope(screw_x, screw_distance)
            assert envelope.intersect(parts[rail]).Volume() > 0
            assert envelope.intersect(parts[block]).Volume() > 0
            assert envelope.intersect(parts[panel]).Volume() == pytest.approx(
                math.pi * (V1_PANEL_FASTENER_DIAMETER_MM / 2) ** 2 * expected_panel_embedment,
                abs=1,
            )

    for placement, fastener_group in zip(
        v1_seam_standoff_placements(),
        (v1_seam_panel_fastener_positions()[index : index + 4] for index in range(0, 20, 4)),
        strict=True,
    ):
        rail_number, _block_x, _block_distance = placement
        rail = f"face_rail_{rail_number}" if rail_number < 5 else "face_rail_center_seam"
        side = "left" if rail_number in (1, 2, 5) else "right"
        block = f"rail_{rail_number}_standoff_main_seam"
        for _fastener_rail, screw_x, screw_distance in fastener_group:
            row = "lower" if screw_distance < V1_PANEL_SIZE_MM else "upper"
            envelope = v1_panel_fastener_envelope(screw_x, screw_distance)
            assert envelope.intersect(parts[f"{rail}_{row}"]).Volume() > 0
            assert envelope.intersect(parts[block]).Volume() > 0
            assert envelope.intersect(parts[f"main_{row}_{side}"]).Volume() == pytest.approx(
                math.pi * (V1_PANEL_FASTENER_DIAMETER_MM / 2) ** 2 * expected_panel_embedment,
                abs=1,
            )

    bores = []
    for row in range(2):
        for column in range(2):
            for x, z, radius in _v1_main_panel_holes(column, row):
                bores.append((x + (column - 0.5) * V1_PANEL_SIZE_MM, z + row * V1_PANEL_SIZE_MM, radius / 2))
    for _, x, _, distance in v1_rail_standoff_placements():
        for bore_x, bore_distance, radius in bores:
            lateral = max(abs(bore_x - x) - 30, 0)
            longitudinal = max(abs(bore_distance - distance) - 40, 0)
            assert math.hypot(lateral, longitudinal) - radius >= V1_STANDOFF_CLEARANCE_MM
    for _, x, distance in v1_seam_standoff_placements():
        for bore_x, bore_distance, radius in bores:
            lateral = max(abs(bore_x - x) - 30, 0)
            longitudinal = max(abs(bore_distance - (distance + 90)) - 90, 0)
            assert math.hypot(lateral, longitudinal) - radius >= V1_STANDOFF_CLEARANCE_MM

    for (left_name, left), (right_name, right) in combinations(parts.items(), 2):
        left_box, right_box = left.BoundingBox(), right.BoundingBox()
        if any(
            min(getattr(left_box, f"{axis}max"), getattr(right_box, f"{axis}max"))
            - max(getattr(left_box, f"{axis}min"), getattr(right_box, f"{axis}min"))
            <= 0.01
            for axis in "xyz"
        ):
            continue
        assert left.intersect(right).Volume() <= 1, f"{left_name} overlaps {right_name}"

    # Every physical part must have a contact path to a floor-bearing leg;
    # this catches visually plausible but disconnected members.
    contacts = {name: set() for name in parts}
    for (left_name, left), (right_name, right) in combinations(parts.items(), 2):
        if left.distance(right) < 0.01:
            contacts[left_name].add(right_name)
            contacts[right_name].add(left_name)
    connected = {"leg_left", "leg_right"}
    frontier = deque(connected)
    while frontier:
        name = frontier.popleft()
        for neighbor in contacts[name] - connected:
            connected.add(neighbor)
            frontier.append(neighbor)
    assert connected == set(parts)


def test_v1_rail_and_tie_axes_follow_the_declared_board_relationships() -> None:
    board = build_v1_concept()
    assert v1_face_rail_centres()[:4] == pytest.approx(
        (-V1_PANEL_SIZE_MM, -V1_PANEL_SIZE_MM / 3, V1_PANEL_SIZE_MM / 3, V1_PANEL_SIZE_MM)
    )
    rail = _shape(next(child for child in board.children if child.name == "face_rail_1_lower"))
    rail_edge = next(edge for edge in rail.Edges() if edge.Length() == pytest.approx(V1_PANEL_SIZE_MM))
    rail_vertices = rail_edge.Vertices()
    rail_dy = rail_vertices[1].Center().y - rail_vertices[0].Center().y
    rail_dz = rail_vertices[1].Center().z - rail_vertices[0].Center().z
    assert math.degrees(math.atan2(abs(rail_dy), abs(rail_dz))) == pytest.approx(40)

    tie = _shape(next(child for child in board.children if child.name == "rear_tie_low_right"))
    tie_edge = next(edge for edge in tie.Edges() if edge.Length() == pytest.approx(180))
    tie_vertices = tie_edge.Vertices()
    tie_dy = tie_vertices[1].Center().y - tie_vertices[0].Center().y
    tie_dz = tie_vertices[1].Center().z - tie_vertices[0].Center().z
    assert tie_dy * math.sin(math.radians(40)) + tie_dz * math.cos(math.radians(40)) == pytest.approx(0)


def test_v1_kicker_main_gusset_fits_its_cut_blank() -> None:
    for side in (-1, 1):
        bounds = _kicker_main_seam_gusset(side).val().BoundingBox()
        assert bounds.xlen == pytest.approx(36)
        assert bounds.ylen <= 400
        assert bounds.zlen <= V1_KICKER_MAIN_GUSSET_BLANK_HEIGHT_MM


def test_v1_climbing_faces_share_the_kicker_main_seam() -> None:
    board = build_v1_concept()
    parts = {child.name: _shape(child) for child in board.children}
    seam_y, seam_z = -PANEL_THICKNESS_MM, 225.0
    assert v1_main_support_origin() == pytest.approx(
        (-PANEL_THICKNESS_MM * (1 + math.cos(math.radians(40))), 225 + PANEL_THICKNESS_MM * math.sin(math.radians(40)))
    )
    for name in ("kicker_left", "main_lower_left"):
        assert any(
            vertex.Center().y == pytest.approx(seam_y, abs=0.001)
            and vertex.Center().z == pytest.approx(seam_z, abs=0.001)
            for vertex in parts[name].Vertices()
        )
