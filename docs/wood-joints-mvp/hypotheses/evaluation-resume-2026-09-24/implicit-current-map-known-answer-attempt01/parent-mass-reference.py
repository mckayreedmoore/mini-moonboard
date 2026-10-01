#!/usr/bin/env python3
"""Independent pinned-quadrature mass/load reference; no native execution."""
from pathlib import Path
import argparse
import hashlib
import json
import tarfile
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "ordinary-port-motion-attempt09-common-map"
ARCHIVE = HERE.parent / "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2"
BODY = "M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION"
PINS = {
    "mesh.inp": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "nut-coupling.inp": "af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shape(q):
    bary = np.array([1 - sum(q), *q])
    db = np.array([[-1., -1., -1.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    n = list(bary * (2 * bary - 1))
    dn = list((4 * bary - 1)[:, None] * db)
    for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)):
        n.append(4 * bary[i] * bary[j])
        dn.append(4 * (db[i] * bary[j] + bary[i] * db[j]))
    return np.array(n), np.array(dn)


def quadrature():
    # Literal pinned gauss3d5 coordinates, not rounded substitutes or a higher rule.
    low, high = .138196601125011, .585410196624968
    return np.array([[low, low, low], [high, low, low],
                     [low, high, low], [low, low, high]])


def integrate(x, pivot, rho):
    """x has element/local-node/xyz axes; return local M*d without forming M."""
    n, dn = zip(*(shape(q) for q in quadrature()))
    n, dn = np.array(n), np.array(dn)
    assert np.max(abs(n.sum(axis=1) - 1)) < 2e-15
    assert np.max(abs(dn.sum(axis=1))) < 2e-15
    jac = np.einsum("eia,qib->eqab", x, dn)
    det = np.linalg.det(jac)
    assert np.all(det > 0), float(det.min())
    weights = det / 24.0
    qx = np.einsum("qi,eia->eqa", n, x)
    r = qx - pivot
    direction = np.cross([0., 1., 0.], r)
    local_load = rho * np.einsum("eq,qi,eqa->eia", weights, n, direction)
    volume = float(weights.sum())
    first = np.einsum("eq,eqa->a", weights, qx)
    r2 = np.einsum("eqa,eqa->eq", r, r)
    inertia = rho * (np.eye(3) * np.sum(weights * r2)
                     - np.einsum("eq,eqa,eqb->ab", weights, r, r))
    return {"volume": volume, "mass": rho * volume, "centroid": first / volume,
            "inertia": inertia, "local_load": local_load,
            "min_jacobian": float(det.min()), "max_jacobian": float(det.max())}


def reference():
    for name, digest in PINS.items():
        assert sha(SOURCE / name) == digest, name
    assert sha(ARCHIVE) == "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
    with tarfile.open(ARCHIVE) as archive:
        members = {name: hashlib.sha256(archive.extractfile(
            "./CalculiX/ccx_2.23/src/" + name).read()).hexdigest()
            for name in ("shape10tet.f", "gauss.f", "e_c3d.f")}
    body = json.loads((SOURCE / "mesh.json").read_text())["bodies"][BODY]
    wanted_nodes, wanted_elements = set(body["nodes"]), set(body["elements"])
    nodes, elements = {}, {}
    mode = None
    for line in (SOURCE / "mesh.inp").read_text().splitlines():
        if line.startswith("**") or not line.strip():
            continue
        if line.startswith("*"):
            mode = line.split(",")[0].upper()
            continue
        row = line.split(",")
        if mode == "*NODE" and int(row[0]) in wanted_nodes:
            assert len(row) == 4
            nodes[int(row[0])] = [float(v) for v in row[1:]]
        elif mode == "*ELEMENT" and int(row[0]) in wanted_elements:
            assert len(row) == 11
            elements[int(row[0])] = [int(v) for v in row[1:]]
    assert set(nodes) == wanted_nodes and set(elements) == wanted_elements
    assert {n for row in elements.values() for n in row} == wanted_nodes
    pivot_rows = [line.split(",") for line in (SOURCE / "nut-coupling.inp").read_text().splitlines()
                  if line.startswith("116163,") and len(line.split(",")) == 4]
    assert len(pivot_rows) == 1
    pivot = np.array([float(v) for v in pivot_rows[0][1:]])
    ids = sorted(nodes)
    position = {n: i for i, n in enumerate(ids)}
    index = np.array([[position[n] for n in elements[e]] for e in sorted(elements)])
    xyz = np.array([nodes[n] for n in ids])
    element_xyz = xyz[index]
    midpoint_errors = [np.linalg.norm(element_xyz[:, k] -
                       (element_xyz[:, i] + element_xyz[:, j]) / 2, axis=1)
                       for k, (i, j) in enumerate(((0,1),(1,2),(2,0),(0,3),(1,3),(2,3)), 4)]
    result = integrate(xyz[index], pivot, 7.85e-9)
    load = np.zeros_like(xyz)
    np.add.at(load, index.ravel(), result["local_load"].reshape(-1, 3))
    r = xyz - pivot
    direction = np.cross([0., 1., 0.], r)
    resultant = load.sum(axis=0)
    moment = np.cross(r, load).sum(axis=0)
    expected_resultant = result["mass"] * np.cross([0., 1., 0.], result["centroid"] - pivot)
    expected_moment = result["inertia"][:, 1]
    assert np.max(abs(resultant - expected_resultant)) < 1e-14
    assert np.max(abs(moment - expected_moment)) < 1e-13
    modal_mass = float(np.sum(direction * load))
    assert abs(modal_mass - result["inertia"][1, 1]) < 1e-13
    # Independent polynomial known answer for a unit straight tetrahedron, rho=6.
    corners = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    mids = [(corners[i] + corners[j]) / 2 for i, j in ((0,1),(1,2),(2,0),(0,3),(1,3),(2,3))]
    test = integrate(np.array([list(corners) + mids]), np.zeros(3), 6.)
    assert abs(test["mass"] - 1) < 2e-14
    assert np.max(abs(test["centroid"] - .25)) < 2e-14
    assert np.max(abs(test["inertia"] - (np.eye(3) * .25 - np.ones((3,3)) * .05))) < 2e-14
    dt, c = .001, 1.2
    states = []
    for inc in range(1, 11):
        t = inc * dt
        theta, omega = c * (t**3 / 6 + t * dt**2 / 12), c * t*t / 2
        states.append({"increment": inc, "time_s": t, "theta_rad": theta,
                       "omega_rad_s": omega, "alpha_rad_s2": c*t,
                       "linearized_ELKE_Nmm": .5 * modal_mass * omega**2})
    return {"schema": "parent_current_map_mass_reference/v1",
            "status": "PASS_OFFLINE_QUADRATURE_AND_LINEARIZED_REFERENCE_ONLY",
            "source_sha256": PINS, "solver_source_members_sha256": members,
            "body": BODY, "nodes": len(nodes), "elements": len(elements),
            "pivot_from_native_control_coordinate_mm": pivot.tolist(),
            "density_tonne_mm3": 7.85e-9, "quadrature": quadrature().tolist(),
            "quadrature_weight_each": 1/24, "volume_mm3": result["volume"],
            "mass_tonne": result["mass"], "centroid_mm": result["centroid"].tolist(),
            "inertia_about_pivot_tonne_mm2": result["inertia"].tolist(),
            "minimum_jacobian_mm3": result["min_jacobian"],
            "maximum_jacobian_mm3": result["max_jacobian"],
            "maximum_midside_midpoint_deviation_mm": float(np.max(midpoint_errors)),
            "Md_resultant_for_unit_angular_acceleration": resultant.tolist(),
            "Md_moment_about_pivot_for_unit_angular_acceleration": moment.tolist(),
            "rotation_y_modal_mass_tonne_mm2": modal_mass,
            "maximum_radius_mm": float(np.linalg.norm(r, axis=1).max()),
            "maximum_y_rotation_direction_mm": float(np.linalg.norm(direction, axis=1).max()),
            "unit_tetrahedron_self_check": "PASS_mass_centroid_inertia",
            "linearized_states": states, "native_execution": False,
            "limits": "Pinned discrete quadrature only; not exact curved-element continuum integration, nonlinear response, current-map native validation, carrier acceptance or joint capacity."}, ids, load


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data, ids, load = reference()
    rendered = json.dumps(data, indent=2, sort_keys=True) + "\n"
    target = HERE / "parent-mass-reference.json"
    if args.write:
        with target.open("x") as stream:
            stream.write(rendered)
    else:
        assert target.read_text() == rendered
    print(json.dumps({k: data[k] for k in ("status", "mass_tonne", "volume_mm3", "rotation_y_modal_mass_tonne_mm2")}))
