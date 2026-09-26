"""Audit the first converged cleat COM response point from a frozen snapshot.

This reads a completed FRD snapshot and the frozen C3D10 mesh. It runs no
solver and imports no CAD. The Gmsh API is used only by the existing
`dynamic_momentum` reference-mesh integrator to build two mass operators.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from fea.dynamic_momentum import calculix_221_mass, consistent_mass, momentum
from fea.wood_joint_mesh_jacobian_audit import parse_c3d10_deck


ROOT = Path.cwd().resolve()
if not (ROOT / "fea").is_dir():
    raise RuntimeError("Run from the repository root")
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SNAPSHOT = BASE / "ordinary-transient-first-increment-snapshot-attempt01"
PILOT = BASE / "ordinary-transient-pilot-attempt03"
OUT = BASE / "ordinary-transient-first-momentum-audit-attempt01"
TIME = 0.0025
WOOD_ID = "W00_BOTTOM_CENTER_RIGHT_CLEAT"
RHO_TONNE_MM3 = 6.0e-10
GMSH_IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, name: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{name} hash mismatch: {actual} != {expected}")
    return actual


def parse_density(materials_path: Path) -> float:
    lines = materials_path.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip().upper() == "*MATERIAL,NAME=WOOD_ELASTIC_DIAGNOSTIC":
            for j in range(i + 1, len(lines)):
                if lines[j].strip().upper() == "*DENSITY":
                    value = float(lines[j + 1].strip())
                    if not math.isfinite(value) or value <= 0:
                        raise ValueError("Wood density must be positive and finite")
                    return value
                if lines[j].strip().startswith("*MATERIAL,"):
                    break
    raise ValueError("WOOD_ELASTIC_DIAGNOSTIC density was not found")


def parse_amplitude(deck_path: Path, target_time: float) -> tuple[list[tuple[float, float]], float, float]:
    lines = deck_path.read_text().splitlines()
    try:
        start = next(i for i, row in enumerate(lines) if row.upper() == "*AMPLITUDE,NAME=RAMP_N") + 1
    except StopIteration as error:
        raise ValueError("RAMP_N amplitude card is absent") from error
    samples = []
    for line in lines[start:]:
        if line.startswith("*"):
            break
        fields = [float(value.strip()) for value in line.split(",")]
        if len(fields) != 2 or not all(map(math.isfinite, fields)):
            raise ValueError("Malformed RAMP_N sample")
        samples.append((fields[0], fields[1]))
    if len(samples) != 101 or samples[0] != (0.0, 0.0):
        raise ValueError("Unexpected sampled RAMP_N table")
    if any(a[0] >= b[0] for a, b in zip(samples, samples[1:])):
        raise ValueError("RAMP_N sample times are not strictly increasing")

    def value_at(t: float) -> float:
        for (t0, a0), (t1, a1) in zip(samples, samples[1:]):
            if t0 <= t <= t1:
                return a0 + (a1 - a0) * ((t - t0) / (t1 - t0))
        raise ValueError(f"Time {t} is outside RAMP_N")

    knots = [(t, a) for t, a in samples if t < target_time]
    knots.append((target_time, value_at(target_time)))
    if not knots or knots[0][0] != 0.0:
        raise ValueError("RAMP_N does not start at zero")
    impulse_factor = math.fsum((t1 - t0) * (a0 + a1) * 0.5
                               for (t0, a0), (t1, a1) in zip(knots, knots[1:]))
    return samples, value_at(target_time), impulse_factor


def parse_cload(deck_path: Path, cleat_nodes: set[int], principal_nodes: set[int]) -> dict[int, tuple[float, float, float]]:
    lines = deck_path.read_text().splitlines()
    try:
        start = next(i for i, row in enumerate(lines) if row.upper() == "*CLOAD,AMPLITUDE=RAMP_N") + 1
    except StopIteration as error:
        raise ValueError("RAMP_N CLOAD card is absent") from error
    loads: dict[int, list[float]] = {}
    count = 0
    for line in lines[start:]:
        if line.startswith("*"):
            break
        fields = [part.strip() for part in line.split(",")]
        if len(fields) != 3:
            raise ValueError("Malformed CLOAD row")
        node, dof, value = int(fields[0]), int(fields[1]), float(fields[2])
        if dof not in (1, 2, 3) or not math.isfinite(value):
            raise ValueError("Invalid CLOAD degree or value")
        row = loads.setdefault(node, [0.0, 0.0, 0.0])
        row[dof - 1] += value
        count += 1
    if count != 662:
        raise ValueError(f"Unexpected physical CLOAD coefficient count: {count}")
    cleat = {node: tuple(value) for node, value in loads.items() if node in cleat_nodes}
    principal = {node: tuple(value) for node, value in loads.items() if node in principal_nodes}
    if len(cleat) != 151:
        raise ValueError(f"Unexpected loaded cleat node count: {len(cleat)}")
    if len(principal) != 180 or len(loads) != 331 or set(loads) != set(cleat) | set(principal):
        raise ValueError("CLOAD ownership differs from the cleat/principal actuator patches")
    return {node: tuple(value) for node, value in loads.items()}


def parse_frd_fields(path: Path, selected_nodes: set[int], target_time: float) -> dict[str, dict[int, tuple[float, float, float]]]:
    wanted = {"DISP": ("D1", "D2", "D3"), "VELO": ("V1", "V2", "V3")}
    result: dict[str, dict[int, tuple[float, float, float]]] = {}
    time = None
    expected_count = None
    active: str | None = None
    labels: list[str] = []
    rows: dict[int, tuple[float, float, float]] = {}
    seen: set[int] = set()
    target_count = None

    with path.open("rt", encoding="ascii", errors="strict") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.startswith("  100CL"):
                if active is not None:
                    raise ValueError(f"Unterminated FRD field before line {line_number}")
                parts = line.split()
                time, expected_count = float(parts[2]), int(parts[3])
                if not math.isfinite(time) or expected_count <= 0:
                    raise ValueError("Invalid FRD time/count")
                continue

            if line.startswith(" -4  "):
                if active is not None:
                    raise ValueError(f"Nested FRD field at line {line_number}")
                parts = line.split()
                field = parts[1]
                if field in wanted and time is not None and math.isclose(time, target_time, rel_tol=0.0, abs_tol=1e-12):
                    if field in result:
                        raise ValueError(f"Duplicate {field} block at target time")
                    if expected_count != 116162:
                        raise ValueError(f"Unexpected {field} node count {expected_count}")
                    active = field
                    labels = []
                    rows = {}
                    seen = set()
                    target_count = expected_count
                else:
                    active = "SKIP"
                continue

            if active is None:
                continue
            if line.startswith(" -5"):
                labels.append(line.split()[1])
            elif line.startswith(" -1"):
                node = int(line[3:13])
                values = [float(line[i:i + 12]) for i in range(13, len(line), 12) if line[i:i + 12].strip()]
                if active == "SKIP":
                    continue
                if node in seen or len(values) != 3 or not all(map(math.isfinite, values)):
                    raise ValueError(f"Invalid {active} node vector at line {line_number}")
                seen.add(node)
                if node in selected_nodes:
                    rows[node] = tuple(values)
            elif line.startswith(" -3"):
                if active != "SKIP":
                    if tuple(labels[:3]) != wanted[active] or len(seen) != target_count:
                        raise ValueError(f"Incomplete {active} labels or node coverage")
                    if set(rows) != selected_nodes:
                        raise ValueError(f"Incomplete selected-node {active} coverage")
                    result[active] = rows
                active = None
                if set(result) == set(wanted):
                    break

    if active is not None or set(result) != set(wanted):
        raise ValueError("Missing or incomplete target-time DISP/VELO fields")
    return result


def dot(left: tuple[float, float, float] | list[float], right: tuple[float, float, float] | list[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right))


def weighted_field(nodes: dict[int, tuple[float, float, float]], blocks: dict, field: dict[int, tuple[float, float, float]]) -> tuple[float, tuple[float, float, float]]:
    mass_terms = []
    component_terms = [[], [], []]
    for node_ids, block in blocks.values():
        for i, node_id in enumerate(node_ids):
            nodal_mass = math.fsum(block[i])
            mass_terms.append(nodal_mass)
            for axis in range(3):
                component_terms[axis].append(nodal_mass * field[node_id][axis])
    mass = math.fsum(mass_terms)
    value = tuple(math.fsum(component_terms[axis]) / mass for axis in range(3))
    return mass, value


def summarize_operator(name: str, blocks: dict, nodes: dict[int, tuple[float, float, float]], u: dict, v: dict,
                       direction: list[float]) -> dict:
    state = momentum(nodes, blocks, u, v)
    mass_u, u_com = weighted_field(nodes, blocks, u)
    mass_x, x_com = weighted_field(nodes, blocks, nodes)
    if not (math.isclose(mass_u, state["mass"], rel_tol=1e-12) and math.isclose(mass_x, state["mass"], rel_tol=1e-12)):
        raise ValueError(f"{name}: inconsistent integrated mass")
    p_n = dot(state["linear_momentum"], direction)
    return {
        "operator": name,
        "mass_tonne": state["mass"],
        "mass_kg": state["mass"] * 1000.0,
        "reference_com_xyz_mm": list(x_com),
        "displacement_com_xyz_mm": list(u_com),
        "displacement_com_n_mm": dot(u_com, direction),
        "velocity_com_xyz_mm_per_s": [p / state["mass"] for p in state["linear_momentum"]],
        "velocity_com_n_mm_per_s": p_n / state["mass"],
        "momentum_com_xyz_ns": list(state["linear_momentum"]),
        "momentum_com_n_ns": p_n,
        "kinetic_energy_nmm": state["kinetic_energy"],
    }


def main() -> None:
    snapshot_path = SNAPSHOT / "snapshot.json"
    snapshot_sha = require_hash(
        snapshot_path,
        "82db7e5ccb0ad52d54a2b2c32499e6cac55b6cfb637fa2f6777a34b549f9d88f",
        "snapshot metadata",
    )
    snapshot_meta = json.loads(snapshot_path.read_text())
    snapshot_freeze_path = SNAPSHOT / "input-freeze.json"
    freeze_sha = require_hash(snapshot_freeze_path, snapshot_meta["source_input_freeze_sha256"], "snapshot input freeze")
    frd_path = SNAPSHOT / "pilot.frd"
    frd_sha = require_hash(frd_path, snapshot_meta["files"]["pilot.frd"]["sha256"], "snapshot FRD")
    if snapshot_meta["target_time_seconds"] != TIME or snapshot_meta["mechanical_acceptance"]:
        raise ValueError("Snapshot target/scope differs from the requested firstpoint audit")

    freeze = json.loads(snapshot_freeze_path.read_text())
    for key, expected in {
        "mesh.inp": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
        "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
        "materials.inp": "e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb",
        "pilot.inp": "29c23fddf0800d8808ef9c28cea93caf4d019719aa68a3f089a7dd09d7870e4c",
        "actuator.json": "cc452f06600b72e576616adcd16f521c38f8bdfdcc7d90029f4eee0fb461b9a7",
    }.items():
        if freeze["artifacts_sha256"].get(key) != expected:
            raise ValueError(f"Frozen input record changed for {key}")
    if Path(snapshot_meta["source_directory"]).name != PILOT.name:
        raise ValueError("Snapshot source directory differs from frozen native03 pilot")
    pilot_dir = PILOT
    mesh_path = pilot_dir / "mesh.inp"
    report_path = pilot_dir / "mesh.json"
    materials_path = pilot_dir / "materials.inp"
    deck_path = pilot_dir / "pilot.inp"
    actuator_path = pilot_dir / "actuator.json"
    actual_source_hashes = {
        "mesh.inp": require_hash(mesh_path, freeze["artifacts_sha256"]["mesh.inp"], "frozen mesh deck"),
        "mesh.json": require_hash(report_path, freeze["artifacts_sha256"]["mesh.json"], "frozen mesh report"),
        "materials.inp": require_hash(materials_path, freeze["artifacts_sha256"]["materials.inp"], "frozen materials"),
        "pilot.inp": require_hash(deck_path, freeze["artifacts_sha256"]["pilot.inp"], "frozen pilot deck"),
        "actuator.json": require_hash(actuator_path, freeze["artifacts_sha256"]["actuator.json"], "frozen actuator"),
    }
    mesh_report = json.loads(report_path.read_text())
    if mesh_report["bodies"][WOOD_ID]["mesh_element_type"] != "C3D10":
        raise ValueError("Cleat is not the expected C3D10 body")
    expected_bodies = frozenset(mesh_report["bodies"])
    all_nodes, all_bodies = parse_c3d10_deck(mesh_path, expected_body_ids=expected_bodies, elset_prefix="")
    body_report = mesh_report["bodies"][WOOD_ID]
    principal_report = mesh_report["bodies"]["W02_BASE_PRINCIPAL_CENTER_RIGHT"]
    element_ids = set(body_report["elements"])
    body_elements = all_bodies[WOOD_ID]
    if set(body_elements) != element_ids:
        raise ValueError("Cleat element ownership differs from the frozen mesh report")
    element_nodes = {n for conn in body_elements.values() for n in conn}
    report_nodes = set(body_report["nodes"])
    if element_nodes != report_nodes:
        raise ValueError("Cleat node ownership differs from frozen C3D10 connectivity")
    nodes = {node: all_nodes[node] for node in report_nodes}
    elements = body_elements

    density = parse_density(materials_path)
    if not math.isclose(density, RHO_TONNE_MM3, rel_tol=0.0, abs_tol=1e-22):
        raise ValueError("Unexpected current elastic timber density scenario")
    if freeze["initial_velocity"] != "zero by solver default" or freeze["direct_fixed_increment"]:
        raise ValueError("Initial condition/increment contract changed")
    deck = deck_path.read_text()
    if "*DYNAMIC,ALPHA=0" not in deck or "EXPLICIT" in deck.upper() or "*MASS" in deck.upper():
        raise ValueError("Step no longer matches the implicit, unscaled source-mass scope")

    actuator = json.loads(actuator_path.read_text())
    direction = [float(value) for value in actuator["direction_global_xyz"]]
    amplitude_samples, amplitude_end, impulse_factor = parse_amplitude(deck_path, TIME)
    principal_nodes = set(principal_report["nodes"])
    load_unit_all = parse_cload(deck_path, report_nodes, principal_nodes)
    cleat_load_unit = {node: row for node, row in load_unit_all.items() if node in report_nodes}
    principal_load_unit = {node: row for node, row in load_unit_all.items() if node in principal_nodes}
    force_unit_xyz = [math.fsum(row[axis] for row in cleat_load_unit.values()) for axis in range(3)]
    principal_force_unit_xyz = [math.fsum(row[axis] for row in principal_load_unit.values()) for axis in range(3)]
    pair_force_unit_xyz = [a + b for a, b in zip(force_unit_xyz, principal_force_unit_xyz)]
    force_unit_n = dot(force_unit_xyz, direction)
    if not math.isclose(force_unit_n, 1.0, rel_tol=0.0, abs_tol=2e-12):
        raise ValueError(f"Cleat load resultant is not +1 N along N: {force_unit_n}")
    force_end_n = amplitude_end * force_unit_n
    discrete_impulse_ns = 0.5 * TIME * force_end_n  # Newmark firststep endpoint trapezoid; F(0)=0.
    continuous_impulse_ns = impulse_factor * force_unit_n

    fields = parse_frd_fields(frd_path, report_nodes | set(load_unit_all), TIME)
    u, v = fields["DISP"], fields["VELO"]
    native_blocks = calculix_221_mass(elements, nodes, density)
    gauss8_blocks = consistent_mass(elements, nodes, density, "Gauss8")
    native = summarize_operator("CalculiX 2.21 source-reconstructed four-point C3D10 mass", native_blocks, nodes, u, v, direction)
    physical = summarize_operator("physical consistent C3D10 mass, Gmsh Gauss8", gauss8_blocks, nodes, u, v, direction)

    cleat_q_mm = math.fsum(dot(cleat_load_unit[node], u[node]) for node in cleat_load_unit)
    principal_q_mm = math.fsum(dot(principal_load_unit[node], u[node]) for node in principal_load_unit)
    pair_q_mm = cleat_q_mm + principal_q_mm
    cleat_step_work_nmm = 0.5 * force_end_n * cleat_q_mm
    pair_step_work_nmm = 0.5 * force_end_n * pair_q_mm
    com_free_velocity_mm_s = discrete_impulse_ns / native["mass_tonne"]
    beta = 0.25
    com_free_displacement_mm = beta * TIME * TIME * force_end_n / native["mass_tonne"]
    cad = body_report["imported_cad"]
    gauss5_volume = body_report["integrated_mesh_audit"]["integrated_mesh_volume_mm3"]

    report = {
        "schema": "wood_joint_first_transient_cleat_momentum_audit/v1",
        "scope": "The first completed .0025 s increment only; no full-pilot response or acceptance claim.",
        "snapshot": {
            "snapshot_json_sha256": snapshot_sha,
            "snapshot_input_freeze_sha256": freeze_sha,
            "snapshot_frd_sha256": frd_sha,
            "target_time_seconds": TIME,
            "snapshot_source_process_still_running": snapshot_meta["source_process_still_running"],
            "frd_node_count_per_field": 116162,
            "frd_fields": ["DISP", "VELO"],
        },
        "frozen_inputs_sha256": actual_source_hashes,
        "helpers_sha256": {
            "audit.py": sha256_file(Path(__file__)),
            "dynamic_momentum.py": sha256_file(ROOT / "fea/dynamic_momentum.py"),
            "wood_joint_mesh_jacobian_audit.py": sha256_file(ROOT / "fea/wood_joint_mesh_jacobian_audit.py"),
            "dynamic_momentum_qualification.md": sha256_file(ROOT / "docs/history/dynamic-momentum-qualification.md"),
            "gmsh_integration_image": GMSH_IMAGE,
        },
        "mesh_and_material": {
            "wood_elset": WOOD_ID,
            "element_type": body_report["mesh_element_type"],
            "element_count": len(elements),
            "node_count": len(nodes),
            "density_tonne_per_mm3": density,
            "density_scenario_kg_per_m3": density * 1e12,
            "mesh_audit_gauss5_volume_mm3": gauss5_volume,
            "mesh_audit_gauss5_mass_tonne": gauss5_volume * density,
            "source_cad_volume_mm3": cad["volume_mm3"],
            "source_cad_centroid_xyz_mm": cad["centroid_global_xyz_mm"],
            "mass_operators": [native, physical],
        },
        "applied_load_first_increment": {
            "direction_global_xyz": direction,
            "time_step_seconds": TIME,
            "ramp_sample_count_total": len(amplitude_samples),
            "amplitude_at_t0": 0.0,
            "amplitude_at_endpoint": amplitude_end,
            "cleat_unit_force_resultant_xyz_n": force_unit_xyz,
            "cleat_unit_force_resultant_N_n": force_unit_n,
            "principal_unit_force_resultant_xyz_n": principal_force_unit_xyz,
            "paired_global_unit_force_residual_xyz_n": pair_force_unit_xyz,
            "cleat_endpoint_force_N_n": force_end_n,
            "native_newmark_endpoint_trapezoid_impulse_Ns": discrete_impulse_ns,
            "continuous_piecewise_linear_sampled_ramp_impulse_Ns": continuous_impulse_ns,
            "discrete_minus_continuous_impulse_Ns": discrete_impulse_ns - continuous_impulse_ns,
            "continuous_impulse_relative_error_vs_discrete": (discrete_impulse_ns / continuous_impulse_ns) - 1.0,
            "native_free_body_endpoint_velocity_N_mm_per_s": com_free_velocity_mm_s,
            "native_free_body_endpoint_displacement_N_mm": com_free_displacement_mm,
            "firstpoint_cleat_load_weighted_displacement_mm": cleat_q_mm,
            "firstpoint_pair_load_weighted_displacement_mm": pair_q_mm,
            "firstpoint_principal_load_weighted_displacement_mm": principal_q_mm,
            "firstpoint_cleat_nodal_endpoint_trapezoid_work_Nmm": cleat_step_work_nmm,
            "firstpoint_pair_nodal_endpoint_trapezoid_work_Nmm": pair_step_work_nmm,
            "native_operator_momentum_minus_discrete_impulse_Ns": native["momentum_com_n_ns"] - discrete_impulse_ns,
        },
        "limits": [
            "The four-point operator is the source-reconstructed untransformed CalculiX 2.21 C3D10 reference mass; current contact-path mass transformations are not qualified by this firstpoint audit.",
            "Gauss8 is the separate physical consistent reference-volume operator; report it separately from the solver-source four-point operator.",
            "The no-contact free-body terms are checks only. Actual cleat momentum differs by contact and other momentum-transfer impulses; initial X/T wood-face normals carry no N component only while their planar normals remain undeformed.",
            "No assumption equates the actuator patch coordinate q with cleat COM translation. Load work is assembled over the actual cleat CLOAD nodes.",
            "This is one first increment only. It does not establish time accuracy, stiffness, capacity, convergence of the remainder, or joint acceptance.",
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    native_row, gauss8_row = report["mesh_and_material"]["mass_operators"]
    readme = f"""# First transient cleat momentum audit — attempt 01

