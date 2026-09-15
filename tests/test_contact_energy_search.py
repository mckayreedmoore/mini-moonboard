"""Normal line-search identity reproduces an independent dense energy fixture."""
import numpy as np
import pytest
from scipy.optimize import minimize_scalar

from fea.contact_energy_search import normal_energy_step


def test_line_search_matches_direct_finite_system_energy_with_contact_switches():
    matrix = np.array([[6.,3.],[3.,3.]])
    normals = np.array([[-2.,-.2],[-1.,1.],[1.,1.4],[.8,-.05]])
    stiffness = np.full(4, 100.)
    force = np.array([.9,1.5])
    first_active = np.ones(4)
    first = np.linalg.solve(matrix+normals.T@np.diag(stiffness*first_active)@normals,force)
    g = normals@first
    next_active = (g<0.).astype(float)
    trial = np.linalg.solve(matrix+normals.T@np.diag(stiffness*next_active)@normals,force)
    h = normals@trial
    result = normal_energy_step(g,stiffness*first_active*g,h,stiffness*next_active*h,stiffness)
    def energy(x):
        return .5*x@matrix@x-force@x+.5*stiffness@np.minimum(normals@x,0.)**2
    independent = minimize_scalar(lambda a:energy(first+a*(trial-first)),bounds=(0.,1.),method='bounded',
                                  options={'xatol':1.e-13})
    assert 0. < result['alpha'] < 1.  # Full Newton step crosses contacts and overshoots.
    selected = first+result['alpha']*(trial-first)
    assert energy(selected) <= independent.fun+1.e-11
    assert result['potential_change_nmm'] == pytest.approx(energy(selected)-energy(first),abs=1.e-12)
    q = np.array(result['linear_contact_force_n'])
    np.testing.assert_allclose(matrix@selected,force-normals.T@q,atol=1.e-12)


def test_interpolated_state_keeps_linear_equilibrium_proxy_for_next_search():
    # Single compression spring against a bilateral support, f=-1.
    # The deliberately inactive initial solve lies at -1; active solve is -1/11.
    result = normal_energy_step([-1.],[0.],[-1/11],[-10/11],[10.])
    assert result['alpha'] == pytest.approx(1.)
    assert result['gap_mm'][0] == pytest.approx(-1/11)
    assert result['potential_change_nmm'] < 0
    assert result['final_native_verification_required']


def test_mismatched_states_with_negative_base_curvature_rejected():
    with pytest.raises(ValueError,match='Negative base curvature'):
        normal_energy_step([0.],[0.],[1.],[1.],[10.])


def test_actual_rounded_splice_term_clamps_only_when_dat_interval_contains_zero():
    # exterior-cells04-a12-left cycles21/22, knee_splice_contact_right_0_0.
    # Each opening is the difference of DAT coordinates with 0.5e-6 mm radii.
    stiffness = 476119.29388742463
    g, h = -1.9999999999242846e-5, -1.8999999999991246e-5
    q, r = stiffness*g, stiffness*h
    with pytest.raises(ValueError,match='outside printed-data interval'):
        normal_energy_step([g],[q],[h],[r],[stiffness])
    result = normal_energy_step([g],[q],[h],[r],[stiffness],
        gap_radius=[1.e-6],linear_force_radius=[stiffness*1.e-6],
        trial_gap_radius=[1.e-6],trial_force_radius=[stiffness*1.e-6])
    assert result['raw_base_directional_curvature_nmm'] == pytest.approx(-4.76119293174769e-7)
    assert result['base_curvature_radius_nmm'] == pytest.approx(3.8089543496740855e-6)
    low,high = result['base_curvature_interval_nmm']
    assert low < 0 < high
    assert result['base_directional_curvature_nmm'] == 0.
    assert result['negative_curvature_clamped_within_printed_interval']
    assert result['gap_radius_mm'] == pytest.approx([1.e-6])
    assert result['linear_contact_force_radius_n'] == pytest.approx([stiffness*1.e-6])
    assert result['final_native_verification_required']


def test_real_negative_curvature_is_not_hidden_by_small_roundoff_interval():
    with pytest.raises(ValueError,match='outside printed-data interval'):
        normal_energy_step([0.],[0.],[1.],[1.],[10.],gap_radius=[1.e-6],
            linear_force_radius=[1.e-6],trial_gap_radius=[1.e-6],trial_force_radius=[1.e-6])
