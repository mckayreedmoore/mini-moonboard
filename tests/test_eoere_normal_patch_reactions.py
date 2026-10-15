"""Finite-area conjugates, residual transfer and reaction-bound controls."""
import hashlib
import math
from collections import defaultdict
from fractions import Fraction as F

import pytest

from scripts import eoere_elastic_core_certificate as core
from scripts import eoere_normal_patch_reactions as model
from scripts import eoere_normal_patch_recession as transfer
from scripts import eoere_normal_patch_trace as trace
from scripts import eoere_original_load_bounds as bounds


def ref(path):
    return {'path': path, 'sha256': hashlib.sha256((model.ROOT/path).read_bytes()).hexdigest()}


def method():
    return trace.methods({'definition_loader': ref('scripts/eoere_cleat_traction_witness.py'),
        'polynomial_helper': ref('scripts/eoere_cleat_virtual_work.py'),
        'bernstein_helper': ref('scripts/eoere_cleat_section_reference.py'),
        'pure_helpers': {'rational': ref('scripts/eoere_section_patches.py'),
                         'polygon': ref('scripts/eoere_cleat_section_dual.py'),
                         'pi': ref('scripts/eoere_curved_bend_field.py')}}, {})


def fixture():
    domain = {'origin_xyz_mm': [0, 0, 2], 'basis_rows_xyz': [[1, 0, 0], [0, 1, 0]],
              'polygon': [[-40, -20], [40, -20], [40, 20], [-40, 20]],
              'holes': [[-12, 0, 5], [12, 0, 5]], 'samples': [[-20, -10], [-20, 10], [20, -10], [20, 10]]}
    timber = {'start': [-10, 0, 0], 'axis': [1, 0, 0], 'stations': [0, 10, 20],
              'index': [list(range(6*i, 6*i+6)) for i in range(3)]}
    port = {'point_reference_xyz_mm': [0, 0, 0]}
    return domain, timber, port, list(range(18, 24))


def test_constant_pressure_conjugate_has_zero_gap_at_known_solution():
    # A=3, kappa=2, c=1/4 => integral force 3/2 and energy 3/16.
    assert model.distributed_gap(F(3, 16), [0], [{'stiffness': F(6)}], [F(3, 2)], [F(0)], [F(1, 4)]) == 0


def test_pressure_reaction_change_attains_the_gap_bound_on_a_constant_bed():
    gap = model.distributed_gap(F(27, 16), [0], [{'stiffness': F(6)}], [F(3, 2)], [F(0)], [F(3, 4)])
    assert gap == F(3, 4)
    result = bounds.functional([{0: F(1)}], [F(3, 2)], [0], [6], gap)
    assert F(result['exact_equilibrium_change_norm_upper']) == 3
    assert F(result['exact_norm_upper']) == F(9, 2)


def test_conjugate_includes_energy_outside_dual_support_and_opening_work():
    # c=x on [-1,1], kappa=1. Trial pressure 1/4 only on [-1,0].
    # The dual-supported region opens, while the other half closes.
    gap = model.distributed_gap(F(1, 6), [0], [{'stiffness': F(1)}], [F(1, 4)], [F(0)], [-F(1, 2)])
    assert gap == F(31, 96)


def test_dual_correction_box_uses_both_quadratic_and_work_uncertainties():
    result = model.distributed_gap(F(2), [0], [{'stiffness': F(3)}], [F(2)], [F(1, 10)], [-F(1, 3)])
    for direction in (-1, 1):
        actual = F(2)+((F(2)+direction*F(1, 10))**2)/6+(F(2)+direction*F(1, 10))/3
        assert result >= actual
    with pytest.raises(ValueError, match='nonnegative dual'):
        model.distributed_gap(1, [0], [{'stiffness': F(1)}], [F(0)], [F(1)], [F(0)])


def test_material_boxes_shrink_for_holes_and_remain_disjoint():
    domain, *_ = fixture()
    half, polygons = model.material_boxes(domain, F(8), trace, method())
    assert half == 4 and len(polygons) == 4
    assert all(transfer.material_box(domain, c, half, trace, method()) == p
               for c, p in zip(domain['samples'], polygons, strict=True))


