"""Replay existing bottom component references on 48 first-order bolt states.

This is parent-executed saved-result arithmetic. It calls no mechanics, CAD,
frame, group-method or catalog producer and asserts no joint qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/bottom-corner-components"
SOURCE = HERE / "rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json"
RECEIPT = SOURCE.with_name("source-pins.json")
COMPONENT = HERE / "bolted-replay-results/bottom-attempt01/component-results.json"
MATERIALS = (
    HERE.parent.parent
    / "hardware-material-specification-2026-09-30/material-inputs.json"
)
FASTENERS = MATERIALS.with_name("fastener-inputs.json")
LATERAL = HERE.parent / "lateral_reference.py"
YIELD_HELPER = ROOT / "fea/dowel_yield.py"
PSI_MPA = 0.006894757293168361
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
FLAGS = {
    "formal_criterion_acceptance": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "reviewed_geometry_changed": False,
}
PINS = {
    SOURCE: "4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed",
    RECEIPT: "5fdeb9927a759644f5c25d462b532fcd2bb9d2f389f69b462b716f33857fcb51",
    COMPONENT: "ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    LATERAL: "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
    YIELD_HELPER: "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}
INDEX_KEYS = (
    "ratio_45ksi_adjusted_component_scenario",
    "ratio_92ksi_adjusted_component_scenario",
    "same_state_92ksi_steel_reserve_ratio",
    "cleat_parallel_force_over_finished_tangent_path",
    "washer_mean_pressure_over_Fc_perp",
    "smooth_bolt_VM_over_92ksi_hypothesis",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, result):
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, "changed consumed source: " + str(path))


def physical_balance(values, force_tolerance, moment_tolerance):
    require(
        len(values) == 6 and all(math.isfinite(v) for v in values),
        "invalid physical wrench",
    )
    require(
        max(abs(v) for v in values[:3]) <= force_tolerance
        and max(abs(v) for v in values[3:]) <= moment_tolerance,
        "source physical balance exceeds its original tolerance",
    )


def build(output: Path):
    """Parent-only same-state arithmetic; write one fresh immutable raw packet."""
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "use a fresh owned bottom-corner-components child",
    )
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    authenticate(pins)
    source, receipt, component, material_inputs, fasteners = map(
        read, (SOURCE, RECEIPT, COMPONENT, MATERIALS, FASTENERS)
    )
    require(
        source["schema"] == "bottom_corner_first_order_independent_traction/v1"
        and source["status"] == "COMPLETE_FIRST_ORDER_LOCAL_FORCES"
        and source["failure"] is None
        and source["known_answers_executed"],
        "bottom first-order source is incomplete",
    )
    require(
        not source["geometric_shortening_and_preload_stiffness"]
        and source["balancing_free_couples_added"] == 0
        and not source["frame_response_changed"]
        and not source["material_or_contact_laws_changed"],
        "source mechanics or frame flags differ",
    )
    require(
        all(source[key] is False for key in FLAGS),
        "source acceptance or geometry flags differ",
    )
    require(
        receipt["output_sha256"]["checks.json"] == pins[SOURCE]
        and receipt["source_sha256"] == source["source_sha256"],
        "first-order receipt differs",
    )
    for relative, expected in source["source_sha256"].items():
        path = (ROOT / relative).resolve()
        require(
            path.is_relative_to(ROOT) and (path not in pins or pins[path] == expected),
            "conflicting source closure",
        )
        pins[path] = expected
    authenticate(pins)
    require(
        pins[COMPONENT]
        == source["source_sha256"][COMPONENT.relative_to(ROOT).as_posix()],
        "bottom geometry reference binding differs",
    )
    require(
        not component["complete_joint_acceptance"]
        and not component["physical_release"],
        "bottom reference claims qualification",
    )
    require(
        component["source_sha256"][str(MATERIALS)] == pins[MATERIALS],
        "bottom material reference differs",
    )
    identities = [(case["side"], case["case_id"]) for case in source["states"]]
    require(
        len(identities) == len(set(identities)) == 12
        and set(identities)
        == {(side, case) for side in ("left", "right") for case in CASES},
        "bottom two-block six-case census differs",
    )

    # Reuse the bottom packet's fixed 4450/5600 psi single-shear arithmetic.
    # The diameter-dependent top-corner reference is a different hypothesis.
    spec = importlib.util.spec_from_file_location("bottom_component_lateral", LATERAL)
    require(
        spec is not None and spec.loader is not None, "missing component arithmetic"
    )
    lateral = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lateral)
    material = material_inputs["conditional_DF_L_No2_base_row"]["base_properties"]
    fv, fc = (material[key] * PSI_MPA for key in ("Fv_parallel", "Fc_perpendicular"))
    washer = fasteners["dimension_inputs"]["washer"]
    paths = {
        (p["axis_id"], p["grain_direction_sign"]): p
        for p in component["finished_paths"]
    }
    old_states = {(s["case_id"], s["axis_id"]): s for s in component["states"]}
    seats = {(s["axis_id"], s["member"]): s for s in component["washer_geometry"]}
    groups = {(g["side"], g["host"]): g for g in source["preparation"]["groups"]}
    method = source["preparation"]["method"]
    states, balances, interfaces = [], [], []
    for case in source["states"]:
        side, case_id, cleat = case["side"], case["case_id"], case["cleat"]
        require(
            cleat == "bottom_outer_" + side + "_cleat"
            and set(case["hosts"]) == {"base_rail_bottom_" + side, "base_side_" + side},
            "bottom block or host identity differs",
        )
        physical_balance(
            case["physical_whole_cleat_residual_n_nmm"],
            method["whole_cleat_force_tolerance_n"],
            method["whole_cleat_moment_tolerance_nmm"],
        )
        balances.append(
            {
                "side": side,
                "case_id": case_id,
                "current_weight_once_n_nmm": case["current_weight_once_n_nmm"],
                "physical_whole_cleat_residual_n_nmm": case[
                    "physical_whole_cleat_residual_n_nmm"
                ],
                "physical_host_residuals_n_nmm": {
                    h: r["physical_host_residual_n_nmm"]
                    for h, r in case["hosts"].items()
                },
            }
        )
        for host, record in case["hosts"].items():
            group, local = groups[side, host], record["state"]
            family = group["family"]
            require(
                group["cleat"] == cleat
                and local["case_id"] == case_id
                and len(local["bolts"]) == 2
                and len(local["face_cells"]) == 4
                and {b["axis_id"] for b in local["bolts"]}
                == {b["axis_id"] for b in group["bolts"]},
                "bottom local geometry or state census differs",
            )
            require(
                family["diameter_mm"] == 6.35 and family["bore_mm"] == 7.5,
                "bottom quarter-inch geometry differs",
            )
            physical_balance(
                record["physical_host_residual_n_nmm"],
                method["host_force_tolerance_n"],
                method["host_moment_tolerance_nmm"],
            )
            grains = [
                np.asarray(
                    group["finished_members"][member]["geometry"]["axis"], dtype=float
                )
                for member in (host, cleat)
            ]
            grains = [g / np.linalg.norm(g) for g in grains]
            require(
                np.max(abs(grains[1] - case["cleat_grain_xyz"])) < 1e-12,
                "actual cleat grain differs",
            )
            lengths = [family["host_length_mm"], family["cleat_length_mm"]]
            interfaces.append(
                {
                    "side": side,
                    "case_id": case_id,
                    "host": host,
                    "cleat": cleat,
                    "face_cells": local["face_cells"],
                    "maximum_cell_pressure_over_Fc_perp": max(
                        f["pressure_mpa"] for f in local["face_cells"]
                    )
                    / fc,
                }
            )
            for bolt in local["bolts"]:
                axis_id, tension = bolt["axis_id"], float(bolt["compatible_T_n"])
                force = -np.asarray(bolt["bore_force_on_host_xyz_n"], dtype=float)
                shear = float(np.linalg.norm(force))
                require(
                    tension >= 0
                    and np.isfinite(force).all()
                    and math.isfinite(tension)
                    and bolt["projected_shortening_mm"] == 0.0
                    and math.isclose(
                        shear, bolt["bore_V_resultant_n"], abs_tol=1e-7, rel_tol=0
                    ),
                    "invalid first-order same-state bolt force",
                )
                own_cleat_force = np.sum(
                    [
                        a["force_xyz_n"]
                        for a in case["physical_cleat_actions"]
                        if a["kind"] == "bore_station_resultant"
                        and a["identity"] == axis_id
                    ],
                    axis=0,
                )
                force_error = own_cleat_force - force
                require(
                    np.max(abs(force_error)) <= method["host_force_tolerance_n"],
                    "opposed bore resultants do not close",
                )
                angles = [lateral.angle(force, grain) for grain in grains]
                references = {
                    yield_psi: lateral.reference(lengths, angles, yield_psi)
                    for yield_psi in (45000.0, 92000.0)
                }
                reference_n = {
                    yield_psi: value["reference_lateral_lbf"] * lateral.N_PER_LBF
                    for yield_psi, value in references.items()
                }
                factors = old_states[case_id, axis_id]["component_factors"]
                multiplier = factors["combined_multiplier"]
                require(
                    multiplier > 0
                    and math.isclose(
                        multiplier,
                        factors["Cg_component_scenario"]
                        * factors["Cdelta_end_scenario"],
                        abs_tol=1e-12,
                    ),
                    "bottom component modifier differs",
                )
                parallel = float(force @ grains[1])
                path = paths[axis_id, 1 if parallel >= 0 else -1]
                require(
                    path["block"] == cleat
                    and path["minimum_finished_one_plane_area_mm2"] > 0,
                    "wrong bottom finished path",
                )
                own_seats, areas = [], []
                for member in (host, cleat):
                    seat = seats[axis_id, member]
                    combined = [
                        a["supported_area_mm2"]
                        for a in seat["conditional_hole_only_areas"]
                        if a["mode"] == "combined"
                    ]
                    require(
                        seat["geometry_screen_pass"]
                        and combined
                        and all(
                            a["hole_only_applicable"]
                            for a in seat["conditional_hole_only_areas"]
                        ),
                        "unsupported own bottom seat",
                    )
                    recovered_seat = next(
                        s
                        for s in record["wood_seat_recovery"]
                        if s["axis_id"] == axis_id and s["member"] == member
                    )
                    require(
                        np.max(
                            abs(
                                np.asarray(
                                    recovered_seat["nominal_outer_wood_seat_xyz_mm"]
                                )
                                - seat["point_xyz_mm"]
                            )
                        )
                        < 1e-7,
                        "same-state seat point differs from bottom geometry",
                    )
                    areas.append(min(combined))
                    own_seats.append(
                        {
                            "member": member,
                            "role": seat["role"],
                            "point_xyz_mm": seat["point_xyz_mm"],
                            "minimum_combined_offset_supported_area_mm2": min(combined),
                        }
                    )
                area = min(areas)
                pressure = tension / area
                axial = tension / (0.0318 * 25.4**2)
                tau = 4 * shear / (3 * math.pi * family["diameter_mm"] ** 2 / 4)
                radicand = (92000 * PSI_MPA) ** 2 - 3 * tau**2
                require(
                    radicand > 0, "direct shear exhausts conditional steel scenario"
                )
                remaining_yield = math.sqrt(radicand) - axial
                require(
                    remaining_yield > 0,
                    "direct axial/shear stress exhausts conditional steel scenario",
                )
                reduced = lateral.reference(lengths, angles, remaining_yield / PSI_MPA)
                reduced_n = reduced["reference_lateral_lbf"] * lateral.N_PER_LBF
                require(
                    reduced_n <= reference_n[92000.0] + 1e-8,
                    "steel reserve raises the unchanged reference",
                )
                ro, ri, thick = (
                    max(washer["od_in"]) * 25.4 / 2,
                    family["flat_radius_mm"],
                    min(washer["thickness_in"]) * 25.4,
                )
                strip = (
                    6
                    * pressure
                    / ri
                    * ((ro**3 - ri**3) / 3 - ri * (ro**2 - ri**2) / 2)
                    / thick**2
                )
                stress = bolt["peak_stress_witness"]
                states.append(
                    {
                        "side": side,
                        "case_id": case_id,
                        "axis_id": axis_id,
                        "block": cleat,
                        "host": host,
                        "tension_n": tension,
                        "shear_n": shear,
                        "shear_xyz_on_cleat_n": force.tolist(),
                        "recovered_cleat_bore_force_xyz_n": own_cleat_force.tolist(),
                        "opposed_bore_force_residual_xyz_n": force_error.tolist(),
                        "receiver_geometry": family,
                        "ordered_wood_lengths_mm": lengths,
                        "grain_axes_host_cleat_xyz": [g.tolist() for g in grains],
                        "load_to_grain_degrees": angles,
                        "reference_45ksi_n": reference_n[45000.0],
                        "reference_92ksi_n": reference_n[92000.0],
                        "component_factors": factors,
                        "ratio_45ksi_adjusted_component_scenario": shear
                        / (reference_n[45000.0] * multiplier),
                        "ratio_92ksi_adjusted_component_scenario": shear
                        / (reference_n[92000.0] * multiplier),
                        "steel_reserve_reference_n": reduced_n,
                        "same_state_92ksi_steel_reserve_ratio": shear
                        / (reduced_n * multiplier),
                        "parallel_force_n": parallel,
                        "finished_path": path,
                        "cleat_parallel_force_over_finished_tangent_path": abs(parallel)
                        / (fv * path["minimum_finished_one_plane_area_mm2"]),
                        "own_outer_seat_geometry": own_seats,
                        "minimum_displaced_washer_area_mm2": area,
                        "washer_mean_pressure_mpa": pressure,
                        "washer_mean_pressure_over_Fc_perp": pressure / fc,
                        "washer_required_radial_strip_stress_mpa": strip,
                        "sampled_end_wood_pressure_peak_mpa": max(
                            e["wood_contact"]["pressure_peak_mpa"]
                            for e in bolt["end_contacts"]
                        ),
                        "smooth_bolt_stress_witness": stress,
                        "smooth_bolt_VM_over_92ksi_hypothesis": stress[
                            "proxy_over_conditional_92ksi_Fyb"
                        ],
                        **FLAGS,
                    }
                )
    require(
        len(states) == len({(s["case_id"], s["axis_id"]) for s in states}) == 48
        and all(
            sum(s["side"] == side for s in states) == 24 for side in ("left", "right")
        ),
        "48-bolt-state census differs",
    )
    peaks = {key: max(states, key=lambda s, key=key: s[key]) for key in INDEX_KEYS}
    by_side = {
        side: {
            key: max(
                (s for s in states if s["side"] == side), key=lambda s, key=key: s[key]
            )
            for key in INDEX_KEYS
        }
        for side in ("left", "right")
    }
    result = {
        "schema": "bottom_first_order_same_state_component_replay/v1",
        "status": "COMPLETE_SAME_STATE_COMPONENT_REFERENCES",
        "counts": {
            "block_states": 12,
            "host_states": 24,
            "bolt_states": 48,
            "left_bolt_states": 24,
            "right_bolt_states": 24,
        },
        "states": states,
        "interfaces": interfaces,
        "peak_witnesses": peaks,
        "peak_witnesses_by_side": by_side,
        "physical_balance_source_receipts": balances,
        "component_references": {
            "Fv_parallel_mpa": fv,
            "Fc_perpendicular_mpa": fc,
            "bearing_strengths_psi": [4450.0, 5600.0],
            "Fyb_scenarios_psi": [45000.0, 92000.0],
            "axial_reserve_area_in2": 0.0318,
            "washer_OD_max_mm": 2 * ro,
            "washer_thickness_min_mm": thick,
            "flat_bearing_radius_mm": ri,
        },
        "host_splitting_original_source_only": component["host_splitting"],
        "source_first_order_limits": source["limits"],
        "limits": [
            "Each reference uses one saved bottom bolt's simultaneous signed bore force, axial tie and beam stress; no top geometry/indices or independent source maxima are transferred.",
            "The cleat-directed single-shear transfer is the opposite of the saved host bore resultant. The independently recovered cleat bore resultant and its numerical discrepancy are retained.",
            "Bottom Cg/Cdelta modifiers, signed finished tangent paths and worst combined-offset supported annulus areas remain their existing component scenarios, not full-group or splitting capacity.",
            "The 0.0318 in2 axial reserve and radial washer strip retain the existing bottom hypotheses. They are not a prescribed interaction rule, delivered thread profile or washer-metal strength.",
            "Mean-seat pressure is a supported-area comparison; K20 sampled peaks are separate diagnostics. Source smooth-bolt stress retains same-state bending and is not a hardware rating.",
            "Original host-splitting records remain history/scope; no redistributed whole-host cut or finished-section resistance is recalculated.",
            "Rigid timber, concentric washers, reference geometry and the frozen original 100 mm frame source remain unchanged. No mechanics, CAD, frame, group method or catalog investigation is invoked.",
        ],
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): h for p, h in sorted(pins.items())
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "mechanics_or_geometry_rerun": False,
        "tests_run": False,
        "review_loop_run": False,
        "actual_hardware_capacity_n": None,
        "actual_washer_capacity_n": None,
        "Ft_perp": None,
        "group_capacity_n": None,
        **FLAGS,
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
            **FLAGS,
        },
    )
    authenticate(pins)
    print(
        json.dumps(
            {
                "status": result["status"],
                "checks_sha256": sha(output / "checks.json"),
                "peak_indices": {key: row[key] for key, row in peaks.items()},
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
