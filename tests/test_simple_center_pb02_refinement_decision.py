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
        3.286506168568004
    )
    assert refinement["maximum_moment_change_percent"] == pytest.approx(
        8.185850827401907
    )
    assert refinement["panel_displacement_change_percent"] == pytest.approx(
        0.00024177338442399332
    )
    assert refinement["maximum_bolt_combined_force_change_percent"] == pytest.approx(
        0.6973226663759324
    )
    assert refinement["governing_bolt_grid_4x4"]["name"] == ("rear_block_post/bolt_2")
    assert refinement["governing_bolt_grid_8x8"]["name"] == ("rear_block_post/bolt_2")
    assert refinement["maximum_active_area_change_percent"] > 40
    assert refinement["maximum_peak_cell_average_pressure_change_percent"] > 20
    assert refinement["selected_force_moment_resolution"] == "8x8"
    assert refinement["local_pressure_qualified"] is False

    density = result["contact_density_sensitivity_8x8"]
    assert density["maximum_force_ratio"] == pytest.approx(1.737700021562633)
    assert density["maximum_moment_ratio"] == pytest.approx(5.082957715910369)
    assert density["governing_bolt_combined_force_ratio"] == pytest.approx(
        1.6494146902645872
    )
    assert density["panel_displacement_ratio"] == pytest.approx(1.0001764021567496)
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
        ("density_2x", lambda report: report.update(candidate="other-candidate")),
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
