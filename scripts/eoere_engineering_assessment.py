"""Review current saved evidence and probe its small-rotation contact maps.

No assembly, solve, CAD operation or capacity adoption. Finite rigid-arm
positions evaluated at the saved linear state are diagnostics, not a finite
contact model, an equilibrated response or a physical error bound.
"""

from __future__ import annotations

import argparse
import bisect
import importlib.metadata
import json
import math
from itertools import pairwise
from pathlib import Path

import numpy as np

from scripts import eoere_current_response as current
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
PACKET = current.DOC / "selected-hardware-v1/current-response-v1"
GAP_TOLERANCE_MM = 1e-8
CONTACT_IDENTITY_KEYS = ["contact_id", "kind", "first", "second", "point_xyz_mm"]
CONTACT_SCALAR_KEYS = ["linear_gap_mm", "fixed_director_finite_arm_gap_mm", "relative_linear_rotation_rad"]
WRENCH_REFERENCE_XYZ_MM = [0., 750., 1100.]
EXPECTED_LOADS = {
    "a12-forward": ("A12", 0., -300.),
    "a12-rear": ("A12", 0., 300.),
    "a12-left": ("A12", -300., 0.),
    "k12-right": ("K12", 300., 0.),
    "k12-rear": ("K12", 0., 300.),
    "a1-rear": ("A1", 0., 300.),
}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded engineering reviewer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def vector(values):
    value = np.asarray(values, dtype=float)
    current.require(value.shape == (3,) and np.isfinite(value).all(), "finite xyz required")
    return value


def load_check(field):
    """Independent units, eccentricity and whole physical-load arithmetic."""
    case = field["source_inputs"]["case"]
    label, fx, fy = EXPECTED_LOADS[field["case_id"]]
    hold = case["hold"]
    expected = np.array([fx, fy, -250. * 2. * 4.4482216152605])
    current.require(hold["label"] == label and np.allclose(hold["force_xyz_n"], expected, rtol=0, atol=1e-9),
                    "recorded six-case climber basis differs")
    loads = field["body_applied_loads"]
    current.require(loads == case["loads"] and len({r["id"] for r in loads}) == len(loads),
                    "unique exact own physical loads required")
    climber = [r for r in loads if r["id"].startswith("climber/")]
    current.require(len(climber) == 1 and climber[0]["id"] == "climber/" + label
                    and climber[0]["body"] == hold["panel"]
                    and climber[0]["point_xyz_mm"] == hold["load_point_xyz_mm"]
                    and np.allclose(climber[0]["force_xyz_n"], expected, rtol=0, atol=1e-9),
                    "own eccentric climber point load required")
    eccentricity = vector(hold["load_point_xyz_mm"]) - vector(hold["panel_midplane_xyz_mm"])
    couple = np.cross(eccentricity, expected)
    current.require(np.allclose(couple, hold["moment_about_panel_midplane_xyz_nmm"], rtol=0, atol=1e-5),
                    "hold force/couple transport differs")
    forces = [vector(r["force_xyz_n"]) for r in loads]
    moments = [np.cross(vector(r["point_xyz_mm"]), f) for r, f in zip(loads, forces, strict=True)]
    force = [math.fsum(f[i] for f in forces) for i in range(3)]
    moment = [math.fsum(m[i] for m in moments) for i in range(3)]
    current.require(np.allclose(force, case["applied_force_xyz_n"], rtol=0, atol=1e-8)
                    and np.allclose(moment, case["applied_moment_about_global_origin_xyz_nmm"], rtol=0, atol=1e-5),
                    "whole physical load wrench differs")
    gravity = -math.fsum(f[2] for r, f in zip(loads, forces, strict=True) if not r["id"].startswith("climber/"))
    return {"case_id": field["case_id"], "hold": label, "panel": hold["panel"],
            "climber_force_xyz_n": expected.tolist(), "load_point_xyz_mm": hold["load_point_xyz_mm"],
            "midplane_couple_xyz_nmm": couple.tolist(), "physical_load_rows": len(loads),
            "whole_force_xyz_n": force, "whole_moment_about_origin_xyz_nmm": moment,
            "permanent_and_accessory_weight_n": gravity, "numerical_load_basis_verified": True}


