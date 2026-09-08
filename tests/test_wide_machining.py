"""Small geometry/semantic checks; no full wide assembly generation."""
import csv
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard import wide_machining as machining


@pytest.mark.parametrize("name", ["main_upper_left", "base_side_right", "base_principal_left",
    "timber_bottom_backing", "base_header", "base_post_center_left_front", "leg_left_inner",
    "timber_base_gusset_right", "kicker_left"])
def test_explicit_part_axes_are_right_handed_and_reversible(name):
    _, _, axes = machining.family_axes(name)
    x, y, z = map(cq.Vector, axes)
    assert (x.cross(y)-z).Length < 1e-12
    frame = {"axes_world": axes, "origin_world_mm": (12., -7., 23.)}
    point = (18., 19., 37.)
    assert machining.to_world(machining.to_local(point, frame), frame) == pytest.approx(point)


def test_actual_oriented_brep_not_world_bounding_box_sets_datum():
    shape = machining.b.block(-10., 20., 30., 90., 5., 15.)
    datum = machining.datum(SimpleNamespace(name="base_principal_left", shape=shape))
    assert datum["origin_world_mm"] == pytest.approx(machining.b.point(-10., 30., 5.).toTuple(), abs=1e-6)
    assert datum["extents_mm"] == pytest.approx((30., 60., 10.), abs=1e-6)
    assert "Virtual" in datum["datum_note"]


def test_housing_does_not_require_datum_corner_to_remain_in_material():
    shape = cq.Solid.makeBox(10., 20., 30.).cut(cq.Solid.makeBox(3., 4., 5.))
    datum = machining.datum(SimpleNamespace(name="base_header", shape=shape))
    assert datum["origin_world_mm"] == pytest.approx((0., 0., 0.))
    assert datum["extents_mm"] == pytest.approx((10., 20., 30.))
    assert not shape.isInside(cq.Vector(*datum["origin_world_mm"]))


def test_insert_pilot_is_not_display_envelope_or_17mm_drilling_instruction():
    c = machining.frame.PanelMachineScrew("panel", cq.Vector(), cq.Vector(0, 0, 1),
        31.75, 6.35, ("main_upper_left", "base_principal_left"))
    assert machining.operation(c, c.members[0])[:2] == ("panel_clearance", 7.)
    label, diameter, note = machining.operation(c, c.members[1])
    assert label == "insert_installation_pilot" and diameter == pytest.approx(9.128125)
    assert "NOT a selected drilling depth" in note


def test_sds_factory_transfer_has_no_invented_pilot():
    c = SimpleNamespace(kind="screw", name="clip_timber_a")
    assert machining.operation(c, "base_header")[1] is None
    with pytest.raises(ValueError):
        machining.family_axes("unknown_part")


def test_generator_refuses_existing_output_before_cad(monkeypatch, tmp_path):
    monkeypatch.setattr(machining, "OUTPUT", tmp_path)
    with pytest.raises(FileExistsError):
        machining.write()


def test_csv_preserves_optional_plane_and_angle_columns(monkeypatch, tmp_path):
    monkeypatch.setattr(machining, "OUTPUT", tmp_path/"schedule")
    rows = [{"part": "panel", "class": "bore"},
            {"part": "panel", "class": "countersink_envelope", "included_angle_deg": 80.},
            {"part": "post", "class": "bearing_plane", "plane_normal_local": [0., 0., 1.],
             "plane_point_local_mm": [0., 0., 20.], "area_mm2": 100.}]
    monkeypatch.setattr(machining, "build", lambda: {
        "datums": {"panel": {"part": "panel"}}, "connections": [{"connection": "bolt"}],
        "features": rows})
    machining.write()
    with (machining.OUTPUT/"features.csv").open() as stream:
        reader = csv.DictReader(stream)
        saved = list(reader)
        assert reader.fieldnames == ["part", "class", "included_angle_deg", "plane_normal_local",
                                    "plane_point_local_mm", "area_mm2"]
    assert saved[0]["included_angle_deg"] == ""
    assert saved[1]["included_angle_deg"] == "80.0"
    assert saved[2]["plane_normal_local"] == "[0.0, 0.0, 1.0]"
    assert saved[2]["plane_point_local_mm"] == "[0.0, 0.0, 20.0]"
