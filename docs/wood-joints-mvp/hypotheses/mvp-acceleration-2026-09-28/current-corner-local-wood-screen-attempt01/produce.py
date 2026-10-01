#!/usr/bin/env python3
"""Reproduce the bounded geometry-only section inputs for BG001/BG003/BG045."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "section-screen.json"

PINS = {
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/bolt-groups.json":
        "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-finished-profile-attempt01/query.json":
        "32d3eb326cbd4e12e91f10418f340f2a9f21509f593e3f91421f10ae6aa574d2",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-three-member-profile-attempt01/query.json":
        "5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json":
        "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_spine.step":
        "081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_inner_frame_block.step":
        "9c7957e22686dff467f533f013172743c9bc8e7a9783331490b8e7c93d92e568",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-ec5-splitting-source-gap-attempt01/source-gap-decision.json":
        "1f4719e87de1b4738a259463b624310813080a12394318645c6a5c9b71668b94",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-wood-splitting-method-attempt01/README.md":
        "3c5b7ea8e1c56083d726933eb3e6cd850c605743dcbce8106a5cbff5afb6eb8f",
    "docs/wood-joints-mvp/wood-limit-state-basis.md":
        "1110e664a88f704773a463e83a2aeac3954b978048d811e4bff1effa55aa7c2e",
}


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def assert_close(actual: float, expected: float, *, tol: float = 1e-8) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol):
        raise AssertionError(f"{actual!r} != {expected!r} within {tol}")


def source_hashes() -> dict[str, str]:
    observed = {}
    for relative, expected in PINS.items():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if digest != expected:
            raise RuntimeError(f"source hash mismatch for {relative}: {digest}")
        observed[relative] = digest
    return observed


def bounds_for(manifest: dict, member_id: str) -> list[float]:
    matches = [m for m in manifest["physical_members"] if m["member_id"] == member_id]
    if len(matches) != 1:
        raise AssertionError(f"expected one physical member {member_id}, found {len(matches)}")
    return matches[0]["graph_finished_geometry_summary"]["bounds_xyz_mm"]


def selected_axes(groups: dict) -> dict[str, dict]:
    ids = {
        "knee_outer_left_post_1", "knee_outer_left_post_2",
        "knee_outer_left_side_1", "knee_outer_left_side_2",
        "knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2",
    }
    found = {a["axis_id"]: a for a in groups["candidate_axes"] if a["axis_id"] in ids}
    if set(found) != ids:
        raise AssertionError(f"corner axis inventory mismatch: {sorted(set(found) ^ ids)}")
    expected_groups = {
        "knee_outer_left_post_1": "BG001", "knee_outer_left_post_2": "BG001",
        "knee_outer_left_side_1": "BG003", "knee_outer_left_side_2": "BG003",
        "knee_outer_left_inner_header_1": "BG045",
        "knee_outer_left_inner_header_2": "BG045",
    }
    for axis_id, axis in found.items():
        if axis["group_id"] != expected_groups[axis_id]:
            raise AssertionError(f"unexpected group for {axis_id}")
        if not math.isclose(axis["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8):
            raise AssertionError(f"unexpected modeled shaft diameter for {axis_id}")
    return found


def ray_bore_diameter(profile: dict, group_id: str, member_id: str) -> float:
    rays = [r for r in profile["rays"] if r["group_id"] == group_id and r["member_id"] == member_id]
    if not rays:
        raise AssertionError(f"no profile rays for {group_id}/{member_id}")
    diameters = []
    for ray in rays:
        own = ray["initial_and_intermediate_void_intervals_mm"][0]
        assert_close(own[0], 0.0)
        diameters.append(2.0 * own[1])
    if any(not math.isclose(d, diameters[0], abs_tol=1e-8) for d in diameters):
        raise AssertionError("profile bore diameter is inconsistent")
    return diameters[0]


def verify_inner_block_crossbores(profile: dict, axes: dict[str, dict], bore_d: float) -> dict:
    """Reconcile the two X bores and two Z bores seen along sampled rays."""
    expected_y = sorted(
        axes[axis_id]["shaft_center_global_xyz_mm"][1]
        for axis_id in ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2")
    )
    observed_y = []
    x_bore_centers = []
    for axis_id in ("knee_outer_left_side_1", "knee_outer_left_side_2"):
        axis = axes[axis_id]
        x_bore_centers.append(axis["shaft_center_global_xyz_mm"])
        rays = [
            r for r in profile["rays"]
            if r["bolt_id"] == axis_id
            and r["member_id"] == "knee_outer_left_inner_frame_block"
            and r["axial_station_label"] == "mid_depth"
            and r["ray_label"] in ("e-", "e+")
        ]
        if len(rays) != 2:
            raise AssertionError(f"expected e+/e- mid-depth rays for {axis_id}")
        for ray in rays:
            intervals = ray["initial_and_intermediate_void_intervals_mm"]
            if len(intervals) != 2:
                raise AssertionError(f"expected one secondary Z-bore interval on {axis_id}/{ray['ray_label']}")
            lo, hi = intervals[1]
            assert_close(hi - lo, bore_d)
            direction_y = ray["ray_direction_global_xyz"][1]
            if not math.isclose(abs(direction_y), 1.0, abs_tol=1e-8):
                raise AssertionError("expected block e ray parallel to global Y")
            center_y = ray["ray_origin_global_xyz_mm"][1] + direction_y * ((lo + hi) / 2.0)
            observed_y.append(center_y)

    if len(observed_y) != 4:
        raise AssertionError("expected four ray observations of the BG045 Z bores")
    for y in expected_y:
        if sum(math.isclose(y, candidate, abs_tol=1e-7) for candidate in observed_y) != 2:
            raise AssertionError(f"BG045 center y={y} not independently seen by both BG003 stations")

    # The X-axis holes are full-width strips in an XY section. A Z-axis bore
    # circle does not overlap a strip if their y-center distance exceeds D.
    pairwise_separations = {
        axis_id: {
            "distances_to_BG045_bore_centers_mm": [
                abs(axes[axis_id]["shaft_center_global_xyz_mm"][1] - y)
                for y in expected_y
            ]
        }
        for axis_id in ("knee_outer_left_side_1", "knee_outer_left_side_2")
    }
    for axis_id, data in pairwise_separations.items():
        if min(data["distances_to_BG045_bore_centers_mm"]) <= bore_d:
            raise AssertionError(f"BG003/BG045 void overlap at {axis_id}; area union needs a new calculation")
    return {
        "bg045_bore_center_y_global_mm": expected_y,
        "ray_reconstructed_bg045_center_y_global_mm": sorted(observed_y),
        "bg003_x_bore_centers_xyz_mm": [
            axes[axis_id]["shaft_center_global_xyz_mm"]
            for axis_id in ("knee_outer_left_side_1", "knee_outer_left_side_2")
        ],
        "minimum_bg003_to_bg045_y_center_separation_mm": min(
            min(v["distances_to_BG045_bore_centers_mm"]) for v in pairwise_separations.values()
        ),
        "area_union_note": "At the two BG003 center planes, each X-hole strip spans the full modeled block width. Each BG045 circular bore is disjoint from that strip because its y-center separation exceeds one modeled bore diameter; the areas are subtracted once each.",
    }


def result() -> dict:
    hashes = source_hashes()
    acceleration = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    manifest_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    groups = read_json(acceleration + "bolt-groups/bolt-groups.json")
    bg001_profile = read_json(acceleration + "current-knee-finished-profile-attempt01/query.json")
    bg003_profile = read_json(acceleration + "current-knee-three-member-profile-attempt01/query.json")
    manifest = read_json(manifest_path)
    axes = selected_axes(groups)

    if len(bg001_profile["rays"]) != 48 or len(bg003_profile["rays"]) != 72:
        raise AssertionError("profile ray counts changed")
    if bg001_profile["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
        raise AssertionError("BG001 profile revision mismatch")
    if bg003_profile["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
        raise AssertionError("BG003 profile revision mismatch")

    # The source STEP bounds define modeled axis-aligned section envelopes;
    # the ray profiles identify bore tracks and mid-depth secondary-bore intervals.
    spine_bounds = bounds_for(manifest, "knee_outer_left_spine")
    block_bounds = bounds_for(manifest, "knee_outer_left_inner_frame_block")
    spine_width = spine_bounds[1] - spine_bounds[0]
    spine_depth = spine_bounds[3] - spine_bounds[2]
    block_width = block_bounds[1] - block_bounds[0]
    block_depth = block_bounds[3] - block_bounds[2]
    assert_close(spine_width, 38.1)
    assert_close(spine_depth, 139.7)
    assert_close(block_width, 88.9)
    assert_close(block_depth, 133.35)

    bore_d = ray_bore_diameter(bg001_profile, "BG001", "knee_outer_left_spine")
    assert_close(bore_d, 7.5)
    assert_close(ray_bore_diameter(bg003_profile, "BG003", "knee_outer_left_inner_frame_block"), bore_d)
    same_plane_voids = verify_inner_block_crossbores(bg003_profile, axes, bore_d)

    spine_gross = spine_width * spine_depth
    spine_x_bore_area = spine_width * bore_d
    spine_net = spine_gross - spine_x_bore_area
    block_gross = block_width * block_depth
    block_x_bore_strip = block_width * bore_d
    block_two_z_bores = 2.0 * math.pi * (bore_d / 2.0) ** 2
    block_net_bg003_center = block_gross - block_x_bore_strip - block_two_z_bores
    block_net_between_bg003_bores = block_gross - block_two_z_bores

    if not (axes["knee_outer_left_side_2"]["shaft_center_global_xyz_mm"][2]
            - axes["knee_outer_left_side_1"]["shaft_center_global_xyz_mm"][2] > bore_d):
        raise AssertionError("BG003 X-bore center planes are not separated")

    def stress_coeff(area_mm2: float) -> dict:
        return {
            "MPa_per_N_for_uniform_globalZ_tension": 1.0 / area_mm2,
            "MPa_per_kN_for_uniform_globalZ_tension": 1000.0 / area_mm2,
        }

    gap = read_json(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-ec5-splitting-source-gap-attempt01/source-gap-decision.json"
    )
    if gap["criterion_disposition"] != "pending" or gap["candidate_capacity"] is not None:
        raise AssertionError("splitting-method source gap status changed")

    return {
        "schema": "current_corner_local_wood_geometry_screen/v1",
        "status": "conditional geometry inputs reproduced; no wood capacity or pass/fail",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": {
            "introduced_groups_only": ["BG001", "BG003", "BG045"],
            "introduced_axis_count": 6,
            "members_screened": ["knee_outer_left_spine", "knee_outer_left_inner_frame_block"],
            "excludes": ["retained original frame/runner bolts", "base_post_outer_left", "base_side_left", "base_header", "other corner members"],
        },
        "source_hashes": hashes,
        "modeled_geometry_inputs": {
            "profile_query_ray_counts": {"BG001": 48, "BG003": 72},
            "modeled_bore_diameter_mm_from_profile_void_intervals": bore_d,
            "spine_XY_envelope_mm": [spine_width, spine_depth],
            "inner_block_XY_envelope_mm": [block_width, block_depth],
            "BG001_spine_bolt_centers_z_mm": [
                axes["knee_outer_left_post_1"]["shaft_center_global_xyz_mm"][2],
                axes["knee_outer_left_post_2"]["shaft_center_global_xyz_mm"][2],
            ],
            "BG003_spine_and_block_bolt_centers_z_mm": [
                axes["knee_outer_left_side_1"]["shaft_center_global_xyz_mm"][2],
                axes["knee_outer_left_side_2"]["shaft_center_global_xyz_mm"][2],
            ],
            "BG045_inner_block_bore_centers_xy_mm": [
                axes["knee_outer_left_inner_header_1"]["shaft_center_global_xyz_mm"][:2],
                axes["knee_outer_left_inner_header_2"]["shaft_center_global_xyz_mm"][:2],
            ],
            "same_section_plane_void_reconciliation": same_plane_voids,
            "oblique_base_side_profile": {
                "group": "BG003",
                "receiver": "base_side_left",
                "g_minus_terminal_face_global_z_mm": 277.0,
                "absolute_normal_dot_proposed_grain": 0.766044,
                "side1_e_plus_hits_oblique_end_side_corner": True,
                "consequence": "not converted to a rectangular row-area or splitting capacity; this is a three-member connection with an oblique middle-member termination",
            },
        },
        "candidate_net_section_inputs": [
            {
                "member_id": "knee_outer_left_spine",
                "applies_to_axes": [
                    "knee_outer_left_post_1", "knee_outer_left_post_2",
                    "knee_outer_left_side_1", "knee_outer_left_side_2",
                ],
                "section_plane": "XY at each distinct modeled X-bore center; normal to proposed +Z grain",
                "gross_envelope_area_mm2": spine_gross,
                "union_of_voids_area_mm2": spine_x_bore_area,
                "candidate_net_area_mm2": spine_net,
                "uniform_tension_stress_coefficient": stress_coeff(spine_net),
            },
            {
                "member_id": "knee_outer_left_inner_frame_block",
                "applies_to_axes": ["knee_outer_left_side_1", "knee_outer_left_side_2"],
                "section_plane": "XY through each BG003 X-bore center; includes that full-width X-bore strip and both BG045 Z-bore circles in the same section plane",
                "gross_envelope_area_mm2": block_gross,
                "union_of_voids_area_mm2": block_x_bore_strip + block_two_z_bores,
                "void_components_mm2": {
                    "one_BG003_X_bore_strip": block_x_bore_strip,
                    "two_BG045_Z_bore_circles": block_two_z_bores,
                    "overlap_subtracted_twice": 0.0,
                },
                "candidate_net_area_mm2": block_net_bg003_center,
                "uniform_tension_stress_coefficient": stress_coeff(block_net_bg003_center),
            },
            {
                "member_id": "knee_outer_left_inner_frame_block",
                "applies_to_axes": ["knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2"],
                "section_plane": "XY within the BG045 Z-axis bores and away from either BG003 X-bore center plane",
                "gross_envelope_area_mm2": block_gross,
                "union_of_voids_area_mm2": block_two_z_bores,
                "candidate_net_area_mm2": block_net_between_bg003_bores,
                "uniform_tension_stress_coefficient": stress_coeff(block_net_between_bg003_bores),
            },
        ],
        "conditional_method_mapping": {
            "possible_next_check": "NDS-2024 Appendix E.2 net-tension component Z'_NT = F'_t A_net, only if its applicability to the actual member action and net plane is demonstrated",
            "current_disposition": "geometry input only; no resistance or demand/capacity ratio",
            "splitting": "pending; no capacity, demand, pass, or failure calculated",
            "reason": "Existing source screen limits first-generation EC5 §8.1.4 corrected by AC:2006 to softwood and the Figure 8.1 connection arrangement. Applicability is not demonstrated for BG001's changed block joint, BG003's three-member stack with multiple orthogonal bore families and an oblique middle-member cut, or BG045's end-grain-axis block/header joint. The project has no selected EC5 edition/jurisdiction/NA or authenticated complete applicable clause/figure/factor set. NDS §§3.8.2 and 11.1.3 do not supply a general splitting formula for these topologies.",
        },
        "not_calculated": [
            "signed member N_z or other joint action; no actual force per unit can be inserted",
            "section bending stress or interaction; no net section modulus or moment distribution calculated",
            "adjusted F'_t or any other wood resistance; actual grade/species/condition and applicable factors are not established for these members",
            "row tear-out, group tear-out, bearing, splitting, washer pull-through, bolt axial action, or complete multi-member load transfer",
        ],
        "exact_missing_signed_group_wrench": {
            "components": ["Fx", "Fy", "Fz", "Mx", "My", "Mz"],
            "datum_and_sign_convention": "state a datum on each interface, give action on each named member and its equal/opposite reaction, and transport moments to a common datum before combining",
            "BG001": "post-to-spine interface wrench on the spine by the post (and equal/opposite wrench on the post)",
            "BG003": "separate wrenches on the spine, base_side_left, and inner_frame_block at the three-member stack/cuts; close force and moment equilibrium across the stack instead of assuming two independent pair groups",
            "BG045": "inner_frame_block-to-base_header interface wrench on the block by the header (and equal/opposite wrench on the header)",
            "simultaneous_effects": "include BG003 actions on the inner block when evaluating its BG045 section, plus all simultaneous group actions on each member",
        },
        "no_capacity_stop": "The geometric net-area and uniform-stress coefficients are not allowable/design values. The screen stops before capacity/DCR because signed local actions and member-specific adjusted strengths are not bound; splitting additionally lacks a demonstrated applicable method/topology mapping.",
    }


def main() -> int:
    value = result()
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if len(sys.argv) == 2 and sys.argv[1] == "--verify":
        if not OUT.exists() or OUT.read_text() != encoded:
            raise SystemExit("section-screen.json does not match source-pinned calculation; run produce.py")
        print("section-screen.json: source hashes, geometry inputs, and arithmetic verified")
        return 0
    if len(sys.argv) > 1:
        raise SystemExit("usage: python3 produce.py [--verify]")
    OUT.write_text(encoded)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
