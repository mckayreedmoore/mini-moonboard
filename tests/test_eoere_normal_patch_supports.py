"""Material unions, exact moments and affine majorants with known answers."""
import ast
import hashlib
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_elastic_core_certificate as core
from scripts import eoere_normal_patch_reactions as base
from scripts import eoere_normal_patch_recession as transfer
from scripts import eoere_normal_patch_supports as model
from scripts import eoere_normal_patch_trace as trace
from scripts import eoere_original_load_bounds as bounds


def ref(path):
    return {'path': path, 'sha256': hashlib.sha256((model.ROOT/path).read_bytes()).hexdigest()}


def helpers():
    method = trace.methods({'definition_loader': ref('scripts/eoere_cleat_traction_witness.py'),
        'polynomial_helper': ref('scripts/eoere_cleat_virtual_work.py'), 'bernstein_helper': ref('scripts/eoere_cleat_section_reference.py'),
        'pure_helpers': {'rational': ref('scripts/eoere_section_patches.py'), 'polygon': ref('scripts/eoere_cleat_section_dual.py'),
                         'pi': ref('scripts/eoere_curved_bend_field.py')}}, {})
    return SimpleNamespace(trace=trace, method=method, transfer=transfer, bounds=bounds, core=core,
                           base_disjoint=base.disjoint, base_relevant=base.relevant_coordinates)


def domain():
    return {'origin_xyz_mm': [0, 0, 2], 'basis_rows_xyz': [[1, 0, 0], [0, 1, 0]],
            'polygon': [[-40, -20], [40, -20], [40, 20], [-40, 20]], 'holes': [[-12, 0, 5], [12, 0, 5]],
            'samples': [[-20, -10], [-20, 10], [20, -10], [20, 10]]}


def test_larger_symmetric_supports_keep_exact_material_and_first_moments():
    h = helpers(); d = domain()
    half, supports = model.patch_supports(d, F(49, 50), F(1, 10**6), h)
    assert half == (F(98, 5), F(49, 5)) and len(supports) == 4
    for center, (tiles, area) in zip(d['samples'], supports, strict=True):
        assert area > 600 and len(tiles) > 1
        measures = [h.method.geometry.moments(tile, F(0)) for tile in tiles]
        assert sum(m[0] for m in measures) == area
        assert [sum(m[i+1] for m in measures) for i in range(2)] == [area*x for x in center]
        for tile in tiles:
            box = trace.bounding_box(tile)
            assert all(trace.previous().box_hole_clearance(box, tuple(map(F, hole))) > 0 for hole in d['holes'])


def test_disjoint_outer_boxes_adapt_exactly_to_close_original_centroids():
    h = helpers(); d = dict(domain(), samples=[[0, 10], [1, 10]])
    half, supports = model.patch_supports(d, F(49, 50), F(1, 10**6), h)
    assert half[0] == F(49, 100) and half[1] == F(49, 200)
    assert len(supports) == 2


def test_ghost_hole_exclusion_preserves_centroid_even_when_center_is_a_void():
    h = helpers(); d = dict(domain(), holes=[[0, 0, 1]])
    tiles, area = model.symmetric_tiles(d, [0, 0], [2, 2], F(1, 10), trace, h.method)
    assert area == F(279, 25)
    assert all(trace.previous().box_hole_clearance(trace.bounding_box(t), (F(0), F(0), F(1))) > 0 for t in tiles)


def test_noninterior_or_duplicate_centroids_cannot_be_silently_moved():
    h = helpers()
    for centers in ([], [[40, 10]], [[0, 10], [0, 10]]):
        with pytest.raises(ValueError, match='centroid'):
            model.patch_supports(dict(domain(), samples=centers), F(49, 50), F(1, 10**6), h)


@pytest.mark.parametrize('fraction', [0, 1, -1])
def test_support_margin_requires_strict_positive_fraction(fraction):
    with pytest.raises(ValueError, match='support fraction'):
        model.patch_supports(domain(), fraction, F(1, 10**6), helpers())


