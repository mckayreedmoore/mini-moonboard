#!/usr/bin/env python3
"""Reuse the frozen service-frame method for the lower-left outer cleat."""

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = HERE.parent / "upper-left-service-frame-clearance-2026-10-01"
BLOCK = "left_service_outer_lower_cleat"
RAIL = "base_rail_service_lower_left"
SIDE = "base_side_left"
HELPER_SHA = "54ebbd0259fa15a201ba05da035df9fca88d65987ff4473b4322216f8ca42164"
VALIDATION_SHA = "7e29a41a7d689d884cfdcba7c7f1eb920f0e66da03d1d46098dd30dc8280d1eb"


def digest(path):
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def component_indices(shear, tension, grip, host_depth):
    """Demand indices only; the inherited bending/washer shapes are hypotheses."""
    diameter, root = 6.35, 0.189 * 25.4
    root_area = math.pi * root**2 / 4
    nominal_modulus = math.pi * diameter**3 / 32
    annulus_quarter = math.pi * (18.4658**2 - 8.3058**2) / 16
    bending = shear * grip / 4  # sensitivity, not a proven bolt-bending bound
    normal = tension / root_area + bending / nominal_modulus
    equivalent = math.sqrt(normal**2 + 3 * (4 * shear / (3 * root_area)) ** 2)
    washer = (
        6
        * tension
        * ((18.4658 - 8.3058) / 2)
        / (math.pi * 8.3058 * (0.051 * 25.4) ** 2)
    )
    return {
        "nominal_shank_bending_scenario_nmm": bending,
        "root_axial_nominal_shank_bending_vm_scenario_mpa": equivalent,
        "index_to_hypothetical_634mpa_steel_yield": equivalent
        / (92000 * 0.006894757293168),
        "quarter_annulus_average_wood_pressure_mpa": tension / annulus_quarter,
        "index_to_hypothetical_4_31mpa_seat_pressure": tension
        / annulus_quarter
        / (625 * 0.006894757293168),
        "nominal_projected_host_bearing_average_mpa": shear / (diameter * host_depth),
        "washer_radial_strip_index_mpa": washer,
        "index_to_hypothetical_250mpa_washer": washer / 250,
    }


