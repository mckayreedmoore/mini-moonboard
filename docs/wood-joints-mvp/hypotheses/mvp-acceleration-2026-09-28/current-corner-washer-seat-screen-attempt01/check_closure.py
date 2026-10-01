#!/usr/bin/env python3
"""Independent unit-action and conditional-reference checks."""

from __future__ import annotations

import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "seat-screen.json").read_text(encoding="utf-8"))
PSI_TO_MPA = 0.006894757293168361

max_action_residual_n = 0.0
max_reference_residual_n = 0.0
for axis in DATA["axes"]:
    area = float(axis["modeled_outer_washer_annular_area_mm2"])
    pressure = float(axis["one_N_full_annulus_average_pressure_MPa"])
    assert len(axis["outer_seats"]) == 2
    assert bool(axis["no_middle_member_axial_washer_seat"]) == (
        axis["modeled_receiver_count"] == 3
    )
    for seat in axis["outer_seats"]:
        # With MPa == N/mm^2, p times projected area must recover the unit tie.
        recovered = pressure * area
        max_action_residual_n = max(max_action_residual_n, abs(recovered - 1.0))
        reference = seat["ideal_dfl2_fc_perp_reference_N"]
        if reference is not None:
            expected = area * 625.0 * PSI_TO_MPA
            max_reference_residual_n = max(
                max_reference_residual_n, abs(float(reference) - expected)
            )
            assert seat["load_grain_relation"] == "perpendicular_to_proposed_grain"
            assert seat["outer_receiver_member_id"] in {
                "base_post_outer_left", "base_header"
            }

assert max_action_residual_n <= 1.0e-12
assert max_reference_residual_n <= 1.0e-9
assert all(
    s["ideal_dfl2_fc_perp_reference_N"] is None
    for a in DATA["axes"]
    for s in a["outer_seats"]
    if s["outer_receiver_member_id"] == "knee_outer_left_inner_frame_block"
)
print(
    "independent closure passed: max unit-seat force residual "
    f"{max_action_residual_n:.3g} N; max conditional Fc-perp arithmetic residual "
    f"{max_reference_residual_n:.3g} N"
)
