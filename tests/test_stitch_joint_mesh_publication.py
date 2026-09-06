"""Portable actual-stitch publication checks, without CAD, Gmsh or solver."""
import json
from pathlib import Path

import pytest

from fea.results.stitch_joint_mesh.publisher import (
    archive_files,
    mesh,
    replay_files,
    sha,
)

DIRECTORY = Path(__file__).resolve().parents[1] / "fea/results/stitch_joint_mesh"


@pytest.fixture(scope="module")
def files():
    return archive_files(DIRECTORY / "evidence.tar.gz")


def mutate(files, name, edit):
    changed = dict(files)
    data = json.loads(changed[name])
    edit(data)
    changed[name] = json.dumps(data).encode()
    changed["manifest.json"] = json.dumps({n: sha(b) for n, b in changed.items() if n != "manifest.json"}).encode()
    return changed


def test_published_actual_mesh_replays_and_matches_report(files):
    report = json.loads((DIRECTORY / "report.json").read_text())
    assert sha((DIRECTORY / "evidence.tar.gz").read_bytes()) == report["archive_sha256"]
    assert (DIRECTORY / "manifest.json").read_bytes() == files["manifest.json"]
    assert sha(files["publisher.py"]) == report["publisher_sha256"]
    result = replay_files(files)
    assert result == report["summary"]
    assert (result["body_count"], result["node_count"], result["element_count"]) == (14, 145787, 70148)
    assert result["shared_body_nodes"] == 0


def test_missing_or_changed_evidence_cannot_replay(files):
    changed = dict(files)
    del changed["mesh/stitch_joint_mesh.py.snapshot"]
    with pytest.raises(ValueError, match="inventory"):
        replay_files(changed)
    changed = dict(files)
    changed["geometry/leg_right_inner.step"] += b"changed"
    with pytest.raises(ValueError, match="digest"):
        replay_files(changed)
    changed = mutate(files, "mesh/mesh.json", lambda data: data.pop("geometry_sha256"))
    with pytest.raises(ValueError, match="metadata"):
        replay_files(changed)
    changed = mutate(files, "mesh/mesh.json", lambda data: data.update(geometry_sha256="0" * 64))
    with pytest.raises(ValueError, match="bound"):
        replay_files(changed)


def test_rehashed_metadata_cannot_fake_ownership_or_complete_surface_cover(files):
    def share_nodes(data):
        data["bodies"]["leg_right_outer"]["nodes"] = data["bodies"]["leg_right_inner"]["nodes"]
    with pytest.raises(ValueError, match="ownership"):
        replay_files(mutate(files, "mesh/mesh.json", share_nodes))

    def lose_surface(data):
        surfaces = data["bodies"]["leg_right_inner"]["surfaces"]
        del surfaces[next(iter(surfaces))]
    with pytest.raises(ValueError, match="complete quadratic exterior"):
        replay_files(mutate(files, "mesh/mesh.json", lose_surface))

    def lose_midside_node(data):
        surface = next(iter(data["bodies"]["leg_right_inner"]["surfaces"].values()))
        surface["nodes"].pop()
    with pytest.raises(ValueError, match="Quadratic surface"):
        replay_files(mutate(files, "mesh/mesh.json", lose_midside_node))


def test_mesh_parser_rejects_duplicate_nodes_and_solver_cards():
    with pytest.raises(ValueError, match="Duplicate"):
        mesh("*NODE\n1,0,0,0\n1,1,0,0\n")
    with pytest.raises(ValueError, match="solver cards"):
        mesh("*MATERIAL,NAME=WOOD\n")
