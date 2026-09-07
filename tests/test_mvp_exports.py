"""Published MVP inventories and exact source/artifact correspondence."""
import csv
import hashlib
import json
import math
import struct
from importlib import import_module
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard.box_exports import exact_bounds


@pytest.mark.parametrize("module,key", [("wood_mvp", "wood-first-mvp"),
                                        ("bracket_mvp", "commercial-bracket-mvp")])
def test_mvp_export_inventory_and_sources(module, key):
    frame = import_module("mini_moonboard."+module)
    directory = Path("exports")/key
    manifest = json.loads((directory/"manifest.json").read_text())
    viewer = json.loads((Path("site/hybrid")/key/"parts.json").read_text())
    assert manifest["design"] == viewer["design"]
    assert viewer["design"]["key"] == key
    assert "NOT build-ready" in viewer["design"]["status"]
    for root, category in ((Path("."), "sources"), (directory, "artifacts"), (Path("site"), "viewer_artifacts")):
        for name, expected in manifest[category].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest() == expected, name
    parts, connections = frame.parts(), frame.connections()
    expected_names = {p.name for p in parts} | {"fastener_"+c.name for c in connections}
    assert len(viewer["parts"]) == len(expected_names)
    assert {p["name"] for p in viewer["parts"]} == expected_names
    assert set(manifest["artifacts"]) == {key+s for s in (".step", "_front.png", "_parts.csv", "_connections.csv")}
    assert set(manifest["viewer_artifacts"]) == {str(Path("hybrid")/key/"parts.json")} | {p["path"] for p in viewer["parts"]}
    shapes = {p.name: p.shape for p in parts}
    shapes.update({"fastener_"+c.name: cq.Compound.makeCompound(c.components()) for c in connections})
    for item in viewer["parts"]:
        data = (Path("site")/item["path"]).read_bytes()
        count = struct.unpack_from("<I", data, 80)[0]
        assert count > 0 and len(data) == 84+50*count, item["name"]
        lower, upper = [math.inf]*3, [-math.inf]*3
        for triangle in struct.iter_unpack("<12fH", data[84:]):
            for axis in range(3):
                coordinates = triangle[3+axis:12:3]
                assert all(math.isfinite(v) for v in coordinates), item["name"]
                lower[axis] = min(lower[axis], *coordinates)
                upper[axis] = max(upper[axis], *coordinates)
        bounds = exact_bounds(shapes[item["name"]])
        assert lower+upper == pytest.approx([getattr(bounds, axis+end)
            for end in ("min", "max") for axis in "xyz"], abs=.501), item["name"]
        assert item["viewer_aabb_mm"] == pytest.approx(
            [bounds.xlen, bounds.ylen, bounds.zlen], abs=1e-5), item["name"]
    # As in the existing development export gate: compare independent imported
    # STEP solids by spatial fingerprints, since the importer may reorder them.
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
                math.isclose(a, b, rel_tol=1e-8, abs_tol=.001)
                for a, b in zip(row, intended, strict=True))), None)
            assert match is not None, intended
            actual.pop(match)
    assert not actual
    with (directory/f"{key}_parts.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(parts)
    by_name = {p.name: p for p in parts}
    for row in rows:
        part = by_name[row["part"]]
        for i, dimension in enumerate(part.blank, 1):
            assert float(row[f"dimension_{i}_mm"]) == pytest.approx(dimension)
            assert float(row[f"dimension_{i}_in"]) == pytest.approx(dimension/25.4)
    with (directory/f"{key}_connections.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(connections)
    by_name = {c.name: c for c in connections}
    for row in rows:
        connection = by_name[row["connection"]]
        assert row["members"].split(" + ") == list(connection.members)
        assert [float(row[f"{axis}_mm"]) for axis in "xyz"] == pytest.approx(connection.start.toTuple())
        assert float(row["length_mm"]) == pytest.approx(connection.length)
        assert float(row["length_in"]) == pytest.approx(connection.length/25.4)
        assert [float(row[f"{axis}_in"]) for axis in "xyz"] == pytest.approx(
            [v/25.4 for v in connection.start.toTuple()])
        for field in ("diameter", "grip"):
            assert float(row[field+"_mm"]) == pytest.approx(getattr(connection, field))
            assert float(row[field+"_in"]) == pytest.approx(getattr(connection, field)/25.4)
