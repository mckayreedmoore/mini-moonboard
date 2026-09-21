"""Provisional signed-equilibrium fixture for the active PB02 center topology.

This is a topology screen, not a candidate demand, stiffness solution, capacity
check, or fabrication release. It applies authenticated old-interface actions
as self-equilibrated replacement duties to the changed seven-body center.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from scripts.bolted_center_demand_extract import extract_files
from scripts.simple_center_connected_kinematics import (
    EDGES,
    NODES,
    ORIGIN,
    ROTATION_SCALE_MM,
    constraint_rows,
)
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT, ACTIVE_TRIAL

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/bolted-candidate-prototypes/center-reference-diagnostic.json"
MEMBER_TO_NODE = {
    "base_principal_center_right": "principal",
    "base_post_center_right": "post",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cross(first, second):
    return np.cross(np.asarray(first, dtype=float), np.asarray(second, dtype=float))


def _add_wrench(load, node, force, moment, point):
    """Add a global wrench using the kinematic model's scaled rotation datum."""
    force = np.asarray(force, dtype=float)
    moment_at_origin = np.asarray(moment, dtype=float) + _cross(
        np.asarray(point, dtype=float) - ORIGIN, force
    )
    start = 6 * NODES.index(node)
    load[start : start + 3] += force
    load[start + 3 : start + 6] += moment_at_origin / ROTATION_SCALE_MM


def _source_cases():
    """Re-extract all accepted old-proxy cases from authenticated raw artifacts."""
    archive = json.loads(ARCHIVE.read_text())
    cases = []
    for row in archive["accepted_default_v2"]:
        report = ROOT / row["source"]["report"]
        record = ROOT / row["source"]["record"]
        if (
            row["status"] != "accepted_proxy_reference"
            or _sha256(report) != row["source"]["report_sha256"]
            or _sha256(record) != row["source"]["record_sha256"]
        ):
            raise ValueError(f"Archived source identity failed: {row['case']}")
        extracted = extract_files(
            report,
            record,
            "base_principal_center_right",
            "base_post_center_right",
        )
        if extracted["source"]["case"] != row["case"]:
            raise ValueError("Extracted case identity changed")
        cases.append(extracted)
    return cases


def _fixture_load(extracted):
    """Apply both complete old-interface wrenches and exact header opposites."""
    load = np.zeros(6 * len(NODES))
    duties = []
    for name in ("principal_header", "post_header"):
        interface = extracted["interfaces"][name]
        member = interface["center_member"]
        node = MEMBER_TO_NODE[member]
        point = interface["origin_xyz_mm"]
        wrench = interface["on_center_member"]
        force = wrench["force_xyz_n"]
        moment = wrench["moment_xyz_nmm"]
        _add_wrench(load, node, force, moment, point)
        _add_wrench(
            load,
            "header",
            [-value for value in force],
            [-value for value in moment],
            point,
        )
        duties.append(
            {
                "old_interface": name,
                "mapped_node": node,
                "origin_xyz_mm": point,
                "complete_action_on_old_partner": wrench,
                "header_action_used": {
                    "force_xyz_n": [-value for value in force],
                    "moment_xyz_nmm": [-value for value in moment],
                },
                "source_interface_residual_passed": interface["residual"]["passed"],
            }
        )
    return load, duties


