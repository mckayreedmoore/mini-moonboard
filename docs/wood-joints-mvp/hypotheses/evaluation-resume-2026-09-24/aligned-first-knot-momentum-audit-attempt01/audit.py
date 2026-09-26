"""Post-process the immutable aligned-100N first-knot snapshot.

This is a bounded C3D10 mass/momentum audit of the W00 cleat only. It runs no
solver, does not load CAD, and keeps the actuator observation q separate from
the cleat center-of-mass displacement.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

from fea.dynamic_momentum import calculix_221_mass, momentum
from fea.wood_joint_mesh_jacobian_audit import parse_c3d10_deck


ROOT = Path.cwd().resolve()
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SNAPSHOT_DIR = BASE / "ordinary-transient-aligned-first-knot-snapshot-attempt01"
PILOT_DIR = BASE / "ordinary-transient-seating-100n-aligned-attempt01"
OUT = BASE / "aligned-first-knot-momentum-audit-attempt01"
FIRST_AUDIT_HELPER = BASE / "ordinary-transient-first-momentum-audit-attempt01/audit.py"
TIME = 0.001
DT = 0.001
WOOD_ID = "W00_BOTTOM_CENTER_RIGHT_CLEAT"
PRINCIPAL_ID = "W02_BASE_PRINCIPAL_CENTER_RIGHT"
GMSH_IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"

EXPECTED = {
    "snapshot.json": "a91a8412e25c92952ab414e5b65e29cb89a6364a9f114a49fa1ef6c7e81d272e",
    "input-freeze.json": "c3349f42bb8aaa3721e90f8f36ffd823c985ba9e0cffc6d8474b8154e1c5e267",
    "pilot.frd": "452a6eac88fc7aa679172bd7a4274082c1de7516e68985b6a4433dfcedada538",
    "pilot.dat": "9bdf44cb6f7216128e0ba97f0c734011a0f0502b339d840ad99d33195e7b8123",
    "mesh.inp": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "materials.inp": "e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb",
    "pilot.inp": "48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963",
    "actuator.json": "cc452f06600b72e576616adcd16f521c38f8bdfdcc7d90029f4eee0fb461b9a7",
    "dynamic_momentum.py": "f97f0214a8dcd6ae8e539ed3f1377603031776e1b84235bb5dd058e48fd104e3",
    "wood_joint_mesh_jacobian_audit.py": "3f9cb7768f2ba0efb4e5b26f56222422a09048bfe5e1acdf5ded26f749d861c0",
    "first_momentum_audit.py": "f484e6ad94803cac2b92a0ac64745296bd0c1d69afef5b5650a4ca9550250ec1",
    "nut_coupling_rigid_fit.py": "7a8ee3499da7f3f4313162f574e28aeba5cfa6850db6b892c23cfc3de903a113",
}


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


def load_first_audit():
    require_hash(FIRST_AUDIT_HELPER, EXPECTED["first_momentum_audit.py"], "FRD/CLOAD helper")
    spec = importlib.util.spec_from_file_location("pinned_first_momentum_helper", FIRST_AUDIT_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import pinned first-point parser helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vector_sum(rows):
    rows = tuple(rows)
    return [math.fsum(row[i] for row in rows) for i in range(3)]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def apply_geometric_rigid_fit(fit, positions, displacements, owner_loads, owner_force_n, direction):
    node_ids = fit["node_ids"]
    flat_u = [displacements[node][axis] for node in node_ids for axis in range(3)]
    coeff = fit["fit_coefficients_u0_then_theta"]
    generalized = [math.fsum(c * u for c, u in zip(row, flat_u)) for row in coeff]
    translation = generalized[:3]
    rotation = generalized[3:]
    predicted = {}
    residual_norms = []
    for node in node_ids:
        relative = [positions[node][axis] - fit["reference_xyz_mm"][axis] for axis in range(3)]
        rigid_part = [translation[axis] + cross(rotation, relative)[axis] for axis in range(3)]
        predicted[node] = rigid_part
        residual = [displacements[node][axis] - rigid_part[axis] for axis in range(3)]
        residual_norms.append(math.sqrt(math.fsum(value * value for value in residual)))

    actual_work = math.fsum(
        math.fsum(owner_loads[node][axis] * displacements[node][axis] for axis in range(3))
        for node in owner_loads
    )
    rigid_work = math.fsum(
        math.fsum(owner_loads[node][axis] * predicted[node][axis] for axis in range(3))
        for node in owner_loads
    )
    q_actual = actual_work / owner_force_n
    q_rigid = rigid_work / owner_force_n
    q_translation = source_dot(owner_force_n, translation, direction)
    return {
        "fit_weighting": "equal weight per unique owned C3D10 node, including midside and interior nodes; geometric least squares, not mass-weighted and mesh-density dependent",
        "reference_xyz_mm": fit["reference_xyz_mm"],
        "translation_at_reference_xyz_mm": translation,
        "translation_along_N_mm": q_translation,
        "infinitesimal_rotation_xyz_rad": rotation,
        "rotation_contribution_to_owner_actuator_q_mm": q_rigid - q_translation,
        "rigid_fit_actuator_q_mm": q_rigid,
        "actual_work_weighted_owner_q_mm": q_actual,
        "nonrigid_residual_contribution_to_owner_q_mm": q_actual - q_rigid,
        "q_decomposition_residual_mm": q_actual - (q_translation + (q_rigid - q_translation) + (q_actual - q_rigid)),
        "node_displacement_residual_rms_mm": math.sqrt(math.fsum(value * value for value in residual_norms) / len(residual_norms)),
        "node_displacement_residual_max_mm": max(residual_norms),
        "fit_condition_estimate_inf_norm": fit["scaled_design_condition_estimate_inf_norm"],
    }


def source_dot(force_n, translation, direction):
    return math.fsum(a * b for a, b in zip(translation, direction))


def build_rigid_fit(node_ids, all_nodes, displacement, owner_loads, owner_force_n, direction, reference):
    from fea.wood_joint_current_nut_coupling import fit_rigid_motion

    positions = {node: all_nodes[node] for node in node_ids}
    fit = fit_rigid_motion(positions, reference)
    fit["reference_xyz_mm"] = list(reference)
    return apply_geometric_rigid_fit(fit, positions, displacement, owner_loads, owner_force_n, direction)


def main() -> None:
    snapshot_path = SNAPSHOT_DIR / "snapshot.json"
    snapshot_sha = require_hash(snapshot_path, EXPECTED["snapshot.json"], "snapshot metadata")
    snapshot = json.loads(snapshot_path.read_text())
    if snapshot["target_time_seconds"] != TIME or snapshot["mechanical_acceptance"]:
        raise ValueError("Snapshot time or scope differs from the first-knot audit")
    if Path(snapshot["source_directory"]).name != PILOT_DIR.name:
        raise ValueError("Snapshot source directory differs from the aligned pilot")

    freeze_path = SNAPSHOT_DIR / "input-freeze.json"
    freeze_sha = require_hash(freeze_path, EXPECTED["input-freeze.json"], "aligned input freeze")
    freeze = json.loads(freeze_path.read_text())
    if freeze["revision"] != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("Unexpected model revision")
    if freeze["final_amplitude_n"] != 15.625 or freeze["initial_velocity"] != "zero by solver default":
        raise ValueError("Unexpected load scale or initial condition")
    if freeze["restart_write_at_step_end"] is not False:
        raise ValueError("Freeze no longer records the missing-restart limitation")

    # The freeze separates source paths (upstream inputs) from generated run
    # artifacts. For example, its source pilot.inp points to the unscaled
    # parent deck, while artifacts_sha256 pins this aligned run's scaled deck.
    # Verify both maps against their corresponding paths instead of mixing the
    # two hash namespaces.
    source_hashes = {}
    for name, relative in freeze["source_paths"].items():
        expected = freeze.get("source_sha256", {}).get(name)
        if expected is None:
            raise ValueError(f"Frozen source hash missing for {name}")
        path = ROOT / relative
        source_hashes[name] = require_hash(path, expected, f"frozen source {name}")
    artifact_hashes = {}
    for name, expected in freeze["artifacts_sha256"].items():
        artifact_hashes[name] = require_hash(PILOT_DIR / name, expected, f"aligned run artifact {name}")
    for name in ("mesh.inp", "mesh.json", "materials.inp", "pilot.inp", "actuator.json"):
        if artifact_hashes.get(name) != EXPECTED[name]:
            raise ValueError(f"Unexpected pinned current source hash for {name}")

    frd_path = SNAPSHOT_DIR / "pilot.frd"
    dat_path = SNAPSHOT_DIR / "pilot.dat"
    frd_sha = require_hash(frd_path, EXPECTED["pilot.frd"], "snapshot FRD")
    dat_sha = require_hash(dat_path, EXPECTED["pilot.dat"], "snapshot DAT")
    for label, expected_key in (("pilot.frd", "pilot.frd"), ("pilot.dat", "pilot.dat")):
        if snapshot["files"][expected_key]["sha256"] != EXPECTED[label]:
            raise ValueError(f"Snapshot metadata does not pin {label}")

    mesh_report = json.loads((PILOT_DIR / "mesh.json").read_text())
    body_ids = frozenset(mesh_report["bodies"])
    all_nodes, bodies = parse_c3d10_deck(PILOT_DIR / "mesh.inp", expected_body_ids=body_ids, elset_prefix="")
    cleat_report = mesh_report["bodies"][WOOD_ID]
    principal_report = mesh_report["bodies"][PRINCIPAL_ID]
    cleat_nodes = set(cleat_report["nodes"])
    principal_nodes = set(principal_report["nodes"])
    cleat_elements = bodies[WOOD_ID]
    if set(cleat_elements) != set(cleat_report["elements"]):
        raise ValueError("Cleat C3D10 element ownership differs from frozen mesh report")
    element_nodes = {node for conn in cleat_elements.values() for node in conn}
    if element_nodes != cleat_nodes:
        raise ValueError("Cleat C3D10 node ownership differs from frozen mesh report")
    nodes = {node: all_nodes[node] for node in cleat_nodes}

    source = load_first_audit()
    density = source.parse_density(PILOT_DIR / "materials.inp")
    if not math.isclose(density, 6.0e-10, rel_tol=0.0, abs_tol=1e-22):
        raise ValueError("Unexpected current diagnostic timber density")
    deck_text = (PILOT_DIR / "pilot.inp").read_text()
    if "*DYNAMIC,ALPHA=0" not in deck_text or "*MASS" in deck_text.upper() or "EXPLICIT" in deck_text.upper():
        raise ValueError("Input no longer matches the unscaled implicit dynamic scope")

    actuator = json.loads((PILOT_DIR / "actuator.json").read_text())
    direction = [float(value) for value in actuator["direction_global_xyz"]]
    samples, amplitude_end, impulse_factor = source.parse_amplitude(PILOT_DIR / "pilot.inp", TIME)
    loads = source.parse_cload(PILOT_DIR / "pilot.inp", cleat_nodes, principal_nodes)
    cleat_loads = {node: row for node, row in loads.items() if node in cleat_nodes}
    principal_loads = {node: row for node, row in loads.items() if node in principal_nodes}
    # parse_cload groups the serialized component entries into one 3-vector
    # per node: 662 nonzero axis terms are 331 loaded nodes, split 151/180.
    component_terms = sum(value != 0.0 for row in loads.values() for value in row)
    if len(loads) != 331 or component_terms != 662 or len(cleat_loads) != 151 or len(principal_loads) != 180:
        raise ValueError("CLOAD node ownership/count differs from the frozen actuator")
    cleat_force_coeff = vector_sum(cleat_loads.values())
    principal_force_coeff = vector_sum(principal_loads.values())
    cleat_force_coeff_n = source.dot(cleat_force_coeff, direction)
    principal_force_coeff_n = source.dot(principal_force_coeff, direction)
    if not math.isclose(cleat_force_coeff_n, 100.0, rel_tol=0.0, abs_tol=2e-9):
        raise ValueError(f"Unexpected cleat CLOAD reference resultant {cleat_force_coeff_n} N")
    if not math.isclose(principal_force_coeff_n, -100.0, rel_tol=0.0, abs_tol=2e-9):
        raise ValueError(f"Unexpected principal CLOAD reference resultant {principal_force_coeff_n} N")

    fields = source.parse_frd_fields(frd_path, cleat_nodes | principal_nodes | set(loads), TIME)
    u, v = fields["DISP"], fields["VELO"]
    blocks = calculix_221_mass(cleat_elements, nodes, density)
    state = source.summarize_operator("CCX 2.21 four-point C3D10 mass", blocks, nodes, u, v, direction)
    principal_elements = bodies[PRINCIPAL_ID]
    principal_owned_nodes = set(principal_report["nodes"])
    principal_blocks = calculix_221_mass(
        principal_elements,
        {node: all_nodes[node] for node in principal_owned_nodes},
        density,
    )
    principal_state = source.summarize_operator(
        "CCX 2.21 four-point C3D10 mass", principal_blocks,
        {node: all_nodes[node] for node in principal_owned_nodes}, u, v, direction,
    )

    cleat_q_num = math.fsum(source.dot(loads[node], u[node]) for node in cleat_loads)
    principal_q_num = math.fsum(source.dot(loads[node], u[node]) for node in principal_loads)
    cleat_q = cleat_q_num / cleat_force_coeff_n
    principal_q = principal_q_num / principal_force_coeff_n
    pair_q = (cleat_q_num + principal_q_num) / cleat_force_coeff_n

    cleat_fit = build_rigid_fit(
        cleat_nodes, all_nodes, u, cleat_loads, cleat_force_coeff_n,
        direction, state["reference_com_xyz_mm"],
    )
    principal_fit = build_rigid_fit(
        principal_owned_nodes, all_nodes, u, principal_loads, principal_force_coeff_n,
        direction, principal_state["reference_com_xyz_mm"],
    )
    pair_fit_decomposition = {
        "cleat_translation_N_mm": cleat_fit["translation_along_N_mm"],
        "principal_translation_N_mm": principal_fit["translation_along_N_mm"],
        "relative_translation_contribution_mm": (
            cleat_fit["translation_along_N_mm"] - principal_fit["translation_along_N_mm"]
        ),
        "cleat_rotation_contribution_mm": cleat_fit["rotation_contribution_to_owner_actuator_q_mm"],
        "principal_rotation_contribution_mm": principal_fit["rotation_contribution_to_owner_actuator_q_mm"],
        "relative_rotation_contribution_mm": (
            cleat_fit["rotation_contribution_to_owner_actuator_q_mm"]
            - principal_fit["rotation_contribution_to_owner_actuator_q_mm"]
        ),
        "cleat_nonrigid_contribution_mm": cleat_fit["nonrigid_residual_contribution_to_owner_q_mm"],
        "principal_nonrigid_contribution_mm": principal_fit["nonrigid_residual_contribution_to_owner_q_mm"],
        "relative_nonrigid_contribution_mm": (
            cleat_fit["nonrigid_residual_contribution_to_owner_q_mm"]
            - principal_fit["nonrigid_residual_contribution_to_owner_q_mm"]
        ),
        "sum_of_relative_components_mm": (
            cleat_fit["translation_along_N_mm"] - principal_fit["translation_along_N_mm"]
            + cleat_fit["rotation_contribution_to_owner_actuator_q_mm"]
            - principal_fit["rotation_contribution_to_owner_actuator_q_mm"]
            + cleat_fit["nonrigid_residual_contribution_to_owner_q_mm"]
            - principal_fit["nonrigid_residual_contribution_to_owner_q_mm"]
        ),
        "source_work_weighted_pair_q_mm": pair_q,
    }

    force_end_n = cleat_force_coeff_n * amplitude_end
    newmark_impulse_n_s = 0.5 * DT * force_end_n
    continuous_ramp_impulse_n_s = impulse_factor * cleat_force_coeff_n
    impulse_xyz = [0.5 * DT * amplitude_end * value for value in cleat_force_coeff]
    p_n = state["momentum_com_n_ns"]
    p_error_n_s = p_n - newmark_impulse_n_s
    free_velocity_n_mm_s = newmark_impulse_n_s / state["mass_tonne"]
    free_newmark_displacement_n_mm = 0.25 * DT * DT * force_end_n / state["mass_tonne"]
    snapshot_q = snapshot["observation"]["q_mm"]

    report = {
        "schema": "wood_joint_aligned_first_knot_cleat_momentum_audit/v1",
        "scope": "Cleat W00 only at the immutable first aligned ramp knot t=0.001 s; no whole-patch response or acceptance claim.",
        "snapshot": {
            "snapshot_json_sha256": snapshot_sha,
            "input_freeze_sha256": freeze_sha,
            "frd_sha256": frd_sha,
            "dat_sha256": dat_sha,
            "source_process_still_running_at_capture": snapshot["source_process_still_running"],
            "target_time_seconds": TIME,
            "physical_frd_node_count_per_field": 116162,
            "fields": ["DISP", "VELO"],
            "converged_iterations": 25,
        },
        "source_hashes_sha256": source_hashes,
        "run_artifact_hashes_sha256": artifact_hashes,
        "helpers_sha256": {
            "audit.py": sha256_file(Path(__file__)),
            "first_momentum_audit.py": EXPECTED["first_momentum_audit.py"],
            "nut_coupling_rigid_fit.py": require_hash(ROOT / "fea/wood_joint_current_nut_coupling.py", EXPECTED["nut_coupling_rigid_fit.py"], "geometric rigid-fit helper"),
            "dynamic_momentum.py": require_hash(ROOT / "fea/dynamic_momentum.py", EXPECTED["dynamic_momentum.py"], "dynamic momentum helper"),
            "wood_joint_mesh_jacobian_audit.py": require_hash(ROOT / "fea/wood_joint_mesh_jacobian_audit.py", EXPECTED["wood_joint_mesh_jacobian_audit.py"], "mesh parser helper"),
            "gmsh_integration_image": GMSH_IMAGE,
        },
        "cleat_mass_and_state": {
            "body_id": WOOD_ID,
            "element_type": cleat_report["mesh_element_type"],
            "element_count": len(cleat_elements),
            "node_count": len(cleat_nodes),
            "density_tonne_per_mm3": density,
            "mass_tonne": state["mass_tonne"],
            "mass_kg": state["mass_kg"],
            "source_mass_operator": state["operator"],
            "COM_reference_xyz_mm": state["reference_com_xyz_mm"],
            "COM_displacement_xyz_mm": state["displacement_com_xyz_mm"],
            "COM_displacement_N_mm": state["displacement_com_n_mm"],
            "COM_velocity_N_mm_per_s": state["velocity_com_n_mm_per_s"],
            "COM_momentum_xyz_Ns": state["momentum_com_xyz_ns"],
            "COM_momentum_N_Ns": p_n,
            "kinetic_energy_Nmm": state["kinetic_energy_nmm"],
        },
        "principal_mass_and_fit_reference": {
            "body_id": PRINCIPAL_ID,
            "element_count": len(principal_elements),
            "node_count": len(principal_owned_nodes),
            "density_tonne_per_mm3": density,
            "mass_kg": principal_state["mass_kg"],
            "COM_reference_xyz_mm": principal_state["reference_com_xyz_mm"],
            "COM_displacement_N_mm": principal_state["displacement_com_n_mm"],
        },
        "geometric_rigid_fit_decomposition": {
            "fit_definition": "Existing fit_rigid_motion helper from wood_joint_current_nut_coupling.py; infinitesimal 6-DOF LS fit over all unique owned C3D10 nodes with equal node weights; reference is each owner's consistent-mass COM.",
            "cleat": cleat_fit,
            "principal": principal_fit,
            "relative_pair_q_components": pair_fit_decomposition,
        },
        "actuator_and_first_increment": {
            "direction_global_xyz": direction,
            "input_reference_force_each_side_N": 100.0,
            "ramp_amplitude_at_endpoint": amplitude_end,
            "per_side_endpoint_force_N": force_end_n,
            "endpoint_force_pair_resultant_xyz_N": [
                amplitude_end * (a + b) for a, b in zip(cleat_force_coeff, principal_force_coeff)
            ],
            "per_side_CLOAD_coeff_resultant_xyz_N": cleat_force_coeff,
            "serialized_CLOAD_nonzero_component_terms": component_terms,
            "serialized_CLOAD_unique_loaded_nodes": len(loads),
            "paired_CLOAD_coeff_resultant_xyz_N": vector_sum((
                [a + b for a, b in zip(cleat_force_coeff, principal_force_coeff)],
            )),
            "exact_Newmark_first_step_impulse_each_side_Ns": newmark_impulse_n_s,
            "exact_Newmark_first_step_impulse_xyz_Ns": impulse_xyz,
            "continuous_sampled_ramp_impulse_each_side_Ns": continuous_ramp_impulse_n_s,
            "cleat_COM_momentum_minus_applied_impulse_Ns": p_error_n_s,
            "cleat_mean_unaccounted_force_along_N_N": p_error_n_s / DT,
            "cleat_mean_unaccounted_force_along_N_interpretation": (
                "Cleat COM momentum residual divided by the full first increment duration; "
                "an average net unaccounted force term aggregating internal contact/constraint "
                "transfer and solver/output residuals, not an instantaneous or contact-assigned force."
            ),
            "free_cleat_COM_endpoint_velocity_N_mm_per_s": free_velocity_n_mm_s,
            "free_cleat_Newmark_endpoint_displacement_N_mm": free_newmark_displacement_n_mm,
            "cleat_load_work_weighted_displacement_N_mm": cleat_q,
            "principal_load_work_weighted_displacement_N_mm": principal_q,
            "pair_relative_load_work_coordinate_q_mm": pair_q,
            "snapshot_reported_pair_q_mm": snapshot_q,
            "pair_q_minus_snapshot_q_mm": pair_q - snapshot_q,
            "endpoint_force_coeff_source": "Actual 100 N per-side CLOAD resultant from the exact frozen deck multiplied by its linearly interpolated RAMP_N amplitude at t=0.001 s.",
            "no_force_partition_claim": "The per-side actuator nodal CLOAD is known; the contact/bolt/washer force split is not resolved by this cleat-only momentum audit.",
        },
        "limits": [
            "The four-point C3D10 operator is the source-reconstructed untransformed CalculiX 2.21 reference mass, verified here only for the isolated W00 body geometry/material scenario.",
            "This audit computes cleat COM momentum and the source-work-weighted actuator coordinate q separately; q is not cleat COM translation.",
            "Momentum difference from external cleat impulse comprises internal contact and constraint transfer plus solver/output residuals; it is not an assigned contact-force result.",
            "Whole-patch P/H/KE were not recomputed; the existing native run and mesh were not repeated or altered.",
            "The snapshot is a single converged increment from a live process at capture, not the terminal run, time-accuracy validation, or mechanical acceptance.",
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    readme = f"""# Aligned 100 N first-knot cleat momentum audit — attempt 01

