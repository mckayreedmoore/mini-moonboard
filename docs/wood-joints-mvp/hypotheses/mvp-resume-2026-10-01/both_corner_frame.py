"""One corrected six-case frame with selected outer-joint clearances included.

Reuse the frozen corrected physical operators and the service worker's
pairwise circular-gap equations. Keep all 66 Hillman axes and explicit
conditional panel properties. Floor bearing and tangent branches may change.
"""

import argparse
import fcntl
import json
from pathlib import Path

import circular_clearance
import numpy as np
import right_corner_clearance as method
import top_corner_actions as accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
sha, read, require = accounting.sha, accounting.read, accounting.require


def retain_stop(
    output,
    vectors,
    local,
    pins,
    k,
    uni,
    normals,
    tangents,
    targets,
    gaps,
    states,
    case_id,
    gap_scale,
    error,
):
    """Preserve a terminal iterate without admitting it as a completed state."""
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    output.mkdir()
    np.savez_compressed(output / "partial-response.npz", **vectors)
    iterate = {name: local[name] for name in ("f", "q", "a") if name in local}
    np.savez_compressed(
        output / "unaccepted-iterate.npz",
        **iterate,
        k=k,
        unilateral=uni,
        floor_normals=normals,
        floor_tangents=tangents,
        clearance_targets=targets,
        clearance_gaps=gaps,
    )
    stop = {
        "schema": "conditional_frame_calculation_stop/v1",
        "case_id": case_id,
        "gap_scale": gap_scale,
        "terminal_exception": str(error),
        "completed_states": states,
        "last_iterate_is_accepted": False,
        "audit_if_available": local.get("audit"),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "producer_sha256": sha(Path(__file__)),
        "physical_frame_failure_claim": False,
        "baseline_replaced": False,
    }
    (output / "stop.json").write_text(
        json.dumps(stop, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())


def run(
    output,
    service_joints=False,
    bottom_corners=False,
    panel_withdrawal_stiffness=None,
    panel_lateral_stiffness=None,
    all_two_receiver_clearances=False,
    bounded_freeplay=False,
):
    import simple_frame as frame

    require(not output.exists(), "preserve the existing calculation")
    assessment = read(FRAME / "operator-assessment.json")
    baseline = read(FRAME / "frame-results.json")
    pins = {ROOT / name: digest for name, digest in assessment["source_sha256"].items()}
    if bounded_freeplay:
        import bounded_clearance

        pins[Path(bounded_clearance.__file__)] = sha(Path(bounded_clearance.__file__))
    pins.update(
        {FRAME / name: digest for name, digest in assessment["output_sha256"].items()}
    )
    pins[FRAME / "frame-response.npz"] = baseline["response_sha256"]
    for path in (
        FRAME / "frame-results.json",
        FRAME / "operator-assessment.json",
        HERE / "service-and-hillman-ingestion.json",
        Path(frame.__file__),
        Path(method.__file__),
        Path(circular_clearance.__file__),
    ):
        pins[path] = sha(path)
    connections_path = (
        HERE.parent
        / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
    )
    connections = {
        c["axis_id"]: c
        for c in read(connections_path)["connections"]
        if c["kind"] == "candidate_bolt"
    }
    if all_two_receiver_clearances:
        require(len(connections) == 92, "candidate bolt census changed")
        pins[connections_path] = sha(connections_path)
    sharing = HERE.parent / "upper-left-service-panel-sharing-2026-10-01"
    receipt = read(sharing / "receipt.json")
    for name, digest in receipt["artifacts_sha256"].items():
        pins[sharing / name] = digest
    pins[sharing / "receipt.json"] = (
        "9b543630412ea9d2be8e832c49547b0ced910f1bd11641475d10b470be53eb5b"
    )
    block_hosts = dict(accounting.BLOCK_HOSTS)
    if service_joints:
        lower = HERE.parent / "lower-left-service-joint"
        completion = lower / "results/attempt01/receipt.json"
        pins[completion] = (
            "dbf9cd4b761af02671a0f91d0539ce755607561cdc84d70a32297f1847918991"
        )
        transferred = read(completion)
        pins.update({lower / p: h for p, h in transferred["artifacts_sha256"].items()})
        pins.update(
            {ROOT / p: h for p, h in transferred["authority_sha256_unchanged"].items()}
        )
        block_hosts.update(
            {
                "left_service_outer_upper_cleat": (
                    "base_rail_service_upper_left",
                    "base_side_left",
                ),
                "left_service_outer_lower_cleat": (
                    "base_rail_service_lower_left",
                    "base_side_left",
                ),
            }
        )
    if bottom_corners:
        block_hosts.update(
            {
                "bottom_outer_left_cleat": (
                    "base_rail_bottom_left",
                    "base_side_left",
                ),
                "bottom_outer_right_cleat": (
                    "base_rail_bottom_right",
                    "base_side_right",
                ),
            }
        )
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    rows = read(FRAME / "row-identities.json")
    with np.load(FRAME / "operators.npz", allow_pickle=False) as operators:
        H, D, e, W, k, uni, normals, tangents, transform, floors = frame.lump_floor(
            *[operators[n] for n in ("H", "D", "e", "W")], rows
        )
    H = (H + H.T) / 2
    retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    corners = set(block_hosts)
    targets = np.array(
        [
            i
            for i, r in enumerate(retained)
            if r["ownership"]["role"] == accounting.LATERAL
            and (
                len(connections[r["row_id"].rsplit("/", 1)[0]]["receiver_member_ids"])
                == 2
                if all_two_receiver_clearances
                else corners.intersection(
                    (r["ownership"]["first_body"], r["ownership"]["second_body"])
                )
            )
        ]
    )
    require(
        len(targets) == (176 if all_two_receiver_clearances else 8 * len(corners)),
        "joint lateral inventory mismatch",
    )
    gaps = np.array(
        [
            1.0625
            if "/side_" in retained[int(pair[0])]["row_id"]
            and set(accounting.BLOCK_HOSTS).intersection(
                (
                    retained[int(pair[0])]["ownership"]["first_body"],
                    retained[int(pair[0])]["ownership"]["second_body"],
                )
            )
            else 1.15
            for pair in targets.reshape(-1, 2)
        ]
    )
    if all_two_receiver_clearances:
        for i, pair in enumerate(targets.reshape(-1, 2)):
            row = retained[int(pair[0])]
            axis = row["row_id"].rsplit("/", 1)[0]
            if set(accounting.BLOCK_HOSTS).intersection(
                (row["ownership"]["first_body"], row["ownership"]["second_body"])
            ):
                continue  # The isolated top proposal has its own changed bore geometry.
            records = connections[axis]["receiver_clearance_geometry"]
            require(len(records) == 2, "two-receiver clearance geometry missing")
            values = [r["geometry_only_centered_radial_gap_mm"] for r in records]
            require(
                all(v is not None and v >= 0 for v in values), "unresolved bore gap"
            )
            gaps[i] = sum(values)
    screw_lateral = [
        i
        for i, r in enumerate(retained)
        if r["ownership"]["role"] == "panel_screw_lateral_plane"
    ]
    screw_axial = [
        i
        for i, r in enumerate(retained)
        if r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal"
    ]
    require(
        len(screw_lateral) == 132 and len(screw_axial) == 66,
        "Hillman inventory changed",
    )
    original_withdrawal = k[screw_axial].copy()
    original_lateral = k[screw_lateral].copy()
    if panel_withdrawal_stiffness is not None:
        require(
            np.isfinite(panel_withdrawal_stiffness) and panel_withdrawal_stiffness > 0,
            "withdrawal stiffness must be finite and positive",
        )
        k[screw_axial] = panel_withdrawal_stiffness
    if panel_lateral_stiffness is not None:
        require(
            np.isfinite(panel_lateral_stiffness) and panel_lateral_stiffness > 0,
            "lateral stiffness must be finite and positive",
        )
        k[screw_lateral] = panel_lateral_stiffness
    model = read(FRAME / "model.json")
    names = model["body_names"]
    centers = {
        b: np.mean(
            [
                model["physical_node_coordinates_mm"][str(n)]
                for n in model["body_nodes"][b]
            ],
            axis=0,
        )
        for b in corners
    }
    states, vectors = [], {}
    with np.load(FRAME / "frame-response.npz", allow_pickle=False) as saved:
        for gap_scale in (0.0, 1.0):
            for index, source in enumerate(baseline["cases"]):
                case_id = source["case_id"]
                seed = transform @ saved[case_id + "_force_n"]
                seed[normals] = saved[case_id + "_bearing_mask"]
                work = (
                    baseline["dead_load_factor"] * W[:, 2 * index] + W[:, 2 * index + 1]
                )
                certificate = None
                try:
                    f, q, a, audit = method.solve(
                        H,
                        D,
                        baseline["dead_load_factor"] * e[:, 2 * index]
                        + e[:, 2 * index + 1],
                        work,
                        k,
                        uni,
                        normals,
                        tangents,
                        targets,
                        gap_scale * gaps,
                        seed,
                        circular_clearance,
                    )
                except ValueError as error:
                    # Retain a failed calculation without treating its last iterate
                    # as an accepted state or discarding completed earlier states.
                    trace = error.__traceback__
                    local = {}
                    while trace is not None:
                        if trace.tb_frame.f_code is method.solve.__code__:
                            local = trace.tb_frame.f_locals
                        trace = trace.tb_next
                    if (
                        bounded_freeplay
                        and str(error) == "unrestrained rigid coordinate"
                    ):
                        try:
                            certificate, _ = (
                                bounded_clearance.finite_clearance_certificate(
                                    D,
                                    local["q"],
                                    local["f"],
                                    k,
                                    uni,
                                    normals,
                                    tangents,
                                    targets,
                                    gap_scale * gaps,
                                    work,
                                )
                            )
                            require(
                                certificate["bounded"],
                                "unbounded fixed-force clearance motion",
                            )
                        except ValueError as certificate_error:
                            retain_stop(
                                output,
                                vectors,
                                local,
                                pins,
                                k,
                                uni,
                                normals,
                                tangents,
                                targets,
                                gap_scale * gaps,
                                states,
                                case_id,
                                gap_scale,
                                certificate_error,
                            )
                            raise
                        f, q, a, audit = (local[n] for n in ("f", "q", "a", "audit"))
                    else:
                        retain_stop(
                            output,
                            vectors,
                            local,
                            pins,
                            k,
                            uni,
                            normals,
                            tangents,
                            targets,
                            gap_scale * gaps,
                            states,
                            case_id,
                            gap_scale,
                            error,
                        )
                        raise
                raw = transform.T @ f
                corner_results = []
                for block, hosts in block_hosts.items():
                    block_index = names.index(block)
                    fits, wrenches, bolts = {}, {}, []
                    for host in hosts:
                        ports = np.array(
                            [
                                i
                                for i, r in enumerate(retained)
                                if {
                                    r["ownership"]["first_body"],
                                    r["ownership"]["second_body"],
                                }
                                == {block, host}
                            ]
                        )
                        mapping = D[ports, 6 * block_index : 6 * block_index + 6].copy()
                        wrench = -mapping.T @ f[ports]
                        wrenches[host] = {
                            "force_on_cleat_n": wrench[:3].tolist(),
                            "moment_on_cleat_nmm": (1000 * wrench[3:]).tolist(),
                        }
                        mapping[:, 3:] *= 1000
                        pose, _, rank, _ = np.linalg.lstsq(
                            mapping, q[ports], rcond=None
                        )
                        require(rank == 6, "incomplete local interface fit")
                        fits[host] = {
                            "translation_mm": pose[:3].tolist(),
                            "rotation_rad": pose[3:].tolist(),
                            "projection_residual_mm": method.maximum(
                                mapping @ pose - q[ports]
                            ),
                        }
                    for pair_index, pair in enumerate(targets.reshape(-1, 2)):
                        r = retained[int(pair[0])]
                        if block not in (
                            r["ownership"]["first_body"],
                            r["ownership"]["second_body"],
                        ):
                            continue
                        axis = r["row_id"].rsplit("/", 1)[0]
                        vector = (
                            -D[pair, 6 * block_index : 6 * block_index + 3].T @ f[pair]
                        )
                        tie = next(
                            i
                            for i, row in enumerate(retained)
                            if row["row_id"] == axis + "/outer-seat-axial-tie"
                        )
                        bolts.append(
                            {
                                "axis_id": axis,
                                "lateral_n": float(np.linalg.norm(vector)),
                                "force_on_cleat_n": vector.tolist(),
                                "tension_n": float(f[tie]),
                                "relative_clearance_mm": float(
                                    gap_scale * gaps[pair_index]
                                ),
                                "slip_mm": float(np.linalg.norm(q[pair])),
                            }
                        )
                    rail, side = hosts
                    relative = (
                        np.array(fits[side]["translation_mm"])
                        - fits[rail]["translation_mm"]
                    )
                    rotation = (
                        np.array(fits[side]["rotation_rad"])
                        - fits[rail]["rotation_rad"]
                    )
                    corner_results.append(
                        {
                            "block": block,
                            "datum_mm": centers[block].tolist(),
                            "interface_wrenches": wrenches,
                            "local_interface_fits": fits,
                            "bolts": bolts,
                            "local_host_movement_mm": float(np.linalg.norm(relative)),
                            "local_host_rotation_degrees": float(
                                np.rad2deg(np.linalg.norm(rotation))
                            ),
                        }
                    )
                screw_pairs = np.array(screw_lateral).reshape(-1, 2)
                worst_shear = int(np.argmax(np.linalg.norm(f[screw_pairs], axis=1)))
                worst_axial = int(screw_axial[int(np.argmax(f[screw_axial]))])
                result = {
                    "case_id": case_id,
                    "gap_scale": gap_scale,
                    "status": "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING"
                    if certificate is not None
                    else "PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                    "audit": audit,
                    "fixed_force_clearance_certificate": certificate,
                    "corners": corner_results,
                    "peak_body_translation_mm": float(
                        np.linalg.norm(a.reshape(-1, 6)[:, :3], axis=1).max()
                    ),
                    "peak_hillman_lateral": {
                        "axis_id": retained[int(screw_pairs[worst_shear, 0])][
                            "row_id"
                        ].split("/")[0],
                        "force_n": float(np.linalg.norm(f[screw_pairs[worst_shear]])),
                    },
                    "peak_hillman_withdrawal": {
                        "axis_id": retained[worst_axial]["row_id"].split("/")[0],
                        "force_n": float(f[worst_axial]),
                    },
                    "zero_gap_difference_from_saved_force_n": method.maximum(
                        raw - saved[case_id + "_force_n"]
                    )
                    if gap_scale == 0
                    else None,
                }
                states.append(result)
                tag = "_gap" if gap_scale else "_zero"
                vectors.update(
                    {
                        case_id + tag + "_raw_force_n": raw,
                        case_id + tag + "_lumped_q_mm": q,
                        case_id + tag + "_rigid_coordinates": a,
                    }
                )
                print(
                    case_id,
                    gap_scale,
                    "corner shears",
                    [max(b["lateral_n"] for b in c["bolts"]) for c in corner_results],
                    "Hillman withdrawal",
                    result["peak_hillman_withdrawal"]["force_n"],
                    flush=True,
                )
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    output.mkdir()
    np.savez_compressed(output / "response.npz", **vectors)
    report = {
        "schema": "coupled_two_receiver_frame_clearance/v1"
        if all_two_receiver_clearances
        else "coupled_outer_corner_frame_clearance/v1"
        if bottom_corners
        else "coupled_top_and_service_frame_clearance/v1"
        if service_joints
        else "both_top_corner_corrected_frame_clearance/v1",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "response_sha256": sha(output / "response.npz"),
        "states": states,
        "modeled_mass_kg": baseline["modeled_mass_kg"],
        "dead_load_factor": baseline["dead_load_factor"],
        "panel_screw_stiffness_n_per_mm": {
            "lateral_components": k[screw_lateral].tolist(),
            "withdrawal": k[screw_axial].tolist(),
            "source_withdrawal": original_withdrawal.tolist(),
            "source_lateral_components": original_lateral.tolist(),
            "withdrawal_override_n_per_mm": panel_withdrawal_stiffness,
            "lateral_override_n_per_mm": panel_lateral_stiffness,
            "product_laws_measured": False,
        },
        "clearance_joint_hosts": block_hosts,
        "clearance_planes": [
            {
                "plane_id": retained[int(pair[0])]["row_id"],
                "relative_radial_gap_mm": float(gap),
            }
            for pair, gap in zip(targets.reshape(-1, 2), gaps, strict=True)
        ],
        "all_two_receiver_candidate_clearances": all_two_receiver_clearances,
        "bounded_nonunique_seating_reported": bounded_freeplay,
        "floor_footprints": floors,
        "limits": [
            "The listed clearance planes receive their declared relative radial gap; all other bolt planes remain at zero clearance. The four continuous knee bolts require a separate common-bolt clearance model.",
            "Hillman lateral and withdrawal stiffness use their listed conditional source values or explicit overrides. Neither is a measured product law or resistance.",
            "Other original stiffness/material/contact hypotheses and 25kg proportional accessory allowance are retained.",
            "Floor bearing and no-slip tangent masks may change during each independent static case; no physical floor acceptance is implied.",
            "Local interface fits report approximation residuals and are not total member/panel deflections.",
            "Bounded-seating states satisfy the original equilibrium and finite laws while retaining failed rank300/strict tangent stability flags; finite fixed-force seating bounds do not establish dynamic or complete-joint acceptance.",
        ],
        "reviewed_geometry_changed": False,
        "hardware_selected": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    (output / "comparison.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--service-joints",
        action="store_true",
        help="include both left outer service-cleat clearances",
    )
    parser.add_argument(
        "--bottom-corners",
        action="store_true",
        help="include both bottom outer-cleat clearances",
    )
    parser.add_argument(
        "--bounded-freeplay",
        action="store_true",
        help="report fixed-force bounded seating explicitly when the rank300 gate fails",
    )
    parser.add_argument(
        "--all-two-receiver-clearances",
        action="store_true",
        help="include saved bore gaps for all 88 candidate bolts having two receivers",
    )
    parser.add_argument(
        "--panel-withdrawal-stiffness",
        type=float,
        help="explicit positive withdrawal stiffness in N/mm for all 66 screws",
    )
    parser.add_argument(
        "--panel-lateral-stiffness",
        type=float,
        help="explicit positive lateral stiffness in N/mm for all 132 screw components",
    )
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(
            read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
            "shared analysis slot occupied",
        )
        run(
            args.output,
            args.service_joints,
            args.bottom_corners,
            args.panel_withdrawal_stiffness,
            args.panel_lateral_stiffness,
            args.all_two_receiver_clearances,
            args.bounded_freeplay,
        )
