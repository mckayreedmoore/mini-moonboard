"""Reject displaced inserts and cut reservations that nominal bodies conceal."""
import cadquery as cq

from fea.round_insert_audit import insert_fit_metrics


def test_actual_insert_identity_is_checked_even_when_both_shapes_fit_receiver():
    raw = cq.Solid.makeBox(30., 30., 30., cq.Vector(-15., -15., 0.))
    expected = cq.Solid.makeCylinder(4., 10., cq.Vector(0., 0., 1.))
    moved = expected.translate((1., 0., 0.))
    envelope = cq.Solid.makeCylinder(5., 11., cq.Vector(0., 0., 1.))
    reserve = cq.Solid.makeCylinder(5., 17.)
    good = insert_fit_metrics(expected, expected, raw, envelope, reserve)
    bad = insert_fit_metrics(expected, moved, raw, envelope, reserve)
    assert good['passed']
    assert not bad['passed']
    assert bad['actual_insert_outside_receiver_mm3'] < .01
    assert bad['actual_insert_shape_mismatch_mm3'] > .01


def test_tolerance_and_depth_reservations_must_fit_even_when_nominal_body_fits():
    raw = cq.Solid.makeBox(30., 30., 14., cq.Vector(-15., -15., 0.))
    body = cq.Solid.makeCylinder(4., 10., cq.Vector(0., 0., 1.))
    envelope = cq.Solid.makeCylinder(5., 14., cq.Vector(0., 0., 1.))
    reserve = cq.Solid.makeCylinder(5., 17.)
    row = insert_fit_metrics(body, body, raw, envelope, reserve)
    assert not row['passed']
    assert row['actual_insert_outside_receiver_mm3'] < .01
    assert row['maximum_envelope_outside_receiver_mm3'] > .01
    assert row['receiver_cut_outside_receiver_mm3'] > .01
