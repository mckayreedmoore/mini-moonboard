"""Isolate panel-normal load sharing with fixed receiving members.

Compare a rigid plate and the saved elastic plywood operator at both screw
counts. This explicitly simplified benchmark removes frame motion, in-plane
connector reactions and panel-seam constraints. It cannot replace the frame.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import simple_frame as solver
import top_corner_actions as accounting


def branch(H, D, e, W, k):
    return solver.solve_branch(H, D, e, W, k, np.ones(len(k), dtype=bool),
                              np.empty((0, 2), dtype=int), np.empty(0, dtype=bool))


def known_answer():
    D = np.array([[1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]], dtype=float)
    for W, expected in (([800, 0, 0], [200, 200, 200, 200]),
                        ([800, 400, 0], [100, 100, 300, 300])):
        f, _, q, _ = branch(np.zeros((4, 4)), D, np.zeros(4), np.array(W), np.full(4, 1000.0))
        np.testing.assert_allclose(f, expected, atol=1e-5)
        np.testing.assert_allclose(q, f / 1000, atol=1e-8)
    return "PASS_FOUR_TIES_CENTERED_AND_ECCENTRIC_LOAD"


def run(operators, output):
    require, read, sha = accounting.require, accounting.read, accounting.sha
    require(not output.exists(), "preserve earlier benchmark")
    assessment = read(operators / "operator-assessment.json")
    paths = [operators / "panel-benchmark.npz", operators / "row-identities.json", Path(__file__), Path(solver.__file__)]
    pins = {p: sha(p) for p in paths}
    for name in ("panel-benchmark.npz", "row-identities.json"):
        require(sha(operators / name) == assessment["output_sha256"][name], "changed benchmark operator")
    rows = read(operators / "row-identities.json")
    baseline = read(HERE.parent / "corner-frame-attempt01/frame-results.json")
    with np.load(operators / "panel-benchmark.npz", allow_pickle=False) as data:
        indices, H, D, e, W = [data[k].copy() for k in ("indices", "H", "D", "e", "W")]
    selected = [rows[int(i)] for i in indices]
    k = np.array([r["law"]["stiffness_N_per_mm"] for r in selected])
    axial = np.array([r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal" for r in selected])
    old = indices < assessment["old_scalar_row_count"]
    results = []
    for count, mask in ((12, old), (20, np.ones(len(old), dtype=bool))):
        ids = np.flatnonzero(mask)
        local_D = D[ids]
        _, values, Vt = np.linalg.svd(local_D, full_matrices=False)
        rank = int(np.count_nonzero(values > values[0] * 1e-10))
        require(rank == 3, "panel normal support must span three rigid motions")
        basis = Vt[:rank].T
        projected_D = local_D @ basis
        ties = axial[ids]
        require(int(ties.sum()) == count, "benchmark screw census changed")
        for elastic in (False, True):
            local_H = (H[np.ix_(ids, ids)] + H[np.ix_(ids, ids)].T) / 2 if elastic else np.zeros((len(ids), len(ids)))
            for case_index, source in enumerate(baseline["cases"]):
                work = assessment["dead_load_factor"] * W[:, 2 * case_index] + W[:, 2 * case_index + 1]
                load_e = assessment["dead_load_factor"] * e[ids, 2 * case_index] + e[ids, 2 * case_index + 1] if elastic else np.zeros(len(ids))
                f, _, q, iterations = branch(local_H, projected_D, load_e, basis.T @ work, k[ids])
                balance = local_D.T @ f - basis @ (basis.T @ work)
                force_residual = float(np.max(abs(balance[:3])))
                moment_residual = float(1000 * np.max(abs(balance[3:])))
                law_residual = float(np.max(abs(f - k[ids] * np.maximum(q, 0))))
                require(force_residual <= 0.1 and moment_residual <= 2 and law_residual <= 0.1 and f.min() >= -0.1 and q.max() <= 10, "benchmark equilibrium/law/domain failed")
                local_ties = np.flatnonzero(ties)
                worst = int(local_ties[np.argmax(f[local_ties])])
                results.append({
                    "main_panel_screws": count, "panel_elastic": elastic,
                    "case_id": source["case_id"], "panel": "main_upper_left",
                    "peak_withdrawal_n": float(f[worst]),
                    "axis_id": selected[int(ids[worst])]["row_id"].split("/")[0],
                    "total_screw_tension_n": float(f[ties].sum()),
                    "total_face_compression_n": float(f[~ties].sum()),
                    "peak_screw_opening_mm": float(q[ties].max()),
                    "audit": {"normal_subspace_force_residual_n": force_residual,
                              "normal_subspace_moment_residual_nmm": moment_residual,
                              "spring_law_residual_n": law_residual, "qp_iterations": iterations},
                    "discarded_rigid_load_components_n_and_knmm": (work - basis @ (basis.T @ work)).tolist(),
                })
    for p, h in pins.items():
        require(sha(p) == h, "benchmark input changed")
    output.mkdir(parents=True)
    report = {"schema": "fixed_receiver_panel_normal_benchmark/v1",
              "known_answer": known_answer(), "states": results,
              "source_sha256": {str(p.relative_to(accounting.ROOT)): h for p, h in pins.items()},
              "limits": ["Receivers fixed; floor/frame movement, panel-seam reactions and in-plane connector reactions omitted.",
                         "Elastic case retains panel response to full frozen load vector but constrains only normal translation/bending rigid load components.",
                         "Rigid case omits panel elastic strain and retains the same normal load/moments, contact locations and spring laws.",
                         "Benchmark is a diagnostic sensitivity, not an adopted force allocation or Hillman product qualification."]}
    (output / "comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    for count in (12, 20):
        for elastic in (False, True):
            state = max((s for s in results if s["main_panel_screws"] == count and s["panel_elastic"] == elastic), key=lambda s: s["peak_withdrawal_n"])
            print(count, "elastic" if elastic else "rigid", state["case_id"], round(state["peak_withdrawal_n"], 3), "N", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operators", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.operators.resolve(), args.output.resolve())
