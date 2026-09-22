"""Integrated center lengths stay distinct from the historical joint trial."""

import pytest

from scripts import owner_barrel_center_post_joint_replan as historical
from scripts import owner_barrel_center_single_layout as single


def _rows(trial, family):
    return {
        name: (row, trial["solids"][name])
        for station in trial["report"]["stations"].values()
        if station["family"] == family
        for name, row in station["bolts"].items()
    }


def _same_shape(a, b):
    assert a.Volume() == pytest.approx(b.Volume(), abs=1e-5)
    ab, bb = a.BoundingBox(), b.BoundingBox()
    for edge in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"):
        assert getattr(ab, edge) == pytest.approx(getattr(bb, edge), abs=1e-5)


@pytest.fixture(scope="module")
def trials():
    return historical.build(), single.build()


def test_integrated_lengths_match_rows_connections_and_shafts(trials):
    old, integrated = trials
    layout = single.build_layout(integrated["wood"])
    for family, count, expected in (
        ("post_header", 4, 3.5 * 25.4),
        ("principal_header", 2, 4.5 * 25.4),
    ):
        rows = _rows(integrated, family)
        assert len(rows) == count
        for name, (row, roles) in rows.items():
            station = next(
                key
                for key, value in integrated["report"]["stations"].items()
                if name in value["bolts"]
            )
            connection = layout["stations"][station]["bolts"][f"{name}_bolt"]
            assert row["bolt_length_mm"] == pytest.approx(expected)
            assert connection.length == pytest.approx(expected)
            start = historical._add(
                row["bolt_seat_xyz_mm"], row["bolt_axis_xyz"], -historical.WASHER_T
            )
            assert connection.start.toTuple() == pytest.approx(start, abs=1e-5)
            assert connection.direction.toTuple() == pytest.approx(row["bolt_axis_xyz"])
            _same_shape(
                roles["shaft"],
                historical._cylinder(
                    start,
                    row["bolt_axis_xyz"],
                    expected,
                    single.center.hardware.THREAD_MAJOR_MM,
                ),
            )
            assert row["complete_thread_engagement_verified"] is False
            assert row["nominal_tip_beyond_thread_axis_mm"] > 0
            assert row["bolt_barrel_intersection_mm3"] == pytest.approx(
                single.protected._volume(
                    roles["bolt_bore"], roles["barrel_cross_bore"]
                ),
                abs=1e-5,
            )

    report = integrated["report"]
    assert report["native_solve"] is False
    assert report["structural_capacity_verified"] is False
    assert not any(report["release_flags"].values())
    assert len(_rows(old, "post_header")) == 4


def test_unchanged_shapes_and_historical_defaults(trials):
    old, integrated = trials
    assert set(old["wood"]) == set(integrated["wood"])
    for name in ("base_header", "base_post_center_left", "base_post_center_right"):
        _same_shape(integrated["wood"][name], old["wood"][name])
    old_post = _rows(old, "post_header")
    new_post = _rows(integrated, "post_header")
    assert set(old_post) == set(new_post)
    for name, (row, roles) in new_post.items():
        historical_row, historical_roles = old_post[name]
        assert historical_row["bolt_length_mm"] == pytest.approx(4 * 25.4)
        assert row["modeled_bore_depth_past_nominal_tip_mm"] == pytest.approx(16.7)
        for role in ("head", "washer", "barrel", "bolt_bore", "barrel_cross_bore"):
            _same_shape(roles[role], historical_roles[role])

    for side in historical.SIDES:
        station = f"clip_split_base_center_{side}"
        original_lengths = [
            row["bolt_length_mm"]
            for row in old["report"]["stations"][station]["bolts"].values()
        ]
        assert original_lengths == pytest.approx([127.0, 114.3])
        name, original_roles, _, _ = single.margin._pose(
            integrated["wood"],
            side,
            1,
            x_offset=0.0,
            entry_z=single.PRINCIPAL_Z_MM,
            bolt_length=127.0,
            barrel_face="rear",
            seat_depth=single.SEAT_DEPTH_MM,
            thread_depth=single.THREAD_DEPTH_MM,
            bolt_angle_deg=single.ANGLE_DEG,
            pocket_lead_mm=single.POCKET_LEAD_MM,
            mouth_relief=False,
        )
        new_row, new_roles = _rows(integrated, "principal_header")[name]
        assert new_row["modeled_bore_depth_past_nominal_tip_mm"] == pytest.approx(16.7)
        for role in (
            "head",
            "washer",
            "barrel",
            "bolt_bore",
            "barrel_cross_bore",
            "head_pocket",
        ):
            _same_shape(new_roles[role], original_roles[role])


def test_bottom_center_family_shortens_only_installed_shafts(trials):
    _, integrated = trials
    wood = integrated["wood"]
    _, former_wood, _ = single.center._wood()
    old = single.center.build_revised_layout(former_wood)
    current = single.build_six_layout(wood)
    assert current["diagnostics"]["integrated_bottom_bolt_length_mm"] == pytest.approx(
        114.3
    )
    for station in (
        "clip_horizontal_bottom_left_2",
        "clip_horizontal_bottom_right_1",
    ):
        before, after = old["stations"][station], current["stations"][station]
        assert set(after["bolts"]) == set(before["bolts"])
        for name, bolt in after["bolts"].items():
            assert bolt.length == pytest.approx(114.3)
            assert before["bolts"][name].length == pytest.approx(127.0)
            assert bolt.start.toTuple() == pytest.approx(
                before["bolts"][name].start.toTuple()
            )
            _same_shape(
                after["stacks"][name]["washer"], before["stacks"][name]["washer"]
            )
            _same_shape(after["stacks"][name]["head"], before["stacks"][name]["head"])
            assert (
                after["stacks"][name]["shaft"].Volume()
                < before["stacks"][name]["shaft"].Volume()
            )
        for path, cutter in after["drilling_paths"].items():
            _same_shape(cutter, before["drilling_paths"][path])
