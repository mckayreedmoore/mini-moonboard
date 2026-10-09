"""Independent bounded CLI probes for v2; temporary fixtures belong to this review."""

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
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/evidence-correction-v1/review-fix-v2"
ISSUED = HERE.parents[1] / "attempt02"
MAP_SHA256 = "1d214a9a31f37cdaf358a58daba2d143baf79e22787677516e8b6251933f83ce"
NAMES = ("result.json", "details.json", "run-provenance.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def cli(arguments):
    command = [sys.executable, "-B", *map(str, arguments)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def summarize(path):
    if not path.exists():
        return {"receipt_exists": False}
    receipt = json.loads(path.read_bytes())
    return {"receipt_exists": True, "receipt": {k: receipt[k] for k in ("status", "validated_claims", "byte_identical_replay", "run_files_sha256")}}


def load_body():
    spec = importlib.util.spec_from_file_location("review_v2_launcher", DOC / "run.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    return launcher.load_body()


def retarget_main(base):
    """Same real main as the supported CLI; inject the owned path change at serialization."""
    legacy = load_body().prepare()
    encoded = legacy.encoded

    def retarget(value):
        data = encoded(value)
        if type(value) is dict and value.get("schema") == "synthetic_limit_corrected_verification/v1":
            replacement = base / "lexical/replacement-link"
            replacement.symlink_to(base / "altered/child", target_is_directory=True)
            os.replace(replacement, base / "lexical/link")
        return data

    legacy.encoded = retarget
    supplied = str(base / "lexical/link/../run")
    sys.argv = [str(DOC / "run.py"), "verify", "--run=" + supplied, "--replay", str(base / "replay"), "--out", str(base / "retarget-receipt.json")]
    legacy.main()


def main():
    map_bytes = (ISSUED / "frozen-packet.json").read_bytes()
    assert sha(map_bytes) == MAP_SHA256
    frozen = json.loads(map_bytes)
    verification = json.loads((DOC / "verification.json").read_bytes())
    watched = {ROOT / p for p in frozen}
    watched |= {ROOT / p for p in verification["source_sha256"]}
    watched |= {ROOT / pin["path"] for pin in verification["raw_evidence"]}
    watched |= {ISSUED / role / name for role in ("fresh-run", "fresh-replay") for name in NAMES}
    watched.add(ISSUED / "frozen-packet.json")
    before = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(watched)}
    for relative, pin in frozen.items():
        data = (ROOT / relative).read_bytes()
        assert sha(data) == pin["sha256"] and len(data) == pin["bytes"]
    assert len(verification["source_sha256"]) == 26
    for relative, expected in verification["source_sha256"].items():
        assert sha((ROOT / relative).read_bytes()) == expected
    for pin in verification["raw_evidence"]:
        data = (ROOT / pin["path"]).read_bytes()
        assert sha(data) == pin["sha256"] and len(data) == pin["bytes"]
    issued_regressions = json.loads((ISSUED / "regressions.json").read_bytes())
    issued_commands = issued_regressions["commands"]
    assert len(issued_commands) == 17
    assert all(c["returncode"] == 0 for c in issued_commands[:3])
    assert all(c["returncode"] != 0 for c in issued_commands[3:])
    assert all(c["stderr"].strip() for c in issued_commands[3:])
    for name in NAMES:
        assert (ISSUED / "fresh-run" / name).read_bytes() == (ISSUED / "fresh-replay" / name).read_bytes()
    original = DOC.parent.parent
    assert (ISSUED / "fresh-run/result.json").read_bytes() == (original / "result.json").read_bytes()
    evidence = {name: (ISSUED / "fresh-run" / name).read_bytes() for name in NAMES}
    base_result = json.loads(evidence["result.json"])
    controls, observations = [], []

    with tempfile.TemporaryDirectory(prefix="owned-v2-probes-", dir=HERE) as temporary:
        temporary = Path(temporary)

        def copied(directory):
            directory.mkdir(parents=True)
            for name, data in evidence.items():
                (directory / name).write_bytes(data)

        def verify(label, run, replay=ISSUED / "fresh-replay"):
            out = temporary / (label + ".json")
            record = cli([DOC / "run.py", "verify", "--run=" + str(run), "--replay", replay, "--out", out])
            record.update(label=label, **summarize(out))
            return record

        clean = verify("clean_issued", ISSUED / "fresh-run")
        assert clean["returncode"] == 0 and clean["receipt_exists"]
        controls.append(clean)

        # Ordinary .. remains a supported path when there are no symlink components.
        plain = temporary / "ordinary"
        copied(plain / "run")
        (plain / "child").mkdir()
        ordinary = verify("ordinary_dotdot", plain / "child/../run")
        assert ordinary["returncode"] == 0 and ordinary["receipt_exists"]
        controls.append(ordinary)

        # A symlink followed by .. is removed by abspath even though kernel path
        # traversal follows the symlink first. Both possible targets initially
        # have valid matching bytes, so a rejection cannot rely on content mismatch.
        race = temporary / "path-race"
        for role in ("lexical/run", "original/run", "altered/run", "replay"):
            copied(race / role)
        (race / "original/child").mkdir()
        (race / "altered/child").mkdir()
        (race / "lexical/link").symlink_to(race / "original/child", target_is_directory=True)
        supplied = race / "lexical/link/../run"
        static = verify("symlink_before_dotdot", supplied, race / "replay")
        static["supplied_result_resolves_to"] = str((supplied / "result.json").resolve())
        static["abspath_checked_by_v2"] = os.path.abspath(supplied / "result.json")
        observations.append(static)
        changed = copy.deepcopy(base_result)
        changed["candidate_joint_capacity"] = 12345.0
        (race / "altered/run/result.json").write_bytes(encode(changed))
        dynamic = cli([Path(__file__).resolve(), "retarget", race])
        dynamic.update(label="retarget_hidden_symlink_during_receipt", **summarize(race / "retarget-receipt.json"))
        dynamic["current_result_sha256"] = sha((supplied / "result.json").read_bytes())
        dynamic["current_candidate_joint_capacity"] = json.loads((supplied / "result.json").read_bytes())["candidate_joint_capacity"]
        if dynamic["receipt_exists"]:
            dynamic["receipt_hash_matches_current_result"] = dynamic["receipt"]["run_files_sha256"]["result.json"] == dynamic["current_result_sha256"]
        observations.append(dynamic)
        current = verify("retargeted_recheck", supplied, race / "replay")
        assert current["returncode"] != 0 and not current["receipt_exists"] and "Replay bytes differ" in current["stderr"]
        controls.append(current)

        # A tiny coordinated scale edit passes the necessary repair lower bound
        # but must still fail the separately reconstructed raw bearing bound.
        def forged_scale(label, factor, case_index):
            altered = copy.deepcopy(base_result)
            grid = altered["cases"][case_index]["grids"][0]
            grid["raw_LP_load_lbf"] *= factor
            grid["numerical_feasibility_scale"] /= factor
            data = encode(altered)
            provenance = json.loads(evidence["run-provenance.json"])
            provenance["output_sha256"]["result.json"] = sha(data)
            for role in ("run", "replay"):
                directory = temporary / label / role
                copied(directory)
                (directory / "result.json").write_bytes(data)
                (directory / "run-provenance.json").write_bytes(encode(provenance))
            return verify(label, temporary / label / "run", temporary / label / "replay")

        raw_bearing = forged_scale("raw_bearing_tolerance", 1 + 2e-8, 0)
        assert raw_bearing["returncode"] != 0 and not raw_bearing["receipt_exists"] and "Raw bearing field exceeds frozen tolerance" in raw_bearing["stderr"], raw_bearing
        controls.append(raw_bearing)
        raw_repair = forged_scale("other_coupon_large_repair", 1.001, 14)
        assert raw_repair["returncode"] != 0 and not raw_repair["receipt_exists"] and "Numerical repair exceeds frozen" in raw_repair["stderr"]
        controls.append(raw_repair)

        direct = cli([DOC / "body.py", "verify", "--run", ISSUED / "fresh-run", "--replay", ISSUED / "fresh-replay", "--out", temporary / "direct-body.json"])
        assert direct["returncode"] != 0 and "Use run.py" in direct["stderr"] and not (temporary / "direct-body.json").exists()
        controls.append({"label": "direct_body_rejected", **direct})

    after = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(watched)}
    assert before == after
    finding = dynamic["returncode"] == 0 and dynamic["receipt_exists"] and not dynamic["receipt_hash_matches_current_result"]
    receipt = {
        "schema": "independent_synthetic_evidence_testing_review/v2",
        "status": "FINDING_REPRODUCED" if finding else "NO_SUBSTANTIAL_FINDING_REPRODUCED",
        "target_frozen_map_sha256": MAP_SHA256,
        "review_command": "uv run python -B " + str(Path(__file__).resolve().relative_to(ROOT)),
        "review_script_sha256": sha(Path(__file__).read_bytes()),
        "source_and_issued_sha256_before": before,
        "source_and_issued_sha256_after": after,
        "all_watched_bytes_unchanged": before == after,
        "target_file_count": len(frozen),
        "watched_file_count": len(watched),
        "issued_audit": {"commands": 17, "successful_production_and_verification_commands": 3, "negative_commands_with_nonzero_exit_and_stderr": 14, "three_file_replay_matches": True, "original_numerical_result_unchanged": True},
        "controls": controls,
        "observations": observations,
        "findings": [{
            "priority": "P2", "file": str((DOC / "body.py").relative_to(ROOT)), "line": 36,
            "title": "Do not normalize away symlink components before checking them",
            "observed": "--run=lexical/link/../run is accepted even when link is a symlink. Retargeting link during final receipt serialization yields exit 0 / VERIFIED_SYNTHETIC_ONLY while --run exposes a non-null candidate capacity and a result hash different from the receipt.",
            "impact": "abspath collapses link/.. before lstat; the guard snapshots lexical/run while the verifier consumes another directory. The existing directory, ancestor and file symlink controls all omit .. and do not catch this bypass of both the no-symlink policy and evidence-drift rejection.",
            "fix": "Reject parent traversal in evidence arguments before normalization, or inspect supplied components without collapsing .. before symlink checks. Add a real CLI symlink/.. control and serialization-time retarget control requiring rejection and no receipt. Preserve ordinary relative-path behavior as intended.",
        }] if finding else [],
        "limits": ["Synthetic JSON and retained field-check CLI only; no CAD, BRep, candidate data, frame/global/native solve or physical work.", "Prior review receipts were authenticated as bytes without reading peer findings.", "Only this review.py and receipt.json remain; temporary owned fixtures were removed by TemporaryDirectory.", "No shared source edits, staging, commits, archive or pruning."],
    }
    (HERE / "receipt.json").write_bytes(encode(receipt))
    print(json.dumps({"status": receipt["status"], "controls": len(controls), "watched_files_unchanged": len(watched), "static_symlink_dotdot_returncode": static["returncode"], "retarget_returncode": dynamic["returncode"]}, sort_keys=True))


if __name__ == "__main__":
    retarget_main(Path(sys.argv[2])) if len(sys.argv) == 3 and sys.argv[1] == "retarget" else main()
