"""Replay the immutable two-cell mathematics under current controls.

The historical verifier intentionally retains its old AGENTS.md pin. This
wrapper proves that its only stale input is the documented workflow-control
paragraph, then reruns the imported pure fixture functions without changing the
historical fixture, observed result, or native authorization.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = BASE / "current-floor-normal-tangent-join-contract-attempt01"
FIXTURE_DIR = BASE / "conditional-floor-two-cell-coupled-stick-fixture-attempt01"
FIXTURE_PATH = FIXTURE_DIR / "fixture.json"
OBSERVED_PATH = FIXTURE_DIR / "observed.json"
VERIFIER_PATH = FIXTURE_DIR / "verify_fixture.py"
CHECKSUMS_PATH = FIXTURE_DIR / "SHA256SUMS"
OUTPUT = HERE / "current-controls-two-cell-replay.json"
HISTORICAL_AGENTS_REVISION = "33d0e129742f5683ee06c3087694c811309b1fd1"
PINNED_AGENTS_SHA256 = "672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536"
EXPECTED_CURRENT_AGENTS_SHA256 = "63c317ead36f0cee13f211d26b7cb8b2cd0109f84525ad9c3efe39698bd39336"
EXPECTED_CONTROL_INSERTION = (
    b"\nUse `master` exclusively for future work, commits and pushes. Do not create\n"
    b"development branches or branch-based worktrees. Coordinate shared staging\n"
    b"and commits with other running agents.\n\n## Working set\n"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_render(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def git_show(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def import_historical_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("immutable_two_cell_verifier", ROOT / VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import the immutable historical two-cell verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_local_fixture_checksums() -> dict[str, str]:
    observed: dict[str, str] = {}
    for raw in (ROOT / CHECKSUMS_PATH).read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        expected, name = raw.split(maxsplit=1)
        name = name.lstrip(" *")
        actual = sha256_file(ROOT / FIXTURE_DIR / name)
        if actual != expected:
            raise ValueError(f"Historical fixture local checksum mismatch for {name}: {actual} != {expected}")
        observed[name] = actual
    if set(observed) != {"README.md", "fixture.json", "verify_fixture.py", "observed.json"}:
        raise ValueError("Historical fixture local checksum inventory changed")
    return observed


def main_result() -> dict[str, Any]:
    module = import_historical_verifier()
    fixture = load_json(ROOT / FIXTURE_PATH)
    observed_bytes = (ROOT / OBSERVED_PATH).read_bytes()
    local_checksums = verify_local_fixture_checksums()

    old_agents = git_show(HISTORICAL_AGENTS_REVISION, "AGENTS.md")
    old_agents_sha = sha256_bytes(old_agents)
    current_agents = (ROOT / "AGENTS.md").read_bytes()
    current_agents_sha = sha256_bytes(current_agents)
    head_agents = git_show("HEAD", "AGENTS.md")
    if current_agents != head_agents:
        raise ValueError("Working-tree AGENTS.md differs from HEAD; controls-only comparison is not established")
    if old_agents_sha != PINNED_AGENTS_SHA256:
        raise ValueError("Historical AGENTS revision does not reproduce the fixture's original pin")
    if current_agents_sha != EXPECTED_CURRENT_AGENTS_SHA256:
        raise ValueError("Current AGENTS.md differs from this packet's pinned controls context")
    marker = b"\n## Working set\n"
    if old_agents.count(marker) != 1:
        raise ValueError("Could not locate the unique insertion point for the historical/current controls comparison")
    old_prefix, old_suffix = old_agents.split(marker)
    expected_current = old_prefix + EXPECTED_CONTROL_INSERTION + old_suffix
    if current_agents != expected_current:
        diff = "".join(difflib.unified_diff(
            old_agents.decode("utf-8").splitlines(keepends=True),
            current_agents.decode("utf-8").splitlines(keepends=True),
            fromfile="historical-AGENTS.md",
            tofile="current-AGENTS.md",
        ))
        raise ValueError("AGENTS.md has changes beyond the known controls paragraph:\n" + diff)

    historical_sources: dict[str, str] = {}
    current_sources: dict[str, str] = {}
    non_agents_hashes: dict[str, str] = {}
    for name, (relative, expected) in module.PINNED_SOURCES.items():
        actual = sha256_file(ROOT / relative)
        if fixture["sources"].get(name) != expected:
            raise ValueError(f"Historical fixture's embedded source pin changed: {name}")
        if name == "AGENTS.md":
            if expected != old_agents_sha or actual != current_agents_sha:
                raise ValueError("Stale AGENTS pin does not match the documented historical/current controls")
            historical_sources[str(relative)] = expected
            current_sources[str(relative)] = actual
        else:
            if actual != expected:
                raise ValueError(f"A non-controls fixture dependency changed: {relative}: {actual} != {expected}")
            historical_sources[str(relative)] = actual
            current_sources[str(relative)] = actual
            non_agents_hashes[str(relative)] = actual

    # Recompute the exact historical output first, to show that its existing
    # result remains reproducible under its original pins.
    historical_result = module.run_fixture(fixture, historical_sources)
    if canonical_render(historical_result) != observed_bytes:
        raise ValueError("Imported pure fixture functions do not reproduce the preserved historical observed.json")

    # Replay once more with the current AGENTS hash. The only changed input hash
    # is controls context; all mathematical result fields must remain identical.
    current_result = module.run_fixture(fixture, current_sources)
    historical_math = {key: value for key, value in historical_result.items() if key != "source_sha256"}
    current_math = {key: value for key, value in current_result.items() if key != "source_sha256"}
    if current_math != historical_math:
        raise ValueError("Current-controls replay changed mathematical fixture results")

    # Reproduce the original official-verifier blocker rather than rewriting its
    # pin or treating a controls-only replay as the historical full verification.
    official = subprocess.run(
        [sys.executable, str(ROOT / VERIFIER_PATH), "--verify"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    stale_message = f"source pin mismatch for AGENTS.md: {current_agents_sha} != {PINNED_AGENTS_SHA256}"
    combined = official.stdout + official.stderr
    if official.returncode == 0 or stale_message not in combined:
        raise ValueError("Historical full-verifier result no longer matches the recorded stale-AGENTS-pin blocker")

    summary = current_result["result_summary"]
    return {
        "schema": "current_controls_two_cell_mathematical_replay/v1",
        "status": "PASS_CURRENT_CONTROLS_MATHEMATICAL_REPLAY",
        "historical_fixture_preservation": {
            "fixture_directory": str(FIXTURE_DIR),
            "original_fixture_sha256": local_checksums["fixture.json"],
            "original_verifier_sha256": local_checksums["verify_fixture.py"],
            "original_observed_sha256": local_checksums["observed.json"],
            "original_local_checksum_manifest_sha256": sha256_file(ROOT / CHECKSUMS_PATH),
            "original_observed_reproduced_under_original_pins": True,
            "fixture_and_observed_files_modified": False,
        },
        "controls_provenance": {
            "historical_agents_revision": HISTORICAL_AGENTS_REVISION,
            "historical_agents_sha256": old_agents_sha,
            "current_agents_sha256": current_agents_sha,
            "only_agents_change": "Added exclusive-master/shared-staging workflow instructions; the remaining bytes are identical.",
            "model_load_geometry_or_fixture_physics_changed_in_agents": False,
            "non_agents_fixture_dependencies_unchanged": True,
            "non_agents_fixture_dependency_sha256": dict(sorted(non_agents_hashes.items())),
        },
        "historical_full_verifier": {
            "status": "BLOCKED_BY_STALE_EXTERNAL_AGENTS_PIN",
            "exit_code": official.returncode,
            "failure": stale_message,
            "full_verifier_claimed_pass": False,
        },
        "fixture_replay": {
            "status": current_result["status"],
            "stage_count": summary["stage_count"],
            "unique_normal_active_set_each_stage": summary["unique_normal_active_set_each_stage"],
            "max_normal_equilibrium_residual": summary["max_normal_equilibrium_residual"],
            "max_tangent_equilibrium_residual": summary["max_tangent_equilibrium_residual"],
            "max_active_stick_slip": summary["max_active_stick_slip"],
            "open_contact_tangent_force": summary["open_contact_tangent_force"],
            "floor_gate_status": summary["floor_gate_status"],
            "native_solve_run": summary["native_solve_run"],
            "mathematical_result_equal_to_historical_replay": True,
            "source_hash_difference": ["AGENTS.md only"],
            "current_source_sha256": dict(sorted(current_sources.items())),
        },
        "authorization_boundary": {
            "native_solve_executed": False,
            "native_authorization_or_freeze_changed": False,
            "interpretation": "This is a mathematical fixture replay under current repository controls. Native authorization, frozen inputs, serialized execution, and any frame solve remain separate parent-owned gates.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="recompute and compare with the separate current-controls record")
    mode.add_argument("--write", action="store_true", help="write only this packet's separate replay record")
    args = parser.parse_args()
    result = main_result()
    rendered = canonical_render(result)
    output = ROOT / OUTPUT
    if args.write:
        output.write_bytes(rendered)
        print(f"wrote {OUTPUT}")
        return
    if not output.is_file():
        raise SystemExit("missing current-controls-two-cell-replay.json; inspect source/control checks then run --write")
    if output.read_bytes() != rendered:
        raise SystemExit("verification failed: current-controls mathematical replay differs from its packet record")
    print(
        "PASS_CURRENT_CONTROLS_MATHEMATICAL_REPLAY: eight-stage two-cell result matches preserved math; "
        "only historical AGENTS pin is stale; no native authorization or run changed"
    )


if __name__ == "__main__":
    main()
