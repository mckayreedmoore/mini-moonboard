"""The native diagnostic runner cannot silently become an acceptance producer."""

import json

import pytest

from scripts import bolted_kerf_diagnostic_probe as probe
from scripts import bolted_kerf_native_diagnostic as runner


def test_runner_uses_kerf_preparation_and_records_diagnostic_scope(tmp_path, monkeypatch):
    seen = {}

    def fake_run(output, **kwargs):
        output.mkdir()
        seen.update(kwargs)
        return {"candidate": kwargs["expected_candidate"], "numerically_accepted": False}

    monkeypatch.setattr(runner.native, "run", fake_run)
    monkeypatch.setattr(runner, "face_contacts", lambda module, **kwargs: [])
    monkeypatch.setattr(runner, "taper_top_monitors", lambda module: [])
    monkeypatch.setattr(runner, "bolt_properties", lambda connection: {
        "basis": "test only", "axial_n_per_mm": 1., "lateral_n_per_mm": 1.,
    })
    output = tmp_path / "diagnostic"
    result = runner.run_case("a12-rear", output)
    assert seen["prepare_factory"] is probe.prepare_diagnostic
    assert seen["expected_candidate"] == probe.DiagnosticProxy.KEY
    assert seen["module"].raw.KEY.endswith("kerf-right")
    assert seen["pounds"] == 250.
    scope = json.loads((output / "diagnostic-scope.json").read_text())
    assert scope["connector_proxy"] == "baseline ML24Z angles and SDS screws"
    assert scope["bolted_joint_demands"] is False
    assert scope["acceptance"] is False
    assert scope["drilling_released"] is False
    assert result["native_report"]["numerically_accepted"] is False


def test_runner_rejects_noncase_before_creating_output(tmp_path):
    output = tmp_path / "diagnostic"
    with pytest.raises(ValueError, match="Unknown unchanged load case"):
        runner.run_case("not-a-case", output)
    assert not output.exists()
