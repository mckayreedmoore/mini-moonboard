"""Geometry ownership and nominal stack only; no mechanical resistance claim."""
import hashlib
import json
import math

import cadquery as cq
import pytest

from fea.stitch_joint_geometry import (
    export,
    solids,
    source_snapshot,
    stitches,
    validate,
    validate_disjoint,
)
from mini_moonboard.box_exports import exact_bounds


@pytest.fixture(scope="module")
def bodies():
    return solids()


def test_actual_separate_stitch_geometry(bodies):
    report = validate(bodies)
    assert report["body_count"] == 14
    assert report["locked_threads"] is False
    assert len(report["nominal_touching_pairs"]) == 19
    for name in ("leg_right_inner", "leg_right_outer"):
        assert len(report["parts"][name]["bore_names"]) == 7
        assert report["parts"][name]["floor_area_mm2"] > 0
    for c in stitches():
        p = c.name + "_"
        for role, radius, length, offset in (("washer_inner", 12.7, 2, 0),
                                             ("washer_outer", 12.7, 2, 40.1),
                                             ("nut", 9, 9, 42.1)):
            shape = bodies[p + role]
            assert shape.Volume() == pytest.approx(math.pi * (radius**2 - 4.7625**2) * length)
            assert exact_bounds(shape).xmin == pytest.approx(c.start.x + offset)
            assert exact_bounds(shape).xlen == pytest.approx(length)
        assert bodies[p + "bolt"].Volume() == pytest.approx(
            math.pi * (4.7625**2 * 57.15 + 9**2 * 6))
        assert exact_bounds(bodies[p + "bolt"]).xmin == pytest.approx(c.start.x - 6)


def test_positive_volume_overlap_is_rejected():
    box = cq.Solid.makeBox(2, 2, 2)
    with pytest.raises(ValueError, match="Positive-volume overlap"):
        validate_disjoint({"first": box, "second": box.translate((1, 0, 0))})
    assert validate_disjoint({"first": box, "touching": box.translate((2, 0, 0))}) == 0


def test_export_roundtrip_and_source_provenance(bodies, tmp_path):
    directory = export(bodies, tmp_path)
    second = export(bodies, tmp_path)
    assert directory != second
    record = json.loads((directory / "geometry.json").read_text())
    assert record["source_binding"] == "export interval only"
    assert len(record["step_sha256"]) == 14
    for name, digest in record["source_sha256"].items():
        assert not name.startswith("/")
        assert hashlib.sha256((directory / "launch_sources" / name).read_bytes()).hexdigest() == digest
    roundtrip = {}
    for name, digest in record["step_sha256"].items():
        path = directory / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        shape = cq.importers.importStep(str(path)).val()
        roundtrip[path.stem] = shape
        assert shape.Volume() == pytest.approx(bodies[path.stem].Volume(), abs=.001)
    assert validate(roundtrip)["body_count"] == 14
    with pytest.raises(ValueError, match="Expected two plies"):
        export({}, tmp_path)
    changed = source_snapshot()
    changed["fea/stitch_joint_geometry.py"] += b"changed"
    with pytest.raises(ValueError, match="Source drift"):
        export(bodies, tmp_path, sources_before=changed)


def test_locked_threads_preserve_geometry_and_separate_washers(bodies, tmp_path):
    locked = solids(locked_threads=True)
    report = validate(locked, locked_threads=True)
    assert report["body_count"] == 11
    assert report["locked_threads"] is True
    assert report["geometry_variant"] == "locked-thread-11-body"
    assert report["preload_assigned"] is False
    assert len(report["separate_washer_bodies"]) == 6
    assert len(report["nominal_touching_pairs"]) == 13
    assert report["union_volume_mm3"] == pytest.approx(sum(s.Volume() for s in bodies.values()), abs=.001)
    for c in stitches():
        prefix = c.name + "_"
        core = locked[prefix + "bolt_nut"]
        assert len(core.Solids()) == 1
        assert core.Volume() == pytest.approx(bodies[prefix + "bolt"].Volume() + bodies[prefix + "nut"].Volume())
        assert prefix + "bolt" not in locked and prefix + "nut" not in locked
        for role in ("washer_inner", "washer_outer"):
            washer = locked[prefix + role]
            assert washer.cut(bodies[prefix + role]).Volume() < .001
            assert washer.intersect(core).Volume() < .001
    with pytest.raises(ValueError, match="Expected two plies"):
        validate(locked)
    directory = export(locked, tmp_path, locked_threads=True)
    record = json.loads((directory / "geometry.json").read_text())
    assert len(record["step_sha256"]) == 11
    assert record["locked_threads"] is True
    source = directory / "launch_sources" / "fea/stitch_joint_geometry.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == record["source_sha256"]["fea/stitch_joint_geometry.py"]
    roundtrip = {path.stem: cq.importers.importStep(str(path)).val() for path in directory.glob("*.step")}
    assert validate(roundtrip, locked_threads=True)["body_count"] == 11
    bad = dict(locked)
    first = stitches()[0].name + "_washer_inner"
    bad[first] = bad[first].translate((1, 0, 0))
    with pytest.raises(ValueError, match="Positive-volume overlap"):
        validate(bad, locked_threads=True)
