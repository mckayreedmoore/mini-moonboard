"""Bound NDS timber-group applicability using completed, same-state block responses.

This is source authentication and small wrench/footprint arithmetic only. It
imports no mechanics or CAD producer and assigns no oblique-group resistance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/block-group-resistance"
SOURCE = HERE.parents[1] / "upper-block-strength-2026-10-01/source-cache"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
RIGHT = HERE / "rawlocal/upper-right-block/attempt01/checks.json"
LEFT = HERE / "rawlocal/upper-left-block/attempt01/checks.json"
RAIL = HERE / "rawlocal/upper-right-rail-pair/attempt01/checks.json"
SIDE = HERE / "rawlocal/upper-right-side-pair/attempt01/checks.json"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
PROPOSAL = HERE.parent / "top-corner-correction/proposal.json"
CONTACT = HERE.parent / "top-corner-contact-geometry.json"
PINS = {
    RIGHT: "0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b",
    LEFT: "5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0",
    RAIL: "e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d",
    SIDE: "b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    PROPOSAL: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    CONTACT: "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    HERE
    / "operators-attempt02/model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    HERE
    / "frame-250-attempt02/comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE
    / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    SOURCE
    / "chapter11-2024-awc-20260911.pdf": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
    SOURCE
    / "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    SOURCE
    / "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
}
CHAPTER3_SHA = "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644"
PRIMARY = {
    "chapter3": {
        "url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf",
        "sha256": CHAPTER3_SHA,
        "printed_pages": [16, 24],
        "clauses": ["3.1.2", "3.1.3", "3.8.1", "3.8.2"],
    },
    "chapter11": {
        "url": "https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf",
        "sha256": PINS[SOURCE / "chapter11-2024-awc-20260911.pdf"],
        "printed_pages": [70, 74],
        "clauses": ["11.1.2", "11.1.3", "11.3.6.1-3"],
    },
    "chapter12": {
        "url": "https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf",
        "sha256": PINS[SOURCE / "chapter12-2024-awc-20260911.pdf"],
        "printed_pages": [97, 98, 99, 100],
        "clauses": ["12.5.1.2-3", "Table 12.5.1C note 2", "12.6.2", "12.6.3"],
    },
    "appendix": {
        "url": "https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf",
        "sha256": PINS[SOURCE / "appendix-2024-awc-20260911.pdf"],
        "printed_pages": [174, 175],
        "clauses": ["E.1", "E.2-1", "E.3-1", "E.3-2b", "E.3.3-4", "E.4-1", "E.4.1"],
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def shifted(wrench, old, new):
    value = np.array(wrench, dtype=float)
    require(value.shape == (6,) and np.isfinite(value).all(), "invalid wrench")
    value[3:] += np.cross(np.array(old) - new, value[:3])
    return value


def basis(descriptor):
    axes = np.array(
        [descriptor[k] for k in ("axis", "section_u", "section_v")], dtype=float
    )
    axes /= np.linalg.norm(axes, axis=1)[:, None]
    require(np.max(abs(axes @ axes.T - np.eye(3))) < 1e-8, "invalid grain frame")
    return axes


def in_grain(wrench, axes):
    return np.r_[axes @ wrench[:3], axes @ wrench[3:]].tolist()


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"source pin differs: {path}")


def bind_closure(pins, record):
    for relative, digest in record["source_sha256"].items():
        path = ROOT / relative
        require(
            path not in pins or pins[path] == digest, f"conflicting source pin: {path}"
        )
        pins[path] = digest


def host_support(state, spec, face, axes):
    """Enclose the existing model's full face, bore and washer footprints."""
    grain = axes[0]
    n = np.array(spec["bolt_axis_head_to_nut_xyz"])
    geometry = spec["geometry"]
    interval = [float(np.array(point) @ grain) for point in face["corners_mm"]]
    radial_projection = np.sqrt(max(0.0, 1 - float(n @ grain) ** 2))
    for bolt in state["bolts"]:
        point = np.array(bolt["interface_point_xyz_mm"])
        head = point - geometry["host_length_mm"] * n
        # The whole bore length/radius and full annulus enclose all sampled
        # contact, including zero-force parts; no point-only footprint claim.
        bore_radius = geometry["bore_mm"] / 2 * radial_projection
        for end in (head, point):
            interval.extend(
                [float(end @ grain) - bore_radius, float(end @ grain) + bore_radius]
            )
        seat_radius = geometry["washer_OD_min_mm"] / 2 * radial_projection
        interval.extend(
            [float(head @ grain) - seat_radius, float(head @ grain) + seat_radius]
        )
    return [min(interval), max(interval)]


