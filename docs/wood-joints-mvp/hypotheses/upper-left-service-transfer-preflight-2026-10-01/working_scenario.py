#!/usr/bin/env python3
"""A small, explicitly assumed rigid-cleat / elastic-spring working scenario."""

import importlib.util
import itertools
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("signed_preflight", HERE / "produce.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
INPUT_SHA = "012fa95ef87113745c1cb60a0ed7e683f5216e7378afbfa19d4e7b1b811e62c4"
LOAD_MULTIPLIER = 2.0
WOOD_E_MPA = 300.0
STEEL_E_MPA = 200000.0
PSI_MPA = 0.006894757293168
DIAMETER_MM = 6.35
ROOT_MM = 0.189 * 25.4
WASHER_AREA_MM2 = math.pi * (18.4658**2 - 8.3058**2) / 4
EFFECTIVE_AREA_FRACTION = 0.25
HOLE_DIAMETER_MM = 7.5
# Two receiver bores each allow radial movement before bearing engages.
RELATIVE_CLEARANCE_MM = HOLE_DIAMETER_MM - DIAMETER_MM


def normal_response(bolts, patches, bolt_stiffness, patch_stiffness, demand):
    """Invert target traction on the cleat to cleat-relative-to-host motion.

    Demand is the desired interface restoring wrench, not an additional
    external load. Positive opening gives bolt tension acting toward the host;
    negative opening gives contact compression acting away from the host.
    """
    b = np.asarray(bolts + patches, dtype=float)
    stiffness = np.asarray([bolt_stiffness] * len(bolts) + patch_stiffness)
    count = len(bolts)
    for active in itertools.product((False, True), repeat=len(b)):
        active = np.asarray(active)
        matrix = b.T @ ((stiffness * active)[:, None] * b)
        if np.linalg.cond(matrix) > 1e12:
            continue
        motion = np.linalg.solve(matrix, -np.asarray(demand))
        opening = b @ motion
        should_be_active = np.r_[opening[:count] > 0, opening[count:] < 0]
        if any(a != s and abs(x) > 1e-7
               for a, s, x in zip(active, should_be_active, opening, strict=True)):
            continue
        tension = stiffness[:count] * np.maximum(opening[:count], 0)
        compression = stiffness[count:] * np.maximum(-opening[count:], 0)
        recovered = b.T @ np.r_[-tension, compression]
        p.require(np.max(np.abs(recovered - demand)) < 0.01, "Normal statics failed")
        return motion.tolist(), tension.tolist(), compression.tolist()
    raise ValueError("No compatible normal bolt/contact state found")


def shear_response(force_pair, force_transverse, torque, pitch, stiffness, clearance):
    """Invert interface traction to compatible cleat-relative-to-host motion."""
    transverse = [force_transverse / 2 - torque / pitch,
                  force_transverse / 2 + torque / pitch]

    def travel(a, b):
        force = math.hypot(a, b)
        if force < 1e-12:
            return [0.0, 0.0]
        factor = clearance / force + 1 / stiffness
        return [a * factor, b * factor]

    low, high = sorted((0.0, force_pair))
    for _ in range(40):
        first = (low + high) / 2
        difference = (travel(first, transverse[0])[0]
                      - travel(force_pair - first, transverse[1])[0])
        if difference > 0:
            high = first
        else:
            low = first
    first = (low + high) / 2
    forces = [[first, transverse[0]], [force_pair - first, transverse[1]]]
    # Allocated forces act on the cleat. Its motion relative to the receiver
    # opposes that restoring traction, as in normal_response.
    displacement = [[-x for x in travel(*v)] for v in forces]
    p.require(abs(displacement[0][0] - displacement[1][0]) < 1e-6,
              "Shear compatibility failed")
    motion = [(displacement[0][0] + displacement[1][0]) / 2,
              (displacement[0][1] + displacement[1][1]) / 2,
              (displacement[1][1] - displacement[0][1]) / pitch]
    return motion, forces


def produce():
    source = p.read_pinned(HERE / "transfer-preflight.json", INPUT_SHA)
    old = p.read_pinned(p.REPORT, p.REPORT_SHA)
    freeze = p.read_pinned(p.ROOT / p.FREEZE, p.FREEZE_SHA)
    responses = {case: p.read_pinned(p.ROOT / row["response"]["path"],
                                   row["response"]["sha256"])
                 for case, row in freeze["cases"].items()}
    root_area = math.pi * ROOT_MM**2 / 4
    root_section_modulus = math.pi * ROOT_MM**3 / 32
    lateral_budget = (old["assumed_local_contract"]["per_bolt_lateral_limit_n"]
                      / old["component_scenario"]
                      ["force_box_to_worst_direction_reference_budget_ratio"])
    rows = []
    for state in source["states"]:
        ports = responses[state["case"]]["increments"][state["increment_index"]]
        ports = ports["physical_connection_forces"]
        for receiver, frame in source["group_frames"].items():
            contact_names = ("contact_74_" if receiver == "base_rail_service_upper_left"
                             else "contact_92_")
            contacts = [ports[contact_names + str(i)] for i in range(4)]
            contact = contacts[0]
            c = [x * (1 if contact["first"] == p.BLOCK else -1)
                 for x in contact["scalar_normal"]]
            c = p.unit(c)
            pair = frame["basis_global_xyz"][0]
            transverse = p.unit(p.cross(c, pair))

            def normal_row(point, frame=frame, c=c, pair=pair, transverse=transverse):
                moment_arm = p.cross(p.sub(point, frame["datum_xyz_mm"]), c)
                return [1.0, p.dot(pair, moment_arm), p.dot(transverse, moment_arm)]

            grip = 127.0 if receiver == "base_rail_service_upper_left" else 177.8
            patch_areas = [r["source_area_mm2"] * EFFECTIVE_AREA_FRACTION for r in contacts]
            patch_stiffness = [WOOD_E_MPA * area / grip for area in patch_areas]
            seat_stiffness = (WOOD_E_MPA * WASHER_AREA_MM2
                              * EFFECTIVE_AREA_FRACTION / 18.4658)
            axial_stiffness = 1 / (grip / (STEEL_E_MPA * root_area) + 2 / seat_stiffness)
            action = state["receiver_actions_on_block"][receiver]
            force = [LOAD_MULTIPLIER * x for x in action["force_global_n"]]
            moment = [LOAD_MULTIPLIER * x for x in action["moment_at_pair_datum_global_nmm"]]
            normal_demand = [p.dot(c, force), p.dot(pair, moment), p.dot(transverse, moment)]
            normal_motion, tension, compression = normal_response(
                [normal_row(v) for v in frame["bolt_point_xyz_mm"]],
                [normal_row(r["point"]) for r in contacts],
                axial_stiffness, patch_stiffness, normal_demand)
            # Assumed lateral stiffness: symmetric infinite beam on a Winkler
            # foundation. Finite embedment and rotation effects remain sensitivities.
            rigidity = STEEL_E_MPA * math.pi * DIAMETER_MM**4 / 64
            beta = (WOOD_E_MPA / (4 * rigidity))**0.25
            lateral_stiffness = rigidity * beta**3
            shear_motion, shear = shear_response(
                p.dot(pair, force), p.dot(transverse, force), p.dot(c, moment),
                frame["pitch_mm"], lateral_stiffness, RELATIVE_CLEARANCE_MM)
            bolts = []
            for axis, axial, lateral in zip(frame["axis_ids"], tension, shear, strict=True):
                lateral_n = math.hypot(*lateral)
                # This is an explicit local bending scenario, not a proved bound
                # or the receiver-datum moment reassigned to a bolt.
                bending_moment = lateral_n * grip / 4
                stress = axial / root_area + bending_moment / root_section_modulus
                equivalent = math.sqrt(stress**2 + 3 * (4 * lateral_n / (3 * root_area))**2)
                # Radial strip demand index only: it does not qualify a washer's
                # actual plate/contact boundary or coupled head/nut transfer.
                washer_index = (6 * axial * ((18.4658 - 8.3058) / 2)
                                 / (math.pi * 8.3058 * (0.051 * 25.4)**2))
                bolts.append({"axis_id": axis, "tension_n": axial,
                              "lateral_components_in_face_n": lateral,
                              "lateral_n": lateral_n,
                              "bending_scenario_nmm": bending_moment,
                              "same_root_steel_scenario_vm_mpa": equivalent,
                              "steel_first_yield_scenario_ratio": equivalent / (92000 * PSI_MPA),
                              "lateral_reference_budget_ratio": lateral_n / lateral_budget,
                              "quarter_annulus_wood_pressure_mpa": axial / (WASHER_AREA_MM2 / 4),
                              "quarter_annulus_wood_ratio": axial / (WASHER_AREA_MM2 / 4) / (625 * PSI_MPA),
                              "washer_radial_strip_index_mpa": washer_index,
                              "washer_index_to_assumed_250mpa_ratio": washer_index / 250})
            # Three normal and three lateral motions form each interface's
            # local sensitivity. No inter-receiver frame compatibility is solved.
            translation = math.hypot(normal_motion[0], *shear_motion[:2])
            rotation = math.degrees(math.hypot(*normal_motion[1:], shear_motion[2]))
            rows.append({"case": state["case"], "increment_index": state["increment_index"],
                         "source_load_factor": state["load_factor"], "receiver": receiver,
                         "normal_motion_mm_rad_rad": normal_motion,
                         "shear_motion_mm_mm_rad": shear_motion,
                         "relative_translation_at_pair_datum_mm": translation,
                         "relative_rotation_degrees": rotation, "bolts": bolts,
                         "face_patch_compression_n": compression,
                         "face_patch_average_pressure_mpa": [load / area for load, area
                                                              in zip(compression, patch_areas, strict=True)]})
    bolts = [bolt for row in rows for bolt in row["bolts"]]
    maxima = {key: max(b[key] for b in bolts) for key in (
        "tension_n", "lateral_n", "bending_scenario_nmm", "same_root_steel_scenario_vm_mpa",
        "steel_first_yield_scenario_ratio", "lateral_reference_budget_ratio",
        "quarter_annulus_wood_ratio", "washer_radial_strip_index_mpa",
        "washer_index_to_assumed_250mpa_ratio")}
    maxima.update({"relative_translation_mm": max(r["relative_translation_at_pair_datum_mm"] for r in rows),
                   "relative_rotation_degrees": max(r["relative_rotation_degrees"] for r in rows),
                   "face_patch_pressure_mpa": max(max(r["face_patch_average_pressure_mpa"]) for r in rows)})
    return {"schema": "upper-left-service-simple-working-scenario/v1",
            "status": "WORKING_SCENARIO_MVP_COMPLETE_JOINT_AUTHORITY_HOLD",
            "candidate": source["candidate"], "geometry_revision_id": source["geometry_revision_id"],
            "block": p.BLOCK, "input_sha256": INPUT_SHA, "producer_sha256": p.digest(Path(__file__)),
            "motion_convention": "Cleat relative to receiver; reported interface forces act on cleat and oppose relative motion.",
            "assumptions": {"load_multiplier": LOAD_MULTIPLIER, "cleat_and_receivers_rigid": True,
                            "interface_models_solved_independently": True,
                            "body_load_effects_through_source_reactions": True,
                            "wood_effective_modulus_mpa": WOOD_E_MPA,
                            "steel_modulus_mpa": STEEL_E_MPA, "bolt_diameter_mm": DIAMETER_MM,
                            "relative_bore_clearance_mm": RELATIVE_CLEARANCE_MM,
                            "effective_face_and_seat_area_fraction": EFFECTIVE_AREA_FRACTION,
                            "zero_initial_face_gap": True, "zero_initial_axial_slack": True,
                            "friction_credit": False, "preload_credit": False,
                            "washer_yield_sensitivity_mpa": 250,
                            "bolt_bending_scenario": "V times wood grip / 4; not a proved upper bound",
                            "assembly": "Bench assembly; metal-thread removal; supported partial frame disassembly for service. Tools and scene assumed available, not qualified."},
            "maxima": maxima, "receiver_states": rows,
            "working_scenario_mvp_complete": True, "complete_joint_accepted": False,
            "local_joint_mvp_complete": False, "frame_compatibility_established": False,
            "six_case_envelope_established": False, "geometry_changed": False,
            "native_solve_executed": False, "fabrication_released": False,
            "drilling_released": False, "structural_released": False, "climbing_released": False,
            "remaining_joint_gates": old["remaining_joint_gates"],
            "limits": "Compatible reduced bolt/contact spring scenario and component sensitivities. "
                      "Finite cleat deformation, physical bolt/washer/head/nut contact, local bolt bending, "
                      "finished-section traction and splitting, complete frame compatibility, missing cases "
                      "and actual assembly access remain unqualified. Rounded presentation does not change "
                      "source authentication or the full 47-criterion authority."}


if __name__ == "__main__":
    print(json.dumps(produce(), indent=2, sort_keys=True))
