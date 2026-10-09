"""Independent arithmetic and changed-coordinate checks for the current shop plan.

These tests use retained Git companions. The full saved-solid/source replay is
an explicit local check and is not a prerequisite for these small tests.
"""

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.eoere_current_shop_followup import (
    OLD,
    OWN,
    PACKET,
    ROOT,
    build,
    cylinder_bounds,
    segment_box_distance,
    selected_hardware_bounds,
)


def rows(name, folder=PACKET):
    with (ROOT / folder / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def read(name):
    return json.loads((ROOT / PACKET / name).read_bytes())


@pytest.mark.parametrize("start,finish,expected", [
    ((-2, .5, .5), (2, .5, .5), 0),
    ((-2, 2, .5), (2, 2, .5), 1),
    ((-1, 5, .5), (5, -1, .5), math.sqrt(2)),
    ((2, 2, 2), (2, 2, 2), math.sqrt(3)),
])
def test_segment_box_interior_endpoint_and_reverse(start, finish, expected):
    box = (0, 1, 0, 1, 0, 1)
    assert segment_box_distance(start, finish, box) == pytest.approx(expected, abs=1e-12)
    assert segment_box_distance(finish, start, box) == pytest.approx(expected, abs=1e-12)


def test_oblique_flat_end_cylinder_bounds():
    r = math.sqrt(2)
    assert cylinder_bounds((0, 0, 0), (4, 4, 0), 2) == pytest.approx((-r, 4+r, -r, 4+r, -2, 2))


def test_hardware_obstructions_extend_shaft_and_put_spacer_after_washer():
    bank = {"a_shaft": {"bounds": [0, 10, -1, 1, -1, 1]},
            "a_nut": {"bounds": [8, 10, -2, 2, -2, 2]},
            "a_nut_washer": {"bounds": [7, 8, -3, 3, -3, 3]}}
    axis = {"direction_xyz": [1, 0, 0], "point_xyz_mm": [0, 0, 0],
            "grip_mm": 6, "after_plate_mm": 1, "hardware_scenario": {"washer_thickness_mm": 1}}
    out = selected_hardware_bounds(bank, {"a": axis},
                                   {"a": {"selected_tip_delta_mm": 2, "nut_side_spacer_mm": 3}})
    assert out["a_shaft"]["bounds"] == [0, 12, -1, 1, -1, 1]
    assert out["a_nut"]["bounds"] == [11, 13, -2, 2, -2, 2]
    assert out["a_nut_washer"] == bank["a_nut_washer"]
    assert out["a_spacer"]["bounds"] == pytest.approx([8, 11, -9.525, 9.525, -9.525, 9.525])
    assert bank["a_shaft"]["bounds"][1] == 10


def test_all_selected_catalog_windows_with_decimal_arithmetic():
    # ASME B18.2.1-2012 full-body Table 12/13, inches: Lb, Lg, minus length.
    limits = {(D(".375"), D("2.5")): (D("1.19"), D("1.5"), D(".04")),
              (D(".375"), D("3.5")): (D("2.19"), D("2.5"), D(".06")),
              (D(".375"), D(4)): (D("2.69"), D(3), D(".06")),
              (D(".375"), D("4.5")): (D("3.19"), D("3.5"), D(".10")),
              (D(".375"), D("4.75")): (D("3.44"), D("3.75"), D(".10")),
              (D(".375"), D("6.5")): (D("4.94"), D("5.25"), D(".18")),
              (D(".5"), D("8.5")): (D("6.62"), D(7), D(".18"))}
    old = {r["axis_id"]: r for r in rows("bolt-stacks.csv", OLD)}
    selected = rows("hardware-selection.csv")
    assert len(selected) == len({r["axis_id"] for r in selected}) == 100
    counts = Counter()
    for r in selected:
        diameter = (D(r["selected_diameter_mm"])/D("25.4")).quantize(D(".001"))
        length = (D(r["selected_underhead_length_mm"])/D("25.4")).quantize(D(".01"))
        counts[diameter, length] += 1
        lb, lg, minus = limits[diameter, length]
        prior = old[r["axis_id"]]
        stack = D(prior["receiver_plus_plate_mm"])+D(r["nut_side_spacer_mm"])
        w_max, w_min = (D(prior[f"catalog_each_washer_{end}_mm"]) for end in ("max", "min"))
        nut_max, pitch = D(prior["catalog_nut_height_max_mm"]), D("25.4")/D(prior["UNC_threads_per_inch"])
        tip_margin = (length-minus)*D("25.4")-stack-2*w_max-nut_max-2*pitch
        seat_margin = stack+2*w_min-lg*D("25.4")
        assert tip_margin > 0 and seat_margin > 0
        assert float(tip_margin) == pytest.approx(float(r["minimum_two_pitch_margin_mm"]), abs=1e-8)
        assert float(seat_margin) == pytest.approx(float(r["minimum_nut_seating_margin_mm"]), abs=1e-8)
        assert float(lb*D("25.4")) == pytest.approx(float(r["minimum_body_mm"]), abs=1e-8)
    assert sorted(counts.values()) == [4, 4, 4, 4, 8, 16, 60]
    assert sum(float(r["selected_tip_delta_mm"]) > 0 for r in selected) == 32


def test_eight_specific_full_stack_body_targets_and_single_spacers():
    selected = {r["axis_id"]: r for r in rows("hardware-selection.csv")}
    headers = {f"eoere_bolt_{n:03}" for n in (65, 66, 79, 80)}
    corners = {f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)}
    spacers = {name for name, r in selected.items() if float(r["nut_side_spacer_mm"]) > 0}
    assert spacers == headers | corners
    for name in spacers:
        r = selected[name]
        assert r["selected_spacer_SKU"] == "13731"
        assert float(r["nut_side_spacer_mm"]) == 12.7
        assert r["selected_recipe"].endswith("nut_washer/spacer/nut")
        assert float(r["minimum_body_to_nominated_target_margin_mm"]) == pytest.approx(2.1844)
        assert float(r["nominated_smooth_body_target_mm"]) == pytest.approx(53.4416 if name in headers else 78.8416)
    # Most other rows cover their nominated shear interfaces, not all far wood.
    assert sum(float(r["body_to_farthest_wood_plate_end_margin_mm"]) < 0 for r in selected.values()) == 92


