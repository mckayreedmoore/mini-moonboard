#!/usr/bin/env python3
"""Reproduce a geometry-only BG001 axial/contact equilibrium envelope."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
SCREEN_REL = BASE / "current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json"
GEOMETRY_REL = BASE / "reduced-static-attempt01/contact-geometry.json"
OUTPUT = HERE / "axial-contact-bounds.json"
TOL = 2e-10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def subtract(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def close(a: list[float], b: list[float], tol: float = TOL) -> bool:
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def rect_weights(dy: float, dz: float, y_bounds: list[float], z_bounds: list[float]) -> list[float]:
    """Bilinear convex weights at LL, LH, HL, HH rectangle corners."""
    y0, y1 = y_bounds
    z0, z1 = z_bounds
    u = (dy - y0) / (y1 - y0)
    v = (dz - z0) / (z1 - z0)
    if not (-TOL <= u <= 1 + TOL and -TOL <= v <= 1 + TOL):
        raise ValueError(f"requested contact center ({dy}, {dz}) lies outside source envelope")
    return [(1 - u) * (1 - v), (1 - u) * v, u * (1 - v), u * v]


def read_inputs() -> tuple[dict, dict, dict, dict]:
    screen_path = ROOT / SCREEN_REL
    geometry_path = ROOT / GEOMETRY_REL
    screen = json.loads(screen_path.read_text())
    geometry = json.loads(geometry_path.read_text())
    patches = [
        patch
        for patch in geometry["contact_patches"]
        if set(patch["member_ids"]) == {"base_post_outer_left", "knee_outer_left_spine"}
    ]
    if len(patches) != 1:
        raise ValueError(f"expected one BG001 contact patch, found {len(patches)}")
    return screen, geometry, patches[0], {
        "screen_path": str(SCREEN_REL),
        "screen_sha256": sha256(screen_path),
        "contact_geometry_path": str(GEOMETRY_REL),
        "contact_geometry_sha256": sha256(geometry_path),
    }


def make_artifact() -> dict:
    screen, geometry, patch, direct_pins = read_inputs()
    group = screen["group"]
    ids = group["axis_ids_lower_to_higher_z"]
    bolt_centers = [group["axis_centers_global_xyz_mm"][axis_id] for axis_id in ids]
    centroid = group["group_centroid_global_xyz_mm"]
    face_x = patch["centroid_xyz_mm"][0]
    datum = [face_x, centroid[1], centroid[2]]
    lever = subtract(centroid, datum)
    pitch = group["modeled_inter_axis_pitch_mm"]
    z_offsets = [bolt_centers[i][2] - datum[2] for i in range(2)]

    # The JSON patch boundary contains four outer rectangle corners and two
    # circular hole boundaries. Pressure support uses only the four actual
    # outer contact corners; the holes are interior voids and do not change
    # this patch's convex hull.
    source_vertices = patch["vertices_xyz_mm"]
    outer = [source_vertices[i] for i in (0, 1, 4, 5)]
    y_values = sorted({point[1] - datum[1] for point in outer})
    z_values = sorted({point[2] - datum[2] for point in outer})
    if len(y_values) != 2 or len(z_values) != 2:
        raise ValueError("source patch outer corners do not form a rectangle")
    y_bounds, z_bounds = y_values, z_values
    by_name = {
        "y-low_z-low": [face_x, datum[1] + y_bounds[0], datum[2] + z_bounds[0]],
        "y-low_z-high": [face_x, datum[1] + y_bounds[0], datum[2] + z_bounds[1]],
        "y-high_z-low": [face_x, datum[1] + y_bounds[1], datum[2] + z_bounds[0]],
        "y-high_z-high": [face_x, datum[1] + y_bounds[1], datum[2] + z_bounds[1]],
    }
    corner_names = list(by_name)
    corner_points = [by_name[name] for name in corner_names]
    contact_area = patch["area_mm2"]
    outer_area = (y_bounds[1] - y_bounds[0]) * (z_bounds[1] - z_bounds[0])
    circles = [
        edge["circle"]["radius_mm"]
        for edge in patch["boundary_edges"]
        if edge["curve_type"] == "CIRCLE"
    ]
    area_from_voids = outer_area - sum(math.pi * radius * radius for radius in circles)
    if len(circles) != 2 or abs(area_from_voids - contact_area) > 2e-7:
        raise ValueError("source patch is not the pinned rectangular face with two circular voids")

    # On the spine (second member), a bolt in axial tension pulls toward the
    # first member (+X); unilateral contact pushes away (-X).
    bolt_columns = []
    for z in z_offsets:
        bolt_columns.append([1.0, z, 0.0])  # [Fx, My, Mz] per N tension
    contact_columns = []
    for point in corner_points:
        dy, dz = point[1] - datum[1], point[2] - datum[2]
        contact_columns.append([-1.0, -dz, dy])  # [Fx, My, Mz] per N compression

    def contact_reactions(total: float, center_dy: float, center_dz: float) -> dict[str, float]:
        weights = rect_weights(center_dy, center_dz, y_bounds, z_bounds)
        return {name: total * weight for name, weight in zip(corner_names, weights)}

    def make_witness(name: str, target: list[float], t1: float, t2: float,
                     contact_total: float, center_dy: float, center_dz: float) -> dict:
        reactions = contact_reactions(contact_total, center_dy, center_dz)
        forces: list[tuple[list[float], list[float]]] = []
        forces.append((bolt_centers[0], [t1, 0.0, 0.0]))
        forces.append((bolt_centers[1], [t2, 0.0, 0.0]))
        for corner, reaction in zip(corner_points, [reactions[n] for n in corner_names]):
            forces.append((corner, [-reaction, 0.0, 0.0]))
        resultant = [0.0, 0.0, 0.0]
        moment = [0.0, 0.0, 0.0]
        for point, force in forces:
            resultant = add(resultant, force)
            moment = add(moment, cross(subtract(point, datum), force))
        recovered = [resultant[0], moment[1], moment[2]]
        passed = close(recovered, target)
        if not passed:
            raise AssertionError(f"{name}: recovered {recovered}, target {target}")
        return {
            "wrench_at_contact_datum_Fx_My_Mz": target,
            "units": ["N", "N mm", "N mm"],
            "bolt_tensions_N": {ids[0]: t1, ids[1]: t2},
            "contact_compression_resultants_N_at_outer_corners": reactions,
            "contact_resultant_center_offset_yz_mm": [center_dy, center_dz],
            "recovered_force_xyz_N": resultant,
            "recovered_moment_xyz_N_mm": moment,
            "closure_passed": passed,
        }

    witnesses = {
        "unit_positive_axial_force": make_witness(
            "unit_positive_axial_force", [1.0, 0.0, 0.0], 0.5, 0.5, 0.0, 0.0, 0.0
        ),
        "unit_negative_axial_force": make_witness(
            "unit_negative_axial_force", [-1.0, 0.0, 0.0], 0.0, 0.0, 1.0, 0.0, 0.0
        ),
        "unit_positive_My_pure_couple": make_witness(
            "unit_positive_My_pure_couple", [0.0, 1.0, 0.0], 0.0, 1 / 73.8,
            1 / 73.8, 0.0, z_bounds[0]
        ),
        "unit_negative_My_pure_couple": make_witness(
            "unit_negative_My_pure_couple", [0.0, -1.0, 0.0], 1 / 67.45, 0.0,
            1 / 67.45, 0.0, z_bounds[1]
        ),
        "unit_positive_Mz_pure_couple": make_witness(
            "unit_positive_Mz_pure_couple", [0.0, 0.0, 1.0], 0.0, 1 / 95.25,
            1 / 95.25, 95.25, 21.025
        ),
        "unit_negative_Mz_pure_couple": make_witness(
            "unit_negative_Mz_pure_couple", [0.0, 0.0, -1.0], 1 / 38.1, 0.0,
            1 / 38.1, -38.1, -21.025
        ),
    }

    # A null equilibrium can be added to every feasible solution: equal bolt
    # tension t at both rows and 2t contact compression centered at the datum.
    # The corner weights expose the pressure-resultant closure envelope.
    null_weights = rect_weights(0.0, 0.0, y_bounds, z_bounds)
    null_mode = {
        "bolt_tension_N_per_t": {ids[0]: 1.0, ids[1]: 1.0},
        "contact_compression_resultants_N_per_t": {
            name: 2.0 * weight for name, weight in zip(corner_names, null_weights)
        },
        "contact_resultant_center_offset_yz_mm": [0.0, 0.0],
        "recovered_Fx_My_Mz_per_t": [0.0, 0.0, 0.0],
    }
    null_force = [0.0, 0.0, 0.0]
    null_moment = [0.0, 0.0, 0.0]
    for point, force in [
        (bolt_centers[0], [1.0, 0.0, 0.0]),
        (bolt_centers[1], [1.0, 0.0, 0.0]),
    ]:
        null_force = add(null_force, force)
        null_moment = add(null_moment, cross(subtract(point, datum), force))
    for point, weight in zip(corner_points, [null_mode["contact_compression_resultants_N_per_t"][n] for n in corner_names]):
        force = [-weight, 0.0, 0.0]
        null_force = add(null_force, force)
        null_moment = add(null_moment, cross(subtract(point, datum), force))
    null_mode["independent_recovered_force_xyz_per_t_N"] = null_force
    null_mode["independent_recovered_moment_xyz_per_t_N_mm"] = null_moment
    null_mode["closure_passed"] = close(null_force, [0.0, 0.0, 0.0]) and close(null_moment, [0.0, 0.0, 0.0])
    if not null_mode["closure_passed"]:
        raise AssertionError("self-equilibrated null mode failed closure")

    # Verify wrench translation in both directions with a synthetic check
    # vector; these numbers are a calculation fixture, not a frame demand.
    synthetic = {
        "force_xyz_N": [17.0, -23.0, 41.0],
        "moment_at_shaft_centroid_xyz_N_mm": [11.0, 29.0, -37.0],
    }
    translated_cross = cross(lever, synthetic["force_xyz_N"])
    synthetic_at_face = add(synthetic["moment_at_shaft_centroid_xyz_N_mm"], translated_cross)
    synthetic_back = subtract(synthetic_at_face, translated_cross)
    if not close(synthetic_back, synthetic["moment_at_shaft_centroid_xyz_N_mm"]):
        raise AssertionError("wrench datum transform failed round trip")

    target_cases = screen["missing_signed_group_wrench"]["six_case_signed_values"]
    artifact = {
        "artifact": "BG001 conditional axial-tension/contact equilibrium bounds",
        "schema": "wood_joint_bg001_axial_contact_bounds/v1",
        "candidate": screen["candidate"],
        "geometry_revision_id": screen["geometry_revision_id"],
        "status": "conditional equilibrium envelope only; accepted signed demand and capacities absent",
        "source_pins": {
            "direct_inputs": direct_pins,
            "contact_geometry_embedded_source_sha256": geometry["source_sha256"],
        },
        "scope": {
            "connection": "BG001: base_post_outer_left to knee_outer_left_spine",
            "action_side": "wrench exerted on knee_outer_left_spine by base_post_outer_left; equal-and-opposite on the other cut side",
            "included": "global X axial tension in the two modeled bolts plus compression-only global X contact resultants",
            "not_included": [
                "global Y/Z force and global X moment (these need a separate lateral-transfer map)",
                "friction, bolt shear, finite contact stiffness, installed gap/contact compatibility, or pressure limits",
                "any capacity, accepted frame demand, group resistance, or complete load-path acceptance",
            ],
        },
        "datum_transform": {
            "shaft_centroid_global_xyz_mm": centroid,
            "contact_datum_global_xyz_mm": datum,
            "shaft_centroid_minus_contact_datum_xyz_mm": lever,
            "formula": "M_contact = M_shaft_centroid + (shaft_centroid - contact_datum) cross F",
            "component_equations": {
                "Mx_contact_N_mm": "Mx_shaft_centroid_N_mm",
                "My_contact_N_mm": "My_shaft_centroid_N_mm - 11.049 * Vz_N",
                "Mz_contact_N_mm": "Mz_shaft_centroid_N_mm + 11.049 * Vy_N",
            },
            "synthetic_round_trip_fixture_not_a_frame_demand": {
                **synthetic,
                "cross_rF_N_mm": translated_cross,
                "moment_at_contact_datum_xyz_N_mm": synthetic_at_face,
                "round_trip_recovered_moment_at_shaft_centroid_xyz_N_mm": synthetic_back,
                "closure_passed": True,
            },
        },
        "contact_support_geometry": {
            "source_contact_patch_area_mm2": contact_area,
            "contact_plane_x_mm": face_x,
            "source_patch_member_ids": patch["member_ids"],
            "normal_on_spine_from_geometry_xyz": patch["normal_on_second_xyz"],
            "compression_force_on_spine_xyz": [-1.0, 0.0, 0.0],
            "shape_read_from_source": "outer rectangle with two interior circular bolt-hole voids",
            "outer_contact_convex_hull_corners_global_xyz_mm": {
                name: by_name[name] for name in corner_names
            },
            "outer_envelope_offsets_from_contact_datum_mm": {
                "y_low_high": y_bounds,
                "z_low_high": z_bounds,
            },
            "outer_area_mm2": outer_area,
            "circular_void_radii_mm": circles,
            "area_reconstruction_mm2": area_from_voids,
            "area_reconstruction_matches_source": abs(area_from_voids - contact_area) <= 2e-7,
            "resultant_envelope_note": (
                "The four outer corners are actual contact boundary points. Their convex hull is the ideal center-of-pressure closure for this face; the interior holes do not change that closure. Corner reactions are ideal statics resultants, not finite-area pressure fields or an installed contact law."
            ),
            "excluded_source_vertex_entries": [
                {
                    "source_vertex_index": i,
                    "global_xyz_mm": source_vertices[i],
                    "reason": "endpoint on a circular bolt-hole boundary; not a contact-pressure support point",
                }
                for i in (2, 3)
            ],
        },
        "conditional_equilibrium_map": {
            "variables": {
                ids[0]: "T1 >= 0 N tension on spine in global +X",
                ids[1]: "T2 >= 0 N tension on spine in global +X",
                "R_corner_i": "nonnegative ideal normal-compression resultant on spine in global -X at each outer corner",
            },
            "axis_centers_global_xyz_mm": {ids[i]: bolt_centers[i] for i in range(2)},
            "bolt_offsets_from_contact_datum_z_mm": {ids[i]: z_offsets[i] for i in range(2)},
            "pitch_mm": pitch,
            "vertex_column_order": [ids[0], ids[1], *[f"R_{name}" for name in corner_names]],
            "vertex_wrench_columns_Fx_My_Mz_per_N": [*bolt_columns, *contact_columns],
            "equilibrium_equations": [
                "Fx = T1 + T2 - sum(R_corner)",
                "My = z1*T1 + z2*T2 - sum(dz_corner*R_corner)",
                "Mz = sum(dy_corner*R_corner)",
            ],
            "units": {"Fx": "N", "My": "N mm", "Mz": "N mm", "T_and_R": "N", "dy_dz": "mm"},
            "signed_unit_wrench_witnesses": witnesses,
            "closure_checks_passed": all(row["closure_passed"] for row in witnesses.values()),
            "self_equilibrated_tension_contact_mode": null_mode,
            "action_bounds_without_a_demand_or_stiffness_law": {
                "for_each_feasible_fixed_Fx_My_Mz_wrench": {
                    "minimum_T1_or_T2": "depends on the specified wrench; no accepted wrench is available",
                    "maximum_T1_and_T2": "unbounded in this equilibrium-only model because any nonnegative multiple of the recorded self-equilibrated mode can be added",
                },
                "for_each_signed_unit_basis_wrench_shown": "witnesses establish equilibrium feasibility only; they do not identify a unique bolt allocation",
                "capacity_interpretation": "none; unbounded is an equilibrium indeterminacy, not predicted physical bolt force or capacity",
            },
        },
        "bolt_only_comparison": {
            "actual_tension_only_map_if_contact_is_omitted": {
                "equations": [
                    "Fx = T1 + T2",
                    "My = (pitch/2) * (T2 - T1)",
                    "Mz = 0",
                    "T1,T2 >= 0",
                ],
                "representability_conditions": "Fx >= 0, Mz = 0, and |My| <= (pitch/2)*Fx",
                "pure_couple_at_Fx_zero": "only My = 0 is representable; no nonzero pure My or Mz couple",
            },
            "signed_collinear_axial_pair_geometry_only": {
                "equations": ["Fx = A1 + A2", "My = (pitch/2)*(A2-A1)", "Mz = 0"],
                "pure_My_couple_actions_if_bilateral_axial_reactions_were_assumed": "A1 = -My/pitch; A2 = +My/pitch",
                "status": "kinematic reference only; the source model permits tension-only bolts and gives no bolt compression mechanism or resistance",
                "Mz": "impossible from the collinear bolt axial-force line alone",
            },
            "with_face_contact": {
                "pure_Fx_zero_couple_envelope_per_equal_total_tension_and_contact_R_N": {
                    "My_over_R_mm": [-67.45, 73.8],
                    "Mz_over_R_mm": [-38.1, 95.25],
                    "basis": "bolt tension centroid z in [-21.025,+21.025] mm; contact center y,z lies in the outer-face convex hull",
                },
                "minimum_total_bolt_tension_for_zero_Fx_pure_couple": {
                    "positive_My_N_per_N_mm": 1 / 73.8,
                    "negative_My_N_per_N_mm_magnitude": 1 / 67.45,
                    "positive_Mz_N_per_N_mm": 1 / 95.25,
                    "negative_Mz_N_per_N_mm_magnitude": 1 / 38.1,
                    "for_1_N_m_moment_N": {
                        "positive_My": 1000 / 73.8,
                        "negative_My": 1000 / 67.45,
                        "positive_Mz": 1000 / 95.25,
                        "negative_Mz": 1000 / 38.1,
                    },
                    "interpretation": "minimum total tie tension in this ideal equilibrium envelope when contact compression equals total tension; no finite maximum follows because a self-equilibrated mode exists",
                },
                "representability": "both signs of pure My and pure Mz have explicit zero-Fx witness equilibria above; therefore bolt-only Mz impossibility does not apply when face contact participates",
            },
        },
        "missing_accepted_demand": {
            "reference_point": "shaft centroid before the datum transform",
            "interface": "wrench on knee_outer_left_spine by base_post_outer_left",
            "units": ["N", "N", "N", "N mm", "N mm", "N mm"],
            "component_order": ["Fx", "Vy", "Vz", "Mx", "My", "Mz"],
            "cases": {
                case_id: {key: None for key in ("F_x_N", "V_y_N", "V_z_N", "M_x_N_mm", "M_y_N_mm", "M_z_N_mm")}
                for case_id in target_cases
            },
            "dependency": "accepted signed cut wrench for all six cases, including cut side and sign convention; current upstream panel wrenches are not BG001 actions",
        },
        "missing_resistance_and_compatibility_inputs": [
            "Delivered bolt grade, thread location through both shear planes, tensile area/yield/rupture basis, and actual head/nut/washer geometry and seating; no bolt tension resistance is assigned.",
            "Actual receiver species, grade, moisture, grain orientation, edge/end distances, net section, perpendicular-to-grain tension, splitting, and local head/washer bearing; no wood anchorage or crushing resistance is assigned.",
            "Verified interface fit/gap and whether the modeled face is closed under each signed load; no active contact law, stiffness, or pressure topology is supplied.",
            "Finite-area pressure/edge-bearing limit and load sharing between the two tension bolts and contact face; ideal corner resultants establish equilibrium closure only.",
            "Separate signed Vy, Vz, and Mx load-transfer resultants, their bolt/contact sharing and capacities, and a path-complete wrench transfer into downstream members/supports.",
        ],
        "nonclaims": [
            "not an actual frame demand or capacity check",
            "not a predicted or unique per-bolt tension split",
            "not a contact pressure solution, finite-pressure traction realization, or installed unilateral-contact law",
            "not acceptance of BG001 or the candidate",
        ],
    }
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    content = json.dumps(make_artifact(), indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(content)
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return 0
    if not OUTPUT.exists() or OUTPUT.read_text() != content:
        print("verification failed: generated JSON differs from the packet")
        return 1
    print("verification passed: source pins, datum transform, witness force/moment closure, and equilibrium-only bounds reproduce")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
