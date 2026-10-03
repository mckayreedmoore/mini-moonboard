#!/usr/bin/env python3
"""Parse pinned CalculiX 2.23 CF/CFN/CFS resultants, not area statistics.

Header/quantity/row formats: printoutcontact.f:219-243 in the archive pinned
by prepare.py. Open-area centroids and mean normals may be undefined; the six
force and origin-moment components parsed here must always be finite.
"""
from __future__ import annotations

import json
import math
import re

HEADER = re.compile(
    r"^statistics for slave set ([^,]+), master set (.+) and time (\S+)$"
)
QUANTITIES = {
    "total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)": "CF",
    "total normal surface force (fx,fy,fz) and its moment about the origin (mx,my,mz)": "CFN",
    "total shear surface force (fx,fy,fz) and its moment about the origin (mx,my,mz)": "CFS",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(token):
    # Fortran Ew.d can omit E for three-digit exponents.
    match = re.fullmatch(r"([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})", token)
    if match:
        token = match[1] + "E" + match[2]
    value = float(token.replace("D", "E").replace("d", "E"))
    require(math.isfinite(value), f"Nonfinite pair-resultant evidence: {token}")
    return value


def parse_pairs(text):
    lines = [" ".join(line.split()) for line in text.splitlines()]
    headers = [(index, HEADER.fullmatch(line)) for index, line in enumerate(lines)
               if HEADER.fullmatch(line)]
    records, seen = [], set()
    for start, header in headers:
        # SECTION PRINT emits separate statistics blocks between contact
        # states. It must not be mistaken for another CF record in this pair.
        end = next((index for index in range(start + 1, len(lines))
                    if lines[index].startswith("statistics for ")), len(lines))
        slave, master, time_token = header.groups()
        time = number(time_token)
        labels = [(index, QUANTITIES[lines[index]])
                  for index in range(start + 1, end) if lines[index] in QUANTITIES]
        require(len(labels) == 1, "Pair block lacks one unique CF/CFN/CFS resultant header")
        label_index, quantity = labels[0]
        value_index = label_index + 1
        while value_index < end and not lines[value_index]:
            value_index += 1
        require(value_index < end, "Missing pair-resultant row")
        tokens = lines[value_index].split()
        require(len(tokens) == 6, "Pair force/origin-moment row must have six values")
        values = [number(token) for token in tokens]
        identity = (slave, master, time, quantity)
        require(identity not in seen, f"Duplicate pair-resultant identity: {identity}")
        seen.add(identity)
        records.append({"slave": slave, "master": master, "time": time,
                        "quantity": quantity, "force_N": values[:3],
                        "moment_N_mm": values[3:]})
    return records


def synthetic_preflight():
    def block(quantity, time, force, moment, undefined_area=False):
        label = next(label for label, name in QUANTITIES.items() if name == quantity)
        stats = "NaN NaN NaN NaN NaN NaN" if undefined_area else "1 1 0 0 0 -1"
        return (
            f"\n statistics for slave set SLAVE, master set MASTER and time {time:.7E}\n\n"
            f"   {label}\n\n  " + " ".join(f"{v:.6E}" for v in force + moment)
            + f"\n\n   center of gravity and mean normal\n\n   {stats}\n"
            + "\n   moment about the center of gravity(mx,my,mz)\n\n   NaN NaN NaN\n"
            + "\n   area, normal force (+ = tension) and shear force (size)\n\n   0 NaN NaN\n"
        )

    zero = [0.0, 0.0, 0.0]
    opened = "".join(block(q, 1, zero, zero, True) for q in ("CF", "CFN", "CFS"))
    compressed = "".join(
        block(q, 3, zero if q == "CFS" else [0.0, 0.0, 400.0],
              zero if q == "CFS" else [400.0, -400.0, 0.0])
        for q in ("CF", "CFN", "CFS")
    )
    section = (
        "\n statistics for surface set SLAVE and time 2.0000000E+00\n\n"
        " total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)\n\n"
        " 999 999 999 999 999 999\n"
    )
    records = parse_pairs(opened + section + compressed + section)
    require(len(records) == 6 and all(row["force_N"] == zero for row in records[:3]),
            "Zero-area finite-force synthetic failed")
    require(records[4]["force_N"] == [0.0, 0.0, 400.0]
            and records[4]["moment_N_mm"] == [400.0, -400.0, 0.0],
            "Compression force/moment synthetic failed")
    first = block("CF", 1, zero, zero, True)
    force_row = " ".join(f"{v:.6E}" for v in zero + zero)
    invalid = {
        "duplicate": first + first,
        "missing_vector": first.replace(force_row, ""),
        "missing_component": first.replace(force_row, "0 0 0 0 0"),
        "nonfinite_force": first.replace(force_row, "NaN 0 0 0 0 0"),
        "nonfinite_moment": first.replace(force_row, "0 0 0 0 Inf 0"),
        "nonfinite_time": first.replace("1.0000000E+00", "NaN"),
        "wrong_quantity_header": first.replace("total surface force", "unknown surface force"),
    }
    rejected = {}
    for name, text in invalid.items():
        try:
            parse_pairs(text)
        except ValueError:
            rejected[name] = True
        else:
            rejected[name] = False
    require(all(rejected.values()), "Invalid pair-resultant evidence was accepted")
    require(number("1.000000-100") == 1e-100, "Fortran exponent parser failed")
    return {"status": "PASS_SYNTHETIC_PAIR_RESULTANT_PARSER", "records": len(records),
            "undefined_zero_area_statistics_ignored": True, "rejected": rejected,
            "native_output_qualified": False}


if __name__ == "__main__":
    print(json.dumps(synthetic_preflight(), sort_keys=True))
