"""The layout publication must identify omissions and match generated geometry."""
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import base_frame as model
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.panel_grid_v2 import main_tnut_datums


def test_published_layout_matches_source_and_explicit_scope():
    directory = Path("exports") / model.KEY
    manifest = json.loads((directory / "manifest.json").read_text())
    viewer = json.loads((Path("site/hybrid") / model.KEY / "parts.json").read_text())
    assert viewer["design"] == manifest["design"]
    assert "connections omitted" in viewer["design"]["status"]
    assert viewer["design"]["tnut_row_stations_mm"] == [main_tnut_datums()[f"A{r}"][1] for r in range(1, 13)]
    baseline = json.loads(Path("exports/bearing-lean-frame/manifest.json").read_text())
    assert set(manifest["sources"]) == set(baseline["sources"]) | {
        f"mini_moonboard/{name}.py" for name in ("base_frame", "base_exports", "panel_grid_v2")}
    assert set(manifest["artifacts"]) == {
        model.KEY+suffix for suffix in (".step", "_front.png", "_parts.csv")}
    assert set(manifest["artifacts"]) == {p.name for p in directory.iterdir() if p.name != "manifest.json"}
    expected_meshes = {f"hybrid/{model.KEY}/models/{p['name']}.stl" for p in viewer["parts"]}
    assert {p["path"] for p in viewer["parts"]} == expected_meshes
    assert set(manifest["viewer_artifacts"]) == expected_meshes | {f"hybrid/{model.KEY}/parts.json"}
    for root, category in ((Path("."), "sources"), (directory, "artifacts"), (Path("site"), "viewer_artifacts")):
        for path, digest in manifest[category].items():
            assert hashlib.sha256((root/path).read_bytes()).hexdigest() == digest, path
    parts = model.parts()
    assert len(viewer["parts"]) == len(parts)
    assert {p["name"] for p in viewer["parts"]} == {p.name for p in parts}
    assert all("hardware not designed" in p["fabrication"]["clearance_status"] for p in viewer["parts"])
    by_name = {p.name: p for p in parts}
    for item in viewer["parts"]:
        part = by_name[item["name"]]
        assert item["path"] == f"hybrid/{model.KEY}/models/{part.name}.stl"
        assert item["fabrication"]["dimensions_mm"] == pytest.approx(part.blank)
        assert item["fabrication"]["description"] == part.description
        bounds = exact_bounds(part.shape)
        assert item["viewer_aabb_mm"] == pytest.approx((bounds.xlen, bounds.ylen, bounds.zlen))
        data = (Path("site")/item["path"]).read_bytes()
        count = struct.unpack_from("<I", data, 80)[0]
        assert count > 0 and len(data) == 84+50*count
        origin = tuple((getattr(bounds, axis+"min")+getattr(bounds, axis+"max"))/2 for axis in "xyz")
        lower, upper, volumes = [math.inf]*3, [-math.inf]*3, []
        for triangle in struct.iter_unpack("<12fH", data[84:]):
            vertices = [tuple(triangle[3+3*i+j]-origin[j] for j in range(3)) for i in range(3)]
            a, z, c = vertices
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
    step = cq.importers.importStep(str(directory / f"{model.KEY}.step")).val()
    assert len(step.Solids()) == len(parts)
    assert step.Volume() == pytest.approx(sum(p.shape.Volume() for p in parts), rel=1e-8)

    def fingerprint(solid):
        bounds = exact_bounds(solid)
        return (*solid.centerOfMass(solid).toTuple(), solid.Volume(),
                *[getattr(bounds, axis+end) for axis in "xyz" for end in ("min", "max")])

    actual = [fingerprint(solid) for solid in step.Solids()]
    for part in parts:
        intended = fingerprint(part.shape)
        match = next((i for i, row in enumerate(actual) if all(
            math.isclose(a, z, rel_tol=1e-8, abs_tol=.001)
            for a, z in zip(row, intended, strict=True))), None)
        assert match is not None, part.name
        actual.pop(match)
    assert not actual

    with (directory/f"{model.KEY}_parts.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(parts) and {row["part"] for row in rows} == by_name.keys()
    for row in rows:
        part = by_name[row["part"]]
        assert int(row["layers"]) == part.laminations
        assert row["description"] == part.description
        for axis, value in enumerate(part.blank, 1):
            assert float(row[f"dimension_{axis}_mm"]) == pytest.approx(value)
            assert float(row[f"dimension_{axis}_in"]) == pytest.approx(value/25.4)
