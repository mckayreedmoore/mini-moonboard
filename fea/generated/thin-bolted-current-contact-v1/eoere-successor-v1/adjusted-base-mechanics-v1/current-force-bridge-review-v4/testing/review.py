"""Independent source-only v4 binding and partial-input testing review."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").exists())
MECH = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
TARGET = MECH / "current-force-bridge-v1/preflight-fix-v4"
EXPECTED = {TARGET / name: digest for name, digest in {
    "preflight.py": "244f441114f3215d82e45d55403da5cfb2417d9b996779bcb5291188c2cd7ad2",
    "test_preflight.py": "ffb459d39cc7855ca4fb3f597bc025ab2f7553486666008e374c691cdf1ecbae",
    "all-bindings.json": "3f80b1185b88812d18219b1cea2ed2c1dee3cb8b323f2dafc72558f3e554f8d4",
    "verification.json": "afc71138a185b23eba2fa2d4d8947691446226814ea0c5f6223d1f08b735ab59",
}.items()}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reject(callback, expected):
    try:
        callback()
    except ValueError as error:
        assert expected in str(error), str(error)
        return
    raise AssertionError("invalid binding fixture passed")


def run():
    assert {path: sha(path) for path in EXPECTED} == EXPECTED
    spec = importlib.util.spec_from_file_location("independent_preflight_v4_testing", TARGET / "preflight.py")
    s = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s)
    previous = s.previous()
    w = previous.corrected()
    b = w.frozen()
    saved = json.loads((TARGET / "all-bindings.json").read_bytes())
    sources = {**EXPECTED, **s.FROZEN, **previous.FROZEN,
        **{ROOT / name: digest for name, digest in s.frozen_pins().items()},
        **{ROOT / name: digest for name, digest in previous.frozen_pins(w).items()},
        **{ROOT / name: digest for name, digest in w.source_pins().items()},
        **{ROOT / ref["path"]: ref["sha256"] for ref in saved["provided"].values()}}
    assert {path: sha(path) for path in sources} == sources
    probe_root = OWN.parent / "_probes"
    probe_root.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="attempt-", dir=probe_root))
    results = subprocess.run(["uv", "run", "pytest", "-q", str(TARGET / "test_preflight.py")],
                             cwd=ROOT, check=True, capture_output=True, text=True)
    checks = [{"name": "issued_v4_tests", "result": results.stdout.strip()}]
    refs = {key: {"path": str(work / key), "sha256": "a" * 64} for key in s.REFERENCE_KEYS}
    geometry = {"report": {"path": "synthetic-geometry", "sha256": "b" * 64},
                "source_manifest": refs["source_manifest"], "cached_source_export": refs["source_export"]}
    method = {"input": refs["inputs"], "input_review": refs["input_review"], "source_manifest": refs["source_manifest"],
              "panel_bank": refs["panel_bank"], "geometry": geometry["report"],
              "input_record": {"path": "synthetic-method", "sha256": "c" * 64}}
    tiny = SimpleNamespace(bundle=SimpleNamespace(artifact_path=str), require=w.require,
                           read_method=lambda *_: method, read_ref=lambda _ref: {"geometry": geometry})
    args = SimpleNamespace(method_input=work / "method", method_input_sha256="c" * 64,
                           **{key: Path(ref["path"]) for key, ref in refs.items()},
                           **{key + "_sha256": ref["sha256"] for key, ref in refs.items()})
    assert s.method_reference_bindings(args, tiny)["complete"] is True
    for key in s.REFERENCE_KEYS:
        for field, value in ((key, work / (key + "-different-path")), (key + "_sha256", "d" * 64)):
            altered = copy.deepcopy(args)
            setattr(altered, field, value)
            reject(lambda altered=altered: s.method_reference_bindings(altered, tiny), "supplied " + key + " reference differs")
    checks.append({"name": "each_of_five_refs_requires_path_and_hash", "negative_controls": 10})
    for key in ("report", "source_manifest"):
        altered_geometry = copy.deepcopy(geometry)
        altered_geometry[key] = {"path": "foreign", "sha256": "0" * 64}
        altered_tiny = SimpleNamespace(**{**vars(tiny), "read_ref": lambda _ref, value=altered_geometry: {"geometry": value}})
        reject(lambda altered_tiny=altered_tiny: s.method_reference_bindings(args, altered_tiny),
               "method-bound input geometry/manifest references differ")
    checks.append({"name": "method_bound_input_geometry_and_manifest", "negative_controls": 2})
    combinations = 0
    keys = (*s.REFERENCE_KEYS, "method_input")
    for states in itertools.product(range(4), repeat=len(keys)):
        # 0 absent, 1 path only, 2 hash only, 3 complete.
        partial = copy.deepcopy(args)
        for key, state in zip(keys, states, strict=True):
            if state in (0, 2):
                setattr(partial, key, None)
            if state in (0, 1):
                setattr(partial, key + "_sha256", None)
        result = s.method_reference_bindings(partial, tiny)
        method_complete = states[-1] == 3
        checked = {key: refs[key] for key, state in zip(s.REFERENCE_KEYS, states[:-1], strict=True) if state == 3}
        assert result["method_provided"] is method_complete
        assert result["checked"] == (checked if method_complete else {})
        assert result["complete"] is (method_complete and len(checked) == len(s.REFERENCE_KEYS))
        assert set(result["unchecked"]) == set(s.REFERENCE_KEYS) - (set(checked) if method_complete else set())
        combinations += 1
    checks.append({"name": "all_partial_path_hash_combinations_truthful", "synthetic_combinations": combinations})
    # Verify guard ordering through the actual public preflight orchestration.
    for key in s.REFERENCE_KEYS:
        altered = copy.deepcopy(args)
        altered.mode, altered.run = "preflight", False
        setattr(altered, key, work / (key + "-foreign"))
        with patch.object(s, "method_reference_bindings", wraps=lambda value, _b: s_method(value, tiny)), \
                patch.object(previous, "preflight", side_effect=AssertionError("mismatch reached frozen preflight")):
            reject(lambda altered=altered: s.preflight(altered, previous, w, b), "supplied " + key + " reference differs")
    checks.append({"name": "five_binding_mismatches_precede_frozen_preflight", "negative_controls": 5})
    race_code = '''
import contextlib,importlib.util,json,sys,time
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location("inert_v4_race",sys.argv[1]);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
previous=s.previous();w=previous.corrected()
b=SimpleNamespace(parse_args=lambda argv:None,core=SimpleNamespace(serial=lambda x:x))
w.frozen=lambda:b
@contextlib.contextmanager
def context(_b):yield _b
w.corrected_context=context
def preflight(*_args):
 with Path(sys.argv[3]).open("a") as f:f.write("callback\\n")
 time.sleep(.2)
 return {"missing":[],"method_reference_bindings":{"complete":True},"production_readiness_claimed":False}
s.preflight=preflight
try:sys.exit(s.main(["--out",sys.argv[2]]))
except FileExistsError:sys.exit(3)
'''
    race_out, marker = work / "race.json", work / "race-callbacks.txt"
    command = [sys.executable, "-c", race_code, str(TARGET / "preflight.py"), str(race_out), str(marker)]
    workers = [subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    codes = []
    for worker in workers:
        stdout, stderr = worker.communicate(timeout=15)
        assert not stderr, (stdout, stderr)
        codes.append(worker.returncode)
    assert sorted(codes) == [0, 3] and marker.read_text().splitlines() == ["callback"]
    assert json.loads(race_out.read_bytes())["production_readiness_claimed"] is False
    checks.append({"name": "actual_v4_main_exclusive_output_race_with_inert_inner_callback", "exit_codes": sorted(codes), "callback_count": 1})
    assert {path: sha(path) for path in sources} == sources
    assert b.OWN == w.FROZEN and b.factory.SCHEMA == b.ORIGINAL_SCHEMA
    receipt = {"schema": "eoere_preflight_v4_testing_review/v1", "status": "CLEAN_NO_SUBSTANTIAL_FINDINGS",
        "substantial_findings": [], "checks": checks, "source_hashes_before_after_unchanged": True,
        "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in sources.items()},
        "review_path": str(OWN.relative_to(ROOT)), "review_sha256": sha(OWN), "probe_directory": str(work.relative_to(ROOT)),
        "candidate_preparation_K_solve_CAD_native_browser_field_consumption_or_slot_edit_performed": False,
        "release": copy.deepcopy(b.core.RELEASE),
        "retention": {"active": "review helper, receipt and ignored owned metadata/race fixtures",
                      "archive_prune_staging_or_commit_performed": False}}
    receipt_path = OWN.with_name("receipt.json")
    assert not receipt_path.exists(), "preserve issued review receipt"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(receipt_path), "sha256": sha(receipt_path), "checks": len(checks)}))


# Capture the genuine helper before any ordering probe replaces its attribute.
s_method = None
if __name__ == "__main__":
    # run() loads the module; expose the original through a tiny lazy adapter.
    def s_method(args, b):
        spec = importlib.util.spec_from_file_location("isolated_v4_binding_helper", TARGET / "preflight.py")
        isolated = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(isolated)
        return isolated.method_reference_bindings(args, b)
    run()
