#!/usr/bin/env python3
"""Check CALC_PRESSION output and mechanical parity for the plane contact coupon."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys


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

C11_MPA = 1200.0
AREA_MM2 = 10.0  # 10 mm interface in a 1 mm plane-strain depth
STIFFNESS_N_PER_MM = 600.0
TIME_TOL = 1.0e-8
PRESSURE_TOL_MPA = 1.0e-6
SHEAR_TOL_MPA = 1.0e-6
INTEGRATED_FORCE_TOL_N = 0.01
PARITY_TOL = 1.0e-10

CONTACT_PARITY_FIELDS = (
    "COOR_X", "COOR_Y", "COOR_Z", "CONT", "JEU", "RN", "RNX", "RNY", "RNZ",
    "GLIX", "GLIY", "GLI", "RTAX", "RTAY", "RTAZ", "RTGX", "RTGY", "RTGZ",
)
REACTION_PARITY_FIELDS = ("COOR_X", "COOR_Y", "COOR_Z", "DX", "DY")


def norm(value: str) -> str:
    return re.sub(r"[^A-Z0-9_]", "", value.upper())


def parse_table(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    header = None
    rows: list[dict[str, str]] = []
    for line in path.read_text(errors="replace").splitlines():
        cells = [cell.strip() for cell in next(csv.reader([line], delimiter=";"))]
        keys = [norm(cell) for cell in cells]
        if all(name in keys for name in required):
            header = keys
            continue
        if header is None or len(cells) != len(header):
            continue
        if any(key in required for key in keys):
            header = keys
            continue
        rows.append(dict(zip(header, cells)))
    if not rows:
        raise ValueError(f"Could not parse {path} with columns {required}")
    return rows


def val(row: dict[str, str], key: str) -> float:
    raw = row.get(key)
    if raw is None or not raw.strip():
        raise ValueError(f"Missing {key} in {row}")
    out = float(raw.replace("D", "E").replace("d", "e"))
    if not math.isfinite(out):
        raise ValueError(f"Nonfinite {key} in {row}")
    return out


def groups(rows: list[dict[str, str]]) -> dict[float, list[dict[str, str]]]:
    out: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        out.setdefault(val(row, "INST"), []).append(row)
    return out


def closest(data: dict[float, list[dict[str, str]]], target: float) -> list[dict[str, str]]:
    time, rows = min(data.items(), key=lambda item: abs(item[0] - target))
    if abs(time - target) > TIME_TOL:
        raise ValueError(f"Missing INST={target:g}; nearest is {time:g}")
    return rows


def verify_times(data: dict[float, list[dict[str, str]]], label: str) -> None:
    expected = [time for time, _ in HISTORY]
    if len(data) != len(expected) or any(
        min(abs(time - wanted) for time in data) > TIME_TOL for wanted in expected
    ):
        raise ValueError(f"Unexpected archived times in {label}: {sorted(data)}")


def key_rows(rows: list[dict[str, str]], label: str) -> dict[tuple[str, float], dict[str, str]]:
    out: dict[tuple[str, float], dict[str, str]] = {}
    for row in rows:
        node_key = "NOEUD" if "NOEUD" in row else "NOEUD_CMP"
        if node_key not in row:
            raise ValueError(f"{label} rows have no node identity: {row}")
        key = (row[node_key].strip(), val(row, "INST"))
        if key in out:
            raise ValueError(f"Duplicate {label} row for {key}")
        out[key] = row
    return out


def compare_parity(
    current: list[dict[str, str]],
    baseline: list[dict[str, str]],
    fields: tuple[str, ...],
    label: str,
) -> dict[str, object]:
    now = key_rows(current, label)
    old = key_rows(baseline, f"baseline {label}")
    if now.keys() != old.keys():
        raise ValueError(f"{label} rows/identities differ from mechanical baseline")
    max_diff = 0.0
    worst = None
    for key in sorted(now):
        for field in fields:
            delta = abs(val(now[key], field) - val(old[key], field))
            if delta > max_diff:
                max_diff, worst = delta, {"row": key, "field": field}
    if max_diff > PARITY_TOL:
        raise ValueError(f"{label} mechanical output changed by {max_diff:g} at {worst}")
    return {"rows": len(now), "fields": list(fields), "max_abs_difference": max_diff,
            "tolerance": PARITY_TOL, "worst_comparison": worst}


def check(
    contact_path: Path,
    reaction_path: Path,
    pressure_path: Path,
    baseline_contact_path: Path,
    baseline_reaction_path: Path,
) -> dict[str, object]:
    contact = parse_table(contact_path, ("INST", "JEU", "RNX"))
    reactions = parse_table(reaction_path, ("INST", "DX"))
    pressures = parse_table(pressure_path, ("INST", "PRES", "CISA"))
    ctime, rtime, ptime = groups(contact), groups(reactions), groups(pressures)
    for data, label in ((ctime, "contact"), (rtime, "reaction"), (ptime, "pressure")):
        verify_times(data, label)

    state_reports = []
    for inst, displacement in HISTORY:
        crows, rrows, prows = closest(ctime, inst), closest(rtime, inst), closest(ptime, inst)
        for rows, label in ((crows, "contact"), (rrows, "reaction"), (prows, "pressure")):
            nodekey = "NOEUD" if "NOEUD" in rows[0] else "NOEUD_CMP"
            nodes = {row[nodekey].strip() for row in rows}
            if len(rows) != 2 or len(nodes) != 2:
                raise ValueError(f"Expected exactly two distinct {label} nodes at {inst:g}: {nodes}")
        pnodekey = "NOEUD" if "NOEUD" in prows[0] else "NOEUD_CMP"
        if {row[pnodekey].strip() for row in prows} != {"5", "8"}:
            raise ValueError(f"Pressure nodes do not match slave interface at INST={inst:g}")

        expected_force = STIFFNESS_N_PER_MM * max(0.0, -displacement)
        # CALC_PRESSION projects the slave-side Cauchy stress; it does not
        # mask the field by contact status. In opening, the right block is in
        # uniaxial tension (C11*u/10); in compression both blocks share the
        # closure equally (C11*u/20).
        expected_pressure = C11_MPA * displacement / (10.0 if displacement >= 0 else 20.0)
        pressure_values = [val(row, "PRES") for row in prows]
        shear_values = [val(row, "CISA") for row in prows]
        if max(abs(value - expected_pressure) for value in pressure_values) > PRESSURE_TOL_MPA:
            raise ValueError(
                f"PRES mismatch at INST={inst:g}: {pressure_values}, expected {expected_pressure:g} MPa"
            )
        if max(abs(value) for value in shear_values) > SHEAR_TOL_MPA:
            raise ValueError(f"Unexpected shear pressure at INST={inst:g}: {shear_values} MPa")
        integrated_force = None
        if displacement < -TIME_TOL:
            integrated_force = -sum(pressure_values) * 0.5 * AREA_MM2
            if abs(integrated_force - expected_force) > INTEGRATED_FORCE_TOL_N:
                raise ValueError(
                    f"Pressure integral mismatch at INST={inst:g}: {integrated_force:g} N, "
                    f"expected {expected_force:g} N"
                )
        state_reports.append({
            "inst": inst,
            "imposed_right_dx_mm": displacement,
            "expected_pressure_mpa": expected_pressure,
            "reported_nodal_pressure_mpa": pressure_values,
            "reported_nodal_cisa_mpa": shear_values,
            "integrated_normal_force_magnitude_n": integrated_force,
            "integral_is_contact_resultant": displacement < -TIME_TOL,
            "expected_force_magnitude_n": expected_force,
        })

    contact_parity = compare_parity(
        contact, parse_table(baseline_contact_path, ("INST", "JEU", "RNX")),
        CONTACT_PARITY_FIELDS, "contact",
    )
    reaction_parity = compare_parity(
        reactions, parse_table(baseline_reaction_path, ("INST", "DX")),
        REACTION_PARITY_FIELDS, "right-end reaction",
    )
    return {
        "scope": "2-D straight plane-strain CALC_PRESSION known-answer only; curved 3-D applicability not inferred",
        "analytic_plane_strain_modulus_mpa": C11_MPA,
        "analytic_series_stiffness_n_per_mm": STIFFNESS_N_PER_MM,
        "interface_area_mm2": AREA_MM2,
        "pressure_tolerance_mpa": PRESSURE_TOL_MPA,
        "shear_tolerance_mpa": SHEAR_TOL_MPA,
        "integrated_force_tolerance_n": INTEGRATED_FORCE_TOL_N,
        "instrumentation_mechanical_parity": {
            "contact": contact_parity,
            "right_end_reaction": reaction_parity,
        },
        "states": state_reports,
        "input_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (contact_path, reaction_path, pressure_path,
                         baseline_contact_path, baseline_reaction_path)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contact", type=Path)
    parser.add_argument("reaction", type=Path)
    parser.add_argument("pressure", type=Path)
    parser.add_argument("baseline_contact", type=Path)
    parser.add_argument("baseline_reaction", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    try:
        report = check(args.contact, args.reaction, args.pressure,
                       args.baseline_contact, args.baseline_reaction)
        for state in report["states"]:
            print(
                f"INST={state['inst']:4.2f}: P={state['reported_nodal_pressure_mpa']} MPa, "
                f"CISA={state['reported_nodal_cisa_mpa']} MPa, "
                f"contact_integral={state['integrated_normal_force_magnitude_n']} N"
            )
        if args.json:
            args.json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    except (OSError, ValueError, csv.Error, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: analytic pressure, shear, pressure resultant, and instrumentation parity match frozen limits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
