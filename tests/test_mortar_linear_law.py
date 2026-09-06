"""Analytic internal-law examples; no claim of a solved contact assembly."""
import math

import pytest

from fea.mortar_linear_law import residuals


def inputs(**changes):
    row = {"ln": 100., "lt": (10., 0.), "lt_start": (0., 0.), "q": .01, "ut": (.1, 0.),
           "mu": .3, "normal_inverse_stiffness": .0001, "tangent_inverse_stiffness": .01,
           "constant_n": 10000., "constant_t": 100., "activity": 1, "ndof": 3,
           "normal_mode": 1, "tangent_mode": 1}
    return row | changes


def test_compressed_stick_state_and_increment_start_history():
    result = residuals(**inputs())
    assert result["eligible"]
    assert result["normal_residual"] == pytest.approx(0)
    assert result["tangent_residual"] == pytest.approx([0, 0])
    assert result["weighted_regularized_opening"] == pytest.approx(0)
    assert result["algorithmic_friction_bound"] == pytest.approx(30)
    assert result["internal_coulomb_excess"] == pytest.approx(-20)
    history = residuals(**inputs(lt_start=(5., 0.), ut=(.05, 0.)))
    assert history["tangent_residual"] == pytest.approx([0, 0])
    wrong_history = residuals(**inputs(ut=(.05, 0.)))
    assert wrong_history["tangent_residual"] == pytest.approx([-.05, 0])


def test_slip_direction_and_wrong_direction_are_distinguished():
    good = residuals(**inputs(activity=2, lt=(30., 0.), ut=(.5, 0.)))
    assert good["tangent_residual"] == pytest.approx([0, 0])
    bad = residuals(**inputs(activity=2, lt=(30., 0.), ut=(-.5, 0.)))
    assert bad["tangent_residual"] == pytest.approx([60, 0])
    assert good["internal_coulomb_excess"] == pytest.approx(0)


def test_oblique_tangent_components_and_nonzero_history():
    good = residuals(**inputs(activity=2, lt=(18., 24.), ut=(.3, .4)))
    assert good["tangent_residual"] == pytest.approx([0, 0])
    bad = residuals(**inputs(activity=2, lt=(18., 24.), ut=(-.3, -.4)))
    assert bad["tangent_residual"] == pytest.approx([36, 48])
    history = residuals(**inputs(lt=(10., 20.), lt_start=(5., 8.), ut=(.05, .12)))
    assert history["tangent_residual"] == pytest.approx([0, 0])
    wrong_history = residuals(**inputs(lt=(10., 20.), ut=(.05, .12)))
    assert wrong_history["tangent_residual"] == pytest.approx([-.05, -.08])


def test_open_inactive_and_excluded_states_do_not_become_passes():
    row = inputs(activity=0, ln=0., lt=(0., 0.), q=-.1, ut=(0., 0.))
    result = residuals(**row)
    assert result["eligible"] and result["normal_residual"] == 0
    assert result["weighted_regularized_opening"] == pytest.approx(.1)
    for excluded in (-3, -2, -1):
        assert not residuals(**(row | {"activity": excluded}))["eligible"]
    assert not residuals(**(row | {"ndof": 0}))["eligible"]


def test_tension_and_normal_mismatch_remain_visible():
    tension = residuals(**inputs(ln=-100., q=-.01))
    assert tension["normal_residual"] == pytest.approx(-30)
    mismatch = residuals(**inputs(q=.02))
    assert mismatch["normal_residual"] == pytest.approx(-30)
    assert mismatch["weighted_complementarity_product"] == pytest.approx(-1)


def test_frictionless_source_branch_does_not_divide_by_mu():
    # getcontactparams sets inverse tangent stiffness to zero when no friction
    # data are present. The supplied algorithmic constant remains finite.
    result = residuals(**inputs(mu=0., q=.02, tangent_inverse_stiffness=0.))
    assert result["normal_residual"] == pytest.approx(-100)
    assert result["tangent_residual"] == [0, 0]


@pytest.mark.parametrize("changes", [
    {"ln": math.nan}, {"q": math.inf}, {"lt": (0.,)}, {"lt": (True, 0.)},
    {"mu": -.1}, {"normal_inverse_stiffness": 0}, {"constant_t": 0},
    {"activity": True}, {"activity": 3}, {"ndof": 4},
    {"activity": 2, "lt": (0., 0.), "ut": (0., 0.)},
    {"ln": 1e308, "q": -1e308},
    {"normal_mode": 2}, {"tangent_mode": 2}, {"normal_mode": True},
    {"mu": .001, "lt": (0., 0.), "ut": (1.3e306, 1.3e306), "activity": 2},
])
def test_invalid_or_undefined_internal_state_fails_closed(changes):
    with pytest.raises(ValueError):
        residuals(**inputs(**changes))
