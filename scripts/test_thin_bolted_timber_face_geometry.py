"""Small geometry checks for the new six-interface query, without frame CAD."""

import math

import cadquery as cq
import numpy as np

from scripts import thin_bolted_timber_face_geometry as query
from scripts import wood_joint_current_face_pair_atlas_attempt01 as atlas


def pair_shapes(*, hole=False, gap=0.):
    first = cq.Solid.makeBox(20., 100., 100., cq.Vector(gap, 0., 0.))
    second = cq.Solid.makeBox(20., 100., 100., cq.Vector(-20., 0., 0.))
    if hole:
        bore = cq.Solid.makeCylinder(5., 40., cq.Vector(-20., 25., 25.), cq.Vector(1., 0., 0.))
        first, second = first.cut(bore), second.cut(bore)
    shapes = {"first": first, "second": second}
    faces = {name: atlas.source_face_records(name, shape) for name, shape in shapes.items()}
    return shapes, faces


def test_finished_rectangle_has_one_opposed_patch_and_exact_moments():
    shapes, faces = pair_shapes()
    patches = query.find_patches("first", "second", faces, shapes, cell_size_mm=25.)
    assert len(patches) == 1
    patch = patches[0]
    assert math.isclose(patch["area_mm2"], 10000., abs_tol=1e-7)
    assert np.allclose(patch["centroid_xyz_mm"], [0., 50., 50.], atol=1e-7)
    assert np.allclose(patch["normal_from_second_to_first_xyz"], [1., 0., 0.], atol=1e-12)
    assert math.isclose(patch["opposed_normal_dot"], -1., abs_tol=1e-12)
    expected = np.diag([0., 10000. * 100.**2 / 12., 10000. * 100.**2 / 12.])
    assert np.allclose(patch["exact_centroidal_second_moment_matrix_xyz_mm4"], expected, atol=1e-5)
    assert math.isclose(patch["second_moment_relative_frobenius_error"], 1. / 16., abs_tol=1e-10)


def test_hole_is_unfilled_and_void_centroid_triggers_refinement():
    shapes, faces = pair_shapes(hole=True)
    patches = query.find_patches("first", "second", faces, shapes, cell_size_mm=50.)
    assert len(patches) == 1
    patch = patches[0]
    hole_area = math.pi * 25.
    expected_area = 10000. - hole_area
    expected_yz = (10000. * 50. - hole_area * 25.) / expected_area
    assert math.isclose(patch["area_mm2"], expected_area, abs_tol=1e-6)
    assert np.allclose(patch["centroid_xyz_mm"], [0., expected_yz, expected_yz], atol=1e-7)
    assert patch["occupancy_refinement_levels"] == 1
    assert patch["trimmed_region_geometry"]["wire_count"] == 2
    assert abs(patch["cell_area_error_mm2"]) < 1e-6
    assert patch["cell_centroid_error_mm"] < 1e-7
    assert all(r["reference_centroid_on_trimmed_patch"] and r["both_inward_material_probes_occupied"]
               for r in patch["cells"])
    assert all(math.hypot(r["point_xyz_mm"][1] - 25., r["point_xyz_mm"][2] - 25.) >= 5. - 1e-7
               for r in patch["cells"])


def test_separated_reference_faces_supply_no_patch():
    shapes, faces = pair_shapes(gap=.1)
    assert query.find_patches("first", "second", faces, shapes, cell_size_mm=25.) == []
