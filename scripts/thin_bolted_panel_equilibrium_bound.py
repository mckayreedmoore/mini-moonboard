"""Necessary panel head-force lower bounds, with deliberately liberal backing.

Compression anywhere in the complete panel rectangle is a superset of actual
wood backing. Lateral reactions lie in the plate midsurface. The minimum peak
head tension is therefore a lower bound within this declared point-force model,
not a compatible response, passing strength check or physical stiffness bound.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.optimize import linprog

from scripts import hl35_candidate as shared
from scripts import thin_bolted_model as model

PACKET = model.LAYOUT.parent
GEOMETRY = PACKET / "native-geometry-v4.json"
GEOMETRY_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
INTEGRATED_SHA = "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e"
LEGACY = shared.ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-method-correction.py"
CASES = [("permanent", None, [0., 0., 0.]),
         ("a12-rear", "A12", [0., 300., -250 * 2 * 4.4482216152605]),
         ("a12-forward", "A12", [0., -300., -250 * 2 * 4.4482216152605]),
         ("a12-left", "A12", [-300., 0., -250 * 2 * 4.4482216152605]),
         ("k12-right", "K12", [300., 0., -250 * 2 * 4.4482216152605]),
         ("k12-rear", "K12", [0., 300., -250 * 2 * 4.4482216152605]),
         ("a1-rear", "A1", [0., 300., -250 * 2 * 4.4482216152605])]


def minimum_peak_tension(screw_xy, backing_xy, normal_balance,
                         x_moment_balance, y_moment_balance, scale_mm=1000.) -> dict:
    """Solve three exact normal/tilt equations; tension and compression >=0."""
    screws, backing = [np.asarray(p, dtype=float).reshape(-1, 2) for p in (screw_xy, backing_xy)]
    if len(screws) == 0 or scale_mm <= 0 or not np.isfinite([normal_balance, x_moment_balance, y_moment_balance, scale_mm]).all():
        raise ValueError("finite normal/tilt balance, screws and positive scale required")
    if not np.isfinite(screws).all() or not np.isfinite(backing).all():
        raise ValueError("finite reaction datums required")
    points = np.r_[screws, backing]
    signs = np.r_[np.ones(len(screws)), -np.ones(len(backing))]
    matrix = np.vstack((np.ones(len(points)), points[:, 1] / scale_mm, -points[:, 0] / scale_mm)) * signs
    rhs = np.array([normal_balance, x_moment_balance / scale_mm, y_moment_balance / scale_mm])
    equal = np.c_[matrix, np.zeros(3)]
    upper = np.zeros((len(screws), len(points) + 1))
    upper[np.arange(len(screws)), np.arange(len(screws))] = 1.
    upper[:, -1] = -1.
    objective = np.zeros(len(points) + 1); objective[-1] = 1.
    solved = linprog(objective, A_ub=upper, b_ub=np.zeros(len(screws)),
                     A_eq=equal, b_eq=rhs, bounds=(0., None), method="highs")
    if not solved.success:
        return {"equilibrium_feasible": False, "status": solved.message,
                "minimum_peak_tension_n": None}
    residual = matrix @ solved.x[:-1] - rhs
    return {"equilibrium_feasible": True, "minimum_peak_tension_n": float(solved.x[-1]),
            "head_tensions_n": solved.x[:len(screws)].tolist(),
            "liberal_corner_compressions_n": solved.x[len(screws):-1].tolist(),
            "normal_force_residual_n": float(residual[0]),
            "tilt_moment_residual_nmm": (residual[1:] * scale_mm).tolist(),
            "objective_dual_balance_multipliers": solved.eqlin.marginals.tolist(),
            "dual_objective_n": float(rhs @ solved.eqlin.marginals)}


def normal_tilt_target(loads, origin, basis) -> tuple[float, float, float]:
    force, moment = np.zeros(3), np.zeros(3)
    for row in loads:
        f, p = np.asarray(row["force_n"]), np.asarray(row["point_xyz_mm"])
        force += f
        moment += np.cross(p - origin, f)
    return -float(force @ basis[:, 2]), -float(moment @ basis[:, 0]), -float(moment @ basis[:, 1])


def evaluate() -> dict:
    if shared.sha(GEOMETRY) != GEOMETRY_SHA or shared.sha(model.EVIDENCE) != INTEGRATED_SHA:
        raise ValueError("frozen exact geometry or integrated model differs")
    layout = model.source_layout()
    integrated, cache = [json.loads(p.read_text()) for p in (model.EVIDENCE, GEOMETRY)]
    features = {r["identity"]: r for r in integrated["panel_machining"]["features"]}
    stock = {r["name"]: r for r in integrated["finished_stock"]}
    total_panel_mass = sum(r["volume_mm3"] * 500e-9 for n, r in stock.items() if n.startswith(("main_", "kicker_")))
    spec = importlib.util.spec_from_file_location("generic_head_reference", LEGACY)
    reference_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference_module)
    reference = reference_module._nds_head_reference(.50, 9., model.PLY - 3. / 3.)
    results = []
    for outline in cache["panel_outline_parts"]:
        name = outline["member"]
        path = shared.ROOT / outline["path"]
        if shared.sha(path) != outline["sha256"]:
            raise ValueError(f"outline differs: {name}")
        shape = cq.Shape.importBrep(str(path))
        screws = [r for r in layout["screw_axes"] if r["panel"] == name]
        normal = np.asarray(screws[0]["direction_xyz"])
        normal /= np.linalg.norm(normal)
        x = np.array([1., 0., 0.]); y = np.cross(normal, x)
        basis = np.column_stack((x, y, normal))
        vertices = np.asarray([v.Center().toTuple() for v in shape.Vertices()])
        projections = vertices @ basis
        low, high = projections.min(axis=0), projections.max(axis=0)
        origin = basis @ np.r_[low[:2], (low[2] + high[2]) / 2]
        width, height = high[:2] - low[:2]
        screw_xy = [(np.asarray(r["origin_xyz_mm"]) - origin) @ basis[:, :2] for r in screws]
        corners = [[0., 0.], [width, 0.], [width, height], [0., height]]
        own_tnuts = [r for r in cache["parts"] if r["kind"] == "tnut" and features[r["id"]]["panel"] == name]
        for accessory in ("original_top", "proportional"):
            for case_id, hold, force in CASES:
                mass = stock[name]["volume_mm3"] * 500e-9
                if accessory == "proportional":
                    mass += 25 * mass / total_panel_mass
                loads = [{"point_xyz_mm": stock[name]["center_of_mass_xyz_mm"],
                          "force_n": [0., 0., -mass * 9.80665], "kind": "panel_gravity"}]
                loads.extend({"point_xyz_mm": r["center_of_mass_xyz_mm"],
                              "force_n": [0., 0., -r["volume_mm3"] * 7850e-9 * 9.80665],
                              "kind": "conditional_tnut_gravity"} for r in own_tnuts)
                if accessory == "original_top" and name.startswith("main_upper_"):
                    top = np.asarray(features["hold_tnut_main_A12"]["start_xyz_mm"]) + normal * model.PLY
                    top[0] = 0.
                    loads.append({"point_xyz_mm": top.tolist(), "force_n": [0., 0., -12.5 * 9.80665], "kind": "original_accessories"})
                if hold and features["hold_tnut_main_" + hold]["panel"] == name:
                    point = np.asarray(features["hold_tnut_main_" + hold]["start_xyz_mm"]) - 100 * normal
                    loads.append({"point_xyz_mm": point.tolist(), "force_n": force, "kind": "climber"})
                target = normal_tilt_target(loads, origin, basis)
                solved = minimum_peak_tension(screw_xy, corners, *target)
                solved.update({"panel": name, "case_id": case_id, "accessory_placement": accessory,
                               "screw_ids": [r["axis_id"] for r in screws], "loads": loads,
                               "normal_tilt_target_n_nmm": list(target),
                               "head_reference_n_CD1": reference,
                               "lower_bound_head_index_CD1": solved["minimum_peak_tension_n"] / reference if solved["equilibrium_feasible"] else None})
                results.append(solved)
    return {"schema": "thin_bolted_panel_necessary_equilibrium_bound/v1", "candidate": model.CANDIDATE,
            "revision": model.REVISION, "source_sha256": {
                str(GEOMETRY.relative_to(shared.ROOT)): GEOMETRY_SHA,
                str(model.EVIDENCE.relative_to(shared.ROOT)): INTEGRATED_SHA,
                str(model.LAYOUT.relative_to(shared.ROOT)): model.LAYOUT_SHA,
                str(LEGACY.relative_to(shared.ROOT)): shared.sha(LEGACY),
                str(Path(__file__).relative_to(shared.ROOT)): shared.sha(Path(__file__))},
            "method": {"all_panel_rectangle_compression_allowed": True, "compression_capacity_unbounded": True,
                       "lateral_screw_reaction_plane": "plate midsurface", "friction_or_clamp_prestress_credited": False,
                       "compatible_stiffness_response": False, "generic_head_reference_hillman_qualification": False,
                       "head_height_scenario_mm": 3., "panels_density_kg_m3": 500., "tnut_density_kg_m3": 7850.},
            "results": results, "release": shared.RELEASE,
            "limits": ["A low minimum peak tension cannot pass a panel, joint or fastener; admissible optimal force allocation is not compatible response.",
                       "The complete-rectangle backing cone is deliberately liberal; real backing, edge transfer and local hole stresses remain separate.",
                       "The lower bound applies to the declared point-force/midsurface-lateral model, not to arbitrary real connector couples or physical screw stiffness.",
                       "Screw gravity is assigned to timber in the frame load study; this panel bound includes panel/T-nut gravity and the recorded 25 kg accessories.",
                       "CAT 23/32/Group1/horizontal grain and generic NDS head equation remain nominal inputs, not observed plywood or qualified Hillman capacity."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PACKET / "panel-equilibrium-lower-bound-v4.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve the prior necessary-equilibrium bound")
    report = evaluate()
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    maximum = max(r["minimum_peak_tension_n"] for r in report["results"] if r["equilibrium_feasible"])
    print(json.dumps({"panel_states": len(report["results"]), "maximum_minimum_peak_tension_n": maximum}, indent=2))


if __name__ == "__main__":
    main()
