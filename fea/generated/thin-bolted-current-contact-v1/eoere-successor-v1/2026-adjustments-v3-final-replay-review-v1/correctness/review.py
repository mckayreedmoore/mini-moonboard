"""Source-only final review: byte authentication and isolated gate control flow."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
GATE = Path("scripts/check_eoere_2026_replay_inputs.py")
EXPECTED = {
    GATE: "185b4a9aedf2e10c2b53943b3086bf12a6992cc8b5d20e50b9104c08dcf8e2c1",
    BASE / "2026-adjustments-v10/replay-gate-v3/result.json": "c1bb7fee5a04b759fee475402761640e407c31f5aa4355a73084e6eb2046b695",
    BASE / "2026-adjustments-v10/replay-gate-v3/cli-controls-v2/cli-controls.json": "fa45aaa7a5f1df86042dba95f64251254fb9d2470e7ec99d9129021aff274c2a",
}
sources = {}
cache = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bind(path, expected=None):
    path = Path(path)
    data = path.read_bytes()
    actual = sha(data)
    if expected is not None:
        assert actual == expected, str(path)
    name = str(path.resolve())
    assert name not in sources or sources[name] == actual, name
    sources[name] = actual
    cache[name] = data
    return data


for path, expected in EXPECTED.items():
    bind(path, expected)
spec = importlib.util.spec_from_file_location("reviewed_source_gate", GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
assert "cadquery" not in sys.modules
assert not gate.NAMESPACE_INITIALIZER.exists()


def reader(path):
    name = str(Path(path).resolve())
    if name == str(gate.NAMESPACE_INITIALIZER.resolve()):
        raise FileNotFoundError(name)
    if name not in cache:
        bind(path)
    return cache[name]


frozen, pins = gate.verify(reader)
assert len(frozen) == 570 and len(pins) == 573
assert str(gate.INITIALIZER.resolve()) in pins
receipt = json.loads(reader(BASE / "2026-adjustments-v10/replay-gate-v3/result.json"))
assert receipt["passed"] and len(receipt["rejected_controls"]) == 29
assert receipt["mode"] == "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY"
assert receipt["cad_execution_this_check"] is False
assert receipt["original_v3_execution_used_this_gate"] is False
assert gate.join_pins(receipt["source_sha256"]) == {**pins, str(GATE.resolve()): EXPECTED[GATE]}
cli = json.loads(reader(BASE / "2026-adjustments-v10/replay-gate-v3/cli-controls-v2/cli-controls.json"))
assert cli["passed"] and cli["cad_execution"] is False
assert [row["case"] for row in cli["cases"]] == ["equal", "nested", "canonical-nested", "disjoint", "exclusive-late"]
for name, expected in cli["source_sha256"].items():
    bind(name, expected)

# Reuse the geometry, mesh and browser findings only after byte authentication.
reused = []
for relative in (
    "2026-adjustments-v3-review-v1/correctness/receipt.json",
    "2026-adjustments-v3-review-v1/correctness/panel-bores.json",
    "2026-adjustments-v3-review-v1/structure/receipt.json",
    "2026-adjustments-v3-review-v1/verification/verification-result-v1.json",
):
    path = BASE / relative
    record = json.loads(bind(path))
    for name, expected in record.get("source_sha256", record.get("frozen_inputs", {})).items():
        bind(name, expected)
    reused.append({"path": str(path), "sha256": sha(path.read_bytes())})
verification = json.loads(reader(BASE / "2026-adjustments-v3-review-v1/verification/verification-result-v1.json"))
for row in verification["screenshots"]:
    bind(row["path"], row["sha256"])
assert verification["passed"] and verification["substantial_findings"] == []
assert gate.PRODUCER.read_bytes() == (BASE / "2026-adjustments-v10/driver.py.snapshot").read_bytes()

controls = []


def rejects(name, operation, required_text):
    try:
        operation()
    except (ValueError, FileNotFoundError) as error:
        assert required_text in str(error), (name, str(error))
        controls.append({"case": name, "rejected": True})
    else:
        raise AssertionError(f"accepted {name}")


reads = []


def changed_parent(path):
    reads.append(str(path))
    return reader(path) + b"changed" if path.resolve() == gate.PARENT.resolve() else reader(path)


rejects("parent rejected before other input reads", lambda: gate.verify(changed_parent), "canonical source differs")
assert reads == [str(gate.PARENT)]
rejects("conflicting canonical aliases", lambda: gate.join_pins({str(gate.PRODUCER): "a" * 64}, {str(gate.PRODUCER.resolve()): "b" * 64}), "conflicting source bindings")
example = {"source_sha256": frozen}


def changed_initializer(path):
    return reader(path) + b"changed" if path.resolve() == gate.INITIALIZER.resolve() else reader(path)


rejects("post-replay initializer bytes changed", lambda: gate.verify_replay_bindings(example, frozen, HERE, changed_initializer), "canonical source differs")
changed_binding = {**frozen, str(gate.INITIALIZER.resolve()): "0" * 64}
rejects("post-replay explicit initializer binding changed", lambda: gate.verify_replay_bindings({"source_sha256": changed_binding}, frozen, HERE, reader), "replayed explicit executable input differs")

# Stub only the producer and reuse authenticated bytes; no CAD is imported/run.
real_verify, real_controls = gate.verify, gate.controls
real_bindings, real_run, real_argv = gate.verify_replay_bindings, subprocess.run, sys.argv
flow = []
try:
    with tempfile.TemporaryDirectory(prefix="source-only-controls-", dir=HERE) as temporary:
        work = Path(temporary)
        for case in ("default", "normal", "preflight-failure", "changed-after-run", "missing-base-binding", "missing-extra-binding", "outside-generated-binding"):
            events = []
            output, result = work / case / "replay", work / case / "receipt.json"

            def fake_verify():
                events.append("verify")
                if case == "preflight-failure":
                    raise ValueError("synthetic preflight failure")
                current = dict(pins)
                if case == "changed-after-run" and "producer" in events:
                    current[str(gate.PRODUCER.resolve())] = "0" * 64
                return dict(frozen), current

            def fake_run(command, **kwargs):
                assert command == [sys.executable, "-B", str(gate.PRODUCER), "--out", str(output)]
                assert kwargs == {"check": True}
                events.append("producer")
                for branch in ("base", "extra"):
                    report = {"source_sha256": dict(frozen)}
                    if case == f"missing-{branch}-binding":
                        report["source_sha256"].pop(str(gate.PRODUCER.resolve()))
                    if case == "outside-generated-binding":
                        report["source_sha256"][str((work / "outside.py").resolve())] = "0" * 64
                    path = output / "base/geometry.json" if branch == "base" else output / "geometry.json"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(report))
                return subprocess.CompletedProcess(command, 0)

            def replay_binding(report, expected, replay_output):
                events.append("binding")
                return real_bindings(report, expected, replay_output, reader)

            gate.verify, gate.controls = fake_verify, lambda: events.append("controls") or []
            gate.verify_replay_bindings, subprocess.run = replay_binding, fake_run
            sys.argv = [str(GATE), "--out", str(result)] + ([] if case == "default" else ["--run-out", str(output)])
            if case in ("default", "normal"):
                gate.main()
                issued = json.loads(result.read_bytes())
                assert issued["passed"] and issued["cad_execution_this_check"] == (case == "normal")
                assert events == (["verify", "controls"] if case == "default" else ["verify", "controls", "producer", "verify", "binding", "binding"])
            else:
                rejects(case, gate.main, "synthetic preflight failure" if case == "preflight-failure" else "changed during execution" if case == "changed-after-run" else "unexpected nongenerated" if case == "outside-generated-binding" else "replayed frozen source differs or is missing")
                assert not result.exists()
                if case == "preflight-failure":
                    assert events == ["verify"] and not output.exists()
                elif case == "changed-after-run":
                    assert events == ["verify", "controls", "producer", "verify"]
                else:
                    assert events[:4] == ["verify", "controls", "producer", "verify"]
            flow.append({"case": case, "events": events, "passed": True})
finally:
    gate.verify, gate.controls = real_verify, real_controls
    gate.verify_replay_bindings, subprocess.run, sys.argv = real_bindings, real_run, real_argv

docs = {}
for path in (Path("docs/wood-joints-mvp/README.md"), Path("docs/wood-joints-mvp/completion-ledger.md")):
    docs[str(path)] = sha(bind(path))
ledger = Path("docs/wood-joints-mvp/completion-ledger.md").read_text()
assert "2026-adjustments-v10/replay-gate-v3/result.json" in ledger
assert "records 29 rejection controls" in ledger
assert "optional CAD replay has not run" in ledger
assert "The original v3 production predates this gate" in ledger
assert "requires the `scripts` namespace initializer to remain absent" in ledger
for name, expected in sources.items():
    assert sha(Path(name).read_bytes()) == expected, name
result = {
    "schema": "eoere_final_replay_correctness_review/v1",
    "status": "NO_CONFIRMED_SUBSTANTIVE_FINDINGS",
    "findings": [],
    "target_sha256": EXPECTED[GATE],
    "authenticated_source_count": len(sources),
    "frozen_source_count": len(frozen),
    "additional_initializer_authenticated": True,
    "namespace_initializer_absent": not gate.NAMESPACE_INITIALIZER.exists(),
    "issued_no_CAD_receipt_authenticated": True,
    "source_only_CLI_proof_authenticated": True,
    "reused_geometry_mesh_browser_evidence": reused,
    "independent_negative_controls": controls,
    "isolated_main_control_flow": flow,
    "current_documentation_sha256": docs,
    "review_helper_sha256": sha(Path(__file__).read_bytes()),
    "reproduction_command": f".venv/bin/python -B {Path(__file__).relative_to(ROOT)}",
    "limits": [
        "Byte hashes, JSON and source-only known-answer controls; no CAD/BRep geometry query, browser recapture, mesh/native/global execution or Git mutation.",
        "Optional producer invocation was stubbed; a genuine CAD replay remains unperformed.",
        "Gate applies to future replay and does not retroactively qualify original production or structural/physical acceptance.",
        "Frozen absolute archive/source witnesses remain environment-bound; the gate is not a hermetic runtime/package certificate.",
    ],
}
with (HERE / "receipt.json").open("x") as handle:
    handle.write(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "controls": len(controls), "receipt_sha256": sha((HERE / "receipt.json").read_bytes())}))
