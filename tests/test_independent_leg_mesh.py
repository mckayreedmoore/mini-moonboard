"""Check complete planar TRI6 floor integration without meshing/solving."""
import hashlib
import json
from pathlib import Path

import pytest

from fea.independent_leg_mesh import floor_selection, replay_archive


def test_floor_selection_integrates_complete_quadratic_face_and_rejects_bad_geometry():
    nodes = {1: (0., 0., 0.), 2: (1., 0., 0.), 3: (0., 1., 0.), 4: (0., 0., 1.),
             5: (.5, 0., 0.), 6: (.5, .5, 0.), 7: (0., .5, 0.), 8: (0., 0., .5),
             9: (.5, 0., .5), 10: (0., .5, .5)}
    elements = {1: tuple(range(1, 11))}
    info = {"parts": {"inner": {"floor_area_mm2": .5, "floor_centroid_mm": [1 / 3, 1 / 3, 0]}}}
    patch = floor_selection(nodes, elements, {"inner": [1]}, info)["inner"]
    assert patch["faces"] == [[1, 1]]
    assert patch["nodes"] == [1, 2, 3, 5, 6, 7]
    assert sum(patch["weights_mm2"].values()) == pytest.approx(.5)
    assert [patch["weights_mm2"][n] for n in (1, 2, 3)] == [0, 0, 0]
    assert [patch["weights_mm2"][n] for n in (5, 6, 7)] == pytest.approx([1 / 6] * 3)
    with pytest.raises(ValueError, match="not affine"):
        floor_selection({**nodes, 5: (.4, 0, 0)}, elements, {"inner": [1]}, info)
    with pytest.raises(ValueError, match="area/centroid"):
        floor_selection(nodes, elements, {"inner": [1]}, {"parts": {"inner": {
            "floor_area_mm2": 1., "floor_centroid_mm": [1 / 3, 1 / 3, 0]}}})
    with pytest.raises(ValueError, match="Incomplete floor"):
        floor_selection(nodes, elements, {"inner": []}, info)


def test_published_actual_leg_mesh_archive_replays_without_cad_or_gmsh():
    directory = Path(__file__).resolve().parents[1] / "fea/results/independent_leg_mesh"
    archive = directory / "evidence.tar.gz"
    report = json.loads((directory / "report.json").read_text())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == report["archive_sha256"]
    records = replay_archive(archive)
    assert records[25]["element_count"] > records[40]["element_count"]
