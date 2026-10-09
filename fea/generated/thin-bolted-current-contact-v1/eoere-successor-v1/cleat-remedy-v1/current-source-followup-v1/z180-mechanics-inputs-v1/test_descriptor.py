"""Known-answer geometry/moment checks and fail-closed source/output controls."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import math
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_source_geometry_fixture", OWN.with_name("descriptor.py"))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def test_full_disk_and_offset_half_disk_known_area_first_and_second_moments():
    r, y, z = 3., 7., 11.
    full = d.disk_strip_moments(y, z, r, y-r, y+r)
    area = math.pi*r*r
    assert full == pytest.approx([area, area*y, area*z, area*y*y+math.pi*r**4/4., area*y*z,
                                area*z*z+math.pi*r**4/4.], rel=1e-13)
    half = d.disk_strip_moments(y, z, r, y, y+r)
    a, first = area/2., 2.*r**3/3.
    assert half == pytest.approx([a, a*y+first, a*z, a*y*y+2.*y*first+math.pi*r**4/8.,
                                z*(a*y+first), a*z*z+math.pi*r**4/8.], rel=1e-13)


def test_disk_split_into_arbitrary_y_strips_conserves_all_six_moments():
    cuts = [-20., -1.1, .2, 1.7, 20.]
    pieces = [d.disk_strip_moments(.3, 4., 2., a, b) for a, b in pairwise(cuts)]
    assert [sum(row[i] for row in pieces) for i in range(6)] == pytest.approx(d.disk_strip_moments(.3, 4., 2., -20., 20.), abs=1e-12)


def test_clipped_disk_first_moment_against_independent_numerical_integration():
    # Smooth interior strip avoids singular endpoints; composite Simpson is an
    # independent quadrature of the geometric cross-sections, not the primitive.
    lo, hi, n, radius = -.7, 1.1, 2000, 2.
    sums = [0.]*4
    for i in range(n+1):
        t = lo+(hi-lo)*i/n
        height = math.sqrt(radius*radius-t*t)
        weight = 1 if i in (0, n) else 4 if i % 2 else 2
        values = [2.*height, 2.*t*height, 2.*t*t*height, 2.*height**3/3.]
        sums = [a+weight*b for a, b in zip(sums, values)]
    area, first, yy, zz = [x*(hi-lo)/(3*n) for x in sums]
    actual = d.disk_strip_moments(0., 0., radius, lo, hi)
    assert [actual[i] for i in (0, 1, 3, 5)] == pytest.approx([area, first, yy, zz], abs=2e-12)


def test_rectangular_centroidal_second_moment_known_answer():
    moments = d.rectangle_moments(4., 10., 20., 24.)
    assert d.yz_central(moments) == [[0., 0., 0.], [0., 72., 0.], [0., 0., 32.]]


def test_void_relocation_com_known_answer_and_no_false_mass_change():
    # A1000mm3 body initially centered atZ10 gains the old10mm3 void atZ15,
    # loses the same void atZ5, so its COM rises0.1mm with unchanged volume.
    old = [(10., [20., 30., 150.])]
    new = [(10., [20., 30., 50.])]
    assert d.replace_centroid(1000., [2., 3., 10.], 1000., old, new) == [2., 3., 10.1]
    volume, first = d.cylinder_moments([10., 3., 4.], [-1., 0., 0.], [2., 6.], 2.)
    assert volume == pytest.approx(4.*math.pi)
    assert [x/volume for x in first] == [6., 3., 4.]


def test_cell_translation_moves_void_between_rows_with_correct_area_and_moment():
    upper = d.cell_moments([0., 10., 10., 20.], [(5., 15., 2.)])
    lower = d.cell_moments([0., 10., 0., 10.], [(5., 5., 2.)])
    assert upper[0] == pytest.approx(100.-4.*math.pi)
    assert lower[0] == pytest.approx(upper[0])
    assert upper[2]/upper[0] - lower[2]/lower[0] == pytest.approx(10.)
    with pytest.raises(ValueError, match="crosses Z grid boundary"):
        d.cell_moments([0., 10., 0., 10.], [(5., 9., 2.)])


def profiles_and_axes():
    profiles = {host: {"host": host, "X_interval_mm": [0., 10.] if "post" in host else [-10., 0.],
        "YZ_polygon_mm": [[0., 0.], [100., 0.], [100., 300.], [0., 300.]], "thickness_mm": 10.} for host in d.HOSTS}
    axes = {}
    for side in ("left", "right"):
        for i in (1, 2):
            identity = "cleat_post_bolt_"+side+"_"+str(i)
            axes[identity] = {"id": identity, "receivers": ["base_post_outer_"+side, "eoere_cleat_"+side],
                "point_xyz_mm": [-10., 25.*i, 200.], "direction_xyz": [1., 0., 0.], "bore_diameter_mm": 10.}
        for kind, host in (("post", "base_post_outer_"+side), ("cleat", "eoere_cleat_"+side)):
            for i in (1, 2):
                identity = "retained/"+side+"/"+kind+"/"+str(i)
                axes[identity] = {"id": identity, "receivers": [host], "point_xyz_mm": [-10., 25.*i, 70.],
                    "direction_xyz": [1., 0., 0.], "bore_diameter_mm": 10.}
    new = copy.deepcopy(axes)
    for identity in d.AXES:
        new[identity]["point_xyz_mm"][2] = 180.
    def walls(rows):
        return {(a["id"], host): {"query_point_xyz_mm": a["point_xyz_mm"], "query_direction_xyz": a["direction_xyz"],
            "bore_diameter_mm": a["bore_diameter_mm"], "partial_wall_present": False,
            "full_wall_intervals_mm": [[x+10. for x in profiles[host]["X_interval_mm"]]], "full_wall_length_mm": 10.,
            "matching_cylindrical_faces": [{"full_circumference_wall": True}]} for a in rows.values() for host in a["receivers"]}
    return profiles, axes, new, walls(axes), walls(new)


def test_full_cylinder_proof_includes_all_four_bores_per_host():
    profiles, old, new, old_walls, new_walls = profiles_and_axes()
    assert len(d.prove_cylinders(old, new, old_walls, new_walls, profiles, 1e-6, .001)) == 4


@pytest.mark.parametrize("failure", ["partial_wall", "missing_faces", "wrong_length", "overlap", "truncated_profile"])
def test_missing_or_incompatible_full_cylinder_evidence_rejected(failure):
    profiles, old, new, old_walls, new_walls = profiles_and_axes()
    key = d.AXES[0], "eoere_cleat_left"
    if failure == "partial_wall":
        new_walls[key]["partial_wall_present"] = True
    elif failure == "missing_faces":
        new_walls[key]["matching_cylindrical_faces"] = []
    elif failure == "wrong_length":
        new_walls[key]["full_wall_length_mm"] = 9.
    elif failure == "overlap":
        new[d.AXES[1]]["point_xyz_mm"][1] = 25.
    else:
        profiles["eoere_cleat_left"]["YZ_polygon_mm"] = [[20., 0.], [100., 0.], [100., 300.], [20., 300.]]
    with pytest.raises(ValueError):
        d.prove_cylinders(old, new, old_walls, new_walls, profiles, 1e-6, .001)


def test_unchanged_region_sweep_proof_requires_whole_region_clearance():
    profiles, old, new, _, _ = profiles_and_axes()
    host = "base_post_outer_left"
    proof = d.swept_separation([0., 0., 0., 100., 0., 100.], host, profiles, old, new, 1e-6)
    assert len(proof) == 2 and all(row["separating_coordinate"] == "Z" for row in proof)
    with pytest.raises(ValueError, match="intersects old/new bore sweep"):
        d.swept_separation([0., 0., 0., 100., 170., 210.], host, profiles, old, new, 1e-6)


def test_analytic_material_reference_and_negative_void_proof():
    profiles, _, new, _, _ = profiles_and_axes()
    own = [profiles["base_post_outer_left"], profiles["eoere_cleat_left"]]
    assert d.material_at_reference([0., 75., 180.], [1., 0., 0.], own, list(new.values()))["both_own_material_probes_proved"]
    with pytest.raises(ValueError, match="outside material"):
        d.material_at_reference([0., 25., 180.], [1., 0., 0.], own, list(new.values()))


def test_six_cell_patch_clipping_retains_ids_and_exact_area_first_moments():
    profiles, old, new, _, _ = profiles_and_axes()
    own = [profiles["base_post_outer_left"], profiles["eoere_cleat_left"]]
    for profile in own:
        profile["YZ_polygon_mm"] = [[0., 0.], [140., 0.], [140., 300.], [0., 300.]]
    # The second hole crosses a Y grid cut. Both Z positions fit wholly in
    # their respective source rows; reversed source-cell order tests ID joins.
    cells = [{"id": str(iy)+"/"+str(iz), "point_xyz_mm": [0., (iy+.5)*140./3., 140.+(iz+.5)*50.]}
             for iy in range(3) for iz in range(2)]
    patch = {"trimmed_region_geometry": {"bounds_xyz_mm": [0., 0., 0., 140., 140., 240.]},
        "effective_cell_size_mm": 50., "occupancy_refinement_levels": 0, "cells": cells[::-1],
        "normal_from_second_to_first_xyz": [1., 0., 0.]}
    evaluated = []
    for axes in (old, new):
        disks = [(*axes[axis]["point_xyz_mm"][1:], 5.) for axis in d.AXES[:2]]
        evaluated.append(d.patch_cells(patch, disks, profiles=own, all_axes=list(axes.values())))
    before, after = evaluated
    expected_area = 140.*100.-2.*math.pi*25.
    assert before[1] == pytest.approx(expected_area)
    assert after[1] == pytest.approx(expected_area)
    assert (after[2][2]-before[2][2])*expected_area == pytest.approx(2.*math.pi*25.*20.)
    assert {c["id"] for c in after[0]} == {c["id"] for c in cells}
    assert after[3] != after[4] and after[5] > 0.
    assert sum(c["area_mm2"] for c in after[0]) == pytest.approx(expected_area)
    assert all(c["analytic_material_at_reference"]["both_own_material_probes_proved"] for c in after[0])


def test_changed_source_native_flags_are_retired_to_honest_parent_reference():
    original = {"id": "patch", "source_first_face": {"signature_sha256": "old"}, "source_second_face": {},
        "trimmed_region_signature_sha256": "old", "opposed_normal_dot": -1., "occupancy_refinement_levels": 0,
        "cells": [{"id": "cell", "both_inward_material_probes_occupied": True,
                   "reference_centroid_on_trimmed_patch": True, "reference_centroid_patch_distance_mm": 0.}]}
    fresh = copy.deepcopy(original)
    d.retire_native_patch_claims(fresh, {"path": "old-export", "sha256": "old-sha"}, original)
    assert "source_first_face" not in fresh and "trimmed_region_signature_sha256" not in fresh
    assert fresh["cells"] == [{"id": "cell"}]
    assert fresh["inherited_native_observation"]["observed_geometry_is_parent_Z200"] is True


def test_byte_authentication_rejects_hash_tamper_and_foreign_source(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("{}")
    ref = {"path": "source.json", "sha256": d.sha(source)}
    assert d.exact_ref(ref, tmp_path) == source
    source.write_text("changed")
    with pytest.raises(ValueError, match="source bytes differ"):
        d.exact_ref(ref, tmp_path)
    with pytest.raises(ValueError, match="relative source"):
        d.exact_ref({"path": str(source), "sha256": d.sha(source)}, tmp_path)


@pytest.mark.parametrize("kind", ["file", "dangling_link"])
def test_fresh_output_reserved_before_source_intake(tmp_path, kind):
    own = tmp_path / "packet/descriptor.py"
    out = own.parent / "runs-v1/existing.json"
    out.parent.mkdir(parents=True)
    if kind == "file":
        out.write_text("preserved")
    else:
        out.symlink_to(out.with_name("missing.json"))
    with patch.object(d, "OWN", own), patch.object(d, "load_inputs", side_effect=AssertionError("source intake reached")), pytest.raises(FileExistsError):
        d.write_descriptor(tmp_path / "inputs.json", "x", out)
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()


def test_failed_source_attempt_remains_reserved(tmp_path):
    own = tmp_path / "packet/descriptor.py"
    out = own.parent / "runs-v1/failure.json"
    with patch.object(d, "OWN", own), patch.object(d, "load_inputs", side_effect=ValueError("input hash tamper")):
        with pytest.raises(ValueError, match="input hash tamper"):
            d.write_descriptor(tmp_path / "inputs.json", "x", out)
        assert json.loads(out.read_bytes())["status"] == "FAILED"
        with pytest.raises(FileExistsError):
            d.write_descriptor(tmp_path / "inputs.json", "x", out)


def test_simultaneous_same_output_allows_one_intake_only(tmp_path):
    own = tmp_path / "packet/descriptor.py"
    out = own.parent / "runs-v1/race.json"
    start = Barrier(2)
    def invoke():
        start.wait(timeout=5)
        try:
            d.write_descriptor(tmp_path / "inputs.json", "x", out)
        except FileExistsError:
            return "reserved"
        return "written"
    loaded = {"source_sha256": {}, "root": tmp_path}
    result = {"geometry_delta_proof": {"counts": {}}, "release": d.RELEASE}
    with patch.object(d, "ROOT", tmp_path), patch.object(d, "OWN", own), \
            patch.object(d, "load_inputs", return_value=loaded) as intake, \
            patch.object(d, "build_descriptor", return_value=result), patch.object(d, "verify"), ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(invoke) for _ in range(2)]
        assert sorted(future.result(timeout=5) for future in futures) == ["reserved", "written"]
        assert intake.call_count == 1
    assert json.loads(out.read_bytes())["source_pins_before_after_unchanged"] is True


def test_imports_are_standard_library_only_without_CAD_numpy_or_mechanics():
    tree = ast.parse(OWN.with_name("descriptor.py").read_bytes())
    names = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    names |= {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert names == {"__future__", "argparse", "copy", "hashlib", "json", "math", "os", "pathlib"}