def timber_pose(row, point, q, scale):
    """Geometric interpolation from the captured owned coordinate chart."""
    axis, start = vector(row["axis"]), vector(row["start"])
    current.require(abs(np.linalg.norm(axis)-1.) < 1e-10, "unit timber axis required")
    station = float((vector(point)-start) @ axis)
    stations = row["stations"]
    current.require(len(stations) == len(row["index"]) and len(stations) >= 2
                    and all(b > a for a, b in pairwise(stations)),
                    "increasing owned timber stations required")
    i = max(0, min(len(stations)-2, bisect.bisect_left(stations, station)-1))
    a, b = stations[i:i+2]
    fraction = min(1., max(0., (station-a)/(b-a)))
    indices = np.asarray(row["index"][i:i+2])
    current.require(indices.shape == (2, 6) and indices.dtype.kind in "iu"
                    and np.all((indices >= 0) & (indices < len(q))), "owned timber indices differ")
    pose = (1.-fraction)*q[indices[0]] + fraction*q[indices[1]]
    return start + axis*(a+fraction*(b-a)), pose[:3], pose[3:]/scale


def fitting_pose(row, port_id, q, scale):
    matches = [r for r in row["ports"] if r["id"] == port_id]
    current.require(len(matches) == 1, "exact owned fitting surface port required")
    port = matches[0]
    indices = np.asarray(row["dof_indices"][6*port["port_index"]:6*port["port_index"]+6])
    current.require(indices.shape == (6,) and indices.dtype.kind in "iu"
                    and np.all((indices >= 0) & (indices < len(q))), "owned fitting indices differ")
    pose = q[indices]
    return vector(port["point_reference_xyz_mm"]), pose[:3], pose[3:]/scale


def rigid_arm_displacements(point, pose, exp):
    anchor, translation, theta = pose
    offset = vector(point)-anchor
    return translation + np.cross(theta, offset), translation + (exp(theta)-np.eye(3)) @ offset


def gap_class(value):
    return 1 if value > GAP_TOLERANCE_MM else -1 if value < -GAP_TOLERANCE_MM else 0


def contact_probe(field, chart, exp):
    """Finite rigid-arm surrogate with fixed original directors, at saved q."""
    q = np.asarray(field["response"]["q"], dtype=float)
    current.require(q.ndim == 1 and np.isfinite(q).all() and len(q) == chart["final_ndof"]
                    and chart["rotation_scale"] == 1000., "finite owned stored coordinates required")
    current.require(canonical_sha(q.tolist()) == field["response"]["q_canonical_sha256"], "saved q digest differs")
    scale = chart["rotation_scale"]
    members, fittings = chart["timber"], chart["four_port_fittings"]
    actions = {r["id"]: r for r in field["contact_actions"]}
    current.require(len(actions) == len(field["contact_actions"]), "unique own contact actions required")
    rows = []
    for contact in field["reference_interaction_descriptors"]:
        if contact["kind"] not in {"timber_face_contact", "flange_contact"}:
            continue
        point, direction = vector(contact["point_xyz_mm"]), vector(contact["direction_xyz"])
        current.require(abs(np.linalg.norm(direction)-1.) < 1e-10, "unit fixed contact director required")
        poses, displacement = [], []
        for side in ["first", "second"]:
            body = contact[side]
            if body in members:
                pose = timber_pose(members[body], point, q, scale)
            else:
                current.require(body in fittings, "probe excludes panels, shafts and floor")
                pose = fitting_pose(fittings[body], contact.get(side+"_port_id"), q, scale)
            poses.append(pose)
            displacement.append(rigid_arm_displacements(point, pose, exp))
        linear = float(-direction @ (displacement[0][0]-displacement[1][0]))
        surrogate = float(-direction @ (displacement[0][1]-displacement[1][1]))
        action = actions[contact["id"]]
        current.require((action["first"], action["second"]) == (contact["first"], contact["second"])
                        and action["point_xyz_mm"] == contact["point_xyz_mm"]
                        and abs(action["compression_n"]-contact["stiffness"]*max(0., linear)) < 1e-5,
                        "independent linear contact gap does not recover its saved action")
        rows.append({"contact_id": contact["id"], "kind": contact["kind"],
                     "first": contact["first"], "second": contact["second"], "point_xyz_mm": point.tolist(),
                     "linear_gap_mm": linear, "fixed_director_finite_arm_gap_mm": surrogate,
                     "gap_change_mm": surrogate-linear,
                     "relative_linear_rotation_rad": float(np.linalg.norm(poses[0][2]-poses[1][2])),
                     "linear_class": gap_class(linear), "surrogate_class": gap_class(surrogate)})
    current.require(rows and len({r["contact_id"] for r in rows}) == len(rows), "unique nonempty probe contacts required")
    changes = [r for r in rows if r["linear_class"]*r["surrogate_class"] == -1]
    return {"case_id": field["case_id"], "state_id": field["state_id"], "contacts": len(rows),
            "all_contact_scalars": [[r[k] for k in CONTACT_SCALAR_KEYS] for r in rows],
            "timber_face_contacts": sum(r["kind"] == "timber_face_contact" for r in rows),
            "flange_contacts": sum(r["kind"] == "flange_contact" for r in rows),
            "maximum_absolute_gap_change": max(rows, key=lambda r: abs(r["gap_change_mm"])),
            "maximum_relative_linear_rotation": max(rows, key=lambda r: r["relative_linear_rotation_rad"]),
            "strict_open_compressed_class_changes": len(changes),
            "open_to_compressed": sum(r["linear_class"] == -1 for r in changes),
            "compressed_to_open": sum(r["linear_class"] == 1 for r in changes),
            "largest_gap_change_class_switch": max(changes, key=lambda r: abs(r["gap_change_mm"]), default=None),
            "physical_error_bound_or_response": False}, rows


