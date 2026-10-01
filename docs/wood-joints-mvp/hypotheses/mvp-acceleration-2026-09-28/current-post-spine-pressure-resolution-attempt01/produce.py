"""Fixed-scenario pressure quadrature sensitivity; no native/frame solve."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
MODEL = BASE / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
GEOMETRY = BASE / "reduced-static-attempt01/contact-geometry.json"
PINS = {MODEL: "d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0",
        GEOMETRY: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151"}
SCALE = 50.
DATUM = np.array([-1219.2, -137.6, 192.475])


def solve(A, k, sign, q, initial):
    def forces(u):
        gap = A @ u
        return k * np.where(sign * gap > 0, gap, 0.)
    def residual(u):
        return A.T @ forces(u) - q
    def jac(u):
        active_k = k * (sign * (A @ u) > 0)
        return A.T @ (active_k[:, None] * A)
    answer = least_squares(residual, initial, jac=jac, method="trf", tr_solver="exact",
                           xtol=1e-13, ftol=1e-13, gtol=1e-13, max_nfev=200)
    # Success status alone is insufficient: test physical force/moment residual.
    physical_error = residual(answer.x) * np.array([1., SCALE, SCALE])
    if np.max(abs(physical_error)) > 1e-6:
        raise ValueError(f"Unclosed local action: {physical_error.tolist()}")
    return answer.x, forces(answer.x), float(max(abs(physical_error)))


def build():
    for p, pin in PINS.items():
        assert hashlib.sha256(p.read_bytes()).hexdigest() == pin
    m = json.loads(MODEL.read_text()); geometry = json.loads(GEOMETRY.read_text())
    patch = next(r for r in geometry["contact_patches"]
                 if set(r["member_ids"]) == {"base_post_outer_left", "knee_outer_left_spine"})
    corners = np.array([patch["vertices_xyz_mm"][i] for i in (0, 1, 4, 5)])
    y0, z0 = corners[:, 1:].min(axis=0); y1, z1 = corners[:, 1:].max(axis=0)
    tie_points = []; tie_k = []
    for i in (1, 2):
        name = f"knee_outer_left_post_{i}/outer-seat-axial-tie"
        tie_points.append(m["connection_ownership"][name]["first_point"])
        tie_k.append(next(r["stiffness_n_per_mm"] for r in m["springs"] if r["name"] == name))
    holes = np.array(tie_points)[:, 1:]
    radius = 3.75
    exact_area = (y1-y0)*(z1-z0)-2*np.pi*radius**2
    assert abs(exact_area-13139.962706617787) < 1e-6
    tie_A = np.array([[1., (p[2]-DATUM[2])/SCALE, (p[1]-DATUM[1])/SCALE] for p in tie_points])
    # Independent 1D oracle, compatible with the scaled three-component guard.
    test_A = np.eye(3); test_k = np.array([2., 3., 4.]); test_sign = np.ones(3)
    u, _, _ = solve(test_A, test_k, test_sign, np.array([10., 9., 8.]), np.ones(3))
    assert np.allclose(u, [5., 3., 2.], atol=1e-12)
    rows = []
    previous = {name: np.array([0.001, 0., 0.]) for name in ("My+", "My-", "Mz+", "Mz-")}
    for n in (16, 32, 64, 128, 256, 512):
        yy, zz = np.meshgrid(y0+(np.arange(n)+.5)*(y1-y0)/n,
                              z0+(np.arange(n)+.5)*(z1-z0)/n)
        y, z = yy.ravel(), zz.ravel()
        keep = np.ones(len(y), dtype=bool)
        for hy, hz in holes:
            keep &= (y-hy)**2+(z-hz)**2 >= radius**2
        y, z = y[keep], z[keep]
        cell_area = (y1-y0)*(z1-z0)/n**2
        A = np.vstack((tie_A, np.column_stack((np.ones(len(y)), (z-DATUM[2])/SCALE, (y-DATUM[1])/SCALE))))
        k = np.r_[tie_k, np.full(len(y), 100.*cell_area)]
        sign = np.r_[np.ones(2), -np.ones(len(y))]
        for name, q in {"My+": [0., 20., 0.], "My-": [0., -20., 0.],
                        "Mz+": [0., 0., -20.], "Mz-": [0., 0., 20.]}.items():
            u, f, err = solve(A, k, sign, np.array(q), previous[name])
            # A distinct starting point checks the reported state, not solver status.
            u2, f2, _ = solve(A, k, sign, np.array(q), u + [1e-4, -1e-4, 1e-4])
            assert np.allclose(u, u2, rtol=1e-7, atol=1e-9)
            assert np.max(abs(f[:2]-f2[:2])) < 1e-5
            previous[name] = u
            row = {"grid": n, "case": name, "represented_area_mm2": len(y)*cell_area,
                   "area_error_mm2": len(y)*cell_area-exact_area, "ties_N": f[:2].tolist(),
                   "total_tie_N": float(sum(f[:2])), "max_wrench_residual": err,
                   "peak_sample_pressure_MPa": float(max(-f[2:])/cell_area),
                   "opening_coordinates_scaled_mm": u.tolist()}
            rows.append(row)
        print("grid", n, {r["case"]: round(r["total_tie_N"], 6) for r in rows if r["grid"] == n}, flush=True)
    return {"pins": {str(p.relative_to(BASE)): pin for p,pin in PINS.items()},
            "scipy_version": scipy.__version__, "numpy_version": np.__version__,
            "method_documentation": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html",
            "exact_contact_area_mm2": exact_area, "rows": rows,
            "scope": "Midpoint quadrature excluding two modeled circles, fixed rigid local members, prescribed 1Nm actions only",
            "qualified_for_design": False, "native_solve_executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(); result = build(); out = HERE / "resolution.json"
    if args.verify:
        saved = json.loads(out.read_text())
        assert result["pins"] == saved["pins"]
        for a,b in zip(result["rows"], saved["rows"], strict=True):
            assert a["grid"] == b["grid"] and a["case"] == b["case"]
            assert np.allclose(a["ties_N"], b["ties_N"], rtol=1e-8, atol=1e-7)
    else:
        out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
