#!/usr/bin/env python3
"""Prepare paired, output-only BOLT/WOOD FORC_NODA resultants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "fea/code_aster_trial/curved_contact/native_input_v3"
CONTROL = ROOT / "fea/code_aster_trial/curved_contact/cell_order_reversal_control"
BASE_RUN = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03"
CONTROL_RUN = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-cell-order-control-attempt01"
IMAGE = "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5"
FILES = ("curved_contact.comm", "curved_contact.export", "curved_contact.mail")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_postprocessing(source: Path, target: Path) -> dict[str, str]:
    comm = (source / "curved_contact.comm").read_text()
    anchor = "RESU = CALC_CHAMP(reuse=RESU, RESULTAT=RESU, FORCE=('FORC_NODA',));\n"
    addition = anchor + (
        "# Body-restricted internal nodal forces isolate each side's interface resultant.\n"
        "BOLT_FORCE = CALC_CHAMP(RESULTAT=RESU, FORCE=('FORC_NODA',), GROUP_MA='BOLT');\n"
        "WOOD_FORCE = CALC_CHAMP(RESULTAT=RESU, FORCE=('FORC_NODA',), GROUP_MA='WOOD');\n"
    )
    if comm.count(anchor) != 1:
        raise SystemExit(f"{source}: could not locate unique post-solve insertion point")
    comm = comm.replace(anchor, addition)
    append = """
for title, force_result, nodes, unit in [
    ('BOLT_SNODE_FORCE', BOLT_FORCE, 'SNODE', 85),
    ('WOOD_MNODE_FORCE', WOOD_FORCE, 'MNODE', 86),
]:
    TABLE = POST_RELEVE_T(ACTION=_F(OPERATION='EXTRACTION', INTITULE=title,
        RESULTAT=force_result, NOM_CHAM='FORC_NODA', GROUP_NO=nodes,
        TOUT_ORDRE='OUI', TOUT_CMP='OUI'));
    IMPR_TABLE(TABLE=TABLE, FORMAT='TABLEAU', UNITE=unit, SEPARATEUR=';', FORMAT_R='E24.16');
