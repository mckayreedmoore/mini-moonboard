"""Expanded four-panel comparison retains actual asymmetric grid and gates."""
import copy
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import split_center_panel_comparison as screen


def fake_module():
    class Screw:
        def __init__(self, name, panel, x, y):
            self.name, self.members = name, (panel, 'receiver')
            self.start, self.length = cq.Vector(x, y, -18.25625), 50.8
    screws = []
    for band in ('lower', 'upper'):
        low = 0 if band == 'lower' else 1219.2
        for side in ('left', 'right'):
            left = -1219.2 if side == 'left' else 0
            panel = f'main_{band}_{side}'
            for i, (x, y) in enumerate(((50, 50), (1169.2, 50), (50, 1169.2), (1169.2, 1169.2))):
                screws.append(Screw(panel+str(i), panel, left+x, low+y))
    return SimpleNamespace(KEY='test', timber=SimpleNamespace(PanelScrew=Screw), connections=lambda: screws,
        b=SimpleNamespace(HALF=1219.2, LENGTH=2438.4, point=lambda x, y, z: cq.Vector(x, y, z), normal=lambda: cq.Vector(0, 0, 1)))


def test_actual_grid_patch_and_both_free_panel_edges():
    model = fake_module()
    for case in screen.CASES:
        row = screen.prepare_panel(model, case, 80)
        assert row['patch_area_mm2'] == pytest.approx(400)
        assert sum(row['loads'].values()) == pytest.approx(2*300*.45359237*9.80665)
        assert row['linear_250_over_300_scale'] == pytest.approx(250/300)
        assert row['vertical_seam_nodes'] and row['seam_nodes']
        assert all(row['nodes'][t][0] == 0 for t in row['vertical_seam_nodes'])
        assert all(row['nodes'][t][1] == 1219.2 for t in row['seam_nodes'])
        if case[2] == 'F3':
            assert row['hold_datum_panel_xy_mm'][0] == pytest.approx(-19.2)
            assert row['patch_mm'][1] == pytest.approx(-9.2)
        if case[2] == 'G3':
            assert row['hold_datum_panel_xy_mm'][0] == pytest.approx(180.8)
        # No rotational constraint or constraint along either free seam.
        assert all(d <= 3 for _, d in row['constraints'])
        assert {t for t, d in row['constraints'] if d == 3} == set(row['screw_nodes'].values())


def test_missing_cases_and_vertical_seam_nonconvergence_cannot_pass():
    cases = [{'candidate': candidate, 'case_id': case[2], 'mesh_mm': size,
              'compliance_mm_per_n': 1., 'max_abs_horizontal_seam_displacement_mm': 2.,
              'max_abs_vertical_seam_displacement_mm': 3.}
             for candidate in ('baseline', 'revised') for case in screen.CASES for size in screen.shell.SIZES]
    assert screen.comparison_summary(cases, 'baseline', 'revised')['numerical_comparison_accepted']
    bad = copy.deepcopy(cases)
    bad[0]['max_abs_vertical_seam_displacement_mm'] *= 1.1
    result = screen.comparison_summary(bad, 'baseline', 'revised')
    assert not result['numerical_comparison_accepted']
    assert 'D6' not in {r['case_id'] for r in result['accepted_case_surrogate_ratios']}
    assert not result['actual_panel_qualified'] and not result['gusset_force_reduction_established']
    with pytest.raises(ValueError, match='32 distinct'):
        screen.comparison_summary(cases[:-1], 'baseline', 'revised')
