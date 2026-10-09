"""Independent bounded v2 provenance review; writes only its own receipt."""

import hashlib
import json
import types
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
V1 = DOC / "evidence-correction-v1"
V2 = V1 / "review-fix-v2"
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
V2_RAW = RAW / "evidence-correction-v1/review-fix-v2"
ATTEMPT = V2_RAW / "attempt02"
HERE = Path(__file__).resolve().parent
FREEZE_SHA = "1d214a9a31f37cdaf358a58daba2d143baf79e22787677516e8b6251933f83ce"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def authenticate(pins):
    actual = {}
    for path, pin in pins.items():
        data = (ROOT / path).read_bytes()
        expected = pin if isinstance(pin, str) else pin["sha256"]
        require(sha(data) == expected, f"Changed pinned source/evidence: {path}")
        if isinstance(pin, dict) and "bytes" in pin:
            require(len(data) == pin["bytes"], f"Changed byte count: {path}")
        actual[path] = sha(data)
    return actual


def tree_snapshot(directory):
    manifest = {}
    total = 0
    for item in sorted(directory.rglob("*")):
        path = str(item.relative_to(ROOT))
        if item.is_symlink():
            manifest[path] = {"symlink": str(item.readlink())}
        elif item.is_file():
            data = item.read_bytes()
            manifest[path] = {"bytes": len(data), "sha256": sha(data)}
            total += len(data)
    return {"entries": len(manifest), "file_bytes": total, "manifest_sha256": sha(encoded(manifest))}


