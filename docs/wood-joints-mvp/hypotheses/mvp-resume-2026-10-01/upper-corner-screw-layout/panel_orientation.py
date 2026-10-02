"""Compare main-panel face grain across width on the unchanged physical mesh.

Reuse the existing C3D20 kernel and elastic quotient method. Authenticate
reassembly against the saved native panel matrices before replacing only
four panel contributions. No native solver, CAD or frame solve runs here.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import corner_frame as method
import top_corner_actions as accounting

ROOT = accounting.ROOT
SOURCE = HERE / "operators-attempt02"
NATIVE = method.NATIVE
PANELS = [f"main_{level}_{side}" for level in ("lower", "upper")
          for side in ("left", "right")]
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def deck_materials(path):
    """Read the nine constants actually assigned to each frozen panel layer."""
    lines = path.read_text().splitlines()
    result = {}
    for i, line in enumerate(lines):
        if not line.startswith("*MATERIAL,NAME=PANEL_LAYER_"):
            continue
        name = line.split("NAME=", 1)[1]
        require(lines[i + 1] == "*ELASTIC,TYPE=ENGINEERING CONSTANTS",
                "unexpected panel material syntax")
        values = []
        for following in lines[i + 2:]:
            if following.startswith("*"):
                break
            values.extend(float(v) for v in following.split(",") if v.strip())
        require(len(values) == 9 and values[3:6] == [0.0, 0.0, 0.0],
                "orientation comparison requires the frozen zero Poisson fit")
        require(values[7] == values[8], "transverse shear axes cannot be silently swapped")
        result[name] = values
    require(len(result) == 4, "expected four assigned panel material layers")
    return result


def build(output):
    started = time.monotonic()
    require(not output.exists(), "preserve previous calculations")
    assessment = read(SOURCE / "operator-assessment.json")
    helper_paths = {
        "parser": accounting.BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "condensation": accounting.BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": accounting.BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
    }
    pins = {ROOT / p: h for p, h in assessment["source_sha256"].items()}
    pins.update({SOURCE / p: h for p, h in assessment["output_sha256"].items()})
    paths = [SOURCE / "operator-assessment.json", NATIVE / "model.inp",
             NATIVE / "model.json", NATIVE / "model.sti", NATIVE / "model.dof",
             Path(__file__), Path(method.__file__), *helper_paths.values(),
             ROOT / "fea/wood_joint_reduced_members.py",
             ROOT / "fea/floor_recess_mesh.py", ROOT / "fea/wood_joint_patch_materials.py"]
    for path in paths:
        digest = sha(path)
        require(path not in pins or pins[path] == digest,
                "inherited source identity differs: " + str(path))
        pins[path] = digest
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    require(sha(SOURCE / "model.json") ==
            "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
            "wrong four-screw source model")
    output.mkdir(parents=True)
    write(output / "inputs.json", {"source_sha256": {
        str(p.relative_to(ROOT)): h for p, h in pins.items()}, "native_launch": False})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    parser = method.module(helper_paths["parser"], "panel_orientation_parser")
    helper = method.module(helper_paths["condensation"], "panel_orientation_condensation")
    quotient = method.module(helper_paths["quotient"], "panel_orientation_quotient")
    source = parser.load_frame_source_model(accounting.MODEL)
    physical = source["model"]
    model = read(SOURCE / "model.json")
    names = model["body_names"]
    coordinates = {int(n): np.array(v) for n, v in
                   model["physical_node_coordinates_mm"].items()}
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    owners = np.array([source["owner_by_node"][n] for n, _ in labels])
    parsed = parser.parse_upper_triangle_file(
        NATIVE / "model.sti", len(labels), owner_by_row=owners, owner_names=names)
    parser.require_no_cross_body_coupling(parsed)
    K = parsed["matrix"]
    B = sparse.load_npz(SOURCE / "B.npz").tocsr()
    constants_by_layer = deck_materials(NATIVE / "model.inp")
    with np.load(SOURCE / "operators.npz", allow_pickle=False) as data:
        H, D, e, W, F = [data[k].copy() for k in ("H", "D", "e", "W", "F")]
    H0, e0 = H.copy(), e.copy()
    cache, reports, affected = {}, [], set()
    for body in PANELS:
        body_id = names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(i)] for i in dofs]
        local_row = {label: i for i, label in enumerate(body_labels)}
        center, R, Q = helper.rigid_basis(body_labels, coordinates)
        axes_record = model["material_binding"]["panel_axes"][body]
        axes = {"L": axes_record["assumed_apa_direction_1_global_xyz"],
                "R": axes_record["assumed_apa_direction_2_global_xyz"],
                "T": axes_record["panel_normal_global_xyz"]}
        indices_i, indices_j, old_values, new_values = [], [], [], []
        for element in physical["physical_body_elements"][body]:
            kind, nodes, group = physical["elements"][str(element)]
            require(kind == "C3D20" and group.startswith(body + "_layer_"),
                    "unexpected source panel element")
            constants = constants_by_layer["PANEL_LAYER_" + group.rsplit("_", 1)[1]]
            positions = np.array([coordinates[n] for n in nodes])
            relative = positions - positions[0]
            key = (tuple(np.round(relative, 6).ravel()), tuple(constants))
            if key not in cache:
                swapped = [constants[1], constants[0], *constants[2:]]
                old, _ = method.brick_stiffness(positions, constants, axes)
                new, _ = method.brick_stiffness(positions, swapped, axes)
                cache[key] = relative, old, new
            reference_positions, old, new = cache[key]
            require(np.max(abs(relative - reference_positions)) < 1e-8,
                    "cached elements are not translated congruent bricks")
            rows = np.array([local_row[(node, d)] for node in nodes for d in (1, 2, 3)])
            indices_i.extend(np.repeat(rows, 60))
            indices_j.extend(np.tile(rows, 60))
            old_values.extend(old.ravel())
            new_values.extend(new.ravel())
        shape = (len(dofs), len(dofs))
        assembled = sparse.coo_matrix((old_values, (indices_i, indices_j)), shape=shape).tocsr()
        changed = sparse.coo_matrix((new_values, (indices_i, indices_j)), shape=shape).tocsr()
        original = K[dofs][:, dofs].tocsr()
        difference = assembled - original
        mismatch = float(np.max(abs(difference.data)) / np.max(abs(original.data)))
        require(mismatch <= 1e-6, body + ": reassembly differs from authenticated native K")
        scale = float(np.max(np.asarray(abs(changed).sum(axis=1))))
        rigid_error = float(np.linalg.norm(changed @ R, ord=np.inf) /
                            (scale * np.linalg.norm(R, ord=np.inf)))
        require(rigid_error <= 1e-8, body + ": changed stiffness loses rigid modes")
        projection = B[:, dofs].tocsr()
        active = np.flatnonzero(np.diff(projection.indptr))
        affected.update(active.tolist())
        require(np.max(abs(projection @ R - D[:, 6 * body_id:6 * body_id + 6])) < 1e-8,
                "unchanged rigid map differs")
        raw = np.column_stack([projection[active].T.toarray(), F[dofs]])
        elastic = raw - Q @ (Q.T @ raw)
        residuals = {}
        motions = []
        for tag, matrix in (("source", original), ("width_grain", changed)):
            factor, system = helper.factor_bordered(matrix, R)
            solved = quotient.solve_quotient_chunk(factor, system, matrix, R, elastic)
            require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                    body + "/" + tag + ": " + solved["status"])
            motions.append(projection[active] @ solved["displacement_mm"])
            residuals[tag] = solved["KKT_upper_force_residual_relative"]
        delta = motions[1] - motions[0]
        H[np.ix_(active, active)] += delta[:, :len(active)]
        e[active] += delta[:, len(active):]
        axes_record["previous_assumed_apa_directions"] = copy.deepcopy(axes)
        axes_record["assumed_apa_direction_1_global_xyz"] = (-np.array(axes["R"])).tolist()
        axes_record["assumed_apa_direction_2_global_xyz"] = list(axes["L"])
        axes_record["axis_status"] = "Conditional factory-long face grain placed along board X"
        axes_record["source_axis_check"] = {"physical_geometry_unchanged": True,
                                           "purchased_sheet_placement_observed": False}
        reports.append({"body": body, "physical_dofs": len(dofs),
                        "elements": len(physical["physical_body_elements"][body]),
                        "scalar_projection_rows": len(active), "datum_mm": center.tolist(),
                        "source_native_matrix_relative_max_difference": mismatch,
                        "changed_rigid_residual_relative": rigid_error,
                        "KKT_upper_force_residual_relative": residuals})
        print(body, "native mismatch", mismatch, "rows", len(active), flush=True)
    scale = float(np.linalg.norm(H, ord=np.inf))
    reciprocity = float(np.linalg.norm(H - H.T, ord=np.inf) / scale)
    minimum = float(np.linalg.eigvalsh((H + H.T) / 2)[0])
    require(reciprocity <= 1e-8 and minimum >= -1e-9 * scale,
            "invalid updated elastic compliance")
    untouched = np.array(sorted(set(range(len(H))) - affected))
    require(np.array_equal(H[np.ix_(untouched, untouched)], H0[np.ix_(untouched, untouched)])
            and np.array_equal(e[untouched], e0[untouched]), "non-panel contribution changed")
    model["development_revision"] = "upper-screw-moves-main-panel-width-grain-comparison-v1"
    model["panel_orientation_comparison"] = {"main_face_grain_global_xyz": [1.0, 0.0, 0.0],
        "main_bodies_changed": PANELS, "kicker_material_unchanged": True,
        "physical_geometry_changed_by_this_comparison": False, "actual_placement_observed": False}
    np.savez_compressed(output / "operators.npz", H=H, D=D, e=e, W=W, F=F)
    for name in ("B.npz", "row-identities.json", "model-inputs.json"):
        (output / name).write_bytes((SOURCE / name).read_bytes())
    write(output / "model.json", model)
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during reassembly: " + str(path))
    write(output / "operator-assessment.json", {
        "schema": "four_main_panel_width_grain_comparison/v1",
        "status": "PASS_UPDATED_ELASTIC_FRAME_OPERATORS", "native_launch": False,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "output_sha256": {name: sha(output / name) for name in
                          ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json")},
        "modeled_mass_kg": assessment["modeled_mass_kg"],
        "dead_load_factor": assessment["dead_load_factor"], "bodies_recomputed": reports,
        "translated_brick_cache_entries": len(cache),
        "compliance_checks": {"relative_reciprocity": reciprocity,
                              "minimum_symmetric_eigenvalue_mm_per_n": minimum,
                              "infinity_norm_mm_per_n": scale},
        "elapsed_seconds": time.monotonic() - started,
        "limits": ["Conditional Group 1 equivalent panel stiffness; actual sheet properties and placement unobserved.",
                   "Only four main-panel stiffness contributions change; geometry, screw count/stations/laws, loads, contacts and timber remain frozen.",
                   "Kicker face grain and all transverse elastic proxies retain the source assumptions.",
                   "Reassembly uses the existing C3D20 kernel with direct comparison to all four native source matrices; no native authentication transfers to response acceptance."],
        "complete_joint_acceptance": False, "physical_release": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
                "shared analysis slot occupied")
        build(args.output.resolve())
