"""Frozen v3 structure review; metadata/AST controls only, no CAD or mesh loading.

Run from the repository root with .venv/bin/python -B PATH/check.py.
"""

import ast
import copy
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path.cwd()
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
OUT = Path(__file__).resolve().parent
FROZEN = {
    str(DOC / "occupied-adjusted-base-v3.json"): "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7",
    str(DOC / "occupied-2026-adjustments-v3.json"): "5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134",
    "scripts/eoere_2026_adjustments.py": "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
    "site/eoere-2026-adjustments-overlay.mjs": "b57759996903d1a5696f9cf5dca85af7e392a3cac38eaf6c5e15f49e54a5110d",
    "site/index.html": "1a1a8bbae255886214d6111769674bfafb8e80c72f3ebfa1acea319b2fa8b883",
    "site/eoere-adjusted-base-v3-scene.json.gz": "d77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947",
    "site/eoere-2026-adjustments-v3-scene.json.gz": "8682bf9a81c0bf8e7ffb23c3f6725adc6d3c9bd4728b00e50edb696ca3305d1d",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def scene(name):
    data = (ROOT / "site" / name).read_bytes()
    return json.loads(gzip.decompress(data) if name.endswith(".gz") else data)


for name, digest in FROZEN.items():
    assert sha(Path(name).read_bytes()) == digest, name
base = read(DOC / "occupied-adjusted-base-v3.json")
extra = read(DOC / "occupied-2026-adjustments-v3.json")
parent = read(DOC / "occupied-aligned-wire-v1.json")
base_patch = scene("eoere-adjusted-base-v3-scene.json.gz")
extra_patch = scene("eoere-2026-adjustments-v3-scene.json.gz")
source_checks = []
for label, report in [("base", base), ("extra", extra)]:
    for name, digest in report["source_sha256"].items():
        assert sha(Path(name).read_bytes()) == digest, name
    for row in report["changed_finished_solids"]:
        assert sha(Path(row["path"]).read_bytes()) == row["sha256"], row["path"]
    assert report["mechanics_ready"] is False
    assert len(report["release"]) == 6 and all(v is False for v in report["release"].values())
    source_checks.append({"report": label, "matching_source_pins": len(report["source_sha256"]),
                          "matching_saved_shape_hashes": len(report["changed_finished_solids"])})
raw = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/2026-adjustments-v10"
assert (DOC / "occupied-adjusted-base-v3.json").read_bytes() == (raw / "base/geometry.json").read_bytes()
assert (DOC / "occupied-2026-adjustments-v3.json").read_bytes() == (raw / "geometry.json").read_bytes()
assert base["parent_geometry"]["sha256"] == sha((DOC / "occupied-aligned-wire-v1.json").read_bytes())
assert extra["parent_geometry"]["sha256"] == FROZEN[str(DOC / "occupied-adjusted-base-v3.json")]
ancestry = []
for name in ["eoere-adjusted-base-v3-scene.json.gz", "eoere-2026-adjustments-v3-scene.json.gz",
             "eoere-aligned-wire-scene.json.gz", "eoere-cleat-trim-scene.json"]:
    patch = scene(name)
    binding = patch["parent_scene"]
    encoded = (ROOT / "site" / binding["url"]).read_bytes()
    assert sha(encoded) == binding["sha256"], name
    if "decoded_sha256" in binding:
        assert sha(gzip.decompress(encoded)) == binding["decoded_sha256"], name
    assert scene(binding["url"])["layout_report"]["sha256"] == binding["layout_sha256"], name
    ancestry.append({"scene": name, "authenticated_parent": binding["url"]})

# Compose only identities and kinds; no Three.js, CAD, or triangle/vertex arrays.
native = read(DOC.parent / "native-geometry-v4.json")
native_rows = {r["id"]: r for r in native["parts"]}
bottom = scene("eoere-bottom-rail-scene.json.gz")
inventory = {n: native_rows[n]["kind"] for n in bottom["retained_shared_part_names"]}
for row in bottom["solids"]:
    assert row["name"] not in inventory
    inventory[row["name"]] = row["fabrication"]["kind"]
assert len(inventory) == 1021
for name, field in [("eoere-cleat-trim-scene.json", "solids"),
                    ("eoere-aligned-wire-scene.json.gz", "solids"),
                    ("eoere-adjusted-base-v3-scene.json.gz", "replacements"),
                    ("eoere-2026-adjustments-v3-scene.json.gz", "replacements")]:
    patch = scene(name)
    rows = patch[field]
    assert len({r["name"] for r in rows}) == len(rows)
    for row in rows:
        assert row["id"] == row["name"] and inventory[row["name"]] == row["fabrication"]["kind"]
        assert "mesh" in row and "transform" not in row and "template_id" not in row
        inventory[row["name"]] = row["fabrication"]["kind"]
    if "additions" in patch:
        templates = {r["id"] for r in patch["templates"]}
        assert len(templates) == len(patch["templates"])
        for row in patch["additions"]:
            assert row["id"] == row["name"] and row["name"] not in inventory
            assert bool(row.get("mesh")) != bool(row.get("template_id"))
            if "template_id" in row:
                assert row["template_id"] in templates and len(row["transform"]) == 16
            inventory[row["name"]] = row["fabrication"]["kind"]
        assert len(inventory) == patch["counts"]["total_visible_parts"]
assert Counter(inventory.values()) == Counter({"timber": 22, "panel": 6, "bracket": 22,
    "bolt": 500, "screw": 66, "wire": 250, "light": 252, "tnut": 262})
assert extra["original_grid_retained"] is True and extra["unofficial_2026_positions"] is True
assert extra["all_midpoints_are_assumed_not_confirmed"] is True
assert base["unofficial_2026_grid_included"] is False
html = Path("site/index.html").read_text()
for text in ["Current eoere geometry", "Preserved aligned-wire geometry", "Preserved trimmed-cleat geometry",
             "Preserved raised-rail frame", "exact midpoints are assumed", "remain when this update is off",
             "updateToggle.checked ? 'eoere-new-2026-adjustments' : 'eoere-adjusted-frame-development'"]:
    assert text in html, text
assert FROZEN[str(DOC / "occupied-adjusted-base-v3.json")] in html
assert FROZEN[str(DOC / "occupied-2026-adjustments-v3.json")] in html

# Run exported validators only. This never invokes loadScene or meshGeometry.
node = """
import fs from 'node:fs'; import zlib from 'node:zlib'; import assert from 'node:assert/strict';
import {validateAdjustedBase,validate2026Adjustments} from './site/eoere-2026-adjustments-overlay.mjs';
const get = n => JSON.parse(zlib.gunzipSync(fs.readFileSync('site/'+n)));
const base=get('eoere-adjusted-base-v3-scene.json.gz'), extra=get('eoere-2026-adjustments-v3-scene.json.gz');
validateAdjustedBase(base,base.layout_report.sha256); validate2026Adjustments(extra,extra.layout_report.sha256);
const controls=[];
for (const [name,mutate] of [
 ['parent hash',p=>p.parent_scene.sha256='0'.repeat(64)],
 ['official-grid claim',p=>p.unofficial_2026_positions=false],
 ['release flag',p=>p.release.fabrication_released=true],
 ['lost base move',p=>p.principal_move_adopted=false],
 ['duplicate replacement identity',p=>p.replacements[1].name=p.replacements[0].name],
 ['template reference',p=>p.additions[0].template_id='missing'],
 ['dropped light',p=>p.additions.splice(p.additions.findIndex(r=>r.fabrication.kind==='light'),1)]]) {
 const p=structuredClone(extra); mutate(p); assert.throws(()=>validate2026Adjustments(p,extra.layout_report.sha256)); controls.push(name);
}
console.log(JSON.stringify({validators_passed:true,rejected_controls:controls}));
"""
viewer_controls = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", node], text=True))

# Extract the exact authentication prefix, stopping before cache loading or CAD.
module = ast.parse(Path("scripts/eoere_2026_adjustments.py").read_text())
build = copy.deepcopy(next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "build"))
stop = next(i for i, n in enumerate(build.body) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "loaded" for t in n.targets))
build.body = build.body[:stop] + [ast.Return(ast.Name("pins", ast.Load()))]
ast.fix_missing_locations(build)
prefix = compile(ast.Module([build], type_ignores=[]), "frozen-generator-authentication-prefix", "exec")
parent_scene = Path("site/eoere-aligned-wire-scene.json.gz")
parent_report = DOC / "occupied-aligned-wire-v1.json"
controls = []
for altered in [DOC / "occupied-bottom-rail-v1.json", DOC.parent / "native-geometry-v4.json"]:
    modified = copy.deepcopy(read(altered))
    row = modified["finished_panel_solids"][0] if "finished_panel_solids" in modified else next(
        r for r in modified["parts"] if r["id"] == "wire_002_A2_A3")
    row["sha256"] = "0" * 64
    altered_bytes = json.dumps(modified).encode()
    expected = parent["source_sha256"][str(altered)]
    assert sha(altered_bytes) != expected
    scope = {"Path": Path, "DOC": DOC, "PARENT_REPORT": parent_report, "PARENT_SCENE": parent_scene,
             "PARENT_SHA": sha(parent_scene.read_bytes()), "PARENT_LAYOUT_SHA": sha(parent_report.read_bytes()),
             "PARENT_DECODED_SHA": sha(gzip.decompress(parent_scene.read_bytes())),
             "hashlib": hashlib, "gzip": gzip, "sys": SimpleNamespace(modules={}),
             "__file__": str(ROOT / "scripts/eoere_2026_adjustments.py"),
             "read": lambda p: copy.deepcopy(modified) if Path(p) == altered else read(p),
             "sha": lambda p: sha(altered_bytes) if Path(p) == altered else sha(Path(p).read_bytes())}
    exec(prefix, scope)
    pins = scope["build"](SimpleNamespace(exists=lambda: False))
    assert pins[str(altered)] == sha(altered_bytes)
    controls.append({"altered_source": str(altered), "trusted_ancestor_sha256": expected,
                     "changed_cache_metadata_sha256": sha(altered_bytes), "authentication_prefix_rejected": False,
                     "new_self_pin_recorded": True, "scope": "authentication prefix only; no CAD or final build acceptance"})

