"""Spread-leg actual C3D10 audit, not a response or resistance test."""
import math
import shutil
import subprocess

import pytest

from fea.gusset_connector_trial import point_weights
from fea.prescribed_tet_control import IMAGE
from fea.solve_easy_frame import digest
from fea.spread_leg_mesh import build
from mini_moonboard import lumber_leg_spread_frame as frame


@pytest.fixture(scope="module")
def meshes():
    if not shutil.which("docker"):
        pytest.skip("Spread mesh requires Docker")
    if subprocess.run(["docker", "info"], capture_output=True, timeout=15, check=False).returncode:
        pytest.skip("Spread mesh requires running Docker")
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True,
                      timeout=15, check=False).returncode:
        pytest.skip("Spread mesh requires locally available pinned image")
    return {side: build("2x8", 300., side, 40.) for side in ("left", "right")}


@pytest.mark.parametrize("side", ("left", "right"))
def test_native_spread_geometry_and_connector_faces(meshes, side):
    nodes, elements, report = meshes[side]
    assert len(nodes) == report["node_count"] and len(elements) == report["element_count"]
    assert all(len(ids) == 10 for ids in elements.values())
    assert report["image"] == IMAGE and report["mesh_size_mm"] == 40.
    assert (report["along_leg_pitch_mm"], report["along_rim_pitch_mm"], report["top_extension_mm"]) == (100., 50., 150.)
    assert report["mesh_volume_mm3"] == pytest.approx(report["cad_volume_mm3"], rel=1e-6)
    assert report["mesh_centroid_mm"] == pytest.approx(report["cad_centroid_mm"], abs=1e-5)
    old = frame.original.leg("2x8", 300., side).shape
    assert report["cad_volume_mm3"]-old.Volume() == pytest.approx(30*38.1*frame.WIDTHS["2x8"])
    assert report["maximum_midpoint_error_mm"] < 1e-6
    assert report["minimum_corner_determinant_mm3"] > 0
    _, foot, along, _ = frame.geometry("2x8", 300.)
    floor = report["floor"]
    assert report["floor_nodes"] == floor["nodes"]
    assert floor["area_mm2"] == pytest.approx(38.1*frame.WIDTHS["2x8"]/along.z)
    assert floor["centroid_mm"][1:] == pytest.approx([foot.y, 0.], abs=1e-5)
    assert set(floor["nodes"]) == {n for n, p in nodes.items() if abs(p[2]) < 1e-5}
    assert report["interface_faces"] == report["inner_interface"]["faces"]
    expected_x = frame.original.b.HALF*(1 if side == "right" else -1)
    for point in frame.bolt_points("2x8", 300.):
        coupled = point_weights(nodes, report["interface_faces"], (point.y, point.z))
        assert sum(coupled["weights"]) == pytest.approx(1.)
        assert coupled["point_mm"] == pytest.approx([expected_x, point.y, point.z])
    for name in ("fea/spread_leg_mesh.py", "fea/lumber_leg_mesh.py",
                 "mini_moonboard/lumber_leg_spread_frame.py", "mini_moonboard/lumber_leg_frame.py"):
        assert report["source_sha256"][name] == digest(name)
    assert all(digest(name) == sha for name, sha in report["source_sha256"].items())


def test_mirrored_spread_mesh_volume_and_centroid(meshes):
    left, right = (meshes[s][2] for s in ("left", "right"))
    assert left["mesh_volume_mm3"] == pytest.approx(right["mesh_volume_mm3"])
    assert left["mesh_centroid_mm"] == pytest.approx([-right["mesh_centroid_mm"][0], *right["mesh_centroid_mm"][1:]])
    assert left["floor"]["area_mm2"] == pytest.approx(right["floor"]["area_mm2"])


@pytest.mark.parametrize("side,size", [("bad", 40.), ("right", 0.), ("right", math.nan),
                                      ("right", 81.), ("right", True)])
def test_invalid_request(side, size):
    with pytest.raises(ValueError):
        build("2x8", 300., side, size)
