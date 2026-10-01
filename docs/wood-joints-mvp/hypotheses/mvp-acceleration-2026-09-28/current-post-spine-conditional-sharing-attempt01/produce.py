"""Bounded prescribed-action calculation; no native solver or frame response."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
PIN = "d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0"
DATUM = np.array([-1219.2, -137.6, 192.475])


def branches(vectors, stiffness, signs, action):
    """Enumerate all finite branches of the convex unilateral spring energy."""
    A, k, s, q = map(np.asarray, (vectors, stiffness, signs, action))
    answers = []
    for bits in itertools.product((False, True), repeat=len(k)):
        active = np.array(bits)
        H = A.T @ np.diag(k * active) @ A
        if np.linalg.matrix_rank(H) < len(q):
            continue
        try:
            u = np.linalg.solve(H, q)
        except np.linalg.LinAlgError:
            continue
        gaps = A @ u
        if any((sg * g < -1e-10 if on else sg * g > 1e-10)
               for sg, g, on in zip(s, gaps, active, strict=True)):
            continue
        signed = k * gaps * active
        if np.max(np.abs(A.T @ signed - q)) > 1e-6:
            continue
        answers.append((u, gaps, signed, active))
    if not answers:
        raise ValueError("No sign-consistent nonsingular branch; stop")
    for answer in answers[1:]:
        if not np.allclose(answer[0], answers[0][0], rtol=1e-8, atol=1e-9):
            raise ValueError("Different compatible states; stop rather than select one")
    return answers[0], len(answers)


def build():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    m = json.loads(raw)
    # Independent scalar known answers: tension k=2, compression k=3.
    for q, expected in [(10., 5.), (-9., -3.)]:
        result, _ = branches([[1.], [1.]], [2., 3.], [1., -1.], [q])
        assert abs(result[0][0] - expected) < 1e-12
    cells = [r for r in m["contact_cell_ownership"]
             if {r["first"], r["second"]} == {"base_post_outer_left", "knee_outer_left_spine"}]
    assert len(cells) == 4
    names, points, stiffness, signs = [], [], [], []
    for i in (1, 2):
        name = f"knee_outer_left_post_{i}/outer-seat-axial-tie"
        owner = m["connection_ownership"][name]
        spring = next(r for r in m["springs"] if r["name"] == name)
        names.append(name); points.append(owner["first_point"])
        stiffness.append(spring["stiffness_n_per_mm"]); signs.append(1.)
    for r in cells:
        assert np.allclose(r["normal_xyz"], [1., 0., 0.])
        names.append(r["name"]); points.append(r["point_xyz_mm"])
        stiffness.append(100. * r["area_mm2"]); signs.append(-1.)
    A = [[1., p[2]-DATUM[2], p[1]-DATUM[1]] for p in points]
    cases = {}
    for label, wrench in {
        "Fx_plus_1N": [1., 0., 0.], "Fx_minus_1N": [-1., 0., 0.],
        "My_plus_1Nm": [0., 1000., 0.], "My_minus_1Nm": [0., -1000., 0.],
        "Mz_plus_1Nm": [0., 0., 1000.], "Mz_minus_1Nm": [0., 0., -1000.],
    }.items():
        # Prescribed JOINT action on spine: Fx=T-C, My=sum dz(T-C), Mz=-sum dy(T-C).
        q = [wrench[0], wrench[1], -wrench[2]]
        try:
            (u, gap, force, active), count = branches(A, stiffness, signs, q)
        except ValueError as exc:
            cases[label] = {"prescribed_joint_action_on_spine_Fx_My_Mz": wrench,
                            "status": "UNRESOLVED", "stop": str(exc)}
            continue
        recovered = np.asarray(A).T @ force
        cases[label] = {
            "prescribed_joint_action_on_spine_Fx_My_Mz": wrench,
            "opening_coordinates_a_b_c": u.tolist(),
            "ties_N": force[:2].tolist(), "contact_compressions_N": (-force[2:]).tolist(),
            "total_tension_N": float(sum(force[:2])),
            "contact_cell_average_pressure_MPa": [float(-f/r["area_mm2"]) for f,r in zip(force[2:], cells, strict=True)],
            "gap_mm": gap.tolist(), "active": active.tolist(),
            "compatible_branch_count": count,
            "max_wrench_residual": float(max(abs(recovered - q))),
        }
    return {"source_sha256": PIN, "datum_mm": DATUM.tolist(), "names": names,
            "stiffness_N_per_mm": stiffness, "coordinates": "gap=a+b*dz+c*dy; a in mm, b/c small angles",
            "scope": "Rigid local post/spine, zero preload/gap, six prescribed interface actions; not frame case demands",
            "method": "64 finite branches; tension-only ties and compression-only four centroid cells; sign and equilibrium guards",
            "known_answer": "Independent scalar +10/2=+5 and -9/3=-3 reproduced",
            "cases": cases, "qualified_for_design": False, "native_solve_executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(); data = build()
    encoded = json.dumps(data, sort_keys=True, indent=2) + "\n"
    out = HERE / "conditional-sharing.json"
    if args.verify:
        assert out.read_text() == encoded
    else:
        out.write_text(encoded)
    for name, row in data["cases"].items():
        print(name, row.get("stop", f"total tie N {row.get('total_tension_N')} closure {row.get('max_wrench_residual')}"))
