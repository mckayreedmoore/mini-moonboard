"""The selectable development assembly must match its separate CAD artifacts."""
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import joint_frame
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.joint_exports import DESIGN, KEY


def test_joint_candidate_viewer_and_exports_match_geometry():
    directory = Path("exports/joint-development")
    manifest = json.loads((directory/"manifest.json").read_text())
    viewer = json.loads((Path("site/hybrid")/KEY/"parts.json").read_text())
    assert viewer["design"] == manifest["design"] == DESIGN
    assert DESIGN["baseline"] == "2x8-foot100"
    assert set(manifest["sources"]) == {f"mini_moonboard/{name}.py" for name in (
        "joint_exports", "joint_frame", "footprint_frame", "shallow_frame", "hybrid_frame",
        "hybrid", "box_frame", "model", "panel_grid", "box_exports", "export", "raster")}
    assert set(manifest["artifacts"]) == {KEY+suffix for suffix in (
        ".step", "_front.png", "_rear.png", "_parts.csv", "_connections.csv")}
    assert set(manifest["artifacts"]) == {p.name for p in directory.iterdir() if p.name != "manifest.json"}
    for root, key in ((Path("."), "sources"), (directory, "artifacts"), (Path("site"), "viewer_artifacts")):
        for filename, digest in manifest[key].items():
            assert hashlib.sha256((root/filename).read_bytes()).hexdigest() == digest, filename
    parts, connections = joint_frame.parts(), joint_frame.connections()
    expected = {p.name: (p.shape, p.blank) for p in parts}
    expected.update({"fastener_"+c.name: (cq.Compound.makeCompound(c.components()),
                     (c.length, c.diameter, c.diameter)) for c in connections})
    assert {p["name"] for p in viewer["parts"]} == set(expected)
    assert len(viewer["parts"]) == len(expected)
    assert set(manifest["viewer_artifacts"]) == {str(Path("hybrid")/KEY/"parts.json")} | {p["path"] for p in viewer["parts"]}
    for item in viewer["parts"]:
        assert item["fabrication"]["dimensions_mm"] == pytest.approx(expected[item["name"]][1])
        assert "NOT structural approval" in item["fabrication"]["clearance_status"]
        data = (Path("site")/item["path"]).read_bytes()
        triangles = struct.unpack_from("<I", data, 80)[0]
        assert triangles > 0 and len(data) == 84+50*triangles
        lower, upper = [math.inf]*3, [-math.inf]*3
        for triangle in struct.iter_unpack("<12fH", data[84:]):
            for axis in range(3):
                coordinates = triangle[3+axis:12:3]
                assert all(map(math.isfinite, coordinates))
                lower[axis] = min(lower[axis], *coordinates)
                upper[axis] = max(upper[axis], *coordinates)
        bounds = exact_bounds(expected[item["name"]][0])
        # CAD STL export uses 0.5 mm tessellation tolerance; include float32
        # rounding at this assembly's metre-scale world coordinates.
        assert lower+upper == pytest.approx([getattr(bounds, axis+end)
            for end in ("min", "max") for axis in "xyz"], abs=.501)
        assert item["viewer_aabb_mm"] == pytest.approx([bounds.xlen, bounds.ylen, bounds.zlen], abs=1e-5)
    with (directory/f"{KEY}_parts.csv").open() as stream:
        rows = {r["part"]: r for r in csv.DictReader(stream)}
    assert rows.keys() == {p.name for p in parts}
    for part in parts:
        row = rows[part.name]
        assert int(row["layers"]) == part.laminations
        for unit, divisor in (("mm", 1), ("in", 25.4)):
            assert [float(row[f"dimension_{axis}_{unit}"]) for axis in (1, 2, 3)] == pytest.approx([v/divisor for v in part.blank])
    with (directory/f"{KEY}_connections.csv").open() as stream:
        rows = {r["connection"]: r for r in csv.DictReader(stream)}
    assert rows.keys() == {c.name for c in connections}
    for connection in connections:
        row = rows[connection.name]
        assert [float(row[f"{axis}_mm"]) for axis in "xyz"] == pytest.approx(connection.start.toTuple())
        assert [float(row[f"axis_{axis}"]) for axis in "xyz"] == pytest.approx(connection.direction.toTuple())
        assert [float(row[field]) for field in ("length_mm", "length_in", "diameter_mm", "grip_mm")] == pytest.approx([
            connection.length, connection.length/25.4, connection.diameter, connection.grip])
    step = cq.importers.importStep(str(directory/f"{KEY}.step")).val()
    assert len(step.Solids()) == sum(len(shape.Solids()) for shape, _ in expected.values())
    assert step.Volume() == pytest.approx(sum(shape.Volume() for shape, _ in expected.values()), rel=1e-8)
    # Match spatial fingerprints, not just total volume: displaced parts retain
    # their volume, and STEP can reorder geometrically identical hardware.
    def fingerprint(solid):
        bounds = solid.BoundingBox()
        return (*solid.centerOfMass(solid).toTuple(), solid.Volume(),
                *[getattr(bounds, axis+end) for axis in "xyz" for end in ("min", "max")])
    actual = [fingerprint(s) for s in step.Solids()]
    for shape, _ in expected.values():
        for solid in shape.Solids():
            intended = fingerprint(solid)
            match = next((i for i, row in enumerate(actual) if all(
                math.isclose(a, b, rel_tol=1e-8, abs_tol=.001)
                for a, b in zip(row, intended, strict=True))), None)
            assert match is not None, intended
            actual.pop(match)
    assert not actual
