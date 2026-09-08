"""Published timber solids, hardware, units and source closure match the model."""
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import timber_frame as model
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.panel_grid_v2 import main_tnut_datums


@pytest.fixture(scope="module")
def publication():
    directory = Path("exports") / model.KEY
    manifest = json.loads((directory / "manifest.json").read_text())
    viewer = json.loads((Path("site/hybrid") / model.KEY / "parts.json").read_text())
    parts = {p.name: p for p in model.parts()}
    connections = model.connections()
    assert len(parts) == 43 and len(connections) == 176
    for c in connections:
        name = "fastener_"+c.name
        parts[name] = model.b.Part(name, cq.Compound.makeCompound(c.components()),
            (c.length, c.diameter, c.diameter), c.product_status+"; "+" + ".join(c.members), 1)
    assert len(parts) == 219
    return directory, manifest, viewer, parts


def test_publication_inventory_scope_and_source_closure(publication):
    directory, manifest, viewer, parts = publication
    assert viewer["design"] == manifest["design"]
    assert viewer["design"]["key"] == model.KEY
    assert "NOT build-ready" in viewer["design"]["status"]
    assert "joint resistance unqualified" in viewer["design"]["status"]
    assert "No transferred FEA" in viewer["design"]["description"]
    assert viewer["design"]["tnut_row_stations_mm"] == [main_tnut_datums()[f"A{r}"][1] for r in range(1, 13)]
    baseline = json.loads(Path("exports/base-bearing-concept/manifest.json").read_text())
    assert set(manifest["sources"]) == set(baseline["sources"]) | {
        "mini_moonboard/timber_frame.py", "mini_moonboard/timber_connections.py",
        "mini_moonboard/timber_exports.py", "docs/ml24z-reference.json"}
    assert all(manifest["sources"][path] == sha for path, sha in baseline["sources"].items())
    assert set(manifest["artifacts"]) == {model.KEY+suffix for suffix in
        (".step", "_front.png", "_parts.csv", "_connections.csv")}
    assert set(manifest["artifacts"]) == {p.name for p in directory.iterdir() if p.name != "manifest.json"}
    assert len(viewer["parts"]) == len(parts)
    assert {p["name"] for p in viewer["parts"]} == parts.keys()
    expected_meshes = {f"hybrid/{model.KEY}/models/{name}.stl" for name in parts}
    assert {p["path"] for p in viewer["parts"]} == expected_meshes
    assert set(manifest["viewer_artifacts"]) == expected_meshes | {f"hybrid/{model.KEY}/parts.json"}
    assert {str(p.relative_to("site")) for p in (Path("site/hybrid")/model.KEY/"models").iterdir()} == expected_meshes
    for root, category in ((Path("."), "sources"), (directory, "artifacts"), (Path("site"), "viewer_artifacts")):
        for path, digest in manifest[category].items():
            assert hashlib.sha256((root/path).read_bytes()).hexdigest() == digest, path


