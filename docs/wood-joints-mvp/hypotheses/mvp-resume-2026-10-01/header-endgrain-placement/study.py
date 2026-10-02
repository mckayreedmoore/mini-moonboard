"""Replay the current twelve header bolt placements; perform no model solve.

Distances are axis-to-boundary distances, not ray travel or bore ligaments.
Generated receipts stay in this child's ignored results directory.
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = HERE.parents[4]
FINAL = PARENT / "header-joint-attempt02/final"
FRAME = PARENT / "corner-frame-attempt01"
CURRENT = PARENT / "two-receiver-frame-attempt03"
GEOMETRY = PARENT / "member-screen-attempt02/all-two-receiver-clearance01/geometry.json"
INPUTS = PARENT.parent / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
FEATURES = PARENT.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
CACHE = PARENT.parent / "upper-block-strength-2026-10-01/source-cache"
D = 6.35
ZERO_N = 1e-10  # The existing header replay's direction threshold, not a capacity.
TOL_MM = 1e-6
PINS = {
    CURRENT / "comparison.json": "0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5",
    CURRENT / "response.npz": "774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52",
    FINAL / "checks.json": "8daded05317ef0babb3be8e60adccd5a688bb386be19e8ce2cea32718ab560f9",
    FINAL / "placement.json": "27b108147a64834c566d64447a15270db0534984457ac1f139d938d1fba38b57",
    FINAL / "joint-states.json": "a09e64e57c4110932d9eab3dcaafb1872228dd1f69142f61bd9286357acec48c",
    FINAL
    / "joint-actions.json": "fcdd3e85f7856220504de79f818724dbf271f029f1066143ec8335f59ed966a4",
    FINAL
    / "header-sections.csv": "05378f3310231b8798da94a316a12c15add2e925db7081efd2878c388aeec32f",
    FINAL / "source-pins.json": "72aa536e1e7a75944ff5339324c86c728c40d4e53ce521f58f50f5d04d7e8090",
    PARENT
    / "header-joint-checks.md": "e426ad02d5e598c7e5d6db59f735a9a723c53655fd390d1fa05777164621df53",
    PARENT
    / "header_joint_checks.py": "299e5cbc226bd4c72ab43a81e59ede35497adf00c78a2cfef77a9d66613ef29c",
    CACHE
    / "source-bounds.json": "91c8c0c33cb7cc35dc31ba332778a80e1c5a972a6134e5e277a473a2adf719c9",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def write_csv(path, records):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    k: json.dumps(v, separators=(",", ":"), allow_nan=False)
                    if isinstance(v, (list, dict))
                    else v
                    for k, v in record.items()
                }
            )


def unit(vector):
    vector = np.asarray(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def close(a, b, tol=TOL_MM):
    require(
        np.max(np.abs(np.asarray(a) - np.asarray(b))) <= tol,
        f"source/arithmetic disagreement: {a} versus {b}",
    )


def distances(point, box, coordinates):
    return {
        sign + "XYZ"[i]: float(point[i] - box[0, i] if sign == "-" else box[1, i] - point[i])
        for i in coordinates
        for sign in ("-", "+")
    }


def main(output):
    require(
        output.parent == HERE / "results" and not output.exists(),
        "use a new immediate child of this study's results directory",
    )
    pins = dict(PINS)
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen input: {path}")
    upstream_pins = {Path(k): v for k, v in read(FINAL / "source-pins.json").items()}
    for path in (
        INPUTS,
        FEATURES,
        GEOMETRY,
        FRAME / "model.json",
        FRAME / "row-identities.json",
        PARENT / "frame_state_contract.py",
        CACHE / "chapter11-2024-awc-20260911.pdf",
        CACHE / "chapter12-2024-awc-20260911.pdf",
        CACHE / "appendix-2024-awc-20260911.pdf",
    ):
        pins[path] = upstream_pins[path]
        require(sha(path) == pins[path], f"changed consumed upstream source: {path}")
    # Import only the small saved-state contract, without CAD or frame helpers.
    spec = importlib.util.spec_from_file_location(
        "header_placement_contract", PARENT / "frame_state_contract.py"
    )
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    comparison, checks = read(CURRENT / "comparison.json"), read(FINAL / "checks.json")
    scope = contract.force_state_scope(comparison)
    require(scope == checks["source_force_state_scope"], "mixed seating/force scope")
    require(
        comparison["response_sha256"]
        == pins[CURRENT / "response.npz"]
        == checks["response_sha256"],
        "mixed response",
    )
    inputs, model, geometry = read(INPUTS), read(FRAME / "model.json"), read(GEOMETRY)
    require(
        inputs["candidate"] == model["candidate"] == checks["candidate"]
        and inputs["revision_id"] == model["source_revision"] == checks["source_revision"],
        "mixed model identity",
    )
    for path in (FRAME / "model.json", FRAME / "row-identities.json"):
        require(
            comparison["source_sha256"][str(path.relative_to(ROOT))] == pins[path],
            "comparison names another frame source",
        )
    states = read(FINAL / "joint-states.json")
    placement = {(s["case_id"], s["axis_id"]): s for s in read(FINAL / "placement.json")}
    axes = sorted({s["axis_id"] for s in states})
    census = {(case, axis) for case in contract.CASES for axis in axes}
    require(
        len(axes) == 12
        and len(states) == len(placement) == 72
        and {(s["case_id"], s["axis_id"]) for s in states} == set(placement) == census,
        "expected twelve axes, each once in all six cases",
    )
    bolts = {b["axis_id"]: b for b in inputs["connections"] if b["kind"] == "candidate_bolt"}
    features = {r["member_id"]: r for r in read(FEATURES)["records"]}
    blocks = {s["block"] for s in states}
    require(len(blocks) == 6, "expected six receivers")
    bounds, receivers = {}, {}
    for body in sorted(blocks | {"base_header"}):
        record = geometry["members"][body]
        path = ROOT / record["current_finished_step"]
        pins[path] = record["current_finished_step_sha256"]
        require(
            upstream_pins[path] == pins[path] == features[body]["step_binding"]["file_sha256"]
            and sha(path) == pins[path],
            "mixed finished receiver",
        )
        boxes = np.array([f["bounds_global_xyz_mm"] for f in features[body]["features"]])
        bounds[body] = np.array([boxes[:, ::2].min(axis=0), boxes[:, 1::2].max(axis=0)])
        grain = model["material_binding"]["orientation_overrides"][body][
            "material_axes_global_xyz"
        ]["L"]
        close(unit(grain), [1, 0, 0] if body == "base_header" else [0, 0, 1])
        close(unit(record["geometry"]["axis"]), unit(grain))
        receivers[body] = {
            "grain_xyz": grain,
            "bounds_xyz_mm": bounds[body].tolist(),
            "finished_step": str(path.relative_to(ROOT)),
            "sha256": pins[path],
        }
    header_box = bounds["base_header"]
    close(header_box, [[-1219.2, -175.7, 238.9], [1216.025, -36, 277]])
    groups = defaultdict(list)
    axis_records, receiver_states, active = [], [], []
    for axis in axes:
        example = next(s for s in states if s["axis_id"] == axis)
        block, bolt = example["block"], bolts[axis]
        require(set(bolt["receiver_member_ids"]) == {block, "base_header"}, "foreign receiver")
        close(abs(unit(bolt["axis_xyz"])), [0, 0, 1])
        point = bolt["source_point_xyz_mm"]
        groups[block].append(axis)
        lengths = {
            r["receiver_id"]: r["receiver_wood_axis_length_mm"]
            for r in bolt["source_record"]["geometry"]["wood_receiver_intervals"]
        }
        ell = min(lengths.values())
        close(ell, 6 * D)
        close(bolt["source_record"]["geometry"]["modeled_shaft_diameter_mm"], D)
        for receiver in bolt["receiver_clearance_geometry"]:
            require(
                receiver["receiver_step_sha256"] == receivers[receiver["receiver_id"]]["sha256"],
                "axis receiver has another source",
            )
        bd = distances(point, bounds[block], (0, 1))
        hd = distances(point, header_box, (0, 1))
        require(
            min(bd.values()) >= 1.5 * D - TOL_MM and min(hd.values()) >= 1.5 * D - TOL_MM,
            "geometric 1.5D comparator is short",
        )
        require(
            min(hd["-X"], hd["+X"]) >= 7 * D - TOL_MM,
            "header all-axis softwood end envelope is short",
        )
        axis_records.append(
            {
                "axis_id": axis,
                "block": block,
                "source_point_xyz_mm": point,
                "source_axis_xyz": bolt["axis_xyz"],
                "block_edge_distances_mm": bd,
                "header_X_end_distances_mm": {k: v for k, v in hd.items() if k.endswith("X")},
                "header_Y_edge_distances_mm": {k: v for k, v in hd.items() if k.endswith("Y")},
                "block_Z_end_distance_mm": None,
                "block_end_applicability": "Through axis parallel to grain: no transverse-fastener center/end construction; shaft midpoint is not end distance.",
                "main_side_bearing_lengths_mm": lengths,
                "ell_over_D": ell / D,
                "header_parallel_edge_min_mm": 1.5 * D,
                "header_half_row_spacing_branch": "ell/D=6, not >6; no half-row-spacing edge enlargement",
                "perpendicular_between_rows_min_mm": 5 * D,
                "bore_diameters_mm": {
                    r["receiver_id"]: 2 * r["unique_bore_radius_mm"]
                    for r in bolt["receiver_clearance_geometry"]
                },
            }
        )
    rows = read(FRAME / "row-identities.json")
    require(
        len(rows) == 1888 and all(r["row"] == i for i, r in enumerate(rows)), "row census changed"
    )
    with np.load(CURRENT / "response.npz", allow_pickle=False) as response:
        for state in states:
            case, axis, block = state["case_id"], state["axis_id"], state["block"]
            saved = response[case + "_gap_raw_force_n"]
            require(saved.shape == (1888,) and np.isfinite(saved).all(), "invalid saved force")
            component_rows = state["component_rows"]
            own = rows[component_rows[0]]["ownership"]
            require(
                {own["first_body"], own["second_body"]} == {block, "base_header"}, "foreign force"
            )
            require(
                all(
                    r["ownership"]["role"] == "candidate_bolt_lateral_plane"
                    and r["row_id"].rsplit("/", 1)[0] == axis
                    for r in (rows[i] for i in component_rows)
                ),
                "wrong force rows",
            )
            force = saved[component_rows] @ np.array(
                [rows[i]["ownership"]["direction_global_xyz"] for i in component_rows]
            )
            if own["first_body"] != block:
                force = -force
            close(force, state["force_on_block_xyz_n"], 1e-9)
            p = placement[(case, axis)]
            close(force, p["signed_force_on_block_xyz_n"], 1e-9)
            close(p["source_axis_point_xyz_mm"], bolts[axis]["source_point_xyz_mm"])
            close(p["block_finished_bounds_xyz_mm"], bounds[block])
            tie = rows[state["tie_row"]]
            require(
                tie["ownership"]["role"] == "physical_bolt_outer_seat_tension"
                and tie["row_id"].rsplit("/", 1)[0] == axis,
                "wrong axial row",
            )
            close(saved[state["tie_row"]], state["tension_n"], 1e-9)
            require(state["tension_n"] >= -ZERO_N, "compressive tension-only tie")
            is_zero = max(abs(force[:2])) < ZERO_N
            require(
                abs(force[1]) < ZERO_N and abs(force[2]) < ZERO_N,
                "new non-X force needs its own applicability interpretation",
            )
            if not is_zero:
                active.append(
                    {"case_id": case, "axis_id": axis, "block_force_xyz_n": force.tolist()}
                )
            for body, own_force in ((block, force), ("base_header", -force)):
                ds = distances(bolts[axis]["source_point_xyz_mm"], bounds[body], (0, 1))
                loaded = (
                    None if is_zero or body == "base_header" else ("+X" if force[0] > 0 else "-X")
                )
                opposite = None if loaded is None else ("-X" if loaded == "+X" else "+X")
                minimum_end = None
                if not is_zero and body == "base_header":
                    toward = "+X" if own_force[0] > 0 else "-X"
                    # Softwood: toward-end 7D and away-from-end 4D, with no reduction.
                    require(
                        ds[toward] >= 7 * D - TOL_MM
                        and ds[("-X" if toward == "+X" else "+X")] >= 4 * D - TOL_MM,
                        "active header end distance is short",
                    )
                    minimum_end = {
                        "toward_end": toward,
                        "toward_mm": ds[toward],
                        "toward_required_mm": 7 * D,
                        "away_mm": ds[("-X" if toward == "+X" else "+X")],
                        "away_required_mm": 4 * D,
                    }
                if loaded:
                    require(
                        ds[loaded] >= 4 * D - TOL_MM and ds[opposite] >= 1.5 * D - TOL_MM,
                        "active perpendicular block edge is short",
                    )
                    require(
                        p["first_intersected_source_envelope_face"] == loaded,
                        "saved diagnostic disagrees with this pure-X direction",
                    )
                    close(ds[loaded], p["first_intersection_normal_distance_mm"])
                else:
                    require(
                        not is_zero or p["first_intersected_source_envelope_face"] is None,
                        "zero state acquired a ray direction",
                    )
                receiver_states.append(
                    {
                        "case_id": case,
                        "axis_id": axis,
                        "receiver": body,
                        "signed_lateral_force_xyz_n": own_force.tolist(),
                        "outer_tie_n": state["tension_n"],
                        "component_rows": component_rows,
                        "tie_row": state["tie_row"],
                        "lateral_direction": "zero_within_1e-10_N"
                        if is_zero
                        else ("+X" if own_force[0] > 0 else "-X"),
                        "load_to_grain_deg": None
                        if is_zero
                        else (0 if body == "base_header" else 90),
                        "Table_A": "no current lateral action; header 7D/4D geometry envelope retained"
                        if is_zero and body == "base_header"
                        else "active parallel softwood ends"
                        if body == "base_header"
                        else "no transverse-fastener end construction for through end-grain shaft",
                        "active_end_obligations_mm": minimum_end,
                        "Table_C": "no lateral direction; all measured edges retained, no loaded-face assignment"
                        if is_zero
                        else "parallel grain: both Y edges >=1.5D, ell/D=6"
                        if body == "base_header"
                        else "perpendicular grain: acting X edge >=4D, opposite X edge >=1.5D; Y faces unselected",
                        "loaded_edge": loaded,
                        "loaded_edge_mm": None if loaded is None else ds[loaded],
                        "loaded_min_mm": None if loaded is None else 4 * D,
                        "opposite_edge_mm": None if opposite is None else ds[opposite],
                        "opposite_min_mm": None if opposite is None else 1.5 * D,
                        "header_parallel_Y_min_mm": None
                        if is_zero or body != "base_header"
                        else 1.5 * D,
                        "pair_spacing_applicability": "no current lateral row direction; dimensional envelope only"
                        if is_zero
                        else "pair separates along Y, transverse to X action: Table D; not Table B load-aligned row",
                        "adopted_detailing_failure": False,
                    }
                )
    require(len(active) == 2 and len(receiver_states) == 144, "current direction census changed")
    spacing = []
    for a, b in combinations(axes, 2):
        dx, dy = np.abs(
            np.array(bolts[a]["source_point_xyz_mm"][:2])
            - np.array(bolts[b]["source_point_xyz_mm"][:2])
        )
        same = bolts[a]["receiver_member_ids"] == bolts[b]["receiver_member_ids"]
        pitch = float(np.hypot(dx, dy))
        require(pitch >= 4 * D - TOL_MM, "header-axis center spacing envelope is short")
        if same:
            close(dx, 0)
            require(dy >= 5 * D - TOL_MM, "pair between-row envelope is short")
        spacing.append(
            {
                "axis_a": a,
                "axis_b": b,
                "receiver": "base_header",
                "also_common_block": same,
                "grain_X_projection_mm": float(dx),
                "transverse_Y_projection_mm": float(dy),
                "axis_spacing_XY_mm": pitch,
                "Table_B_3D_min_mm": 3 * D,
                "Table_B_parallel_full_value_mm": 4 * D,
                "Table_B_applicability": "not a load-aligned X row"
                if same
                else "separate interfaces; distance inventory, no combined row or Cg inferred",
                "Table_D_header_parallel_min_mm": 1.5 * D if same else None,
                "Table_D_block_perpendicular_min_mm": 5 * D if same else None,
                "perpendicular_Table_B_full_value": "required spacing for attached members, not a universal 4D",
                "Table_D_applicability": "active X states: transverse pair; other states: geometry envelope"
                if same
                else "separate interfaces; small Y offset alone is not an adopted adjacent-row failure",
            }
        )
    require(len(groups) == 6 and all(len(g) == 2 for g in groups.values()), "pair census changed")
    span = max(bolts[a]["source_point_xyz_mm"][1] for a in axes) - min(
        bolts[a]["source_point_xyz_mm"][1] for a in axes
    )
    require(span <= 127 + TOL_MM, "header target-axis cross-grain spread exceeds five inches")
    # Inventory crossing bores without extending parallel-axis spacing tables.
    neighbors, inventory = [], []
    for body in sorted(receivers):
        other = [
            b
            for b in inputs["connections"]
            if body in b["receiver_member_ids"] and b["axis_id"] not in axes
        ]
        inventory.append(
            {
                "receiver": body,
                "other_connections": [
                    {"axis_id": b["axis_id"], "kind": b["kind"], "axis_xyz": b["axis_xyz"]}
                    for b in other
                ],
                "scope": "Other duties remain separate; no target-bolt rule assigned to Hillman screws or orthogonal bolts.",
            }
        )
        if body == "base_header":
            continue
        require(
            len(other) == 2 and all(b["kind"] == "candidate_bolt" for b in other),
            "neighbor census changed",
        )
        for axis in groups[body]:
            bolt = bolts[axis]
            for neighbor in other:
                close(abs(unit(neighbor["axis_xyz"])), [1, 0, 0])
                p, q = (
                    np.array(bolt["source_point_xyz_mm"]),
                    np.array(neighbor["source_point_xyz_mm"]),
                )
                require(
                    bounds[body][0, 0] <= p[0] <= bounds[body][1, 0]
                    and bounds[body][0, 2] <= q[2] <= bounds[body][1, 2],
                    "closest points outside receiver",
                )
                radii = [
                    next(
                        r["unique_bore_radius_mm"]
                        for r in b["receiver_clearance_geometry"]
                        if r["receiver_id"] == body
                    )
                    for b in (bolt, neighbor)
                ]
                sep = float(abs(p[1] - q[1]))
                neighbors.append(
                    {
                        "receiver": body,
                        "target_axis": axis,
                        "orthogonal_axis": neighbor["axis_id"],
                        "axis_separation_mm": sep,
                        "source_bore_radii_mm": radii,
                        "nominal_between_bores_ligament_mm": sep - sum(radii),
                        "applicability": "Z/X crossing bores: geometric ligament only; Tables B/D supply no adopted cross-axis rule",
                        "local_split_resistance_established": False,
                    }
                )
    joints = read(FINAL / "joint-actions.json")["interfaces"]
    require(
        len(joints) == 36
        and {(j["case_id"], j["block"]) for j in joints}
        == {(c, b) for c in contract.CASES for b in groups},
        "joint census changed",
    )
    retained_joints = []
    for joint in joints:
        wrenches = joint["role_wrenches_xyz_n_nmm"]
        # Elementary saved point-action arithmetic, retaining every free couple.
        datum = np.array(joint["datum_xyz_mm"])
        for role, saved_wrench in wrenches.items():
            actions = [a for a in joint["actions_on_block"] if a["role"] == role]
            restored = np.sum(
                [
                    np.r_[
                        a["force_n"],
                        np.cross(np.array(a["point_mm"]) - datum, a["force_n"])
                        + a["free_moment_nmm"],
                    ]
                    for a in actions
                ],
                axis=0,
            )
            close(restored, saved_wrench)
        close(np.sum(list(wrenches.values()), axis=0), joint["interface_wrench_on_block_xyz_n_nmm"])
        require(
            max(abs(v) for v in joint["reciprocity_residual_xyz_n_nmm"]) < 1e-5,
            "interface imbalance",
        )
        target_states = [
            s for s in states if s["case_id"] == joint["case_id"] and s["block"] == joint["block"]
        ]
        close(
            np.sum([s["force_on_block_xyz_n"] for s in target_states], axis=0),
            wrenches["candidate_bolt_lateral_plane"][:3],
        )
        require(joint["pair"]["equal_sharing_assumed"] is False, "equal sharing entered source")
        retained_joints.append(
            {
                k: joint[k]
                for k in (
                    "case_id",
                    "block",
                    "axis_ids",
                    "datum_xyz_mm",
                    "interface_wrench_on_block_xyz_n_nmm",
                    "role_wrenches_xyz_n_nmm",
                    "pair",
                    "header_connection_zone_signed_peaks",
                    "header_VY_demand_n",
                    "splitting_design_resistance_established",
                )
            }
        )
    peak = max(joints, key=lambda j: j["header_VY_demand_n"])
    sources = read(CACHE / "source-bounds.json")["sources"]
    for path, digest in pins.items():
        require(sha(path) == digest, f"source changed during arithmetic: {path}")
    output.mkdir(parents=True)
    write_csv(output / "axes.csv", axis_records)
    write_csv(output / "receiver-states.csv", receiver_states)
    write_csv(output / "spacing.csv", spacing)
    write_csv(output / "neighbor-bores.csv", neighbors)
    write_json(output / "joint-demands.json", retained_joints)
    pins[Path(__file__).resolve()] = sha(Path(__file__))
    write_json(
        output / "source-pins.json", {str(p.relative_to(ROOT)): h for p, h in sorted(pins.items())}
    )
    summary = {
        "schema": "current_header_endgrain_placement/v1",
        "status": "APPLICABLE_CURRENT_TRANSLATIONAL_PLACEMENT_CHECKS_CLEAR_LOCAL_SPLITTING_OPEN",
        "counts": {
            "axes": 12,
            "bolt_states": 72,
            "receiver_states": 144,
            "zero_in_plane_states": 70,
            "directional_states": 2,
            "pairs": 6,
            "header_axis_pairs": len(spacing),
            "cross_axis_bore_pairs": len(neighbors),
            "joint_states": 36,
        },
        "candidate": checks["candidate"],
        "source_revision": checks["source_revision"],
        "source_force_state_scope": scope,
        "signed_active_states": active,
        "D_mm": D,
        "zero_direction_threshold_n": ZERO_N,
        "distance_tolerance_mm": TOL_MM,
        "ell_over_D": 6,
        "header_target_cross_grain_span_mm": span,
        "cross_grain_span_limit_mm": 127,
        "minimum_header_end_mm": min(
            min(r["header_X_end_distances_mm"].values()) for r in axis_records
        ),
        "minimum_header_Y_edge_mm": min(
            min(r["header_Y_edge_distances_mm"].values()) for r in axis_records
        ),
        "minimum_pair_pitch_mm": min(
            r["axis_spacing_XY_mm"] for r in spacing if r["also_common_block"]
        ),
        "minimum_cross_axis_nominal_ligament_mm": min(
            r["nominal_between_bores_ligament_mm"] for r in neighbors
        ),
        "receiver_bindings": receivers,
        "other_receiver_connections": inventory,
        "adopted_actual_detailing_failures": [],
        "axis_moves_required_by_this_calculation": [],
        "remaining_requirement": {
            "clauses": ["NDS 11.1.2", "11.1.3", "12.6.1-.3", "Table 12.5.1C note 2 / 3.8.2"],
            "exact_missing_fact": "Applicable local load distribution and resistance for the source-pinned bored blocks and header under each simultaneous lateral/axial/contact wrench and couple. Include header Y/Z tension perpendicular to X grain, end-grain block transverse splitting, bore-to-bore ligaments and disconnected header strips. Assess below-neutral-axis concentrated-load applicability using the actual load path; if it applies, prove mechanical/equivalent reinforcement. Do not replace moments with net force or invent Ft-perp from Fc-perp/Fv.",
            "maximum_header_zone_VY_n": peak["header_VY_demand_n"],
            "maximum_header_zone_VY_state": {
                "case_id": peak["case_id"],
                "block": peak["block"],
                **peak["header_connection_zone_signed_peaks"]["VY"],
            },
            "maximum_saved_header_torque_state": checks["peaks"]["header_torque"],
            "splitting_design_resistance_established": False,
            "uniform_group_stress_or_equal_sharing_established": False,
            "stagger_and_gravity_axis_requirement": "Apply 12.6.1's symmetric staggering where possible and evaluate 12.6.2's member gravity-axis/center-of-resistance condition for these eccentric multiple-fastener joints. Current unequal forces and couples establish no uniform-group-stress credit; Table D dimensions alone do not satisfy these obligations.",
            "next_action": "Use these current 36 saved joint wrenches and existing finished-section/washer evidence to evaluate one applicable local splitting/load-transfer resistance; parent owns integration and any heavy work.",
        },
        "applicability_limits": [
            "Seventy directions are null at the existing 1e-10 N threshold; raw signed forces remain. Null does not remove axial ties, contact forces, moments or local stress obligations.",
            "Two active pure-X translations support direct X-edge distances. Historical five oblique states and Y-edge failure rules are not consumed. Ray diagnostics are not normative rules.",
            "Through end-grain shaft midpoint Z is not a transverse-fastener end distance. Ordinary Tables A/B provide no new torque or through-end-grain splitting capacity.",
            "Target pairs are transverse to current X action, not load-aligned rows. Other-state Table D values are dimensional envelopes. Perpendicular Table B full-value spacing is attached-member dependent; 4D is only the parallel full-value comparator.",
            "Separate header interfaces are not merged into a fictitious row from small Y projections. No new Cg, uniform sharing or moment capacity is inferred; source Cg remains a sensitivity.",
            "The 127 mm spread check covers the twelve target axes. Orthogonal bores and ten Hillman axes are inventoried; no mixed-axis spacing or mixed-fastener capacity is invented.",
            "Ceg=.67 does not waive placement; no Cdelta reduction waives edge minima. Existing lateral resistance method is not recomputed here.",
            "Table E is for withdrawal-only lag screws; Table F is glulam; Table G is CLT. None applies to these sawn-lumber through bolts.",
            "Distances bind nominal finished-source geometry, not delivered/inspected cuts, bores, grade, shanks or installed hardware. Installation qualification remains upstream.",
        ],
        "official_sources": [
            s
            for s in sources
            if s["cache_path"]
            in (
                "chapter11-2024-awc-20260911.pdf",
                "chapter12-2024-awc-20260911.pdf",
                "appendix-2024-awc-20260911.pdf",
            )
        ],
        "tool_versions": {"python": platform.python_version(), "numpy": np.__version__},
        "native_solve_run": False,
        "frame_solve_run": False,
        "CAD_run": False,
        "software_tests_run": False,
        "review_run": False,
        "geometry_changed": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
        "producer_sha256": sha(Path(__file__)),
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir())},
    }
    write_json(output / "worksheet.json", summary)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "counts": summary["counts"],
                "worksheet_sha256": sha(output / "worksheet.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/final")
    args = parser.parse_args()
    main((HERE / args.output).resolve())
