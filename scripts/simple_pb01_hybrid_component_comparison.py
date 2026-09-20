"""Conditional PB01 a12-left bolt components from the frozen hybrid bundle."""

import json
import math

from mini_moonboard.bolted_timber_checks import dfl_axial_wood_bearing_reference_lbf
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from scripts.simple_pb01_hybrid_local_actions import (
    ARCHIVE_SHA256,
    CANDIDATE,
    REPORT_SHA256,
    extract,
)

N_TO_LBF = 0.22480894387096
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
UNKNOWN = (
    "bolt_axial_steel_nut",
    "washer_metal_stiffness",
    "group",
    "cleat",
    "contact",
)


def require(condition, label):
    if not condition:
        raise ValueError(label)


def angle_to_grain(lateral, grain):
    """Unsigned lateral force angle to a unit modeled grain axis, 0–90 degrees."""
    require(
        len(lateral) == len(grain) == 3
        and all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            for value in (*lateral, *grain)
        )
        and math.isclose(sum(value * value for value in grain), 1.0, abs_tol=1e-6),
        "Invalid lateral or grain axis",
    )
    magnitude = math.sqrt(sum(value * value for value in lateral))
    require(magnitude > 0, "Angle requires nonzero lateral force")
    cosine = abs(sum(a * b for a, b in zip(lateral, grain, strict=True))) / magnitude
    return math.degrees(math.acos(min(1.0, cosine)))


def yield_component(root, side_length, main_angle, side_angle):
    reduction = (10 * root + 0.5) * (1 + 0.25 * max(main_angle, side_angle) / 90)
    return wood_wood_single_shear_reference(
        main_bearing_length_in=1.5,
        side_bearing_length_in=side_length,
        main_load_to_grain_degrees=main_angle,
        side_load_to_grain_degrees=side_angle,
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=0.25,
        bolt_thread_root_diameter_in=root,
        main_thread_bearing_length_in=1.5,
        side_thread_bearing_length_in=side_length,
        bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=45_000, effective_diameter_in=root
        ),
        bolt_bending_yield_strength_psi=45_000,
        gap_in=0,
        reduction_terms=dict.fromkeys(MODES, reduction),
    )


