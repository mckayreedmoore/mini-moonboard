"""Both ends and both edges govern the reversible placement screen.

Keep the originally pinned test source unchanged and supplement its controls.
"""

import pytest

from scripts import eoere_front_bolt_placement as method
from scripts.thin_bolted_timber_resistance import end_geometry_factor


@pytest.mark.parametrize(
    ("point", "end_factor", "edge_margin"),
    [
        ([60., 0., 70.], 6/7, 30.),
        ([240., 0., 70.], 6/7, 30.),
        ([34., 0., 70.], None, 30.),
        ([266., 0., 70.], None, 30.),
        ([100., 0., 39.], 1., -1.),
        ([100., 0., 101.], 1., -1.),
    ],
)
def test_inadequate_distance_on_either_side_fails(point, end_factor, edge_margin):
    profile = {
        "basis_grain_u_v_xyz": [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]],
        "datum_xyz_mm": [0., 0., 0.],
        "raw_profile_vertices_luv_mm": [[l, u, v] for l in (0., 300.) for u in (0., 40.) for v in (0., 140.)],
        "end_cut_planes": [
            {"outward_normal_luv": [-1., 0., 0.], "offset_from_datum_mm": 0.},
            {"outward_normal_luv": [1., 0., 0.], "offset_from_datum_mm": 300.},
        ],
    }
    shaft = {"axis_id": "reversal_control", "basis": [[0., 1., 0.]], "point": point, "diameter_mm": 10.}
    surface = {"host": "reversal_member", "interval_mm": [0., 40.]}
    row = method.placement(profile, shaft, surface, end_geometry_factor)
    actual = row["conservative_end_component"]["end_factor_only"]
    assert actual is None if end_factor is None else actual == pytest.approx(end_factor)
    assert row["minimum_outer_edge_4D_margin_mm"] == pytest.approx(edge_margin)
    assert row["full_value_end_and_outer_edge_screen_pass"] is False
