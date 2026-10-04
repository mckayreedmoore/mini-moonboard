"""Prepare and run the 994 applicable ordinary washer end references.

Import is inert. Parent-only build(output) reuses the pinned fine48 source
loader and unchanged annular edge method: three models, at most 958 loaded
state calls, and 36 exact-zero references. No central extension or retry.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-ordinary-fine-reference"
FINE48 = HERE / "washer-top-side-fine-reference.py"
FINE48_SHA = "3905be16b88c55feadfad9145f7aaf896cf1dd16691bf982f467d7922919cb53"
SOURCE = HERE / "rawlocal/washer-end-reference-join/attempt01"
SOURCE_SHA = "8f8b06d4a90b6c9462fb5f21fa398e42582a7d9be337c1fb327324b42d035783"
ROWS_SHA = "b5e3160ec167ee9ef00cd7542a7701912ce43ab4db4673abbaa6291e8d0c717e"
FULL_SUPPORT = {"SAVED_NOMINAL_FULL_ANNULUS_MATCHES_MODEL",
                "CURRENT_MATCHED_FULL_NOMINAL_ANNULUS"}
PROFILES = {
    "quarter": {"part": "K.L. Jack 25NWUS", "count": 850,
                "profile": {"inner_radius_mm": 4.1529, "outer_radius_mm": 9.2329,
                            "head_radius_mm": 5.0, "thickness_mm": 1.2954}},
    "retained_15025": {"part": "Bolt Depot 15025", "count": 48,
                       "profile": {"inner_radius_mm": 7.3279, "outer_radius_mm": 17.3736,
                                   "head_radius_mm": 9.3472, "thickness_mm": 2.1844}},
    "retained_15023": {"part": "Bolt Depot 15023", "count": 96,
                       "profile": {"inner_radius_mm": 5.7531, "outer_radius_mm": 12.6111,
                                   "head_radius_mm": 6.9977, "thickness_mm": 1.6256}},
}
FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
         "physical_release": False, "fabrication_release": False,
         "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
         "actual_washer_yield_mpa": None, "global_frame_feedback": False,
         "loaded_shift_or_tilt_qualified": False, "actual_hardware_inspected": False,
         "formal_criteria_updated": False, "coupon_or_retry_or_sweep_run": False,
         "CAD_or_shaft_or_frame_or_native_solve_run": False}
ELIGIBLE = "ELIGIBLE_POSITIVE_T_FINE_REFERENCE"
ZERO = "ANALYTIC_ZERO_DEMAND"
LIMIT = "HEAD_COMPRESSION_LOAD_PATH_LIMIT"


def load_fine48():
    """Reuse its inert source loader; do not execute its build or input_rows."""
    import hashlib
    if hashlib.sha256(FINE48.read_bytes()).hexdigest() != FINE48_SHA:
        raise ValueError("STOP: frozen fine48 consumer changed")
    spec = importlib.util.spec_from_file_location("ordinary_saved_fine48", FINE48)
    if spec is None or spec.loader is None:
        raise ValueError("STOP: frozen fine48 loader unavailable")
    prior = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior
    return module


def head_certificate(tension, magnitude, radius):
    # ponytail: exact source zeros only; a small positive load remains loaded.
    status = (ZERO if tension == 0.0 and magnitude == 0.0 else
              LIMIT if tension == 0.0 or magnitude / tension > radius else ELIGIBLE)
    return {"status": status, "T_n": tension, "M_magnitude_nmm": magnitude,
            "pressing_outer_radius_mm": radius,
            "eccentricity_mm": magnitude / tension if tension > 0.0 else None,
            "eccentricity_over_head_radius": magnitude / tension / radius if tension > 0.0 else None,
            "necessary_condition_only": True,
            "physical_hardware_failure_proved": False,
            "zero_force_nonzero_moment_invented_pressure": False}


def source_row(helper, api, row, profile_id):
    end, binding = row["own_end_source"], PROFILES[profile_id]
    profile, hypotheses = binding["profile"], end["contact_hypotheses"]
    inner, outer, head, thickness = (profile[k] for k in (
        "inner_radius_mm", "outer_radius_mm", "head_radius_mm", "thickness_mm"))
    catalog, origin = hypotheses["catalog_washer_envelope"], end["source_join"]
    helper.require(0 < inner < head < outer and thickness > 0
                   and row["seat_datum_match"] is True
                   and row["current_nominal_contact_patch_status"] in FULL_SUPPORT
                   and hypotheses["first_order"] is True and hypotheses["concentric_annuli"] is True
                   and hypotheses["preload_n"] == 0
                   and (hypotheses["Kwood_mpa_per_mm"], hypotheses["Khead_mpa_per_mm"]) == (20., 10000.)
                   and catalog["part"] == binding["part"]
                   and inner == catalog["inside_diameter_mm"][1] / 2
                   and outer == catalog["outside_diameter_mm"][0] / 2
                   and thickness == catalog["thickness_mm"][0]
                   and hypotheses["wood_contact_inner_outer_radii_mm"] == [inner, outer]
                   and hypotheses["head_nut_contact_inner_outer_radii_mm"] == [inner, head],
                   "full annulus, catalog minimum profile or unchanged contact law differs")
    helper.require(end["status"] == "COMPLETE_ISOLATED_END_SOURCE"
                   and end["schema"] == "ordinary_washer_own_end_source/v1"
                   and end["join_key"] == row["join_key"] == list(helper.identity(row))
                   and end["gap_scale"] == 1.0
                   and origin["source_comparison_sha256"] == api.PINS[api.FRAME]
                   and origin["source_response_sha256"] == api.PINS[api.RESPONSE]
                   and origin["fresh_force_source_sha256"] == row["fresh_force_source_sha256"],
                   "own-end identity or simultaneous frozen frame differs")
    normal = helper.vector(end["normal_into_receiver_xyz"], 3)
    moment = helper.vector(end["own_end_M_signed_xyz_nmm"], 3)
    force = helper.vector(end["force_on_receiver_xyz_n"], 3)
    tension, magnitude = float(end["normal_compression_T_n"]), float(row["own_end_M_magnitude_nmm"])
    helper.require(math.isfinite(tension) and tension >= 0 and math.isfinite(magnitude) and magnitude >= 0
                   and tension == row["fresh_signed_T_n"] == end["fresh_signed_T_n"]
                   and math.isclose(magnitude, float(end["own_end_M_magnitude_nmm"]), rel_tol=0, abs_tol=1e-6)
                   and math.isclose(math.hypot(*normal), 1, rel_tol=0, abs_tol=1e-8)
                   and helper.close_vector(force, [tension * x for x in normal], 1e-6)
                   and math.isclose(math.hypot(*moment), magnitude, rel_tol=0, abs_tol=1e-6)
                   and abs(api.dot(normal, moment)) <= 1e-6,
                   "simultaneous signed force or own-seat moment convention differs")
    certificate = head_certificate(tension, magnitude, head)
    if certificate["status"] == ZERO:
        helper.require(end["own_end_M_magnitude_nmm"] == 0.0 and all(x == 0.0 for x in force + moment),
                       "analytic zero would discard a nonzero physical vector")
    if magnitude > 0:
        local_x = [x / magnitude for x in api.cross(normal, moment)]
    else:
        basis = min(([1., 0., 0.], [0., 1., 0.], [0., 0., 1.]), key=lambda axis: abs(api.dot(axis, normal)))
        direction = api.cross(normal, basis)
        local_x = [x / math.hypot(*direction) for x in direction]
    helper.require(math.isclose(math.hypot(*local_x), 1, rel_tol=0, abs_tol=1e-8)
                   and helper.close_vector([magnitude * x for x in api.cross(local_x, normal)], moment, 1e-6),
                   "circular drive would lose the physical own-moment direction")
    wood_reference = float(row["wood_reference_mpa"])
    helper.require(math.isfinite(wood_reference) and wood_reference > 0,
                   "missing conditional timber base comparison")
    return {"state_id": "/".join(row["join_key"]), "join_key": row["join_key"],
            "case_id": row["case_id"], "axis_id": row["axis_id"], "end_role": row["end_role"],
            "receiver_member": row["receiver_member"], "profile_id": profile_id,
            "family": "rail", "T_n": tension, "M_magnitude_nmm": magnitude,
            "source_signed_own_M_xyz_nmm": moment, "force_on_receiver_xyz_n": force,
            "normal_into_receiver_xyz": normal,
            "own_seat_xyz_mm": helper.vector(end["end_wrench_datum_global_xyz_mm"], 3),
            "local_pressure_offset_x_xyz": local_x, "local_y_xyz": api.cross(normal, local_x),
            "plate_pressure_first_moment_targets_nmm": [magnitude, 0.],
            "head_compression_certificate": certificate,
            "saved_rigid_contact": end["saved_end_contact"],
            "rigid_contact_used_as_initialization_only": True,
            "conditional_wood_reference_mpa": wood_reference,
            "wood_reference_route": row["wood_reference_route"],
            "catalog_washer_envelope": catalog, "source_join": origin,
            "nominal_support_status": row["current_nominal_contact_patch_status"],
            "support_source": row["support_source"], "support_source_sha256": row["support_source_sha256"],
            "new_nominal_land_source": row["new_nominal_land_source"], "joined_receipt_sha256": SOURCE_SHA}


def inputs(helper, api, pins):
    _, receipt = helper.packet(pins, SOURCE, SOURCE_SHA, "washer-end-reference-join",
                               "washer_end_reference_join_receipt/v1")
    helper.require(receipt["status"] == "FINITE_JOIN_WITH_TWO_NULL_ENDS"
                   and receipt["sources_authenticated_before_and_after"] is True
                   and receipt["output_sha256"]["washer-end-states.jsonl"] == ROWS_SHA,
                   "completed join receipt differs")
    rows = [json.loads(line) for line in (SOURCE / "washer-end-states.jsonl").read_text().splitlines()]
    helper.require(len(rows) == len({tuple(row["join_key"]) for row in rows}) == 1056,
                   "joined end census differs")
    ordinary = [row for row in rows if row["scope"] == "outside_corner_axial_reference"]
    common = [row for row in rows if row["scope"] == "common_knee_outer_end_TM_source"]
    selected, remaining = {}, []
    for profile_id, binding in PROFILES.items():
        matching = [row for row in ordinary if row["own_end_source"]["status"] == "COMPLETE_ISOLATED_END_SOURCE"
                    and row["own_end_source"]["contact_hypotheses"]["catalog_washer_envelope"]["part"] == binding["part"]
                    and row["current_nominal_contact_patch_status"] in FULL_SUPPORT]
        helper.require(len(matching) == binding["count"] and {row["case_id"] for row in matching} == set(api.CASES),
                       "applicable profile census differs: " + profile_id)
        selected[profile_id] = [source_row(helper, api, row, profile_id)
                                for row in sorted(matching, key=lambda item: tuple(item["join_key"]))]
    selected_keys = {tuple(row["join_key"]) for group in selected.values() for row in group}
    for row in ordinary:
        if tuple(row["join_key"]) not in selected_keys:
            remaining.append({"join_key": row["join_key"], "source_status": row["source_status"],
                              "null_reason": row["source_null_reason"],
                              "contact_patch_status": row["current_nominal_contact_patch_status"],
                              "T_n": row["fresh_signed_T_n"], "M_nmm": row["own_end_M_magnitude_nmm"],
                              "central_static_trial": row["central_recovered_moment_static_trial"],
                              "direct_full_annulus_recipe_applicable": False})
    helper.require(len(ordinary) == 1008 and len(common) == 48 and len(selected_keys) == 994
                   and len(remaining) == 14
                   and sum(row["M_nmm"] is None for row in remaining) == 2
                   and sum(row["central_static_trial"] is not None for row in remaining) == 6,
                   "central/null/common separation differs")
    retained = helper.read(api.RETAINED_SUPPORT)
    seats = {(seat["axis_id"], seat["role"], seat["member"]): seat for seat in retained["seats"]}
    helper.require(retained["schema"] == "retained_washer_saved_step_support/v1" and len(seats) == 24,
                   "retained nominal support packet differs")
    for profile_id in ("retained_15025", "retained_15023"):
        profile = PROFILES[profile_id]["profile"]
        for source in selected[profile_id]:
            seat = seats[tuple(source["join_key"][1:])]
            annulus = seat["nominal_concentric_annulus_mm"]
            helper.require(source["support_source_sha256"] == api.PINS[api.RETAINED_SUPPORT]
                           and seat["washer_part"] == PROFILES[profile_id]["part"]
                           and annulus["maximum_id"] / 2 == profile["inner_radius_mm"]
                           and annulus["minimum_od"] / 2 == profile["outer_radius_mm"]
                           and helper.close_vector(source["own_seat_xyz_mm"],
                               seat["source_interval_face_binding"]["face_center_global_xyz_mm"], 1e-7)
                           and all(depth["nominal_concentric_supported_fraction"] >= 1 - 1e-6
                                   for depth in seat["depth_results"]),
                           "retained parameter instance lacks matching full nominal support")
    census = {}
    for profile_id, group in selected.items():
        counts = {status: sum(row["head_compression_certificate"]["status"] == status for row in group)
                  for status in (ELIGIBLE, ZERO, LIMIT)}
        loaded = [row for row in group if row["T_n"] > 0]
        peak = max(loaded, key=lambda row: row["head_compression_certificate"]["eccentricity_mm"])
        census[profile_id] = {"profile_binding": PROFILES[profile_id], "head_certificate_counts": counts,
                             "physical_nominal_lands": len({tuple(row["join_key"][1:]) for row in group}),
                             "maximum_eccentricity_witness": {"join_key": peak["join_key"],
                                                              **peak["head_compression_certificate"]},
                             "general_annular_method_accepts_parameter_instance": True,
                             "old_fixed_source_loader_used": False}
    return selected, census, remaining


def metrics_from_state(helper, source, state, fields):
    wood = max(fields, key=lambda row: row["wood_pressure_mpa"])
    stress = state["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"]
    metrics = {"sampled_stress_proxy_mpa": stress, "stress_proxy_over_Fy250": stress / 250.,
               "sampled_wood_pressure_peak_mpa": wood["wood_pressure_mpa"],
               "sampled_wood_peak_over_base_reference": wood["wood_pressure_mpa"] / source["conditional_wood_reference_mpa"],
               "wood_pressure_peak_witness": wood, "scaled_gradient_maximum_n": state["scaled_gradient_maximum_n"]}
    helper.require(all(math.isfinite(value) for key, value in metrics.items() if key != "wood_pressure_peak_witness"),
                   "nonfinite returned fine comparison")
    return metrics


def build(output):
    """Parent-only three-profile finite execution; preserve every numerical stop."""
    started = time.monotonic()
    output = Path(output).absolute()
    fine48 = load_fine48()
    helper, settings = fine48.load_helper(), dict(fine48.SETTINGS)
    helper.require(output.resolve() == output and output.parent == RAW and not output.exists(),
                   "use a fresh unaliased child of rawlocal/washer-ordinary-fine-reference")
    api = helper.load_n09()
    pins = {**api.PINS, FINE48: FINE48_SHA, fine48.HELPER: fine48.HELPER_SHA,
            helper.N09: helper.N09_SHA, Path(__file__).resolve(): helper.sha(__file__)}
    groups, census, remaining = inputs(helper, api, pins)
    helper.authenticate(pins)
    before = {api.display(path): helper.sha(path) for path in sorted(pins)}
    planned = sum(c["head_certificate_counts"][ELIGIBLE] for c in census.values())
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    plan = {"schema": "ordinary_fine_washer_plan/v1", "profiles_and_census": census,
            "resolution": settings, "source_rows": groups, "separate_central_and_null_rows": remaining,
            "unchanged_common_knee_rows_outside_run": 48,
            "source_receipt_sha256": SOURCE_SHA, "source_rows_sha256": ROWS_SHA,
            "solver_calls_allowed": ["make_model", "solve_state"],
            "planned_state_calls": planned, "maximum_model_calls": 3, **FLAGS}
    (output / "input-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n")
    edge, flexure, import_failure = None, None, None
    try:
        flexure = api.load_module(api.FLEXURE, "ordinary_fine_pinned_material_source")
        edge = api.load_module(api.EDGE, "ordinary_fine_pinned_edge_method")
        helper.require(flexure.FAMILIES["rail"] == PROFILES["quarter"]["profile"]
                       and edge.RESOLUTIONS["fine"] == settings
                       and (flexure.ESTEEL, flexure.NU, flexure.KWOOD, flexure.KHEAD, flexure.FY_HYPOTHESIS)
                           == (200000., 0.3, 20., 10000., 250.)
                       and (edge.GRADIENT_TOLERANCE, edge.FORCE_TOLERANCE, edge.MOMENT_TOLERANCE)
                           == (1e-4, .001, .02),
                       "fine resolution, existing rail profile or unchanged material/law tolerances differ")
    except (ValueError, RuntimeError, OSError, ArithmeticError, ImportError) as error:
        import_failure = {"error": str(error), "physical_incompatibility_proved": False}
    records, failures, timings = [], [], {}
    model_calls, state_calls = 0, 0
    with (output / "end-states.jsonl").open("x") as stream:
        for profile_id, sources in groups.items():
            group_started = time.monotonic()
            model, setup_failure = None, import_failure
            if setup_failure is None:
                try:
                    # The general helper reads this slot; its fixed old source loader is bypassed.
                    flexure.FAMILIES = {**flexure.FAMILIES, "rail": dict(PROFILES[profile_id]["profile"])}
                    model_calls += 1
                    model = edge.make_model(flexure, "fine")
                except (ValueError, RuntimeError, OSError, ArithmeticError) as error:
                    setup_failure = {"error": str(error), "physical_incompatibility_proved": False}
            setup_seconds = time.monotonic() - group_started
            for source in sources:
                state_started = time.monotonic()
                debug, state, failure, metrics = {}, None, None, None
                certificate_status = source["head_compression_certificate"]["status"]
                status = certificate_status
                if certificate_status == ZERO:
                    state = {"basis": "Exact T=0 and M=0 permits an unstressed zero-pressure reference.",
                             "pressure_mpa": 0., "stress_proxy_mpa": 0.,
                             "unique_unloaded_pose_established": False,
                             "head_closure_mm": None, "head_tilt_components_rad": None}
                    metrics = {"sampled_stress_proxy_mpa": 0., "stress_proxy_over_Fy250": 0.,
                               "sampled_wood_pressure_peak_mpa": 0., "sampled_wood_peak_over_base_reference": 0.,
                               "wood_pressure_peak_witness": None, "scaled_gradient_maximum_n": None,
                               "basis": "Analytical zero comparison; no numerical sampling or pose solve."}
                elif certificate_status == ELIGIBLE:
                    failure = setup_failure
                    if model is not None and failure is None:
                        try:
                            edge.STATE_ID = source["state_id"]
                            state_calls += 1
                            state, fields = edge.solve_state(model, source, debug)
                            metrics = metrics_from_state(helper, source, state, fields)
                            del fields
                        except (ValueError, RuntimeError, OSError, ArithmeticError) as error:
                            metrics = None
                            failure = {"error": str(error), "last_accepted_state": api.json_value(debug),
                                       "physical_incompatibility_proved": False, "retry_performed": False}
                    status = "FINITE_ORDINARY_WASHER_HYPOTHESIS" if failure is None else "NUMERICAL_STOP"
                record = {"join_key": source["join_key"], "profile_id": profile_id, "source": source,
                          "status": status, "state": api.json_value(state), "metrics": metrics,
                          "failure": failure, "elapsed_seconds": time.monotonic() - state_started, **FLAGS}
                if failure is not None:
                    failures.append({"join_key": source["join_key"], "profile_id": profile_id, **failure})
                records.append(record)
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
            timings[profile_id] = {"setup_seconds": setup_seconds,
                                   "total_seconds": time.monotonic() - group_started}
            del model  # Keep only one 1,142-unknown profile assembly resident.
    finite = [row for row in records if row["status"] == "FINITE_ORDINARY_WASHER_HYPOTHESIS"]
    zero = [row for row in records if row["status"] == ZERO]
    limits = [row["join_key"] for row in records if row["status"] == LIMIT]
    exceedances = [row["join_key"] for row in finite if row["metrics"]["stress_proxy_over_Fy250"] > 1.]
    witnesses = {}
    for column in ("sampled_stress_proxy_mpa", "stress_proxy_over_Fy250", "sampled_wood_peak_over_base_reference"):
        row = max(finite, key=lambda item: item["metrics"][column]) if finite else None
        witnesses[column] = None if row is None else {"join_key": row["join_key"], "profile_id": row["profile_id"],
            "value": row["metrics"][column], "same_state_T_n": row["source"]["T_n"],
            "same_state_M_nmm": row["source"]["M_magnitude_nmm"],
            "conditional_wood_reference_mpa": row["source"]["conditional_wood_reference_mpa"]}
    helper.authenticate(pins)
    after = {api.display(path): helper.sha(path) for path in sorted(pins)}
    helper.require(before == after, "source bytes changed during ordinary fine run")
    status = "FINITE_ORDINARY_WASHER_REFERENCES"
    if failures or limits:
        status = "PARTIAL_ORDINARY_WASHER_REFERENCES_WITH_EXPLICIT_LIMITS"
    elif exceedances:
        status = "FINITE_ORDINARY_WASHER_REFERENCES_WITH_HYPOTHETICAL_YIELD_EXCEEDANCES"
    counts = {"source_end_states": len(records), "completed_end_states": len(finite) + len(zero),
              "completed_numerical_states": len(finite), "analytic_zero_states": len(zero),
              "compression_only_head_load_path_limits": len(limits), "numerical_stops": len(failures),
              "model_calls": model_calls, "state_calls": state_calls, "planned_state_calls": planned,
              "sampled_Fy250_exceedances": len(exceedances), "separate_central_rows": 12,
              "separate_central_static_trials": 6, "separate_null_ordinary_rows": 2,
              "separate_common_knee_rows": 48}
    result = {"schema": "ordinary_fine_washer_reference/v1", "status": status, "counts": counts,
              "profiles_and_source_census": census, "resolution": settings,
              "hypotheses": {"E_mpa": 200000., "nu": .3, "Fy_mpa_comparator": 250.,
                             "Kwood_mpa_per_mm": 20., "Khead_mpa_per_mm": 10000.,
                             "catalog_ID_max_OD_min_thickness_min": True,
                             "primary_energy_source": flexure.ENERGY_SOURCE if flexure else None},
              "same_state_peak_witnesses": witnesses, "sampled_yield_exceedance_keys": exceedances,
              "head_load_path_limit_keys": limits, "import_failure": import_failure,
              "numerical_failures": failures, "separate_central_and_null_rows": remaining,
              "source_receipt_sha256": SOURCE_SHA, "source_before_sha256": before,
              "source_after_sha256": after, "sources_authenticated_before_and_after": True,
              "runtime": {"python": sys.version, "numpy": edge.np.__version__ if edge else None,
                          "scipy": edge.scipy.__version__ if edge else None,
                          "elapsed_seconds": time.monotonic() - started, "profile_seconds": timings},
              "limits": ["Necessary head-pressure centroid certificate does not establish compatible contact or strength.",
                         "Exact zero-force/zero-moment references do not establish a unique unloaded pose.",
                         "Own-end force/moment is prescribed; no washer feedback into shaft/group/frame equilibrium.",
                         "Full nominal support is bound; loaded shift/tilt and changed support remain unqualified.",
                         "Circular head profiles, catalog minimum thickness, steel properties and seat stiffness remain hypotheses.",
                         "The quarter profile geometry matches an older catalog envelope; no grade or capacity transfers.",
                         "Sampled stress excludes contact sigmaZZ, three-dimensional edges, plasticity, friction and preload.",
                         "No new convergence sweep or actual washer resistance qualification is performed.",
                         "Timber comparison retains each end's existing conditional base reference and grain route.",
                         "Twelve central restricted-contact rows, including six static trials, are outside this full-annulus recipe.",
                         "Two G7 unknown-moment rows are not zero-load references; 48 common-knee rows stay separate.",
                         "Numerical stops remain explicit; no retry, added stiffness or physical failure inference.",
                         "All formal criteria and joint/release HOLD boundaries remain unchanged."], **FLAGS}
    (output / "washer-ordinary-fine-reference.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    artifacts = {path.name: helper.sha(path) for path in sorted(output.iterdir()) if path.is_file()}
    (output / "receipt.json").write_text(json.dumps({"schema": "ordinary_fine_washer_reference_receipt/v1",
        "status": status, "source_sha256": before, "source_before_sha256": before, "source_after_sha256": after,
        "sources_authenticated_before_and_after": True, "output_sha256": artifacts,
        "counts": counts, **FLAGS}, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "same_state_peak_witnesses": result["same_state_peak_witnesses"]}, indent=2))