def compare():
    """Fail on unexpected source/ownership; report components, never a joint verdict."""
    source = extract()  # Extractor authenticates archive, report, snapshots and case.
    require(
        source["scope"] == "diagnostic_only"
        and source["case"] == "a12-left"
        and source["candidate"] == CANDIDATE
        and source["archive_sha256"] == ARCHIVE_SHA256
        and source["report_sha256"] == REPORT_SHA256
        and source["proxy_station_count"] == 23,
        "PB01 source identity changed",
    )
    require(
        set(source["interfaces"]) == {"upright", "rail"},
        "PB01 interface identity changed",
    )
    washer_lbf = dfl_axial_wood_bearing_reference_lbf(0.734, 7.5 / 25.4, 0.312)
    interfaces = {}
    tangent = (0, math.cos(math.radians(50)), math.sin(math.radians(50)))
    normal = (0, -math.sin(math.radians(50)), math.cos(math.radians(50)))
    for (
        family,
        host,
        side_length,
        expected_axis,
        host_grain,
        row_grain,
        pitch_mm,
        names,
    ) in (
        (
            "upright",
            "base_principal_center_right",
            5.5,
            (1, 0, 0),
            tangent,
            normal,
            45.0,
            ("pb01_upright_u1", "pb01_upright_u2"),
        ),
        (
            "rail",
            "base_rail_service_lower_right",
            2.25,
            tangent,
            (1, 0, 0),
            (1, 0, 0),
            40.0,
            ("pb01_rail_r1", "pb01_rail_r2"),
        ),
    ):
        face = source["interfaces"][family]
        require(
            face["host"] == host and face["cleat"] == "base_cleat_pb01",
            "PB01 ownership changed",
        )
        require(
            tuple(b["name"] for b in face["bolts"]) == names,
            "PB01 bolt identity changed",
        )
        row_delta = [
            second - first
            for first, second in zip(
                face["bolts"][0]["point_xyz_mm"],
                face["bolts"][1]["point_xyz_mm"],
                strict=True,
            )
        ]
        row_pitch = math.sqrt(sum(value * value for value in row_delta))
        require(
            math.isclose(row_pitch, pitch_mm, abs_tol=0.01), "PB01 row pitch changed"
        )
        row_axis = [value / row_pitch for value in row_delta]
        require(
            math.isclose(
                abs(sum(a * b for a, b in zip(row_axis, row_grain, strict=True))),
                1.0,
                abs_tol=1e-5,
            ),
            "PB01 row direction changed",
        )
        rows = []
        for bolt in face["bolts"]:
            require(
                all(
                    math.isclose(a, b, abs_tol=1e-6)
                    for a, b in zip(bolt["axis_xyz"], expected_axis, strict=True)
                ),
                "PB01 installation axis changed",
            )
            axial = bolt["axial_n"]
            lateral = bolt["lateral_magnitude_n"]
            require(
                math.isfinite(axial) and math.isfinite(lateral) and lateral >= 0,
                "Invalid PB01 bolt action",
            )
            lateral_xyz = bolt["lateral_xyz_n"]
            require(
                math.isclose(
                    lateral,
                    math.sqrt(sum(value * value for value in lateral_xyz)),
                    abs_tol=1e-6,
                ),
                "PB01 lateral vector/magnitude differ",
            )
            host_angle = angle_to_grain(lateral_xyz, host_grain)
            cleat_angle = angle_to_grain(lateral_xyz, normal)
            roots = {}
            for root in (0.189, 0.180):
                bounds = {
                    angle: yield_component(root, side_length, angle, angle)
                    for angle in (0, 90)
                }
                modeled = yield_component(root, side_length, host_angle, cleat_angle)
                roots[f"{root:.3f}"] = {
                    "0deg_reference_lbf": bounds[0]["reference_lateral_lbf"],
                    "90deg_reference_lbf": bounds[90]["reference_lateral_lbf"],
                    "0deg_ratio": lateral
                    * N_TO_LBF
                    / bounds[0]["reference_lateral_lbf"],
                    "90deg_ratio": lateral
                    * N_TO_LBF
                    / bounds[90]["reference_lateral_lbf"],
                    "governing_mode_0deg": bounds[0]["governing_mode"],
                    "governing_mode_90deg": bounds[90]["governing_mode"],
                    "modeled_direction_reference_lbf": modeled["reference_lateral_lbf"],
                    "modeled_direction_ratio": lateral
                    * N_TO_LBF
                    / modeled["reference_lateral_lbf"],
                    "governing_mode_modeled_direction": modeled["governing_mode"],
                }
            rows.append(
                {
                    "name": bolt["name"],
                    "installation_axis_host_to_cleat_xyz": bolt["axis_xyz"],
                    "force_on_host_xyz_n": bolt["force_on_host_xyz_n"],
                    "axial_on_host_n": axial,
                    "lateral_on_host_xyz_n": bolt["lateral_xyz_n"],
                    "lateral_on_host_magnitude_n": lateral,
                    "host_grain_axis_xyz": host_grain,
                    "cleat_grain_axis_xyz": normal,
                    "host_load_to_grain_degrees": host_angle,
                    "cleat_load_to_grain_degrees": cleat_angle,
                    "row_to_lateral_degrees": angle_to_grain(lateral_xyz, row_axis),
                    "group_action_factor": None,
                    "conditional_lateral_yield": roots,
                    "washer_positive_axial_reference_lbf": washer_lbf,
                    "washer_positive_axial_ratio": axial * N_TO_LBF / washer_lbf
                    if axial > 0
                    else None,
                    "unknowns": dict.fromkeys(UNKNOWN),
                }
            )
        interfaces[family] = {
            "host": host,
            "row_axis_xyz": row_axis,
            "row_pitch_mm": row_pitch,
            "aligned_row_group_action_status": "unresolved_oblique_lateral_force",
            "bolts": rows,
        }
    return {
        "case": "a12-left",
        "scope": "diagnostic_one_cleat_23_old_proxies",
        "source_archive_sha256": ARCHIVE_SHA256,
        "proxy_station_count": 23,
        "washer_wood_bearing_basis": "0.734-in OD / 0.312-in ID / 7.5-mm bore; dry DF-L 625 psi; ideal full annulus",
        "interfaces": interfaces,
        "all_six_case_joint_verdicts": dict.fromkeys(CASES),
        "joint_utilization": None,
        "design_pass": None,
    }


if __name__ == "__main__":
    print(json.dumps(compare(), indent=2))