def stability_requirements(records):
    """Domain-only effective lengths; no brace, K or member design adopted."""
    current.require(len({r["member"] for r in records}) == len(records), "unique member domain records required")
    rows = []
    for row in records:
        span, limit = row["span_mm"], row["weak_column_domain_limit_mm"]
        current.require(math.isfinite(span) and math.isfinite(limit) and span > 0 and limit > 0, "positive spans required")
        rows.append({"member": row["member"], "full_span_mm": span, "maximum_effective_length_for_l_over_d_50_mm": limit,
                     "maximum_effective_length_factor_for_full_span": limit/span,
                     "full_span_K1_outside_domain": span > limit,
                     "actual_effective_length_factor": None, "bracing_or_member_strength_qualified": False})
    return rows


def load_path_screen(field):
    """Necessary active-action connectivity, without directional stiffness credit."""
    owners = field["body_identities"]
    current.require(len(set(owners)) == len(owners) and "floor" not in owners, "unique physical owners required")
    graph = {name: set() for name in [*owners, "floor"]}
    indices = {name: i for i, name in enumerate(graph)}
    edges = {}
    active = 0
    for key in ["common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions", "floor_actions"]:
        for row in field[key]:
            first, second = row["first"], row["second"]
            current.require(first in graph and second in graph and first != second, "own physical action endpoints required")
            force = vector(row["force_on_first_xyz_n"])
            moment = vector(row.get("moment_at_point_model_xyz_nmm", row.get("moment_on_first_at_point_xyz_nmm", [0., 0., 0.])))
            if np.linalg.norm(force) <= 1e-6 and np.linalg.norm(moment) <= 1e-5:
                continue
            graph[first].add(second)
            graph[second].add(first)
            edge = tuple(sorted([indices[first], indices[second]]))
            edges[edge] = edges.get(edge, 0)+1
            active += 1
    reached, pending = {"floor"}, ["floor"]
    while pending:
        for name in graph[pending.pop()]:
            if name not in reached:
                reached.add(name)
                pending.append(name)
    missing = sorted(set(owners)-reached)
    return {"case_id": field["case_id"], "state_id": field["state_id"], "physical_owners": len(owners),
            "physical_owner_ids": list(owners),
            "active_edge_census": [[*edge, count] for edge, count in sorted(edges.items())],
            "active_action_rows": active, "owners_without_active_action_path_to_floor": missing,
            "all_owners_have_active_action_path_to_floor": not missing,
            "force_threshold_n": 1e-6, "moment_threshold_nmm": 1e-5,
            "directional_restraint_capacity_or_complete_joint_behavior_qualified": False}


