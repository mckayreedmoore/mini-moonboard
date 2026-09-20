"""The PB-01 hybrid run carries its provisional scope and producer identity."""

import pytest

from scripts import simple_pb01_hybrid_diagnostic_run as runner


def test_producer_inventory_includes_adapter_pose_and_runner():
    names = runner.LOADED_PRODUCER_SHA256
    assert "scripts/simple_pb01_hybrid_native.py" in names
    assert "scripts/simple_pb01_hybrid_diagnostic_run.py" in names
    assert "docs/bolted-candidate-prototypes/simple_rail_joint_comparison.json" in names
    assert runner.native.extra_source_hashes(runner.PRODUCER_PATHS) == names


def test_changed_hybrid_producer_is_rejected_before_native_run(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "LOADED_PRODUCER_SHA256", {"stale": "digest"})
    with pytest.raises(ValueError, match="changed after import"):
        runner.run_case("a12-left", tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()
