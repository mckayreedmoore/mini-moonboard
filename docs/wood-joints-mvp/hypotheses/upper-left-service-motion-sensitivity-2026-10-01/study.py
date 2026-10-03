#!/usr/bin/env python3
"""Finite clearance/stiffness study; preserve the original working packet."""

import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path

from normal_model import normal_response

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.with_name("upper-left-service-transfer-preflight-2026-10-01")
PREVIOUS_CODE_SHA = "43e77e0fef513afd0749b00f75b520ae6c6bac6c4154a07fc8c4db56e028973d"
PREVIOUS_REPORT_SHA = "eb4aa47b41c78d591723146e3f6d1621ec0f9fc9058d349bafaa63d25c832c18"
HELPER_SHA = "36c06f9fbce6f3ab51dc7e0a45832899126d84db42deea34fa37c4613b9e1aec"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for filename, expected in (("working_scenario.py", PREVIOUS_CODE_SHA), ("produce.py", HELPER_SHA)):
    if digest(PREVIOUS / filename) != expected:
        raise ValueError(f"Previous source changed: {filename}")
spec = importlib.util.spec_from_file_location("previous_scenario", PREVIOUS / "working_scenario.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
p = previous.p


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def scaled(a, factor):
    return [x * factor for x in a]


def motion_at_point(translation, rotation, datum, point):
    """Small-motion displacement at a new point: u(x)=t+theta×(x-datum)."""
    return add(translation, p.cross(rotation, p.sub(point, datum)))


def global_motion(normal, shear, pair, transverse, compression_direction):
    translation = [normal[0] * compression_direction[i] + shear[0] * pair[i]
                   + shear[1] * transverse[i] for i in range(3)]
    rotation = [normal[1] * pair[i] + normal[2] * transverse[i]
                + shear[2] * compression_direction[i] for i in range(3)]
    return translation, rotation


def relative_host_motion(rail, side):
    """Rail relative to side, with both cleat/host motions at the same datum."""
    return p.sub(side[0], rail[0]), p.sub(side[1], rail[1])


def inputs():
    source = p.read_pinned(PREVIOUS / "transfer-preflight.json", previous.INPUT_SHA)
    original = p.read_pinned(PREVIOUS / "working-scenario.json", PREVIOUS_REPORT_SHA)
    old = p.read_pinned(p.REPORT, p.REPORT_SHA)
    freeze = p.read_pinned(p.ROOT / p.FREEZE, p.FREEZE_SHA)
    responses, source_gaps = {}, {}
    pins = {str(PREVIOUS / "transfer-preflight.json"): previous.INPUT_SHA,
            str(PREVIOUS / "working-scenario.json"): PREVIOUS_REPORT_SHA,
            str(PREVIOUS / "working_scenario.py"): PREVIOUS_CODE_SHA,
            str(PREVIOUS / "produce.py"): HELPER_SHA,
            str(p.REPORT): p.REPORT_SHA, p.FREEZE: p.FREEZE_SHA}
    for case, row in freeze["cases"].items():
        responses[case] = p.read_pinned(p.ROOT / row["response"]["path"], row["response"]["sha256"])
        model = p.read_pinned(p.ROOT / row["model"]["path"], row["model"]["sha256"])
        source_gaps[case] = model["connection_scenario"]["bolt_gap_factor"]
        for kind in ("response", "model"):
            pins[row[kind]["path"]] = row[kind]["sha256"]
    return source, original, old, responses, source_gaps, pins


def evaluate(clearance, wood_e, seat_factor, source, responses, lateral_budget):
    """Inverse interface sensitivities; no coupled frame equilibrium solve."""
    if clearance < 0 or wood_e <= 0 or seat_factor <= 0:
        raise ValueError("Invalid clearance or stiffness assumption")
    rows, combined = [], []
    root_area = math.pi * previous.ROOT_MM**2 / 4
    root_modulus = math.pi * previous.ROOT_MM**3 / 32
    for state in source["states"]:
        motions = {}
        for receiver, frame in source["group_frames"].items():
            prefix = "contact_74_" if receiver == "base_rail_service_upper_left" else "contact_92_"
            ports = responses[state["case"]]["increments"][state["increment_index"]]["physical_connection_forces"]
            contacts = [ports[prefix + str(i)] for i in range(4)]
            contact = contacts[0]
            c = p.unit(scaled(contact["scalar_normal"], 1 if contact["first"] == p.BLOCK else -1))
            pair = frame["basis_global_xyz"][0]
            transverse = p.unit(p.cross(c, pair))

            def normal_row(point, frame=frame, c=c, pair=pair, transverse=transverse):
                arm = p.cross(p.sub(point, frame["datum_xyz_mm"]), c)
                return [1, p.dot(pair, arm), p.dot(transverse, arm)]

            grip = 127.0 if receiver == "base_rail_service_upper_left" else 177.8
            areas = [r["source_area_mm2"] * previous.EFFECTIVE_AREA_FRACTION for r in contacts]
            seat_k = wood_e * previous.WASHER_AREA_MM2 * previous.EFFECTIVE_AREA_FRACTION / 18.4658 * seat_factor
            axial_k = 1 / (grip / (previous.STEEL_E_MPA * root_area) + 2 / seat_k)
            action = state["receiver_actions_on_block"][receiver]
            force = scaled(action["force_global_n"], previous.LOAD_MULTIPLIER)
            moment = scaled(action["moment_at_pair_datum_global_nmm"], previous.LOAD_MULTIPLIER)
            normal = normal_response([normal_row(x) for x in frame["bolt_point_xyz_mm"]],
                                     [normal_row(r["point"]) for r in contacts], axial_k,
                                     [wood_e * area / grip for area in areas],
                                     [p.dot(c, force), p.dot(pair, moment), p.dot(transverse, moment)])
            rigidity = previous.STEEL_E_MPA * math.pi * previous.DIAMETER_MM**4 / 64
            lateral_k = rigidity * (wood_e / (4 * rigidity))**0.75
            shear_motion, shear = previous.shear_response(
                p.dot(pair, force), p.dot(transverse, force), p.dot(c, moment),
                frame["pitch_mm"], lateral_k, clearance)
            translation, rotation = global_motion(normal["motion_mm_rad_rad"], shear_motion, pair, transverse, c)
            bolt_rows, point_forces = [], []
            for axis, tension, lateral, point in zip(frame["axis_ids"], normal["tension_n"],
                                                     shear, frame["bolt_point_xyz_mm"], strict=True):
                lateral_n = math.hypot(*lateral)
                stress = tension / root_area + lateral_n * grip / 4 / root_modulus
                vm = math.sqrt(stress**2 + 3 * (4 * lateral_n / (3 * root_area))**2)
                traction = [lateral[0] * pair[i] + lateral[1] * transverse[i] - tension * c[i]
                            for i in range(3)]
                point_forces.append((point, traction))
                u = motion_at_point(translation, rotation, frame["datum_xyz_mm"], point)
                radius = math.hypot(*lateral)
                inverse = [-x * (clearance / radius + 1 / lateral_k) if radius > 1e-12 else 0
                           for x in lateral]
                p.require(max(abs(p.dot(basis, u) - value) for basis, value
                              in zip((pair, transverse), inverse, strict=True)) < 1e-6,
                          "Returned rigid motion violates bolt shear compatibility")
                bolt_rows.append({"axis_id": axis, "tension_n": tension, "lateral_n": lateral_n,
                                  "lateral_components_n": lateral,
                                  "steel_bending_scenario_ratio": vm / (92000 * previous.PSI_MPA),
                                  "lateral_reference_budget_ratio": lateral_n / lateral_budget,
                                  "quarter_annulus_wood_ratio": tension / (previous.WASHER_AREA_MM2 / 4)
                                  / (625 * previous.PSI_MPA)})
            point_forces += [(r["point"], scaled(c, load))
                             for r, load in zip(contacts, normal["compression_n"], strict=True)]
            recovered_force = p.summed([f for _, f in point_forces])
            recovered_moment = p.summed([p.cross(p.sub(x, frame["datum_xyz_mm"]), f)
                                         for x, f in point_forces])
            p.close(recovered_force, force, 1e-5, "Six-component force reconstruction failed")
            p.close(recovered_moment, moment, 1e-3, "Six-component moment reconstruction failed")
            motions[receiver] = (motion_at_point(translation, rotation, frame["datum_xyz_mm"],
                                                state["common_block_datum_xyz_mm"]), rotation)
            rows.append({"case": state["case"], "increment_index": state["increment_index"],
                         "load_factor": state["load_factor"], "receiver": receiver,
                         "normal": normal, "shear_motion_mm_mm_rad": shear_motion,
                         "translation_at_pair_datum_global_mm": translation,
                         "rotation_global_rad": rotation,
                         "translation_mm": math.hypot(*translation),
                         "rotation_degrees": math.degrees(math.hypot(*rotation)),
                         "normal_tilt_degrees": math.degrees(math.hypot(*normal["motion_mm_rad_rad"][1:])),
                         "face_spin_degrees": math.degrees(abs(shear_motion[2])), "bolts": bolt_rows,
                         "six_component_reconstruction_residual": p.sub(recovered_force, force)
                         + p.sub(recovered_moment, moment)})
        rail_t, rail_r = motions["base_rail_service_upper_left"]
        side_t, side_r = motions["base_side_left"]
        # u_host = -u_cleat/host for a fixed cleat reference. Rail relative to
        # side is therefore u_cleat/side - u_cleat/rail at the SAME datum.
        relative_t, relative_r = relative_host_motion((rail_t, rail_r), (side_t, side_r))
        combined.append({"case": state["case"], "increment_index": state["increment_index"],
                         "load_factor": state["load_factor"],
                         "common_datum_xyz_mm": state["common_block_datum_xyz_mm"],
                         "rail_relative_to_side_translation_global_mm": relative_t,
                         "rail_relative_to_side_rotation_global_rad": relative_r,
                         "translation_mm": math.hypot(*relative_t),
                         "rotation_degrees": math.degrees(math.hypot(*relative_r))})
    bolts = [b for row in rows for b in row["bolts"]]
    maxima = {key: max(b[key] for b in bolts) for key in
              ("tension_n", "lateral_n", "steel_bending_scenario_ratio",
               "lateral_reference_budget_ratio", "quarter_annulus_wood_ratio")}
    maxima.update({key: max(r[key] for r in rows) for key in
                   ("translation_mm", "rotation_degrees", "normal_tilt_degrees", "face_spin_degrees")})
    maxima.update({"both_host_translation_mm": max(r["translation_mm"] for r in combined),
                   "both_host_rotation_degrees": max(r["rotation_degrees"] for r in combined)})
    return {"parameters": {"relative_clearance_mm": clearance, "effective_timber_modulus_mpa": wood_e,
                           "seat_stiffness_multiplier": seat_factor}, "maxima": maxima,
            "normal_motion_uniqueness_unestablished_states": sum(not r["normal"]["motion_uniqueness_established"]
                                                               for r in rows),
            "peak_both_host_translation_state": max(combined, key=lambda r: r["translation_mm"]),
            "peak_both_host_rotation_state": max(combined, key=lambda r: r["rotation_degrees"]),
            "receiver_states": rows, "both_host_states": combined}


def produce():
    source, original, old, responses, source_gaps, pins = inputs()
    lateral_budget = old["assumed_local_contract"]["per_bolt_lateral_limit_n"] / old["component_scenario"][
        "force_box_to_worst_direction_reference_budget_ratio"]
    scenarios = [evaluate(clearance, wood_e, seat_factor, source, responses, lateral_budget)
                 for clearance, wood_e, seat_factor in itertools.product((0.0, 0.5, 1.15),
                                                                         (150.0, 300.0, 600.0), (0.5, 1.0, 2.0))]
    baseline = next(r for r in scenarios if r["parameters"] == {
        "relative_clearance_mm": 1.15, "effective_timber_modulus_mpa": 300.0, "seat_stiffness_multiplier": 1.0})
    previous_rows = {(r["case"], r["increment_index"], r["receiver"]): r for r in original["receiver_states"]}
    deltas = []
    for r in baseline["receiver_states"]:
        before = previous_rows[r["case"], r["increment_index"], r["receiver"]]
        deltas.append({"case": r["case"], "increment_index": r["increment_index"], "receiver": r["receiver"],
                       "normal_motion_difference_mm_rad_rad": p.sub(r["normal"]["motion_mm_rad_rad"],
                                                                   before["normal_motion_mm_rad_rad"]),
                       "face_spin_difference_rad": r["shear_motion_mm_mm_rad"][2]
                       - before["shear_motion_mm_mm_rad"][2]})
    fixture_bolts = [[1, 0, -1], [1, 0, 1]]
    fixture_patches = [[1, -2, -2], [1, -2, 2], [1, 2, -2], [1, 2, 2]]
    fixture = normal_response(fixture_bolts, fixture_patches, 1, [1] * 4, [-20, 0, 0])
    prior_fixture = previous.normal_response(fixture_bolts, fixture_patches, 1, [1] * 4, [-20, 0, 0])
    return {"schema": "upper-left-service-motion-sensitivity/v1",
            "status": "FINITE_WORKING_SCENARIO_STUDY_JOINT_HOLD",
            "candidate": source["candidate"], "geometry_revision_id": source["geometry_revision_id"],
            "block": p.BLOCK, "source_pins": pins,
            "producer_sha256": digest(Path(__file__)), "normal_model_sha256": digest(HERE / "normal_model.py"),
            "load_multiplier": previous.LOAD_MULTIPLIER, "source_model_bolt_gap_factor_by_case": source_gaps,
            "source_cases": source["source_cases"], "missing_frame_cases": source["missing_frame_cases"],
            "counts": {"parameter_scenarios": len(scenarios), "same_state_source_pairs": len(source["states"]),
                       "receiver_states_evaluated": sum(len(s["receiver_states"]) for s in scenarios),
                       "both_host_states_evaluated": sum(len(s["both_host_states"]) for s in scenarios)},
            "abstract_pure_tension_known_answer": {"prior_motion_mm_rad_rad": prior_fixture[0],
                "corrected": fixture,
                "scope": "Abstract 1 N/mm spring fixture with 1/2 mm arms; demonstrates ambiguity, not physical cleat motions."},
            "parameter_status": {
                "clearance": "0 and 0.5 mm hypothetical; 1.15 mm from 7.5 minus 6.35 mm modeled bore/bolt, not observed fit.",
                "effective_timber_modulus": "150/300/600 MPa hypothetical effective face, seat and lateral-foundation stiffness; not measured DF-L moduli.",
                "seat_multiplier": "0.5/1/2 hypothetical uncertainty about E*A_eff/18.4658 mm, in addition to the timber-modulus factor."},
            "scenarios": scenarios, "baseline_motion_comparison": deltas,
            "complete_joint_accepted": False, "local_joint_mvp_complete": False,
            "frame_compatibility_established": False, "six_case_envelope_established": False,
            "geometry_changed": False, "native_solve_executed": False,
            "fabrication_released": False, "drilling_released": False,
            "structural_released": False, "climbing_released": False,
            "limits": "Inverse local interface sensitivities at simultaneous source states. Both-host motion is a common-datum kinematic combination, not coupled frame equilibrium. Small-motion estimates, rigid cleat/hosts, no friction/preload credit. Neutral normal poses explicitly representative. Prior material/bending sensitivities remain hypothetical, not qualified resistance. Full 47-criterion authority unchanged."}


if __name__ == "__main__":
    print(json.dumps(produce(), indent=2, sort_keys=True))
