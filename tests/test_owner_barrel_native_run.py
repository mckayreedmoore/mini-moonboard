"""Candidate-only wrapper for integrated barrel native diagnostics."""

import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import owner_barrel_native_run as runner


class FakeModule:
    KEY = "owner-barrel-test-candidate"
    barrel_bolt_names = frozenset(f"barrel-{index:02d}" for index in range(46))


def _prepared_case(case, **kwargs):
    hold, horizontal = runner.CASE_LOADS[case]
    structure = SimpleNamespace(
        springs=[
            {"name": name, "tension_only_assumption": True}
            for name in FakeModule.barrel_bolt_names
        ]
    )
    contacts = [
        {"name": f"contact-{index:03d}"}
        for index in range(runner.EXPECTED_CONTACT_CELLS)
    ]
    force_names = [*FakeModule.barrel_bolt_names, *(f"other-{index:03d}" for index in range(78))]
    radial_names = {
        f"{name}__radial_clearance" for name in FakeModule.barrel_bolt_names
    }
    metadata = {
        "candidate": FakeModule.KEY,
        "hold": hold,
        "pounds": 250.0,
        "force_xyz_n": [*horizontal, runner.EXPECTED_VERTICAL_FORCE_N],
        "angle_stations": [],
        "connection_ownership": {name: {} for name in force_names},
        "radial_clearance_ownership": {name: {} for name in radial_names},
        "member_contacts": contacts,
        "acceptance": False,
    }
    summary = {
        "barrel_pairs": 46,
        "retained_bolts": 12,
        "panel_screws": 66,
        "face_contact_cells": runner.EXPECTED_BARREL_CONTACT_CELLS,
        "retained_face_contact_cells": runner.EXPECTED_RETAINED_CONTACT_CELLS,
        "structural_released": False,
    }
    return structure, metadata, summary


def _mock_native(monkeypatch, seen, mutate=None):
    monkeypatch.setattr(runner, "IntegratedBarrelNative", FakeModule)

    def fake_run(output, **kwargs):
        seen.update(kwargs)
        Path(output).mkdir()
        structure, metadata = kwargs["prepare_factory"]()
        radial_names = sorted(metadata["radial_clearance_ownership"])
        supplied_radial = kwargs.get("initial_radial_clearance_states")
        initial_radial = (
            {name: None for name in radial_names}
            if supplied_radial is None
            else copy.deepcopy(supplied_radial)
        )
        report = {
            "candidate": kwargs["expected_candidate"],
            "source_sha256": dict(runner.LOADED_PRODUCER_SHA256),
            "artifact_sha256": {},
            "parameters": {
                key: metadata[key] for key in ("hold", "pounds", "force_xyz_n")
            },
            "angle_stations": [],
            "axial_tension_names": sorted(
                spring["name"]
                for spring in structure.springs
                if spring.get("tension_only_assumption")
            ),
            "physical_connection_forces": {
                name: {"force_on_first_xyz_n": [0.0, 0.0, 0.0]}
                for name in metadata["connection_ownership"]
            },
            "member_contacts": copy.deepcopy(metadata["member_contacts"]),
            "initial_radial_clearance_states": initial_radial,
            "radial_clearance_states": {
                name: None for name in metadata["radial_clearance_ownership"]
            },
            "radial_clearance_names": radial_names,
            "axial_tension_assumption_passed": True,
            "radial_clearance_assumption_passed": True,
            **{name: True for name in runner.REQUIRED_NUMERICAL_AUDITS},
            "numerically_accepted": True,
        }
        if mutate is not None:
            mutate(report)
        return report

    monkeypatch.setattr(runner.native, "run", fake_run)


def test_source_inventory_includes_runner_preparation_and_current_dependencies():
    names = runner.LOADED_PRODUCER_SHA256
    assert "scripts/owner_barrel_native_run.py" in names
    assert "scripts/owner_barrel_native_preparation.py" in names
    assert "scripts/export_owner_barrel_scene.py" in names
    assert "fea/current_response_run.py" in names
    assert "docs/floor-flush-construction/connection-axes.csv" in names
    assert "docs/floor-flush-construction-kerf-right/connection-axes.csv" in names
    assert "docs/floor-flush-construction-kerf-right/stock-profiles.json" in names
    assert runner.native.extra_source_hashes(runner.PRODUCER_PATHS) == names


