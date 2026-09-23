"""Build and check the separate, unreleased barrel-candidate authority record."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "barrel-nut-candidate.json"
CANDIDATE = "compact-floor-flush-bolted-development"
SELECTED_CANDIDATE = "compact-floor-flush-development"
SCHEMA = "owner_barrel_candidate_contract/v1"
STATION_REGISTER = "docs/barrel-nut-stations.json"
SCENE = "site/owner-barrel-layout-scene.json"
SOURCE_PATHS = (
    "scripts/owner_barrel_candidate_contract.py",
    "scripts/owner_barrel_validation_register.py",
    "scripts/export_owner_barrel_scene.py",
    "scripts/owner_barrel_native_connector_inventory.py",
)
DATA_PATHS = (STATION_REGISTER, SCENE)
EXPECTED_COUNTS = {
    "stations": 24,
    "barrel_bolts": 46,
    "barrels": 46,
    "barrel_pairs": 46,
    "barrel_face_contact_cells": 132,
    "drilling_paths": 98,
    "access_paths": 92,
    "retained_frame_bolts": 12,
    "fixed_panel_kicker_screws": 66,
    "removed_legacy_structural_sds": 144,
}
EXPECTED_UNITS = {
    "length": "mm",
    "area": "mm^2",
    "volume": "mm^3",
    "force": "N",
    "moment": "N*mm",
    "mass": "kg",
    "stiffness": "N/mm",
    "areal_stiffness": "N/mm^3",
    "weight_request": "lbf",
}
GEOMETRY_KEYS = (
    "baseline",
    "station_modes",
    "station_dispositions",
    "solids",
    "barrel_nut_envelopes",
    "diagnostic_bolt_axes",
    "rail_head_washer_envelopes",
    "other_head_washer_envelopes",
    "conditional_outer_header_recess_envelopes",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True
    ).stdout


def _head_commit() -> str:
    commit = _git("rev-parse", "HEAD").decode().strip()
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Git HEAD is not a full SHA-1 identity")
    return commit


def _status_entries() -> list[str]:
    entries = _git("status", "--porcelain=v1", "--untracked-files=all", "-z")
    return sorted(
        entry.decode(errors="surrogateescape")
        for entry in entries.split(b"\0")
        if entry and not entry.decode(errors="surrogateescape").endswith(
            " barrel-nut-candidate.json"
        )
    )


def _dirty_snapshot(entries: list[str]) -> str:
    tracked_diff = _git("diff", "--binary", "HEAD", "--", ".")
    untracked = {}
    for entry in entries:
        if not entry.startswith("?? "):
            continue
        name = entry[3:]
        path = ROOT / name
        untracked[name] = _sha256(path) if path.is_file() else "not_a_regular_file"
    return _digest(
        {
            "porcelain_entries": entries,
            "tracked_diff_sha256": hashlib.sha256(tracked_diff).hexdigest(),
            "untracked_file_sha256": untracked,
        }
    )


def _repository_state() -> dict:
    entries = _status_entries()
    return {
        "head_commit": _head_commit(),
        "worktree_clean_at_generation": not entries,
        "uncommitted_changes_present_at_generation": bool(entries),
        "porcelain_entries_at_generation": entries,
        "dirty_snapshot_sha256": _dirty_snapshot(entries),
        "contract_output_excluded_from_snapshot": "barrel-nut-candidate.json",
        "status_policy": (
            "Generation-time snapshot only. Per-file hashes bind candidate inputs; "
            "this record does not claim a clean or frozen repository state."
        ),
    }


def _load_json(name: str) -> dict:
    value = json.loads((ROOT / name).read_text())
    if not isinstance(value, dict):
        raise TypeError(f"{name} must contain one JSON object")
    return value


def _geometry_fingerprint(scene: dict) -> str:
    missing = set(GEOMETRY_KEYS) - set(scene)
    if missing:
        raise ValueError(f"Scene lacks geometry fields: {sorted(missing)}")
    return _digest({key: scene[key] for key in GEOMETRY_KEYS})


def validate_contract(contract: dict) -> None:
    """Validate finite identity and fail closed on any release claim."""
    station = contract.get("station_register", {})
    authority = contract.get("authority", {})
    if contract.get("schema") != SCHEMA or contract.get("candidate") != CANDIDATE:
        raise ValueError("Unexpected barrel candidate contract identity")
    if (
        authority.get("role") != "separate_development_candidate"
        or authority.get("selected_candidate") != SELECTED_CANDIDATE
        or authority.get("replaces_selected_authority") is not False
        or authority.get("selected_authority_path") != "current-candidate.json"
    ):
        raise ValueError("Candidate-only authority boundary changed")
    if station.get("path") != STATION_REGISTER:
        raise ValueError("Station-register binding changed")
    if (
        set(contract.get("source_sha256", {})) != set(SOURCE_PATHS)
        or set(contract.get("data_sha256", {})) != set(DATA_PATHS)
        or station.get("sha256") != contract["data_sha256"][STATION_REGISTER]
        or contract.get("geometry", {}).get("scene_sha256")
        != contract["data_sha256"][SCENE]
    ):
        raise ValueError("Candidate source/data binding changed")
    if (
        station.get("counts") != EXPECTED_COUNTS
        or contract.get("counts") != EXPECTED_COUNTS
    ):
        raise ValueError("Candidate connection counts changed")
    if station.get("units") != EXPECTED_UNITS or contract.get("units") != EXPECTED_UNITS:
        raise ValueError("Candidate units changed")
    if (
        contract.get("release") is not False
        or not contract.get("release_flags")
        or any(contract["release_flags"].values())
    ):
        raise ValueError("Candidate contract must remain unreleased")
    repository = contract.get("repository_state", {})
    if (
        type(repository.get("worktree_clean_at_generation")) is not bool
        or type(repository.get("uncommitted_changes_present_at_generation")) is not bool
        or repository["worktree_clean_at_generation"]
        == repository["uncommitted_changes_present_at_generation"]
        or len(repository.get("dirty_snapshot_sha256", "")) != 64
    ):
        raise ValueError("Repository dirty-state disclosure is invalid")


def build_contract() -> dict:
    source_sha256 = {name: _sha256(ROOT / name) for name in SOURCE_PATHS}
    data_sha256 = {name: _sha256(ROOT / name) for name in DATA_PATHS}
    selected_sha256 = _sha256(ROOT / "current-candidate.json")
    register = _load_json(STATION_REGISTER)
    scene = _load_json(SCENE)
    selected = _load_json("current-candidate.json")
    if (
        register.get("candidate") != CANDIDATE
        or register.get("counts") != EXPECTED_COUNTS
        or register.get("units") != EXPECTED_UNITS
        or register.get("release") is not False
        or any(register.get("release_flags", {}).values())
    ):
        raise ValueError("Station register is not authenticated and unreleased")
    if selected.get("candidate") != SELECTED_CANDIDATE:
        raise ValueError("Selected authority changed; do not promote through this contract")
    if any(
        scene.get(flag) is not False
        for flag in (
            "layout_clearance_approved",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    ):
        raise ValueError("Scene unexpectedly claims release")
    contract = {
        "schema": SCHEMA,
        "candidate": CANDIDATE,
        "status": "development_contract_unreleased",
        "authority": {
            "role": "separate_development_candidate",
            "selected_authority_path": "current-candidate.json",
            "selected_candidate": SELECTED_CANDIDATE,
            "selected_authority_sha256": selected_sha256,
            "replaces_selected_authority": False,
        },
        "repository_state": _repository_state(),
        "source_sha256": source_sha256,
        "data_sha256": data_sha256,
        "station_register": {
            "path": STATION_REGISTER,
            "sha256": data_sha256[STATION_REGISTER],
            "schema": register["schema"],
            "repository_commit": register["repository_commit"],
            "counts": register["counts"],
            "units": register["units"],
            "connector_inventory_fingerprint_sha256": register[
                "connector_inventory_fingerprint_sha256"
            ],
            "source_sha256": register["source_sha256"],
        },
        "geometry": {
            "scene_path": SCENE,
            "scene_sha256": data_sha256[SCENE],
            "fingerprint_sha256": _geometry_fingerprint(scene),
            "fingerprint_fields": list(GEOMETRY_KEYS),
            "fingerprint_method": (
                "SHA-256 of canonical JSON for the named scene geometry fields"
            ),
        },
        "counts": register["counts"],
        "units": register["units"],
        "release": False,
        "release_flags": {
            "geometry_accepted": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "diy_ready": False,
        },
        "limits": (
            "Candidate-only development identity. Hash and geometry agreement do not "
            "establish hardware properties, joint resistance, accepted native demands, "
            "fabrication dimensions, or DIY release."
        ),
    }
    if (
        source_sha256
        != {name: _sha256(ROOT / name) for name in SOURCE_PATHS}
        or data_sha256 != {name: _sha256(ROOT / name) for name in DATA_PATHS}
        or selected_sha256 != _sha256(ROOT / "current-candidate.json")
    ):
        raise ValueError("Candidate input changed during contract generation; retry")
    validate_contract(contract)
    return contract


def check_contract(contract: dict) -> dict[str, bool]:
    """Check bound files and report repository drift without hiding dirty state."""
    validate_contract(contract)
    scene = _load_json(SCENE)
    source_match = contract["source_sha256"] == {
        name: _sha256(ROOT / name) for name in SOURCE_PATHS
    }
    data_match = contract["data_sha256"] == {
        name: _sha256(ROOT / name) for name in DATA_PATHS
    }
    selected_match = (
        contract["authority"]["selected_authority_sha256"]
        == _sha256(ROOT / "current-candidate.json")
    )
    geometry_match = (
        contract["geometry"]["fingerprint_sha256"]
        == _geometry_fingerprint(scene)
    )
    current_repository = _repository_state()
    snapshot_match = (
        contract["repository_state"]["head_commit"]
        == current_repository["head_commit"]
        and contract["repository_state"]["dirty_snapshot_sha256"]
        == current_repository["dirty_snapshot_sha256"]
    )
    return {
        "source_hashes_match": source_match,
        "data_hashes_match": data_match,
        "selected_authority_hash_matches": selected_match,
        "geometry_fingerprint_matches": geometry_match,
        "repository_snapshot_matches": snapshot_match,
        "worktree_currently_dirty": current_repository[
            "uncommitted_changes_present_at_generation"
        ],
        "bound_inputs_valid": all(
            (source_match, data_match, selected_match, geometry_match)
        ),
        "fully_reproduced_including_dirty_snapshot": all(
            (source_match, data_match, selected_match, geometry_match, snapshot_match)
        ),
        "valid": all((source_match, data_match, selected_match, geometry_match)),
    }


def render(contract: dict) -> str:
    return json.dumps(contract, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        result = check_contract(json.loads(args.output.read_text()))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    # Write twice so generation-time Git status includes all new inputs while
    # explicitly excluding only this generated contract artifact.
    args.output.write_text(render(build_contract()))
    args.output.write_text(render(build_contract()))


if __name__ == "__main__":
    main()
