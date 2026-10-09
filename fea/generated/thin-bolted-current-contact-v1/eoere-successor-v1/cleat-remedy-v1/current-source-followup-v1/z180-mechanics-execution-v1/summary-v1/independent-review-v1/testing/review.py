"""Bounded inert testing review; no genuine candidate artifacts or operations."""
import builtins
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "summarize.py": "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d",
    "test_summarize.py": "53fb7a6a9be0678116f877de6b7659a8b9356406765b9ca9035b32059d1dcb7d",
    "source-proof.json": "94fb0a568c3d8332c30653b136c5b57e2d0fdffe4e2353a10a705d90b514be39",
    "verification.json": "d74713c46802bb959b450646175fa08f907ce403ee31cdc3dbae5deaa2b79c09",
}
FORBIDDEN = {"cadquery", "OCP", "numpy", "scipy"}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def rejected(call, text):
    try:
        call()
    except (ValueError, FileExistsError) as error:
        require(text in str(error), f"unexpected rejection: {error!r}, wanted {text!r}")
        return {"type": type(error).__name__, "message": str(error)}
    raise AssertionError("invalid fixture accepted")


def snapshot(paths):
    return {str(path.relative_to(ROOT)): {"sha256": digest(path), "bytes": path.stat().st_size}
            for path in paths}


def read_case(fixture, index):
    binding = fixture.manifest["cases"][index]
    refs = {**binding["component"], "field": binding["field"], "admission": binding["admission"]}
    docs = {key: json.loads((fixture.root/ref["path"]).read_bytes())
            for key, ref in refs.items() if key not in ("stdout", "stderr")}
    for key in ("source_pins_before", "source_pins_after"):
        docs[key] = json.loads((fixture.root/docs["process"][key]["path"]).read_bytes())
    return docs


