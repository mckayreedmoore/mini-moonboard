"""Compact long-bolt geometry package consistency, not native FE acceptance."""
import json
import struct
from pathlib import Path

import pytest

from mini_moonboard import compact_hardware_exports as exports


def test_package_identity_reuse_and_units():
    data = json.loads((exports.DIRECTORY/"parts.json").read_text())
    manifest = json.loads((exports.DIRECTORY/"manifest.json").read_text())
    parent = json.loads(exports.base.VIEWER.read_text())
    inherited = {p["name"]: p for p in parent["parts"] if not exports.base.replaced(p["name"])}
    items = {p["name"]: p for p in data["parts"]}
    assert len(items) == len(data["parts"]) == 283
    assert (manifest["body_count"], manifest["connection_count"]) == (101,182)
    assert (manifest["new_mesh_count"], manifest["reused_mesh_count"]) == (12,271)
    assert {n: items[n] for n in inherited} == inherited
    changed = items.keys()-inherited.keys()
    assert changed == {f"{prefix}_{side}" for prefix in ("base_side", "lumber_leg")
                       for side in ("left", "right")} | {
        f"fastener_lumber_leg_bolt_{side}_{i}" for side in ("left", "right") for i in range(1,5)}
    assert {p.name for p in (exports.DIRECTORY/"models").iterdir()} == {n+".stl" for n in changed}
    for name in changed:
        item = items[name]
        assert item["path"] == f"hybrid/{exports.KEY}/models/{name}.stl"
        fabrication = item["fabrication"]
        assert fabrication["dimensions_imperial"] == pytest.approx([v/25.4 for v in fabrication["dimensions_mm"]])
        assert fabrication["clearance_status"] == exports.LIMITS
        # Inspect generated binary STL dimensions independently of its metadata.
        raw = (Path("site")/item["path"]).read_bytes()
        count = struct.unpack_from("<I", raw, 80)[0]
        assert len(raw) == 84+50*count and count > 0
        vertices = [row[3+i:6+i] for row in struct.iter_unpack("<12fH", raw[84:]) for i in (0,3,6)]
        bounds = [max(p[i] for p in vertices)-min(p[i] for p in vertices) for i in range(3)]
        assert bounds == pytest.approx(item["viewer_aabb_mm"], abs=.51)
        if name.startswith("fastener_"):
            assert fabrication["dimensions_mm"][0] == 107.95
            assert "four Wrought 014423 washers" in fabrication["description"]
    design = data["design"]
    assert design == manifest["design"]
    assert design["key"] == exports.KEY and design["extra_foot_extension_mm"] == 0.
    assert design["washers_per_bolt"] == 4
    assert design["washer_thickness_mm"] == exports.model.WASHER_NOMINAL
    assert not design["native_fe_match"] and not design["qualified_for_design"]
    assert "not an FE-matched model or strength approval" in design["description"]
    assert design["tnut_row_stations_mm"] == parent["design"]["tnut_row_stations_mm"]
    assert manifest["viewer_artifacts"].keys() == {p["path"] for p in items.values()} | {
        f"hybrid/{exports.KEY}/parts.json"}
    original = json.loads(exports.base.PARENT.read_text())
    assert manifest["sources"].items() >= original["sources"].items()
    assert manifest["parent_viewer_artifacts"] == original["viewer_artifacts"]
    assert manifest["hardware_sources"] == exports.model.SOURCES
    for path in ("mini_moonboard/compact_hardware_exports.py", "mini_moonboard/leg_hardware_trial.py"):
        assert path in manifest["sources"]
    for path, sha in manifest["sources"].items():
        assert exports.base.digest(path) == sha, path
    for field in ("parent_viewer_artifacts", "viewer_artifacts"):
        for path, sha in manifest[field].items():
            assert exports.base.digest(Path("site")/path) == sha, path


def test_actual_compact_leg_geometry():
    data = json.loads((exports.DIRECTORY/"parts.json").read_text())
    items = {p["name"]: p for p in data["parts"]}
    for side in ("left", "right"):
        part = exports.model.base.leg("2x6", 0., side)
        item = items[part.name]
        assert item["fabrication"]["dimensions_mm"] == pytest.approx(part.blank)
        b = exports.exact_bounds(part.shape)
        assert item["viewer_aabb_mm"] == pytest.approx([b.xlen,b.ylen,b.zlen])


def test_existing_package_not_overwritten():
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        exports.export()


def test_changed_parent_rejected(tmp_path, monkeypatch):
    manifest = json.loads(exports.base.PARENT.read_text())
    manifest["viewer_artifacts"][str(exports.base.VIEWER.relative_to("site"))] = "0"*64
    path = tmp_path/"manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(exports.base, "PARENT", path)
    with pytest.raises(RuntimeError, match="Parent geometry or viewer evidence changed"):
        exports.export()


def test_selector_is_additive():
    text = Path("site/index.html").read_text()
    assert f"lumberModels.push(['{exports.KEY}'," in text
    assert "long bolts / four washers · geometry only" in text
    assert "? requestedModel : 'selective-2x6-development'" in text
    assert "const model = ['plywood'," in text
