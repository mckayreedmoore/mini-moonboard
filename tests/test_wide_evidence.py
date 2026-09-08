"""Replay accepted wide-principal diagnostic evidence without inferring capacity."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from fea import publish_wide_structural as publisher
from fea import wide_structural as prepare
from fea.publish_bearing_structural import validate_metadata
from fea.solve_easy_frame import audit, digest


@pytest.mark.parametrize("size", [40, 60])
def test_published_wide_stiffness_replays(size):
    row = json.loads((publisher.OUTPUT/f"mesh{size}.json").read_text())
    assert row["candidate"] == prepare.KEY == row["frozen_geometry"]["candidate"]
    assert row["mesh_size_mm"] == row["size_mm"] == size
    geometry_sources = row["frozen_geometry"]["geometry_source_sha256"]
    expected = set(geometry_sources) | {
        "fea/solve_bearing_frame.py", "fea/solve_easy_frame.py", "fea/box_results.py",
        "fea/floor_contact.py", "fea/floor_contact_results.py", "fea/hybrid_results.py"}
    assert set(row["source_sha256"]) == expected
    assert all(row["source_sha256"][p] == sha for p, sha in geometry_sources.items())
    assert all(digest(p) == sha for p, sha in row["source_sha256"].items())
    assert row["publisher_source_sha256"] == {p: digest(p) for p in publisher.PUBLISHER_SOURCES}
    assert set(row["replay_archives"]) == {
        f"mesh{size}{suffix}.gz" for suffix in (".inp", ".dat", ".context.json", ".log", ".sta")}
    decoded = {}
    for name, hashes in row["replay_archives"].items():
        payload = (publisher.OUTPUT/name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == hashes["gzip_sha256"]
        data = gzip.decompress(payload)
        assert hashlib.sha256(data).hexdigest() == hashes["uncompressed_sha256"]
        assert hashes["uncompressed_sha256"] == row["evidence_sha256"][hashes["original_name"]]
        decoded[name.removesuffix(".gz")] = data.decode()
    deck = decoded[f"mesh{size}.inp"]
    assert hashlib.sha256(deck.encode()).hexdigest() == row["deck_sha256"]
    context = json.loads(decoded[f"mesh{size}.context.json"])
    validate_metadata(row, deck, context)
    for key in ("modulus_mpa", "nodes", "elements", "mesh_volume_mm3"):
        with pytest.raises(ValueError):
            validate_metadata({**row, key: row[key]+1}, deck, context)
    replay = audit(deck, decoded[f"mesh{size}.dat"], row["frozen_geometry"])
    assert all(json.loads(json.dumps(value)) == row[key] for key, value in replay.items())
    assert "*ERROR" not in decoded[f"mesh{size}.log"].upper()
    assert row["min_jacobian"] > 0
    assert row["maximum_midpoint_error_mm"] <= 1e-6
    assert 0 <= row["volume_relative_error"] <= .005
    assert row["mesh_settings"]["Mesh.SecondOrderLinear"] == 1
    assert row["high_order_optimizer_used"] is False
    assert row["limits"] == row["frozen_geometry"]["assumptions"] == prepare.LIMITS
    targets = [p for label, p, _ in prepare.locations()
               if label in ("A12", "C12", "F12", "H12", "K12")]
    assert row["frozen_geometry"]["audited_load_targets_mm"] == json.loads(json.dumps(targets))


def test_mesh_comparison_uses_identical_inputs():
    rows = [json.loads((publisher.OUTPUT/f"mesh{size}.json").read_text()) for size in (40, 60)]
    for key in ("frozen_geometry", "modulus_mpa", "input_sha256", "source_sha256"):
        assert rows[0][key] == rows[1][key], key


def test_wide_moment_screen_replays_corrected_cases():
    row = json.loads(prepare.STABILITY.read_text())
    manifest = "exports/wide-principal-development/manifest.json"
    expected = set(json.loads(Path(manifest).read_text())["sources"]) | {
        manifest, "fea/wide_structural.py", "fea/prepare_easy_structural.py",
        "fea/user_load_envelope.py", "mini_moonboard/stability.py", "mini_moonboard/panel_grid_v2.py"}
    assert row["candidate"] == prepare.KEY
    assert set(row["source_sha256"]) == expected
    assert all(digest(p) == sha for p, sha in row["source_sha256"].items())
    cases = prepare.envelope(row["state"], prepare.locations(), (150, 200, 250, 300))
    assert len(cases) == 96
    assert json.loads(json.dumps(cases)) == row["cases"]
    assert {str(w): prepare.common.summarize([c for c in cases if c["climber_lb"] == w])
            for w in (150, 200, 250, 300)} == row["summaries"]


def test_wide_published_mass_and_contacts_match_actual_cad():
    from mini_moonboard import wide_frame as frame

    saved = json.loads(prepare.STABILITY.read_text())["state"]
    actual = prepare.mass_state(frame.parts(True))
    assert saved["mass_kg"] == pytest.approx(actual["mass_kg"])
    assert saved["part_count"] == actual["part_count"] == 47
    for key in ("centre_xy_mm", "centre_xyz_mm"):
        assert saved[key] == pytest.approx(actual[key])
    assert len(saved["support_polygon_mm"]) == len(actual["support_polygon_mm"])
    for previous, current in zip(saved["support_polygon_mm"], actual["support_polygon_mm"], strict=True):
        assert previous == pytest.approx(current)
