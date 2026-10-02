"""Six-case local top-corner references with exact declared tear-out planes.

Keep component checks and material hypotheses explicit. No native solver,
geometry change, complete-joint acceptance or independent review is invoked.
"""

import csv
import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
import top_corner_actions as actions_method

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses"
INPUTS = BASE / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
SEATS = BASE / "upper-block-strength-2026-10-01/seats.json"
FASTENERS = BASE / "hardware-material-specification-2026-09-30/fastener-inputs.json"
SOURCE_CACHE = BASE / "upper-block-strength-2026-10-01/source-cache"
PINS = {
    INPUTS: "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    SEATS: "4463f581490842095224afefd0b355428f82668f039b2e6035dfe4ec879c96c1",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    SOURCE_CACHE
    / "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
    SOURCE_CACHE
    / "chapter11-2024-awc-20260911.pdf": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
    SOURCE_CACHE
    / "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
}
sha = actions_method.sha
require = actions_method.require
read = actions_method.read
PSI_MPA = 0.006894757293168361


def unit(vector):
    vector = np.array(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def shear_plane(shape, point, grain, transverse, offset, lo, hi):
    """Actual STEP wood area on one declared tangent shear plane and interval."""
    plane = cq.Plane(
        origin=tuple(point + offset * transverse),
        xDir=tuple(grain),
        normal=tuple(transverse),
    )
    section = cq.Workplane(plane).add(shape).section().val()
    # Wide mask in the bolt direction; only its along-grain interval clips
    # the source section. Two mm depth straddles the section plane.
    mask = cq.Workplane(plane).center((lo + hi) / 2, 0).box(hi - lo, 2000, 2).val()
    clipped = section.intersect(mask)
    faces = clipped.Faces()
    require(clipped.isValid() and faces, "invalid or empty shear plane")
    return {
        "plane_origin_mm": list(plane.origin.toTuple()),
        "plane_normal_xyz": transverse.tolist(),
        "bore_tangent_offset_mm": offset,
        "grain_interval_relative_to_bolt_mm": [lo, hi],
        "wood_area_mm2": sum(f.Area() for f in faces),
        "material_face_count": len(faces),
    }


def tearout_geometry(group, bolts, members):
    block = group["block"]
    descriptor = members[block]
    path = ROOT / descriptor["step_path"]
    require(sha(path) == descriptor["step_sha256"], "changed cleat STEP")
    PINS[path] = descriptor["step_sha256"]
    shape = cq.importers.importStep(str(path)).val()
    require(shape.isValid() and len(shape.Solids()) == 1, "invalid cleat solid")
    grain = unit(descriptor["axis"])
    start = np.array(descriptor["start"])
    length = float(np.linalg.norm(np.array(descriptor["end"]) - start))
    records = []
    for axis in group["axis_ids"]:
        bolt = bolts[axis]
        point = np.array(bolt["source_point_xyz_mm"])
        axis_direction = unit(bolt["axis_xyz"])
        require(abs(grain @ axis_direction) < 1e-8, "end-grain bolt outside method")
        transverse = unit(np.cross(grain, axis_direction))
        clearance = next(
            r for r in bolt["receiver_clearance_geometry"] if r["receiver_id"] == block
        )
        radius = clearance["unique_bore_radius_mm"]
        require(
            clearance["receiver_step_sha256"] == descriptor["step_sha256"],
            "bore STEP mismatch",
        )
        station = float(grain @ (point - start))
        bearing = next(
            r
            for r in bolt["source_record"]["geometry"]["wood_receiver_intervals"]
            if r["receiver_id"] == block
        )
        spans = bearing["current_shaft_intersection_solid_intervals_from_underhead_mm"]
        require(len(spans) == 1, "noncontiguous bearing length")
        thickness = spans[0][1] - spans[0][0]
        for direction in (-1, 1):
            distance = station if direction < 0 else length - station
            boundary = "grain_end"
            for other in group["axis_ids"]:
                if other == axis:
                    continue
                delta = np.array(bolts[other]["source_point_xyz_mm"]) - point
                if (
                    abs(transverse @ delta) < 1e-6
                    and direction * float(grain @ delta) > 1e-6
                ):
                    pitch = abs(float(grain @ delta))
                    if pitch < distance:
                        distance, boundary = pitch, other
            lo, hi = (-distance, 0.0) if direction < 0 else (0.0, distance)
            planes = [
                shear_plane(shape, point, grain, transverse, s * radius, lo, hi)
                for s in (-1, 1)
            ]
            minimum = min(p["wood_area_mm2"] for p in planes)
            gross = thickness * distance
            require(0 < minimum <= gross + 1e-5, "impossible tear-out area")
            records.append(
                {
                    "axis_id": axis,
                    "block": block,
                    "grain_direction_sign": direction,
                    "bolt_grain_station_mm": station,
                    "critical_distance_mm": distance,
                    "interval_boundary": boundary,
                    "bearing_thickness_mm": thickness,
                    "bore_diameter_mm": radius * 2,
                    "gross_one_plane_area_mm2": gross,
                    "minimum_finished_one_plane_area_mm2": minimum,
                    "removed_area_on_minimum_plane_mm2": gross - minimum,
                    "two_declared_shear_planes": planes,
                    "formula": "n*Fv*min(one-plane areas); triangular stress, two lines, no additional factor of two",
                    "scope": "Declared bore-tangent paths toward the end or next bolt in the same grain row. Other crack paths, oblique loading and interactions are separate.",
                }
            )
    return records


def group_factor(count, pitch_in, main_ea, side_ea):
    """NDS-2024 Eq. 11.3-1 arithmetic for explicitly declared component rows."""
    gamma = 180000 * 0.25**1.5
    re = min(main_ea, side_ea) / max(main_ea, side_ea)
    u = 1 + gamma * pitch_in / 2 * (1 / main_ea + 1 / side_ea)
    m = 1 / (u + math.sqrt(u * u - 1))
    value = (
        m
        * (1 - m ** (2 * count))
        / (count * ((1 + re * m**count) * (1 + m) - 1 + m ** (2 * count)))
        * (1 + re)
        / (1 - m)
    )
    require(0 < value <= 1 + 1e-10, "group factor outside physical domain")
    return min(1.0, value)


def geometry_comparators(group, bolts, members):
    records = []
    for member in (group["block"], group["host"]):
        geom = members[member]
        grain = unit(geom["axis"])
        u, v = unit(geom["section_u"]), unit(geom["section_v"])
        start = np.array(geom["start"])
        length = np.linalg.norm(np.array(geom["end"]) - start)
        for axis in group["axis_ids"]:
            point = np.array(bolts[axis]["source_point_xyz_mm"])
            transverse = unit(np.cross(grain, unit(bolts[axis]["axis_xyz"])))
            station = float(grain @ (point - start))
            width = (
                abs(transverse @ u) * geom["width_mm"]
                + abs(transverse @ v) * geom["depth_mm"]
            )
            q = float(transverse @ (point - start))
            require(
                abs(q) < width / 2 and 0 < station < length,
                "bolt center outside member",
            )
            ends = [station, float(length - station)]
            edges = [width / 2 + q, width / 2 - q]
            require(
                min(ends) >= 3.5 * 6.35,
                "end below conservative softwood tension minimum",
            )
            require(
                min(edges) >= 4 * 6.35,
                "edge below full perpendicular loaded-edge scenario",
            )
            records.append(
                {
                    "member": member,
                    "axis_id": axis,
                    "grain_end_distances_mm": ends,
                    "outer_face_edge_distances_mm": edges,
                    "conservative_end_Cdelta_scenario": min(
                        1.0, min(ends) / (7 * 6.35)
                    ),
                    "geometry_basis": "Pinned rectangular external stock faces. Neighboring holes are retained in the separate finished shear-plane query.",
                }
            )
    return records


def main():
    for path, digest in PINS.items():
        require(sha(path) == digest, "changed source: " + str(path))
    actions_path = HERE / "top-corner-actions.json"
    actions = read(actions_path)
    for relative, digest in actions["source_sha256"].items():
        require(sha(ROOT / relative) == digest, "changed action source")
    require(
        actions["static_response_sha256"] == sha(HERE / "simple-frame-response.npz"),
        "changed response",
    )
    require(
        actions["producer_sha256"] == sha(HERE / "top_corner_actions.py"),
        "changed action producer",
    )
    inputs, inventory, seat_report = (
        read(INPUTS),
        read(actions_method.GEOMETRY),
        read(SEATS),
    )
    members = {
        m["member_id"]: m["reduced_geometry_descriptor"] for m in inputs["members"]
    }
    bolts = {
        b["axis_id"]: b for b in inputs["connections"] if b["kind"] == "candidate_bolt"
    }
    groups = [
        g
        for g in inventory["two_bolt_groups"]
        if g["block"] in actions_method.BLOCK_HOSTS
    ]
    require(
        len(groups) == 4 and len(actions["cases"]) == 6, "incomplete corner coverage"
    )
    material = read(actions_method.MATERIALS)["conditional_DF_L_No2_base_row"][
        "base_properties"
    ]
    lateral_summary = read(HERE / "simple-lateral-reference-summary.json")
    lateral_csv = HERE / "simple-lateral-references.csv"
    require(
        sha(lateral_csv) == lateral_summary["output_csv_sha256"],
        "changed lateral references",
    )
    demand_summary = read(HERE / "simple-bolt-demand-summary.json")
    require(
        demand_summary["source_response_sha256"] == actions["static_response_sha256"],
        "mixed response versions",
    )
    require(
        lateral_summary["source_demands_sha256"] == demand_summary["csv_sha256"],
        "mixed bolt-demand versions",
    )
    with lateral_csv.open(newline="") as stream:
        lateral_for = {(r["case_id"], r["axis_id"]): r for r in csv.DictReader(stream)}
    fv, fc = material["Fv_parallel"] * PSI_MPA, material["Fc_perpendicular"] * PSI_MPA
    paths, comparators, factors = [], [], []
    for group in groups:
        paths.extend(tearout_geometry(group, bolts, members))
        comparison = geometry_comparators(group, bolts, members)
        comparators.extend(comparison)
        is_rail = group["host"] == "base_rail_top"
        cleat = members[group["block"]]
        em = material["E"] * cleat["width_mm"] * cleat["depth_mm"] / 25.4**2
        # Pure N component: cleat parallel to grain; rail perpendicular.
        # A single row across the rail grain uses its minimum parallel-grain
        # bolt spacing (3D in Table 12.5.1B), not the actual 33 mm pitch
        # across its grain. Also retain the 4D full-Cdelta-width scenario.
        equivalent_width = 3 * 6.35
        es = material["E"] * 38.1 * equivalent_width / 25.4**2
        cg = group_factor(2, 33 / 25.4, em, es) if is_rail else 1.0
        require(
            abs(group_factor(1, 33 / 25.4, em, es) - 1) < 1e-10,
            "singleton equation identity",
        )
        factors.append(
            {
                "group_id": group["group_id"],
                "block": group["block"],
                "host": group["host"],
                "conservative_end_Cdelta_scenario": min(
                    r["conservative_end_Cdelta_scenario"] for r in comparison
                ),
                "pure_N_component_Cg_scenario": cg,
                "rail_single_row_equivalent_width_parallel_to_grain_mm": equivalent_width
                if is_rail
                else None,
                "rail_single_row_equivalent_area_mm2": 38.1 * equivalent_width
                if is_rail
                else None,
                "pure_N_Cg_with_full_Cdelta_4D_width_scenario": group_factor(
                    2, 33 / 25.4, em, material["E"] * 38.1 * (4 * 6.35) / 25.4**2
                )
                if is_rail
                else None,
                "other_transverse_component_Cg_singleton_scenario": 1.0,
                "application": "Component/direction scenarios only; not an adopted factor for the full oblique coupled group.",
            }
        )
    path_for = {(p["axis_id"], p["grain_direction_sign"]): p for p in paths}
    factor_for = {(f["block"], f["host"]): f for f in factors}
    seats_for = {}
    axes = {a for g in groups for a in g["axis_ids"]}
    for seat in seat_report["geometry_seats"]:
        if seat["axis_id"] in axes:
            seats_for.setdefault(seat["axis_id"], []).append(seat)
    require(
        len(seats_for) == 8 and all(len(s) == 2 for s in seats_for.values()),
        "missing two-seat support",
    )
    annulus = next(
        a
        for a in seat_report["washer_annulus_scenarios"]
        if a["scenario_id"] == "catalog_minimum_area"
    )
    nut_dimensions = read(FASTENERS)["dimension_inputs"]["nut"]
    thread_area = nut_dimensions["tensile_stress_area_in2"] * 25.4**2
    shank_area = math.pi * 6.35**2 / 4
    states, row_groups = [], []
    for case in actions["cases"]:
        for interface in case["interfaces"]:
            block = interface["block"]
            grain = unit(members[block]["axis"])
            group_rows = []
            for bolt in interface["lateral_bolt_pair"]["individual_bolts"]:
                axis = bolt["axis_id"]
                parallel = float(np.array(bolt["force_n"]) @ grain)
                direction = 1 if parallel >= 0 else -1
                path = path_for[(axis, direction)]
                reference = fv * path["minimum_finished_one_plane_area_mm2"]
                ties = [
                    a
                    for a in interface["individual_source_actions_on_block"]
                    if a["role"] == "physical_bolt_outer_seat_tension"
                    and a["source_id"].rsplit("/", 1)[0] == axis
                ]
                require(len(ties) == 1, "missing axial tie")
                tension = max(0.0, ties[0]["scalar_row_force_n"])
                for seat in seats_for[axis]:
                    require(
                        seat["grain_relation"] == "perpendicular_to_bolt_axis",
                        "washer grain route changed",
                    )
                    require(
                        seat["scenario_support"]["catalog_minimum_area"][
                            "support_status"
                        ]
                        == "full_modeled_support",
                        "partial seat in corner subset",
                    )
                    relative = seat["member_source_geometry"]["finished_step"]
                    require(
                        sha(ROOT / relative)
                        == seat["member_source_geometry"]["finished_step_sha256"],
                        "changed seat STEP",
                    )
                pressure = tension / annulus["annulus_area_mm2"]
                axial_stress = tension / thread_area
                shear_stress = bolt["force_resultant_n"] / shank_area
                record = {
                    "case_id": case["case_id"],
                    "block": block,
                    "host": interface["host"],
                    "axis_id": axis,
                    "parallel_force_n": parallel,
                    "loaded_grain_direction_sign": direction,
                    "declared_finished_single_path_reference_n": reference,
                    "parallel_component_over_path_reference": abs(parallel) / reference,
                    "outer_tie_n": tension,
                    "ideal_minimum_annulus_pressure_mpa": pressure,
                    "ideal_annulus_pressure_over_Fc_perp_reference": pressure / fc,
                    "direct_axial_stress_at_nominal_thread_tensile_area_mpa": axial_stress,
                    "direct_shank_shear_stress_mpa": shear_stress,
                    "direct_von_Mises_proxy_mpa": math.sqrt(
                        axial_stress**2 + 3 * shear_stress**2
                    ),
                    "bolt_bending_moment_included": False,
                }
                factor = factor_for[(block, interface["host"])]
                multiplier = (
                    factor["conservative_end_Cdelta_scenario"]
                    * factor["pure_N_component_Cg_scenario"]
                )
                lateral = lateral_for[(case["case_id"], axis)]
                record["illustrative_Cg_Cdelta_multiplier"] = multiplier
                record["lateral_106ksi_ratio_with_illustrative_factors"] = (
                    float(lateral["ratio_106ksi"]) / multiplier
                )
                record["lateral_45ksi_ratio_with_illustrative_factors"] = (
                    float(lateral["ratio_45ksi"]) / multiplier
                )
                states.append(record)
                group_rows.append(record)
            if interface["host"] == "base_rail_top":
                directions = {r["loaded_grain_direction_sign"] for r in group_rows}
                require(
                    len(directions) == 1, "rail row has opposing parallel components"
                )
                direction = next(iter(directions))
                minimum = min(
                    path_for[(r["axis_id"], direction)][
                        "minimum_finished_one_plane_area_mm2"
                    ]
                    for r in group_rows
                )
                row_groups.append(
                    {
                        "case_id": case["case_id"],
                        "block": block,
                        "bolt_count": 2,
                        "signed_parallel_group_force_n": sum(
                            r["parallel_force_n"] for r in group_rows
                        ),
                        "finished_two_bolt_row_reference_n": 2 * fv * minimum,
                        "parallel_group_over_row_reference": abs(
                            sum(r["parallel_force_n"] for r in group_rows)
                        )
                        / (2 * fv * minimum),
                    }
                )
    for path, digest in PINS.items():
        require(sha(path) == digest, "source changed during calculation")
    csv_path = HERE / "top-corner-local-summary.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(states[0]))
        writer.writeheader()
        writer.writerows(states)
    report = {
        "schema": "simple_static_top_corner_local_references/v1",
        "candidate": actions["candidate"],
        "revision_id": actions["revision_id"],
        "action_report_sha256": sha(actions_path),
        "source_sha256": {str(p.relative_to(ROOT)): d for p, d in PINS.items()},
        "producer_sha256": sha(Path(__file__)),
        "summary_csv_sha256": sha(csv_path),
        "source_lateral_references_sha256": sha(lateral_csv),
        "conditional_properties_mpa": {"Fv_parallel": fv, "Fc_perpendicular": fc},
        "counts": {
            "declared_grain_paths": len(paths),
            "queried_shear_planes": 2 * len(paths),
            "individual_bolt_states": len(states),
            "two_bolt_parallel_row_states": len(row_groups),
            "nominal_washer_seats_reused": 16,
        },
        "finished_tearout_geometry": paths,
        "external_stock_end_edge_comparators": comparators,
        "group_and_geometry_factor_scenarios": factors,
        "simultaneous_bolt_states": states,
        "simultaneous_rail_parallel_row_states": row_groups,
        "max_parallel_path_ratio": max(
            states, key=lambda r: r["parallel_component_over_path_reference"]
        ),
        "max_ideal_washer_wood_pressure_ratio": max(
            states, key=lambda r: r["ideal_annulus_pressure_over_Fc_perp_reference"]
        ),
        "max_direct_bolt_stress_proxy": max(
            states, key=lambda r: r["direct_von_Mises_proxy_mpa"]
        ),
        "limits": [
            "Parallel components are screened against declared actual bore-tangent paths. No all-path fracture or combined splitting resistance is established.",
            "Fv/Fc references are the existing dry DF-L No.2 normal-duration scenario, without a service-factor increase. Stock is unobserved.",
            "Pure-component Cg and conservative end-direction Cdelta scenarios are not a code interpolation for full oblique group actions.",
            "Washer comparison is ideal supported-annulus wood pressure only; actual head/nut footprint, washer bending, prying and metal resistance remain distinct.",
            "Direct bolt stress includes axial and shear proxies, not co-located bolt bending or thread/runout geometry qualification.",
        ],
        "complete_joint_acceptance": False,
        "physical_release": False,
        "reviewed_geometry_changed": False,
        "native_run": False,
    }
    (HERE / "top-corner-local-references.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    print(
        "Computed 32 finished shear-plane areas and 48 simultaneous local bolt states."
    )
    print(
        "Peak parallel-path ratio",
        round(
            report["max_parallel_path_ratio"]["parallel_component_over_path_reference"],
            4,
        ),
    )
    print(
        "Peak ideal washer wood-pressure ratio",
        round(
            report["max_ideal_washer_wood_pressure_ratio"][
                "ideal_annulus_pressure_over_Fc_perp_reference"
            ],
            4,
        ),
    )
    for factor in factors:
        print(
            factor["group_id"],
            "Cdelta end scenario",
            round(factor["conservative_end_Cdelta_scenario"], 6),
            "Cg N-component scenario",
            round(factor["pure_N_component_Cg_scenario"], 6),
        )


if __name__ == "__main__":
    main()
