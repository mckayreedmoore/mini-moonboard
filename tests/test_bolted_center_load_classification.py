"""Classifier unit tests independent of ignored native diagnostic artifacts."""

import json
from pathlib import Path

import pytest

import scripts.bolted_center_load_classification as classifier

RAW = Path(__file__).resolve().parents[1] / "fea/results/diagnostics/kerf-right-center"


@pytest.fixture(autouse=True)
def raw_reports_unavailable(monkeypatch):
    """Exercise the core suite as if local native results were absent."""
    original_bytes = Path.read_bytes
    original_text = Path.read_text

    def read_bytes(path):
        if path.is_relative_to(RAW):
            raise FileNotFoundError(path)
        return original_bytes(path)

    def read_text(path, *args, **kwargs):
        if path.is_relative_to(RAW):
            raise FileNotFoundError(path)
        return original_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(Path, "read_text", read_text)


def _run(root, stiffness, upper_force):
    root.mkdir()
    (root / "cycle-00").mkdir()
    members = [
        {"name": name, "start": [0, 0, start], "end": [0, 0, end],
         "axis": [0, 0, 1], "section_u": [1, 0, 0]}
        for name, start, end in (
            ("base_principal_center_left", 0, 10),
            ("base_post_center_left", -10, 0),
        )
    ]
    members.append({"name": "base_header", "start": [-10, 0, 0],
                    "end": [10, 0, 0], "axis": [1, 0, 0],
                    "section_u": [0, 1, 0]})
    angles = [
        {"name": "upper", "wood_member": "base_principal_center_left",
         "vertical_points": [[0, 0, 1], [0, 0, 2]]},
        {"name": "lower", "wood_member": "base_post_center_left",
         "vertical_points": [[0, 0, -1], [0, 0, -2]]},
    ]
    bolts = [
        {"name": f"bolt_{i}", "top_point": [i, 0, 1],
         "bottom_point": [i, 0, -1], "wood_upper_point": [i, 0, 0.5],
         "wood_lower_point": [i, 0, -0.5]}
        for i in (1, 2)
    ]
    owners, physical, springs = {}, {}, []
    extracted = {"angles": {}, "shared_bolts": {}}

    def add(name, wood, other, point, axis, force, dofs):
        owners[name] = {"first": wood, "second": other, "point": point,
                        "axis": axis}
        physical[name] = {"first": wood, "second": other, "point": point,
                          "force_on_first_xyz_n": force,
                          "force_on_second_xyz_n": [-value for value in force]}
        springs.extend({"name": name, "dof": dof} for dof in dofs)

    for angle in angles:
        name, wood = angle["name"], angle["wood_member"]
        names = []
        for i, point in enumerate(angle["vertical_points"]):
            branch = f"{name}_wood_{i}"
            add(branch, wood, name, point, [1, 0, 0],
                upper_force if name == "upper" else [0, 1, 1], [1, 2, 3])
            names.append(branch)
        extracted["angles"][name] = {"branch_names": {"wood": names}}
    for bolt in bolts:
        names = []
        for side in ("upper", "lower"):
            branch = f"{bolt['name']}_bore_{side}"
            add(branch, "base_header", bolt["name"],
                bolt[f"wood_{side}_point"], [0, 0, 1], [1, 2, 0], [1, 2])
            names.append(branch)
        extracted["shared_bolts"][bolt["name"]] = {
            "branches": {"middle_wood": {"connection_names": names}}}
    record = {"members": members, "connection_ownership": owners,
              "springs": springs,
              "diagnostic_center_joint": {"angles": angles,
                                          "shared_header_bolts": bolts,
                                          "wood_bearing_lateral_n_per_mm": stiffness}}
    report = {"contact_cycles": [{"directory": "cycle-00"}],
              "physical_connection_forces": physical}
    path = root / "report.json"
    path.write_text(json.dumps(report))
    (root / "cycle-00/input.json").write_text(json.dumps(record))
    extracted["source"] = {"case": "a1-rear", "report_sha256": str(stiffness),
                           "record_sha256": str(stiffness),
                           "producer_sha256": {"joint": "same-source"}}
    return path, extracted


def test_grain_rotation_zero_lateral_and_oblique_rejection():
    result = classifier.classify_force([0, 3, 4], [1, 0, 0], [0, 0, 1])
    assert result["lateral_force_xyz_n"] == pytest.approx([0, 3, 4])
    assert result["parallel_to_grain_n"] == pytest.approx(4)
    assert result["perpendicular_to_grain_n"] == pytest.approx(3)
    rotated = classifier.classify_force([0, 3, 4], [1, 0, 0], [0, 1, 0])
    assert rotated["parallel_to_grain_n"] == pytest.approx(3)
    assert rotated["perpendicular_to_grain_n"] == pytest.approx(4)
    axial = classifier.classify_force([5, 0, 0], [1, 0, 0], [0, 0, 1])
    assert axial["axial_force_along_bolt_n"] == pytest.approx(5)
    assert axial["lateral_force_xyz_n"] == pytest.approx([0, 0, 0])
    assert axial["direction_class"] == "zero_lateral"
    with pytest.raises(ValueError, match="perpendicular to bolt"):
        classifier.classify_force([0, 3, 4], [1, 0, 0], [0.6, 0, 0.8])


def test_synthetic_inventory_and_reversal(tmp_path, monkeypatch):
    fixtures = [_run(tmp_path / str(stiffness), stiffness, force)
                for stiffness, force in ((1000, [0, 0, 4]),
                                         (10000, [0, 4, 0]),
                                         (100000, [0, 5, 0]))]
    authenticated = dict(fixtures)
    monkeypatch.setattr(classifier, "extract_files",
                        lambda path, record=None: authenticated[Path(path)])
    paths = [path for path, _ in fixtures]
    result = classifier.classify_files(paths[0])
    assert set(result["vertical_ab205"]) == {"upper", "lower"}
    assert set(result["shared_header_bores"]) == {"bolt_1", "bolt_2"}
    assert all(len(row["branches"]) == 2 for row in result["vertical_ab205"].values())
    assert all(len(row["branches"]) == 2 for row in result["shared_header_bores"].values())
    assert result["vertical_ab205"]["upper"]["branches"][0]["parallel_to_grain_n"] == 4
    comparison = classifier.compare_stiffness_runs(paths)
    assert comparison["any_observed_reversal"] is True
    assert comparison["reversal_by_branch"]["upper_wood_0"] is True
    assert comparison["reversal_by_branch"]["lower_wood_0"] is False
    assert comparison["source"]["case"] == "a1-rear"
    with pytest.raises(ValueError, match="three distinct"):
        classifier.compare_stiffness_runs([paths[0]] * 3)


def test_ownership_and_provenance_rejection(tmp_path, monkeypatch):
    path, extracted = _run(tmp_path / "trial", 10000, [0, 0, 4])
    monkeypatch.setattr(classifier, "extract_files", lambda *_: extracted)
    record_path = path.parent / "cycle-00/input.json"
    record = json.loads(record_path.read_text())
    record["connection_ownership"]["upper_wood_0"]["axis"] = [0, 0, 1]
    record_path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="bolt axis mismatch"):
        classifier.classify_files(path)


def test_untrusted_report_rejected_before_classification(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"candidate": "wrong", "contact_cycles": []}))
    with pytest.raises(ValueError, match="artifact manifest"):
        classifier.classify_files(path)