def host_cuts(saved, support, source, derived, old_datum, axes):
    """Update exterior saved cut equilibrium, keeping all remote actions frozen.

    An exterior cut admits the whole interface or none. It therefore depends
    on its full wrench, not on the redistributed individual allocations.
    A cut intersecting the interface is refused instead of inventing shares.
    """
    output = []
    for cut in saved["cuts"]:
        datum = np.array(cut["datum_mm"])
        station = float(datum @ axes[0])
        side = None
        # 1e-6 mm only accommodates the pinned stock-frame rounding at a
        # terminal/touching face. It is not a moved cut or clearance allowance.
        if support[0] >= station - 1e-6:
            side = "positive"
        elif support[1] <= station + 1e-6:
            side = "negative"
        delta = shifted(derived - source, old_datum, datum)
        halves = {}
        for half in ("positive", "negative"):
            field = cut[f"internal_on_{half}_half"]
            original = np.r_[field["force_xyz_n"], field["moment_xyz_nmm"]]
            revised = (
                None if side is None else original - (delta if half == side else 0)
            )
            halves[half] = {
                "saved_current_complete_host_internal_wrench_n_nmm": original.tolist(),
                "compatible_complete_host_internal_wrench_n_nmm": None
                if revised is None
                else revised.tolist(),
                "compatible_complete_host_internal_grain_u_v_n_nmm": None
                if revised is None
                else in_grain(revised, axes),
            }
        output.append(
            {
                "station_mm": cut["station_mm"],
                "datum_xyz_mm": datum.tolist(),
                "interface_support_global_grain_interval_mm": support,
                "interface_side_of_cut": side,
                "interface_wrench_change_at_cut_n_nmm": delta.tolist(),
                "halves": halves,
                "other_contact_footprints_crossing_cut": cut[
                    "other_contact_footprints_crossing_cut"
                ],
                "exterior_transfer_demand_reusable": side is not None,
                "interior_cut_or_stress_distribution_qualified": False,
            }
        )
    return output