def test_run_binds_candidate_stiffnesses_active_sets_and_scope(
    tmp_path, monkeypatch
):
    seen = {}
    prepared = {}
    _mock_native(monkeypatch, seen)

    def fake_prepare(case, **kwargs):
        prepared.update(case=case, **kwargs)
        return _prepared_case(case, **kwargs)

    monkeypatch.setattr(runner, "prepare_case", fake_prepare)
    output = tmp_path / "a12-rear"
    report = runner.run_case(
        "a12-rear",
        output,
        barrel_axial_n_per_mm=1100.0,
        barrel_lateral_n_per_mm=550.0,
        contact_n_per_mm3=90.0,
        max_cycles=17,
        contact_update_strategy="one_at_a_time",
        initial_contact_names=["contact-b", "contact-a"],
        initial_axial_tension_names=["barrel-bolt"],
    )

    assert seen["module"].KEY == seen["expected_candidate"] == FakeModule.KEY
    assert seen["max_cycles"] == 17
    assert seen["contact_update_strategy"] == "one_at_a_time"
    assert seen["initial_contact_names"] == ["contact-b", "contact-a"]
    assert seen["initial_axial_tension_names"] == ["barrel-bolt"]
    assert seen["initial_radial_clearance_states"] is None
    assert set(seen["extra_source_paths"]) == set(runner.PRODUCER_PATHS)
    assert prepared == {
        "case": "a12-rear",
        "module": seen["module"],
        "barrel_axial_n_per_mm": 1100.0,
        "barrel_lateral_n_per_mm": 550.0,
        "contact_n_per_mm3": 90.0,
    }
    scope = report["owner_barrel_diagnostic_scope"]
    assert scope["case_load"] == {
        "hold": "A12",
        "horizontal_force_xy_n": [0.0, 300.0],
        "applied_force_xyz_n": [0.0, 300.0, runner.EXPECTED_VERTICAL_FORCE_N],
        "pounds": 250.0,
    }
    assert scope["initial_contact_names"] == ["contact-a", "contact-b"]
    assert scope["tension_only_barrel_axial_springs"] is True
    assert scope["compression_only_face_contacts"] is True
    assert scope["conditional_only"] is True
    assert scope["joint_resistance_qualified"] is False
    assert all(scope[flag] is False for flag in runner.RELEASE_FLAGS)
    assert report["qualified_for_design"] is False
    assert report["acceptance"] is False
    assert report["structural_released"] is False
    assert report["owner_barrel_wrapper_accepted"] is True
    assert report["retry_checkpoint_eligible"] is False
    assert (output / "diagnostic-scope.json").is_file()
    assert (output / "report.json").is_file()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda report: report["parameters"].update(hold="K12"),
            "load identity",
        ),
        (lambda report: report["angle_stations"].append("legacy"), "angle stations"),
        (
            lambda report: report["axial_tension_names"].pop(),
            "axial spring inventory",
        ),
        (
            lambda report: report["physical_connection_forces"].popitem(),
            "physical-force row inventory",
        ),
        (
            lambda report: report["member_contacts"].pop(),
            "member-contact row inventory",
        ),
        (
            lambda report: report["radial_clearance_states"].popitem(),
            "radial-clearance state inventory",
        ),
        (
            lambda report: report.update(contact_active_set_converged=False),
            "did not converge",
        ),
        (
            lambda report: report.update(fabrication_released=True),
            "release flag",
        ),
    ],
)
def test_report_identity_failures_are_retained_as_rejected(
    tmp_path, monkeypatch, mutate, message
):
    seen = {}
    _mock_native(monkeypatch, seen, mutate)
    monkeypatch.setattr(runner, "prepare_case", _prepared_case)
    output = tmp_path / message.replace(" ", "-")

    with pytest.raises(ValueError, match=message):
        runner.run_case(
            "a12-rear",
            output,
            barrel_axial_n_per_mm=1000.0,
            barrel_lateral_n_per_mm=500.0,
            contact_n_per_mm3=100.0,
        )

    retained = runner.json.loads((output / "report.json").read_text())
    assert retained["numerically_accepted"] is False
    assert retained["owner_barrel_wrapper_accepted"] is False
    assert retained["owner_barrel_validation_error"]
    assert all(retained[flag] is False for flag in runner.RELEASE_FLAGS)
    assert not (output / "diagnostic-scope.json").exists()


