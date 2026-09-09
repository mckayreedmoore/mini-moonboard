"""Spread viewer package identity, reuse and changed-stock geometry checks."""
import json
from pathlib import Path

import pytest

from mini_moonboard import spread_leg_exports as exports

DIRECTORY = Path("site/hybrid")/exports.KEY


def test_spread_package_reuses_only_unchanged_wide_assets():
    data = json.loads((DIRECTORY/"parts.json").read_text())
    manifest = json.loads((DIRECTORY/"manifest.json").read_text())
    parent = json.loads(exports.base.VIEWER.read_text())
    original = json.loads(Path("site/hybrid/lumber-leg-2x8-e300/parts.json").read_text())
    inherited = {p["name"]: p for p in parent["parts"] if not exports.base.replaced(p["name"])}
    items = {p["name"]: p for p in data["parts"]}
    old = {p["name"]: p for p in original["parts"]}
    assert len(items) == len(data["parts"]) == 283
    assert (manifest["body_count"], manifest["connection_count"]) == (101, 182)
    assert (manifest["reused_mesh_count"], manifest["new_mesh_count"]) == (271, 12)
    assert {name: items[name] for name in inherited} == inherited
    changed = items.keys()-inherited.keys()
    assert changed == {f"{prefix}_{side}" for prefix in ("base_side", "lumber_leg")
                       for side in ("left", "right")} | {
        f"fastener_lumber_leg_bolt_{side}_{i}" for side in ("left", "right") for i in range(1, 5)}
    assert {p.name for p in (DIRECTORY/"models").iterdir()} == {name+".stl" for name in changed}
    for name in changed:
        p = items[name]
        assert p["path"] == f"hybrid/{exports.KEY}/models/{name}.stl"
        assert exports.base.digest(Path("site")/p["path"]) != exports.base.digest(Path("site")/old[name]["path"])
        assert p["fabrication"]["dimensions_imperial"] == pytest.approx(
            [v/25.4 for v in p["fabrication"]["dimensions_mm"]])
        assert "NOT build-ready" in p["fabrication"]["clearance_status"]
        assert "spread100x50/top150" in p["fabrication"]["description"]
    assert data["design"] == manifest["design"]
    assert data["design"]["key"] == exports.KEY
    assert data["design"]["tnut_row_stations_mm"] == parent["design"]["tnut_row_stations_mm"]
    assert [data["design"][n] for n in ("extra_foot_extension_mm", "along_leg_pitch_mm",
                                      "along_rim_pitch_mm", "top_extension_mm")] == [300., 100., 50., 150.]
    assert "not a native FE result or strength approval" in data["design"]["description"]
    assert manifest["viewer_artifacts"].keys() == {p["path"] for p in items.values()} | {
        f"hybrid/{exports.KEY}/parts.json"}
    parent_manifest = json.loads(exports.base.PARENT.read_text())
    assert manifest["parent_viewer_artifacts"] == parent_manifest["viewer_artifacts"]
    assert manifest["sources"].items() >= parent_manifest["sources"].items()
    for source in ("mini_moonboard/lumber_leg_frame.py", "mini_moonboard/lumber_leg_exports.py",
                   "mini_moonboard/lumber_leg_spread_frame.py", "mini_moonboard/spread_leg_exports.py", "uv.lock"):
        assert source in manifest["sources"]
    for path, sha in manifest["sources"].items():
        assert exports.base.digest(path) == sha, path
    for field in ("parent_viewer_artifacts", "viewer_artifacts"):
        for path, sha in manifest[field].items():
            assert exports.base.digest(Path("site")/path) == sha, path


def test_changed_leg_metadata_matches_spread_geometry():
    data = json.loads((DIRECTORY/"parts.json").read_text())
    items = {p["name"]: p for p in data["parts"]}
    for side in ("left", "right"):
        part = exports.model.leg(exports.SIZE, exports.EXTENSION, side)
        old = exports.model.original.leg(exports.SIZE, exports.EXTENSION, side)
        item = items[part.name]
        assert item["fabrication"]["dimensions_mm"] == pytest.approx(part.blank)
        assert part.blank[0] == pytest.approx(old.blank[0]+30.)
        bounds = exports.exact_bounds(part.shape)
        assert item["viewer_aabb_mm"] == pytest.approx([bounds.xlen, bounds.ylen, bounds.zlen])


def test_parent_hash_change_rejected_before_export(tmp_path, monkeypatch):
    manifest = json.loads(exports.base.PARENT.read_text())
    manifest["viewer_artifacts"][str(exports.base.VIEWER.relative_to("site"))] = "0"*64
    path = tmp_path/"manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(exports.base, "PARENT", path)
    with pytest.raises(RuntimeError, match="Parent geometry or viewer evidence changed"):
        exports.export()
