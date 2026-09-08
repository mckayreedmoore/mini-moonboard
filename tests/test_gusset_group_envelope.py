import pytest

from fea.gusset_group_envelope import build, pair_forces


def test_two_bolt_hand_solutions():
    assert pair_forces([(0, -1), (0, 1)], (10, 0), 4) == [[7, 0], [3, 0]]
    with pytest.raises(ValueError):
        pair_forces([(0, 0), (0, 0)], (1, 0), 0)


def test_current_groups_balance_force_and_moment():
    rows = build()
    assert len(rows) == 6
    for row in rows:
        points = row["upper_yz_mm"]+row["lower_yz_mm"]
        forces = row["bolt_forces_per_unit"]
        for axis in (0, 1):
            assert sum(f[axis] for f in forces) == pytest.approx(0, abs=1e-10)
        assert sum(y*fz-z*fy for (y, z), (fy, fz) in zip(points, forces, strict=True)) == pytest.approx(0, abs=1e-9)
        assert row["upper_to_lower_centroid_delta_yz_mm"] == pytest.approx([90, 240])
        assert row["conditional_basis_scale"] > 0
        if row["basis"] == "unit_FZ":
            assert forces[2][1] == pytest.approx(-.5-90/140)
            assert forces[3][1] == pytest.approx(-.5+90/140)
        elif row["basis"] == "unit_FY":
            assert abs(forces[2][1]) == pytest.approx(240/140)
        else:
            assert abs(forces[0][0]) == pytest.approx(1/80)
            assert abs(forces[2][1]) == pytest.approx(1/140)
    for left, right in zip(rows[:3], rows[3:], strict=True):
        assert left["conditional_basis_scale"] == pytest.approx(right["conditional_basis_scale"])
