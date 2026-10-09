"""Four bounded engineering checks; frozen old actions, current local geometry.

No response assembly, native mechanics execution, geometry rebuild or mesh export.
Detailed query rows belong in an ignored output directory. Reuse issued admission
and existing arithmetic rather than copying their implementations.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import brentq
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
sys.path.insert(0, str(ROOT))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def merge(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "conflicting pin: " + path)
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def read(ref):
    require(sha(ROOT / ref["path"]) == ref["sha256"], "source reference differs")
    return json.loads((ROOT / ref["path"]).read_bytes())


def trimmed_ray(polygon, point, direction):
    """Current convex YZ silhouette ray; no circular-bore/stress qualification."""
    p, d = np.asarray(point)[1:], np.asarray(direction)[1:]
    rows = []
    for a, b, c in ConvexHull(np.asarray(polygon)).equations:
        normal = np.array([a, b])
        remaining, speed = -c - normal @ p, normal @ d
        require(remaining >= -1e-5, "bore point outside trimmed cleat")
        if speed > 1e-10:
            rows.append(
                {
                    "distance_mm": float(max(0.0, remaining) / speed),
                    "outward_normal_yz": normal.tolist(),
                    "boundary_normal_to_grain_deg": math.degrees(
                        math.acos(min(1.0, abs(b)))
                    ),
                }
            )
    require(rows, "trimmed ray must hit an edge")
    return min(rows, key=lambda r: r["distance_mm"])


def opening_force(rows, cut_y):
    """Force-only opening demand from complete nonintersected bore supports.

    All other external actions in this cleat have zero Y component. Their
    moments can require additional tension and are not disposed by this bound.
    """
    require(
        all(hi < cut_y or lo > cut_y for lo, hi, _ in rows), "cut crosses bore support"
    )
    high = sum(force for lo, _, force in rows if lo > cut_y)
    return {
        "signed_external_Y_on_high_portion_n": high,
        "necessary_integrated_Y_tension_under_fixed_actions_n": max(0.0, high),
    }


def timber_study(cases, geometry, trim, arithmetic):
    components, placements, openings, groups = [], [], [], []
    for case, field, reports in cases:
        members = {m["name"]: m for m in field["source_inputs"]["timber_rows"]}
        shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
        timber = reports["timber"]
        for row in timber["shaft_components"]:
            component = row["component"]
            if (
                component is not None
                and component.get("V_over_unadjusted_component_Z") is not None
            ):
                components.append(
                    {"case_id": case, "axis_id": row["axis_id"], **component}
                )
        for duty in timber["duties"]:
            groups.extend(
                {"case_id": case, "duty_id": duty["duty_id"], **pair}
                for pair in duty.get("own_receiver_pair_geometry_and_actions", [])
            )
        for row in timber["wood_surfaces"]:
            if not row["receiver"].startswith("eoere_cleat"):
                continue
            member = members[row["receiver"]]
            point, signed = (
                row["own_aggregate_point_xyz_mm"],
                row["own_signed_components"],
            )
            directions = {
                "grain_positive": np.asarray(member["axis"]),
                "grain_negative": -np.asarray(member["axis"]),
                "crossgrain_positive": np.asarray(signed["cross_grain_axis_xyz"]),
                "crossgrain_negative": -np.asarray(signed["cross_grain_axis_xyz"]),
            }
            rays = {
                key: trimmed_ray(trim["retained_YZ_polygon_mm"], point, direction)
                for key, direction in directions.items()
            }
            old = {
                key: arithmetic.raw_ray(member, point, direction.tolist())
                for key, direction in directions.items()
            }
            placements.append(
                {
                    "case_id": case,
                    "receiver": row["receiver"],
                    "axis_id": row["axis_id"],
                    "own_signed_components": signed,
                    "old_raw_rays": old,
                    "current_silhouette_rays": rays,
                    "actual_geometry_factor_and_splitting_capacity": None,
                }
            )
        for name in ("eoere_cleat_left", "eoere_cleat_right"):
            bore_terms = []
            for row in timber["wood_surfaces"]:
                if row["receiver"] == name:
                    y = row["own_aggregate_point_xyz_mm"][1]
                    radius = shafts[row["axis_id"]]["bore_diameter_mm"] / 2
                    bore_terms.append(
                        (y - radius, y + radius, row["own_force_xyz_n"][1])
                    )
            require(len(bore_terms) == 4, "four physical cleat bores required")
            for table in (
                "contact_actions",
                "shaft_end_capture_actions",
                "panel_screw_actions",
            ):
                require(
                    all(
                        abs(r["force_on_first_xyz_n"][1]) < 1e-10
                        for r in field[table]
                        if name in (r["first"], r["second"])
                    ),
                    "unaccounted cleat Y action",
                )
            require(
                all(
                    abs(r["force_xyz_n"][1]) < 1e-10
                    for r in field["body_applied_loads"]
                    if r["body"] == name
                ),
                "unaccounted applied Y action",
            )
            require(
                abs(sum(q[2] for q in bore_terms)) < 1e-5, "cleat Y equilibrium fails"
            )
            opening = opening_force(bore_terms, -105.85)
            openings.append(
                {
                    "case_id": case,
                    "member": name,
                    "plane_y_mm": -105.85,
                    "whole_bore_supports_y_min_max_force_n": bore_terms,
                    **opening,
                    "actual_timber_perpendicular_tension_capacity": None,
                    "retained_X_axis_bolts_cross_this_Y_normal_plane": False,
                    "moment_shear_and_other_crack_planes_closed": False,
                }
            )
    changed = [
        p
        for p in placements
        if any(
            abs(
                p["old_raw_rays"][key]["distance_mm"]
                - p["current_silhouette_rays"][key]["distance_mm"]
            )
            > 1e-5
            for key in p["old_raw_rays"]
        )
    ]
    worst = max(components, key=lambda r: r["V_over_unadjusted_component_Z"])
    return (
        {
            "question": "Which conventional bolt components and cleat splitting paths can be resolved without another field?",
            "current_revision": geometry["revision"],
            "supported_single_bolt_comparisons": len(components),
            "worst_unadjusted_lateral_component": worst,
            "mixed_or_shared_unsupported_shafts_per_case": 8,
            "complete_Cg_Cdelta_joint_and_splitting_resistances": None,
            "own_pair_group_records": len(groups),
            "records_with_established_uniform_load_aligned_row": sum(
                r["uniform_load_aligned_row_qualified"] for r in groups
            ),
            "trimmed_cleat_bore_records": len(placements),
            "changed_silhouette_records": len(changed),
            "nearest_current_grain_positive_ray": min(
                placements,
                key=lambda r: r["current_silhouette_rays"]["grain_positive"][
                    "distance_mm"
                ],
            ),
            "cleat_force_only_opening_bounds": openings,
            "worst_cleat_force_only_opening": max(
                openings,
                key=lambda r: r["necessary_integrated_Y_tension_under_fixed_actions_n"],
            ),
            "next_input": "A matching revised field; an applicable eccentric complete-group/timber splitting route. Existing X-axis clamp forces are already spent and do not cross the Y-normal crack.",
        },
        {
            "components": components,
            "trimmed_cleat_placements": placements,
            "groups": groups,
        },
    )


def heel_study(inputs, pins):
    original, nominal = read(inputs["heel_input"]), read(inputs["heel_nominal_result"])
    core = module("bounded_heel_core", original["files"]["kernel"]["path"])
    rows = []
    whole_flange = None
    for case, ref in original["cases"].items():
        report = read(ref)
        merge(pins, report["source_sha256"])
        for angle in report["angles"]:
            if (
                case == nominal["worst"]["case_id"]
                and angle["body"] == nominal["worst"]["body"]
            ):
                whole_flange = angle["whole_flange_torsion_warping_references"]
            for band in angle["bands"]:
                require(band["half_band_width_mm"] == 44.45, "heel strip width changed")
                rows.append((case, angle, band))
    require(len(rows) == 528, "six-case heel roster changed")

    def evaluate(t):
        values = []
        for case, angle, band in rows:
            c = core.heel_component(
                band["root"],
                width=44.45,
                thickness=t,
                inside_radius=6.35,
                fy=235.0,
                factor=1.67,
                weight_n=angle["own_physical_source_weight_n"],
                bound_radius_mm=angle["gravity_bounding_radius_mm"],
            )
            values.append(
                {
                    "case_id": case,
                    "body": angle["body"],
                    "port_id": band["port_id"],
                    "comparison": c,
                }
            )
        return max(
            values,
            key=lambda r: r["comparison"]["conditional_combined_yield_reference_ratio"],
        )

    replay = evaluate(6.35)
    require(replay == nominal["worst"], "nominal heel replay differs")
    threshold = brentq(
        lambda t: (
            evaluate(t)["comparison"]["conditional_combined_yield_reference_ratio"]
            - 1.0
        ),
        6.0,
        7.0,
        xtol=1e-10,
    )
    ratio = replay["comparison"]["conditional_combined_yield_reference_ratio"]
    return {
        "question": "How much section/material uncertainty can the owner nominal heel comparison tolerate?",
        "held_inside_radius_mm": 6.35,
        "nominal_thickness_mm": 6.35,
        "exact_nominal_replay": True,
        "comparison_count": len(rows),
        "worst": replay,
        "thickness_at_scalar_reference_boundary_mm": threshold,
        "nominal_minus_scalar_boundary_mm": 6.35 - threshold,
        "minimum_scenario_Fy_for_this_comparison_mpa": 235.0 * ratio,
        "maximum_uniform_scale_of_all_root_actions_and_own_gravity_to_reference": 1.0
        / ratio,
        "same_case_whole_flange_references_not_added_to_half_band": whole_flange,
        "actual_3D_heel_capacity": None,
        "next_input": "Delivered minimum thickness/radius, thinning and grade, or a matching manufacturer multi-action connector resistance. Whole-flange torsion, holes and transverse continuity need their own applicability; no second grid sweep resolves these inputs.",
    }


def washer_study(cases, pressure):
    rows, thicknesses = [], []
    for case, _, reports in cases:
        report = reports["washers"]
        for row in report["all200_own_end_diagnostics"]:
            require(
                row["own_model_couple_xyz_Nmm"] == [0.0, 0.0, 0.0],
                "washer pressure law changed",
            )
            scenarios = [("nominal", row["nominal_own_hardware_geometry"])]
            scenarios += [
                ("catalog_corner_" + str(i), s)
                for i, s in enumerate(row["USS_catalog_corners_min_thickness"])
            ]
            for label, s in scenarios:
                a, b, c = (
                    s["ID_mm"] / 2,
                    s["OD_mm"] / 2,
                    s["uniform_load_ring_outer_radius_mm"],
                )
                n = row["N_n"]
                head = pressure(
                    axial_n=n,
                    moment_xy_nmm=[0.0, 0.0],
                    inner_radius_mm=a,
                    outer_radius_mm=c,
                )
                support = pressure(
                    axial_n=n,
                    moment_xy_nmm=[0.0, 0.0],
                    inner_radius_mm=max(a, s["source_support_opening_diameter_mm"] / 2),
                    outer_radius_mm=b,
                )
                m_limit = min(
                    head["moment_full_contact_limit_nmm"],
                    support["moment_full_contact_limit_nmm"],
                )
                wood_index = None
                if (
                    row["receiver_kind"] == "wood"
                    and row["grain_axis_abs_cos_to_pressure_normal"] < 1e-8
                ):
                    p = pressure(
                        axial_n=n,
                        moment_xy_nmm=[m_limit, 0.0],
                        inner_radius_mm=max(
                            a, s["source_support_opening_diameter_mm"] / 2
                        ),
                        outer_radius_mm=b,
                    )
                    wood_index = (
                        p["pressure_max_mpa"]
                        / report["references"]["wood_Fc_perp625psi_mpa_unincreased"]
                    )
                rows.append(
                    {
                        "case_id": case,
                        "capture_id": row["capture_id"],
                        "host": row["host"],
                        "scenario": label,
                        "N_n": n,
                        "ID_OD_thickness_mm": [s["ID_mm"], s["OD_mm"], s["t_mm"]],
                        "two_face_affine_full_contact_moment_limit_nmm": m_limit,
                        "two_face_affine_eccentricity_limit_mm": min(
                            (a * a + c * c) / (4 * c),
                            (
                                max(a, s["source_support_opening_diameter_mm"] / 2) ** 2
                                + b * b
                            )
                            / (4 * b),
                        ),
                        "source_nominal_full_support": s[
                            "source_nominal_supported_ring_landing_full"
                        ],
                        "wood_peak_reference_at_two_face_contact_limit": wood_index,
                        "axial_only_Fy_required_mpa": s[
                            "sampled_axial_only_Fy_required_mpa"
                        ],
                        "actual_own_moment_and_combined_metal_resistance": None,
                    }
                )
            thicknesses.append(row["nominal_own_hardware_geometry"]["t_mm"])
    eligible = [
        r
        for r in rows
        if r["source_nominal_full_support"]
        and r["wood_peak_reference_at_two_face_contact_limit"] is not None
    ]
    active = [r for r in rows if r["N_n"] > 1e-8]
    return {
        "question": "Does washer thickening close axial bending, eccentric seating and wood bearing together?",
        "own_end_cases": 1200,
        "including_catalog_corner_rows": len(rows),
        "nominal_washer_thicknesses_mm": sorted(set(thicknesses)),
        "worst_axial_only_required_Fy": max(
            rows, key=lambda r: r["axial_only_Fy_required_mpa"]
        ),
        "minimum_positive_load_two_face_affine_eccentricity_mm": min(
            r["two_face_affine_eccentricity_limit_mm"] for r in active
        ),
        "maximum_two_face_affine_eccentricity_mm": max(
            r["two_face_affine_eccentricity_limit_mm"] for r in active
        ),
        "worst_full_supported_wood_pressure_at_contact_limit": max(
            eligible, key=lambda r: r["wood_peak_reference_at_two_face_contact_limit"]
        ),
        "conditional_wood_landings_per_case": reports["washers"]["census"][
            "conditional_wood_outer_landing"
        ],
        "unmeasured_actual_seated_moment_and_combined_washer_strength": None,
        "next_input": "Washer minimum dimensions/grade and actual two-face seated moment/contact behavior. Thickness reduces the axial plate diagnostic but does not increase the geometric full-contact eccentricity limit.",
    }, rows


def member_study(cases, gross):
    from fea import reinforced_timber_resistance as nds
    from scripts import thin_bolted_timber_common_shaft_checks as own

    summary, all_cuts = [], []
    for case, field, _ in cases:
        actions, gravity = own.member_point_inputs(field)
        for member in field["source_inputs"]["timber_rows"]:
            grain, u, v = (
                np.asarray(member[k]) for k in ("axis", "section_u", "section_v")
            )
            start, end = np.asarray(member["start"]), np.asarray(member["end"])
            low, high = grain @ start, grain @ end
            length = float(high - low)
            width, depth = member["width_mm"], member["depth_mm"]
            short, long = sorted((width, depth))
            stations = set(np.linspace(low, high, 51).tolist())
            for point, _, _ in actions[member["name"]]:
                stations.update(
                    float(np.clip(grain @ point + delta, low, high))
                    for delta in (-1e-5, 1e-5)
                )
            cuts = []
            for station in sorted(stations):
                cut = start + grain * (station - low)
                wrench = own.previous.member_cut_wrench(
                    grain.tolist(),
                    float(low),
                    float(high),
                    cut.tolist(),
                    *gravity[member["name"]],
                    actions[member["name"]],
                )
                local = np.r_[
                    np.asarray([grain, u, v]) @ wrench["force_on_lower_portion_xyz_n"],
                    np.asarray([grain, u, v])
                    @ wrench["moment_on_lower_portion_about_cut_xyz_nmm"],
                ].tolist()
                full = gross.rectangle.rectangle_check(local, width, depth, length)
                # Independent restraint scenario: only weak-column effective
                # length is capped at 50b. Strong-column and beam assumptions
                # remain those in the original reference; no brace is credited.
                kernel = nds.member_check(
                    width_mm=short,
                    depth_mm=long,
                    axial_n=0.0,
                    moment_strong_nmm=0.0,
                    moment_weak_nmm=0.0,
                    shear_strong_n=0.0,
                    shear_weak_n=0.0,
                    torsion_nmm=0.0,
                    column_effective_strong_mm=length,
                    column_effective_weak_mm=min(length, 50.0 * short),
                    beam_effective_mm=nds.effective_beam_length(length, long),
                    reference_override=nds.adjusted_reference(139.7),
                )
                capped = gross.rectangle.normal_check(
                    local, width, depth, kernel, kernel["references"]
                )
                cuts.append(
                    {
                        "case_id": case,
                        "member": member["name"],
                        "station_mm": station,
                        "local_same_cut_actions_n_nmm": local,
                        "full_length_K1": full[
                            "full_length_K1_pin_end_normal_sensitivity"
                        ],
                        "weak_column_50b_scenario": capped,
                        "fully_braced_normal": full[
                            "fully_braced_component_normal_interaction"
                        ],
                        "shear_torsion_sufficient_reference": full[
                            "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"
                        ],
                    }
                )
            for key in ("fully_braced_normal", "shear_torsion_sufficient_reference"):
                summary.append(max(cuts, key=lambda r, key=key: r[key]))
            summary.append(
                max(cuts, key=lambda r: r["full_length_K1"]["interaction_ratio"])
            )
            all_cuts.extend(cuts)
    domains = sorted(
        {
            r["member"]
            for r in all_cuts
            if not r["full_length_K1"]["within_slenderness_limits"]
        }
    )
    lengths = [
        {
            "member": m["name"],
            "full_span_mm": float(np.linalg.norm(np.asarray(m["end"]) - m["start"])),
            "weak_column_effective_length_domain_cap_mm": 50
            * min(m["width_mm"], m["depth_mm"]),
            "actual_restraint_qualified": False,
        }
        for m in cases[0][1]["source_inputs"]["timber_rows"]
        if m["name"] in domains
    ]
    return {
        "question": "Do sampled gross stresses conceal a conventional member stability problem?",
        "case_members": 132,
        "same_cut_comparisons": len(all_cuts),
        "worst_fully_braced_normal": max(
            summary, key=lambda r: r["fully_braced_normal"]
        ),
        "worst_shear_torsion_sufficient_reference": max(
            summary, key=lambda r: r["shear_torsion_sufficient_reference"]
        ),
        "worst_full_span_K1_normal": max(
            summary, key=lambda r: r["full_length_K1"]["interaction_ratio"]
        ),
        "weak_column_domain_exceeding_members": lengths,
        "worst_50b_weak_column_scenario": max(
            all_cuts, key=lambda r: r["weak_column_50b_scenario"]["interaction_ratio"]
        ),
        "actual_bracing_finished_net_strength_or_continuous_maximum": None,
        "next_input": "Document actual lateral restraint and load transfer for each long member. Effective-length scenarios are requirements, not installed bracing.",
    }, all_cuts


def section_study(cases, current, old, trim, section_helper):
    import cadquery as cq

    from fea import reinforced_timber_resistance as nds
    from scripts import thin_bolted_timber_common_shaft_checks as own

    method = section_helper.section_method(
        sha(ROOT / "scripts/wood_joint_wj12_sections.py")
    )
    members = {r["name"]: r for r in cases[0][1]["source_inputs"]["timber_rows"]}
    old_solids = {r["id"]: r for r in old["finished_solids"]}
    new_solids = {
        r["id"]: r
        for r in current["changed_finished_solids"] + trim["changed_finished_solids"]
    }
    wires = {r["name"]: r for r in current["wire_proposals"]}
    rows = []
    for name, source in sorted(new_solids.items()):
        member = members[name]
        grain, u, v = (
            np.asarray(member[k]) for k in ("axis", "section_u", "section_v")
        )
        stations = set()
        for shaft in cases[0][1]["source_inputs"]["shafts"]:
            if any(s["host"] == name for s in shaft["surfaces"]):
                s = float(grain @ shaft["source_axis"]["point_xyz_mm"])
                stations.update((s - 1e-4, s + 1e-4))
        if name.startswith("eoere_cleat"):
            stations.update((334.398105944 - 1e-4, 334.398105944 + 1e-4, 429.4 - 1e-4))
        else:
            for cut in current["service_cuts"]:
                if cut["receiver"] == name and cut["service"] in wires:
                    for x in {p[0] for p in wires[cut["service"]]["route_local_mm"]}:
                        if (
                            source["bounds_xyz_mm"][0][0] + 1e-4
                            < x
                            < source["bounds_xyz_mm"][0][1] - 1e-4
                        ):
                            stations.add(float(grain[0] * x))
        shapes = {
            "old": cq.Shape.importBrep(str(ROOT / old_solids[name]["path"])),
            "current": cq.Shape.importBrep(str(ROOT / source["path"])),
        }
        require(
            all(s.isValid() and len(s.Solids()) == 1 for s in shapes.values()),
            "one valid cached solid required",
        )
        start = np.asarray(member["start"])
        for station in sorted(stations):
            point = start + grain * (station - grain @ start)
            measures = {
                label: method(
                    shape,
                    origin=cq.Vector(*point),
                    normal=cq.Vector(*grain),
                    u_axis=cq.Vector(*u),
                    v_axis=cq.Vector(*v),
                )
                for label, shape in shapes.items()
            }
            require(
                all(m["area_mm2"] > 0 for m in measures.values()),
                "section must contain timber",
            )
            case_bounds = []
            for case, field, _ in cases:
                actions, gravity = own.member_point_inputs(field)
                wrench = own.previous.member_cut_wrench(
                    grain.tolist(),
                    float(grain @ start),
                    float(grain @ np.asarray(member["end"])),
                    point.tolist(),
                    *gravity[name],
                    actions[name],
                )
                f = np.asarray(wrench["force_on_lower_portion_xyz_n"])
                n, shear = (
                    float(f @ grain),
                    float(np.linalg.norm(f - grain * (f @ grain))),
                )
                reference = nds.adjusted_reference(139.7)
                area = measures["current"]["area_mm2"]
                case_bounds.append(
                    {
                        "case_id": case,
                        "parallel_axial_n": n,
                        "transverse_shear_n": shear,
                        "necessary_axial_average_reference": max(n, 0.0)
                        / area
                        / reference["Ft_mpa"]
                        + max(-n, 0.0) / area / reference["Fc_star_mpa"],
                        "necessary_shear_average_reference": shear
                        / area
                        / reference["Fv_mpa"],
                    }
                )
            rows.append(
                {
                    "member": name,
                    "station_mm": station,
                    "point_xyz_mm": point.tolist(),
                    **measures,
                    "current_over_old_area": measures["current"]["area_mm2"]
                    / measures["old"]["area_mm2"],
                    "current_over_gross_rectangle_area": measures["current"]["area_mm2"]
                    / (member["width_mm"] * member["depth_mm"]),
                    "fixed_old_action_average_bounds": case_bounds,
                }
            )
    summaries = []
    for name in sorted(new_solids):
        own_rows = [r for r in rows if r["member"] == name]
        summaries.append(
            {
                "member": name,
                "sample_plane_count": len(own_rows),
                "minimum_current_over_old_area": min(
                    own_rows, key=lambda r: r["current_over_old_area"]
                ),
                "minimum_current_over_gross_area": min(
                    own_rows, key=lambda r: r["current_over_gross_rectangle_area"]
                ),
            }
        )
    return {
        "changed_members": len(summaries),
        "exact_cached_section_planes": len(rows),
        "members": summaries,
        "new_global_gravity_distribution_stiffness_or_actions_evaluated": False,
        "bending_torsion_stress_concentrations_and_splitting_strength": None,
        "next_input": "Matching current response and applicable net bending/shear/torsion/connection treatment. Areas and necessary average bounds do not dispose bending or fracture.",
    }, rows


def known_answers(pressure, section_helper):
    rectangle = [[-2.0, 0.0], [2.0, 0.0], [2.0, 4.0], [-2.0, 4.0]]
    require(
        trimmed_ray(rectangle, [0.0, 0.0, 1.0], [0.0, 0.0, 1.0])["distance_mm"] == 3.0,
        "trimmed vertical ray fixture",
    )
    require(
        trimmed_ray(rectangle, [0.0, 0.0, 1.0], [0.0, -1.0, 0.0])["distance_mm"] == 2.0,
        "trimmed signed transverse ray fixture",
    )
    oblique = trimmed_ray(
        [[-2.0, 0.0], [2.0, 0.0], [2.0, 4.0]], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]
    )
    require(
        abs(oblique["distance_mm"] - 1.0) < 1e-12
        and abs(oblique["boundary_normal_to_grain_deg"] - 45.0) < 1e-12,
        "oblique end must not be classified square",
    )
    require(
        opening_force([(-12.0, -8.0, -100.0), (8.0, 12.0, 100.0)], 0.0)[
            "necessary_integrated_Y_tension_under_fixed_actions_n"
        ]
        == 100.0,
        "opening sign fixture",
    )
    require(
        opening_force([(-12.0, -8.0, 100.0), (8.0, 12.0, -100.0)], 0.0)[
            "necessary_integrated_Y_tension_under_fixed_actions_n"
        ]
        == 0.0,
        "compression fixture",
    )
    rejected = False
    try:
        opening_force([(-12.0, -8.0, -100.0), (8.0, 12.0, 100.0)], 9.0)
    except ValueError:
        rejected = True
    require(rejected, "intersected bearing support accepted")
    p = pressure(
        axial_n=100.0,
        moment_xy_nmm=[312.5, 0.0],
        inner_radius_mm=5.0,
        outer_radius_mm=10.0,
    )
    require(
        abs(p["pressure_min_mpa"]) < 1e-12 and p["full_contact_admissible"],
        "annulus kern fixture",
    )
    outside = pressure(
        axial_n=100.0,
        moment_xy_nmm=[313.0, 0.0],
        inner_radius_mm=5.0,
        outer_radius_mm=10.0,
    )
    require(not outside["full_contact_admissible"], "annulus tension fixture")
    import cadquery as cq

    method = section_helper.section_method(
        sha(ROOT / "scripts/wood_joint_wj12_sections.py")
    )
    shape = cq.Workplane("XY").box(20.0, 10.0, 30.0).val()
    area = method(
        shape,
        origin=cq.Vector(0.0, 0.0, 0.0),
        normal=cq.Vector(0.0, 0.0, 1.0),
        u_axis=cq.Vector(1.0, 0.0, 0.0),
        v_axis=cq.Vector(0.0, 1.0, 0.0),
    )["area_mm2"]
    require(abs(area - 200.0) < 1e-6, "exact planar rectangle fixture")
    return {
        "opening_and_compression_signs": True,
        "intersected_support_rejected": True,
        "trimmed_rectangular_and_oblique_ray_known_answers": True,
        "independent_annulus_kern_312p5_Nmm_and_tension_rejection": True,
        "exact_CAD_rectangle_area_mm2": area,
    }


def run():
    inputs = json.loads((HERE / "inputs.json").read_bytes())
    pins = dict(inputs["direct_source_sha256"])
    merge(
        pins,
        {
            str(p.relative_to(ROOT)): sha(p)
            for p in (HERE / "analyze.py", HERE / "inputs.json")
        },
    )
    verify(pins)
    current, old, trim = (
        read(inputs[k]) for k in ("current_geometry", "old_geometry", "trim_geometry")
    )
    require(
        current["revision"] == "eoere-grid-aligned-wire-cutouts-v1"
        and current["mechanics_ready"] is False,
        "current revision contract",
    )
    require(
        current["axes"] == old["axes"] and current["screw_axes"] == old["screw_axes"],
        "100 bolt and 66 screw record identities must be retained",
    )
    merge(pins, current["source_sha256"])
    changed_names = {
        r["id"]
        for r in current["changed_finished_solids"] + trim["changed_finished_solids"]
    }
    for row in (
        current["changed_finished_solids"]
        + trim["changed_finished_solids"]
        + old["finished_solids"]
    ):
        if row["id"] in changed_names:
            merge(pins, {row["path"]: row["sha256"]})
    consumer = module("bounded_issued_intake", inputs["helpers"]["admission"])
    timber_arithmetic = module("bounded_timber_placement", inputs["helpers"]["timber"])
    gross = module("bounded_member_method", inputs["helpers"]["members"])
    section_helper = module("bounded_section_method", inputs["helpers"]["sections"])
    from scripts.thin_bolted_steel_resistance import annulus_pressure

    merge(pins, gross.source_pins())
    cases = []
    for spec in inputs["cases"]:
        field, admitted = consumer.load_admitted(ROOT / spec["manifest"]["path"])
        merge(pins, admitted)
        reports = {key: read(ref) for key, ref in spec["reports"].items()}
        for report in reports.values():
            merge(pins, report.get("source_sha256", {}))
        require(
            field["case_id"] == spec["case_id"]
            and field["source_inputs"]["geometry"]["report"] == inputs["old_geometry"],
            "old response identity",
        )
        require(
            all(r["case_id"] == spec["case_id"] for r in reports.values()),
            "cross-case report substitution",
        )
        cases.append((spec["case_id"], field, reports))
    verify(pins)
    checks = known_answers(annulus_pressure, section_helper)
    timber, timber_rows = timber_study(cases, current, trim, timber_arithmetic)
    heel = heel_study(inputs, pins)
    washers, washer_rows = washer_study(cases, annulus_pressure)
    members, member_rows = member_study(cases, gross)
    sections, section_rows = section_study(cases, current, old, trim, section_helper)
    verify(pins)
    result = {
        "schema": "eoere_four_bounded_strength_studies/v1",
        "status": "COMPLETE_FIXED_OLD_ACTION_STUDIES_CURRENT_GEOMETRY_RESPONSE_UNEVALUATED",
        "current_geometry": inputs["current_geometry"],
        "response_geometry": inputs["old_geometry"],
        "case_ids": [c for c, _, _ in cases],
        "load_contract": inputs["load_contract"],
        "timber_bolts_and_splitting": timber,
        "bracket_heel": heel,
        "washers_and_timber_seats": washers,
        "members_stability_and_net_sections": {
            **members,
            "current_section_queries": sections,
        },
        "known_answers": checks,
        "source_binding": {
            "direct_source_sha256": {
                **inputs["direct_source_sha256"],
                **{
                    str(p.relative_to(ROOT)): sha(p)
                    for p in (HERE / "analyze.py", HERE / "inputs.json")
                },
            },
            "pin_count": len(pins),
            "canonical_sha256": canonical(pins),
            "verified_before_after": True,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "limits": [
            "All demand comes from the preserved untrimmed raised-rail six-case fields; current trim/wire geometry has no matching response.",
            "Current local geometry queries at fixed old actions are sensitivities, not current-case strength passes.",
            "The 2x climber multiplier and no-slip floor remain unverified analytical assumptions.",
            "Existing panel/screw exceedances remain recorded; stopped remedy studies remain stopped.",
            "No fabricated or delivered part, physical test, floor restraint or complete joint resistance is verified.",
        ],
        "release": {
            "current_complete_resistance": False,
            "candidate_selection": False,
            "physical_work": False,
            "climbing": False,
        },
    }
    details = {
        "complete_source_sha256": pins,
        "timber": timber_rows,
        "washers": washer_rows,
        "members": member_rows,
        "sections": section_rows,
    }
    return result, details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--details", type=Path, required=True)
    args = parser.parse_args()
    require(
        not args.out.exists() and not args.details.exists(),
        "fresh output paths required",
    )
    result, details = run()
    for path, value in ((args.out, result), (args.details, details)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "status": result["status"],
                "pins": result["source_binding"]["pin_count"],
                "result_sha256": sha(args.out),
                "details_sha256": sha(args.details),
            },
            indent=2,
        )
    )
