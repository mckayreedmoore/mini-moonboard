"""Join the final 1008 ordinary washer ends, retaining two explicit nulls.

Import is inert. Parent-only build(output) reuses frozen join arithmetic and
completed nominal geometry. No shaft, contact, plate, CAD or frame solve runs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-end-reference-join"
HELPER = HERE / "washer-end-source-completion.py"
HELPER_SHA = "dbf242d54ae501c0bf8d4241447837dcf08e7e4d2d108703f43a2fc0e1c078c9"
BASE = HERE / "rawlocal/washer-end-source-completion/attempt02"
BASE_SHA = "d974544f39a670bde1d9a493754224b199fe10f5126fc266f9914101d5fcbe00"
N10 = HERE / "rawlocal/bolt-reference-completion/two-recovery-attempt01"
N10_SHA = "353f5890dd8cccc8db5cbf29bd7f2daa1de8877e3031825343a807a47421aa22"
N10_SUMMARY_SHA = "776f597ec63e31be4c45a87302f0d849222cc6f4346361dda6d2bf8df04c43b0"
LAND = HERE / "rawlocal/washer-land-completion/attempt01"
LAND_SHA = "7d541cef4b05b03a6d501243759dd1ea435eeb42be4ce2d71eda27cd9ea78679"
SIDE = HERE / "rawlocal/washer-land-reference-completion/attempt01"
SIDE_SHA = "0218731514788a808ea8cb313945fe1000cbf63b51c181c9415b366ab374a46a"
NULL_AXIS = "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1"
NULL_KEYS = {("a12-left", NULL_AXIS, "head", "wj04_upper_g7_crosscut_full_stock_cleat"),
             ("a12-left", NULL_AXIS, "nut", "base_rail_service_upper_right")}
FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
         "fabrication_release": False, "physical_release": False,
         "actual_washer_capacity_n": None, "actual_washer_stress_mpa": None,
         "actual_washer_yield_mpa": None, "global_frame_feedback": False,
         "loaded_shift_or_tilt_qualified": False, "new_solver_calls": 0,
         "formal_criteria_updated": False}


def load_helper():
    import hashlib
    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
        raise ValueError("STOP: frozen source consumer changed")
    spec = importlib.util.spec_from_file_location("washer_end_frozen_join", HELPER)
    if spec is None or spec.loader is None:
        raise ValueError("STOP: frozen source consumer loader unavailable")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def n10_packet(helper, pins):
    """Bind consumed producer history to its snapshots; leave old receipts intact."""
    helper.add_pin(pins, N10 / "receipt.json", N10_SHA)
    helper.authenticate(pins)
    receipt = helper.read(N10 / "receipt.json")
    helper.require(receipt["schema"] == "bolt_reference_completion_receipt/v2"
                   and receipt["mode"] == "full"
                   and receipt["status"] == "PARTIAL_NULL_SHAFT_STATES"
                   and receipt["sources_authenticated_before_and_after"] is True
                   and receipt["complete_joint_acceptance"] is False
                   and receipt["physical_release"] is False
                   and receipt["output_sha256"]["summary.json"] == N10_SUMMARY_SHA,
                   "final N10 receipt identity, scope or boundaries differ")
    for name, expected in {"completed_shaft_states": 503, "null_shaft_states": 1,
                           "washer_end_states": 1008, "recovered_washer_end_states": 1006,
                           "null_washer_end_states": 2}.items():
        helper.require(receipt["counts"][name] == expected, "final N10 census differs: " + name)
    substitutions = []
    maintained = HERE / "bolt-reference-completion.py"
    for name, digest in receipt["source_sha256"].items():
        original = ROOT / name
        if original == maintained:
            helper.require(digest == receipt["producer_sha256"]
                           == receipt["output_sha256"]["producer.py.snapshot"],
                           "N10 maintained producer does not match its consumed snapshot")
            resolved = N10 / "producer.py.snapshot"
            substitutions.append({"original_source_path": name, "original_source_sha256": digest,
                                  "authenticated_snapshot_path": resolved.relative_to(ROOT).as_posix(),
                                  "receipt_or_source_repinned": False})
        else:
            resolved = original
        helper.add_pin(pins, resolved, digest)
    for name, digest in receipt["output_sha256"].items():
        helper.require(Path(name).name == name and not (N10 / name).is_symlink(), "N10 artifact alias")
        helper.add_pin(pins, N10 / name, digest)
    historical = receipt["historical_producer_snapshot_bindings"]
    helper.require(len(historical) == 3 and len(substitutions) == 1,
                   "N01/full/recovery producer snapshot census differs")
    for binding in historical:
        helper.require(ROOT / binding["original_maintained_path"] == maintained,
                       "historical producer belongs to another maintained source")
        helper.add_pin(pins, ROOT / binding["snapshot_path"], binding["sha256"])
    helper.require(receipt["historical_producer_snapshot_binding"] in historical,
                   "single recovery snapshot is absent from full history")
    helper.authenticate(pins)
    return receipt, substitutions


def current_land_reference(helper, row, end, lands, requests):
    """Add current geometry credit only for the same physical ring and datum."""
    row["current_nominal_contact_patch_status"] = row["contact_patch_geometry_status"]
    row["current_bound_rigid_wood_peak_over_reference"] = row["rigid_model_continuous_wood_peak_over_reference"]
    row["current_metal_method_candidate"] = row["existing_metal_method_candidate"]
    row["new_nominal_land_source"] = None
    key = tuple(end["join_key"][1:])
    land = lands.get(key)
    if (end["status"] != "COMPLETE_ISOLATED_END_SOURCE" or land is None
            or not land["nominal_annulus_support_established"]):
        return
    request = requests[key]
    radii = end["contact_hypotheses"]["wood_contact_inner_outer_radii_mm"]
    if not (helper.close_vector(radii, request["annulus_inner_outer_radii_mm"], 1e-9)
            and helper.close_vector(end["end_wrench_datum_global_xyz_mm"], land["point_xyz_mm"], 1e-7)
            and helper.close_vector(end["normal_into_receiver_xyz"], land["inward_normal_xyz"], 1e-8)):
        return
    helper.require(math.isclose(math.pi * (radii[1] ** 2 - radii[0] ** 2),
                                row["ideal_annulus_area_mm2"], rel_tol=0, abs_tol=1e-6),
                   "current supported ring does not match the original area reference")
    row["current_nominal_contact_patch_status"] = "CURRENT_MATCHED_FULL_NOMINAL_ANNULUS"
    row["new_nominal_land_source"] = {"path": (LAND / "washer-land-completion.json").relative_to(ROOT).as_posix(),
                                     "receipt_sha256": LAND_SHA, "physical_land_key": list(key)}
    if row["wood_reference_mpa"] is not None:
        row["current_bound_rigid_wood_peak_over_reference"] = (
            row["rigid_model_continuous_wood_pressure_peak_mpa"] / row["wood_reference_mpa"])
    head = end["contact_hypotheses"]["head_nut_contact_inner_outer_radii_mm"]
    if helper.close_vector(radii, [4.1529, 9.2329], 1e-9) and helper.close_vector(head, [4.1529, 5.0], 1e-9):
        row["current_metal_method_candidate"] = "original_quarter_inch_fine_plate_hypothesis_not_executed"


def build(output):
    """Parent-only saved-source join and arithmetic; no engineering solver import."""
    output = Path(output).absolute()
    helper = load_helper()
    helper.require(output.resolve() == output and output.parent == RAW and not output.exists(),
                   "use a fresh unaliased child of rawlocal/washer-end-reference-join")
    api = helper.load_n09()
    pins = {**api.PINS, HELPER: HELPER_SHA, helper.N09: helper.N09_SHA,
            Path(__file__).resolve(): helper.sha(__file__)}
    helper.packet(pins, BASE, BASE_SHA, "washer-end-source-completion", "washer_end_source_completion_receipt/v1")
    n10_receipt, substitutions = n10_packet(helper, pins)
    helper.packet(pins, LAND, LAND_SHA, "washer-land-completion", "washer_land_completion_receipt/v1")
    helper.packet(pins, SIDE, SIDE_SHA, "washer-land-reference-completion", "washer_land_reference_completion_receipt/v1")
    baseline = [json.loads(line) for line in (BASE / "washer-end-states.jsonl").read_text().splitlines()]
    ordinary = {helper.identity(row): row for row in baseline if row["scope"] == "outside_corner_axial_reference"}
    common = [row for row in baseline if row["scope"] == "common_knee_outer_end_TM_source"]
    ends = [json.loads(line) for line in (N10 / "washer-ends.jsonl").read_text().splitlines()]
    keyed = {helper.identity(row): row for row in ends}
    helper.require(len(baseline) == 1056 and len(common) == 48
                   and all(row["own_end_M_magnitude_nmm"] is not None for row in common)
                   and len(ends) == len(keyed) == len(ordinary) == 1008
                   and set(keyed) == set(ordinary)
                   and {row["case_id"] for row in ends} == set(api.CASES)
                   and len({row["axis_id"] for row in ends}) == 84
                   and {helper.identity(row) for row in ends if row["status"] == "NULL_UNSUPPORTED"} == NULL_KEYS,
                   "ordinary/common census or two final null keys differ")
    axis_map = {row["axis_id"]: row for row in helper.read(api.REGISTER)["axes"]}
    support, *_context = api.normalized_supports(pins, axis_map)
    for seat in helper.read(api.RETAINED_SUPPORT)["seats"]:
        saved = support[(seat["axis_id"], seat["member"])]
        saved["seat_point_xyz_mm"] = seat["source_interval_face_binding"]["face_center_global_xyz_mm"]
        annulus = seat["nominal_concentric_annulus_mm"]
        saved["annulus_inner_outer_radii_mm"] = [annulus["maximum_id"] / 2, annulus["minimum_od"] / 2]
    central = helper.read(api.CENTRAL)
    land_result = helper.read(LAND / "washer-land-completion.json")
    lands = {tuple(row["physical_land_key"]): row for row in land_result["geometry"]["seats"]}
    requests = {tuple(row["physical_land_key"]): row for row in helper.read(LAND / "worker-input.json")["new_land_queries"]}
    side_result = helper.read(SIDE / "washer-land-reference-completion.json")
    helper.require(len(lands) == len(requests) == 20
                   and side_result["status"] == "COMPLETE_MATCHED_TOP_SIDE_NOMINAL_REFERENCES"
                   and side_result["counts"]["full_actual_profile_lands"] == 8,
                   "completed nominal-land inputs differ")
    helper.authenticate(pins)
    before = {api.display(path): helper.sha(path) for path in sorted(pins)}
    joined = []
    for key in sorted(keyed):
        row = helper.join_row(api, ordinary[key], keyed[key], support[(key[1], key[3])], central)
        current_land_reference(helper, row, keyed[key], lands, requests)
        joined.append(row)
    joined.extend(common)  # ponytail: retain the completed common-pose recovery exactly.
    finite = [row for row in joined if row["own_end_M_magnitude_nmm"] is not None]
    null = [row for row in joined if row["own_end_M_magnitude_nmm"] is None]
    helper.require(len(finite) == 1054 and len(null) == 2, "final finite/null end census differs")
    witnesses = {}
    for column in ("fresh_signed_T_n", "own_end_M_magnitude_nmm", "own_end_eccentricity_mm",
                   "current_bound_rigid_wood_peak_over_reference"):
        available = [(row, row.get(column, row.get("rigid_model_continuous_wood_peak_over_reference")
                                   if column == "current_bound_rigid_wood_peak_over_reference" else None))
                     for row in joined]
        available = [(row, value) for row, value in available if value is not None]
        witness, value = max(available, key=lambda item: item[1]) if available else (None, None)
        witnesses[column] = None if witness is None else {
            "join_key": witness["join_key"], "scope": witness["scope"], "value": value,
            "same_state_T_n": witness["fresh_signed_T_n"], "same_state_M_nmm": witness["own_end_M_magnitude_nmm"]}
    trials = [{"join_key": row["join_key"], **row["central_recovered_moment_static_trial"]}
              for row in joined if row["central_recovered_moment_static_trial"] is not None]
    helper.authenticate(pins)
    after = {api.display(path): helper.sha(path) for path in sorted(pins)}
    helper.require(before == after, "source bytes changed during fixed-source join")
    result = {"schema": "washer_end_reference_join/v1", "status": "FINITE_JOIN_WITH_TWO_NULL_ENDS",
              "counts": {"ordinary_rows_consumed": 1008, "ordinary_finite_own_ends": 1006,
                         "ordinary_null_own_ends": 2, "completed_N10_shafts": 503,
                         "common_knee_rows_reused_unchanged": 48, "joined_rows": 1056,
                         "finite_own_end_sources": 1054, "null_own_end_sources": 2,
                         "new_current_nominal_land_rows": sum(row.get("new_nominal_land_source") is not None for row in joined),
                         "central_recovered_moment_trials": len(trials),
                         "retail_plate_states_in_separate_unchanged_packet": 48,
                         "top_side_mean_states_in_separate_packet": 48},
              "same_state_peak_witnesses": witnesses,
              "central_recovered_moment_trials": trials,
              "null_end_sources": [{"join_key": row["join_key"], "reason": row["source_null_reason"],
                                    "fresh_signed_T_n": row["fresh_signed_T_n"],
                                    "own_end_M_magnitude_nmm": None,
                                    "unknown_moment_not_set_to_zero": True} for row in null],
              "n10_receipt_sha256": N10_SHA, "historical_snapshot_substitutions": substitutions,
              "historical_producer_snapshot_bindings": n10_receipt["historical_producer_snapshot_bindings"],
              "original_common_source_receipt_sha256": BASE_SHA,
              "separate_top_side_nominal_mean_reference": {"receipt_sha256": SIDE_SHA,
                  "status": side_result["status"], "same_state_peak_witnesses": side_result["same_state_peak_witnesses"]},
              "source_before_sha256": before, "source_after_sha256": after,
              "sources_authenticated_before_and_after": True,
              "limits": ["Finite source coverage is not complete joint or washer qualification.",
                         "Ordinary ends are isolated first-order hypotheses; common-knee poses are reused without frame feedback.",
                         "Nominal lands do not establish loaded support; pressure maxima use the rigid contact law, not washer flexure.",
                         "Original support applicability is retained; current matched geometry is added in separate fields.",
                         "Central static trials do not prove elastic compatibility, first yield or actual capacity.",
                         "Fine plate candidates are not executed; retained larger washer families remain separate.",
                         "Actual top-side 5/16 mean references and quarter-inch retail stress references are separate, without family transfer.",
                         "All authority, formal criteria and release HOLD boundaries remain unchanged."], **FLAGS}
    output.mkdir(parents=True)
    files = {".gitignore": "*\n", "producer.py.snapshot": Path(__file__).read_text(),
             "washer-end-reference-join.json": json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
             "washer-end-states.jsonl": "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in joined)}
    for name, payload in files.items():
        with (output / name).open("x") as stream:
            stream.write(payload)
    with (output / "receipt.json").open("x") as stream:
        json.dump({"schema": "washer_end_reference_join_receipt/v1", "status": result["status"],
                   "source_sha256": before, "source_before_sha256": before, "source_after_sha256": after,
                   "sources_authenticated_before_and_after": True,
                   "output_sha256": {name: helper.sha(output / name) for name in files},
                   "counts": result["counts"], **FLAGS}, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"]}, indent=2))