def produce():
    helper_path = PRIOR / "check_frame.py"
    if (
        digest(helper_path) != HELPER_SHA
        or digest(PRIOR / "parent-validation.json") != VALIDATION_SHA
    ):
        raise ValueError("reviewed helper/validation pin changed")
    spec = importlib.util.spec_from_file_location("lower_service_frame", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    # ponytail: adapt this process's four scope constants; keep the saved helper
    # unchanged. Its equilibrium/law algorithms work for any four paired axes.
    helper.TARGET = np.arange(96, 104)
    helper.BLOCK, helper.RAIL, helper.SIDE = BLOCK, RAIL, SIDE
    frame = helper.Frame()
    helper.DATUM = frame.centers[BLOCK].copy()
    axial = np.array(
        [
            i
            for i, r in enumerate(frame.rows)
            if r["ownership"]["role"] == "physical_bolt_outer_seat_tension"
            and BLOCK in (r["ownership"]["first_body"], r["ownership"]["second_body"])
        ]
    )
    if not np.array_equal(axial, np.arange(1580, 1584)):
        raise ValueError("lower cleat axial mapping differs")
    for i, row in enumerate(axial):
        pair = helper.TARGET[2 * i : 2 * i + 2]
        axis = frame.rows[int(row)]["row_id"].rsplit("/", 1)[0]
        if any(frame.rows[int(j)]["row_id"].rsplit("/", 1)[0] != axis for j in pair):
            raise ValueError("lower cleat axis pairing differs")
        basis = np.array(
            [frame.rows[int(j)]["ownership"]["direction_global_xyz"] for j in pair]
        )
        if helper.maxabs(basis @ basis.T - np.eye(2)) > 1e-9:
            raise ValueError("lower bolt force basis is not orthonormal")
    authority = read(PRIOR / "parent-validation.json")["authority_sha256_unchanged"]
    pins = dict(frame.pins)
    pins.update(authority)
    pins[str(helper_path.relative_to(ROOT))] = HELPER_SHA
    pins[str((PRIOR / "parent-validation.json").relative_to(ROOT))] = VALIDATION_SHA
    pins[str(Path(__file__).relative_to(ROOT))] = digest(Path(__file__))
    for path, expected in pins.items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"pin changed: {path}")
    rigidity = 200000 * math.pi * 6.35**4 / 64
    low_k = rigidity * (150 / (4 * rigidity)) ** 0.75
    scenarios = [("source", c, None) for c in (0.0, 0.5, 1.15)] + [
        ("hypothetical E150", 1.15, low_k)
    ]
    states, arrays, summary, rank_cache = [], [], [], {}
    for label, clearance, stiffness in scenarios:
        group = []
        for case in sorted(frame.sources):
            for increment in range(7):
                r, v = frame.evaluate(case, increment, 2.0, clearance, stiffness)
                if not r["audit"]["floor_branch_consistent"]:
                    raise ValueError("comparison floor branch changed")
                # The old helper's tension report is specific to its upper scope;
                # replace that display field using authenticated lower-axis rows.
                r["target_axial_tension_n"] = v["f"][axial].tolist()
                r["scenario"] = label
                for i, b in enumerate(r["target_bolts"]):
                    b["tension_n"] = float(v["f"][axial[i]])
                    rail = i < 2
                    b["component_demand_indices"] = component_indices(
                        b["shear_n"],
                        b["tension_n"],
                        127.0 if rail else 177.8,
                        38.1 if rail else 88.9,
                    )
                bearing = (
                    list(np.setdiff1d(frame.bilateral, helper.TARGET))
                    + list(frame.unilateral[v["f"][frame.unilateral] > 1e-6])
                    + list(v["held_floor_rows"])
                )
                for pair in helper.TARGET.reshape(4, 2):
                    if clearance == 0 or np.linalg.norm(v["f"][pair]) > 1e-6:
                        bearing.extend(pair)
                key = tuple(sorted({int(i) for i in bearing}))
                if key not in rank_cache:
                    singular = np.linalg.svd(frame.D[list(key)], compute_uv=False)
                    rank_cache[key] = {
                        "rank": int(np.count_nonzero(singular > 1e-10 * singular[0])),
                        "smallest_singular_value": float(singular[-1]),
                    }
                if rank_cache[key]["rank"] != 300:
                    raise ValueError("motion relies on a rigid mechanism")
                r["force_bearing_rigid_rank"] = rank_cache[key]["rank"]
                if clearance == 0 and (
                    r["zero_clearance_native_force_max_difference_n"] > 0.002
                    or r["zero_clearance_native_q_max_difference_mm"] > 1e-4
                ):
                    raise ValueError("practical source baseline comparison failed")
                group.append(r)
                states.append(r)
                arrays.append(v)
        bolts = [b for r in group for b in r["target_bolts"]]
        summary.append(
            {
                "scenario": label,
                "clearance_mm": clearance,
                "lateral_stiffness_n_per_mm": stiffness,
                "states": len(group),
                "floor_consistent_states": len(group),
                "local_host_motion_peak_mm": max(
                    r["local_fit_rail_side_movement_mm"] for r in group
                ),
                "local_host_rotation_peak_deg": max(
                    r["local_fit_rail_side_rotation_deg"] for r in group
                ),
                "bolt_shear_peak_n": max(b["shear_n"] for b in bolts),
                "bolt_tension_peak_n": max(b["tension_n"] for b in bolts),
                "bolt_slip_peak_mm": max(b["slip_mm"] for b in bolts),
                "local_fit_projection_residual_peak_mm": max(
                    f["maximum_nonrigid_projection_residual_mm"]
                    for r in group
                    for f in r["local_interface_projection_fits"].values()
                ),
                "component_index_peaks": {
                    key: max(b["component_demand_indices"][key] for b in bolts)
                    for key in bolts[0]["component_demand_indices"]
                },
            }
        )
        print(json.dumps(summary[-1]), file=sys.stderr, flush=True)
    for path, expected in pins.items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"source changed during comparison: {path}")
    return {
        "schema": "lower_left_service_outer_working_assessment/v1",
        "status": "CONDITIONAL_WORKING_COMPARISON",
        "complete_joint": "HOLD",
        "release": False,
        "native_run": False,
        "geometry_changed": False,
        "block": BLOCK,
        "rail": RAIL,
        "side": SIDE,
        "datum_xyz_mm": helper.DATUM.tolist(),
        "target_lateral_rows": helper.TARGET.tolist(),
        "target_axial_rows": axial.tolist(),
        "load_scale": 2.0,
        "states": states,
        "summary": summary,
        "source_sha256": pins,
        "authority_sha256_unchanged": authority,
        "force_bearing_rigid_rank": 300,
        "distinct_force_bearing_row_sets": len(rank_cache),
        "minimum_smallest_rigid_singular_value": min(
            x["smallest_singular_value"] for x in rank_cache.values()
        ),
        "assumptions": {
            "gravity_and_climber_scaled_together": True,
            "other_bolts_zero_clearance": True,
            "hillman_laws_unqualified": True,
            "source_floor_masks_conditional": True,
            "open_zero_force_extension_below_negative_10mm": True,
            "provisional_local_movement_target_mm": 1.0,
            "provisional_local_rotation_target_deg": 0.5,
            "component_indices_are_hypotheses_not_resistances": True,
            "bending_scenario": "V*grip/4 on nominal 6.35 mm shank; axial stress on hypothetical 0.189 inch root; not a bending bound",
            "washer_index": "radial-strip index, not a qualified plate/contact solution",
        },
    }, {k: np.stack([v[k] for v in arrays]) for k in ("f", "q", "a")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    if args.outdir.exists():
        raise ValueError("refusing to overwrite evidence directory")
    report, vectors = produce()
    args.outdir.mkdir(parents=True)
    np.savez_compressed(args.outdir / "vectors.npz", **vectors)
    report["vectors_sha256"] = digest(args.outdir / "vectors.npz")
    (args.outdir / "comparison.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "outdir": str(args.outdir),
                "report_sha256": digest(args.outdir / "comparison.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
