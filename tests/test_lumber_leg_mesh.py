import math
import shutil
import subprocess

import pytest

from fea.gusset_connector_trial import point_weights
from fea.lumber_leg_mesh import build
from fea.prescribed_tet_control import IMAGE
from mini_moonboard import lumber_leg_frame as frame


@pytest.fixture(scope="module")
def docker_available():
    if not shutil.which("docker"):
        pytest.skip("Native leg mesh requires Docker")
    if subprocess.run(["docker", "info"], capture_output=True, timeout=15, check=False).returncode:
        pytest.skip("Native leg mesh requires a running Docker daemon")
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True,
                      timeout=15, check=False).returncode:
        pytest.skip("Native leg mesh requires the locally available pinned Docker image")


@pytest.mark.parametrize("size,extension,side", [("2x6", 0., "right"), ("2x12", 300., "left")])
def test_leg_mesh_geometry_floor_and_actual_bolt_interpolation(size, extension, side, docker_available):
    nodes, elements, report = build(size, extension, side)
    assert len(nodes) == report["node_count"] and len(elements) == report["element_count"]
    assert report["mesh_volume_mm3"] == pytest.approx(report["cad_volume_mm3"], rel=1e-6)
    assert report["mesh_centroid_mm"] == pytest.approx(report["cad_centroid_mm"], abs=1e-5)
    assert report["maximum_midpoint_error_mm"] < 1e-6
    assert report["minimum_corner_determinant_mm3"] > 0
    _, foot, along, _ = frame.geometry(size, extension)
    floor = report["floor"]
    assert report["floor_nodes"] == floor["nodes"]
    assert report["interface_faces"] == report["inner_interface"]["faces"]
    assert floor["area_mm2"] == pytest.approx(38.1*frame.WIDTHS[size]/along.z)
    assert floor["centroid_mm"][1:] == pytest.approx([foot.y, 0.], abs=1e-5)
    assert set(floor["nodes"]) == {n for n, p in nodes.items() if abs(p[2]) < 1e-5}
    for point in frame.bolt_points(size, extension):
        coupling = point_weights(nodes, report["inner_interface"]["faces"], (point.y, point.z))
        assert sum(coupling["weights"]) == pytest.approx(1.)
        assert coupling["point_mm"][1:] == pytest.approx([point.y, point.z])


def test_mirrored_leg_and_mesh_size_preserve_geometry(docker_available):
    reports = [build("2x6", 0., side, 60.)[2] for side in ("left", "right")]
    left, right = reports
    assert left["mesh_volume_mm3"] == pytest.approx(right["mesh_volume_mm3"])
    assert left["mesh_centroid_mm"] == pytest.approx([-right["mesh_centroid_mm"][0], *right["mesh_centroid_mm"][1:]])
    assert left["floor"]["area_mm2"] == pytest.approx(right["floor"]["area_mm2"])


@pytest.mark.parametrize("side,size", [("bad", 40.), ("right", 0.), ("right", math.nan), ("right", 81.)])
def test_rejects_invalid_mesh_requests(side, size):
    with pytest.raises(ValueError):
        build("2x6", 0., side, size)
