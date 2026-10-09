"""Source-only testing review plus authentication of one fresh Three.js check."""
from __future__ import annotations

import builtins
import copy
import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())

NODE_CONTROLS = r"""
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {createHash, webcrypto} from 'node:crypto';
import {gunzipSync, gzipSync} from 'node:zlib';
const context = JSON.parse(fs.readFileSync(0, 'utf8'));
const root = context.root, source = fs.readFileSync(root + '/site/index.html', 'utf8');
globalThis.crypto ??= webcrypto;
const {validateLowerCleatPreview, loadLowerCleatPreviewScene} = await import(pathToFileURL(root + '/site/eoere-lower-cleat-z180-overlay.mjs'));
const asset = fs.readFileSync(root + '/site/eoere-lower-cleat-z180-scene.json.gz');
const data = JSON.parse(gunzipSync(asset)), layoutHash = data.layout_report.sha256;
const sha = value => createHash('sha256').update(value).digest('hex');
validateLowerCleatPreview(data, layoutHash);
const controls = [
  ['schema', p => p.schema = 'other'], ['revision', p => p.revision = 'historical'],
  ['candidate', p => p.candidate = 'other'], ['status', p => p.status = 'ADOPTED'],
  ['layout_path', p => p.layout_report.path = 'other'], ['layout_hash', p => p.layout_report.sha256 = '0'.repeat(64)],
  ['extra_grid', p => p.optional_2026_extra = true], ['response_transfer', p => p.saved_response_transferred = true],
  ['resistance', p => p.complete_joint_resistance = 0],
  ['missing_host', p => p.replacements.pop()], ['duplicate_host', p => p.replacements[1] = p.replacements[0]],
  ['wrong_host_id', p => p.replacements[0].id = 'wrong'], ['host_transform', p => p.replacements[0].transform = [1]],
  ['host_template', p => p.replacements[0].template_id = 'other'], ['host_brep_hash', p => p.replacements[0].source_brep_sha256 = 'bad'],
  ['host_kind', p => p.replacements[0].fabrication.kind = 'panel'],
  ['host_revision', p => p.replacements[0].fabrication.lower_cleat_revision = 'old'],
  ['missing_translation', p => p.bolt_translations.pop()], ['duplicate_translation', p => p.bolt_translations[1] = p.bolt_translations[0]],
  ['wrong_axis', p => p.bolt_translations[0].axis_id = 'wrong'],
  ['wrong_X_translation', p => p.bolt_translations[0].translation_xyz_mm[0] = 1],
  ['wrong_Z_translation', p => p.bolt_translations[0].translation_xyz_mm[2] = -19],
];
for (const key of Object.keys(data.parent_scene)) controls.push(['parent_' + key, p => p.parent_scene[key] = 'wrong']);
for (const key of ['timber','panel','bracket','bolt','physical_bolt_axes','screw','lights','tnuts','wire','total_visible_parts'])
  controls.push(['count_' + key, p => p.counts[key]++]);
for (const key of Object.keys(data.release)) controls.push(['release_' + key, p => p.release[key] = true]);
for (const [name, mutate] of controls) {
  const changed = structuredClone(data); mutate(changed);
  assert.throws(() => validateLowerCleatPreview(changed, layoutHash), undefined, name);
}
const earlyLoaderControls = [];
for (const key of ['expectedSha256', 'decodedSha256']) {
  let fetches = 0; globalThis.fetch = async () => {fetches++; throw Error('unexpected fetch');};
  await assert.rejects(() => loadLowerCleatPreviewScene({}, {url:'review', expectedSha256:sha(asset), decodedSha256:sha(gunzipSync(asset)), [key]:'bad'}), /scene hashes required/);
  assert.equal(fetches, 0); earlyLoaderControls.push('invalid_' + key);
}
const topology = Object.keys(data.triangle_topologies)[0];
const topologyControls = [
  ['topology_type', p => p.triangle_topologies[topology].triangle_component_type = 'float32', /valid triangle topology/],
  ['topology_count', p => p.triangle_topologies[topology].index_count++, /valid triangle topology/],
  ['topology_hash', p => {p.triangle_topologies['0'.repeat(64)] = p.triangle_topologies[topology]; delete p.triangle_topologies[topology];}, /triangle bytes differ/],
];
for (const [name, mutate, expected] of topologyControls) {
  const changed = structuredClone(data); mutate(changed);
  const decoded = Buffer.from(JSON.stringify(changed)), encoded = gzipSync(decoded); let fetches = 0;
  globalThis.fetch = async url => {assert.equal(url, 'review'); fetches++; return new Response(encoded, {status:200});};
  await assert.rejects(() => loadLowerCleatPreviewScene({}, {url:'review', expectedSha256:sha(encoded), decodedSha256:sha(decoded), layoutSha256:layoutHash}), expected);
  assert.equal(fetches, 1); earlyLoaderControls.push(name);
}
const loaderNames = [...new Set(source.match(/load[A-Za-z0-9]+Scene/g))];
function dispatch(text, model) {
  const start = text.indexOf("const reviewed = model === 'wood-joints-reviewed';");
  const finish = text.indexOf("document.querySelector('#model-status').textContent =", start);
  assert(start > 0 && finish > start);
  const block = text.slice(start, finish);
  const fn = new Function(...loaderNames, 'THREE', 'baselineText', 'sharedMeshes', 'resolveMeshPath', 'model',
    'return (async () => {' + block + ';return data;})()');
  return fn(...loaderNames.map(name => async (_, options) => ({loader:name, options:JSON.parse(JSON.stringify(options))})), {}, '{"parts":[]}', {}, value=>value, model);
}
function choices(text) {
  const begin = text.indexOf('const woodJointModels = ') + 'const woodJointModels = '.length;
  const end = text.indexOf('];', begin) + 1;
  return new Function('return (' + text.slice(begin, end) + ')')();
}
const oldChoices = choices(context.old_index), newChoices = choices(source);
assert.equal(new Set(newChoices.map(([key])=>key)).size, newChoices.length);
assert.deepEqual(newChoices.filter(([key])=>key!=='eoere-lower-cleat-z180-development'), oldChoices);
for (const [model] of oldChoices) assert.deepEqual(await dispatch(source, model), await dispatch(context.old_index, model), model);
const preview = await dispatch(source, 'eoere-lower-cleat-z180-development');
assert.equal(preview.loader, 'loadLowerCleatPreviewScene');
assert.equal(preview.options.url, 'eoere-lower-cleat-z180-scene.json.gz');
assert.equal(preview.options.expectedSha256, sha(asset));
assert.equal(preview.options.decodedSha256, sha(gunzipSync(asset)));
assert.equal(preview.options.layoutSha256, layoutHash);
const adjustmentStart = source.indexOf('const extendedCleatModels = ');
const adjustmentEnd = source.indexOf('const updateLabel = ', adjustmentStart);
const constants = source.slice(adjustmentStart, adjustmentEnd);
const toggleVisible = new Function('model', constants + 'return adjustmentModels.includes(model);');
assert.equal(toggleVisible('eoere-lower-cleat-z180-development'), false);
const changeBegin = source.indexOf("updateToggle.addEventListener('change', () => {") + "updateToggle.addEventListener('change', () => {".length;
const changeEnd = source.indexOf('});', changeBegin);
let assigned;
const toggle = new Function('model','updateToggle','location', constants + source.slice(changeBegin, changeEnd));
const toggleCases = [];
for (const [off,on] of [['eoere-extended-cleat-frame-development','eoere-extended-cleat-2026-development'],['eoere-adjusted-frame-development','eoere-new-2026-adjustments']])
  for (const current of [off,on]) for (const checked of [false,true]) {
    toggle(current,{checked},{href:'https://example.invalid/index.html?view=rear&bolt=kept',assign:url=>assigned=url});
    const url = new URL(assigned); assert.equal(url.searchParams.get('model'),checked?on:off);
    assert.equal(url.searchParams.get('view'),'rear'); assert.equal(url.searchParams.get('bolt'),'kept');
    toggleCases.push([current,checked,url.searchParams.get('model')]);
  }
assert(source.includes('Current six-case results remain bound to Z200.'));
console.log(JSON.stringify({validator_controls:controls.map(([name])=>name),pre_parent_loader_controls:earlyLoaderControls,
  unchanged_old_choices_and_dispatch:oldChoices.length,new_preview_dispatch:preview,toggle_cases:toggleCases,new_preview_toggle_visible:false}));
"""


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def read(path):
    return json.loads(Path(path).read_bytes())


