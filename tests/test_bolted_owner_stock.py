"""Owner-reported structural stock state is kept separate from inspection."""

import json
from pathlib import Path

from mini_moonboard import compact_floor_flush_bolted_frame as candidate

ROOT = Path(__file__).parents[1]


def test_owner_stock_report_is_consistent_without_claiming_inspection() -> None:
    owner = json.loads((ROOT / "docs/bolted-candidate-owner-inputs.json").read_text())
    interfaces = json.loads((ROOT / "docs/bolted-candidate-interfaces.json").read_text())
    metadata = candidate.candidate_metadata()
    assert owner["structural_stock"]["condition"] == "uncut_undrilled"
    assert owner["structural_stock"]["source"] == "owner_report_in_codex_task"
    assert owner["structural_stock"]["physical_receiving_inspection_complete"] is False
    assert metadata["actual_structural_stock_condition"] == "owner_reported_uncut_undrilled"
    assert owner["physical_width_packet"]["option"] == "kerf-right"
    assert owner["physical_width_packet"]["kicker_blank_width_mm"] == 1217.6125
    assert metadata["owner_physical_width_option"] == "kerf-right"
    assert metadata["fabrication_release"] is False
    assert owner["frame_change_scope"]["owner_decision"] == (
        "hidden_frame_changes_allowed_for_factory_connector_design"
    )
    assert owner["frame_change_scope"]["source"] == "direct_owner_reply_in_codex_task"
    assert interfaces["physical_state"] == "owner-reported uncut and undrilled; receiving inspection pending"
