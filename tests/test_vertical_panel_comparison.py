"""Load quadrature, shell topology and independent equilibrium rejection."""
import pytest

from fea import vertical_panel_comparison as screen


def test_exact_quadratic_pressure_preserves_force_and_first_moments():
    xs = screen.mesh_axes(-100, 0, 25, [-70, -30])
    ys = screen.mesh_axes(0, 100, 25, [30, 70])
    nodes, elements, _ = screen.grid(xs, ys)
    loads, area = screen.pressure_load(nodes, elements, (-70, -30, 30, 70), 1200)
    assert area == pytest.approx(1600)
    assert sum(loads.values()) == pytest.approx(1200)
    assert sum(nodes[t][0]*v for t, v in loads.items()) == pytest.approx(-50*1200)
    assert sum(nodes[t][1]*v for t, v in loads.items()) == pytest.approx(50*1200)
    # Consistent quadratic interpolation integrates an affine virtual field.
    work = sum(v*(2+3*nodes[t][0]-4*nodes[t][1]) for t, v in loads.items())
    assert work == pytest.approx(1200*(2+3*-50-4*50))
    assert all(len(set(ids)) == 8 for ids in elements.values())
    with pytest.raises(ValueError, match='imprinted'):
        screen.pressure_load(nodes, elements, (-69, -30, 30, 70), 1200)


def test_beam_reference_and_consistent_edge_load_are_independent():
    record = screen.benchmark()
    assert sum(record['loads'].values()) == pytest.approx(1)
    assert record['benchmark_tip_mm'] == pytest.approx(4/(7000*100*10**3)*1000**3+1000/((5/6)*3500*1000))
    assert all(record['nodes'][t][1] == 0 for t, _ in record['constraints'])
    assert '*ELEMENT,TYPE=S8' in screen.deck(record)


def test_reaction_audit_rejects_force_and_moment_errors():
    record = {'candidate': 'comparison', 'nodes': {1: [0, 0, 0], 2: [2, 0, 0], 3: [1, 1, 0], 4: [1, .5, 0]},
              'constraints': [(1, 3), (2, 3), (3, 3)], 'loads': {4: 100}, 'seam_nodes': [1, 2], 'screw_nodes': {'one': 1}}

    def data(reactions):
        return ('displacements (vx,vy,vz) for set ALLN and time 1\n\n'
                '1 0 0 0\n2 0 0 0\n3 0 0 0\n4 0 0 .1\n\n'
                'forces (fx,fy,fz) for set ALLN and time 1\n\n'+
                '\n'.join(f'{n} 0 0 {v}' for n, v in enumerate(reactions, 1))+'\n')

    assert screen.assess(record, data([-25, -25, -50, 100]))['external_work_nmm'] == pytest.approx(10)
    with pytest.raises(ValueError, match='Force equilibrium'):
        screen.assess(record, data([-24, -25, -50, 100]))
    with pytest.raises(ValueError, match='Moment equilibrium'):
        screen.assess(record, data([-15, -35, -50, 100]))


def test_unconverged_comparison_suppresses_ratios():
    cases = [{'candidate': candidate, 'band': band, 'mesh_mm': size,
              'compliance_mm_per_n': factor, 'seam_profile': [[0, factor], [1, factor/2]]}
             for candidate, factor in (('paired-rail', 2), ('vertical-principal', 1))
             for band in ('lower', 'upper') for size in screen.SIZES]
    accepted = screen.comparison_summary(cases)
    assert accepted['numerical_comparison_accepted']
    assert accepted['fine_mesh_surrogate_ratios'][0]['vertical_over_paired_patch_compliance'] == .5
    cases[0]['compliance_mm_per_n'] *= 1.2
    rejected = screen.comparison_summary(cases)
    assert not rejected['numerical_comparison_accepted'] and rejected['fine_mesh_surrogate_ratios'] == []
    assert not rejected['qualified_for_design']