def test_viewer_meshes_and_step_match_actual_solids(publication):
    directory, _, viewer, parts = publication
    connections = {"fastener_"+c.name: c for c in model.connections()}
    for item in viewer["parts"]:
        part = parts[item["name"]]
        assert item["fabrication"]["dimensions_mm"] == pytest.approx(part.blank)
        assert item["fabrication"]["description"] == part.description
        assert item["fabrication"]["kind"] == (connections[part.name].kind if part.name in connections else "part")
        assert "fit and strength require qualification" in item["fabrication"]["clearance_status"]
        bounds = exact_bounds(part.shape)
        assert item["viewer_aabb_mm"] == pytest.approx((bounds.xlen, bounds.ylen, bounds.zlen))
        data = (Path("site")/item["path"]).read_bytes()
        count = struct.unpack_from("<I", data, 80)[0]
        assert count > 0 and len(data) == 84+50*count
        origin = tuple((getattr(bounds, axis+"min")+getattr(bounds, axis+"max"))/2 for axis in "xyz")
        lower, upper, volumes = [math.inf]*3, [-math.inf]*3, []
        for triangle in struct.iter_unpack("<12fH", data[84:]):
            a, z, c = [tuple(triangle[3+3*i+j]-origin[j] for j in range(3)) for i in range(3)]
            cross = (z[1]*c[2]-z[2]*c[1], z[2]*c[0]-z[0]*c[2], z[0]*c[1]-z[1]*c[0])
            volumes.append(sum(a[i]*cross[i] for i in range(3))/6)
            for axis in range(3):
                coordinates = triangle[3+axis:12:3]
                assert all(math.isfinite(v) for v in coordinates)
                lower[axis] = min(lower[axis], *coordinates)
                upper[axis] = max(upper[axis], *coordinates)
        tolerance = .001 if part.name.startswith(("main_", "kicker_")) else .02
        assert abs(math.fsum(volumes)) == pytest.approx(part.shape.Volume(), rel=tolerance, abs=.01), part.name
        assert lower+upper == pytest.approx([getattr(bounds, axis+end)
            for end in ("min", "max") for axis in "xyz"], abs=.501), part.name
    aggregate = exact_bounds(cq.Compound.makeCompound([p.shape for p in parts.values()]))
    for index, end in enumerate(("min", "max")):
        assert viewer["bounds_mm"][index] == pytest.approx([getattr(aggregate, axis+end) for axis in "xyz"])
    step = cq.importers.importStep(str(directory / f"{model.KEY}.step")).val()
    assert len(step.Solids()) == sum(len(p.shape.Solids()) for p in parts.values())
    assert step.Volume() == pytest.approx(sum(p.shape.Volume() for p in parts.values()), rel=1e-8)

    def fingerprint(solid):
        bounds = exact_bounds(solid)
        return (*solid.centerOfMass(solid).toTuple(), solid.Volume(),
                *[getattr(bounds, axis+end) for axis in "xyz" for end in ("min", "max")])

    actual = [fingerprint(solid) for solid in step.Solids()]
    for part in parts.values():
        for solid in part.shape.Solids():
            intended = fingerprint(solid)
            match = next((i for i, row in enumerate(actual) if all(
                math.isclose(a, z, rel_tol=1e-8, abs_tol=.001)
                for a, z in zip(row, intended, strict=True))), None)
            assert match is not None, part.name
            actual.pop(match)
    assert not actual


def test_metric_imperial_parts_and_connection_tables(publication):
    directory, _, _, parts = publication
    with (directory/f"{model.KEY}_parts.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(parts) and {row["part"] for row in rows} == parts.keys()
    for row in rows:
        part = parts[row["part"]]
        assert int(row["layers"]) == part.laminations
        assert row["description"] == part.description
        for axis, value in enumerate(part.blank, 1):
            assert float(row[f"dimension_{axis}_mm"]) == pytest.approx(value)
            assert float(row[f"dimension_{axis}_in"]) == pytest.approx(value/25.4)
    with (directory/f"{model.KEY}_connections.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    connections = {c.name: c for c in model.connections()}
    assert len(rows) == len(connections) and {row["connection"] for row in rows} == connections.keys()
    for row in rows:
        c = connections[row["connection"]]
        assert row["kind"] == c.kind
        assert row["members"] == " + ".join(c.members)
        assert row["status"] == c.product_status
        for label, value in (("length", c.length), ("diameter", c.diameter)):
            assert float(row[label+"_mm"]) == pytest.approx(value)
            assert float(row[label+"_in"]) == pytest.approx(value/25.4)
        assert float(row["grip_mm"]) == pytest.approx(c.grip)
        assert [float(row[axis+"_mm"]) for axis in "xyz"] == pytest.approx(c.start.toTuple())
        assert [float(row["axis_"+axis]) for axis in "xyz"] == pytest.approx(c.direction.toTuple())
