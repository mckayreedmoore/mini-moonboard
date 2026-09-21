"""PB02 refinement evidence produces one bounded development decision."""

import copy
import hashlib
import json
import shutil

import pytest

from scripts import simple_center_pb02_refinement_decision as decision


def test_refinement_and_density_evidence_are_authenticated_and_bounded():
    result = decision.screen()

    assert set(result["authentication"]) == {
        "grid_2x2",
        "grid_4x4",
        "grid_8x8",
        "density_0p5x",
        "density_2x",
    }
    assert result["source_snapshot_authentication"] == {
        "path": "source_snapshots",
        "file_count": 278,
        "source_sha256_map_identical_across_reports": True,
        "all_snapshot_hashes_match": True,
    }
    refinement = result["grid_refinement_4x4_to_8x8"]
    assert refinement["maximum_force_change_percent"] == pytest.approx(
        3.008075895613427
    )
    assert refinement["maximum_moment_change_percent"] == pytest.approx(
        5.616425553541626
    )
    assert refinement["panel_displacement_change_percent"] == pytest.approx(
        0.0002846069631745607
    )
    assert refinement["maximum_bolt_combined_force_change_percent"] == pytest.approx(
        0.8191841896050933
    )
    assert refinement["governing_bolt_grid_4x4"]["name"] == (
        "principal_block_principal/bolt_1"
    )
    assert refinement["governing_bolt_grid_8x8"]["name"] == (
        "principal_block_principal/bolt_1"
    )
    assert refinement["maximum_active_area_change_percent"] > 8
    assert refinement["maximum_peak_cell_average_pressure_change_percent"] > 20
    assert refinement["selected_force_moment_resolution"] == "8x8"
    assert refinement["local_pressure_qualified"] is False

    density = result["contact_density_sensitivity_8x8"]
    assert density["maximum_force_ratio"] == pytest.approx(2.1709384552729065)
    assert density["maximum_moment_ratio"] == pytest.approx(2.392028216656416)
    assert density["governing_bolt_combined_force_ratio"] == pytest.approx(
        1.1391976155276395
    )
    assert density["panel_displacement_ratio"] == pytest.approx(1.000152465468062)
    assert density["stiffness_qualified"] is False

    assert result["decision"] == "RETAIN_PB02_FOR_DEVELOPMENT_WITH_REVISION"
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def _mutated_evidence(tmp_path, monkeypatch, name, mutate):
    reports = copy.deepcopy(decision.REPORTS)
    for report_name, (relative, digest) in reports.items():
        reports[report_name] = (str(decision.EVIDENCE / relative), digest)
    relative, _ = decision.REPORTS[name]
    source = decision.EVIDENCE / relative
    report = json.loads(source.read_text())
    mutate(report)
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report))
    final_cycle = report["contact_cycles"][-1]["directory"]
    for filename in decision.RETAINED_FINAL_FILES:
        artifact_source = source.parent / final_cycle / filename
        artifact_target = target.parent / final_cycle / filename
        artifact_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact_source, artifact_target)
    reports[name] = (str(target), hashlib.sha256(target.read_bytes()).hexdigest())
    monkeypatch.setattr(decision, "REPORTS", reports)


@pytest.mark.parametrize(
    ("name", "mutate"),
    [
        ("grid_4x4", lambda report: report["diagnostic_scope"].update(case="a12-rear")),
        (
            "grid_4x4",
            lambda report: report["diagnostic_scope"]["stiffness_selection"][
                "contact_model"
            ].update(grid_resolution=[8, 8]),
        ),
        (
            "density_0p5x",
            lambda report: report["diagnostic_scope"]["stiffness_selection"][
                "exact_selected_values"
            ].update(face_normal_total_per_interface_n_per_mm=1000.0),
        ),
        (
            "density_0p5x",
            lambda report: report["diagnostic_scope"]["stiffness_selection"][
                "exact_selected_values"
            ].update(floor_contact_n_per_mm=100000.0),
        ),
        (
            "grid_8x8",
            lambda report: report["parameters"].update(
                force_xyz_n=[0.0, -299.0, -2224.11080763025]
            ),
        ),
        (
            "density_2x",
            lambda report: report["diagnostic_scope"].update(
                candidate="other-candidate"
            ),
        ),
        ("density_2x", lambda report: report.update(pb02_model_identity="changed")),
        ("density_2x", lambda report: report.update(numerically_accepted=False)),
        ("density_2x", lambda report: report.update(drilling_released=True)),
        (
            "density_2x",
            lambda report: report["source_sha256"].update(
                {decision.GEOMETRY_SOURCE: "changed"}
            ),
        ),
    ],
)
def test_refinement_authentication_fails_closed(tmp_path, monkeypatch, name, mutate):
    _mutated_evidence(tmp_path, monkeypatch, name, mutate)

    with pytest.raises(ValueError, match="changed"):
        decision.screen()


def test_refinement_authentication_rejects_changed_common_snapshot(
    tmp_path, monkeypatch
):
    snapshots = tmp_path / "source_snapshots"
    shutil.copytree(decision.SOURCE_SNAPSHOTS, snapshots)
    target = snapshots / decision.GEOMETRY_SOURCE
    target.write_text(target.read_text() + "\n# changed\n")
    monkeypatch.setattr(decision, "SOURCE_SNAPSHOTS", snapshots)

    with pytest.raises(ValueError, match="source snapshot closure changed"):
        decision.screen()


def test_refinement_authentication_ignores_python_cache_only(tmp_path, monkeypatch):
    snapshots = tmp_path / "source_snapshots"
    shutil.copytree(decision.SOURCE_SNAPSHOTS, snapshots)
    cache = snapshots / "scripts/__pycache__/geometry.cpython-312.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"transient bytecode")
    monkeypatch.setattr(decision, "SOURCE_SNAPSHOTS", snapshots)
    reports = {
        name: json.loads((decision.EVIDENCE / relative).read_text())
        for name, (relative, _) in decision.REPORTS.items()
    }
    monkeypatch.setattr(decision, "EVIDENCE", tmp_path)

    assert decision._authenticate_source_snapshots(reports)["file_count"] == 278

    unlisted = snapshots / "scripts/unlisted.py"
    unlisted.write_text("pass\n")
    with pytest.raises(ValueError, match="extra=\\['scripts/unlisted.py'\\]"):
        decision._authenticate_source_snapshots(reports)

    unlisted.unlink()
    (snapshots / decision.GEOMETRY_SOURCE).unlink()
    with pytest.raises(
        ValueError, match="missing=\\['scripts/simple_center_pb02_geometry.py'\\]"
    ):
        decision._authenticate_source_snapshots(reports)
