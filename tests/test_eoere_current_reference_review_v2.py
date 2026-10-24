import copy

import numpy as np
import pytest

from scripts.eoere_current_reference_review_v2 import flange_probe_points


def test_corner_probe_is_invariant_when_the_bolt_head_origin_reverses():
    axes = [{"point_xyz_mm": [i, 0, 0], "attachments": [{"angle_id": fitting, "point": [i, 2, 3]}]}
            for fitting in ("eoere_clip_single_top_left_1", "eoere_clip_single_top_right_2") for i in range(4)]
    geometry = {"axes": axes}
    before = flange_probe_points(geometry)
    reversed_geometry = copy.deepcopy(geometry)
    for axis in reversed_geometry["axes"]:
        axis["point_xyz_mm"][0] -= 88.9
    after = flange_probe_points(reversed_geometry)
    for fitting in before:
        np.testing.assert_array_equal(before[fitting], [1.5, 2, 3])
        np.testing.assert_array_equal(before[fitting], after[fitting])


def test_missing_physical_corner_hole_is_rejected():
    with pytest.raises(ValueError, match="four physical"):
        flange_probe_points({"axes": []})
