"""The PB-01 hybrid run carries its provisional scope and producer identity."""

from scripts import simple_pb01_hybrid_diagnostic_run as runner


def test_producer_inventory_includes_adapter_pose_and_runner():
    names = runner.LOADED_PRODUCER_SHA256
    assert "scripts/simple_pb01_hybrid_native.py" in names
    assert "scripts/simple_pb01_hybrid_diagnostic_run.py" in names
    assert "docs/bolted-candidate-prototypes/simple_rail_joint_comparison.json" in names
    assert runner.native.extra_source_hashes(runner.PRODUCER_PATHS) == names