def group_scope(block, host, state, spec, datum, frames, paths):
    """Record simultaneous actions and reject an unsupported Appendix E use."""
    grain = frames[block][0]
    bolts = state["bolts"]
    wrench = np.sum([b["wrench_on_host_at_face_datum_n_nmm"] for b in bolts], axis=0)
    wrench += state["face_wrench_on_host_at_face_datum_n_nmm"]
    derived = shifted(wrench, spec["face_datum_xyz_mm"], datum)
    source = shifted(
        state["source_connector_wrench_on_host_n_nmm"], spec["face_datum_xyz_mm"], datum
    )
    # These are energy-dual rigid-cleat reactions. Do not rename them as
    # recovered timber tractions or silently replace the normal-seat moments.
    cleat = -derived
    bolt_witnesses = []
    for bolt in bolts:
        host_wrench = shifted(
            bolt["wrench_on_host_at_face_datum_n_nmm"], spec["face_datum_xyz_mm"], datum
        )
        lateral = -np.array(bolt["bore_force_on_host_xyz_n"])
        parallel = float(lateral @ grain)
        bolt_witnesses.append(
            {
                "axis_id": bolt["axis_id"],
                "bore_resultant_parallel_on_cleat_n": parallel,
                "bore_resultant_perpendicular_on_cleat_n": float(
                    np.linalg.norm(lateral - parallel * grain)
                ),
                "compatible_T_n": bolt["compatible_T_n"],
                "rigid_cleat_dual_bolt_wrench_at_common_datum_n_nmm": (
                    -host_wrench
                ).tolist(),
                "saved_end_moments_on_beam_xyz_nmm": [
                    e["moment_on_beam_xyz_nmm"] for e in bolt["end_contacts"]
                ],
            }
        )
    local_paths = [
        p
        for p in paths
        if p["block"] == block and p["axis_id"] in {b["axis_id"] for b in bolts}
    ]
    require(len(local_paths) == 4, "two signed finished paths per bolt required")
    # Finished interval boundaries identify the existing grain rows. They
    # do not identify an E.4 group-net area for the orthogonal four-bolt array.
    adjacent = any(p["interval_boundary"] != "grain_end" for p in local_paths)
    row_axes = (
        [[b["axis_id"] for b in bolts]] if adjacent else [[b["axis_id"]] for b in bolts]
    )
    rows = [
        {
            "axis_ids": ids,
            "fasteners_in_grain_row": len(ids),
            "minimum_finished_one_plane_area_by_sign_mm2": {
                str(sign): min(
                    p["minimum_finished_one_plane_area_mm2"]
                    for p in local_paths
                    if p["axis_id"] in ids and p["grain_direction_sign"] == sign
                )
                for sign in (-1, 1)
            },
            "complete_row_or_group_resistance_assigned": False,
        }
        for ids in row_axes
    ]
    perpendicular_interface_force = float(
        np.linalg.norm(cleat[:3] - float(cleat[:3] @ grain) * grain)
    )
    require(
        perpendicular_interface_force > 0.002,
        "pinned current oblique-interface applicability finding no longer holds",
    )
    delta = derived - source
    require(
        np.max(abs(delta[:3])) < 0.002 and np.max(abs(delta[3:])) < 0.6,
        "completed interface wrench differs beyond existing block tolerances",
    )
    return {
        "block": block,
        "host": host,
        "case_id": state["case_id"],
        "common_datum_xyz_mm": datum.tolist(),
        "source_interface_wrench_on_host_n_nmm": source.tolist(),
        "compatible_interface_wrench_on_host_n_nmm": derived.tolist(),
        "compatible_interface_host_grain_u_v_n_nmm": in_grain(derived, frames[host]),
        "rigid_cleat_dual_interface_wrench_n_nmm": cleat.tolist(),
        "rigid_cleat_dual_interface_grain_u_v_n_nmm": in_grain(cleat, frames[block]),
        "face_wrench_on_host_at_common_datum_n_nmm": shifted(
            state["face_wrench_on_host_at_face_datum_n_nmm"],
            spec["face_datum_xyz_mm"],
            datum,
        ).tolist(),
        "source_vs_compatible_interface_wrench_n_nmm": delta.tolist(),
        "bolt_witnesses": bolt_witnesses,
        "parallel_bore_component_signed_sum_n": sum(
            b["bore_resultant_parallel_on_cleat_n"] for b in bolt_witnesses
        ),
        "parallel_bore_component_positive_sum_n": sum(
            max(0.0, b["bore_resultant_parallel_on_cleat_n"]) for b in bolt_witnesses
        ),
        "parallel_bore_component_negative_sum_n": sum(
            min(0.0, b["bore_resultant_parallel_on_cleat_n"]) for b in bolt_witnesses
        ),
        "complete_interface_perpendicular_to_cleat_grain_force_n": perpendicular_interface_force,
        "complete_interface_moment_norm_at_common_datum_nmm": float(
            np.linalg.norm(cleat[3:])
        ),
        "finished_path_geometry": local_paths,
        "finished_grain_rows_for_this_bolt_family": rows,
        "appendix_E_whole_interface_resistance_applicable": False,
        "appendix_E_whole_interface_resistance_n": None,
        "appendix_E_limitation": "Oblique bolt actions, compression-only normal seats/faces and full interface couples require a local transfer model beyond E.1's parallel-load procedure. Parallel projection alone does not establish that procedure's applicability.",
        "Cg_limitation": "11.3.6.2 defines equal-diameter rows aligned with load. The saved conditional multiplier is not a four-bolt wood group or splitting capacity; no new Cg is imposed on the completed allocations.",
        "NDS_splitting_design_resistance_n": None,
        "tension_perpendicular_stress_or_failure_demonstrated": False,
        "normal_axial_channel": "The existing through shaft routes its own axial load into inward washer bearing on both receivers. This does not qualify a bridge for bore-induced splits or the other group's stresses.",
    }


