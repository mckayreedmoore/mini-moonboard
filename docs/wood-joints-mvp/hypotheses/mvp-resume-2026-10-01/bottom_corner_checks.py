"""Join finished bottom-cleat geometry to one saved six-joint response.

Reuse the member action extraction and existing NDS component arithmetic.
No native solve, frame solve, stock change or complete-joint pass is implied.
"""

import argparse
import csv
import json
import math
from pathlib import Path

import corner_checks as checks
import frame_state_contract as frame_contract
import numpy as np
import remaining_joint_screen as remaining

HERE, ROOT = checks.HERE, checks.ROOT
local, accounting = checks.local, checks.accounting
sha, read, require = checks.sha, checks.read, checks.require
HOSTS = {
    "bottom_outer_left_cleat": ("base_rail_bottom_left", "base_side_left"),
    "bottom_outer_right_cleat": ("base_rail_bottom_right", "base_side_right"),
}


def pair_action(group, actions, datum, geometry):
    """Keep pure-couple and zero-force pairs without inventing a load direction."""
    bolts = []
    for axis in group["axis_ids"]:
        components = [
            a
            for a in actions
            if a["role"] == accounting.LATERAL
            and a["source_id"].rsplit("/", 1)[0] == axis
        ]
        require(len(components) == 2, "missing paired lateral components")
        point = np.array(components[0]["point_mm"])
        value = accounting.wrench(components, point)
        bolts.append(
            {
                "axis_id": axis,
                "point_mm": point.tolist(),
                "force_n": value[:3].tolist(),
                "force_resultant_n": float(np.linalg.norm(value[:3])),
                "free_moment_nmm": value[3:].tolist(),
            }
        )
    resultant = np.sum([b["force_n"] for b in bolts], axis=0)
    if np.linalg.norm(resultant) > 1e-8 and all(
        b["force_resultant_n"] > 1e-8 for b in bolts
    ):
        return accounting.pair_action(group, actions, datum, geometry)
    sources = [a for a in actions if a["role"] == accounting.LATERAL]
    center = np.mean([b["point_mm"] for b in bolts], axis=0)
    return {
        "individual_bolts": bolts,
        "lateral_wrench_about_body_datum": accounting.record_wrench(
            accounting.wrench(sources, datum), geometry
        ),
        "lateral_moment_about_pair_center_xyz_nmm": accounting.wrench(sources, center)[
            3:
        ].tolist(),
        "pair_resultant_n": float(np.linalg.norm(resultant)),
        "sum_individual_magnitudes_n": sum(b["force_resultant_n"] for b in bolts),
        "pitch_along_resultant_mm": None,
        "pitch_transverse_to_resultant_mm": None,
        "angle_between_signed_bolt_forces_degrees": None,
        "staggered_row_merger_geometry_trigger": None,
        "direction_status": "zero_resultant_or_zero_individual_direction_undefined",
        "equal_sharing_assumed": False,
    }


def saved_actions(body, case, record, arrays):
    """Restore exact point forces/free couples already extracted by member_screen."""
    values = arrays[case + "__" + body + "__point_force_free_couple_xyz"]
    positions = arrays[body + "__point_xyz_mm"]
    stations = arrays[body + "__point_stations_mm"]
    footprints = arrays[body + "__point_footprints_mm"]
    rows = arrays[body + "__point_rows"]
    return [
        {
            "row": int(row),
            "source_id": identity,
            "role": role,
            "other_body": other,
            "point_mm": point.tolist(),
            "force_n": value[:3].tolist(),
            "free_moment_nmm": value[3:].tolist(),
            "station_mm": float(station),
            "footprint_mm": footprint.tolist(),
        }
        for identity, role, other, point, value, station, footprint, row in zip(
            record["point_action_ids"],
            record["point_action_roles"],
            record["point_action_other_bodies"],
            positions,
            values,
            stations,
            footprints,
            rows,
            strict=True,
        )
    ]


