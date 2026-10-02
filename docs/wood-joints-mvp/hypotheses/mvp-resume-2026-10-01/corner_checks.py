"""Finished wood and simultaneous bolt references for the corrected frame.

Use conditional Grade 5 tensile-yield input on all eight corner bolts.
Use the same-state response with both top-corner clearances included. Keep
reference calculations separate from formal qualification.
"""

import argparse
import copy
import fcntl
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
import top_corner_actions as accounting
import top_corner_correction as correction
import top_corner_local as local

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sha, read, require = accounting.sha, accounting.read, accounting.require


def lateral_reference(force, diameter, lengths, grains, fyb):
    d = diameter / 25.4
    angles = [correction.lateral.angle(force, g) for g in grains]
    parallel, perpendicular = 5600.0, 6100 * 0.5**1.45 / math.sqrt(d)
    bearing = [
        parallel
        * perpendicular
        / (
            parallel * math.sin(math.radians(a)) ** 2
            + perpendicular * math.cos(math.radians(a)) ** 2
        )
        for a in angles
    ]
    factor = 1 + 0.25 * max(angles) / 90
    result = correction.lateral.single_shear(
        main_length_in=lengths[0] / 25.4,
        side_length_in=lengths[1] / 25.4,
        main_bearing_lb_in=bearing[0] * d,
        side_bearing_lb_in=bearing[1] * d,
        main_yield_moment_lb_in=fyb * d**3 / 6,
        side_yield_moment_lb_in=fyb * d**3 / 6,
        gap_in=0,
        reduction_terms={
            key: value * factor
            for key, value in {
                "Im": 4.0,
                "Is": 4.0,
                "II": 3.6,
                "IIIm": 3.2,
                "IIIs": 3.2,
                "IV": 3.2,
            }.items()
        },
    )
    return {
        "reference_n": result["reference_lateral_lbf"] * correction.lateral.N_PER_LBF,
        "governing_mode": result["governing_mode"],
        "grain_angles_degrees": angles,
        "bearing_strengths_psi": bearing,
    }


