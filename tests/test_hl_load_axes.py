"""Physical HL load axes follow the catalog installation, not the bend."""

from pathlib import Path

import pytest

from scripts.hl_load_axes import frame_for_reach, local_wrench, pose_frames

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_reference_fixture_and_quarter_turn():
    typical = frame_for_reach((1, 0, 0))
    assert typical.reach == (1, 0, 0)  # F1, along beam/flange reach.
    assert typical.bend == (0, 1, 0)
    assert typical.uplift == (0, 0, 1)
    turned = frame_for_reach((0, 1, 0))
    assert turned.reach == (0, 1, 0)
    assert turned.bend == (-1, 0, 0)
    assert turned.uplift == (0, 0, 1)


def test_left_right_reflection_preserves_uplift_and_flips_f1():
    right = frame_for_reach((1, 0, 0))
    left = frame_for_reach((-1, 0, 0))
    assert left.reach == (-1, 0, 0)
    assert left.bend == (0, -1, 0)
    assert right.uplift == left.uplift
    assert right.reach != left.reach


def test_all_installed_frames_are_orthonormal_and_handed():
    for frame in pose_frames().values():
        vectors = (frame.reach, frame.bend, frame.uplift)
        for i, a in enumerate(vectors):
            for j, b in enumerate(vectors):
                assert sum(x * y for x, y in zip(a, b, strict=True)) == (i == j)
        ax, ay, az = frame.reach
        bx, by, bz = frame.bend
        assert (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx) == (
            frame.uplift
        )
    with pytest.raises(ValueError):
        frame_for_reach((0, 0, 1))


def test_inverted_b_seat_rotates_catalog_uplift_and_bend_sign():
    lower_right = frame_for_reach((1, 0, 0), uplift=(0, 0, -1))
    assert lower_right.reach == (1, 0, 0)
    assert lower_right.bend == (0, -1, 0)
    assert lower_right.uplift == (0, 0, -1)
    assert local_wrench(lower_right, (7, 11, 13), (17, 19, 23)) == {
        "force": (7, -11, -13),
        "moment": (17, -19, -23),
    }
    expected = {
        "b_lower_right_front": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
        "b_lower_right_rib": ((-1, 0, 0), (0, 1, 0), (0, 0, -1)),
        "b_lower_left_front": ((-1, 0, 0), (0, 1, 0), (0, 0, -1)),
        "b_lower_left_rib": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
    }
    for name, (reach, bend, uplift) in expected.items():
        assert pose_frames()[name] == frame_for_reach(reach, uplift)
        assert pose_frames()[name].bend == bend
    with pytest.raises(ValueError):
        frame_for_reach((1, 0, 0), uplift=(0, 1, 0))


def test_signed_force_and_moment_projection_in_actual_poses():
    right = frame_for_reach((1, 0, 0))
    left = frame_for_reach((-1, 0, 0))
    lower = frame_for_reach((0, -1, 0))
    assert local_wrench(right, (7, 11, 13), (17, 19, 23)) == {
        "force": (7, 11, 13),
        "moment": (17, 19, 23),
    }
    assert local_wrench(left, (7, 11, 13), (17, 19, 23)) == {
        "force": (-7, -11, 13),
        "moment": (-17, -19, 23),
    }
    assert local_wrench(lower, (7, 11, 13), (17, 19, 23)) == {
        "force": (-11, 7, 13),
        "moment": (-19, 17, 23),
    }


def test_current_decision_text_uses_corrected_outward_axis():
    audit = (
        ROOT / "docs/bolted-candidate-prototypes/hl-load-axis-audit.md"
    ).read_text()
    screen = (
        ROOT / "docs/bolted-candidate-prototypes/hardware-first-conditional-screen.md"
    ).read_text()
    assert "maps to global **X**" in audit
    assert "unlisted horizontal transverse axis is **Y**" in audit
    assert "B lower right front, inverted" in audit
    assert "not permission to use a seat-up catalog allowable" in audit
    assert "horizontal flange reach into global X" in screen
    assert "global-Y transverse action" in screen
