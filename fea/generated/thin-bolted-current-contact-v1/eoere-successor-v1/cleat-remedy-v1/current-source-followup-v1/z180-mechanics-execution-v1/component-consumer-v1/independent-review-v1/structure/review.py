"""Independent frozen architecture/provenance review; source inspection only.

The separately observed 39-test run used only inert stand-ins and source bytes.
This helper imports no target, gate, config, field, admission or reducer module.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[10]
TARGET = OWN.parents[2]
EXECUTION = TARGET.parent
BASE = EXECUTION.parents[2]
MECH = BASE / "adjusted-base-mechanics-v1"
PINS = {
    TARGET / "consume.py": "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80",
    TARGET / "test_consume.py": "1024873b79c965172ddd7d4324063863c4d41561570f30c24d9cd895b6bd7d44",
    TARGET / "verification.json": "fe7cdb509058d116049fef87bf91266378d4dc252b68c9e80b64d9a439ce2286",
    MECH / "current-component-bridge-v1/consumer-v1/consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    MECH / "current-component-bridge-v1/followups-v1/followups.py": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798",
    MECH / "current-component-bridge-v1/component_plan.py": "caf5d1307d999843c3ea16f3536f5bdd25edb390ebbab6e624cf5f5a86dc727e",
    MECH / "current-force-bridge-v1/review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
    EXECUTION / "review-fix-v2/bridge.py": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55",
    EXECUTION / "bridge.py": "fc95da9c8b81b8153813b6c98895401c4f4b5cf96e61d68973ba417c386917c6",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def calls(tree, name):
    return sorted(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and ast.unparse(n.func) == name)


def check():
    for path, expected in PINS.items():
        require(sha(path) == expected, "reviewed source differs: " + relative(path))
    source = ast.parse((TARGET / "consume.py").read_bytes())
    functions = {n.name: n for n in source.body if isinstance(n, ast.FunctionDef)}
    auth = functions["authenticate"]
    loads = [n for n in ast.walk(auth) if isinstance(n, ast.Call) and ast.unparse(n.func) == "load"]
    require(len(loads) == 1 and ast.unparse(loads[0].args[0]) == "refs['gate']",
            "raw authentication can load only the config-bound own gate")
    run = functions["consume"]
    require(calls(run, "authenticate")[0] < calls(run, "reduce_admitted")[0]
            < calls(run, "verify")[0], "admission/reduction/final-pin order differs")
    reducers = functions["reduce_admitted"]
    require(calls(reducers, "source_contract")[0] < calls(reducers, "c._reduce")[0],
            "current source contract must precede coarse arithmetic")
    compiler = [n for n in ast.walk(reducers) if isinstance(n, ast.Call)
                and ast.unparse(n.func) == "load" and ast.unparse(n.args[0]) == "FROZEN['compiler']"]
    require(len(compiler) == 1, "frozen genuine compiler provider must stay separate from own admission gate")
    output = functions["consume_to_file"]
    reservation = next(n for n in output.body if isinstance(n, ast.With))
    require(ast.unparse(reservation.items[0].context_expr) == "Path(out).open('x+')"
            and calls(reservation, "write")[0] < calls(reservation, "consume")[0],
            "exclusive output and durable STARTED record must precede config intake")
    frozen = json.loads((TARGET / "verification.json").read_bytes())
    require(frozen["readiness"]["genuine_config_supplied"] is False
            and frozen["readiness"]["actual_component_reducer_executed"] is False
            and frozen["readiness"]["ready_for_genuine_consumption"] is False
            and not any(frozen["release"].values()), "inert verification/release scope differs")
    for path, expected in PINS.items():
        require(sha(path) == expected, "reviewed source changed during source audit: " + relative(path))
    return {
        "schema": "eoere_z180_component_independent_structure_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_FINDINGS_IN_SOURCE_AND_INERT_SCOPE",
        "substantial_confirmed_findings": [],
        "source_sha256": {**{relative(p): h for p, h in PINS.items()}, relative(OWN): sha(OWN)},
        "source_immutability_verified_before_after": True,
        "target_source_test_verification_bytes": sum(p.stat().st_size for p in PINS if p.parent == TARGET),
        "observed_independent_checks_before_receipt_creation": [
            {"command": [".venv/bin/python", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", relative(TARGET / "test_consume.py")],
             "exit_code": 0, "result": "39 passed in 0.50s", "scope": "inert stand-ins, source/AST checks and tiny bytes only"},
            {"command": [".venv/bin/ruff", "check", relative(TARGET)],
             "exit_code": 0, "result": "All checks passed!"},
        ],
        "architecture_and_provenance_evidence": [
            {"path": relative(TARGET / "consume.py"), "lines": [103, 119, 137, 144, 150, 158, 289, 325],
             "observation": "Config, raw pair, exact own sources and Z180 gate are authenticated before C/F reducer import. Corrected source join and current descriptor rows precede arithmetic; field/state/case/placement remain tied to the admitted payload."},
            {"path": relative(TARGET / "consume.py"), "lines": [27, 302, 304, 313, 315],
             "observation": "Frozen491653 compiler definitions provide checked_ast; the config-bound own Z180 gate supplies admission identity. Hooks are lexical context managers around fresh C/F module objects and restore on success/failure. The consumer serializes its calls with LOCK."},
            {"path": relative(TARGET / "consume.py"), "lines": [170, 173, 176, 242, 256],
             "observation": "All100 axes come from full authenticated descriptors; four proposed axes join the partial layout and96 axes join the exact parent. Washer composition explicitly binds these sources,27 v3 service cuts and22 own dimensional scenarios."},
            {"path": relative(TARGET / "consume.py"), "lines": [184, 201, 203, 207, 219, 225, 235, 266],
             "observation": "Nominal112 seats are16 own source/datum/hardware-bound annuli plus96 unchanged source/shaft/end proofs. Old nominal evidence is authenticated in its original scope; no old actions, strength, pressure or complete-joint acceptance transfer."},
            {"path": relative(TARGET / "consume.py"), "lines": [208, 252, 307, 317, 320, 338],
             "observation": "Missing16-seat evidence leaves nominal support null. Unsupported full washer composition skips full washer arithmetic and adds an explicit missing-input disposition. Finished sections and complete resistance stay unknown; original exceedance tables and equations remain in the frozen C/F reducers."},
            {"path": relative(TARGET / "consume.py"), "lines": [345, 349, 355, 356, 362],
             "observation": "Exclusive inode creation rejects existing paths, dangling links and competitors before intake. Durable STARTED and retained FAILED records preserve failed attempts; success carries source pins, mode, own field/admission and allfalse release."},
        ],
        "assessment": "The distinct Z180 adapter changes source identity and narrowly scoped hooks while reusing frozen arithmetic. Full descriptors, partial proposal layout, retained v3 cuts and seat observations keep distinct provenance. Inert controls exercise fail-closed ordering and restoration; they do not establish genuine reducer execution or production readiness.",
        "readiness_and_claim_boundary": {
            "genuine_config_supplied_or_consumed_by_review": False,
            "genuine_field_admission_or_reducer_run": False,
            "final_gate_definition_reviewed_only": {
                "path": relative(EXECUTION / "review-fix-v2/bridge.py"),
                "sha256": PINS[EXECUTION / "review-fix-v2/bridge.py"],
            },
            "missing": "Parent must freeze the exact final gate/config, descriptor and matching review, then one own admitted field/admission/state/case before genuine consumption.",
            "complete_joint_resistance": None,
            "panel_or_screw_remedy_authorized_or_performed": False,
        },
        "retention": {
            "keep_active": "This consumer/test/verification, frozen C/F arithmetic and compiler, own gate/source adapter, parent source and nominal-seat evidence remain active. Future output requires its exact config/raw pair and complete source closure.",
            "historical_boundary": "Retained96 nominal proofs keep their original scope;16 replacement-host seats need own observations. Old responses, passes and viewer aliases remain historical.",
            "output_ownership": "No real output pair or candidate computation was created; synthetic tests use temporary fixtures. Failed reserved outputs must remain reviewable and cannot be overwritten by retry.",
            "compact_reuse": "The distinct small source/test/verification packet reuses original equations and assets. This review adds only its helper/receipt; no copied dependencies, manuals, BREP, meshes, K banks or bulky raw runs.",
            "archive_or_delete": "None performed or authorized; preserve frozen sources and failed attempts. Later pruning requires existing consumer/ownership/process checks and verified external archive recovery.",
        },
        "execution": {
            "source_and_inert_only": True, "actual_config_field_admission_or_reducer_run": False,
            "CAD_BREP_K_q_solver_or_browser": False, "target_old_or_peer_edits": False,
            "docs_Git_staging_commits_or_cleanup": False,
        },
        "release": frozen["release"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "helper_sha256": sha(OWN), "receipt_sha256": sha(args.out),
                      "substantial_confirmed_findings": 0}))


if __name__ == "__main__":
    main()
