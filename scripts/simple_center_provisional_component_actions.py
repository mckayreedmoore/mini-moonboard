"""Assemble provisional PB02 component actions from solved spring reactions.

The source cases are authenticated historical actions used to exercise the
development topology.  They are not current PB02 design demands or strengths.
"""

import json

import numpy as np

from scripts.simple_center_connected_kinematics import (
    EDGES,
    NODES,
    ORIGIN,
    ROTATION_SCALE_MM,
)
from scripts.simple_center_signed_duty_fixture import _fixture_load, _source_cases
from scripts.simple_center_stiffness_sensitivity import screen as stiffness_screen

PATHS = {
    "header_to_post": ("post_block", "block_header"),
    "header_to_principal": (
        "header_principal_block",
        "principal_block_principal",
    ),
    "return_path": (
        "principal_upright_block",
        "upright_rear_block",
        "rear_block_post",
    ),
}
FORCE_TOLERANCE_N = 1e-5
MOMENT_TOLERANCE_NMM = 1e-3


def _vector(values):
    return [float(value) for value in values]


def _norm(values):
    return float(np.linalg.norm(values))


def _row_force_on_second(row):
    """Compatibility reaction convention: r*d on second, -r*d on first."""
    return float(row["signed_reaction_n"]) * np.asarray(row["direction"], dtype=float)


def _side_wrench(rows, side, center):
    force = np.zeros(3)
    moment = np.zeros(3)
    sign = 1.0 if side == "second" else -1.0
    center = np.asarray(center, dtype=float)
    for row in rows:
        row_force = sign * _row_force_on_second(row)
        force += row_force
        moment += np.cross(np.asarray(row["point_mm"], dtype=float) - center, row_force)
    return {
        "force_n": _vector(force),
        "moment_about_interface_center_nmm": _vector(moment),
    }


def _bolt_actions(edge_rows, edge):
    bolts = []
    bolt_count = len(EDGES[edge][3])
    for bolt_index in range(1, bolt_count + 1):
        prefix = f"{edge}/bolt_{bolt_index}/"
        selected = [row for row in edge_rows if row["name"].startswith(prefix)]
        shear_rows = [row for row in selected if row["kind"] == "bolt_shear"]
        tension_rows = [row for row in selected if row["kind"] == "bolt_tension"]
        if len(shear_rows) != 2 or len(tension_rows) != 1:
            raise ValueError(f"Unexpected PB02 row inventory for {prefix}")
        tension_row = tension_rows[0]
        shear_second = sum(
            (_row_force_on_second(row) for row in shear_rows), np.zeros(3)
        )
        axial_second = (
            _row_force_on_second(tension_row) if tension_row["active"] else np.zeros(3)
        )
        combined_second = shear_second + axial_second
        tension_n = (
            max(0.0, -float(tension_row["signed_reaction_n"]))
            if tension_row["active"]
            else 0.0
        )
        bolts.append(
            {
                "bolt": f"bolt_{bolt_index}",
                "point_mm": tension_row["point_mm"],
                "shear": {
                    "force_on_second_n": _vector(shear_second),
                    "force_on_first_n": _vector(-shear_second),
                    "magnitude_n": _norm(shear_second),
                },
                "axial_tension": {
                    "active": bool(tension_row["active"]),
                    "tension_n": tension_n,
                    "force_on_second_n": _vector(axial_second),
                    "force_on_first_n": _vector(-axial_second),
                },
                "combined": {
                    "force_on_second_n": _vector(combined_second),
                    "force_on_first_n": _vector(-combined_second),
                    "magnitude_n": _norm(combined_second),
                },
            }
        )
    return bolts


def _contact_actions(edge_rows, interface_center):
    contacts = [row for row in edge_rows if row["kind"] == "contact_compression"]
    if len(contacts) != 4:
        raise ValueError("Each PB02 face must retain four contact samples")
    return {
        "sample_count": len(contacts),
        "active_sample_count": sum(bool(row["active"]) for row in contacts),
        "on_first": _side_wrench(contacts, "first", interface_center),
        "on_second": _side_wrench(contacts, "second", interface_center),
    }


def _edge_actions(result):
    edges = {}
    for edge, (first, second, _, _, center) in EDGES.items():
        edge_rows = [row for row in result["rows"] if row["edge"] == edge]
        on_first = _side_wrench(edge_rows, "first", center)
        on_second = _side_wrench(edge_rows, "second", center)
        force_error = np.asarray(on_first["force_n"]) + np.asarray(on_second["force_n"])
        moment_error = np.asarray(
            on_first["moment_about_interface_center_nmm"]
        ) + np.asarray(on_second["moment_about_interface_center_nmm"])
        equal_opposite = {
            "force_residual_n": _vector(force_error),
            "moment_residual_nmm": _vector(moment_error),
            "maximum_force_residual_n": float(np.max(np.abs(force_error))),
            "maximum_moment_residual_nmm": float(np.max(np.abs(moment_error))),
        }
        equal_opposite["passed"] = (
            equal_opposite["maximum_force_residual_n"] <= FORCE_TOLERANCE_N
            and equal_opposite["maximum_moment_residual_nmm"] <= MOMENT_TOLERANCE_NMM
        )
        if not equal_opposite["passed"]:
            raise ValueError(f"PB02 interface actions are not equal-opposite: {edge}")
        edges[edge] = {
            "first": first,
            "second": second,
            "interface_center_mm": _vector(center),
            "bolts": _bolt_actions(edge_rows, edge),
            "face_contact": _contact_actions(edge_rows, center),
            "complete_interface_action": {
                "on_first": on_first,
                "on_second": on_second,
            },
            "equal_and_opposite_check": equal_opposite,
        }
    return edges


