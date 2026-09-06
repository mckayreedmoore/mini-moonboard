import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import tied_base as candidate
from mini_moonboard.footprint_frame import parts as original_parts


@pytest.mark.parametrize("height", [0, 294.45, math.nan, math.inf])
def test_rejects_undefined_geometry_variants(height):
    with pytest.raises(ValueError, match="comparisons"):
        candidate.parts(height)


@pytest.mark.parametrize("height", [100, 275])
def test_new_parts_preserve_source_and_have_real_contacts(height):
    base = tuple(p for p in original_parts(100, False) if not p.name.startswith("angle_"))
    parts = candidate.parts(height)
    assert len(parts) == len(base)+4
    assert all(old is new for old, new in zip(base, parts[:len(base)], strict=True))
    assert all(p.shape.isValid() and len(p.shape.Solids()) == 1 for p in parts)
    report = candidate.inspect(height)
    assert report["floor_polygon_unchanged"] and report["new_part_overlap_mm3"] == []
    assert report["candidate_state"]["support_polygon_mm"] == report["baseline"]["support_polygon_mm"]
    contacts = {tuple(row["parts"]): row["area_mm2"] for row in report["intended_face_contacts"]}
    for side in ("left", "right"):
        assert contacts[(f"base_rail_{side}", f"leg_{side}")] > 17000
        assert contacts[(f"base_rail_{side}", f"base_spacer_{side}")] == pytest.approx(12540.8637854)
        cheek = contacts[(f"base_spacer_{side}", f"kicker_cheek_{side}")]
        rim = contacts[(f"base_spacer_{side}", f"box_side_{side}")]
        assert cheek > 7000
        assert rim == pytest.approx(0 if height == 100 else 5297.34471908, abs=.001)
        assert cheek+rim == pytest.approx(12540.8637854)
    mass = sum(row["mass_kg"] for row in report["added_parts"])
    assert report["added_mass_kg"] == pytest.approx(mass)
    assert mass > 6.7446  # Includes the actual spacer solids, not rails alone.
    assert report["candidate_state"]["overall_dimensions_mm"][0] == pytest.approx(2667)
    assert "CONNECTIONS UNRESOLVED" in report["status"]
    for row in report["added_parts"]:
        assert row["blank_dimensions_in"] == pytest.approx([v/25.4 for v in row["blank_dimensions_mm"]])


def test_missing_front_contact_fails_closed(monkeypatch):
    monkeypatch.setattr(candidate, "face_contact_area", lambda _a, _b: 0.)
    with pytest.raises(ValueError, match="Missing intended face adjacency"):
        candidate.inspect(275)


def test_existing_export_is_preserved(tmp_path):
    original = tmp_path/"summary.json"
    original.write_text("previous result")
    with pytest.raises(ValueError, match="overwritten"):
        candidate.export(tmp_path)
    assert original.read_text() == "previous result"


@pytest.mark.parametrize("height", [100, 275])
def test_published_step_and_summary_match_geometry_milestone(height):
    directory = Path("exports/tied-base")/f"z{height}"
    report = json.loads((directory/"summary.json").read_text())
    assert report["candidate"] == f"2x8-foot100-tied-base-z{height}"
    assert report["height_mm"] == height
    assert "GEOMETRY CHECKS ONLY" in report["status"]
    assert "ALL NEW CONNECTIONS UNRESOLVED" in report["status"]
    assert "NOT STRUCTURAL APPROVAL" in report["status"]
    assert set(report["artifact_sha256"]) == {"candidate.step"}
    step = directory/"candidate.step"
    assert hashlib.sha256(step.read_bytes()).hexdigest() == report["artifact_sha256"][step.name]
    # These exports are the current geometry milestone. If retained as history
    # after a source change, archive its generating sources and replay those;
    # do not silently relabel old STEP files with new source hashes.
    assert "mini_moonboard/tied_base.py" in report["source_sha256"]
    for source, digest in report["source_sha256"].items():
        assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == digest

    shape = cq.importers.importStep(str(step)).val()
    solids = shape.Solids()
    assert len(solids) == report["candidate_state"]["part_count"] == 49
    assert all(solid.isValid() and solid.Volume() > 0 for solid in solids)
    volume = sum(solid.Volume() for solid in solids)
    assert volume == pytest.approx(report["candidate_state"]["volume_mm3"], rel=1e-9)
    centre = [sum(solid.Volume()*solid.Center().toTuple()[axis] for solid in solids)/volume
              for axis in range(3)]
    assert centre == pytest.approx(report["candidate_state"]["centre_mm"], abs=1e-6, rel=0)
    bounds = candidate.exact_bounds(shape)
    for axis, expected in zip("xyz", report["candidate_state"]["bounds_mm"], strict=True):
        assert [getattr(bounds, axis+"min"), getattr(bounds, axis+"max")] == pytest.approx(expected, abs=1e-6, rel=0)
    rails = [solid for solid in solids if abs(solid.Center().x) > 1295.4]
    assert len(rails) == 2
    for rail in rails:
        box = candidate.exact_bounds(rail)
        assert [box.zmin, box.zmax] == pytest.approx([height-44.45, height+44.45], abs=1e-6, rel=0)
        assert box.xlen == pytest.approx(38.1, abs=1e-6, rel=0)


def test_positive_new_part_collision_fails_closed(monkeypatch):
    monkeypatch.setattr(candidate, "overlap", lambda _a, _b: .02)
    with pytest.raises(ValueError, match="New-part solid overlap"):
        candidate.inspect(275)
