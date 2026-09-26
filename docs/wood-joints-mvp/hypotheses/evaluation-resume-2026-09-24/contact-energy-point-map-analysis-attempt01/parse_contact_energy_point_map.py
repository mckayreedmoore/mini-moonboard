#!/usr/bin/env python3
"""Audit the first complete accepted C contact-energy map block against DAT tags."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Iterable

CSV_FIELDS = [
    "record_type", "step", "increment", "time_s", "dtime_s",
    "element_c_index", "element_fortran_number", "igauss", "jfaces",
    "spring_area_mm2", "native_clear_mm", "pressure_N_per_mm2",
    "writer_energy_index_fortran", "writer_elastic_Nmm", "writer_viscous_Nmm",
    "compact_energy_index_fortran", "compact_elastic_Nmm", "compact_viscous_Nmm",
    "nener", "mi0", "ne0", "ne", "point_count",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dec(token: str) -> Decimal:
    return Decimal(token.strip().replace("D", "E").replace("d", "e"))


def numeric_tolerance(*tokens: str) -> Decimal:
    """Sum half-units in the last printed decimal place for source tokens."""
    total = Decimal(0)
    for token in tokens:
        value = dec(token)
        total += Decimal("0.5") * (Decimal(10) ** value.as_tuple().exponent)
    return total


def close_tokens(a: str, b: str) -> bool:
    return abs(dec(a) - dec(b)) <= numeric_tolerance(a, b)


def read_sta(path: Path) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]]]:
    accepted: dict[tuple[int, int], dict[str, Any]] = {}
    rejected: list[dict[str, Any]] = []
    with path.open(encoding="ascii", errors="replace") as stream:
        for line in stream:
            parts = line.split()
            if len(parts) < 7 or not parts[0].isdigit() or not parts[1].isdigit():
                continue
            if parts[2].rstrip("Uu").isdigit() is False:
                continue
            step, inc = int(parts[0]), int(parts[1])
            accepted_attempt = parts[2].isdigit()
            row = {
                "step": step,
                "increment": inc,
                "attempt": parts[2],
                "accepted": accepted_attempt,
                "total_time_token": parts[4],
                "step_time_token": parts[5],
                "increment_time_token": parts[6],
                "iterations_token": parts[3],
            }
            if accepted_attempt:
                if (step, inc) in accepted:
                    raise ValueError(f"duplicate accepted STA identity step={step} inc={inc}")
                accepted[(step, inc)] = row
            else:
                rejected.append(row)
    return accepted, rejected


def sta_matches_block(sta_row: dict[str, Any], block: dict[str, Any]) -> bool:
    # .sta carries fewer significant digits than the C CSV. Use its printed
    # rounding quantum as the acceptance window, and also bind dtime to INC TIME.
    return (
        abs(dec(sta_row["total_time_token"]) - dec(block["time_s"]))
        <= numeric_tolerance(sta_row["total_time_token"])
        and abs(dec(sta_row["increment_time_token"]) - dec(block["dtime_s"]))
        <= numeric_tolerance(sta_row["increment_time_token"])
    )


def parse_csv_blocks(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocks: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    with path.open(newline="", encoding="ascii", errors="strict") as stream:
        reader = csv.reader(stream)
        for line_no, fields in enumerate(reader, 1):
            if not fields:
                continue
            if fields[0] == "record_type":
                if fields != CSV_FIELDS:
                    raise ValueError(f"CSV header differs from pinned 23-column schema at line {line_no}")
                continue
            if fields[0] == "STATE":
                if current is not None:
                    incomplete.append({"line": current["line"], "reason": "new STATE before END"})
                if len(fields) != len(CSV_FIELDS):
                    raise ValueError(f"STATE row has {len(fields)} columns at line {line_no}")
                current = {"line": line_no, "state": dict(zip(CSV_FIELDS, fields)), "points": []}
            elif fields[0] == "POINT":
                if current is None:
                    raise ValueError(f"POINT row outside STATE block at line {line_no}")
                if len(fields) != len(CSV_FIELDS):
                    raise ValueError(f"POINT row has {len(fields)} columns at line {line_no}")
                row = dict(zip(CSV_FIELDS, fields))
                st = current["state"]
                for name in ("step", "increment", "time_s", "dtime_s"):
                    if name in ("step", "increment"):
                        same = row[name] == st[name]
                    else:
                        same = close_tokens(row[name], st[name])
                    if not same:
                        raise ValueError(f"POINT/STATE {name} mismatch at line {line_no}")
                current["points"].append(row)
            elif fields[0] == "END":
                if current is None:
                    raise ValueError(f"END row outside STATE block at line {line_no}")
                if len(fields) != len(CSV_FIELDS):
                    raise ValueError(f"END row has {len(fields)} columns at line {line_no}")
                st = current["state"]
                for name in ("step", "increment"):
                    if fields[CSV_FIELDS.index(name)] != st[name]:
                        raise ValueError(f"END/STATE {name} mismatch at line {line_no}")
                for name in ("time_s", "dtime_s"):
                    if not close_tokens(fields[CSV_FIELDS.index(name)], st[name]):
                        raise ValueError(f"END/STATE {name} mismatch at line {line_no}")
                declared_state = int(st["point_count"])
                declared_end = int(fields[CSV_FIELDS.index("point_count")])
                actual_count = len(current["points"])
                current["end_line"] = line_no
                current["declared_state_count"] = declared_state
                current["declared_end_count"] = declared_end
                current["actual_point_count"] = actual_count
                current["complete"] = declared_state == declared_end == actual_count
                current["state_key"] = (int(st["step"]), int(st["increment"]))
                if current["complete"]:
                    blocks.append(current)
                else:
                    incomplete.append({
                        "line": current["line"],
                        "end_line": line_no,
                        "step": st["step"],
                        "increment": st["increment"],
                        "declared_state_count": declared_state,
                        "declared_end_count": declared_end,
                        "actual_point_count": actual_count,
                        "reason": "STATE/END/actual POINT count mismatch",
                    })
                current = None
            else:
                raise ValueError(f"unknown record type {fields[0]!r} at line {line_no}")
    if current is not None:
        incomplete.append({"line": current["line"], "reason": "EOF before END"})
    return blocks, incomplete


def accepted_blocks(blocks: list[dict[str, Any]], accepted: dict[tuple[int, int], dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    result = []
    for block in blocks:
        sta = accepted.get(block["state_key"])
        if sta is not None and sta_matches_block(sta, block["state"]):
            result.append((block, sta))
    return result


def parse_dat(path: Path) -> dict[str, Any]:
    cep: list[dict[str, Any]] = []
    eif: list[dict[str, Any]] = []
    cels: list[dict[str, Any]] = []
    pending_cep: dict[str, Any] | None = None
    pending_eif: dict[str, Any] | None = None
    cels_header_re = re.compile(r"contact spring energy .*? time\s+([^\s]+)", re.I)
    eif_re = re.compile(
        r"WJ_E_IF_FRICTIONLESS_LINEAR_DYNAMIC\s+pair=\s*(\d+),\s*slave=(.*?),\s*master=(.*?),\s*time=\s*([^\s]+)"
    )
    with path.open(encoding="ascii", errors="replace") as stream:
        lines = iter(stream)
        for line_no, line in enumerate(lines, 1):
            if line.startswith("WJ_CEP_POINT,"):
                if pending_cep is not None:
                    pending_cep["complete"] = False
                    cep.append(pending_cep)
                fields = [f.strip() for f in line.strip().split(",")]
                if len(fields) != 8:
                    pending_cep = {"line": line_no, "complete": False, "parse_error": f"point fields={len(fields)}"}
                    continue
                pending_cep = {
                    "line": line_no,
                    "tie": int(fields[1]),
                    "slave": fields[2],
                    "master": fields[3],
                    "element_fortran_number": int(fields[4]),
                    "igauss": int(fields[5]),
                    "jfaces": int(fields[6]),
                    "time_token": fields[7],
                    "complete": False,
                }
            elif line.startswith("WJ_CEP_VALUE,"):
                fields = [f.strip() for f in line.strip().split(",")]
                if pending_cep is None or len(fields) != 6:
                    if pending_cep is not None:
                        pending_cep["parse_error"] = f"value fields={len(fields)}"
                        cep.append(pending_cep)
                        pending_cep = None
                    continue
                try:
                    pending_cep.update({
                        "area_token": fields[1],
                        "native_clear_token": fields[2],
                        "pressure_token": fields[3],
                        "clearproj_token": fields[4],
                        "printer_energy_token": fields[5],
                        "complete": True,
                    })
                except IndexError:
                    pending_cep["complete"] = False
                cep.append(pending_cep)
                pending_cep = None
            else:
                if pending_cep is not None and line.strip():
                    pending_cep["complete"] = False
                    pending_cep["parse_error"] = "non-value line between point and value"
                    cep.append(pending_cep)
                    pending_cep = None
            if pending_cep is not None and not line.startswith("WJ_CEP_POINT,") and not line.startswith("WJ_CEP_VALUE,"):
                if line.strip():
                    pending_cep["complete"] = False
                    pending_cep["parse_error"] = "non-value line between point and value"
                    cep.append(pending_cep)
                    pending_cep = None

            match = eif_re.search(line)
            if match:
                pending_eif = {
                    "line": line_no,
                    "tie": int(match.group(1)),
                    "slave": match.group(2),
                    "master": match.group(3),
                    "time_token": match.group(4),
                }
                try:
                    next_line = next(lines)
                    line_no += 1
                    val = next_line.strip().split()
                    if not val:
                        raise ValueError("empty WJ_E_IF value row")
                    pending_eif["energy_token"] = val[0]
                    eif.append(pending_eif)
                except (StopIteration, ValueError):
                    pending_eif["incomplete"] = True
                    eif.append(pending_eif)
                pending_eif = None

            cels_match = cels_header_re.search(line)
            if cels_match:
                time_token = cels_match.group(1)
                rows = 0
                total = Decimal(0)
                saw_data = False
                for cels_line in lines:
                    if not cels_line.strip():
                        if saw_data:
                            break
                        continue
                    fields = cels_line.split()
                    if len(fields) < 3:
                        if saw_data:
                            break
                        continue
                    try:
                        row_energy = dec(fields[2])
                    except Exception:
                        if saw_data:
                            break
                        continue
                    saw_data = True
                    rows += 1
                    total += row_energy
                cels.append({"time_token": time_token, "rows": rows, "energy_sum_token": str(total)})
    if pending_cep is not None:
        pending_cep["complete"] = False
        cep.append(pending_cep)
    return {"cep": cep, "eif": eif, "cels": cels}


def sum_field(rows: Iterable[dict[str, str]], field: str) -> Decimal | None:
    vals = [r[field] for r in rows if r.get(field, "") not in ("", "NA")]
    if not vals:
        return None
    return sum((dec(v) for v in vals), Decimal(0))


def point_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (int(row["element_fortran_number"]), int(row["igauss"]), int(row["jfaces"]))


def same_time(token_a: str, token_b: str) -> bool:
    # `.dat` uses a 16-digit scientific write; C is %.17g.
    return abs(dec(token_a) - dec(token_b)) <= numeric_tolerance(token_a, token_b)


def point_formula(pressure: Decimal, area: Decimal, clear: Decimal) -> Decimal:
    # Reconstruct the point value using the printer operation order:
    # normalforce = pressure * area, then energy = -0.5*normalforce*clear.
    # This is mathematically equivalent for the pinned linear branch, but is
    # not a bitwise replay of springforc_f2f's internal elas calculation.
    value = -0.5 * (float(pressure) * float(area)) * float(clear)
    return Decimal(str(value))


def point_formula_exact_decimal_tokens(pressure: Decimal, area: Decimal, clear: Decimal) -> Decimal:
    """Exact product of printed decimal tokens, without binary64 rounding."""
    with localcontext() as context:
        context.prec = 80
        return Decimal("-0.5") * pressure * area * clear


def summarize_first(csv_path: Path, dat_path: Path, sta_path: Path, log_path: Path | None = None) -> dict[str, Any]:
    accepted, rejected = read_sta(sta_path)
    blocks, incomplete = parse_csv_blocks(csv_path)
    candidates = accepted_blocks(blocks, accepted)
    if not candidates:
        raise ValueError("no complete C map block matched an accepted .sta step/increment/time")
    block, sta_row = candidates[0]
    selected_state = block["state"]
    key_step_inc = block["state_key"]
    ttoken = selected_state["time_s"]
    dttoken = selected_state["dtime_s"]
    dat = parse_dat(dat_path)
    fortran_all = [r for r in dat["cep"] if r.get("complete") and same_time(r["time_token"], ttoken)]
    eif = [r for r in dat["eif"] if "energy_token" in r and same_time(r["time_token"], ttoken)]
    cels_matches = [r for r in dat["cels"] if same_time(r["time_token"], ttoken)]
    if len(cels_matches) > 1:
        raise ValueError(f"multiple CELS sections match selected time {ttoken}")
    cels = cels_matches[0] if cels_matches else None

    crows = block["points"]
    c_by_key: dict[tuple[int, int, int], dict[str, str]] = {}
    for row in crows:
        key = point_key(row)
        if key in c_by_key:
            raise ValueError(f"duplicate C point key {key}")
        c_by_key[key] = row
    f_by_key: dict[tuple[int, int, int], dict[str, Any]] = {}
    duplicate_f = []
    for row in fortran_all:
        key = point_key(row)
        if key in f_by_key:
            duplicate_f.append(key)
        f_by_key[key] = row

    matches = []
    matched_by_pair: dict[str, dict[str, Any]] = {}
    max_writer_formula_abs = 0.0
    max_writer_exact_token_formula_abs = 0.0
    max_writer_printer_abs = 0.0
    writer_printer_differences: list[float] = []
    max_printer_formula_abs = 0.0
    max_printer_exact_token_formula_abs = 0.0
    max_native_clear_difference_abs = 0.0
    max_clearproj_difference_abs = 0.0
    max_pressure_difference_abs = 0.0
    max_area_difference_abs = 0.0
    for key, crow in c_by_key.items():
        frow = f_by_key.get(key)
        if frow is None:
            continue
        pair_id = f"{frow['tie']}:{frow['slave']}:{frow['master']}"
        writer_energy = None if crow["writer_elastic_Nmm"] == "NA" else float(dec(crow["writer_elastic_Nmm"]))
        compact_energy = None if crow["compact_elastic_Nmm"] == "NA" else float(dec(crow["compact_elastic_Nmm"]))
        native_formula = float(point_formula(dec(crow["pressure_N_per_mm2"]), dec(crow["spring_area_mm2"]), dec(crow["native_clear_mm"])))
        native_formula_exact_tokens = point_formula_exact_decimal_tokens(dec(crow["pressure_N_per_mm2"]), dec(crow["spring_area_mm2"]), dec(crow["native_clear_mm"]))
        printer_formula = float(point_formula(dec(frow["pressure_token"]), dec(frow["area_token"]), dec(frow["clearproj_token"])))
        printer_formula_exact_tokens = point_formula_exact_decimal_tokens(dec(frow["pressure_token"]), dec(frow["area_token"]), dec(frow["clearproj_token"]))
        printer_energy = float(dec(frow["printer_energy_token"]))
        native_clear_delta = float(dec(crow["native_clear_mm"]) - dec(frow["native_clear_token"]))
        clearproj_delta = float(dec(frow["clearproj_token"]) - dec(crow["native_clear_mm"]))
        pressure_delta = float(dec(crow["pressure_N_per_mm2"]) - dec(frow["pressure_token"]))
        area_delta = float(dec(crow["spring_area_mm2"]) - dec(frow["area_token"]))
        if writer_energy is not None:
            max_writer_formula_abs = max(max_writer_formula_abs, abs(writer_energy - native_formula))
            max_writer_exact_token_formula_abs = max(max_writer_exact_token_formula_abs, abs(float(dec(crow["writer_elastic_Nmm"]) - native_formula_exact_tokens)))
            writer_printer_differences.append(writer_energy - printer_energy)
            max_writer_printer_abs = max(max_writer_printer_abs, abs(writer_energy - printer_energy))
        max_printer_formula_abs = max(max_printer_formula_abs, abs(printer_energy - printer_formula))
        max_printer_exact_token_formula_abs = max(max_printer_exact_token_formula_abs, abs(float(dec(frow["printer_energy_token"]) - printer_formula_exact_tokens)))
        max_native_clear_difference_abs = max(max_native_clear_difference_abs, abs(native_clear_delta))
        max_clearproj_difference_abs = max(max_clearproj_difference_abs, abs(clearproj_delta))
        max_pressure_difference_abs = max(max_pressure_difference_abs, abs(pressure_delta))
        max_area_difference_abs = max(max_area_difference_abs, abs(area_delta))
        pair_rec = matched_by_pair.setdefault(pair_id, {
            "pair": pair_id, "tie": frow["tie"], "slave": frow["slave"], "master": frow["master"],
            "matched_point_count": 0, "writer_energy_sum_Nmm": Decimal(0),
            "compact_energy_sum_Nmm": Decimal(0), "native_formula_sum_Nmm": Decimal(0),
            "printer_energy_sum_Nmm": Decimal(0), "writer_compact_address_mismatch_count": 0,
        })
        pair_rec["matched_point_count"] += 1
        pair_rec["native_formula_sum_Nmm"] += Decimal(str(native_formula))
        pair_rec["printer_energy_sum_Nmm"] += dec(frow["printer_energy_token"])
        if writer_energy is not None and compact_energy is not None:
            pair_rec["writer_energy_sum_Nmm"] += dec(crow["writer_elastic_Nmm"])
            pair_rec["compact_energy_sum_Nmm"] += dec(crow["compact_elastic_Nmm"])
        if crow["writer_energy_index_fortran"] != crow["compact_energy_index_fortran"]:
            pair_rec["writer_compact_address_mismatch_count"] += 1
        joined = {
            "key": list(key), "tie": frow["tie"], "slave": frow["slave"], "master": frow["master"],
            "writer_energy_index_fortran": int(crow["writer_energy_index_fortran"]) if crow["writer_energy_index_fortran"] != "NA" else None,
            "compact_energy_index_fortran": int(crow["compact_energy_index_fortran"]) if crow["compact_energy_index_fortran"] != "NA" else None,
            "spring_area_mm2": float(dec(crow["spring_area_mm2"])),
            "native_clear_mm": float(dec(crow["native_clear_mm"])),
            "pressure_N_per_mm2": float(dec(crow["pressure_N_per_mm2"])),
            "native_clear_C_minus_DAT_mm": native_clear_delta,
            "pressure_C_minus_DAT_N_per_mm2": pressure_delta,
            "area_C_minus_DAT_mm2": area_delta,
            "writer_energy_Nmm": writer_energy,
            "compact_energy_Nmm": compact_energy,
            "native_clear_formula_Nmm": native_formula,
            "native_clear_exact_decimal_token_formula_Nmm": float(native_formula_exact_tokens),
            "printer_energy_Nmm": printer_energy,
            "printer_clear_formula_Nmm": printer_formula,
            "printer_clear_exact_decimal_token_formula_Nmm": float(printer_formula_exact_tokens),
            "clearproj_mm": float(dec(frow["clearproj_token"])),
            "clearproj_minus_native_clear_mm": clearproj_delta,
        }
        matches.append(joined)

    writer_elastic = sum_field(crows, "writer_elastic_Nmm")
    writer_viscous = sum_field(crows, "writer_viscous_Nmm")
    compact_elastic = sum_field(crows, "compact_elastic_Nmm")
    compact_viscous = sum_field(crows, "compact_viscous_Nmm")
    native_formula_sum = sum((point_formula(dec(r["pressure_N_per_mm2"]), dec(r["spring_area_mm2"]), dec(r["native_clear_mm"])) for r in crows), Decimal(0))
    with localcontext() as context:
        context.prec = 80
        native_exact_formula_sum = sum((point_formula_exact_decimal_tokens(dec(r["pressure_N_per_mm2"]), dec(r["spring_area_mm2"]), dec(r["native_clear_mm"])) for r in crows), Decimal(0))
        printer_exact_formula_sum = sum((point_formula_exact_decimal_tokens(dec(r["pressure_token"]), dec(r["area_token"]), dec(r["clearproj_token"])) for r in fortran_all), Decimal(0))
    printer_energy_sum = sum((dec(r["printer_energy_token"]) for r in fortran_all), Decimal(0))
    printer_formula_sum = sum((point_formula(dec(r["pressure_token"]), dec(r["area_token"]), dec(r["clearproj_token"])) for r in fortran_all), Decimal(0))
    eif_sum = sum((dec(r["energy_token"]) for r in eif), Decimal(0))

    f_by_pair: dict[str, dict[str, Any]] = {}
    for row in fortran_all:
        pair_id = f"{row['tie']}:{row['slave']}:{row['master']}"
        rec = f_by_pair.setdefault(pair_id, {"tie": row["tie"], "slave": row["slave"], "master": row["master"], "point_count": 0, "printer_energy_sum_Nmm": Decimal(0), "clearproj_formula_sum_Nmm": Decimal(0)})
        rec["point_count"] += 1
        rec["printer_energy_sum_Nmm"] += dec(row["printer_energy_token"])
        rec["clearproj_formula_sum_Nmm"] += point_formula(dec(row["pressure_token"]), dec(row["area_token"]), dec(row["clearproj_token"]))
    eif_by_pair = {f"{r['tie']}:{r['slave']}:{r['master']}": dec(r["energy_token"]) for r in eif}
    pair_rows = []
    all_pair_ids = sorted(set(f_by_pair) | set(eif_by_pair))
    for pair_id in all_pair_ids:
        rec = f_by_pair.get(pair_id, {
            "tie": int(pair_id.split(":", 1)[0]),
            "slave": pair_id.split(":", 2)[1],
            "master": pair_id.split(":", 2)[2],
            "point_count": 0,
            "printer_energy_sum_Nmm": Decimal(0),
            "clearproj_formula_sum_Nmm": Decimal(0),
        })
        eif_val = eif_by_pair.get(pair_id)
        pair_rows.append({
            "pair": pair_id,
            "point_count": rec["point_count"],
            "WJ_CEP_records_present": pair_id in f_by_pair,
            "printer_energy_sum_Nmm": float(rec["printer_energy_sum_Nmm"]),
            "clearproj_formula_sum_Nmm": float(rec["clearproj_formula_sum_Nmm"]),
            "WJ_E_IF_Nmm": None if eif_val is None else float(eif_val),
            "printer_minus_WJ_E_IF_Nmm": None if eif_val is None else float(rec["printer_energy_sum_Nmm"] - eif_val),
        })

    input_pins = {"csv": {"path": str(csv_path), "sha256": sha256(csv_path)}, "dat": {"path": str(dat_path), "sha256": sha256(dat_path)}, "sta": {"path": str(sta_path), "sha256": sha256(sta_path)}}
    if log_path:
        input_pins["log"] = {"path": str(log_path), "sha256": sha256(log_path)}
    result: dict[str, Any] = {
        "schema": "wj-contact-energy-point-map-analysis/v1",
        "status": "first-complete-accepted-block-parsed",
        "scope": "Output audit only; no mechanics acceptance or physical joint capacity inference.",
        "inputs": input_pins,
        "sta": {"accepted_step_increments": len(accepted), "rejected_attempt_rows": rejected},
        "csv": {
            "complete_blocks": len(blocks), "incomplete_blocks": incomplete,
            "selected_step": key_step_inc[0], "selected_increment": key_step_inc[1],
            "selected_time_s": float(dec(ttoken)), "selected_dtime_s": float(dec(dttoken)),
            "accepted_STA_row": sta_row, "declared_state_count": block["declared_state_count"],
            "declared_end_count": block["declared_end_count"], "independently_counted_point_rows": len(crows),
            "expected_count_marker_note": "END repeats the producer's expected point count; parser independently counts POINT rows. A complete block requires STATE == END == actual POINT count.",
            "point_count": len(crows), "nener_values": sorted({int(r["nener"]) for r in crows}),
            "writer_energy_sum_Nmm": None if writer_elastic is None else float(writer_elastic),
            "writer_viscous_energy_sum_Nmm": None if writer_viscous is None else float(writer_viscous),
            "compact_reader_energy_sum_Nmm": None if compact_elastic is None else float(compact_elastic),
            "compact_reader_viscous_energy_sum_Nmm": None if compact_viscous is None else float(compact_viscous),
            "native_clear_linear_formula_sum_Nmm": float(native_formula_sum),
            "native_clear_exact_decimal_token_formula_sum_Nmm": float(native_exact_formula_sum),
            "max_abs_point_writer_minus_native_clear_formula_Nmm": max_writer_formula_abs,
            "max_abs_point_writer_minus_exact_decimal_token_formula_Nmm": max_writer_exact_token_formula_abs,
            "max_abs_point_writer_minus_printer_energy_Nmm": max_writer_printer_abs,
            "writer_minus_printer_point_energy_sum_Nmm": math.fsum(writer_printer_differences),
            "writer_minus_native_clear_formula_Nmm": None if writer_elastic is None else float(writer_elastic - native_formula_sum),
            "compact_minus_writer_energy_Nmm": None if compact_elastic is None or writer_elastic is None else float(compact_elastic - writer_elastic),
            "writer_vs_compact_address_mismatch_count": sum(1 for r in crows if r["writer_energy_index_fortran"] != r["compact_energy_index_fortran"]),
            "writer_vs_compact_energy_value_mismatch_count": sum(1 for r in crows if r["writer_elastic_Nmm"] != r["compact_elastic_Nmm"]),
        },
        "dat": {
            "complete_WJ_CEP_point_value_records_at_selected_time": len(fortran_all),
            "incomplete_WJ_CEP_records_total": sum(1 for r in dat["cep"] if not r.get("complete")),
            "duplicate_point_keys": [list(k) for k in duplicate_f],
            "WJ_E_IF_pair_records_at_selected_time": len(eif),
            "WJ_CEP_printer_energy_sum_Nmm": float(printer_energy_sum),
            "WJ_CEP_clearproj_formula_sum_Nmm": float(printer_formula_sum),
            "WJ_CEP_clearproj_exact_decimal_token_formula_sum_Nmm": float(printer_exact_formula_sum),
            "max_abs_point_printer_minus_clearproj_formula_Nmm": max_printer_formula_abs,
            "max_abs_point_printer_minus_exact_decimal_token_formula_Nmm": max_printer_exact_token_formula_abs,
            "WJ_E_IF_pair_sum_Nmm": float(eif_sum),
            "max_abs_C_vs_DAT_native_clear_difference_mm": max_native_clear_difference_abs,
            "max_abs_printer_clearproj_minus_native_clear_mm": max_clearproj_difference_abs,
            "max_abs_C_vs_DAT_pressure_difference_N_per_mm2": max_pressure_difference_abs,
            "max_abs_C_vs_DAT_area_difference_mm2": max_area_difference_abs,
            "CELS_section": None if cels is None else {"time_s": float(dec(cels["time_token"])), "row_count": cels["rows"], "displayed_energy_sum_Nmm": float(dec(cels["energy_sum_token"]))},
            "pair_summaries": pair_rows,
            "joined_pair_summaries": [
                {
                    "pair": r["pair"], "matched_point_count": r["matched_point_count"],
                    "writer_energy_sum_Nmm": float(r["writer_energy_sum_Nmm"]),
                    "compact_energy_sum_Nmm": float(r["compact_energy_sum_Nmm"]),
                    "compact_minus_writer_Nmm": float(r["compact_energy_sum_Nmm"] - r["writer_energy_sum_Nmm"]),
                    "native_formula_sum_Nmm": float(r["native_formula_sum_Nmm"]),
                    "writer_compact_address_mismatch_count": r["writer_compact_address_mismatch_count"],
                }
                for r in sorted(matched_by_pair.values(), key=lambda x: x["tie"])
            ],
        },
        "join": {
            "join_key": ["Fortran element number", "igauss", "jfaces", "selected time"],
            "matched_point_rows": len(matches), "C_point_rows_without_DAT_match": [list(k) for k in sorted(set(c_by_key) - set(f_by_key))],
            "DAT_point_rows_without_C_match": [list(k) for k in sorted(set(f_by_key) - set(c_by_key))],
            "point_rows": matches,
        },
        "interpretation_limits": [
            "The current frictionless linear spring source path supports per-point -0.5 * pressure * area * clearance; native clearance and printer clearproj are reported separately.",
            "The binary64 reconstruction evaluates normalforce = pressure * area, then -0.5 * normalforce * clearance, matching the printer path. Native springforc_f2f computes senergy = -elas * clear / 2 and cstr(4) = elas / springarea; the reconstruction is mathematically equivalent for this linear branch, not a bitwise replay of native intermediate operations.",
            "Writer energy uses ne0+igauss while compact CELS/LOG readers use nelem; compare the recorded slots, do not assume they coincide.",
            "The `compact_*` values are the raw nelem-index values from this exact uncorrected instrumented executable (SHA-256 af0da93038dda93e7d9807f392a5fe6c4fd5f2b9d0b47d0de5d107936795d174). They are not a generic label for a future corrected reader.",
            "CELS and the standard LOG elastic contact-energy total share the compact-reader lineage and are not independent pointwise checks.",
            "The longer 0.025 s horizon can change clearini*reltime at increment 1 relative to a preserved shorter paired arm, even if dt and loads match. Interpret this run using its own native clear, pressure, energy, and matched point identifiers; do not import old per-point energies as expected values.",
            "This audit reports output arithmetic and identity only. It does not infer force-path acceptance, seating, capacity, reaction, or mechanical convergence from a single state.",
        ],
    }
    if log_path:
        lines = log_path.read_text(encoding="ascii", errors="replace").splitlines()
        terms = []
        for line in lines:
            m = re.search(r"elastic contact energy\s*=\s*([^\s]+)", line, re.I)
            if m:
                terms.append(m.group(1))
        result["dat"]["LOG_elastic_contact_energy_records"] = terms
        if cels is not None and terms:
            result["dat"]["CELS_minus_LOG_displayed_energy_Nmm"] = float(dec(cels["energy_sum_token"]) - dec(terms[0]))
    if cels is not None and compact_elastic is not None:
        result["dat"]["CELS_minus_C_compact_sum_Nmm"] = float(dec(cels["energy_sum_token"]) - compact_elastic)
        result["dat"]["CELS_row_count_equals_C_point_count"] = cels["rows"] == len(crows)
    if compact_elastic is not None:
        result["csv"]["WJ_E_IF_minus_compact_reader_energy_Nmm"] = float(eif_sum - compact_elastic)
        result["csv"]["WJ_E_IF_minus_writer_energy_Nmm"] = None if writer_elastic is None else float(eif_sum - writer_elastic)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--dat", type=Path, required=True)
    parser.add_argument("--sta", type=Path, required=True)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--execution", type=Path)
    parser.add_argument("--binary-source-index", type=Path)
    parser.add_argument("--points-output", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize_first(args.csv, args.dat, args.sta, args.log)
    if args.binary_source_index:
        result["inputs"]["binary_source_index"] = {"path": str(args.binary_source_index), "sha256": sha256(args.binary_source_index)}
        source_index = json.loads(args.binary_source_index.read_text(encoding="utf-8"))
        result["binary"] = {
            "instrumented_executable_sha256": source_index["instrumented_executable_sha256"],
            "solver_image_sha256": source_index["solver_image_sha256"],
            "diagnostic_outputs": source_index.get("diagnostic_outputs", []),
            "mechanical_acceptance": source_index.get("mechanical_acceptance"),
        }
    if args.execution:
        execution = json.loads(args.execution.read_text(encoding="utf-8"))
        result["inputs"]["execution"] = {"path": str(args.execution), "sha256": sha256(args.execution)}
        result["execution"] = {
            "status": execution.get("status"), "returncode": execution.get("returncode"),
            "accepted_horizon_endpoint_verified": execution.get("accepted_horizon_endpoint_verified"),
            "binary_sha256": execution.get("binary", {}).get("sha256"),
            "binary_source_index_sha256": execution.get("binary_source_index_sha256"),
        }
        output_hashes = execution.get("output_sha256", {})
        for filename, input_path in (("pilot.wj-contact-energy-map.csv", args.csv), ("pilot.dat", args.dat), ("pilot.sta", args.sta)):
            declared = output_hashes.get(filename)
            actual = sha256(input_path)
            if declared and declared != actual:
                raise ValueError(f"execution.json output pin mismatch for {filename}")
        if args.binary_source_index and execution.get("binary_source_index_sha256") != sha256(args.binary_source_index):
            raise ValueError("execution.json binary source index pin mismatch")
        if args.binary_source_index and execution.get("binary", {}).get("sha256") != result["binary"]["instrumented_executable_sha256"]:
            raise ValueError("execution.json executable pin differs from source index")
    points_path = args.points_output or args.output.with_name("matched-points.csv")
    if result["join"]["point_rows"]:
        points_path.parent.mkdir(parents=True, exist_ok=True)
        fields = list(result["join"]["point_rows"][0])
        with points_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in result["join"]["point_rows"]:
                item = dict(row)
                item["key"] = "/".join(map(str, item["key"]))
                writer.writerow(item)
        result["join"]["matched_points_artifact"] = {"path": str(points_path), "sha256": sha256(points_path), "rows": len(result["join"]["point_rows"])}
    result["join"].pop("point_rows", None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "selected": {"step": result["csv"]["selected_step"], "increment": result["csv"]["selected_increment"], "time_s": result["csv"]["selected_time_s"]}, "c_points": result["csv"]["point_count"], "dat_points": result["dat"]["complete_WJ_CEP_point_value_records_at_selected_time"], "matched": result["join"]["matched_point_rows"], "output": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
