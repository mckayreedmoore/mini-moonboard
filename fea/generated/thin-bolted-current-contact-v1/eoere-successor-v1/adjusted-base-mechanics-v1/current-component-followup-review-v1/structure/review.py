"""Independent architecture/source/retention review of the richer followups.

This script performs an inert source-closure audit with numerical/CAD imports
blocked. It never calls consume, _reduce, _methods or any real field reducer.
The separately observed test/lint outputs are retained as review observations.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
TARGET = MECH / "current-component-bridge-v1/followups-v1"
EXPECTED = {
    TARGET / "followups.py": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798",
    TARGET / "test_followups.py": "eec79c2a9f33305f9cccfbec14520806f69a4a46a34efb995e4dc7ab31df912f",
    TARGET / "verification.json": "1390a83569c7885e0006645e1a8fb11814c1751900ebad6f0118daeea454173f",
    MECH / "current-component-bridge-v1/consumer-v1/consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    MECH / "current-component-bridge-v1/component_plan.py": "caf5d1307d999843c3ea16f3536f5bdd25edb390ebbab6e624cf5f5a86dc727e",
    MECH / "current-force-bridge-v1/review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def calls(function, name):
    return sorted(n.lineno for n in ast.walk(function) if isinstance(n, ast.Call)
                  and ast.unparse(n.func) == name)


def inert_closure():
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        require(name.split(".")[0] not in {"numpy", "scipy", "cadquery", "OCP", "mini_moonboard"},
                "inert source audit cannot import " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", guarded_import):
        spec = importlib.util.spec_from_file_location("independent_followup_structure_source_audit", TARGET / "followups.py")
        subject = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(subject)
        consumer = subject._consumer()
        plan = consumer._load_plan()
        contract = plan.component_plan()
        pins = dict(contract["source_sha256"])
        plan_count, plan_canonical = len(pins), subject.canonical(pins)
        _, _, _, material = subject._materials(consumer, plan, pins)
        plan.merge(pins, dict(subject.SOURCES.values()))
        consumer.verify(pins)
        return {
            "numerical_CAD_imports_blocked": True,
            "genuine_field_or_reducer_consumed": False,
            "frozen_plan_source_count": plan_count,
            "frozen_plan_sources_canonical_sha256": plan_canonical,
            "full_source_count": len(pins),
            "full_sources_canonical_sha256": subject.canonical(pins),
            "static_root_evidence_maps": len(material["root_evidence_maps"]),
            "nominal_wood_seats": contract["nominal_seat_geometry"]["nominal_wood_seats"],
        }


def check():
    for path, expected in EXPECTED.items():
        require(sha(path) == expected, "frozen review input differs: " + relative(path))
    old = list((MECH / "current-component-bridge-v1").glob("*.py"))
    old += list((MECH / "current-component-bridge-v1").glob("verification.json"))
    old += list((MECH / "current-component-bridge-v1/consumer-v1").glob("*.py"))
    old += list((MECH / "current-component-bridge-v1/consumer-v1").glob("verification.json"))
    for folder in ("correctness", "testing", "structure"):
        old += [MECH / "current-component-bridge-review-v1" / folder / name
                for name in ("review.py", "receipt.json")]
    require(len(old) == 12, "prior source/test/review census differs")
    old_before = {relative(path): sha(path) for path in old}
    tree = ast.parse((TARGET / "followups.py").read_bytes())
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    intake = functions["consume"]
    require(calls(intake, "c.authenticate")[0] < calls(intake, "c._current_contract")[0]
            < calls(intake, "_reduce")[0] < calls(intake, "canonical")[-1],
            "admission, metadata, reducer and immutability order differs")
    output = functions["consume_to_file"]
    reservation = next(n for n in output.body if isinstance(n, ast.With))
    require(ast.unparse(reservation.items[0].context_expr) == "Path(out).open('x')"
            and calls(reservation, "write_record")[0] < calls(reservation, "consume")[0],
            "exclusive reservation/STARTED record must precede intake")
    report = json.loads((TARGET / "verification.json").read_bytes())
    closure = inert_closure()
    require(closure["full_source_count"] == 1126
            and closure["full_sources_canonical_sha256"]
            == "fdfa5382833e53d6327c4a006524025bd41defb8b28b6f53256d71342dd08a96",
            "inert current-plus-followup closure differs")
    require(closure["frozen_plan_source_count"] == 1099
            and closure["frozen_plan_sources_canonical_sha256"]
            == "c526260b67d9603b20fe0e6416d9cc9dcdd0a99144767a9c6c118aab974fd2a5",
            "frozen current source plan differs")
    require(report["execution"]["genuine_force_field_consumed"] is False
            and report["execution"]["genuine_reducer_callback"] is False
            and not any(report["release"].values()), "method evidence boundary differs")
    require(all(sha(ROOT / path) == expected for path, expected in old_before.items()),
            "prior files changed during inert review")
    require(all(sha(path) == expected for path, expected in EXPECTED.items()),
            "reviewed inputs changed during source review")
    return {
        "schema": "eoere_current_component_followup_independent_structure_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_FINDINGS_WITHIN_SOURCE_INERT_AND_SYNTHETIC_SCOPE",
        "substantial_confirmed_findings": [],
        "source_sha256": {**{relative(p): h for p, h in EXPECTED.items()}, relative(OWN): sha(OWN)},
        "target_source_test_receipt_bytes": sum(p.stat().st_size for p in EXPECTED if p.parent == TARGET),
        "inert_independent_source_closure": closure,
        "prior_12_source_test_receipt_files_unchanged_during_inert_audit": old_before,
        "observed_independent_checks_before_receipt_creation": [
            {"command": [".venv/bin/python", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", relative(TARGET / "test_followups.py")],
             "exit_code": 0, "result": "30 passed in 5.38s", "scope": "inert/source and tiny synthetic controls only"},
            {"command": ["uv", "run", "ruff", "check", relative(TARGET)],
             "exit_code": 0, "result": "All checks passed!"},
        ],
        "architecture_evidence": [
            {"path": relative(TARGET / "followups.py"), "lines": [259, 261, 263, 267, 268],
             "observation": "Frozen consumer authenticates exact current raw field/admission/gate before current descriptor joins and lazy rich reducers; canonical before/after check rejects reducer payload mutation."},
            {"path": relative(TARGET / "followups.py"), "lines": [155, 165, 168, 171, 184, 197],
             "observation": "Exact-byte checked private AST compilation and constants reuse replace full historical CLI intake. Returned functions have explicit private namespaces; scoped AST patch restores on exceptions."},
            {"path": relative(TARGET / "followups.py"), "lines": [123, 140, 144, 151],
             "observation": "Static material/root evidence is pinned; historical force/viewer dependency maps are source evidence and are not merged as current runtime aliases."},
            {"path": relative(TARGET / "followups.py"), "lines": [93, 99, 101, 104, 114, 239, 246],
             "observation": "Washer input composes 100 current axes, exact v3 parent27 cuts and all22 own dimensional scenarios. Full200 diagnostics remain distinct from carried nominal112-seat support proof."},
            {"path": relative(TARGET / "followups.py"), "lines": [224, 228, 231, 233, 237, 248, 252],
             "observation": "Only current raw field and static material facts enter scoped timber intake; no assessment joins. Full100 shaft rows and eight mixed-stack nulls survive; group, finished-section, restraint, washer and complete-joint gaps remain explicit."},
            {"path": relative(TARGET / "followups.py"), "lines": [282, 290, 296, 297, 303],
             "observation": "Exclusive output creation precedes source intake; flushed/fsynced STARTED and retained FAILED records preserve failed/abrupt attempts. Existing files and dangling links are preserved."},
        ],
        "architecture_assessment": "Bounded extension is cohesive: admission stays in the frozen consumer, current source assembly stays in adapters, and equations stay in existing reducers. Explicit source pins and private namespaces make the coupling reviewable without copying equations or historical assets. Synthetic tests establish these method boundaries; genuine current reducer behavior remains unobserved.",
        "retention": {
            "active": "Followup three files, current consumer/plan/gate, current saved descriptors, geometry/manifest refs, frozen reducer sources and static material/source-map evidence remain active inputs.",
            "historical": "Original reducer and review bytes, old force/geometry evidence and old /tmp diagnostic metadata remain preserved with their old meaning. No historical action or pass is adopted by this followup.",
            "compact_reuse": "59,230-byte adapter/test/receipt packet reuses frozen reducers, compiler and shared assets. This review creates no fields, BREP/mesh copies, K banks or bulky raw runs.",
            "archive_or_delete": "None performed or authorized. Future rich output retention belongs in the existing task summary; any closed-run pruning needs current-consumer/ownership/process checks and the verified external archive workflow.",
        },
        "next_actions": [
            "Parent may schedule one genuine admitted current-field followup after independent reviews are accepted; this review supplies no production execution or acceptance.",
            "Retain per-state raw field/admission/source binding, full own tables, exceedances and unknown mechanisms when producing six-case reporting.",
        ],
        "execution_limits": {
            "genuine_field_consumption": False, "genuine_followup_reducer_callback": False,
            "CAD_query_or_rebuild": False, "operator_K_or_preparation": False,
            "frame_native_or_browser": False, "target_or_old_file_edits": False,
            "shared_docs_staging_commits_or_cleanup": False,
        },
        "complete_joint_resistance": None,
        "release": report["release"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "sha256": sha(args.out), "substantial_confirmed_findings": 0}))


if __name__ == "__main__":
    main()