def run(output, chapter3):
    require(
        output.is_relative_to(RAW) and not output.exists(),
        "use a fresh attempt inside owned rawlocal/block-group-resistance",
    )
    pins = dict(PINS)
    pins[chapter3] = CHAPTER3_SHA
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    authenticate(pins)
    right, left, rail, side = (read(path) for path in (RIGHT, LEFT, RAIL, SIDE))
    for record in (right, left, rail, side):
        require(
            [s["case_id"] for s in record["states"]] == list(CASES),
            "six-case census differs",
        )
        require(
            not record["complete_joint_acceptance"] and not record["physical_release"],
            "source claims qualification",
        )
        bind_closure(pins, record)
    component, inputs, proposal, contacts = (
        read(path) for path in (COMPONENT, INPUTS, PROPOSAL, CONTACT)
    )
    descriptors = {
        m["member_id"]: m["reduced_geometry_descriptor"] for m in inputs["members"]
    }
    frames = {
        name: basis(descriptors[name])
        for name in (
            "top_outer_right_cleat",
            "top_outer_left_cleat",
            "base_rail_top",
            "base_side_right",
            "base_side_left",
        )
    }
    geometry = []
    for prop in proposal["proposals"]:
        block = prop["block"]
        require(
            prop["proposed_section_X_T_mm"] == [88.9, 139.7],
            "current cleat section differs",
        )
        step = HERE.parent / "top-corner-correction" / (block + ".step")
        pins[step] = proposal["proposal_step_sha256"][str(step.relative_to(ROOT))]
        geometry.append(
            {
                "block": block,
                "grain_frame_rows_xyz": frames[block].tolist(),
                "current_section_X_T_mm": prop["proposed_section_X_T_mm"],
                "grain_length_mm": prop["grain_length_mm"],
                "current_finished_step": str(step.relative_to(ROOT)),
                "current_finished_step_sha256": pins[step],
                "descriptor_scope": "Pinned model-inputs supply grain axes only; their old 88.9 mm depth and original STEP are not current cleat section evidence.",
                "net_section_note": "3.1.2.2's staggered parallel-array rule requires actual applicable rows. The side stations lie between the rail stations, 16.5 mm from each. Separate old bore sections, gross area, or summed tangent paths are not a complete net-section check for the orthogonal array.",
            }
        )
    authenticate(pins)
    groups, blocks = [], []
    for case_index, case in enumerate(CASES):
        for block, completed in (
            ("top_outer_right_cleat", right),
            ("top_outer_left_cleat", left),
        ):
            state = completed["states"][case_index]
            if block == "top_outer_right_cleat":
                datum = np.array(right["common_datum_xyz_mm"])
                hosts = [
                    (g["model"]["host"], g["states"][case_index], g["model"])
                    for g in (rail, side)
                ]
                weight = state["applied_weight_wrench_n_nmm"]
                balance = state["compatible_balance_residual_n_nmm"]
            else:
                datum = np.array(left["model"]["common_cleat_datum_xyz_mm"])
                hosts = []
                for host, host_state in state["hosts"].items():
                    spec = left["model"]["host_groups"][host]
                    hosts.append(
                        (
                            host,
                            host_state,
                            {
                                "geometry": spec["receiver_geometry"],
                                "face_datum_xyz_mm": spec[
                                    "host_interface_datum_xyz_mm"
                                ],
                                "bolt_axis_head_to_nut_xyz": spec[
                                    "bolt_axis_head_to_nut_xyz"
                                ],
                            },
                        )
                    )
                weight = state["whole_cleat"][
                    "current_W_cleat_applied_wrench_at_common_datum_n_nmm"
                ]
                balance = state["whole_cleat"][
                    "derived_whole_cleat_balance_residual_n_nmm"
                ]
            block_groups = []
            face_record = next(c for c in contacts["cleats"] if c["block"] == block)
            for host, host_state, spec in hosts:
                require(
                    len(host_state["bolts"]) == 2
                    and len(host_state["face_cells"]) == 16,
                    "host census differs",
                )
                group = group_scope(
                    block,
                    host,
                    host_state,
                    spec,
                    datum,
                    frames,
                    component["finished_paths"],
                )
                face = next(f for f in face_record["faces"] if f["host"] == host)
                support = host_support(host_state, spec, face, frames[host])
                saved = next(
                    s
                    for s in component["host_splitting"]
                    if (s["case_id"], s["block"], s["host"]) == (case, block, host)
                )
                group["exterior_complete_host_cut_replay"] = host_cuts(
                    saved,
                    support,
                    np.array(group["source_interface_wrench_on_host_n_nmm"]),
                    np.array(group["compatible_interface_wrench_on_host_n_nmm"]),
                    datum,
                    frames[host],
                )
                groups.append(group)
                block_groups.append(group)
            combined = (
                np.sum(
                    [
                        g["rigid_cleat_dual_interface_wrench_n_nmm"]
                        for g in block_groups
                    ],
                    axis=0,
                )
                + weight
            )
            require(
                np.max(abs(combined[:3])) < 0.002 and np.max(abs(combined[3:])) < 0.6,
                "same-state block balance differs",
            )
            require(
                np.max(abs(combined - balance)) < 1e-6,
                "completed block balance replay differs",
            )
            blocks.append(
                {
                    "block": block,
                    "case_id": case,
                    "common_datum_xyz_mm": datum.tolist(),
                    "current_W_wrench_n_nmm_included_once": weight,
                    "completed_rigid_block_balance_residual_n_nmm": balance,
                    "both_host_wrenches_retained": True,
                    "whole_body_net_wrench_is_local_stress_or_group_resistance": False,
                }
            )
    require(
        len(groups) == 24 and len(blocks) == 12, "two-block six-case census differs"
    )
    cuts = [c for g in groups for c in g["exterior_complete_host_cut_replay"]]
    reusable = [c for c in cuts if c["exterior_transfer_demand_reusable"]]
    summary = {
        "block_states": len(blocks),
        "host_states": len(groups),
        "complete_host_cuts": len(cuts),
        "reusable_exterior_complete_host_cuts": len(reusable),
        "cuts_refused_due_to_interface_crossing": len(cuts) - len(reusable),
        "maximum_interface_force_change_n": max(
            max(abs(np.array(g["source_vs_compatible_interface_wrench_n_nmm"])[:3]))
            for g in groups
        ),
        "maximum_interface_moment_change_at_common_datum_nmm": max(
            max(abs(np.array(g["source_vs_compatible_interface_wrench_n_nmm"])[3:]))
            for g in groups
        ),
        "whole_interface_Appendix_E_resistances_assigned": 0,
        "NDS_splitting_resistances_assigned": 0,
    }
    result = {
        "schema": "current_upper_block_timber_group_applicability/v1",
        "summary": summary,
        "primary_sources": PRIMARY,
        "current_cleat_geometry": geometry,
        "block_states": blocks,
        "host_states": groups,
        "completed_component_evidence": {
            "right_checks_sha256": PINS[RIGHT],
            "right_existing_peak_indices": {
                k: row[k] for k, row in right["peak_witnesses"].items()
            },
            "left_checks_sha256": PINS[LEFT],
            "left_component_replay": "Parent-owned upper-left-block-components.py; no replay or transferred right acceptance here.",
        },
        "remaining_timber_requirement": "Actual finished cleat net-section/ligament transfer and local oblique-group stresses under both host wrenches, normal contacts, bore distributions and seat moments; an applicable resistance or justified mechanical transfer for any induced perpendicular tension. Exterior host cut resultants alone do not close these checks.",
        "limits": [
            "Exterior complete-host cuts retain frozen remote actions and body loads. Only the completed local interface change is applied. Interior cuts are not inferred from whole-interface balance.",
            "No projected-force Appendix E ratio, summed independent peaks, automatic oblique Cg, Ft-perpendicular, characteristic-to-design conversion or new capacity is assigned.",
            "Source grain is reused. R/T material assignment remains unresolved; geometric section axes do not select a radial/tangential constitutive law.",
            "Inward axial seat forces supply a topology for the shaft's own normal transfer, not reinforcement qualification for every crack path.",
            "The current rigid-cleat model supplies wrenches, not elastic wood stresses or compatible force shares in disconnected net-section regions.",
            "No mechanics, native, CAD or frame solve, component replay, geometry/hardware change, authority update or physical release occurs.",
        ],
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): h
            for p, h in sorted(pins.items())
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    authenticate(pins)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
        },
    )
    print(
        json.dumps({"checks_sha256": sha(output / "checks.json"), "summary": summary})
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--nds-chapter3", type=Path, default=Path("/tmp/nds2024-ch3.pdf")
    )
    args = parser.parse_args()
    run(args.output.resolve(), args.nds_chapter3.resolve())
