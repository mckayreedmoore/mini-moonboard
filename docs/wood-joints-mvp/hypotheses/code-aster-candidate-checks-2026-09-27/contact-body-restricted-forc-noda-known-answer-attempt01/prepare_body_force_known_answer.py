#!/usr/bin/env python3
"""Prepare output-only body-restricted FORC_NODA extraction on flat coupon."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/contact-3d-flat-attempt02"
SURFACE_PREP = ROOT / "fea/code_aster_trial/contact_surface_force"
IMAGE = "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5"
FILES = ("contact_3d.comm", "contact_3d.export", "contact_coupon.mail")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze = json.loads((BASE / "input-freeze.json").read_text())
    for name in FILES:
        if digest(BASE / name) != freeze["input_sha256"][name]:
            raise SystemExit(f"frozen baseline input changed: {name}")
    surface_readiness = json.loads((SURFACE_PREP / "readiness.json").read_text())
    for name in FILES:
        if digest(SURFACE_PREP / name) != surface_readiness["prepared_input_sha256"][name]:
            raise SystemExit(f"surface-force prepared source changed: {name}")
        if digest(BASE / name) != surface_readiness["baseline_input_sha256"][name]:
            raise SystemExit(f"surface-force readiness no longer matches baseline: {name}")

    comm = (SURFACE_PREP / "contact_3d.comm").read_text()
    anchor = 'RESU = CALC_CHAMP(reuse=RESU, RESULTAT=RESU, CONTRAINTE=("SIEF_NOEU",))\n'
    addition = (
        anchor
        + "# Separate result concepts calculate forces on each requested body only.\n"
        + "SFORCE = CALC_CHAMP(RESULTAT=RESU, FORCE=(\"FORC_NODA\",), GROUP_MA=\"S_SOLID\")\n"
    )
    if comm.count(anchor) != 1:
        raise SystemExit("could not locate unique post-solve insertion point")
    comm = comm.replace(anchor, addition)
    old_row = '    ("SLAVE_SURFACE_INTERNAL_FORCE", "FORC_NODA", 88),\n'
    new_row = old_row + '    ("SLAVE_BODY_INTERNAL_FORCE", "FORC_NODA", 89),\n'
    if comm.count(old_row) != 1:
        raise SystemExit("could not locate unique extraction-list insertion point")
    comm = comm.replace(old_row, new_row)
    old_nodes = '"SLAVE_SURFACE_INTERNAL_FORCE"):'
    new_nodes = '"SLAVE_SURFACE_INTERNAL_FORCE", "SLAVE_BODY_INTERNAL_FORCE"):'
    if comm.count(old_nodes) != 1:
        raise SystemExit("could not locate unique output-group mapping")
    comm = comm.replace(old_nodes, new_nodes)
    old_result = '            RESULTAT=RESU,\n'
    new_result = (
        '            RESULTAT=(SFORCE if GROUP == "SLAVE_BODY_INTERNAL_FORCE" else RESU),\n'
    )
    if comm.count(old_result) != 1:
        raise SystemExit("could not locate unique POST_RELEVE_T RESULTAT field")
    comm = comm.replace(old_result, new_result)

    export = (SURFACE_PREP / "contact_3d.export").read_text()
    anchor_unit = "F dat slave_surface_internal_force.csv R 88\n"
    if export.count(anchor_unit) != 1:
        raise SystemExit("could not locate unique output unit insertion point")
    export = export.replace(anchor_unit, anchor_unit + "F dat slave_body_internal_force.csv R 89\n")

    (HERE / "contact_3d.comm").write_text(comm)
    (HERE / "contact_3d.export").write_text(export)
    (HERE / "contact_coupon.mail").write_bytes((BASE / "contact_coupon.mail").read_bytes())
    readiness = {
        "status": "READY_FOR_NATIVE_KNOWN_ANSWER",
        "scope": "Flat fully active PENTA15/TRIA6 coupon; output-only S_SOLID-restricted FORC_NODA on SLNOD.",
        "baseline_attempt": str(BASE.relative_to(ROOT)),
        "runtime_image": IMAGE,
        "baseline_input_freeze_sha256": digest(BASE / "input-freeze.json"),
        "baseline_input_sha256": {name: digest(BASE / name) for name in FILES},
        "prepared_input_sha256": {name: digest(HERE / name) for name in FILES},
        "mesh_byte_identical": digest(HERE / "contact_coupon.mail") == digest(BASE / "contact_coupon.mail"),
        "physical_solution_block_byte_identical": (
            comm.split("# Separate result concepts", 1)[0].rstrip()
            == (BASE / "contact_3d.comm").read_text().split("for GROUP, FIELD, UNIT in", 1)[0].rstrip()
        ),
        "new_postprocessing": [
            "CALC_CHAMP on GROUP_MA=S_SOLID into separate SFORCE result concept",
            "POST_RELEVE_T FORC_NODA on the existing SLNOD group at unit 89",
        ],
        "expected_internal_force_n": [0.0, 0.0, 3000.0],
        "tolerance_n": 0.1,
        "mechanical_acceptance": "NOT_INFERRED",
    }
    if not readiness["mesh_byte_identical"] or not readiness["physical_solution_block_byte_identical"]:
        raise SystemExit("prepared fixture is not output-only")
    (HERE / "readiness.json").write_text(json.dumps(readiness, indent=2) + "\n")
    print(json.dumps(readiness, indent=2))


if __name__ == "__main__":
    main()
