"""Prepare two frozen strong-X operator packets with patch59 refined in X.

Replace 22 area-centroid contact rows with 44, retaining clipped face area,
first moment, contact normal and penalty modulus. No force allocation,
native solver, frame response or CAD operation is performed. Parent owns
serialized operator preparation and the subsequent finite A1 comparison.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import math
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import corner_frame as method
import top_corner_actions as accounting

ROOT, BASE, NATIVE = accounting.ROOT, accounting.BASE, method.NATIVE
sha, read, require = accounting.sha, accounting.read, accounting.require
RECOVERY = HERE / "contact-gap-recovery.py"
RECOVERY_SHA = "37d8b7a1f6789fe993f0036ba7e390c5f1a55262b5736c9bfc4e484dc04ea93b"
SOURCE_SHA = "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8"
CONTACT_SHA = "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151"
SOURCES = {
    12: (HERE / "panel-width-operators-attempt01",
         "47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0"),
    20: (HERE / "count20-width-grain-operators-attempt02",
         "d94732bb20ede8da48a7799c014b2c9d66e16062b7c4f485ec008e494c5488a1"),
}
BODIES = ("main_lower_left", "base_rail_bottom_left")


def write(path, value):
    import json

    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def pin(path, pins, expected=None):
    digest = sha(path)
    require(expected is None or digest == expected, "Changed source: " + str(path))
    require(path not in pins or pins[path] == digest, "Inconsistent source identity")
    pins[path] = digest


def half_disk_strip(x0, x1, center_x, radius, sign):
    """Exact area and X/T first moments of one centered disk half in an X strip."""
    a = max(-radius, x0 - center_x)
    b = min(radius, x1 - center_x)
    if b <= a:
        return 0.0, 0.0, 0.0

    def primitive(u):
        return 0.5 * (u * math.sqrt(max(radius * radius - u * u, 0.0))
                      + radius * radius * math.asin(max(-1.0, min(1.0, u / radius))))

    area = primitive(b) - primitive(a)
    mx = center_x * area + ((max(radius * radius - a * a, 0.0) ** 1.5
                             - max(radius * radius - b * b, 0.0) ** 1.5) / 3)
    mt = sign * 0.5 * (radius * radius * (b - a) - (b ** 3 - a ** 3) / 3)
    return area, mx, mt


def geometry(physical, contacts):
    """Use the saved rectangle and its two midline circular holes, without CAD."""
    patch = contacts["contact_patches"][59]
    require(patch["member_ids"] == [BODIES[1], BODIES[0]], "Unexpected patch59 members")
    center = np.array(patch["centroid_xyz_mm"])
    normal = np.array(patch["normal_on_first_xyz"])
    require(abs(normal[0]) < 1e-10 and abs(np.linalg.norm(normal) - 1) < 1e-10,
            "Expected unit normal perpendicular to X")
    tangent = np.cross([1.0, 0.0, 0.0], normal)
    lines = [edge for edge in patch["boundary_edges"] if edge["curve_type"] == "LINE"]
    circles = [edge["circle"] for edge in patch["boundary_edges"] if edge["curve_type"] == "CIRCLE"]
    require(len(lines) == 4 and len(circles) == 2, "Expected four outer edges and two circular holes")
    corners = np.array([edge[end] for edge in lines for end in ("start_xyz_mm", "end_xyz_mm")])
    require(np.max(abs((corners - center) @ normal)) < 1e-6, "Outer edges left source plane")
    xmin, xmax = float(corners[:, 0].min()), float(corners[:, 0].max())
    ts = (corners - center) @ tangent
    tmin, tmax = float(ts.min()), float(ts.max())
    require(abs(tmin + tmax) < 1e-6, "Expected centered transverse bounds")
    half_width = (tmax - tmin) / 2
    require(all(min(abs(t - tmin), abs(t - tmax)) < 1e-6 for t in ts),
            "Outer boundary is not the saved rectangle")
    for edge in lines:
        a, b = [np.array(edge[key]) for key in ("start_xyz_mm", "end_xyz_mm")]
        require(abs(a[0] - b[0]) < 1e-6 or abs((a - b) @ tangent) < 1e-6,
                "Rectangle edge is not aligned with source X/T")
    for hole in circles:
        point = np.array(hole["center_xyz_mm"])
        radius = hole["radius_mm"]
        require(abs((point - center) @ tangent) < 1e-6
                and abs((point - center) @ normal) < 1e-6,
                "Circle is not centered on the source transverse midline")
        require(xmin < point[0] - radius < point[0] + radius < xmax
                and 0 < radius < half_width, "Circle extends beyond source rectangle")
        require(abs(abs(np.dot(hole["axis_xyz"], normal)) - 1) < 1e-10,
                "Circle axis differs from source plane")

    def cells(nx):
        result = []
        for ix in range(nx):
            x0, x1 = [xmin + (xmax - xmin) * i / nx for i in (ix, ix + 1)]
            for it, (t0, t1, sign) in enumerate(((-half_width, 0.0, -1), (0.0, half_width, 1))):
                area = (x1 - x0) * (t1 - t0)
                mx, mt = area * (x0 + x1) / 2, area * (t0 + t1) / 2
                for hole in circles:
                    da, dx, dt = half_disk_strip(x0, x1, hole["center_xyz_mm"][0], hole["radius_mm"], sign)
                    area, mx, mt = area - da, mx - dx, mt - dt
                require(area > 0, "Empty clipped rectangle cell")
                point = center + (mx / area - center[0]) * np.array([1.0, 0.0, 0.0]) + (mt / area) * tangent
                result.append({"name": f"contact_59_refined_X2_{ix:02}_{it}",
                               "point_xyz_mm": point.tolist(), "area_mm2": area,
                               "first": BODIES[1], "second": BODIES[0],
                               "normal_xyz": (-normal).tolist(), "source_patch_index": 59,
                               "kind": "timber_or_panel_contact", "x_bin": ix, "transverse_bin": it})
        return result

    original = [row for row in physical["contact_cell_ownership"] if row.get("source_patch_index") == 59]
    require(len(original) == 22, "Expected twenty-two original patch59 cells")
    coarse, refined = cells(11), cells(22)
    coarse_errors = []
    unmatched = list(original)
    for cell in coarse:
        saved = min(unmatched, key=lambda row: np.linalg.norm(np.array(row["point_xyz_mm"]) - cell["point_xyz_mm"]))
        unmatched.remove(saved)
        point_error = float(np.max(abs(np.array(saved["point_xyz_mm"]) - cell["point_xyz_mm"])))
        area_error = abs(saved["area_mm2"] - cell["area_mm2"])
        require(point_error < 1e-6 and area_error < 1e-5, "Analytic coarse cells differ from saved clipping")
        coarse_errors.append((point_error, area_error))
    checks = []
    for tag, samples in (("coarse", coarse), ("refined", refined)):
        area = sum(row["area_mm2"] for row in samples)
        centroid = sum((np.array(row["point_xyz_mm"]) * row["area_mm2"] for row in samples), np.zeros(3)) / area
        require(abs(area - patch["area_mm2"]) < 1e-5
                and np.max(abs(centroid - center)) < 1e-6, "Clipping lost source area or first moment")
        checks.append({"grid": tag, "cell_count": len(samples), "area_mm2": area,
                       "source_area_error_mm2": area - patch["area_mm2"],
                       "centroid_xyz_mm": centroid.tolist(),
                       "source_centroid_max_error_mm": float(np.max(abs(centroid - center)))})
    return {"patch_index": 59, "patch": patch, "cells": refined,
            "removed_cell_names": [row["name"] for row in original],
            "x_bounds_mm": [xmin, xmax], "transverse_bounds_relative_to_patch_centroid_mm": [-half_width, half_width],
            "old_x_divisions": 11, "new_x_divisions": 22, "transverse_divisions": 2,
            "analytic_clipping": "Rectangle minus two midline circular holes; exact half-disk strip integrals",
            "coarse_centroid_max_difference_mm": max(item[0] for item in coarse_errors),
            "coarse_cell_area_max_difference_mm2": max(item[1] for item in coarse_errors),
            "area_first_moment_checks": checks}


def geometry_only(output):
    require(not output.exists(), "Use a fresh geometry output child")
    pins = {}
    pin(accounting.MODEL, pins, SOURCE_SHA)
    pin(accounting.CONTACTS, pins, CONTACT_SHA)
    pin(Path(__file__), pins)
    record = geometry(read(accounting.MODEL), read(accounting.CONTACTS))
    output.mkdir(parents=True)
    write(output / "geometry.json", record)
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()}})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print("geometry_sha256", sha(output / "geometry.json"), flush=True)


def build(output):
    require(not output.exists(), "Use a fresh operator output child")
    pins, packets = {}, {}
    paths = {
        "parser": BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "helper": BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
        "orientation": HERE / "panel_orientation.py",
    }
    pin(accounting.MODEL, pins, SOURCE_SHA)
    pin(accounting.CONTACTS, pins, CONTACT_SHA)
    pin(RECOVERY, pins, RECOVERY_SHA)
    for count, (folder, digest) in SOURCES.items():
        pin(folder / "operator-assessment.json", pins, digest)
        assessment = read(folder / "operator-assessment.json")
        for relative, source_digest in assessment["source_sha256"].items():
            pin(ROOT / relative, pins, source_digest)
        for filename, output_digest in assessment["output_sha256"].items():
            pin(folder / filename, pins, output_digest)
        packets[count] = {"folder": folder, "assessment": assessment,
                          "rows": read(folder / "row-identities.json"), "model": read(folder / "model.json"),
                          "model_inputs": read(folder / "model-inputs.json"), "B": sparse.load_npz(folder / "B.npz").tocsr()}
        with np.load(folder / "operators.npz", allow_pickle=False) as data:
            packets[count].update({key: data[key].copy() for key in ("H", "D", "e", "W", "F")})
    for path in [Path(__file__), Path(method.__file__), *paths.values(),
                 NATIVE / "model.inp", NATIVE / "model.dof", NATIVE / "model.sti",
                 ROOT / "fea/wood_joint_reduced_members.py", ROOT / "fea/floor_recess_mesh.py",
                 ROOT / "fea/wood_joint_patch_materials.py"]:
        pin(path, pins)
    pin(paths["orientation"], pins, "3268faa94ba050d82d66df1393fc4b8e4d9e4a79b87412fe0f4cfdbf72dd7e93")
    pin(NATIVE / "model.inp", pins, "71dc0b73450b597aba35c0458befff5ca3b85dd87f3cfbed9992f4755b5124d5")
    modules = {name: method.module(path, "patch_refinement_" + name) for name, path in paths.items()}
    recovery = method.module(RECOVERY, "patch_refinement_recovery")
    parser, helper, quotient = [modules[name] for name in ("parser", "helper", "quotient")]
    source = parser.load_frame_source_model(accounting.MODEL)
    physical = source["model"]
    model = packets[12]["model"]
    names = model["body_names"]
    require(list(source["bodies"]) == names == packets[20]["model"]["body_names"], "Body order mismatch")
    require(model["physical_node_coordinates_mm"] == packets[20]["model"]["physical_node_coordinates_mm"],
            "Physical coordinates differ between count packets")
    require(np.array_equal(packets[12]["F"], packets[20]["F"])
            and np.array_equal(packets[12]["W"], packets[20]["W"]), "Count packets changed nodal/rigid loads")
    coordinates = {int(node): np.array(xyz) for node, xyz in model["physical_node_coordinates_mm"].items()}
    record = geometry(physical, read(accounting.CONTACTS))
    output.mkdir(parents=True)
    write(output / "geometry.json", record)
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()}})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    row_for = {label: i for i, label in enumerate(labels)}
    owners = np.array([source["owner_by_node"][node] for node, _ in labels])
    parsed = parser.parse_upper_triangle_file(NATIVE / "model.sti", len(labels), owner_by_row=owners, owner_names=names)
    parser.require_no_cross_body_coupling(parsed)
    new_B = sparse.lil_matrix((44, len(labels)))
    for index, cell in enumerate(record["cells"]):
        for body, sign in ((cell["first"], -1), (cell["second"], 1)):
            terms = method.point_terms(body, cell["point_xyz_mm"], sign * np.array(cell["normal_xyz"]),
                                       physical, coordinates, row_for)
            for dof, value in terms.items():
                new_B[index, dof] += value
    new_B = new_B.tocsr()
    removed_names = set(record["removed_cell_names"])
    for packet in packets.values():
        removed = [i for i, row in enumerate(packet["rows"]) if row["row_id"] in removed_names]
        require(len(removed) == 22, "Expected exactly twenty-two removed rows")
        templates = [packet["rows"][i] for i in removed]
        moduli = []
        cells_by_name = {r["name"]: r for r in physical["contact_cell_ownership"] if r.get("source_patch_index") == 59}
        for row in templates:
            require(row["family"] == "unilateral_springa" and row["law"]["intended_law"] == "compression_only",
                    "Source patch has a different law")
            moduli.append(row["law"]["stiffness_N_per_mm"] / cells_by_name[row["row_id"]]["area_mm2"])
        require(max(abs(value - 100.0) for value in moduli) < 1e-8, "Source penalty modulus differs")
        retained = np.array([i for i in range(len(packet["rows"])) if i not in removed], dtype=int)
        n = len(retained)
        packet["retained"], packet["retained_count"] = retained, n
        packet["newH"] = np.zeros((n + 44, n + 44))
        packet["newD"] = np.zeros((n + 44, 300))
        packet["newe"] = np.zeros((n + 44, packet["e"].shape[1]))
        packet["newH"][:n, :n] = packet["H"][np.ix_(retained, retained)]
        packet["newD"][:n] = packet["D"][retained]
        packet["newe"][:n] = packet["e"][retained]
        rows = copy.deepcopy([packet["rows"][i] for i in retained])
        for i, row in enumerate(rows):
            row["row"] = i
        for index, cell in enumerate(record["cells"]):
            row = copy.deepcopy(templates[0])
            for key in ("source_element", "source_group", "source_inventory_row_index"):
                row.pop(key, None)
            row.update(row=n + index, row_id=cell["name"], patch59_X2_replacement=True)
            row["ownership"].update(point_mm=cell["point_xyz_mm"], direction_global_xyz=cell["normal_xyz"],
                                    first_body=cell["first"], second_body=cell["second"])
            k = 100.0 * cell["area_mm2"]
            row["law"]["stiffness_N_per_mm"] = k
            row["law"]["scalar_force_table_N_mm"] = [[0.0, -10.0], [0.0, 0.0], [10 * k, 10.0]]
            row["refined_cell_area_mm2"] = cell["area_mm2"]
            rows.append(row)
        packet["new_rows"] = rows
    reports = []
    for body in BODIES:
        body_id = names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        _, R, Q = helper.rigid_basis([labels[int(i)] for i in dofs], coordinates)
        body_K = parsed["matrix"][dofs][:, dofs].tocsr()
        mismatch = None
        if body == BODIES[0]:
            body_K, mismatch = recovery.width_panel_K(physical, model, labels, coordinates, dofs,
                                                       body_K, modules["orientation"])
        projection = new_B[:, dofs].tocsr()
        rhs = projection.T.toarray()
        factor, system = helper.factor_bordered(body_K, R)
        solved = quotient.solve_quotient_chunk(factor, system, body_K, R, rhs - Q @ (Q.T @ rhs))
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": " + solved["status"])
        displacement = solved["displacement_mm"]
        for packet in packets.values():
            n, kept = packet["retained_count"], packet["retained"]
            old_projection = packet["B"][:, dofs].tocsr()
            require(np.max(abs(old_projection @ R - packet["D"][:, 6 * body_id:6 * body_id + 6])) < 1e-8,
                    "Source rigid projection differs")
            cross = old_projection[kept] @ displacement
            packet["newH"][:n, n:] += cross
            packet["newH"][n:, :n] += cross.T
            packet["newH"][n:, n:] += projection @ displacement
            packet["newD"][n:, 6 * body_id:6 * body_id + 6] += projection @ R
            packet["newe"][n:] += displacement.T @ packet["F"][dofs]
        reports.append({"body": body, "new_scalar_rhs_count": 44, "physical_dofs": len(dofs),
                        "strong_X_main_panel_K": body == BODIES[0],
                        "source_native_K_relative_difference": mismatch,
                        "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
        print("projected", body, "44 refined contact rows", flush=True)
    outputs = {}
    for count, packet in packets.items():
        target = output / f"operators-{count}"
        target.mkdir()
        n, kept = packet["retained_count"], packet["retained"]
        H, D, e = [packet[key] for key in ("newH", "newD", "newe")]
        require(np.array_equal(H[:n, :n], packet["H"][np.ix_(kept, kept)])
                and np.array_equal(D[:n], packet["D"][kept]) and np.array_equal(e[:n], packet["e"][kept]),
                "Retained operator block changed")
        symmetry = float(np.linalg.norm(H - H.T, ord=np.inf) / np.linalg.norm(H, ord=np.inf))
        require(symmetry <= 1e-8, "Refined compliance loses reciprocity")
        np.savez_compressed(target / "operators.npz", H=H, D=D, e=e, W=packet["W"], F=packet["F"])
        sparse.save_npz(target / "B.npz", sparse.vstack((packet["B"][kept], new_B), format="csr"))
        write(target / "row-identities.json", packet["new_rows"])
        frame_model = copy.deepcopy(packet["model"])
        frame_model["patch59_contact_refinement"] = {"old_cells": 22, "new_cells": 44,
            "physical_geometry_changed": False, "penalty_modulus_changed": False,
            "source_operator_directory": str(packet["folder"].relative_to(ROOT))}
        write(target / "model.json", frame_model)
        (target / "model-inputs.json").write_bytes((packet["folder"] / "model-inputs.json").read_bytes())
        write(target / "operator-assessment.json", {"schema": "patch59_X2_elastic_operators/v1",
            "status": "PREPARED_PATCH59_REFINED_OPERATORS", "screws_per_main_panel": count,
            "source_operator_directory": str(packet["folder"].relative_to(ROOT)),
            "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
            "output_sha256": {name: sha(target / name) for name in
                              ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json")},
            "modeled_mass_kg": packet["assessment"]["modeled_mass_kg"],
            "dead_load_factor": packet["assessment"]["dead_load_factor"],
            "bodies_recomputed": reports, "source_scalar_row_count": len(packet["rows"]),
            "removed_contact_row_ids": record["removed_cell_names"],
            "appended_contact_row_ids": [cell["name"] for cell in record["cells"]],
            "refined_scalar_row_count": len(packet["new_rows"]),
            "retained_source_row_indices": kept.tolist(),
            "area_first_moment_checks": record["area_first_moment_checks"],
            "relative_reciprocity": symmetry, "retained_H_D_e_exact": True, "F_W_unchanged": True,
            "native_launch": False, "frame_solve_executed": False, "complete_joint_acceptance": False,
            "limits": ["Patch59-only discretization comparison; unchanged penalty/contact/screw hypotheses.",
                       "Refined cells are area-centroid springs, not continuous pressure or capacity.",
                       "Model inputs retain original physical contact geometry; row identities define refined analysis sampling.",
                       "No frame response or adoption is performed by this producer."], "physical_release": False})
        outputs[str(count)] = {"directory": str(target.relative_to(ROOT)),
                               "assessment_sha256": sha(target / "operator-assessment.json")}
    for path, digest in pins.items():
        require(sha(path) == digest, "Source changed during refinement")
    write(output / "result.json", {"schema": "patch59_X2_operator_pair/v1",
        "status": "PREPARED_BOTH_COUNT_OPERATORS", "operators": outputs,
        "geometry_sha256": sha(output / "geometry.json"),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "native_launch": False, "frame_solve_executed": False, "physical_release": False})
    print("result_sha256", sha(output / "result.json"), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--geometry-only", action="store_true")
    args = cli.parse_args()
    if args.geometry_only:
        geometry_only(args.output.resolve())
    else:
        lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
        with lock.open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "Shared mechanics slot occupied")
            build(args.output.resolve())
