"""Producer stiffness overrides remain explicit in native inputs and scope."""

import json

import pytest

from scripts import bolted_center_native_diagnostic as runner


def test_one_independent_stiffness_changes_only_its_joint_input(tmp_path, monkeypatch):
    seen = []

    def fake_run(output, **kwargs):
        output.mkdir()
        seen.append(kwargs)
        return {"numerically_accepted": False, "artifact_sha256": {}}

    monkeypatch.setattr(runner.native, "run", fake_run)
    monkeypatch.setattr(runner, "_sources", lambda: runner.LOADED_SOURCES)
    monkeypatch.setattr(runner.probe, "DiagnosticCenterBolted", lambda: type("Module", (), {
        "KEY": "test-candidate", "raw": type("Raw", (), {"KEY": "test-geometry"})(),
        "connections": lambda self: [type("Bolt", (), {"name": "retained", "kind": "bolt"})()],
    })())
    monkeypatch.setattr(runner.bolted_center_joint_model, "shared_center_joint",
                        lambda module, **kwargs: kwargs)
    monkeypatch.setattr(runner, "bolt_properties", lambda connection: {
        "basis": "test", "axial_n_per_mm": 1., "lateral_n_per_mm": 1.,
    })
    monkeypatch.setattr(runner, "face_contacts", lambda module: [])
    monkeypatch.setattr(runner, "taper_top_monitors", lambda module: [])
    baseline = runner.run_case("a1-rear", tmp_path / "baseline", spring_n_per_mm=10000.)
    varied = runner.run_case(
        "a1-rear", tmp_path / "varied", spring_n_per_mm=10000.,
        header_bore_total_lateral_n_per_mm=30000.,
    )

    original = seen[0]["diagnostic_center_joint"]
    changed = seen[1]["diagnostic_center_joint"]
    assert {key for key in original if original[key] != changed[key]} == {
        "wood_bearing_lateral_n_per_mm"
    }
    assert original["wood_bearing_lateral_n_per_mm"] == 10000.
    assert changed["wood_bearing_lateral_n_per_mm"] == 15000.
    assert original["vertical_spring"] == original["steel_bolt_spring"] == {
        "axial_n_per_mm": 10000., "lateral_n_per_mm": 10000.,
    }
    assert original["flange_contact_n_per_mm"] == 10000.
    assert seen[0]["dynamic_factor"] == seen[1]["dynamic_factor"] == 2.0
    assert baseline["dynamic_factor"] == varied["dynamic_factor"] == 2.0
    assert baseline["header_bore_total_lateral_n_per_mm"] == 20000.
    assert varied["header_bore_total_lateral_n_per_mm"] == 30000.
    assert all(varied[name] == 10000. for name in (
        "vertical_bolt_axial_n_per_mm", "vertical_bolt_lateral_n_per_mm",
        "steel_to_bolt_axial_n_per_mm", "steel_to_bolt_lateral_n_per_mm",
        "flange_contact_n_per_mm",
    ))
    assert json.loads((tmp_path / "varied" / "diagnostic-scope.json").read_text()) == {
        key: value for key, value in varied.items() if key != "native_report"
    }
    assert varied["native_report"]["diagnostic_scope"]["header_bore_total_lateral_n_per_mm"] == 30000.


@pytest.mark.parametrize("name", [
    "vertical_bolt_axial_n_per_mm", "vertical_bolt_lateral_n_per_mm",
    "steel_to_bolt_axial_n_per_mm", "steel_to_bolt_lateral_n_per_mm",
    "header_bore_total_lateral_n_per_mm", "flange_contact_n_per_mm",
])
@pytest.mark.parametrize("invalid", [0., -1., float("nan"), float("inf"), 1e13, True])
def test_invalid_independent_stiffness_rejected_before_native_run(
    tmp_path, monkeypatch, name, invalid
):
    monkeypatch.setattr(runner.native, "run", lambda *args, **kwargs: pytest.fail("native run"))
    with pytest.raises(ValueError, match="finite positive"):
        runner.run_case(
            "a1-rear", tmp_path / "invalid", spring_n_per_mm=10000.,
            **{name: invalid},
        )
