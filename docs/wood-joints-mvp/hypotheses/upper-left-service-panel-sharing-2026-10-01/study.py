#!/usr/bin/env python3
"""Reuse the completed frame baseline; vary only hypothetical Hillman laws."""

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = HERE.parent / "upper-left-service-frame-clearance-2026-10-01"
PANEL = HERE.parent / "current-panel-receiver-transfer-2026-10-01"
PINS = {
    PRIOR
    / "check_frame.py": "54ebbd0259fa15a201ba05da035df9fca88d65987ff4473b4322216f8ca42164",
    PRIOR
    / "comparison-final.json": "8ab5575e11cb79b7e330131f101e866a985c459454f32da5b5a1b6c93741d883",
    PRIOR
    / "response-vectors-final.npz": "1dcba6ca765393917a63934733bcd29b4766be14f62fcef96ae5d21f5bf2586e",
    PRIOR
    / "parent-validation.json": "7e29a41a7d689d884cfdcba7c7f1eb920f0e66da03d1d46098dd30dc8280d1eb",
    PANEL
    / "receiver-transfer.json": "0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534",
    PANEL
    / "hillman-applicability.md": "8a5f5a031c429eee9d2c08a20047dd0b01c2b1be44b849b30132cc3ad5056354",
}


def sha(path):
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def authenticate(pins):
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError(f"source pin changed: {path}")


def rows_for(frame, role):
    return np.array(
        [i for i, r in enumerate(frame.rows) if r["ownership"]["role"] == role]
    )


def no_withdrawal_certificate(frame, withdrawal):
    """Project D.T f=W onto a source-geometry outward rigid translation.

    This is a necessary force-equilibrium condition, independent of stiffness.
    A singular trial branch alone would not prove the absence of equilibrium.
    """
    certificates = []
    tolerance = 1e-12
    remaining = np.setdiff1d(frame.unilateral, withdrawal)
    floor = np.arange(1640, 1840)
    for panel in ("main_upper_left", "main_upper_right"):
        own = np.array(
            [
                i
                for i in withdrawal
                if frame.rows[int(i)]["ownership"]["second_body"] == panel
            ]
        )
        normal = np.array(frame.rows[int(own[0])]["ownership"]["direction_global_xyz"])
        if len(own) != 12 or abs(np.linalg.norm(normal) - 1) > tolerance:
            raise ValueError("upper panel withdrawal geometry differs")
        mode = np.zeros(300)
        start = 6 * frame.body_names.index(panel)
        mode[start : start + 3] = normal
        projection = frame.D @ mode
        bilateral_error = float(np.max(np.abs(projection[frame.bilateral])))
        unilateral_positive = float(np.max(projection[remaining]))
        floor_error = float(np.max(np.abs(projection[floor])))
        own_error = float(np.max(np.abs(projection[own] - 1)))
        if (
            max(bilateral_error, unilateral_positive, floor_error, own_error)
            > tolerance
        ):
            raise ValueError("outward-mode certificate sign/orthogonality check failed")
        states = []
        for case in sorted(frame.sources):
            columns = [
                c["column"]
                for c in frame.record["load_columns"]
                if c["case_id"] == case
            ]
            for increment, inc in enumerate(frame.sources[case]["increments"]):
                required = float(
                    mode @ (2 * inc["load_factor"] * frame.W[:, columns].sum(axis=1))
                )
                if required <= 1e-6:
                    raise ValueError(
                        "nonpositive outward load; cannot claim no-credit failure"
                    )
                states.append(
                    {
                        "case": case,
                        "increment": increment,
                        "minimum_group_withdrawal_n": required,
                        "equal_share_average_lower_bound_n": required / len(own),
                    }
                )
        certificates.append(
            {
                "panel": panel,
                "outward_translation_global_xyz": normal.tolist(),
                "withdrawal_rows": own.tolist(),
                "states": states,
                "bilateral_projection_max_abs": bilateral_error,
                "remaining_unilateral_projection_max": unilateral_positive,
                "floor_projection_max_abs": floor_error,
                "withdrawal_unit_projection_max_error": own_error,
                "projection_roundoff_tolerance": tolerance,
                "status": "NO_EQUILIBRIUM_WITH_ZERO_WITHDRAWAL_IN_DECLARED_MODEL",
            }
        )
    return certificates


def screw_actions(frame, f, lateral, withdrawal):
    force = f[withdrawal]
    i = int(np.argmax(force))
    row = frame.rows[int(withdrawal[i])]
    groups = {}
    for panel in sorted(
        {frame.rows[int(r)]["ownership"]["second_body"] for r in withdrawal}
    ):
        own = [
            r
            for r in withdrawal
            if frame.rows[int(r)]["ownership"]["second_body"] == panel
        ]
        groups[panel] = float(f[own].sum())
    return {
        "peak_withdrawal_n": float(force[i]),
        "peak_withdrawal_axis": row["row_id"].split("/")[0],
        "peak_withdrawal_receiver": row["ownership"]["first_body"],
        "peak_lateral_resultant_n": float(
            np.linalg.norm(f[lateral].reshape(66, 2), axis=1).max()
        ),
        "withdrawal_group_totals_n": groups,
    }


