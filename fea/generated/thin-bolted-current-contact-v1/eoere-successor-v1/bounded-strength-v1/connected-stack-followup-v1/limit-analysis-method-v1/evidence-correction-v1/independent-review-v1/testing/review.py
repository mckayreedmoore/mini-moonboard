"""Independent CLI coverage probes; all temporary fixtures are reviewer-owned."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
CORRECTION = DOC / "evidence-correction-v1"
RAW = HERE.parents[1]
ISSUED = RAW / "attempt01"
NAMES = ("result.json", "details.json", "run-provenance.json")
MAP_SHA = "ace9ab9d51c7f6320fb87be5f88329299f38b4bde5e7f1a9f2f0d77e98d2d371"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=True) + "\n").encode()


def summarize_receipt(receipt):
    return {k: receipt[k] for k in ("status", "validated_claims", "byte_identical_replay", "run_files_sha256")}


def load_correction():
    spec = importlib.util.spec_from_file_location("independent_correction", CORRECTION / "correction.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def retarget_main(base):
    """Invoke the unmodified main, retargeting one owned symlink at serialization."""
    correction = load_correction()
    original_encode = correction.encoded

    def retarget(value):
        data = original_encode(value)
        if type(value) is dict and value.get("schema") == "synthetic_limit_corrected_verification/v1":
            link = base / "run-link"
            replacement = base / "replacement-link"
            replacement.symlink_to(base / "altered-run", target_is_directory=True)
            os.replace(replacement, link)
        return data

    correction.encoded = retarget
    sys.argv = [str(CORRECTION / "correction.py"), "verify", "--run", str(base / "run-link"), "--replay", str(base / "replay"), "--out", str(base / "accepted-receipt.json")]
    correction.main()


def run_cli(arguments):
    command = [sys.executable, "-B", *map(str, arguments)]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def main():
    frozen_map = json.loads((CORRECTION / "inputs.json").read_bytes())["frozen_files"]
    correction_map_bytes = (ISSUED / "frozen-packet.json").read_bytes()
    assert digest(correction_map_bytes) == MAP_SHA
    correction_map = json.loads(correction_map_bytes)
    verification = json.loads((CORRECTION / "verification.json").read_bytes())
    sources = {**frozen_map, **correction_map}
    watched = {ROOT / p for p in sources}
    watched |= {ROOT / p for p in verification["source_sha256"]}
    watched |= {ROOT / p["path"] for p in verification["raw_evidence"]}
    watched.add(ISSUED / "frozen-packet.json")
    watched |= {ISSUED / role / name for role in ("fresh-run", "fresh-replay") for name in NAMES}
    before = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(watched)}
    for relative, pin in sources.items():
        data = (ROOT / relative).read_bytes()
        assert len(data) == pin["bytes"] and digest(data) == pin["sha256"]
    for relative, pin in verification["source_sha256"].items():
        assert digest((ROOT / relative).read_bytes()) == pin
    for pin in verification["raw_evidence"]:
        data = (ROOT / pin["path"]).read_bytes()
        assert len(data) == pin["bytes"] and digest(data) == pin["sha256"]
    issued_regressions = json.loads((ISSUED / "regressions.json").read_bytes())
    commands = issued_regressions["commands"]
    assert len(commands) == 36 and sum(c["returncode"] == 0 for c in commands) == 3
    assert len(issued_regressions["real_CLI_corruptions_rejected"]) == 23
    assert len(issued_regressions["real_CLI_source_drift_rejected_before_any_output"]) == 5
    assert all(c["returncode"] == 1 and c["stderr"].startswith("Evidence rejected:") for c in commands[8:31])
    assert all(c["returncode"] != 0 and "Source/evidence drift:" in c["stderr"] for c in commands[31:])
    issued_regression_audit = {"commands": len(commands), "successes": 3, "rejections": 33, "forged_result_controls_with_expected_evidence_rejection": 23, "source_drift_controls_with_specific_drift_rejection": 5, "regressions_sha256": digest((ISSUED / "regressions.json").read_bytes())}
    evidence = {name: (ISSUED / "fresh-run" / name).read_bytes() for name in NAMES}
    base_result = json.loads(evidence["result.json"])
    base_details = json.loads(evidence["details.json"])
    base_provenance = json.loads(evidence["run-provenance.json"])
    controls = []
    observations = []

    with tempfile.TemporaryDirectory(prefix="owned-probes-", dir=HERE) as temporary:
        temporary = Path(temporary)

        def verify(run, replay, out):
            result = run_cli([CORRECTION / "correction.py", "verify", "--run", run, "--replay", replay, "--out", out])
            result["receipt_exists"] = out.exists()
            if out.exists():
                result["receipt"] = summarize_receipt(json.loads(out.read_bytes()))
            return result

        clean = verify(ISSUED / "fresh-run", ISSUED / "fresh-replay", temporary / "clean.json")
        assert clean["returncode"] == 0 and clean["receipt_exists"]
        controls.append({"label": "issued_distinct_replay", **clean})

        # Every forged pair has matching replay bytes and updated hash bindings.
        def forged(label, edit_result=None, edit_details=None, edit_provenance=None, missing_marker=False):
            result, details, provenance = map(copy.deepcopy, (base_result, base_details, base_provenance))
            if edit_result:
                edit_result(result)
            if edit_details:
                edit_details(details)
            values = {"result.json": encode(result), "details.json": encode(details)}
            provenance["output_sha256"] = {name: digest(data) for name, data in values.items()}
            if edit_provenance:
                edit_provenance(provenance)
            values["run-provenance.json"] = encode(provenance)
            for role in ("run", "replay"):
                destination = temporary / label / role
                destination.mkdir(parents=True)
                for name, data in values.items():
                    if not (missing_marker and name == "run-provenance.json"):
                        (destination / name).write_bytes(data)
            return verify(temporary / label / "run", temporary / label / "replay", temporary / label / "receipt.json")

        first_key = next(iter(base_details))
        negative_probes = [
            ("missing_marker", {"missing_marker": True}, "No such file"),
            ("extra_provenance_capacity", {"edit_provenance": lambda p: p.update(fabrication_release=True)}, "Bad production provenance schema"),
            ("boolean_case_count", {"edit_result": lambda r: r["summary"].update(case_count=True)}, "Wrong summary census"),
            ("extra_detail_claim", {"edit_details": lambda d: d[first_key].update(candidate_joint_capacity=123.0)}, "Bad field schema"),
            ("nonfinite_density", {"edit_details": lambda d: d[first_key]["bearing_density_lb_in"].__setitem__(0, float("nan"))}, "Nonfinite JSON constant"),
            ("wrong_end_moment", {"edit_result": lambda r: r["cases"][0]["grids"][0].update(end_moment_lb_in=123.0)}, "Changed reported end moment"),
        ]
        for label, arguments, expected in negative_probes:
            result = forged(label, **arguments)
            assert result["returncode"] != 0 and not result["receipt_exists"] and expected in result["stderr"], result
            controls.append({"label": label, **result})

        same = verify(ISSUED / "fresh-run", ISSUED / "fresh-run", temporary / "same-run.json")
        observations.append({"label": "same_directory_used_twice", **same})
        ratio = forged("invented_control_ratio", edit_result=lambda r: r["solver_controls"].update(loose_bending_cap_load_ratio=1e99))
        observations.append({"label": "invented_control_ratio", "original_ratio": base_result["solver_controls"]["loose_bending_cap_load_ratio"], "forged_ratio": 1e99, **ratio})

        # Existing regular-file drift is tested by the packet. This adds a
        # directory-symlink retarget while leaving the resolved old files intact.
        race = temporary / "retarget"
        for role in ("original-run", "altered-run", "replay"):
            directory = race / role
            directory.mkdir(parents=True)
            for name, data in evidence.items():
                (directory / name).write_bytes(data)
        altered = copy.deepcopy(base_result)
        altered["candidate_joint_capacity"] = 12345.0
        (race / "altered-run/result.json").write_bytes(encode(altered))
        (race / "run-link").symlink_to(race / "original-run", target_is_directory=True)
        retarget = run_cli([Path(__file__).resolve(), "retarget", race])
        accepted = race / "accepted-receipt.json"
        retarget["receipt_exists"] = accepted.exists()
        retarget["new_current_capacity"] = json.loads((race / "run-link/result.json").read_bytes())["candidate_joint_capacity"]
        retarget["current_result_sha256"] = digest((race / "run-link/result.json").read_bytes())
        if accepted.exists():
            receipt = json.loads(accepted.read_bytes())
            retarget["receipt"] = summarize_receipt(receipt)
            retarget["receipt_hash_matches_current_result"] = receipt["run_files_sha256"]["result.json"] == retarget["current_result_sha256"]
        observations.append({"label": "directory_symlink_retarget_after_receipt_serialization", **retarget})
        current = verify(race / "run-link", race / "replay", race / "second-receipt.json")
        assert current["returncode"] != 0 and not current["receipt_exists"] and "Replay bytes differ" in current["stderr"]
        controls.append({"label": "recheck_retargeted_evidence_rejects", **current})

    after = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(watched)}
    assert after == before, "Source or issued evidence changed"
    receipt = {
        "schema": "independent_synthetic_evidence_testing_review/v1",
        "question": "Do real CLI rejection controls and final evidence stability checks cover false-positive verification receipts?",
        "review_command": "uv run python -B " + str(Path(__file__).resolve().relative_to(ROOT)),
        "target_frozen_map_sha256": MAP_SHA,
        "target_count": len(sources),
        "watched_file_count": len(watched),
        "source_and_issued_sha256_before": before,
        "source_and_issued_sha256_after": after,
        "all_watched_bytes_unchanged": before == after,
        "issued_regression_audit": issued_regression_audit,
        "controls": controls,
        "observations": observations,
        "review_script_sha256": digest(Path(__file__).read_bytes()),
        "limits": ["Synthetic JSON and stdlib/retained dimensional-check CLI only.", "No CAD, BRep, panel bank, frame stiffness, native mechanics, shared edits, staging, commits or archive pruning.", "Prior independent review receipts were hash-checked without reading their findings.", "Temporary fixtures were exclusively reviewer-created and removed by TemporaryDirectory."],
        "findings": [{
            "priority": "P2",
            "file": str((CORRECTION / "correction.py").relative_to(ROOT)),
            "line": 581,
            "title": "Recheck the consumed evidence paths as well as their resolved targets",
            "observed": "Retargeting the run directory symlink to changed evidence during receipt serialization exits 0 and writes VERIFIED_SYNTHETIC_ONLY; the receipt hash disagrees with the result now reachable at --run.",
            "impact": "The final evidence-drift guard certifies an old resolved target while the supplied run path points to different, unverified evidence. The existing regular-file drift regression misses this false-positive receipt path.",
            "fix": "Keep each original absolute lexical evidence path and its resolved identity; after serialization verify both path resolution and consumed bytes are unchanged, or reject symlinked evidence paths. Add a CLI regression for directory/file symlink retargeting that requires rejection and no receipt.",
        }] if retarget["returncode"] == 0 and retarget["receipt_exists"] and not retarget["receipt_hash_matches_current_result"] else [],
        "status": "FINDING_REPRODUCED" if retarget["returncode"] == 0 and retarget["receipt_exists"] and not retarget["receipt_hash_matches_current_result"] else "NO_FINDING_REPRODUCED",
    }
    (HERE / "receipt.json").write_bytes(encode(receipt))
    print(json.dumps({"status": receipt["status"], "negative_controls": len(negative_probes) + 1, "source_unchanged": before == after, "observations": [{"label": o["label"], "returncode": o["returncode"]} for o in observations]}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "retarget":
        retarget_main(Path(sys.argv[2]))
    else:
        main()
