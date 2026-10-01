#!/usr/bin/env python3
"""Regenerate the independent curved-TETRA10 quadrature reference JSON."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from aster_tetra10_mass import (
    FPG4_POINTS,
    FPG15_POINTS,
    FPG15_WEIGHTS,
    fpg15_reference,
    tetra10_inertia_duffy,
    tetra10_mass_matrix,
    tetra10_mass_matrix_duffy,
)


COORDS = np.array([
    [0.0, 0.0, 0.0], [100.0, 0.0, 0.0], [0.0, 100.0, 0.0], [0.0, 0.0, 100.0],
    [50.0, 0.0, 3.5], [50.0, 50.0, -2.0], [0.0, 50.0, 1.5],
    [0.0, 0.0, 50.0], [50.0, 0.0, 50.0], [0.0, 50.0, 50.0],
], dtype=float)
DENSITY = 7.85e-9  # tonne/mm^3
PIVOT = np.array([134.5, 1.178456090256, 410.856889078727])  # mm


def metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    delta = a - b
    return {
        "frobenius_relative_to_first": float(np.linalg.norm(delta) / np.linalg.norm(a)),
        "max_abs_entry": float(np.max(np.abs(delta))),
        "max_relative_entry": float(np.max(np.abs(delta) / np.maximum(np.abs(a), 1e-300))),
    }


def main() -> None:
    m15 = tetra10_mass_matrix(COORDS, DENSITY, "fpg15")
    m4 = tetra10_mass_matrix(COORDS, DENSITY, "fpg4")
    m6 = tetra10_mass_matrix_duffy(COORDS, DENSITY, order=6)
    m8 = tetra10_mass_matrix_duffy(COORDS, DENSITY, order=8)
    ref15 = fpg15_reference(COORDS, DENSITY, PIVOT)
    i6 = tetra10_inertia_duffy(COORDS, DENSITY, PIVOT, order=6)
    i8 = tetra10_inertia_duffy(COORDS, DENSITY, PIVOT, order=8)

    # Code_Aster's assembly ordering is read from NUME_DDL at runtime. This
    # auxiliary expansion is node-major DX,DY,DZ and is labelled as a layout
    # convention, not substituted for the native deck's explicit DOF map.
    full30_node_major = np.kron(m15, np.eye(3))
    data = {
        "schema": "independent-curved-tetra10-mass-reference-v1",
        "source_rule": {
            "solver_option": "CALC_MATR_ELEM(OPTION='MASS_MECA')",
            "reference": "Code_Aster v17 R3.01.01 volumetric elements, TETRA10/FPG15",
            "claim": "Pinned 17.4 native attempt01 matches the independent FPG15 matrix for this curved TETRA10; FPG15 is the discrete operator, separate in method from the physical integral",
        },
        "units": {"coordinates": "mm", "density": "tonne/mm^3", "mass": "tonne", "inertia": "tonne*mm^2"},
        "density": DENSITY,
        "pivot_mm": PIVOT.tolist(),
        "local_node_order": [
            "corner 1", "corner 2", "corner 3", "corner 4",
            "edge 1-2", "edge 2-3", "edge 3-1", "edge 1-4", "edge 2-4", "edge 3-4",
        ],
        "coordinates_mm": COORDS.tolist(),
        "quadrature": {
            "fpg15_point_count": int(len(FPG15_POINTS)),
            "fpg15_reference_volume_weight_sum": float(FPG15_WEIGHTS.sum()),
            "fpg15_det_j_min_mm3": ref15["det_j_min_fpg15"],
            "fpg15_det_j_max_mm3": ref15["det_j_max_fpg15"],
            "duffy_gl_order6_vs_order8_mass_frobenius_relative": metrics(m8, m6)["frobenius_relative_to_first"],
            "duffy_gl_order6_vs_order8_inertia_max_abs_tonne_mm2": float(np.max(np.abs(i8 - i6))),
        },
        "aster_candidate_fpg15": {
            "total_mass_tonne": float(m15.sum()),
            "centroid_mm": ref15["centroid"],
            "inertia_about_pivot_tonne_mm2": ref15["inertia_about_pivot"],
            "scalar_nodal_mass_matrix_10x10_tonne": m15.tolist(),
            "full_translation_matrix_30x30_node_major_tonne": full30_node_major.tolist(),
        },
        "physical_integral_high_order_duffy_gl8": {
            "total_mass_tonne": float(m8.sum()),
            "inertia_about_pivot_tonne_mm2": i8.tolist(),
            "scalar_nodal_mass_matrix_10x10_tonne": m8.tolist(),
            "description": "8x8x8 Duffy-transformed Gauss-Legendre evaluation; the degree-seven TETRA10 constant-density mass/inertia integrands are polynomial-exact for Duffy order >=6 (transformed degrees <=9,8,7); order 6/8 roundoff agreement is recorded above; independent of Aster FPG15",
        },
        "fpg4_discriminator_only": {
            "scalar_nodal_mass_matrix_10x10_tonne": m4.tolist(),
            "fpg4_vs_fpg15": metrics(m15, m4),
            "interpretation": "degree-2 rule used only as a matrix discriminator, not asserted as Aster MASS_MECA rule",
        },
        "native_probe_output": {
            "expected_shape": [30, 30],
            "expected_dofs": 30,
            "native_deck_exports_runtime_dof_map": True,
            "comparison": "reindex by returned node_name/component; compare all 30x30 entries using parent's frozen bounds",
        },
        "mapping_and_integration_note": "The quadratic isoparametric map is evaluated at each quadrature point. TETRA10 det(J) is generally cubic; multiplying by N_i*N_j gives degree up to seven. FPG15 is degree-five and can differ from the high-order physical integral on curved elements. Affine tetrahedra do not expose this distinction because det(J) is constant.",
    }
    out = Path(__file__).with_name("curved-tetra10-mass-reference.json")
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    print("FPG4/FPG15 relative Frobenius separation:", data["fpg4_discriminator_only"]["fpg4_vs_fpg15"]["frobenius_relative_to_first"])
    print("Duffy GL6/GL8 mass relative difference:", data["quadrature"]["duffy_gl_order6_vs_order8_mass_frobenius_relative"])


if __name__ == "__main__":
    main()
