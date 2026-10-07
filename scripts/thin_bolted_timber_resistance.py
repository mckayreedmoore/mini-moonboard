"""Source-bound timber/bolt component checks for the reviewed thin frame.

The frozen occupied model supplies geometry, never force or resistance. Fresh
signed attachment actions and explicit material scenarios are optional inputs.
Missing inputs, unsupported unequal steel-side actions and local fracture are
reported separately from calculated component references. No model is changed
and no native solver, historical force transfer or release is performed.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from mini_moonboard.bolted_steel_wood_yield import wood_steel_single_shear_reference
from mini_moonboard.bolted_steel_wood_double_shear import wood_steel_double_shear_reference
from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_dowel_bearing_psi,
    dfl_net_parallel_tension_reference_lbf,
    dfl_parallel_row_tear_out_reference_lbf,
)
from mini_moonboard.nds_2024_multi_member_bolt_yield import (
    _reduction_terms,
    _single_shear_modes,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
LAYOUT = PACKET / "mixed-offset-rows-shallow-wires-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
INTEGRATED = PACKET / "integrated-model-v4.json"
INTEGRATED_SHA = "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e"
RAW = PACKET / "mixed-far-hole-raw-v2.json"
NDS = ROOT / (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-"
    "Dowel-type-fasteners.pdf"
)
NDS_SHA = "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
SUPPLEMENT = NDS.parent / "AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf"
SUPPLEMENT_SHA = "1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b"
CANDIDATE = "compact-floor-flush-thin-bolted-development"
N_PER_LBF = 4.4482216152605
RELEASE = {
    "candidate_accepted": False,
    "complete_joint_acceptance": False,
    "capacity_established": False,
    "fabrication_released": False,
    "structural_released": False,
    "climbing_released": False,
}
METHOD_SOURCES = {
    "nds": {
        "url": "https://awc.org/resources/2024-nds/",
        "cached_chapter_path": str(NDS.relative_to(ROOT)),
        "cached_chapter_sha256": NDS_SHA,
        "locators": [
            "12.3.1 / Table 12.3.1A-B, printed 91-92: six single-shear modes",
            "12.3.3-12.3.7, printed 92-95: bearing, direction, Fyb and threads",
            "12.3.9 / 12.5.1, printed 96-99: axial bearing and geometry",
            "12.6, printed 100: multiple-fastener load introduction and local stress",
        ],
    },
    "tr12": {
        "url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf",
        "locators": ["Table 1-1, printed 3", "Appendix A, printed 25-29"],
        "scope": "Published yielding method and material input derivation; no Eaton material or joint rating transfer.",
    },
    "eaton": {
        "url": "https://www.eaton.com/us/en-us/catalog/support-systems/strut-fittings-and-accessories.html",
        "scope": "ASTM A1018 minimum Fy 33000 psi statement; no published product Fu or bolt Fyb. The separate Fe scenario labels its additional inference and applicability conditions.",
    },
    "elasticity": {
        "url": "https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_05_fpl_gtr282.pdf",
        "locator": "Table 5-1, printed 5-2: Douglas-fir clear-wood elastic ratios at approximately 12% moisture",
        "scope": "Conditional orthotropic analogy only; no measured DF-L No.2 constants or growth-ring orientation.",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def vector(value, label: str) -> list[float]:
    require(isinstance(value, (tuple, list)) and len(value) == 3, f"{label}: require xyz")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in value),
            f"{label}: require finite numbers")
    return [float(v) for v in value]


def dot(first, second) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def unit(value) -> list[float]:
    v = vector(value, "axis")
    length = math.hypot(*v)
    require(length > 0, "zero axis")
    return [a / length for a in v]


def cross(first, second) -> list[float]:
    a, b, c = first
    d, e, f = second
    return [b * f - c * e, c * d - a * f, a * e - b * d]


def source_inputs() -> tuple[dict, dict, dict, dict]:
    """Fail closed on every source bound by the reviewed frozen outputs."""
    require(sha(LAYOUT) == LAYOUT_SHA, "frozen reviewed layout differs")
    require(sha(INTEGRATED) == INTEGRATED_SHA, "frozen integrated model differs")
    require(sha(NDS) == NDS_SHA, "authenticated NDS chapter differs")
    require(sha(SUPPLEMENT) == SUPPLEMENT_SHA, "authenticated NDS Supplement differs")
    layout, integrated, raw = [json.loads(p.read_text()) for p in (LAYOUT, INTEGRATED, RAW)]
    for report in (layout, integrated):
        require(report["candidate"] == CANDIDATE, "candidate identity differs")
        for path, expected in report["source_sha256"].items():
            require(sha(ROOT / path) == expected, f"bound source differs: {path}")
    contract = json.loads((ROOT / "thin-bolted-candidate.json").read_text())
    require(contract["candidate"] == CANDIDATE and contract["evidence"]["sha256"] == INTEGRATED_SHA,
            "development contract differs")
    require(all(contract["release"][k] is False for k in RELEASE), "unexpected release")
    axes = layout["installed_axes"]
    require(len(axes) == 70 and len({a["id"] for a in axes}) == 70, "physical shaft census differs")
    require(sum(bool(a["attachments"]) for a in axes) == 58, "new shaft census differs")
    require(sum(len(a["attachments"]) for a in axes) == 72, "flange attachment census differs")
    return layout, integrated, raw, contract


def resolved_action(force, grain, shaft) -> dict:
    """Signed decomposition on one specific wood member; no opposite-member reuse."""
    force, grain, shaft = vector(force, "member force"), unit(grain), unit(shaft)
    require(abs(dot(grain, shaft)) < 1e-8, "end-grain/oblique shaft requires a different method")
    q = unit(cross(grain, shaft))
    axial = dot(force, shaft)
    lateral = [f - axial * a for f, a in zip(force, shaft, strict=True)]
    magnitude = math.hypot(*lateral)
    parallel, transverse = dot(lateral, grain), dot(lateral, q)
    zero = 1e-10 * max(magnitude, 1.)
    theta = None if magnitude < zero else math.degrees(math.atan2(abs(transverse), abs(parallel)))
    return {
        "force_on_receiver_xyz_n": force,
        "grain_axis_xyz": grain,
        "axial_signed_n": axial,
        "lateral_xyz_n": lateral,
        "lateral_n": magnitude,
        "parallel_grain_signed_n": parallel,
        "cross_grain_signed_n": transverse,
        "cross_grain_axis_xyz": q,
        "load_to_grain_degrees": theta,
        "grain_loaded_end": None if abs(parallel) < zero else ("positive" if parallel > 0 else "negative"),
        "cross_grain_loaded_edge": None if abs(transverse) < zero else ("positive" if transverse > 0 else "negative"),
        "oblique_lateral_action": abs(parallel) >= zero and abs(transverse) >= zero,
    }


def end_geometry_factor(distance_mm: float, diameter_mm: float, category: str) -> dict:
    """One classified square-end factor only; never an oblique/global Cdelta."""
    require(type(distance_mm) in (int, float) and math.isfinite(distance_mm) and distance_mm >= 0,
            "end distance must be finite and nonnegative")
    require(type(diameter_mm) in (int, float) and math.isfinite(diameter_mm) and diameter_mm > 0,
            "diameter must be positive and finite")
    require(category in ("softwood_parallel_tension", "parallel_compression", "perpendicular"),
            "unclassified end category")
    low, full = ((3.5, 7.) if category == "softwood_parallel_tension" else (2., 4.))
    minimum, full_distance = low * diameter_mm, full * diameter_mm
    factor = None if distance_mm < minimum - 1e-6 else min(1., distance_mm / full_distance)
    return {"category": category, "actual_distance_mm": distance_mm,
            "minimum_distance_mm": minimum, "full_value_distance_mm": full_distance,
            "end_factor_only": factor,
            "status": "below_minimum" if factor is None else "classified_end_factor_only",
            "complete_geometry_factor": None}


def geometry_rows(layout: dict) -> list[dict]:
    rays = {r["axis_id"]: r for r in layout["grain_ray_end_diagnostic"]}
    rows = []
    for axis in layout["installed_axes"]:
        ray = rays.get(axis["id"])
        h = axis["hardware_scenario"]
        rows.append({
            "axis_id": axis["id"], "receiver_ids": axis["receivers"],
            "source": axis["source"], "diameter_mm": axis["diameter_mm"],
            "bore_diameter_mm": axis["bore_diameter_mm"],
            "point_xyz_mm": axis["point"], "axis_xyz": axis["direction"],
            "total_grip_mm": axis["grip_mm"],
            "before_plate_mm": axis["before_plate_mm"], "after_plate_mm": axis["after_plate_mm"],
            "attached_fittings": [{k: a[k] for k in ("angle_id", "duty_id", "flange", "receiver")}
                                  for a in axis["attachments"]],
            "metal_side_pattern": ("two_steel_sides_actions_not_assumed_symmetric"
                                  if len(axis["attachments"]) == 2 else
                                  "single_steel_side" if axis["attachments"] else "two_wood_members"),
            "grain_axis_xyz": None if ray is None else ray["grain_axis_xyz"],
            "raw_midshaft_grain_end_rays_mm": None if ray is None else ray["grain_ray_end_distances_mm"],
            "raw_end_markers_only": None if ray is None else {
                "softwood_tension_3p5D": ray["minimum_grain_ray_end_mm"] >= 3.5 * axis["diameter_mm"] - 1e-6,
                "softwood_tension_7D": ray["minimum_grain_ray_end_mm"] >= 7. * axis["diameter_mm"] - 1e-6,
            },
            "nominal_length_mm": axis["nominal_under_head_length_mm"],
            "thread_pitch_mm": 25.4 / h["threads_per_inch"],
            "actual_full_body_length_mm": None, "actual_thread_root_mm": None,
            "actual_Fyb_psi": None, "effective_NDS_diameter_mm": None,
            "signed_formal_finished_end_edge_status": "pending_signed_actions_and_finished_boundary_method",
            "retained_axis_demand_inherited": False,
        })
    return rows


def neighboring_holes(layout: dict) -> list[dict]:
    """Deduplicated physical axes, with actual grain/cross-grain separations."""
    rays = {r["axis_id"]: r for r in layout["grain_ray_end_diagnostic"]}
    by_member = defaultdict(list)
    for axis in layout["installed_axes"]:
        if axis["id"] in rays:
            by_member[axis["receivers"][0]].append(axis)
    output = []
    for member, axes in sorted(by_member.items()):
        for i, first in enumerate(axes):
            grain = unit(rays[first["id"]]["grain_axis_xyz"])
            cross_grain = unit(cross(grain, unit(first["direction"])))
            for second in axes[i + 1:]:
                if abs(abs(dot(unit(first["direction"]), unit(second["direction"]))) - 1.) > 1e-8:
                    continue
                delta = [a - b for a, b in zip(rays[second["id"]]["midpoint_xyz_mm"],
                                             rays[first["id"]]["midpoint_xyz_mm"], strict=True)]
                g, q = abs(dot(delta, grain)), abs(dot(delta, cross_grain))
                if math.hypot(g, q) > 150.:
                    continue
                d, ell = max(first["diameter_mm"], second["diameter_mm"]), min(first["grip_mm"], second["grip_mm"])
                row_spacing = 2.5 * d if ell / d <= 2 else 5 * d if ell / d >= 6 else (5 * ell + 10 * d) / 8
                output.append({
                    "member": member, "axis_ids": [first["id"], second["id"]],
                    "grain_separation_mm": g, "cross_grain_separation_mm": q,
                    "euclidean_plane_separation_mm": math.hypot(g, q),
                    "parallel_grain_row_spacing_minimum_mm": 1.5 * d,
                    "perpendicular_grain_rows_spacing_scenario_mm": row_spacing,
                    "perpendicular_grain_rows_margin_scenario_mm": q - row_spacing,
                    "row_spacing_ell_scenario_mm": ell,
                    "same_grain_row": q < 1e-5,
                    "same_cross_grain_row": g < 1e-5,
                    "connected_group_and_signed_direction_classified": False,
                    "formal_spacing_status": "pending_group_ownership_and_direction",
                    "limits": "Staggered axes and separate duties are not merged into one NDS group automatically; Euclidean spacing is not a row-rule substitution.",
                })
    return output


def washer_rows(layout: dict) -> list[dict]:
    """The ideal wood annulus applies only to ends directly seating on wood."""
    result = []
    for seat in layout["washer_seats"]:
        wood = seat["support_material"] == "wood"
        value = (dfl_axial_wood_bearing_reference_lbf(
            seat["od_mm"] / 25.4, seat["planned_support_opening_mm"] / 25.4,
            seat["id_mm"] / 25.4) * N_PER_LBF if wood else None)
        result.append({
            "axis_id": seat["axis_id"], "role": seat["role"],
            "support_material": seat["support_material"], "od_mm": seat["od_mm"],
            "id_mm": seat["id_mm"], "support_opening_mm": seat["planned_support_opening_mm"],
            "nominal_annulus_backed_fraction": seat["actual_annulus_backed_fraction"],
            "wood_Fc_perp_psi": 625. if wood else None,
            "ideal_full_contact_wood_annulus_reference_n": value,
            "duration_increase_applied_to_Fc_perp": False,
            "bearing_area_increase_credited": False,
            "washer_steel_spreading_resistance_n": None,
            "head_nut_thread_capacity_n": None, "complete_axial_resistance_n": None,
            "support_transfer": ("direct_wood_annulus_reference_only" if wood else
                                 "washer_on_angle_plate; wood_transfer_is_a_separate_plate_contact_path"),
            "actual_contact_or_parts_inspected": False,
        })
    return result


def single_shear_reference(axis: dict, action: dict, material: dict | None) -> dict:
    """All six yield modes, only with explicit complete scenario inputs."""
    required = ("scenario_id", "source", "steel_Fe_psi", "bolt_Fyb_psi",
                "full_body_diameter_in", "thread_root_diameter_in",
                "wood_thread_bearing_length_in", "steel_thread_bearing_length_in")
    missing = [key for key in required if not material or material.get(key) is None]
    if len(axis["attachments"]) != 1:
        return {"status": "unavailable_for_this_topology", "resistance_n": None,
                "missing": ["unequal_two_steel_side_member_yield_method_and_actions"
                            if axis["attachments"] else "two_member_bearing_lengths_and_grain_actions"],
                "symmetric_double_shear_assumed": False}
    if action["load_to_grain_degrees"] is None:
        return {"status": "zero_lateral_action", "resistance_n": None, "missing": []}
    if missing:
        return {"status": "material_inputs_unavailable", "resistance_n": None, "missing": missing}
    thickness = max(axis["before_plate_mm"], axis["after_plate_mm"])
    require(material["full_body_diameter_in"] * 25.4 <= axis["diameter_mm"] + 1e-6,
            "material full-body scenario exceeds reviewed occupied shaft")
    value = wood_steel_single_shear_reference(
        bolt_full_body_diameter_in=material["full_body_diameter_in"],
        bolt_thread_root_diameter_in=material["thread_root_diameter_in"],
        wood_thread_bearing_length_in=material["wood_thread_bearing_length_in"],
        steel_thread_bearing_length_in=material["steel_thread_bearing_length_in"],
        bolt_bending_yield_psi=material["bolt_Fyb_psi"], steel_bearing_psi=material["steel_Fe_psi"],
        wood_bearing_length_in=axis["grip_mm"] / 25.4, steel_thickness_in=thickness / 25.4,
        grain_load_angle_degrees=action["load_to_grain_degrees"],
    )
    z = value["reference_lateral_lbf"] * N_PER_LBF
    return {
        "status": "explicit_material_scenario_unadjusted_component_reference",
        "scenario_id": material["scenario_id"], "material_source": material["source"],
        "mode_values_n": {mode: n * N_PER_LBF for mode, n in value["reference_values_lbf"].items()},
        "governing_mode": value["governing_mode"],
        "effective_diameter_in": value["effective_bolt_diameter_in"],
        "wood_Fe_psi": value["wood_bearing_psi"], "single_fastener_reference_n": z,
        "witness_force_over_unadjusted_reference": action["lateral_n"] / z,
        "adjusted_joint_resistance_n": None, "joint_utilization": None,
        "CD": None, "CM": None, "Ct": None, "Cg": None, "Cdelta": None,
        "NDS_Fyb_or_actual_product_adopted": False,
    }


def required_fyb_for_single_shear(axis: dict, action: dict, material: dict, target_n: float) -> dict:
    """Invert the complete six-mode component at a fixed explicit diameter/Fe.

    All Fyb-independent bearing ceilings remain in the inversion. Increasing Fyb never
    repairs an exhausted wood/steel bearing mode or a different failure mode.
    """
    require(type(target_n) in (int, float) and math.isfinite(target_n) and target_n > 0,
            "target lateral force must be positive and finite")
    require(len(axis["attachments"]) == 1, "Fyb inversion requires one actual shear plane")

    def value(fyb):
        candidate_material = dict(material, bolt_Fyb_psi=fyb)
        return single_shear_reference(axis, action, candidate_material)

    ceiling = value(1e12)
    if ceiling["single_fastener_reference_n"] < target_n:
        return {"status": "fixed_bearing_geometry_cannot_carry_target",
                "required_Fyb_psi": None,
                "bearing_ceiling_reference_n": ceiling["single_fastener_reference_n"],
                "bearing_ceiling_governing_mode": ceiling["governing_mode"],
                "Fyb_independent_mode_ceilings_n": {mode: ceiling["mode_values_n"][mode]
                                                   for mode in ("Im", "Is", "II")},
                "complete_joint_utilization": None}
    low, high = 1e-3, 1e12
    for _ in range(90):
        mid = math.sqrt(low * high)
        if value(mid)["single_fastener_reference_n"] < target_n:
            low = mid
        else:
            high = mid
    final = value(high)
    return {"status": "required_material_parameter_for_component_only", "required_Fyb_psi": high,
            "target_lateral_force_n": target_n,
            "governing_mode_at_required_Fyb": final["governing_mode"],
            "fixed_effective_diameter_in": final["effective_diameter_in"],
            "fixed_steel_Fe_psi": material["steel_Fe_psi"],
            "spacing_group_axial_splitting_qualification": False,
            "complete_joint_utilization": None}


def shared_shaft_reference(axis: dict, attachment_actions: list[dict],
                           material: dict | None) -> dict:
    """Test same-state vector symmetry before entering the maintained method.

    A scalar sum or equal magnitudes do not establish NDS symmetry. This
    method keeps both flange datums and free moments, which are not assigned
    to the bolt as a bending demand without local load-path evidence.
    """
    require(len(axis["attachments"]) == len(attachment_actions) == 2,
            "shared-shaft check requires both physical flange actions")
    first, second = attachment_actions
    require(first["case_id"] == second["case_id"], "shared flange actions must be same-state")
    require(isinstance(first.get("state_id"), str) and first["state_id"].strip()
            and first["state_id"] == second.get("state_id"), "shared flange actions need one explicit state identity")
    seen = set()
    for row in attachment_actions:
        require(row.get("axis_id") == axis["id"], "shared witness belongs to a foreign shaft")
        matches = [a for a in axis["attachments"] if a["angle_id"] == row.get("angle_id")
                   and a["flange"] == row.get("flange") and a["receiver"] == row.get("receiver")]
        require(len(matches) == 1, "shared witness belongs to a foreign flange/member")
        key = (row["angle_id"], row["flange"])
        require(key not in seen, "duplicate shared physical flange")
        seen.add(key)
        require(math.dist(vector(row["point_xyz_mm"], "shared flange datum"), matches[0]["entry_xyz_mm"]) < 1e-5,
                "shared flange datum differs")
        checked = resolved_action(row["force_on_receiver_xyz_n"], row["grain_axis_xyz"], axis["direction"])
        theta = checked["load_to_grain_degrees"]
        require((theta is None and row["load_to_grain_degrees"] is None) or
                (theta is not None and row["load_to_grain_degrees"] is not None and
                 abs(theta - row["load_to_grain_degrees"]) < 1e-8),
                "shared grain/action angle differs")
    require(math.dist(unit(first["grain_axis_xyz"]), unit(second["grain_axis_xyz"])) < 1e-8,
            "shared receiver grain differs")
    forces = [vector(row["force_on_receiver_xyz_n"], "shared flange force")
              for row in attachment_actions]
    moments = [vector(row["free_attachment_moment_xyz_nmm"], "shared flange free moment")
               for row in attachment_actions]
    points = [vector(row["point_xyz_mm"], "shared flange datum")
              for row in attachment_actions]
    origin = axis["point"]
    resultant = [sum(force[i] for force in forces) for i in range(3)]
    eccentric = [sum(moment[i] + cross([p[j] - origin[j] for j in range(3)], force)[i]
                      for p, force, moment in zip(points, forces, moments, strict=True))
                 for i in range(3)]
    scale = max(math.hypot(*forces[0]), math.hypot(*forces[1]), 1.)
    equal_vectors = math.dist(*forces) <= 1e-8 * scale
    zero_free_couples = all(math.hypot(*moment) < 1e-7 for moment in moments)
    lateral_only = all(abs(dot(force, unit(axis["direction"]))) < 1e-8 * scale for force in forces)
    base = {"state_id": first["state_id"], "case_id": first["case_id"], "axis_id": axis["id"],
            "flange_actions": attachment_actions,
            "combined_force_on_receiver_xyz_n": resultant,
            "combined_external_moment_about_axis_point_xyz_nmm": eccentric,
            "equal_vector_side_actions_established": equal_vectors,
            "both_side_actions_lateral_only": lateral_only,
            "zero_free_attachment_couples": zero_free_couples,
            "free_attachment_couple_is_not_assigned_to_bolt_bending": True,
            "complete_common_shaft_response_established": False,
            "adjusted_joint_resistance_n": None, "joint_utilization": None,
            "two_single_shear_references_added": False}
    if not (equal_vectors and lateral_only and zero_free_couples):
        return {**base, "status": "unequal_or_axial_couple_pattern_outside_symmetric_NDS_method",
                "four_mode_reference_n": None,
                "required": "actual common-shaft lateral/contact/bending response under both recorded flange force vectors and couples"}
    required = ("scenario_id", "source", "steel_Fe_psi", "bolt_Fyb_psi",
                "full_body_diameter_in", "thread_root_diameter_in",
                "wood_thread_bearing_length_in", "steel_side_a_thread_bearing_length_in",
                "steel_side_b_thread_bearing_length_in")
    missing = [key for key in required if not material or material.get(key) is None]
    if missing:
        return {**base, "status": "symmetric_vector_pattern_material_inputs_unavailable",
                "four_mode_reference_n": None, "missing": missing}
    require(material["full_body_diameter_in"] * 25.4 <= axis["diameter_mm"] + 1e-6,
            "shared material full-body scenario exceeds reviewed occupied shaft")
    theta = first["load_to_grain_degrees"]
    if theta is None:
        return {**base, "status": "zero_lateral_action", "four_mode_reference_n": None}
    value = wood_steel_double_shear_reference(
        bolt_full_body_diameter_in=material["full_body_diameter_in"],
        bolt_thread_root_diameter_in=material["thread_root_diameter_in"],
        wood_thread_bearing_length_in=material["wood_thread_bearing_length_in"],
        steel_side_a_thread_bearing_length_in=material["steel_side_a_thread_bearing_length_in"],
        steel_side_b_thread_bearing_length_in=material["steel_side_b_thread_bearing_length_in"],
        bolt_bending_yield_psi=material["bolt_Fyb_psi"], steel_bearing_psi=material["steel_Fe_psi"],
        wood_bearing_length_in=axis["grip_mm"] / 25.4,
        steel_side_a_bearing_length_in=axis["before_plate_mm"] / 25.4,
        steel_side_b_bearing_length_in=axis["after_plate_mm"] / 25.4,
        grain_load_angle_degrees=theta, symmetric_side_actions_established=True)
    return {**base, "status": "vector_symmetric_conditional_four_mode_component_reference",
            "scenario_id": material["scenario_id"],
            "mode_values_n": {mode: load * N_PER_LBF for mode, load in value["reference_values_lbf"].items()},
            "governing_mode": value["governing_mode"],
            "four_mode_reference_n": value["reference_lateral_lbf"] * N_PER_LBF,
            "member_face_contact_is_an_explicit_unverified_scenario": True}


def generic_material_curves(layout: dict, finished: dict | None = None) -> dict:
    """Compute published generic-bolt/explicit steel-lower-bound scenarios.

    Generic Fyb45ksi is the TR12/NDS table reference, not the product's measured
    Fyb. For the conforming Fy33ksi Eaton hypothesis, Fu cannot be below tensile
    yield; TR12's AISC-bearing derivation gives Fe=2.4Fu/1.6. The explicit Fu33ksi
    lower-bound scenario therefore uses Fe49.5ksi, subject to metal-method and
    product applicability. It is not a substitution of Fy for Fe.
    """
    receivers = {} if finished is None else {
        (r["axis_id"], r["member"]): r for r in finished["receiver_boundary_geometry"]}
    curves = []
    for axis in layout["installed_axes"]:
        if not axis["attachments"]:
            continue
        receiver = axis["receivers"][0]
        length = receivers.get((axis["id"], receiver), {}).get("finished_full_wall_length_mm", axis["grip_mm"])
        for attachment in axis["attachments"]:
            plane = dict(axis, attachments=[attachment], grip_mm=length)
            for diameter_class, root_fraction in (("conditional_full_body", 1.),
                                                   ("explicit_0p8D_root_sensitivity", .8)):
                material = {
                    "scenario_id": f"generic_Fyb45ksi_Eaton_Fu33ksi_lower_bound_{diameter_class}",
                    "source": "AWC TR12 Table A2 generic >=3/8in bolt Fyb45ksi; Appendix A steel-bearing derivation; Eaton conditional ASTM A1018 Fy33ksi",
                    "steel_Fe_psi": 2.4 * 33000. / 1.6, "bolt_Fyb_psi": 45000.,
                    "full_body_diameter_in": axis["diameter_mm"] / 25.4,
                    "thread_root_diameter_in": root_fraction * axis["diameter_mm"] / 25.4,
                    "wood_thread_bearing_length_in": 0. if root_fraction == 1. else length / 25.4,
                    "steel_thread_bearing_length_in": 0.,
                }
                values = []
                for theta in (0., 45., 90.):
                    action = {"load_to_grain_degrees": theta, "lateral_n": 1.}
                    value = single_shear_reference(plane, action, material)
                    value.pop("witness_force_over_unadjusted_reference")
                    values.append({"angle_to_grain_degrees": theta, **value})
                curves.append({"axis_id": axis["id"], "angle_id": attachment["angle_id"],
                               "flange": attachment["flange"], "receiver": receiver,
                               "actual_physical_attachment_count": len(axis["attachments"]),
                               "member_bearing_length_scenario_mm": length,
                               "diameter_class": diameter_class,
                               "root_fraction_scenario": root_fraction,
                               "isolated_single_shear_plane_references": values,
                               "combined_shared_shaft_capacity_n": None,
                               "actual_material_or_thread_window_adopted": False})
    return {
        "scenario_status": "numerical_component_scenarios_only",
        "generic_bolt_Fyb_psi": 45000., "steel_Fu_lower_bound_scenario_psi": 33000.,
        "steel_Fe_from_AISC_nominal_bearing_divided_1p6_psi": 49500.,
        "steel_Fy_reused_as_Fe": False,
        "steel_parameter_basis_status": "conditional_inference_not_authenticated_Eaton_Fe",
        "steel_parameter_conditions": [
            "Exact fitting conforms to the stated ASTM A1018 minimum Fy33ksi material hypothesis.",
            "Fu>=Fy is an inference from tensile strength definitions, not a published product Fu.",
            "The AISC nominal hole-bearing route applies to the actual formed plate/detail.",
            "Complete metal design, hole edge/tear-out and deformation checks remain separate.",
        ],
        "Fyb_45ksi_is_published_table_basis_not_delivered_measurement": True,
        "root_0p8D_is_explicit_sensitivity_not_a_measured_or_standard_minimum": True,
        "angle_and_diameter_curves": curves,
        "limits": "Full-body requires the NDS thread exposure condition in every member. All actual metal side patterns remain recorded; isolated plane values are not summed into a symmetric or unequal shared-shaft capacity. Metal hole/bend checks and every other adjustment/failure mode remain separate.",
    }


def retained_wood_wood_curves(layout: dict, finished: dict) -> dict:
    """Fresh reference curves for the actual two-member retained shaft stacks.

    Each direction is one common lateral force vector with opposed member
    actions. Both actual grain directions enter bearing and reduction terms.
    Contact is an explicit scenario; a continuous geometric support union does
    not verify delivered face contact or actual thread-bearing occupancy.
    """
    receivers = {(r["axis_id"], r["member"]): r
                 for r in finished["receiver_boundary_geometry"]}
    rows = []
    for axis in layout["installed_axes"]:
        if axis["attachments"]:
            continue
        require(len(axis["receivers"]) == 2, "retained wood stack needs two separate members")
        first, second = [receivers[(axis["id"], member)] for member in axis["receivers"]]
        shaft, grain = unit(axis["direction"]), first["grain_axis_xyz"]
        q = unit(cross(grain, shaft))
        for diameter_class, fraction in (("conditional_full_body", 1.),
                                         ("explicit_0p8D_root_sensitivity", .8)):
            diameter = fraction * axis["diameter_mm"] / 25.4
            require(diameter >= .25, "retained scenario outside large-bolt range")
            values = []
            for orientation in (-45., 0., 45., 90.):
                radians = math.radians(orientation)
                force = [math.cos(radians) * a + math.sin(radians) * b
                         for a, b in zip(grain, q, strict=True)]
                actions = [resolved_action(force, first["grain_axis_xyz"], shaft),
                           resolved_action([-v for v in force], second["grain_axis_xyz"], shaft)]
                members = [{"member": receiver["member"],
                            "bearing_length_in": receiver["finished_full_wall_length_mm"] / 25.4,
                            "grain_axis_xyz": receiver["grain_axis_xyz"],
                            "load_to_grain_degrees": action["load_to_grain_degrees"],
                            "fe_theta_psi": dfl_dowel_bearing_psi(diameter, action["load_to_grain_degrees"])}
                           for receiver, action in zip((first, second), actions, strict=True)]
                reductions = _reduction_terms(diameter_in=diameter,
                    nominal_diameter_in=axis["diameter_mm"] / 25.4,
                    angle_max_degrees=max(a["load_to_grain_degrees"] for a in actions))
                modes = _single_shear_modes(members[0], members[1], diameter, 45000., reductions)
                mode_n = {key: value * N_PER_LBF for key, value in modes.items()}
                values.append({"lateral_direction_xyz": force,
                               "orientation_about_first_member_grain_degrees": orientation,
                               "members": members, "mode_values_n": mode_n,
                               "governing_mode": min(mode_n, key=mode_n.get),
                               "two_member_reference_n": min(mode_n.values()),
                               "adjusted_connection_resistance_n": None})
            rows.append({"axis_id": axis["id"], "diameter_class": diameter_class,
                         "effective_diameter_in": diameter,
                         "generic_Fyb_scenario_psi": 45000.,
                         "opposed_same_state_force_directions": values,
                         "actual_contact_and_thread_window_verified": False,
                         "historical_result_transferred": False})
    return {"scenario_status": "fresh_actual_stack_conditional_component_curves",
            "conditional_member_face_gap_mm": 0., "curves": rows,
            "limits": "All six two-member modes use actual separate finished bearing lengths and grain orientations. The generic Fyb45ksi table basis, delivered diameter/thread window and face-contact scenario remain unadopted; no retained-axis demand or complete-joint reserve is inherited."}


def compare_actions(layout: dict, payload: dict, materials: dict | None = None) -> list[dict]:
    """Compare signed same-state witnesses without elevating them to physical demand."""
    require(payload.get("candidate") == CANDIDATE, "fresh action candidate differs")
    require(payload.get("layout_sha256", payload.get("layout_report_sha256")) == LAYOUT_SHA,
            "fresh action geometry is not independently bound to reviewed v4")
    axes = {a["id"]: a for a in layout["installed_axes"]}
    rays = {r["axis_id"]: r for r in layout["grain_ray_end_diagnostic"]}
    seen, result = set(), []
    for source in payload.get("attachment_actions", []):
        state = source.get("state_id", payload.get("state_id"))
        require(isinstance(state, str) and bool(state.strip()), "signed witness requires explicit state_id")
        identity = (state, source["case_id"], source["axis_id"], source["angle_id"], source["flange"])
        require(identity not in seen, "duplicate signed attachment witness")
        seen.add(identity)
        require(source["axis_id"] in axes, "foreign shaft")
        axis = axes[source["axis_id"]]
        matches = [a for a in axis["attachments"] if a["angle_id"] == source["angle_id"]
                   and a["flange"] == source["flange"] and a["receiver"] == source["receiver"]]
        require(len(matches) == 1, "foreign flange/member")
        expected = matches[0]["entry_xyz_mm"]
        point = vector(source["point_xyz_mm"], "attachment point")
        require(math.dist(point, expected) < 1e-5, "attachment datum differs")
        action = resolved_action(source["force_on_receiver_xyz_n"],
                                 rays[axis["id"]]["grain_axis_xyz"], axis["direction"])
        end_side = action["grain_loaded_end"]
        distances = rays[axis["id"]]["grain_ray_end_distances_mm"]
        end_distance = None if end_side is None else distances[0 if end_side == "negative" else 1]
        moment = vector(source["moment_on_receiver_at_point_xyz_nmm"], "free attachment moment")
        result.append({
            "state_id": state, "case_id": source["case_id"], "axis_id": source["axis_id"],
            "angle_id": source["angle_id"], "flange": source["flange"],
            "receiver": source["receiver"], "point_xyz_mm": point,
            **action, "free_attachment_moment_xyz_nmm": moment,
            "raw_signed_loaded_grain_end_ray_mm": end_distance,
            "square_end_component_factor_diagnostic": (None if end_distance is None else
                end_geometry_factor(end_distance, axis["diameter_mm"], "softwood_parallel_tension")),
            "formal_finished_geometry_factor": None,
            "force_field_classification": payload.get("demand_status", "conditional_statics_witness_only"),
            "compatible_force_field_accepted": False,
            "reference": single_shear_reference(axis, action, None if materials is None else materials.get(axis["id"])),
            "complete_joint_disposition": "pending",
            "free_couple_is_not_bolt_bending_demand": True,
        })
    return result


def compare_shared_axes(layout: dict, witnesses: list[dict], materials: dict | None = None) -> list[dict]:
    by_axis = {axis["id"]: axis for axis in layout["installed_axes"]}
    groups = defaultdict(list)
    for witness in witnesses:
        if len(by_axis[witness["axis_id"]]["attachments"]) == 2:
            groups[(witness["state_id"], witness["case_id"], witness["axis_id"])].append(witness)
    result = []
    for (_, _, axis_id), rows in sorted(groups.items()):
        require(len(rows) == 2, "shared shaft lacks its second same-state flange witness")
        result.append(shared_shaft_reference(by_axis[axis_id], rows,
                       None if materials is None else materials.get(axis_id)))
    return result


def geometry_references(layout: dict, raw: dict) -> list[dict]:
    """Raw stock/net-one-bore and row values, never finished section capacities."""
    stock = {r["member"]: r for r in raw["takeoff_sensitivity"]["timber"]}
    rays = {r["axis_id"]: r for r in layout["grain_ray_end_diagnostic"]}
    values = []
    for axis in layout["installed_axes"]:
        if not axis["attachments"]:
            continue
        member = axis["receivers"][0]
        width, thickness = 139.7, axis["grip_mm"]
        require(math.isclose(stock[member]["blank_mm"][1], width, abs_tol=1e-6), "stock width differs")
        bore, end = axis["bore_diameter_mm"], rays[axis["id"]]["minimum_grain_ray_end_mm"]
        values.append({
            "axis_id": axis["id"], "member": member,
            "raw_full_section_area_mm2": width * thickness,
            "raw_one_bore_net_area_mm2": (width - bore) * thickness,
            "raw_one_bore_parallel_tension_reference_n": dfl_net_parallel_tension_reference_lbf(
                thickness / 25.4, width / 25.4, (bore / 25.4,)) * N_PER_LBF,
            "raw_nearest_end_one_bolt_row_tearout_reference_n": dfl_parallel_row_tear_out_reference_lbf(
                thickness / 25.4, 1, end / 25.4) * N_PER_LBF,
            "actual_finished_net_section_reference_n": None,
            "actual_connected_group_tearout_reference_n": None,
            "splitting_resistance_n": None,
            "capacity_applicable": False,
            "limits": "One raw bore at its center; neighboring bores, front service channels, rear recess, oblique ends and actual signed group are separate checks.",
        })
    return values


def finished_bore_wall_intervals(shape, point, direction, bore_radius_mm: float) -> dict:
    """Find the own full-circumference cylindrical walls in finished material.

    Raw receiver bounds may overlap an adjacent member's housed seat. They
    cannot supply the bearing length of that finished receiver. Partial walls
    are exposed but not promoted to a full bearing interval by this method.
    """
    import cadquery as cq
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    direction = direction.normalized()
    faces = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = BRepAdaptor_Surface(face.wrapped).Cylinder()
        origin = cq.Vector(cylinder.Location().X(), cylinder.Location().Y(), cylinder.Location().Z())
        axis = cq.Vector(cylinder.Axis().Direction().X(), cylinder.Axis().Direction().Y(),
                         cylinder.Axis().Direction().Z())
        delta = origin - point
        perpendicular = delta - direction.multiply(delta.dot(direction))
        if (abs(cylinder.Radius() - bore_radius_mm) > 1e-5 or
                abs(abs(axis.dot(direction)) - 1.) > 1e-8 or perpendicular.Length > 1e-5):
            continue
        parameters = [(vertex.Center() - point).dot(direction) for vertex in face.Vertices()]
        require(bool(parameters), "own bore face has no finite trim vertices")
        low, high = min(parameters), max(parameters)
        require(high > low + 1e-6, "zero-length cylindrical wall")
        theoretical_area = 2. * math.pi * bore_radius_mm * (high - low)
        fraction = face.Area() / theoretical_area
        faces.append({"interval_mm": [low, high], "wall_area_mm2": face.Area(),
                      "full_cylinder_area_mm2": theoretical_area,
                      "circumference_integral_fraction": fraction,
                      "full_circumference_wall": abs(fraction - 1.) <= 1e-6})
    require(bool(faces), "own matching bore wall is absent from finished timber")
    intervals = []
    for low, high in sorted(face["interval_mm"] for face in faces if face["full_circumference_wall"]):
        if intervals and low <= intervals[-1][1] + 1e-6:
            intervals[-1][1] = max(intervals[-1][1], high)
        else:
            intervals.append([low, high])
    return {"matching_cylindrical_faces": faces, "full_wall_intervals_mm": intervals,
            "full_wall_length_mm": sum(high - low for low, high in intervals),
            "partial_wall_present": any(not face["full_circumference_wall"] for face in faces),
            "qualified_directional_bearing_length_mm": None}


def exact_finished_geometry(cache_path: Path, layout: dict) -> dict:
    """Read the parent's one frozen BREP cache; query it without recreating CAD.

    Section planes include bolt centers and CAD face/vertex event stations.
    This is event sampling, explicitly not a proof of the continuous minimum.
    Own bores are restored only inside the matching raw solid for directional
    boundary queries; all other holes and service cuts remain in the query.
    """
    import cadquery as cq
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt

    from scripts.hl35_full_fit_candidate import line_span
    from scripts.wood_joint_wj12_sections import _section_measure

    cache = json.loads(cache_path.read_text())
    require(cache["candidate"] == CANDIDATE, "foreign BREP candidate")
    geometry_binding = cache.get("layout_sha256", cache.get("layout_report_sha256"))
    if geometry_binding is None:
        geometry_binding = cache.get("source_sha256", {}).get(str(LAYOUT.relative_to(ROOT)))
    require(geometry_binding == LAYOUT_SHA, "BREP cache does not bind reviewed layout")
    for path, expected in cache.get("source_sha256", {}).items():
        require(sha(ROOT / path) == expected, f"BREP source differs: {path}")
    parts = cache["parts"]
    require(isinstance(parts, list), "BREP parts must be an ordered list")
    parts = [dict(p, kind="finished_timber") if p.get("kind") == "timber" else p
             for p in parts]
    parts.extend(dict(p, id=p["member"], kind="raw_timber") for p in cache.get("raw_parts", []))
    by_kind = defaultdict(dict)
    pins = {str(cache_path.relative_to(ROOT)): sha(cache_path)}
    for part in parts:
        path = ROOT / part["path"]
        require(sha(path) == part["sha256"], f"BREP bytes differ: {part['id']}")
        if "grain_axis_xyz" not in part or part["grain_axis_xyz"] is None:
            continue
        shape = cq.Shape.importBrep(str(path))
        require(shape.isValid(), f"invalid BREP: {part['id']}")
        require(abs(shape.Volume() - part["volume_mm3"]) < max(.01, 1e-9 * shape.Volume()),
                f"BREP volume differs: {part['id']}")
        by_kind[part["kind"]][part["id"]] = (shape, unit(part["grain_axis_xyz"]))
        pins[part["path"]] = part["sha256"]
    raw_key = next((k for k in by_kind if k.startswith("raw")), None)
    finished_key = next((k for k in by_kind if k.startswith("finished")), None)
    require(raw_key is not None and finished_key is not None, "cache needs distinct raw and finished timber")
    raw, finished = by_kind[raw_key], by_kind[finished_key]
    require(len(raw) == len(finished) == 20 and set(raw) == set(finished), "twenty matched timber bodies required")

    def first_boundaries(shape, point, direction) -> dict:
        require(any(solid.isInside(point, 1e-6) for solid in shape.Solids()),
                "restored bore probe is not inside timber")
        query = IntCurvesFace_ShapeIntersector()
        query.Load(shape.wrapped, 1e-7)
        query.Perform(gp_Lin(gp_Pnt(*point.toTuple()), gp_Dir(*direction.toTuple())), -10000., 10000.)
        hits = sorted((query.WParameter(i), i) for i in range(1, query.NbPnt() + 1)
                      if abs(query.WParameter(i)) > 1e-6)
        sides = {}
        for side, candidates in (("negative", [(t, i) for t, i in hits if t < 0]),
                                 ("positive", [(t, i) for t, i in hits if t > 0])):
            require(bool(candidates), "finite directional boundary missing")
            t, index = min(candidates, key=lambda item: abs(item[0]))
            face = cq.Face(query.Face(index))
            normal, _ = face.normalAt(query.UParameter(index), query.VParameter(index))
            sides[side] = {"distance_mm": abs(t), "face_kind": face.geomType(),
                           "boundary_point_xyz_mm": list((point + direction.multiply(t)).toTuple()),
                           "face_normal_xyz": list(normal.toTuple()),
                           "square_to_query_direction": abs(normal.dot(direction)) > .999999}
        return sides

    receiver_rows, shaft_support = [], []
    for axis in layout["installed_axes"]:
        p, direction = cq.Vector(*axis["point"]), cq.Vector(*unit(axis["direction"]))
        support_intervals = []
        for member in axis["receivers"]:
            raw_shape, grain_array = raw[member]
            shape, checked_grain = finished[member]
            require(math.dist(grain_array, checked_grain) < 1e-8, "raw/finished grain differs")
            grain = cq.Vector(*grain_array)
            require(abs(grain.dot(direction)) < 1e-8, "bolt-axis/end-grain method gap")
            cross_grain = grain.cross(direction).normalized()
            raw_low, raw_high = line_span(raw_shape, p, direction)
            raw_low, raw_high = max(0., raw_low), min(axis["grip_mm"], raw_high)
            wall = finished_bore_wall_intervals(shape, p, direction, axis["bore_diameter_mm"] / 2.)
            intervals = [[max(0., low), min(axis["grip_mm"], high)]
                         for low, high in wall["full_wall_intervals_mm"]]
            require(intervals and all(high - low > 1e-6 for low, high in intervals),
                    "no fully supported own-bore wall interval; partial-wall method required")
            restored = shape
            for low, high in intervals:
                # The exact matching full cylindrical wall excludes a larger
                # recess. Never extend the restoration to the raw grip.
                own_bore = cq.Solid.makeCylinder(axis["bore_diameter_mm"] / 2.,
                                                high - low, p + direction.multiply(low), direction)
                restored = restored.fuse(own_bore.intersect(raw_shape)).clean()
                support_intervals.append({"member": member, "interval_mm": [low, high]})
            probes = []
            for low, high in intervals:
                for fraction in (.001, .25, .5, .75, .999):
                    point = p + direction.multiply(low + (high - low) * fraction)
                    probes.append({"bearing_interval_mm": [low, high], "bearing_fraction": fraction,
                                   "point_xyz_mm": list(point.toTuple()),
                                   "grain": first_boundaries(restored, point, grain),
                                   "cross_grain": first_boundaries(restored, point, cross_grain)})
            minima = {family: {side: min(probe[family][side]["distance_mm"] for probe in probes)
                               for side in ("negative", "positive")}
                      for family in ("grain", "cross_grain")}
            receiver_rows.append({
                "axis_id": axis["id"], "member": member,
                "grain_axis_xyz": grain_array, "cross_grain_axis_xyz": list(cross_grain.toTuple()),
                "raw_member_axis_interval_from_axis_point_mm": [raw_low, raw_high],
                "raw_member_axis_length_mm": raw_high - raw_low,
                "finished_bore_wall_audit": wall,
                "finished_full_wall_intervals_from_axis_point_mm": intervals,
                "finished_full_wall_length_mm": sum(high - low for low, high in intervals),
                "own_bore_restore_clipped_to_raw_timber": True,
                "own_bore_restore_restricted_to_matching_full_wall_intervals": True,
                "other_cuts_retained": True, "boundary_probes": probes,
                "sampled_minimum_distances_to_first_finished_boundary_mm": minima,
                "formal_NDS_end_edge_acceptance": False,
                "limits": "Five bearing-depth probes; first material boundary may be a service cut or neighboring hole, not a classified member end. Square/oblique face metadata is retained. No continuous end/edge minimum is proved.",
            })
        occupied = []
        for item in sorted(support_intervals, key=lambda item: item["interval_mm"]):
            low, high = item["interval_mm"]
            if occupied and low <= occupied[-1][1] + 1e-6:
                occupied[-1][1] = max(occupied[-1][1], high)
            else:
                occupied.append([low, high])
        gaps, cursor = [], 0.
        for low, high in occupied:
            if low > cursor + 1e-6:
                gaps.append([cursor, low])
            cursor = max(cursor, high)
        if cursor < axis["grip_mm"] - 1e-6:
            gaps.append([cursor, axis["grip_mm"]])
        shaft_support.append({"axis_id": axis["id"], "member_intervals": support_intervals,
                              "union_intervals_mm": occupied, "unsupported_nominal_grip_intervals_mm": gaps,
                              "full_nominal_grip_has_wood_wall_support": not gaps,
                              "contact_between_member_end_faces_verified": False})

    sections = []
    by_member_axes = defaultdict(list)
    for axis in layout["installed_axes"]:
        for member in axis["receivers"]:
            by_member_axes[member].append(axis)
    for member, (shape, grain_array) in sorted(finished.items()):
        raw_shape = raw[member][0]
        grain = cq.Vector(*grain_array)
        u = cq.Vector(1., 0., 0.) if abs(grain.x) < .9 else cq.Vector(0., 1., 0.)
        u = (u - grain.multiply(u.dot(grain))).normalized()
        v = grain.cross(u).normalized()
        # Vertices locate curve endpoints, faces locate circular-feature center
        # planes; bolt centers are explicit even if no vertex lies there.
        stations = {round(vertex.Center().dot(grain), 7) for vertex in shape.Vertices()}
        stations.update(round(face.Center().dot(grain), 7) for face in shape.Faces()
                        if face.geomType() in ("CYLINDER", "TORUS", "SPHERE"))
        stations.update(round(cq.Vector(*axis["point"]).dot(grain), 7)
                        for axis in by_member_axes[member])
        # Include midpoints between topology events. No claim that this finds a
        # continuous minimum or all stress-concentration/oblique-end sections.
        ordered = sorted(stations)
        stations.update(round((a + b) / 2., 7) for a, b in zip(ordered, ordered[1:]))
        values = []
        for station in sorted(stations):
            origin = grain.multiply(station)
            raw_measure = _section_measure(raw_shape, origin=origin, normal=grain, u_axis=u, v_axis=v)
            if raw_measure["area_mm2"] is None or raw_measure["area_mm2"] < 1e-4:
                continue
            measure = _section_measure(shape, origin=origin, normal=grain, u_axis=u, v_axis=v)
            area, raw_area = measure["area_mm2"], raw_measure["area_mm2"]
            require(area is not None and area <= raw_area + 1e-3, "finished area exceeds matching raw section")
            values.append({"station_global_grain_projection_mm": station,
                           "raw_area_mm2": raw_area, "finished_area_mm2": area,
                           "raw_area_retained_fraction": area / raw_area,
                           "bounds_uv_mm": measure["bounds_uv_mm"],
                           "parallel_tension_area_reference_n": 575. * area / 25.4**2 * N_PER_LBF,
                           "compatible_section_wrench_n_nmm": None,
                           "net_section_utilization": None})
        require(bool(values), f"no finite section samples: {member}")
        maximum_raw = max(row["raw_area_mm2"] for row in values)
        for row in values:
            row["raw_full_cross_section_plane"] = row["raw_area_mm2"] >= maximum_raw * (1. - 1e-6)
        full_cross_sections = [row for row in values if row["raw_full_cross_section_plane"]]
        sections.append({"member": member, "grain_axis_xyz": grain_array,
                         "sampled_sections": values,
                         "sampled_minimum_area_row": min(values, key=lambda row: row["finished_area_mm2"]),
                         "sampled_minimum_retained_fraction_row": min(values, key=lambda row: row["raw_area_retained_fraction"]),
                         "sampled_minimum_area_with_full_raw_cross_section_row": min(full_cross_sections, key=lambda row: row["finished_area_mm2"]),
                         "continuous_minimum_section_proved": False,
                         "fracture_or_splitting_capacity_established": False})
    return {"source_sha256": pins, "receiver_boundary_geometry": receiver_rows,
            "physical_shaft_wood_support": shaft_support,
            "finished_member_sections": sections,
            "method": "exact zero-thickness plane intersection using shared _section_measure; first line crossings excluding only the own bore",
            "native_solve_executed": False, "geometry_changed": False,
            "release": RELEASE}


def reused_finished_geometry(report_path: Path, producer_path: Path) -> tuple[dict, dict]:
    """Authenticate unchanged exact queries without repeating CAD sections.

    The source snapshot must recover the recorded producer bytes exactly.
    Every other recorded source remains current, and both geometry query
    functions must be byte-identical to this producer's implementations.
    """
    previous = json.loads(report_path.read_text())
    require(previous["candidate"] == CANDIDATE and previous["layout_report_sha256"] == LAYOUT_SHA,
            "reusable geometry candidate/layout differs")
    original_producer = "scripts/thin_bolted_timber_resistance.py"
    require(previous["source_sha256"][original_producer] == sha(producer_path),
            "reusable producer snapshot does not recover recorded bytes")
    for relative, expected in previous["source_sha256"].items():
        if relative != original_producer:
            require(sha(ROOT / relative) == expected, f"reusable source differs: {relative}")

    def functions(path):
        source = path.read_text()
        tree = ast.parse(source)
        return {node.name: ast.get_source_segment(source, node) for node in tree.body
                if isinstance(node, ast.FunctionDef)}

    old, new = functions(producer_path), functions(Path(__file__))
    names = ("finished_bore_wall_intervals", "exact_finished_geometry")
    require(all(old[name] == new[name] for name in names), "geometry query implementation changed; repeat required")
    pins = {str(path.resolve().relative_to(ROOT)): sha(path) for path in (report_path, producer_path)}
    metadata = {"input_report_path": str(report_path.resolve().relative_to(ROOT)),
                "input_report_sha256": sha(report_path),
                "producer_snapshot_path": str(producer_path.resolve().relative_to(ROOT)),
                "producer_snapshot_sha256": sha(producer_path),
                "unchanged_query_function_sha256": {name: hashlib.sha256(new[name].encode()).hexdigest()
                                                      for name in names},
                "all_recorded_nonproducer_sources_verified_unchanged": True,
                "CAD_section_queries_repeated": False}
    return copy.deepcopy(previous["finished_geometry_queries"]), {"pins": pins, "metadata": metadata}


def build_report(actions: Path | None = None, materials: Path | None = None,
                 geometry_cache: Path | None = None, reuse_geometry: Path | None = None,
                 geometry_producer: Path | None = None) -> dict:
    layout, integrated, raw, contract = source_inputs()
    sources = {str(p.relative_to(ROOT)): sha(p) for p in (
        LAYOUT, INTEGRATED, RAW, NDS, SUPPLEMENT, ROOT / "thin-bolted-candidate.json", Path(__file__),
        ROOT / "mini_moonboard/bolted_timber_checks.py",
        ROOT / "mini_moonboard/bolted_steel_wood_yield.py", ROOT / "fea/dowel_yield.py",
        ROOT / "mini_moonboard/bolted_steel_wood_double_shear.py",
        ROOT / "mini_moonboard/nds_2024_group_action.py", ROOT / "uv.lock",
        ROOT / "mini_moonboard/nds_2024_multi_member_bolt_yield.py",
    )}
    witnesses = []
    if actions:
        payload = json.loads(actions.read_text())
        scenarios = None if materials is None else json.loads(materials.read_text())
        witnesses = compare_actions(layout, payload, scenarios)
        for path in (actions, materials):
            if path:
                sources[str(path.resolve().relative_to(ROOT))] = sha(path)
    else:
        require(materials is None, "materials require a same-state signed action input")
    rows, pairs, washers = geometry_rows(layout), neighboring_holes(layout), washer_rows(layout)
    result = {
        "schema": "thin_bolted_timber_bolt_resistance/v1", "candidate": CANDIDATE,
        "revision": contract["revision"], "layout_report_sha256": LAYOUT_SHA,
        "question": "What timber/bolt component inputs and formal applicability are established for the reviewed thinner bolted frame?",
        "source_sha256": sources, "method_sources": METHOD_SOURCES,
        "load_basis": contract["load_basis"],
        "material_basis": {"wood": "declared DF-L No.2 solid-sawn stock",
                           "G": .50, "Ft_psi": 575., "Fv_psi": 180., "Fc_perp_psi": 625.,
                           "Fb_psi": 900., "Fc_psi": 1350., "E_psi": 1600000., "Emin_psi": 580000.,
                           "stock_classification": "Table 4A nominal2-4in dimension lumber, both 2x6 and4x6; not Table4D5x5+ timbers",
                           "six_inch_width_size_factors": {"Fb": 1.3, "Ft": 1.3, "Fc": 1.1},
                           "size_factor_included_in_raw_base_references": False,
                           "repetitive_member_factor_credited": False,
                           "conditional_Douglas_fir_elastic_ratios": {
                               "ET_over_EL": .050, "ER_over_EL": .068,
                               "GLR_over_EL": .064, "GLT_over_EL": .078, "GRT_over_EL": .007,
                               "clear_wood_analogy": True, "actual_constants_measured": False,
                               "radial_tangential_stock_orientation_verified": False},
                           "CD": 1., "CM": 1., "Ct": 1.,
                           "basis_status": "unadjusted_dry_normal_temperature_reference_inputs",
                           "actual_stock_inspected": False,
                           "bolt_Fyb_psi": None, "thread_root_mm": None, "steel_Fe_psi": None,
                           "steel_Fy_not_reused_as_Fe": True},
        "counts": {"physical_axes": len(rows), "new_axes": 58, "retained_frame_axes": 12,
                   "flange_attachments": 72, "single_steel_side_axes": 44,
                   "two_steel_side_axes": 14, "washer_ends": len(washers),
                   "direct_wood_washer_ends": sum(w["support_material"] == "wood" for w in washers),
                   "same_state_signed_attachment_witnesses": len(witnesses),
                   "accepted_complete_joints": 0},
        "axis_inputs": rows, "nearby_parallel_shaft_geometry": pairs,
        "raw_geometry_references": geometry_references(layout, raw),
        "washer_wood_interface_references": washers,
        "signed_witness_checks": witnesses,
        "signed_shared_shaft_checks": compare_shared_axes(layout, witnesses,
                                           scenarios if actions else None),
        "finished_member_geometry": integrated["finished_stock"],
        "failure_mode_disposition": {
            "individual_single_shear_yield": "all-six-mode generic45ksi/conditionalFe49.5ksi body/root component curves; actual product inputs and compatible signed load required",
            "unequal_two_steel_side_yield": "unavailable; neither two independent shafts nor symmetric double shear is assumed",
            "retained_twelve_wood_wood_bolts": "fresh two-member bearing/grain/demand checks required; historical pass not inherited",
            "NDS_end_edge_spacing": "signed source geometry available; finished oblique/cut-boundary and connected group applicability pending",
            "net_sections": "raw one-bore references only pending shared finished BREP queries and compatible section wrenches",
            "parallel_row_and_group_tearout": "raw single-row reference only; signed connected group plus critical finished shear/tension areas needed",
            "splitting": "NDS transverse tension prohibition/local-stress applicability and complete load path must be checked; no invented Ft_perp",
            "group_action": "maintained helper excludes steel-side/oblique patterns; no blanket Cg=1 assigned",
            "axial_load": "direct wood annulus reference separate from steel washer/angle spread, bolt/head/nut/thread and local fracture",
        },
        "remaining_inputs": [
            "Compatible fresh candidate same-state attachment, retained bolt and member-section force/moment fields.",
            "Explicit sourced bolt material/Fyb, body/root diameter and thread exposure per bearing member; nominal length is not shank.",
            "Eaton Fe derivation bound to product Fu and applicable metal method; Fy33ksi alone is insufficient.",
            "Finished-cut loaded boundaries, critical sections and connected-group shear/tension areas.",
            "Unequal two-side bolt response including both flange forces and bending, and complete washer/contact axial path.",
        ],
        "release": RELEASE, "native_solve_executed": False,
        "geometry_changed": False, "compatible_demands_accepted": False,
        "limits": [
            "Conditional component references supply no complete-joint reserve or physical release.",
            "Raw midshaft rays and nearest-end markers cannot qualify oblique end cuts or signed finished geometry.",
            "Static admissibility or minimum-force allocations are witnesses, not physical compatible demands or upper bounds.",
            "No CD1.6 increase is applied automatically; Fc-perp is not increased by load duration.",
            "No preload/friction resistance, actual inspection, floor anchor or verified no-slip support is claimed.",
        ],
    }
    require(not (geometry_cache and reuse_geometry), "choose new queries or authenticated reuse")
    require(bool(reuse_geometry) == bool(geometry_producer), "geometry reuse requires its exact producer snapshot")
    if geometry_cache is not None or reuse_geometry is not None:
        if reuse_geometry is not None:
            exact, reused = reused_finished_geometry(reuse_geometry.resolve(), geometry_producer.resolve())
            result["source_sha256"].update(reused["pins"])
            result["geometry_query_reuse"] = reused["metadata"]
            previous = json.loads(reuse_geometry.read_text())
            for relative, expected in previous["source_sha256"].items():
                if relative.startswith("fea/generated/") or relative.endswith("native-geometry-v4.json"):
                    result["source_sha256"][relative] = expected
        else:
            exact = exact_finished_geometry(geometry_cache.resolve(), layout)
            result["source_sha256"].update(exact.pop("source_sha256"))
        result["finished_geometry_queries"] = exact
        result["failure_mode_disposition"]["net_sections"] = (
            "actual finished zero-thickness event samples; continuous minimum and compatible section-wrench checks remain pending")
        for relative in ("scripts/wood_joint_wj12_sections.py", "scripts/hl35_full_fit_candidate.py"):
            result["source_sha256"][relative] = sha(ROOT / relative)
    result["generic_material_component_curves"] = generic_material_curves(
        layout, result.get("finished_geometry_queries"))
    if "finished_geometry_queries" in result:
        result["retained_wood_wood_component_curves"] = retained_wood_wood_curves(
            layout, result["finished_geometry_queries"])
        result["failure_mode_disposition"]["retained_twelve_wood_wood_bolts"] = (
            "fresh all-six-mode actual two-member bearing/grain scenario curves; actual materials/contact/threads and compatible demands remain pending")
    return result


def compact_report(report: dict, detail_path: Path, detail_sha256: str) -> dict:
    """Retain auditable controlling rows; put verbose event/probe output in cache."""
    result = copy.deepcopy(report)
    geometry = result.get("finished_geometry_queries")
    if geometry is None:
        return result
    for receiver in geometry["receiver_boundary_geometry"]:
        probes = receiver.pop("boundary_probes")
        receiver["boundary_probe_count"] = len(probes)
        controlling = {}
        for family in ("grain", "cross_grain"):
            controlling[family] = {}
            for side in ("negative", "positive"):
                probe = min(probes, key=lambda p: p[family][side]["distance_mm"])
                controlling[family][side] = {
                    "bearing_interval_mm": probe["bearing_interval_mm"],
                    "bearing_fraction": probe["bearing_fraction"],
                    "point_xyz_mm": probe["point_xyz_mm"],
                    "boundary": probe[family][side]}
        receiver["controlling_boundary_probes"] = controlling
    for member in geometry["finished_member_sections"]:
        member["sampled_section_count"] = len(member.pop("sampled_sections"))
    for curve in result["generic_material_component_curves"]["angle_and_diameter_curves"]:
        for value in curve["isolated_single_shear_plane_references"]:
            for key in ("status", "scenario_id", "material_source", "adjusted_joint_resistance_n",
                        "joint_utilization", "CD", "CM", "Ct", "Cg", "Cdelta",
                        "NDS_Fyb_or_actual_product_adopted"):
                value.pop(key)
    result["reproducible_detail_artifact"] = {
        "path": str(detail_path.resolve().relative_to(ROOT)), "sha256": detail_sha256,
        "kind": "ignored full probe/event result from the same source-bound producer",
        "retained_boundary_and_section_rows": "controlling sampled rows; complete event/probe arrays remain in the detail artifact",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actions", type=Path)
    parser.add_argument("--materials", type=Path)
    parser.add_argument("--geometry-cache", type=Path)
    parser.add_argument("--reuse-geometry", type=Path)
    parser.add_argument("--geometry-producer", type=Path)
    parser.add_argument("--detail-out", type=Path,
                        help="write complete probe/event output here and a compact tracked --out report")
    parser.add_argument("--out", type=Path, default=PACKET / "timber-bolt-resistance-v4.json")
    args = parser.parse_args()
    require(not args.out.exists(), "preserve distinct frozen timber resistance evidence")
    if args.detail_out:
        require(not args.detail_out.exists(), "preserve distinct frozen timber detail evidence")
        require(args.detail_out.resolve() != args.out.resolve(), "detail and compact reports need separate paths")
    report = build_report(args.actions, args.materials, args.geometry_cache,
                          args.reuse_geometry, args.geometry_producer)
    if args.detail_out:
        args.detail_out.parent.mkdir(parents=True, exist_ok=True)
        args.detail_out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        report = compact_report(report, args.detail_out, sha(args.detail_out))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "counts": report["counts"],
                      "actual_material_resistance": "unavailable", "release": report["release"]}, indent=2))


if __name__ == "__main__":
    main()
