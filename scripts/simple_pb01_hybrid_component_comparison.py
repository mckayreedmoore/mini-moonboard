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


def yield_component(root, side_length, angle):
    reduction = (10 * root + 0.5) * (1 + 0.25 * angle / 90)
    return wood_wood_single_shear_reference(
        main_bearing_length_in=1.5,
        side_bearing_length_in=side_length,
        main_load_to_grain_degrees=angle,
        side_load_to_grain_degrees=angle,
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
    for family, host, side_length, expected_axis, names in (
        (
            "upright",
            "base_principal_center_right",
            5.5,
            (1, 0, 0),
            ("pb01_upright_u1", "pb01_upright_u2"),
        ),
        (
            "rail",
            "base_rail_service_lower_right",
            2.25,
            (0, math.cos(math.radians(50)), math.sin(math.radians(50))),
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
            roots = {}
            for root in (0.189, 0.180):
                bounds = {
                    angle: yield_component(root, side_length, angle)
                    for angle in (0, 90)
                }
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
                }
            rows.append(
                {
                    "name": bolt["name"],
                    "installation_axis_host_to_cleat_xyz": bolt["axis_xyz"],
                    "force_on_host_xyz_n": bolt["force_on_host_xyz_n"],
                    "axial_on_host_n": axial,
                    "lateral_on_host_xyz_n": bolt["lateral_xyz_n"],
                    "lateral_on_host_magnitude_n": lateral,
                    "conditional_lateral_yield": roots,
                    "washer_positive_axial_reference_lbf": washer_lbf,
                    "washer_positive_axial_ratio": axial * N_TO_LBF / washer_lbf
                    if axial > 0
                    else None,
                    "unknowns": dict.fromkeys(UNKNOWN),
                }
            )
        interfaces[family] = {"host": host, "bolts": rows}
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
