"""Reproduce the three conditional BG003 double-shear reference scenarios."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
sys.path.insert(0, str(ROOT))
from mini_moonboard.bolted_wood_wood_double_shear import wood_wood_double_shear_reference

d = json.loads((HERE / "calculation.json").read_text())
pins = {
    "wood_wood_double_shear_helper_sha256": ROOT / "mini_moonboard/bolted_wood_wood_double_shear.py",
    "dfl_bearing_input_helper_sha256": ROOT / "mini_moonboard/bolted_timber_checks.py",
    "bolt_groups_json_sha256": HERE.parent / "bolt-groups/bolt-groups.json",
    "member_geometry_json_sha256": HERE.parent / "reduced-static-attempt01/member-geometry.json",
    "current_knee_profile_query_sha256": HERE.parent / "current-knee-three-member-profile-attempt01/query.json",
}
for key, path in pins.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == d["source_pins"][key], key
lengths = d["modeled_geometry_inputs"]["raw_modeled_bearing_lengths_in"]
s = d["conditional_scenario_inputs"]
main = s["main_member_id"]
side_a, side_b = s["side_member_ids"]
assert s["symmetric_action_scenario_per_one_bolt"]["signed_action_magnitudes_lbf"] == [1, -2, 1]
for row in d["scenarios"]:
    angles = row["load_to_grain_degrees"]
    result = wood_wood_double_shear_reference(
        main_bearing_length_in=lengths[main],
        side_a_bearing_length_in=lengths[side_a],
        side_b_bearing_length_in=lengths[side_b],
        main_load_to_grain_degrees=angles["base_side_left_main"],
        side_a_load_to_grain_degrees=angles["both_outer_side_members"],
        side_b_load_to_grain_degrees=angles["both_outer_side_members"],
        main_bolt_axis_parallel_to_grain=False,
        side_a_bolt_axis_parallel_to_grain=False,
        side_b_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=s["bolt_nominal_full_body_diameter_in"],
        bolt_thread_root_diameter_in=s["bolt_thread_root_diameter_in"],
        main_thread_bearing_length_in=s["thread_bearing_lengths_in"][1],
        side_a_thread_bearing_length_in=s["thread_bearing_lengths_in"][0],
        side_b_thread_bearing_length_in=s["thread_bearing_lengths_in"][2],
        bolt_bending_yield_strength_psi=s["bolt_bending_yield_strength_psi"],
        side_a_gap_in=s["face_gaps_in"][0], side_b_gap_in=s["face_gaps_in"][1],
        symmetric_side_actions_established=True,  # Declared unit scenario, not actual frame forces.
    )
    assert result["reference_values_lbf"] == row["reference_yield_modes_lbf"]
    assert result["governing_mode"] == row["governing_mode"]
    assert result["reference_lateral_lbf"] == row["one_bolt_three_member_reference_Z_lbf"]
    assert result["effective_side_bearing_length_in"] == min(lengths[side_a], lengths[side_b])
    fm, fs = row["bearing_strength_psi"]["main"], row["bearing_strength_psi"]["side"]
    # Independent NDS double-shear mode-IV expression, separate from helper.
    iv = 2 * s["bolt_nominal_full_body_diameter_in"]**2 / (3.2 * row["k_theta"])
    iv *= math.sqrt(2 * fm * s["bolt_bending_yield_strength_psi"] / (3 * (1 + fm / fs)))
    assert math.isclose(iv, row["reference_yield_modes_lbf"]["IV"], rel_tol=1e-12)
print("BG003 verified: five source pins, three four-mode results, shorter-side rule, independent mode IV")
