"""Independent source/architecture review; hashes and a source-only path control.

Run from the repository root with .venv/bin/python -B PATH/check.py.
No CAD modules, BREP readers, meshes, browsers, or native solvers are invoked.
"""

import hashlib
import json
import runpy
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1")
GATE = Path("scripts/check_eoere_2026_replay_inputs.py")
GATE_RECEIPT = BASE / "2026-adjustments-v10/replay-gate-v3/result.json"
CLI_RECEIPT = BASE / "2026-adjustments-v10/replay-gate-v3/cli-controls-v2/cli-controls.json"
FROZEN = {
    str(GATE): "185b4a9aedf2e10c2b53943b3086bf12a6992cc8b5d20e50b9104c08dcf8e2c1",
    str(GATE_RECEIPT): "c1bb7fee5a04b759fee475402761640e407c31f5aa4355a73084e6eb2046b695",
    str(CLI_RECEIPT): "fa45aaa7a5f1df86042dba95f64251254fb9d2470e7ec99d9129021aff274c2a",
    str(DOC / "occupied-adjusted-base-v3.json"): "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7",
    str(DOC / "occupied-2026-adjustments-v3.json"): "5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134",
    "scripts/eoere_2026_adjustments.py": "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
    "site/eoere-2026-adjustments-overlay.mjs": "b57759996903d1a5696f9cf5dca85af7e392a3cac38eaf6c5e15f49e54a5110d",
    "site/index.html": "1a1a8bbae255886214d6111769674bfafb8e80c72f3ebfa1acea319b2fa8b883",
    "site/eoere-adjusted-base-v3-scene.json.gz": "d77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947",
    "site/eoere-2026-adjustments-v3-scene.json.gz": "8682bf9a81c0bf8e7ffb23c3f6725adc6d3c9bd4728b00e50edb696ca3305d1d",
}
REUSED = {
    "2026-adjustments-v3-review-v1/structure/receipt.json": "2b4837adc7b6e2a8b4dfd0ba98ea3c7b218bfa14cd4bd909d38f6a1bb255b34a",
    "2026-adjustments-v3-review-v1/correctness/review.json": "2997304b9b6b431b01d3539d0c675da05bf60b218b8aa329e21032cc3fcc374d",
    "2026-adjustments-v3-review-v1/correctness/receipt.json": "0907933e79a0b24f9f2a2c9e7744ed08d7f2badb94a633dba1ea70d3afab1d13",
    "2026-adjustments-v3-review-v1/verification/verification-result-v1.json": "bee7b40d7f2171f78b65bcd41e0296c92e79cb27883144702179eb459fd512fc",
    "2026-adjustments-v10/actual-mesh-check-v1.json": "3d280e0003e970b909b79ee916444fde2088ed72b11b0c89195762084ad55816",
    "2026-adjustments-v10/browser-v1/result.json": "a4e5c4444d67df32a9b9e372739e614b9214d8023327229a2e5da01ee79b8d98",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


for name, expected in FROZEN.items():
    assert sha(name) == expected, name
gate = runpy.run_path(str(GATE.resolve()), run_name="independent_source_review")
frozen, pins = gate["verify"]()
assert len(frozen) == 570 and len(pins) == 573
base = read(DOC / "occupied-adjusted-base-v3.json")
extra = read(DOC / "occupied-2026-adjustments-v3.json")
assert base["source_sha256"] == extra["source_sha256"]
assert gate["join_pins"](base["source_sha256"]) == frozen
assert not any(Path(p).is_relative_to((BASE / "2026-adjustments-v10").resolve()) for p in frozen)
parent = read(gate["PARENT"])
canonical = {str(p): parent["source_sha256"][str(p)] for p in gate["INPUTS"]}
assert all(frozen[str(Path(p).resolve())] == expected for p, expected in canonical.items())
assert parent["source_sha256"][str(gate["INITIALIZER"])] == gate["INITIALIZER_SHA"]
assert not gate["NAMESPACE_INITIALIZER"].exists()
assert gate["join_pins"]({str(GATE): FROZEN[str(GATE)]}, {str(GATE.resolve()): FROZEN[str(GATE)]}) == {str(GATE.resolve()): FROZEN[str(GATE)]}
try:
    gate["join_pins"]({str(GATE): "a" * 64}, {str(GATE.resolve()): "b" * 64})
except ValueError:
    alias_conflict_rejected = True
else:
    raise AssertionError("conflicting path aliases accepted")

no_cad = read(GATE_RECEIPT)
assert no_cad["passed"] and no_cad["mode"] == "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY"
assert all(no_cad[k] is False for k in ("original_v3_execution_used_this_gate", "geometry_or_assets_reissued", "cad_execution_this_check", "native_solver"))
assert len(no_cad["rejected_controls"]) == 29
assert no_cad["new_generated_output_binding_control_passed"]
assert gate["join_pins"](no_cad["source_sha256"]) == {**pins, str(GATE.resolve()): FROZEN[str(GATE)]}
assert (BASE / "2026-adjustments-v10/replay-gate-v3/driver.py.snapshot").read_bytes() == GATE.read_bytes()
cli = read(CLI_RECEIPT)
assert cli["passed"] and cli["genuine_cli_subprocesses"] and cli["inner_producer_subprocess_stubbed"]
assert cli["cad_execution"] is False and cli["native_solver"] is False
assert [r["case"] for r in cli["cases"]] == ["equal", "nested", "canonical-nested", "disjoint", "exclusive-late"]
assert all(r["passed"] for r in cli["cases"])
for name, expected in cli["source_sha256"].items():
    assert sha(name) == expected, name

reused = []
for name, expected in REUSED.items():
    path = BASE / name
    assert sha(path) == expected, path
    evidence = read(path)
    for source, digest in evidence.get("source_sha256", {}).items():
        assert sha(source) == digest, source
    for source, digest in evidence.get("frozen_inputs", {}).items():
        assert sha(source) == digest, source
    reused.append({"path": str(path), "sha256": expected, "source_pins_rehashed": len(evidence.get("source_sha256", {}))})
for report, raw in [(DOC / "occupied-adjusted-base-v3.json", BASE / "2026-adjustments-v10/base/geometry.json"),
                    (DOC / "occupied-2026-adjustments-v3.json", BASE / "2026-adjustments-v10/geometry.json")]:
    assert report.read_bytes() == raw.read_bytes()
for report in (base, extra):
    assert report["mechanics_ready"] is False
    assert all(value is False for value in report["release"].values())
for row in read(BASE / "2026-adjustments-v3-review-v1/verification/verification-result-v1.json")["screenshots"]:
    assert sha(row["path"]) == row["sha256"]

# This unresolved opposite-ancestor case is outside the documented separate-path use.
# Only the producer subprocess is stubbed; the real main/preflight/postflight run.
with tempfile.TemporaryDirectory(prefix="receipt-ancestor-control-", dir=OUT) as work:
    receipt_path = Path(work) / "receipt.json"
    replay_path = receipt_path / "cad"
    observation = {"producer_stub_invoked": False, "cad_execution": False}

    def stub_run(args, **kwargs):
        observation["producer_stub_invoked"] = True
        output = Path(args[args.index("--out") + 1])
        output.mkdir(parents=True)
        for path in (output / "base/geometry.json", output / "geometry.json"):
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps({"source_sha256": frozen, "source_only_stub": True}))

    original_run, original_argv = gate["subprocess"].run, sys.argv
    gate["subprocess"].run = stub_run
    sys.argv = [str(GATE.resolve()), "--out", str(receipt_path), "--run-out", str(replay_path)]
    try:
        gate["main"]()
    except FileExistsError:
        observation.update({"raised": "FileExistsError", "receipt_created": False,
                            "requested_receipt_became_directory": receipt_path.is_dir(),
                            "fresh_stub_reports_written": (replay_path / "geometry.json").is_file(),
                            "existing_evidence_overwritten": False})
    else:
        raise AssertionError("receipt ancestor unexpectedly accepted")
    finally:
        gate["subprocess"].run, sys.argv = original_run, original_argv