"""
    if "FIN();" not in comm or comm.count("FIN();") != 1:
        raise SystemExit(f"{source}: could not locate unique deck terminator")
    comm = comm.replace("FIN();", append + "FIN();")

    export = (source / "curved_contact.export").read_text()
    if "F dat SDISP.csv R 84\n" not in export or export.count("F dat SDISP.csv R 84\n") != 1:
        raise SystemExit(f"{source}: could not locate unique export insertion point")
    export = export.replace("F dat SDISP.csv R 84\n",
                            "F dat SDISP.csv R 84\nF dat BOLT_SNODE_FORCE.csv R 85\nF dat WOOD_MNODE_FORCE.csv R 86\n")
    target.mkdir(parents=True, exist_ok=False)
    (target / "curved_contact.comm").write_text(comm)
    (target / "curved_contact.export").write_text(export)
    (target / "curved_contact.mail").write_bytes((source / "curved_contact.mail").read_bytes())
    return {name: digest(target / name) for name in FILES}


def main() -> None:
    baseline_freeze = json.loads((BASE_RUN / "input-freeze.json").read_text())
    control_freeze = json.loads((CONTROL_RUN / "input-freeze.json").read_text())
    for name in FILES:
        if digest(BASE / name) != baseline_freeze["input_sha256"][name]:
            raise SystemExit(f"baseline frozen input changed: {name}")
        if digest(CONTROL / name) != control_freeze["input_sha256"][name]:
            raise SystemExit(f"order-control frozen input changed: {name}")
    if baseline_freeze["image"] != IMAGE or control_freeze["image"] != IMAGE:
        raise SystemExit("source runs do not use the selected pinned image")
    if digest(BASE / "curved_contact.comm") != digest(CONTROL / "curved_contact.comm"):
        raise SystemExit("paired source decks differ before output-only additions")
    if digest(BASE / "curved_contact.export") != digest(CONTROL / "curved_contact.export"):
        raise SystemExit("paired source exports differ before output-only additions")

    baseline_dir = HERE / "baseline"
    control_dir = HERE / "order_control"
    baseline_hashes = add_postprocessing(BASE, baseline_dir)
    control_hashes = add_postprocessing(CONTROL, control_dir)
    if baseline_hashes["curved_contact.comm"] != control_hashes["curved_contact.comm"]:
        raise SystemExit("paired prepared decks differ")
    if baseline_hashes["curved_contact.export"] != control_hashes["curved_contact.export"]:
        raise SystemExit("paired prepared exports differ")

    baseline_mail_hash = digest(baseline_dir / "curved_contact.mail")
    control_mail_hash = digest(control_dir / "curved_contact.mail")
    if baseline_mail_hash != digest(BASE / "curved_contact.mail"):
        raise SystemExit("baseline mesh was changed")
    if control_mail_hash != digest(CONTROL / "curved_contact.mail"):
        raise SystemExit("control mesh was changed")

    baseline_readiness = {
        "status": "READY_FOR_PARENT_NATIVE_CHECK",
        "scope": "Paired curved TETRA10 contact-method force-resultant check; baseline slave cell order.",
        "source_attempt": str(BASE_RUN.relative_to(ROOT)),
        "runtime_image": IMAGE,
        "source_input_freeze_sha256": digest(BASE_RUN / "input-freeze.json"),
        "source_input_sha256": {name: digest(BASE / name) for name in FILES},
        "prepared_input_sha256": baseline_hashes,
        "mesh_byte_identical_to_source": True,
        "body_groups": {"BOLT": "SNODE", "WOOD": "MNODE"},
        "only_new_physical_commands": [],
        "postprocessing_changes": [
            "CALC_CHAMP(FORC_NODA, GROUP_MA=BOLT) into separate BOLT_FORCE concept",
            "CALC_CHAMP(FORC_NODA, GROUP_MA=WOOD) into separate WOOD_FORCE concept",
            "POST_RELEVE_T of BOLT_FORCE on SNODE and WOOD_FORCE on MNODE",
        ],
        "mechanical_acceptance": "NOT_INFERRED",
    }
    control_readiness = {
        **baseline_readiness,
        "scope": "Paired curved TETRA10 contact-method force-resultant check; reversed slave cell order.",
        "source_attempt": str(CONTROL_RUN.relative_to(ROOT)),
        "source_input_freeze_sha256": digest(CONTROL_RUN / "input-freeze.json"),
        "source_input_sha256": {name: digest(CONTROL / name) for name in FILES},
        "prepared_input_sha256": control_hashes,
        "mesh_byte_identical_to_source": True,
    }
    if baseline_readiness["prepared_input_sha256"]["curved_contact.comm"] != control_readiness["prepared_input_sha256"]["curved_contact.comm"]:
        raise SystemExit("prepared decks are not byte-identical")
    if baseline_readiness["prepared_input_sha256"]["curved_contact.export"] != control_readiness["prepared_input_sha256"]["curved_contact.export"]:
        raise SystemExit("prepared exports are not byte-identical")
    (baseline_dir / "readiness.json").write_text(json.dumps(baseline_readiness, indent=2) + "\n")
    (control_dir / "readiness.json").write_text(json.dumps(control_readiness, indent=2) + "\n")
    (HERE / "pair-readiness.json").write_text(json.dumps({
        "status": "READY_FOR_PARENT_NATIVE_CHECK",
        "baseline_prepared_input_sha256": baseline_hashes,
        "order_control_prepared_input_sha256": control_hashes,
        "paired_comm_export_identical": True,
        "baseline_mesh_sha256": baseline_mail_hash,
        "order_control_mesh_sha256": control_mail_hash,
        "same_pinned_image": IMAGE,
        "mechanical_acceptance": "NOT_INFERRED",
    }, indent=2) + "\n")
    print(json.dumps({"baseline": baseline_readiness, "order_control": control_readiness}, indent=2))


if __name__ == "__main__":
    main()
