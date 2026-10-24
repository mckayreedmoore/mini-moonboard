"""Measure panel restraint in the current saved tangent operators.

These are fixed-contact, infinitesimal stiffness comparisons, not changed-load
equilibria or joint strengths. All panels, screw springs and panel contacts are
removed together in the frame-only comparator. Balanced probe loads enter the
timbers directly; no climber load is left on a disconnected panel.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import importlib.metadata
import json
from contextlib import ExitStack
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, diags, vstack
from scipy.sparse.linalg import splu

from scripts import eoere_current_response as response
from scripts import eoere_v6_analysis as analysis
from scripts import eoere_v6_checks as checks
from scripts import thin_bolted_numerical_step as laws
from scripts.eoere_paired_frame_basis import ref, sha

OWN = Path(__file__).resolve()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compliance(matrix, loads):
    """Solve exact probe loads without adding supports or numerical stiffness."""
    matrix = matrix.tocsr()
    loads = np.asarray(loads, dtype=float)
    require(loads.ndim == 2 and matrix.shape == (loads.shape[0], loads.shape[0]), "probe dimensions")
    diagonal = matrix.diagonal()
    keep = diagonal != 0.
    require(np.all(diagonal[keep] > 0.), "nonpositive stiffness diagonal")
    require(np.max(np.abs(matrix[~keep].toarray()), initial=0.) == 0., "zero-diagonal coupled row")
    require(np.max(np.abs(loads[~keep]), initial=0.) == 0., "probe loads a free coordinate")
    scale = 1 / np.sqrt(diagonal[keep])
    submatrix = matrix[keep][:, keep].tocsc()
    scaled = diags(scale) @ submatrix @ diags(scale)
    factor = splu(scaled.tocsc())
    rhs = loads[keep]
    solved = (scale[:, None] * factor.solve(scale[:, None] * rhs)).astype(np.longdouble)
    # Cancellation in an almost-rigid mode can obscure unit-probe residuals.
    # Refine the same literal operator using wider accumulation, never damping
    # or added supports. Retain both residuals and the original admission gate.
    wide_matrix = submatrix.astype(np.longdouble)
    wide_rhs = rhs.astype(np.longdouble)
    for _ in range(6):
        residual = np.asarray(wide_rhs - wide_matrix @ solved, dtype=float)
        solved += (scale[:, None] * factor.solve(scale[:, None] * residual)).astype(np.longdouble)
    errors = np.max(np.abs(wide_matrix @ solved - wide_rhs), axis=0) / np.max(np.abs(rhs), axis=0)
    binary64 = np.max(np.abs(submatrix @ solved.astype(float) - rhs), axis=0) / np.max(np.abs(rhs), axis=0)
    require(np.max(errors) < 1e-7, f"probe residual too large: {errors}")
    result = np.asarray(wide_rhs.T @ solved, dtype=float)
    require(np.all(np.diag(result) > 0.), "nonpositive probe compliance")
    normalized = np.sqrt(np.outer(np.diag(result), np.diag(result)))
    reciprocity = float(np.max(np.abs(result - result.T) / normalized))
    require(reciprocity < 1e-6, "probe reciprocity failed")
    work = np.sum(solved * (wide_matrix @ solved), axis=0)
    require(np.allclose(work, np.diag(result), rtol=1e-6, atol=0.), "probe energy/work failed")
    return result, {"maximum_relative_equilibrium_error": float(np.max(errors)),
                    "maximum_relative_binary64_equilibrium_error": float(np.max(binary64)),
                    "residual_accumulation_mantissa_bits": int(np.finfo(np.longdouble).nmant),
                    "maximum_normalized_reciprocity_error": reciprocity,
                    "zero_uncoupled_unloaded_coordinates_omitted": int(np.sum(~keep)),
                    "added_stiffness_or_supports": False}


def rotation_port(maps, body, point):
    """Use the saved timber chart's linear rotation interpolation and units."""
    member = maps.members[body]
    station = float((np.asarray(point) - member["start"]) @ member["axis"])
    require(member["stations"][0] - 1e-7 <= station <= member["stations"][-1] + 1e-7,
            "probe outside timber span")
    i = int(np.clip(np.searchsorted(member["stations"], station) - 1, 0, len(member["stations"]) - 2))
    lo, hi = member["stations"][i:i+2]
    t = (station - lo) / (hi - lo)
    block = np.hstack(((1-t)*np.eye(3), t*np.eye(3))) / 1000.
    return maps.embed(block, member["index"][i:i+2, 3:].ravel())