This post-processes only the immutable native03 first-converged snapshot at
`t={TIME:.4f} s`. It hashes and checks the frozen current mesh/deck/materials,
then integrates the W00 cleat's C3D10 mass and the raw FRD `DISP`/`VELO` fields.
It runs no solver and imports no CAD. The Gmsh use is mesh-only quadrature.

The mesh contains {len(elements):,} cleat C3D10 elements and {len(nodes):,}
owned nodes. The frozen wood density is {density:.9g} tonne/mm³ (the 600 kg/m³
elastic scenario). The source-CAD reference centroid is
`{cad['centroid_global_xyz_mm'][0]:.9f}, {cad['centroid_global_xyz_mm'][1]:.9f}, {cad['centroid_global_xyz_mm'][2]:.9f} mm`;
the source volume is `{cad['volume_mm3']:.6f} mm³`.

The applied cleat force is the serialized CLOAD patch's `{force_end_n:.9g} N`
endpoint resultant along N. The exact Newmark endpoint-trapezoid impulse for
this increment is `{discrete_impulse_ns:.9g} N·s`; the exact integral of the
sampled piecewise-linear input ramp is `{continuous_impulse_ns:.9g} N·s`.
Those differ because the native step spans amplitude knots. Compare the
firstpoint body momentum against the **discrete** impulse plus contact/reaction
impulse corrections; do not treat the continuous-ramp integral as the native
one-step balance target.