def test_two_panel_rows_move_twenty_mm_and_all_other_machining_rows_stay():
    previous = rows("panel-machining.csv", OLD)
    current = rows("panel-machining.csv")
    assert len(current) == len(previous) == 340
    changes = []
    for old, new in zip(previous, current, strict=True):
        if old != new:
            changes.append(new["identity"])
            assert float(new["origin_z_mm"])-float(old["origin_z_mm"]) == pytest.approx(20)
            assert new["origin_x_mm"] == old["origin_x_mm"]
            assert new["origin_y_mm"] == old["origin_y_mm"]
    assert set(changes) == {"round_kicker_left_rim_2", "round_kicker_right_rim_2"}


def test_current_member_sources_match_profiles_and_only_three_sources_change():
    current = read("current_profiles.json")
    previous = json.loads((ROOT / OLD / "current_profiles.json").read_bytes())
    assert {name for name in current if current[name] != previous[name]} == {
        "base_principal_center_right", "kicker_left", "kicker_right"}
    for r in rows("members.csv"):
        assert r["current_finished_source_path"] == current[r["member"]]["finished"]["path"]
        assert r["current_finished_source_sha256"] == current[r["member"]]["finished"]["sha256"]


def test_all_retained_channel_routes_round_trip_through_current_member_datums():
    profiles = read("current_profiles.json")
    channels = rows("service-channel-datums.csv")
    assert len(channels) == 32
    assert [r["service"] for r in channels if r["receiver"] == "base_principal_center_right"] == ["wire_072_F1_G1"]
    for row in channels:
        profile = profiles[row["receiver"]]
        for local, world in zip(json.loads(row["control_route_receiver_L_U_V_mm"]),
                                json.loads(row["control_route_world_xyz_mm"]), strict=True):
            reconstructed = [profile["datum_xyz_mm"][i]+sum(local[j]*profile["basis_grain_u_v_xyz"][j][i]
                                                          for j in range(3)) for i in range(3)]
            assert reconstructed == pytest.approx(world, abs=1e-8)


