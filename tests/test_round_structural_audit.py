"""Actual ray exits distinguish containment, breakthrough and hidden service gaps."""
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea import round_structural_audit as audit


def screw(length, *, start=(0, 0, 0), direction=(0, 0, 1), name='panel', kind='screw'):
    return SimpleNamespace(name=name, start=cq.Vector(*start), direction=cq.Vector(*direction),
                           length=length, members=('panel', 'receiver'), kind=kind,
                           product_status='Synthetic geometry test')


def receiver(z0, z1):
    return cq.Workplane('XY').box(20, 20, z1-z0, centered=(True, True, False)).translate((0, 0, z0)).val()


def check(shape, connection):
    return audit.screw_tip_checks({'receiver': SimpleNamespace(shape=shape)}, [connection])[0]


def test_tip_uses_receiver_entry_and_full_exit_not_screw_length_clipping():
    row = check(receiver(18, 56.1), screw(50.8))
    assert row['passed']
    assert row['receiver_entry_mm'] == pytest.approx(18)
    assert row['receiver_first_exit_mm'] == pytest.approx(56.1)
    assert row['gross_penetration_mm'] == pytest.approx(32.8)
    assert row['tip_to_first_exit_mm'] == pytest.approx(5.3)


@pytest.mark.parametrize('length', [56.1, 60])
def test_tip_at_or_beyond_back_face_fails(length):
    row = check(receiver(18, 56.1), screw(length))
    assert not row['passed']
    assert row['tip_to_first_exit_mm'] == pytest.approx(56.1-length)


def test_service_void_before_tip_fails_even_if_tip_reenters_wood():
    shape = receiver(0, 60).cut(receiver(20, 30))
    row = check(shape, screw(50))
    assert row['receiver_intervals_mm'] == pytest.approx([(0, 20), (30, 60)])
    assert not row['passed']
    assert row['tip_to_first_exit_mm'] == pytest.approx(-30)


def test_oblique_sds_tip_uses_actual_exit_through_side_of_receiver():
    row = check(receiver(0, 100), screw(20, start=(0, 0, 1), direction=(1, 0, 1), name='clip_sds'))
    assert row['receiver_first_exit_mm'] == pytest.approx(10*2**.5)
    assert not row['passed']


def test_through_bolts_are_not_misclassified_as_screws():
    rows = audit.screw_tip_checks({'receiver': SimpleNamespace(shape=receiver(0, 20))},
                                  [screw(50, kind='bolt')])
    assert rows == []


def test_source_closure_authenticates_producers_excludes_consumers():
    sources = audit.sources()
    assert {'mini_moonboard/round_structural_frame.py',
            'mini_moonboard/round_structural_wiring.py',
            'mini_moonboard/round_insert_frame.py',
            'mini_moonboard/round_insert_hardware.py',
            'fea/round_structural_audit.py'} <= sources.keys()
    assert not {'mini_moonboard/round_structural_exports.py',
                'mini_moonboard/round_structural_drilling.py'} & sources.keys()