def restitch(fixture, index, docs):
    """Repair byte/reference joins so each corruption reaches its semantic guard."""
    binding = fixture.manifest["cases"][index]
    refs = binding["component"]
    field = fixture.save(binding["field"]["path"], docs["field"])
    docs["admission"].update(input_raw_sha256=field["sha256"],
                             input_canonical_sha256=hashlib.sha256(json.dumps(
                                 docs["field"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest())
    admission = fixture.save(binding["admission"]["path"], docs["admission"])
    binding.update(field=field, admission=admission)
    for key in ("config", "result"):
        docs[key].update(field=field, admission=admission)
        refs[key] = fixture.save(refs[key]["path"], docs[key])
    process = docs["process"]
    process.update(field=field, admission=admission)
    for key in ("config", "result"):
        process[key] = {**refs[key], "bytes": (fixture.root/refs[key]["path"]).stat().st_size}
    for key in ("source_pins_before", "source_pins_after"):
        ref = fixture.save(process[key]["path"], docs[key])
        process[key] = {**ref, "bytes": (fixture.root/ref["path"]).stat().st_size}
    process["command"][process["command"].index("--config-sha256")+1] = refs["config"]["sha256"]
    refs["process"] = fixture.save(refs["process"]["path"], process)
    fixture.ref = fixture.save("manifest.json", fixture.manifest)


def set_value(docs, path, value):
    row = docs
    for key in path[:-1]:
        row = row[key]
    row[path[-1]] = value


def coherent_state(docs):
    for key in ("field", "admission", "result", "config"):
        docs[key]["state_id"] = "eoere-z180-fixed-floor-inert-0"


def run():
    require(not (OUT/"receipt.json").exists(), "receipt already issued")
    target_paths = [PACKET/name for name in EXPECTED]
    for path in target_paths:
        require(digest(path) == EXPECTED[path.name], f"frozen target drift: {path.name}")
    verification = json.loads((PACKET/"verification.json").read_bytes())
    proof = json.loads((PACKET/"source-proof.json").read_bytes())
    method_pins = verification["verified_method_sources"]
    require(method_pins == proof["verified_source_pins"], "method proof pin maps differ")
    for path, expected in method_pins.items():
        require(digest(ROOT/path) == expected, f"method source drift: {path}")
    paths = list(dict.fromkeys([*target_paths, *(ROOT/path for path in method_pins)]))
    before = snapshot(paths)
    checks = {}
    real_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        require(name.split(".")[0] not in FORBIDDEN, "forbidden dependency import: "+name)
        return real_import(name, *args, **kwargs)
    with tempfile.TemporaryDirectory(prefix="inert-", dir=OUT) as scratch_name, pytest.MonkeyPatch.context() as import_patch:
        scratch = Path(scratch_name)
        import_patch.setattr(builtins, "__import__", guarded_import)
        tests = load(PACKET/"test_summarize.py", "independent_z180_saved_fixture")
        a = tests.a

        @contextlib.contextmanager
        def fixture(name):
            root = scratch/name
            root.mkdir()
            with pytest.MonkeyPatch.context() as patch:
                value = tests.fixture.__wrapped__(root, patch)
                yield value, patch

        def probe(name, mutation, message, index=0):
            with fixture(name) as (value, _):
                docs = read_case(value, index)
                mutation(docs)
                restitch(value, index, docs)
                checks[name] = rejected(lambda: a.build(value.manifest, value.ref), message)

        mutations = [
            ("coherent_duplicate_state", coherent_state, "six unique", 1),
            ("wrong_accessory", lambda d: set_value(d, ("result", "accessory_placement"), "other"), "same-state own identity", 0),
            ("wrong_config_state", lambda d: set_value(d, ("config", "state_id"), "other"), "exact combined consumer config", 0),
            ("admission_failed", lambda d: set_value(d, ("admission", "unadopted_z180_equilibrium_and_recovery_pass"), False), "schemas/admission", 0),
            ("release_true", lambda d: set_value(d, ("result", "release", "fabrication_released"), True), "all-false", 0),
            ("nonnull_coarse_joint", lambda d: set_value(d, ("result", "findings", "coarse", "angle_duties", 0,
                                                       "complete_group_heel_hole_prying_or_corner_resistance"), 1), "24 complete joints", 0),
            ("nonnull_rich_joint", lambda d: set_value(d, ("result", "findings", "rich", "timber", "duties", 0,
                                                     "complete_joint_resistance_n"), 1), "24 unknown joints", 0),
            ("own16_duplicate", lambda d: set_value(d, ("result", "nominal_seat_geometry", "new_own_nominal_seats", 15,
                                                    "capture_id"), "own0"), "distinct own16", 0),
            ("inherited96_duplicate", lambda d: set_value(d, ("result", "nominal_seat_geometry", "unaffected_capture_ids", 95),
                                                        "unchanged0"), "own16/unchanged96", 0),
            ("nominal_sets_overlap", lambda d: set_value(d, ("result", "nominal_seat_geometry", "new_own_nominal_seats", 0,
                                                        "capture_id"), "unchanged0"), "distinct own16", 0),
            ("old_actions_transfer", lambda d: set_value(d, ("result", "nominal_seat_geometry", "old_actions_or_strength_transferred"),
                                                       True), "own16/unchanged96", 0),
            ("false_complete_snapshot", lambda d: set_value(d, ("source_pins_after", "result_pins_missing_before_snapshot"), []),
                                        "coverage caveat", 0),
            ("after_snapshot_wrong_digest", lambda d: set_value(d, ("source_pins_after", "observed_after", "consumer.py"), "0"*64),
                                            "after snapshot omits", 0),
            ("snapshot_result_census", lambda d: set_value(d, ("source_pins_after", "result_source_pin_count"), 999),
                                       "source census", 0),
            ("admission_conflicting_pin", lambda d: set_value(d, ("admission", "source_sha256", "consumer.py"), "0"*64),
                                          "conflicting source pin", 0),
            ("process_failed", lambda d: set_value(d, ("process", "exit_code"), 1), "successful serialized process", 0),
            ("duplicate_cli_flag", lambda d: d["process"]["command"].extend(["--samples", "41"]), "command binding", 0),
        ]
        for name, mutation, message, index in mutations:
            probe(name, mutation, message, index)

        for name, transform in (("five_cases", lambda cases: cases[:-1]),
                                ("seven_cases", lambda cases: [*cases, cases[0]]),
                                ("repeated_case", lambda cases: [cases[0], *cases[:-1]])):
            with fixture(name) as (value, _):
                value.manifest["cases"] = transform(value.manifest["cases"])
                value.ref = value.save("manifest.json", value.manifest)
                checks[name] = rejected(lambda: a.build(value.manifest, value.ref), "six exact ordered")

        with fixture("actual_main") as (value, _):
            expected = a.build(value.manifest, value.ref)
            destination = a.OWN.parent/"runs-v1/main/result.json"
            stdout = io.StringIO()
            argv = ["--manifest", value.ref["path"], "--manifest-sha256", value.ref["sha256"], "--out", str(destination)]
            with contextlib.redirect_stdout(stdout):
                a.main(argv)
            raw = destination.read_bytes()
            require(raw == (json.dumps(expected, sort_keys=True, indent=2, allow_nan=False)+"\n").encode(), "main/build byte replay differs")
            require(json.loads(stdout.getvalue())["cases"] == 6, "main status case count")
            require(expected["cases"][0]["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is False,
                    "incomplete first snapshot caveat lost")
            require(expected["cases"][1]["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is True,
                    "complete later snapshot changed")
            require(expected["complete_joint_resistance"] is None and expected["release"] == a.RELEASE,
                    "null resistance/release boundary changed")
            require(expected["cases"][0]["coarse"]["gross_raw_members"]["fully_braced_component_normal_interaction"]
                    ["saved_witness_exceedances"], "exceedances suppressed")
            checks["inert_actual_main_byte_exact"] = {"sha256": hashlib.sha256(raw).hexdigest(), "cases": 6,
                "source_union_count": expected["verified_source_union"]["count"], "stdout": json.loads(stdout.getvalue())}
            checks["main_retry_preserves_existing"] = rejected(lambda: a.main(argv), "File exists")
            require(destination.read_bytes() == raw, "retry modified existing result")

        for name, raw in (("nan", b'{"x":NaN}'), ("positive_inf", b'{"x":Infinity}'),
                          ("negative_inf", b'{"x":-Infinity}'), ("overflow_float", b'{"x":1e999}'),
                          ("duplicate_key", b'{"x":1,"x":2}')):
            message = "duplicate JSON key" if name == "duplicate_key" else ("finite JSON" if name == "overflow_float" else "nonfinite JSON")
            checks[name] = rejected(lambda raw=raw: a.decode(raw), message)

        for name in ("outside", "dangling", "existing", "traversal", "runs_symlink"):
            with fixture("output_"+name) as (value, patch):
                runs = a.OWN.parent/"runs-v1"
                destination = runs/"owned/out.json"
                foreign = value.root/"foreign"
                foreign.mkdir()
                if name == "runs_symlink":
                    runs.symlink_to(foreign, target_is_directory=True)
                    destination = runs/"out.json"
                elif name == "outside":
                    destination = foreign/"out.json"
                else:
                    destination.parent.mkdir(parents=True)
                    if name == "existing":
                        destination.write_bytes(b"preserve\n")
                    elif name == "dangling":
                        destination.symlink_to(foreign/"absent.json")
                    else:
                        destination = destination.parent/".."/"out.json"
                def blocked(*_args, **_kwargs):
                    raise AssertionError("source evaluation before output rejection")
                patch.setattr(a, "checked", blocked)
                checks["output_"+name] = rejected(lambda value=value, destination=destination: a.write_to_file(value.ref, destination),
                    "File exists" if name in ("existing", "dangling") else "output parent traversal" if name == "traversal" else "own runs-v1")
                require(not (foreign/"out.json").exists() and not (foreign/"absent.json").exists(), "foreign output modified")
                if name == "existing":
                    require(destination.read_bytes() == b"preserve\n", "existing output modified")
                if name == "dangling":
                    require(destination.is_symlink(), "dangling output link modified")

        with fixture("failed_main") as (value, _):
            destination = a.OWN.parent/"runs-v1/failure/result.json"
            argv = ["--manifest", value.ref["path"], "--manifest-sha256", "0"*64, "--out", str(destination)]
            checks["failed_main_retained"] = rejected(lambda: a.main(argv), "exact source bytes differ")
            raw = destination.read_bytes()
            failed = json.loads(raw)
            require(failed["status"] == "FAILED" and failed["release"] == a.RELEASE, "failure receipt lost")
            rejected(lambda: a.main(argv), "File exists")
            require(destination.read_bytes() == raw, "retry rewrote FAILED receipt")

        with fixture("canonical_parent_replacement") as (value, patch):
            original = a.OWN.parent/"runs-v1/original"
            original.mkdir(parents=True)
            parked, foreign = original.with_name("parked"), value.root/"foreign"
            foreign.mkdir()
            original_open = Path.open
            def replace_parent(path, *args, **kwargs):
                if path == original/"out.json" and args and args[0] == "x+":
                    original.rename(parked)
                    original.symlink_to(foreign, target_is_directory=True)
                return original_open(path, *args, **kwargs)
            patch.setattr(Path, "open", replace_parent)
            error = rejected(lambda: a.write_to_file({**value.ref, "sha256": "0"*64}, original/"out.json"),
                             "exact source bytes differ")
            require((foreign/"out.json").is_file(), "output race did not reproduce")
            require(not (parked/"out.json").exists(), "original parent unexpectedly used")
            foreign_record = json.loads((foreign/"out.json").read_bytes())
            require(foreign_record["status"] == "FAILED", "foreign write not demonstrated")
            checks["canonical_parent_replacement_escape"] = {"reproduced": True, "source_error": error,
                "foreign_output_status": foreign_record["status"], "original_parent_has_output": False,
                "control_hook": "Replace resolved canonical parent with foreign-directory symlink immediately before x+ open; all paths synthetic and owned."}

        require(not FORBIDDEN.intersection(name.split(".")[0] for name in sys.modules), "forbidden dependency loaded")
        child_program = """import builtins, sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'cadquery', 'OCP', 'numpy', 'scipy'}:
        raise AssertionError('forbidden dependency import: '+name)
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
"""
        command = [sys.executable, "-B", "-c", child_program, "-q", str(PACKET/"test_summarize.py"),
                   "--basetemp", str(scratch/"pytest"), "--confcutdir", str(PACKET), "-p", "no:cacheprovider",
                   "-o", "addopts="]
        child = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
                               capture_output=True, text=True, check=False)
        require(child.returncode == 0 and "26 passed" in child.stdout, "original inert tests failed: "+child.stdout+child.stderr)
        checks["original_inert_suite_own_execution"] = {"exit_code": child.returncode, "stdout": child.stdout.strip(),
            "stderr": child.stderr.strip(), "plugin_autoload": False, "cache_provider": False,
            "forbidden_import_guard": sorted(FORBIDDEN)}

    lint_command = [str(ROOT/".venv/bin/ruff"), "check", "--no-cache", "--select", "E4,E7,E9,F,I,B,RUF", str(OWN)]
    lint = subprocess.run(lint_command, cwd=ROOT, capture_output=True, text=True, check=False)
    require(lint.returncode == 0, "own Ruff failed: "+lint.stdout+lint.stderr)
    after = snapshot(paths)
    require(before == after, "frozen reviewed source bytes changed")
    findings = [{"severity": "medium", "file": str((PACKET/"summarize.py").relative_to(ROOT)), "lines": [272, 281],
        "title": "Canonical output parent can be replaced before exclusive reservation",
        "impact": "A concurrent replacement of the resolved parent directory by a symlink between bind_output and x+ open redirects STARTED/FAILED and potentially final summary writes outside owned runs-v1. The parent inode is first captured after the redirected open, so the later guard accepts the replacement. Exclusive x+ still protects an existing leaf; this is an ownership escape for a fresh leaf, not an overwrite or numerical-acceptance bypass.",
        "evidence": "canonical_parent_replacement_escape; existing test_parent_alias_retarget_cannot_redirect_reserved_output only changes the already-resolved alias, not the bound directory itself.",
        "fix": "Reserve relative to an authenticated opened parent-directory descriptor, using a no-follow exclusive leaf open and checks that the descriptor's directory remains inside the owned runs tree. Authenticate/create parent directories without following replacements, rather than first capturing parent identity after the output open."}]
    receipt = {"schema": "independent_z180_saved_summary_testing_review/v1", "status": "FINDING_INERT_SOURCE_ONLY",
        "helper": {"path": str(OWN.relative_to(ROOT)), "sha256": digest(OWN)},
        "targets_before": {str((PACKET/name).relative_to(ROOT)): before[str((PACKET/name).relative_to(ROOT))] for name in EXPECTED},
        "sources_before": before, "sources_after": after, "sources_preserved": True,
        "method_sources_authenticated_count": len(method_pins), "checks": checks, "findings": findings,
        "own_ruff": {"command": lint_command, "exit_code": lint.returncode, "stdout": lint.stdout.strip()},
        "scope": {"own_execution": "Original26 inert tests; actual summarize.main/build over reused synthetic JSON/source fixture; coherently rehashed negative cases; static and canonical-parent race output controls.",
            "reused": "Frozen test_summarize.fixture and byte-authenticated original0547 selectors/8ab closure pure definitions. Method source hash authentication is not execution of gate or consumer.",
            "actual_manifest_or_result_issued_or_consumed": False, "candidate_fields_config_roster_descriptor_read": False,
            "gate_consumer_reducer_production_CAD_native_global_called": False, "forbidden_imports_loaded": [],
            "unadopted_Z180_current_Z200_and_HOLD_unchanged": True, "complete_joint_resistance": None,
            "release": {key: False for key in proof["release"]}, "temporary_fixture_outputs_removed": True}}
    with (OUT/"receipt.json").open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt_sha256": digest(OUT/"receipt.json"), "helper_sha256": digest(OWN),
                      "findings": len(findings), "checks": len(checks)}))


if __name__ == "__main__":
    run()