receipt = {"schema": "eoere_v3_structure_independent_review/v1", "frozen_inputs": FROZEN,
    "review_helper_sha256": sha(Path(__file__).read_bytes()), "python_version": sys.version.split()[0],
    "node_version": subprocess.check_output(["node", "--version"], text=True).strip(),
    "source_checks": source_checks, "scene_ancestry": ancestry,
    "inventory": dict(Counter(inventory.values())), "base_parts": 1021, "extra_parts": 1380,
    "base_replacements": 136, "extra_replacements": 23, "extra_additions": 359,
    "viewer_validator_controls": viewer_controls, "source_authentication_controls": controls,
    "findings": [{"priority": "P2", "title": "Authenticate secondary cache metadata before reading/importing it",
        "sources": ["scripts/eoere_2026_adjustments.py:543", "scripts/eoere_2026_adjustments.py:547",
                    "scripts/eoere_2026_adjustments.py:312", "scripts/eoere_2026_adjustments.py:801"],
        "observed": "Raised/native JSON and bottom-rail bracket scene are self-pinned at runtime, without comparison to the hashes already in the authenticated aligned-wire parent's source_sha256. Two AST-only controls accept changed raised/native cache metadata and record its new hash.",
        "impact": "Replay may read changed cache authority before CAD, so its self-consistent BREP rows and bracket transforms are not necessarily the preserved parent inputs. All 570 current frozen pins match, so this finding does not establish an error in today's v3 geometry.",
        "recommendation": "Before any secondary cache read or BREP import, compare raised/native/bracket hashes with the authenticated parent source_sha256; reject missing pins and mismatches. Keep the frozen v3 producer/source witness unchanged."}],
    "limitations": ["No CAD import, native solve, actual mesh construction/decoding, browser run, materialization, broad tests, or Git commands.",
        "Source-authentication negative controls execute only the generator prefix, not a complete CAD build.",
        "Frozen evidence contains two absolute source witness locations; existing ledger records archive location and recovery. It is an environment-bound witness, not a standalone portable bundle.",
        "README and completion-ledger v2-to-v3 edits belong to the parent and were not adjudicated here."],
    "mechanics_or_physical_release": False}
with (OUT / "receipt.json").open("x") as handle:
    json.dump(receipt, handle, indent=2)
    handle.write("\n")
print(json.dumps({"source_pins_match": True, "metadata_inventory_match": True,
                  "findings": len(receipt["findings"]), "receipt": str(OUT / "receipt.json")}))
