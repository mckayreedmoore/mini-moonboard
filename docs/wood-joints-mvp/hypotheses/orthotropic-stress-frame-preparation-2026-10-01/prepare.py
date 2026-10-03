"""Prepare an unfrozen, unexecuted C3D10 stress-frame method fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/washer-annular-affine-native-2026-10-01-attempt01"
)
ORACLE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/orthotropic-stress-frame-parent-oracle.json"
)
PINS = {
    "model.inp": "36333a78ef54299cefc1fbb4ca0449ec889ce8a174b3dfc0c5ce8d3b17e93e95",
    "model.json": "85a02498a9a73901cc6fd27910803fe33f4abc26939fba31ca660f0d8d6707f6",
    "freeze.json": "093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817",
}
ORACLE_SHA = "1e82a2869b3609558024a3299363859f88e9d62c5770bacb26f92b4dfce5f5ff"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("nonfinite deck value")
    result = format(value, ".13e")
    if len(result) > 20:
        raise ValueError("numeric field exceeds the pinned solver's 20-character limit")
    return result


def prepare() -> tuple[str, dict]:
    for name, expected in PINS.items():
        if digest((SOURCE / name).read_bytes()) != expected:
            raise ValueError("changed source: " + name)
    if digest(ORACLE.read_bytes()) != ORACLE_SHA:
        raise ValueError("changed analytical oracle")
    source = (SOURCE / "model.inp").read_text()
    model = json.loads((SOURCE / "model.json").read_text())
    oracle = json.loads(ORACLE.read_text())
    if oracle["native_run_executed"] or oracle["capacity_established"]:
        raise ValueError("analytical oracle scope changed")
    prefix, separator, _ = source.partition("*MATERIAL,NAME=DIAGNOSTIC_ELASTIC\n")
    if not separator:
        raise ValueError("source material boundary absent")
    nodes = {}
    active = False
    for raw in prefix.splitlines():
        if raw.startswith("*"):
            active = raw.upper() == "*NODE"
        elif active and raw.strip():
            fields = raw.split(",")
            nodes[int(fields[0])] = tuple(float(x) for x in fields[1:])
    boundary = model["boundary_node_ids"]
    elements = model["mesh"]["element_ids"]
    if len(nodes) != 800 or len(boundary) != 512 or elements != list(range(1, 385)):
        raise ValueError("retained affine mesh census changed")
    _, node_keyword, mesh_prefix = prefix.partition("*NODE\n")
    if not node_keyword:
        raise ValueError("source node section absent")
    lines = [
        "*HEADING",
        "Hypothetical rotated orthotropic C3D10 stress-frame method fixture",
        "** Units: mm, N, MPa. Homogeneous linear strain; no contact or capacity.",
        "*NODE",
        *mesh_prefix.rstrip().splitlines(),
    ]
    for name in ("SGLOBAL", "SLOCAL", "SDEFAULT"):
        lines += [f"*ELSET,ELSET={name},GENERATE", "1,384,1"]
    constants = oracle["engineering_constants"]
    axes = oracle["global_axes_columns_L_R_T"]
    orientation = [axes[i][j] for j in (0, 1) for i in range(3)]
    lines += [
        "*MATERIAL,NAME=METHOD_ORTHOTROPIC",
        "*ELASTIC,TYPE=ENGINEERING CONSTANTS",
        ",".join(number(x) for x in constants[:8]),
        number(constants[8]),
        "*ORIENTATION,NAME=WOODLRT,SYSTEM=RECTANGULAR",
        ",".join(number(x) for x in orientation),
        "*SOLID SECTION,ELSET=ANNULUS,MATERIAL=METHOD_ORTHOTROPIC,ORIENTATION=WOODLRT",
        "*BOUNDARY",
    ]
    strain = oracle["global_strain_tensor"]
    for node in sorted(boundary):
        xyz = nodes[node]
        for dof in range(3):
            value = math.fsum(strain[dof][j] * xyz[j] for j in range(3))
            lines.append(f"{node},{dof + 1},{dof + 1},{number(value)}")
    lines += [
        "*STEP",
        "*STATIC,DIRECT",
        "1.0,1.0",
        "*NODE PRINT,NSET=ALLNODES",
        "U",
        "*EL PRINT,ELSET=SGLOBAL,GLOBAL=YES",
        "S",
        "*EL PRINT,ELSET=SLOCAL,GLOBAL=NO",
        "S",
        "*EL PRINT,ELSET=SDEFAULT",
        "S",
        "*EL PRINT,ELSET=ANNULUS,TOTALS=ONLY",
        "ELSE",
        "*END STEP",
    ]
    deck = "\n".join(lines) + "\n"
    expected = {
        "schema": "orthotropic_stress_frame_preparation/v1",
        "status": "PREPARED_UNFROZEN_UNEXECUTED",
        "scope": "hypothetical homogeneous-strain stress-output frame check only",
        "source_sha256": PINS,
        "oracle_sha256": ORACLE_SHA,
        "deck_sha256": digest(deck.encode()),
        "mesh": {
            "nodes": 800,
            "C3D10_elements": 384,
            "boundary_nodes": 512,
            "boundary_dofs": 1536,
            "free_dofs": 864,
            "integration_points_per_set": 1536,
        },
        "orientation_name": "WOODLRT",
        "global_stress_tensor_MPa": oracle["global_stress_tensor_MPa"],
        "local_stress_tensor_MPa": oracle["local_stress_tensor_MPa"],
        "default_output_must_match": "SLOCAL",
        "expected_energy_N_mm": oracle["energy_density_N_per_mm3"]
        * model["mesh"]["corner_tet_volume_sum_mm3"],
        "native_run_executed": False,
        "ready_for_native_run": False,
        "input_freeze_created": False,
        "mechanical_acceptance": False,
        "formal_criteria_pending": 47,
    }
    return deck, expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    deck, expected = prepare()
    args.output_directory.mkdir(parents=False, exist_ok=False)
    (args.output_directory / "model.inp").write_text(deck)
    (args.output_directory / "expected.json").write_text(
        json.dumps(expected, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {"status": expected["status"], "deck_sha256": expected["deck_sha256"]}
        )
    )


if __name__ == "__main__":
    main()