assert observation["producer_stub_invoked"] and observation["requested_receipt_became_directory"]

readme_path = Path("docs/wood-joints-mvp/README.md")
ledger_path = Path("docs/wood-joints-mvp/completion-ledger.md")
readme, ledger = readme_path.read_text(), ledger_path.read_text()
for claim in ("geometry evidence only", "no historical pass transfers", "unofficial and not fully greenlit", "Local viewer changes do not assert publication"):
    assert claim in readme, claim
section = ledger.split("### Adjusted base and unofficial 2026 toggle\n", 1)[1].split("\n### ", 1)[0]
for claim in ("Omitting `--run-out` checks existing inputs without CAD", "optional CAD replay has not run",
              "The original v3 production predates this gate", "source-only\nproducer stub",
              "All release flags remain false", "No archive,\npruning, candidate selection or publication occurred"):
    assert claim in section, claim
assert "eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json --destination" in ledger
assert "uv sync --locked" in Path("CONTRIBUTING.md").read_text()
assert "cadquery" not in sys.modules and "OCP" not in sys.modules

result = {
    "schema": "eoere_v3_final_replay_architecture_review/v1",
    "status": "NO_CONFIRMED_SUBSTANTIVE_FINDINGS",
    "passed": True,
    "substantial_findings": [],
    "source_sha256": {**FROZEN, **{str(BASE / p): h for p, h in REUSED.items()},
                      str(readme_path): sha(readme_path), str(ledger_path): sha(ledger_path),
                      str(Path(__file__).relative_to(ROOT)): sha(__file__)},
    "source_contract": {"frozen_join_count": len(frozen), "verified_preflight_pins": len(pins),
                        "frozen_source_suffix_counts": dict(Counter(Path(p).suffix for p in frozen)),
                        "canonical_inputs_sha256": canonical,
                        "additional_initializer_sha256": gate["INITIALIZER_SHA"],
                        "scripts_initializer_absent": True, "conflicting_alias_rejected": alias_conflict_rejected,
                        "original_base_and_extra_share_source_map": True,
                        "new_generated_output_has_separate_ownership": True},
    "reused_evidence": reused,
    "source_only_gate": {"mode": no_cad["mode"], "rejection_controls": 29, "positive_generated_binding_control": True,
                         "cli_cases": [r["case"] for r in cli["cases"]], "optional_actual_CAD_replay_performed": False},
    "architecture_assessment": [
        "The stdlib wrapper authenticates parent-derived canonical metadata, the complete frozen producer/import/cache map and package bootstrap before launching the unchanged producer.",
        "Path resolution joins relative/absolute aliases and rejects differing bindings; postflight preserves every frozen source, permits new bindings only beneath the fresh replay root and rehashes each binding.",
        "CAD generation, publication assets, real mesh validation and browser validation remain separate layers; preserved source-bound geometry/mesh/browser evidence is reused without execution or reissue.",
        "The current summary and ledger distinguish nominal geometry, unofficial preview assumptions, historical mechanics, source-only gate evidence and the unperformed optional replay.",
        "The existing retention entry keeps current compact inputs/assets/helpers active and failed attempts recoverable; the preceding aligned-wire archive manifest and recovery command remain explicit dependencies."
    ],
    "minor_observations": [{"priority": "P3", "title": "Ancestor receipt path fails after fresh replay output creation",
                            "sources": ["scripts/check_eoere_2026_replay_inputs.py:207", "scripts/check_eoere_2026_replay_inputs.py:252"],
                            "control": observation,
                            "impact": "Invalid arguments can consume producer work before failing. No passed receipt or overwrite occurs; documented separate receipt/CAD paths avoid this edge case.",
                            "optional_improvement": "Reject both ancestry directions before a producer launch."}],
    "boundaries": [
        "Hash verification reads saved bytes only; no CAD/BREP import, mesh reconstruction, browser execution, native solve or complete test suite ran.",
        "The additional path control stubs only the inner producer subprocess and is not an actual CAD replay; its temporary synthetic reports were removed within this owned review folder.",
        "Frozen authority contains an external manifest and retained ignored caches. This is environment-bound replay evidence, not a self-contained fresh-clone bundle or a hermetic interpreter/third-party-environment attestation.",
        "Only this assigned ignored review folder was written; no shared source, geometry, assets or evidence was changed. Initial branch/status inspection was read-only; no Git mutation occurred.",
        "No structural acceptance, physical inspection, fabrication, drilling, candidate selection or publication is established."
    ],
    "python_version": sys.version.split()[0],
    "reproduction_command": ".venv/bin/python -B " + str(Path(__file__).relative_to(ROOT)),
    "mechanics_or_physical_release": False,
}
with (OUT / "receipt.json").open("x") as handle:
    handle.write(json.dumps(result, indent=2) + "\n")
print(json.dumps({"passed": True, "substantial_findings": 0, "minor_observations": 1,
                  "frozen_sources_rehashed": len(frozen), "receipt": str(OUT / "receipt.json")}))
