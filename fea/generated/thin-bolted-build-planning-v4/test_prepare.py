"""Known-answer coordinate/stack and byte-binding checks; no CAD or response."""

import importlib.util
import math
from pathlib import Path

import pytest

LEAF = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("thin_shop_prepare", LEAF / "prepare.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def box():
    return [[x, y, z] for x in (0., 2.) for y in (0., 3.) for z in (0., 5.)]


def test_hull_volume_and_oblique_line():
    faces, volume = p.hull(box())
    assert len(faces) == 6
    assert volume == pytest.approx(30.)
    assert p.line_interval([1., 1.5, 2.5], [1., 1., 0.], faces) == pytest.approx([-1., 1.])


def test_rotated_translated_profile_has_actual_corner():
    s = math.sqrt(.5)
    basis = [[s, s, 0.], [-s, s, 0.], [0., 0., 1.]]
    vertices = [[11 + s * x - s * y, -7 + s * x + s * y, z] for x, y, z in box()]
    faces, volume = p.hull(vertices)
    cached = {"bounds_xyz_mm": [[min(q[i] for q in vertices), max(q[i] for q in vertices)] for i in range(3)],
              "volume_mm3": volume, "grain_axis_xyz": basis[0], "path": "toy", "sha256": "toy"}
    record, _ = p.profile_record("toy", {"vertices_world_mm": vertices, "stock_blank_allowance_mm": [2, 3, 5]}, cached, basis)
    assert record["datum_xyz_mm"] in vertices
    assert record["raw_volume_error_mm3"] == 0
    assert min(point[0] for point in record["raw_profile_vertices_luv_mm"]) >= -1e-12
    assert p.line_interval(vertices[0], basis[0], faces) == pytest.approx([0., 2.])


@pytest.mark.parametrize("corruption", ["bounds", "volume", "grain", "nonfinite"])
def test_forged_raw_profile_rejected(corruption):
    vertices = box()
    cached = {"bounds_xyz_mm": [[0, 2], [0, 3], [0, 5]], "volume_mm3": 30.,
              "grain_axis_xyz": [1, 0, 0], "path": "toy", "sha256": "toy"}
    if corruption == "bounds":
        cached["bounds_xyz_mm"][0][1] = 2.1
    elif corruption == "volume":
        cached["volume_mm3"] = 29.
    elif corruption == "grain":
        cached["grain_axis_xyz"] = [0, 1, 0]
    else:
        vertices[0][0] = math.inf
    with pytest.raises(ValueError):
        p.profile_record("toy", {"vertices_world_mm": vertices, "stock_blank_allowance_mm": [2, 3, 5]}, cached,
                         [[1, 0, 0], [0, 1, 0], [0, 0, 1]])


def test_reflected_reference_chart_rejected():
    with pytest.raises(ValueError, match="improper"):
        p.proper([[1, 0, 0], [0, 1, 0], [0, 0, -1]])


def test_short_eight_inch_tip_is_not_two_threads():
    axis = {"hardware_scenario": {"nut_height_mm": 11.5316, "threads_per_inch": 13},
            "before_plate_mm": 0., "after_plate_mm": 0., "grip_mm": 177.8,
            "nominal_under_head_length_mm": 203.2, "tip_projection_beyond_nut_mm": 7.5184}
    pair = [[34.925, 14.2875, 3.175], [34.925, 14.2875, 3.175]]
    result = p.stack(axis, pair, {"product": 407, "length_tolerance_in": [-.18, 0.]}, .448 * 25.4)
    assert result["comparison_shortest_tip_threads_frozen_stack"] == pytest.approx(1.508)
    assert result["comparison_shortest_tip_threads_frozen_washers_nut_max"] == pytest.approx(1.586)
    assert result["comparison_two_tip_margin_mm_frozen_washers_nut_max"] < 0


def test_own_small_head_moves_interval_and_never_uses_small_nut_as_head():
    axis = {"id": "toy", "hardware_scenario": {"washer_od_mm": 35.052, "washer_id_mm": 14.2875, "washer_thickness_mm": 3.3528}}
    change = {("toy", "head_washer"): {"od_mm": 27.7368, "id_mm": 13.8684, "thickness_mm": 3.0734}}
    pair = p.washers(axis, change)
    assert pair[0][2] - pair[1][2] == pytest.approx(-.2794)
    assert p.thread_exposure([[8.62965, 46.72965]], 34.544, 44.45) == pytest.approx([38.1, 2.27965, 12.18565])
    other = p.washers(axis, {("toy", "nut_washer"): change[("toy", "head_washer")]})
    assert other[0][2] == 3.3528


def test_forged_input_rejected_before_any_source_load(tmp_path):
    changed = tmp_path / "input.json"
    changed.write_text((LEAF / "input.json").read_text() + " ")
    with pytest.raises(ValueError, match="input byte binding"):
        p.prepare(changed)


def test_changed_source_pin_rejected(tmp_path):
    source = tmp_path / "source"
    source.write_text("old")
    pinned = p.sha(source)
    source.write_text("new")
    with pytest.raises(ValueError, match="source pin"):
        p.verify_pins({"source": pinned}, tmp_path)


def test_nominal_tip_mismatch_rejected():
    axis = {"hardware_scenario": {"nut_height_mm": 10, "threads_per_inch": 13}, "before_plate_mm": 0,
            "after_plate_mm": 0, "grip_mm": 38.1, "nominal_under_head_length_mm": 76.2,
            "tip_projection_beyond_nut_mm": 100}
    with pytest.raises(ValueError, match="stack replay"):
        p.stack(axis, [[30, 14, 3], [30, 14, 3]], {"product": 0, "length_tolerance_in": [0, 0]}, 10)


def test_shared_shaft_keeps_two_distinct_own_washer_pressure_planes():
    axis = {"id": "toy", "point": [0, 0, 0], "direction": [0, 0, 1], "before_plate_mm": 5,
            "after_plate_mm": 5, "grip_mm": 38, "receivers": ["wood"],
            "attachments": [{"angle_id": "first", "flange": "beam", "entry_xyz_mm": [0, 0, 0], "axis_xyz": [0, 0, 1]},
                            {"angle_id": "second", "flange": "beam", "entry_xyz_mm": [0, 0, 38], "axis_xyz": [0, 0, -1]}]}
    seats = {("toy", role): {"support_material": "steel", "planned_support_opening_mm": 14}
             for role in ("head_washer", "nut_washer")}
    rows = p.receiving_planes(axis, {}, seats)
    assert rows[0][3:6] == [["first", "beam"], [0., 0., -5.], [0., 0., 1.]]
    assert rows[1][3:6] == [["second", "beam"], [0., 0., 43.], [-0., -0., -1.]]
    axis["attachments"][1]["entry_xyz_mm"][0] = 1
    with pytest.raises(ValueError, match="not on its own shaft"):
        p.receiving_planes(axis, {}, seats)


def test_rear_runner_head_ownership_uses_finished_recess_not_overlapping_raw_leg():
    axis = {"id": "toy", "point": [0, 0, 0], "direction": [1, 0, 0], "before_plate_mm": 0,
            "after_plate_mm": 0, "grip_mm": 88.9, "receivers": ["runner", "leg"], "attachments": []}
    receiver_map = {("toy", "runner"): (0, {"finished_full_wall_intervals_from_axis_point_mm": [[0, 38.1]]}),
                    ("toy", "leg"): (1, {"finished_full_wall_intervals_from_axis_point_mm": [[38.1, 88.9]]})}
    seats = {("toy", role): {"support_material": "wood", "planned_support_opening_mm": 11.1125}
             for role in ("head_washer", "nut_washer")}
    rows = p.receiving_planes(axis, receiver_map, seats)
    assert rows[0][3] == ["runner", "finished_outer_face"]
    assert rows[1][3] == ["leg", "finished_outer_face"]


def test_pure_replay_joins_all_current_geometry_and_corrects_twelve_head_offsets():
    report = p.prepare()
    assert report["counts"] == {"timbers": 20, "panels": 6, "fittings": 36, "physical_bolts": 70,
                                "timber_bolt_receivers": 82, "fitting_hole_ownerships": 72,
                                "Hillman_42605_axes": 66, "small_washer_roles": 14}
    assert len(report["verification"]["old_generic_to_own_small_head_offsets_mm"]) == 12
    assert len(report["dimensional_issues"]["shortest_priced_8inch_comparison"]) == 4
    assert len(report["washer_receiving_plane_rows"]) == 140
    assert len(report["steel_bearing_rows"]) == 72
    assert report["recesses"][1]["cut_profile_world_x_global_grain_s_mm"][0][0] == pytest.approx(1216.025)
    assert "q" not in report and "force" not in report
