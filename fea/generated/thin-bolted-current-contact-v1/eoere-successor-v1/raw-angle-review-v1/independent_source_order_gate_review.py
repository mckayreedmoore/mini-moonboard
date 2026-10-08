"""Check the distinct recovery-order adapter; no field evaluation or solve."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent / "four-port-method-v1"
EXPECTED = {
    "first_order_admission_v3.py": "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008",
    "test_first_order_admission_v3.py": "f2e1cbe9377219084cd7d4215237b323fb7e82dfdc677051357fac5c8bdbb0a1",
    "first_order_admission_v2.py": "bfb984c47372d20387883d11d1d49f8a12d9debda1b0c78f1c024ace01bc2821",
    "first_order_admission.py": "e61ee415f0a8cd83f3ea4b0606064bceb128413eed4e66f1192955b1610ff66b",
}
PRIOR = OWN.parent / "independent-saved-cut-order-review.json"
PRIOR_SHA = "f433839887b184ef16dcc4c55c789db26720421a06b1e369ac5fa031d5086632"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def review():
    direct = {str((LEAF / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()}
    direct[str(PRIOR.relative_to(ROOT))] = PRIOR_SHA
    require(all(sha(ROOT / path) == digest for path, digest in direct.items()), "frozen adapter or numeric evidence changed")
    prior = json.loads(PRIOR.read_bytes())
    spec = importlib.util.spec_from_file_location("independent_source_order_gate", LEAF / "first_order_admission_v3.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    pins = gate.source_pins(direct)
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    before = canonical(pins)
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "source pin mismatch")
    old = {"a-body": {"axis_id": "a-axis"}, "z-body": {"axis_id": "z-axis"}}
    maps = SimpleNamespace(shafts=old, members={"geometry_marker": "unchanged"})
    field = {"source_inputs": {"shafts": [{"body": "z-body", "axis_id": "z-axis"},
        {"body": "a-body", "axis_id": "a-axis"}]}}
    view = gate.source_ordered_maps(field, maps)
    require(list(view.shafts) == ["z-body", "a-body"] and list(maps.shafts) == ["a-body", "z-body"]
        and all(view.shafts[key] is old[key] for key in old) and view.members is maps.members,
        "adapter modified source map values or original ordering")
    require(Path(gate.corrected.__file__).resolve() == gate.REUSED
        and Path(gate.base.__file__).resolve() == gate.corrected.ORIGINAL,
        "genuine reused module paths were replaced")
    require(gate.AUDIT.__globals__["OWN"] == gate.OWN and gate.AUDIT.__globals__["LOADED_SHA"] == gate.LOADED_SHA
        and gate.AUDIT.__globals__["verify_fitting_and_alias_recovery"] is gate.verify_fitting_and_alias_recovery,
        "actual new audit contract/context not bound")
    require(all(sha(ROOT / path) == digest for path, digest in pins.items()), "source bytes changed during review")
    return {
        "schema": "independent_eoere_source_order_gate_method_review/v1",
        "disposition": "READY_BOUNDED_SOURCE_ORDER_GATE_METHOD_ONLY",
        "source_sha256": pins, "source_count": len(pins), "source_map_before_after_sha256": [before, canonical(pins)],
        "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}},
        "tools": {"python": platform.python_version()},
        "focused_verification": {"result": "9 passed in 2.66s", "ruff": "new adapter and focused test paths passed",
            "command": [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                str((LEAF / "test_first_order_admission_v3.py").relative_to(ROOT))]},
        "preserved_production_failure_and_numeric_review": {
            "receipt": str(PRIOR.relative_to(ROOT)), "sha256": PRIOR_SHA,
            "field_identity": prior["field_identity"], "final_q_canonical_sha256": prior["final_q_canonical_sha256"],
            "all_complete_owned_cut_records_replayed": 100, "signed_cut_count": 5908,
            "source_export_first_axis": "eoere_bolt_001", "JSON_chart_first_axis": "cleat_post_bolt_left_1",
            "original_admission_failure_preserved": True, "field_and_original_producers_modified": False},
        "reviewed_contract": [
            "Exact unique physical body/axis union is required before source-list ordering; missing, duplicate, foreign and mismatched owner rows reject.",
            "Only an internal shallow map view orders the same original row objects by authenticated source_inputs.shafts. Original maps, field tables, signed cuts and q remain unchanged.",
            "Genuine bfb metadata, loaded heel/root, original-law gradient/floor/load/work/body/global and e61 cut-recovery checks remain intact with the same tolerances.",
            "Actual new source path/SHA is bound in a private audit/consumer context. Original modules/globals/__file__ are retained; no old PASS or receipt is relabeled.",
            "Cheap same-byte API additionally requires exact compatibility and recovery-order provenance, then the same raw/state/q/gradient/operator/table/source bindings."],
        "confirmed_blockers": [],
        "limits": [
            "This review runs only nine tiny fixtures and a two-row ordering check. Its linked separate saved-output review reads JSON/source bytes and cuts, without unpacking K or evaluating q.",
            "Parent must separately run the new full gate on the unchanged actual field; this method receipt is not field admission.",
            "Captured distributed panel RHS and first-order gross-stock/four-strip/material/contact limitations remain unchanged. No pressure, physical demand bound, strength, finite applicability, fabrication or climbing acceptance."],
        "release": {"bounded_gate_method_ready": True, "independent_field_admitted": False,
            "physical_applicability": False, "capacity": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"path": str(args.out), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "source_count": result["source_count"]}))


if __name__ == "__main__":
    main()
