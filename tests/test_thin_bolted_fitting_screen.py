"""Independent rectangular joints verify the fitting comparison's CAD queries."""

import cadquery as cq
import pytest

from scripts import thin_bolted_fitting_screen as screen


def rectangular_joint(post_high_y=100.):
    return {
        "beam": cq.Solid.makeBox(300., 38.1, 139.7,
                                 cq.Vector(0, -38.1, -69.85)),
        "post": cq.Solid.makeBox(38.1, post_high_y + 100., 139.7,
                                 cq.Vector(-38.1, -100., -69.85)),
    }


def station():
    return ("rectangular_rail", cq.Vector(), cq.Vector(1, 0, 0),
            cq.Vector(0, 1, 0), "beam", "post")


def test_known_square_butt_has_two_complete_far_hole_bores():
    fitting = screen.FITTINGS["B102ZN"]
    wood = rectangular_joint()
    angle = screen.pose(fitting, wood, station(), 0.)
    result = screen.audit_pose(angle, fitting, wood, [])
    assert [h["raw_full_bore_fraction"] for h in result["holes"]] == [1., 1.]
    assert [h["projected_raw_thickness_mm"] for h in result["holes"]] == [38.1, 38.1]
    assert [h["entry_xyz_mm"] for h in result["holes"]] == [
        [68.2625, 0., 0.], [0., 36.5125, 0.],
    ]
    assert not result["ideal_plate_raw_wood_intersections"]
    assert [s["ideal_rectangular_seat_fraction"] for s in result["seats"]] == [1., 1.]
    assert result["strength_checked"] is False


def test_end_of_post_removes_receiver_without_creating_a_geometric_pass():
    fitting = screen.FITTINGS["B102ZN"]
    wood = rectangular_joint(post_high_y=25.)
    angle = screen.pose(fitting, wood, station(), 0.)
    result = screen.audit_pose(angle, fitting, wood, [])
    post = next(h for h in result["holes"] if h["flange"] == "post")
    assert post["raw_full_bore_fraction"] == 0.
    assert next(s for s in result["seats"] if s["flange"] == "post")[
        "ideal_rectangular_seat_fraction"
    ] < .5
    assert result["end_distance_classified"] is False


def test_beam_face_pair_shares_one_bore_but_separates_post_holes():
    fitting = screen.FITTINGS["B102ZN"]
    wood = rectangular_joint()
    rows = [screen.audit_pose(screen.pose(fitting, wood, station(), 0., other),
                              fitting, wood, []) for other in (False, True)]
    beam = [next(h for h in r["holes"] if h["flange"] == "beam") for r in rows]
    post = [next(h for h in r["holes"] if h["flange"] == "post") for r in rows]
    assert beam[0]["key"] == beam[1]["key"]
    assert post[0]["key"] != post[1]["key"]
    assert len({tuple(h["key"]) for r in rows for h in r["holes"]}) == 3


def test_shift_can_fail_edge_marker_while_bore_remains_inside_wood():
    fitting = screen.FITTINGS["B102ZN"]
    wood = rectangular_joint()
    angle = screen.pose(fitting, wood, station(), 25.4)
    result = screen.audit_pose(angle, fitting, wood, [])
    for h in result["holes"]:
        assert h["raw_full_bore_fraction"] == 1.
        assert h["conditional_two_edge_4d_reserve_mm"] == pytest.approx(-6.35)


def test_invalid_flange_or_hole_policy_fails_closed():
    fitting = screen.FITTINGS["B102ZN"]
    with pytest.raises(ValueError):
        fitting.offsets("other")
    wood = rectangular_joint()
    angle = screen.pose(fitting, wood, station(), 0.)
    with pytest.raises(ValueError):
        screen.audit_pose(angle, fitting, wood, [], holes="other")
