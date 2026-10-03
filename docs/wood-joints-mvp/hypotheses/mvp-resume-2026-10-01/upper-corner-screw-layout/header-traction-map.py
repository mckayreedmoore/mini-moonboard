"""Map frozen header actions to supported boundary points without free couples.

This is conditional boundary accounting. It solves neither bolt/contact
compatibility nor a timber stress field, and establishes no resistance.
The coordinator owns numeric execution.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
INPUT = HERE / "rawlocal/header-local-transfer/attempt01"
REMAINING = Path("/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json")
ECCENTRIC = Path("/tmp/mini-moonboard-eccentric-parent-check-2026-10-01.json")
PRIMARY = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/seat-screen.json"
PINS = {
    INPUT / "inputs.json": "cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b",
    INPUT / "model.json": "eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52",
    INPUT / "header-sections.csv": "f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953",
    INPUT / "receipt.json": "3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8",
    REMAINING: "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3",
    ECCENTRIC: "0ae0af403cd99b323f0deb489e64bdf7cf94e0d32f0b84f0a9344efda2369354",
    PRIMARY: "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    ROOT / "fea/wood_joint_reduced_contacts.py": "4e088d485cee8953bfdca411f646f18abfb49271c9d8f3b46044588a6a7c1ce7",
}
FLAGS = {"native_readiness": False, "compatibility_solved": False,
         "new_resistance_established": False, "complete_joint_acceptance": False,
         "physical_release": False}
FORCE_TOL = 1e-7
MOMENT_TOL = 1e-5


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"changed frozen input: {path}")


def wrench(actions, datum, *, source=False):
    value = np.zeros(6)
    for action in actions:
        force = np.array(action["force_n"])
        value[:3] += force
        value[3:] += np.cross(np.array(action["point_mm"]) - datum, force)
        if source:
            value[3:] += action["free_moment_nmm"]
    return value


def check_wrench(source, mapped, datum):
    delta = wrench(mapped, datum) - wrench(source, datum, source=True)
    require(max(abs(delta[:3])) < FORCE_TOL and max(abs(delta[3:])) < MOMENT_TOL,
            f"physical point map loses source wrench: {delta.tolist()}")
    return delta.tolist()


def point_action(original, point, force, label):
    return {"row": original["row"], "source_id": original["source_id"],
            "role": original["role"], "other_body": original["other_body"],
            "point_mm": np.asarray(point).tolist(), "force_n": np.asarray(force).tolist(),
            "mapping": label, "free_moment_nmm": [0.0, 0.0, 0.0]}


def header_seats(model):
    axes = {a["axis_id"] for a in model["header_connections"]}
    result = {}
    for index, seat in enumerate(read(REMAINING)["seats"]):
        if seat["axis_id"] not in axes or seat["member"] != "base_header":
            continue
        require(seat["geometry_screen_pass"] and seat["all_direction_hole_only_applicable"],
                "saved header washer support is incomplete")
        result[seat["axis_id"]] = {"center_mm": seat["point_xyz_mm"], "role": seat["role"],
                                  "source": str(REMAINING), "pointer": f"/seats/{index}"}
    primary = read(PRIMARY)
    for axis_index, seat_index in ((4, 0), (5, 1)):
        axis = primary["axes"][axis_index]
        seat = axis["outer_seats"][seat_index]
        require(seat["outer_receiver_member_id"] == "base_header", "primary header seat mismatch")
        result[axis["axis_id"]] = {"center_mm": seat["seat_point_xyz_mm"],
                                  "role": seat["seat_role"].removesuffix("_washer_seat"),
                                  "source": str(PRIMARY.relative_to(ROOT)),
                                  "pointer": f"/axes/{axis_index}/outer_seats/{seat_index}"}
    sweep = read(ECCENTRIC)["swept_step_envelope"]
    require(sweep["all_direction_hole_only_support_proven_within_BREP_tolerance"],
            "primary eccentric support witness is incomplete")
    require(set(result) == axes and len(result) == 12, "header seat census mismatch")
    for seat in result.values():
        z = seat["center_mm"][2]
        require(min(abs(z - 238.9), abs(z - 277.0)) < 1e-7, "unexpected header bearing face")
        seat["inward_normal_xyz"] = [0.0, 0.0, 1.0 if abs(z - 238.9) < 1e-7 else -1.0]
    return result


def contact_geometry(cell, patch):
    """Prove the saved resultant point occupies the rectangle minus full bores."""
    lines = [e for e in patch["boundary_edges"] if e["curve_type"] == "LINE"]
    require(len(lines) == 4, "contact outer boundary is not a saved rectangle")
    require(set(patch["boundary_edge_types"]) <= {"LINE", "CIRCLE"}, "unsupported contact edge")
    normal = np.array(patch["normal_on_first_xyz"])
    origin = np.array(lines[0]["start_xyz_mm"])
    u = np.array(lines[0]["end_xyz_mm"]) - origin
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    vertices = np.array([e[k] for e in lines for k in ("start_xyz_mm", "end_xyz_mm")])
    local = np.column_stack(((vertices - origin) @ u, (vertices - origin) @ v))
    lo, hi = local.min(axis=0), local.max(axis=0)
    require(np.max(abs((vertices - origin) @ normal)) < 1e-6, "nonplanar contact boundary")
    require(all(min(abs(p[0] - lo[0]), abs(p[0] - hi[0])) < 1e-6
                and min(abs(p[1] - lo[1]), abs(p[1] - hi[1])) < 1e-6 for p in local),
            "contact lines do not form the saved aligned rectangle")
    require(abs(np.prod(hi - lo) - sum(e["circle"]["radius_mm"] ** 2 * math.pi
                for e in patch["boundary_edges"] if e["curve_type"] == "CIRCLE")
                - patch["area_mm2"]) < 1e-5, "saved rectangle/bore area mismatch")
    point = np.array(cell["point_xyz_mm"])
    xy = np.array([(point - origin) @ u, (point - origin) @ v])
    clearances = [*list(xy - lo), *list(hi - xy)]
    holes = []
    for edge in patch["boundary_edges"]:
        if edge["curve_type"] != "CIRCLE":
            continue
        circle = edge["circle"]
        require(abs(circle["last_parameter_rad"] - circle["first_parameter_rad"] - 2 * math.pi) < 1e-7,
                "clipped or partial bore is outside this bounded map")
        require(abs(abs(np.dot(circle["axis_xyz"], normal)) - 1) < 1e-8,
                "bore axis is not normal to the contact patch")
        clearance = np.linalg.norm(point - circle["center_xyz_mm"]) - circle["radius_mm"]
        clearances.append(float(clearance))
        holes.append(circle)
    require(abs((point - origin) @ normal) < 1e-6 and min(clearances) > 1e-7,
            f"contact centroid not in occupied patch: {cell['name']}")
    return {"source_patch_index": cell["source_patch_index"], "cell_area_mm2": cell["area_mm2"],
            "source_centroid_mm": cell["point_xyz_mm"], "minimum_patch_boundary_clearance_mm": min(clearances),
            "rectangle_origin_mm": origin.tolist(), "rectangle_u_xyz": u.tolist(),
            "rectangle_v_xyz": v.tolist(), "rectangle_bounds_uv_mm": [lo.tolist(), hi.tolist()],
            "full_bore_circles": holes,
            "scope": "Saved clipped-cell area/centroid and its occupied point; no new cell partition or pressure peak."}


def map_case(case, model, seats, radius_inner, radius_outer, contact_domains):
    mapped, records, lateral = [], [], []
    connections = {a["axis_id"]: a for a in model["header_connections"]}
    datum = np.array([-1.5875, -105.85, 257.95])
    annulus_area = math.pi * (radius_outer ** 2 - radius_inner ** 2)
    quadrature_radius = math.sqrt((radius_outer ** 2 + radius_inner ** 2) / 2)
    for original in case["complete_header_actions"]:
        role, force = original["role"], np.array(original["force_n"])
        require(max(abs(np.array(original["free_moment_nmm"]))) < MOMENT_TOL,
                "source contains a substantive free couple")
        if role == "physical_bolt_outer_seat_tension":
            axis = original["source_id"].split("/")[0]
            require(axis in seats, "unknown header axial tie")
            seat = seats[axis]
            center, normal = np.array(seat["center_mm"]), np.array(seat["inward_normal_xyz"])
            tension = float(force @ normal)
            require(tension > -FORCE_TOL and np.linalg.norm(force - tension * normal) < FORCE_TOL,
                    "tie cannot act as compression on this header washer")
            atoms = []
            for j in range(8):
                angle = 2 * math.pi * (j + 0.5) / 8
                point = center + quadrature_radius * np.array([math.cos(angle), math.sin(angle), 0.0])
                atoms.append(point_action(original, point, force / 8, "concentric_uniform_annulus_linear_exact_quadrature"))
            residual = check_wrench([original], atoms, datum)
            mapped.extend(atoms)
            records.append({"axis_id": axis, "source_row": original["row"], "seat": seat,
                            "tension_n": tension, "annulus_area_mm2": annulus_area,
                            "uniform_pressure_hypothesis_mpa": tension / annulus_area,
                            "source_to_seat_shift_mm": (center - original["point_mm"]).tolist(),
                            "wrench_residual_xyz_n_nmm": residual})
        elif role == "candidate_bolt_lateral_plane":
            # Numerical zero rows have no physical contact location to recover.
            if np.linalg.norm(force) <= FORCE_TOL:
                continue
            axis = original["source_id"].split("/")[0]
            require(axis in connections and abs(force[2]) < FORCE_TOL, "unexpected header lateral action")
            receiver = next(r for r in connections[axis]["receiver_clearance_geometry"]
                            if r["receiver_id"] == "base_header")
            radius = receiver["unique_bore_radius_mm"]
            center = np.array(seats[axis]["center_mm"])
            thickness, mid = 38.1, 257.95
            require(abs(original["point_mm"][2] - 277.0) < 1e-6, "lateral source is not the frozen upper face")
            direction = force / np.linalg.norm(force)
            upper, lower = center.copy(), center.copy()
            upper += radius * direction
            lower -= radius * direction
            upper[2], lower[2] = mid + thickness / 4, mid - thickness / 4
            atoms = [point_action(original, upper, 1.5 * force, "hypothetical_upper_bore_wall_compression"),
                     point_action(original, lower, -0.5 * force, "hypothetical_opposite_lower_bore_wall_compression")]
            residual = check_wrench([original], atoms, datum)
            uniform = point_action(original, [center[0], center[1], mid], force, "same_wall_uniform_mid_depth_diagnostic")
            deficit = wrench([uniform], datum) - wrench([original], datum, source=True)
            mapped.extend(atoms)
            lateral.append({"case_id": case["case_id"], "axis_id": axis, "source_row": original["row"],
                            "source_force_xyz_n": force.tolist(), "source_point_mm": original["point_mm"],
                            "bore_radius_mm": radius, "modeled_radial_clearance_mm": receiver["geometry_only_centered_radial_gap_mm"],
                            "point_actions": atoms, "wrench_residual_xyz_n_nmm": residual,
                            "same_wall_uniform_wrench_deficit_xyz_n_nmm": deficit.tolist(),
                            "compatibility": "Opposite-wall compression is an explicit static hypothesis, not a demonstrated bolt bend/contact state."})
        elif role == "timber_or_panel_contact":
            cell = model["contact_cells"][original["source_id"]]
            patch = model["contact_patches_by_global_source_index"][str(cell["source_patch_index"])]
            sign = "first" if patch["member_ids"][0] == "base_header" else "second"
            normal = -np.array(patch[f"normal_on_{sign}_xyz"])
            compression = float(force @ normal)
            require(compression > -FORCE_TOL and np.linalg.norm(force - compression * normal) < FORCE_TOL,
                    "saved header contact is not compressive normal traction")
            require(np.max(abs(np.array(original["point_mm"]) - cell["point_xyz_mm"])) < 1e-6,
                    "source contact point differs from saved cell centroid")
            contact_domains[original["source_id"]] = contact_geometry(cell, patch)
            mapped.append(point_action(original, original["point_mm"], force, "saved_supported_contact_centroid_uniform_cell_hypothesis"))
        else:
            # Body loads and other retained analytical row actions stay explicit.
            mapped.append(point_action(original, original["point_mm"], force, "retained_source_action_not_a_new_boundary_qualification"))
    delta = check_wrench(case["complete_header_actions"], mapped, datum)
    groups = []
    for interface in case["interfaces"]:
        source = interface["exact_reciprocal_header_actions"]
        physical = [a for a in mapped if a["other_body"] == interface["block"]]
        group_datum = np.array(interface["datum_xyz_mm"])
        group_delta = check_wrench(source, physical, group_datum)
        contacts = [a for a in source if a["role"] == "timber_or_panel_contact"]
        groups.append({"block": interface["block"], "datum_xyz_mm": group_datum.tolist(),
                       "source_header_wrench_xyz_n_nmm": wrench(source, group_datum, source=True).tolist(),
                       "physical_header_wrench_xyz_n_nmm": wrench(physical, group_datum).tolist(),
                       "residual_xyz_n_nmm": group_delta,
                       "sampled_contact_count": len(contacts),
                       "sampled_contact_force_magnitudes_n": [float(np.linalg.norm(a["force_n"])) for a in contacts]})
    return {"case_id": case["case_id"], "datum_xyz_mm": datum.tolist(),
            "source_action_count": len(case["complete_header_actions"]), "mapped_action_count": len(mapped),
            "source_body_residual_xyz_n_nmm": wrench(case["complete_header_actions"], datum, source=True).tolist(),
            "mapped_body_residual_xyz_n_nmm": wrench(mapped, datum).tolist(),
            "mapping_residual_xyz_n_nmm": delta, "header_washer_records": records,
            "lateral_route_records": lateral, "interface_records": groups, "mapped_point_actions": mapped}


def source_witness(inputs, model):
    case = next(c for c in inputs["cases"] if c["case_id"] == "a1-rear")
    section = next(s for s in model["saved_header_sections"] if s["plane_id"] == "base_header:section:2d69ffdf7163d5db")
    require(section["properties"]["component_count"] == 3 and section["properties"]["disconnected_ligaments"],
            "source witness is not the preserved three-ligament section")
    datum = np.array(section["properties"]["centroid_global_xyz_mm"])
    with (INPUT / "header-sections.csv").open(newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["case_id"] == "a1-rear" and row["plane_id"] == section["plane_id"]]
    cuts = []
    for row in rows:
        after = row["trace"] == "after"
        actions = [a for a in case["complete_header_actions"]
                   if a["point_mm"][0] < datum[0] - 1e-6
                   or (after and abs(a["point_mm"][0] - datum[0]) <= 1e-6)]
        restored = -wrench(actions, datum, source=True)
        expected = np.array(json.loads(row["centroid_N_VY_VZ_T_M_Y_M_Z"]))
        require(max(abs(restored[:3] - expected[:3])) < FORCE_TOL
                and max(abs(restored[3:] - expected[3:])) < MOMENT_TOL, "source simultaneous section wrench not reproduced")
        roles = {role: (-wrench([a for a in actions if a["role"] == role], datum, source=True)).tolist()
                 for role in sorted({a["role"] for a in actions})}
        cuts.append({"trace": row["trace"], "signed_N_VY_VZ_T_MY_MZ": expected.tolist(),
                     "source_restoration_residual_xyz_n_nmm": (restored - expected).tolist(),
                     "source_signed_section_wrench_by_role": roles})
    require(len(cuts) == 2, "source section before/after traces missing")
    interface = next(q for q in case["interfaces"] if q["block"] == "knee_outer_left_inner_frame_block")
    return {"case_id": "a1-rear", "station_mm": section["station_mm"], "plane_id": section["plane_id"],
            "section_centroid_xyz_mm": datum.tolist(), "section_geometry": copy.deepcopy(section),
            "source_signed_simultaneous_traces": cuts,
            "source_knee_interface_on_block_xyz_n_nmm": interface["interface_wrench_on_block_xyz_n_nmm"],
            "limits": "Source point-load traces remain unchanged. Spreading washers across X changes interior section traces; no center-plane stress or ligament sharing is inferred from this mapping."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    owned = (HERE / "rawlocal/header-traction-map").resolve()
    require(output != owned and output.is_relative_to(owned) and not output.exists(), "use a fresh owned output child")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    authenticate(pins)
    inputs, model, receipt = read(INPUT / "inputs.json"), read(INPUT / "model.json"), read(INPUT / "receipt.json")
    require(receipt["status"] == "PREPARED_HEADER_INPUT_CONTRACT_FOR_METHOD_SELECTION", "header contract not prepared")
    for name in ("inputs.json", "model.json", "header-sections.csv"):
        require(receipt["output_sha256"][name] == pins[INPUT / name], "header receipt artifact mismatch")
    header = model["bodies"]["base_header"]["member_geometry"]
    pins[ROOT / header["current_finished_step"]] = header["current_finished_step_sha256"]
    authenticate(pins)
    scenario = next(s for s in read(ECCENTRIC)["scenarios"]
                    if s["scenario"] == "K.L. Jack 25NWUS plain Type A Wide / OD minimum / ID maximum")
    ri, ro = scenario["washer_id_mm"] / 2, scenario["washer_od_mm"] / 2
    seats, domains = header_seats(model), {}
    states = [map_case(c, model, seats, ri, ro, domains) for c in inputs["cases"]]
    require(len(states) == 6 and sum(len(s["interface_records"]) for s in states) == 36, "six-case interface census mismatch")
    require(sum(len(s["header_washer_records"]) for s in states) == 72, "same-state header washer census mismatch")
    witness = source_witness(inputs, model)
    lateral = [r for s in states for r in s["lateral_route_records"]]
    require(len(lateral) == 2, "nonzero lateral source census changed")
    authenticate(pins)
    result = {"schema": "header_supported_boundary_mapping/v1", "status": "CONDITIONAL_STATIC_BOUNDARY_ROUTE_COMPATIBILITY_AND_LIGAMENT_TRANSFER_UNRESOLVED",
              "source_force_state_scope": inputs["source_force_state_scope"],
              "boundary_mapping_executed": True, "native_mechanics_executed": False,
              "annulus_hypothesis": {"scenario": scenario["scenario"], "inner_radius_mm": ri,
                                     "outer_radius_mm": ro, "concentric_on_bore": True,
                                     "pressure": "uniform conditional pressure; eight points integrate force and first moments exactly"},
              "contact_hypothesis": "Saved clipped-cell centroid actions represent uniform compressive cell pressure; actual pressure/tilt and peaks remain unqualified.",
              "contact_domains": domains, "header_seats": seats, "cases": states,
              "source_A1_rear_133_35mm_witness": witness,
              "finite_decision": "Supported normal boundary actions preserve all six simultaneous header/interface wrenches. Two lateral states require a demonstrated bearing/bending contact route. Internal compatibility and load sharing between the three paired-hole ligaments remain uncomputed.",
              "next_single_missing_check": "A compatible local header/bolt/contact calculation under these same signed boundary actions, carrying torque around paired holes through the actual connected three-dimensional wood; retain the two lateral opposite-wall hypotheses as explicit and unverified.",
              "unavailable_design_resistances": inputs["unavailable_design_resistances"],
              "limits": ["No balancing couple or new resistance is added.",
                         "Concentric washer seats and uniform cell pressure are declared study hypotheses, not observed hardware states.",
                         "Opposed bore-wall forces are a static construction; clearance closure and bolt/wood compatibility are not solved.",
                         "Full source section torque is distinct from the knee group's four sampled contact forces.",
                         "Original 100 mm frame and its force laws remain unchanged; no motion uniqueness or complete joint acceptance is transferred."], **FLAGS}
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "result.json", result)
    sources = {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): d for p, d in sorted(pins.items())}
    artifacts = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
    write(output / "receipt.json", {"schema": "header_traction_map_receipt/v1", "status": result["status"],
          "counts": {"cases": len(states), "interfaces": 36, "header_seats": 12,
                     "washer_states": 72, "header_contact_cells": len(domains), "nonzero_lateral_states": len(lateral)},
          "source_sha256": sources, "output_sha256": artifacts,
          "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}, **FLAGS})
    print(json.dumps({"status": result["status"], "result_sha256": sha(output / "result.json"),
                      "receipt_sha256": sha(output / "receipt.json"), "nonzero_lateral_states": len(lateral)}))


if __name__ == "__main__":
    main()
