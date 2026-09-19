"""The native diagnostic runner cannot silently become an acceptance producer."""

import hashlib
import json

import pytest

from scripts import bolted_kerf_diagnostic_probe as probe
from scripts import bolted_kerf_native_diagnostic as runner


def test_runner_uses_kerf_preparation_and_records_diagnostic_scope(tmp_path, monkeypatch):
    seen = {}

    def fake_run(output, **kwargs):
        output.mkdir()
        seen.update(kwargs)
        return {"candidate": kwargs["expected_candidate"], "numerically_accepted": False,
                "artifact_sha256": {}}

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
    assert seen["contact_update_strategy"] == "all"
    scope = json.loads((output / "diagnostic-scope.json").read_text())
    assert scope["connector_proxy"] == "baseline ML24Z angles and SDS screws"
    assert scope["bolted_joint_demands"] is False
    assert scope["acceptance"] is False
    assert scope["drilling_released"] is False
    assert scope["numerically_converged"] is False
    assert result["native_report"]["numerically_accepted"] is False
    assert result["native_report"]["diagnostic_scope"] == scope
    assert result["native_report"]["artifact_sha256"]["diagnostic-scope.json"] == hashlib.sha256(
        (output / "diagnostic-scope.json").read_bytes()).hexdigest()
    assert json.loads((output / "report.json").read_text())["diagnostic_scope"] == scope


def test_runner_rejects_noncase_before_creating_output(tmp_path):
    output = tmp_path / "diagnostic"
    with pytest.raises(ValueError, match="Unknown unchanged load case"):
        runner.run_case("not-a-case", output)
    assert not output.exists()


def test_search_seed_requires_accepted_same_source_and_proxy(tmp_path):
    path = tmp_path / "seed.json"
    report = {
        "candidate": probe.DiagnosticProxy.KEY,
        "numerically_accepted": True,
        "diagnostic_scope": {
            "source_geometry": "compact-floor-flush-bolted-development-kerf-right",
            "connector_proxy": "baseline ML24Z angles and SDS screws",
            "connection_scale": 1.,
            "contact_stiffness_per_area_n_per_mm3": 100.,
        },
        "source_sha256": runner._sources(),
        "bearings": [{"name": "normal", "active": True},
                     {"name": "inactive", "active": False},
                     {"name": "normal_friction", "active": True}],
    }
    path.write_text(json.dumps(report))
    names, digest = runner._seed_contacts(path, probe.DiagnosticProxy.KEY, 1., 100.)
    assert names == ["normal"]
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    report["source_sha256"]["scripts/clear_space_batch.py"] = "changed"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="source changed"):
        runner._seed_contacts(path, probe.DiagnosticProxy.KEY, 1., 100.)