def test_union_coordinate_rows_keep_rigid_fitting_first_moment_and_station_knot():
    h = helpers(); d = domain()
    timber = {'start': [-10, 0, 0], 'axis': [1, 0, 0], 'stations': [0, 10, 20],
              'index': [list(range(6*i, 6*i+6)) for i in range(3)]}
    indices = list(range(18, 24)); port = {'point_reference_xyz_mm': [0, 0, 0]}
    tiles, area = model.symmetric_tiles(d, [0, 10], [1, 1], F(1, 10**6), trace, h.method)
    row, measure, count, moments = model.union_average(d, tiles, timber, port, indices, [0, 0, 1], h)
    assert measure == area == 4 and count == len(moments) == 2
    assert row[8] == F(19, 20) and row[20] == -1
    assert row.get(22, F(0)) == 0 and row[21] == -F(1, 100)
    assert sum(m[0, 0] for m in moments.values()) == 4
    assert sum(m[2, 0] for m in moments.values()) == F(4, 3)
    assert sum(m[0, 2] for m in moments.values()) == F(1204, 3)


@pytest.mark.parametrize('subdivisions', [1, 2, 4])
def test_affine_partial_contact_integrates_exact_known_energy(subdivisions):
    h = helpers(); polygon = model.rectangle([-1, 1, -1, 1])
    upper, cells = model.affine_energy_upper({(1, 0): 1}, polygon, 3, subdivisions, h)
    assert upper >= 1 and upper-1 < F(1, 10**22)
    assert cells == subdivisions**2


def test_constant_open_and_constant_closing_integer_inputs_remain_exact():
    h = helpers(); polygon = model.rectangle([-1, 1, -1, 1])
    assert model.affine_energy_upper({(0, 0): 1}, polygon, 3, 4, h)[0] == 0
    assert model.affine_energy_upper({(0, 0): -2}, polygon, 3, 4, h)[0] == 24


@pytest.mark.parametrize('polynomial, exact', [({(2, 0): 1, (0, 0): -1}, F(16, 15)),
    ({(2, 0): 1, (0, 0): -F(1, 4)}, F(1, 30)), ({(1, 1): 1}, F(1, 9))])
def test_quadratic_positive_part_is_bounded_above_without_assuming_affinity(polynomial, exact):
    h = helpers(); polygon = model.rectangle([-1, 1, -1, 1])
    coarse, _ = model.affine_energy_upper(polynomial, polygon, 1, 1, h)
    fine, _ = model.affine_energy_upper(polynomial, polygon, 1, 4, h)
    assert exact <= fine <= coarse


def test_clipped_triangle_grid_keeps_area_and_known_affine_square_integral():
    # c=x on 0<=y<=x<=1: integral x²*x dx /2 = 1/8.
    upper, cells = model.affine_energy_upper({(1, 0): -1}, [[0, 0], [1, 0], [1, 1]], 1, 4, helpers())
    assert F(1, 8) <= upper < F(1, 8)+F(1, 10**22) and 0 < cells < 16


def test_majorant_refuses_unrepresented_degree_and_invalid_grid():
    h = helpers(); polygon = model.rectangle([-1, 1, -1, 1])
    for polynomial, n in [({(3, 0): 1}, 4), ({(0, 0): 1}, 0), ({(0, 0): 1}, True)]:
        with pytest.raises(ValueError, match='quadratic trace'):
            model.affine_energy_upper(polynomial, polygon, 1, n, h)


def test_driver_ast_changes_only_the_declared_support_keys_and_gate():
    data = (model.ROOT/model.BASE['path']).read_bytes(); before = ast.parse(data)
    after = model.driver_tree(data)
    # Undo exactly the declared changes and compare complete syntax trees.
    run = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    replacements = [n for n in ast.walk(run) if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                    and n.slice.value == 'support_fraction']
    assert len(replacements) == 2
    gate = next(n for n in ast.walk(run) if isinstance(n, ast.Compare) and n.left in replacements)
    assert gate.comparators[0].value == '49/50'
    gate.comparators[0].value = '8'
    for node in replacements:
        node.slice.value = 'material_box_maximum_half_width_mm'
    assert ast.dump(before) == ast.dump(after)
    with pytest.raises(ValueError, match='support-control AST'):
        model.driver_tree(data.replace(b"== '8'", b"== '7'"))


def test_sources_are_authenticated_before_compiling(tmp_path, monkeypatch):
    (tmp_path/'source.py').write_text('raise RuntimeError("do not run")\n')
    monkeypatch.setattr(model, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='source changed'):
        model.private({'path': 'source.py', 'sha256': '0'*64}, {})
