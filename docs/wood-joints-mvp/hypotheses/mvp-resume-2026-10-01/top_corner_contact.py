"""Coupled two-face normal transfer for the isolated top-corner proposal.

Keep both host faces fixed and the cleat rigid. Apply the simultaneous lateral
actions from each frozen frame scenario, then solve compression-only contact
and tension-only bolts together. This is a local compliance scenario, not a
recomputed frame or a complete-joint resistance qualification.
"""

import argparse
import fcntl
import json
import math
import sys
from pathlib import Path

import numpy as np
import top_corner_actions as accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
PROPOSAL = HERE / "top-corner-correction/proposal.json"
PREPARED = HERE / "top-corner-contact-geometry.json"
X = np.array([1.0, 0.0, 0.0])
T = np.array([0.0, 0.642787610, 0.766044443])
T /= np.linalg.norm(T)
N = np.cross(X, T)
# Five restrained modes. Translation along N is supplied by the fixed lateral
# actions; retain and check its force balance separately.
BASIS = np.zeros((6, 5))
BASIS[:3, :2] = np.array([X, T]).T
BASIS[3:, 2:] = np.eye(3) / 1000
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepare():
    import cadquery as cq

    from fea import wood_joint_reduced_properties as properties

    proposal = read(PROPOSAL)
    require(
        sha(PROPOSAL)
        == "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
        "changed correction proposal",
    )
    pins = {PROPOSAL: sha(PROPOSAL), **accounting.PINS}
    for relative, digest in proposal["producer_dependency_sha256"].items():
        path = ROOT / relative
        require(sha(path) == digest, "changed proposal helper: " + relative)
        pins[path] = digest
    for relative, digest in proposal["source_sha256"].items():
        path = ROOT / relative
        require(sha(path) == digest, "changed proposal source: " + relative)
        pins[path] = digest
    for relative, digest in proposal["proposal_step_sha256"].items():
        path = ROOT / relative
        require(sha(path) == digest, "changed proposed STEP: " + relative)
        pins[path] = digest
    inputs_path = accounting.BASE / "reduced-static-attempt01/model-inputs.json"
    inputs = read(inputs_path)
    verified = {}
    materials = properties._load_member_material_scenarios(inputs, verified)
    pins.update({ROOT / p: h for p, h in verified.items()})
    pins[Path(properties.__file__)] = sha(Path(properties.__file__))
    model = read(accounting.MODEL)
    result = []
    for prop in proposal["proposals"]:
        block = prop["block"]
        old = model["body_geometry"][block]["geometry_record"]
        old_center = (np.array(old["start"]) + old["end"]) / 2
        center = old_center - 25.4 * T
        left = block.endswith("left_cleat")
        shape = cq.importers.importStep(
            str(HERE / "top-corner-correction" / (block + ".step"))
        ).val()
        rows, faces = [], []
        for host, normal, u, v, face_center, width, depth, bore in [
            (
                "base_side_left" if left else "base_side_right",
                X if left else -X,
                N,
                T,
                center + (-44.45 if left else 44.45) * X,
                119.7,
                139.7,
                9.0,
            ),
            ("base_rail_top", -T, X, N, center + 69.85 * T, 88.9, 119.7, 7.5),
        ]:
            candidates = [
                f
                for f in shape.Faces()
                if f.geomType() == "PLANE"
                and abs(np.dot(np.array(f.Center().toTuple()) - face_center, normal))
                < 1e-5
                and abs(np.dot(f.normalAt().toTuple(), normal)) > 1 - 1e-8
            ]
            require(len(candidates) == 1, "missing proposed contact face")
            face = candidates[0]
            expected_area = width * depth - 2 * math.pi * (bore / 2) ** 2
            require(
                abs(face.Area() - expected_area) < 1e-3, "contact face area mismatch"
            )
            face_record = {
                "host": host,
                "center_mm": face_center.tolist(),
                "normal_force_on_cleat_xyz": normal.tolist(),
                "exact_finished_area_mm2": face.Area(),
                "corners_mm": [
                    (face_center + a * width / 2 * u + b * depth / 2 * v).tolist()
                    for a in (-1, 1)
                    for b in (-1, 1)
                ],
            }
            cells = []
            for i in range(4):
                for j in range(4):
                    p = face_center + ((i + 0.5) / 4 - 0.5) * width * u
                    p += ((j + 0.5) / 4 - 0.5) * depth * v
                    mask = (
                        cq.Workplane(
                            cq.Plane(
                                origin=tuple(p),
                                xDir=tuple(u),
                                normal=tuple(np.cross(u, v)),
                            )
                        )
                        .box(width / 4, depth / 4, 2)
                        .val()
                    )
                    clipped = face.intersect(mask)
                    area = sum(f.Area() for f in clipped.Faces())
                    require(area > 0 and clipped.isValid(), "invalid contact cell")
                    point = np.array(clipped.Center().toTuple())
                    row = {
                        "kind": "contact",
                        "host": host,
                        "point_mm": point.tolist(),
                        "direction_xyz": normal.tolist(),
                        "area_mm2": area,
                        "stiffness_n_per_mm": 100 * area,
                    }
                    rows.append(row)
                    cells.append(row)
            require(
                abs(sum(r["area_mm2"] for r in cells) - face.Area()) < 1e-3,
                "contact partition area mismatch",
            )
            faces.append(face_record)
            for axis in prop["axes"]:
                side = "/side_" in axis["axis_id"]
                if side != host.startswith("base_side_"):
                    continue
                point = np.array(axis["proposed_axis_point_mm"])
                point += np.dot(face_center - point, normal) * normal
                diameter = axis["nominal_bolt_diameter_mm"]
                # Existing quarter-inch CAD annulus; explicit catalog nominal
                # 5/16-inch USS annulus. Neither is a delivered washer measurement.
                od, inside, thickness = (
                    (22.225, 9.525, 2.032) if side else (18.6436, 8.0, 2.032)
                )
                area = math.pi * (od**2 - inside**2) / 4
                geometry = {
                    "modeled_shaft_diameter_mm": diameter,
                    "washer_annular_bearing_area_mm2": area,
                    "washer_thickness_mm": thickness,
                    "seat_spacing_mm": 177.8,
                    "wood_grip_mm": 177.8,
                    "axis_head_to_nut_xyz": normal.tolist(),
                    "outer_receiver_member_ids_head_to_nut": [host, block],
                    "outer_seat_points_xyz_mm": [
                        (point - (88.9 if side else 38.1) * normal).tolist(),
                        (point + (88.9 if side else 139.7) * normal).tolist(),
                    ],
                    "head_washer": {"modeled_volume_mm3": area * thickness},
                    "nut_washer": {"modeled_volume_mm3": area * thickness},
                    "compression_contact_pairs": [
                        {"receiver_member_ids": [host, block]}
                    ],
                }
                law = properties._bolt_axial_law(
                    {"kind": "candidate_bolt", "axis_id": axis["axis_id"]},
                    geometry,
                    [],
                    materials,
                )
                rows.append(
                    {
                        "kind": "bolt_tension",
                        "host": host,
                        "axis_id": axis["axis_id"],
                        "point_mm": point.tolist(),
                        "direction_xyz": (-normal).tolist(),
                        "stiffness_n_per_mm": law["stiffness_n_per_mm"],
                        "nominal_washer_area_mm2": area,
                        "nominal_washer_OD_ID_thickness_mm": [od, inside, thickness],
                        "axial_law": law,
                    }
                )
        require(len(rows) == 36, "incomplete coupled cleat")
        result.append(
            {
                "block": block,
                "datum_mm": old_center.tolist(),
                "faces": faces,
                "rows": rows,
            }
        )
    write(
        PREPARED,
        {
            "schema": "top_corner_normal_contact_geometry/v1",
            "producer_sha256": sha(Path(__file__)),
            "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
            "cleats": result,
            "reviewed_geometry_changed": False,
            "physical_release": False,
        },
    )
    print("Prepared two cleats: 64 exact-area contact cells and eight axial laws.")


