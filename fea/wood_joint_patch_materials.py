"""Proposal-only orthotropic material inputs and grain-frame transforms.

The only elastic values in this module are the nine scenario values recorded
in ``docs/wood-joints-mvp/orthotropic-material-scenario.md``.  They are an
unmeasured diagnostic proposal, not stock properties or a resistance law.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA = "wood_joint_patch_material_scenario/v1"
SCENARIO_ID = "douglas_fir_orthotropic_elastic_diagnostic_2026-09-24"
STATUS = "proposal_only_unmeasured_unaccepted"
SOURCE_DOCUMENT = "docs/wood-joints-mvp/orthotropic-material-scenario.md"
SOURCE_DOCUMENT_SHA256 = "f6b723ddfc911284958df7a5348162f6d659396bbc03b83a74fcfbb125b3477f"
CALCULIX_MANUAL_PATH = "fea/generated/connection/ccx_2.21.pdf"
CALCULIX_MANUAL_SHA256 = "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8"
CALCULIX_MANUAL_SECTIONS = (
    "7.46 *ELASTIC",
    "7.102 *ORIENTATION",
)
LOCAL_AXIS_NAMES = ("X", "T", "N")

# CalculiX TYPE=ENGINEERING CONSTANTS order.  Material axes are L, R, T;
# these names do not refer to CAD axes with the same letters.
ENGINEERING_CONSTANT_ORDER = (
    "E_L",
    "E_R",
    "E_T",
    "nu_LR",
    "nu_LT",
    "nu_RT",
    "G_LR",
    "G_LT",
    "G_RT",
)
SCENARIO_CONSTANTS_MPA = (
    11032.0,
    750.176,
    551.6,
    0.292,
    0.449,
    0.390,
    706.048,
    860.496,
    77.224,
)
COMPLIANCE_VOIGT_ORDER = ("11", "22", "33", "12", "13", "23")
SHEAR_STRAIN_CONVENTION = "engineering shear: gamma_ij = 2 * epsilon_ij"

LIMITATIONS = (
    "Proposal-only Douglas-fir elastic diagnostic; not measured properties of purchased stock.",
    "This mixed NDS/FPL scenario is not a grade-specific measured clear-wood property set.",
    "No strength, embedment, splitting, crushing, or resistance claim.",
    "Unknown growth-ring orientation is represented by separate R/T frame cases.",
    "This mathematical admissibility check is not physical calibration or acceptance.",
)


def _finite_constants(values: Sequence[float]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("Require nine finite engineering constants")
    try:
        raw = tuple(values)
    except TypeError as error:
        raise TypeError("Require nine finite engineering constants") from error
    if len(raw) != 9:
        raise ValueError("Require nine finite engineering constants")
    if any(isinstance(value, bool) for value in raw):
        raise TypeError("Boolean values are not elastic constants")
    try:
        constants = tuple(float(value) for value in raw)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Require nine finite engineering constants") from error
    if not all(math.isfinite(value) for value in constants):
        raise ValueError("Require nine finite engineering constants")
    return constants


def _compliance_matrix(constants: tuple[float, ...]) -> tuple[tuple[float, ...], ...]:
    e_l, e_r, e_t, nu_lr, nu_lt, nu_rt, g_lr, g_lt, g_rt = constants
    rows = [[0.0] * 6 for _ in range(6)]
    rows[0][0] = 1.0 / e_l
    rows[1][1] = 1.0 / e_r
    rows[2][2] = 1.0 / e_t
    rows[0][1] = rows[1][0] = -nu_lr / e_l
    rows[0][2] = rows[2][0] = -nu_lt / e_l
    rows[1][2] = rows[2][1] = -nu_rt / e_r
    # Engineering shear strain gamma_ij has compliance 1/G_ij.
    rows[3][3] = 1.0 / g_lr
    rows[4][4] = 1.0 / g_lt
    rows[5][5] = 1.0 / g_rt
    return tuple(tuple(row) for row in rows)


def _cholesky_lower(matrix: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    size = len(matrix)
    lower = [[0.0] * size for _ in range(size)]
    for row in range(size):
        if len(matrix[row]) != size:
            raise ValueError("Compliance matrix must be square")
        for column in range(row + 1):
            value = float(matrix[row][column]) - math.fsum(
                lower[row][k] * lower[column][k] for k in range(column)
            )
            if row == column:
                if not math.isfinite(value) or value <= 0.0:
                    raise ValueError("Elastic compliance must be positive definite")
                lower[row][column] = math.sqrt(value)
            else:
                pivot = lower[column][column]
                if pivot <= 0.0:
                    raise ValueError("Elastic compliance must be positive definite")
                lower[row][column] = value / pivot
    return tuple(tuple(row) for row in lower)


def validate_engineering_constants(values: Sequence[float]) -> dict[str, Any]:
    """Validate reciprocal orthotropic compliance and return its audit record.

    Inputs follow CalculiX ``*ELASTIC,TYPE=ENGINEERING CONSTANTS`` order:
    ``E1,E2,E3,nu12,nu13,nu23,G12,G13,G23``.  Poisson ratios are defined here
    with the first subscript as stress direction and the second as transverse
    strain direction.  Positive definiteness is checked on the full symmetric
    compliance matrix, including engineering-shear terms.
    """

    constants = _finite_constants(values)
    e_l, e_r, e_t, nu_lr, nu_lt, nu_rt, g_lr, g_lt, g_rt = constants
    if min(e_l, e_r, e_t, g_lr, g_lt, g_rt) <= 0.0:
        raise ValueError("Young's and shear moduli must be positive")

    compliance = _compliance_matrix(constants)
    # Confirm symmetry explicitly before factorization so malformed future
    # changes cannot be hidden by the lower-triangular Cholesky pass.
    for row in range(6):
        for column in range(6):
            if not math.isclose(
                compliance[row][column], compliance[column][row],
                rel_tol=0.0, abs_tol=1e-15,
            ):
                raise ValueError("Elastic compliance must be symmetric")
    lower = _cholesky_lower(compliance)
    reciprocal = {
        "nu_RL": nu_lr * e_r / e_l,
        "nu_TL": nu_lt * e_t / e_l,
        "nu_TR": nu_rt * e_t / e_r,
    }
    return {
        "constants": constants,
        "engineering_constant_order": ENGINEERING_CONSTANT_ORDER,
        "compliance_voigt_order": COMPLIANCE_VOIGT_ORDER,
        "shear_strain_convention": SHEAR_STRAIN_CONVENTION,
        "compliance_matrix_mpa_inv": compliance,
        "compliance_cholesky_diagonal": tuple(lower[index][index] for index in range(6)),
        "derived_reciprocal_poisson_ratios": reciprocal,
        "positive_definite": True,
    }


def material_scenario() -> dict[str, Any]:
    """Return the exact dated, proposal-only nine-constant scenario record."""

    audit = validate_engineering_constants(SCENARIO_CONSTANTS_MPA)
    record = {
        "schema": SCHEMA,
        "scenario_id": SCENARIO_ID,
        "status": STATUS,
        "material_basis": "Douglas-fir diagnostic elastic scenario",
        "source_document": SOURCE_DOCUMENT,
        "source_document_sha256": SOURCE_DOCUMENT_SHA256,
        "source_basis": (
            "Declared E_L = 11032 MPa scenario with Douglas-fir USDA Wood Handbook "
            "elastic ratios; reciprocal Poisson ratios are derived for a symmetric law"
        ),
        "solver_input_format_reference": {
            "document": CALCULIX_MANUAL_PATH,
            "sha256": CALCULIX_MANUAL_SHA256,
            "version": "2.21",
            "sections": CALCULIX_MANUAL_SECTIONS,
        },
        "units": {"moduli": "MPa", "compliance": "MPa^-1"},
        "material_axis_names": ("L", "R", "T"),
        "material_axis_meaning": {
            "L": "longitudinal grain direction",
            "R": "radial transverse direction",
            "T": "tangential transverse direction",
        },
        "calculix_engineering_constants": audit["constants"],
        "engineering_constant_order": audit["engineering_constant_order"],
        "compliance_voigt_order": audit["compliance_voigt_order"],
        "shear_strain_convention": audit["shear_strain_convention"],
        "compliance_matrix_mpa_inv": audit["compliance_matrix_mpa_inv"],
        "compliance_cholesky_diagonal": audit["compliance_cholesky_diagonal"],
        "derived_reciprocal_poisson_ratios": audit[
            "derived_reciprocal_poisson_ratios"
        ],
        "positive_definite": audit["positive_definite"],
        "stock_properties_measured": False,
        "grade_specific_measured_properties_claim": False,
        "qualified_for_design": False,
        "resistance_claim": False,
        "limitations": LIMITATIONS,
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
    record["scenario_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return record


def _vec3(value: Any, context: str) -> tuple[float, float, float]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{context}: expected a finite three-component vector")
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite three-component vector") from error
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{context}: expected a finite three-component vector")
    return result  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _orientation_axes(
    orientation: Mapping[str, Any],
) -> dict[str, tuple[float, float, float]]:
    axes = orientation.get("material_axes_global_xyz")
    if not isinstance(axes, Mapping) or set(axes) != {"L", "R", "T"}:
        raise ValueError("orientation must contain global L/R/T axes")
    basis = {name: _unit(axes[name], f"material {name} axis") for name in ("L", "R", "T")}
    if (
        abs(_dot(basis["L"], basis["R"])) > 1e-8
        or abs(_dot(basis["L"], basis["T"])) > 1e-8
        or abs(_dot(basis["R"], basis["T"])) > 1e-8
        or _dot(_cross(basis["L"], basis["R"]), basis["T"]) < 1.0 - 1e-8
    ):
        raise ValueError("orientation axes must be an orthonormal right-handed L/R/T frame")
    return basis


def _unit(value: Any, context: str) -> tuple[float, float, float]:
    vector = _vec3(value, context)
    length = math.sqrt(_dot(vector, vector))
    if not math.isfinite(length) or length <= 0.0:
        raise ValueError(f"{context}: expected a nonzero unit direction")
    if not math.isclose(length, 1.0, rel_tol=0.0, abs_tol=1e-8):
        raise ValueError(f"{context}: source direction must already be unit length")
    return vector


def member_orientation(
    grain_frame: Mapping[str, Any], *, radial_axis_local_name: str
) -> dict[str, Any]:
    """Bind one explicit L/R/T material frame to a source grain/local frame.

    ``radial_axis_local_name`` is required because the ring orientation is not
    identified by a grain vector alone.  The remaining transverse vector is
    signed to make the material frame right-handed.  Orthotropic axes have no
    polarity, so this retains the selected radial/tangential directions while
    satisfying the rectangular local-frame convention.
    """

    if not isinstance(grain_frame, Mapping):
        raise TypeError("grain frame must be a mapping from the source inventory")
    grain_name = grain_frame.get("grain_axis_local_name")
    if grain_name not in LOCAL_AXIS_NAMES:
        raise ValueError("grain frame must name an explicit X, T, or N grain axis")
    axes_raw = grain_frame.get("local_axes_global_xyz")
    if not isinstance(axes_raw, Mapping) or set(axes_raw) != set(LOCAL_AXIS_NAMES):
        raise ValueError("grain frame must contain exactly the explicit X/T/N axes")
    axes = {name: _unit(axes_raw[name], f"source {name} axis") for name in LOCAL_AXIS_NAMES}
    for index, first in enumerate(LOCAL_AXIS_NAMES):
        for second in LOCAL_AXIS_NAMES[index + 1 :]:
            if abs(_dot(axes[first], axes[second])) > 1e-8:
                raise ValueError("source X/T/N axes must be orthogonal")
    if _dot(_cross(axes["X"], axes["T"]), axes["N"]) < 1.0 - 1e-8:
        raise ValueError("source X/T/N frame must be right-handed")

    grain = _unit(grain_frame.get("grain_axis_global_xyz"), "source grain vector")
    if abs(_dot(grain, axes[grain_name])) < 1.0 - 1e-8:
        raise ValueError("source grain vector must align with its named local axis")
    if radial_axis_local_name not in LOCAL_AXIS_NAMES or radial_axis_local_name == grain_name:
        raise ValueError("radial axis must be one of the two transverse source axes")

    other_transverse = next(
        name for name in LOCAL_AXIS_NAMES
        if name not in {grain_name, radial_axis_local_name}
    )
    longitudinal = grain
    radial = axes[radial_axis_local_name]
    tangential = _cross(longitudinal, radial)
    if abs(_dot(tangential, axes[other_transverse])) < 1.0 - 1e-8:
        raise ValueError("source transverse axes do not complete the grain frame")

    axes_lrt = {"L": longitudinal, "R": radial, "T": tangential}
    orientation_points = (*longitudinal, *radial)
    return {
        "schema": "wood_joint_material_orientation/v1",
        "status": "explicit_source_grain_with_ring_orientation_scenario",
        "source_grain_axis_local_name": grain_name,
        "radial_axis_local_name": radial_axis_local_name,
        "tangential_axis_local_name": other_transverse,
        "material_axes_global_xyz": axes_lrt,
        # CalculiX rectangular *ORIENTATION takes point a on local X' and
        # point b in the X'-Y' plane.  Unit direction coordinates from global
        # origin give local X'=L, Y'=R, Z'=L cross R=T.
        "calculix_orientation_points_global_xyz": orientation_points,
        "right_handed": True,
        "proposal_only": True,
    }


def material_orientation_cases(grain_frame: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Return both transverse assignments required when ring orientation is unknown."""

    if not isinstance(grain_frame, Mapping):
        raise TypeError("grain frame must be a mapping from the source inventory")
    grain_name = grain_frame.get("grain_axis_local_name")
    if grain_name not in LOCAL_AXIS_NAMES:
        raise ValueError("grain frame must name an explicit X, T, or N grain axis")
    transverse = tuple(name for name in LOCAL_AXIS_NAMES if name != grain_name)
    cases = []
    for radial_name in transverse:
        row = member_orientation(grain_frame, radial_axis_local_name=radial_name)
        row["scenario_id"] = f"ring_R_on_{radial_name}"
        cases.append(row)
    return tuple(cases)


