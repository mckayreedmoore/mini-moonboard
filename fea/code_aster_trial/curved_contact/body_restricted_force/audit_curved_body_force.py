#!/usr/bin/env python3
"""Audit paired body-restricted force resultants on the curved contact crop."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CHECKS = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27"
BASELINE = CHECKS / "curved-contact-body-force-attempt01"
CONTROL = CHECKS / "curved-contact-body-force-order-control-attempt01"
BASE_SOURCE = CHECKS / "curved-contact-attempt03"
CONTROL_SOURCE = CHECKS / "curved-contact-cell-order-control-attempt01"
PAIR_READY = HERE / "pair-readiness.json"
EXPECTED_IMAGE = "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5"
FORCE_TOL_N = 1.0e-6
MOMENT_TOL_N_MM = 1.0e-6
ORDER_TOL_N = 1.0e-6
ORDER_TOL_N_MM = 1.0e-6
EXPECTED_NODES = {"SNODE": 218, "MNODE": 194, "CONTACT": 218, "SCUT": 110, "MCUT": 136}
INSTANCES = (-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0)
DIAGNOSTIC_INSTANCES = (5.0, 6.0, 7.0, 11.0)
COMM_ANCHOR = "RESU = CALC_CHAMP(reuse=RESU, RESULTAT=RESU, FORCE=('FORC_NODA',));\n"
COMM_ADDITION = (
    COMM_ANCHOR
    + "# Body-restricted internal nodal forces isolate each side's interface resultant.\n"
    + "BOLT_FORCE = CALC_CHAMP(RESULTAT=RESU, FORCE=('FORC_NODA',), GROUP_MA='BOLT');\n"
    + "WOOD_FORCE = CALC_CHAMP(RESULTAT=RESU, FORCE=('FORC_NODA',), GROUP_MA='WOOD');\n"
)
COMM_EXTRACTION = """
for title, force_result, nodes, unit in [
    ('BOLT_SNODE_FORCE', BOLT_FORCE, 'SNODE', 85),
    ('WOOD_MNODE_FORCE', WOOD_FORCE, 'MNODE', 86),
]:
    TABLE = POST_RELEVE_T(ACTION=_F(OPERATION='EXTRACTION', INTITULE=title,
        RESULTAT=force_result, NOM_CHAM='FORC_NODA', GROUP_NO=nodes,
        TOUT_ORDRE='OUI', TOUT_CMP='OUI'));
    IMPR_TABLE(TABLE=TABLE, FORMAT='TABLEAU', UNITE=unit, SEPARATEUR=';', FORMAT_R='E24.16');
