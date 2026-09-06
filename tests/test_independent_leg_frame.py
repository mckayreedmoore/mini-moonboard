"""Mechanical candidate geometry checks, never connection/stability approval."""
import math
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import cadquery as cq
import pytest

from mini_moonboard import independent_leg_frame as frame
from mini_moonboard import joint_frame as baseline


@pytest.mark.parametrize("drilled", [False, True])
def test_distinct_plies_preserve_profiles_floor_and_baseline(drilled):
    original = {p.name: p for p in baseline.parts(drilled)}
    candidate = {p.name: p for p in frame.parts(drilled)}
    assert len(candidate) == len(frame.parts(drilled))
    assert len(candidate) == len(original) + 2
    for name, part in original.items():
        if name not in ("leg_left", "leg_right"):
            assert candidate[name] is part
            continue
        plies = [candidate[name + "_" + layer] for layer in ("inner", "outer")]
        for ply in plies:
            assert ply.laminations == 1 and ply.blank[2] == 19.05
            assert ply.shape.isValid() and len(ply.shape.Solids()) == 1
            assert ply.shape.BoundingBox().xlen == pytest.approx(19.05)
            floors = [f for f in ply.shape.Faces() if abs(f.BoundingBox().zmin) < 1e-5
                      and abs(f.BoundingBox().zmax) < 1e-5]
            assert len(floors) == 1 and floors[0].geomType() == "PLANE"
            old_floor = [f for f in part.shape.Faces() if abs(f.BoundingBox().zmin) < 1e-5
                         and abs(f.BoundingBox().zmax) < 1e-5]
            assert floors[0].Area() == pytest.approx(old_floor[0].Area()/2, abs=.01)
            assert "no adhesive or interface-friction credit" in ply.description
        inner, outer = [p.shape for p in plies]
        assert abs(inner.Center().x) < abs(outer.Center().x)
        assert inner.intersect(outer).Volume() < .01
        assert inner.distance(outer) == pytest.approx(0, abs=1e-5)
        reconstructed = inner.fuse(outer)
        assert reconstructed.cut(part.shape).Volume() < .01
        assert part.shape.cut(reconstructed).Volume() == pytest.approx(
            3 * math.pi * 5**2 * 38.1 if drilled else 0, abs=.01)


def test_three_member_upper_bolts_and_internal_stitch_graph():
    old = {c.name: c for c in baseline.connections()}
    current = {c.name: c for c in frame.connections()}
    assert len(current) == len(frame.connections()) == 226
    assert current.keys() == old.keys() | {
        f"leg_stitch_{side}_{index}" for side in ("left", "right") for index in (1, 2, 3)}
    parts = {p.name: p for p in frame.parts()}
    adjacency = {name: set() for name in parts}
    stitches = []
    upper = []
    for connection in frame.connections():
        assert set(connection.members) <= parts.keys()
        for member in connection.members:
            adjacency[member].update(set(connection.members) - {member})
        if connection.name.startswith("leg_stitch_"):
            stitches.append(connection)
            assert connection.grip == pytest.approx(38.1)
            assert connection.length - connection.grip - 4 - 9 == pytest.approx(6.05)
            assert len(connection.members) == 2
            assert all(name.startswith("leg_") for name in connection.members)
        elif connection.name.startswith("analysis_leg_wall_bolt_"):
            upper.append(connection)
            side = "left" if "left" in connection.name else "right"
            assert connection.members == (f"box_side_{side}", f"leg_{side}_inner", f"leg_{side}_outer")
            assert connection.start == old[connection.name].start
            assert connection.length == old[connection.name].length
            assert connection.grip == pytest.approx(76.2)
        else:
            assert connection is old[connection.name]
    assert len(stitches) == 6 and len(upper) == 8
    reached, todo = set(), [next(iter(parts))]
    while todo:
        name = todo.pop()
        if name not in reached:
            reached.add(name)
            todo.extend(adjacency[name] - reached)
    assert reached == parts.keys()
    # All seven bores remain inside each ply, with a complete material annulus.
    for connection in stitches + upper:
        for member in connection.members:
            if not member.startswith("leg_"):
                continue
            shape = parts[member].shape
            start = cq.Vector(shape.BoundingBox().xmin, connection.start.y, connection.start.z)
            # Include the documented 30 mm face-bearing envelope, in addition
            # to the actual nominal 25.4 mm washers on the generic hardware.
            for radius, area in ((5, 0), (6, math.pi*(6**2-5**2)), (15, math.pi*(15**2-5**2))):
                probe = cq.Solid.makeCylinder(radius, 19.05, start, cq.Vector(1, 0, 0))
                assert probe.intersect(shape).Volume() == pytest.approx(area*19.05, abs=.01)


