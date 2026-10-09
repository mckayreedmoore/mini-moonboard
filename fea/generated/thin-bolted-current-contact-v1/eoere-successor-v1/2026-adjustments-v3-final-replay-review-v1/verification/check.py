"""Independent source-only review; run from the repository with python3 -B."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
BASE = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
TARGET = ROOT / "scripts/check_eoere_2026_replay_inputs.py"
TRUSTED = {
    TARGET: "185b4a9aedf2e10c2b53943b3086bf12a6992cc8b5d20e50b9104c08dcf8e2c1",
    BASE / "2026-adjustments-v10/replay-gate-v3/result.json": "c1bb7fee5a04b759fee475402761640e407c31f5aa4355a73084e6eb2046b695",
    BASE / "2026-adjustments-v10/replay-gate-v3/cli-controls-v2/cli-controls.json": "fa45aaa7a5f1df86042dba95f64251254fb9d2470e7ec99d9129021aff274c2a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_rejected(call, marker):
    try:
        call()
    except (ValueError, FileNotFoundError) as error:
        assert marker in str(error), (marker, str(error))
        return type(error).__name__
    raise AssertionError("invalid input accepted: " + marker)


for path, expected in TRUSTED.items():
    assert sha(path) == expected, path
spec = importlib.util.spec_from_file_location("independent_replay_gate", TARGET)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
visited = set()


def observed_reader(path):
    visited.add(str(path.resolve()))
    return path.read_bytes()


frozen, pins = gate.verify(observed_reader)
assert len(frozen) == 570 and len(pins) == 573
assert set(pins).issubset(visited)
assert str(gate.INITIALIZER.resolve()) not in frozen
assert str(gate.INITIALIZER.resolve()) in pins
baseline = {name: Path(name).read_bytes() for name in pins}


def reader(path, target=None, mode=None):
    name = str(path.resolve())
    if target is not None and name == str(target.resolve()):
        if mode == "missing":
            raise FileNotFoundError(str(path))
        return baseline.get(name, b"") + b"independent-invalid-input"
    if name == str(gate.NAMESPACE_INITIALIZER.resolve()):
        raise FileNotFoundError(str(path))
    return baseline[name]


source_controls = []
cache = Path(next(name for name in frozen if name.endswith(".brep")))
helper = Path("scripts/thin_bolted_occupied.py")
targets = (gate.PARENT, *gate.INPUTS, gate.PRODUCER, *gate.REPORTS, helper, cache, gate.INITIALIZER)
for target in targets:
    for mode in ("changed", "missing"):
        kind = assert_rejected(
            lambda target=target, mode=mode: gate.verify(
                lambda path: reader(path, target, mode)
            ), target.name,
        )
        source_controls.append({"path": str(target), "mode": mode, "exception": kind})
assert_rejected(
    lambda: gate.verify(lambda path: reader(path, gate.NAMESPACE_INITIALIZER, "changed")),
    "unexpected executable namespace initializer",
)
assert_rejected(lambda: gate.join_pins({str(helper): "a" * 64}, {str(helper.resolve()): "b" * 64}), "conflicting source bindings")
reported_controls = gate.controls()
saved_gate = json.loads(next(path for path in TRUSTED if path.name == "result.json").read_bytes())
assert reported_controls == saved_gate["rejected_controls"] and len(reported_controls) == 29
assert len({json.dumps(row, sort_keys=True) for row in reported_controls}) == 29

reused = {}
old = BASE / "2026-adjustments-v3-review-v1/verification/verification-result-v1.json"
proof = json.loads(old.read_bytes())
assert proof["passed"] and not proof["substantial_findings"]
reused[str(old)] = sha(old)
for name, expected in proof["source_sha256"].items():
    path = Path(name)
    assert sha(path) == expected, path
    reused[str(path)] = expected
for row in proof["screenshots"]:
    path = Path(row["path"])
    assert sha(path) == row["sha256"], path
    reused[str(path)] = row["sha256"]
for row in proof["raw_published_pairs"]:
    for label, field in (("report", "layout_sha256"), ("raw_report", "layout_sha256"), ("scene", "compressed_sha256"), ("raw_scene", "compressed_sha256")):
        path = Path(row[label])
        assert sha(path) == row[field], path
        reused[str(path)] = row[field]

STUB = '''import hashlib,json,os,subprocess
from pathlib import Path
original_read = Path.read_bytes
mode = os.environ['REVIEW_MODE']
marker = Path(os.environ['REVIEW_MARKER'])
receipt = Path(os.environ['REVIEW_RECEIPT'])
producer = Path('scripts/eoere_2026_adjustments.py').resolve()
post = False
def controlled_read(path):
    changed = producer if mode == 'post-producer' else Path('mini_moonboard/__init__.py').resolve()
    if post and mode == 'post-namespace' and path.resolve() == Path('scripts/__init__.py').resolve(): return b'executable namespace initializer'
    if post and mode != 'post-namespace' and path.resolve() == changed: return original_read(path)+b'changed after producer'
    return original_read(path)
Path.read_bytes = controlled_read
def fake_run(args, **kwargs):
    global post
    assert args[1:4] == ['-B', 'scripts/eoere_2026_adjustments.py', '--out']
    assert kwargs == {'check': True}
    marker.write_text(json.dumps(args))
    if mode == 'producer-failure':
        raise subprocess.CalledProcessError(7, args)
    root = Path(args[4]).resolve()
    root.mkdir(parents=True)
    p = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-adjusted-base-v3.json')
    pins = json.loads(original_read(p))['source_sha256']
    output = root/'synthetic-output.bin'
    output.write_bytes(b'no CAD geometry; isolated subprocess fixture')
    pins[str(output)] = hashlib.sha256(original_read(output)).hexdigest()
    for layer, path in (('base', root/'base/geometry.json'), ('extra', root/'geometry.json')):
        path.parent.mkdir(exist_ok=True)
        binding = dict(pins)
        if mode == 'missing-'+layer+'-binding': binding.pop(str(producer))
        if mode == 'changed-'+layer+'-binding': binding[str(producer)] = '0'*64
        if mode == 'initializer-'+layer+'-binding': binding[str(Path('mini_moonboard/__init__.py').resolve())] = '0'*64
        if mode == 'bad-generated-'+layer: binding[str(output)] = '0'*64
        if mode == 'missing-'+layer+'-report': continue
        if mode == 'unexpected-external-'+layer:
            external = root.parent/'outside.bin'; external.write_bytes(b'external')
            binding[str(external)] = hashlib.sha256(original_read(external)).hexdigest()
        path.write_text(json.dumps({'source_sha256': binding, 'synthetic_fixture': True}))
    if mode == 'exclusive-late': receipt.write_text('keep late receipt unchanged')
    post = mode.startswith('post-')
    return subprocess.CompletedProcess(args, 0)
subprocess.run = fake_run
'''

cli_controls = []
with tempfile.TemporaryDirectory(prefix="source-only-", dir=HERE) as directory:
    work = Path(directory)
    fixture = work / "fixture"
    fixture.mkdir()
    (fixture / "sitecustomize.py").write_text(STUB)
    cases = (
        "default", "existing-receipt", "existing-replay", "equal", "nested",
        "canonical-nested", "symlink-nested", "disjoint", "exclusive-late",
        "producer-failure", "missing-base-binding", "missing-extra-binding",
        "changed-base-binding", "changed-extra-binding", "bad-generated-base",
        "bad-generated-extra", "missing-base-report", "missing-extra-report",
        "initializer-base-binding", "initializer-extra-binding",
        "unexpected-external-base", "unexpected-external-extra", "post-producer",
        "post-initializer", "post-namespace",
    )
    for mode in cases:
        case = work / mode
        case.mkdir()
        output, receipt, marker = case / "replay", case / "receipt.json", case / "invocation.json"
        if mode == "existing-receipt": receipt.write_text("preserve existing receipt")
        if mode == "existing-replay":
            output.mkdir(); (output / "existing.bin").write_bytes(b"preserve existing output")
        if mode == "equal": receipt = output
        if mode == "nested": receipt = output / "geometry.json"
        if mode == "canonical-nested": receipt = output / ".." / "replay" / "base" / "geometry.json"
        if mode == "symlink-nested":
            alias = case / "alias"; alias.symlink_to(output, target_is_directory=True)
            receipt = alias / "geometry.json"
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(fixture), "REVIEW_MODE": mode, "REVIEW_MARKER": str(marker), "REVIEW_RECEIPT": str(receipt)}
        cmd = [sys.executable, "-B", str(TARGET), "--out", str(receipt)]
        if mode != "default": cmd += ["--run-out", str(output)]
        completed = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        early = mode in {"existing-receipt", "existing-replay", "equal", "nested", "canonical-nested", "symlink-nested"}
        good = mode in {"default", "disjoint"}
        assert (completed.returncode == 0) == good, (mode, completed.stderr)
        assert marker.exists() == (not early and mode != "default"), mode
        if good:
            data = json.loads(receipt.read_bytes())
            assert data["passed"] and len(data["rejected_controls"]) == 29
            assert data["cad_execution_this_check"] == (mode == "disjoint")
            assert data["mode"] == ("VERIFIED_REPLAY" if mode == "disjoint" else "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY")
            if mode == "default": assert not output.exists()
            else:
                for path in (output / "base/geometry.json", output / "geometry.json"):
                    assert data["source_sha256"][str(path)] == sha(path)
                    assert json.loads(path.read_bytes())["synthetic_fixture"]
        elif mode == "existing-receipt": assert receipt.read_text() == "preserve existing receipt"
        elif mode == "existing-replay":
            assert (output / "existing.bin").read_bytes() == b"preserve existing output"
            assert not receipt.exists()
        elif mode == "exclusive-late":
            assert receipt.read_text() == "keep late receipt unchanged"
            assert "FileExistsError" in completed.stderr
        else: assert not receipt.exists(), mode
        cli_controls.append({"case": mode, "returncode": completed.returncode, "inner_producer_stub_invoked": marker.exists(), "passed": True})

for path, expected in TRUSTED.items():
    assert sha(path) == expected, path
assert gate.verify() == (frozen, pins)
result = {
    "schema": "eoere_v3_final_replay_independent_verification/v1",
    "passed": True,
    "substantial_findings": [],
    "python_version": sys.version.split()[0],
    "target_sha256": TRUSTED[TARGET],
    "source_sha256": {**{str(path): expected for path, expected in TRUSTED.items()}, str(Path(__file__).resolve()): sha(Path(__file__).resolve())},
    "complete_frozen_sources_verified": len(frozen),
    "all_unique_input_pins_verified": len(pins),
    "separate_initializer_gate_verified": True,
    "namespace_absence_gate_verified": True,
    "genuine_recorded_rejection_controls_verified": 29,
    "independent_changed_missing_input_controls": source_controls,
    "fresh_cli_subprocess_controls": cli_controls,
    "fixture_sha256": hashlib.sha256(STUB.encode()).hexdigest(),
    "unchanged_geometry_mesh_browser_evidence_reused_sha256": reused,
    "cad_execution": False,
    "native_solver": False,
    "actual_optional_CAD_replay_performed": False,
    "mechanics_or_physical_release": False,
    "limits": ["Optional replay tests use synthetic reports and generated bytes from a stubbed inner producer; they verify gate dispatch, source validation and failure handling only.", "Existing geometry, actual mesh and browser proofs are hash-reused; no CAD/BREP import, mesh materialization, browser or broad suite executed."],
}
with (HERE / "receipt.json").open("x") as stream:
    stream.write(json.dumps(result, indent=2) + "\n")
print(json.dumps({"passed": True, "recorded_controls": 29, "independent_cli_controls": len(cli_controls), "substantial_findings": []}))
