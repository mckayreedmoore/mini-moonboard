#!/usr/bin/env python3
"""Generate and independently check the free C3D20 MATRIXSTORAGE fixture."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DECK_PATH = HERE / "elastic-cube-matrixstorage.inp"
NODE_COORDS = (
    (1, (0.0, 0.0, 0.0)),
    (2, (1.0, 0.0, 0.0)),
    (3, (1.0, 1.0, 0.0)),
    (4, (0.0, 1.0, 0.0)),
    (5, (0.0, 0.0, 1.0)),
    (6, (1.0, 0.0, 1.0)),
    (7, (1.0, 1.0, 1.0)),
    (8, (0.0, 1.0, 1.0)),
    (9, (0.5, 0.0, 0.0)),
    (10, (1.0, 0.5, 0.0)),
    (11, (0.5, 1.0, 0.0)),
    (12, (0.0, 0.5, 0.0)),
    (13, (0.5, 0.0, 1.0)),
    (14, (1.0, 0.5, 1.0)),
    (15, (0.5, 1.0, 1.0)),
    (16, (0.0, 0.5, 1.0)),
    (17, (0.0, 0.0, 0.5)),
    (18, (1.0, 0.0, 0.5)),
    (19, (1.0, 1.0, 0.5)),
    (20, (0.0, 1.0, 0.5)),
)
VOIGT_PAIRS = ((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1))
RANK_RTOL = 1e-8
RIGID_RTOL = 1e-8
ENERGY_RTOL = 5e-7
ENERGY_ATOL_REL = 2e-8


def require(condition, message):
    if not condition:
        raise ValueError(message)


def deck_text():
    angle = math.radians(37.0)
    cosine, sine = math.cos(angle), math.sin(angle)
    lines = [
        "*HEADING",
        "Free 1 mm orthotropic C3D20 matrix-storage method fixture",
        "*NODE",
    ]
    lines.extend(f"{node},{x:g},{y:g},{z:g}" for node, (x, y, z) in NODE_COORDS)
    lines.extend(
        [
            "*ELEMENT,TYPE=C3D20,ELSET=EALL",
            "1,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15",
            "16,17,18,19,20",
            "*MATERIAL,NAME=ORTHO",
            "*DENSITY",
            "1.0e-9",
            "*ELASTIC,TYPE=ENGINEERING CONSTANTS",
            "1200.,800.,600.,0.2,0.15,0.1,300.,250.",
            "200.",
            "*ORIENTATION,NAME=R37,SYSTEM=RECTANGULAR",
            f"{cosine:.16g},{sine:.16g},0.,{-sine:.16g},{cosine:.16g},0.",
            "*SOLID SECTION,ELSET=EALL,MATERIAL=ORTHO,ORIENTATION=R37",
            "*STEP",
            "*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES",
            "6",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines)


def parse_dof(text, node_count=20):
    """Map each node.direction string to its one-based matrix row."""
    rows = {}
    for line_number, raw in enumerate(text.splitlines(), 1):
        token = raw.strip()
        if not token:
            continue
        parts = token.split(".")
        require(
            len(parts) == 2
            and all(part.isascii() and part.isdecimal() for part in parts),
            f".dof line {line_number}: expected node.direction",
        )
        node, direction = map(int, parts)
        require(1 <= node <= node_count, f".dof line {line_number}: node out of range")
        require(
            direction in (1, 2, 3), f".dof line {line_number}: direction out of range"
        )
        key = (node, direction)
        require(key not in rows, f".dof line {line_number}: duplicate DOF {token}")
        rows[key] = len(rows)

    expected = {
        (node, direction)
        for node in range(1, node_count + 1)
        for direction in (1, 2, 3)
    }
    require(set(rows) == expected, ".dof is not a bijection over all cube translations")
    return rows


def parse_sti(text, size=60):
    """Reconstruct one symmetric matrix from a single stored triangle."""
    matrix = np.zeros((size, size), dtype=float)
    seen = set()
    diagonals = set()
    triangle = None
    entries = 0
    for line_number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        require(
            len(fields) == 3, f".sti line {line_number}: expected row, column, value"
        )
        require(
            all(field.isascii() and field.isdecimal() for field in fields[:2]),
            f".sti line {line_number}: indices must be positive integers",
        )
        row, column = map(int, fields[:2])
        require(
            1 <= row <= size and 1 <= column <= size,
            f".sti line {line_number}: index out of range",
        )
        try:
            value = float(fields[2].replace("D", "E").replace("d", "e"))
        except ValueError as error:
            raise ValueError(
                f".sti line {line_number}: invalid matrix value"
            ) from error
        require(
            math.isfinite(value), f".sti line {line_number}: nonfinite matrix value"
        )

        pair = (min(row, column), max(row, column))
        require(
            pair not in seen,
            f".sti line {line_number}: duplicate or mirrored entry {pair}",
        )
        seen.add(pair)
        if row == column:
            diagonals.add(row)
        if row != column:
            orientation = "upper" if row < column else "lower"
            require(
                triangle in (None, orientation), ".sti contains both matrix triangles"
            )
            triangle = orientation
        matrix[row - 1, column - 1] = value
        matrix[column - 1, row - 1] = value
        entries += 1

    require(entries > 0, ".sti contains no matrix entries")
    require(
        diagonals == set(range(1, size + 1)),
        ".sti is missing one or more diagonal entries",
    )
    require(np.array_equal(matrix, matrix.T), "symmetric reconstruction failed")
    return matrix


def local_compliance():
    """Engineering compliance for [11,22,33,23,13,12], in 1/MPa."""
    e1, e2, e3 = 1200.0, 800.0, 600.0
    nu12, nu13, nu23 = 0.2, 0.15, 0.1
    g12, g13, g23 = 300.0, 250.0, 200.0
    compliance = np.zeros((6, 6), dtype=float)
    compliance[0, 0], compliance[1, 1], compliance[2, 2] = 1 / e1, 1 / e2, 1 / e3
    compliance[0, 1] = compliance[1, 0] = -nu12 / e1
    compliance[0, 2] = compliance[2, 0] = -nu13 / e1
    compliance[1, 2] = compliance[2, 1] = -nu23 / e2
    compliance[3, 3], compliance[4, 4], compliance[5, 5] = 1 / g23, 1 / g13, 1 / g12
    return compliance


def global_engineering_stiffness(angle_degrees=37.0):
    """Invert compliance and rotate its fourth-order stiffness tensor to global axes."""
    compliance = local_compliance()
    local = np.linalg.inv(compliance)
    require(
        np.allclose(local, local.T, rtol=0.0, atol=1e-12),
        "local stiffness is not symmetric",
    )
    require(
        np.min(np.linalg.eigvalsh(local)) > 0,
        "local engineering constants are not positive definite",
    )

    tensor = np.zeros((3, 3, 3, 3), dtype=float)
    for i, (a, b) in enumerate(VOIGT_PAIRS):
        for j, (c, d) in enumerate(VOIGT_PAIRS):
            for p, q in {(a, b), (b, a)}:
                for r, s in {(c, d), (d, c)}:
                    tensor[p, q, r, s] = local[i, j]

    angle = math.radians(angle_degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    rotation = np.array(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    rotated = np.einsum(
        "iI,jJ,kK,lL,IJKL->ijkl", rotation, rotation, rotation, rotation, tensor
    )
    engineering = np.array(
        [[rotated[a, b, c, d] for c, d in VOIGT_PAIRS] for a, b in VOIGT_PAIRS],
        dtype=float,
    )
    require(
        np.allclose(engineering, engineering.T, rtol=0.0, atol=1e-10),
        "rotated stiffness is not symmetric",
    )
    return engineering


def rigid_modes(dof_rows):
    modes = np.zeros((60, 6), dtype=float)
    axes = np.eye(3)
    for node, xyz in NODE_COORDS:
        centered = np.asarray(xyz, dtype=float) - 0.5
        for direction in range(1, 4):
            row = dof_rows[(node, direction)]
            modes[row, direction - 1] = 1.0
            for axis in range(3):
                modes[row, axis + 3] = np.cross(axes[axis], centered)[direction - 1]
    return modes


def affine_strains(dof_rows):
    basis = np.zeros((60, 6), dtype=float)
    for column, (i, j) in enumerate(VOIGT_PAIRS):
        strain = np.zeros((3, 3), dtype=float)
        strain[i, j] = strain[j, i] = 1.0 if i == j else 0.5
        for node, xyz in NODE_COORDS:
            displacement = strain @ (np.asarray(xyz, dtype=float) - 0.5)
            for direction in range(1, 4):
                basis[dof_rows[(node, direction)], column] = displacement[direction - 1]
    return basis


def check_operator_matrix(stiffness, dof_rows, angle_degrees=37.0):
    require(stiffness.shape == (60, 60), "stiffness matrix must be 60 by 60")
    require(
        np.all(np.isfinite(stiffness)), "stiffness matrix contains nonfinite values"
    )
    require(np.array_equal(stiffness, stiffness.T), "stiffness matrix is not symmetric")
    eigenvalues = np.linalg.eigvalsh(stiffness)
    spectral_scale = float(np.max(np.abs(eigenvalues)))
    require(
        math.isfinite(spectral_scale) and spectral_scale > 0,
        "empty or invalid stiffness spectrum",
    )

    rigid = rigid_modes(dof_rows)
    rigid_work = np.einsum("ij,ij->j", rigid, stiffness @ rigid)
    rigid_scale = spectral_scale * np.einsum("ij,ij->j", rigid, rigid)
    rigid_work_ratio = np.abs(rigid_work) / rigid_scale
    require(
        np.max(rigid_work_ratio) <= RIGID_RTOL,
        "rigid motion has nonzero stiffness work",
    )
    rigid_residual = np.max(np.abs(stiffness @ rigid), axis=0) / (
        spectral_scale * np.max(np.abs(rigid), axis=0)
    )
    require(
        np.max(rigid_residual) <= RIGID_RTOL,
        "stiffness does not annihilate all rigid motions",
    )

    zero_modes = int(
        np.count_nonzero(np.abs(eigenvalues) <= RANK_RTOL * spectral_scale)
    )
    require(zero_modes == 6, f"expected six rigid eigenvalues, found {zero_modes}")
    nonrigid = eigenvalues[6:]
    require(len(nonrigid) == 54, "expected 54 non-rigid eigenvalues")
    require(
        np.min(nonrigid) > RANK_RTOL * spectral_scale,
        "non-rigid stiffness spectrum is not positive",
    )

    affine = affine_strains(dof_rows)
    actual_cross_energy = affine.T @ stiffness @ affine
    expected_cross_energy = global_engineering_stiffness(
        angle_degrees
    )  # volume is 1 mm^3
    difference = np.abs(actual_cross_energy - expected_cross_energy)
    energy_scale = float(np.max(np.abs(expected_cross_energy)))
    allowed = (
        ENERGY_RTOL * np.abs(expected_cross_energy) + ENERGY_ATOL_REL * energy_scale
    )
    require(np.all(difference <= allowed), "affine strain energy/cross-energy mismatch")
    return {
        "status": "PASS_SMALL_FIXTURE_OPERATOR_CHECKS_ONLY",
        "dofs": len(dof_rows),
        "zero_modes": zero_modes,
        "positive_nonrigid_modes": len(nonrigid),
        "minimum_nonrigid_eigenvalue": float(np.min(nonrigid)),
        "maximum_rigid_work_ratio": float(np.max(rigid_work_ratio)),
        "maximum_affine_energy_error_N_mm": float(np.max(difference)),
        "matrix_files_checked": False,
        "native_provenance_validated": False,
    }


def validate_operator(sti_text, dof_text):
    dof_rows = parse_dof(dof_text)
    stiffness = parse_sti(sti_text, size=len(dof_rows))
    result = check_operator_matrix(stiffness, dof_rows)
    result["matrix_files_checked"] = True
    return result


def expect_rejected(function, message):
    try:
        function()
    except ValueError as error:
        require(
            message in str(error), f"fixture rejected for the wrong reason: {error}"
        )
        return
    raise AssertionError("invalid fixture was accepted")


def known_operator(dof_rows, angle_degrees=37.0):
    """Construct an algebraic oracle only; this is not an FE element kernel."""
    constitutive = global_engineering_stiffness(angle_degrees)
    rigid = rigid_modes(dof_rows)
    affine = affine_strains(dof_rows)
    rigid_q, _ = np.linalg.qr(rigid, mode="reduced")
    projected_affine = affine - rigid_q @ (rigid_q.T @ affine)
    gram = affine.T @ projected_affine
    gram_inverse = np.linalg.inv(gram)
    material_space = (
        projected_affine
        @ gram_inverse
        @ constitutive
        @ gram_inverse
        @ projected_affine.T
    )
    basis, _ = np.linalg.qr(
        np.column_stack((rigid_q, projected_affine)), mode="reduced"
    )
    complete_basis, _ = np.linalg.qr(basis, mode="complete")
    complement_basis = complete_basis[:, 12:]
    complement = complement_basis @ complement_basis.T
    operator = material_space + 500.0 * complement
    return (operator + operator.T) / 2.0, complement_basis


def self_test():
    deck = deck_text()
    element_block = deck.split("*ELEMENT,TYPE=C3D20,ELSET=EALL\n", 1)[1].split(
        "\n*MATERIAL", 1
    )[0]
    element_lines = [line for line in element_block.splitlines() if line.strip()]
    connectivity = [int(value) for line in element_lines for value in line.split(",")]
    require(
        len(element_lines) == 2 and connectivity == [1, *range(1, 21)],
        "generated C3D20 continuation lost or reordered nodes",
    )
    require(
        [len(line.split(",")) for line in element_lines] == [16, 5],
        "generated C3D20 continuation exceeds the native line-entry limit",
    )
    require(
        all(
            keyword not in deck
            for keyword in ("*BOUNDARY", "*MPC", "*SPRING", "*CLOAD", "*DLOAD")
        ),
        "known-answer deck contains a constraint, spring, or load",
    )
    require(
        deck.rstrip().endswith("*END STEP"),
        "MATRIXSTORAGE frequency step is not terminal",
    )

    valid_dof = "\n".join(
        f"{node}.{direction}" for node in range(20, 0, -1) for direction in (3, 2, 1)
    )
    mapping = parse_dof(valid_dof)
    require(mapping[(20, 3)] == 0 and len(mapping) == 60, "valid .dof fixture failed")
    invalid = [
        (lambda: parse_dof(valid_dof + "\n1.1"), "duplicate DOF"),
        (lambda: parse_dof("\n".join(valid_dof.splitlines()[1:])), "not a bijection"),
        (lambda: parse_dof(valid_dof.replace("20.3", "21.3")), "node out of range"),
        (
            lambda: parse_dof(valid_dof.replace("20.3", "20.4")),
            "direction out of range",
        ),
    ]

    fixture = "1 1 4\n1 2 1\n2 2 3\n2 3 -2\n3 3 5\n"
    known = np.array([[4.0, 1.0, 0.0], [1.0, 3.0, -2.0], [0.0, -2.0, 5.0]])
    reconstructed = parse_sti(fixture, size=3)
    require(
        np.array_equal(reconstructed, known), "exact symmetric operator fixture failed"
    )
    invalid.extend(
        [
            (
                lambda: parse_sti(fixture + "1 1 4\n", size=3),
                "duplicate or mirrored entry",
            ),
            (
                lambda: parse_sti(fixture + "2 1 1\n", size=3),
                "duplicate or mirrored entry",
            ),
            (
                lambda: parse_sti(fixture + "2 1 9\n", size=3),
                "duplicate or mirrored entry",
            ),
            (
                lambda: parse_sti("1 1 2\n1 2 3\n3 2 4\n", size=3),
                "both matrix triangles",
            ),
            (lambda: parse_sti("1 1 nan\n", size=3), "nonfinite matrix value"),
            (lambda: parse_sti("1 1 inf\n", size=3), "nonfinite matrix value"),
            (lambda: parse_sti("0 1 2\n", size=3), "index out of range"),
            (lambda: parse_sti("4 4 2\n", size=3), "index out of range"),
            (lambda: parse_sti("1 4 2\n", size=3), "index out of range"),
            (lambda: parse_sti("1 1 2\n", size=3), "missing one or more diagonal"),
            (
                lambda: parse_sti("1.0 1 2\n", size=3),
                "indices must be positive integers",
            ),
        ]
    )

    for function, message in invalid:
        expect_rejected(function, message)

    local = np.linalg.inv(local_compliance())
    global_zero = global_engineering_stiffness(angle_degrees=0.0)
    require(
        np.allclose(local, global_zero, rtol=1e-13, atol=1e-12),
        "zero-angle tensor fixture failed",
    )
    rotated = global_engineering_stiffness()
    require(
        rotated.shape == (6, 6) and np.min(np.linalg.eigvalsh(rotated)) > 0,
        "rotated tensor fixture failed",
    )

    operator, complement_basis = known_operator(mapping)
    synthetic_sti = "\n".join(
        f"{row + 1} {column + 1} {operator[row, column]:.17g}"
        for row in range(60)
        for column in range(row, 60)
    )
    valid_result = validate_operator(synthetic_sti, valid_dof)
    require(
        valid_result["zero_modes"] == 6
        and valid_result["matrix_files_checked"]
        and not valid_result["native_provenance_validated"],
        "synthetic exact operator validation fixture failed",
    )
    mode = complement_basis[:, 0]
    extra_mechanism = operator - 500.0 * np.outer(mode, mode)
    expect_rejected(
        lambda: check_operator_matrix(extra_mechanism, mapping),
        "expected six rigid eigenvalues",
    )
    negative_mode = operator - 1000.0 * np.outer(mode, mode)
    expect_rejected(
        lambda: check_operator_matrix(negative_mode, mapping),
        "non-rigid stiffness spectrum is not positive",
    )
    wrong_orientation, _ = known_operator(mapping, angle_degrees=0.0)
    expect_rejected(
        lambda: check_operator_matrix(wrong_orientation, mapping),
        "affine strain energy/cross-energy mismatch",
    )
    return {
        "invalid_parser_fixtures_rejected": len(invalid),
        "exact_known_operator_reconstructed": True,
        "synthetic_operator_checks": 1,
        "operator_corruptions_rejected": 3,
        "affine_basis_modes_checked": 6,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-input", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-results", nargs=2, metavar=("STI", "DOF"))
    arguments = parser.parse_args()
    if not (arguments.write_input or arguments.self_test or arguments.check_results):
        parser.error("choose --write-input, --self-test, or --check-results STI DOF")
    result = {}
    if arguments.self_test:
        result["self_test"] = self_test()
    if arguments.write_input:
        DECK_PATH.write_text(deck_text(), encoding="utf-8")
        result["proposed_input"] = str(DECK_PATH)
    if arguments.check_results:
        sti_path, dof_path = map(Path, arguments.check_results)
        result.update(
            validate_operator(
                sti_path.read_text(encoding="utf-8"),
                dof_path.read_text(encoding="utf-8"),
            )
        )
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