def _solve(
    load,
    *,
    contact,
    tension,
    omitted_contact_edges=(),
    omitted_tension_edges=(),
):
    rows = constraint_rows(closed=EDGES if contact else (), axial=tension)
    rows = [
        row
        for row in rows
        if not (
            row["kind"] == "contact_compression"
            and row["edge"] in omitted_contact_edges
        )
        and not (row["kind"] == "bolt_tension" and row["edge"] in omitted_tension_edges)
    ]
    matrix = np.asarray([row["row"] for row in rows]).T
    bounds = []
    for row in rows:
        if row["kind"] == "contact_compression":
            bounds.append((0, None))
        elif row["kind"] == "bolt_tension":
            # Positive gap is separation. Tension pulls the bodies together.
            bounds.append((None, 0))
        else:
            bounds.append((None, None))
    solved = linprog(
        np.zeros(len(rows)),
        A_eq=matrix,
        b_eq=-load,
        bounds=bounds,
        method="highs",
    )
    result = {
        "contact_rows": contact,
        "tension_rows": tension,
        "feasible": bool(solved.success),
        "solver_status": int(solved.status),
        "solver_message": solved.message,
    }
    if not solved.success:
        return result
    residual = matrix @ solved.x + load
    force_residual = []
    moment_residual = []
    for index in range(len(NODES)):
        force_residual.extend(residual[6 * index : 6 * index + 3])
        moment_residual.extend(
            residual[6 * index + 3 : 6 * index + 6] * ROTATION_SCALE_MM
        )
    result.update(
        {
            "max_force_residual_n": float(np.max(np.abs(force_residual))),
            "max_moment_residual_nmm": float(np.max(np.abs(moment_residual))),
        }
    )
    return result


def screen():
    """Return four signed reaction-model feasibility states for each old case."""
    cases = []
    for extracted in _source_cases():
        load, duties = _fixture_load(extracted)
        contact_omission = {
            edge: _solve(
                load,
                contact=True,
                tension=True,
                omitted_contact_edges=(edge,),
            )["feasible"]
            for edge in EDGES
        }
        tension_omission = {
            edge: _solve(
                load,
                contact=True,
                tension=True,
                omitted_tension_edges=(edge,),
            )["feasible"]
            for edge in EDGES
        }
        net_force = [float(load[offset::6].sum()) for offset in range(3)]
        net_moment = [
            float(load[offset::6].sum() * ROTATION_SCALE_MM) for offset in range(3, 6)
        ]
        cases.append(
            {
                "case": extracted["source"]["case"],
                "source": extracted["source"],
                "simultaneous_replacement_duties": duties,
                "self_equilibrium": {
                    "net_force_n": net_force,
                    "net_moment_about_model_origin_nmm": net_moment,
                },
                "reaction_models": {
                    "signed_contact_and_tension": _solve(
                        load, contact=True, tension=True
                    ),
                    "tension_only_no_contact": _solve(
                        load, contact=False, tension=True
                    ),
                    "contact_only_no_tension": _solve(
                        load, contact=True, tension=False
                    ),
                    "shear_only": _solve(load, contact=False, tension=False),
                },
                "single_edge_omission": {
                    "contact_edge_removal_feasible": contact_omission,
                    "tension_edge_removal_feasible": tension_omission,
                    "required_contact_edges_in_this_point_model": sorted(
                        edge
                        for edge, feasible in contact_omission.items()
                        if not feasible
                    ),
                    "required_tension_edges_in_this_point_model": sorted(
                        edge
                        for edge, feasible in tension_omission.items()
                        if not feasible
                    ),
                },
            }
        )
    return {
        "scope": "PB02 provisional signed replacement-duty equilibrium fixture",
        "variant_id": ACTIVE_TRIAL.variant_id,
        "source_fingerprint": ACTIVE_FINGERPRINT,
        "model": {
            "nodes": NODES,
            "edges": list(EDGES),
            "bolt_shear": "bilateral point action",
            "bolt_axial": "no-preload tension only",
            "face_contact": "compression only at four illustrative rank points",
        },
        "cases": cases,
        "limitations": [
            "Old complete interface actions are authenticated examples, not PB02 design demands.",
            "The five cases omit a12-forward and are not a complete envelope.",
            "Feasibility proves equilibrium only; it does not solve gaps, stiffness, compatibility, force sharing, strength, or pressure.",
            "Contact samples are illustrative rank points, not verified bearing patches.",
            "A feasible LP witness is nonunique and its reaction magnitudes are not design forces.",
        ],
        "strength_or_fabrication_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
