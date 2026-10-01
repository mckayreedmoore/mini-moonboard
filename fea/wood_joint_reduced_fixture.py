"""Small known-answer tests of the reused static spring/MPC/gap methods.

Preparation never launches a solver. The parent runner requires a separate
exact-freeze review and explicit coordinator call. No joint is represented.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fea import horizontal_panel_frame as frame
from fea.current_response_model import directional_connector
from fea.current_response_run import configure_radial_clearance, physical_forces
from fea.round_insert_frame import normal_contact
from fea.wood_joint_reduced_native import freeze, write_json


def build():
    model = frame.Structure()
    owners, checks = {}, []
    axis = np.array([1., 2., 3.]) / np.sqrt(14.)
    stiffness = {"axial_n_per_mm": 1000., "lateral_n_per_mm": 500.}
    point = [7., 11., 13.]
    free, ground = model.node(point), model.node(point)
    model.fixed.add(ground)
    owner = {"first": "rotated_free", "second": "ground", "point": point, "axis": axis.tolist()}
    directional_connector(model, free, ground, stiffness, "rotated", owner)
    owners["rotated"] = owner
    force = np.array([10., -20., 30.])
    model.loads[free] = force
    basis = np.asarray(owner["force_basis"])
    expected = basis.T @ ((basis @ force) / np.array([1000., 500., 500.]))
    checks.append({"name": "rotated", "node": free, "expected_u_mm": expected.tolist(),
                   "expected_force_on_first_n": (-force).tolist()})

    point = [21., 25., 29.]
    free, ground = model.node(point), model.node(point)
    model.fixed.add(ground)
    model.equations.extend([[(free, 1, 1.)], [(free, 2, 1.)]])
    normal_contact(model, "normal", free, [ground], [1.], point, [0., 0., 1.], 1000.)
    owners["normal"] = {"first": "compression_free", "second": "ground", "point": point,
                         "scalar_normal": [0., 0., 1.]}
    model.loads[free] = np.array([0., 0., -100.])
    checks.append({"name": "normal", "node": free, "expected_u_mm": [0., 0., -.1],
                   "expected_force_on_first_n": [0., 0., 100.]})

    point = [31., 37., 41.]
    ground, free = model.node(point), model.node(point)
    model.fixed.add(ground)
    owner = {"first": "ground", "second": "radial_free", "point": point, "axis": axis.tolist()}
    directional_connector(model, ground, free, stiffness, "radial", owner)
    owners["radial"] = owner
    normal = np.array([.6, .8])
    local_force = np.array([0., 60., 80.])
    basis = np.asarray(owner["force_basis"])
    model.loads[free] = basis.T @ local_force
    for spring in model.springs:
        if spring["name"] == "radial" and spring["dof"] in (2, 3):
            spring.update(radial_clearance_assumption=True, radial_clearance_mm=1.15)
    configure_radial_clearance(model, {"radial": normal}, model.loads)
    expected = basis.T @ np.array([0., *(normal * (1.15 + 100. / 500.))])
    checks.append({"name": "radial", "node": free, "expected_u_mm": expected.tolist(),
                   "expected_force_on_first_n": (basis.T @ local_force).tolist()})
    # Numpy values are converted before recording the frozen JSON.
    model.loads = {n: np.asarray(f).tolist() for n, f in model.loads.items()}
    metadata = {
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "Three disconnected known-answer static method fixtures only; no candidate joint",
        "connection_ownership": owners, "checks": checks,
        "tolerances": {"displacement_abs_mm": 2e-6, "physical_force_abs_n": .002},
        "documentation": {"url": "https://www.dhondt.de/ccx_2.23.pdf",
            "section": "6.2.41 SPRING2; keyword EQUATION, SPRING, NODE PRINT",
            "interpretation": "Scalar spring displacement components are projected by linear MPCs; an imposed gap reference load is removed when recovering physical spring force."},
        "limits": ["Active branches only, not active-set convergence or stability of a frame",
                   "No member/panel constitutive qualification or physical fastener capacity",
                   "Auxiliary local CLOAD values are not global physical external loads"],
    }
    return model, metadata


def assess(directory):
    directory = Path(directory)
    record = json.loads((directory / "model.json").read_text())
    data = (directory / "model.dat").read_text()
    native = frame.panel_kernel.read_blocks(data)
    assessed = frame.assess(record, data)
    recovered = physical_forces(record, assessed, frame.displacement_roundoff(data))
    results = []
    for check in record["checks"]:
        u = np.asarray(native["displacements"][check["node"]])
        f = np.asarray(recovered[check["name"]]["force_on_first_xyz_n"])
        displacement_error = float(np.max(np.abs(u - check["expected_u_mm"])))
        force_error = float(np.max(np.abs(f - check["expected_force_on_first_n"])))
        results.append({**check, "observed_u_mm": u.tolist(), "observed_force_on_first_n": f.tolist(),
            "displacement_error_mm": displacement_error, "physical_force_error_n": force_error,
            "passed": bool(displacement_error <= record["tolerances"]["displacement_abs_mm"]
                           and force_error <= record["tolerances"]["physical_force_abs_n"])})
    result = {"checks": results, "mpc_audit": assessed["mpc_printed_precision_audit"],
        "normal_compression_sign_passed": assessed["closed_bearing_assumption_passed"],
        "passed": all(r["passed"] for r in results) and assessed["mpc_check_passed"]
                  and assessed["closed_bearing_assumption_passed"],
        "limits": record["limits"], "mechanical_acceptance": False}
    write_json(directory / "result.json", result)
    return result


def build_body_gravity():
    """Exact quadratic axial displacement of a uniform hanging/compressed bar."""
    from fea.wood_joint_reduced_body_loads import add_body_self_weight

    model = frame.Structure()
    model.member({"name": "gravity_bar", "start": [0., 0., 0.], "end": [0., 0., 1000.],
                  "section_u": [1., 0., 0.], "width_mm": 100., "depth_mm": 50.}, size=200.)
    model.fixed.update(model.members["gravity_bar"]["sections"][0.])
    applied = add_body_self_weight(model, "gravity_bar", 2.5, [0., 0., 500.])
    checks = []
    # nu=0 permits exactly zero transverse motion, including the fixed face.
    # EA*u''=q; u(0)=0, EA*u'(L)=0 gives u=-q*z*(L-z/2)/EA.
    for node, point in model.nodes.items():
        z = point[2]
        expected = -(2.5*9.80665/1000.)*z*(1000.-z/2.)/(7000.*5000.)
        checks.append({"node": node, "expected_u_mm": [0., 0., expected]})
    model.loads = {n: np.asarray(f).tolist() for n, f in model.loads.items()}
    metadata = {"candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "Known-answer C3D20 consistent self-weight fixture only; no candidate joint",
        "checks": checks, "expected_total_reaction_n": [0., 0., 2.5*9.80665],
        "tolerances": {"displacement_abs_mm": 2e-8, "reaction_abs_n": .002},
        "body_load_check": {k: v for k, v in applied.items() if k != "loads"},
        "documentation": {"url": "https://www.dhondt.de/ccx_2.23.pdf",
            "method": "C3D20 with standard elastic solid, nodal CLOAD and NODE PRINT U/RF; consistent shape-function gravity integrates an exactly representable quadratic displacement"},
        "limits": ["Zero-Poisson isotropic prismatic gravity field only",
                   "Does not qualify conditional timber/panel properties or local hardware mass condensation"]}
    return model, metadata


def assess_body_gravity(directory):
    from fea.wood_joint_reduced_native import digest, verify

    directory = Path(directory)
    verify(directory, check_live=False)
    execution = json.loads((directory/"execution.json").read_text())
    if execution.get("returncode") != 0 or not execution.get("container_confirmed_terminal"):
        raise ValueError("Gravity fixture did not complete successfully")
    for name, expected in execution["outputs_sha256"].items():
        if digest(directory/name) != expected:
            raise ValueError("Gravity fixture output changed")
    record = json.loads((directory/"model.json").read_text())
    output = frame.panel_kernel.read_blocks((directory/"model.dat").read_text())
    error = max(float(np.max(np.abs(np.asarray(output["displacements"][row["node"]])-row["expected_u_mm"])))
                for row in record["checks"])
    external_rf = sum((np.asarray(output["forces"][n]) for n in record["fixed_nodes"]), np.zeros(3))
    fixed_cload = sum((np.asarray(record["loads"].get(str(n), [0., 0., 0.]))
                       for n in record["fixed_nodes"]), np.zeros(3))
    # Pinned 2.23 manual pp.398/568: RF includes CLOAD at constrained nodes.
    # This fixture uses nodal loads only, with no DLOAD or MPC reactions.
    reaction = external_rf-fixed_cload
    reaction_error = float(np.max(np.abs(reaction-record["expected_total_reaction_n"])))
    result = {"maximum_displacement_error_mm": error, "reaction_error_n": reaction_error,
        "observed_total_reaction_n": reaction.tolist(),
        "printed_fixed_node_rf_sum_n": external_rf.tolist(),
        "fixed_node_cload_sum_n": fixed_cload.tolist(),
        "reaction_recovery": "RF minus the applied CLOAD at fixed nodes; no DLOAD or MPC in this fixture",
        "manual_reference": {"url": "https://www.dhondt.de/ccx_2.23.pdf", "pdf_pages": [398, 568],
            "sha256": "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"},
        "postprocessor_sha256": digest(__file__),
        "passed": error <= record["tolerances"]["displacement_abs_mm"]
            and reaction_error <= record["tolerances"]["reaction_abs_n"],
        "limits": record["limits"], "native_solve_executed": True, "mechanical_acceptance": False}
    write_json(directory/"result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "assess"))
    parser.add_argument("directory")
    args = parser.parse_args()
    if args.mode == "prepare":
        structure, metadata = build()
        freeze(args.directory, structure, metadata, [__file__])
        print("Frozen three static method fixtures; no native solve launched")
    else:
        print(json.dumps(assess(args.directory), indent=2))