def annotated_inputs(data, chart, properties):
    """Retain the same exact plywood metadata join as the issued replay."""
    joined = copy.deepcopy(data)
    for row in joined["timber_rows"]:
        if row["name"].startswith("eoere_cleat_"):
            row["explicit_plywood_operator"] = copy.deepcopy(properties)
        require(row == chart["timber"][row["name"]]["source"], "timber/material source join differs")
    return joined


def probes(snapshot, maps, geometry):
    records, columns = [], []
    for side, fitting in (("left", "eoere_clip_single_top_left_1"),
                          ("right", "eoere_clip_single_top_right_2")):
        axes = [a for a in geometry["axes"] if any(p["angle_id"] == fitting for p in a["attachments"])]
        require(len(axes) == 4, "four own corner axes required")
        point = np.mean([a["point_xyz_mm"] for a in axes], axis=0)
        first, second = "base_rail_top", "base_side_" + side
        translation = maps.port(first, point) - maps.port(second, point)
        rotation = rotation_port(maps, first, point) - rotation_port(maps, second, point)
        top = np.asarray(geometry["profiles"][first]["basis_grain_u_v_xyz"][0])
        slope = np.asarray(geometry["profiles"][second]["basis_grain_u_v_xyz"][0])
        normal = np.cross(top, slope)
        normal /= np.linalg.norm(normal)
        for mode, direction, port, unit in (
            ("top_grain_compression", top, translation, "N/mm"),
            ("side_grain_compression", slope, translation, "N/mm"),
            ("panel_normal_translation", normal, translation, "N/mm"),
            ("top_grain_torsion", top, rotation, "Nmm/rad"),
            ("side_grain_torsion", slope, rotation, "Nmm/rad"),
            ("in_plane_corner_rotation", normal, rotation, "Nmm/rad"),
        ):
            vector = np.asarray(port.T @ direction).ravel()
            require(np.max(np.abs(snapshot.rigid_modes.T @ vector)) < 1e-8,
                    "probe must have zero total external force and moment")
            columns.append(vector)
            records.append({"corner": side, "first": first, "second": second, "mode": mode,
                            "point_xyz_mm": point.tolist(), "direction_xyz": direction.tolist(),
                            "stiffness_unit": unit, "joint_axis_ids": [a["id"] for a in axes]})
    return np.column_stack(columns), records


def tangent(snapshot, state, *, panels):
    """Reuse the issued spring/contact Hessian with the same active branches."""
    panel_ids = set(snapshot.coordinate_map["panels"])
    groups = [row for row in snapshot.groups if panels or row["kind"] != "panel_screw"]
    contacts = [row for row in snapshot.contacts if panels or
                not ({row["first"], row["second"]} & panel_ids)]
    linear = snapshot.assembly.K.copy()
    for row in snapshot.tangents:
        if row["first"] in analysis.HOSTS:
            linear += row["stiffness"] * (row["B"].T @ row["B"])
    contact_matrix = vstack([row["B"] for row in contacts], format="csr")
    stiffness = np.array([row["stiffness"] for row in contacts])
    fields = laws.physical_fields(linear, np.zeros(snapshot.assembly.ndof), groups,
                                  contact_matrix, stiffness, state, tangent=True)
    require(sum(row["kind"] == "panel_screw" for row in groups) == (66 if panels else 0),
            "complete screw ablation required")
    keep = np.ones(snapshot.assembly.ndof, dtype=bool)
    if not panels:
        for row in snapshot.coordinate_map["panels"].values():
            keep[row["indices"]] = False
    return fields[2][keep][:, keep], keep, {
        "screw_springs_retained": sum(row["kind"] == "panel_screw" for row in groups),
        "panel_contacts_retained": sum(row["kind"] == "panel_contact" for row in contacts),
        "ndof": int(np.sum(keep)), "contact_branches_frozen_at_original_state": True}


def controls():
    # A frame spring k=100 in parallel with screw k=200 and panel k=50 in series.
    matrix = csr_matrix([[300., -200.], [-200., 250.]])
    observed, _ = compliance(matrix, np.array([[1.], [0.]]))
    expected = 1 / (100 + 1 / (1/200 + 1/50))
    require(np.isclose(observed[0, 0], expected, rtol=1e-12), "series/parallel control")
    bare, _ = compliance(csr_matrix([[100.]]), np.ones((1, 1)))
    require(np.isclose(bare[0, 0] / observed[0, 0], 1.4, rtol=1e-12), "known stiffness gain")
    # A floating panel tied to the frame at only one point supplies no brace.
    floating, _ = compliance(csr_matrix([[300., -200.], [-200., 200.]]), np.array([[1.], [0.]]))
    require(np.isclose(floating[0, 0], bare[0, 0], rtol=1e-12), "floating panel cannot brace")
    return {"series_parallel_gain": 1.4, "floating_panel_gain": 1.,
            "known_answer_controls_passed": True}


