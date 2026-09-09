"""Portable viewer-package checks: no solver or full CAD rebuild required."""
import json
from pathlib import Path

import pytest

from mini_moonboard import lumber_leg_exports as exports
from mini_moonboard import lumber_leg_frame as model


@pytest.mark.parametrize("size,extension", [(s, e) for s in model.WIDTHS for e in model.EXTENSIONS])
def test_variant_package(size, extension):
    key = exports.key(size, extension)
    directory = Path("site/hybrid")/key
    data = json.loads((directory/"parts.json").read_text())
    manifest = json.loads((directory/"manifest.json").read_text())
    parent = json.loads(exports.VIEWER.read_text())
    inherited = {p["name"]: p for p in parent["parts"] if not exports.replaced(p["name"])}
    items = {p["name"]: p for p in data["parts"]}
    assert len(data["parts"]) == len(items) == 283
    assert manifest["body_count"] == 101
    assert manifest["connection_count"] == 182
    assert manifest["new_mesh_count"] == 12
    assert manifest["reused_mesh_count"] == len(inherited) == 271
    assert {name: items[name] for name in inherited} == inherited
    changed = set(items)-inherited.keys()
    assert changed == {f"{prefix}_{side}" for prefix in ("base_side", "lumber_leg")
                       for side in ("left", "right")} | {
        f"fastener_lumber_leg_bolt_{side}_{i}" for side in ("left", "right") for i in range(1, 5)}
    assert {p.name for p in (directory/"models").iterdir()} == {name+".stl" for name in changed}
    for name in changed:
        item = items[name]
        assert item["path"] == f"hybrid/{key}/models/{name}.stl"
        fabrication = item["fabrication"]
        assert fabrication["dimensions_imperial"] == pytest.approx([v/25.4 for v in fabrication["dimensions_mm"]])
        assert "NOT build-ready" in fabrication["clearance_status"]
    for side in ("left", "right"):
        assert items[f"lumber_leg_{side}"]["fabrication"]["dimensions_mm"][1:] == [model.WIDTHS[size], 38.1]
    assert len([p for p in items if p.startswith("fastener_")]) == 182
    assert not any(p.startswith(("leg_", "fastener_leg_stitch_", "fastener_analysis_leg_wall_bolt_")) for p in items)
    assert data["design"] == manifest["design"]
    assert data["design"]["key"] == key
    assert data["design"]["tnut_row_stations_mm"] == parent["design"]["tnut_row_stations_mm"]
    assert "no member, connection or stability approval" in data["design"]["description"]
    assert len(data["bounds_mm"]) == 2
    assert all(a < b for a, b in zip(*data["bounds_mm"], strict=True))
    expected = {p["path"] for p in items.values()} | {f"hybrid/{key}/parts.json"}
    assert manifest["viewer_artifacts"].keys() == expected
    parent_manifest = json.loads(exports.PARENT.read_text())
    assert manifest["parent_viewer_artifacts"] == parent_manifest["viewer_artifacts"]
    assert manifest["sources"].items() >= parent_manifest["sources"].items()
    assert manifest["sources"][str(exports.PARENT)] == exports.digest(exports.PARENT)
    for path in ("mini_moonboard/lumber_leg_exports.py", "mini_moonboard/lumber_leg_frame.py", "uv.lock"):
        assert manifest["sources"][path] == exports.digest(path)
    for path, sha in manifest["sources"].items():
        assert exports.digest(path) == sha, path
    for field in ("parent_viewer_artifacts", "viewer_artifacts"):
        for path, sha in manifest[field].items():
            assert exports.digest(Path("site")/path) == sha, path


def test_refuses_changed_parent_before_export(tmp_path, monkeypatch):
    manifest = json.loads(exports.PARENT.read_text())
    manifest["viewer_artifacts"][str(exports.VIEWER.relative_to("site"))] = "0"*64
    path = tmp_path/"manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(exports, "PARENT", path)
    with pytest.raises(RuntimeError, match="Parent geometry or viewer evidence changed"):
        exports.export("2x8")


@pytest.mark.parametrize("size,extension", [("2x4", 0), ("2x8", 100)])
def test_invalid_variant(size, extension):
    with pytest.raises(ValueError):
        exports.key(size, extension)
