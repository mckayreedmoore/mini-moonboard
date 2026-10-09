"""Prescribed old stack wrenches: continuous bearing statics, not resistance.

Reuse the issued six-field intake. An affine bearing distribution reproduces
each member's own lateral force and moment; it does not establish compatible
deformation, a yield mechanism, an NDS design value or a revised-frame response.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "stack_parent", HERE.parent / "analyze.py"
)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def line_bound(length, force, first_moment):
    """Exact scalar minimum q for integral f=F, integral x*f=S, |f|<=q.

    The interval is centered, length L. For fixed F and q the extreme first
    moment is q*L**2/4 - F**2/(4*q), attained by a signed step distribution.
    This is a necessary directional bound for a vector bearing distribution.
    It is not a wood allowable stress or a complete connection yield value.
    """
    parent.require(
        math.isfinite(length)
        and length > 0
        and math.isfinite(force)
        and math.isfinite(first_moment),
        "positive finite bearing interval and finite actions required",
    )
    return (
        2 * abs(first_moment) + math.hypot(2 * first_moment, force * length)
    ) / length**2


def bearing_trial(shaft, index, port, raw_bearings, captures):
    """Recenter the own wrench before forming a continuous affine density."""
    surface = shaft["surfaces"][index]
    lo, hi = surface["interval_mm"]
    length = hi - lo
    g = np.asarray(shaft["basis"][0], dtype=float)
    p = np.asarray(shaft["point"], dtype=float)
    parent.require(
        length > 0 and abs(np.linalg.norm(g) - 1) < 1e-10,
        "positive interval and unit shaft axis required",
    )
    parent.require(
        port["host"] == surface["host"]
        and port["surface_index"] == index
        and port["surface_interval_mm"] == surface["interval_mm"],
        "own member/interval binding differs",
    )
    center = p + g * ((lo + hi) / 2)
    point = np.asarray(port["point_xyz_mm"])
    full_force = np.asarray(port["force_on_host_xyz_n"])
    force = full_force - g * float(full_force @ g)
    moment = np.asarray(port["moment_on_host_at_point_xyz_nmm"]) + np.cross(
        point - center, full_force
    )
    parent.require(
        abs(float(moment @ g)) < 1e-5, "shaft-axis couple needs another path"
    )
    parent.require(
        np.linalg.norm(np.cross(point - p, g)) < 1e-5,
        "aggregate datum leaves shaft centerline",
    )
    first = -np.cross(g, moment)
    raw_force, raw_moment = np.zeros(3), np.zeros(3)
    for key, table, point_key in (
        ("own_bearing_points", raw_bearings, "point_xyz_mm"),
        ("own_end_captures", captures, "host_support_point_xyz_mm"),
    ):
        for identity in port[key]:
            action = table[identity]
            parent.require(
                action["axis_id"] == shaft["axis_id"]
                and action["second"] == surface["host"],
                "foreign bearing/capture owner",
            )
            for label in ("state_id", "case_id", "accessory_placement"):
                parent.require(action[label] == port[label], "mixed own action state")
            f = np.asarray(action["force_on_second_xyz_n"])
            raw_force += f
            raw_moment += np.cross(np.asarray(action[point_key]) - center, f)
            raw_moment += action["moment_on_second_at_point_xyz_nmm"]
    ferr = float(np.linalg.norm(raw_force - full_force))
    merr = float(np.linalg.norm(raw_moment - moment))
    parent.require(ferr < 1e-6 and merr < 1e-5, "own raw force/moment replay differs")
    endpoints = [
        force / length - 6 * first / length**2,
        force / length + 6 * first / length**2,
    ]
    # Independent two-point Gauss integration is exact for this affine trial.
    positions = [-length / (2 * math.sqrt(3)), length / (2 * math.sqrt(3))]
    densities = [force / length + 12 * first * x / length**3 for x in positions]
    integrated_force = sum(densities) * length / 2
    integrated_first = sum(x * q for x, q in zip(positions, densities)) * length / 2
    parent.require(
        np.linalg.norm(integrated_force - force) < 1e-8
        and np.linalg.norm(np.cross(g, integrated_first) - moment) < 1e-5,
        "continuous trial fails own wrench",
    )
    directions = list(np.asarray(shaft["basis"])[1:])
    for vector in (force, first):
        if np.linalg.norm(vector) > 1e-10:
            directions.append(vector / np.linalg.norm(vector))
    bounds = [
        line_bound(length, float(force @ d), float(first @ d)) for d in directions
    ]
    lower = max(bounds)
    upper = max(float(np.linalg.norm(q)) for q in endpoints)
    parent.require(upper + 1e-8 >= lower, "affine trial below necessary bearing bound")
    return {
        "surface_index": index,
        "host": surface["host"],
        "kind": surface["kind"],
        "interval_from_axis_point_mm": [lo, hi],
        "center_xyz_mm": center.tolist(),
        "lateral_force_on_host_xyz_n": force.tolist(),
        "moment_on_host_about_interval_center_xyz_nmm": moment.tolist(),
        "lateral_first_moment_xyz_nmm": first.tolist(),
        "original_port_moment_magnitude_nmm": float(
            np.linalg.norm(port["moment_on_host_at_point_xyz_nmm"])
        ),
        "centered_moment_magnitude_nmm": float(np.linalg.norm(moment)),
        "lateral_n": float(np.linalg.norm(force)),
        "force_only_mean_line_density_n_mm": float(np.linalg.norm(force)) / length,
        "necessary_directional_peak_line_density_bound_n_mm": lower,
        "affine_endpoint_line_density_vectors_n_mm": [q.tolist() for q in endpoints],
        "affine_trial_peak_line_density_n_mm": upper,
        "raw_force_replay_error_n": ferr,
        "raw_moment_replay_error_nmm": merr,
        "deformation_compatibility_or_yield_capacity_established": False,
    }


def known_answers():
    parent.require(line_bound(10, 100, 0) == 10, "uniform-force bound")
    parent.require(line_bound(10, 0, 100) == 4, "pure-couple bound")
    q = line_bound(10, 100, 100)
    switch = -100 / (2 * q)
    f = q * (5 - switch) - q * (switch + 5)
    s = q * (25 - switch**2)
    parent.require(abs(f - 100) < 1e-10 and abs(s - 100) < 1e-10, "signed-step closure")
    parent.require(line_bound(10, -100, -100) == q, "action reversal")
    # AWC TR12 (2015) Example 3.1, mode II: equal l=1.5, q=2400,
    # no gap. Rigid-dowel equilibrium gives P=q*l/(1+sqrt(2)), Z=P/3.6.
    p = 2400 * 1.5 / (1 + math.sqrt(2))
    parent.require(
        abs(line_bound(1.5, p, p * 1.5 / 2) - 2400) < 1e-9, "TR12 rigid-dowel mode II"
    )
    synthetic = {
        "axis_id": "fixture",
        "point": [0.0, 0.0, 0.0],
        "basis": [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        "surfaces": [{"interval_mm": [0.0, 10.0], "host": "wood", "kind": "wood"}],
    }
    raw = {
        "a": {
            "axis_id": "fixture",
            "second": "wood",
            "point_xyz_mm": [0.0, 0.0, 2.0],
            "force_on_second_xyz_n": [30.0, 0.0, 0.0],
            "moment_on_second_at_point_xyz_nmm": [0.0, 0.0, 0.0],
            "state_id": "fixture",
            "case_id": "fixture",
            "accessory_placement": "fixture",
        },
        "b": {
            "axis_id": "fixture",
            "second": "wood",
            "point_xyz_mm": [0.0, 0.0, 8.0],
            "force_on_second_xyz_n": [70.0, 0.0, 0.0],
            "moment_on_second_at_point_xyz_nmm": [0.0, 0.0, 0.0],
            "state_id": "fixture",
            "case_id": "fixture",
            "accessory_placement": "fixture",
        },
    }
    port = {
        "host": "wood",
        "surface_index": 0,
        "surface_interval_mm": [0.0, 10.0],
        "point_xyz_mm": [0.0, 0.0, 0.0],
        "force_on_host_xyz_n": [100.0, 0.0, 0.0],
        "moment_on_host_at_point_xyz_nmm": [0.0, 620.0, 0.0],
        "own_bearing_points": ["a", "b"],
        "own_end_captures": [],
        "state_id": "fixture",
        "case_id": "fixture",
        "accessory_placement": "fixture",
    }
    trial = bearing_trial(synthetic, 0, port, raw, {})
    centered = port | {
        "point_xyz_mm": [0.0, 0.0, 5.0],
        "moment_on_host_at_point_xyz_nmm": [0.0, 120.0, 0.0],
    }
    other = bearing_trial(synthetic, 0, centered, raw, {})
    parent.require(
        trial["affine_endpoint_line_density_vectors_n_mm"]
        == other["affine_endpoint_line_density_vectors_n_mm"],
        "datum invariance",
    )
    rejected = []
    for label, bad in (
        ("shaft_torque", port | {"moment_on_host_at_point_xyz_nmm": [0.0, 620.0, 1.0]}),
        ("wrong_host", port | {"host": "other"}),
        ("altered_force", port | {"force_on_host_xyz_n": [101.0, 0.0, 0.0]}),
        ("foreign_state", port | {"case_id": "foreign"}),
    ):
        try:
            bearing_trial(synthetic, 0, bad, raw, {})
        except ValueError:
            rejected.append(label)
    for length in (0, -1, math.nan):
        try:
            line_bound(length, 100, 100)
        except ValueError:
            rejected.append("invalid_length")
    parent.require(len(rejected) == 7, "negative controls must reject")
    return {
        "uniform_force_and_pure_couple": True,
        "signed_step_equilibrium": True,
        "port_datum_invariance_and_affine_quadrature": True,
        "TR12_2015_example3p1_modeII_Z_lbf": p / 3.6,
        "rejection_controls": rejected,
    }


def run():
    inputs = json.loads((HERE / "inputs.json").read_bytes())
    refs = inputs["references"]
    audited = parent.read(refs["audit_result"])
    details = parent.read(refs["audit_details"])
    original = parent.read(refs["original_inputs"])
    pins = dict(details["complete_source_sha256"])
    parent.merge(pins, {r["path"]: r["sha256"] for r in refs.values()})
    parent.merge(
        pins,
        {
            str(p.relative_to(ROOT)): parent.sha(p)
            for p in (Path(__file__), HERE / "inputs.json")
        },
    )
    parent.verify(pins)
    intake = parent.module("stack_admitted_intake", original["helpers"]["admission"])
    methods = parent.module("stack_thread_methods", refs["timber_helper"]["path"])
    wood = parent.module("stack_dfl_methods", "mini_moonboard/bolted_timber_checks.py")
    catalog = parent.read(refs["catalog"])
    roots = parent.read(refs["roots"])
    known = known_answers()
    ids = {r["axis_id"] for r in audited["group_applicability"]["unsupported_shafts"]}
    parent.require(len(ids) == 8, "eight unresolved shafts required")
    all_rows, stack_rows = [], []
    for case in original["cases"]:
        manifest = parent.read(case["manifest"])
        field, admitted_pins = intake.load_admitted(ROOT / case["manifest"]["path"])
        parent.merge(pins, admitted_pins)
        parent.require(
            field["source_inputs"]["geometry"]["report"] == manifest["geometry"],
            "old field geometry binding",
        )
        timber = parent.read(case["reports"]["timber"])
        shaft_markers = parent.read(case["reports"]["shafts"])
        parent.require(
            timber["source_field_sha256"] == manifest["field"]["sha256"]
            and shaft_markers["source_field"] == manifest["field"],
            "own-case report field binding",
        )
        shafts = {r["axis_id"]: r for r in field["source_inputs"]["shafts"]}
        ports = {
            (r["axis_id"], r["surface_index"]): r
            for k in (
                "common_shaft_wood_bearing_actions",
                "common_shaft_steel_port_actions",
            )
            for r in field[k]
        }
        bearings = {r["id"]: r for r in field["common_shaft_bearing_actions"]}
        captures = {r["id"]: r for r in field["shaft_end_capture_actions"]}
        windows = {r["axis_id"]: r["thread_window"] for r in timber["shaft_components"]}
        markers = {r["axis_id"]: r for r in shaft_markers["physical_shafts"]}
        for aid in sorted(ids):
            shaft = shafts[aid]
            parent.require(
                len(shaft["surfaces"]) == 3, "three occupied member intervals required"
            )
            window = methods.thread_windows(shaft, catalog, roots)
            parent.require(window == windows[aid], "thread-window replay differs")
            own_rows = []
            for i, surface in enumerate(shaft["surfaces"]):
                port = ports[aid, i]
                for label in ("state_id", "case_id", "accessory_placement"):
                    parent.require(
                        port[label] == field[label], "foreign aggregate state"
                    )
                row = bearing_trial(shaft, i, port, bearings, captures)
                d = window["effective_D_in"] * 25.4
                row.update(
                    {
                        "case_id": case["case_id"],
                        "axis_id": aid,
                        "bearing_screen_D_mm": d,
                        "affine_trial_peak_projected_bearing_mpa": row[
                            "affine_trial_peak_line_density_n_mm"
                        ]
                        / d,
                    }
                )
                if surface["kind"] == "wood":
                    fe = wood.dfl_dowel_bearing_psi(d / 25.4, 90) * 0.006894757293168
                    row.update(
                        {
                            "DFL_Fe90_material_parameter_mpa": fe,
                            "affine_peak_over_Fe90_parameter": row[
                                "affine_trial_peak_projected_bearing_mpa"
                            ]
                            / fe,
                        }
                    )
                else:
                    row["eoere_product_bearing_resistance_mpa"] = None
                own_rows.append(row)
            # Affine bearings preserve each own lateral F/M. Add the actual
            # original axial captures and metal gravity to close the shaft.
            p = np.asarray(shaft["point"])
            total_f, total_m = np.zeros(3), np.zeros(3)
            for row in own_rows:
                f = -np.asarray(row["lateral_force_on_host_xyz_n"])
                total_f += f
                total_m += -np.asarray(
                    row["moment_on_host_about_interval_center_xyz_nmm"]
                ) + np.cross(np.asarray(row["center_xyz_mm"]) - p, f)
            for action in field["shaft_end_capture_actions"]:
                if action["axis_id"] == aid:
                    f = np.asarray(action["force_on_first_xyz_n"])
                    total_f += f
                    total_m += (
                        np.cross(np.asarray(action["point_xyz_mm"]) - p, f)
                        + action["moment_on_first_at_point_xyz_nmm"]
                    )
            for load in field["body_applied_loads"]:
                if load["body"] == shaft["body"]:
                    f = np.asarray(load["force_xyz_n"])
                    total_f += f
                    total_m += np.cross(
                        np.asarray(load["point_xyz_mm"]) - p, f
                    ) + load.get("moment_xyz_nmm", [0.0, 0.0, 0.0])
            ferr, merr = float(np.linalg.norm(total_f)), float(np.linalg.norm(total_m))
            parent.require(
                ferr < 1e-3 and merr < 1e-3, "connected shaft does not close"
            )
            stack_rows.append(
                {
                    "case_id": case["case_id"],
                    "axis_id": aid,
                    "source_field": manifest["field"],
                    "connected_force_residual_n": ferr,
                    "connected_moment_residual_nmm": merr,
                    "thread_window": window,
                    "old_same_cut_shaft_marker": markers[aid],
                    "current_geometry_response_or_joint_capacity": None,
                }
            )
            all_rows.extend(own_rows)
    parent.require(
        len(all_rows) == 144 and len(stack_rows) == 48,
        "six-case connected stack census",
    )
    wood_rows = [r for r in all_rows if r["kind"] == "wood"]
    steel_rows = [r for r in all_rows if r["kind"] == "steel"]
    summaries = []
    moved = {r["axis_id"] for r in audited["geometry_delta"]["moved_shafts"]}
    for aid in sorted(ids):
        rows = [r for r in all_rows if r["axis_id"] == aid]
        own_stacks = [r for r in stack_rows if r["axis_id"] == aid]
        peak_shaft = max(
            own_stacks,
            key=lambda r: r["old_same_cut_shaft_marker"]["governing"][
                "specified_material_first_yield_index"
            ],
        )
        summaries.append(
            {
                "axis_id": aid,
                "moved_in_base_v3": aid in moved,
                "thread_window": own_stacks[0]["thread_window"],
                "peak_wood_affine_parameter_comparison": max(
                    (r for r in rows if r["kind"] == "wood"),
                    key=lambda r: r["affine_peak_over_Fe90_parameter"],
                ),
                "peak_steel_required_affine_bearing": max(
                    (r for r in rows if r["kind"] == "steel"),
                    key=lambda r: r["affine_trial_peak_projected_bearing_mpa"],
                ),
                "peak_old_shaft_first_yield_marker": {
                    "case_id": peak_shaft["case_id"],
                    "source_field": peak_shaft["source_field"],
                    **peak_shaft["old_same_cut_shaft_marker"],
                },
                "adjusted_complete_joint_resistance_n": None,
            }
        )
    parent.verify(pins)
    result = {
        "schema": "eoere_connected_stack_bearing_statics/v1",
        "status": "COMPLETE_PRESCRIBED_OLD_ACTION_STATICS_RESISTANCE_UNRESOLVED",
        "question": "Can continuous full-interval bearing reproduce all eight stacks' own forces and moments without assuming symmetric loading or summing capacities?",
        "source_geometry_revision": audited["six_field_geometry_revision"],
        "target_geometry_revision_not_evaluated": audited["current_geometry_revision"],
        "case_count": 6,
        "stack_case_count": 48,
        "member_case_count": 144,
        "maximum_connected_force_residual_n": max(
            r["connected_force_residual_n"] for r in stack_rows
        ),
        "maximum_connected_moment_residual_nmm": max(
            r["connected_moment_residual_nmm"] for r in stack_rows
        ),
        "maximum_raw_port_force_replay_error_n": max(
            r["raw_force_replay_error_n"] for r in all_rows
        ),
        "maximum_raw_port_moment_replay_error_nmm": max(
            r["raw_moment_replay_error_nmm"] for r in all_rows
        ),
        "peak_wood_affine_parameter_comparison": max(
            wood_rows, key=lambda r: r["affine_peak_over_Fe90_parameter"]
        ),
        "peak_steel_required_affine_bearing": max(
            steel_rows, key=lambda r: r["affine_trial_peak_projected_bearing_mpa"]
        ),
        "stacks": summaries,
        "known_answers": known,
        "source_pin_count": len(pins),
        "complete_source_canonical_sha256": parent.canonical(pins),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "source_observations": inputs["source_observations"],
        "limits": inputs["limits"],
        "execution": {
            "native_solve": False,
            "response_assembly": False,
            "geometry_rebuild": False,
            "physical_test": False,
        },
        "fabrication_or_climbing_release": False,
    }
    return result, {
        "complete_source_sha256": pins,
        "member_bearing_trials": all_rows,
        "connected_stacks": stack_rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    result, details = run()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (("result.json", result), ("details.json", details)):
        serialized = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.compare:
            parent.require(
                (args.compare / name).read_text() == serialized,
                "reproduction differs: " + name,
            )
        (args.out / name).write_text(serialized)
    print(
        json.dumps(
            {
                "status": result["status"],
                "stack_cases": result["stack_case_count"],
                "source_pins": result["source_pin_count"],
                "maximum_connected_force_residual_n": result[
                    "maximum_connected_force_residual_n"
                ],
                "maximum_connected_moment_residual_nmm": result[
                    "maximum_connected_moment_residual_nmm"
                ],
            }
        )
    )
