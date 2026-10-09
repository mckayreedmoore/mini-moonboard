"""Independent v3 path-boundary review, reusing the prior structure helper."""

import json
import subprocess
import sys
import types
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
V2 = DOC / "evidence-correction-v1/review-fix-v2"
V3 = V2 / "path-boundary-v3"
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
V2_RAW = RAW / "evidence-correction-v1/review-fix-v2"
V3_RAW = V2_RAW / "path-boundary-v3"
ATTEMPT = V3_RAW / "attempt02"
HERE = Path(__file__).resolve().parent
FREEZE_SHA = "4acc36d1b238177ed8f5cca62397a6d5d52eedb247d5b43b28ae870f1d5dd467"
HELPER_SHA = "4514c3a2c86a842c4f0259c2d2751663d4e72552567cc873d34da0693bc57e02"


def load_source(path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def main():
    helper_path = V2_RAW / "independent-review-v1/structure/review.py"
    # Reuse the previous independent hash/tree helpers, without reading peer findings.
    import hashlib

    if hashlib.sha256(helper_path.read_bytes()).hexdigest() != HELPER_SHA:
        raise ValueError("Changed independent review helper")
    helper = load_source(helper_path, "prior_independent_structure_helpers")
    require, sha, encoded = helper.require, helper.sha, helper.encoded
    output = HERE / "receipt.json"
    require(not output.exists(), "Preserve an issued receipt")
    freeze = (ATTEMPT / "frozen-packet.json").read_bytes()
    require(sha(freeze) == FREEZE_SHA, "Unrecognized v3 freeze")
    targets = json.loads(freeze)
    targets.update(json.loads((V3 / "inputs.json").read_bytes())["frozen_v2_files"])
    targets.update(json.loads((V2 / "inputs.json").read_bytes())["frozen_v1_files"])
    targets.update(json.loads((V2.parent / "inputs.json").read_bytes())["frozen_files"])
    require(len(targets) == 22, "Expected five v3 and seventeen preserved files")
    compact = json.loads((V3 / "verification.json").read_bytes())
    sources = compact["source_sha256"]
    require(len(sources) == 34, "Expected thirty-four source pins")
    raw_pins = {pin["path"]: pin for pin in compact["raw_evidence"]}
    before = {"targets": helper.authenticate(targets), "sources": helper.authenticate(sources), "raw": helper.authenticate(raw_pins)}
    trees = [V3_RAW / "attempt01", ATTEMPT]
    before_trees = {str(path.relative_to(ROOT)): helper.tree_snapshot(path) for path in trees}
    wrapper = load_source(V3 / "run.py", "independent_v3_path_wrapper")
    engine = wrapper._engine()
    require(engine.snapshot()["pins"] == sources, "Runtime closure differs")
    probe_results = []

    def forbidden(*args):
        raise AssertionError("Parent path reached engine/backend")

    def rejects(label, operation, args):
        try:
            operation(*args)
        except ValueError as error:
            require("Parent component '..'" in str(error), f"Wrong rejection: {label}")
            probe_results.append({"case": label, "rejected_before_backend": True})
        else:
            raise ValueError(f"Parent component accepted: {label}")

    ordinary = [ATTEMPT / "fresh-run", ATTEMPT / "fresh-replay", HERE / "unwritten-verification.json"]
    bad = HERE / "uncreated/../unwritten-target"
    make_engine = wrapper._engine
    wrapper._engine = forbidden
    try:
        rejects("public_produce_out", wrapper.produce, (bad,))
        for position, label in enumerate(("run", "replay", "out")):
            args = ordinary.copy()
            args[position] = bad
            rejects("public_verify_" + label, wrapper.verify, args)
    finally:
        wrapper._engine = make_engine
    for function, freevar, labels, base in (
        (engine.produce, "previous_produce", ("out",), [ordinary[2]]),
        (engine.verify, "previous_verify", ("run", "replay", "out"), ordinary),
    ):
        cell = dict(zip(function.__code__.co_freevars, function.__closure__))[freevar]
        previous = cell.cell_contents
        cell.cell_contents = forbidden
        try:
            for position, label in enumerate(labels):
                args = list(base)
                args[position] = bad
                rejects("backend_" + function.__name__ + "_" + label, function, args)
        finally:
            cell.cell_contents = previous
    cli_results = []
    commands = [[sys.executable, "-B", str(V3 / "run.py"), "produce", f"--out={bad}"]]
    for position in range(3):
        args = ordinary.copy()
        args[position] = bad
        commands.append([sys.executable, "-B", str(V3 / "run.py"), "verify", *[f"--{name}={path}" for name, path in zip(("run", "replay", "out"), args)]])
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        require(completed.returncode == 1 and "Parent component '..'" in completed.stderr, "CLI parent boundary failed")
        cli_results.append({"command": command, "returncode": completed.returncode, "stderr": completed.stderr})
    # Clean production evidence is checked through the unchanged engine; capture its output in memory.
    writes = []
    engine.new_file = lambda path, data: writes.append(data)
    positive = engine.verify(*ordinary)
    require(len(writes) == 1 and writes[0] == (ATTEMPT / "clean-verification.json").read_bytes(), "Clean verifier receipt changed")
    require(not ordinary[2].exists() and not (HERE / "uncreated").exists(), "Probe wrote an output")
    require(positive["validated_claims"] == {"candidate_inputs_used": False, "candidate_joint_capacity": None, "capacity_or_pass_claim": False}, "Synthetic claim boundary changed")
    replay = {}
    for name in ("result.json", "details.json", "run-provenance.json"):
        data = (ATTEMPT / "fresh-run" / name).read_bytes()
        require(data == (ATTEMPT / "fresh-replay" / name).read_bytes(), f"Issued replay differs: {name}")
        replay[name] = sha(data)
    reg = json.loads((ATTEMPT / "regressions.json").read_bytes())
    require([row["returncode"] for row in reg["commands"]] == [0] * 3 + [1] * 7, "Changed issued control census")
    after = {"targets": helper.authenticate(targets), "sources": helper.authenticate(sources), "raw": helper.authenticate(raw_pins)}
    after_trees = {str(path.relative_to(ROOT)): helper.tree_snapshot(path) for path in trees}
    require(before == after and before_trees == after_trees, "Review changed source/evidence bytes")
    result = {
        "schema": "synthetic_limit_v3_independent_structure_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_IN_BOUNDED_SCOPE",
        "findings": [],
        "review_script_sha256": sha(Path(__file__).read_bytes()),
        "reused_helper_sha256": HELPER_SHA,
        "frozen_v3_map_sha256": FREEZE_SHA,
        "target_count": len(targets),
        "source_count": len(sources),
        "target_files_sha256": before["targets"],
        "source_sha256": before["sources"],
        "raw_files_sha256": before["raw"],
        "targets_sources_and_raw_pins_unchanged": before == after,
        "retained_trees_before": before_trees,
        "retained_trees_after": after_trees,
        "API_parent_boundary_probes": probe_results,
        "actual_CLI_parent_boundary_probes": cli_results,
        "clean_verification_receipt_reproduced_in_memory": True,
        "issued_three_file_replay_sha256": replay,
        "issued_command_census": {"successes": 3, "rejections": 7},
        "validated_claims": positive["validated_claims"],
        "independent_checks": positive["independent_checks"],
        "architecture_and_retention": [
            "Public functions reject parent components before engine loading, and installed engine methods reject them before the preserved backend. CLI parsing retains these components for the same checks.",
            "V3 executes frozen captured v2 launcher bytes, extends the source closure and retains the prior mechanics, raw feasibility, finite schema, synthetic claims and lexical identity responsibilities.",
            "Five new files and seventeen preceding files are bound by the checked maps. Thirty-four source dependencies remain available, including prior receipts consumed only as opaque hash-bound bytes.",
            "Both v3 attempts remain recoverable, with the exploratory source-at-run preserved. No archival/pruning or substitution of old receipts is proposed.",
        ],
        "limits": [
            "Fresh bounded structure/source/claim review; reused prior hash/tree helper without reading peer findings.",
            "No synthetic LP optimization, CAD, native/global calculation, candidate field reads, shared edits, staging, commits or pruning.",
            "Verifier writes were intercepted. Actual negative CLI probes rejected before engine loading and wrote no outputs.",
            "Synthetic evidence supplies no candidate resistance, capacity, material qualification, fabrication instruction or release.",
        ],
    }
    with output.open("xb") as stream:
        stream.write(encoded(result))
    print(json.dumps({"status": result["status"], "API_probes": len(probe_results), "CLI_probes": len(cli_results)}, sort_keys=True))


if __name__ == "__main__":
    main()
