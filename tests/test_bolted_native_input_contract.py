"""LB-12 native producer/input contract checks."""

import json
from pathlib import Path

from scripts.bolted_candidate_native_contract import (
    CANONICAL_CASES,
    digest,
    validate_contract,
)


def test_native_contract_preserves_all_six_case_ids_and_panel_scope() -> None:
    result = validate_contract()
    assert tuple(result["canonical_cases"]) == CANONICAL_CASES
    assert result["case_count"] == 6
    assert result["panel_connection_count"] == 66
    assert result["structural_screw_macros_remaining"] == []
    assert result["owner_physical_width_scope"] == "kerf-right"
    assert (
        result["candidate_geometry_width_scope"]
        == "official prototype pending kerf-right native adapter"
    )


def test_native_contract_is_explicitly_not_ready_for_a_solve() -> None:
    result = validate_contract()
    assert result["native_ready"] is False
    assert result["no_native_cases_run"] is True
    assert "adapter" in result["native_blocker"]
    assert len(result["required_artifacts_per_case"]) >= 5


def test_native_contract_fingerprints_candidate_and_producer_sources() -> None:
    result = validate_contract()
    sources = result["source_sha256"]
    required = {
        "mini_moonboard/compact_floor_flush_frame.py",
        "mini_moonboard/compact_floor_flush_bolted_frame.py",
        "mini_moonboard/bolted_layout_common.py",
        "mini_moonboard/bolted_layouts/center_base.py",
        "mini_moonboard/demountable_connections.py",
        "mini_moonboard/bolted_timber_checks.py",
        "mini_moonboard/bolted_steel_checks.py",
        "fea/floor_flush_mesh.py",
        "fea/floor_flush_run.py",
        "fea/user_load_envelope.py",
        "scripts/clear_space_batch.py",
        "docs/floor-flush-construction/connection-axes.csv",
        "docs/floor-flush-construction-kerf-right/connection-axes.csv",
        "mini_moonboard/floor_flush_width.py",
        "docs/bolted-candidate-owner-inputs.json",
    }
    assert required <= sources.keys()
    assert all(
        Path(path).is_file() and digest(path) == sha for path, sha in sources.items()
    )


def test_saved_native_input_is_explicitly_stale_until_v4_candidate_is_frozen() -> None:
    saved = json.loads(Path("docs/bolted-candidate-native-input.json").read_text())
    current = validate_contract()["source_sha256"]
    old = saved["source_sha256"]
    # V4 changed owner authority, but this historical non-ready input was not
    # regenerated or falsely labeled as evidence for a new native solve.
    assert {
        path
        for path in old.keys() | current.keys()
        if old.get(path) != current.get(path)
    } == {"docs/bolted-candidate-owner-inputs.json"}
    assert saved["native_ready"] is False
    assert saved["no_native_cases_run"] is True
