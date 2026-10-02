"""Static requirements for unadopted panel corner restraints; no frame solve."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(PARENT))
import frame_state_contract as contract

FRAME = PARENT / "corner-frame-attempt01"
SOURCE = PARENT / "two-receiver-frame-attempt03"
PANELS = ("main_upper_left", "main_upper_right", "main_lower_left", "main_lower_right")
X = np.array([1.0, 0.0, 0.0])
T = np.array([0.0, 0.6427876096865394, 0.7660444431189781])
N = np.cross(X, T)
BASIS = np.array([X, T, N])
WIDTH = 20.0
THICKNESS = 18.25625
AXIAL = "non_qualifying_parametric_screw_withdrawal"
LATERAL = "panel_screw_lateral_plane"
AUTHORITY = {
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def regions(model, panel):
    points = np.array(
        [
            model["physical_node_coordinates_mm"][str(i)]
            for i in model["body_nodes"][panel]
        ]
    )
    local = points @ BASIS.T
    lo, hi = local.min(axis=0), local.max(axis=0)
    require(abs(hi[2] - lo[2] - THICKNESS) < 1e-6, "changed plywood thickness")
    center = points.mean(axis=0)
    records, columns = [], []
    for xi, ti in ((0, 0), (1, 0), (0, 1), (1, 1)):
        bx, bt = (hi if xi else lo)[0], (hi if ti else lo)[1]
        x, t = (
            bx + (1 if xi == 0 else -1) * WIDTH / 2,
            bt + (1 if ti == 0 else -1) * WIDTH / 2,
        )
        mid = (lo[2] + hi[2]) / 2
        specs = (
            ("front", [x, t, lo[2]], N, WIDTH**2),
            ("X_edge", [bx, t, mid], X * (1 if xi == 0 else -1), WIDTH * THICKNESS),
            ("T_edge", [x, bt, mid], T * (1 if ti == 0 else -1), WIDTH * THICKNESS),
        )
        for role, point_local, direction, area in specs:
            point = np.array(point_local) @ BASIS
            records.append(
                {
                    "corner": len(records) // 3,
                    "role": role,
                    "point_global_mm": point.tolist(),
                    "point_X_T_N_mm": point_local,
                    "force_direction_on_panel": direction.tolist(),
                    "bearing_area_mm2": area,
                }
            )
            columns.append(
                np.r_[-direction, -np.cross(point - center, direction) / 1000]
            )
    return records, np.array(columns).T


def run(output):
    require(
        output.parent == HERE / "results" and not output.exists(),
        "choose a fresh results child",
    )
    pins = {
        SOURCE
        / "comparison.json": "0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5",
        SOURCE
        / "response.npz": "774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52",
    }
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed current source: {path}")
    comparison = read(SOURCE / "comparison.json")
    scope = contract.force_state_scope(comparison)
    for name in ("model.json", "row-identities.json", "operators.npz"):
        path = FRAME / name
        pins[path] = comparison["source_sha256"][str(path.relative_to(ROOT))]
    pins[SOURCE / "producer.py.snapshot"] = comparison["producer_sha256"]
    pins[Path(contract.__file__)] = (
        "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5"
    )
    pins.update({ROOT / name: digest for name, digest in AUTHORITY.items()})
    pins[Path(__file__)] = sha(Path(__file__))
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed input: {path}")
    model, rows = read(FRAME / "model.json"), read(FRAME / "row-identities.json")
    require(
        len(rows) == 1888 and len(model["body_names"]) == 50, "changed source census"
    )
    states = comparison["states"]
    require(
        len(states) == 12
        and {(s["case_id"], s["gap_scale"]) for s in states}
        == {(case, gap) for case in contract.CASES for gap in (0, 1)},
        "incomplete source",
    )
    panels, results = {}, []
    with (
        np.load(FRAME / "operators.npz", allow_pickle=False) as operators,
        np.load(SOURCE / "response.npz", allow_pickle=False) as saved,
    ):
        D = operators["D"]
        for panel in PANELS:
            block = model["body_names"].index(panel) * 6
            screw = [
                r["row"]
                for r in rows
                if r["ownership"]["role"] in (AXIAL, LATERAL)
                and panel
                in (r["ownership"]["first_body"], r["ownership"]["second_body"])
            ]
            axial = [i for i in screw if rows[i]["ownership"]["role"] == AXIAL]
            require(
                len(screw) == 36 and len(axial) == 12, "changed panel screw inventory"
            )
            require(
                np.max(np.abs(D[axial, block : block + 3] + N)) < 1e-8,
                "withdrawal sign differs",
            )
            contacts = [
                r["row"]
                for r in rows
                if r["ownership"]["role"] == "timber_or_panel_contact"
                and panel
                in (r["ownership"]["first_body"], r["ownership"]["second_body"])
                and np.linalg.norm(np.cross(D[r["row"], block : block + 3], N)) < 1e-8
                and D[r["row"], block : block + 3] @ N > 1 - 1e-8
            ]
            require(
                contacts and np.max(np.abs(D[contacts, block : block + 3] - N)) < 1e-8,
                "back-face contact sign differs",
            )
            require(
                all(
                    rows[i]["law"]["intended_law"] == "compression_only"
                    for i in contacts
                ),
                "face contact is not compression-only",
            )
            changed = screw + contacts
            other = [
                r["row"]
                for r in rows
                if r["row"] not in changed
                and np.any(np.abs(D[r["row"], block : block + 6]) > 1e-12)
            ]
            region, keeper = regions(model, panel)
            matrix = np.c_[keeper, D[contacts, block : block + 6].T]
            require(np.linalg.matrix_rank(matrix) == 6, "proposal wrench rank differs")
            count = matrix.shape[1]
            limits = np.zeros((4, count + 1))
            for corner in range(4):
                limits[corner, corner * 3 : corner * 3 + 3] = 1
            limits[:, -1] = -1
            panels[panel] = {
                "regions": region,
                "source_screw_rows": screw,
                "back_face_rows": contacts,
                "unchanged_other_rows": other,
            }
            for state in states:
                case, gap = state["case_id"], state["gap_scale"]
                force = saved[f"{case}_{'zero' if gap == 0 else 'gap'}_raw_force_n"]
                require(
                    force.shape == (1888,) and np.isfinite(force).all(),
                    "invalid source force",
                )
                target = D[changed, block : block + 6].T @ force[changed]
                # ponytail: six-equation free-body statics only; no stiffness or receiver solve.
                solution = linprog(
                    np.r_[np.zeros(count), 1],
                    A_ub=limits,
                    b_ub=np.zeros(4),
                    A_eq=np.c_[matrix, np.zeros(6)],
                    b_eq=target,
                    bounds=[(0, None)] * (count + 1),
                    method="highs",
                )
                require(
                    solution.success,
                    f"proposal statics infeasible: {panel}/{case}/{gap}",
                )
                allocated, peak = solution.x[:-1], float(solution.fun)
                residual = matrix @ allocated - target
                dual = float(target @ solution.eqlin.marginals)
                require(
                    max(abs(residual[:3])) < 1e-6
                    and 1000 * max(abs(residual[3:])) < 1e-3
                    and min(allocated) >= -1e-7
                    and max(limits @ solution.x) < 1e-7
                    and abs(peak - dual) < 1e-5,
                    "LP witness/primal/dual mismatch",
                )
                keeper_force = allocated[:12].reshape(4, 3)
                results.append(
                    {
                        "panel": panel,
                        "case_id": case,
                        "gap_scale": gap,
                        "minimum_largest_corner_L1_force_n": peak,
                        "corner_front_Xedge_Tedge_forces_n": keeper_force.tolist(),
                        "maximum_front_mean_pressure_mpa": float(
                            keeper_force[:, 0].max() / WIDTH**2
                        ),
                        "maximum_edge_mean_pressure_mpa": float(
                            keeper_force[:, 1:].max() / (WIDTH * THICKNESS)
                        ),
                        "source_panel_wrench_n_nmm": (
                            -target * [1, 1, 1, 1000, 1000, 1000]
                        ).tolist(),
                        "unchanged_other_panel_wrench_n_nmm": (
                            -D[other, block : block + 6].T
                            @ force[other]
                            * [1, 1, 1, 1000, 1000, 1000]
                        ).tolist(),
                        "source_maximum_screw_withdrawal_n": float(force[axial].max()),
                        "allocated_back_face_forces_n": allocated[12:].tolist(),
                        "force_residual_n": float(max(abs(residual[:3]))),
                        "moment_residual_nmm": float(1000 * max(abs(residual[3:]))),
                        "dual_objective_n": dual,
                    }
                )
    require(len(results) == 48, "proposal state census differs")
    for path, digest in pins.items():
        require(sha(path) == digest, f"source changed during calculation: {path}")
    output.mkdir(parents=True)
    report = {
        "schema": "unadopted_panel_edge_restraint_static_proposal/v1",
        "source_force_state_scope": scope,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "main_panels": panels,
        "states": results,
        "panel_states": 48,
        "front_margin_mm": WIDTH,
        "kicker_screws_separate": 18,
        "source_main_panel_screw_count": 48,
        "source_total_panel_screw_count": 66,
        "new_frame_solve": False,
        "keeper_geometry_defined": False,
        "compatible_allocation": False,
        "receiver_balance_evaluated": False,
        "new_bearing_resistance_assigned": False,
        "physical_release": False,
        "geometry_changed": False,
        "hardware_changed": False,
    }
    write(output / "result.json", report)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "panel_states": len(results),
                "optimistic_corner_L1_peak_n": max(
                    r["minimum_largest_corner_L1_force_n"] for r in results
                ),
                "result_sha256": sha(output / "result.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=HERE / "results/edge-restraint-attempt01"
    )
    run(parser.parse_args().output.resolve())
