"""Synthetic execution chains only; no Docker, native run or shared ledger writes."""

import importlib.util
import json
import runpy
import shutil
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "stress_provenance", Path(__file__).with_name("check_provenance.py")
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


@pytest.fixture
def chain(tmp_path, monkeypatch):
    original_root = checker.ROOT
    original_preparation = checker.PREPARATION
    fixture = runpy.run_path(str(original_preparation / "test_output.py"))
    dat, _, _, _ = fixture["build_fixture"]()
    root = tmp_path / "repo"
    copied = [
        Path(__file__).with_name("check_provenance.py"),
        original_preparation / "prepare.py",
        original_preparation / "check_output.py",
        checker.ORACLE,
        checker.PROFILE,
        original_root / "fea/wood_joint_reduced_native.py",
        original_root / "AGENTS.md",
        original_root / "fea/generated/ccx_2.23.pdf",
    ]
    affine = (
        original_preparation.parent
        / "washer-annular-affine-native-2026-10-01-attempt01"
    )
    copied.extend(affine / name for name in ("model.inp", "model.json", "freeze.json"))
    for source in copied:
        target = root / source.relative_to(original_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    checker_path = root / Path(checker.__file__).relative_to(original_root)
    monkeypatch.setattr(checker, "__file__", str(checker_path))
    for name in ("ROOT", "PREPARATION", "ORACLE", "PROFILE", "LEDGER"):
        old = getattr(checker, name)
        monkeypatch.setattr(
            checker,
            name,
            root if name == "ROOT" else root / old.relative_to(original_root),
        )
    from fea import wood_joint_reduced_native as native

    monkeypatch.setattr(native, "ROOT", root)
    directory = root / "docs/attempt"
    directory.mkdir(parents=True)
    deck, expected = runpy.run_path(str(checker.PREPARATION / "prepare.py"))[
        "prepare"
    ]()
    (directory / "model.inp").write_text(deck)
    write_json(directory / "expected.json", expected)
    write_json(
        directory / "model.json",
        {
            "scope": checker.SCOPE,
            "candidate": checker.CANDIDATE,
            "geometry_revision_id": checker.REVISION,
            "synthetic_only": True,
            "mechanical_acceptance": False,
        },
    )
    sources = {}
    for source in copied[:6]:
        relative = str(source.relative_to(original_root))
        live = root / relative
        snapshot = directory / "sources" / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(live, snapshot)
        sources[relative] = checker.digest(live)
    profile = checker.load_json(checker.PROFILE)
    packet = {
        "schema": "wood_joint_reduced_native_freeze/v1",
        "scope": checker.SCOPE,
        "candidate": checker.CANDIDATE,
        "geometry_revision_id": checker.REVISION,
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "solver_profile": profile,
        "source_sha256": sources,
        "files_sha256": {
            name: checker.digest(directory / name)
            for name in ("model.inp", "model.json", "expected.json")
        },
    }
    write_json(directory / "freeze.json", packet)
    freeze_sha = checker.digest(directory / "freeze.json")
    review_path = root / "docs/review.json"
    write_json(
        review_path,
        {"input_freeze_sha256": freeze_sha, "ready_for_scoped_native_run": True},
    )
    run_id = "synthetic-stress-frame-only"
    command = [
        "docker",
        "--context",
        "default",
        "run",
        "--rm",
        "--name",
        "moonboard-" + run_id,
        "--network=none",
        "--cpus=1",
        "--memory=1g",
        "--user",
        "1000:1000",
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
        "/usr/bin/timeout",
        "--signal=KILL",
        "60s",
        profile["binary_path"],
        "-i",
        "model",
    ]
    authorization = {
        "run_id": run_id,
        "scope": checker.SCOPE,
        "input_freeze_sha256": freeze_sha,
        "parent_readiness": True,
        "native_execution_authorized": True,
        "mechanical_acceptance": False,
        "owner_authority_sha256": checker.digest(root / "AGENTS.md"),
        "command": command,
        "timeout_control": checker.TIMEOUT_CONTROL.copy(),
        "independent_review": "docs/review.json",
        "independent_review_sha256": checker.digest(review_path),
    }
    write_json(directory / "authorization.json", authorization)
    (directory / "model.dat").write_text(dat)
    (directory / "native.stdout").write_text("synthetic fixture; no native execution\n")
    (directory / "native.stderr").write_text("")
    execution = {
        "run_id": run_id,
        "returncode": 0,
        "native_solve_executed": True,
        "container_confirmed_terminal": True,
        "mechanical_acceptance": False,
        "command": command,
        "timeout_control": checker.TIMEOUT_CONTROL.copy(),
        "outputs_sha256": {
            p.name: checker.digest(p)
            for p in directory.iterdir()
            if p.is_file()
            and (p.name.startswith("model.") or p.name.startswith("native."))
        },
    }
    write_json(directory / "execution.json", execution)
    ledger = {
        "runs": [
            {
                "run_id": run_id,
                "scope": checker.SCOPE,
                "attempt_directory": "docs/attempt",
                "input_freeze_sha256": freeze_sha,
                "max_launches": 1,
                "launches_consumed": 1,
                "state": "consumed_terminal",
                "parent_readiness": True,
                "native_execution_authorized": True,
                "authorization_sha256": checker.digest(
                    directory / "authorization.json"
                ),
                "execution_record_sha256": checker.digest(directory / "execution.json"),
            }
        ]
    }
    write_json(checker.LEDGER, ledger)
    return directory, freeze_sha


def test_synthetic_full_chain_and_numerical_rows_pass(chain):
    result = checker.check(*chain)
    assert result["numerical"]["stress_rows"] == 4608
    assert result["numerical"]["displacement_rows"] == 800
    assert result["mechanical_acceptance"] is False
    assert result["engineering_mvp_complete"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "external_hash",
        "input",
        "source",
        "expectation",
        "missing_source",
        "profile",
        "authorization_freeze",
        "review_hash",
        "review_freeze",
        "returncode",
        "nonterminal",
        "duplicate_ledger",
        "ledger_hash",
        "missing_output_hash",
        "output_drift",
        "wrong_memory",
        "term_only",
        "numerical_drift",
        "path_utility",
        "utility_hash",
        "swap_allowance",
    ],
)
def test_broken_chain_or_numerical_answer_is_refused(chain, mutation):
    directory, freeze_sha = chain
    authorization_path = directory / "authorization.json"
    execution_path = directory / "execution.json"
    authorization = checker.load_json(authorization_path)
    execution = checker.load_json(execution_path)
    ledger = checker.load_json(checker.LEDGER)
    if mutation == "external_hash":
        freeze_sha = "0" * 64
    elif mutation == "input":
        with (directory / "model.inp").open("a") as stream:
            stream.write("** changed\n")
    elif mutation == "source":
        with (checker.PREPARATION / "check_output.py").open("a") as stream:
            stream.write("\n# changed\n")
    elif mutation in ("expectation", "missing_source", "profile"):
        packet = checker.load_json(directory / "freeze.json")
        if mutation == "expectation":
            expected = checker.load_json(directory / "expected.json")
            expected["expected_energy_N_mm"] *= 2
            write_json(directory / "expected.json", expected)
            packet["files_sha256"]["expected.json"] = checker.digest(
                directory / "expected.json"
            )
        elif mutation == "missing_source":
            del packet["source_sha256"][
                checker.relative_source(checker.PREPARATION / "check_output.py")
            ]
        else:
            packet["solver_profile"]["image_id"] = "sha256:" + "0" * 64
        write_json(directory / "freeze.json", packet)
        freeze_sha = checker.digest(directory / "freeze.json")
    elif mutation == "authorization_freeze":
        authorization["input_freeze_sha256"] = "0" * 64
    elif mutation == "review_hash":
        authorization["independent_review_sha256"] = "0" * 64
    elif mutation == "review_freeze":
        review = checker.ROOT / authorization["independent_review"]
        write_json(
            review,
            {"input_freeze_sha256": "0" * 64, "ready_for_scoped_native_run": True},
        )
        authorization["independent_review_sha256"] = checker.digest(review)
    elif mutation == "returncode":
        execution["returncode"] = 137
    elif mutation == "nonterminal":
        execution["container_confirmed_terminal"] = False
    elif mutation == "duplicate_ledger":
        ledger["runs"].append(ledger["runs"][0].copy())
    elif mutation == "ledger_hash":
        ledger["runs"][0]["execution_record_sha256"] = "0" * 64
    elif mutation == "missing_output_hash":
        del execution["outputs_sha256"]["model.dat"]
    elif mutation == "output_drift":
        with (directory / "native.stdout").open("a") as stream:
            stream.write("changed\n")
    elif mutation in ("wrong_memory", "term_only"):
        for record in (authorization, execution):
            record["command"][9 if mutation == "wrong_memory" else 23] = (
                "--memory=2g" if mutation == "wrong_memory" else "--signal=TERM"
            )
    elif mutation == "numerical_drift":
        lines = (directory / "model.dat").read_text().splitlines()
        lines[-1] = "999"
        (directory / "model.dat").write_text("\n".join(lines))
        execution["outputs_sha256"]["model.dat"] = checker.digest(
            directory / "model.dat"
        )
    elif mutation in ("path_utility", "swap_allowance"):
        for record in (authorization, execution):
            record["command"][22 if mutation == "path_utility" else 14] = (
                "timeout" if mutation == "path_utility" else "--memory-swap=2g"
            )
    elif mutation == "utility_hash":
        execution["timeout_control"]["sha256"] = "0" * 64
    write_json(authorization_path, authorization)
    write_json(execution_path, execution)
    # Synchronize outer hashes so failures exercise the intended inner links.
    if mutation != "ledger_hash":
        for row in ledger["runs"]:
            row["authorization_sha256"] = checker.digest(authorization_path)
            row["execution_record_sha256"] = checker.digest(execution_path)
    write_json(checker.LEDGER, ledger)
    with pytest.raises(ValueError):
        checker.check(directory, freeze_sha)
