"""Authenticate a stress-frame execution before calling its pure DAT reader.

This module has no launch path. The caller supplies the separately reviewed
freeze digest; the result is limited to the hypothetical software fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREPARATION = HERE.parent / "orthotropic-stress-frame-preparation-2026-10-01"
ORACLE = (
    HERE.parent
    / "mvp-integration-2026-10-01/orthotropic-stress-frame-parent-oracle.json"
)
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
LEDGER = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json"
SCOPE = "hypothetical homogeneous-strain stress-output frame check only"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PROFILE_SHA256 = "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c"
LEGACY_SHA256 = "ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61"
TIMEOUT_CONTROL = {
    "path": "/usr/bin/timeout",
    "sha256": "4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def relative_source(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), f"record is not an object: {path}")
    return value


def bound_review(authorization: dict) -> tuple[dict, str]:
    name = authorization.get("independent_review")
    require(isinstance(name, str) and bool(name), "independent review path absent")
    relative = Path(name)
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "independent review path is not repository-relative",
    )
    path = (ROOT / relative).resolve()
    require(
        path.is_relative_to(ROOT.resolve()), "independent review escapes repository"
    )
    actual = digest(path)
    require(
        actual == authorization.get("independent_review_sha256"),
        "independent review hash changed",
    )
    return load_json(path), actual


def check_command(command: object, directory: Path, run_id: str, profile: dict) -> None:
    require(
        isinstance(command, list) and all(isinstance(x, str) for x in command),
        "execution command is not an argument list",
    )
    require(len(command) == 28, "execution command has unexpected arguments")
    require(re.fullmatch(r"\d+:\d+", command[11]) is not None, "invalid container user")
    expected = [
        "docker",
        "--context",
        "default",
        "run",
        "--rm",
        "--name",
        "moonboard-" + run_id.lower(),
        "--network=none",
        "--cpus=1",
        "--memory=1g",
        "--user",
        command[11],
        "-e",
        "OMP_NUM_THREADS=1",
        "--memory-swap=1g",
        "-v",
        f"{directory}:/output",
        "-v",
        f"{directory / 'model.inp'}:/output/model.inp:ro",
        "-w",
        "/output",
        profile["image_id"],
        TIMEOUT_CONTROL["path"],
        "--signal=KILL",
        "60s",
        profile["binary_path"],
        "-i",
        "model",
    ]
    require(
        command == expected,
        "execution command differs from scoped hard-stop invocation",
    )


def check(directory: Path, expected_freeze_sha256: str) -> dict:
    """Check exact inputs, reconstruction, terminal links and every numerical row."""
    require(
        re.fullmatch(r"[0-9a-f]{64}", expected_freeze_sha256) is not None,
        "externally supplied exact freeze hash is required",
    )
    directory = directory.resolve()
    require(directory.is_relative_to(ROOT.resolve()), "attempt is outside repository")
    require(
        digest(directory / "freeze.json") == expected_freeze_sha256,
        "freeze differs from externally reviewed hash",
    )
    packet = load_json(directory / "freeze.json")
    require(
        packet.get("schema") == "wood_joint_reduced_native_freeze/v1"
        and packet.get("scope") == SCOPE
        and packet.get("candidate") == CANDIDATE
        and packet.get("geometry_revision_id") == REVISION
        and packet.get("native_solve_executed") is False
        and packet.get("mechanical_acceptance") is False,
        "freeze identity or software-only scope changed",
    )
    required_sources = {
        relative_source(Path(__file__)),
        relative_source(PREPARATION / "prepare.py"),
        relative_source(PREPARATION / "check_output.py"),
        relative_source(ORACLE),
        relative_source(PROFILE),
        "fea/wood_joint_reduced_native.py",
    }
    sources = packet.get("source_sha256")
    require(
        isinstance(sources, dict) and required_sources.issubset(sources),
        "freeze omits a required implementation, oracle or profile source",
    )
    require(
        sources["fea/wood_joint_reduced_native.py"] == LEGACY_SHA256
        and sources[relative_source(PROFILE)] == PROFILE_SHA256,
        "preserved runner or profile identity changed",
    )
    require(
        set(packet.get("files_sha256", {}))
        == {"model.inp", "model.json", "expected.json"},
        "freeze must bind deck, model and numerical expectation",
    )
    sys.path.insert(0, str(ROOT))
    from fea.wood_joint_reduced_native import verify

    verify(directory)
    profile = packet.get("solver_profile")
    require(
        profile == load_json(PROFILE),
        "embedded profile differs from pinned stock profile",
    )
    producer = runpy.run_path(str(PREPARATION / "prepare.py"))
    deck, expected = producer["prepare"]()
    require(
        (directory / "model.inp").read_bytes() == deck.encode()
        and load_json(directory / "expected.json") == expected,
        "frozen deck or expectation differs from pinned source reconstruction",
    )
    model = load_json(directory / "model.json")
    require(
        model.get("scope") == SCOPE
        and model.get("candidate") == CANDIDATE
        and model.get("geometry_revision_id") == REVISION
        and model.get("synthetic_only") is True
        and model.get("mechanical_acceptance") is False,
        "model record changed the fixture identity or scope",
    )
    authorization_path = directory / "authorization.json"
    execution_path = directory / "execution.json"
    authorization = load_json(authorization_path)
    execution = load_json(execution_path)
    run_id = authorization.get("run_id")
    require(
        isinstance(run_id, str)
        and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}", run_id) is not None,
        "invalid authorized run ID",
    )
    require(
        authorization.get("scope") == SCOPE
        and authorization.get("input_freeze_sha256") == expected_freeze_sha256
        and authorization.get("parent_readiness") is True
        and authorization.get("native_execution_authorized") is True
        and authorization.get("mechanical_acceptance") is False,
        "authorization does not bind this scoped freeze",
    )
    require(
        authorization.get("owner_authority_sha256") == digest(ROOT / "AGENTS.md"),
        "authorization does not bind current owner instructions",
    )
    require(
        execution.get("run_id") == run_id
        and execution.get("returncode") == 0
        and execution.get("native_solve_executed") is True
        and execution.get("container_confirmed_terminal") is True
        and execution.get("mechanical_acceptance") is False
        and "exception" not in execution
        and "cleanup_exception" not in execution,
        "execution is not successful and confirmed terminal",
    )
    require(
        execution.get("command") == authorization.get("command"),
        "authorization and execution commands differ",
    )
    require(
        authorization.get("timeout_control") == TIMEOUT_CONTROL
        and execution.get("timeout_control") == TIMEOUT_CONTROL,
        "runner records do not bind the qualified absolute timeout utility",
    )
    check_command(execution["command"], directory, run_id, profile)
    review, review_sha256 = bound_review(authorization)
    require(
        review.get("input_freeze_sha256") == expected_freeze_sha256
        and review.get("ready_for_scoped_native_run") is True,
        "independent review does not approve this exact freeze",
    )
    ledger = load_json(LEDGER)
    rows = [row for row in ledger.get("runs", []) if row.get("run_id") == run_id]
    require(len(rows) == 1, "ledger must have one unique run row")
    row = rows[0]
    require(
        row.get("scope") == SCOPE
        and row.get("attempt_directory") == relative_source(directory)
        and row.get("input_freeze_sha256") == expected_freeze_sha256
        and row.get("max_launches") == 1
        and row.get("launches_consumed") == 1
        and row.get("state") == "consumed_terminal"
        and row.get("parent_readiness") is True
        and row.get("native_execution_authorized") is True
        and row.get("authorization_sha256") == digest(authorization_path)
        and row.get("execution_record_sha256") == digest(execution_path),
        "ledger row does not bind the unique terminal execution",
    )
    observed = {
        p.name: digest(p)
        for p in directory.iterdir()
        if p.is_file() and (p.name.startswith("model.") or p.name.startswith("native."))
    }
    require(
        {
            "model.inp",
            "model.json",
            "model.dat",
            "native.stdout",
            "native.stderr",
        }.issubset(observed),
        "required inputs or captured outputs are absent",
    )
    require(
        execution.get("outputs_sha256") == observed,
        "captured output inventory or hashes differ from terminal execution",
    )
    coordinates = {}
    active = False
    for raw in deck.splitlines():
        if raw.startswith("*"):
            active = raw.upper() == "*NODE"
        elif active and raw.strip():
            fields = raw.split(",")
            coordinates[int(fields[0])] = tuple(float(x) for x in fields[1:])
    oracle = load_json(ORACLE)
    reader = runpy.run_path(str(PREPARATION / "check_output.py"))
    numerical = reader["check"](
        (directory / "model.dat").read_text(),
        expected,
        coordinates,
        oracle["global_strain_tensor"],
    )
    return {
        "schema": "orthotropic_stress_frame_authenticated_result/v1",
        "status": "PASS_AUTHENTICATED_STRESS_FRAME_SOFTWARE_FIXTURE_ONLY",
        "input_freeze_sha256": expected_freeze_sha256,
        "run_id": run_id,
        "scope": SCOPE,
        "image_id": profile["image_id"],
        "binary_sha256": profile["binary_sha256"],
        "authorization_sha256": digest(authorization_path),
        "execution_sha256": digest(execution_path),
        "independent_review_sha256": review_sha256,
        "ledger_sha256": digest(LEDGER),
        "ledger_row": row,
        "outputs_sha256": observed,
        "numerical": numerical,
        "mechanical_acceptance": False,
        "engineering_mvp_complete": False,
        "formal_criteria_pending": 47,
        "physical_releases": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected-freeze-sha256", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            check(args.directory, args.expected_freeze_sha256),
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
