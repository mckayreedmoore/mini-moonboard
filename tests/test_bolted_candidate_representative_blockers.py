"""Keep illustrative archived wrenches distinct from separate historical peaks."""

import json
from pathlib import Path


def test_representative_blockers_cite_separate_archived_peaks():
    record = json.loads(
        Path("docs/bolted-candidate-representative-blockers.json").read_text()
    )
    historical = json.loads(
        Path(
            "docs/bolted-candidate-prototypes/representative-historical-demands.json"
        ).read_text()
    )
    assert record["same_case_is_not_archived_peak_or_envelope"] is True
    assert record["separate_historical_peak_source"].startswith(
        "docs/bolted-candidate-prototypes/representative-historical-demands.json"
    )
    for joint in record["joints"].values():
        beam = historical["stations"][joint["station"]]["flanges"]["beam"]
        peaks = joint["archived_separate_peak_norms"]
        assert peaks["force"] == {
            "case": beam["force_case"],
            "norm_n": beam["maximum_force_norm_n"],
        }
        assert peaks["moment"] == {
            "case": beam["moment_case"],
            "norm_nmm": beam["maximum_moment_norm_nmm"],
        }
        assert joint["new_candidate_demand_available"] is False


def test_center_blockers_track_new_fixed_support_and_access_evidence():
    record = json.loads(
        Path("docs/bolted-candidate-representative-blockers.json").read_text()
    )
    center = record["joints"]["center_header"]
    assert "center-y-stagger.json" in center["fixed_support_row_screen"]
    assert "center-access.json" in center["nominal_access_screen"]
    assert center["capacity_claim"] is False
