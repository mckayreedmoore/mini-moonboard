"""The selectable development assembly must match its separate CAD artifacts."""
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import cadquery as cq
import numpy as np
import pytest

from mini_moonboard import independent_leg_frame, joint_frame, spacing_frame
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.joint_exports import DESIGN, INDEPENDENT_DESIGN, SPACING_DESIGN


def segment_hits_triangles(triangles, start, end):
    """Two-sided Möller–Trumbore intersections, limited to the bore segment."""
    start, end = np.asarray(start), np.asarray(end)
    edge1, edge2 = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    cross = np.cross(end - start, edge2)
    determinant = np.einsum("ij,ij->i", edge1, cross)
    valid = np.abs(determinant) > 1e-9
    if not valid.any():
        return False
    edge1, edge2, cross, determinant = edge1[valid], edge2[valid], cross[valid], determinant[valid]
    relative = start - triangles[valid, 0]
    u = np.einsum("ij,ij->i", relative, cross) / determinant
    q = np.cross(relative, edge1)
    v = q.dot(end - start) / determinant
    t = np.einsum("ij,ij->i", edge2, q) / determinant
    return bool(((u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7)
                 & (t >= -1e-7) & (t <= 1 + 1e-7)).any())


def test_bore_segment_detects_filled_cap_without_hitting_beyond_pilot():
    cap = np.array([[[-5., -5., 0.], [5., -5., 0.], [0., 5., 0.]]])
    assert segment_hits_triangles(cap, (0, 0, -1), (0, 0, 1))
    assert segment_hits_triangles(cap[:, ::-1], (0, 0, -1), (0, 0, 1))
    assert not segment_hits_triangles(cap, (10, 0, -1), (10, 0, 1))
    assert not segment_hits_triangles(cap, (0, 0, -2), (0, 0, -1))


