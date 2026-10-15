"""Exact integration, cone relaxation and inherited rank/weight controls."""
import hashlib
import math
import sys
from collections import defaultdict
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from scripts import eoere_normal_patch_recession as model
from scripts import eoere_normal_patch_trace as trace
from scripts import eoere_recession_certificate as exact


def ref(path):
    return {'path':path,'sha256':hashlib.sha256((model.ROOT/path).read_bytes()).hexdigest()}


def method():
    return trace.methods({'definition_loader':ref('scripts/eoere_cleat_traction_witness.py'),
                          'polynomial_helper':ref('scripts/eoere_cleat_virtual_work.py'),
                          'bernstein_helper':ref('scripts/eoere_cleat_section_reference.py'),
                          'pure_helpers':{'rational':ref('scripts/eoere_section_patches.py'),
                                          'polygon':ref('scripts/eoere_cleat_section_dual.py'),
                                          'pi':ref('scripts/eoere_curved_bend_field.py')}},{})


def fixture():
    domain={'origin_xyz_mm':[0,0,2],'basis_rows_xyz':[[1,0,0],[0,1,0]],
            'polygon':[[-40,-20],[40,-20],[40,20],[-40,20]],'holes':[[-12,0,5],[12,0,5]]}
    timber={'start':[-10,0,0],'axis':[1,0,0],'stations':[0,10,20],
            'index':[list(range(6*i,6*i+6)) for i in range(3)]}
    port={'point_reference_xyz_mm':[0,0,0]}
    return domain,timber,port,list(range(18,24))


@pytest.mark.parametrize('powers',[(0,0),(1,0),(0,1),(2,0),(1,1),(0,2)])
def test_triangle_rule_is_exact_for_every_quadratic_monomial(powers):
    i,j=powers
    actual=model.triangle_integral({powers:F(1)},[(F(0),F(0)),(F(1),F(0)),(F(0),F(1))],method().poly.evaluate)
    assert actual == F(math.factorial(i)*math.factorial(j),math.factorial(i+j+2))


def test_polygon_fan_integral_has_known_mixed_moment_and_rejects_wrong_domain():
    polygon=[(F(-2),F(1)),(F(4),F(1)),(F(4),F(5)),(F(-2),F(5))]
    assert model.triangle_integral({(1,1):F(1)},polygon,method().poly.evaluate)==72
    with pytest.raises(ValueError,match='counterclockwise'):
        model.triangle_integral({(0,0):F(1)},polygon[::-1],method().poly.evaluate)
    with pytest.raises(ValueError,match='quadratic'):
        model.triangle_integral({(3,0):F(1)},polygon,method().poly.evaluate)


def test_integer_and_stored_float_geometry_keep_exact_real_arithmetic():
    helper=method()
    result=model.triangle_integral({(0,0):.1},[(0,0),(1,0),(0,1)],helper.poly.evaluate)
    assert isinstance(result,F) and result==F(.1)/2


def test_box_average_covers_both_sides_of_a_station_knot_exactly():
    domain,timber,port,indices=fixture(); helper=method()
    polygon=model.material_box(domain,(0,10),F(1),trace,helper)
    pose=defaultdict(F,{8:F(1)})
    row,regions,area=model.average_compression_row(domain,polygon,timber,port,indices,{7:pose},[0,0,1],trace,helper)
    assert len(regions)==2 and area==4 and row=={7:F(19,20)}


def test_constant_gap_average_and_endpoint_clamps_keep_exact_sign_and_area():
    domain,timber,port,indices=fixture(); helper=method()
    pose=defaultdict(F,{20:F(1,8)})
    for center in [(-35,10),(0,10),(35,10)]:
        polygon=model.material_box(domain,center,F(1,3),trace,helper)
        row,_,area=model.average_compression_row(domain,polygon,timber,port,indices,{3:pose},[0,0,1],trace,helper)
        assert row=={3:-F(1,8)} and area==F(4,9)


def test_material_boxes_refuse_holes_edges_and_zero_area():
    domain,*_=fixture(); helper=method()
    for center,half in [((-12,0),F(1)),((40,10),F(1)),((0,10),F(0))]:
        with pytest.raises(ValueError):
            model.material_box(domain,center,half,trace,helper)