def _body_equilibrium(result, external_load):
    internal = {node: {"force": np.zeros(3), "moment": np.zeros(3)} for node in NODES}
    for row in result["rows"]:
        force_second = _row_force_on_second(row)
        point = np.asarray(row["point_mm"], dtype=float)
        for node, force in (
            (row["first"], -force_second),
            (row["second"], force_second),
        ):
            internal[node]["force"] += force
            internal[node]["moment"] += np.cross(point - ORIGIN, force)

    bodies = {}
    all_force_residuals = []
    all_moment_residuals = []
    for index, node in enumerate(NODES):
        start = 6 * index
        external_force = np.asarray(external_load[start : start + 3], dtype=float)
        # Fixture rotational entries are moments about ORIGIN divided by the
        # kinematic model's rotation scale. Recover physical N-mm directly from
        # the solver's already reported whole-body residual relationship.
        external_moment = (
            np.asarray(external_load[start + 3 : start + 6], dtype=float)
            * ROTATION_SCALE_MM
        )
        force_residual = internal[node]["force"] + external_force
        moment_residual = internal[node]["moment"] + external_moment
        all_force_residuals.extend(force_residual)
        all_moment_residuals.extend(moment_residual)
        bodies[node] = {
            "internal_reaction_wrench_about_origin": {
                "force_n": _vector(internal[node]["force"]),
                "moment_nmm": _vector(internal[node]["moment"]),
            },
            "matching_external_load_wrench_about_origin": {
                "force_n": _vector(external_force),
                "moment_nmm": _vector(external_moment),
            },
            "residual": {
                "force_n": _vector(force_residual),
                "moment_nmm": _vector(moment_residual),
                "maximum_force_component_n": float(np.max(np.abs(force_residual))),
                "maximum_moment_component_nmm": float(np.max(np.abs(moment_residual))),
            },
        }
    maximum_force = float(np.max(np.abs(all_force_residuals)))
    maximum_moment = float(np.max(np.abs(all_moment_residuals)))
    passed = (
        maximum_force <= FORCE_TOLERANCE_N and maximum_moment <= MOMENT_TOLERANCE_NMM
    )
    if not passed:
        raise ValueError("PB02 reconstructed body equilibrium failed")
    return {
        "moment_reference_mm": _vector(ORIGIN),
        "bodies": bodies,
        "maximum_force_residual_n": maximum_force,
        "maximum_moment_residual_nmm": maximum_moment,
        "passed": passed,
    }


def _path_groups(edges):
    return {
        name: {
            "ordered_edges": list(edge_names),
            "interfaces": {edge: edges[edge] for edge in edge_names},
            "wrenches_summed_as_capacity": False,
        }
        for name, edge_names in PATHS.items()
    }


def screen():
    """Return complete provisional component actions for all 50 solved records."""
    stiffness = stiffness_screen()
    source_loads = {
        extracted["source"]["case"]: _fixture_load(extracted)[0]
        for extracted in _source_cases()
    }
    records = []
    for result in stiffness["results"]:
        case = result["case"]
        edges = _edge_actions(result)
        records.append(
            {
                "case": case,
                "scenario": result["scenario"],
                "trial_stiffness_n_per_mm": result["trial_stiffness_n_per_mm"],
                "edges": edges,
                "body_equilibrium": _body_equilibrium(result, source_loads[case]),
                "path_groups": _path_groups(edges),
            }
        )
    if (
        len(records) != 50
        or len({(record["case"], record["scenario"]) for record in records}) != 50
    ):
        raise ValueError("Expected 50 unique PB02 case/scenario action records")
    return {
        "scope": "PB02 provisional component actions from historical spring cases",
        "variant_id": stiffness["variant_id"],
        "source_fingerprint": stiffness["source_fingerprint"],
        "reaction_convention": (
            "signed_reaction_n times direction acts on second; its opposite acts "
            "on first"
        ),
        "moment_conventions": {
            "interface_actions": "physical N-mm about EDGES[edge][4]",
            "body_equilibrium": "physical N-mm about ORIGIN",
        },
        "record_count": len(records),
        "records": records,
        "limitations": [
            "These are historical-action provisional results, not current PB02 design demands.",
            "The source set has no a12-forward case.",
            "No bolt, wood, contact, washer, block, or combined strength is checked.",
            "This report is not a structural, drilling, fabrication, or construction release.",
            "Case/scenario identity is preserved; no Frankenstein envelope combines unrelated maxima.",
            "Path groups organize serial interfaces and do not sum unrelated interface wrenches as capacity.",
        ],
        "strength_or_fabrication_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))
