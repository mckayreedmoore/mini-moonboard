"""2024 NDS component sensitivities for the revised center principal/header.

The direct barrel-nut joint has no qualified complete-joint resistance here.
No native solve, fabrication coordinates, or release are produced.
"""

import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_dowel_bearing_psi,
    dfl_net_parallel_tension_reference_lbf,
)
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from scripts import owner_barrel_center_post_joint_replan as replan
from scripts.owner_barrel_coordinates import N, T, local_bounds

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "docs/bolted-candidate-material-basis.json"
STATION = "clip_split_base_center_right"
MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
ROOT_IN_SENSITIVITY = 0.189  # 2024 NDS Appendix L typical, not delivered geometry.
FYB_PSI_SENSITIVITY = 45_000  # 2024 NDS Appendix I bolt class, not a SKU rating.
STEEL_E_MPA_SENSITIVITY = 205_000  # Prior steel-only model assumption.
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _angle(a, grain):
    return math.degrees(math.acos(min(1.0, abs(_dot(a, grain)))))


def _material():
    record = json.loads(MATERIAL.read_text())
    values = record["reference_values"]
    if (
        record["source"]["edition"] != "2024 NDS and 2024 NDS Supplement"
        or record["species_grade"] != "US Douglas Fir-Larch No. 2 dimension lumber"
        or values["Ft_parallel"]["value"] != 575
        or values["Fc_perpendicular"]["value"] != 625
        or values["E"]["value"] != 1_600_000
        or values["G"]["value"] != 0.5
    ):
        raise ValueError("2024 DF-L source basis changed")
    return values


def _yield_surrogate(header_length_mm, principal_length_mm, lateral):
    """One conditional ordinary-wood/wood lateral comparison, not barrel Z."""
    header_grain = (1.0, 0.0, 0.0)
    principal_grain = (0.0, *T)
    header_angle = _angle(lateral, header_grain)
    principal_angle = _angle(lateral, principal_grain)
    k_theta = 1 + 0.25 * max(header_angle, principal_angle) / 90
    reduction = (10 * ROOT_IN_SENSITIVITY + 0.5) * k_theta
    result = wood_wood_single_shear_reference(
        main_bearing_length_in=header_length_mm / MM_PER_IN,
        side_bearing_length_in=principal_length_mm / MM_PER_IN,
        main_load_to_grain_degrees=header_angle,
        side_load_to_grain_degrees=principal_angle,
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=0.25,
        bolt_thread_root_diameter_in=ROOT_IN_SENSITIVITY,
        main_thread_bearing_length_in=header_length_mm / MM_PER_IN,
        side_thread_bearing_length_in=principal_length_mm / MM_PER_IN,
        bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=FYB_PSI_SENSITIVITY,
            effective_diameter_in=ROOT_IN_SENSITIVITY,
        ),
        bolt_bending_yield_strength_psi=FYB_PSI_SENSITIVITY,
        gap_in=0.0,
        reduction_terms=dict.fromkeys(MODES, reduction),
    )
    return {
        "header_load_to_grain_deg": round(header_angle, 6),
        "principal_load_to_grain_deg": round(principal_angle, 6),
        "governing_mode": result["governing_mode"],
        "one_bolt_reference_n": round(result["reference_lateral_lbf"] * N_PER_LBF, 3),
        "one_bolt_reference_lbf": round(result["reference_lateral_lbf"], 3),
    }


def _sampled_section(principal, cutters, centers_t):
    """Sample actual X–N cut area in the barrel zone at 0.5 mm T pitch."""
    cut = principal
    for shape in cutters:
        cut = cut.cut(shape)
    bounds = local_bounds(principal)
    thickness = 0.5
    low, high = min(centers_t) - 10, max(centers_t) + 10
    samples = []
    for index in range(math.ceil((high - low) / thickness) + 1):
        t = low + index * thickness
        slab = cq.Solid.makeBox(
            bounds["x"][1] - bounds["x"][0] + 2,
            thickness,
            bounds["n"][1] - bounds["n"][0] + 2,
            cq.Vector(bounds["x"][0] - 1, t - thickness / 2, bounds["n"][0] - 1),
        ).rotate((0, 0, 0), (1, 0, 0), math.degrees(math.atan2(T[1], T[0])))
        gross = principal.intersect(slab).Volume() / thickness
        net = cut.intersect(slab).Volume() / thickness
        samples.append((t, gross, net))
    t, gross, net = min(samples, key=lambda row: row[2])
    return {
        "scope": "principal barrel zone, current two blind cross-bores and two machine bores",
        "sample_pitch_t_mm": thickness,
        "sample_count": len(samples),
        "critical_sample_t_mm": round(t, 3),
        "gross_area_mm2": round(gross, 3),
        "minimum_sampled_net_area_mm2": round(net, 3),
        "removed_area_mm2": round(gross - net, 3),
        "unadjusted_Ft_times_sampled_area_n": round(
            575 * net / MM_PER_IN**2 * N_PER_LBF, 3
        ),
        "capacity_qualified": False,
    }