def produce():
    authenticate(PINS)
    spec = importlib.util.spec_from_file_location(
        "saved_frame_helper", PRIOR / "check_frame.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    frame = helper.Frame()
    prior, validation, panel = (
        read(PRIOR / "comparison-final.json"),
        read(PRIOR / "parent-validation.json"),
        read(PANEL / "receiver-transfer.json"),
    )
    pins = dict(PINS)
    pins.update({ROOT / p: h for p, h in prior["source_sha256"].items()})
    authority = {
        ROOT / p: h for p, h in validation["authority_sha256_unchanged"].items()
    }
    pins.update(authority)
    authenticate(pins)
    lateral = rows_for(frame, "panel_screw_lateral_plane")
    withdrawal = rows_for(frame, "non_qualifying_parametric_screw_withdrawal")
    if not np.array_equal(lateral, np.arange(216, 348)) or not np.array_equal(
        withdrawal, np.arange(1470, 1536)
    ):
        raise ValueError("current 66-axis row mapping differs")
    for i, r in enumerate(withdrawal):
        axis = frame.rows[int(r)]["row_id"].split("/")[0]
        if any(
            frame.rows[int(j)]["row_id"].split("/")[0] != axis
            for j in lateral[2 * i : 2 * i + 2]
        ):
            raise ValueError("screw lateral/withdrawal pairing differs")
    base_k = frame.k.copy()
    if np.ptp(base_k[np.r_[lateral, withdrawal]]) > 1e-10:
        raise ValueError("source axial/lateral stiffness ratio differs from one")
    certificates = no_withdrawal_certificate(frame, withdrawal)
    source_peaks = []
    for case in sorted(frame.sources):
        saved = [s for s in panel["actions"]["states"] if s["case"] == case]
        peak = max(
            (
                screw["withdrawal_scalar_component"]["native_internal_force_n"],
                screw["axis_id"],
            )
            for s in saved
            for screw in s["screw_states"]
        )
        source_peaks.append(
            {"case": case, "peak_withdrawal_n": peak[0], "axis": peak[1]}
        )
        for s in saved:
            _, f, _, _ = frame.source_state(case, s["increment_index"])
            by_axis = {r["axis_id"]: r for r in s["screw_states"]}
            if any(
                abs(
                    f[int(i)]
                    - by_axis[frame.rows[int(i)]["row_id"].split("/")[0]][
                        "withdrawal_scalar_component"
                    ]["native_internal_force_n"]
                )
                > 1e-9
                for i in withdrawal
            ):
                raise ValueError(
                    "existing screw-force packet and reused frame sources differ"
                )
    # ponytail: reuse all 21 saved baseline states; only 42 new solves are needed.
    selected = [
        (i, r)
        for i, r in enumerate(prior["states"])
        if r["clearance_mm"] == 1.15
        and r["lateral_stiffness_n_per_mm"] == "frozen source"
    ]
    if len(selected) != 21:
        raise ValueError("saved baseline does not contain exactly 21 states")
    states, arrays, stopped = [], [], []
    with np.load(PRIOR / "response-vectors-final.npz", allow_pickle=False) as data:
        for i, r in selected:
            values = {key: data[key][i].copy() for key in ("f", "q", "a")}
            r["hillman_stiffness_multiplier"] = 1.0
            r["calculation_origin"] = "REUSED_SAVED_BASELINE"
            r["panel_screw_actions"] = screw_actions(
                frame, values["f"], lateral, withdrawal
            )
            states.append(r)
            arrays.append(values)
    for multiplier in (0.5, 0.25):
        frame.k = base_k.copy()
        frame.k[np.r_[lateral, withdrawal]] *= multiplier
        for case in sorted(frame.sources):
            for increment in range(7):
                try:
                    r, values = frame.evaluate(case, increment, 2.0, 1.15)
                except ValueError as exc:
                    # Preserve the helper's existing gates. A changed floor
                    # branch is a comparison stop, not a physical failure.
                    prefix = "source normal law/domain failed: "
                    if not str(exc).startswith(prefix):
                        raise
                    diagnostic = ast.literal_eval(str(exc)[len(prefix) :])
                    if diagnostic["floor_branch_consistent"]:
                        raise
                    stopped.append(
                        {
                            "hillman_stiffness_multiplier": multiplier,
                            "case": case,
                            "increment": increment,
                            "status": "STOP_FIXED_SOURCE_FLOOR_BRANCH",
                            "helper_diagnostic": diagnostic,
                            "physical_frame_failure_established": False,
                        }
                    )
                    print(
                        f"multiplier={multiplier} {case} increment={increment}: STOP_FIXED_SOURCE_FLOOR_BRANCH",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue
                if not r["audit"]["floor_branch_consistent"]:
                    raise ValueError(
                        "helper returned an inconsistent floor without its law refusal"
                    )
                r["hillman_stiffness_multiplier"] = multiplier
                r["calculation_origin"] = "NEW_HYPOTHETICAL_STIFFNESS_COMPARISON"
                r["panel_screw_actions"] = screw_actions(
                    frame, values["f"], lateral, withdrawal
                )
                # Check both changed laws directly against all returned rows.
                error = helper.maxabs(
                    values["f"][lateral] - frame.k[lateral] * values["q"][lateral]
                )
                if error > 1e-6:
                    raise ValueError("changed lateral spring law failed")
                r["audit"]["hillman_lateral_law_residual_n"] = error
                states.append(r)
                arrays.append(values)
                print(
                    f"multiplier={multiplier} {case} increment={increment}: {r['status']}",
                    file=sys.stderr,
                    flush=True,
                )
    summary = []
    for multiplier in (1.0, 0.5, 0.25):
        group = [r for r in states if r["hillman_stiffness_multiplier"] == multiplier]
        refused = [
            r for r in stopped if r["hillman_stiffness_multiplier"] == multiplier
        ]
        if not group:
            summary.append(
                {
                    "hillman_stiffness_multiplier": multiplier,
                    "hypothetical_lateral_and_withdrawal_k_n_per_mm": float(
                        base_k[lateral[0]] * multiplier
                    ),
                    "attempted_states": len(refused),
                    "states": 0,
                    "floor_consistent_states": 0,
                    "stopped_states": len(refused),
                    "local_host_movement_peak_mm": None,
                    "local_host_rotation_peak_deg": None,
                    "panel_screw_peak_withdrawal_n": None,
                }
            )
            continue
        worst = max(group, key=lambda r: r["panel_screw_actions"]["peak_withdrawal_n"])
        summary.append(
            {
                "hillman_stiffness_multiplier": multiplier,
                "hypothetical_lateral_and_withdrawal_k_n_per_mm": float(
                    base_k[lateral[0]] * multiplier
                ),
                "states": len(group),
                "attempted_states": len(group) + len(refused),
                "stopped_states": len(refused),
                "floor_consistent_states": sum(
                    r["audit"]["floor_branch_consistent"] for r in group
                ),
                "local_host_movement_peak_mm": max(
                    r["local_fit_rail_side_movement_mm"] for r in group
                ),
                "local_host_rotation_peak_deg": max(
                    r["local_fit_rail_side_rotation_deg"] for r in group
                ),
                "target_bolt_peak_shear_n": max(
                    b["shear_n"] for r in group for b in r["target_bolts"]
                ),
                "target_bolt_peak_tension_n": max(
                    max(r["target_axial_tension_n"]) for r in group
                ),
                "panel_screw_peak_withdrawal_n": worst["panel_screw_actions"][
                    "peak_withdrawal_n"
                ],
                "withdrawal_peak_case": worst["case"],
                "withdrawal_peak_increment": worst["increment"],
                "withdrawal_peak_axis": worst["panel_screw_actions"][
                    "peak_withdrawal_axis"
                ],
                "panel_screw_peak_lateral_resultant_n": max(
                    r["panel_screw_actions"]["peak_lateral_resultant_n"] for r in group
                ),
                "upper_left_withdrawal_group_peak_n": max(
                    r["panel_screw_actions"]["withdrawal_group_totals_n"][
                        "main_upper_left"
                    ]
                    for r in group
                ),
                "local_fit_maximum_projection_residual_mm": max(
                    f["maximum_nonrigid_projection_residual_mm"]
                    for r in group
                    for f in r["local_interface_projection_fits"].values()
                ),
            }
        )
    authenticate(pins)
    report = {
        "schema": "upper_left_service_panel_sharing/v1",
        "status": "CONDITIONAL_COMPARISON_ONLY",
        "complete_joint": "HOLD",
        "release": False,
        "native_run": False,
        "geometry_changed": False,
        "load_scale": 2.0,
        "clearance_mm": 1.15,
        "reused_states": 21,
        "new_state_attempts": 42,
        "new_valid_states": len(states) - 21,
        "stopped_states": stopped,
        "stiffness_range_status": "Hypothetical 0.25x/0.5x/1x source laws, not Hillman product bounds; both lateral and withdrawal vary together, ratio 1 retained.",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "authority_sha256_unchanged": validation["authority_sha256_unchanged"],
        "source_panel_packet_counts": panel["actions"]["counts"],
        "existing_source_withdrawal_peaks": source_peaks,
        "zero_withdrawal_certificates": certificates,
        "summary": summary,
        "states": states,
    }
    report["source_sha256"][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    return report, {key: np.stack([a[key] for a in arrays]) for key in ("f", "q", "a")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vectors", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.vectors.exists():
        raise ValueError("refusing to overwrite existing evidence")
    report, vectors = produce()
    np.savez_compressed(args.vectors, **vectors)
    report["vectors_sha256"] = sha(args.vectors)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sha256": sha(args.output),
                "summary": report["summary"],
            }
        )
    )


if __name__ == "__main__":
    main()