def test_stitch_hardware_access_and_floor_clearances():
    parts = frame.parts()
    connections = frame.connections()
    for stitch in (c for c in connections if c.name.startswith("leg_stitch_")):
        components = stitch.components()
        assert all(component.BoundingBox().zmin > 0 for component in components)
        for component in components:
            assert all(component.intersect(part.shape).Volume() < .01 for part in parts)
        # 36 mm nominal socket/access cylinder on both exposed faces and through
        # the stack. Receivers are intentional; every other object must clear.
        access = cq.Solid.makeCylinder(18, 80, stitch.start-stitch.direction*18, stitch.direction)
        assert all(access.intersect(p.shape).Volume() < .01 for p in parts if p.name not in stitch.members)
        assert all(access.intersect(shape).Volume() < .01 for c in connections if c.name != stitch.name
                   for shape in c.components())


def test_real_predecessor_export_does_not_change_ply_geometry_or_artifacts(tmp_path):
    # A fresh process avoids inheriting triangulations or already-split cached
    # plies from another test. Exercise the actual predecessor exporter before
    # rebuilding the independent plies, not a mocked BoundingBox return value.
    script = dedent('''
        import hashlib
        import math
        import sys
        from pathlib import Path

        import cadquery as cq

        from mini_moonboard import independent_leg_frame as frame
        from mini_moonboard import joint_exports, joint_frame
        from mini_moonboard.box_exports import exact_bounds
        from mini_moonboard.export import _export_step

        root = Path(sys.argv[1])
        cold = {p.name: p.shape for p in frame.parts() if p.name.startswith("leg_")}
        sources = {p.name: p.shape for p in joint_frame.parts(True) if p.name.startswith("leg_")}

        def artifacts(plies, directory):
            directory.mkdir()
            assembly = cq.Assembly(name="independent_leg_profiles")
            for name, shape in plies.items():
                assembly.add(shape, name=name)
                cq.exporters.export(shape, str(directory / (name + ".stl")),
                                    cq.exporters.ExportTypes.STL, tolerance=.5)
            _export_step(assembly, directory / "legs.step")
            return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}

        before = artifacts(cold, root / "cold")
        # Real sequence: each STL, normalized STEP, front raster and rotated
        # rear raster, including their cached display tessellations.
        joint_exports.export(root / "predecessor", root / "viewer")
        frame.parts.cache_clear()
        warm = {p.name: p.shape for p in frame.parts() if p.name.startswith("leg_")}
        assert warm.keys() == cold.keys()
        for name, shape in warm.items():
            bounds = exact_bounds(shape)
            assert abs(bounds.xlen - 19.05) < 1e-8, (name, bounds.xlen)
            assert abs(bounds.zmin) < 1e-8, (name, bounds.zmin)
            assert shape.cut(cold[name]).Volume() < 1e-5, name
            assert cold[name].cut(shape).Volume() < 1e-5, name
        for side in ("left", "right"):
            inner, outer = (warm[f"leg_{side}_{layer}"] for layer in ("inner", "outer"))
            assert inner.distance(outer) < 1e-8, side
            combined = inner.fuse(outer)
            original = sources["leg_" + side]
            assert combined.cut(original).Volume() < 1e-5, side
            removed = original.cut(combined).Volume()
            assert abs(removed - 3 * math.pi * 5**2 * 38.1) < .01, (side, removed)
        assert artifacts(warm, root / "warm") == before
    ''')
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
