"""Freeze a short, gauge-free clearance-motion diagnostic on the current mesh.

This provisional stiff-engagement scenario is not a service-load case. It
retains physical inertia and removes the reference-tangent static gauge.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from fea.wood_joint_current_native_preflight import BASE, ROOT, set_cards, sha

PREFLIGHT_SHA = "630c0819c51e1cdf727c182ba52ebaeacd23d2e8184e21cf5b01bcec4d447e26"
ACTUATOR_SHA = "cc452f06600b72e576616adcd16f521c38f8bdfdcc7d90029f4eee0fb461b9a7"


def numeric(value):
    if not math.isfinite(value):
        raise ValueError("nonfinite solver field")
    token = f"{value:.13e}"
    if len(token) > 20:
        raise ValueError("solver field exceeds f20 width")
    return token


def load_pattern(actuator):
    """Serialize, then audit the forces actually supplied to the solver."""
    lines = ["*CLOAD,AMPLITUDE=RAMP_N"]
    nodes = {}
    for owner in actuator["owner_unit_wrench_distributions"]:
        for row in owner["nodal_forces"]:
            node = row["node_id"]
            if node in nodes:
                raise ValueError("duplicate nodal force owner")
            f = [float(numeric(v)) for v in row["force_xyz_n"]]
            nodes[node] = {"force_xyz_n": f, "point_xyz_mm": row["point_xyz_mm"]}
            lines.extend(
                f"{node},{dof},{numeric(value)}"
                for dof, value in enumerate(f, 1)
                if value != 0.0
            )
    force = np.sum([row["force_xyz_n"] for row in nodes.values()], axis=0)
    moment = np.sum(
        [np.cross(row["point_xyz_mm"], row["force_xyz_n"]) for row in nodes.values()],
        axis=0,
    )
    if np.linalg.norm(force) > 1e-10 or np.linalg.norm(moment) > 1e-8:
        raise ValueError("serialized applied wrench does not close")
    return "\n".join(lines) + "\n", nodes, force.tolist(), moment.tolist()


def contact_pairs(text):
    lines = text.splitlines()
    pairs = []
    for i, line in enumerate(lines):
        if line.upper().startswith("*CONTACT PAIR,"):
            data = next(
                x.strip()
                for x in lines[i + 1 :]
                if x.strip() and not x.startswith("**")
            )
            names = data.split(",")
            if len(names) != 2 or any(not x.strip() or "*" in x for x in names):
                raise ValueError("invalid contact pair")
            pairs.append(tuple(x.strip() for x in names))
    if len(pairs) != 35 or len(set(pairs)) != 35:
        raise ValueError("expected 35 distinct current contact pairs")
    return pairs


def prepare(
    destination,
    *,
    initial_increment_seconds=0.0005,
    direct=False,
    end_seconds=0.025,
    restart_write=False,
    iteration_diagnostics=False,
):
    if not 1e-6 <= initial_increment_seconds <= 0.0025:
        raise ValueError("pilot increment must lie in frozen 1e-6..0.0025 s range")
    if not initial_increment_seconds <= end_seconds <= 0.025:
        raise ValueError(
            "pilot endpoint must include the first increment and not exceed 0.025 s"
        )
    destination = Path(destination).resolve()
    source = BASE / "ordinary-native-preflight-attempt04"
    actuator_path = BASE / "ordinary-seating-actuator-attempt03/actuator.json"
    if (
        sha(source / "input-freeze.json") != PREFLIGHT_SHA
        or sha(actuator_path) != ACTUATOR_SHA
    ):
        raise ValueError("unexpected frozen source")
    old = json.loads((source / "input-freeze.json").read_text())
    actuator = json.loads(actuator_path.read_text())
    names = [
        "mesh.inp",
        "mesh.json",
        "materials.inp",
        "nut-coupling.inp",
        "rigid-carriers.inp",
        "contact-fragment.inc",
        "contact-manifest.json",
        "output-sets.inp",
    ]
    sources = {name: source / name for name in names}
    for name, path in sources.items():
        if sha(path) != old["artifacts_sha256"][name]:
            raise ValueError(f"changed preflight input: {name}")
    if actuator["input_sha256"]["mesh_deck"] != sha(sources["mesh.inp"]):
        raise ValueError("actuator mesh differs")
    sources["nut-coupling.json"] = (
        BASE / "ordinary-nut-coupling-pivot-attempt02/nut-coupling.json"
    )
    nut = json.loads(sources["nut-coupling.json"].read_text())
    if nut["include_file_sha256"] != sha(sources["nut-coupling.inp"]):
        raise ValueError("corrected pivot metadata differs from actual cards")
    sources["actuator.json"] = actuator_path
    sources["preflight-input-freeze.json"] = source / "input-freeze.json"
    sources["producer.py.snapshot"] = Path(__file__)
    cload, nodes, force, moment = load_pattern(actuator)
    if len(nodes) != 331 or len(cload.splitlines()) != 663:
        raise ValueError("unexpected current load patch size")
    controls = [
        n
        for row in old["rigid_carriers"]
        for n in (row["reference_node"], row["rotation_node"])
    ]
    mesh = json.loads(sources["mesh.json"].read_text())
    physical = {n for row in mesh["bodies"].values() for n in row["nodes"]}
    if not set(nodes) <= physical or set(controls) & physical:
        raise ValueError("load or control ownership mismatch")
    sets = set_cards("NSET", "PILOT_MONITOR", [*nodes, *controls])
    sets += set_cards("NSET", "PILOT_ALL_NODES", [*physical, *controls])
    ramp = (
        "*AMPLITUDE,NAME=RAMP_N" + (",TIME=TOTAL TIME" if restart_write else "") + "\n"
    )
    ramp_samples = []
    for i in range(101):
        fraction = i / 100
        ramp += (
            f"{numeric(fraction * 0.1)},{numeric(3 * fraction**2 - 2 * fraction**3)}\n"
        )
        ramp_samples.append(
            (
                float(numeric(fraction * 0.1)),
                float(numeric(3 * fraction**2 - 2 * fraction**3)),
            )
        )
    node_file = "*NODE FILE,NSET=PILOT_ALL_NODES,FREQUENCY=1"
    if iteration_diagnostics:
        node_file += ",LAST ITERATIONS,CONTACT ELEMENTS"
    step = (
        "*STEP,NLGEOM,INC=250\n*DYNAMIC,ALPHA=0"
        + (",DIRECT" if direct else "")
        + f"\n{numeric(initial_increment_seconds)},{numeric(end_seconds)},1e-6,2.5e-3\n"
        + cload
        + node_file
        + "\nU,V\n"
        "*NODE PRINT,NSET=PILOT_MONITOR,FREQUENCY=1\nU\n"
        "*EL PRINT,ELSET=CURRENT_ALL_ELEMENTS,TOTALS=ONLY,FREQUENCY=1\nELSE,ELKE,EMAS,EVOL\n"
        "*EL PRINT,ELSET=CURRENT_NUT_CARRIERS,TOTALS=ONLY,FREQUENCY=1\nELSE,ELKE\n"
        "*CONTACT PRINT,FREQUENCY=1\nCDIS,CSTR,CELS,CNUM\n"
        "*CONTACT FILE,FREQUENCY=1\nCDIS,CSTR,CELS\n"
    )
    for slave, master in contact_pairs(sources["contact-fragment.inc"].read_text()):
        step += (
            f"*CONTACT PRINT,SLAVE={slave},MASTER={master},FREQUENCY=1\nCF,CFN,CFS\n"
        )
    if restart_write:
        step += "*RESTART,WRITE,FREQUENCY=1\n"
    step += "*END STEP\n"
    included = [name for name in names if name.endswith((".inp", ".inc"))]
    deck = "** Gauge-free short transient; diagnostic stiff nut engagement only.\n"
    deck += "".join(f"*INCLUDE,INPUT={name}\n" for name in included)
    deck += "*INCLUDE,INPUT=pilot-sets.inp\n" + ramp + step
    for name in included:
        keywords = {
            line.strip().split(",", 1)[0].upper()
            for line in sources[name].read_text().splitlines()
            if line.strip().startswith("*") and not line.strip().startswith("**")
        }
        if any(
            x in keywords
            for x in (
                "*BOUNDARY",
                "*CLOAD",
                "*DLOAD",
                "*INITIAL CONDITIONS",
                "*FRICTION",
                "*PRE-TENSION",
            )
        ):
            raise ValueError(f"unexpected boundary/load/friction in {name}")
    pins = {name: sha(path) for name, path in sources.items()}
    destination.mkdir(parents=True, exist_ok=False)
    for name, path in sources.items():
        (destination / name).write_bytes(path.read_bytes())
    (destination / "pilot.inp").write_text(deck)
    (destination / "pilot-sets.inp").write_text(sets)
    if pins != {name: sha(path) for name, path in sources.items()}:
        raise ValueError("source changed during freeze")
    report = {
        "schema": "wood_joint_current_transient/v1",
        "status": "FROZEN_NOT_EXECUTED",
        "revision": old["revision"],
        "solver_image": old["solver_image"],
        "source_paths": {
            name: str(path.relative_to(ROOT)) for name, path in sources.items()
        },
        "source_sha256": pins,
        "step_scope": f"Gauge-free {end_seconds:g} s motion diagnostic; 1 N sampled cubic ramp over 0.1 s; provisional stiff engagement, no capacity or quasistatic claim.",
        "static_gauge_omitted": True,
        "initial_velocity": "zero by solver default",
        "ramp_seconds": 0.1,
        "end_seconds": end_seconds,
        "final_amplitude_n": float(
            np.interp(
                end_seconds, [x[0] for x in ramp_samples], [x[1] for x in ramp_samples]
            )
        ),
        "restart_write_at_step_end": restart_write,
        "amplitude_time_basis": "TOTAL TIME" if restart_write else "STEP TIME",
        "iteration_diagnostics": iteration_diagnostics,
        "ramp_interpolation": "101 sampled cubic points, piecewise linear in native solver",
        "initial_increment_seconds": initial_increment_seconds,
        "direct_fixed_increment": direct,
        "maximum_increment_seconds": 0.0025,
        "minimum_increment_seconds": 0.000001,
        "hht_alpha": 0,
        "sampled_travel_stop_mm": 3.0,
        "sampled_controller_rotation_stop_rad": 0.01,
        "sampled_loaded_node_displacement_stop_mm": 5.0,
        "monitor_nodes": sorted([*nodes, *controls]),
        "rotation_nodes": [row["rotation_node"] for row in old["rigid_carriers"]],
        "serialized_unit_load_nodes": nodes,
        "serialized_net_force_n": force,
        "serialized_initial_net_moment_nmm": moment,
        "mechanical_acceptance": False,
        "limits": [
            "The static six-DOF gauge is deliberately omitted: inertia defines free global motion.",
            "Initial mass and zero-displacement tangent audits do not validate dynamic response.",
            "First complete printed increment beyond a sampled motion limit terminates the run; these are not exact event bounds.",
            "Load directions and six-DOF shaft fits are linearized; current moment and fit errors require audit.",
            "Nut display volumes are zero-mass rigid carriers; delivered nut inertia, threads and engagement are unqualified.",
            "No friction, preload, gravity, service-load demand or artificial supporting restraint is added.",
        ],
        "artifacts_sha256": {p.name: sha(p) for p in destination.iterdir()},
    }
    (destination / "input-freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(prepare(parser.parse_args().directory), indent=2))
