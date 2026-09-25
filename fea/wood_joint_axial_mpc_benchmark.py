"""Prepare a tiny CalculiX check of a scalar mean-axial joint MPC.

This is a solver implementation benchmark only.  It never invokes CalculiX,
and its steel-like elastic fixture is not a bolt/thread property or a joint
capacity model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "fea" / "results" / "ccx_wood_joint_axial_mpc_benchmark"
DECK_NAME = "axial-mean-mpc.inp"
MANIFEST_NAME = "manifest.json"

SOLVER_IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
SOLVER_BINARY_SHA256 = (
    "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b"
)
MANUAL_PATH = "fea/generated/connection/ccx_2.21.pdf"
MANUAL_SHA256 = "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8"
MANUAL_URL = "https://www.dhondt.de/ccx_2.21.pdf"

# Units are mm, N, N/mm^2. The elastic constants are chosen for a clean
# analytic solver oracle only; they are not a delivered-bolt property claim.
BAR_LENGTH_MM = 100.0
BAR_WIDTH_MM = 10.0
BAR_AREA_MM2 = BAR_WIDTH_MM**2
ELASTIC_MODULUS_MPA = 200_000.0
POISSON_RATIO = 0.30
APPLIED_AXIAL_LOAD_N = 1_000.0
BOTTOM_NODES = tuple(range(1, 10))
TOP_NODES = tuple(range(10, 19))
NUT_NODES = tuple(range(21, 29))
REFERENCE_NODE = 900
ROTATION_NODE = 901

# Exact face-integrated shape-function weights for a 2x2 C3D8 cross-section.
TOP_AREA_WEIGHTS = {
    10: 1 / 16,
    11: 1 / 8,
    12: 1 / 16,
    13: 1 / 8,
    14: 1 / 4,
    15: 1 / 8,
    16: 1 / 16,
    17: 1 / 8,
    18: 1 / 16,
}

_GRID = ((0.0, 5.0, 10.0), (0.0, 5.0, 10.0))


def _nodes() -> list[tuple[int, float, float, float]]:
    result: list[tuple[int, float, float, float]] = []
    for layer, z in ((0, 0.0), (9, BAR_LENGTH_MM)):
        for j, y in enumerate(_GRID[1]):
            for i, x in enumerate(_GRID[0]):
                node = layer + j * 3 + i + 1
                result.append((node, x, y, z))
    # Finite 10 x 10 x 5 mm rigid nut surrogate; no nut elements/material.
    for node, x, y, z in (
        (21, 0.0, 0.0, 100.0),
        (22, 10.0, 0.0, 100.0),
        (23, 10.0, 10.0, 100.0),
        (24, 0.0, 10.0, 100.0),
        (25, 0.0, 0.0, 105.0),
        (26, 10.0, 0.0, 105.0),
        (27, 10.0, 10.0, 105.0),
        (28, 0.0, 10.0, 105.0),
    ):
        result.append((node, x, y, z))
    result.extend(
        (
            (REFERENCE_NODE, 5.0, 5.0, 100.0),
            # ROT NODE coordinates are immaterial, but it must be outside all
            # elements and carries the nut's three rotation DOFs as U1..U3.
            (ROTATION_NODE, 99.0, 99.0, 99.0),
        )
    )
    return result


def _equation_rows() -> list[str]:
    # Use the center face node as the eliminated/dependent DOF: its tributary
    # area is largest. Keep the loaded reference-node U3 independent.
    ordered_nodes = (14, 10, 11, 12, 13, 15, 16, 17, 18, REFERENCE_NODE)
    terms = [
        (node, 3, -1.0 if node == REFERENCE_NODE else TOP_AREA_WEIGHTS[node])
        for node in ordered_nodes
    ]
    rows = [str(len(terms))]
    for start in range(0, len(terms), 4):
        rows.append(
            ",".join(
                f"{node},{dof},{coefficient:.12g}"
                for node, dof, coefficient in terms[start : start + 4]
            )
        )
    return rows


def _nset_rows(nodes: tuple[int, ...], width: int = 16) -> list[str]:
    return [
        ",".join(str(node) for node in nodes[start : start + width])
        for start in range(0, len(nodes), width)
    ]


def render_deck() -> str:
    """Return the one-step, one-equation CalculiX input deck."""
    node_rows = [f"{n},{x:g},{y:g},{z:g}" for n, x, y, z in _nodes()]
    element_rows = (
        "1,1,2,5,4,10,11,14,13",
        "2,2,3,6,5,11,12,15,14",
        "3,4,5,8,7,13,14,17,16",
        "4,5,6,9,8,14,15,18,17",
    )
    return "\n".join(
        [
            "** CCX 2.21 scalar mean-axial MPC implementation benchmark only.",
            "** Four C3D8 elements form a 10 x 10 x 100 mm elastic bar surrogate.",
            "** Eight isolated nodes form a finite rigid-only nut surrogate.",
            "** One area-weighted mean-U3 equality joins the bar face to nut REF NODE.",
            "** No thread, contact, fit, transverse, bending, or capacity law is modeled.",
            "*NODE",
            *node_rows,
            "*ELEMENT,TYPE=C3D8,ELSET=BOLT",
            *element_rows,
            "*NSET,NSET=BOLT_BOTTOM",
            ",".join(str(n) for n in BOTTOM_NODES),
            "*NSET,NSET=BOLT_TOP",
            ",".join(str(n) for n in TOP_NODES),
            "*NSET,NSET=NUT_NODES",
            *_nset_rows(NUT_NODES),
            "*NSET,NSET=ALL_NODES",
            *_nset_rows(tuple(n for n, *_ in _nodes())),
            "*MATERIAL,NAME=ELASTIC_FIXTURE_ONLY",
            "*ELASTIC",
            f"{ELASTIC_MODULUS_MPA:g},{POISSON_RATIO:g}",
            "*SOLID SECTION,ELSET=BOLT,MATERIAL=ELASTIC_FIXTURE_ONLY",
            ",",
            f"*RIGID BODY,NSET=NUT_NODES,REF NODE={REFERENCE_NODE},ROT NODE={ROTATION_NODE}",
            "*EQUATION",
            *_equation_rows(),
            "*STEP,INC=10",
            "*STATIC",
            "1,1,1e-8,1",
            "*BOUNDARY",
            "BOLT_BOTTOM,3,3,0",
            "5,1,2,0",
            "6,2,2,0",
            f"{REFERENCE_NODE},1,2,0",
            f"{ROTATION_NODE},1,3,0",
            "*CLOAD",
            f"{REFERENCE_NODE},3,{APPLIED_AXIAL_LOAD_N:g}",
            "*NODE PRINT,NSET=ALL_NODES,FREQUENCY=1",
            "U,RF",
            "*EL PRINT,ELSET=BOLT,FREQUENCY=1",
            "S,E",
            "*END STEP",
            "",
        ]
    )


def analytical_oracle() -> dict[str, Any]:
    """Return the exact affine elastic-bar displacement and wrench oracle."""
    force = APPLIED_AXIAL_LOAD_N
    area = BAR_AREA_MM2
    strain_z = force / (area * ELASTIC_MODULUS_MPA)
    delta = strain_z * BAR_LENGTH_MM
    stress_z = force / area
    nodal_weights = {
        node: weight
        for node, weight in zip(BOTTOM_NODES, TOP_AREA_WEIGHTS.values(), strict=True)
    }
    reaction_by_node = {
        str(node): -force * weight for node, weight in nodal_weights.items()
    }
    support_force = (0.0, 0.0, -force)
    support_moment = (0.0, 0.0, 0.0)
    for node in nodal_weights:
        x = ((node - 1) % 3) * 5.0
        y = ((node - 1) // 3) * 5.0
        # At the bottom z=0, r x (0,0,Rz) = (y*Rz,-x*Rz,0).
        support_moment = (
            support_moment[0] + y * reaction_by_node[str(node)],
            support_moment[1] - x * reaction_by_node[str(node)],
            support_moment[2],
        )
    load_moment = (5.0 * force, -5.0 * force, 0.0)
    return {
        "axial_extension_mm": delta,
        "reference_node_u3_mm": delta,
        "weighted_bolt_face_mean_u3_mm": delta,
        "axial_strain": strain_z,
        "lateral_strain_x_y": -POISSON_RATIO * strain_z,
        "stress_mpa_voigt_11_22_33_12_13_23": [0.0, 0.0, stress_z, 0.0, 0.0, 0.0],
        "bottom_reaction_by_node_n_u3": reaction_by_node,
        "load_force_n": [0.0, 0.0, force],
        "support_force_n": list(support_force),
        "load_moment_about_global_origin_nmm": list(load_moment),
        "support_moment_about_global_origin_nmm": list(support_moment),
        "force_residual_n": [0.0, 0.0, force + support_force[2]],
        "moment_residual_nmm": [
            load_moment[axis] + support_moment[axis] for axis in range(3)
        ],
        "guide_reactions_expected": "zero; the uniaxial affine field satisfies each gauge exactly",
    }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_data(deck: str) -> dict[str, Any]:
    deck_bytes = deck.encode("utf-8")
    source_path = Path(__file__)
    return {
        "schema": "ccx-wood-joint-axial-mpc-benchmark/v1",
        "status": "PREPARED_NOT_SOLVED",
        "purpose": "Verify one explicit scalar area-weighted axial *EQUATION and a finite rigid nut surrogate against a geometrically linear elastic analytic coupon oracle.",
        "solver": {
            "product": "CalculiX CrunchiX",
            "version": "2.21",
            "pinned_image": SOLVER_IMAGE,
            "binary_sha256": SOLVER_BINARY_SHA256,
            "execution_status": "not_run; parent owns frozen native execution",
        },
        "manual": {
            "title": "CalculiX 2.21 User's Manual",
            "local_path": MANUAL_PATH,
            "sha256": MANUAL_SHA256,
            "url": MANUAL_URL,
            "keywords_used": [
                "*ELASTIC",
                "*EQUATION",
                "*RIGID BODY",
                "*NODE PRINT",
                "*EL PRINT",
            ],
        },
        "units": {"length": "mm", "force": "N", "stress": "N/mm^2", "moment": "N mm"},
        "fixture": {
            "bar_dimensions_mm": [BAR_WIDTH_MM, BAR_WIDTH_MM, BAR_LENGTH_MM],
            "bar_element_type": "C3D8",
            "bar_element_count": 4,
            "elastic_modulus_mpa": ELASTIC_MODULUS_MPA,
            "poisson_ratio": POISSON_RATIO,
            "material_notice": "Analytic benchmark fixture only; not the WJ24 delivered bolt's sourced material or thread stiffness.",
            "nut_surrogate": "eight nodes spanning 10 x 10 x 5 mm, rigid-only via *RIGID BODY; no nut solid elements or nut compliance",
        },
        "axial_endpoint": {
            "explicit_equation_count": 1,
            "law": "sum(A_i/A_face * bolt_top_U3_i) - nut_reference_U3 = 0",
            "bolt_top_area_weights": {
                str(node): weight for node, weight in TOP_AREA_WEIGHTS.items()
            },
            "dependent_dof": {"node": 14, "dof": 3},
            "nut_reference_node": REFERENCE_NODE,
            "loads_applied_to_dependent_dof": False,
            "other_endpoint_dofs": "not coupled; bolt/nut transverse motion and bolt-end rotation are outside this scalar axial diagnostic",
        },
        "guides_and_gauges": {
            "bolt_bottom_u3": list(BOTTOM_NODES),
            "bolt_center_bottom_u1_u2": 5,
            "bolt_spin_gauge_u2": 6,
            "nut_reference_u1_u2": REFERENCE_NODE,
            "nut_rotation_u1_u3": ROTATION_NODE,
            "reason": "Remove otherwise unloaded lateral translation and rigid spin only; exact affine uniaxial field satisfies these gauges with zero reaction.",
            "limitation": "These restraints create a one-axis coupon benchmark and do not represent support/contact conditions in the wood joint.",
        },
        "load": {
            "applied_at": {"node": REFERENCE_NODE, "dof": 3},
            "force_n": [0.0, 0.0, APPLIED_AXIAL_LOAD_N],
            "application_point_mm": [5.0, 5.0, BAR_LENGTH_MM],
        },
        "oracle": analytical_oracle(),
        "required_audit": [
            "one converged step endpoint",
            "U3 at reference node and area-weighted bolt-face mean agree with EA/L extension",
            "all four-element integration-point stress/strain match the uniform affine oracle",
            "bottom reaction sum and global-origin reaction wrench balance applied load",
            "transverse and rotation-gauge reactions are zero within numerical tolerance",
            "the explicit mean-U3 MPC residual is zero within numerical tolerance",
        ],
        "absolute_tolerances": {
            "reference_and_weighted_mean_displacement_mm": 1e-6,
            "mpc_residual_mm": 1e-6,
            "integration_point_stress_mpa": 0.02,
            "integration_point_strain": 1e-7,
            "bottom_nodal_reaction_n": 0.1,
            "global_force_residual_n": 0.1,
            "global_moment_residual_nmm": 1.0,
            "gauge_force_n": 0.1,
            "rotation_gauge_moment_nmm": 1.0,
        },
        "claim_boundary": [
            "MPC implementation verification only; not an actual bolt or nut test.",
            "No thread force law, contact, clearance, partial-thread engagement, seating, friction, capacity, or load sharing claim.",
            "No shear, bending, torsion, pull-through, wood bearing/splitting, fatigue, or joint acceptance result.",
        ],
        "artifacts": {
            "input_deck": DECK_NAME,
            "input_deck_sha256": _sha256_bytes(deck_bytes),
            "producer": "fea/wood_joint_axial_mpc_benchmark.py",
            "producer_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        },
    }


def prepare_artifacts(output_dir: Path = ARTIFACT_DIR) -> tuple[Path, Path]:
    """Write the deck and manifest; this function has no solver side effects."""
    output_dir.mkdir(parents=True, exist_ok=True)
    deck_path = output_dir / DECK_NAME
    manifest_path = output_dir / MANIFEST_NAME
    deck = render_deck()
    deck_path.write_text(deck, encoding="utf-8")
    manifest_path.write_text(
        json.dumps(manifest_data(deck), indent=2) + "\n", encoding="utf-8"
    )
    return deck_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ARTIFACT_DIR)
    args = parser.parse_args()
    deck, manifest = prepare_artifacts(args.output_dir)
    print(f"Prepared unsolved benchmark deck: {deck}")
    print(f"Prepared manifest: {manifest}")


if __name__ == "__main__":
    main()
