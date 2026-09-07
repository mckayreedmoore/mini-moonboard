"""Square-cut publication geometry, grouped blanks and inspection hole datums."""
import csv
import hashlib
import json
import math
import struct
from collections import defaultdict
from importlib import import_module
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.connection_geometry import material_intervals


@pytest.fixture(scope="module", params=[("easy_frame", "square-cut-bracket"),
                                       ("easy_blocks", "square-cut-wood-blocks")])
def candidate(request):
    module, key = request.param
    return import_module("mini_moonboard."+module), key, Path("exports")/key


def read_rows(directory, key, suffix):
    with (directory/f"{key}_{suffix}.csv").open() as stream:
        return list(csv.DictReader(stream))


def test_export_geometry_inventory_and_source_closure(candidate):
    frame, key, directory = candidate
    manifest = json.loads((directory/"manifest.json").read_text())
    viewer = json.loads((Path("site/hybrid")/key/"parts.json").read_text())
    assert manifest["design"] == viewer["design"]
    assert viewer["design"]["key"] == key
    assert viewer["design"]["baseline"] == "commercial-bracket-mvp"
    assert "NOT build-ready" in viewer["design"]["status"]
    baseline = json.loads(Path("exports/commercial-bracket-mvp/manifest.json").read_text())
    assert set(manifest["sources"]) == set(baseline["sources"]) | {
        f"mini_moonboard/{name}.py" for name in
        ("easy_frame", "easy_blocks", "easy_exports", "connection_geometry")}
    assert set(manifest["artifacts"]) == {key+suffix for suffix in (
        ".step", "_front.png", "_parts.csv", "_connections.csv", "_blank_groups.csv", "_hole_entries.csv")}
    assert set(manifest["artifacts"]) == {p.name for p in directory.iterdir() if p.name != "manifest.json"}
    for root, category in ((Path("."), "sources"), (directory, "artifacts"), (Path("site"), "viewer_artifacts")):
        for name, digest in manifest[category].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
    parts, connections = frame.parts(), frame.connections()
    shapes = {p.name: p.shape for p in parts}
    shapes.update({"fastener_"+c.name: cq.Compound.makeCompound(c.components()) for c in connections})
    assert len(shapes) == len(parts)+len(connections)
    assert len(viewer["parts"]) == len(shapes)
    assert {p["name"] for p in viewer["parts"]} == shapes.keys()
    assert set(manifest["viewer_artifacts"]) == {str(Path("hybrid")/key/"parts.json")} | {p["path"] for p in viewer["parts"]}
    for item in viewer["parts"]:
        data = (Path("site")/item["path"]).read_bytes()
        count = struct.unpack_from("<I", data, 80)[0]
        assert count > 0 and len(data) == 84+50*count
        lower, upper = [math.inf]*3, [-math.inf]*3
        for triangle in struct.iter_unpack("<12fH", data[84:]):
            for axis in range(3):
                coordinates = triangle[3+axis:12:3]
                assert all(math.isfinite(v) for v in coordinates)
                lower[axis] = min(lower[axis], *coordinates)
                upper[axis] = max(upper[axis], *coordinates)
        bounds = exact_bounds(shapes[item["name"]])
        assert lower+upper == pytest.approx([getattr(bounds, axis+end)
            for end in ("min", "max") for axis in "xyz"], abs=.501), item["name"]
        assert item["viewer_aabb_mm"] == pytest.approx([bounds.xlen, bounds.ylen, bounds.zlen], abs=1e-5)
    step = cq.importers.importStep(str(directory/f"{key}.step")).val()
    assert len(step.Solids()) == sum(len(shape.Solids()) for shape in shapes.values())
    assert step.Volume() == pytest.approx(sum(shape.Volume() for shape in shapes.values()), rel=1e-8)
    def fingerprint(solid):
        bounds = exact_bounds(solid)
        return (*solid.centerOfMass(solid).toTuple(), solid.Volume(),
                *[getattr(bounds, axis+end) for axis in "xyz" for end in ("min", "max")])
    actual = [fingerprint(solid) for solid in step.Solids()]
    for shape in shapes.values():
        for solid in shape.Solids():
            intended = fingerprint(solid)
            match = next((i for i, row in enumerate(actual) if all(
                math.isclose(a, z, rel_tol=1e-8, abs_tol=.001)
                for a, z in zip(row, intended, strict=True))), None)
            assert match is not None, intended
            actual.pop(match)
    assert not actual


