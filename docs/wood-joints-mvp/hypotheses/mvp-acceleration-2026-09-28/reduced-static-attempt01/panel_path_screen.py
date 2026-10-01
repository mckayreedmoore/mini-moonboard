"""Necessary panel-body equilibrium with no screw axial restraint.

This small linear-programming screen permits unbounded lateral screw reactions
and compressive reactions anywhere in the convex hull of each actual contact
patch. It supplies neither compatible deformations nor design demands. Loads
include the source panel/T-nut gravity table, not deferred hardware/accessories.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent


def screen():
    model = json.loads((HERE / "model-inputs.json").read_text())
    geometry = json.loads((HERE / "contact-geometry.json").read_text())
    panels = sorted(row["member_id"] for row in model["members"] if row["member_kind"] == "panel")
    reference = {row["member_id"]: np.array(row["reference_xyz_mm"])
                 for row in model["cases"][0]["body_external_wrenches"] if row["member_id"] in panels}
    columns, bounds, descriptions = [], [], []

    def add(kind, name, actions, bound):
        column = np.zeros(6*len(panels))
        for body, point, force in actions:
            if body in panels:
                i = 6*panels.index(body)
                column[i:i+3] += force
                column[i+3:i+6] += np.cross(np.asarray(point)-reference[body], force)/1000.
        if np.linalg.norm(column) > 1e-12:
            columns.append(column)
            bounds.append(bound)
            descriptions.append({"kind": kind, "name": name})

    for index, patch in enumerate(geometry["contact_patches"]):
        first, second = patch["member_ids"]
        if first not in panels and second not in panels:
            continue
        inward = -np.array(patch["normal_on_first_xyz"])
        points = [patch["centroid_xyz_mm"], *patch["vertices_xyz_mm"]]
        for j, point in enumerate(points):
            add("compression", f"patch_{index}_{j}", [(first, point, inward), (second, point, -inward)], (0., None))
    for screw in model["connections"]:
        if screw["kind"] != "panel_screw":
            continue
        first = screw["source_record"]["panel_member"]
        axis = np.array(screw["axis_xyz"], dtype=float)
        axis /= np.linalg.norm(axis)
        tangent = np.cross(axis, np.eye(3)[np.argmin(abs(axis))])
        tangent /= np.linalg.norm(tangent)
        # The source point is on the head face. Moving the lateral resultant
        # axially to the wood interface changes moment, but not normal force.
        # This screen records that relaxation; it is not a screw demand model.
        for j, direction in enumerate((tangent, np.cross(axis, tangent))):
            add("lateral_screw", f"{screw['axis_id']}_{j}",
                [(first, screw["source_point_xyz_mm"], direction)], (None, None))
    matrix = np.array(columns).T
    results = []
    for case in model["cases"]:
        applied = np.zeros(len(panels)*6)
        for row in case["body_external_wrenches"]:
            if row["member_id"] in panels:
                i = panels.index(row["member_id"])*6
                applied[i:i+3] = row["assigned_external_force_xyz_n"]
                applied[i+3:i+6] = np.array(row["assigned_external_moment_xyz_nmm"])/1000.
        solved = linprog(np.zeros(len(columns)), A_eq=matrix, b_eq=-applied, bounds=bounds,
                         method="highs", options={"primal_feasibility_tolerance": 1e-8})
        residual = None if not solved.success else float(np.max(abs(matrix @ solved.x + applied)))
        # A single-body outward projection gives a stronger interpretable
        # impossibility certificate when every permitted reaction is nonnegative.
        certificates = []
        for panel in panels:
            if not panel.startswith("main_"):
                continue
            normal = np.array([0., np.cos(np.deg2rad(40.)), -np.sin(np.deg2rad(40.))])
            i = 6*panels.index(panel)
            projection = normal @ matrix[i:i+3]
            free_max = max((abs(projection[j]) for j, bound in enumerate(bounds) if bound[0] is None), default=0.)
            contact_min = min((projection[j] for j, bound in enumerate(bounds) if bound[0] == 0.), default=0.)
            demand = float(normal @ applied[i:i+3])
            if free_max < 1e-8 and contact_min > -1e-8 and demand > 1e-6:
                certificates.append({"panel": panel, "outward_normal_xyz": normal.tolist(),
                    "certificate_scope": "Nominal-geometry direction-tolerance screen, not an exact-arithmetic LP dual certificate; unbounded reactions cannot mathematically treat a merely small coefficient as exactly zero.",
                    "external_outward_component_n": demand,
                    "minimum_compression_reaction_outward_component_per_unit_n": float(contact_min),
                    "maximum_lateral_reaction_outward_component_per_unit_n": float(free_max),
                    "meaning": "Positive external outward force cannot be balanced by these allowed reactions."})
        results.append({"case_id": case["case_id"], "linear_program_status": solved.status,
            "message": solved.message, "equilibrium_feasible": bool(solved.success),
            "maximum_force_and_scaled_moment_residual": residual, "normal_force_certificates": certificates})
    return {"scope": __doc__, "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [HERE / "model-inputs.json", HERE / "contact-geometry.json", Path(__file__)]},
            "panels": panels, "reaction_variable_count": len(columns), "cases": results,
            "limits": ["No compatibility, stiffness, finite strength or joint acceptance",
                "Normal-force screens interpret source-intended parallel/tangent directions within 1e-8 numerical tolerance; they are not exact-arithmetic infeasibility certificates for arbitrary nonzero geometric perturbations",
                "Contact hull point forces relax the actual distributed-pressure problem",
                "Lateral screw forces act at source head points; normal-force certificates do not depend on their axial application position",
                "Deferred hardware gravity and accessory loads are excluded; certificates refer to the stated panel and T-nut source loads",
                "Failure identifies missing restraint in this no-axial-credit idealization, not failure of actual screws or frame"],
            "native_fea_run": False, "mechanical_acceptance": False}


if __name__ == "__main__":
    result = screen()
    (HERE / "panel-path-screen.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"cases": [{"case": row["case_id"], "feasible": row["equilibrium_feasible"],
          "normal_certificates": len(row["normal_force_certificates"])} for row in result["cases"]]}, indent=2))