def test_overlap_is_not_treated_as_disjoint_pressure_support():
    assert model.disjoint([(0, 1, 0, 1), (1, 2, 0, 1)])
    assert not model.disjoint([(0, 2, 0, 2), (1, 3, 1, 3)])
    domain, *_ = fixture(); domain['samples'] = [[0, 10], [1, 10]]
    half, _ = model.material_boxes(domain, F(8), trace, method())
    assert half == F(1, 2)


def test_source_on_a_hole_or_boundary_is_refused_instead_of_moved():
    domain, *_ = fixture()
    for bad in [[[-12, 0]], [[40, 10]]]:
        with pytest.raises(ValueError, match='no certified'):
            model.material_boxes(dict(domain, samples=bad), F(8), trace, method())


def test_relevant_coordinates_cover_clamps_and_both_sides_of_station_knot():
    _, timber, _, fitting = fixture()
    assert model.relevant_coordinates(timber, fitting, [{'mode': 'interior', 'segment': 0}, {'mode': 'interior', 'segment': 1}]) == list(range(24))
    assert model.relevant_coordinates(timber, fitting, [{'mode': 'after', 'segment': 1}]) == list(range(12, 24))
    with pytest.raises(ValueError, match='station mode'):
        model.relevant_coordinates(timber, fitting, [{'mode': 'unregistered', 'segment': 0}])


def test_full_coordinate_average_matches_direct_pose_across_knot():
    domain, timber, port, indices = fixture(); helper = method()
    polygon = transfer.material_box(domain, (0, 10), F(1), trace, helper)
    regions = trace.pieces(dict(domain, polygon=polygon), timber, helper.geometry, helper.poly)
    coordinates = model.relevant_coordinates(timber, indices, regions)
    row, _, area = transfer.average_compression_row(domain, polygon, timber, port, indices,
        {i: defaultdict(F, {i: F(1)}) for i in coordinates}, [0, 0, 1], trace, helper)
    pose = defaultdict(F, {i: F((-1)**i*(i+1), 17) for i in range(24)})
    direct, _, _ = transfer.average_compression_row(domain, polygon, timber, port, indices, {0: pose}, [0, 0, 1], trace, helper)
    assert area == 4 and core.action([row], pose)[0] == direct[0]
    assert row[8] == F(19, 20)


def certificates():
    return [{'body': 'coupon', 'coordinates': 2, 'global_coordinates': [0, 1], 'datum_local_coordinates': [0],
             'quotient_positive_certificate': {'exact_smallest_eigenvalue_lower': '2'},
             'constructed_core_PSD_and_exact_registered_kernel_proven': True}]


def test_complementary_residual_transfer_attains_known_scalar_bound():
    # K0=diag(0,2), old residual h=(0,2), change=(0,3).
    value, records = model.residual_transfer([{1: F(3)}], [{}], [F(1)], [F(0)], [F(0)], certificates(),
        [{'body': 'coupon', 'exact_complementary_residual_square_upper': '2'}], core, bounds)
    assert value >= F(25, 2) and value-F(25, 2) < F(1, 10**22)
    assert F(records[0]['exact_changed_dual_load_square_upper_nmm']) == F(9, 2)


def test_residual_transfer_retains_tiny_nonzero_rows_and_both_corrections():
    epsilon = F(1, 10**30)
    value, rows = model.residual_transfer([{1: F(1)}], [{1: 1+epsilon}], [F(2)], [epsilon], [epsilon], certificates(),
        [{'body': 'coupon', 'exact_complementary_residual_square_upper': '0'}], core, bounds)
    assert value > 0 and F(rows[0]['exact_changed_dual_load_square_upper_nmm']) > 0
    with pytest.raises(ValueError, match='body residual'):
        model.residual_transfer([{}], [{}], [F(1)], [F(0)], [F(0)], certificates(),
            [{'body': 'other', 'exact_complementary_residual_square_upper': '0'}], core, bounds)