| Mass operator | Mass (kg) | COM N displacement (mm) | COM N velocity (mm/s) | COM N momentum (N·s) |
| --- | ---: | ---: | ---: | ---: |
| CalculiX 2.21 source-reconstructed four-point | {native_row['mass_kg']:.12g} | {native_row['displacement_com_n_mm']:.12g} | {native_row['velocity_com_n_mm_per_s']:.12g} | {native_row['momentum_com_n_ns']:.12g} |
| Physical consistent C3D10 Gauss8 | {gauss8_row['mass_kg']:.12g} | {gauss8_row['displacement_com_n_mm']:.12g} | {gauss8_row['velocity_com_n_mm_per_s']:.12g} | {gauss8_row['momentum_com_n_ns']:.12g} |

For a free cleat with zero initial motion, the four-point mass and the first
Newmark endpoint force predict `{com_free_velocity_mm_s:.12g} mm/s` and
`{com_free_displacement_mm:.12g} mm` at the endpoint. The loaded pilot is not a
free body: all omitted contact impulse enters its body balance, and the initial
wood-face normals (X/T) suppress N only as long as those planar normals remain
unrotated. Bore-wall or rotated/deformed contact normals can contribute N.
The observed four-point COM momentum differs from the discrete applied impulse
by `{native['momentum_com_n_ns'] - discrete_impulse_ns:.6g} N·s`. This firstpoint
net closure does not show that individual contact impulses are zero; they may
cancel and require the separately recorded contact-force audit.