This post-processes the immutable first-knot snapshot at `t={TIME:.3f} s`. The
FRD parser verified complete 116,162-node `DISP` and `VELO` blocks, while the
mass integration used only the current W00 cleat's {len(cleat_elements):,}
C3D10 elements and {len(cleat_nodes):,} owned nodes. It used the frozen
600 kg/m³ elastic timber density scenario and the source-reconstructed
CalculiX 2.21 four-point reference mass. No solver or CAD was run.

The exact deck supplies {cleat_force_coeff_n:.9g} N per side before the
piecewise-linear `RAMP_N` factor. At the first knot the amplitude is
`{amplitude_end:.9g}`, giving `{force_end_n:.9g} N` on the cleat. The native
Newmark endpoint-trapezoid impulse is `{newmark_impulse_n_s:.12g} N·s`;
the sampled-ramp integral is `{continuous_ramp_impulse_n_s:.12g} N·s` for
this first linear segment. The paired global resultant is near zero, but this
audit does not assign either side's force to any particular contact.

| Cleat-only quantity | Four-point result |
| --- | ---: |
| Integrated mass | {state['mass_kg']:.9g} kg |
| COM displacement along N | {state['displacement_com_n_mm']:.12g} mm |
| COM velocity along N | {state['velocity_com_n_mm_per_s']:.12g} mm/s |
| COM momentum along N | {p_n:.12g} N·s |
| Momentum minus known cleat external impulse | {p_error_n_s:.12g} N·s |
| Mean unaccounted N-force term over the increment | {p_error_n_s / DT:.12g} N |
| Newmark free-cleat endpoint displacement | {free_newmark_displacement_n_mm:.12g} mm |
| Work-weighted pair coordinate q | {pair_q:.12g} mm |
| Frozen snapshot q observation | {snapshot_q:.12g} mm |
| Relative rigid-fit translation contribution | {pair_fit_decomposition['relative_translation_contribution_mm']:.12g} mm |
| Relative rigid-fit rotation contribution | {pair_fit_decomposition['relative_rotation_contribution_mm']:.12g} mm |
| Relative nonrigid residual contribution | {pair_fit_decomposition['relative_nonrigid_contribution_mm']:.12g} mm |