def test_grouped_blanks_and_connection_schedules(candidate):
    frame, key, directory = candidate
    parts = {p.name: p for p in frame.parts()}
    rows = read_rows(directory, key, "parts")
    assert len(rows) == len(parts) and {r["part"] for r in rows} == parts.keys()
    for row in rows:
        part = parts[row["part"]]
        assert int(row["layers"]) == part.laminations
        for axis, value in enumerate(part.blank, 1):
            assert float(row[f"dimension_{axis}_mm"]) == pytest.approx(value)
            assert float(row[f"dimension_{axis}_in"]) == pytest.approx(value/25.4)
    expected = defaultdict(set)
    for part in parts.values():
        if not part.name.startswith("clip_"):
            expected[tuple(round(v, 6) for v in part.blank)].add(part.name)
    groups = read_rows(directory, key, "blank_groups")
    assert len(groups) == len(expected)
    seen = set()
    for row in groups:
        dimensions = tuple(float(row[f"dimension_{axis}_mm"]) for axis in (1, 2, 3))
        assert dimensions in expected and dimensions not in seen
        seen.add(dimensions)
        names = row["parts"].split(" + ")
        assert len(names) == len(set(names)) == int(row["quantity"])
        assert set(names) == expected[dimensions]
        assert [float(row[f"dimension_{axis}_in"]) for axis in (1, 2, 3)] == pytest.approx([v/25.4 for v in dimensions])
        assert "Blank grouping only" in row["status"]
    connections = {c.name: c for c in frame.connections()}
    rows = read_rows(directory, key, "connections")
    assert len(rows) == len(connections) and {r["connection"] for r in rows} == connections.keys()
    for row in rows:
        c = connections[row["connection"]]
        assert row["kind"] == c.kind and row["members"].split(" + ") == list(c.members)
        for axis, value in zip("xyz", c.start.toTuple(), strict=True):
            assert float(row[axis+"_mm"]) == pytest.approx(value)
            assert float(row[axis+"_in"]) == pytest.approx(value/25.4)
        assert [float(row["axis_"+axis]) for axis in "xyz"] == pytest.approx(c.direction.toTuple())
        for field, value in (("length", c.length), ("diameter", c.diameter), ("grip", c.grip)):
            assert float(row[field+"_mm"]) == pytest.approx(value)
            assert float(row[field+"_in"]) == pytest.approx(value/25.4)


def test_hole_entries_reconstruct_each_actual_net_material_run(candidate):
    frame, key, directory = candidate
    rows = read_rows(directory, key, "hole_entries")
    grouped = defaultdict(list)
    for row in rows:
        assert "NOT machining approval" in row["status"]
        assert not row["part"].startswith("clip_")
        grouped[(row["part"], row["connection"])].append(row)
    raw = {p.name: p for p in frame.parts(False)}
    origin = b.point(0, 0, 0)
    axes = (cq.Vector(1, 0, 0), cq.Vector(0, math.sin(math.radians(40)), math.cos(math.radians(40))),
            cq.Vector(0, -math.cos(math.radians(40)), math.sin(math.radians(40))))
    expected_keys = set()
    for c in frame.connections():
        for name in c.members:
            if name.startswith("clip_"):
                continue
            shape = raw[name].shape
            intervals = material_intervals(shape, c.start, c.direction, 0., c.length)
            if intervals:
                expected_keys.add((name, c.name))
            records = grouped.get((name, c.name), [])
            assert len(records) == len(intervals), (name, c.name)
            local = cq.Plane(origin=origin, xDir=axes[0], normal=axes[2]).toLocalCoords(shape)
            bound = exact_bounds(local)
            minima = [bound.xmin, bound.ymin, bound.zmin]
            reconstructed = []
            for row in records:
                offsets = [float(row[f"from_min_{axis}_mm"]) for axis in ("x", "s", "n")]
                assert [float(row[f"from_min_{axis}_in"]) for axis in ("x", "s", "n")] == pytest.approx([v/25.4 for v in offsets])
                point = origin
                for axis, low, offset in zip(axes, minima, offsets, strict=True):
                    point = point+axis*(low+offset)
                distance = (point-c.start).dot(c.direction)
                assert (point-c.start-c.direction*distance).Length < 1e-6
                assert [float(row["axis_"+axis]) for axis in ("x", "s", "n")] == pytest.approx([c.direction.dot(axis) for axis in axes])
                reconstructed.append((distance, distance+float(row["material_run_mm"])))
            for actual, expected in zip(sorted(reconstructed), intervals, strict=True):
                assert actual == pytest.approx(expected, abs=1e-6), (name, c.name)
    assert grouped.keys() == expected_keys