The serialized `q` is an actuator patch observation, not the cleat COM motion.
The reported center-of-mass fields integrate the actual C3D10 interpolation
with element mass matrices; no equal-node averaging is used. The nodal
actuator projection for the full force pair is `{pair_q_mm:.12g} mm`;
its firstpoint endpoint-trapezoid work is `{pair_step_work_nmm:.12g} N·mm`
(`{cleat_step_work_nmm:.12g} N·mm` from the cleat-side loads). This is the
actual serialized CLOAD shape applied to FRD U, separately from COM motion.

The native four-point operator follows the CalculiX 2.21 source reconstruction
recorded in [`dynamic-momentum-qualification.md`](../../../../history/dynamic-momentum-qualification.md).
Its archived controls do not qualify transformed contact mass for this model;
the physical Gauss8 result is deliberately reported separately. Hashes and
full values are in [`report.json`](report.json); the executable method is
[`audit.py`](audit.py).
"""
    (OUT / "README.md").write_text(readme)
    print(json.dumps({
        "report": str((OUT / "report.json").relative_to(ROOT)),
        "sha256": sha256_file(OUT / "report.json"),
        "native_operator": native_row,
        "physical_gauss8": gauss8_row,
        "firstpoint_load": report["applied_load_first_increment"],
    }, indent=2))


if __name__ == "__main__":
    main()
