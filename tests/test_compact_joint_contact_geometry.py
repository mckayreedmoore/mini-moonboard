"""Elastic geometry hypotheses, including explicit unverified thread retention."""
import hashlib
import json
import math

import cadquery as cq
import pytest

from fea import compact_joint_contact_geometry as model


@pytest.fixture(scope="module", params=[("left","smooth"),("left","root-reference"),("right","root-reference")])
def prepared(request):
    return model.prepare(*request.param)


def test_real_members_minimum_washers_hex_dimensions_and_step(prepared):
    bodies,report = prepared
    assert report["body_count"] == len(bodies) == 26
    assert report["washer_thickness_mm"] == 2.794
    assert report["head_nut_flats_mm"] == pytest.approx(.562*25.4)
    assert report["head_height_mm"] == pytest.approx(.243*25.4)
    assert report["nut_height_mm"] == pytest.approx(.337*25.4)
    actual = {p.name:p.shape for p in model.model.parts(extension=0.)}
    for name in report["wood_members"]:
        assert bodies[name] is actual[name]
    original = {c.name:c for c in model.model.connections(model.model.WASHER_MIN,extension=0.)}
    for row in report["connections"]:
        bolt = original[row["name"]]
        assert row["start_xyz_mm"] == bolt.start.toTuple()
        assert row["axis_xyz"] == bolt.direction.toTuple()
        assert row["wood_intervals_underhead_mm"] == [[5.588,43.688],[43.688,81.788]]
        names = row["hardware_bodies"]
        head_volume = math.sqrt(3)/2*model.FLATS**2*model.HEAD_HEIGHT
        diameter = 9.525 if report["variant"] == "smooth" else 7.5692
        if report["variant"] == "smooth":
            shaft_volume = math.pi/4*9.525**2*107.95
            assert row["diameter_transition_underhead_mm"] is None
        else:
            shaft_volume = math.pi/4*(9.525**2*74.6125+7.5692**2*(107.95-74.6125))
            assert row["diameter_transition_underhead_mm"] == 74.6125
            # Transition is inside the outer wood member, not beyond all wood.
            assert row["wood_intervals_underhead_mm"][1][0] < 74.6125 < row["wood_intervals_underhead_mm"][1][1]
        assert bodies[names[0]].Volume() == pytest.approx(head_volume+shaft_volume,rel=1e-9)
        assert bodies[names[-1]].Volume() == pytest.approx(
            (math.sqrt(3)/2*model.FLATS**2-math.pi/4*diameter**2)*model.NUT_HEIGHT,rel=1e-9)
        assert sum(f.geomType()=="PLANE" for f in bodies[names[-1]].Faces()) == 8
        for name in names[1:5]:
            assert bodies[name].Volume() == pytest.approx(math.pi/4*(model.model.WASHER_OD_MAX**2-model.model.WASHER_ID_MIN**2)*2.794)
        tie = row["planned_tied_engagement"]
        assert tie["underhead_interval_mm"] == pytest.approx([87.376,87.376+model.NUT_HEIGHT])
        assert tie["diameter_mm"] == pytest.approx(diameter)
        assert tie["bodies"] == [names[0],names[-1]]
        assert not tie["applied"] and not tie["physical_thread_capacity_verified"]
        bore = cq.Solid.makeCylinder(11.1125/2,bolt.length,bolt.start,bolt.direction)
        assert all(bodies[name].intersect(bore).Volume() < .001 for name in row["members"])
    assert report["maximum_overlap_mm3"] <= .001
    assert len(report["planar_adjacencies"]) == 25
    assert len({frozenset(row["bodies"]) for row in report["planar_adjacencies"]}) == 25
    assert not report["physical_bounds_verified"] and not report["qualified_for_design"]
    assert report["applied_ties"] == report["loads"] == report["boundary_conditions"] == []
    assert "not a manufacturer minimum" in report["limits"]


def test_exclusive_export_and_hashes(prepared,tmp_path,monkeypatch):
    bodies,report = prepared
    monkeypatch.setattr(model,"prepare",lambda *args:(bodies,report.copy()))
    path = model.export(tmp_path/"contact",report["side"],report["variant"])
    saved = json.loads((path/"geometry.json").read_text())
    assert set(saved["step_sha256"]) == {n+".step" for n in bodies}
    for name,sha in saved["step_sha256"].items():
        assert hashlib.sha256((path/name).read_bytes()).hexdigest() == sha
    for name,sha in saved["source_sha256"].items():
        assert hashlib.sha256((path/"launch_sources"/name).read_bytes()).hexdigest() == sha
    for name in report["wood_members"]:
        assert saved["original_part_step_sha256"][name] == saved["step_sha256"][name+".step"]
    with pytest.raises(FileExistsError):
        model.export(path)


def test_invalid_variant():
    with pytest.raises(ValueError,match="smooth or root-reference"):
        model.prepare(variant="qualified-thread")
