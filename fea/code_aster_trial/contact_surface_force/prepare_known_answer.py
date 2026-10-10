#!/usr/bin/env python3
"""Prepare an output-only FORC_NODA extraction on the flat 3-D coupon."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/contact-3d-flat-attempt02"
IMAGE = "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5"
FILES = ("contact_3d.comm", "contact_3d.export", "contact_coupon.mail")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze = json.loads((BASE / "input-freeze.json").read_text())
    for name in FILES:
        expected = freeze["input_sha256"][name]
        actual = digest(BASE / name)
        if actual != expected:
            raise SystemExit(f"baseline input changed: {name}")

    comm = (BASE / "contact_3d.comm").read_text()
    comm_before = comm
    old_row = '    ("SLAVE_STRESS", "SIEF_NOEU", 83),\n'
    new_row = old_row + '    ("SLAVE_SURFACE_INTERNAL_FORCE", "FORC_NODA", 88),\n'
    if comm.count(old_row) != 1:
        raise SystemExit("could not locate unique extraction-list insertion point")
    comm = comm.replace(old_row, new_row)
    old_nodes = 'if GROUP in ("SLAVE_CONTACT", "SLAVE_LAGRANGE", "SLAVE_STRESS"):'
    new_nodes = ('if GROUP in ("SLAVE_CONTACT", "SLAVE_LAGRANGE", "SLAVE_STRESS", '
                 '"SLAVE_SURFACE_INTERNAL_FORCE"):')
    if comm.count(old_nodes) != 1:
        raise SystemExit("could not locate unique SLNOD output-group mapping")
    comm = comm.replace(old_nodes, new_nodes)

    export = (BASE / "contact_3d.export").read_text()
    old_unit = "F master_reaction master_cut_reaction.csv R 87\n"
    if export.count(old_unit) != 1:
        raise SystemExit("could not locate unique export-unit insertion point")
    export = export.replace(old_unit, old_unit +
                            "F dat slave_surface_internal_force.csv R 88\n")

    (HERE / "contact_3d.comm").write_text(comm)
    (HERE / "contact_3d.export").write_text(export)
    (HERE / "contact_coupon.mail").write_bytes((BASE / "contact_coupon.mail").read_bytes())

    changed_lines = [
        "Add one `POST_RELEVE_T` extraction of `FORC_NODA` over `SLNOD`.",
        "Add unit 88 for that table.",
        "No model, mesh, material, boundary, load, contact or increment changes.",
    ]
    readiness = {
        "status": "READY_FOR_PARENT_REVIEW",
        "scope": "Flat, fully active 3-D contact-surface internal-force known-answer only.",
        "baseline_attempt": str(BASE.relative_to(ROOT)),
        "baseline_image": IMAGE,
        "baseline_attempt_input_freeze_sha256": digest(BASE / "input-freeze.json"),
        "baseline_input_sha256": {name: digest(BASE / name) for name in FILES},
        "prepared_input_sha256": {name: digest(HERE / name) for name in FILES},
        "mesh_exactly_unchanged": digest(HERE / "contact_coupon.mail") ==
                                  digest(BASE / "contact_coupon.mail"),
        "physical_analysis_block_exactly_unchanged": comm_before.split("for GROUP, FIELD, UNIT in", 1)[0] ==
                                                     comm.split("for GROUP, FIELD, UNIT in", 1)[0],
        "changes": changed_lines,
        "frozen_analytic_expected_surface_forc_noda_n": [0.0, 0.0, 3000.0],
        "frozen_analytic_expected_contact_force_on_slave_n": [0.0, 0.0, -3000.0],
        "force_output_sign_basis": "FORC_NODA is the stress-derived internal nodal force; at the free slave contact boundary it is expected to oppose contact RN and equal the analytic +Z internal traction resultant.",
        "force_resultant_limit_n": 0.1,
        "mechanical_acceptance": "NOT_INFERRED",
    }
    if not readiness["mesh_exactly_unchanged"]:
        raise SystemExit("prepared mesh differs from the frozen flat coupon")
    if not readiness["physical_analysis_block_exactly_unchanged"]:
        raise SystemExit("physical analysis commands differ from the frozen flat coupon")
    (HERE / "readiness.json").write_text(json.dumps(readiness, indent=2) + "\n")
    print(json.dumps(readiness, indent=2))


if __name__ == "__main__":
    main()
