#!/usr/bin/env python3
"""Recover existing upper-joint actions and conditional component references.

No native solve or geometry change. This packet does not accept a joint.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from mini_moonboard.wood_joint_bolt_resistance import (
    bolt_first_yield_reference,
    wood_washer_annulus_reference_lbf,
)
from mini_moonboard.wood_joint_directional_geometry import classify_member_fastener_load

STATIONS = {
    "top_outer_left_cleat": "top_outer/clip_single_top_left_1/",
    "top_outer_right_cleat": "top_outer/clip_single_top_right_2/",
    "top_center_left_cleat": "top_center/clip_split_top_center_left/",
    "top_center_right_cleat": "top_center/clip_split_top_center_right/",
}
INCREMENT_GATES = (
    "mpc_interval_checks_passed",
    "retained_bilateral_checks_passed",
    "springa_law_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
LBF_N = 4.4482216152605
PSI_MPA = 0.006894757293168


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_text())


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a, factor):
    return [factor * x for x in a]


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    return scale(a, 1 / norm(a))


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def sum_vectors(rows):
    return [math.fsum(row[i] for row in rows) for i in range(3)]


def close(a, b, tolerance):
    if max(map(abs, sub(a, b))) > tolerance:
        raise AssertionError((a, b, tolerance))


def endpoint(row, body):
    side = "first" if row["first"] == body else "second"
    assert row[side] == body
    return row.get(side + "_point", row["point"]), row["force_on_" + side + "_xyz_n"]


def box(model, member):
    g = model["body_geometry"][member]["geometry_record"]
    axes = [unit(g[k]) for k in ("section_u", "section_v", "axis")]
    close(cross(axes[0], axes[1]), axes[2], 1e-8)
    bounds = [
        [-g["width_mm"] / 2, g["width_mm"] / 2],
        [-g["depth_mm"] / 2, g["depth_mm"] / 2],
        [0, norm(sub(g["end"], g["start"]))],
    ]
    return g, axes, bounds


def direction(model, member, lateral, force):
    g, axes, bounds = box(model, member)
    axis = unit(lateral["axis"])
    index = max(range(3), key=lambda i: abs(dot(axis, axes[i])))
    assert abs(abs(dot(axis, axes[index])) - 1) < 1e-8
    # Move along this bolt line into the member for closed-box classification.
    # This leaves all grain/end and transverse-edge coordinates unchanged.
    center = lateral["point"]
    local = dot(sub(center, g["start"]), axes[index])
    center = add(center, scale(axes[index], sum(bounds[index]) / 2 - local))
    result = classify_member_fastener_load(
        force_on_member_global_n=force,
        grain_axis_global_unit=unit(g["source_descriptor"]["grain_global_xyz"]),
        bolt_axis_global_unit=axis,
        bolt_center_global_mm=center,
        member_frame_origin_global_mm=g["start"],
        member_axes_global_unit=axes,
        member_bounds_local_mm=bounds,
    )
    angle = math.degrees(
        math.acos(
            min(
                1,
                abs(result["force_parallel_to_grain_signed_n"])
                / result["bolt_lateral_force_magnitude_n"],
            )
        )
    )
    compact = {
        k: result[k]
        for k in (
            "force_parallel_to_grain_signed_n",
            "force_cross_grain_signed_on_frame_axis_n",
            "grain_end_direction",
            "cross_grain_edge_direction",
        )
    }
    compact["unsigned_load_to_grain_degrees"] = angle
    return compact, {
        "member": member,
        "box_origin_xyz_mm": g["start"],
        "box_axes_xyz": axes,
        "box_bounds_mm": bounds,
        "conditional_grain_xyz": unit(g["source_descriptor"]["grain_global_xyz"]),
        "bolt_line_mid_bearing_xyz_mm": center,
        "bearing_length_mm": bounds[index][1] - bounds[index][0],
        "finished_step": g["geometry_diagnostics"]["geometry_source"],
        "finished_step_sha256": g["geometry_diagnostics"]["geometry_sha256"],
        "boundary_limit": "Outer box only; local cuts and other bores are separate checks.",
    }


def lateral_reference(geometry, directions, demand):
    # Both interpretations were explicitly preserved in the earlier method note.
    # Neither is adopted here; nominal-D bearing and root-D bearing remain distinct.
    angles = [
        directions[x]["unsigned_load_to_grain_degrees"] for x in ("block", "host")
    ]
    lengths = [geometry[x]["bearing_length_mm"] / 25.4 for x in ("block", "host")]
    effective_d = 0.189  # Labeled typical-root scenario, not a class or lot bound.
    factor = (10 * effective_d + 0.5) * (1 + 0.25 * max(angles) / 90)
    result = {}
    for name, fe_d in (
        ("nominal_D_bearing_root_yield", 0.25),
        ("root_D_bearing_root_yield_sensitivity", effective_d),
    ):
        fe = [dfl_dowel_bearing_psi(fe_d, angle) for angle in angles]
        ref = single_shear(
            main_length_in=lengths[0],
            side_length_in=lengths[1],
            main_bearing_lb_in=fe[0] * effective_d,
            side_bearing_lb_in=fe[1] * effective_d,
            main_yield_moment_lb_in=106000 * effective_d**3 / 6,
            side_yield_moment_lb_in=106000 * effective_d**3 / 6,
            gap_in=0,
            reduction_terms=dict.fromkeys(MODES, factor),
        )
        ref_n = ref["reference_lateral_lbf"] * LBF_N
        result[name] = {
            "bearing_input_psi_block_host": fe,
            "reference_lateral_n": ref_n,
            "six_reference_modes_n": {
                k: v * LBF_N for k, v in ref["reference_values_lbf"].items()
            },
            "governing_mode": ref["governing_mode"],
            "demand_to_unadjusted_reference": demand / ref_n,
        }
    return result


def body_balance(model, increment, body, incident):
    source = increment["physical_balance"]["body_equilibrium"][body]
    assert source["printed_resultants_passed"] and source["interval_resultants_passed"]
    datum = source["reference_xyz_mm"]
    forces, moments, radii, moment_radii = [], [], [], []
    receiver_actions = {}
    for name, row in incident.items():
        point, force = endpoint(row, body)
        arm = sub(point, datum)
        moment = cross(arm, force)
        radius = row["force_rounding_radius_xyz_n"]
        forces.append(force)
        moments.append(moment)
        radii.append(radius)
        moment_radii.append(
            [
                abs(arm[1]) * radius[2] + abs(arm[2]) * radius[1],
                abs(arm[2]) * radius[0] + abs(arm[0]) * radius[2],
                abs(arm[0]) * radius[1] + abs(arm[1]) * radius[0],
            ]
        )
        receiver = row["second"] if row["first"] == body else row["first"]
        group = receiver_actions.setdefault(
            receiver, {"forces": [], "moments": [], "source_names": []}
        )
        group["forces"].append(force)
        group["moments"].append(moment)
        group["source_names"].append(name)
    for node, ref_force in model["physical_body_loads"][body].items():
        force = scale(ref_force, increment["load_factor"])
        forces.append(force)
        moments.append(cross(sub(model["nodes"][str(node)], datum), force))
    f, m = sum_vectors(forces), sum_vectors(moments)
    rf, rm = sum_vectors(radii), sum_vectors(moment_radii)
    close(f, source["force_residual_xyz_n"], 1e-8)
    close(m, source["moment_residual_xyz_nmm"], 1e-6)
    assert max(map(abs, f)) <= 0.1 and max(map(abs, m)) <= 2
    assert all(abs(v) <= r + 1e-9 for v, r in zip(f, rf))
    assert all(abs(v) <= r + 1e-6 for v, r in zip(m, rm))
    return {
        "case": model["case_id"],
        "load_factor": increment["load_factor"],
        "block": body,
        "datum_xyz_mm": datum,
        "force_residual_n": f,
        "moment_residual_nmm": m,
        "force_rounding_radius_n": rf,
        "moment_rounding_radius_nmm": rm,
        "source_load_node_count": len(model["physical_body_loads"][body]),
        "incident_connection_count": len(incident),
        "source_balance_reproduced": True,
        "receiver_actions_on_block": {
            k: {
                "force_n": sum_vectors(v["forces"]),
                "moment_at_block_datum_nmm": sum_vectors(v["moments"]),
                "source_names": v["source_names"],
            }
            for k, v in sorted(receiver_actions.items())
        },
    }


def produce():
    freeze = load(HERE / "freeze.json")
    manifest = [item for case in freeze["cases"].values() for item in case.values()]
    manifest += freeze["method_and_hardware_sources"]
    for item in manifest:
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError("Frozen input changed: " + item["path"])
    hardware_path = next(
        x["path"] for x in manifest if x["path"].endswith("fastener-axis-register.json")
    )
    hardware = load(ROOT / hardware_path)
    hardware_by_axis = {x["axis_id"]: x for x in hardware["candidate_axis_rows"]}
    washer = wood_washer_annulus_reference_lbf(
        washer_outer_diameter_in=18.4658 / 25.4,
        washer_inner_diameter_in=8.3058 / 25.4,
        wood_bore_diameter_in=7.5 / 25.4,
    )
    output = {
        "schema": "upper-frame-joint-review/v1",
        "candidate": freeze["candidate"],
        "geometry_revision_id": freeze["geometry_revision_id"],
        "status": "CONDITIONAL_UPPER_ACTIONS_AND_COMPONENT_REFERENCES_ONLY",
        "producer_sha256": sha(Path(__file__)),
        "freeze_sha256": sha(HERE / "freeze.json"),
        "method_scenarios": {
            "direct_steel": "Hypothetical Grade 5 Fy=92 ksi; At=0.0318 in2. Root shear Av=pi*(0.189 in)^2/4, assumed at plane. No co-located combined stress or bolt bending established.",
            "wood_lateral": "Unadopted typical 0.189-in root across bearing, Fyb=106 ksi Commentary estimate, two DF-L solid members and a hypothetical contacting zero-gap interface. Loaded-face contacting applicability is not established by the frame spring response. Separate nominal-D and root-D Fe conventions. No adjustments, group sum, splitting, axial interaction or physical force-distribution bound.",
            "direction": "Equal-and-opposite signed lateral forces on each receiver, conditional grain, finite outer-box boundaries. Pure-direction NDS comparisons are diagnostic; oblique applicability and nearer cut/bore boundaries remain open.",
            "washer": washer,
            "washer_dimensions_basis": "Representative ASME Type A wide nominal support scenario: minimum OD18.4658 mm, maximum ID8.3058 mm; full annulus, no preload or plate-spreading credit.",
        },
        "source_cases": freeze["cases"],
        "geometry_by_axis": {},
        "case_assumptions": {},
        "bolt_actions": [],
        "block_balances": [],
        "complete_joint_resistance_established": False,
        "six_case_envelope_established": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "native_solve_executed_by_this_packet": False,
        "reviewed_geometry_changed": False,
    }
    for case, files in freeze["cases"].items():
        model, response = (
            load(ROOT / files["model"]["path"]),
            load(ROOT / files["response"]["path"]),
        )
        terminal, audit = (
            load(ROOT / files["terminal"]["path"]),
            load(ROOT / files["all_body_audit"]["path"]),
        )
        assert model["candidate"] == response["candidate"] == output["candidate"]
        assert (
            model["geometry_revision_id"]
            == response["geometry_revision_id"]
            == output["geometry_revision_id"]
        )
        assert model["case_id"] == response["case_id"] == case
        for claim in (
            "qualified_for_design",
            "mechanical_acceptance",
            "joint_demand_accepted",
            "floor_capacity_established",
            "friction_qualified",
        ):
            assert response[claim] is False
        assert response["source_inventory"]["new_candidate_bolt_axes"] == 92
        assert response["source_inventory"]["retained_leg_runner_bolt_axes"] == 12
        assert response["source_inventory"]["panel_screw_axes"] == 66
        assert audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
        assert audit["source_model_sha256"] == files["model"]["sha256"]
        assert audit["source_response_sha256"] == files["response"]["sha256"]
        usable = terminal.get(
            "conditional_case_forces_usable",
            terminal.get("response_usable_for_conditional_joint_checks"),
        )
        assert usable is True
        for name, key in (
            ("model", "source_input_model_json_sha256"),
            ("deck", "source_input_deck_sha256"),
            ("native_data", "native_data_sha256"),
        ):
            assert response[key] == files[name]["sha256"]
        assert (
            len(response["increments"]) == 7
            and response["increments"][-1]["load_factor"] == 1
        )
        output["case_assumptions"][case] = {
            "material_binding": model["material_binding"],
            "connection_scenario": model["connection_scenario"],
        }
        for index, increment in enumerate(response["increments"]):
            assert all(increment[k] is True for k in INCREMENT_GATES)
            connections = increment["physical_connection_forces"]
            for block, prefix in STATIONS.items():
                incident = {
                    k: v
                    for k, v in connections.items()
                    if block in (v["first"], v["second"])
                }
                assert len(incident) == 16
                balance = body_balance(model, increment, block, incident)
                balance["increment_index"] = index
                output["block_balances"].append(balance)
                lateral_rows = {
                    k: v
                    for k, v in incident.items()
                    if v["role"] == "candidate_bolt_lateral_plane"
                }
                assert len(lateral_rows) == 4
                assert (
                    sum(
                        v["role"] == "timber_or_panel_contact"
                        for v in incident.values()
                    )
                    == 8
                )
                for name, lateral in sorted(lateral_rows.items()):
                    axis_id = lateral["axis_id"]
                    assert axis_id.startswith(prefix)
                    axial = connections[axis_id + "/outer-seat-axial-tie"]
                    close(
                        lateral["force_on_first_xyz_n"],
                        scale(lateral["force_on_second_xyz_n"], -1),
                        1e-10,
                    )
                    close(
                        axial["force_on_first_xyz_n"],
                        scale(axial["force_on_second_xyz_n"], -1),
                        1e-10,
                    )
                    host = (
                        lateral["second"]
                        if lateral["first"] == block
                        else lateral["first"]
                    )
                    assert {axial["first"], axial["second"]} == {block, host}
                    directions, geometry = {}, {}
                    for role, member in (("block", block), ("host", host)):
                        _, force = endpoint(lateral, member)
                        directions[role], geometry[role] = direction(
                            model, member, lateral, force
                        )
                        if case == "a12-rear" and index == 0:
                            assert (
                                sha(ROOT / geometry[role]["finished_step"])
                                == geometry[role]["finished_step_sha256"]
                            )
                    if axis_id in output["geometry_by_axis"]:
                        assert (
                            output["geometry_by_axis"][axis_id]["members"] == geometry
                        )
                    else:
                        output["geometry_by_axis"][axis_id] = {
                            "block": block,
                            "host": host,
                            "members": geometry,
                            "lateral_plane_xyz_mm": lateral["point"],
                            "head_to_nut_axis_xyz": lateral["axis"],
                            "outer_seat_endpoints_xyz_mm": [
                                axial["first_point"],
                                axial["second_point"],
                            ],
                            "hardware_axis_record": hardware_by_axis[axis_id],
                        }
                    grip = math.fsum(g["bearing_length_mm"] for g in geometry.values())
                    assert (
                        abs(grip - hardware_by_axis[axis_id]["modeled_wood_grip_mm"])
                        < 1e-6
                    )
                    assert (
                        abs(
                            norm(sub(axial["second_point"], axial["first_point"]))
                            - grip
                        )
                        < 1e-6
                    )
                    shear = norm(lateral["force_on_first_xyz_n"])
                    tension = axial["axial_along_installation_direction_n"]
                    assert abs(shear - lateral["transverse_shear_n"]) < 1e-9
                    assert tension >= -1e-8
                    steel = bolt_first_yield_reference(
                        axial_force_n=tension,
                        lateral_shear_vector_n=(shear, 0.0),
                        minimum_tensile_area_mm2=0.0318 * 25.4**2,
                        shear_plane_area_mm2=math.pi * (0.189 * 25.4) ** 2 / 4,
                        specified_min_yield_mpa=92000 * PSI_MPA,
                        property_scenario_id="hypothetical_grade5_typical_root_shear",
                        material_basis="Pinned conditional Grade 5 steel note; project minima, not delivered properties.",
                        tensile_area_basis="Nominal 1/4-20 thread stress area, not observed root area.",
                        shear_area_basis="Typical 0.189-in circular root assumed at this shear plane, not a part bound.",
                    )
                    output["bolt_actions"].append(
                        {
                            "case": case,
                            "increment_index": index,
                            "load_factor": increment["load_factor"],
                            "block": block,
                            "host": host,
                            "axis_id": axis_id,
                            "lateral_source_name": name,
                            "axial_source_name": axis_id + "/outer-seat-axial-tie",
                            "lateral_source_row_ids": lateral["source_row_ids"],
                            "axial_source_row_ids": axial["source_row_ids"],
                            "lateral_force_on_block_n": endpoint(lateral, block)[1],
                            "lateral_force_rounding_radius_n": lateral[
                                "force_rounding_radius_xyz_n"
                            ],
                            "axial_force_on_block_n": endpoint(axial, block)[1],
                            "axial_force_rounding_radius_n": axial[
                                "force_rounding_radius_xyz_n"
                            ],
                            "lateral_magnitude_n": shear,
                            "axial_tension_n": tension,
                            "member_directions": directions,
                            "direct_steel_reference": steel,
                            "wood_lateral_references": lateral_reference(
                                geometry, directions, shear
                            ),
                            "washer_tension_to_ideal_annulus_reference": tension
                            / (washer["wood_bearing_reference_lbf"] * LBF_N),
                        }
                    )
    rows = output["bolt_actions"]
    assert len(rows) == 336 and len(output["block_balances"]) == 84
    assert len(output["geometry_by_axis"]) == 16
    output["counts"] = {
        "cases": 3,
        "increments_per_case": 7,
        "upper_blocks": 4,
        "physical_bolts": 16,
        "bolt_action_records": len(rows),
        "signed_member_direction_records": 2 * len(rows),
        "complete_block_balance_records": 84,
    }
    output["sampled_maxima_by_block"] = {}
    for block in STATIONS:
        selected = [r for r in rows if r["block"] == block]
        summary = {}
        for key in ("lateral_magnitude_n", "axial_tension_n"):
            peak = max(selected, key=lambda r: r[key])
            summary[key] = {
                "value": peak[key],
                "case": peak["case"],
                "load_factor": peak["load_factor"],
                "axis_id": peak["axis_id"],
            }
        peak = max(
            selected,
            key=lambda r: r["wood_lateral_references"]["nominal_D_bearing_root_yield"][
                "demand_to_unadjusted_reference"
            ],
        )
        summary["largest_unadopted_lateral_reference_ratio"] = {
            "value": peak["wood_lateral_references"]["nominal_D_bearing_root_yield"][
                "demand_to_unadjusted_reference"
            ],
            "case": peak["case"],
            "load_factor": peak["load_factor"],
            "axis_id": peak["axis_id"],
        }
        output["sampled_maxima_by_block"][block] = summary
    output["pure_direction_geometry_comparisons"] = {
        "nominal_bolt_diameter_mm": 6.35,
        "conditional_softwood_parallel_tension_7D_mm": 44.45,
        "conditional_perpendicular_loaded_edge_4D_mm": 25.4,
        "end_component_shorter_than_7D": [],
        "edge_component_shorter_than_4D": [],
        "applicability": "These compare signed component directions with pure-direction thresholds only. They are not adopted criteria, an oblique-load interpretation or an applied C_delta.",
    }
    compare = output["pure_direction_geometry_comparisons"]
    for row in rows:
        for role, d in row["member_directions"].items():
            for kind, key, threshold in (
                ("grain_end_direction", "end_component_shorter_than_7D", 44.45),
                ("cross_grain_edge_direction", "edge_component_shorter_than_4D", 25.4),
            ):
                distance = d[kind]["distance_to_loaded_outer_boundary_mm"]
                if distance is not None and distance < threshold:
                    compare[key].append(
                        {
                            "case": row["case"],
                            "load_factor": row["load_factor"],
                            "axis_id": row["axis_id"],
                            "member_role": role,
                            "member": output["geometry_by_axis"][row["axis_id"]][
                                "members"
                            ][role]["member"],
                            "loaded_boundary_distance_mm": distance,
                            "signed_grain_component_n": d[
                                "force_parallel_to_grain_signed_n"
                            ],
                            "signed_cross_grain_component_n": d[
                                "force_cross_grain_signed_on_frame_axis_n"
                            ],
                        }
                    )
    return output


def csv_text(report):
    stream = io.StringIO(newline="")
    fields = [
        "case",
        "load_factor",
        "block",
        "axis_id",
        "lateral_n",
        "tension_n",
        "block_grain_angle_deg",
        "host_grain_angle_deg",
        "nominal_Fe_root_yield_reference_n",
        "demand_to_unadjusted_reference",
        "steel_tension_reference_ratio",
        "steel_root_shear_reference_ratio",
    ]
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    for row in report["bolt_actions"]:
        ref = row["wood_lateral_references"]["nominal_D_bearing_root_yield"]
        writer.writerow(
            dict(
                zip(
                    fields,
                    [
                        row["case"],
                        row["load_factor"],
                        row["block"],
                        row["axis_id"],
                        row["lateral_magnitude_n"],
                        row["axial_tension_n"],
                        row["member_directions"]["block"][
                            "unsigned_load_to_grain_degrees"
                        ],
                        row["member_directions"]["host"][
                            "unsigned_load_to_grain_degrees"
                        ],
                        ref["reference_lateral_n"],
                        ref["demand_to_unadjusted_reference"],
                        row["direct_steel_reference"][
                            "tension_first_yield_utilization"
                        ],
                        row["direct_steel_reference"]["shear_first_yield_utilization"],
                    ],
                    strict=True,
                )
            )
        )
    return stream.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = produce()
    files = {
        "upper-joints.json": json.dumps(report, indent=2, sort_keys=True) + "\n",
        "bolt-actions.csv": csv_text(report),
    }
    for name, text in files.items():
        if args.verify:
            assert (HERE / name).read_text() == text, (
                name + " differs from frozen replay"
            )
        else:
            (HERE / name).write_text(text)
    print(
        json.dumps(
            {
                "verified": args.verify,
                "counts": report["counts"],
                "sampled_maxima_by_block": report["sampled_maxima_by_block"],
            },
            indent=2,
        )
    )
