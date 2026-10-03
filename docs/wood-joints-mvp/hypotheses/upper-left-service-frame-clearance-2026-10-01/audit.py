#!/usr/bin/env python3
"""Independent saved-vector audit of the finite frame clearance comparison."""

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = HERE / "comparison-final.json"
VECTORS = HERE / "response-vectors-final.npz"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
COMP = BASE / "current-frame-connector-compliance-attempt04"
AUTHORITY = {
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    "docs/wood-joints-mvp/criteria.json": "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
    "docs/wood-joints-mvp/current-criteria-coverage.json": "c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c",
    "docs/wood-joints-mvp/authority-integrity.json": "34eab2d747af074cfd21a6247be5136e03b29d8bc7649c0a7e5bd39abdf99399",
}


def digest(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def magnitude(values):
    return float(np.max(np.abs(values), initial=0.0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="compare to the saved audit without writing")
    args = parser.parse_args()
    report = read(REPORT)
    assert digest(REPORT) == "8ab5575e11cb79b7e330131f101e866a985c459454f32da5b5a1b6c93741d883"
    assert digest(VECTORS) == report["vectors_sha256"]
    for path, expected in report["source_sha256"].items():
        assert digest(ROOT / path) == expected, path
    for path, expected in AUTHORITY.items():
        assert digest(ROOT / path) == expected, path
    assert len(read(ROOT / "docs/wood-joints-mvp/current-criteria-coverage.json")["criteria"]) == 47
    authority = read(ROOT / "wood-joints-candidate.json")
    assert authority["release"] is False and not any(authority["release_flags"].values())
    assert report["complete_joint"] == "HOLD" and report["native_run"] is False
    with np.load(VECTORS, allow_pickle=False) as data:
        f, q, a = (data[key] for key in ("f", "q", "a"))
    with np.load(COMP / "operators.npz", allow_pickle=False) as data:
        H, D, e, W = (data[key] for key in ("H", "D", "e", "W"))
    identities = read(COMP / "row-identities.json")
    record = read(COMP / "assessment.json")
    freeze = read(ROOT / "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/freeze.json")
    sources = {case: read(ROOT / paths["response"]["path"]) for case, paths in freeze["cases"].items()}
    assert f.shape == q.shape == (252, 1840) and a.shape == (252, 300)
    loads_e, loads_w = [], []
    for row in report["states"]:
        columns = [c["column"] for c in record["load_columns"] if c["case_id"] == row["case"]]
        loads_e.append(row["effective_load_factor"] * e[:, columns].sum(axis=1))
        loads_w.append(row["effective_load_factor"] * W[:, columns].sum(axis=1))
    compatibility = magnitude(q - (a @ D.T + np.array(loads_e) - f @ H.T))
    equilibrium = magnitude(f @ D - np.array(loads_w))
    assert compatibility < 1e-8 and equilibrium < 1e-6
    unilateral = np.array([i for i, r in enumerate(identities) if r["family"] == "unilateral_springa"])
    bilateral = np.array([i for i, r in enumerate(identities) if r["family"] == "bilateral_spring2" and not 112 <= i < 120])
    k = np.array([r["law"].get("stiffness_N_per_mm", 0.) for r in identities])
    normal_law = magnitude(f[:, unilateral] - k[unilateral] * np.maximum(q[:, unilateral], 0.))
    bilateral_law = magnitude(f[:, bilateral] - k[bilateral] * q[:, bilateral])
    assert normal_law < 1e-4 and bilateral_law < 1e-6
    assert f[:, unilateral].min() >= -1e-6 and q[:, unilateral].max() <= 10
    gap_law, floor_gap, moment_error, fit_error = 0., 0., 0., 0.
    rank_cache = {}
    names = record["body_names_in_rigid_column_order"]
    block = "left_service_outer_upper_cleat"
    block_index = names.index(block)
    datum = np.array([-1085.85, 769.502826578, 1367.736899429])
    for state, row in enumerate(report["states"]):
        inc = sources[row["case"]]["increments"][row["increment"]]
        held_ids = {p["source_row_id"] for p in inc["exact_floor_tangent_reactions"]}
        closed_ids = {p["normal_cell"] for p in inc["exact_floor_tangent_reactions"]}
        held = np.array([i for i in range(1640, 1840) if identities[i]["row_id"] in held_ids])
        released = np.setdiff1d(np.arange(1640, 1840), held)
        closed = np.array([i for i in range(1370, 1470) if identities[i]["row_id"] in closed_ids])
        opened = np.setdiff1d(np.arange(1370, 1470), closed)
        assert f[state, closed].min() > 1e-6 and q[state, closed].min() > 1e-8
        assert q[state, opened].max() < -1e-8 and magnitude(f[state, released]) == 0
        floor_gap = max(floor_gap, magnitude(q[state, held]))
        bearing = list(bilateral) + list(unilateral[f[state, unilateral] > 1e-6]) + list(held)
        for pair in range(4):
            positions = np.arange(112 + 2*pair, 114 + 2*pair)
            displacement = q[state, positions]
            radius = np.linalg.norm(displacement)
            stiffness = row["lateral_stiffness_n_per_mm"]
            if stiffness == "frozen source":
                stiffness = k[positions[0]]
            expected = stiffness * max(1 - row["clearance_mm"] / max(radius, 1e-300), 0.) * displacement
            gap_law = max(gap_law, magnitude(f[state, positions] - expected))
            if row["clearance_mm"] == 0 or np.linalg.norm(f[state, positions]) > 1e-6:
                bearing.extend(positions)
        # Exclude touching/zero-force normals and zero-force gap pairs. D's
        # rank checks rigid mechanisms in this conditional tangent branch;
        # it does not adopt stiffness values or qualify the floor history.
        key = tuple(sorted({int(i) for i in bearing}))
        if key not in rank_cache:
            singular = np.linalg.svd(D[list(key)], compute_uv=False)
            rank_cache[key] = (int(np.count_nonzero(singular > 1e-10*singular[0])), float(singular[-1]))
        assert rank_cache[key][0] == 300
        for host, fit in row["local_interface_projection_fits"].items():
            ports = fit["row_positions"]
            scalar_vectors = D[ports, 6*block_index:6*block_index+3]
            # Construct local motion and moment maps from source world port
            # geometry, independently of the producer's centroid shift.
            arms = np.array([identities[i]["ownership"]["point_mm"] for i in ports]) - datum
            mapping = np.hstack((scalar_vectors, np.cross(arms, scalar_vectors)))
            pose = np.array(fit["cleat_relative_to_host_translation_at_common_datum_mm"]
                            + fit["cleat_relative_to_host_rotation_rad"])
            residual = magnitude(mapping @ pose - q[state, ports])
            fit_error = max(fit_error, abs(residual - fit["maximum_nonrigid_projection_residual_mm"]))
            forces = -scalar_vectors * f[state, ports, None]
            torque = np.cross(arms, forces).sum(axis=0)
            returned = row["simultaneous_interface_wrenches"][host]
            moment_error = max(moment_error, magnitude(torque - np.array(returned["moment_on_cleat_at_common_datum_nmm"])))
        rail = row["local_interface_projection_fits"]["base_rail_service_upper_left"]
        side = row["local_interface_projection_fits"]["base_side_left"]
        relative = np.array(side["cleat_relative_to_host_translation_at_common_datum_mm"]) - np.array(rail["cleat_relative_to_host_translation_at_common_datum_mm"])
        assert magnitude(relative - row["local_fit_rail_relative_to_side_translation_mm"]) < 1e-12
    assert floor_gap < 1e-8 and gap_law < 1e-6 and fit_error < 1e-7 and moment_error < 1e-5
    result = {
        "status": "PASS_SAVED_VECTOR_COMPARISON_CHECKS_ONLY", "states_checked": 252,
        "raw_compatibility_max_error_mm": compatibility, "body_scaled_wrench_max_error_n": equilibrium,
        "normal_force_law_max_error_n": normal_law, "bilateral_force_law_max_error_n": bilateral_law,
        "circular_gap_force_law_max_error_n": gap_law, "held_floor_gap_max_mm": floor_gap,
        "force_bearing_rigid_rank_all_states": 300, "distinct_force_bearing_row_sets": len(rank_cache),
        "minimum_smallest_rigid_singular_value": min(v[1] for v in rank_cache.values()),
        "world_port_moment_rejoin_error_nmm": moment_error,
        "local_projection_fit_residual_recheck_error_mm": fit_error,
        "authority_sha256_unchanged": AUTHORITY, "criteria_count": 47,
        "complete_joint": "HOLD", "native_run": False, "release": False,
        "report_sha256": digest(REPORT), "vectors_sha256": digest(VECTORS),
        "initial_producer_snapshot": "/tmp/upper-left-service-frame-clearance-initial-0ph7j9ef",
    }
    output = HERE / "parent-validation.json"
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert output.read_text() == rendered, "saved audit differs"
    else:
        assert not output.exists(), "preserve existing validation evidence"
        output.write_text(rendered)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
