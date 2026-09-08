"""Replay committed source-bound evidence; no structural safety verdict."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from fea import bearing_joint_audit as joints
from fea import prepare_bearing_structural as prepare
from fea.publish_bearing_structural import validate_metadata
from fea.solve_easy_frame import audit, digest


@pytest.mark.parametrize("size", [40, 60])
def test_published_stiffness_archives_replay(size):
    directory = Path("fea/results/bearing-frame")
    row = json.loads((directory/f"mesh{size}.json").read_text())
    assert row["candidate"] == "bearing-lean-frame"
    assert row["mesh_size_mm"] == size
    expected = set(row["frozen_geometry"]["geometry_source_sha256"]) | {
        "fea/solve_bearing_frame.py", "fea/solve_easy_frame.py", "fea/box_results.py",
        "fea/floor_contact.py", "fea/floor_contact_results.py", "fea/hybrid_results.py"}
    assert set(row["source_sha256"]) == expected
    assert all(digest(p) == sha for p, sha in row["source_sha256"].items())
    assert row["publisher_source_sha256"] == {
        "fea/publish_bearing_structural.py": digest("fea/publish_bearing_structural.py")}
    assert set(row["replay_archives"]) == {
        f"mesh{size}{suffix}.gz" for suffix in (".inp", ".dat", ".context.json", ".log", ".sta")}
    decoded = {}
    for name, hashes in row["replay_archives"].items():
        payload = (directory/name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == hashes["gzip_sha256"]
        data = gzip.decompress(payload)
        assert hashlib.sha256(data).hexdigest() == hashes["uncompressed_sha256"]
        assert hashes["uncompressed_sha256"] == row["evidence_sha256"][hashes["original_name"]]
        decoded[name.removesuffix(".gz")] = data.decode()
    context = json.loads(decoded[f"mesh{size}.context.json"])
    validate_metadata(row, decoded[f"mesh{size}.inp"], context)
    for key in ("modulus_mpa", "nodes", "elements", "mesh_volume_mm3"):
        with pytest.raises(ValueError):
            validate_metadata({**row, key: row[key]+1}, decoded[f"mesh{size}.inp"], context)
    replay = audit(decoded[f"mesh{size}.inp"], decoded[f"mesh{size}.dat"], row["frozen_geometry"])
    assert all(json.loads(json.dumps(value)) == row[key] for key, value in replay.items())
    assert row["min_jacobian"] > 0
    assert row["maximum_midpoint_error_mm"] < 1e-6
    assert row["volume_relative_error"] < .005
    assert row["mesh_settings"]["Mesh.SecondOrderLinear"] == 1
    assert row["high_order_optimizer_used"] is False
    assert "no gravity" in row["limits"] and "not" in row["limits"]


def test_bearing_moment_screen_replays_source_bound_cases():
    row = json.loads(prepare.STABILITY.read_text())
    manifest = "exports/bearing-lean-frame/manifest.json"
    expected = set(json.loads(Path(manifest).read_text())["sources"]) | {
        manifest, "fea/prepare_bearing_structural.py", "fea/prepare_easy_structural.py",
        "fea/user_load_envelope.py", "mini_moonboard/stability.py"}
    assert set(row["source_sha256"]) == expected
    assert all(digest(p) == sha for p, sha in row["source_sha256"].items())
    cases = prepare.envelope(row["state"], prepare.locations(), (150, 200, 250, 300))
    assert len(cases) == 96
    assert json.loads(json.dumps(cases)) == row["cases"]
    assert {str(w): prepare.summarize([c for c in cases if c["climber_lb"] == w])
            for w in (150, 200, 250, 300)} == row["summaries"]


def test_published_joint_stack_replays_and_does_not_claim_capacity():
    row = json.loads(joints.OUTPUT.read_text())
    manifest = "exports/bearing-lean-frame/manifest.json"
    expected = set(json.loads(Path(manifest).read_text())["sources"]) | {
        manifest, "fea/bearing_joint_audit.py", "mini_moonboard/selected_hardware.py",
        "mini_moonboard/connection_geometry.py"}
    assert set(row["source_sha256"]) == expected
    assert all(digest(p) == sha for p, sha in row["source_sha256"].items())
    assert row["leg_bolt_count"] == len(row["leg_bolts"]) == 8
    assert row["unselected_kicker_corner_screw_count"] == len(row["unselected_kicker_corner_screws"]) == 12
    for bolt in row["leg_bolts"]:
        replay = joints.bolt_stack(bolt["length_mm"], bolt["nominal_grip_mm"], bolt["assumed_underlength_mm"])
        assert all(bolt[key] == value for key, value in replay.items())
        assert bolt["connection_strength_qualified"] is False
        assert joints.validate_receiver_grip(bolt["receiver_intervals_from_under_head_mm"],
            bolt["nominal_grip_mm"], bolt["washer_max_thickness_mm"]) == pytest.approx(114.3)


def test_published_state_and_receiver_inventory_match_current_cad():
    from mini_moonboard import bearing_frame as frame
    from mini_moonboard.connection_geometry import material_intervals

    state = json.loads(prepare.STABILITY.read_text())["state"]
    actual = prepare.mass_state(frame.parts(True))
    assert state["mass_kg"] == pytest.approx(actual["mass_kg"])
    assert state["part_count"] == actual["part_count"]
    for key in ("centre_xy_mm", "centre_xyz_mm"):
        assert state[key] == pytest.approx(actual[key])
    assert len(state["support_polygon_mm"]) == len(actual["support_polygon_mm"])
    for saved, current in zip(state["support_polygon_mm"], actual["support_polygon_mm"], strict=True):
        assert saved == pytest.approx(current)
    report = json.loads(joints.OUTPUT.read_text())
    bolts, unresolved = joints.inventory(frame.connections())
    assert {c.name for c in bolts} == {c["connection"] for c in report["leg_bolts"]}
    assert unresolved == report["unselected_kicker_corner_screws"]
    raw = {p.name: p for p in frame.parts(False)}
    for c in bolts:
        record = next(r for r in report["leg_bolts"] if r["connection"] == c.name)
        intervals = {name: material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
                     for name in c.members}
        assert json.loads(json.dumps(intervals)) == record["receiver_intervals_from_under_head_mm"]
