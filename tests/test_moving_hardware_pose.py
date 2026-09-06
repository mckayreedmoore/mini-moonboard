"""Full-polynomial clearance bounds and retained catalog CAD pose; no solver."""
import hashlib
import json
import math
import tarfile
from fractions import Fraction
from pathlib import Path

import pytest

from fea import moving_hardware_pose as pose


@pytest.fixture(scope="module")
def evidence(tmp_path_factory):
    path = Path(__file__).resolve().parents[1] / "fea/results/moving_hardware_control/fourth-direct-quiescent.tar.gz"
    root = tmp_path_factory.mktemp("pose-evidence")
    with tarfile.open(path) as archive:
        for member in archive:
            if member.isfile() and (member.name.startswith("prepared/") or member.name in (
                "geometry/geometry.json", "geometry/leg_stitch_right_1_bolt_nut.step", "geometry/leg_stitch_right_1_washer_inner.step")):
                target = root / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    return root


def test_bounds_detect_between_node_minimum_and_subdivide_exactly():
    uv = ((0, 0), (1, 0), (0, 1), (.5, 0), (.5, .5), (0, .5))
    points = [(0, 1 + (Fraction(u) - Fraction(1, 4))**2, 0) for u, _ in uv]
    assert min(p[1] for p in points) == Fraction(17, 16)
    coarse = pose.quadratic_bounds(points)
    assert coarse[2] < 1  # Entire-polynomial bound catches the interior dip.
    children = pose.subdivide(points)
    assert len(children) == 4
    lower, depth, leaves = pose.refined_bounds(points, Fraction(1), True)
    assert lower[2] == 1 and depth <= 2 and leaves > 1
    assert coarse[2] <= lower[2] <= lower[3] <= coarse[3]


def test_quadratic_affine_bounds_are_exact_and_nonfinite_rejected():
    points = [(0., 2., 0.)] * 6
    assert pose.quadratic_bounds(points) == (0, 0, 4, 4)
    with pytest.raises(ValueError, match="finite TRI6"):
        pose.quadratic_bounds([(0, math.nan, 0)] * 6)


def test_actual_pose_is_frozen_and_strictly_separated(evidence, tmp_path):
    original = (evidence / "prepared/context.json").read_bytes()
    directory = pose.write_preflight(evidence / "geometry", evidence / "prepared", tmp_path)
    report = json.loads((directory / "report.json").read_text())
    mesh = report["quadratic_mesh"]
    assert mesh["strictly_separated_selected_surfaces"] is True
    assert mesh["radial_gap_lower_mm"] == pytest.approx(.0007702642876363796, abs=1e-12)
    assert mesh["axial_gap_lower_mm"] == pytest.approx(.001)
    assert mesh["subdivision_maximum_depth"]["WASHER_BORE"] == 2
    assert mesh["surface_face_counts"] == {"WASHER_HEAD": 220, "CORE_HEAD": 126, "WASHER_BORE": 134, "CORE_SHANK": 3356}
    assert report["CAD"]["overlap_volume_mm3"] == 0
    assert report["CAD"]["CAD_min_distance_mm"] == pytest.approx(.001, abs=1e-7)
    assert report["CAD"]["projected_head_bearing_area_mm2"] == pytest.approx(math.pi * (81 - 5.4991**2))
    assert report["CAD"]["nominal_constant_velocity_engagement_time_s"] == pytest.approx({"head": 1e-5, "bore": 1e-5})
    assert (directory / "original-context.json").read_bytes() == original == (evidence / "prepared/context.json").read_bytes()
    posed = json.loads((directory / "posed-nodes.json").read_text())
    context = json.loads(original)
    for n in context["bodies"]["BOLT_NUT"]["nodes"]:
        assert posed["nodes"][str(n)] == context["nodes"][str(n)]
    for name, digest in report["source_sha256"].items():
        assert hashlib.sha256((directory / (name + ".snapshot")).read_bytes()).hexdigest() == digest
    assert hashlib.sha256((directory / "posed-nodes.json").read_bytes()).hexdigest() == report["posed_nodes_sha256"]


def test_overlapping_cad_pose_is_rejected(evidence):
    context = json.loads((evidence / "prepared/context.json").read_text())
    with pytest.raises(ValueError, match="CAD overlap"):
        pose.cad_clearance(evidence / "geometry", context, (.001, .737, 0))


def test_pose_serialization_keeps_core_and_rejects_nonfinite(evidence):
    context = json.loads((evidence / "prepared/context.json").read_text())
    nodes, metadata = pose.posed_nodes(context)
    assert metadata["maximum_serialization_error_mm"] <= 5e-10
    assert len(nodes) == len(context["nodes"])
    assert all(nodes[n] == tuple(context["nodes"][str(n)]) for n in context["bodies"]["BOLT_NUT"]["nodes"])
    with pytest.raises(ValueError, match="rigid translation"):
        pose.posed_nodes(context, (math.nan, 0, 0))


def test_changed_source_cannot_publish(tmp_path, monkeypatch):
    monkeypatch.setattr(pose, "TRANSLATION_MM", (0, 0, 0))
    with pytest.raises(ValueError, match="source/configuration"):
        pose.write_preflight(tmp_path, tmp_path, tmp_path / "output")
    assert not (tmp_path / "output").exists()