def report(trial=None):
    """Build the right principal/header component ledger from the current CAD."""
    _material()
    trial = replan.build() if trial is None else trial
    if trial["report"]["nominal_geometry_disposition"] != "CLEAR_OCCUPANCY":
        raise ValueError("Integrated center nominal geometry is not clear")
    wood = trial["wood"]
    header, principal = wood["base_header"], wood["base_principal_center_right"]
    header_top = header.BoundingBox().zmax
    bounds = local_bounds(principal)
    rows = trial["report"]["stations"][STATION]["bolts"]
    if len(rows) != 2 or len(trial["solids"]) != 8:
        raise ValueError("Expected two principal/header rows and eight center bolts")
    names = sorted(rows)
    axes, geometry_rows, yield_rows, cutters, centers_t = [], [], [], [], []
    for name in names:
        datum, shapes = rows[name], trial["solids"][name]
        seat, axis, thread = (
            tuple(datum[key])
            for key in ("bolt_seat_xyz_mm", "bolt_axis_xyz", "thread_axis_xyz_mm")
        )
        if (
            datum["entry_face"] != "header_rear_recess"
            or not math.isclose(datum["washer_diameter_mm"], 19.05, abs_tol=1e-6)
            or not math.isclose(
                datum["joined_wood_bore_core_fraction"], 1.0, abs_tol=1e-6
            )
            or not math.isclose(
                datum["tip_extension_in_receiver_fraction"], 1.0, abs_tol=1e-6
            )
            or not math.isclose(datum["modeled_bore_depth_past_nominal_tip_mm"], 4.0)
        ):
            raise ValueError(f"{name}: revised principal/header pose changed")
        header_length = (header_top - seat[2]) / axis[2]
        principal_length = (
            _dot(tuple(thread[i] - seat[i] for i in range(3)), axis) - header_length
        )
        if header_length <= 0 or principal_length <= 0:
            raise ValueError(f"{name}: invalid two-member path")
        t = thread[1] * T[0] + thread[2] * T[1]
        n = thread[1] * N[0] + thread[2] * N[1]
        centers_t.append(t)
        axes.append((seat, axis, thread))
        cutters.extend((shapes["bolt_bore"], shapes["barrel_cross_bore"]))
        geometry_rows.append(
            {
                "bolt": name,
                "nominal_bolt_length_mm": round(datum["bolt_length_mm"], 3),
                "seat_to_header_butt_mm": round(header_length, 3),
                "butt_to_barrel_axis_in_principal_mm": round(principal_length, 3),
                "seat_to_barrel_axis_mm": round(header_length + principal_length, 3),
                "nominal_tip_past_barrel_axis_mm": datum[
                    "nominal_tip_beyond_thread_axis_mm"
                ],
                "nominal_tip_past_barrel_far_wall_mm": round(
                    datum["nominal_tip_beyond_thread_axis_mm"] - replan.OD / 2, 3
                ),
                "bore_past_nominal_tip_mm": datum[
                    "modeled_bore_depth_past_nominal_tip_mm"
                ],
                "barrel_cross_bore_depth_mm": datum["barrel_cross_bore_depth_mm"],
                "barrel_recess_mm": datum["barrel_recess_mm"],
                "thread_center_t_n_mm": [round(t, 3), round(n, 3)],
                "barrel_center_to_principal_grain_end_mm": round(t - bounds["t"][0], 3),
                "barrel_radius_to_nearest_n_edge_mm": round(
                    min(n - bounds["n"][0], bounds["n"][1] - n) - replan.OD / 2, 3
                ),
            }
        )
        lateral_yz = (0.0, -axis[2], axis[1])
        yield_rows.append(
            {
                "bolt": name,
                "directions": {
                    "across_x": _yield_surrogate(
                        header_length, principal_length, (1.0, 0.0, 0.0)
                    ),
                    "transverse_yz": _yield_surrogate(
                        header_length, principal_length, lateral_yz
                    ),
                },
            }
        )
    seat_a, axis, _ = axes[0]
    seat_b = axes[1][0]
    delta = tuple(b - a for a, b in zip(seat_a, seat_b, strict=True))
    axial_projection = _dot(delta, axis)
    pitch = math.sqrt(sum(v * v for v in delta) - axial_projection**2)
    bore_a = trial["solids"][names[0]]["barrel_cross_bore"].BoundingBox()
    bore_b = trial["solids"][names[1]]["barrel_cross_bore"].BoundingBox()
    bore_cap_gap = bore_b.xmin - bore_a.xmax
    if bore_cap_gap <= 0:
        raise ValueError("Opposing principal barrel bores overlap in X")
    section = _sampled_section(principal, cutters, centers_t)
    washer_n = (
        dfl_axial_wood_bearing_reference_lbf(
            19.05 / MM_PER_IN, 7.5 / MM_PER_IN, 6.35 / MM_PER_IN
        )
        * N_PER_LBF
    )
    root_mm = ROOT_IN_SENSITIVITY * MM_PER_IN
    nominal_area = math.pi * 6.35**2 / 4
    root_area = math.pi * root_mm**2 / 4
    steel_lengths = [
        row["seat_to_barrel_axis_mm"] + replan.WASHER_T for row in geometry_rows
    ]
    return {
        "schema": "owner_barrel_integrated_center_prelim/v1",
        "edition": "2024 NDS / 2024 NDS Supplement",
        "source_station": STATION,
        "geometry": {
            "principal_section_x_n_mm": [
                round(bounds["x"][1] - bounds["x"][0], 3),
                round(bounds["n"][1] - bounds["n"][0], 3),
            ],
            "rows": geometry_rows,
            "row_axis_pitch_mm": round(pitch, 3),
            "opposing_barrel_bore_cap_x_gap_mm": round(bore_cap_gap, 3),
            "nominal_centered_machine_bore_radial_slack_mm": round((7.5 - 6.35) / 2, 3),
        },
        "wood": {
            "assumed_species_grade": "dry unincised US DF-L No. 2; actual stock unverified",
            "ideal_washer_fc_perp_n_per_bolt": round(washer_n, 3),
            "nominal_dowel_bearing_psi": {
                "parallel": dfl_dowel_bearing_psi(0.25, 0),
                "perpendicular": dfl_dowel_bearing_psi(0.25, 90),
            },
            "typical_root_dowel_bearing_psi": dfl_dowel_bearing_psi(
                ROOT_IN_SENSITIVITY, 90
            ),
            "sampled_principal_net_section": section,
            "two_full_slot_parallel_tension_sensitivity_n": round(
                dfl_net_parallel_tension_reference_lbf(
                    (bounds["x"][1] - bounds["x"][0]) / MM_PER_IN,
                    (bounds["n"][1] - bounds["n"][0]) / MM_PER_IN,
                    (replan.OD / MM_PER_IN,) * 2,
                )
                * N_PER_LBF,
                3,
            ),
            "barrel_bearing_breakout_splitting_resistance_n": None,
        },
        "lateral_yield_surrogate": {
            "basis": "2024 NDS ordinary two-solid-wood single-shear with nominal centerline bearing lengths, 0.189-in typical root and 45,000-psi class Fyb; angled butt has partial member sections and this is not a barrel-joint rating",
            "rows": yield_rows,
            "actual_bearing_lengths_qualified": False,
            "actual_barrel_joint_rating_n": None,
        },
        "bolt_shaft": {
            "nominal_shank_area_mm2": round(nominal_area, 3),
            "typical_root_area_mm2_sensitivity": round(root_area, 3),
            "conditional_axial_n_per_mpa": "A_t(mm2) × verified tensile stress(MPa)",
            "actual_axial_resistance_n": None,
            "combined_tension_shear_bending_verified": False,
        },
        "barrel_thread": {
            "assumed_thread_axis_offset_mm": replan.OFFSET,
            "delivered_thread_open_exit_verified": False,
            "verified_thread_strip_n": None,
            "verified_barrel_wall_flexure_n": None,
            "verified_resistance_n": None,
        },
        "axial_withdrawal": {
            "wood_screw_withdrawal_formula_applicable": False,
            "conditional_path": "min(shaft tension, thread strip, barrel wall, barrel-to-wood breakout, washer/wood bearing)",
            "complete_path_resistance_n": None,
        },
        "stiffness": {
            "steel_modulus_mpa_sensitivity": STEEL_E_MPA_SENSITIVITY,
            "modeled_head_side_to_barrel_axis_mm": steel_lengths,
            "steel_only_nominal_shank_n_per_mm": round(
                STEEL_E_MPA_SENSITIVITY * nominal_area / steel_lengths[0], 3
            ),
            "steel_only_typical_root_n_per_mm": round(
                STEEL_E_MPA_SENSITIVITY * root_area / steel_lengths[0], 3
            ),
            "nds_group_modulus_comparison_n_per_mm": round(
                180_000 * 0.25**1.5 * N_PER_LBF / MM_PER_IN, 3
            ),
            "complete_joint_n_per_mm": None,
        },
        "group_action": {
            "row_axis_pitch_mm": round(pitch, 3),
            "two_bolt_resistance_n": None,
            "load_share_verified": False,
        },
        "actual_new_topology_joint_demands": None,
        "missing_inputs": [
            "signed new-topology joint forces and moments with contact/load sharing",
            "delivered bolt root, thread length, steel yield/tension/shear and combined stress",
            "identified barrel steel, thread engagement/strip, wall strength and bearing test",
            "delivered barrel through-thread/open exit and usable far-side bolt travel",
            "actual lumber grade, moisture, cuts, grain, splitting and barrel breakout",
            "washer product compliance, bending and local seat contact",
            "net-section/eccentric member action and classified edge/end/group factors",
            "measured slip, seating, preload, tolerances and assembly-cycle stiffness",
        ],
        "native_solve": False,
        "release_flags": {
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
