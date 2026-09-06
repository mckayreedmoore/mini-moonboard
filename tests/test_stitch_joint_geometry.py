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