"""
EXPORT_ANCHOR = "F dat SDISP.csv R 84\n"
EXPORT_ADDITION = EXPORT_ANCHOR + "F dat BOLT_SNODE_FORCE.csv R 85\nF dat WOOD_MNODE_FORCE.csv R 86\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_table(path: Path) -> list[dict[str, str]]:
    lines = [line for line in path.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError(f"empty table: {path}")
    return list(csv.DictReader(lines, delimiter=";"))


def by_instant(rows: list[dict[str, str]], instant: float) -> list[dict[str, str]]:
    selected = [row for row in rows if abs(float(row["INST"]) - instant) <= 1.0e-8]
    if not selected:
        raise ValueError(f"no rows at INST={instant:g}")
    return selected


def summed_vector(rows: list[dict[str, str]], fields: tuple[str, str, str] = ("DX", "DY", "DZ")) -> tuple[float, float, float]:
    return tuple(math.fsum(float(row[key]) for row in rows) for key in fields)


def first_moment(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    components: list[list[float]] = [[], [], []]
    for row in rows:
        x, y, z = (float(row[name]) for name in ("COOR_X", "COOR_Y", "COOR_Z"))
        fx, fy, fz = (float(row[name]) for name in ("DX", "DY", "DZ"))
        components[0].append(y * fz - z * fy)
        components[1].append(z * fx - x * fz)
        components[2].append(x * fy - y * fx)
    return tuple(math.fsum(values) for values in components)


def norm(vector: tuple[float, float, float]) -> float:
    return math.dist(vector, (0.0, 0.0, 0.0))


def difference(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a[index] - b[index] for index in range(3))


def check_attempt(attempt: Path, readiness_name: str, source_attempt: Path) -> dict[str, list[dict[str, str]]]:
    freeze = json.loads((attempt / "input-freeze.json").read_text())
    readiness = json.loads((attempt / readiness_name).read_text())
    source_freeze = json.loads((source_attempt / "input-freeze.json").read_text())
    execution = json.loads((attempt / "execution.json").read_text())
    if execution.get("returncode") != 0 or execution.get("timed_out") is not False:
        raise ValueError(f"native run did not complete: {attempt.name}")
    if execution.get("changed_frozen_inputs"):
        raise ValueError(f"native run changed frozen inputs: {attempt.name}")
    if freeze.get("image") != EXPECTED_IMAGE or readiness.get("runtime_image") != EXPECTED_IMAGE:
        raise ValueError(f"wrong runtime image: {attempt.name}")
    if readiness.get("source_input_freeze_sha256") != digest(source_attempt / "input-freeze.json"):
        raise ValueError(f"source input-freeze provenance mismatch: {attempt.name}")
    for name, expected in freeze["input_sha256"].items():
        if digest(attempt / name) != expected:
            raise ValueError(f"input-freeze mismatch in {attempt.name}: {name}")
    for name in ("curved_contact.comm", "curved_contact.export", "curved_contact.mail"):
        if digest(source_attempt / name) != source_freeze["input_sha256"][name]:
            raise ValueError(f"source run input hash mismatch: {source_attempt.name}/{name}")
        if readiness["source_input_sha256"][name] != source_freeze["input_sha256"][name]:
            raise ValueError(f"readiness source-input provenance mismatch: {attempt.name}/{name}")
        if digest(attempt / name) != readiness["prepared_input_sha256"][name]:
            raise ValueError(f"prepared-input hash mismatch in {attempt.name}: {name}")
    source_comm = (source_attempt / "curved_contact.comm").read_text()
    if source_comm.count(COMM_ANCHOR) != 1 or source_comm.count("FIN();") != 1:
        raise ValueError(f"source deck lacks unique output-only insertion points: {source_attempt.name}")
    expected_comm = source_comm.replace(COMM_ANCHOR, COMM_ADDITION).replace("FIN();", COMM_EXTRACTION + "FIN();")
    if (attempt / "curved_contact.comm").read_text() != expected_comm:
        raise ValueError(f"prepared deck includes unexpected changes: {attempt.name}")
    source_export = (source_attempt / "curved_contact.export").read_text()
    if source_export.count(EXPORT_ANCHOR) != 1:
        raise ValueError(f"source export lacks unique output-only insertion point: {source_attempt.name}")
    expected_export = source_export.replace(EXPORT_ANCHOR, EXPORT_ADDITION)
    if (attempt / "curved_contact.export").read_text() != expected_export:
        raise ValueError(f"prepared export includes unexpected changes: {attempt.name}")
    if digest(attempt / "curved_contact.mail") != digest(source_attempt / "curved_contact.mail"):
        raise ValueError(f"prepared mesh is not byte-identical to source: {attempt.name}")
    if readiness.get("mesh_byte_identical_to_source") is not True:
        raise ValueError(f"mesh/source identity not established in {attempt.name}")
    message_log = (attempt / "curved_contact.mess").read_text(errors="replace").lower()
    if "aucune alarme" not in message_log:
        raise ValueError(f"native message log does not report a clean alarm summary: {attempt.name}")
    names = ("BOLT_SNODE_FORCE", "WOOD_MNODE_FORCE", "CONTACT", "SCUT", "MCUT", "SDISP")
    return {name: read_table(attempt / f"{name}.csv") for name in names}


def unique_node_count(rows: list[dict[str, str]]) -> int:
    nodes = [row["NOEUD"].strip() for row in rows]
    if len(nodes) != len(set(nodes)):
        raise ValueError("duplicate node rows at a single instant")
    return len(nodes)


def output_field_delta(a: list[dict[str, str]], b: list[dict[str, str]], fields: tuple[str, ...]) -> dict[str, float]:
    key = lambda row: (row["NOEUD"].strip(), float(row["INST"]))
    ma = {key(row): row for row in a}
    mb = {key(row): row for row in b}
    if ma.keys() != mb.keys():
        raise ValueError("paired field rows do not cover identical nodes and instants")
    return {field: max(abs(float(ma[k][field]) - float(mb[k][field])) for k in ma)
            for field in fields}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=CHECKS / "curved-contact-body-force-audit.json")
    args = parser.parse_args()
    pair = json.loads(PAIR_READY.read_text())
    base_ready = json.loads((BASELINE / "readiness.json").read_text())
    control_ready = json.loads((CONTROL / "readiness.json").read_text())
    base = check_attempt(BASELINE, "readiness.json", BASE_SOURCE)
    control = check_attempt(CONTROL, "readiness.json", CONTROL_SOURCE)
    for name in ("curved_contact.comm", "curved_contact.export"):
        if pair["baseline_prepared_input_sha256"][name] != pair["order_control_prepared_input_sha256"][name]:
            raise ValueError(f"paired preparations do not share {name}")

    states: dict[str, dict] = {}
    maxima = {
        "body_action_reaction_n": 0.0,
        "bolt_plus_scut_n": 0.0,
        "wood_plus_mcut_n": 0.0,
        "bolt_action_reaction_moment_n_mm": 0.0,
        "wood_action_reaction_moment_n_mm": 0.0,
        "order_delta_bolt_force_n": 0.0,
        "order_delta_wood_force_n": 0.0,
        "order_delta_scut_n": 0.0,
        "order_delta_mcut_n": 0.0,
        "order_delta_depl_max_component": 0.0,
    }
    order_checks: dict[str, dict] = {}
    rn_checks: dict[str, dict] = {}
    for instant in INSTANCES:
        key = f"{instant:g}"
        groups = {}
        for label, data in (("baseline", base), ("order_control", control)):
            bolt = by_instant(data["BOLT_SNODE_FORCE"], instant)
            wood = by_instant(data["WOOD_MNODE_FORCE"], instant)
            contact = by_instant(data["CONTACT"], instant)
            scut = by_instant(data["SCUT"], instant)
            mcut = by_instant(data["MCUT"], instant)
            bolt_vector = summed_vector(bolt)
            wood_vector = summed_vector(wood)
            scut_vector = summed_vector(scut)
            mcut_vector = summed_vector(mcut)
            rn_vector = summed_vector(contact, ("RNX", "RNY", "RNZ"))
            bolt_moment = first_moment(bolt)
            wood_moment = first_moment(wood)
            scut_moment = first_moment(scut)
            mcut_moment = first_moment(mcut)
            bolt_cut_error = norm(tuple(bolt_vector[i] + scut_vector[i] for i in range(3)))
            wood_cut_error = norm(tuple(wood_vector[i] + mcut_vector[i] for i in range(3)))
            bolt_moment_error = norm(tuple(bolt_moment[i] + scut_moment[i] for i in range(3)))
            wood_moment_error = norm(tuple(wood_moment[i] + mcut_moment[i] for i in range(3)))
            body_pair_error = norm(tuple(bolt_vector[i] + wood_vector[i] for i in range(3)))
            rn_gap = norm(tuple(bolt_vector[i] + rn_vector[i] for i in range(3)))
            groups[label] = {
                "node_counts": {"SNODE": unique_node_count(bolt), "MNODE": unique_node_count(wood),
                                "CONTACT": unique_node_count(contact), "SCUT": unique_node_count(scut),
                                "MCUT": unique_node_count(mcut)},
                "bolt_snode_force_n": list(bolt_vector),
                "wood_mnode_force_n": list(wood_vector),
                "sum_rn_contact_action_n": list(rn_vector),
                "scut_forc_noda_n": list(scut_vector),
                "mcut_forc_noda_n": list(mcut_vector),
                "bolt_snode_first_moment_n_mm_about_global_origin": list(bolt_moment),
                "wood_mnode_first_moment_n_mm_about_global_origin": list(wood_moment),
                "scut_first_moment_n_mm_about_global_origin": list(scut_moment),
                "mcut_first_moment_n_mm_about_global_origin": list(mcut_moment),
                "equilibrium_residuals": {
                    "bolt_body_action_reaction_n": bolt_cut_error,
                    "wood_body_action_reaction_n": wood_cut_error,
                    "bolt_body_action_reaction_moment_n_mm": bolt_moment_error,
                    "wood_body_action_reaction_moment_n_mm": wood_moment_error,
                    "bolt_wood_interface_force_pair_n": body_pair_error,
                },
                "rn_to_bolt_body_force_gap_n": rn_gap,
            }
            if groups[label]["node_counts"] != EXPECTED_NODES:
                raise ValueError(f"unexpected group node counts for {label} at INST={instant:g}: "
                                 f"{groups[label]['node_counts']}")
            maxima["body_action_reaction_n"] = max(maxima["body_action_reaction_n"], body_pair_error)
            maxima["bolt_plus_scut_n"] = max(maxima["bolt_plus_scut_n"], bolt_cut_error)
            maxima["wood_plus_mcut_n"] = max(maxima["wood_plus_mcut_n"], wood_cut_error)
            maxima["bolt_action_reaction_moment_n_mm"] = max(maxima["bolt_action_reaction_moment_n_mm"], bolt_moment_error)
            maxima["wood_action_reaction_moment_n_mm"] = max(maxima["wood_action_reaction_moment_n_mm"], wood_moment_error)
            rn_checks.setdefault(label, {})[key] = {"gap_n": rn_gap, "rn_vector_n": list(rn_vector),
                                                     "bolt_snode_force_n": list(bolt_vector)}
        states[key] = groups

        order_specs = {
            "BOLT_SNODE_FORCE": (base["BOLT_SNODE_FORCE"], control["BOLT_SNODE_FORCE"], ("DX", "DY", "DZ")),
            "WOOD_MNODE_FORCE": (base["WOOD_MNODE_FORCE"], control["WOOD_MNODE_FORCE"], ("DX", "DY", "DZ")),
            "SCUT": (base["SCUT"], control["SCUT"], ("DX", "DY", "DZ")),
            "MCUT": (base["MCUT"], control["MCUT"], ("DX", "DY", "DZ")),
            "CONTACT_RN": (base["CONTACT"], control["CONTACT"], ("RNX", "RNY", "RNZ")),
            "SDISP": (base["SDISP"], control["SDISP"], ("DX", "DY", "DZ")),
        }
        measured = {}
        for name, (base_table, control_table, components) in order_specs.items():
            base_rows = by_instant(base_table, instant)
            control_rows = by_instant(control_table, instant)
            if len(base_rows) != len(control_rows):
                raise ValueError(f"paired {name} row counts differ at INST={instant:g}")
            if name == "SDISP":
                field = output_field_delta(base_rows, control_rows, components)
                measured[name] = {"maximum_absolute_delta_by_component_mm": field,
                                  "maximum_absolute_delta_mm": max(field.values())}
                maxima["order_delta_depl_max_component"] = max(maxima["order_delta_depl_max_component"], max(field.values()))
            else:
                base_vector = summed_vector(base_rows, components)
                control_vector = summed_vector(control_rows, components)
                delta = norm(tuple(base_vector[i] - control_vector[i] for i in range(3)))
                measured[name] = {"baseline_resultant": list(base_vector),
                                  "order_control_resultant": list(control_vector),
                                  "resultant_delta": delta}
                map_name = {
                    "BOLT_SNODE_FORCE": "order_delta_bolt_force_n",
                    "WOOD_MNODE_FORCE": "order_delta_wood_force_n",
                    "SCUT": "order_delta_scut_n",
                    "MCUT": "order_delta_mcut_n",
                }.get(name)
                if map_name:
                    maxima[map_name] = max(maxima[map_name], delta)
        order_checks[key] = measured

    active_state_rn = {
        label: {instant: rn_checks[label][f"{instant:g}"]["gap_n"] for instant in DIAGNOSTIC_INSTANCES}
        for label in ("baseline", "order_control")
    }
    rn_order_deltas = {
        f"{instant:g}": order_checks[f"{instant:g}"]["CONTACT_RN"]["resultant_delta"]
        for instant in DIAGNOSTIC_INSTANCES
    }
    pointwise_order_checks = {}
    for name, fields in (
        ("BOLT_SNODE_FORCE", ("DX", "DY", "DZ")),
        ("WOOD_MNODE_FORCE", ("DX", "DY", "DZ")),
        ("SCUT", ("DX", "DY", "DZ")),
        ("MCUT", ("DX", "DY", "DZ")),
        ("CONTACT", ("CONT", "JEU", "RN", "RNX", "RNY", "RNZ")),
    ):
        pointwise_order_checks[name] = output_field_delta(base[name], control[name], fields)

    result = {
        "scope": "Paired static curved pair-021 crop; body-restricted TETRA10 FORC_NODA resultants and order-control comparison.",
        "method": "Calculate FORC_NODA separately on the BOLT and WOOD volume groups, then sum on SNODE and MNODE. Check each body's interface resultant and first moment against that body's cut field.",
        "source_basis": {
            "code_aster_manual": "https://code-aster.org/doc/v17/manuals/man_u/u4/u4.81.04/index.html",
            "manual_claim": "CALC_CHAMP GROUP_MA assembles FORC_NODA from the selected elements and is intended to measure one model piece's reaction on another.",
            "known_answer": "contact-body-restricted-forc-noda-known-answer-attempt01",
            "same_runtime_image": EXPECTED_IMAGE,
            "prepared_pair_readiness": str(PAIR_READY.relative_to(ROOT)),
        },
        "preflight": {
            "paired_deck_and_export_identical": pair["paired_comm_export_identical"],
            "baseline_mesh_hash": pair["baseline_mesh_sha256"],
            "order_control_mesh_hash": pair["order_control_mesh_sha256"],
            "baseline_inputs_frozen_and_execution_successful": True,
            "order_control_inputs_frozen_and_execution_successful": True,
            "native_message_logs_report_no_alarms": True,
            "only_output_extraction_added": True,
            "native_attempts": [str(BASELINE.relative_to(ROOT)), str(CONTROL.relative_to(ROOT))],
        },
        "tolerances": {
            "body_interface_pair_and_cut_force_n": FORCE_TOL_N,
            "within_body_first_moment_balance_n_mm": MOMENT_TOL_N_MM,
            "baseline_to_reversed_force_resultant_n": ORDER_TOL_N,
            "baseline_to_reversed_displacement_component_mm": 1.0e-9,
        },
        "observed_maxima": maxima,
        "order_control_rn_resultant_delta_n_at_loaded_diagnostic_states": rn_order_deltas,
        "maximum_pointwise_baseline_to_order_control_field_deltas": pointwise_order_checks,
        "rn_gap_from_body_restricted_force_n_at_loaded_diagnostic_states": active_state_rn,
        "all_state_details": states,
        "all_state_order_comparisons": order_checks,
        "interpretation": {
            "body_restricted_route": "PASS",
            "contact_rn_to_body_force_screen": "FAILS; the gap exceeds the pre-existing 0.118-0.398 N state limits at all four loaded diagnostic states.",
            "order_control": "BOLT/WOOD body resultants, cut resultants, and displacement are invariant to roundoff under reversal; reported RN is order-sensitive.",
            "mechanical_acceptance": "NOT_INFERRED",
        },
        "limitations": [
            "This is an output-recovery and equilibrium check for one displacement-controlled contact crop, not an independent pressure solution.",
            "Body-restricted FORC_NODA comes from the same solved stress state; it verifies integrated force/wrench transmission and exposes the nonconservative RN output but does not recover local contact pressure.",
            "The displacement-controlled crop has no analytical force-magnitude oracle; the flat coupon provides the independent 3000 N resultant known-answer.",
            "The two contact surfaces are nonmatching and separated. Their first moments must not be compared as equal-and-opposite about a common origin without accounting for the force application locations.",
            "No wood response qualification, joint resistance, full-joint result, or candidate acceptance is inferred.",
        ],
        "route_status": "PASS" if all(
            maxima[name] <= limit for name, limit in (
                ("body_action_reaction_n", FORCE_TOL_N),
                ("bolt_plus_scut_n", FORCE_TOL_N),
                ("wood_plus_mcut_n", FORCE_TOL_N),
                ("bolt_action_reaction_moment_n_mm", MOMENT_TOL_N_MM),
                ("wood_action_reaction_moment_n_mm", MOMENT_TOL_N_MM),
                ("order_delta_bolt_force_n", ORDER_TOL_N),
                ("order_delta_wood_force_n", ORDER_TOL_N),
                ("order_delta_scut_n", ORDER_TOL_N),
                ("order_delta_mcut_n", ORDER_TOL_N),
                ("order_delta_depl_max_component", 1.0e-9),
            )
        ) and all(
            max(pointwise_order_checks[name].values()) <= ORDER_TOL_N
            for name in ("BOLT_SNODE_FORCE", "WOOD_MNODE_FORCE", "SCUT", "MCUT")
        ) else "FAIL",
        "mechanical_acceptance": "NOT_INFERRED",
    }
    output = args.output.resolve()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"route_status": result["route_status"], "observed_maxima": maxima,
                      "rn_order_deltas": rn_order_deltas,
                      "rn_gaps": active_state_rn, "output": str(output)}, indent=2))
    if result["route_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