def test_selected_additions_clear_only_their_declared_nominal_envelopes():
    review = read("hardware-envelope-review.json")
    assert review["all_changed_envelopes_nominally_clear"] is True
    assert review["physical_fit_observed"] is False
    assert review["hardware_model_updated"] is False
    assert len(review["rows"]) == 48
    refined = [q for r in review["rows"] for q in r["refined_nominal_angle_queries"]]
    assert len(refined) == review["refined_query_count"] == 12
    assert all(q["intersection_mm3"] < 1e-5 and q["distance_mm"] > 1e-5 for q in refined)


def test_drilling_reach_counts_guide_and_backer_for_every_axis():
    drilling = rows("drilling-requirements.csv")
    assert len(drilling) == 100
    for row in drilling:
        expected = float(row["nominal_wood_path_mm"])+19.05+6.35
        assert float(row["minimum_usable_bit_projection_mm"]) == pytest.approx(expected)
    assert max(float(r["minimum_usable_bit_projection_mm"]) for r in drilling) == pytest.approx(203.2)


def test_no_observed_fields_or_release_and_companions_authenticate():
    result = read("result.json")
    assert all(value is False for value in result["release"].values())
    for name, ref in result["files"].items():
        raw = (ROOT / PACKET / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == ref["sha256"]
        assert len(raw) == ref["bytes"]
        if name.endswith(".csv"):
            assert all(value == "" for r in rows(name) for key, value in r.items()
                       if key.startswith("Actual") or key == "Disposition")
    assert result["reference_tool_obstruction_count"] == 1029
    assert sum(result["reference_tool_screen_counts"].values()) == 200
    assert all(r["actual_tool_and_continuous_removal_verified"] == "False" for r in rows("access-requirements.csv"))


def test_changed_mechanics_keeps_gross_model_and_new_response_distinct():
    result = read("mechanical-change-review.json")
    inc = result["principal_inclusion_query"]
    assert inc["old_minus_new_volume_mm3"] == 0
    assert inc["added_volume_mm3"] == pytest.approx(97352.067293234, abs=1e-5)
    assert inc["added_weight_N"] == pytest.approx(inc["added_mass_kg_at_500kg_m3"]*9.80665)
    assert inc["maximum_envelope_coordinate_change_mm"] < 1e-5
    disposition = result["source_change_disposition"]
    assert disposition["new_six_case_response_generated"] is False
    assert disposition["declared_gross_stock_beam_stiffness_operator_changes_from_filled_internal_cuts"] is False
    assert disposition["complete_joint_resistance"] is None
    assert len(result["preceding_signed_action_trials"]) == 12
    assert all(r["new_layout_action"] is False for r in result["preceding_signed_action_trials"])


def test_wrong_input_digest_rejected_before_dependencies(tmp_path):
    path = tmp_path / "input.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="frozen input digest differs"):
        build(path, "0"*64)


def test_external_output_directory_rejected_before_source_replay(tmp_path):
    marker = tmp_path / "preserved"
    marker.write_text("keep")
    completed = subprocess.run([sys.executable, "-B", str(OWN), "--inputs-sha256", "0"*64,
                                "--out", str(tmp_path)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert completed.returncode != 0
    assert "ignored generated output required" in completed.stderr
    assert marker.read_text() == "keep"
    assert list(tmp_path.iterdir()) == [marker]


def test_existing_generated_directory_rejected_before_source_replay():
    generated = ROOT / "fea/generated"
    generated.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="shop-fresh-output-", dir=generated) as folder:
        marker = Path(folder) / "preserved"
        marker.write_text("keep")
        completed = subprocess.run([sys.executable, "-B", str(OWN), "--inputs-sha256", "0"*64,
                                    "--out", folder], cwd=ROOT, capture_output=True, text=True, check=False)
        assert completed.returncode != 0
        assert "File exists" in completed.stderr
        assert marker.read_text() == "keep"
        assert list(marker.parent.iterdir()) == [marker]


@pytest.mark.parametrize("key,value", [("schema", "wrong"), ("revision", "old"), ("optional_grid", True)])
def test_incompatible_scope_rejected_before_source_replay(tmp_path, key, value):
    inputs = read("inputs.json")
    inputs[key] = value
    path = tmp_path / "input.json"
    path.write_text(json.dumps(inputs))
    with pytest.raises(ValueError, match="current extra-off inputs required"):
        build(path, hashlib.sha256(path.read_bytes()).hexdigest())
