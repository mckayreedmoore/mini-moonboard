"""Compare finished six-inch PB01 tension-only native cases as components only."""

import hashlib
import json
import math
import zipfile
from pathlib import Path

from scripts.simple_pb01_hybrid_component_comparison import (
    N_TO_LBF,
    angle_to_grain,
    yield_component,
)
from scripts.simple_pb01_hybrid_local_actions import dot, vector, wrench
from scripts.simple_pb01_short_tension_evidence import verify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/bolted-candidate-evidence"
RUNS = {
    "a12-left": EVIDENCE / "pb01-short-tension-a12-165adbf-evidence.zip",
    "k12-right": EVIDENCE / "pb01-short-tension-k12-165adbf-evidence.zip",
}
ARCHIVE_SHA256 = {
    "a12-left": "4a3a700222fb8335fa8365339be5b1f3b0a72df0e803c91ee894729546c3dfa8",
    "k12-right": "e5fafb5fd56bf73901d7438e38304a378344808b57840a8632b16c937cfedd7c",
}
COMPARISON = EVIDENCE / "pb01-short-tension-a12-k12-165adbf-comparison.json"
COMPARISON_SHA256 = "09df8d9f7e59f1518c41c65942d6aebf02a2ccaf5b7b5373fb41d63f4038d194"
REPORT_SHA256 = {
    "a12-left": "1219b3718ef31ecb65de4a58044a8037a06a13e601b3d16750bedc40dc097576",
    "k12-right": "4d098ea43353f24eb7c8a5eacea749755879b581df61862f0a1c132e4747d0fc",
}
CANDIDATE = "pb01-kerf-right-cleat-quarter-short-hybrid-preparation-only"
HOSTS = {
    "upright": "base_principal_center_right",
    "rail": "base_rail_service_lower_right",
}
BOLTS = {
    "upright": ("pb01_upright_u1", "pb01_upright_u2"),
    "rail": ("pb01_rail_r1", "pb01_rail_r2"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_json(raw, digest, label):
    require(
        hashlib.sha256(raw).hexdigest() == digest, f"Source digest changed: {label}"
    )
    return json.loads(raw)


def read_case(case, path):
    """Bind one verified retained archive to its case and final-cycle audit."""
    require(
        hashlib.sha256(path.read_bytes()).hexdigest() == ARCHIVE_SHA256[case],
        f"Archive digest changed: {path}",
    )
    require(verify(path)["case"] == case, "PB01 archive case changed")
    with zipfile.ZipFile(path) as bundle:
        report = checked_json(bundle.read("report.json"), REPORT_SHA256[case], "report")
        artifacts = report["artifact_sha256"]
        inputs = checked_json(
            bundle.read("cycle-13/input.json"),
            artifacts["cycle-13/input.json"],
            "final input",
        )
        cycle = checked_json(
            bundle.read("cycle-13/report.json"),
            artifacts["cycle-13/report.json"],
            "final report",
        )
        scope = checked_json(
            bundle.read("diagnostic-scope.json"),
            artifacts["diagnostic-scope.json"],
            "scope",
        )
    require(
        report["candidate"] == inputs["candidate"] == CANDIDATE
        and scope["case"] == report["diagnostic_scope"]["case"] == case
        and report["diagnostic_scope"] == scope
        and inputs["hold"] == ("A12" if case == "a12-left" else "K12")
        and inputs["pb01_pose_variant"]
        == scope["pb01_pose_variant"]
        == "quarter_short",
        "PB01 short case or scope changed",
    )
    require(
        scope["diagnostic_only"] is True
        and scope["v4_same_case_demand"] is False
        and scope["qualified_for_design"] is False
        and scope["drilling_released"] is False
        and report["qualified_for_design"] is False
        and report["actual_joint_demands_qualified"] is False
        and inputs["preparation_only"] is True
        and inputs["pb01_same_case_demand"] is False,
        "PB01 short scope no longer provisional",
    )
    require(
        scope["pb01_axial_law"]
        == report["pb01_axial_law"]
        == inputs["pb01_axial_law"]
        == "tension_only_no_preload"
        and scope["pb01_face_contact_law"] == "compression_only"
        and all(
            report[key] is True
            for key in (
                "numerically_accepted",
                "contact_active_set_converged",
                "axial_tension_active_set_converged",
                "axial_tension_assumption_passed",
                "closed_bearing_assumption_passed",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
                "mpc_check_passed",
            )
        ),
        "PB01 short law or numerical acceptance changed",
    )
    require(
        all(
            cycle[key] == report[key]
            for key in (
                "force_residual_n",
                "moment_residual_nmm",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
                "axial_tension_assumption_passed",
                "closed_bearing_assumption_passed",
            )
        )
        and max(map(abs, vector(report["force_residual_n"], "force residual"))) <= 0.1
        and max(map(abs, vector(report["moment_residual_nmm"], "moment residual")))
        <= 2,
        "PB01 short final-cycle audit changed",
    )
    proxies = inputs["legacy_proxy_stations"]
    require(
        len(proxies) == len(set(proxies)) == scope["old_ml24z_sds_proxy_stations"] == 23
        and {row["name"] for row in inputs["angle_stations"]} == set(proxies)
        and {row["name"] for row in report["angle_stations"]} == set(proxies)
        and scope["pb01_cleat_station"] not in proxies,
        "PB01 short legacy proxy inventory changed",
    )
    require(
        inputs["pb01_bolt_groups"] == {key: list(value) for key, value in BOLTS.items()}
        and set(inputs["pb01_contact_names"])
        == {
            f"pb01_{family}_compression_{i}_{j}"
            for family in HOSTS
            for i in range(2)
            for j in range(2)
        },
        "PB01 short connector inventory changed",
    )
    return report, inputs


def one_bolt_ratios(lateral_xyz, host_grain, cleat_grain, side_length):
    magnitude = math.sqrt(dot(lateral_xyz, lateral_xyz))
    if magnitude <= 1e-12:
        return None
    host_angle = angle_to_grain(lateral_xyz, host_grain)
    cleat_angle = angle_to_grain(lateral_xyz, cleat_grain)
    roots = {}
    for root in (0.189, 0.180):
        reference = yield_component(root, side_length, host_angle, cleat_angle)
        roots[f"{root:.3f}"] = {
            "reference_lbf": reference["reference_lateral_lbf"],
            "modeled_direction_ratio": magnitude
            * N_TO_LBF
            / reference["reference_lateral_lbf"],
            "governing_mode": reference["governing_mode"],
        }
    return host_angle, cleat_angle, roots


def case_components(case, path):
    report, inputs = read_case(case, Path(path))
    ownership = inputs["connection_ownership"]
    physical = report["physical_connection_forces"]
    axial = {row["name"]: row for row in report["axial_tension"]}
    bearings = {row["name"]: row for row in report["bearings"]}
    spring = {
        row["name"]: row for row in inputs["springs"] if row["name"].startswith("pb01_")
    }
    bolt_names = [name for family in BOLTS for name in BOLTS[family]]
    datum = [
        sum(ownership[name]["point"][i] for name in bolt_names) / 4 for i in range(3)
    ]
    tangent = (0, math.cos(math.radians(50)), math.sin(math.radians(50)))
    normal = (0, -math.sin(math.radians(50)), math.cos(math.radians(50)))
    faces = {}
    for family, host in HOSTS.items():
        names = list(BOLTS[family]) + [
            f"pb01_{family}_compression_{i}_{j}" for i in range(2) for j in range(2)
        ]
        bolts, contacts, actions = [], [], []
        host_grain = tangent if family == "upright" else (1, 0, 0)
        side_length = 5.5 if family == "upright" else 2.25
        for name in names:
            owner, row = ownership[name], physical[name]
            require(
                owner["first"] == row["first"] == host
                and owner["second"] == row["second"] == "base_cleat_pb01"
                and owner["point"] == row["point"],
                f"PB01 connector ownership changed: {name}",
            )
            point = vector(owner["point"], name + " point")
            force = vector(row["force_on_first_xyz_n"], name + " force")
            opposite = vector(row["force_on_second_xyz_n"], name + " opposite")
            require(
                all(abs(a + b) < 1e-7 for a, b in zip(force, opposite)),
                f"Pair mismatch: {name}",
            )
            actions.append((point, force))
            if name in BOLTS[family]:
                axis = vector(owner["axis"], name + " axis")
                require(
                    axis == vector(row["axis"], name + " reported axis")
                    and abs(dot(axis, axis) - 1) < 1e-6,
                    f"Axis changed: {name}",
                )
                axial_n = dot(force, axis)
                lateral = [f - axial_n * a for f, a in zip(force, axis)]
                lateral_n = math.sqrt(dot(lateral, lateral))
                state = axial[name]
                require(
                    abs(axial_n - row["axial_along_installation_direction_n"]) < 1e-5
                    and abs(lateral_n - row["transverse_shear_n"]) < 1e-5
                    and abs(axial_n - state["tension_force_n"]) < 1e-5
                    and state["tension_only_assumption_satisfied"] is True
                    and state["active"] == (axial_n > 1e-6)
                    and axial_n >= -1e-6,
                    f"Bolt tension/lateral mismatch: {name}",
                )
                angles = one_bolt_ratios(lateral, host_grain, normal, side_length)
                bolts.append(
                    {
                        "name": name,
                        "point_xyz_mm": point,
                        "installation_axis_host_to_cleat_xyz": axis,
                        "force_on_host_xyz_n": force,
                        "axial_on_host_n": axial_n,
                        "axial_status": "tension" if state["active"] else "slack",
                        "lateral_on_host_xyz_n": lateral,
                        "lateral_on_host_magnitude_n": lateral_n,
                        "host_load_to_grain_degrees": angles[0] if angles else None,
                        "cleat_load_to_grain_degrees": angles[1] if angles else None,
                        "conditional_one_bolt_lateral": angles[2] if angles else None,
                        "group_utilization": None,
                        "washer_utilization": None,
                    }
                )
            else:
                bearing = bearings[name]
                normal_axis = vector(owner["scalar_normal"], name + " normal")
                compression = dot(force, normal_axis)
                require(
                    abs(compression - bearing["compression_force_n"]) < 1e-5
                    and abs(
                        compression
                        - spring[name]["stiffness_n_per_mm"]
                        * max(-bearing["opening_mm"], 0)
                    )
                    < 1e-3
                    and bearing["active"] is spring[name]["active"]
                    and bearing["active"] == (compression > 1e-6)
                    and bearing["compression_only_assumption_satisfied"] is True,
                    f"Face contact mismatch: {name}",
                )
                contacts.append(
                    {
                        "name": name,
                        "active": bearing["active"],
                        "point_xyz_mm": point,
                        "normal_xyz": normal_axis,
                        "force_on_host_xyz_n": force,
                        "compression_n": compression,
                    }
                )
        result_force = [sum(force[i] for _, force in actions) for i in range(3)]
        result_moment = [
            sum(wrench(point, force, datum)[1][i] for point, force in actions)
            for i in range(3)
        ]
        faces[family] = {
            "host": host,
            "cleat": "base_cleat_pb01",
            "bolts": bolts,
            "contacts": contacts,
            "active_contact_count": sum(row["active"] for row in contacts),
            "compression_n": sum(row["compression_n"] for row in contacts),
            "resultant_on_host": {
                "force_xyz_n": result_force,
                "moment_xyz_nmm": result_moment,
            },
            "resultant_on_cleat": {
                "force_xyz_n": [-x for x in result_force],
                "moment_xyz_nmm": [-x for x in result_moment],
            },
            "group_utilization": None,
            "cleat_utilization": None,
            "contact_utilization": None,
        }
    return {
        "archive_sha256": ARCHIVE_SHA256[case],
        "report_sha256": REPORT_SHA256[case],
        "numerically_accepted": True,
        "datum_xyz_mm": datum,
        "interfaces": faces,
        "group_utilization": None,
        "washer_utilization": None,
        "cleat_utilization": None,
        "contact_utilization": None,
        "whole_joint_utilization": None,
        "design_pass": None,
    }


def compare(paths=None):
    """Keep each case's simultaneous forces together; never issue a joint pass."""
    paths = RUNS if paths is None else paths
    require(set(paths) == set(RUNS), "PB01 short case inventory changed")
    comparison = checked_json(COMPARISON.read_bytes(), COMPARISON_SHA256, "comparison")
    require(
        comparison["classification"] == "diagnostic_only_not_structural_qualification"
        and comparison["left_archive_sha256"] == ARCHIVE_SHA256["a12-left"]
        and comparison["right_archive_sha256"] == ARCHIVE_SHA256["k12-right"],
        "PB01 retained comparison identity changed",
    )
    cases = {case: case_components(case, paths[case]) for case in RUNS}
    for family_key, result_key in (
        ("axial_tension", "bolts"),
        ("face_contact", "contacts"),
    ):
        expected_names = {
            item["name"]
            for face in cases["a12-left"]["interfaces"].values()
            for item in face[result_key]
        }
        require(
            {row["name"] for row in comparison[family_key]} == expected_names
            and len(comparison[family_key]) == len(expected_names),
            "PB01 retained comparison inventory changed",
        )
        for row in comparison[family_key]:
            for case, side in (("a12-left", "a12"), ("k12-right", "k12")):
                component = next(
                    item
                    for face in cases[case]["interfaces"].values()
                    for item in face[result_key]
                    if item["name"] == row["name"]
                )
                force_key = (
                    "axial_on_host_n" if result_key == "bolts" else "compression_n"
                )
                evidence_key = (
                    "tension_force_n"
                    if result_key == "bolts"
                    else "compression_force_n"
                )
                require(
                    math.isclose(
                        component[force_key], row[side][evidence_key], abs_tol=1e-5
                    )
                    and (
                        component["axial_status"] == "tension"
                        if result_key == "bolts"
                        else component["active"]
                    )
                    == row[side]["active"],
                    "PB01 retained comparison force changed",
                )
    require(
        all(
            abs(a - b) < 1e-6
            for a, b in zip(
                cases["a12-left"]["datum_xyz_mm"], cases["k12-right"]["datum_xyz_mm"]
            )
        ),
        "PB01 short case datums differ",
    )
    return {
        "candidate": CANDIDATE,
        "block_length_mm": 152.4,
        "scope": "provisional_same_scenario_component_comparison",
        "proxy_station_count_per_case": 23,
        "retained_comparison_sha256": COMPARISON_SHA256,
        "moment_reference_xyz_mm": cases["a12-left"]["datum_xyz_mm"],
        "cases": cases,
        "group_utilization": None,
        "washer_utilization": None,
        "cleat_utilization": None,
        "contact_utilization": None,
        "whole_joint_utilization": None,
        "design_pass": None,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(compare(), indent=2))
