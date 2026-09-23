"""Nominal combined-cut breakout map for vertical principal barrels.

The output maps actual signed rays, two candidate shear planes, net sections,
and splitting-sensitive ligaments.  It deliberately does not turn nominal
geometry or unadjusted wood values into an adopted connection capacity.
"""

from __future__ import annotations

import json
import math

import cadquery as cq

from scripts import owner_barrel_candidate_service as service
from scripts import owner_barrel_vertical_center_capacity as capacity
from scripts import owner_barrel_vertical_center_probe as probe
from scripts import owner_layout_protected as protected
from scripts.owner_barrel_coordinates import N, T, local_bounds

SCHEMA = "owner_barrel_vertical_center_breakout/v1"
SECTION_EPS_MM = 0.05
SHEAR_EPS_MM = (0.5, 0.25, 0.1, 0.05)
MAX_LAST_STEP_CHANGE_MM2 = 1.0


def _round(value, digits=6):
    return round(float(value), digits)


def _local_box(x_bounds, t_bounds, n_bounds):
    return cq.Solid.makeBox(
        x_bounds[1] - x_bounds[0],
        t_bounds[1] - t_bounds[0],
        n_bounds[1] - n_bounds[0],
        cq.Vector(x_bounds[0], t_bounds[0], n_bounds[0]),
    ).rotate((0, 0, 0), (1, 0, 0), math.degrees(math.atan2(T[1], T[0])))


def _combined_solids():
    """Build current host solids from every maintained and candidate cutter."""
    _, barrel, washer, bolt = probe._hardware()
    source, wood, seam = probe._source_geometry()
    post_geometry = probe._post_and_backer_geometry(wood, seam)
    joint = probe._joint_geometry(wood, post_geometry, barrel, washer, bolt)
    inventory = protected.inventory()["solids"]
    connections = {row.name: row for row in source.connections()}
    inherited = service.candidate_service_cutters(source, wood)
    additional = tuple(source.additional_machining_cutters())
    hosts = {
        "base_header",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    result = {}
    for member in hosts:
        shape = wood[member]
        counts = {
            "candidate_service": 0,
            "additional_machining": 0,
            "panel_screws": 0,
            "retained_frame_bolts": 0,
            "candidate_joint": 0,
        }
        for host, _name, cutter in inherited:
            if host == member:
                shape = shape.cut(cutter)
                counts["candidate_service"] += 1
        for additional_row in additional:
            host, cutter = additional_row[0], additional_row[-1]
            if host == member:
                shape = shape.cut(cutter)
                counts["additional_machining"] += 1
        for family, count_key in (
            ("panel_screws", "panel_screws"),
            ("frame_bolts", "retained_frame_bolts"),
        ):
            for name, cutter in inventory[family].items():
                connection = connections[name]
                if (
                    member in connection.members
                    and cutter.intersect(wood[member]).Volume() > 1e-6
                ):
                    shape = shape.cut(cutter)
                    counts[count_key] += 1
        for cutter in joint["cuts"][member]:
            shape = shape.cut(cutter)
            counts["candidate_joint"] += 1
        shape = shape.clean()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f"{member}: combined-cut solid invalid or disconnected")
        result[member] = {"shape": shape, "cut_counts": counts}
    return result, wood, joint, barrel


def _section_area(shape, raw, center_t, epsilon=SECTION_EPS_MM):
    bounds = local_bounds(raw)
    slab = _local_box(
        (bounds["x"][0] - 1, bounds["x"][1] + 1),
        (center_t - epsilon / 2, center_t + epsilon / 2),
        (bounds["n"][0] - 1, bounds["n"][1] + 1),
    )
    return shape.intersect(slab).Volume() / epsilon


def _plane_area(shape, raw, center_t, plane_n, end_t, sign, epsilon):
    bounds = local_bounds(raw)
    n_bounds = (
        (plane_n - epsilon, plane_n) if sign < 0 else (plane_n, plane_n + epsilon)
    )
    slab = _local_box(
        (bounds["x"][0] - 1, bounds["x"][1] + 1),
        (end_t, center_t),
        n_bounds,
    )
    return shape.intersect(slab).Volume() / epsilon