@pytest.mark.parametrize("model,design,baseline", [
    (joint_frame, DESIGN, "2x8-foot100"),
    (independent_leg_frame, INDEPENDENT_DESIGN, "joint-development"),
    (spacing_frame, SPACING_DESIGN, "independent-leg-development"),
], ids=[DESIGN["key"], INDEPENDENT_DESIGN["key"], SPACING_DESIGN["key"]])
def test_joint_candidate_viewer_and_exports_match_geometry(model, design, baseline):
    key = design["key"]
    directory = Path("exports")/key
    manifest = json.loads((directory/"manifest.json").read_text())
    viewer = json.loads((Path("site/hybrid")/key/"parts.json").read_text())
    assert viewer["design"] == manifest["design"] == design
    assert design["baseline"] == baseline
    sources = {f"mini_moonboard/{name}.py" for name in (
        "joint_exports", "joint_frame", "footprint_frame", "shallow_frame", "hybrid_frame",
        "hybrid", "box_frame", "model", "panel_grid", "box_exports", "export", "raster")}
    if model is not joint_frame:
        sources.add("mini_moonboard/independent_leg_frame.py")
    if model is spacing_frame:
        sources.add("mini_moonboard/spacing_frame.py")
    assert set(manifest["sources"]) == sources
    assert set(manifest["artifacts"]) == {key+suffix for suffix in (
        ".step", "_front.png", "_rear.png", "_parts.csv", "_connections.csv")}
    assert set(manifest["artifacts"]) == {p.name for p in directory.iterdir() if p.name != "manifest.json"}
    for root, category in ((Path("."), "sources"), (directory, "artifacts"), (Path("site"), "viewer_artifacts")):
        for filename, digest in manifest[category].items():
            assert hashlib.sha256((root/filename).read_bytes()).hexdigest() == digest, filename
    parts, connections = model.parts(), model.connections()
    expected = {p.name: (p.shape, p.blank) for p in parts}
    expected.update({"fastener_"+c.name: (cq.Compound.makeCompound(c.components()),
                     (c.length, c.diameter, c.diameter)) for c in connections})
    assert {p["name"] for p in viewer["parts"]} == set(expected)
    assert len(viewer["parts"]) == len(expected)
    assert set(manifest["viewer_artifacts"]) == {str(Path("hybrid")/key/"parts.json")} | {p["path"] for p in viewer["parts"]}
    bore_connections = [c for c in connections if c.name.startswith("leg_stitch_")
                        or ("_seam_" in c.name and c.name.startswith(("rib_", "angle_rib_")))]
    assert len(bore_connections) == (30 if model is joint_frame else 36)
    bore_members = {name for c in bore_connections for name in c.members}
    meshes = {}
    for item in viewer["parts"]:
        assert item["fabrication"]["dimensions_mm"] == pytest.approx(expected[item["name"]][1])
        assert "NOT structural approval" in item["fabrication"]["clearance_status"]
        data = (Path("site")/item["path"]).read_bytes()
        triangles = struct.unpack_from("<I", data, 80)[0]
        assert triangles > 0 and len(data) == 84+50*triangles
        if item["name"] in bore_members:
            meshes[item["name"]] = np.array([record[3:12] for record in
                struct.iter_unpack("<12fH", data[84:])]).reshape(-1, 3, 3)
        lower, upper = [math.inf]*3, [-math.inf]*3
        for triangle in struct.iter_unpack("<12fH", data[84:]):
            for axis in range(3):
                coordinates = triangle[3+axis:12:3]
                assert all(map(math.isfinite, coordinates))
                lower[axis] = min(lower[axis], *coordinates)
                upper[axis] = max(upper[axis], *coordinates)
        bounds = exact_bounds(expected[item["name"]][0])
        # CAD STL export uses 0.5 mm tessellation tolerance; include float32
        # rounding at this assembly's metre-scale world coordinates.
        assert lower+upper == pytest.approx([getattr(bounds, axis+end)
            for end in ("min", "max") for axis in "xyz"], abs=.501)
        assert item["viewer_aabb_mm"] == pytest.approx([bounds.xlen, bounds.ylen, bounds.zlen], abs=1e-5)
    # Inspect served triangles independently of CAD and regenerated hashes:
    # filling a bore leaves the bounding box unchanged. Probe the axis and four
    # radial offsets, inside the clearance/pilot radius with tessellation margin.
    for connection in bore_connections:
        direction = np.array(connection.direction.toTuple())
        radial = np.cross(direction, (1, 0, 0))
        if np.linalg.norm(radial) < .5:
            radial = np.cross(direction, (0, 1, 0))
        radial /= np.linalg.norm(radial)
        transverse = np.cross(direction, radial)
        for index, name in enumerate(connection.members):
            radius = 5 if connection.kind == "bolt" else (2.6 if index == 0 else 1.6)
            for offset in (np.zeros(3), radial, -radial, transverse, -transverse):
                start = np.array(connection.start.toTuple()) + offset * (radius - .75)
                # Drilling extends from -1 to length+1. Stop within that cut so
                # receiving-member blind-pilot bottoms are not false failures.
                assert not segment_hits_triangles(meshes[name], start - direction * .5,
                    start + direction * (connection.length + .5)), (connection.name, name, offset)
    with (directory/f"{key}_parts.csv").open() as stream:
        records = list(csv.DictReader(stream))
    rows = {r["part"]: r for r in records}
    assert len(records) == len(rows) == len(parts)
    assert rows.keys() == {p.name for p in parts}
    for part in parts:
        row = rows[part.name]
        assert int(row["layers"]) == part.laminations
        for unit, divisor in (("mm", 1), ("in", 25.4)):
            assert [float(row[f"dimension_{axis}_{unit}"]) for axis in (1, 2, 3)] == pytest.approx([v/divisor for v in part.blank])
    with (directory/f"{key}_connections.csv").open() as stream:
        records = list(csv.DictReader(stream))
    rows = {r["connection"]: r for r in records}
    assert len(records) == len(rows) == len(connections)
    assert rows.keys() == {c.name for c in connections}
    for connection in connections:
        row = rows[connection.name]
        assert row["members"].split(" + ") == list(connection.members)
        assert row["kind"] == connection.kind
        assert row["status"] == design["status"]
        if model is not joint_frame and connection.name.startswith("analysis_leg_wall_bolt_"):
            assert len(row["members"].split(" + ")) == 3
        assert [float(row[f"{axis}_mm"]) for axis in "xyz"] == pytest.approx(connection.start.toTuple())
        assert [float(row[f"axis_{axis}"]) for axis in "xyz"] == pytest.approx(connection.direction.toTuple())
        assert [float(row[field]) for field in ("length_mm", "length_in", "diameter_mm", "grip_mm")] == pytest.approx([
            connection.length, connection.length/25.4, connection.diameter, connection.grip])
    step = cq.importers.importStep(str(directory/f"{key}.step")).val()
    assert len(step.Solids()) == sum(len(shape.Solids()) for shape, _ in expected.values())
    assert step.Volume() == pytest.approx(sum(shape.Volume() for shape, _ in expected.values()), rel=1e-8)
    # Match spatial fingerprints, not just total volume: displaced parts retain
    # their volume, and STEP can reorder geometrically identical hardware.
    def fingerprint(solid):
        bounds = exact_bounds(solid)
        return (*solid.centerOfMass(solid).toTuple(), solid.Volume(),
                *[getattr(bounds, axis+end) for axis in "xyz" for end in ("min", "max")])
    actual = [fingerprint(s) for s in step.Solids()]
    for shape, _ in expected.values():
        for solid in shape.Solids():
            intended = fingerprint(solid)
            match = next((i for i, row in enumerate(actual) if all(
                math.isclose(a, b, rel_tol=1e-8, abs_tol=.001)
                for a, b in zip(row, intended, strict=True))), None)
            assert match is not None, intended
            actual.pop(match)
    assert not actual