`q` is reconstructed from the exact nodal CLOAD distribution and FRD
displacements, then normalized by the per-side resultant. It is a relative
actuator coordinate, not W00 COM translation. The remaining cleat momentum
after subtracting its external impulse is an aggregate internal transfer and
numerical residual. Dividing that signed residual by the full first increment
duration gives a mean unaccounted N-force term, not an instantaneous or
contact-assigned force.
The optional decomposition uses the existing infinitesimal rigid-motion
fitter on every unique C3D10 node with equal geometric node weights, not mass
weights. The residual is the fitted-node displacement remainder projected
through the actuator load weights; it is a kinematic split only. The
principal block's scaled-design infinity-norm condition estimate is about
`{principal_fit['fit_condition_estimate_inf_norm']:.3g}`, so its fitted
components deserve extra caution. Each fit is referenced at that body's
consistent-mass COM, but the translation/rotation allocation depends on the
chosen origin and equal-node fit; it is not the mass-weighted COM displacement.
The reported COM displacement and momentum come from consistent C3D10 mass
integration, and the fit pieces are not a unique physical
translation/rotation/deformation partition.

Hashes and full numeric details are in [`report.json`](report.json), and the
reproducible bounded script is [`audit.py`](audit.py). Whole-patch momentum and
energy were intentionally omitted because no serialized whole-patch mass
operator cache was available for this distinct snapshot.
"""
    (OUT / "README.md").write_text(readme)
    print(json.dumps({
        "report_sha256": sha256_file(OUT / "report.json"),
        "audit_py_sha256": sha256_file(Path(__file__)),
        "mass_kg": state["mass_kg"],
        "cleat_COM_displacement_N_mm": state["displacement_com_n_mm"],
        "cleat_COM_momentum_N_Ns": p_n,
        "applied_impulse_Ns": newmark_impulse_n_s,
        "momentum_minus_impulse_Ns": p_error_n_s,
        "pair_q_mm": pair_q,
        "snapshot_q_mm": snapshot_q,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
