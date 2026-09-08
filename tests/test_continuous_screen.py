"""Replay source-bound moment evidence; not a structural-capacity test."""
import json
from pathlib import Path

import pytest

from fea import continuous_screen as screen


def test_frozen_continuous_screen_replays_current_sources():
    report = json.loads(Path("fea/results/continuous-frame/stability.json").read_text())
    assert report["candidate"] == "continuous-lean-frame"
    manifest = "exports/continuous-lean-frame/manifest.json"
    expected = set(json.loads(Path(manifest).read_text())["sources"]) | {
        manifest, "fea/continuous_screen.py", "fea/lean_screen.py",
        "fea/prepare_easy_structural.py", "fea/user_load_envelope.py"}
    assert set(report["source_sha256"]) == expected
    assert all(screen.digest(path) == sha for path, sha in report["source_sha256"].items())
    replay = screen.candidate_report(report["state"], screen.locations())
    assert replay["summaries"] == report["summaries"]
    assert json.loads(json.dumps(replay["cases"])) == report["cases"]
    assert len(report["cases"]) == 96
    assert all(row["case_count"] == 24 for row in report["summaries"].values())
    assert any("not strength" in text.lower() or "not fea" in text.lower()
               for text in report["assumptions"])


def test_saved_mass_and_contacts_match_drilled_cad():
    from mini_moonboard import continuous_frame

    report = json.loads(Path("fea/results/continuous-frame/stability.json").read_text())
    actual = screen.mass_state(continuous_frame.parts(True))
    assert report["state"]["mass_kg"] == pytest.approx(actual["mass_kg"])
    assert report["state"]["part_count"] == actual["part_count"]
    for field in ("centre_xy_mm", "centre_xyz_mm"):
        assert report["state"][field] == pytest.approx(actual[field])
    assert len(report["state"]["support_polygon_mm"]) == len(actual["support_polygon_mm"])
    for saved, current in zip(report["state"]["support_polygon_mm"], actual["support_polygon_mm"], strict=True):
        assert saved == pytest.approx(current)


def test_frozen_evidence_cannot_be_overwritten():
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        screen.main()
