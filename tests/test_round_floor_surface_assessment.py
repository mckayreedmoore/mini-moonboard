"""Layering and support loss must change inputs instead of only surface labels."""
import gzip
import json

import pytest

from fea.round_floor_surface_assessment import (
    BASE,
    SURFACES,
    effective_friction,
    support_points,
)


def test_layered_floor_is_limited_by_weaker_interface():
    assert effective_friction(SURFACES['horse_stall_mats']) == .4
    assert effective_friction(SURFACES['horse_stall_mats'], True) == .12
    assert effective_friction(SURFACES['carpet']) == .25
    assert effective_friction(SURFACES['hardwood_floor'], True) == .1


def test_rear_contact_loss_changes_the_actual_hull():
    contacts = json.loads(gzip.decompress(BASE.read_bytes()))['selected_floor_support_bodies']
    complete = support_points(contacts)
    left = support_points(contacts, 'lumber_leg_left')
    right = support_points(contacts, 'lumber_leg_right')
    assert complete != left != right
    assert max(p[1] for p in left if p[0] < 0) < 0
    with pytest.raises(ValueError, match='valid unavailable'):
        support_points(contacts, 'invented_support')


def test_lower_interface_adds_horizontal_load_overturning_moment():
    from fea.round_floor_surface_assessment import interface_wrench

    assert interface_wrench([100, 200, -2000, 10, 20, 30], 19) == [100, 200, -2000, -3790, 1920, 30]
    assert interface_wrench([100, 200, -2000, 10, 20, 30], 0) == [100, 200, -2000, 10, 20, 30]
