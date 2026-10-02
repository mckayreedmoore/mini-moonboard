"""Apply the service worker's circular-gap method to the top-right corner.

Reuse the simple six-case frame, all Hillman components and existing physical
operators. Keep geometry, material laws and load cases fixed. Only the four
right-corner lateral bolt laws receive their modeled relative clearance.
"""

import argparse
import copy
import fcntl
import importlib.util
import json
import math
from pathlib import Path

import lateral_reference as lateral
import numpy as np
import top_corner_actions as accounting
from scipy import linalg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKER = HERE.parent / "upper-left-service-frame-clearance-2026-10-01/check_frame.py"
BLOCK, RAIL, SIDE = "top_outer_right_cleat", "base_rail_top", "base_side_right"
sha, read, require = accounting.sha, accounting.read, accounting.require
FORCE_TOL, GAP_TOL = 1e-4, 1e-8


def maximum(value):
    return float(np.max(np.abs(value), initial=0.0))


def load_worker():
    spec = importlib.util.spec_from_file_location("saved_service_clearance", WORKER)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    return worker


def solve(H, D, e, W, k, uni, normals, tangents, targets, gaps, seed, worker):
    """Existing LU branch equations and pairwise circular gaps."""
    target_count = len(targets)
    pairs = targets.reshape(-1, 2)
    require(len(pairs) == len(gaps), "gap/bolt count mismatch")
    active = np.flatnonzero(uni & (seed > 1e-6))
    bilateral = np.flatnonzero(~uni & (k > 0))
    seen, history = set(), []
    for iteration in range(30):
        key = tuple(active)
        require(key not in seen, "normal active-set cycle")
        seen.add(key)
        held = tangents[np.isin(normals, active)].ravel()
        positions = np.sort(np.r_[bilateral, active, held])
        target_local = np.searchsorted(positions, targets)
        require(
            np.array_equal(positions[target_local], targets),
            "missing target lateral row",
        )
        n = len(positions)
        inverse_k = np.divide(
            1.0, k[positions], out=np.zeros(n), where=k[positions] > 0
        )
        matrix = np.zeros((n + 300, n + 300))
        matrix[:n, :n] = H[np.ix_(positions, positions)] + np.diag(inverse_k)
        matrix[:n, n:] = -D[positions]
        matrix[n:, :n] = D[positions].T
        rhs = np.zeros((n + 300, 1 + target_count))
        rhs[:n, 0], rhs[n:, 0] = e[positions], W
        rhs[target_local, np.arange(1, 1 + target_count)] = 1.0
        lu, pivot = linalg.lu_factor(matrix, check_finite=False)
        response = linalg.lu_solve((lu, pivot), rhs, check_finite=False)
        scale = np.repeat(gaps, 2)
        if np.max(scale) == 0:
            h, gap_audit = (
                np.zeros(target_count),
                {"projection_residual_mm": 0.0, "evaluations": 0},
            )
        else:
            # h=G*z converts the four unequal disks to unit disks. The
            # worker's existing projection solves G*f0 - G*R*G*z.
            z, gap_audit = worker.clearance_offsets(
                scale * response[target_local, 0],
                scale[:, None] * response[target_local, 1:] * scale[None, :],
                1.0,
            )
            h = scale * z
        value = response[:, 0] - response[:, 1:] @ h
        f = np.zeros(len(k))
        f[positions] = value[:n]
        a = value[n:]
        q = D @ a + e - H @ f
        release = active[f[active] < -FORCE_TOL]
        inactive = np.setdiff1d(np.flatnonzero(uni), active)
        engage = inactive[q[inactive] > GAP_TOL]
        history.append(
            {
                "iteration": iteration,
                "released": release.tolist(),
                "engaged": engage.tolist(),
            }
        )
        if not len(release) and not len(engage):
            break
        active = np.union1d(np.setdiff1d(active, release), engage)
    else:
        raise ValueError("normal active-set iteration limit")
    expected = k * np.where(uni, np.maximum(q, 0), q)
    expected_gap = np.zeros(target_count)
    for i, (pair, gap) in enumerate(zip(pairs, gaps, strict=True)):
        radius = np.linalg.norm(q[pair])
        expected_gap[2 * i : 2 * i + 2] = (
            k[pair] * max(radius - gap, 0.0) * q[pair] / max(radius, 1e-300)
        )
    expected[targets] = expected_gap
    audit = {
        "force_balance_n": maximum((D.T @ f - W).reshape(-1, 6)[:, :3]),
        "moment_balance_nmm": 1000 * maximum((D.T @ f - W).reshape(-1, 6)[:, 3:]),
        "finite_law_error_n": maximum(f[k > 0] - expected[k > 0]),
        "circular_gap_law_error_n": maximum(f[targets] - expected_gap),
        "minimum_unilateral_force_n": float(f[uni].min()),
        "held_floor_motion_mm": maximum(q[held]),
        "released_floor_force_n": maximum(f[np.setdiff1d(tangents.ravel(), held)]),
        "positive_normal_domain_mm": float(q[uni].max()),
        "open_normal_beyond_negative_table_endpoint": int(
            np.count_nonzero(q[uni] < -10)
        ),
        "gap_projection": gap_audit,
        "normal_branch_history": history,
    }
    require(
        audit["force_balance_n"] < 0.1 and audit["moment_balance_nmm"] < 2,
        "body imbalance",
    )
    require(
        audit["finite_law_error_n"] < FORCE_TOL
        and audit["minimum_unilateral_force_n"] >= -FORCE_TOL,
        "connector law failure",
    )
    require(
        audit["held_floor_motion_mm"] < GAP_TOL
        and audit["released_floor_force_n"] == 0.0,
        "floor law failure",
    )
    require(audit["positive_normal_domain_mm"] <= 10, "positive spring domain exceeded")
    rank_rows = np.union1d(
        bilateral, np.r_[np.flatnonzero(uni & (f > FORCE_TOL)), held]
    )
    free_gap_rows = (
        np.concatenate([pair for pair in pairs if np.linalg.norm(f[pair]) <= FORCE_TOL])
        if any(np.linalg.norm(f[pair]) <= FORCE_TOL for pair in pairs)
        else np.array([], dtype=int)
    )
    rank_rows = np.setdiff1d(rank_rows, free_gap_rows)
    audit["force_bearing_rigid_rank"] = int(np.linalg.matrix_rank(D[rank_rows]))
    require(audit["force_bearing_rigid_rank"] == 300, "unrestrained rigid coordinate")
    return f, q, a, audit


