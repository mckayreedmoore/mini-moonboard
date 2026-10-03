"""Complete saved washer-end sources and prepare missing land queries.

Import is inert. The parent executes ``build`` against completed N09 and
common-knee packets, optionally supplying a full N10 endpoint packet. No
shaft, contact, plate, frame, CAD or native solver runs in this consumer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-end-source-completion"
N09 = HERE / "washer-reference-completion.py"
N09_SHA = "8746aed9bba5c8a1a897bb1bbf60a14ecd3f0928a760803ca05a309231a3575a"
N09_DIRECTORY = HERE / "rawlocal/washer-reference-completion/attempt02"
N09_RECEIPT_SHA = "fceaeb1c3d2a2f4d6e23ec1beb19e48ad40e8ab1a2eac1d50b5d39b7af4acac2"
COMMON_DIRECTORY = HERE / "rawlocal/knee-common-shafts/attempt01"
COMMON_RECEIPT_SHA = "7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda"
COMMON_REPORT_SHA = "dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0"
FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
         "physical_release": False, "fabrication_release": False,
         "actual_washer_capacity_n": None, "actual_washer_stress_mpa": None}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def add_pin(pins, path, digest):
    path = Path(path).resolve()
    require(path not in pins or pins[path] == digest, "conflicting source binding: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source bytes changed: " + str(path))


def packet(pins, directory, receipt_sha, raw_name, schema):
    directory = Path(directory).absolute()
    require(directory.resolve() == directory
            and directory.parent == HERE / "rawlocal" / raw_name,
            "input must be an unaliased immediate child of " + raw_name)
    require(len(receipt_sha) == 64 and set(receipt_sha) <= set("0123456789abcdef"),
            "freeze the input receipt SHA-256 explicitly")
    receipt_path = directory / "receipt.json"
    add_pin(pins, receipt_path, receipt_sha)
    require(sha(receipt_path) == receipt_sha, "input receipt differs from the parent's freeze")
    receipt = read(receipt_path)
    require(receipt["schema"] == schema and receipt["complete_joint_acceptance"] is False
            and receipt["physical_release"] is False, "input receipt schema or claim boundary differs")
    for name, digest in receipt["output_sha256"].items():
        require(Path(name).name == name and not (directory / name).is_symlink(),
                "input artifact is not an ordinary file in its frozen packet")
        add_pin(pins, directory / name, digest)
    for name, digest in receipt["source_sha256"].items():
        add_pin(pins, ROOT / name, digest)
    authenticate(pins)
    return directory, receipt


def identity(row):
    return tuple(row[key] for key in ("case_id", "axis_id", "end_role", "receiver_member"))


def vector(value, size):
    require(isinstance(value, list) and len(value) == size, "missing physical vector")
    result = [float(x) for x in value]
    require(all(math.isfinite(x) for x in result), "nonfinite physical vector")
    return result


def close_vector(actual, expected, tolerance):
    return max(abs(a - b) for a, b in zip(actual, expected, strict=True)) <= tolerance


def load_n09():
    require(sha(N09) == N09_SHA, "N09 source differs from the corrected frozen mapping")
    spec = importlib.util.spec_from_file_location("washer_end_saved_support", N09)
    require(spec is not None and spec.loader is not None, "N09 support reader unavailable")
    prior = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior
    return module


def csv_rows(path):
    # ponytail: retain the original worksheet; annotate a separate ordinary-end join.
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key, value in row.items():
            try:
                row[key] = json.loads(value)
            except json.JSONDecodeError:
                pass
    return rows


def central_trial(api, contract, end):
    """Reuse the existing centered ring ansatz with recovered own-seat M."""
    require(end["axis_id"] == contract["axis_id"] and end["receiver_member"] == contract["body"]
            and end["end_role"] == "nut", "central ring receiver differs")
    require(close_vector(vector(end["end_wrench_datum_global_xyz_mm"], 3),
                         contract["seat_point_global_xyz_mm"], 1e-7)
            and close_vector(vector(end["normal_into_receiver_xyz"], 3),
                             contract["inward_global_xyz"], 1e-8), "central ring datum or normal differs")
    radii = end["contact_hypotheses"]["wood_contact_inner_outer_radii_mm"]
    head_radii = end["contact_hypotheses"]["head_nut_contact_inner_outer_radii_mm"]
    require(close_vector(radii, [4.1529, 5.0], 1e-9)
            and close_vector(head_radii, radii, 1e-9), "central paired contact rings differ")
    patch = contract["credited_transfer_patch"]
    area, second = float(patch["area_mm2"]), float(patch["second_moment_yy_zz_mm4"])
    require(patch["unsupported_crescent_credited"] is False
            and patch["full_washer_annulus_credited"] is False, "central unsupported area was credited")
    force = vector(end["force_on_receiver_xyz_n"], 3)
    moment = vector(end["own_end_M_signed_xyz_nmm"], 3)
    require(max(abs(force[1]), abs(force[2]), abs(moment[0])) <= 1e-7,
            "central normal-column ansatz cannot transmit shear or torsion")
    mean = force[0] / area
    amplitude = 5.0 * math.hypot(moment[1], moment[2]) / second
    minimum, maximum = mean - amplitude, mean + amplitude
    admissible = minimum >= 0.0
    return {"status": "COMPRESSION_ONLY_STATIC_TRIAL" if admissible else "AFFINE_TRIAL_REQUIRES_TENSION",
            "moment_provenance": "recovered N10 own-seat receiver moment, not the old axial-tie lever",
            "area_mm2": area, "second_moment_mm4": second,
            "q_mean_mpa": mean, "q_min_mpa": minimum, "q_max_mpa": maximum,
            "compression_only": admissible,
            "required_hypothetical_ductile_washer_yield_mpa": maximum if admissible else None,
            "q_max_over_conditional_Fc_perp": maximum / api.FC_PERP_MPA if admissible else None,
            "identical_boundary_pressure_fields_assumed": True,
            "elastic_contact_compatibility_established": False,
            "first_yield_or_actual_capacity_established": False,
            "full_washer_annulus_or_crescent_credited": False}


def join_row(api, baseline, end, saved, contract):
    require(identity(baseline) == identity(end) and end["join_key"] == list(identity(end))
            and end["schema"] == "ordinary_washer_own_end_source/v1" and end["gap_scale"] == 1.0,
            "ordinary own-end key or force-state scope differs")
    source = end["source_join"]
    require(source["source_comparison_sha256"] == api.PINS[api.FRAME]
            and source["source_response_sha256"] == api.PINS[api.RESPONSE]
            and source["fresh_force_source_sha256"] == baseline["fresh_force_source_sha256"]
            and source["fresh_source_row_id"] == baseline["fresh_source_row_id"],
            "own-end source belongs to a different simultaneous response or axial tie")
    require(math.isclose(float(end["fresh_signed_T_n"]), float(baseline["fresh_signed_T_n"]),
                         rel_tol=0, abs_tol=1e-8), "own-end axial force differs from N09")
    row = {**baseline, "join_key": list(identity(end)), "source_status": end["status"],
           "source_null_reason": end["null_reason"], "own_end_source": end,
           "own_end_M_magnitude_nmm": None, "own_end_M_signed_xyz_nmm": None,
           "local_end_moment_status": "UNKNOWN_NOT_SET_TO_ZERO",
           "seat_datum_match": None, "contact_patch_geometry_status": "NOT_EVALUATED",
           "rigid_model_continuous_wood_pressure_peak_mpa": None,
           "rigid_model_continuous_wood_peak_over_reference": None,
           "own_end_eccentricity_mm": None, "existing_metal_method_candidate": None,
           "central_recovered_moment_static_trial": None,
           "metal_simultaneous_TM_status": "UNQUALIFIED_END_SOURCE_OR_METAL_METHOD", **FLAGS}
    if end["status"] != "COMPLETE_ISOLATED_END_SOURCE":
        require(end["status"] == "NULL_UNSUPPORTED"
                and end["own_end_M_magnitude_nmm"] is None, "unsupported end carries an accepted moment")
        return row
    axis = vector(end["shaft_axis_head_to_nut_xyz"], 3)
    inward = vector(end["normal_into_receiver_xyz"], 3)
    force = vector(end["force_on_receiver_xyz_n"], 3)
    moment = vector(end["own_end_M_signed_xyz_nmm"], 3)
    tension, magnitude = float(end["normal_compression_T_n"]), math.hypot(*moment)
    sign = 1 if end["end_role"] == "head" else -1
    require(math.isclose(math.hypot(*axis), 1.0, abs_tol=1e-8)
            and close_vector(inward, [sign * x for x in axis], 1e-8)
            and close_vector(force, [tension * x for x in inward], 1e-7)
            and math.isclose(float(end["signed_T_n"]), sign * tension, rel_tol=0, abs_tol=1e-7)
            and math.isclose(tension, float(baseline["fresh_signed_T_n"]), rel_tol=0, abs_tol=1e-8)
            and math.isclose(float(end["own_end_M_magnitude_nmm"]), magnitude, rel_tol=0, abs_tol=1e-6)
            and abs(api.dot(moment, axis)) <= 1e-6, "signed end force/moment convention differs")
    recovery = end["pressure_recovery"]
    expected = force + moment
    require(close_vector(vector(recovery["wood_pressure_wrench_at_seat_n_nmm"], 6), expected, 1e-6)
            and close_vector(vector(recovery["washer_force_moment_balance_residual_n_nmm"], 6), [0.] * 6, 1e-6),
            "saved own-seat pressure resultants do not balance")
    require(saved["modeled_support_applicability"] is baseline["modeled_support_applicability"],
            "N09 saved support applicability changed")
    seat = saved["seat_point_xyz_mm"]
    row.update({"own_end_M_magnitude_nmm": magnitude, "own_end_M_signed_xyz_nmm": moment,
                "local_end_moment_status": end["local_end_moment_status"],
                "own_end_eccentricity_mm": magnitude / tension if tension > 0 else None,
                "seat_datum_match": close_vector(vector(end["end_wrench_datum_global_xyz_mm"], 3), seat, 1e-7)
                    if seat is not None else None,
                "metal_simultaneous_TM_status": "OWN_END_SOURCE_AVAILABLE_METAL_TRANSFER_PENDING"})
    hypotheses = end["contact_hypotheses"]
    radii = vector(hypotheses["wood_contact_inner_outer_radii_mm"], 2)
    head_radii = vector(hypotheses["head_nut_contact_inner_outer_radii_mm"], 2)
    wood = end["saved_end_contact"]["wood_contact"]
    require(hypotheses["first_order"] is True and hypotheses["rigid_washer"] is True
            and hypotheses["concentric_annuli"] is True and hypotheses["preload_n"] == 0
            and 0 < radii[0] < radii[1], "end contact hypothesis changed")
    peak = (float(hypotheses["Kwood_mpa_per_mm"]) * max(
        float(wood["closure_mm"]) + abs(float(wood["tilt_rad"])) * radii[1], 0.0)
        if tension > 0 else 0.0)
    row["zero_T_contact_inactive_under_source_law"] = tension == 0
    row["rigid_model_continuous_wood_pressure_peak_mpa"] = peak
    if identity(end)[1:] == (contract["axis_id"], "nut", contract["body"]):
        trial = central_trial(api, contract, end)
        row["central_recovered_moment_static_trial"] = trial
        row["contact_patch_geometry_status"] = "DOCUMENTED_CENTRAL_RING_ONLY"
        row["existing_metal_method_candidate"] = "central_supported_ring_static_trial"
    else:
        full_area = float(baseline["ideal_annulus_area_mm2"])
        saved_radii = saved.get("annulus_inner_outer_radii_mm",
                                [api.GENERIC_INNER_MM, api.GENERIC_OUTER_MM])
        matched_ring = close_vector(radii, saved_radii, 1e-9) and math.isclose(
            math.pi * (radii[1] ** 2 - radii[0] ** 2), full_area, rel_tol=0, abs_tol=1e-6)
        full_support = saved["modeled_support_applicability"] is True and float(saved["saved_support_fraction"] or 0) >= 1 - 1e-6
        if row["seat_datum_match"] is True and matched_ring and full_support:
            row["contact_patch_geometry_status"] = "SAVED_NOMINAL_FULL_ANNULUS_MATCHES_MODEL"
            if baseline["wood_reference_mpa"] is not None:
                row["rigid_model_continuous_wood_peak_over_reference"] = peak / baseline["wood_reference_mpa"]
            if close_vector(radii, [4.1529, 9.2329], 1e-9) and close_vector(head_radii, [4.1529, 5.0], 1e-9):
                row["existing_metal_method_candidate"] = "original_quarter_inch_fine_plate_hypothesis_not_executed"
        else:
            row["contact_patch_geometry_status"] = "END_DATUM_OR_COMPLETE_ANNULUS_SUPPORT_UNRESOLVED"
    return row


def recover_traction(api, traction, seat, common_datum, force_tolerance, moment_tolerance):
    points, forces = traction["reference_points_mm"], traction["point_forces_xyz_n"]
    require(len(points) == len(forces) == len(traction["pressure_mpa"])
            == len(traction["quadrature_area_mm2"]) == 256, "common end quadrature census differs")
    force = [math.fsum(float(f[i]) for f in forces) for i in range(3)]
    terms = [api.cross([p[i] - seat[i] for i in range(3)], vector(f, 3))
             for p, f in zip(points, forces, strict=True)]
    moment = [math.fsum(term[i] for term in terms) for i in range(3)]
    about_common = [a + b for a, b in zip(
        moment, api.cross([seat[i] - common_datum[i] for i in range(3)], force), strict=True)]
    integrated = traction["integrated_wrench_about_common_datum"]
    require(close_vector(force, vector(integrated["force_xyz_n"], 3), force_tolerance)
            and close_vector(about_common, vector(integrated["moment_xyz_nmm"], 3), moment_tolerance),
            "point tractions disagree with the saved common-datum wrench")
    return force, moment


def common_rows(api, baseline, support, directory, receipt):
    """Replace only the old isolated 48 ends, using the accepted common poses."""
    require(receipt["status"] == "COMPLETE_12_CONDITIONAL_COMMON_RECEIVER_EQUILIBRIA"
            and receipt["sources_unchanged_before_and_after"] is True
            and receipt["global_frame_feedback"] is False
            and receipt["output_sha256"]["report.json"] == COMMON_REPORT_SHA,
            "accepted common-knee receipt differs")
    report = read(directory / "report.json")
    contract = read(directory / "input-contract.json")["contract"]
    descriptors = report["states"]
    require(report["status"] == receipt["status"] and len(descriptors) == 12
            and {(row["side"], row["case_id"]) for row in descriptors}
                == {(side, case) for side in ("left", "right") for case in api.CASES},
            "common receiver state census differs")
    geometry = contract["geometry"]
    boundaries = {(row["case_id"], row["axis_id"]): row for row in contract["boundaries"]}
    require(len(geometry) == 4 and len(boundaries) == 24, "common geometry/boundary census differs")
    model = contract["model"]
    profile = model["end_profile"]
    radii = [profile["washer_ID_max_mm"] / 2, profile["washer_OD_min_mm"] / 2]
    require(close_vector(radii, [api.GENERIC_INNER_MM, api.GENERIC_OUTER_MM], 1e-9)
            and profile["hypothetical_concentric_head_and_nut_flat_radius_mm"] == 5.0,
            "common washer profile differs from the saved quarter-inch family")
    tolerances = model["numerical_tolerances"]
    ftol, mtol = float(tolerances["force_n"]), float(tolerances["moment_nmm"])
    joined = []
    for descriptor in descriptors:
        name = descriptor["path"]
        require(Path(name).name == name and receipt["output_sha256"].get(name) == descriptor["sha256"],
                "common state descriptor is not receipt bound")
        state = read(directory / name)
        require(state["case_id"] == descriptor["case_id"] and state["side"] == descriptor["side"]
                and state["status"] == "CONDITIONAL_COMMON_RECEIVER_EQUILIBRIUM"
                and state["combined_full_wrenches_closed"] is True and len(state["shafts"]) == 2,
                "common state is not an accepted two-shaft receiver equilibrium")
        for shaft in state["shafts"]:
            axis_id = shaft["axis_id"]
            geom = geometry[axis_id]
            boundary = boundaries[(state["case_id"], axis_id)]
            require(axis_id.startswith("knee_outer_" + state["side"] + "_")
                    and boundary["gap_scale"] == 1.0
                    and boundary["fresh_source_comparison_sha256"] == api.PINS[api.FRAME]
                    and boundary["fresh_source_response_sha256"] == api.PINS[api.RESPONSE],
                    "common end belongs to another shaft or simultaneous frame response")
            tension = float(shaft["redistributed_tension_n"])
            require(tension >= 0 and math.isclose(tension, shaft["normal_transfer"]["single_physical_tie_n"],
                                                 rel_tol=0, abs_tol=ftol),
                    "common redistributed force differs from its single physical tie")
            axis, common_datum = vector(geom["bolt_axis_xyz"], 3), vector(geom["datum_mm"], 3)
            trans = [vector(v, 3) for v in boundary["transverse_basis_xyz"]]
            require(len(trans) == 2 and math.isclose(math.hypot(*axis), 1, abs_tol=1e-8)
                    and all(math.isclose(math.hypot(*v), 1, abs_tol=1e-8)
                            and abs(api.dot(v, axis)) <= 1e-8 for v in trans)
                    and abs(api.dot(*trans)) <= 1e-8, "common physical basis differs")
            ends = shaft["outer_seat_fields"]
            require(len(ends) == 2 and {end["end"] for end in ends} == {"head", "nut"},
                    "common shaft must have exactly two outer washer ends")
            for end in ends:
                role, receiver = end["end"], end["receiver"]
                require(receiver == geom["receiver_order"][0 if role == "head" else -1],
                        "middle receiver was assigned an outer washer")
                key = (state["case_id"], axis_id, role, receiver)
                require(key in baseline, "common outer end missing from original N09")
                old, saved = baseline[key], support[(axis_id, receiver)]
                require(math.isclose(float(old["fresh_signed_T_n"]), shaft["source_tension_n"],
                                     rel_tol=0, abs_tol=ftol)
                        and saved["modeled_support_applicability"] is old["modeled_support_applicability"],
                        "common source tie or original land binding differs")
                seat = vector(geom[role + "_seat_point_mm"], 3)
                inward = [(1 if role == "head" else -1) * x for x in axis]
                wood = end["point_tractions"]["wood_contact"]
                hardware = end["point_tractions"]["head_contact"]
                require(wood["on"] == "receiver" and hardware["on"] == "bolt",
                        "common pressure traction signs differ")
                force, moment = recover_traction(api, wood, seat, common_datum, ftol, mtol)
                hforce, hmoment = recover_traction(api, hardware, seat, common_datum, ftol, mtol)
                magnitude = math.hypot(*moment)
                series = end["series_contact"]
                require(close_vector(force, [tension * n for n in inward], ftol)
                        and close_vector([a + b for a, b in zip(force, hforce, strict=True)], [0.] * 3, ftol)
                        and close_vector([a + b for a, b in zip(moment, hmoment, strict=True)], [0.] * 3, mtol)
                        and abs(api.dot(moment, axis)) <= mtol
                        and math.isclose(magnitude, series["moment_nmm"], rel_tol=1e-8, abs_tol=mtol),
                        "common own-seat force or moment recovery does not balance")
                pair = [api.dot(v, moment) for v in trans]
                require(math.isclose(math.hypot(*pair), magnitude, rel_tol=1e-8, abs_tol=mtol),
                        "common signed transverse moment loses a component")
                area, wood_ref = float(old["ideal_annulus_area_mm2"]), old["wood_reference_mpa"]
                app_area = old["applicable_supported_area_mm2"]
                mean = tension / area
                supported_mean = tension / float(app_area) if app_area else None
                seat_match = (close_vector(seat, saved["seat_point_xyz_mm"], 1e-7)
                              if saved["seat_point_xyz_mm"] is not None else None)
                full_support = (saved["modeled_support_applicability"] is True
                                and float(saved["saved_support_fraction"] or 0) >= 1 - 1e-6
                                and math.isclose(area, math.pi * (radii[1] ** 2 - radii[0] ** 2), abs_tol=1e-6))
                wc = series["wood_contact"]
                pressure_peak = (float(model["wood_bore_and_seat_stiffness_mpa_per_mm"]) * max(
                    float(wc["closure_mm"]) + abs(float(wc["tilt_rad"])) * radii[1], 0.)
                    if tension > 0 else 0.)
                row = {**old, "scope": "common_knee_outer_end_TM_source", "join_key": list(key),
                       "historical_isolated_end": {k: old[k] for k in (
                           "fresh_signed_T_n", "own_end_M_magnitude_nmm", "own_end_M_signed_xyz_nmm",
                           "fresh_force_source", "fresh_force_source_sha256", "fresh_source_row_id")},
                       "global_frame_source_T_n": shaft["source_tension_n"],
                       "fresh_signed_T_n": tension, "fresh_force_source": api.display(directory / name),
                       "fresh_force_source_sha256": descriptor["sha256"],
                       "fresh_source_row_id": state["case_id"] + "/" + axis_id + "/redistributed_tension_n",
                       "source_status": "COMPLETE_COMMON_KNEE_END_SOURCE", "source_null_reason": None,
                       "normal_into_receiver_xyz": inward, "force_on_receiver_xyz_n": force,
                       "end_wrench_datum_global_xyz_mm": seat,
                       "common_shaft_datum_xyz_mm": common_datum,
                       "own_end_M_magnitude_nmm": magnitude, "own_end_M_signed_xyz_nmm": moment,
                       "own_end_M_signed_transverse_pair_nmm": pair,
                       "physical_transverse_basis_rows_xyz": trans,
                       "local_end_moment_status": "COMMON_POSE_SIGNED_OWN_WOOD_TRACTION_RECOVERY",
                       "own_end_eccentricity_mm": magnitude / tension if tension > 0 else None,
                       "ideal_annulus_mean_pressure_mpa": mean,
                       "ideal_mean_over_wood_reference": mean / wood_ref if wood_ref else None,
                       "supported_mean_pressure_mpa": supported_mean,
                       "supported_mean_over_wood_reference": supported_mean / wood_ref
                           if supported_mean is not None and wood_ref else None,
                       "seat_datum_match": seat_match,
                       "contact_patch_geometry_status": "SAVED_NOMINAL_FULL_ANNULUS_MATCHES_MODEL"
                           if seat_match is True and full_support else "END_DATUM_OR_ANNULUS_SUPPORT_UNRESOLVED",
                       "rigid_model_continuous_wood_pressure_peak_mpa": pressure_peak,
                       "rigid_model_continuous_wood_peak_over_reference": pressure_peak / wood_ref
                           if seat_match is True and full_support and wood_ref else None,
                       "existing_metal_method_candidate": "original_quarter_inch_fine_plate_hypothesis_not_executed"
                           if seat_match is True and full_support else None,
                       "central_recovered_moment_static_trial": None,
                       "metal_simultaneous_TM_status": "COMMON_OWN_END_SOURCE_AVAILABLE_METAL_TRANSFER_PENDING",
                       "saved_rigid_wood_contact": wc,
                       "zero_T_contact_inactive_under_source_law": tension == 0,
                       "physical_head_to_nut_order_verified": geom["physical_head_to_nut_order_verified"],
                       "global_frame_feedback": False, "elastic_timber_field_qualified": False, **FLAGS}
                joined.append(row)
    require(len(joined) == len(baseline) == 48 and {identity(row) for row in joined} == set(baseline),
            "new common ends must replace exactly 48 isolated N09 records")
    return sorted(joined, key=identity)


def land_queries(api, support, effective, axis_map, n09_directory):
    """List the exact unresolved joins; query only current physical land datums."""
    unresolved = {key: row for key, row in support.items()
                  if row["modeled_support_applicability"] is not True}
    require(len(unresolved) == 25, "original N09 unresolved physical land census differs")
    corner = read(api.CORNER)
    axis_indices = {row["axis_id"]: index for index, row in enumerate(read(api.REGISTER)["axes"])}
    central_index = next(index for index, row in enumerate(read(api.REMAINING_SUPPORT)["seats"])
                         if row["axis_id"] == "center_principal_right_2" and row["role"] == "nut")
    current_seats = {}
    physical_roles = {"host_head": ("head", "host"), "host_nut": ("nut", "host"),
                      "cleat_head": ("head", "cleat"), "cleat_nut": ("nut", "cleat")}
    for state_index, state in enumerate(corner["states"]):
        for host, packet_host in state["hosts"].items():
            bolts = {bolt["axis_id"]: bolt for bolt in packet_host["state"]["bolts"]}
            for seat_index, seat in enumerate(packet_host["wood_seat_recovery"]):
                require(seat["end"] in physical_roles, "unknown saved corner physical end label")
                role, owner = physical_roles[seat["end"]]
                axis_id = seat["axis_id"]
                tie = axis_map[axis_id]["outer_tie"]
                receiver = host if owner == "host" else state["cleat"]
                bolt = bolts[axis_id]
                physical_axis = bolt.get("actual_axis_head_to_nut_xyz", bolt.get("bolt_axis_head_to_nut_xyz"))
                require(receiver == tie["first_body" if role == "head" else "second_body"]
                        and close_vector(vector(physical_axis, 3), vector(tie["direction_global_xyz"], 3), 1e-8),
                        "saved corner end owner or physical head-to-nut axis differs from register")
                key = (axis_id, receiver)
                entry = {"role": role, "point": seat["nominal_outer_wood_seat_xyz_mm"],
                         "source": api.display(api.CORNER), "source_sha256": api.PINS[api.CORNER],
                         "pointer": f"/states/{state_index}/hosts/{host}/wood_seat_recovery/{seat_index}"}
                if key in current_seats:
                    require(current_seats[key]["role"] == role
                            and close_vector(current_seats[key]["point"], entry["point"], 1e-7),
                            "corner nominal land datum changes with load case")
                else:
                    current_seats[key] = entry
    retail_inventory = read(api.OLD_RETAIL)["nominal_support_inventory"]
    original_result = read(n09_directory / "washer-reference-completion.json")
    require(original_result["support_join"]["unknown_or_not_applicable_seat_rows"] == 25,
            "original washer worksheet unknown land count differs")
    existing_rows = csv_rows(n09_directory / "washer-reference-states.csv")
    retail_rows = { (r["axis_id"], r["receiver_member"]): r for r in existing_rows
                   if r["scope"] == "fresh_top_retail_plate_contact" and r["end_role"] == "cleat" }
    requests, central, reuse = [], [], []
    for key, saved in sorted(unresolved.items()):
        axis_id, member = key
        role = saved["role"]
        tie = axis_map[axis_id]["outer_tie"]
        require(member == tie["first_body" if role == "head" else "second_body"],
                "unresolved support end differs from registered physical receiver")
        current_step = effective[member]
        if key in current_seats:
            nominal = current_seats[key]
            require(nominal["role"] == role, "current corner physical role differs from original land obligation")
        else:
            require(role == "head" or axis_id == "center_principal_right_2",
                    "noncorner unresolved datum lacks a registered head source")
            nominal = {"role": role, "point": tie["point_mm"], "source": api.display(api.REGISTER),
                       "source_sha256": api.PINS[api.REGISTER],
                       "pointer": f"/axes/{axis_indices[axis_id]}/outer_tie/point_mm"}
            # The sole central nut reuses its actual saved face point, not the head tie point.
            if axis_id == "center_principal_right_2":
                nominal = {"role": role, "point": saved["seat_point_xyz_mm"],
                           "source": saved["source"], "source_sha256": saved["source_sha256"],
                           "pointer": f"/seats/{central_index}/point_xyz_mm"}
            else:
                require(close_vector(nominal["point"], saved["seat_point_xyz_mm"], 1e-7),
                        "service head land differs from registered current head datum")
        inward = [(1 if role == "head" else -1) * x for x in vector(tie["direction_global_xyz"], 3)]
        require(math.isclose(math.hypot(*inward), 1, abs_tol=1e-8), "land normal is not unit length")
        entry = {"physical_land_key": [axis_id, role, member],
                 "original_N09_applicability": saved["modeled_support_applicability"],
                 "original_N09_basis": saved["support_applicability_basis"],
                 "original_support_source": saved["source"],
                 "original_support_source_sha256": saved["source_sha256"],
                 "old_saved_step": {"path": saved["support_step_path"], "sha256": saved["support_step_sha256"]},
                 "effective_step": current_step,
                 "old_saved_seat_point_xyz_mm": saved["seat_point_xyz_mm"],
                 "current_nominal_seat_point_xyz_mm": nominal["point"],
                 "current_nominal_datum_binding": {k: nominal[k] for k in ("source", "source_sha256", "pointer")},
                 "current_inward_normal_xyz": inward,
                 "inward_normal_source": api.display(api.REGISTER),
                 "inward_normal_source_sha256": api.PINS[api.REGISTER],
                 "annulus_inner_outer_radii_mm": [api.GENERIC_INNER_MM, api.GENERIC_OUTER_MM],
                 "depths_mm": [0.01, 0.05, 0.1], "loaded_shift_or_tilt_qualified": False,
                 "physical_geometry_inspected": False}
        if axis_id == "center_principal_right_2":
            require(saved["modeled_support_applicability"] is False
                    and role == "nut" and saved["support_step_path"] == current_step["path"]
                    and saved["support_step_sha256"] == current_step["sha256"],
                    "central failure is not the unchanged saved full-annulus failure")
            entry.update({"disposition": "REUSE_KNOWN_PARTIAL_FULL_RING_FAILURE",
                          "saved_support_fraction": saved["saved_support_fraction"],
                          "saved_supported_area_mm2": saved["saved_supported_area_mm2"],
                          "alternative_supported_ring_contract": api.display(api.CENTRAL),
                          "alternative_supported_ring_contract_sha256": api.PINS[api.CENTRAL],
                          "intersection_requests": []})
            central.append(entry)
        elif axis_id.startswith("top_outer/") and "/rail_" in axis_id and role == "nut":
            prior = retail_inventory[axis_id + "/cleat"]
            actual = retail_rows[key]
            require(actual["modeled_support_applicability"] is True
                    and actual["support_step_path"] == current_step["path"]
                    and actual["support_step_sha256"] == current_step["sha256"]
                    and close_vector(prior["seat_xyz_mm"], nominal["point"], 0.002),
                    "current rail nut is not bound to corrected retail nominal support")
            displacement = math.dist(prior["seat_xyz_mm"], nominal["point"])
            require(prior["own_saved_bore_radius_mm"] + displacement < api.GENERIC_INNER_MM
                    and prior["minimum_outer_disk_edge_margin_mm"] > displacement
                    and prior["minimum_other_bore_clearance_mm"] > displacement,
                    "retail clearances do not cover the current concentric minimum annulus")
            entry.update({"disposition": "REUSE_CORRECTED_RETAIL_CURRENT_LAND",
                          "old_saved_datum_replaced_not_certified": True,
                          "retail_support_source": api.display(api.OLD_RETAIL),
                          "retail_support_source_sha256": api.PINS[api.OLD_RETAIL],
                          "retail_support_pointer": "/nominal_support_inventory/"
                              + (axis_id + "/cleat").replace("~", "~0").replace("/", "~1"),
                          "corrected_section_source": api.display(api.CORNER_TIMBER),
                          "corrected_section_source_sha256": api.PINS[api.CORNER_TIMBER],
                          "saved_current_seat_displacement_mm": displacement,
                          "retail_supported_annulus_radii_mm": [api.RAIL_FAMILY["inner_radius_mm"],
                                                                 api.RAIL_FAMILY["outer_radius_mm"]],
                          "retail_full_annulus_area_mm2": prior["nominal_supported_annulus_area_mm2"],
                          "intersection_requests": []})
            reuse.append(entry)
        else:
            probes = [{"offset_from_seat_mm": sign * depth,
                       "direction": "inward" if sign == 1 else "outward"}
                      for sign in (1, -1) for depth in entry["depths_mm"]]
            entry.update({"disposition": "PARENT_CURRENT_STEP_ANNULUS_QUERY_REQUIRED",
                          "intersection_requests": probes,
                          "expected_observation": "Record annulus/STEP intersection area and fraction at each signed offset; retain outward observations separately from inward support."})
            requests.append(entry)
    require(len(requests) == 20 and len(central) == 1 and len(reuse) == 4,
            "minimal land obligation partition differs from 20 new, 1 known, 4 reused")
    return {"schema": "washer_land_query_plan/v1", "status": "PREPARED_NO_GEOMETRY_QUERIES_RUN",
            "counts": {"original_unproved_or_inapplicable_physical_lands": 25,
                       "known_central_full_ring_failures_reused": 1,
                       "corrected_retail_current_lands_reused": 4,
                       "new_physical_land_queries": 20,
                       "new_annulus_intersection_requests": 120,
                       "inward_intersection_requests": 60, "outward_intersection_requests": 60},
            "new_land_queries": requests, "known_partial_land": central,
            "reused_corrected_retail_lands": reuse,
            "original_aggregate_applicability_rewritten": False, "geometry_queries_run": 0, **FLAGS}


def build(output, *, n10_directory=None, n10_receipt_sha256=None):
    """Parent-owned saved arithmetic; optional full N10 sources can arrive later."""
    output = Path(output).absolute()
    require(output.resolve() == output and output.parent == RAW and not output.exists(),
            "use a fresh unaliased immediate child of rawlocal/washer-end-source-completion")
    api = load_n09()
    pins = {**api.PINS, N09: N09_SHA, Path(__file__).resolve(): sha(__file__)}
    n09_directory, n09_receipt = packet(pins, N09_DIRECTORY, N09_RECEIPT_SHA,
                                       "washer-reference-completion", "washer_reference_completion_receipt/v1")
    require(n09_receipt["output_sha256"]["producer.py.snapshot"] == N09_SHA
            and n09_receipt["source_pins_unchanged"] is True, "corrected N09 frozen run is missing")
    common_directory, common_receipt = packet(pins, COMMON_DIRECTORY, COMMON_RECEIPT_SHA,
                                             "knee-common-shafts", "knee_common_shafts_receipt/v1")
    require((n10_directory is None) == (n10_receipt_sha256 is None),
            "supply both optional N10 directory and receipt hash, or neither")
    n10_receipt = None
    if n10_directory is not None:
        n10_directory, n10_receipt = packet(pins, n10_directory, n10_receipt_sha256,
                                           "bolt-reference-completion", "bolt_reference_completion_receipt/v2")
        require(n10_receipt["mode"] == "full"
                and n10_receipt["sources_authenticated_before_and_after"] is True,
                "full N10 frozen run is missing")
    rows = csv_rows(n09_directory / "washer-reference-states.csv")
    require(len(rows) == 1104 and len({identity(row) for row in rows}) == 1104,
            "original N09 physical end census differs")
    baseline = {identity(row): row for row in rows if row["scope"] == "outside_corner_axial_reference"}
    require(len(baseline) == 1008, "ordinary N09 census differs")
    keyed = None
    if n10_directory is not None:
        ends = [json.loads(line) for line in (n10_directory / "washer-ends.jsonl").read_text().splitlines()]
        keyed = {identity(row): row for row in ends}
        require(len(ends) == len(keyed) == 1008 and set(baseline) == set(keyed)
                and len({key[1] for key in keyed}) == 84 and {key[0] for key in keyed} == set(api.CASES),
                "N10 must join exactly the 1008 ordinary N09 end states")
    *_prior, axis_map = api.geometry_and_fresh_inputs(pins)
    support, effective, *_context = api.normalized_supports(pins, axis_map)
    retained = read(api.RETAINED_SUPPORT)
    for seat in retained["seats"]:
        saved = support[(seat["axis_id"], seat["member"])]
        saved["seat_point_xyz_mm"] = seat["source_interval_face_binding"]["face_center_global_xyz_mm"]
        annulus = seat["nominal_concentric_annulus_mm"]
        saved["annulus_inner_outer_radii_mm"] = [annulus["maximum_id"] / 2, annulus["minimum_od"] / 2]
    contract = read(api.CENTRAL)
    authenticate(pins)
    before = {api.display(path): sha(path) for path in sorted(pins)}
    if keyed is not None:
        ordinary = [join_row(api, baseline[key], keyed[key], support[(key[1], key[3])], contract)
                    for key in sorted(keyed)]
    else:
        ordinary = [{**baseline[key], "join_key": list(key), "source_status": "N10_PACKET_PENDING",
                     "source_null_reason": "No full N10 endpoint packet supplied.",
                     "own_end_eccentricity_mm": None, "existing_metal_method_candidate": None,
                     "central_recovered_moment_static_trial": None,
                     "rigid_model_continuous_wood_peak_over_reference": None, **FLAGS}
                    for key in sorted(baseline)]
    isolated = {identity(row): row for row in rows if row["scope"] == "continuous_shaft_outer_end_TM_source"}
    common = common_rows(api, isolated, support, common_directory, common_receipt)
    land_plan = land_queries(api, support, effective, axis_map, n09_directory)
    joined = ordinary + common
    finite = [row for row in joined if row["own_end_M_magnitude_nmm"] is not None]
    candidates = [row for row in joined if row["existing_metal_method_candidate"] == "original_quarter_inch_fine_plate_hypothesis_not_executed"]
    trials = [row for row in joined if row["central_recovered_moment_static_trial"] is not None]
    witnesses = {}
    for column in ("fresh_signed_T_n", "own_end_M_magnitude_nmm", "own_end_eccentricity_mm",
                   "rigid_model_continuous_wood_peak_over_reference"):
        available = [row for row in joined if row[column] is not None]
        witness = max(available, key=lambda row: row[column]) if available else None
        witnesses[column] = None if witness is None else {
            "join_key": witness["join_key"], "value": witness[column],
            "same_state_T_n": witness["fresh_signed_T_n"], "same_state_M_nmm": witness["own_end_M_magnitude_nmm"]}
    authenticate(pins)
    after = {api.display(path): sha(path) for path in sorted(pins)}
    require(before == after, "source bytes changed during own-end transfer arithmetic")
    result = {"schema": "washer_end_source_completion/v1", "status": "FINITE_PARTIAL_END_SOURCE_COMPLETION",
              "counts": {"required_ordinary_end_states": 1008, "current_outside_corner_end_states": len(joined),
                         "n10_ordinary_end_states_consumed": len(ordinary) if keyed is not None else 0,
                         "common_knee_end_states_replacing_isolated": len(common),
                         "original_retail_plate_states_reused_unchanged": 48,
                         "finite_own_end_sources": len(finite), "null_own_end_sources": len(joined) - len(finite),
                         "existing_quarter_plate_method_candidates": len(candidates),
                         "central_recovered_moment_trials": len(trials), "new_plate_or_shaft_solves": 0,
                         **land_plan["counts"]},
              "same_state_peak_witnesses": witnesses,
              "central_recovered_moment_trials": [{"join_key": row["join_key"], **row["central_recovered_moment_static_trial"]} for row in trials],
              "null_end_sources": [{"join_key": row["join_key"], "reason": row["source_null_reason"]} for row in joined if row["own_end_M_magnitude_nmm"] is None],
              "original_n09_receipt_sha256": N09_RECEIPT_SHA,
              "common_knee_receipt_sha256": COMMON_RECEIPT_SHA,
              "n10_receipt_sha256": n10_receipt_sha256,
              "sources_authenticated_before_and_after": True, "source_sha256": before,
              "limits": [
                  "Ordinary ends are isolated first-order N10 hypotheses when supplied; pending sources remain null.",
                  "Common knee ends use the accepted shared receiver poses and redistributed tie forces, without global frame feedback, a passive internal-V law, or qualified elastic timber.",
                  "Nominal support applies only at the pinned seat; loaded shift, tilt and actual contact are unqualified.",
                  "Continuous pressure maxima evaluate the saved rigid annulus law, not actual washer flexure.",
                  "Quarter-inch plate candidates reuse the old 1.2954-mm method geometry; no plate calculation ran here.",
                  "Central compression-only trial assumes identical admissible pressure on the two supported ring faces and ductile metal; yield remains a required hypothetical floor, not actual first yield or capacity.",
                  "Retained larger washers have no matching existing fine plate family in this consumer.",
                  "Original retail plate results are reused unchanged; the other top/bottom corner ends and internal ties retain separate packets.",
                  "Land queries are requests only. No STEP intersection or loaded-seat support qualification runs here.",
                  "All formal criteria, proposal status and release HOLD boundaries remain unchanged."], **FLAGS}
    output.mkdir(parents=True)
    files = {".gitignore": "*\n", "producer.py.snapshot": Path(__file__).read_text(),
             "washer-end-source-completion.json": json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
             "land-query-plan.json": json.dumps(land_plan, indent=2, sort_keys=True, allow_nan=False) + "\n",
             "washer-end-states.jsonl": "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in joined)}
    for name, payload in files.items():
        with (output / name).open("x") as stream:
            stream.write(payload)
    receipt = {"schema": "washer_end_source_completion_receipt/v1", "source_sha256": before,
               "source_before_sha256": before, "source_after_sha256": after,
               "sources_authenticated_before_and_after": True,
               "output_sha256": {name: sha(output / name) for name in files},
               "counts": result["counts"], **FLAGS}
    with (output / "receipt.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n10-directory", type=Path)
    parser.add_argument("--n10-receipt-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, n10_directory=args.n10_directory,
                           n10_receipt_sha256=args.n10_receipt_sha256), indent=2, allow_nan=False))
