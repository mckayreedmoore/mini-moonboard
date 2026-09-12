"""Independent wrench recovery for restricted proposed-kicker reactions."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fea.round_structural_kicker_revision import solve_case, wrench


@pytest.mark.parametrize('version',[1,2])
def test_every_saved_case_closes_six_equations_and_individual_references(version):
    r=json.loads(Path(f'fea/results/round-structural-kicker-revision-v{version}.json').read_text())
    assert r['case_count'] == r['restricted_reference_witness_count'] == 450
    assert r['maximum_minimax_tension_reference_ratio'] < .9
    for c in r['cases']:
        recovered=np.array(c['applied_wrench_n_nmm'])
        transfer=np.zeros(6)
        for reaction in c['reaction_forces']:
            f=reaction['force_on_panel_n'];p=reaction['point_mm']
            recovered += np.r_[f,[p[1]*f[2]-p[2]*f[1],p[2]*f[0]-p[0]*f[2],p[0]*f[1]-p[1]*f[0]]]
            assert reaction['magnitude_n'] >= -1e-8
            if reaction['kind']=='screw':
                assert f[0] == f[2] == 0
                assert reaction['interaction']['wood_interaction_ratio'] <= 1
                assert reaction['interaction']['head_pull_through_ratio'] <= 1
        for value in c['receiver_wrenches_from_panel_n_nmm'].values():
            transfer += value
        assert max(abs(recovered[:3])) < 1e-6
        assert max(abs(recovered[3:])) < 1e-3
        assert transfer == pytest.approx(c['applied_wrench_n_nmm'],abs=1e-3)
    assert not r['qualified_for_design'] and not r['geometry_audited']


def test_off_axis_force_cannot_be_silently_balanced_by_normal_supports():
    with pytest.raises(ValueError,match='did not resolve'):
        solve_case(screws=[{'point_mm':[0,18,140],'receiver':'post'}],
                   backing=[{'point_mm':[0,0,25],'receiver':'post'}],
                   floor=[{'point_mm':[0,9,0],'receiver':'floor'}],
                   live_point=[0,18,150],live_force=[300,0,-1200],
                   dead_point=[0,9,100],dead_n=20,
                   withdrawal_n=733,lateral_n=235,head_n=304)


def test_wrench_includes_eccentric_normal_and_vertical_moments():
    assert wrench([50,100,150],[0,300,-1200]).tolist()==[0,300,-1200,-165000,60000,15000]


def test_v2_authenticates_revised_panel_and_five_tnut_dead_load():
    r=json.loads(Path('fea/results/round-structural-kicker-revision-v2.json').read_text())
    assert not r['predecessor_mass_reused']
    assert r['mass_source_candidate']=='round-reinforcement-development'
    for path,sha in r['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
    inventory={p['name']:p for p in json.loads(Path(r['mass_report']).read_text())['mass_inventory']}
    for c in r['cases']:
        assert len(c['dead_components'])==6
        assert sum(n.startswith('hold_tnut_kicker_') for n in c['dead_components'])==5
        parts=[inventory[n] for n in c['dead_components']]
        mass=sum(p['mass_kg'] for p in parts)
        expected=[sum(p['mass_kg']*p['centre_xyz_mm'][i] for p in parts)/mass for i in range(3)]
        expected[1]+=36.
        assert c['dead_n']==pytest.approx(mass*9.80665)
        assert c['dead_point_mm']==pytest.approx(expected)
