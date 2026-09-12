"""APA unit conversions and hold contact equilibrium, without effective widths."""
import hashlib
import json
import math
from pathlib import Path

import pytest

from fea.reinforced_panel_checks import (
    LBF_N,
    hold_demand,
    panel_reference,
    section_check,
    size_factor,
)


def case(**overrides):
    inputs={'downward_n':600*LBF_N,'horizontal_outward_n':300.,'angle_deg':40.,
            'standoff_mm':100.,'contact_lever_arm_mm':50.,'flange_diameter_mm':25.4,
            'panel_hole_mm':11.112,'retention_hole_mm':3.2,'retention_hole_count':3}
    return hold_demand(**(inputs|overrides))


def test_normal_only_load_exceeds_even_impossible_unperforated_flange():
    r=case(standoff_mm=0.)
    assert r['gross_disk_bearing_reference_n']==pytest.approx(360*math.pi/4*LBF_N)
    assert r['normal_outward_n']==pytest.approx(1945.3703765932692)
    assert r['gross_disk_reference_exceeded_without_standoff']
    assert r['normal_only_gross_disk_ratio'] > 1.54
    assert r['normal_only_net_bearing_ratio'] > 2.


def test_hold_tension_and_compression_close_actual_couple():
    r=case()
    compression=r['minimum_bolt_tension_n']-r['normal_outward_n']
    assert compression*50. == pytest.approx(r['tangential_n']*100.)
    assert r['minimum_bolt_tension_n']==pytest.approx(5648.740350939783)
    assert case(contact_lever_arm_mm=25.)['minimum_bolt_tension_n'] > r['minimum_bolt_tension_n']
    inward=case(downward_n=0.,horizontal_outward_n=-300.,standoff_mm=0.)
    assert inward['minimum_bolt_tension_n']==0.


def test_apa_family_units_and_narrow_kicker_direction():
    p=panel_reference(1219.2)
    assert p['bending_nmm_per_mm']==pytest.approx(455*.67*LBF_N/12)
    assert p['apparent_ei_per_width_nmm']==pytest.approx(90500*.56*LBF_N*25.4/12)
    assert p['compression_n_per_mm']==pytest.approx(2900*.61*LBF_N/304.8)
    assert size_factor(25.4)==.5
    assert size_factor(1219.2)==1.
    assert size_factor(225.)==pytest.approx(.25+.0313*225/25.4)
    assert panel_reference(225.)['compression_n_per_mm']==p['compression_n_per_mm']


def test_section_check_uses_physical_width_and_signed_axial_demands():
    r=section_check(panel='kicker_left',width_mm=1219.2,height_mm=225.,
        nx_n_per_mm=-30.,ny_n_per_mm=0.,mx_nmm_per_mm=80.,my_nmm_per_mm=0.,
        qx_n_per_mm=0.,qy_n_per_mm=0.,nxy_n_per_mm=0.,deflection_mm=2.,deflection_limit_mm=1.)
    assert set(r['exceeded_components'])=={'axial_x','bending_x','deflection'}
    assert not r['combined_loading_accepted']


def test_saved_report_source_hashes_and_all_independent_panels():
    r=json.loads(Path('fea/results/reinforced-panel-checks-v1.json').read_text())
    assert len(r['panel_references'])==6
    assert r['case_count']==216
    assert not r['global_panel_response_evaluated']
    for path,sha in r['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
    assert r['minimum_same_seam_flange_edge_ligament_mm']==pytest.approx(6.5)