def run(clearance, member_dir, lateral_dir, output):
    require(not output.exists(), "preserve existing component evidence")
    comparison = read(clearance / "comparison.json")
    force_scope = frame_contract.force_state_scope(comparison)
    member_report = read(member_dir / "member-results.json")
    lateral_report = read(lateral_dir / "screen.json")
    require(
        lateral_report["source_comparison_sha256"] == sha(clearance / "comparison.json")
        and lateral_report["source_response_sha256"] == comparison["response_sha256"],
        "lateral and joint responses differ",
    )
    require(
        sha(lateral_dir / "bolt-states.csv")
        == lateral_report["output_sha256"]["bolt-states.csv"],
        "changed lateral CSV",
    )
    member_geometry = read(member_dir / "geometry.json")
    require(
        member_report["clearance_input_directory"] == str(clearance.relative_to(ROOT)),
        "member and joint responses differ",
    )
    pins = {ROOT / p: h for p, h in member_report["source_sha256"].items()}
    pins.update({member_dir / p: h for p, h in member_report["output_sha256"].items()})
    pins.update(local.PINS)
    pins[remaining.SUPPORT] = remaining.PINS[remaining.SUPPORT]
    for path in (
        member_dir / "member-results.json",
        clearance / "comparison.json",
        clearance / "response.npz",
        lateral_dir / "bolt-states.csv",
        lateral_dir / "screen.json",
        Path(__file__),
        Path(frame_contract.__file__),
        Path(checks.__file__),
        Path(remaining.lateral.__file__),
        remaining.lateral.HELPER,
        Path(local.__file__),
        Path(accounting.__file__),
    ):
        pins[path] = sha(path)
    require(
        sha(clearance / "response.npz") == comparison["response_sha256"],
        "changed frame response",
    )
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    inputs = read(local.INPUTS)
    members = {
        m["member_id"]: m["reduced_geometry_descriptor"] for m in inputs["members"]
    }
    bolts = {
        b["axis_id"]: b for b in inputs["connections"] if b["kind"] == "candidate_bolt"
    }
    groups = []
    for block, hosts in HOSTS.items():
        for host in hosts:
            axes = sorted(
                a
                for a, b in bolts.items()
                if set(b["receiver_member_ids"]) == {block, host}
            )
            require(len(axes) == 2, "bottom joint does not have two bolts per face")
            groups.append({"block": block, "host": host, "axis_ids": axes})
    paths = [p for g in groups for p in local.tearout_geometry(g, bolts, members)]
    pins.update(
        {ROOT / members[b]["step_path"]: members[b]["step_sha256"] for b in HOSTS}
    )
    path_for = {(p["axis_id"], p["grain_direction_sign"]): p for p in paths}
    seats = [
        s
        for s in read(remaining.SUPPORT)["seats"]
        if s["axis_id"] in {a for g in groups for a in g["axis_ids"]}
    ]
    require(
        len(seats) == 16 and all(s["geometry_screen_pass"] for s in seats),
        "bottom washer support incomplete",
    )
    seat_for, changed_seat_checks, changed_shapes = {}, [], {}
    for seat in seats:
        body = seat["member"]
        path = ROOT / members[body]["step_path"]
        require(
            read(remaining.SUPPORT)["finished_step_pins"][body]["sha256"]
            == members[body]["step_sha256"],
            "seat STEP identity differs",
        )
        pins[path] = members[body]["step_sha256"]
        current_path = HERE / "top-corner-correction" / (body + ".step")
        if current_path.exists():
            pins[current_path] = sha(current_path)
            if body not in changed_shapes:
                changed_shapes[body] = checks.cq.importers.importStep(
                    str(current_path)
                ).val()
            inward = local.unit(bolts[seat["axis_id"]]["axis_xyz"]) * (
                1 if seat["role"] == "head" else -1
            )
            plane = checks.cq.Plane(
                origin=tuple(seat["point_xyz_mm"]),
                xDir=tuple(local.unit(members[body]["axis"])),
                normal=tuple(inward),
            )
            fractions = []
            for depth in (0.01, 0.05, 0.1):
                ring = (
                    checks.cq.Workplane(plane)
                    .circle(seat["sweep_radius_mm"])
                    .circle(seat["bore_radius_mm"])
                    .extrude(depth)
                    .val()
                )
                fraction = ring.intersect(changed_shapes[body]).Volume() / ring.Volume()
                require(
                    abs(fraction - 1) < 1e-6,
                    "changed side host loses bottom washer sweep support",
                )
                fractions.append(
                    {
                        "depth_mm": depth,
                        "outside_bore_sweep_supported_fraction": fraction,
                    }
                )
            changed_seat_checks.append(
                {
                    "axis_id": seat["axis_id"],
                    "member": body,
                    "role": seat["role"],
                    "current_STEP_sha256": pins[current_path],
                    "sweep_radius_mm": seat["sweep_radius_mm"],
                    "measurements": fractions,
                }
            )
        areas = [
            r["supported_area_mm2"]
            for r in seat["conditional_hole_only_areas"]
            if r["mode"] == "combined"
        ]
        require(
            areas
            and all(
                r["hole_only_applicable"] for r in seat["conditional_hole_only_areas"]
            ),
            "unsupported displaced annulus",
        )
        seat_for.setdefault(seat["axis_id"], []).append(min(areas))
    with (lateral_dir / "bolt-states.csv").open(newline="") as stream:
        lateral_for = {(r["case_id"], r["axis_id"]): r for r in csv.DictReader(stream)}
    material = read(accounting.MATERIALS)["conditional_DF_L_No2_base_row"][
        "base_properties"
    ]
    fv, fc = (
        material["Fv_parallel"] * local.PSI_MPA,
        material["Fc_perpendicular"] * local.PSI_MPA,
    )
    factors, comparators = {}, []
    for group in groups:
        block, host = group["block"], group["host"]
        geom = local.geometry_comparators(group, bolts, members)
        comparators.extend(geom)
        cdelta = min(r["conservative_end_Cdelta_scenario"] for r in geom)
        pitch = np.linalg.norm(
            np.array(bolts[group["axis_ids"][1]]["source_point_xyz_mm"])
            - bolts[group["axis_ids"][0]]["source_point_xyz_mm"]
        )
        rail = host.startswith("base_rail_")
        ea = material["E"] * (88.9**2 if rail else 88.9 * 139.7) / 25.4**2
        equivalent_ea = material["E"] * (38.1 if rail else 88.9) * (3 * 6.35) / 25.4**2
        cg = local.group_factor(2, pitch / 25.4, ea, equivalent_ea)
        factors[(block, host)] = {
            "Cg_component_scenario": cg,
            "Cdelta_end_scenario": cdelta,
            "combined_multiplier": cg * cdelta,
            "pitch_mm": float(pitch),
            "equivalent_single_row_width_mm": 3 * 6.35,
        }
    states, interfaces, splitting, balances = [], [], [], []
    records = member_geometry["members"]
    source_rows = read(HERE / "corner-frame-attempt01/row-identities.json")
    contact = read(accounting.MODEL)["contact_cell_ownership"]
    cell_area = {
        c["name"]: c["area_mm2"] for c in contact if c["kind"] == accounting.CONTACT
    }
    bodies = set(HOSTS) | {h for hosts in HOSTS.values() for h in hosts}
    with (
        np.load(member_dir / "action-section-arrays.npz", allow_pickle=False) as arrays,
        np.load(clearance / "response.npz", allow_pickle=False) as response,
    ):
        for case in (s["case_id"] for s in comparison["states"] if s["gap_scale"] == 1):
            actions = {b: saved_actions(b, case, records[b], arrays) for b in bodies}
            force = response[case + "_gap_raw_force_n"]
            for body in bodies:
                center = np.mean(
                    arrays[body + "__point_xyz_mm"][
                        np.array(records[body]["point_action_roles"])
                        == "discrete_body_load"
                    ],
                    axis=0,
                )
                closure = accounting.wrench(actions[body], center)
                require(
                    np.max(abs(closure[:3])) < 0.1 and np.max(abs(closure[3:])) < 2,
                    "saved body imbalance",
                )
                balances.append(
                    {
                        "case_id": case,
                        "body": body,
                        "closure_xyz_n_nmm": closure.tolist(),
                    }
                )
            for group in groups:
                block, host = group["block"], group["host"]
                target = [a for a in actions[block] if a["other_body"] == host]
                datum = (np.array(members[block]["start"]) + members[block]["end"]) / 2
                contact_rows = [a for a in target if a["role"] == accounting.CONTACT]
                pressures = [
                    max(0, float(force[a["row"]])) / cell_area[a["source_id"]]
                    for a in contact_rows
                ]
                interfaces.append(
                    {
                        "case_id": case,
                        "block": block,
                        "host": host,
                        "wrench_on_cleat_xyz_n_nmm": accounting.wrench(
                            target, datum
                        ).tolist(),
                        "signed_bolt_pair": pair_action(
                            group, target, datum, records[block]["geometry"]
                        ),
                        "contact_cell_pressures_mpa": pressures,
                        "maximum_cell_pressure_over_Fc_perp": max(pressures) / fc,
                    }
                )
                for axis in group["axis_ids"]:
                    row = lateral_for[(case, axis)]
                    vector = np.array(
                        [float(row["shear_" + a + "_n"]) for a in ("x", "y", "z")]
                    )
                    components = [
                        source_rows[int(row[k])]
                        for k in ("component_1_row", "component_2_row")
                    ]
                    require(
                        all(r["row_id"].rsplit("/", 1)[0] == axis for r in components),
                        "lateral row axis differs",
                    )
                    expected = np.array(
                        [force[r["row"]] for r in components]
                    ) @ np.array(
                        [r["ownership"]["direction_global_xyz"] for r in components]
                    )
                    require(
                        np.max(abs(expected - vector)) < 1e-8,
                        "lateral CSV comes from another response",
                    )
                    if row["first_body"] != block:
                        vector = -vector
                    require(
                        {row["first_body"], row["second_body"]} == {block, host},
                        "wrong lateral receiver",
                    )
                    shear, tension = (
                        float(row["shear_resultant_n"]),
                        float(row["outer_tie_signed_n"]),
                    )
                    tie = source_rows[int(row["tie_row"])]
                    require(
                        tie["row_id"] == axis + "/outer-seat-axial-tie"
                        and abs(force[tie["row"]] - tension) < 1e-8,
                        "axial CSV comes from another response",
                    )
                    parallel = float(vector @ local.unit(members[block]["axis"]))
                    path = path_for[(axis, 1 if parallel >= 0 else -1)]
                    multiplier = factors[(block, host)]["combined_multiplier"]
                    pressure = tension / min(seat_for[axis])
                    axial = tension / (0.0318 * 25.4**2)
                    tau = 4 * shear / (3 * math.pi * 6.35**2 / 4)
                    remaining_yield = (
                        math.sqrt((92000 * local.PSI_MPA) ** 2 - 3 * tau**2) - axial
                    )
                    require(
                        remaining_yield > 0, "direct stress exhausts conditional yield"
                    )
                    reduced = remaining.lateral.reference(
                        [
                            float(row[k])
                            for k in (
                                "first_bearing_length_mm",
                                "second_bearing_length_mm",
                            )
                        ],
                        [
                            float(row[k])
                            for k in (
                                "first_load_to_grain_deg",
                                "second_load_to_grain_deg",
                            )
                        ],
                        remaining_yield / local.PSI_MPA,
                    )
                    reduced_reference_n = (
                        reduced["reference_lateral_lbf"] * remaining.lateral.N_PER_LBF
                    )
                    require(
                        reduced_reference_n <= float(row["reference_92ksi_n"]) + 1e-8,
                        "steel reserve unexpectedly raises the source reference",
                    )
                    ro, ri, thick = 0.749 * 25.4 / 2, 5.0, 0.051 * 25.4
                    strip = (
                        6
                        * pressure
                        / ri
                        * ((ro**3 - ri**3) / 3 - ri * (ro**2 - ri**2) / 2)
                        / thick**2
                    )
                    states.append(
                        {
                            "case_id": case,
                            "block": block,
                            "host": host,
                            "axis_id": axis,
                            "shear_xyz_on_cleat_n": vector.tolist(),
                            "shear_n": shear,
                            "tension_n": tension,
                            "component_factors": factors[(block, host)],
                            "ratio_45ksi_adjusted_component_scenario": float(
                                row["ratio_45ksi"]
                            )
                            / multiplier,
                            "ratio_92ksi_adjusted_component_scenario": float(
                                row["ratio_92ksi"]
                            )
                            / multiplier,
                            "same_state_92ksi_steel_reserve_ratio": shear
                            / (reduced_reference_n * multiplier),
                            "cleat_parallel_force_over_finished_tangent_path": abs(
                                parallel
                            )
                            / (fv * path["minimum_finished_one_plane_area_mm2"]),
                            "minimum_displaced_washer_area_mm2": min(seat_for[axis]),
                            "washer_mean_pressure_mpa": pressure,
                            "washer_mean_pressure_over_Fc_perp": pressure / fc,
                            "washer_required_radial_strip_stress_mpa": strip,
                        }
                    )
                host_actions = [a for a in actions[host] if a["other_body"] == block]
                geometry = records[host]["geometry"]
                length = np.linalg.norm(np.array(geometry["end"]) - geometry["start"])
                cuts = [
                    accounting.host_cut(actions[host], station, geometry, before)
                    for station, before in (
                        (
                            max(0, min(a["footprint_mm"][0] for a in host_actions) - 1),
                            True,
                        ),
                        (
                            min(
                                float(length),
                                max(a["footprint_mm"][1] for a in host_actions) + 1,
                            ),
                            False,
                        ),
                    )
                ]
                demand = max(
                    abs(c[s]["force_global_N_n"])
                    for c in cuts
                    for s in ("internal_on_positive_half", "internal_on_negative_half")
                )
                h, b = 139.7, (88.9 if host.startswith("base_side_") else 38.1)
                center = (np.array(geometry["start"]) + geometry["end"]) / 2
                coordinates = [
                    float(
                        accounting.N_AXIS
                        @ (np.array(bolts[a]["source_point_xyz_mm"]) - center)
                    )
                    for a in group["axis_ids"]
                ]
                distances = [h / 2 - min(coordinates), h / 2 + max(coordinates)]
                require(
                    all(0 < he < h for he in distances),
                    "splitting geometry outside scenario",
                )
                refs = [14 * b * math.sqrt(he / (1 - he / h)) for he in distances]
                splitting.append(
                    {
                        "case_id": case,
                        "block": block,
                        "host": host,
                        "signed_section_cuts": cuts,
                        "both_loaded_edge_he_mm": distances,
                        "both_F90_characteristic_n": refs,
                        "whole_section_N_shear_over_smaller_characteristic": demand
                        / min(refs),
                    }
                )
    require(
        len(states) == 48
        and len(paths) == 16
        and len(interfaces) == 24
        and len(balances) == 36,
        "incomplete bottom joint coverage",
    )
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    report = {
        "schema": "bottom_outer_same_state_component_references/v1",
        "source_force_state_scope": force_scope,
        "source_sha256": {str(p): h for p, h in pins.items()},
        "counts": {
            "bolt_states": len(states),
            "finished_tangent_paths": len(paths),
            "exact_tangent_planes": 2 * len(paths),
            "washer_seats": len(seats),
            "interface_states": len(interfaces),
            "body_balances": len(balances),
        },
        "states": states,
        "finished_paths": paths,
        "outer_geometry_comparators": comparators,
        "washer_geometry": seats,
        "changed_side_host_washer_sweep_rechecks": changed_seat_checks,
        "interfaces": interfaces,
        "host_splitting": splitting,
        "whole_body_balances": balances,
        "limits": [
            "The selected saved frame retains conditional Hillman laws, dry DF-L No.2 and no-slip floor branches. Its bound source schema and force-state scope define which clearances and seating freedoms apply.",
            "Component Cg uses two-bolt 33mm pitch and a declared 3D single-row equivalent width at the receiver loaded across grain. Cdelta uses minimum finished rectangular grain-end distance. These are conservative component scenarios, not acceptance of the full oblique group.",
            "Exact finished bore-tangent paths carry signed grain-parallel forces only; no capacity for other cracks or combined 3D splitting is inferred.",
            "EN1995 Eq8.4 comparisons use characteristic values and complete same-state host-section N shear. Design conversion and combined local joint effects remain separate.",
            "Washer pressure uses the smallest saved offset annulus. The four bottom washer sweeps on changed side-host STEP copies are rechecked at all three source probe depths. Radial strip stress assumes a 10mm flat bearing circle; washer yield/head-nut footprint are not qualified.",
            "The steel reserve is the parent's explicit axial/parabolic-shear scenario, not an adopted NDS combined-load equation.",
            "Finished disconnected section areas are geometry evidence; no common strain field or force share is assigned.",
        ],
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": False,
        "physical_release": False,
    }
    output.mkdir()
    (output / "component-results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    for block in HOSTS:
        subset = [s for s in states if s["block"] == block]
        print(
            block,
            {
                key: max(s[key] for s in subset)
                for key in (
                    "ratio_45ksi_adjusted_component_scenario",
                    "ratio_92ksi_adjusted_component_scenario",
                    "same_state_92ksi_steel_reserve_ratio",
                    "cleat_parallel_force_over_finished_tangent_path",
                    "washer_mean_pressure_over_Fc_perp",
                    "washer_required_radial_strip_stress_mpa",
                )
            },
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("clearance", "members", "lateral", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    run(
        args.clearance.resolve(),
        args.members.resolve(),
        args.lateral.resolve(),
        args.output.resolve(),
    )