def test_unchanged_gap_keeps_clearance_and_skips_only_replaced_flange_law():
    ports = [{'type': 'vector', 'descriptor': {'kind': 'bearing', 'ka': 0, 'kl': 2, 'clearance': 1, 'tension_only': True},
              'columns': [None, 0, 1]},
             {'type': 'normal', 'descriptor': {'kind': 'flange_contact'}, 'columns': [2]},
             {'type': 'normal', 'descriptor': {'kind': 'floor_normal', 'stiffness': 3}, 'columns': [3]}]
    # Lateral travel=1, force=2 gives zero gap; opening floor with positive dual gives nonzero gap.
    result = model.unchanged_gaps(ports, [F(2), F(0), F(999), F(1)], [F(0)]*4, [F(2), F(0), F(0), -F(1)], bounds)
    assert result == {'bearing': F(0), 'floor_normal': bounds.upper(F(7, 6))}


def test_captured_source_is_verified_before_execution(tmp_path, monkeypatch):
    path = tmp_path/'foreign.py'; path.write_text('raise RuntimeError("must not run")\n')
    monkeypatch.setattr(model, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='source changed'):
        model.private({'path': 'foreign.py', 'sha256': '0'*64}, {})


def test_pure_bound_functions_do_not_require_a_static_or_response_solver(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('no new solve is needed for these proof steps')
    monkeypatch.setattr(bounds, 'nearby_witness', forbidden)
    monkeypatch.setattr(core, 'exact_inverse', forbidden)
    monkeypatch.setattr(core, 'shifted_cholesky', forbidden)
    assert model.distributed_gap(0, [0], [{'stiffness': F(1)}], [F(0)], [F(0)], [F(0)]) == 0
    result, _ = model.residual_transfer([{}], [{}], [F(0)], [F(0)], [F(0)], certificates(),
        [{'body': 'coupon', 'exact_complementary_residual_square_upper': '0'}], core, bounds)
    assert result == 0


def test_finite_box_pressure_is_an_auxiliary_field_not_point_contact_energy():
    # On a domain of area 2, a unit pressure supported on half the domain has
    # conjugate 1/2 at kappa=1. Treating it as a point/whole-domain spring gives 1/4.
    gap = model.distributed_gap(F(1), [0], [{'stiffness': F(1)}], [F(1)], [F(0)], [F(0)])
    assert gap == F(3, 2) and gap != F(5, 4)
    assert math.isfinite(float(gap))


def test_continuous_resultant_metric_uses_full_patch_not_dual_support_area():
    domain, *_ = fixture()
    nominal = {'patch': {'analytic_domain': domain, 'declared_existing_stiffness_n_mm3': 2}}
    records = [{'patch_id': 'patch', 'column': j, 'exact_area_mm2': '1'} for j in range(4)]
    result, = model.patch_resultants(records, nominal, [F(1)]*4, [F(0)]*4, F(1), method(), bounds)
    assert result['exact_material_area_upper_mm2'] == '3200'
    assert result['normal_resultant']['exact_weighted_Gram_spectral_upper'] == '6400'
    assert F(result['normal_resultant']['exact_equilibrium_change_norm_upper']) > 100


def test_conditional_scope_cannot_claim_structural_acceptance(tmp_path, monkeypatch):
    path = tmp_path/'input.json'; path.write_text('{"schema":"other"}')
    monkeypatch.setattr(model, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='scope, input and runtime'):
        model.run({'path': 'input.json', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})


def test_credited_normal_resultant_error_can_be_inconclusive_without_failure():
    fixture_ports = [{'descriptor': {'id': f'floor-{i}', 'kind': 'floor_normal', 'first': 'leg', 'direction_xyz': [0., 0., 1.]},
                      'columns': [i]} for i in range(4)]
    functional = lambda rows, x, r, k, gap: bounds.functional(rows, x, r, k, gap)
    loader = model.private(ref('scripts/eoere_cleat_traction_witness.py'), {})
    audit = loader.definitions(ref('scripts/eoere_original_load_audit.py'), ('functional', 'rear_leg'), (),
                               {'F': F, 'method': bounds}, {})
    # Existing result contract distinguishes a nonpositive lower bound from an unbearing state.
    result = audit.rear_leg(fixture_ports, 'leg', [F(1)]*4, [F(0)]*4, [F(1)]*4, F(100))
    assert result['strict_positive_normal_resultant_certified'] is False
    assert F(result['normal_resultant']['exact_scalar_lower']) < 0
    assert functional([{i: F(1) for i in range(4)}], [F(1)]*4, [F(0)]*4, [F(1)]*4, F(0))['exact_scalar_lower'] == '4'
