"""Reuse saved frame forces to screen the 66 purchased panel screw stations.

Generic wood-screw references and optimistic panel-only redistribution are
decision aids, not Hillman ratings or a new compatible frame response.
"""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FRAME = HERE.parent / "corner-frame-attempt01"
DEFAULT = HERE.parent / "all-outer-corner-frame-attempt01"
DEFAULT_SHA = "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3"
N_PER_LBF = 4.4482216152605
CASES = {"a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"}
AXIAL = "non_qualifying_parametric_screw_withdrawal"
LATERAL = "panel_screw_lateral_plane"
AUTHORITY = {
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    "docs/wood-joints-mvp/criteria.json": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
    "docs/wood-joints-mvp/current-criteria-coverage.json": "c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c",
    "docs/wood-joints-mvp/authority-integrity.json": "34eab2d747af074cfd21a6247be5136e03b29d8bc7649c0a7e5bd39abdf99399",
}
NDS = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache"
)
NDS_PINS = {
    NDS
    / "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    NDS
    / "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
    Path(
        "/tmp/upper-panel-awc-head-pull-through-paper.pdf"
    ): "b0f7b80cfa891b4babea733894ee856b3da944abb8ce9a982477cb90c4887e2f",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def withdrawal_reference(g, penetration_mm):
    """NDS 2024 12.2.2 generic cut/rolled side-grain screw reference, N."""
    return 2850 * g**2 * 0.190 * penetration_mm / 25.4 * N_PER_LBF


def head_reference(g, diameter_mm, net_thickness_mm):
    """NDS 12.2.5 circular-head reference for declared geometry, N."""
    diameter, thickness = diameter_mm / 25.4, net_thickness_mm / 25.4
    return (
        (
            690 * np.pi * diameter * thickness
            if thickness <= 2.5 * diameter
            else 1725 * np.pi * diameter**2
        )
        * g**2
        * N_PER_LBF
    )


def redistribution(mapping, force, tie_indices=None):
    """Minimize the largest tie force while preserving this normal wrench.

    ponytail: lateral forces stay fixed. Contact can change only when its
    ports are passed. No elastic compatibility or receiver balance is imposed.
    """
    matrix = mapping.T
    target = matrix @ force
    count = len(force)
    ties = np.arange(count) if tie_indices is None else np.array(tie_indices)
    require(np.linalg.matrix_rank(matrix) == 3, "unexpected panel axial rank")
    limits = np.zeros((len(ties), count + 1))
    limits[np.arange(len(ties)), ties] = 1
    limits[:, -1] = -1
    result = linprog(
        np.r_[np.zeros(count), 1.0],
        A_ub=limits,
        b_ub=np.zeros(len(ties)),
        A_eq=np.c_[matrix, np.zeros(6)],
        b_eq=target,
        bounds=[(0, None)] * (count + 1),
        method="highs",
    )
    require(result.success, "panel allocation LP failed: " + result.message)
    allocated, peak = result.x[:-1], float(result.x[-1])
    residual = matrix @ allocated - target
    dual = float(target @ result.eqlin.marginals)
    require(
        np.max(np.abs(residual[:3])) < 1e-6
        and 1000 * np.max(np.abs(residual[3:])) < 1e-3
        and allocated.min() >= -1e-7
        and allocated[ties].max() <= peak + 1e-7
        and abs(peak - dual) < 1e-6,
        "panel allocation primal/dual check failed",
    )
    return {
        "minimum_largest_tie_n": peak,
        "allocated_ties_n": allocated[ties].tolist(),
        "allocated_contact_forces_n": allocated[
            np.setdiff1d(np.arange(count), ties)
        ].tolist(),
        "signed_force_on_panel_n": (-target[:3]).tolist(),
        "signed_moment_on_panel_nmm": (-1000 * target[3:]).tolist(),
        "force_residual_n": float(np.max(np.abs(residual[:3]))),
        "moment_residual_nmm": float(1000 * np.max(np.abs(residual[3:]))),
        "dual_objective_n": dual,
    }


def run(source, output):
    require(not output.exists(), "preserve existing output")
    comparison = read(source / "comparison.json")
    require(
        comparison["schema"]
        in {
            "coupled_top_and_service_frame_clearance/v1",
            "coupled_outer_corner_frame_clearance/v1",
        },
        "requires a coupled outer-corner/service frame packet",
    )
    if source.resolve() == DEFAULT.resolve():
        require(
            sha(source / "comparison.json") == DEFAULT_SHA, "default source changed"
        )
    pins = {source / "comparison.json": sha(source / "comparison.json")}
    pins[source / "response.npz"] = comparison["response_sha256"]
    pins[source / "producer.py.snapshot"] = comparison["producer_sha256"]
    assessment = read(FRAME / "operator-assessment.json")
    require(
        assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS", "operator STOP"
    )
    pins[FRAME / "operator-assessment.json"] = sha(FRAME / "operator-assessment.json")
    for name, digest in assessment["output_sha256"].items():
        pins[FRAME / name] = digest
        require(
            comparison["source_sha256"][str((FRAME / name).relative_to(ROOT))]
            == digest,
            "mixed frame output: " + name,
        )
    pins[FRAME / "frame-results.json"] = sha(FRAME / "frame-results.json")
    require(
        all(
            comparison["source_sha256"][str(p.relative_to(ROOT))] == pins[p]
            for p in (FRAME / "frame-results.json", FRAME / "operator-assessment.json")
        ),
        "mixed frame metadata",
    )
    for path, digest in AUTHORITY.items():
        pins[ROOT / path] = digest
    inventory_path = (
        HERE.parent.parent
        / "current-panel-receiver-transfer-2026-10-01/receiver-transfer.json"
    )
    pins[inventory_path] = (
        "0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534"
    )
    pins.update(NDS_PINS)
    pins[ROOT / "docs/current-panel-screw-purchase.md"] = sha(
        ROOT / "docs/current-panel-screw-purchase.md"
    )
    pins[Path(__file__)] = sha(Path(__file__))
    for path, digest in pins.items():
        require(sha(path) == digest, "changed input: " + str(path))
    states = comparison["states"]
    require(
        len(states) == 12
        and {(s["case_id"], s["gap_scale"]) for s in states}
        == {(c, g) for c in CASES for g in (0.0, 1.0)}
        and all(s["status"] == "PASS_CONDITIONAL_COUPLED_FRAME_LAWS" for s in states),
        "incomplete source census",
    )
    model, rows = read(FRAME / "model.json"), read(FRAME / "row-identities.json")
    baseline = read(FRAME / "frame-results.json")
    inventory = {r["axis_id"]: r for r in read(inventory_path)["inventory"]["axes"]}
    axes, lateral = {}, defaultdict(list)
    retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    positions = {r["row"]: i for i, r in enumerate(retained)}
    for r in rows:
        axis = r["row_id"].split("/")[0]
        if r["ownership"]["role"] == AXIAL:
            require(axis not in axes, "duplicate axial station")
            axes[axis] = r
        elif r["ownership"]["role"] == LATERAL:
            lateral[axis].append(r)
    require(
        set(axes) == set(lateral) == set(inventory) and len(axes) == 66,
        "66-axis census changed",
    )
    stiffness = {r["row"]: r["law"]["stiffness_N_per_mm"] for r in retained}
    source_stiffness = comparison.get("panel_screw_stiffness_n_per_mm")
    if source_stiffness is not None:
        axial_rows = [r for r in retained if r["ownership"]["role"] == AXIAL]
        lateral_rows = [r for r in retained if r["ownership"]["role"] == LATERAL]
        axial_k = np.asarray(source_stiffness["withdrawal"], dtype=float)
        require(
            axial_k.shape == (66,)
            and np.isfinite(axial_k).all()
            and (axial_k > 0).all()
            and source_stiffness["product_laws_measured"] is False
            and np.array_equal(
                source_stiffness["source_withdrawal"],
                [stiffness[r["row"]] for r in axial_rows],
            )
            and np.array_equal(
                source_stiffness["lateral_components"],
                [stiffness[r["row"]] for r in lateral_rows],
            ),
            "unsupported stiffness metadata or changed lateral law",
        )
        stiffness.update(
            {r["row"]: k for r, k in zip(axial_rows, axial_k, strict=True)}
        )
    centers = {
        name: np.mean(
            [model["physical_node_coordinates_mm"][str(n)] for n in nodes], axis=0
        )
        for name, nodes in model["body_nodes"].items()
    }
    records, allocations, relaxed_allocations, balance_checks = [], [], [], []
    with (
        np.load(FRAME / "operators.npz", allow_pickle=False) as operators,
        np.load(source / "response.npz", allow_pickle=False) as saved,
    ):
        D, W, H, e = (operators[name] for name in ("D", "W", "H", "e"))
        for state in states:
            case, gap = state["case_id"], state["gap_scale"]
            tag = case + ("_gap" if gap else "_zero")
            force, q = saved[tag + "_raw_force_n"], saved[tag + "_lumped_q_mm"]
            rigid = saved[tag + "_rigid_coordinates"]
            require(
                force.shape == (len(rows),)
                and rigid.shape == (6 * len(model["body_names"]),)
                and np.isfinite(force).all()
                and np.isfinite(rigid).all()
                and np.isfinite(q).all(),
                "invalid force vector",
            )
            index = next(
                i for i, c in enumerate(baseline["cases"]) if c["case_id"] == case
            )
            load = (
                comparison["dead_load_factor"] * W[:, 2 * index] + W[:, 2 * index + 1]
            )
            residual = (D.T @ force - load).reshape(-1, 6)
            relative = (
                D @ rigid
                + comparison["dead_load_factor"] * e[:, 2 * index]
                + e[:, 2 * index + 1]
                - H @ force
            )
            compatibility_error = float(
                np.max(
                    np.abs(relative[[r["row"] for r in retained]] - q[: len(retained)])
                )
            )
            require(
                np.max(np.abs(residual[:, :3])) < 1e-5
                and 1000 * np.max(np.abs(residual[:, 3:])) < 0.01
                and compatibility_error < 1e-6,
                "saved body balance or returned motion differs",
            )
            balance_checks.append(
                {
                    "case_id": case,
                    "gap_scale": gap,
                    "force_residual_n": float(np.max(np.abs(residual[:, :3]))),
                    "moment_residual_nmm": float(
                        1000 * np.max(np.abs(residual[:, 3:]))
                    ),
                    "returned_motion_compatibility_residual_mm": compatibility_error,
                }
            )
            for axis, axial in axes.items():
                station = inventory[axis]
                panel = station["panel_member"]
                receiver = station["receiver_member"]
                group = [*lateral[axis], axial]
                require(
                    len(group) == 3 and len(lateral[axis]) == 2, "missing screw scalar"
                )
                require(
                    all(
                        {r["ownership"]["first_body"], r["ownership"]["second_body"]}
                        == {panel, receiver}
                        for r in group
                    ),
                    "receiver join mismatch",
                )
                require(
                    all(
                        np.linalg.norm(
                            np.array(r["ownership"]["point_mm"])
                            - axial["ownership"]["point_mm"]
                        )
                        < 1e-6
                        for r in group
                    ),
                    "screw datum mismatch",
                )
                raw_ids = [r["row"] for r in group]
                block = model["body_names"].index(panel) * 6
                direction = D[raw_ids, block : block + 3]
                require(
                    np.max(np.abs(direction @ direction.T - np.eye(3))) < 1e-10,
                    "screw basis is not orthonormal",
                )
                signed = -direction.T @ force[raw_ids]
                tension = float(force[axial["row"]])
                shear = float(np.linalg.norm(force[raw_ids[:2]]))
                expected = [
                    stiffness[r["row"]]
                    * (
                        max(0, q[positions[r["row"]]])
                        if r is axial
                        else q[positions[r["row"]]]
                    )
                    for r in group
                ]
                require(
                    tension >= -1e-6
                    and np.max(np.abs(force[raw_ids] - expected)) < 1e-5,
                    "saved screw law differs",
                )
                point = np.asarray(axial["ownership"]["point_mm"])
                poses = {}
                for body in (panel, receiver):
                    offset = model["body_names"].index(body) * 6
                    rotation = rigid[offset + 3 : offset + 6] / 1000
                    translation = rigid[offset : offset + 3] + np.cross(
                        rotation, point - centers[body]
                    )
                    require(
                        np.max(
                            np.abs(
                                D[raw_ids, offset + 3 : offset + 6]
                                - np.cross(
                                    point - centers[body],
                                    D[raw_ids, offset : offset + 3],
                                )
                                / 1000
                            )
                        )
                        < 1e-8,
                        "common datum and rigid operator disagree",
                    )
                    poses[body] = (translation, rotation)
                total_relative = direction.T @ q[[positions[n] for n in raw_ids]]
                rigid_relative = poses[panel][0] - poses[receiver][0]
                resultant = float(np.hypot(tension, shear))
                axial_reference = withdrawal_reference(0.50, 45.24375)
                withdrawal_term = (
                    tension**2 / (resultant * axial_reference) if resultant else 0.0
                )
                records.append(
                    {
                        "case_id": case,
                        "gap_scale": gap,
                        "axis_id": axis,
                        "panel": panel,
                        "receiver": receiver,
                        "withdrawal_n": tension,
                        "lateral_1_signed_n": float(force[raw_ids[0]]),
                        "lateral_2_signed_n": float(force[raw_ids[1]]),
                        "lateral_resultant_n": shear,
                        "force_on_panel_x_n": float(signed[0]),
                        "force_on_panel_y_n": float(signed[1]),
                        "force_on_panel_z_n": float(signed[2]),
                        "withdrawal_stiffness_hypothesis_n_per_mm": float(
                            stiffness[axial["row"]]
                        ),
                        "screw_relative_opening_mm": max(
                            0.0, float(q[positions[axial["row"]]])
                        ),
                        "screw_relative_translation_mm": float(
                            np.linalg.norm(total_relative)
                        ),
                        "common_datum_x_mm": float(point[0]),
                        "common_datum_y_mm": float(point[1]),
                        "common_datum_z_mm": float(point[2]),
                        **{
                            f"{label}_rigid_motion_{component}_mm": float(value)
                            for body, label in (
                                (panel, "panel"),
                                (receiver, "receiver"),
                            )
                            for component, value in zip(
                                "xyz", poses[body][0], strict=True
                            )
                        },
                        "relative_rigid_translation_mm": float(
                            np.linalg.norm(rigid_relative)
                        ),
                        "relative_elastic_translation_mm": float(
                            np.linalg.norm(total_relative - rigid_relative)
                        ),
                        "relative_rigid_rotation_degrees": float(
                            np.rad2deg(
                                np.linalg.norm(poses[panel][1] - poses[receiver][1])
                            )
                        ),
                        "withdrawal_reference_ratio_G050_45mm": tension
                        / axial_reference,
                        "head_reference_ratio_G050_standard_head_reduced_net": tension
                        / head_reference(0.50, 0.363 * 25.4, 18.25625 - 1.0),
                        "NDS12_4_withdrawal_term_G050_45mm": withdrawal_term,
                        "NDS12_4_required_lateral_reference_n_G050_45mm": (
                            shear**2 / (resultant * (1 - withdrawal_term))
                            if resultant and withdrawal_term < 1
                            else (0.0 if not resultant else None)
                        ),
                    }
                )
            for panel in ("main_upper_left", "main_upper_right"):
                panel_axes = [a for a in axes if inventory[a]["panel_member"] == panel]
                ids = [axes[a]["row"] for a in panel_axes]
                require(len(ids) == 12, "upper panel screw census changed")
                block = model["body_names"].index(panel) * 6
                allocations.append(
                    {
                        "case_id": case,
                        "gap_scale": gap,
                        "panel": panel,
                        "axis_ids": panel_axes,
                        "saved_total_withdrawal_n": float(force[ids].sum()),
                        "saved_largest_withdrawal_n": float(force[ids].max()),
                        **redistribution(D[ids, block : block + 6], force[ids]),
                    }
                )
                normal_ids = [
                    r["row"]
                    for r in rows
                    if r["ownership"]["role"] in {AXIAL, "timber_or_panel_contact"}
                    and panel
                    in (r["ownership"]["first_body"], r["ownership"]["second_body"])
                    and np.linalg.norm(
                        np.cross(
                            D[ids[0], block : block + 3], D[r["row"], block : block + 3]
                        )
                    )
                    < 1e-8
                ]
                tie_indices = [
                    i
                    for i, n in enumerate(normal_ids)
                    if rows[n]["ownership"]["role"] == AXIAL
                ]
                require(
                    len(tie_indices) == 12
                    and all(
                        rows[n]["family"] == "unilateral_springa" for n in normal_ids
                    ),
                    "invalid normal allocation inventory",
                )
                require(
                    all(
                        np.dot(D[n, block : block + 3], D[ids[0], block : block + 3])
                        < -1 + 1e-8
                        for n in normal_ids
                        if rows[n]["ownership"]["role"] != AXIAL
                    ),
                    "face contact and tie directions are not opposed",
                )
                relaxed_allocations.append(
                    {
                        "case_id": case,
                        "gap_scale": gap,
                        "panel": panel,
                        "axis_ids": [
                            rows[normal_ids[i]]["row_id"].split("/")[0]
                            for i in tie_indices
                        ],
                        "contact_row_ids": [
                            rows[n]["row_id"]
                            for n in normal_ids
                            if rows[n]["ownership"]["role"] != AXIAL
                        ],
                        **redistribution(
                            D[normal_ids, block : block + 6],
                            force[normal_ids],
                            tie_indices,
                        ),
                    }
                )
    worst = max(records, key=lambda r: r["withdrawal_n"])
    nominal_worst = max(
        (r for r in records if r["gap_scale"] == 1), key=lambda r: r["withdrawal_n"]
    )
    sensitivity = [
        {
            "timber_G_hypothesis": g,
            "effective_thread_penetration_mm_hypothesis": length,
            "unadjusted_generic_withdrawal_n": withdrawal_reference(g, length),
            "nominal_gap_peak_ratio": nominal_worst["withdrawal_n"]
            / withdrawal_reference(g, length),
            "zero_or_gap_peak_ratio": worst["withdrawal_n"]
            / withdrawal_reference(g, length),
            "same_state_nominal_peak_NDS12_4_withdrawal_term_as_lateral_allowance_tends_to_infinity": nominal_worst[
                "withdrawal_n"
            ]
            ** 2
            / (
                np.hypot(
                    nominal_worst["withdrawal_n"], nominal_worst["lateral_resultant_n"]
                )
                * withdrawal_reference(g, length)
            ),
        }
        for g in (0.45, 0.50, 0.55)
        for length in (30.0, 38.1, 63.5 * 2 / 3, 45.24375)
    ]
    allocation_peak = max(
        a["minimum_largest_tie_n"] for a in allocations if a["gap_scale"] == 1
    )
    head_demands = [
        {
            "hypothetical_punch_diameter_mm": diameter,
            "hypothetical_net_plywood_thickness_mm": thickness,
            "hypothetical_cylindrical_punch_area_mm2": float(
                np.pi * diameter * thickness
            ),
            "saved_nominal_gap_peak_mean_punch_shear_mpa": nominal_worst["withdrawal_n"]
            / (np.pi * diameter * thickness),
            "optimistic_upper_panel_allocation_peak_mean_punch_shear_mpa": allocation_peak
            / (np.pi * diameter * thickness),
        }
        for diameter in (7.5, 0.363 * 25.4)
        for thickness in (14.0, 18.25625)
    ]
    head_sensitivity = [
        {
            "plywood_G_hypothesis": g,
            "circular_head_diameter_mm_hypothesis": diameter,
            "net_plywood_thickness_mm_hypothesis": thickness,
            "unadjusted_generic_head_reference_n": head_reference(
                g, diameter, thickness
            ),
            "saved_nominal_gap_peak_ratio": nominal_worst["withdrawal_n"]
            / head_reference(g, diameter, thickness),
        }
        for g in (0.42, 0.50)
        for diameter in (7.5, 0.363 * 25.4)
        for thickness in (14.0, 18.25625 - 3.0 / 3, 18.25625)
    ]
    groups = defaultdict(list)
    for record in records:
        groups[
            record["case_id"],
            record["gap_scale"],
            record["panel"],
            record["receiver"],
        ].append(record)
    group_demands = []
    for (case, gap, panel, receiver), members in groups.items():
        forces = np.array(
            [[r[f"force_on_panel_{c}_n"] for c in "xyz"] for r in members]
        )
        points = np.array([[r[f"common_datum_{c}_mm"] for c in "xyz"] for r in members])
        group_demands.append(
            {
                "case_id": case,
                "gap_scale": gap,
                "panel": panel,
                "receiver": receiver,
                "axis_ids": [r["axis_id"] for r in members],
                "total_head_withdrawal_n": sum(r["withdrawal_n"] for r in members),
                "force_on_panel_n": forces.sum(axis=0).tolist(),
                "moment_on_panel_about_panel_centroid_nmm": np.cross(
                    points - centers[panel], forces
                )
                .sum(axis=0)
                .tolist(),
                "force_on_receiver_n": (-forces.sum(axis=0)).tolist(),
                "moment_on_receiver_about_receiver_centroid_nmm": np.cross(
                    points - centers[receiver], -forces
                )
                .sum(axis=0)
                .tolist(),
            }
        )
    report = {
        "schema": "conditional_panel_attachment_screen/v1",
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): h
            for p, h in pins.items()
        },
        "producer_sha256": sha(Path(__file__)),
        "frame_cases": len(CASES),
        "saved_frame_states": len(states),
        "withdrawal_stiffness_hypotheses_n_per_mm": sorted(
            {float(stiffness[r["row"]]) for r in axes.values()}
        ),
        "frame_clearance_joint_hosts": comparison["clearance_joint_hosts"],
        "screw_states": len(records),
        "upper_panel_allocations": len(allocations),
        "upper_panel_contact_relaxed_allocations": len(relaxed_allocations),
        "same_state_peak_withdrawal": worst,
        "same_state_nominal_gap_peak_withdrawal": nominal_worst,
        "same_state_peak_lateral": max(records, key=lambda r: r["lateral_resultant_n"]),
        "same_state_peak_relative_opening": max(
            records, key=lambda r: r["screw_relative_opening_mm"]
        ),
        "same_state_panel_receiver_screw_group_demands": group_demands,
        "withdrawal_sensitivities": sensitivity,
        "head_demand_geometry_sensitivities": head_demands,
        "generic_head_reference_sensitivities": head_sensitivity,
        "panel_only_static_allocations": allocations,
        "panel_only_contact_relaxed_static_allocations": relaxed_allocations,
        "saved_balance_checks": balance_checks,
        "limits": [
            "No new frame or native solve. All force records reuse the saved conditional frame.",
            "Stiffness overrides, when present, are read from the saved frame metadata and checked against all 66 axial laws. They are explicit unqualified hypotheses, not product measurements.",
            "Common-datum panel/receiver motions contain the returned rigid components. Total connection relative motion additionally contains both bodies' elastic response. Individual absolute elastic body motions are not reconstructed; no movement acceptance limit is adopted.",
            "Generic NDS cut/rolled side-grain reference is not a Hillman rating; applicability and all end-use adjustments are unresolved.",
            "G and effective thread lengths are declared hypotheses, not material or delivered screw measurements. 45.24375mm is nominal penetration, not measured effective thread. 42.3333mm is an approximate standard cut-thread scenario, not a delivered Hillman dimension.",
            "AWC supporting head pull-through research includes flush countersunk flathead screws. Circular plan shape, head dimensions, net plywood thickness and product applicability remain assumptions. The generic circular-head calculation is a conditional reference, not Hillman resistance. Cylindrical punch metrics are mean demands only, with an assumed failure surface and no resistance assigned.",
            "Head pull-through, screw lateral and combined resistance are not adopted by this withdrawal comparison.",
            "Group force/moment records include only the purchased screws. Other contact/bolt actions and complete receiver resistance must be checked by the parent; group head-force sums do not establish a group capacity.",
            "Fixed-contact allocations preserve the saved panel axial wrench with existing contact/lateral actions held. Contact-relaxed allocations preserve the saved net panel normal wrench, allow compression contacts to change and keep lateral actions held. Both omit elastic compatibility, contact opening/closure and individual receiver balance; neither replaces the source frame force allocation.",
        ],
        "reviewed_geometry_changed": False,
        "hardware_changed": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    for path, digest in pins.items():
        require(sha(path) == digest, "input changed during screen: " + str(path))
    output.mkdir(parents=True)
    with (output / "screw-states.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (output / "comparison.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    receipt = {
        "schema": "conditional_panel_attachment_screen_receipt/v1",
        "source_frame_comparison_sha256": pins[source / "comparison.json"],
        "artifact_sha256": {
            name: sha(output / name)
            for name in ("comparison.json", "screw-states.csv", "producer.py.snapshot")
        },
        "authority_sha256_unchanged": AUTHORITY,
        "saved_screw_inventory_and_law_checks_passed": True,
        "saved_body_balance_checks_passed": True,
        "saved_returned_motion_compatibility_checks_passed": True,
        "panel_only_allocation_primal_dual_checks_passed": True,
        "physical_release": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "peak": nominal_worst,
                "optimistic_largest_tie_n": max(
                    a["minimum_largest_tie_n"]
                    for a in allocations
                    if a["gap_scale"] == 1
                ),
                "contact_relaxed_optimistic_largest_tie_n": max(
                    a["minimum_largest_tie_n"]
                    for a in relaxed_allocations
                    if a["gap_scale"] == 1
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
