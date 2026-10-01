#!/usr/bin/env python3
"""Join the bottom-left joint's frozen bolts, contacts and cleat balance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = HERE.parent
OLD = PACKETS / "remaining-single-shear-reference-2026-10-01/produce.py"
OLD_SHA = "5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf"
REPORT_SHA = "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e"
GRAPH_DIR = PACKETS / "evaluation-resume-2026-09-24/current-geometric-interface-map-attempt02-2026-09-28"
MATERIAL = PACKETS / "hardware-material-specification-2026-09-30/material-inputs.json"
EXPORT = PACKETS / "mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py"
PINS = {
    "previous_producer": (OLD, OLD_SHA),
    "contact_graph": (GRAPH_DIR / "complete-contact-graph.json",
                      "7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26"),
    "contact_graph_pins": (GRAPH_DIR / "source-pins.json",
                           "590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c"),
    "contact_graph_verifier": (GRAPH_DIR / "verify_packet.py",
                               "f839cfe233155bcd5ab56fea943cc2a13d211053d4876e98f4cb48dfdb3c3e43"),
    "face_atlas": (PACKETS / "evaluation-resume-2026-09-24/current-geometric-interface-face-atlas-attempt01-2026-09-28/face-pair-atlas.json",
                   "d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9"),
    "material_inputs": (MATERIAL, "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a"),
    "balance_method": (EXPORT, "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8"),
}
CLEAT = "bottom_outer_left_cleat"
SIDE = "base_side_left"
RAIL = "base_rail_bottom_left"
PAIRS = {(RAIL, CLEAT): 58, (SIDE, CLEAT): 88, (RAIL, SIDE): 56}
AXES = {f"bottom_outer/clip_horizontal_bottom_left_1/{role}_{i}"
        for role in ("rail", "side") for i in (1, 2)}
PSI_TO_MPA = 0.006894757293168361


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, expected, name):
    require(path.is_file() and sha(path) == expected, f"pinned method changed: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "method unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def vector_close(a, b, label, tolerance=1e-8):
    require(len(a) == len(b) == 3 and all(
        math.isfinite(float(x)) and math.isfinite(float(y))
        and math.isclose(x, y, rel_tol=1e-10, abs_tol=tolerance)
        for x, y in zip(a, b, strict=True)), label)


def reference_context(final, pressure, normal, material_members, members, contact_state):
    result = {}
    for member in members:
        grain = material_members[member]["source_proposed_longitudinal_grain_global_xyz"]
        alignment = abs(final.dot(final.unit(normal), final.unit(grain)))
        classification = ("perpendicular" if alignment <= 1e-6 else
                          "parallel" if alignment >= 1 - 1e-6 else "oblique")
        perpendicular = classification == "perpendicular"
        compressive = contact_state == "active_resolved"
        applicable = perpendicular and compressive
        result[member] = {
            "normal_to_proposed_grain": classification,
            "absolute_normal_grain_dot": alignment,
            "unadjusted_Fc_perpendicular_psi": 625.0 if perpendicular else None,
            "compression_reference_comparison_applicable": applicable,
            "cell_average_to_unadjusted_Fc_perpendicular_ratio":
                pressure / (625.0 * PSI_TO_MPA) if applicable else None,
            "reference_exclusion":
                "different_grain_direction_requires_separate_applicable_method" if not perpendicular else
                "source_cell_not_resolved_compressive" if not compressive else None,
            "fully_adjusted_ratio": False, "bearing_accepted": False,
        }
    return result


def checked_cell(final, cell, action, binding, component, inventory):
    name = cell["name"]
    owner = binding["physical_owner"]
    require(binding["name"] == name and binding["force_law"] == "k * max(q_mm, 0)"
            and action["role"] == owner["role"] == "timber_or_panel_contact",
            "wrong compression-cell identity/law")
    require(action["source_row_ids"] == [binding["source_row_id"]]
            and component["source_row_id"] == binding["source_row_id"]
            and component["source_inventory_row_index"] == binding["source_inventory_row_index"]
            and component["element"] == binding["source_element"]
            and component["intended_source_law"] == "compression_only",
            "contact/native source mapping differs")
    source = inventory[binding["source_inventory_row_index"]]
    require(source["physical_owner"] == owner and source["name"] == name
            and source["intended_law"] == "compression_only"
            and action["source_inventory_rows"] == [{
                "source_inventory_row_index": binding["source_inventory_row_index"],
                "source_row_id": binding["source_row_id"],
                "source_connection_name": name, "intended_law": "compression_only"}],
            "contact raw inventory differs")
    for key in ("first", "second"):
        require(cell[key] == action[key] == owner[key], "contact receiver differs")
    area = float(cell["area_mm2"])
    require(math.isfinite(area) and area > 0 and final.close(area, action["source_area_mm2"])
            and final.close(area, owner["source_area_mm2"]), "contact area differs")
    vector_close(cell["point_xyz_mm"], action["point"], "cell/action datum differs")
    vector_close(action["point"], owner["point"], "cell/binding datum differs")
    vector_close(cell["normal_xyz"], action["scalar_normal"], "cell normal differs")
    vector_close(action["scalar_normal"], owner["scalar_normal"], "binding normal differs")
    for gate in ("inside_table_domain_including_rounding", "table_force_interval_intersects_native_rf",
                 "native_endpoint_action_reaction_passed", "numerical_ground_rf_excluded_from_physical_balance"):
        require(component[gate] is True, f"source contact gate failed: {gate}")
    force = float(component["native_endpoint_internal_force_N"])
    radius = float(component["native_endpoint_internal_radius_N"])
    require(math.isfinite(force) and force >= 0 and math.isfinite(radius) and radius >= 0,
            "invalid signed compression force/radius")
    require(math.isclose(final.dot(action["scalar_normal"], action["scalar_normal"]),
                         1.0, rel_tol=0, abs_tol=1e-8), "contact normal is not unit length")
    normal = final.unit(action["scalar_normal"])
    vector_close(action["force_on_first_xyz_n"], [force * v for v in normal],
                 "native contact action differs")
    vector_close(component["physical_force_on_first_body_xyz_n"], action["force_on_first_xyz_n"],
                 "native contact owner vector differs")
    vector_close(action["force_on_second_xyz_n"], [-v for v in action["force_on_first_xyz_n"]],
                 "contact action/reaction differs")
    vector_close(action["force_rounding_radius_xyz_n"], [radius * abs(v) for v in normal],
                 "native/action contact force radii differ")
    q, qr = component["q_relative_projection_mm"], component["q_relative_projection_radius_mm"]
    require(all(math.isfinite(v) for v in (q, qr)) and qr >= 0, "invalid contact q interval")
    interval = component["native_table_force_interval_N"]
    require(len(interval) == 2 and all(math.isfinite(v) for v in interval)
            and 0 <= interval[0] <= interval[1]
            and interval[0] <= force + radius and force - radius <= interval[1],
            "native force and table intervals do not intersect")
    state = ("active_resolved" if force - radius > 0 else
             "open_resolved" if force == 0 and q + qr < 0
             and max(abs(v) for v in component["native_table_force_interval_N"]) == 0 else
             "ambiguous_at_rounded_boundary")
    return {"name": name, "source_row_id": binding["source_row_id"],
            "area_mm2": area, "point_xyz_mm": cell["point_xyz_mm"], "normal_xyz": normal,
            "native_compression_force_N": force, "native_force_radius_N": radius,
            "source_q_mm": q, "source_q_radius_mm": qr, "contact_state": state,
            "modeled_cell_average_pressure_MPa": force / area,
            "compression_average_pressure_interval_MPa":
                [max(0.0, force-radius)/area, (force+radius)/area]}


def checked_tie_radius(action, component):
    radius = component["native_endpoint_internal_radius_N"]
    require(math.isfinite(radius) and radius >= 0, "invalid native tie force radius")
    vector_close(action["force_rounding_radius_xyz_n"],
                 [radius * abs(v) for v in action["scalar_normal"]],
                 "native/action tie force radii differ")


def produce(source_report):
    pins = {}
    for name, (path, expected) in PINS.items():
        require(sha(path) == expected, f"source changed: {name}")
        pins[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": expected}
    final = load(OLD, OLD_SHA, "bottom_prior_reference")
    pins.update(final.pin_sources())
    require(sha(source_report) == REPORT_SHA, "prior 52-bolt report changed")
    report = json.loads(source_report.read_text())
    require(report["producer_sha256"] == OLD_SHA and report["claim_limits"]["joint_accepted"] is False,
            "prior reference identity/acceptance differs")
    graph_check = load(*PINS["contact_graph_verifier"], "bottom_graph_verifier")
    graph_verified = graph_check.verify(ROOT)
    require(graph_verified["result"] == "PASS", "finished geometry evidence failed")
    graph = json.loads(PINS["contact_graph"][0].read_text())
    atlas = json.loads(PINS["face_atlas"][0].read_text())
    require(graph["revision_id"] == atlas["revision_id"] == final.REVISION,
            "contact graph/atlas revision differs")
    graph_pairs = {tuple(row["member_ids"]): row for row in graph["edges"]}
    atlas_pairs = {tuple(row["member_ids"]): row for row in atlas["finite_opposed_interfaces"]}
    pair_geometry = {}
    for pair in PAIRS:
        key = tuple(sorted(pair))
        edge, face = graph_pairs[key], atlas_pairs[key]
        require(edge["geometry_state"] == "finite_opposed_planar_touch"
                and edge["common_volume_mm3"] == 0
                and abs(edge["finite_shared_planar_face_area_mm2"] - face["reconstructed_opposed_area_mm2"]) < 1e-6,
                "nominal paired-face evidence differs")
        pair_geometry["|".join(pair)] = {"graph_edge": edge, "face_atlas": face}
    materials = json.loads(MATERIAL.read_text())
    require(materials["candidate"] == final.CANDIDATE
            and materials["geometry_revision"] == final.REVISION
            and materials["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"] == 625,
            "conditional material reference differs")
    for pin in materials["source_pins"]:
        require(sha(ROOT / pin["path"]) == pin["sha256"], "material source changed")
    material_members = {row["member_id"]: row for row in materials["members"]}
    shared = final.load_module("bottom_shared", final.DEMAND_PATH, final.PINS["remaining_demand_producer"][1])
    right = final.load_module("bottom_plane", final.RIGHT_PATH, final.PINS["right_plane_checker"][1])
    export = load(*PINS["balance_method"], "bottom_balance")
    geometry = shared.load_method("geometry")
    _, connections, primary, upper = final.load_geometry_and_partition(shared, right)
    selected = {row["axis_id"]: row for row in connections if row["axis_id"] in AXES}
    require(set(selected) == AXES and not AXES.intersection(primary + upper), "bottom axis scope differs")
    seats = {axis: {row["role"]: row for row in geometry.source_seats(c)} for axis, c in selected.items()}
    require(sha(shared.FREEZE) == shared.FREEZE_SHA, "three-case freeze changed")
    freeze = json.loads(shared.FREEZE.read_text())
    require(report["source_acceptance"]["source_cases"] == freeze["cases"], "case sources differ")
    old_rows = {(row["case_id"], row["increment_index"], row["axis_id"]): row
                for row in report["state_rows"] if row["axis_id"] in AXES}
    require(len(old_rows) == 84, "four-bolt reference-state coverage differs")
    cleat_expected = ({row["lateral_plane_source_name"] for row in old_rows.values()}
                      | {axis + "/outer-seat-axial-tie" for axis in AXES}
                      | {f"contact_{patch}_{i}" for patch in (58, 88) for i in range(4)})
    require(len(cleat_expected) == 16, "four-bolt cleat boundary identity differs")
    states, cells, pair_states = [], [], []
    fingerprints = []
    for case, files in freeze["cases"].items():
        for pin in files.values():
            require(sha(ROOT / pin["path"]) == pin["sha256"], "frozen case source changed")
        model = json.loads((ROOT / files["model"]["path"]).read_text())
        response = json.loads((ROOT / files["response"]["path"]).read_text())
        audit = json.loads((ROOT / files["all_body_audit"]["path"]).read_text())
        require(model["candidate"] == response["candidate"] == final.CANDIDATE
                and model["geometry_revision_id"] == response["geometry_revision_id"] == final.REVISION
                and model["case_id"] == response["case_id"] == case
                and tuple(row["load_factor"] for row in response["increments"]) == final.FACTORS
                and audit["physical_tolerances_N_Nmm"] == [0.1, 2.0], "source case identity/gates differ")
        contact_cells = {row["name"]: row for row in model["contact_cell_ownership"]
                         if (row["first"], row["second"]) in PAIRS}
        names = {f"contact_{patch}_{i}" for patch in PAIRS.values() for i in range(4)}
        require(set(contact_cells) == names, "three-pair contact-cell coverage differs")
        fingerprints.append(contact_cells)
        bindings = {row["name"]: row for row in model["unilateral_springa_bindings"]}
        springs = {row["source_row_id"]: row for row in model["springs"]}
        inventory = model["raw_source_carrier_law_inventory_rows"]
        cleat_names = {row["name"] for row in inventory
                       if CLEAT in (row["physical_owner"]["first"], row["physical_owner"]["second"])}
        require(cleat_names == cleat_expected, "complete cleat boundary inventory differs")
        record = model["body_geometry"][CLEAT]["geometry_record"]
        datum = [(a+b)/2 for a, b in zip(record["start"], record["end"], strict=True)]
        for member in (CLEAT, SIDE, RAIL):
            descriptor = model["body_geometry"][member]["geometry_record"]["source_descriptor"]
            grain = material_members[member]["source_proposed_longitudinal_grain_global_xyz"]
            require(abs(abs(final.dot(final.unit(grain), final.unit(descriptor["grain_global_xyz"]))) - 1) < 1e-8,
                    "material/model proposed grain differs")
        for index, inc in enumerate(response["increments"]):
            require(all(inc[key] is True for key in shared.GATES), "source response gate failed")
            identity = {"case_id": case, "increment_index": index, "load_factor": inc["load_factor"]}
            components = {row["source_row_id"]: row for row in inc["springa_components"]}
            bilateral = {row["source_row_id"]: row for row in inc["retained_bilateral_spring2_components"]}
            actions = inc["physical_connection_forces"]
            for pair, patch in PAIRS.items():
                pair_cells = []
                for i in range(4):
                    name = f"contact_{patch}_{i}"
                    binding = bindings[name]
                    cell = checked_cell(final, contact_cells[name], actions[name], binding,
                                        components[binding["source_row_id"]], inventory)
                    cell["grain_reference_context"] = reference_context(
                        final, cell["modeled_cell_average_pressure_MPa"], cell["normal_xyz"],
                        material_members, pair, cell["contact_state"])
                    row = {**identity, "member_pair": list(pair), **cell}
                    cells.append(row)
                    pair_cells.append(row)
                area = math.fsum(row["area_mm2"] for row in pair_cells)
                graph_area = pair_geometry["|".join(pair)]["graph_edge"]["finite_shared_planar_face_area_mm2"]
                require(abs(area - graph_area) < 1e-6, "four modeled cell areas do not match finished shared area")
                pair_states.append({**identity, "member_pair": list(pair), "source_cell_names": [row["name"] for row in pair_cells],
                                    "finished_shared_area_mm2": graph_area, "modeled_cell_area_sum_mm2": area,
                                    "total_native_compression_force_N": math.fsum(row["native_compression_force_N"] for row in pair_cells),
                                    "joint_accepted": False})
            bolt_rows = []
            for axis in sorted(AXES):
                old = old_rows[(case, index, axis)]
                plane = actions[old["lateral_plane_source_name"]]
                owner = springs[plane["source_row_ids"][0]]["physical_owner"]
                force, force_radius = right.checked_plane(plane, springs, bilateral, inventory, owner)
                vector_close(force, old["actual_lateral_force_on_receiver_0_N"], "old/new lateral force differs")
                vector_close(force_radius, old["actual_lateral_force_rounding_radius_N"],
                             "old/new lateral force radii differ")
                name = axis + "/outer-seat-axial-tie"
                binding = bindings[name]
                tie = shared.checked_tie(actions[name], binding, components[binding["source_row_id"]], seats[axis])
                checked_tie_radius(actions[name], components[binding["source_row_id"]])
                require(final.close(tie, old["same_state_signed_outer_tie_N_once"]), "old/new same-state tie differs")
                bolt_rows.append(old)
            boundary = {name: actions[name] for name in sorted(cleat_names)}
            balance = export.member_balance(model, {"corner_body_names": [CLEAT]},
                                            {"descriptor_midpoint_datums_mm": {CLEAT: datum}}, boundary, inc["load_factor"])[CLEAT]
            original = audit["increments"][index]["body_equilibrium"][CLEAT]
            require(balance["raw_balance_passed"] and balance["rounding_interval_balance_passed"], "cleat FBD failed")
            vector_close(balance["combined_residual_wrench"]["force_xyz_n"], original["force_residual_xyz_n"], "cleat force audit differs")
            vector_close(balance["combined_residual_wrench"]["moment_xyz_nmm"], original["moment_residual_xyz_nmm"], "cleat moment audit differs", 1e-6)
            states.append({**identity, "bolt_reference_rows": bolt_rows, "cleat_complete_boundary_actions": boundary,
                           "cleat_source_balance": balance, "direct_host_contact_names": [f"contact_56_{i}" for i in range(4)],
                           "joint_accepted": False})
    require(all(value == fingerprints[0] for value in fingerprints), "case contact geometry differs")
    require(len(states) == 21 and len(cells) == 252 and len(pair_states) == 63, "joint/contact state coverage differs")
    return {"schema": "bottom_outer_joint_disposition/v1", "status": "PASS_SOURCE_JOIN_AND_CONDITIONAL_REFERENCE_CONTEXT_ONLY",
            "producer_sha256": sha(HERE / "produce.py"), "candidate": final.CANDIDATE, "geometry_revision_id": final.REVISION,
            "source_report_sha256": REPORT_SHA, "source_pins": pins, "case_sources": freeze["cases"],
            "material_source_pins": materials["source_pins"], "nominal_pair_geometry": pair_geometry,
            "counts": {"joint_states": 21, "bolt_reference_rows": 84, "contact_cell_states": 252,
                       "contact_pair_states": 63, "complete_cleat_balance_states": 21},
            "joint_states": states, "contact_cell_states": cells, "contact_pair_states": pair_states,
            "claim_limits": {"joint_accepted": False, "adopted_capacity": False, "fully_adjusted_ratios": False,
                             "actual_pressure_peak_established": False, "physical_contact_or_stiffness_qualified": False,
                             "complete_host_member_boundary_or_finished_section": False, "native_solve": False,
                             "geometry_changed": False, "criterion_pass": False}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", type=Path, required=True)
    print(json.dumps(produce(parser.parse_args().source_report), indent=2, allow_nan=False))