def to_material_components(
    global_vector: Sequence[float], orientation: Mapping[str, Any]
) -> tuple[float, float, float]:
    """Resolve a global vector into the orientation's L/R/T components."""

    vector = _vec3(global_vector, "global vector")
    basis = _orientation_axes(orientation)
    return tuple(_dot(vector, basis[name]) for name in ("L", "R", "T"))


def to_global_components(
    material_vector: Sequence[float], orientation: Mapping[str, Any]
) -> tuple[float, float, float]:
    """Resolve L/R/T vector components into global XYZ components."""

    components = _vec3(material_vector, "material vector")
    basis = _orientation_axes(orientation)
    return tuple(
        math.fsum(components[index] * basis[name][coordinate]
                  for index, name in enumerate(("L", "R", "T")))
        for coordinate in range(3)
    )


_CARD_NAME_RE = re.compile(r"[A-Z][A-Z0-9_]{0,79}\Z")


def _card_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("CalculiX card name must be text")
    normalized = name.upper()
    if not _CARD_NAME_RE.fullmatch(normalized):
        raise ValueError("CalculiX card name must start with a letter and use A-Z, 0-9, or _")
    return normalized


def render_material_card(name: str = "WOOD_PROPOSAL") -> str:
    """Render the proposal constants and revalidate their written decimal values."""

    card_name = _card_name(name)
    original = material_scenario()["calculix_engineering_constants"]
    formatted = tuple(format(value, ".17g") for value in original)
    deck_values = tuple(float(value) for value in formatted)
    validate_engineering_constants(deck_values)
    return (
        f"*MATERIAL,NAME={card_name}\n"
        "*ELASTIC,TYPE=ENGINEERING CONSTANTS\n"
        + ",".join(formatted[:8])
        + "\n"
        + formatted[8]
    )


def render_orientation_card(name: str, orientation: Mapping[str, Any]) -> str:
    """Render one CalculiX rectangular orientation card from the bound L/R frame."""

    card_name = _card_name(name)
    points = orientation.get("calculix_orientation_points_global_xyz")
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)) or len(points) != 6:
        raise ValueError("orientation does not contain six CalculiX point coordinates")
    coordinates = _vec3(points[:3], "CalculiX orientation point a") + _vec3(
        points[3:], "CalculiX orientation point b"
    )
    # Revalidate the frame immediately before material-card serialization.
    axes = _orientation_axes(orientation)
    longitudinal = axes["L"]
    radial = axes["R"]
    expected_points = (*longitudinal, *radial)
    if any(abs(a - b) > 1e-12 for a, b in zip(coordinates, expected_points, strict=True)):
        raise ValueError("CalculiX points differ from the validated L/R material axes")
    return (
        f"*ORIENTATION,NAME={card_name}\n"
        + ",".join(format(value, ".17g") for value in coordinates)
    )