def main():
    output = HERE / "receipt.json"
    require(not output.exists(), "Preserve the issued review receipt")
    freeze = (ATTEMPT / "frozen-packet.json").read_bytes()
    require(sha(freeze) == FREEZE_SHA, "Unrecognized v2 frozen map")
    targets = json.loads(freeze)
    metadata = json.loads((V2 / "inputs.json").read_bytes())
    targets.update(metadata["frozen_v1_files"])
    targets.update(json.loads((V1 / "inputs.json").read_bytes())["frozen_files"])
    require(len(targets) == 17, "Expected six v2 and eleven preserved target files")
    compact = json.loads((V2 / "verification.json").read_bytes())
    sources = compact["source_sha256"]
    require(len(sources) == 26, "Expected twenty-six source pins")
    raw_pins = {pin["path"]: pin for pin in compact["raw_evidence"]}
    original = json.loads((DOC / "verification.json").read_bytes())
    raw_pins.update({pin["path"]: pin for pin in original["run_files"].values()})
    before = {"targets": authenticate(targets), "sources": authenticate(sources), "raw": authenticate(raw_pins)}
    retained = [RAW / "evidence-correction-v1/attempt01", V2_RAW / "attempt01", ATTEMPT]
    before_trees = {str(path.relative_to(ROOT)): tree_snapshot(path) for path in retained}
    launcher_path = V2 / "run.py"
    launcher = types.ModuleType("independent_structure_v2_launcher")
    launcher.__file__ = str(launcher_path)
    exec(compile(launcher_path.read_bytes(), str(launcher_path), "exec"), launcher.__dict__)
    body = launcher.load_body()
    legacy = body.prepare()
    require(legacy.snapshot()["pins"] == sources, "Runtime source closure differs")
    writes = []
    unwritten = HERE / "unwritten-verification.json"

    def capture_write(path, data):
        require(Path(path) == unwritten, "Unexpected verifier write")
        writes.append(data)

    legacy.new_file = capture_write
    positive = legacy.verify(ATTEMPT / "fresh-run", ATTEMPT / "fresh-replay", unwritten)
    require(len(writes) == 1, "Clean verification must issue one receipt")
    require(writes[0] == (ATTEMPT / "clean-verification.json").read_bytes(), "Clean receipt changed")
    link = ATTEMPT / "symlinks/directory/linked-run"
    supplied = link / "../real-run"
    require(link.is_symlink(), "Existing inert symlink fixture required")
    files = [supplied / name for name in ("result.json", "details.json", "run-provenance.json")]
    identities, _ = body.lexical_snapshot(files)
    require(link not in identities, "Symlink unexpectedly retained by normalized snapshot")
    bypass = legacy.verify(supplied, ATTEMPT / "fresh-replay", unwritten)
    require(len(writes) == 2 and bypass["status"] == "VERIFIED_SYNTHETIC_ONLY", "Path edge case no longer reproduces")
    require(not unwritten.exists(), "Review unexpectedly wrote a verifier output")
    reg = json.loads((ATTEMPT / "regressions.json").read_bytes())
    require(len(reg["commands"]) == 17, "Changed issued command census")
    require([row["returncode"] for row in reg["commands"]] == [0] * 3 + [1] * 14, "Changed issued command statuses")
    replay = {}
    for name in ("result.json", "details.json", "run-provenance.json"):
        first = (ATTEMPT / "fresh-run" / name).read_bytes()
        require(first == (ATTEMPT / "fresh-replay" / name).read_bytes(), f"Replay differs: {name}")
        replay[name] = sha(first)
    after = {"targets": authenticate(targets), "sources": authenticate(sources), "raw": authenticate(raw_pins)}
    after_trees = {str(path.relative_to(ROOT)): tree_snapshot(path) for path in retained}
    require(before == after and before_trees == after_trees, "Review changed preserved files")
    result = {
        "schema": "synthetic_limit_v2_independent_structure_review/v1",
        "status": "SUBSTANTIAL_FINDING_CONFIRMED",
        "review_script_sha256": sha(Path(__file__).read_bytes()),
        "frozen_v2_map_sha256": FREEZE_SHA,
        "findings": [{
            "priority": "P2",
            "title": "Reject parent traversal before normalizing evidence paths",
            "file": str((V2 / "body.py").relative_to(ROOT)),
            "line": 36,
            "cause": "os.path.abspath collapses '..' before lstat traversal, so a symlink component canceled by '..' is never inspected or identity-pinned. The reused verifier still consumes the original path.",
            "reproduction": str(supplied.relative_to(ROOT)),
            "observed_status": bypass["status"],
            "impact": "A run path containing a symlink is accepted despite the documented policy. Later changes to that omitted component are outside the lexical identity checks, leaving the addressed evidence path unbound through receipt serialization.",
            "recommended_fix": "Reject supplied paths containing '..' before normalization, or inspect and retain every original traversal component. Add a real CLI control using the existing linked-run/../real-run fixture.",
        }],
        "target_count": len(targets),
        "source_count": len(sources),
        "target_files_sha256": before["targets"],
        "source_sha256": before["sources"],
        "raw_files_sha256": before["raw"],
        "targets_sources_and_raw_pins_unchanged": before == after,
        "retained_trees_before": before_trees,
        "retained_trees_after": after_trees,
        "clean_verification_reproduced_in_memory": True,
        "canceled_symlink_component_omitted_from_snapshot": True,
        "canceled_symlink_path_accepted_in_memory": True,
        "issued_three_file_replay_sha256": replay,
        "issued_command_statuses": {"successes": 3, "rejections": 14},
        "validated_claims": positive["validated_claims"],
        "independent_checks": positive["independent_checks"],
        "architecture_and_retention": [
            "Launcher owns captured-body execution; body owns raw feasibility and lexical path guards while retaining the frozen v1 production and compact verification implementation.",
            "All twenty-six declared source dependencies remain available and hash-matched, including prior review receipts consumed only as opaque bytes.",
            "Original method, v1 correction and both v2 attempts remain recoverable; no archive or prune is proposed.",
        ],
        "limits": [
            "Fresh bounded source/architecture/retention pass; did not inspect peer review findings.",
            "Used the existing inert symlink fixture without modification and intercepted both verifier writes; only this script and receipt are written.",
            "No LP optimization, CAD, native/global mechanics, candidate force fields, shared edits, staging, commits or pruning.",
            "Synthetic validation does not supply candidate resistance, acceptance, material qualification or physical-work authorization.",
        ],
    }
    with output.open("xb") as stream:
        stream.write(encoded(result))
    print(json.dumps({"status": result["status"], "findings": len(result["findings"]), "sources": len(sources)}, sort_keys=True))


if __name__ == "__main__":
    main()