def solve():
    import simple_frame as frame

    geometry = read(PREPARED)
    require(
        geometry["producer_sha256"] == sha(Path(__file__)), "changed contact producer"
    )
    pins = {PREPARED: sha(PREPARED), Path(frame.__file__): sha(Path(frame.__file__))}
    pins.update({ROOT / p: h for p, h in geometry["source_sha256"].items()})
    pins.update({frame.COMP / p: h for p, h in frame.PINS.items()})
    for path, digest in pins.items():
        require(sha(path) == digest, "changed contact input: " + str(path))
    model, rows = read(accounting.MODEL), read(frame.COMP / "row-identities.json")
    assessment = read(frame.COMP / "assessment.json")
    loads = {c["case_id"]: c for c in read(accounting.LOADS)["cases"]}
    with np.load(frame.COMP / "operators.npz", allow_pickle=False) as operators:
        D_source = operators["D"].copy()
    cases = []
    for scenario, result_name, response_name in [
        (
            "original_with_parametric_withdrawal",
            "simple-frame-results.json",
            "simple-frame-response.npz",
        ),
    ]:
        result_path, response_path = HERE / result_name, HERE / response_name
        results = read(result_path)
        require(
            results["response_sha256"] == sha(response_path), "changed frame response"
        )
        require(
            all(
                c["status"] == "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS"
                for c in results["cases"]
            ),
            "frame scenario did not pass its numerical checks",
        )
        pins.update({result_path: sha(result_path), response_path: sha(response_path)})
        with np.load(response_path, allow_pickle=False) as response:
            for case in results["cases"]:
                case_id = case["case_id"]
                for cleat in geometry["cleats"]:
                    block = cleat["block"]
                    actions, datum, _ = accounting.physical_actions(
                        block,
                        {**loads[case_id], "dead_load_factor": frame.DEAD_LOAD_FACTOR},
                        response[case_id + "_force_n"],
                        model,
                        rows,
                        D_source,
                        assessment["body_names_in_rigid_column_order"],
                        {},
                    )
                    require(
                        np.max(abs(datum - cleat["datum_mm"])) < 1e-6,
                        "mixed body datum",
                    )
                    applied = accounting.wrench(
                        [
                            a
                            for a in actions
                            if a["role"] in (accounting.LATERAL, "discrete_body_load")
                        ],
                        datum,
                    )
                    source_closure = accounting.wrench(actions, datum)
                    require(
                        np.max(abs(source_closure[:3])) < 0.1
                        and np.max(abs(source_closure[3:])) < 2,
                        "unbalanced source cleat",
                    )
                    require(
                        abs(N @ applied[:3]) < 0.1,
                        "fixed lateral actions leave an unrestrained force",
                    )
                    mechanics = []
                    for row in cleat["rows"]:
                        normal = np.array(row["direction_xyz"])
                        mechanics.append(
                            np.r_[
                                normal,
                                np.cross(np.array(row["point_mm"]) - datum, normal),
                            ]
                        )
                    mechanics = np.array(mechanics)
                    D = mechanics @ BASIS
                    require(np.linalg.matrix_rank(D) == 5, "missing normal load path")
                    stiffness = np.array(
                        [r["stiffness_n_per_mm"] for r in cleat["rows"]]
                    )
                    f, a, q, iterations = frame.solve_branch(
                        np.zeros((len(D), len(D))),
                        D,
                        np.zeros(len(D)),
                        -BASIS.T @ applied,
                        stiffness,
                        np.ones(len(D), dtype=bool),
                        np.empty((0, 2), dtype=int),
                        np.empty(0, dtype=bool),
                    )
                    residual = mechanics.T @ f + applied
                    law_residual = np.max(abs(f - stiffness * np.maximum(q, 0)))
                    checks = {
                        "force_balance": bool(np.max(abs(residual[:3])) <= 0.1),
                        "moment_balance": bool(np.max(abs(residual[3:])) <= 2),
                        "spring_laws": bool(law_residual <= 0.1),
                        "nonnegative_forces": bool(np.min(f) >= -0.1),
                    }
                    state_rows = [
                        {
                            **r,
                            "force_n": float(f[i]),
                            "signed_approach_or_extension_mm": float(q[i]),
                        }
                        for i, r in enumerate(cleat["rows"])
                    ]
                    face_states = []
                    for face in cleat["faces"]:
                        normal = np.array(face["normal_force_on_cleat_xyz"])
                        pressures = []
                        for corner in face["corners_mm"]:
                            mode = (
                                np.r_[
                                    normal, np.cross(np.array(corner) - datum, normal)
                                ]
                                @ BASIS
                            )
                            pressures.append(100 * max(0, float(mode @ a)))
                        contact = [
                            r
                            for r in state_rows
                            if r["kind"] == "contact" and r["host"] == face["host"]
                        ]
                        face_states.append(
                            {
                                "host": face["host"],
                                "contact_resultant_n": sum(
                                    r["force_n"] for r in contact
                                ),
                                "positive_contact_cell_count": sum(
                                    r["force_n"] > 0.01 for r in contact
                                ),
                                "peak_cell_mean_pressure_mpa": max(
                                    r["force_n"] / r["area_mm2"] for r in contact
                                ),
                                "affine_peak_pressure_at_face_edge_mpa": max(pressures),
                                "peak_pressure_over_unadjusted_Fc_perp_625psi": max(
                                    pressures
                                )
                                / (625 * 0.006894757293168361),
                            }
                        )
                    bolts = [
                        {k: v for k, v in r.items() if k != "axial_law"}
                        for r in state_rows
                        if r["kind"] == "bolt_tension"
                    ]
                    for bolt in bolts:
                        bolt["ideal_nominal_annulus_wood_pressure_mpa"] = (
                            bolt["force_n"] / bolt["nominal_washer_area_mm2"]
                        )
                    cases.append(
                        {
                            "frame_scenario": scenario,
                            "case_id": case_id,
                            "block": block,
                            "status": "PASS_LOCAL_NORMAL_BALANCE_AND_LAWS"
                            if all(checks.values())
                            else "STOP_LOCAL_NORMAL_CHECK",
                            "checks": checks,
                            "applied_lateral_and_old_body_load_wrench_n_nmm": applied.tolist(),
                            "full_wrench_residual_n_nmm": residual.tolist(),
                            "spring_law_residual_n": float(law_residual),
                            "conjugate_modes_mm_and_scaled_rotation": a.tolist(),
                            "qp_iterations": iterations,
                            "faces": face_states,
                            "bolts": bolts,
                            "contact_cells": [
                                {k: v for k, v in r.items() if k != "axial_law"}
                                for r in state_rows
                                if r["kind"] == "contact"
                            ],
                        }
                    )
    for path, digest in pins.items():
        require(sha(path) == digest, "input changed during calculation")
    write(
        HERE / "top-corner-contact-results.json",
        {
            "schema": "top_corner_coupled_normal_transfer/v1",
            "producer_sha256": sha(Path(__file__)),
            "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
            "cases": cases,
            "assumptions": [
                "One rigid cleat and two fixed host faces, solved together in five restrained modes.",
                "Six simultaneous source lateral wrenches and original nodal self-weight from the original conditional frame scenario; moving side axes preserves their full lateral wrench.",
                "Sixteen exact finished-area centroid contact cells per face, penalty 100 N/mm3, zero initial gaps and no face friction or preload.",
                "Tension-only elastic bolts use the existing steel-plus-two-wood-seat law, proposed 177.8 mm grips and explicit nominal washer dimensions.",
                "Affine edge pressure extrapolates the solved face motion; cell quadrature and rigid hosts are conditional approximations, not bounds on local wood stress.",
            ],
            "limits": [
                "Source lateral forces, original cleat self-weight and host motion are held fixed. New gross stiffness, extra cleat weight and six-case frame redistribution remain open.",
                "No lateral clearance/slip, nonlinear crushing, washer metal/bending or thread/head/nut qualification is provided.",
                "Normal forces share through both faces; this does not establish full coupled lateral/normal timber behavior, splitting or complete joint resistance.",
            ],
            "whole_frame_redistribution_recomputed": False,
            "complete_joint_acceptance": False,
            "reviewed_geometry_changed": False,
            "physical_release": False,
        },
    )
    print("Coupled local corner states:", len(cases))
    for block in accounting.BLOCK_HOSTS:
        subset = [c for c in cases if c["block"] == block]
        print(
            block,
            "statuses",
            sorted({c["status"] for c in subset}),
            "peak bolt tension N",
            max(b["force_n"] for c in subset for b in c["bolts"]),
            "peak face pressure MPa",
            max(
                f["affine_peak_pressure_at_face_edge_mpa"]
                for c in subset
                for f in c["faces"]
            ),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "solve"))
    stage = parser.parse_args().stage
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(
            read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
            "shared analysis slot occupied",
        )
        (prepare if stage == "prepare" else solve)()
