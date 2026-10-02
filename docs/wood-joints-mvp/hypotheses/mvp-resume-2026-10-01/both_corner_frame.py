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


def run(output, service_joints=False, bottom_corners=False):
    import simple_frame as frame

    require(not output.exists(), "preserve the existing calculation")
    assessment = read(FRAME / "operator-assessment.json")
    baseline = read(FRAME / "frame-results.json")
    pins = {ROOT / name: digest for name, digest in assessment["source_sha256"].items()}
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
            and corners.intersection(
                (r["ownership"]["first_body"], r["ownership"]["second_body"])
            )
        ]
    )
    require(len(targets) == 8 * len(corners), "joint lateral inventory mismatch")
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
                f, q, a, audit = method.solve(
                    H,
                    D,
                    baseline["dead_load_factor"] * e[:, 2 * index]
                    + e[:, 2 * index + 1],
                    baseline["dead_load_factor"] * W[:, 2 * index]
                    + W[:, 2 * index + 1],
                    k,
                    uni,
                    normals,
                    tangents,
                    targets,
                    gap_scale * gaps,
                    seed,
                    circular_clearance,
                )
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
                    "status": "PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                    "audit": audit,
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
        "schema": "coupled_outer_corner_frame_clearance/v1"
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
        "clearance_joint_hosts": block_hosts,
        "floor_footprints": floors,
        "limits": [
            "Listed joints receive modeled relative clearance; all other bolted joints remain at zero clearance.",
            "Hillman lateral and withdrawal stiffness remain conditional 2689.679 N/mm per scalar, not measured product laws or resistance.",
            "Other original stiffness/material/contact hypotheses and 25kg proportional accessory allowance are retained.",
            "Floor bearing and no-slip tangent masks may change during each independent static case; no physical floor acceptance is implied.",
            "Local interface fits report approximation residuals and are not total member/panel deflections.",
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
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(
            read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
            "shared analysis slot occupied",
        )
        run(args.output, args.service_joints, args.bottom_corners)
