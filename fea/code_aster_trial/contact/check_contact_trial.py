#!/usr/bin/env python3
"""Check exported Code_Aster coupon tables against independent mechanics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys


# (time, imposed right-end DX); displacement in mm. Every listed time is an
# archived middle/end state from the prescribed opening-compression-reopening path.
HISTORY = (
    (0.00, 0.00),
    (0.25, 0.05),
    (0.50, 0.15),
    (0.75, 0.20),
    (1.00, 0.10),
    (1.25, 0.00),
    (1.50, -0.10),
    (1.75, -0.20),
    (2.00, -0.40),
    (2.25, -0.30),
    (2.50, -0.20),
    (2.75, -0.10),
    (3.00, 0.00),
    (3.25, 0.10),
)

E = 1000.0  # MPa = N/mm^2
NU = 0.25
L_TOTAL = 20.0  # mm
WIDTH = 10.0  # mm in the 2-D section
DEPTH = 1.0  # mm, plane-strain unit depth
LAM = E * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
MU = E / (2.0 * (1.0 + NU))
C11 = LAM + 2.0 * MU
STIFFNESS = C11 * WIDTH * DEPTH / L_TOTAL  # N/mm

FORCE_ABS_TOL = 0.05  # N
GAP_ABS_TOL = 2.0e-5  # mm
TIME_TOL = 1.0e-8


def normalized(value: str) -> str:
    return re.sub(r"[^A-Z0-9_]", "", value.upper())


def parse_table(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """Read semicolon IMPR_TABLE output, ignoring its human-readable preamble."""
    lines = path.read_text(errors="replace").splitlines()
    header = None
    rows: list[dict[str, str]] = []
    for line in lines:
        cells = next(csv.reader([line], delimiter=";", skipinitialspace=True))
        cells = [c.strip() for c in cells]
        keys = [normalized(c) for c in cells]
        if all(name in keys for name in required):
            header = keys
            continue
        if header is None or not line.strip() or line.lstrip().startswith(("#", "*")):
            continue
        if len(cells) != len(header):
            continue
        # IMPR_TABLE may emit an additional human-readable heading between tables.
        if any(normalized(c) in required for c in cells):
            header = keys
            continue
        rows.append(dict(zip(header, cells)))
    if not rows:
        raise ValueError(
            f"No rows with columns {required} could be parsed from {path}. "
            "Inspect the frozen run's IMPR_TABLE output and adapt only the parser."
        )
    return rows


def number(row: dict[str, str], name: str) -> float:
    value = row.get(name)
    if value is None or not value.strip():
        raise ValueError(f"Missing {name} in parsed table row: {row}")
    result = float(value.replace("D", "E").replace("d", "e"))
    if not math.isfinite(result):
        raise ValueError(f"Non-finite {name} in parsed table row: {row}")
    return result


def assert_two_distinct_nodes(rows: list[dict[str, str]], table_name: str, inst: float) -> None:
    """Reject duplicated/missing extraction rows rather than summing them twice."""
    node_column = next((name for name in ("NOEUD", "NOEUD_CMP") if name in rows[0]), None)
    if node_column is None:
        raise ValueError(f"{table_name} table has no NOEUD/NOEUD_CMP key for duplicate checking")
    nodes = [row[node_column].strip() for row in rows]
    if any(not node for node in nodes) or len(set(nodes)) != 2:
        raise ValueError(f"Expected two distinct node rows in {table_name} at INST={inst:g}, got {nodes}")


def grouped(rows: list[dict[str, str]]) -> dict[float, list[dict[str, str]]]:
    by_time: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        t = number(row, "INST")
        by_time.setdefault(t, []).append(row)
    return by_time


def closest_time(data: dict[float, list[dict[str, str]]], target: float) -> list[dict[str, str]]:
    candidates = [(abs(t - target), rows) for t, rows in data.items()]
    error, rows = min(candidates, key=lambda item: item[0])
    if error > TIME_TOL:
        raise ValueError(f"No output at INST={target:g}; nearest archived time differs by {error:g}")
    return rows


def assert_archived_times(data: dict[float, list[dict[str, str]]], table_name: str) -> None:
    expected_times = [inst for inst, _ in HISTORY]
    if len(data) != len(expected_times):
        raise ValueError(
            f"Expected exactly {len(expected_times)} archived instants in {table_name}, got {sorted(data)}"
        )
    unmatched = [target for target in expected_times if min(abs(t - target) for t in data) > TIME_TOL]
    if unmatched:
        raise ValueError(f"Missing {table_name} archive instants: {unmatched}")
    unexpected = [t for t in data if min(abs(t - target) for target in expected_times) > TIME_TOL]
    if unexpected:
        raise ValueError(f"Unexpected {table_name} archive instants: {unexpected}")


def check(contact_path: Path, reaction_path: Path) -> list[dict[str, object]]:
    contact_rows = parse_table(contact_path, ("INST", "JEU", "RNX"))
    reaction_rows = parse_table(reaction_path, ("INST", "DX"))
    contact = grouped(contact_rows)
    reactions = grouped(reaction_rows)
    assert_archived_times(contact, "contact")
    assert_archived_times(reactions, "right-end reaction")
    reports: list[dict[str, object]] = []

    for inst, imposed_dx in HISTORY:
        crows = closest_time(contact, inst)
        rrows = closest_time(reactions, inst)
        if len(crows) != 2:
            raise ValueError(f"Expected both slave-node contact rows at INST={inst:g}, got {len(crows)}")
        if len(rrows) != 2:
            raise ValueError(f"Expected both right-end reaction rows at INST={inst:g}, got {len(rrows)}")
        assert_two_distinct_nodes(crows, "contact", inst)
        assert_two_distinct_nodes(rrows, "right-end reaction", inst)

        gap_values = [number(row, "JEU") for row in crows]
        reported_rnx_sum = sum(number(row, "RNX") for row in crows)
        contact_resultant = abs(reported_rnx_sum)
        end_dx_sum = sum(number(row, "DX") for row in rrows)
        end_resultant = abs(end_dx_sum)
        expected_force = STIFFNESS * max(0.0, -imposed_dx)
        expected_end_dx_sum = -expected_force
        expected_gap = max(0.0, imposed_dx)

        if expected_force > FORCE_ABS_TOL:
            if max(abs(gap) for gap in gap_values) > GAP_ABS_TOL:
                raise ValueError(f"Closed-contact gap not near zero at INST={inst:g}: {gap_values}")
        elif expected_gap > GAP_ABS_TOL:
            if min(gap_values) < -GAP_ABS_TOL:
                raise ValueError(f"Opening state has negative slave gap at INST={inst:g}: {gap_values}")
            for gap in gap_values:
                if abs(gap - expected_gap) > GAP_ABS_TOL:
                    raise ValueError(
                        f"Open gap mismatch at INST={inst:g}: got {gap_values}, expected {expected_gap:g} mm"
                    )
        else:
            if any(abs(gap) > GAP_ABS_TOL for gap in gap_values):
                raise ValueError(f"Zero-displacement contact gap not near zero at INST={inst:g}: {gap_values}")

        if abs(contact_resultant - expected_force) > FORCE_ABS_TOL:
            raise ValueError(
                f"Contact resultant mismatch at INST={inst:g}: {contact_resultant:g} N, "
                f"expected {expected_force:g} N"
            )
        if abs(end_resultant - expected_force) > FORCE_ABS_TOL:
            raise ValueError(
                f"Right-end reaction mismatch at INST={inst:g}: {end_resultant:g} N, "
                f"expected {expected_force:g} N"
            )
        if abs(end_dx_sum - expected_end_dx_sum) > FORCE_ABS_TOL:
            raise ValueError(
                f"Signed right-end DX sum mismatch at INST={inst:g}: {end_dx_sum:g} N, "
                f"expected {expected_end_dx_sum:g} N"
            )
        if abs(contact_resultant - end_resultant) > FORCE_ABS_TOL:
            raise ValueError(
                f"Independent resultants disagree at INST={inst:g}: contact={contact_resultant:g} N, "
                f"right end={end_resultant:g} N"
            )
        reports.append({
            "inst": inst,
            "imposed_dx_mm": imposed_dx,
            "expected_force_magnitude_n": expected_force,
            "expected_gap_mm": expected_gap,
            "reported_rnx_sum_n": reported_rnx_sum,
            "contact_resultant_magnitude_n": contact_resultant,
            "right_end_forc_noda_dx_sum_n": end_dx_sum,
            "right_end_resultant_magnitude_n": end_resultant,
            "slave_jeu_mm": gap_values,
        })
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contact_table", type=Path)
    parser.add_argument("reaction_table", type=Path)
    parser.add_argument("--json", type=Path, help="Write a machine-readable checked-state summary")
    args = parser.parse_args()
    try:
        print(f"Analytic plane-strain stiffness: {STIFFNESS:.8g} N/mm (C11={C11:.8g} MPa)")
        states = check(args.contact_table, args.reaction_table)
        for state in states:
            print(
                f"INST={state['inst']:4.2f}: U={state['imposed_dx_mm']:+.3f} mm, "
                f"RNXsum={state['reported_rnx_sum_n']:+.5f} N "
                f"(|.|={state['contact_resultant_magnitude_n']:.5f}), "
                f"right-end DXsum={state['right_end_forc_noda_dx_sum_n']:+.5f} N, "
                f"JEU={state['slave_jeu_mm']} mm"
            )
        if args.json:
            summary = {
                "scope": "Code_Aster stock contact method coupon; mechanical acceptance not inferred",
                "analysis_kind": "post-run oracle check of frozen output tables; no native rerun",
                "runtime_image": "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5",
                "analytic_plane_strain_stiffness_n_per_mm": STIFFNESS,
                "plane_strain_C11_mpa": C11,
                "force_tolerance_n": FORCE_ABS_TOL,
                "gap_tolerance_mm": GAP_ABS_TOL,
                "checked_archive_count": len(states),
                "input_tables": {
                    str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (args.contact_table, args.reaction_table)
                },
                "states": states,
            }
            args.json.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    except (OSError, ValueError, csv.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: contact gap, contact resultant magnitude, and signed independent end force match the coupon oracle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