def run():
    producer = own_ref()
    response_ref, component_ref = current.ref(PACKET / "result.json"), current.ref(PACKET / "components.json")
    forces, components = current.read(response_ref), current.read(component_ref)
    manifest = current.manifest()
    current.require(forces["schema"] == "eoere_selected_hardware_six_case_response/v1"
                    and components["schema"] == "eoere_current_six_case_structural_references/v1"
                    and forces["case_sequence"] == components["case_sequence"] == SEQUENCE
                    and [r["case_id"] for r in forces["cases"]] == [r["case_id"] for r in components["cases"]] == SEQUENCE
                    and components["current_response"] == response_ref
                    and forces["geometry"] == components["geometry"] == manifest["geometry"]
                    and forces["hardware_model"] == components["hardware_model"] == manifest["hardware_model"]
                    and forces["geometry_revision"] == components["geometry_revision"] == manifest["geometry_revision"]
                    and forces["hardware_revision"] == components["hardware_revision"] == manifest["hardware_revision"]
                    and forces["extra_grid"] is False and components["extra_grid"] is False
                    and forces["all_six_saved_field_admissions_pass"] is True
                    and forces["complete_joint_resistance"] is None and components["complete_joint_resistance"] is None
                    and forces["finished_member_capacity"] is None and components["finished_member_capacity"] is None
                    and forces["release"] == components["release"] == manifest["release"], "exact current OFF evidence required")
    maps = [current.read(r["source_union"]["record"]) for r in [forces, components]]
    for report, pins in zip([forces, components], maps, strict=True):
        current.require(len(pins) == report["source_union"]["count"]
                        and canonical_sha(pins) == report["source_union"]["canonical_sha256"], "frozen evidence union differs")
    pins = current.join(*maps, {r["path"]: r["sha256"] for r in [producer, response_ref, component_ref,
                                                               *[d["source_union"]["record"] for d in [forces, components]]]})
    current.verify(pins)
    # Reuse the pinned SO(3) helper only after its frozen source closure verifies.
    from scripts.thin_bolted_corotational_methods import so3_exp

    loads, probes, paths, raw_probes, cases, hold_geometry = [], [], [], {}, [], {}
    for binding, component in zip(forces["cases"], components["cases"], strict=True):
        field, operator = current.read(binding["field"]), current.read(binding["operator_bundle"]["manifest"])
        chart = operator["coordinate_map"]
        admission = current.read(binding["admission"])
        current.require(binding["case_id"] == component["case_id"] == field["case_id"]
                        and binding["state_id"] == component["state_id"] == field["state_id"]
                        and component["field"] == binding["field"] and component["admission"] == binding["admission"]
                        and admission[current.SUCCESS] is True
                        and admission["schema"] == "eoere_selected_hardware_field_admission/v1"
                        and admission["case_id"] == field["case_id"] and admission["state_id"] == field["state_id"]
                        and admission["input_raw_sha256"] == binding["field"]["sha256"]
                        and admission["q_canonical_sha256"] == field["response"]["q_canonical_sha256"]
                        and admission["operator_bundle"] == binding["operator_bundle"] == field["operator_bundle"]
                        and field["schema"] == current.FIELD_SCHEMA
                        and field["response"]["converged"] is True
                        and operator["rigid_modes_reference_xyz_mm"] == WRENCH_REFERENCE_XYZ_MM
                        and len(chart["timber"]) == 22 and len(chart["four_port_fittings"]) == 22
                        and len(field["body_identities"]) == 150,
                        "own admitted case/state/chart required")
        loads.append(load_check(field))
        hold = field["source_inputs"]["case"]["hold"]
        geometry = {k: hold[k] for k in ["panel", "load_point_xyz_mm", "panel_midplane_xyz_mm"]}
        current.require(hold_geometry.setdefault(hold["label"], geometry) == geometry, "same owned hold geometry required")
        paths.append(load_path_screen(field))
        probe, raw = contact_probe(field, chart, so3_exp)
        probes.append(probe)
        raw_probes[field["case_id"]] = raw
        cases.append({k: binding[k] for k in ["case_id", "state_id", "field", "admission", "operator_bundle"]})
    requirements = stability_requirements(components["cases"][0]["gross_member_stability"]["all_member_witness_records"])
    current.require(len(requirements) == 22 and all(stability_requirements(c["gross_member_stability"]["all_member_witness_records"])
                                                 == requirements for c in components["cases"]), "same 22 member domains required")
    identities = [{k: r[k] for k in CONTACT_IDENTITY_KEYS} for r in raw_probes[SEQUENCE[0]]]
    current.require(all([{k: r[k] for k in CONTACT_IDENTITY_KEYS} for r in raw_probes[case]] == identities
                        for case in SEQUENCE), "same ordered contact identities required")
    current.verify(pins)
    own_ref()
    return {"schema": "eoere_current_engineering_assessment/v1", "producer": producer,
            "geometry": forces["geometry"], "geometry_revision": forces["geometry_revision"],
            "hardware_model": forces["hardware_model"], "hardware_revision": forces["hardware_revision"],
            "current_response": response_ref, "current_components": component_ref,
            "case_sequence": SEQUENCE, "cases": cases, "load_checks": loads,
            "active_action_load_path_screen": paths,
            "recorded_load_basis": {"climber_lb": 250, "downward_multiplier": 2., "horizontal_force_n": 300.,
                                    "accessory_mass_kg": 25., "dynamic_spectrum_or_all_hold_direction_envelope_verified": False},
            "recorded_hold_geometry": hold_geometry,
            "equilibrium_wrench_reference_xyz_mm": WRENCH_REFERENCE_XYZ_MM,
            "finite_arm_contact_probe": {"fixed_original_directors": True, "evaluated_at_saved_linear_state": True,
                                         "classification_tolerance_mm": GAP_TOLERANCE_MM, "cases": probes,
                                         "contact_identities": identities, "contact_scalar_columns": CONTACT_SCALAR_KEYS,
                                         "finite_equilibrium_contact_law_or_error_bound": False},
            "member_effective_length_domain": requirements,
            "verified_input_unions": [r["source_union"] for r in [forces, components]],
            "all_input_sources_unchanged": True,
            "tool_versions": {n: importlib.metadata.version(n) for n in ["numpy", "scipy"]},
            "screw_panel_exceedance_resolution_deferred_by_owner": True,
            "screw_panel_load_path_removed_or_capacity_accepted": False,
            "small_motion_threshold_adopted": None, "physical_demand_bounds_established": False,
            "complete_joint_resistance": None, "finished_member_capacity": None,
            "structural_acceptance": False, "release": forces["release"],
            "native_solve_CAD_rebuild_or_remedy_performed": False,
            "status": "ENGINEERING_ASSESSMENT_COMPLETE_ACCEPTANCE_NOT_ESTABLISHED"}, raw_probes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--raw-probes", type=Path, required=True)
    args = parser.parse_args()
    current.require(args.out.resolve() != args.raw_probes.resolve()
                    and args.raw_probes.resolve().is_relative_to(current.ROOT)
                    and not args.out.exists() and not args.raw_probes.exists(), "distinct fresh outputs and repository raw identity required")
    report, raw = run()
    raw = {"schema": "eoere_saved_state_contact_probe_rows/v1", "producer": report["producer"],
           "current_response": report["current_response"], "current_components": report["current_components"],
           "cases": raw}
    args.raw_probes.parent.mkdir(parents=True, exist_ok=True)
    with args.raw_probes.open("x") as stream:
        json.dump(raw, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    report["contact_probe_rows"] = current.ref(args.raw_probes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "cases": len(report["cases"]),
                      "probe_contacts": sum(c["contacts"] for c in report["finite_arm_contact_probe"]["cases"])}))


if __name__ == "__main__":
    main()
