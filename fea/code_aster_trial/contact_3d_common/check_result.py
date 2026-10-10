#!/usr/bin/env python3
"""Audit the frozen 3-D contact coupon tables; no solver invocation."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from preflight import parse_mesh


def rows(path: Path):
    with path.open(newline="") as stream:
        reader = csv.DictReader((line for line in stream if not line.startswith("#")), delimiter=";")
        if reader.fieldnames is None:
            raise ValueError(f"no CSV header in {path}")
        return [{k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
                for row in reader]


def number(row, name):
    return float(row[name])


def final_rows(path: Path, inst: float = 1.0):
    result = [r for r in rows(path) if abs(number(r, "INST") - inst) < 1.0e-10]
    if not result:
        raise ValueError(f"no data at INST={inst:g} in {path}")
    return result


def vector_sum(items, fields=("DX", "DY", "DZ")):
    return np.asarray([sum(number(r, field) for r in items) for field in fields])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve()
    source = json.loads((attempt / "input-freeze.json").read_text())
    frozen_hashes = source["input_sha256"]
    changed = []
    import hashlib
    for name, expected in frozen_hashes.items():
        p = attempt / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            changed.append(name)
    if changed:
        raise ValueError(f"frozen input hash mismatch: {changed}")
    readiness = json.loads((attempt / "readiness.json").read_text())
    variant = readiness["variant"]
    mail_lines, coords, _penta, tria, gm, gn = parse_mesh(attempt / "contact_coupon.mail")
    _ = mail_lines
    contact = final_rows(attempt / "contact.csv")
    lagrange = final_rows(attempt / "lagrange.csv")
    stress = final_rows(attempt / "stress.csv")
    slave_cut_force = final_rows(attempt / "slave_cut_force.csv")
    master_cut_force = final_rows(attempt / "master_cut_force.csv")
    slave_cut_reaction = final_rows(attempt / "slave_cut_reaction.csv")
    master_cut_reaction = final_rows(attempt / "master_cut_reaction.csv")
    node_id = {label: str(int(label[1:])) for label in coords}
    for name, data, expected in (("CONT_NOEU", contact, gn["SLNOD"]),
                                 ("DEPL/LAGS_C", lagrange, gn["SLNOD"]),
                                 ("SIEF_NOEU", stress, gn["SLNOD"]),
                                 ("SCUT/FORC_NODA", slave_cut_force, gn["SCUT"]),
                                 ("MCUT/FORC_NODA", master_cut_force, gn["MCUT"]),
                                 ("SCUT/REAC_NODA", slave_cut_reaction, gn["SCUT"]),
                                 ("MCUT/REAC_NODA", master_cut_reaction, gn["MCUT"])):
        labels = {row["NOEUD"] for row in data}
        if labels != {node_id[label] for label in expected}:
            raise ValueError(f"{name} nodal coverage differs: got {len(labels)}, expected {len(expected)}")

    rn = np.asarray([sum(number(r, field) for r in contact) for field in ("RNX", "RNY", "RNZ")])
    fs_force = vector_sum(slave_cut_force)
    fm_force = vector_sum(master_cut_force)
    fs_reaction = vector_sum(slave_cut_reaction)
    fm_reaction = vector_sum(master_cut_reaction)
    lam_values = np.asarray([number(r, "LAGS_C") for r in lagrange])
    sizz_values = np.asarray([number(r, "SIZZ") for r in stress])
    gap_values = np.asarray([number(r, "JEU") for r in contact])
    statuses = sorted(set(number(r, "CONT") for r in contact))
    report = {
        "variant": variant,
        "scope": "bounded output/method fixture only; mechanical acceptance NOT_INFERRED",
        "native_execution": json.loads((attempt / "execution.json").read_text()),
        "final_instant": 1.0,
        "coverage_counts": {"CONT_NOEU": len(contact), "DEPL_LAGS_C": len(lagrange),
                            "SIEF_NOEU": len(stress), "SCUT_FORC_NODA": len(slave_cut_force),
                            "MCUT_FORC_NODA": len(master_cut_force),
                            "SCUT_REAC_NODA": len(slave_cut_reaction),
                            "MCUT_REAC_NODA": len(master_cut_reaction)},
        "contact_status_values": statuses,
        "contact_gap_mm": {"min": float(np.min(gap_values)), "max": float(np.max(gap_values)),
                            "max_abs": float(np.max(np.abs(gap_values)))},
        "rn_vector_n": rn.tolist(),
        "slave_cut_forc_noda_n": fs_force.tolist(),
        "master_cut_forc_noda_n": fm_force.tolist(),
        "slave_cut_reac_noda_n": fs_reaction.tolist(),
        "master_cut_reac_noda_n": fm_reaction.tolist(),
        "forc_noda_cut_pair_sum_n": (fs_force + fm_force).tolist(),
        "reac_noda_cut_pair_sum_n": (fs_reaction + fm_reaction).tolist(),
        "rn_minus_slave_reac_noda_n": (rn - fs_reaction).tolist(),
        "rn_z_vs_slave_reac_noda_residual_n": float(rn[2] - fs_reaction[2]),
        "lags_c_mpa": {"min": float(np.min(lam_values)), "max": float(np.max(lam_values)),
                        "mean": float(np.mean(lam_values)),
                        "max_abs_error_from_minus_0p3": float(np.max(np.abs(lam_values + 0.3)))},
        "sizz_mpa": {"min": float(np.min(sizz_values)), "max": float(np.max(sizz_values)),
                     "mean": float(np.mean(sizz_values)),
                     "max_abs_error_from_minus_0p3": float(np.max(np.abs(sizz_values + 0.3)))},
    }

    tolerances = {"force_n": 0.1, "pressure_mpa": 0.003, "stress_mpa": 0.003,
                  "gap_mm": 0.01}
    report["frozen_limits"] = tolerances
    if variant == "flat-full-contact":
        report["checks"] = {
            "all_slave_nodes_active": statuses == [2.0],
            "reac_noda_cut_z_resultants_equal_opposite": abs(fs_reaction[2] + fm_reaction[2]) <= tolerances["force_n"],
            "slave_reac_noda_matches_analytic_force": abs(abs(fs_reaction[2]) - 3000.0) <= tolerances["force_n"],
            "master_reac_noda_matches_analytic_force": abs(abs(fm_reaction[2]) - 3000.0) <= tolerances["force_n"],
            "rn_matches_slave_cut_reac_noda_vector": float(np.linalg.norm(rn - fs_reaction)) <= tolerances["force_n"],
            "lags_c_matches_analytic_uniform_pressure": float(np.max(np.abs(lam_values + 0.3))) <= tolerances["pressure_mpa"],
            "stress_matches_analytic_uniform_pressure": float(np.max(np.abs(sizz_values + 0.3))) <= tolerances["stress_mpa"],
            "gap_below_limit": float(np.max(np.abs(gap_values))) <= tolerances["gap_mm"],
            "no_tangential_contact_resultant": float(np.linalg.norm(rn[:2])) <= tolerances["force_n"],
            "forc_noda_slave_cut_matches_analytic_force_magnitude": abs(abs(fs_force[2]) - 3000.0) <= tolerances["force_n"],
            "forc_noda_master_cut_matches_analytic_force_magnitude": abs(abs(fm_force[2]) - 3000.0) <= tolerances["force_n"],
        }
        report["checks"] = {key: bool(value) for key, value in report["checks"].items()}
        report["status"] = "PASS" if all(report["checks"].values()) else "FAIL"
    elif variant == "mixed-active-open":
        active_label = readiness.get("active_slave_face_label", "ST00001")
        open_label = readiness.get("open_slave_face_label", "ST00002")
        contact_group_order = readiness.get("contact_group_order", gm["SLAVE"])
        active_conn = set(tria[active_label])
        open_conn = set(tria[open_label])
        shared = active_conn & open_conn
        active_only = active_conn - shared
        open_only = open_conn - shared
        by_node = {r["NOEUD"]: r for r in contact}
        active_ids = {node_id[node] for node in active_only}
        open_ids = {node_id[node] for node in open_only}
        shared_ids = {node_id[node] for node in shared}
        active_statuses = {node: number(by_node[node], "CONT") for node in active_ids}
        open_statuses = {node: number(by_node[node], "CONT") for node in open_ids}
        shared_statuses = {node: number(by_node[node], "CONT") for node in shared_ids}
        shared_rn = {node: number(by_node[node], "RN") for node in shared_ids}
        active_only_rn = {node: number(by_node[node], "RN") for node in active_ids}
        later_face = contact_group_order[-1]
        later_face_is_active = later_face == active_label
        expected_shared_status = 2.0 if later_face_is_active else 0.0
        rn_z_vs_cut_residual = float(rn[2] - fs_reaction[2])
        diagnostics = {
            "active_slave_face": active_label,
            "open_slave_face": open_label,
            "slave_contact_group_order": contact_group_order,
            "later_face_is_active": later_face_is_active,
            "active_face_unique_node_statuses": active_statuses,
            "open_face_unique_node_statuses": open_statuses,
            "shared_node_statuses_after_all_face_writes": shared_statuses,
            "shared_node_RN_after_all_face_writes_N": shared_rn,
            "active_face_only_RN_N": active_only_rn,
            "slave_cut_reaction_magnitude_n": float(np.linalg.norm(fs_reaction)),
            "RN_sum_magnitude_n": float(np.linalg.norm(rn)),
            "RN_cut_relative_discrepancy": float(np.linalg.norm(rn - fs_reaction) / max(np.linalg.norm(fs_reaction), 1.0e-12)),
            "RN_z_vs_SCUT_REAC_NODA_residual_n": rn_z_vs_cut_residual,
        }
        shared_rn_matches_order = (
            max(abs(v) for v in shared_rn.values()) > 1.0e-8
            if later_face_is_active
            else all(abs(v) <= 1.0e-10 for v in shared_rn.values())
        )
        witness = (all(v == 2.0 for v in active_statuses.values())
                   and all(v == 0.0 for v in open_statuses.values())
                   and all(v == expected_shared_status for v in shared_statuses.values())
                   and shared_rn_matches_order
                   and max(abs(v) for v in active_only_rn.values()) > 1.0e-8
                   and abs(fs_reaction[2] + fm_reaction[2]) <= tolerances["force_n"])
        report["diagnostics"] = diagnostics
        report["status"] = "CONSISTENT_WITH_SOURCE_ORDERED_OVERWRITE" if witness else "INCONCLUSIVE_OR_HYPOTHESIS_NOT_OBSERVED"
    else:
        raise ValueError(f"unknown frozen variant {variant!r}")

    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["status"] in {"FAIL", "INCONCLUSIVE_OR_HYPOTHESIS_NOT_OBSERVED"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
