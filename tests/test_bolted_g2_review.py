"""G2 cannot open while resistance or native-input gates are unresolved."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_g2_review_keeps_native_cases_closed() -> None:
    review = json.loads((ROOT / "docs/bolted-candidate-g2-review.json").read_text())
    assert review["status"] == "blocked_pending_engineering_inputs"
    assert review["criteria"]["ready_for_first_native_case"] is False
    assert review["native_cases_run"] is False
    assert review["baseline_evidence_transferred"] is False
    assert any("factory hole" in action for action in review["blocking_actions"])
    assert any("resistance basis" in action for action in review["blocking_actions"])