def diameter_reference(lengths, angles, diameter_mm, fyb):
    """Existing six-mode arithmetic with diameter-specific wood bearing."""
    d = diameter_mm / 25.4
    parallel, perpendicular = 5600.0, 6100 * 0.5**1.45 / math.sqrt(d)
    bearing = [
        parallel
        * perpendicular
        / (
            parallel * math.sin(math.radians(a)) ** 2
            + perpendicular * math.cos(math.radians(a)) ** 2
        )
        for a in angles
    ]
    factor = 1 + 0.25 * max(angles) / 90
    result = lateral.single_shear(
        main_length_in=lengths[0] / 25.4,
        side_length_in=lengths[1] / 25.4,
        main_bearing_lb_in=bearing[0] * d,
        side_bearing_lb_in=bearing[1] * d,
        main_yield_moment_lb_in=fyb * d**3 / 6,
        side_yield_moment_lb_in=fyb * d**3 / 6,
        gap_in=0,
        reduction_terms={
            key: value * factor
            for key, value in {
                "Im": 4.0,
                "Is": 4.0,
                "II": 3.6,
                "IIIm": 3.2,
                "IIIs": 3.2,
                "IV": 3.2,
            }.items()
        },
    )
    return result["reference_lateral_lbf"] * lateral.N_PER_LBF


