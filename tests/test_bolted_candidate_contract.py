"""LB-06 scaffold and baseline-preservation contract."""

import pytest

from mini_moonboard import compact_floor_flush_bolted_frame as candidate


def test_candidate_identity_and_scope_are_explicit() -> None:
    metadata = candidate.candidate_metadata()
    assert candidate.KEY == "compact-floor-flush-bolted-development"
    assert metadata["baseline_candidate"] == "compact-floor-flush-development"
    assert metadata["selected_as_repository_default"] is False
    assert metadata["panel_policy"] == "retain_existing_66_hillman_screws"
    assert metadata["future_panel_inserts"] == "deferred_not_a_dependency"


def test_scaffold_preserves_raw_inventory_and_panel_connections() -> None:
    parts = candidate.uncut_wood_parts()
    assert len(parts) == 26
    assert sum(part.name.startswith(("main_", "kicker_")) for part in parts) == 6
    assert len(parts) - 6 == 20
    assert len(candidate.panel_connections()) == 66
    assert sum(connection.kind == "bolt" for connection in candidate.connections()) == 12
    assert sum(connection.kind == "screw" for connection in candidate.connections()) == 66
    assert candidate.structural_joint_records() == ()


def test_finished_parts_are_rejected_until_all_families_exist() -> None:
    with pytest.raises(candidate.IncompleteCandidateError, match="missing structural layout"):
        candidate.parts()