def test_average_constraints_are_only_a_relaxation_of_continuous_contact():
    domain,timber,port,indices=fixture(); helper=method()
    pose=defaultdict(F,{20:F(3,100),22:F(1)})
    for center in [(-20,-10),(-20,10),(20,-10),(20,10)]:
        polygon=model.material_box(domain,center,F(1,10000),trace,helper)
        row,_,_=model.average_compression_row(domain,polygon,timber,port,indices,{0:pose},[0,0,1],trace,helper)
        assert row[0] < 0
    # All auxiliary constraints can open while unsampled material still closes.
    result=trace.trace(domain,timber,port,indices,pose,[0,0,1],1,helper)
    assert F(result['material_witness']['exact_normal_force_lower_n']) > 0


def rank_fixture():
    rows=[{1:F(1)},{2:F(1)}];selected=[1,2]
    proof={'full_rank_proven':True,'minor_dimension':2,'exact_minor_sha256':exact.matrix_digest(exact.minor(rows,selected)),
           'exact_inverse_norm_upper':'1'}
    return rows,selected,proof


def test_neumann_transfer_uses_a_nonprefix_minor_and_retains_tiny_changes():
    old,selected,prior=rank_fixture();epsilon=F(1,10**60)
    new=[{1:1-epsilon},{2:1+epsilon}]
    rank=model.perturb_rank(old,new,selected,prior,exact)
    assert rank['full_rank_proven'] is True
    assert F(rank['exact_minor_perturbation_inf'])==F(rank['exact_Neumann_product_upper'])==epsilon
    assert F(rank['exact_inverse_norm_upper'])==1/(1-epsilon)
    proof=exact.certify(new,3,1,[1,1],[0,1,1],selected,rank)
    assert F(proof['exact_selected_correction_inf_upper'])==epsilon/(1-epsilon)
    assert F(proof['exact_strict_weight_margin_lower'])>0


def test_inconclusive_perturbation_is_not_a_singularity_or_nonexistence_claim():
    old,selected,prior=rank_fixture()
    rank=model.perturb_rank(old,[{1:F(2)},{2:F(1)}],selected,prior,exact)
    assert rank['full_rank_proven'] is False and rank['exact_inverse_norm_upper'] is None
    with pytest.raises(ValueError,match='original certified minor'):
        model.perturb_rank(old,old,selected,dict(prior,exact_minor_sha256='0'*64),exact)


def test_zero_change_reuses_the_bound_exactly_and_does_not_count_unselected_columns():
    old,selected,prior=rank_fixture();new=[{0:F(10**20),1:F(1)},{2:F(1)}]
    proof=model.perturb_rank(old,new,selected,prior,exact)
    assert proof['exact_minor_perturbation_inf']=='0' and proof['exact_inverse_norm_upper']=='1'


def test_case_check_refuses_a_different_original_load_before_any_proof():
    keys=('binding','operator_bundle','exact_constraint_matrix_sha256','exact_registered_rigid_basis_sha256',
          'exact_rigid_load_sha256','original_applied_binary64_sha256')
    old={k:'same' for k in keys}; imported=dict(old,exact_rigid_load_sha256='other')
    with pytest.raises(ValueError,match='unchanged own original'):
        model.case_check([],imported,old,{},[],exact)


def test_uncertified_auxiliary_weights_are_reported_without_a_nonexistence_claim():
    rows,selected,rank=rank_fixture()
    keys=('binding','operator_bundle','exact_constraint_matrix_sha256','exact_registered_rigid_basis_sha256',
          'exact_rigid_load_sha256','original_applied_binary64_sha256')
    common={k:'same' for k in keys}
    imported=dict(common,columns=3,bilateral=1,load=[-1,-1]);old=dict(common,candidate_auxiliary_weights=[0,1,1])
    result=model.case_check(rows,imported,old,rank,selected,exact)
    assert result['strict_exact_certificate_proven'] is False
    assert result['reason']=='strict one-sided exact witness not certified'
    result=model.case_check(rows,imported,old,dict(rank,full_rank_proven=False),selected,exact)
    assert result['strict_exact_certificate_proven'] is False and 'inconclusive' in result['reason']


def test_private_capture_ignores_ordinary_cached_helpers(monkeypatch):
    sentinel=SimpleNamespace(rational=lambda _: 'foreign')
    monkeypatch.setitem(sys.modules,'scripts.eoere_recession_certificate',sentinel)
    module=model.private(ref('scripts/eoere_recession_certificate.py'),{})
    assert module is not sentinel and module.rational(.1)==F(.1)
    assert sys.modules['scripts.eoere_recession_certificate'] is sentinel