def run(output, corrected=False):
    import simple_frame as frame

    require(not output.exists(), "preserve the existing comparison")
    ingestion = read(HERE / "service-and-hillman-ingestion.json")
    require(
        sha(WORKER) == ingestion["source_sha256"][str(WORKER.relative_to(ROOT))],
        "worker method changed",
    )
    pins = {accounting.COMP / name: digest for name, digest in frame.PINS.items()}
    for name in (
        "simple-frame-results.json",
        "simple-frame-response.npz",
        "service-and-hillman-ingestion.json",
        "simple_frame.py",
        "lateral_reference.py",
    ):
        pins[HERE / name] = sha(HERE / name)
    pins[WORKER] = sha(WORKER)
    pins[accounting.MODEL] = accounting.PINS[accounting.MODEL]
    pins[lateral.INPUTS] = lateral.PINS[lateral.INPUTS]
    pins[lateral.HELPER] = lateral.PINS[lateral.HELPER]
    source = HERE / "corner-frame-attempt01" if corrected else accounting.COMP
    result_path = (
        source / "frame-results.json"
        if corrected
        else HERE / "simple-frame-results.json"
    )
    response_path = (
        source / "frame-response.npz"
        if corrected
        else HERE / "simple-frame-response.npz"
    )
    baseline = read(result_path)
    require(
        sha(response_path) == baseline["response_sha256"], "response binding changed"
    )
    for path in (result_path, response_path):
        pins[path] = sha(path)
    if corrected:
        assessment = read(source / "operator-assessment.json")
        pins[source / "operator-assessment.json"] = sha(
            source / "operator-assessment.json"
        )
        pins.update(
            {
                source / name: digest
                for name, digest in assessment["output_sha256"].items()
            }
        )
        pins.update(
            {
                ROOT / path: digest
                for path, digest in assessment["source_sha256"].items()
            }
        )
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    rows = read(source / "row-identities.json")
    with np.load(source / "operators.npz", allow_pickle=False) as op:
        H, D, e, W, k, uni, normals, tangents, transform, _ = frame.lump_floor(
            *[op[n] for n in ("H", "D", "e", "W")], rows
        )
    H = (H + H.T) / 2
    retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    targets = np.array(
        [
            i
            for i, r in enumerate(retained)
            if r["ownership"]["role"] == accounting.LATERAL
            and BLOCK in (r["ownership"]["first_body"], r["ownership"]["second_body"])
        ]
    )
    require(len(targets) == 8, "expected four top-right lateral pairs")
    require(
        sum(r["ownership"]["role"] == "panel_screw_lateral_plane" for r in rows) == 132
        and sum(
            r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal"
            for r in rows
        )
        == 66,
        "missing Hillman path",
    )
    model = read(source / "model.json") if corrected else read(accounting.MODEL)
    names = (
        model["body_names"]
        if corrected
        else read(accounting.COMP / "assessment.json")[
            "body_names_in_rigid_column_order"
        ]
    )
    coordinates = model["physical_node_coordinates_mm"] if corrected else model["nodes"]
    body_nodes = model["body_nodes"] if corrected else model["physical_body_nodes"]
    centers = {
        body: np.mean([coordinates[str(n)] for n in body_nodes[body]], axis=0)
        for body in names
    }
    datum = centers[BLOCK]
    inputs = read(lateral.INPUTS)
    members = {
        r["member_id"]: r["reduced_geometry_descriptor"] for r in inputs["members"]
    }
    bolts = {
        r["axis_id"]: copy.deepcopy(r)
        for r in inputs["connections"]
        if r["kind"] == "candidate_bolt"
    }
    target_axes = [
        retained[int(pair[0])]["row_id"].rsplit("/", 1)[0]
        for pair in targets.reshape(4, 2)
    ]
    if corrected:
        for axis in target_axes:
            bolt = bolts[axis]
            side = "/side_" in axis
            bolt["source_record"]["geometry"]["modeled_shaft_diameter_mm"] = (
                7.9375 if side else 6.35
            )
            for receiver in bolt["receiver_clearance_geometry"]:
                receiver["unique_bore_radius_mm"] = 4.5 if side else 3.75
            if not side:
                interval = next(
                    r
                    for r in bolt["source_record"]["geometry"][
                        "wood_receiver_intervals"
                    ]
                    if r["receiver_id"] == BLOCK
                )
                spans = interval[
                    "current_shaft_intersection_solid_intervals_from_underhead_mm"
                ]
                interval[
                    "current_shaft_intersection_solid_intervals_from_underhead_mm"
                ] = [[spans[0][0], spans[0][0] + 139.7]]
    gaps = np.array(
        [
            sum(
                r["unique_bore_radius_mm"]
                - bolts[axis]["source_record"]["geometry"]["modeled_shaft_diameter_mm"]
                / 2
                for r in bolts[axis]["receiver_clearance_geometry"]
            )
            for axis in target_axes
        ]
    )
    require(np.all(gaps > 0), "nonpositive modeled relative clearance")
    worker = load_worker()
    states, arrays = [], {}
    with np.load(response_path, allow_pickle=False) as saved:
        for clearance_scale in (0.0, 1.0):
            gap = float(gaps.max()) * clearance_scale
            for i, case in enumerate(baseline["cases"]):
                name = case["case_id"]
                seed = transform @ saved[name + "_force_n"]
                seed[normals] = saved[name + "_bearing_mask"]
                f, q, a, audit = solve(
                    H,
                    D,
                    baseline["dead_load_factor"] * e[:, 2 * i] + e[:, 2 * i + 1],
                    baseline["dead_load_factor"] * W[:, 2 * i] + W[:, 2 * i + 1],
                    k,
                    uni,
                    normals,
                    tangents,
                    targets,
                    gaps * clearance_scale,
                    seed,
                    worker,
                )
                raw = transform.T @ f
                pairs, fits, wrenches = [], {}, {}
                bi = names.index(BLOCK)
                for pair in targets.reshape(4, 2):
                    r = retained[int(pair[0])]
                    axis = r["row_id"].rsplit("/", 1)[0]
                    host = (
                        r["ownership"]["second_body"]
                        if r["ownership"]["first_body"] == BLOCK
                        else r["ownership"]["first_body"]
                    )
                    vector = -D[pair, 6 * bi : 6 * bi + 3].T @ f[pair]
                    lengths = [
                        span[
                            "current_shaft_intersection_solid_intervals_from_underhead_mm"
                        ][0][1]
                        - span[
                            "current_shaft_intersection_solid_intervals_from_underhead_mm"
                        ][0][0]
                        for span in bolts[axis]["source_record"]["geometry"][
                            "wood_receiver_intervals"
                        ]
                    ]
                    grains = [
                        members[b]["axis"] for b in bolts[axis]["receiver_member_ids"]
                    ]
                    angles = [lateral.angle(vector, g) for g in grains]
                    diameter = bolts[axis]["source_record"]["geometry"][
                        "modeled_shaft_diameter_mm"
                    ]
                    refs = {
                        str(fyb): diameter_reference(lengths, angles, diameter, fyb)
                        for fyb in (45000, 92000, 106000)
                    }
                    pairs.append(
                        {
                            "axis_id": axis,
                            "diameter_mm": diameter,
                            "modeled_relative_clearance_mm": float(
                                gaps[target_axes.index(axis)] * clearance_scale
                            ),
                            "host": host,
                            "lateral_n": float(np.linalg.norm(vector)),
                            "force_on_cleat_xyz_n": vector.tolist(),
                            "slip_mm": float(np.linalg.norm(q[pair])),
                            "conditional_unadjusted_references_n": refs,
                            "conditional_unadjusted_ratios": {
                                fyb: float(np.linalg.norm(vector)) / ref
                                for fyb, ref in refs.items()
                            },
                        }
                    )
                for host in (RAIL, SIDE):
                    ports = np.array(
                        [
                            i
                            for i, r in enumerate(retained)
                            if {
                                r["ownership"]["first_body"],
                                r["ownership"]["second_body"],
                            }
                            == {BLOCK, host}
                        ]
                    )
                    mapping = D[ports, 6 * bi : 6 * bi + 6].copy()
                    generalized = -mapping.T @ f[ports]
                    wrenches[host] = {
                        "force_on_cleat_n": generalized[:3].tolist(),
                        "moment_on_cleat_nmm": (1000 * generalized[3:]).tolist(),
                    }
                    mapping[:, 3:] *= 1000
                    pose, _, rank, _ = np.linalg.lstsq(mapping, q[ports], rcond=None)
                    require(rank == 6, "incomplete interface motion fit")
                    fits[host] = {
                        "translation_mm": pose[:3].tolist(),
                        "rotation_rad": pose[3:].tolist(),
                        "projection_residual_mm": maximum(mapping @ pose - q[ports]),
                    }
                relative = (
                    np.array(fits[SIDE]["translation_mm"])
                    - fits[RAIL]["translation_mm"]
                )
                rotation = (
                    np.array(fits[SIDE]["rotation_rad"]) - fits[RAIL]["rotation_rad"]
                )
                screw_states = []
                for screw in (
                    r
                    for r in inputs["connections"]
                    if r["kind"] == "panel_screw"
                    and r["receiver_member_ids"][0] == "main_upper_right"
                ):
                    axis = screw["axis_id"]
                    components = [r for r in rows if r["row_id"].split("/")[0] == axis]
                    require(len(components) == 3, "incomplete right-panel screw state")
                    pi = names.index("main_upper_right")
                    ids = [r["row"] for r in components]
                    panel_force = -(
                        (read_original_D(rows, transform, D, ids, pi)) @ raw[ids]
                    )
                    tension = next(
                        raw[r["row"]]
                        for r in components
                        if r["ownership"]["role"]
                        == "non_qualifying_parametric_screw_withdrawal"
                    )
                    lateral_n = math.sqrt(
                        sum(
                            raw[r["row"]] ** 2
                            for r in components
                            if r["ownership"]["role"] == "panel_screw_lateral_plane"
                        )
                    )
                    screw_states.append(
                        {
                            "axis_id": axis,
                            "receiver": screw["receiver_member_ids"][1],
                            "force_on_panel_xyz_n": panel_force.tolist(),
                            "lateral_n": lateral_n,
                            "withdrawal_n": float(tension),
                        }
                    )
                ties = [
                    r["row"]
                    for r in rows
                    if r["ownership"]["role"] == "physical_bolt_outer_seat_tension"
                    and BLOCK
                    in (r["ownership"]["first_body"], r["ownership"]["second_body"])
                ]
                states.append(
                    {
                        "case_id": name,
                        "clearance_mm": gap,
                        "status": "PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                        "audit": audit,
                        "bolts": pairs,
                        "peak_bolt_tension_n": float(raw[ties].max()),
                        "interface_wrenches": wrenches,
                        "local_interface_fits": fits,
                        "local_rail_side_movement_mm": float(np.linalg.norm(relative)),
                        "local_rail_side_rotation_degrees": float(
                            np.rad2deg(np.linalg.norm(rotation))
                        ),
                        "right_upper_panel_screws": screw_states,
                        "zero_gap_difference_from_saved_force_n": maximum(
                            raw - saved[name + "_force_n"]
                        )
                        if gap == 0
                        else None,
                    }
                )
                key = name + ("_zero" if gap == 0 else "_gap")
                arrays.update(
                    {
                        key + "_raw_force_n": raw,
                        key + "_lumped_q_mm": q,
                        key + "_rigid_coordinates": a,
                    }
                )
                print(
                    name,
                    gap,
                    "peak bolt lateral",
                    max(b["lateral_n"] for b in pairs),
                    "local motion",
                    states[-1]["local_rail_side_movement_mm"],
                    flush=True,
                )
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    output.mkdir()
    np.savez_compressed(output / "response.npz", **arrays)
    report = {
        "schema": "top_right_corner_coupled_clearance_comparison/v1",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "response_sha256": sha(output / "response.npz"),
        "candidate": "compact-floor-flush-wood-joints-development",
        "source_revision": "led-clearance-2x6-runner-seated-blocks-v1",
        "analysis_geometry": "isolated top-corner 4x6/5_16 proposal"
        if corrected
        else "reviewed geometry",
        "modeled_mass_kg": baseline["modeled_mass_kg"],
        "dead_load_factor": baseline["dead_load_factor"],
        "modeled_relative_clearances_mm": {
            axis: float(gap) for axis, gap in zip(target_axes, gaps, strict=True)
        },
        "common_datum_mm": datum.tolist(),
        "states": states,
        "limits": [
            "Only this corner has lateral clearance. Other bolted joints remain zero gap.",
            "All 66 Hillman axes retain their conditional 2689.679 N/mm lateral and axial laws; this is load sharing, not product strength qualification.",
            "Loads, wood/plywood stiffness and no-slip lumped floor assumptions are the parent's six-case simple model, not the worker's doubled three-case histories.",
            "Zero force is extended on open contacts beyond the negative table endpoint if reported; positive branches remain within 10 mm.",
            "Local interface fits are approximations with reported residuals, not total member or panel deflections.",
            "Single-bolt lateral ratios are unadjusted references; splitting, group effects and complete resistance are separate.",
        ],
        "reviewed_geometry_changed": False,
        "hardware_change_selected": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    (output / "comparison.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())


def read_original_D(rows, transform, D, ids, body_index):
    """Nonfloor rows survive the floor transform unchanged, including screws."""
    lumped = [int(np.flatnonzero(transform[:, i])[0]) for i in ids]
    require(
        all(transform[j, i] == 1.0 for j, i in zip(lumped, ids, strict=True)),
        "unexpected screw transform",
    )
    return D[lumped, 6 * body_index : 6 * body_index + 3].T


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--corrected",
        action="store_true",
        help="Use the preserved isolated top-corner proposal frame.",
    )
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(
            read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
            "shared analysis slot occupied",
        )
        run(args.output, args.corrected)
