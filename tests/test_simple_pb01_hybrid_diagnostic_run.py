"""The PB-01 hybrid run carries its provisional scope and producer identity."""

import pytest

from scripts import simple_pb01_hybrid_diagnostic_run as runner


def test_producer_inventory_includes_adapter_pose_and_runner():
    names = runner.LOADED_PRODUCER_SHA256
    assert "scripts/simple_pb01_hybrid_native.py" in names
    assert "scripts/simple_pb01_hybrid_diagnostic_run.py" in names
    assert "scripts/simple_rail_joint_comparison.py" in names
    assert "docs/bolted-candidate-prototypes/simple_rail_joint_comparison.json" in names
    assert runner.native.extra_source_hashes(runner.PRODUCER_PATHS) == names


def test_changed_hybrid_producer_is_rejected_before_native_run(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "LOADED_PRODUCER_SHA256", {"stale": "digest"})
    with pytest.raises(ValueError, match="changed after import"):
        runner.run_case("a12-left", tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()


def test_quarter_runner_has_distinct_candidate_and_diagnostic_scope(
    tmp_path, monkeypatch
):
    seen = {}

    def fake_run(output, **kwargs):
        seen.update(kwargs)
        output.mkdir()
        return {"artifact_sha256": {}, "numerically_accepted": True}

    monkeypatch.setattr(runner.native, "run", fake_run)
    outcome = runner.run_case("a12-left", tmp_path / "quarter", variant="quarter")
    assert seen["module"].KEY == seen["expected_candidate"]
    assert "quarter" in seen["expected_candidate"]
    assert outcome["diagnostic_scope"]["pb01_pose_variant"] == "quarter"
    assert outcome["diagnostic_scope"]["pb01_nominal_trial_bolt_diameter_mm"] == 6.35
    assert outcome["diagnostic_scope"]["bore_diameter_changes_mesh"] is False
    assert (
        "trial_stack_mass_only"
        in outcome["diagnostic_scope"]["variant_native_difference"]
    )
    assert outcome["diagnostic_scope"]["v4_same_case_demand"] is False