def test_opt_in_returns_authenticated_nonconvergence_for_retry_only(
    tmp_path, monkeypatch
):
    seen = {}

    def nonconverged(report):
        report["contact_active_set_converged"] = False
        report["closed_bearing_assumption_passed"] = False
        report["numerically_accepted"] = False

    _mock_native(monkeypatch, seen, nonconverged)
    monkeypatch.setattr(runner, "prepare_case", _prepared_case)
    names = sorted(
        f"{name}__radial_clearance" for name in FakeModule.barrel_bolt_names
    )
    initial_radial = {
        name: ([1.0, 0.0] if index == 0 else None)
        for index, name in enumerate(names)
    }
    output = tmp_path / "retry"

    report = runner.run_case(
        "a12-rear",
        output,
        barrel_axial_n_per_mm=1000.0,
        barrel_lateral_n_per_mm=500.0,
        contact_n_per_mm3=100.0,
        initial_radial_clearance_states=initial_radial,
        allow_retry_checkpoint=True,
    )

    assert seen["initial_radial_clearance_states"] is initial_radial
    assert report["native_numerically_accepted"] is False
    assert report["numerically_accepted"] is False
    assert report["owner_barrel_wrapper_accepted"] is False
    assert report["retry_checkpoint_eligible"] is True
    assert all(report[flag] is False for flag in runner.RELEASE_FLAGS)
    scope = report["owner_barrel_diagnostic_scope"]
    assert scope["rejected_for_acceptance"] is True
    assert scope["retry_checkpoint_only"] is True
    assert scope["conditional_only"] is True
    assert scope["initial_radial_clearance_states"] == initial_radial
    assert all(scope[flag] is False for flag in runner.RELEASE_FLAGS)
    assert (output / "diagnostic-scope.json").is_file()


def test_opt_in_does_not_allow_identity_failure(tmp_path, monkeypatch):
    seen = {}

    def wrong_identity_and_nonconverged(report):
        report["parameters"]["pounds"] = 249.0
        report["contact_active_set_converged"] = False
        report["numerically_accepted"] = False

    _mock_native(monkeypatch, seen, wrong_identity_and_nonconverged)
    monkeypatch.setattr(runner, "prepare_case", _prepared_case)
    output = tmp_path / "rejected"

    with pytest.raises(ValueError, match="load identity"):
        runner.run_case(
            "a12-rear",
            output,
            barrel_axial_n_per_mm=1000.0,
            barrel_lateral_n_per_mm=500.0,
            contact_n_per_mm3=100.0,
            allow_retry_checkpoint=True,
        )

    retained = runner.json.loads((output / "report.json").read_text())
    assert retained["owner_barrel_wrapper_accepted"] is False
    assert retained.get("retry_checkpoint_eligible") is not True
    assert not (output / "diagnostic-scope.json").exists()


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"case": "not-a-case"}, "six-case load inventory"),
        ({"barrel_axial_n_per_mm": 0.0}, "positive and finite"),
        ({"barrel_lateral_n_per_mm": float("inf")}, "positive and finite"),
        ({"contact_n_per_mm3": float("nan")}, "positive and finite"),
        ({"max_cycles": 0}, "positive integer"),
        ({"contact_update_strategy": "guess"}, "Unknown contact"),
    ],
)
def test_invalid_controls_stop_before_native_run(tmp_path, monkeypatch, changes, message):
    called = False

    def fake_run(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(runner.native, "run", fake_run)
    values = {
        "case": "a12-forward",
        "output": tmp_path / "never-created",
        "barrel_axial_n_per_mm": 1000.0,
        "barrel_lateral_n_per_mm": 500.0,
        "contact_n_per_mm3": 100.0,
    }
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        runner.run_case(**values)
    assert called is False
    assert not values["output"].exists()


def test_changed_producer_stops_before_native_run(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "LOADED_PRODUCER_SHA256", {"stale": "digest"})
    monkeypatch.setattr(
        runner.native,
        "run",
        lambda *_args, **_kwargs: pytest.fail("native run should not start"),
    )
    with pytest.raises(ValueError, match="changed after import"):
        runner.run_case(
            "a1-rear",
            tmp_path / "never-created",
            barrel_axial_n_per_mm=1000.0,
            barrel_lateral_n_per_mm=500.0,
            contact_n_per_mm3=100.0,
        )


@pytest.mark.parametrize(
    ("candidate", "sources", "message"),
    [
        ("wrong", {}, "candidate identity"),
        (FakeModule.KEY, {}, "authenticate barrel producer sources"),
    ],
)
def test_report_must_authenticate_candidate_and_sources(
    tmp_path, monkeypatch, candidate, sources, message
):
    monkeypatch.setattr(runner, "IntegratedBarrelNative", FakeModule)

    def fake_run(output, **_kwargs):
        Path(output).mkdir()
        return {
            "candidate": candidate,
            "source_sha256": sources,
            "artifact_sha256": {},
        }

    monkeypatch.setattr(runner.native, "run", fake_run)
    with pytest.raises(ValueError, match=message):
        runner.run_case(
            "k12-right",
            tmp_path / message.replace(" ", "-"),
            barrel_axial_n_per_mm=1000.0,
            barrel_lateral_n_per_mm=500.0,
            contact_n_per_mm3=100.0,
        )
