"""Fresh v3 boundary review, reusing the frozen v2 review's stdlib helpers."""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HELPER = HERE.parents[2] / "independent-review-v1/testing/review.py"
spec = importlib.util.spec_from_file_location("prior_testing_helpers", HELPER)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
ROOT, sha, encode, cli, summarize = prior.ROOT, prior.sha, prior.encode, prior.cli, prior.summarize
DOC = prior.DOC / "path-boundary-v3"
ISSUED = HERE.parents[1] / "attempt02"
MAP_SHA256 = "4acc36d1b238177ed8f5cca62397a6d5d52eedb247d5b43b28ae870f1d5dd467"
NAMES = prior.NAMES


def load_wrapper():
    spec = importlib.util.spec_from_file_location("independent_v3_path_wrapper", DOC / "run.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    return wrapper


def preflight(marker, arguments):
    wrapper = load_wrapper()

    def forbidden_engine():
        marker.write_text("unexpected engine entry\n")
        raise AssertionError("Engine reached before parent-path rejection")

    wrapper._engine = forbidden_engine
    sys.argv = [str(DOC / "run.py"), *arguments]
    wrapper.main()


def retarget(base, kind):
    wrapper = load_wrapper()
    engine_factory = wrapper._engine

    def instrumented():
        (base / "engine-entered").write_text("entered\n")
        engine = engine_factory()
        encoded = engine.encoded

        def changed(value):
            data = encoded(value)
            if type(value) is dict and value.get("schema") == "synthetic_limit_corrected_verification/v1":
                (base / "serialization-entered").write_text("entered\n")
                if kind == "parent":
                    (base / "link").unlink()
                    (base / "link").symlink_to(base / "altered/nested", target_is_directory=True)
                else:
                    active = base / "run"
                    active.rename(base / "preserved-run")
                    (base / "replacement").rename(active)
            return data

        engine.encoded = changed
        return engine

    wrapper._engine = instrumented
    supplied = base / "link/../run" if kind == "parent" else base / "run"
    sys.argv = [str(DOC / "run.py"), "verify", "--run=" + str(supplied), "--replay", str(base / "replay"), "--out", str(base / "receipt.json")]
    wrapper.main()


def main():
    assert sha(HELPER.read_bytes()) == "152ba51ec9b0491aeaf3ee4f3ae5eb77f06d322a10fb8f2d58149d92fc214bad"
    map_bytes = (ISSUED / "frozen-packet.json").read_bytes()
    assert sha(map_bytes) == MAP_SHA256
    frozen = json.loads(map_bytes)
    verification = json.loads((DOC / "verification.json").read_bytes())
    watched = {ROOT / p for p in frozen} | {ROOT / p for p in verification["source_sha256"]}
    watched |= {ROOT / p["path"] for p in verification["raw_evidence"]}
    watched |= {ISSUED / role / name for role in ("fresh-run", "fresh-replay") for name in NAMES}
    original_details = prior.ISSUED.parent.parent.parent / "attempt03/details.json"
    watched |= {ISSUED / "frozen-packet.json", HELPER, original_details}
    before = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(watched)}
    for relative, pin in frozen.items():
        data = (ROOT / relative).read_bytes()
        assert sha(data) == pin["sha256"] and len(data) == pin["bytes"]
    assert len(verification["source_sha256"]) == 34
    for relative, expected in verification["source_sha256"].items():
        assert sha((ROOT / relative).read_bytes()) == expected
    for pin in verification["raw_evidence"]:
        data = (ROOT / pin["path"]).read_bytes()
        assert sha(data) == pin["sha256"] and len(data) == pin["bytes"]
    issued = json.loads((ISSUED / "regressions.json").read_bytes())
    assert len(issued["commands"]) == 10
    assert all(c["returncode"] == 0 for c in issued["commands"][:3])
    assert all(c["returncode"] != 0 for c in issued["commands"][3:])
    assert len(issued["API_parent_path_controls_rejected"]) == 4
    for name in NAMES:
        assert (ISSUED / "fresh-run" / name).read_bytes() == (ISSUED / "fresh-replay" / name).read_bytes()
    original = prior.DOC.parent.parent
    assert (ISSUED / "fresh-run/result.json").read_bytes() == (original / "result.json").read_bytes()
    assert (ISSUED / "fresh-run/details.json").read_bytes() == original_details.read_bytes()
    controls, api_controls = [], []
    evidence = {name: (ISSUED / "fresh-run" / name).read_bytes() for name in NAMES}
    with tempfile.TemporaryDirectory(prefix="owned-v3-probes-", dir=HERE) as temporary:
        temporary = Path(temporary)

        def copied(directory):
            directory.mkdir(parents=True)
            for name, data in evidence.items():
                (directory / name).write_bytes(data)

        # Use the public CLI with its unchanged source and issued distinct runs.
        out = temporary / "positive.json"
        supplied = "./" + str((ISSUED / "fresh-run").relative_to(ROOT))
        positive = cli([DOC / "run.py", "verify", "--run=" + supplied, "--replay", ISSUED / "fresh-replay", "--out", out])
        positive.update(label="ordinary_relative_replay", **summarize(out))
        assert positive["returncode"] == 0 and positive["receipt_exists"]
        controls.append(positive)

        valid, bad = ISSUED / "fresh-run", temporary / "nonexistent/../run"
        for label, arguments in (
            ("produce_out", ["produce", "--out=" + str(bad)]),
            ("verify_run", ["verify", "--run=" + str(bad), "--replay", valid, "--out", temporary / "bad-run.json"]),
            ("verify_replay", ["verify", "--run", valid, "--replay=" + str(bad), "--out", temporary / "bad-replay.json"]),
            ("verify_out", ["verify", "--run", valid, "--replay", valid, "--out=" + str(bad)]),
        ):
            marker = temporary / (label + "-engine-entered")
            result = cli([Path(__file__).resolve(), "preflight", marker, *arguments])
            assert result["returncode"] == 1 and "Parent component '..'" in result["stderr"] and not marker.exists()
            controls.append({"label": label, "engine_entered": False, **result})

        # Recreate the reported symlink/.. form with an installed retarget hook.
        for kind in ("parent", "ordinary"):
            base = temporary / kind
            for role in ("run", "replacement", "replay"):
                copied(base / role)
            for role in ("actual/run", "altered/run"):
                copied(base / role)
            for role in ("actual/nested", "altered/nested"):
                (base / role).mkdir()
            altered = json.loads((base / "altered/run/result.json").read_bytes())
            altered["candidate_joint_capacity"] = 12345.0
            (base / "altered/run/result.json").write_bytes(encode(altered))
            (base / "link").symlink_to(base / "actual/nested", target_is_directory=True)
            result = cli([Path(__file__).resolve(), "retarget", base, kind])
            result.update(label=kind + "_serialization_retarget", engine_entered=(base / "engine-entered").exists(), serialization_entered=(base / "serialization-entered").exists(), receipt_exists=(base / "receipt.json").exists())
            assert result["returncode"] == 1 and not result["receipt_exists"]
            if kind == "parent":
                assert "Parent component '..'" in result["stderr"] and not result["engine_entered"] and not result["serialization_entered"]
            else:
                assert "Lexical evidence identity changed:" in result["stderr"] and result["engine_entered"] and result["serialization_entered"]
            controls.append(result)

        wrapper = load_wrapper()
        engine_factory = wrapper._engine
        wrapper._engine = lambda: (_ for _ in ()).throw(AssertionError("Public API reached engine"))
        operations = [("produce_out", lambda target: target.produce(bad)), ("verify_run", lambda target: target.verify(bad, valid, temporary / "api-run.json")), ("verify_replay", lambda target: target.verify(valid, bad, temporary / "api-replay.json")), ("verify_out", lambda target: target.verify(valid, valid, bad))]
        for label, operation in operations:
            try:
                operation(wrapper)
            except ValueError as error:
                assert "Parent component '..'" in str(error)
                api_controls.append("public_" + label)
            else:
                raise AssertionError("Public API accepted parent component")
        wrapper._engine = engine_factory
        engine = wrapper._engine()
        for label, operation in operations:
            try:
                operation(engine)
            except ValueError as error:
                assert "Parent component '..'" in str(error)
                api_controls.append("backend_" + label)
            else:
                raise AssertionError("Backend API accepted parent component")

    after = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(watched)}
    assert after == before
    receipt = {"schema": "independent_synthetic_path_boundary_testing/v3", "status": "NO_SUBSTANTIAL_FINDINGS", "findings": [], "target_frozen_map_sha256": MAP_SHA256, "review_command": "uv run python -B " + str(Path(__file__).resolve().relative_to(ROOT)), "review_script_sha256": sha(Path(__file__).read_bytes()), "reused_helper_sha256": sha(HELPER.read_bytes()), "target_file_count": len(frozen), "watched_file_count": len(watched), "source_and_issued_sha256_before": before, "source_and_issued_sha256_after": after, "all_watched_bytes_unchanged": before == after, "issued_audit": {"commands": 10, "successful_production_and_verification_commands": 3, "negative_CLI_controls": 7, "API_controls": 4, "three_file_byte_identical_replay": True, "result_and_45_fields_match_original_bytes": True}, "fresh_controls": controls, "fresh_API_controls": api_controls, "limits": ["Synthetic evidence path boundary and retained verification only; no new mechanics, CAD, native or current-frame work.", "Preserved source/review receipts authenticated as bytes; no peer findings read.", "Temporary fixtures exclusively owned and removed by TemporaryDirectory; no shared edits, staging, archive or pruning."]}
    (HERE / "receipt.json").write_bytes(encode(receipt))
    print(json.dumps({"status": receipt["status"], "fresh_CLI_controls": len(controls), "fresh_API_controls": len(api_controls), "watched_files_unchanged": len(watched)}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "preflight":
        preflight(Path(sys.argv[2]), sys.argv[3:])
    elif len(sys.argv) == 4 and sys.argv[1] == "retarget":
        retarget(Path(sys.argv[2]), sys.argv[3])
    else:
        main()
