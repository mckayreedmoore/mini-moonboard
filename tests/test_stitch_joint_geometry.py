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


def test_catalog_washer_variant_changes_only_exact_bore_annuli(tmp_path):
    legacy = solids(locked_threads=True)
    catalog = solids(locked_threads=True, catalog_washer_bore=True)
    report = validate(catalog, locked_threads=True, catalog_washer_bore=True)
    assert report["geometry_variant"] == "locked-thread-fw38-minimum-bore-11-body"
    assert report["catalog_washer_bore"] is True
    assert report["body_count"] == 11
    dimensions = report["catalog_washer"]
    assert dimensions["minimum_nominal_radial_gap_mm"] == pytest.approx(.7366)
    assert dimensions["purchased_or_measured"] is False
    removed_one = math.pi * (5.4991**2 - 4.7625**2) * 2
    assert dimensions["removed_volume_all_six_washers_mm3"] == pytest.approx(6 * removed_one, abs=.001)
    for name, original in legacy.items():
        modified = catalog[name]
        assert modified.cut(original).Volume() < .001
        if "_washer_" not in name:
            assert original.cut(modified).Volume() < .001
    for c in stitches():
        assert next(s for s in report["stitches"] if s["name"] == c.name)["washer_bore_diameter_mm"] == 10.9982
        for role, offset in (("washer_inner", 0), ("washer_outer", 40.1)):
            name = c.name + "_" + role
            washer = catalog[name]
            origin = c.start + cq.Vector(offset, 0, 0)
            bore = cq.Solid.makeCylinder(5.4991, 2, origin, cq.Vector(1, 0, 0))
            expected_removed = bore.cut(cq.Solid.makeCylinder(4.7625, 2, origin, cq.Vector(1, 0, 0)))
            removed = legacy[name].cut(washer)
            assert removed.Volume() == pytest.approx(removed_one, abs=.001)
            assert removed.cut(expected_removed).Volume() < .001
            assert expected_removed.cut(removed).Volume() < .001
            assert washer.intersect(bore).Volume() < .001
            b = exact_bounds(washer)
            assert (b.xmin, b.xlen, b.ylen, b.zlen) == pytest.approx((origin.x, 2, 25.4, 25.4))
            bearing = [f for f in washer.Faces() if f.geomType() == "PLANE"]
            assert len(bearing) == 2
            assert all(f.Area() == pytest.approx(math.pi * (12.7**2 - 5.4991**2)) for f in bearing)
            for x in (origin.x, origin.x + 2):
                assert any(abs(exact_bounds(f).xmin - x) < 1e-5 for f in bearing)
    with pytest.raises(ValueError, match="changed nominal geometry"):
        validate(catalog, locked_threads=True)
    with pytest.raises(ValueError, match="removed annulus"):
        validate(legacy, locked_threads=True, catalog_washer_bore=True)
    bad = dict(catalog)
    name = stitches()[0].name + "_washer_inner"
    bad[name] = bad[name].translate((-.1, 0, 0))
    with pytest.raises(ValueError, match="Positive-volume overlap"):
        validate(bad, locked_threads=True, catalog_washer_bore=True)
    directory = export(catalog, tmp_path, locked_threads=True, catalog_washer_bore=True)
    record = json.loads((directory / "geometry.json").read_text())
    assert record["catalog_washer"] == dimensions
    assert len(record["step_sha256"]) == 11
    roundtrip = {p.stem: cq.importers.importStep(str(p)).val() for p in directory.glob("*.step")}
    assert validate(roundtrip, locked_threads=True, catalog_washer_bore=True)["body_count"] == 11


def test_catalog_variant_requires_explicit_thread_choice():
    with pytest.raises(ValueError, match="requires explicit locked threads"):
        solids(catalog_washer_bore=True)
    with pytest.raises(ValueError, match="requires explicit locked threads"):
        validate({}, catalog_washer_bore=True)
