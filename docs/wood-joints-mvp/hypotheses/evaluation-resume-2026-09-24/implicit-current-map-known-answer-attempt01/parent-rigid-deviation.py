#!/usr/bin/env python3
"""Compare rigid-limit and linearized fields; this is not an elastic error bound."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "ordinary-port-motion-attempt09-common-map"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calculate():
    mass = json.loads((HERE / "parent-mass-reference.json").read_text())
    rigid = json.loads((HERE / "parent-rigid-reference.json").read_text())
    assert rigid["mass_reference_sha256"] == sha(HERE / "parent-mass-reference.json")
    assert sha(SOURCE / "mesh.inp") == mass["source_sha256"]["mesh.inp"]
    assert sha(SOURCE / "nut-coupling.json") == "568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960"
    body = json.loads((SOURCE / "mesh.json").read_text())["bodies"][mass["body"]]
    ids = sorted(body["nodes"])
    wanted = set(ids)
    nodes = {}
    mode = None
    for line in (SOURCE / "mesh.inp").read_text().splitlines():
        if line.startswith("*"):
            if not line.startswith("**"):
                mode = line.split(",")[0].upper()
        elif mode == "*NODE":
            row = line.split(",")
            if int(row[0]) in wanted:
                nodes[int(row[0])] = [float(v) for v in row[1:]]
    assert set(nodes) == wanted
    xyz = np.array([nodes[n] for n in ids])
    center = np.array(mass["centroid_mm"])
    pivot = np.array(mass["pivot_from_native_control_coordinate_mm"])
    direction = np.cross([0.,1.,0.], xyz-pivot)
    nut = json.loads((SOURCE / "nut-coupling.json").read_text())["per_nut"][0]
    fit = nut["least_squares_rigid_motion_fit"]
    index = {n:i for i,n in enumerate(ids)}
    fit_index = [index[n] for n in fit["node_ids"]]
    coefficients = np.array(fit["fit_coefficients_u0_then_theta"])
    assert coefficients.shape == (6, 3*len(fit_index))
    rows = []
    for state in rigid["states"]:
        u = np.array(state["centroid_displacement_mm"]) + (xyz-center) @ np.array(state["rotation_matrix_minus_identity"]).T
        v = np.array(state["centroid_velocity_mm_s"]) + (xyz-center) @ np.array(state["velocity_coefficient_matrix_per_s"]).T
        linear_u = direction*state["linearized_theta_rad"]
        linear_v = direction*state["linearized_omega_rad_s"]
        qu, qv = [coefficients @ a[fit_index].ravel() for a in (u,v)]
        qlu, qlv = [coefficients @ a[fit_index].ravel() for a in (linear_u,linear_v)]
        rows.append({"increment":state["increment"], "time_s":state["time_s"],
            "max_component_rigid_minus_linear_U_mm":np.max(abs(u-linear_u),axis=0).tolist(),
            "max_component_rigid_minus_linear_V_mm_s":np.max(abs(v-linear_v),axis=0).tolist(),
            "fitted_rigid_REF_ROT_U":qu.tolist(), "fitted_rigid_REF_ROT_V":qv.tolist(),
            "fitted_linear_REF_ROT_U":qlu.tolist(), "fitted_linear_REF_ROT_V":qlv.tolist(),
            "control_U_difference":(qu-qlu).tolist(), "control_V_difference":(qv-qlv).tolist()})
    return {"schema":"parent_rigid_linearized_field_comparison/v1",
        "status":"OFFLINE_RIGID_LIMIT_COMPARISON_ONLY", "physical_node_count":len(ids),
        "rigid_reference_sha256":sha(HERE / "parent-rigid-reference.json"),
        "mass_reference_sha256":sha(HERE / "parent-mass-reference.json"),
        "fit_source_sha256":sha(SOURCE / "nut-coupling.json"),
        "maximum_centroid_radius_mm":float(np.linalg.norm(xyz-center,axis=1).max()),
        "control_order":["REF_U1","REF_U2","REF_U3","ROT_U1","ROT_U2","ROT_U3"],
        "states":rows, "native_execution":False, "joint_acceptance":False,
        "limits":"Finite rigid-limit versus linearized fields only. This neither bounds elastic FE discrepancy nor verifies native constraints, mass reduction or outputs. REF/ROT are the original weighted linear fit, not an assumed exact rigid-body angle."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = calculate()
    target = HERE / "parent-rigid-deviation.json"
    rendered = json.dumps(data,indent=2,sort_keys=True)+"\n"
    if args.write:
        with target.open("x") as stream:
            stream.write(rendered)
    else:
        assert target.read_text() == rendered
    print(json.dumps({"status":data["status"],"terminal":data["states"][-1]}))