def rejected(call):
    try:
        call()
    except (ValueError, KeyError, FileNotFoundError, FileExistsError) as exc:
        return str(exc)
    raise AssertionError("expected rejection")


def review():
    manifest_path = PACKET / "review-target-v1.json"
    manifest = read(manifest_path)
    before = {name: sha(ROOT / name) for name in manifest["files"]}
    require(before == manifest["files"], "frozen viewer targets differ")
    manifest_digest = sha(manifest_path)
    own_mesh_path = OUT / "actual-mesh-check-v1.json"
    own_mesh = read(own_mesh_path)
    frozen_mesh = read(PACKET / "mesh-check-v1.json")
    require(own_mesh == frozen_mesh and own_mesh["passed"] is True, "fresh actual Three check differs")
    require(own_mesh["unchanged_parts"] == 997 and own_mesh["replaced_receivers"] == 4 and own_mesh["translated_bolt_components"] == 20, "mesh composition")
    require(all(sha(ROOT / name) == digest for name, digest in own_mesh["source_sha256"].items()), "fresh mesh source bindings")
    spec = importlib.util.spec_from_file_location("frozen_z180_display_exporter_review", PACKET / "export.py")
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    inp, pins, runtime, descriptor, bodies, audit = exporter.prepare()
    descriptor_bytes = json.dumps(descriptor, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    layout_path = PACKET / "runs-v1/export01/layout.json"
    require(descriptor_bytes == layout_path.read_bytes(), "source-only descriptor replay differs")
    geometry, placement = read(ROOT / inp["current_geometry"]), read(ROOT / inp["placement"])
    axes = {row["id"]: row for row in geometry["axes"]}
    moved = {row["id"]: row for row in placement["proposed_axes"]}
    datums = descriptor["receiver_datums"]
    require(len(datums) == 8 and len({(row["axis_id"], row["receiver"]) for row in datums}) == 8, "unique eight datums")
    expected_pairs = {(axis["id"], name) for axis in moved.values() for name in axis["receivers"]}
    require({(row["axis_id"], row["receiver"]) for row in datums} == expected_pairs, "datum joins")
    for row in datums:
        axis = moved[row["axis_id"]]
        bounds = bodies[row["receiver"]]["bounds_xyz_mm"]
        require(row["world_axis_point_xyz_mm"] == axis["point_xyz_mm"] and row["world_direction_xyz"] == axis["direction_xyz"], "datum coordinate/direction")
        expected = [axis["point_xyz_mm"][1] - bounds[1][0], 180 - bounds[2][0], bounds[2][1] - 180]
        require(all(abs(row[key] - value) < 1e-7 for key, value in zip(("from_Ymin_mm", "from_Zmin_mm", "from_Zmax_mm"), expected, strict=True)), "datum bound offsets")
        require(row["bit_instruction"] is None and row["actual"] is None, "unadopted datums")
    for name, axis in moved.items():
        expected = copy.deepcopy(axes[name])
        expected["point_xyz_mm"][2] = 180
        require(axis == expected, "only four Z translations")
    require(len(geometry["axes"]) == 100 and len(geometry["screw_axes"]) == 66, "100/66 authority")
    require(audit["pass"] is True and descriptor["saved_response_transferred"] is False and descriptor["complete_joint_resistance"] is None and all(value is False for value in descriptor["release"].values()), "display boundary")
    export_result = read(PACKET / "runs-v1/export01/export-result.json")
    require(export_result["source_sha256"] == pins and export_result["runtime"] == runtime, "export source map")
    for row in export_result["output"].values():
        require(sha(ROOT / row["path"]) == row["sha256"] and (ROOT / row["path"]).stat().st_size == row["bytes"], "export output binding")
    scene = ROOT / "site/eoere-lower-cleat-z180-scene.json.gz"
    exported_scene = PACKET / "runs-v1/export01/scene.json.gz"
    require(scene.read_bytes() == exported_scene.read_bytes(), "published scene differs from frozen export")
    require(hashlib.sha256(gzip.decompress(scene.read_bytes())).hexdigest() == export_result["scene_decoded_sha256"], "decoded scene binding")

    original_read = exporter.read
    permit_path = PACKET / "parent-readiness.json"
    input_path = PACKET / "inputs.json"
    permit = read(permit_path)
    gate_controls = []

    def virtual_prepare(p, i):
        def overridden(path):
            if Path(path) == permit_path:
                return copy.deepcopy(p)
            if Path(path) == input_path:
                return copy.deepcopy(i)
            return original_read(path)
        with patch.object(exporter, "read", side_effect=overridden):
            return exporter.prepare()

    for key, value in (("only_four_saved_BREP_display_tessellations", False), ("native_mechanics_or_full_frame_CAD_authorized", True), ("geometry_adoption_authorized_by_this_file", True), ("inputs_sha256", "0" * 64), ("exporter_sha256", "0" * 64)):
        changed = copy.deepcopy(permit)
        changed[key] = value
        gate_controls.append({"name": key, "rejection": rejected(lambda changed=changed: virtual_prepare(changed, inp))})
    changed = copy.deepcopy(inp)
    changed["runtime"]["cadquery"] = "0.0"
    gate_controls.append({"name": "runtime", "rejection": rejected(lambda: virtual_prepare(permit, changed))})
    changed = copy.deepcopy(inp)
    changed["source_sha256"][inp["native_result"]] = "0" * 64
    gate_controls.append({"name": "saved_result_hash", "rejection": rejected(lambda: virtual_prepare(permit, changed))})
    conflicting_permit = copy.deepcopy(permit)
    conflicting_permit["reviewed_native_result_sha256"] = "0" * 64
    accepted = virtual_prepare(conflicting_permit, inp)
    require(accepted[-1]["pass"] is True and accepted[1][inp["native_result"]] != conflicting_permit["reviewed_native_result_sha256"], "readiness-binding finding no longer reproduces")

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    old_index = subprocess.run(["git", "show", head + ":site/index.html"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    node = subprocess.run(["node", "--input-type=module", "-e", NODE_CONTROLS], cwd=ROOT, input=json.dumps({"root": str(ROOT), "old_index": old_index}), check=False, capture_output=True, text=True)
    require(node.returncode == 0, node.stderr)
    node_controls = json.loads(node.stdout)
    require(before == {name: sha(ROOT / name) for name in before} and sha(manifest_path) == manifest_digest, "targets changed during review")
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "export sources changed during review")
    return {
        "schema": "eoere_lower_cleat_z180_viewer_independent_testing_review/v1",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "review_target_manifest": {"path": str(manifest_path.relative_to(ROOT)), "sha256": manifest_digest},
        "target_sha256_before_after": before,
        "export_source_pins_verified": len(pins),
        "fresh_actual_Three_check": {"path": str(own_mesh_path.relative_to(ROOT)), "sha256": sha(own_mesh_path), "command": "node scripts/check_eoere_lower_cleat_z180.mjs " + str(own_mesh_path.relative_to(ROOT)), "executions": 1, "byte_equal_frozen_mesh_check": True, "unchanged_parts": 997, "replacement_receivers": 4, "translated_hardware_components": 20, "retained_axes": 100, "retained_screws": 66, "claim_controls": 13, "hash_controls": 3},
        "source_only_descriptor_exact_replay": True,
        "eight_unique_datums_independently_rejoined": True,
        "export_preflight_controls": gate_controls,
        "cheap_node_controls": node_controls,
        "historical_index_comparison": {"commit": head, "index_sha256": hashlib.sha256(old_index.encode()).hexdigest()},
        "findings": [{"severity": "medium", "file": str((PACKET / "export.py").relative_to(ROOT)), "line": 68,
            "problem": "The bounded readiness gate never compares reviewed_native_result_sha256 with the consumed native-result source pin.",
            "evidence": "Changing only the readiness digest to 64 zeros in memory still lets actual stdlib prepare() return saved audit.pass true and descriptor bytes for result 6efea34ce52b3521da6d14b89853ef83ab9c1a1f7861c71f6410fc8db7738cb3.",
            "impact": "A stale or contradictory parent readiness can authorize display work on a result other than the one its explicit approval digest names. The issued frozen readiness and geometry currently agree; this is a guard defect, not a wrong issued observation.",
            "fix": "Before verifier/native work, require the readiness reviewed_native_result_sha256 to equal the pinned inp.native_result digest; add a conflicting-readiness negative control."}],
        "sources_unchanged_before_after": True,
        "scope": "One actual existing Node/Three checker execution; stdlib exporter intake and exact descriptor replay; byte hashes; tiny synthetic JS validator/early loader controls and extracted source routing/toggle functions. Existing saved receiver verifier reused during prepare, not independently re-audited.",
        "excluded": ["CAD/native imports", "BREP query/reconstruction/tessellation", "mechanics/FEA/frame/global solve", "browser execution or screenshots", "field admission or strength acceptance", "source/shared edits"],
        "browser_status": manifest["browser_check_status"],
        "mechanics_or_physical_release": False,
    }


if __name__ == "__main__":
    original_import = builtins.__import__
    native_attempts = []

    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in ("cadquery", "OCP"):
            native_attempts.append(name)
            raise AssertionError("forbidden native import: " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=no_native):
        receipt = review()
    require(not native_attempts, "native import attempted")
    receipt["native_import_attempts"] = native_attempts
    output = OUT / "receipt.json"
    with output.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "sha256": sha(output), "findings": len(receipt["findings"])}))
