"""Independent architecture/source/retention review of a synthetic-only method."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "current-candidate.json").is_file())
PACKET_REL = "bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1" / PACKET_REL
BASE = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1" / PACKET_REL
FROZEN = BASE / "attempt03/frozen-packet.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def relative(path):
    return str(Path(path).relative_to(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    frozen_sha = sha(FROZEN)
    frozen = read(FROZEN)
    require(len(frozen) == 6, "six frozen packet files expected")
    require({Path(p).name for p in frozen} == {"README.md", "analyze.py", "verify.py", "inputs.json", "result.json", "verification.json"}, "packet file census")
    for path, record in frozen.items():
        require(sha(ROOT / path) == record["sha256"] and (ROOT / path).stat().st_size == record["bytes"], "frozen target mismatch: " + path)
    inputs, result, verification = (read(DOC / p) for p in ("inputs.json", "result.json", "verification.json"))
    input_pins = {r["path"]: r["sha256"] for r in inputs["references"]}
    require(len(input_pins) == 5, "five declared source references")
    for path, digest in input_pins.items():
        require(sha(ROOT / path) == digest, "declared source reference mismatch")
    for filename in ("analyze.py", "verify.py"):
        ast.parse((DOC / filename).read_bytes(), filename=filename)
    raw_before = {}
    for record in verification["run_files"].values():
        path = ROOT / record["path"]
        require(sha(path) == record["sha256"], "issued raw output mismatch")
        raw_before[record["path"]] = sha(path)
    require((DOC / "result.json").read_bytes() == (BASE / "attempt03/result.json").read_bytes(), "published result differs from issued output")
    require((DOC / "verification.json").read_bytes() == (BASE / "attempt03/verification.json").read_bytes(), "published verification differs from issued output")
    for filename in ("result.json", "details.json"):
        require((BASE / "attempt03" / filename).read_bytes() == (BASE / "replay" / filename).read_bytes(), "issued/replay output differs")
    producer = load("architecture_synthetic_producer", DOC / "analyze.py")
    checker = load("architecture_saved_field_checker", DOC / "verify.py")
    producer.check_pins(inputs)  # Environment and five references only; no LP calculation.
    independent = checker.check(result, read(BASE / "attempt03/details.json"), inputs)
    require(independent == verification["independent_checks"], "saved-field audit differs")
    require(independent["independently_integrated_fields"] == 45, "45-field audit census")
    require(result["analyze_sha256"] == sha(DOC / "analyze.py") and result["inputs_sha256"] == sha(DOC / "inputs.json"), "producer/source binding differs")
    require(verification["verify_sha256"] == sha(DOC / "verify.py"), "checker/source binding differs")
    require(result["source_pins"] == inputs["references"] and result["environment"] == inputs["environment"], "source/environment provenance differs")
    require(result["candidate_inputs_used"] is False and result["candidate_joint_capacity"] is None and result["capacity_or_pass_claim"] is False, "synthetic/candidate claim boundary")
    require(result["summary"]["case_count"] == 15 and result["summary"]["LP_benchmark_count"] == 45, "synthetic result census")
    require(set(result["summary"]["governing_modes_verified"]) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"}, "six raw mode census")
    local_links = []
    for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", (DOC / "README.md").read_text()):
        if not target.startswith("https:"):
            require((DOC / target.split("#")[0]).resolve().exists(), "missing local reading destination: " + label)
            local_links.append(target)
    # Exercise only fail-fast paths: neither command can calculate or write.
    guards = []
    for argv, marker in (
        ([sys.executable, "-B", str(DOC / "analyze.py"), "--out", str(BASE / "attempt03")], "must be a new directory"),
        ([sys.executable, "-B", str(DOC / "verify.py"), "--run", str(BASE / "attempt03"), "--replay", str(BASE / "replay"), "--out", str(BASE / "attempt03/verification.json")], "Verification output must be new"),
    ):
        completed = subprocess.run(argv, capture_output=True, text=True, check=False)
        require(completed.returncode == 2 and marker in completed.stderr, "existing-output guard did not reject")
        guards.append({"entrypoint": Path(argv[2]).name, "returncode": completed.returncode, "existing_output_rejected": True})
    for path, digest in raw_before.items():
        require(sha(ROOT / path) == digest, "guard altered issued raw output")
    for path, record in frozen.items():
        require(sha(ROOT / path) == record["sha256"], "target changed during architecture review")
    require(sha(FROZEN) == frozen_sha, "frozen map changed during review")
    producer.check_pins(inputs)
    require("cadquery" not in sys.modules, "unexpected CAD library import")
    retained_history = {relative(BASE / p): sha(BASE / p) for p in ("attempt01/prototype.py", "attempt02/source-at-run-inputs.json", "attempt02/source-at-run-analyze.py")}
    receipt = {
        "schema": "independent_synthetic_method_structure_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_FINDINGS",
        "findings": [],
        "scope": "Module ownership, declared dependencies, frozen provenance, reproducibility, claim boundaries, compact retention and output safety. Candidate current-force bridge and actual joint methods excluded.",
        "frozen_packet_map": {"path": relative(FROZEN), "sha256": frozen_sha},
        "frozen_packet_files": frozen,
        "permanent_file_count": len(frozen),
        "permanent_bytes": sum(r["bytes"] for r in frozen.values()),
        "five_source_references_verified_before_after": input_pins,
        "pinned_runtime_verified": producer.environment(),
        "producer_and_checker_source_bindings_verified": True,
        "published_issued_and_replay_result_details_bytes_agree": True,
        "saved_45_field_checker_exact_receipt_reproduction": independent,
        "guard_rejections": guards,
        "local_reading_destinations_verified": local_links,
        "history_source_witnesses_present_sha256": retained_history,
        "ownership_and_reuse": "The packet owns the synthetic LP, benchmark inputs and a separately expressed dimensional checker. It calls the existing fea.dowel_yield.single_shear helper and reads no candidate action/geometry/material tables. Predecessor result references establish frozen provenance only.",
        "retention": "Six compact permanent files total 90,651 bytes. Roughly 498-kB detailed fields remain in ignored issued/replay attempts; prototype and pre-cleanup input/source witnesses remain present. No copied manuals, meshes, dependencies, archives or pruning.",
        "scope_limits_preserved": "Scalar two-member statics and six raw mode comparisons only; no ASD value, compatible deformation, actual mixed-stack strength or physical release. Candidate resistance remains null and panel remedies paused.",
        "new_LP_solve_performed": False,
        "CAD_query_current_bank_frame_native_geometry_browser_global_case_performed": False,
        "target_and_issued_raw_files_unchanged": True,
        "staging_commit_or_prune_performed": False,
        "review_script_sha256": sha(__file__),
        "command": "PYTHONPATH=. .venv/bin/python -B " + relative(Path(__file__)),
    }
    output = Path(__file__).with_name("receipt.json")
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "receipt": relative(output), "receipt_sha256": sha(output)}))


if __name__ == "__main__":
    main()
