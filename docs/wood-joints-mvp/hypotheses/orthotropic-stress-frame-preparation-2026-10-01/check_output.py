"""Pure checker for the proposed stress-frame fixture; no native launch path."""

from __future__ import annotations

import math
import re

HEADER = re.compile(
    r"^(displacements \(vx,vy,vz\)|stresses \(elem, integ\.pnt\.,sxx,syy,szz,sxy,sxz,syz\)|total internal energy)"
    r" for set (\w+) and time\s+(\S+)$"
)
STRESS_ABS_MPA = 1e-6
STRESS_REL = 1e-5
DISPLACEMENT_ABS_MM = 1e-9
DISPLACEMENT_REL = 1e-6
ENERGY_ABS_N_MM = 1e-10
ENERGY_REL = 1e-5


def finite(value: str) -> float:
    result = float(value.replace("D", "E"))
    if not math.isfinite(result):
        raise ValueError("nonfinite output")
    return result


def tensor_components(tensor: list[list[float]]) -> list[float]:
    return [
        tensor[0][0],
        tensor[1][1],
        tensor[2][2],
        tensor[0][1],
        tensor[0][2],
        tensor[1][2],
    ]


def check(
    dat: str,
    expected: dict,
    coordinates: dict[int, tuple[float, float, float]],
    strain: list[list[float]],
) -> dict:
    """Read all requested rows, refusing duplicate, missing or foreign IDs/frames."""
    blocks = {}
    current = None
    for raw in dat.splitlines():
        line = raw.strip()
        if not line or line.startswith(("S T E P", "INCREMENT")):
            continue
        match = HEADER.fullmatch(line)
        if match:
            variable, name, timestamp = match.groups()
            if finite(timestamp) != 1.0:
                raise ValueError("unexpected output time")
            key = (variable.split(" (")[0], name)
            if key in blocks:
                raise ValueError("duplicate output block")
            blocks[key] = []
            current = key
        else:
            if current is None:
                raise ValueError("row outside requested output block")
            blocks[current].append(line.split())
    required = {
        ("displacements", "ALLNODES"),
        ("stresses", "SGLOBAL"),
        ("stresses", "SLOCAL"),
        ("stresses", "SDEFAULT"),
        ("total internal energy", "ANNULUS"),
    }
    if set(blocks) != required:
        raise ValueError("missing or foreign output block")
    maximum_stress_error = 0.0
    desired_ids = {
        (element, point) for element in range(1, 385) for point in range(1, 5)
    }
    for name in ("SGLOBAL", "SLOCAL", "SDEFAULT"):
        is_global = name == "SGLOBAL"
        tensor = expected[
            "global_stress_tensor_MPa" if is_global else "local_stress_tensor_MPa"
        ]
        reference = tensor_components(tensor)
        seen = set()
        for row in blocks["stresses", name]:
            if len(row) != (8 if is_global else 9):
                raise ValueError("stress row has wrong width/frame tag")
            if not is_global and row[-1] != "WOODLRT":
                raise ValueError("wrong local orientation tag")
            identity = (int(row[0]), int(row[1]))
            if identity not in desired_ids or identity in seen:
                raise ValueError("foreign or duplicate integration point")
            seen.add(identity)
            for actual, wanted in zip(map(finite, row[2:8]), reference, strict=True):
                maximum_stress_error = max(maximum_stress_error, abs(actual - wanted))
                if not math.isclose(
                    actual, wanted, rel_tol=STRESS_REL, abs_tol=STRESS_ABS_MPA
                ):
                    raise ValueError(
                        "stress component differs from analytical frame answer"
                    )
        if seen != desired_ids:
            raise ValueError("missing integration point")
    seen_nodes = set()
    maximum_u_error = 0.0
    for row in blocks["displacements", "ALLNODES"]:
        if len(row) != 4:
            raise ValueError("wrong displacement row width")
        node = int(row[0])
        if node not in coordinates or node in seen_nodes:
            raise ValueError("foreign or duplicate displacement node")
        seen_nodes.add(node)
        for dof, actual in enumerate(map(finite, row[1:])):
            wanted = math.fsum(strain[dof][j] * coordinates[node][j] for j in range(3))
            maximum_u_error = max(maximum_u_error, abs(actual - wanted))
            if not math.isclose(
                actual, wanted, rel_tol=DISPLACEMENT_REL, abs_tol=DISPLACEMENT_ABS_MM
            ):
                raise ValueError("displacement differs from homogeneous strain field")
    if len(coordinates) != 800 or seen_nodes != set(coordinates):
        raise ValueError("missing displacement node or wrong coordinate census")
    energy_rows = blocks["total internal energy", "ANNULUS"]
    if len(energy_rows) != 1 or len(energy_rows[0]) != 1:
        raise ValueError("wrong energy row census")
    energy = finite(energy_rows[0][0])
    if not math.isclose(
        energy,
        expected["expected_energy_N_mm"],
        rel_tol=ENERGY_REL,
        abs_tol=ENERGY_ABS_N_MM,
    ):
        raise ValueError("internal energy differs from analytical answer")
    return {
        "status": "PASS_STRESS_FRAME_NUMERICAL_CHECK_ONLY",
        "stress_rows": 4608,
        "displacement_rows": 800,
        "maximum_stress_component_error_MPa": maximum_stress_error,
        "maximum_displacement_component_error_mm": maximum_u_error,
        "energy_N_mm": energy,
        "mechanical_acceptance": False,
    }