def _raw_end_t_at_n(raw, center_t, plane_n):
    """Return exact lower-grain polygon intercept for a fixed local N plane."""
    # Current principal lower face is horizontal at its minimum Z.  Intersect
    # z = t*Tz + n*Nz with that source-built face elevation.
    z_min = raw.BoundingBox().zmin
    end_t = (z_min - plane_n * N[1]) / T[1]
    if not end_t < center_t:
        raise ValueError("Signed lower-grain ray does not reach principal end")
    return end_t


def build_report():
    material, _hardware, _proxy, _selected_barrel, _washer, _bolt = (
        capacity._load_inputs()
    )
    combined, wood, joint, barrel = _combined_solids()
    raw_rays = {
        row["bolt"]: row
        for row in capacity._principal_raw_ray_distances(
            barrel, probe._hardware()[2], probe._hardware()[3]
        )
    }
    diameter = barrel["nominal_body_od_mm"]
    radius = diameter / 2
    fv_psi = material["reference_values"]["Fv_parallel"]["value"]
    fv_mpa = fv_psi * capacity.MPA_PER_PSI
    service_record = next(
        row
        for row in probe._source_geometry()[0].bore_records()
        if row["name"] == service.F1_G1_BORE
    )
    service_axis_yz = service_record["start_mm"][1:]
    candidate_service_radius = service.F1_G1_DIAMETER_MM / 2
    rows = []
    for record in joint["records"]:
        member = record["hosts"][1]
        raw = wood[member]
        shape = combined[member]["shape"]
        _x, y, z = record["thread_axis_xyz_mm"]
        center_t = y * T[0] + z * T[1]
        center_n = y * N[0] + z * N[1]
        rays = raw_rays[record["name"]]
        planes = []
        for sign in (-1, 1):
            plane_n = center_n + sign * radius
            end_t = _raw_end_t_at_n(raw, center_t, plane_n)
            convergence = [
                {
                    "epsilon_mm": epsilon,
                    "area_mm2": _round(
                        _plane_area(
                            shape,
                            raw,
                            center_t,
                            plane_n,
                            end_t,
                            sign,
                            epsilon,
                        )
                    ),
                }
                for epsilon in SHEAR_EPS_MM
            ]
            extrapolated = 2 * convergence[-1]["area_mm2"] - convergence[-2]["area_mm2"]
            planes.append(
                {
                    "cross_grain_sign": sign,
                    "plane_n_mm": _round(plane_n),
                    "signed_end_length_mm": _round(center_t - end_t),
                    "area_convergence": convergence,
                    "zero_thickness_linear_extrapolation_mm2": _round(extrapolated),
                    "last_step_change_mm2": _round(
                        abs(convergence[-1]["area_mm2"] - convergence[-2]["area_mm2"])
                    ),
                }
            )
        two_plane_area = sum(
            row["zero_thickness_linear_extrapolation_mm2"] for row in planes
        )
        split_end_t = _raw_end_t_at_n(raw, center_t, center_n)
        split_area = _plane_area(
            shape,
            raw,
            center_t,
            center_n,
            split_end_t,
            1,
            SECTION_EPS_MM,
        )
        raw_clear_ligaments = {
            "grain_positive": _round(rays["grain_positive_mm"] - radius),
            "grain_negative": _round(rays["grain_negative_mm"] - radius),
            "cross_grain_positive": _round(rays["cross_grain_positive_mm"] - radius),
            "cross_grain_negative": _round(rays["cross_grain_negative_mm"] - radius),
        }
        service_gap = None
        if member == service_record["member"]:
            service_gap = math.hypot(y - service_axis_yz[0], z - service_axis_yz[1]) - (
                radius + candidate_service_radius
            )
        rows.append(
            {
                "bolt": record["name"],
                "member": member,
                "local_center_tn_mm": [_round(center_t), _round(center_n)],
                "signed_raw_face_rays_mm": {
                    key: value for key, value in rays.items() if key.endswith("_mm")
                },
                "two_plane_shear_paths": planes,
                "two_plane_area_mm2": _round(two_plane_area),
                "awc_appendix_e_unadjusted_reference_n": _round(
                    fv_mpa * two_plane_area / 2
                ),
                "grain_normal_net_section_area_mm2": _round(
                    _section_area(shape, raw, center_t)
                ),
                "center_split_plane_area_mm2": _round(split_area),
                "raw_face_clear_ligaments_mm": raw_clear_ligaments,
                "minimum_raw_face_clear_ligament_mm": min(raw_clear_ligaments.values()),
                "candidate_service_bore_clear_gap_mm": (
                    _round(service_gap) if service_gap is not None else None
                ),
            }
        )
    t_values = [row["local_center_tn_mm"][0] for row in rows if "left" in row["bolt"]]
    n_values = [row["local_center_tn_mm"][1] for row in rows if "left" in row["bolt"]]
    maximum_step_change = max(
        plane["last_step_change_mm2"]
        for row in rows
        for plane in row["two_plane_shear_paths"]
    )
    if maximum_step_change > MAX_LAST_STEP_CHANGE_MM2 or any(
        row["two_plane_area_mm2"] <= 0
        or row["grain_normal_net_section_area_mm2"] <= 0
        or row["center_split_plane_area_mm2"] <= 0
        for row in rows
    ):
        raise ValueError("Nominal breakout section mapping failed convergence")
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "nominal signed combined-cut principal breakout map",
        "cut_inventory": {
            name: row["cut_counts"] for name, row in sorted(combined.items())
        },
        "row_geometry": {
            "global_y_pitch_mm": probe.PRINCIPAL_ROWS_Y_MM[1]
            - probe.PRINCIPAL_ROWS_Y_MM[0],
            "grain_t_stagger_mm": _round(abs(t_values[1] - t_values[0])),
            "cross_grain_n_stagger_mm": _round(abs(n_values[1] - n_values[0])),
            "bolt_bore_clear_gap_mm": _round(80.0 - probe.BOLT_BORE_DIAMETER_MM),
            "barrel_bore_clear_gap_mm": _round(80.0 - diameter),
            "mixed_bore_clear_gap_mm": _round(
                80.0 - (probe.BOLT_BORE_DIAMETER_MM + diameter) / 2
            ),
            "minimum_candidate_service_bore_clear_gap_mm": _round(
                min(
                    row["candidate_service_bore_clear_gap_mm"]
                    for row in rows
                    if row["candidate_service_bore_clear_gap_mm"] is not None
                )
            ),
        },
        "rows": rows,
        "mapping_quality": {
            "maximum_last_step_change_mm2": _round(maximum_step_change),
            "accepted_maximum_last_step_change_mm2": MAX_LAST_STEP_CHANGE_MM2,
            "all_mapped_areas_positive": True,
        },
        "decision": {
            "nominal_geometry_map": "MAPPED",
            "bearing_row_and_net_section": "REFERENCE_ONLY",
            "group_tearout": "UNRESOLVED_NOT_ENUMERATED",
            "tension_perpendicular_splitting": "UNSUPPORTED_RESISTANCE",
            "adverse_tolerance_geometry": "UNRESOLVED",
            "fresh_demand": "UNRESOLVED",
            "finite_decision": "EVIDENCE_BLOCKED",
            "diy_ready": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
        "limits": [
            "The Appendix E value is an unadjusted parallel-grain reference; this barrel action is 40 degrees to grain.",
            "A blind partial-width cross dowel is not an ordinary through bolt, and no connector capacity is transferred.",
            "The mapped center split plane has no adopted tension-perpendicular resistance.",
            "Nominal planar paths do not prove the globally minimum fracture surface or adverse-tolerance section.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