def run(out, case_ids):
    require(out.resolve().is_relative_to(analysis.BASE), "use the current ignored analysis packet")
    require(not out.exists(), "fresh output directory required")
    control = controls()
    geometry, fields, pins = checks.load()
    chosen = [row for row in fields if row[1] in case_ids]
    require({row[1] for row in chosen} == set(case_ids), "own admitted cases required")
    bridge = response.load("bridge").frozen()
    material = json.loads(analysis.MATERIAL.read_bytes())
    results = []
    out.mkdir(parents=True)
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    for _, case, binding, field in chosen:
        snapshot = bridge.bundle.read_snapshot(field["operator_bundle"])
        pins.update({r["path"]: r["sha256"] for r in field["operator_bundle"].values()})
        require(field["source_inputs"]["plywood_material"] == ref(analysis.MATERIAL), "own material required")
        joined = annotated_inputs(field["source_inputs"], snapshot.coordinate_map, material["properties"])
        centroidal = bridge.driver.load(bridge.driver.CENTROIDAL, bridge.driver.CENTROIDAL_SHA,
                                        "panel_bracing_saved_centroidal_maps")
        with response.load("bridge").corrected_context(bridge), ExitStack() as stack:
            for factory in {id(f): f for f in
                            (bridge.factory, bridge.base.factory, bridge.old_gate.base.factory)}.values():
                stack.enter_context(centroidal.correction_context(factory))
            maps = bridge.base.OwnedMaps(snapshot, joined)
            loads, records = probes(snapshot, maps, geometry)
        state = np.asarray(field["response"]["q"])
        matrices, audits = {}, {}
        for label, with_panels in (("with_panels", True), ("without_panels", False)):
            matrix, keep, census = tangent(snapshot, state, panels=with_panels)
            matrices[label], audit = compliance(matrix, loads[keep])
            audits[label] = {**census, **audit}
        for i, row in enumerate(records):
            full, bare = matrices["with_panels"][i, i], matrices["without_panels"][i, i]
            require(bare / full >= 1 - 1e-6, "removing positive panel restraint cannot stiffen this comparator")
            row.update(with_panels_stiffness=float(1/full), without_panels_stiffness=float(1/bare),
                       modeled_stiffness_ratio=float(bare/full))
        results.append({"case_id": case, "field": binding, "operator_bundle": field["operator_bundle"],
                        "audits": audits, "probes": records})
        print(case, [(r["corner"], r["mode"], round(r["modeled_stiffness_ratio"], 4)) for r in records], flush=True)
    for path in (OWN, Path("scripts/thin_bolted_numerical_step.py"), Path("scripts/thin_bolted_frame_mechanics.py")):
        pins[ref(path)["path"]] = sha(path)
    for path, digest in pins.items():
        require(sha(path) == digest, f"source changed: {path}")
    result = {"schema": "eoere_current96_fixed_branch_panel_bracing/v1", "producer": ref(OWN),
              "geometry": ref(analysis.GEOMETRY), "source_sha256": pins, "controls": control,
              "tools": {name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
              "cases": results, "limits": [
                  "Balanced unit force/couple probes measure relative top-rail/side-member tangent compliance at the same declared corner point.",
                  "The full frame can deform and redistribute incremental loads. All six panels, 66 screws and all panel contacts are removed together only in the comparator.",
                  "Other contacts and bearing active branches stay frozen at each original braced equilibrium. The unbraced comparator is not a newly equilibrated climber-load case.",
                  "Compression labels identify a translation probe along a member grain direction, not timber crushing or column capacity.",
                  "Stiffness gains do not establish strength gains, physical Hillman behavior, fracture resistance, or clearance/finite-motion applicability.",
                  "No strength criterion, geometry, physical loading or adopted current result is changed. No native solver or CAD rebuild is used."],
              "strength_gain_established": False, "structural_acceptance": False, "release": False}
    with (out / "result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(ref(out / "result.json"), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", choices=checks.CASES, default=list(checks.CASES))
    args = parser.parse_args()
    with (analysis.ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(args.out, args.cases)


if __name__ == "__main__":
    main()