def run(frame_dir, clearance_dir, output):
    frame_dir, clearance_dir, output = (
        path.resolve() for path in (frame_dir, clearance_dir, output)
    )
    operator = read(frame_dir / "operator-assessment.json")
    results = read(frame_dir / "frame-results.json")
    require(
        all(
            c["status"] == "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS"
            for c in results["cases"]
        ),
        "incomplete revised frame",
    )
    require(
        sha(frame_dir / "frame-response.npz") == results["response_sha256"],
        "changed revised response",
    )
    clearance = read(clearance_dir / "comparison.json")
    require(
        sha(clearance_dir / "response.npz") == clearance["response_sha256"],
        "changed clearance response",
    )
    selected = [s for s in clearance["states"] if s["gap_scale"] == 1.0]
    require(
        [s["case_id"] for s in selected] == [s["case_id"] for s in results["cases"]],
        "clearance case identity mismatch",
    )
    require(
        all(s["status"] == "PASS_CONDITIONAL_COUPLED_FRAME_LAWS" for s in selected),
        "incomplete coupled clearance frame",
    )
    for name, digest in clearance["source_sha256"].items():
        require(sha(ROOT / name) == digest, "changed clearance source: " + name)
    for name, digest in operator["output_sha256"].items():
        require(sha(frame_dir / name) == digest, "changed revised model artifact")
    output.mkdir(exist_ok=False)
    pins = {
        frame_dir / name: sha(frame_dir / name)
        for name in [
            "operator-assessment.json",
            "frame-results.json",
            "frame-response.npz",
            "operators.npz",
            "model.json",
            "row-identities.json",
        ]
    }
    pins.update({ROOT / p: h for p, h in operator["source_sha256"].items()})
    pins.update({ROOT / p: h for p, h in clearance["source_sha256"].items()})
    pins.update(local.PINS)
    for path in [
        clearance_dir / "comparison.json",
        clearance_dir / "response.npz",
        HERE / "top-corner-correction/proposal.json",
        HERE / "top-corner-hardware/hardware-inputs.json",
    ]:
        pins[path] = sha(path)
    for module in [accounting, correction, local, correction.lateral]:
        pins[Path(module.__file__)] = sha(Path(module.__file__))
    inputs = read(local.INPUTS)
    members = {
        r["member_id"]: copy.deepcopy(r["reduced_geometry_descriptor"])
        for r in inputs["members"]
    }
    bolts = {
        r["axis_id"]: copy.deepcopy(r)
        for r in inputs["connections"]
        if r["kind"] == "candidate_bolt"
    }
    proposal = read(HERE / "top-corner-correction/proposal.json")
    prepared = read(HERE / "top-corner-contact-geometry.json")
    pins[HERE / "top-corner-contact-geometry.json"] = sha(
        HERE / "top-corner-contact-geometry.json"
    )
    for prop in proposal["proposals"]:
        block = prop["block"]
        member = members[block]
        member["start"] = (np.array(member["start"]) - 25.4 * correction.T).tolist()
        member["end"] = (np.array(member["end"]) - 25.4 * correction.T).tolist()
        member["depth_mm"] = 139.7
        path = HERE / "top-corner-correction" / (block + ".step")
        member["step_path"], member["step_sha256"] = (
            str(path.relative_to(ROOT)),
            sha(path),
        )
        for axis in prop["axes"]:
            bolt = bolts[axis["axis_id"]]
            bolt["source_point_xyz_mm"] = axis["proposed_axis_point_mm"]
            for receiver in bolt["receiver_clearance_geometry"]:
                receiver["unique_bore_radius_mm"] = (
                    axis["proposed_CAD_bore_envelope_mm"] / 2
                )
                if receiver["receiver_id"] == block:
                    receiver["receiver_step_sha256"] = member["step_sha256"]
            if "/rail_" in axis["axis_id"]:
                interval = next(
                    i
                    for i in bolt["source_record"]["geometry"][
                        "wood_receiver_intervals"
                    ]
                    if i["receiver_id"] == block
                )
                old_lo = interval[
                    "current_shaft_intersection_solid_intervals_from_underhead_mm"
                ][0][0]
                interval[
                    "current_shaft_intersection_solid_intervals_from_underhead_mm"
                ] = [[old_lo, old_lo + 139.7]]
    groups = [
        g
        for g in read(accounting.GEOMETRY)["two_bolt_groups"]
        if g["block"] in accounting.BLOCK_HOSTS
    ]
    paths = [p for g in groups for p in local.tearout_geometry(g, bolts, members)]
    path_for = {(p["axis_id"], p["grain_direction_sign"]): p for p in paths}
    material = read(accounting.MATERIALS)["conditional_DF_L_No2_base_row"][
        "base_properties"
    ]
    fv, fc = (
        material["Fv_parallel"] * local.PSI_MPA,
        material["Fc_perpendicular"] * local.PSI_MPA,
    )
    cg_rail = local.group_factor(
        2,
        33 / 25.4,
        material["E"] * 88.9 * 139.7 / 25.4**2,
        material["E"] * 38.1 * (3 * 6.35) / 25.4**2,
    )
    cdelta_rail = 43.35 / (7 * 6.35)
    model_doc = read(frame_dir / "model.json")
    model = read(accounting.MODEL)
    model["nodes"] = model_doc["physical_node_coordinates_mm"]
    for block in accounting.BLOCK_HOSTS:
        model["body_geometry"][block]["geometry_record"].update(members[block])
    rows = read(frame_dir / "row-identities.json")
    names = model_doc["body_names"]
    # Native DOF order is retained by the corrected model's physical operators.
    from corner_frame import module

    sparse_parser = module(
        accounting.BASE
        / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "corner_check_labels",
    )
    labels = sparse_parser.parse_dof_file(
        accounting.BASE
        / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
    )
    old_contact = read(accounting.CONTACTS)
    patches = {
        c["name"]: {
            "area": c["area_mm2"],
            "vertices": old_contact["contact_patches"][c["source_patch_index"]][
                "vertices_xyz_mm"
            ],
        }
        for c in model["contact_cell_ownership"]
        if c["kind"] == accounting.CONTACT
    }
    for row in rows:
        if "contact_area_mm2" not in row:
            continue
        own = row["ownership"]
        cleat = next(c for c in prepared["cleats"] if c["block"] == own["second_body"])
        face = next(f for f in cleat["faces"] if f["host"] == own["first_body"])
        patches[row["row_id"]] = {
            "area": row["contact_area_mm2"],
            "vertices": face["corners_mm"],
        }
    # Sixteen modeled washer seats: exact supported annuli at both outer faces.
    seats = []
    shapes = {}
    for body in set(accounting.BLOCK_HOSTS) | {
        h for hosts in accounting.BLOCK_HOSTS.values() for h in hosts
    }:
        path = HERE / "top-corner-correction" / (body + ".step")
        if not path.exists():
            path = ROOT / members[body]["step_path"]
        pins[path] = sha(path)
        shapes[body] = cq.importers.importStep(str(path)).val()
    for cleat in prepared["cleats"]:
        for r in cleat["rows"]:
            if r["kind"] != "bolt_tension":
                continue
            side = "/side_" in r["axis_id"]
            # Exact minimum area / maximum envelope from catalog bounds.
            od_min, od_max, id_min, id_max, thickness = (
                (0.868, 0.905, 0.370, 0.390, 0.064)
                if side
                else (0.727, 0.749, 0.307, 0.327, 0.051)
            )
            nominal_axis = -np.array(r["direction_xyz"])
            for body, point, inward in zip(
                r["axial_law"]["endpoint_member_ids_head_to_nut"],
                r["axial_law"]["outer_seat_points_xyz_mm"],
                [nominal_axis, -nominal_axis],
                strict=True,
            ):
                ring = (
                    cq.Workplane(
                        cq.Plane(
                            origin=tuple(point),
                            xDir=tuple(correction.N),
                            normal=tuple(inward),
                        )
                    )
                    .circle(od_max * 25.4 / 2)
                    .circle(id_min * 25.4 / 2)
                    .extrude(0.05)
                    .val()
                )
                ratio = ring.intersect(shapes[body]).Volume() / ring.Volume()
                require(
                    abs(ratio - 1) < 1e-6,
                    "washer envelope lacks full modeled wood support",
                )
                seats.append(
                    {
                        "axis_id": r["axis_id"],
                        "body": body,
                        "seat_point_mm": point,
                        "maximum_envelope_supported_fraction": ratio,
                        "minimum_annulus_area_mm2": math.pi
                        / 4
                        * 25.4**2
                        * (od_min**2 - id_max**2),
                        "minimum_thickness_mm": thickness * 25.4,
                    }
                )
    seat_for = {r["axis_id"]: r for r in seats}
    states, balances, host_splitting, contacts = [], [], [], []
    with (
        np.load(frame_dir / "operators.npz", allow_pickle=False) as operators,
        np.load(clearance_dir / "response.npz", allow_pickle=False) as response,
    ):
        D, F = operators["D"], operators["F"]
        for i, result in enumerate(results["cases"]):
            case_id = result["case_id"]
            force = response[case_id + "_gap_raw_force_n"]
            maps = []
            for column in (2 * i, 2 * i + 1):
                mapping = {}
                for (node, dof), value in zip(labels, F[:, column], strict=True):
                    if value != 0:
                        mapping.setdefault(str(node), [0.0, 0.0, 0.0])[dof - 1] = float(
                            value
                        )
                maps.append(mapping)
            case = {
                "gravity_nodal_map": maps[0],
                "climber_nodal_map": maps[1],
                "dead_load_factor": results["dead_load_factor"],
            }
            actions_by_body = {}
            for body in shapes:
                actions, datum, geometry = accounting.physical_actions(
                    body, case, force, model, rows, D, names, patches
                )
                closure = accounting.wrench(actions, datum)
                require(
                    np.max(abs(closure[:3])) < 0.1 and np.max(abs(closure[3:])) < 2,
                    "revised whole-body action imbalance",
                )
                actions_by_body[body] = actions, datum, geometry
                balances.append(
                    {
                        "case_id": case_id,
                        "body": body,
                        "force_residual_n": closure[:3].tolist(),
                        "moment_residual_nmm": closure[3:].tolist(),
                    }
                )
            for group in groups:
                block, host = group["block"], group["host"]
                actions, datum, geometry = actions_by_body[block]
                target = [a for a in actions if a["other_body"] == host]
                side = host.startswith("base_side_")
                for axis in group["axis_ids"]:
                    lateral = [
                        a
                        for a in target
                        if a["role"] == accounting.LATERAL
                        and a["source_id"].rsplit("/", 1)[0] == axis
                    ]
                    require(len(lateral) == 2, "missing same-state lateral components")
                    wrench = accounting.wrench(
                        lateral, np.array(lateral[0]["point_mm"])
                    )
                    vector = wrench[:3]
                    magnitude = float(np.linalg.norm(vector))
                    tie = next(
                        a
                        for a in target
                        if a["source_id"] == axis + "/outer-seat-axial-tie"
                    )
                    tension = max(0.0, tie["scalar_row_force_n"])
                    diameter, fyb = (7.9375, 92000.0) if side else (6.35, 92000.0)
                    lengths = [88.9, 88.9] if side else [38.1, 139.7]
                    grains = [members[host]["axis"], members[block]["axis"]]
                    reference = lateral_reference(
                        vector, diameter, lengths, grains, fyb
                    )
                    adjustment = 1.0 if side else cg_rail * cdelta_rail
                    parallel = float(vector @ np.array(members[block]["axis"]))
                    path = path_for[(axis, 1 if parallel >= 0 else -1)]
                    seat = seat_for[axis]
                    washer_pressure = tension / seat["minimum_annulus_area_mm2"]
                    # A declared uniform annulus / independent radial cantilever
                    # strip screen. Required steel stress is reported, not a
                    # capacity attributed to an unspecified low-carbon washer.
                    outer_radius = (0.905 if side else 0.749) * 25.4 / 2
                    flat_radius = 6.0 if side else 5.0
                    moment_per_width = (
                        washer_pressure
                        / flat_radius
                        * (
                            (outer_radius**3 - flat_radius**3) / 3
                            - flat_radius * (outer_radius**2 - flat_radius**2) / 2
                        )
                    )
                    stress = 6 * moment_per_width / seat["minimum_thickness_mm"] ** 2
                    area_thread = (0.0524 if side else 0.0318) * 25.4**2
                    proof = 85000.0 * local.PSI_MPA
                    state = {
                        "case_id": case_id,
                        "block": block,
                        "host": host,
                        "axis_id": axis,
                        "force_on_cleat_xyz_n": vector.tolist(),
                        "lateral_n": magnitude,
                        "tension_n": tension,
                        "conditional_Fyb_psi": fyb,
                        "diameter_mm": diameter,
                        "reference": reference,
                        "declared_Cg_Cdelta_multiplier": adjustment,
                        "lateral_over_adjusted_conditional_reference": magnitude
                        / (reference["reference_n"] * adjustment),
                        "parallel_component_over_finished_path_reference": abs(parallel)
                        / (fv * path["minimum_finished_one_plane_area_mm2"]),
                        "minimum_annulus_wood_pressure_mpa": washer_pressure,
                        "washer_wood_pressure_over_Fc_perp": washer_pressure / fc,
                        "axial_stress_at_nominal_thread_tensile_area_mpa": tension
                        / area_thread,
                        "direct_combined_axial_shank_shear_von_mises_proxy_mpa": math.sqrt(
                            (tension / area_thread) ** 2
                            + 3 * (magnitude / (math.pi * diameter**2 / 4)) ** 2
                        ),
                        "axial_stress_over_conditional_bolt_proof_stress": tension
                        / area_thread
                        / proof,
                        "declared_washer_radial_strip_bending_stress_mpa": stress,
                        "declared_head_nut_flat_bearing_circle_diameter_mm": flat_radius
                        * 2,
                        "washer_metal_capacity_established": False,
                    }
                    states.append(state)
                for cell in [a for a in target if a["role"] == accounting.CONTACT]:
                    pressure = (
                        max(0.0, cell["scalar_row_force_n"]) / cell["cell_area_mm2"]
                    )
                    contacts.append(
                        {
                            "case_id": case_id,
                            "block": block,
                            "host": host,
                            "source_id": cell["source_id"],
                            "cell_mean_pressure_mpa": pressure,
                            "mean_pressure_over_Fc_perp": pressure / fc,
                        }
                    )
                host_actions, _, host_geometry = actions_by_body[host]
                transfer = [a for a in host_actions if a["other_body"] == block]
                lower, upper = (
                    min(a["footprint_mm"][0] for a in transfer),
                    max(a["footprint_mm"][1] for a in transfer),
                )
                length = np.linalg.norm(
                    np.array(host_geometry["end"]) - host_geometry["start"]
                )
                cuts = [
                    accounting.host_cut(host_actions, station, host_geometry, before)
                    for station, before in [
                        (max(0.0, lower - 1), True),
                        (min(float(length), upper + 1), False),
                    ]
                ]
                demand = max(
                    abs(c[s]["force_global_N_n"])
                    for c in cuts
                    for s in ("internal_on_positive_half", "internal_on_negative_half")
                )
                h, b = (139.7, 88.9) if side else (139.7, 38.1)
                center = (np.array(host_geometry["start"]) + host_geometry["end"]) / 2
                coordinates = [
                    float(
                        correction.N
                        @ (np.array(bolts[a]["source_point_xyz_mm"]) - center)
                    )
                    for a in group["axis_ids"]
                ]
                distances = [h / 2 - min(coordinates), h / 2 + max(coordinates)]
                refs = [14 * b * math.sqrt(he / (1 - he / h)) for he in distances]
                host_splitting.append(
                    {
                        "case_id": case_id,
                        "block": block,
                        "host": host,
                        "cuts": cuts,
                        "maximum_complete_section_N_shear_n": demand,
                        "h_b_mm": [h, b],
                        "both_loaded_edge_he_mm": distances,
                        "both_F90_characteristic_references_n": refs,
                        "demand_over_smaller_characteristic_reference": demand
                        / min(refs),
                        "design_conversion_and_3d_group_acceptance_established": False,
                    }
                )
    for path, digest in pins.items():
        require(sha(path) == digest, "input changed during corner checks")
    report = {
        "schema": "corrected_frame_corner_component_references/v1",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "counts": {
            "simultaneous_bolt_states": len(states),
            "finished_grain_paths": len(paths),
            "finished_shear_planes": 2 * len(paths),
            "washer_seats": len(seats),
            "complete_body_states": len(balances),
            "host_splitting_states": len(host_splitting),
        },
        "conditional_bolt_material_specification": {
            "side": "SAE J429 Grade 5, conditional ASTM F606 tensile-yield basis Fyb92ksi",
            "rail": "SAE J429 Grade 5, conditional ASTM F606 tensile-yield basis Fyb92ksi",
            "formal_product_and_test_basis_verification": "remaining",
            "hardware_selected": False,
        },
        "component_references_mpa": {"Fv_parallel": fv, "Fc_perpendicular": fc},
        "rail_component_Cg_Cdelta": [cg_rail, cdelta_rail],
        "states": states,
        "finished_paths": paths,
        "washer_seats": seats,
        "body_balances": balances,
        "host_splitting": host_splitting,
        "contact_cells": contacts,
        "limits": [
            "Reference calculations retain normal-duration dry DF-L No.2 and specified conditional steel inputs, not observed stock or hardware.",
            "Rail Cg and Cdelta are conservative declared component scenarios; full oblique/multiple-plane group behavior and cleat splitting remain separate.",
            "Host splitting references are EN1995-1-1 Eq8.4 characteristic values, both edges; they are not adopted design resistances.",
            "Washer metal screen assumes uniform annulus pressure, minimum catalog thickness, and 10mm rail/12mm side flat bearing circles. It reports required bending stress, not a material capacity or verified head footprint.",
            "Direct steel stress proxies exclude bolt bending; the lateral yield references include dowel bending separately. A coupled axial/lateral steel interaction is not qualified.",
            "Source frame retains parametric panel screws, modeled gaps at both top corners, no preload/friction and conditional gross member stiffness. Other bolted joints have zero lateral gap.",
        ],
        "complete_joint_acceptance": False,
        "physical_release": False,
        "reviewed_geometry_changed": False,
    }
    require(
        report["counts"]
        == {
            "simultaneous_bolt_states": 48,
            "finished_grain_paths": 16,
            "finished_shear_planes": 32,
            "washer_seats": 16,
            "complete_body_states": 30,
            "host_splitting_states": 24,
        },
        "incomplete corner checks",
    )
    (output / "component-results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    for block in accounting.BLOCK_HOSTS:
        subset = [s for s in states if s["block"] == block]
        print(
            block,
            "peak conditional lateral ratio",
            max(s["lateral_over_adjusted_conditional_reference"] for s in subset),
            "finished path ratio",
            max(s["parallel_component_over_finished_path_reference"] for s in subset),
            "washer wood ratio",
            max(s["washer_wood_pressure_over_Fc_perp"] for s in subset),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--clearance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(
            read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
            "shared analysis slot occupied",
        )
        run(args.frame, args.clearance, args.output)
