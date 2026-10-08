"""The bounded cleat adapter must preserve all other axes and raw ownership."""

import cadquery as cq
import pytest

from scripts.eoere_bolted_cleat_revision import retarget_cleat_axes


def fixture():
    wood = {"cleat": cq.Solid.makeBox(38.1, 139.7, 100),
            "post": cq.Solid.makeBox(38.1, 139.7, 100, cq.Vector(38.1, 0, 0))}
    axes = [{"id": f"cleat_{i}", "source": "cleat_post_through_bolt",
             "point": cq.Vector(0, 30 + i * 20, 40), "direction": cq.Vector(1, 0, 0),
             "receivers": ["cleat", "post"], "grip_mm": 76.2} for i in range(4)]
    return wood, axes


def test_only_cleat_axes_move_and_input_rows_stay_unchanged():
    wood, axes = fixture()
    retained = {"source": "original_starting_frame_axis", "id": "retained"}
    result, changes = retarget_cleat_axes([retained, *axes], wood, 60)
    assert result[0] is retained
    assert len(changes) == 4
    assert all(row["point"].z == 60 for row in result[1:])
    assert all(row["point"].z == 40 for row in axes)
    assert all(row["receivers"] == ["cleat", "post"] for row in result[1:])


def test_height_outside_the_finite_receiver_is_rejected():
    wood, axes = fixture()
    with pytest.raises(ValueError):
        retarget_cleat_axes(axes, wood, 200)


def test_nonfinite_height_and_wrong_census_are_rejected():
    wood, axes = fixture()
    with pytest.raises(ValueError):
        retarget_cleat_axes(axes, wood, float("nan"))
    with pytest.raises(ValueError):
        retarget_cleat_axes(axes[:3], wood, 60)
