"""Whole-member geometry/ownership checks; no solved contact or strength result."""
import hashlib
import json

import cadquery as cq
import pytest

from fea import compact_leg_joint_geometry as model


@pytest.fixture(scope="module", params=("left", "right"))
def prepared(request):
    return model.prepare(request.param)


def test_complete_members_four_bores_and_separate_stacks(prepared):
    bodies, report = prepared
    side = report["side"]
    original = {p.name: p.shape for p in model.model.parts(extension=0.)}
    assert len(bodies) == report["body_count"] == 26
    assert len(report["connections"]) == 4
    assert not report["cropped"] and report["cut_planes"] == []
    assert report["loads"] == report["boundary_conditions"] == []
    assert not report["qualified_for_design"] and not report["hardware_contact_geometry_verified"]
    assert len(report["required_contact_geometry_replacements"]) == 6
    for name in report["wood_members"]:
        assert bodies[name] is original[name]
        assert report["bodies"][name]["source_part_name"] == name
    bolts = {c.name:c for c in model.model.connections(extension=0.) if c.name.startswith(f"lumber_leg_bolt_{side}_")}
    for row in report["connections"]:
        bolt = bolts[row["name"]]
        assert row["start_xyz_mm"] == bolt.start.toTuple()
        assert row["axis_xyz"] == bolt.direction.toTuple()
        assert len(row["hardware_bodies"]) == 6
        assert row["length_mm"] == 107.95 and row["grip_mm"] == 76.2
        assert sum("washer" in n for n in row["hardware_bodies"]) == 4
        components = bolt.components()
        assert bodies[bolt.name+"_bolt"].Volume() == pytest.approx(components[0].Volume()+components[5].Volume())
        for name in row["members"]:
            bore = cq.Solid.makeCylinder(11.1125/2, bolt.length, bolt.start, bolt.direction)
            assert bodies[name].intersect(bore).Volume() < .001
    assert len(report["planar_adjacencies"]) == 25
    for pair in report["planar_adjacencies"]:
        assert set(pair["bodies"]) <= bodies.keys()
        assert sum(f["area_mm2"] for f in pair["source_faces"]) > 0
    along = cq.Vector(report["local_axes"]["leg_grain"])
    across = cq.Vector(report["local_axes"]["leg_across_grain"])
    assert along.Length == pytest.approx(1) and across.Length == pytest.approx(1)
    assert along.dot(across) == pytest.approx(0, abs=1e-12)
    assert report["maximum_overlap_mm3"] <= .001


def test_exclusive_step_export_with_original_part_and_source_hashes(prepared, tmp_path, monkeypatch):
    bodies, report = prepared
    monkeypatch.setattr(model, "prepare", lambda side: (bodies, report.copy()))
    directory = model.export(tmp_path/"joint", report["side"])
    saved = json.loads((directory/"geometry.json").read_text())
    assert set(saved["step_sha256"]) == {name+".step" for name in bodies}
    for name, sha in saved["step_sha256"].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha
    for name, sha in saved["original_part_step_sha256"].items():
        shape = cq.importers.importStep(str(directory/(name+".step"))).val()
        assert shape.Volume() == pytest.approx(bodies[name].Volume(), rel=1e-9)
        assert sha == saved["step_sha256"][name+".step"]
    for name, sha in saved["source_sha256"].items():
        assert hashlib.sha256((directory/"launch_sources"/name).read_bytes()).hexdigest() == sha
    with pytest.raises(FileExistsError):
        model.export(directory)


def test_invalid_side_rejected():
    with pytest.raises(ValueError, match="left or right"):
        model.prepare("front")


def test_changed_parent_source_rejected_before_geometry(tmp_path, monkeypatch):
    parent = json.loads(model.PARENT.read_text())
    parent["sources"]["mini_moonboard/leg_hardware_trial.py"] = "0"*64
    path = tmp_path/"manifest.json"
    path.write_text(json.dumps(parent))
    monkeypatch.setattr(model, "PARENT", path)
    with pytest.raises(ValueError, match="Parent hardware geometry source changed"):
        model.prepare()
