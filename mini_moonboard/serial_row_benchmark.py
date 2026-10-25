"""Elastic two-member serial-row benchmark for NDS group-action factors.

This is a mechanics benchmark, not a candidate-joint acceptance method. The
model has two axial bars with stiffnesses ``EA_main`` and ``EA_side``. Adjacent
row stations are joined by axial bar elements with stiffness ``EA / pitch``;
each station pair is joined by a slip spring with stiffness ``gamma``. The
boundary condition applies ``+P`` to the main member at the first row station
and ``-P`` to the side member at the last station. All other ends are free.

``compare_serial_row_to_nds`` obtains the NDS factor and its corrected
wood-to-wood ``gamma`` from the maintained, source-bound
``nds_2024_group_action`` evaluator. Its factor is compared with
``1 / (n * max(abs(bolt_force / P)))`` from this elastic model under the same
boundary condition. The helper uses synthetic, deterministic bindings only
to invoke the maintained equation implementation; they do not establish
source authority for any real connection.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any

from mini_moonboard.nds_2024_group_action import (
    SCHEMA_VERSION,
    SOURCE_ROLES,
    canonical_group_record_sha256,
    evaluate_group_action_factor,
)

LBF_TO_N = 4.4482216152605
IN_TO_MM = 25.4


@dataclass(frozen=True)
class SerialRowDistribution:
    """Bolt-force distribution and equilibrium diagnostics for one row."""

    fastener_count: int
    applied_load: float
    bolt_forces: tuple[float, ...]
    bolt_force_fractions: tuple[float, ...]
    max_force_fraction: float
    max_force_fastener_index: int
    cg_from_distribution: float
    total_transferred_force: float
    force_balance_residual: float
    force_balance_relative_residual: float
    boundary_condition: str = (
        "+P on main at first row station; -P on side at last row station"
    )


@dataclass(frozen=True)
class NDSBenchmarkComparison:
    """Comparison of the serial-row result with maintained NDS Eq. 11.3-1."""

    distribution: SerialRowDistribution
    nds_cg: float
    nds_gamma_lbf_per_in: float
    cg_difference: float
    matches_within_tolerance: bool
    comparison_scope: str = (
        "synthetic two-member wood-to-wood elastic serial row only; no candidate Cg"
    )


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _positive(name: str, value: Any) -> float:
    if not _finite_number(value) or value <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return float(value)


def _finite_nonzero(name: str, value: Any) -> float:
    if not _finite_number(value) or value == 0.0:
        raise ValueError(f"{name} must be finite and nonzero")
    return float(value)


def _validate_count(fastener_count: Any) -> int:
    if (
        isinstance(fastener_count, bool)
        or not isinstance(fastener_count, int)
        or fastener_count < 1
    ):
        raise ValueError("fastener_count must be a positive integer")
    return fastener_count


def _add_spring(matrix: list[list[float]], i: int, j: int, stiffness: float) -> None:
    matrix[i][i] += stiffness
    matrix[j][j] += stiffness
    matrix[i][j] -= stiffness
    matrix[j][i] -= stiffness


def _solve_dense(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve a small dense system by Gaussian elimination with pivoting."""
    size = len(rhs)
    augmented = [matrix[row][:] + [rhs[row]] for row in range(size)]
    if any(not math.isfinite(value) for row in augmented for value in row):
        raise ValueError("serial-row system overflowed finite arithmetic")

    for column in range(size):
        pivot_row = max(
            range(column, size), key=lambda row: abs(augmented[row][column])
        )
        pivot = augmented[pivot_row][column]
        if not math.isfinite(pivot) or pivot == 0.0:
            raise ValueError("serial-row stiffness system is singular")
        if pivot_row != column:
            augmented[column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[column],
            )

        pivot = augmented[column][column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot
            if factor == 0.0:
                continue
            augmented[row][column] = 0.0
            for entry in range(column + 1, size + 1):
                augmented[row][entry] -= factor * augmented[column][entry]

    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        remainder = augmented[row][size] - math.fsum(
            augmented[row][column] * solution[column]
            for column in range(row + 1, size)
        )
        solution[row] = remainder / augmented[row][row]
        if not math.isfinite(solution[row]):
            raise ValueError("serial-row displacement solution is not finite")
    return solution


def solve_serial_row(
    *,
    fastener_count: int,
    pitch: float,
    ea_main: float,
    ea_side: float,
    slip_modulus: float,
    load: float = 1.0,
) -> SerialRowDistribution:
    """Solve a two-bar elastic row using any one consistent unit system.

    ``ea_main`` and ``ea_side`` are axial stiffnesses in force units;
    ``pitch`` is length; and ``slip_modulus`` is force per length. ``load`` is
    a nonzero signed force. A singleton is supported as a mechanics control,
    although NDS §11.3.6.2's group-action row scope starts at two fasteners.
    """
    count = _validate_count(fastener_count)
    pitch_value = _positive("pitch", pitch)
    main_ea = _positive("ea_main", ea_main)
    side_ea = _positive("ea_side", ea_side)
    gamma = _positive("slip_modulus", slip_modulus)
    applied_load = _finite_nonzero("load", load)

    node_count = 2 * count
    stiffness = [[0.0] * node_count for _ in range(node_count)]
    main_bar_stiffness = main_ea / pitch_value
    side_bar_stiffness = side_ea / pitch_value
    if not math.isfinite(main_bar_stiffness) or not math.isfinite(side_bar_stiffness):
        raise ValueError("axial bar stiffness is outside finite arithmetic")

    for station in range(count - 1):
        _add_spring(stiffness, station, station + 1, main_bar_stiffness)
        _add_spring(
            stiffness,
            count + station,
            count + station + 1,
            side_bar_stiffness,
        )
    for station in range(count):
        _add_spring(stiffness, station, count + station, gamma)

    external = [0.0] * node_count
    external[0] = applied_load
    external[-1] = -applied_load

    # Remove the common translation mode by setting the first main-bar node
    # to zero. The applied forces sum to zero, so this reference constraint
    # creates no physical reaction.
    reduced_matrix = [row[1:] for row in stiffness[1:]]
    reduced_rhs = external[1:]
    reduced_displacements = _solve_dense(reduced_matrix, reduced_rhs)
    displacements = [0.0, *reduced_displacements]

    forces = tuple(
        gamma * (displacements[station] - displacements[count + station])
        for station in range(count)
    )
    if any(not math.isfinite(force) for force in forces):
        raise ValueError("serial-row bolt force is not finite")
    fractions = tuple(force / applied_load for force in forces)
    max_fraction = max(abs(fraction) for fraction in fractions)
    if not math.isfinite(max_fraction) or max_fraction <= 0.0:
        raise ValueError("serial-row force distribution is degenerate")

    transferred = math.fsum(forces)
    residual = transferred - applied_load
    relative_residual = abs(residual) / abs(applied_load)
    if not math.isfinite(relative_residual) or relative_residual > 1.0e-9:
        raise ValueError("serial-row bolt forces do not balance the applied load")

    return SerialRowDistribution(
        fastener_count=count,
        applied_load=applied_load,
        bolt_forces=forces,
        bolt_force_fractions=fractions,
        max_force_fraction=max_fraction,
        max_force_fastener_index=max(
            range(count), key=lambda index: abs(fractions[index])
        )
        + 1,
        cg_from_distribution=1.0 / (count * max_fraction),
        total_transferred_force=transferred,
        force_balance_residual=residual,
        force_balance_relative_residual=relative_residual,
    )


def imperial_row_inputs_to_si(
    *,
    pitch_in: float,
    ea_main_lbf: float,
    ea_side_lbf: float,
    slip_modulus_lbf_per_in: float,
    load_lbf: float = 1.0,
) -> dict[str, float]:
    """Convert consistent imperial serial-row inputs to N, mm, N/mm."""
    pitch_value = _positive("pitch_in", pitch_in)
    main_ea = _positive("ea_main_lbf", ea_main_lbf)
    side_ea = _positive("ea_side_lbf", ea_side_lbf)
    gamma = _positive("slip_modulus_lbf_per_in", slip_modulus_lbf_per_in)
    applied_load = _finite_nonzero("load_lbf", load_lbf)
    return {
        "pitch": pitch_value * IN_TO_MM,
        "ea_main": main_ea * LBF_TO_N,
        "ea_side": side_ea * LBF_TO_N,
        "slip_modulus": gamma * LBF_TO_N / IN_TO_MM,
        "load": applied_load * LBF_TO_N,
    }


def _synthetic_nds_record(
    *,
    fastener_count: int,
    diameter_in: float,
    pitch_in: float,
    elastic_modulus_main_psi: float,
    area_main_in2: float,
    elastic_modulus_side_psi: float,
    area_side_in2: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    main_id = "serial-row-main"
    side_id = "serial-row-side"
    bindings: dict[str, Any] = {
        role: {
            "source_id": f"synthetic-serial-row-benchmark/{role}",
            "sha256": hashlib.sha256(role.encode("ascii")).hexdigest(),
        }
        for role in SOURCE_ROLES
    }
    bindings["member_sections"].update(
        main_member_id=main_id,
        side_member_ids=[side_id],
        shear_planes=1,
    )
    record: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "candidate_id": "synthetic-only",
        "revision_id": "serial-row-benchmark-v1",
        "group_id": "one-row",
        "scenario_id": "opposite-end-force-transfer",
        "source_bindings": bindings,
        "group_geometry": {
            "row_axis_xyz": [1.0, 0.0, 0.0],
            "fasteners": [
                {
                    "fastener_id": f"bolt-{station + 1}",
                    "center_in": [station * pitch_in, 0.0, 0.0],
                    "nominal_diameter_in": diameter_in,
                    "type": "dowel",
                }
                for station in range(fastener_count)
            ],
        },
        "load_case": {
            "case_id": "unit-opposite-end-loads",
            "lateral_resultant_xyz_lbf": [1.0, 0.0, 0.0],
        },
        "members": {
            "shear_planes": 1,
            "main": {
                "member_id": main_id,
                "material": "wood",
                "elastic_modulus_psi": elastic_modulus_main_psi,
                "gross_section_area_in2": area_main_in2,
                "grain_axis_xyz": [1.0, 0.0, 0.0],
            },
            "side_members": [
                {
                    "member_id": side_id,
                    "material": "wood",
                    "elastic_modulus_psi": elastic_modulus_side_psi,
                    "gross_section_area_in2": area_side_in2,
                    "grain_axis_xyz": [1.0, 0.0, 0.0],
                }
            ],
        },
    }
    return record, bindings


def compare_serial_row_to_nds(
    *,
    fastener_count: int,
    diameter_in: float,
    pitch_in: float,
    elastic_modulus_main_psi: float,
    area_main_in2: float,
    elastic_modulus_side_psi: float,
    area_side_in2: float,
    load_lbf: float = 1.0,
    relative_tolerance: float = 1.0e-10,
    absolute_tolerance: float = 1.0e-12,
) -> NDSBenchmarkComparison:
    """Compare the elastic row distribution with maintained NDS Eq. 11.3-1.

    The NDS evaluator supplies both ``Cg`` and the corrected wood-to-wood
    slip modulus for the same synthetic geometry and member EA terms. Inputs
    are limited to the evaluator's two-member wood-to-wood row scope and to
    ``1/4 <= D <= 1 in``. A mismatch is reported as a boolean and difference;
    this function does not tune the boundary condition to force agreement.
    """
    count = _validate_count(fastener_count)
    if count < 2:
        raise ValueError("NDS group-action comparison requires at least two fasteners")
    diameter = _positive("diameter_in", diameter_in)
    if not 0.25 <= diameter <= 1.0:
        raise ValueError("NDS comparison requires 1/4 <= diameter_in <= 1")
    pitch = _positive("pitch_in", pitch_in)
    em = _positive("elastic_modulus_main_psi", elastic_modulus_main_psi)
    am = _positive("area_main_in2", area_main_in2)
    es = _positive("elastic_modulus_side_psi", elastic_modulus_side_psi)
    area_s = _positive("area_side_in2", area_side_in2)
    load = _finite_nonzero("load_lbf", load_lbf)
    if not _finite_number(relative_tolerance) or relative_tolerance < 0.0:
        raise ValueError("relative_tolerance must be finite and nonnegative")
    if not _finite_number(absolute_tolerance) or absolute_tolerance < 0.0:
        raise ValueError("absolute_tolerance must be finite and nonnegative")

    record, bindings = _synthetic_nds_record(
        fastener_count=count,
        diameter_in=diameter,
        pitch_in=pitch,
        elastic_modulus_main_psi=em,
        area_main_in2=am,
        elastic_modulus_side_psi=es,
        area_side_in2=area_s,
    )
    nds_result = evaluate_group_action_factor(
        record,
        expected_bindings=bindings,
        expected_payload_sha256=canonical_group_record_sha256(record),
    )
    if nds_result.get("status") != "calculated_method_only":
        raise ValueError(
            "maintained NDS evaluator rejected synthetic benchmark input: "
            + ", ".join(nds_result.get("reason_codes", []))
        )

    gamma = nds_result.get("gamma_lbf_per_in")
    nds_cg = nds_result.get("cg")
    if not _finite_number(gamma) or not _finite_number(nds_cg):
        raise ValueError("maintained NDS evaluator returned incomplete benchmark values")

    distribution = solve_serial_row(
        fastener_count=count,
        pitch=pitch,
        ea_main=em * am,
        ea_side=es * area_s,
        slip_modulus=gamma,
        load=load,
    )
    difference = distribution.cg_from_distribution - float(nds_cg)
    return NDSBenchmarkComparison(
        distribution=distribution,
        nds_cg=float(nds_cg),
        nds_gamma_lbf_per_in=float(gamma),
        cg_difference=difference,
        matches_within_tolerance=math.isclose(
            distribution.cg_from_distribution,
            float(nds_cg),
            rel_tol=float(relative_tolerance),
            abs_tol=float(absolute_tolerance),
        ),
    )
