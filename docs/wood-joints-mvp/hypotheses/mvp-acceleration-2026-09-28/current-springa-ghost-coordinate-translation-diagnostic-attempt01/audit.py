#!/usr/bin/env python3
"""Read-only binary64 check of one emitted SPRINGA carrier and a common shift."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tarfile
from decimal import Decimal, localcontext
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[5]
CASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03"
SOURCE_ARCHIVE = Path("/tmp/ccx_2.23.src.tar.bz2")
EXPECTED_INPUT_HASHES = {
    "model.inp": "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    "model.json": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "model.dat": "1f98a6737908286b86771ec4184e8ab08a4b3c1ce95b48a2d42e8284353ffd54",
    "response.json": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
}
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
SOURCE_FILE_HASHES = {
    "./CalculiX/ccx_2.23/src/springforc_n2f.f": "706d066ef4b951c6382b754094bc576d98865b86f6272da535b588c7e7282d60",
    "./CalculiX/ccx_2.23/src/calcspringforc.f": "67d945c054f9e0584432a0f4aef5bd6d3373688530ceaafe4c96796c72b975aa",
    "./CalculiX/ccx_2.23/src/materialdata_sp.f": "b1089a3d57be2e5477cc9351866513333453bcb050617a408a7b3ff491c083a5",
}
EXPECTED_ANSWER = Path(__file__).with_name("known-answer.json")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pinned_sources() -> dict[str, str]:
    data = SOURCE_ARCHIVE.read_bytes()
    assert sha256(data) == SOURCE_ARCHIVE_SHA256, "pinned CCX source archive hash differs"
    out: dict[str, str] = {}
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for name, expected in SOURCE_FILE_HASHES.items():
            member = archive.getmember(name)
            raw = archive.extractfile(member).read()
            assert sha256(raw) == expected, f"pinned source member hash differs: {name}"
            out[name] = raw.decode("latin1")

    spring = out["./CalculiX/ccx_2.23/src/springforc_n2f.f"]
    assert "pl(j,i)=xl(j,i)+vl(j,i)" in spring
    assert "dd0=dsqrt((xl(1,2)-xl(1,1))**2" in spring
    assert "dd=dsqrt((pl(1,2)-pl(1,1))**2" in spring
    assert "val=dd-dd0" in spring
    material = out["./CalculiX/ccx_2.23/src/calcspringforc.f"]
    assert "fk=yiso(id)+xk*(val-xiso(id))" in material
    material_data = out["./CalculiX/ccx_2.23/src/materialdata_sp.f"]
    assert "plconloc(2*k-1), k=1...200: displacement" in material_data
    assert "plconloc(2*k),k=1...200:    force" in material_data
    return out


def pinned_input_bytes() -> dict[str, bytes]:
    out = {name: (CASE / name).read_bytes() for name in EXPECTED_INPUT_HASHES}
    for name, data in out.items():
        assert sha256(data) == EXPECTED_INPUT_HASHES[name], f"pinned case input hash differs: {name}"
    return out


def parse_deck(deck: str) -> tuple[dict[int, tuple[float, float, float]], list[int], list[tuple[float, float]]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    element_nodes: list[int] | None = None
    table: list[tuple[float, float]] = []
    section: str | None = None
    for raw in deck.splitlines():
        line = raw.strip()
        if line.startswith("*"):
            upper = line.upper()
            if upper.startswith("*NODE"):
                section = "node"
            elif upper.startswith("*ELEMENT,TYPE=SPRINGA,ELSET=SPR1787"):
                section = "element"
            elif upper.startswith("*SPRING,ELSET=SPR1787,NONLINEAR"):
                section = "spring"
            else:
                section = None
            continue
        if not line:
            continue
        fields = [field.strip() for field in line.split(",")]
        if section == "node" and len(fields) >= 4:
            try:
                label = int(fields[0])
                if label in (21300, 21301):
                    nodes[label] = tuple(float(value) for value in fields[1:4])
            except ValueError:
                pass
        elif section == "element" and len(fields) >= 3:
            if int(fields[0]) == 3690:
                element_nodes = [int(fields[1]), int(fields[2])]
        elif section == "spring" and len(fields) >= 2:
            try:
                table.append((float(fields[0]), float(fields[1])))
            except ValueError:
                pass
    assert set(nodes) == {21300, 21301}, "carrier endpoint coordinates missing"
    assert element_nodes == [21300, 21301], f"unexpected SPRINGA endpoints: {element_nodes}"
    assert table == [(0.0, -10.0), (0.0, 0.0), (39758.157914988, 10.0)]
    return nodes, element_nodes, table


def parse_final_displacements(dat: str) -> dict[int, tuple[float, float, float]]:
    lines = dat.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "displacements (vx,vy,vz) for set ALLN" in line and "0.1000000E+01" in line:
            start = i + 1
    assert start is not None, "final printed displacement table missing"
    got: dict[int, tuple[float, float, float]] = {}
    for line in lines[start:]:
        if "forces (fx,fy,fz)" in line or "INCREMENT" in line:
            break
        fields = line.split()
        if len(fields) != 4:
            continue
        try:
            label = int(fields[0])
            if label in (21300, 21301):
                got[label] = tuple(float(value) for value in fields[1:4])
        except ValueError:
            pass
    assert set(got) == {21300, 21301}, "final carrier displacement rows missing"
    return got


def parse_final_displacement_tokens(dat: str) -> dict[int, tuple[str, str, str]]:
    lines = dat.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "displacements (vx,vy,vz) for set ALLN" in line and "0.1000000E+01" in line:
            start = i + 1
    assert start is not None
    got: dict[int, tuple[str, str, str]] = {}
    for line in lines[start:]:
        if "forces (fx,fy,fz)" in line or "INCREMENT" in line:
            break
        fields = line.split()
        if len(fields) == 4:
            try:
                label = int(fields[0])
            except ValueError:
                continue
            if label in (21300, 21301):
                got[label] = tuple(fields[1:4])
    return got


def length(v: tuple[float, float, float] | list[float]) -> float:
    # Match the three squared-coordinate terms and square root in the pinned
    # Fortran routine rather than using a scaled hypot implementation.
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def spring_component(response: dict) -> dict:
    for row in response["increments"][-1]["springa_components"]:
        if row.get("element") == 3690:
            return row
    raise AssertionError("element 3690 final response record missing")


def exact_decimal_result(x1s, x2s, u1s, u2s, k: Decimal) -> dict[str, str]:
    with localcontext() as ctx:
        ctx.prec = 80
        x1 = [Decimal(x) for x in x1s]
        x2 = [Decimal(x) for x in x2s]
        u1 = [Decimal(x) for x in u1s]
        u2 = [Decimal(x) for x in u2s]
        initial = [x2[i] - x1[i] for i in range(3)]
        current = [initial[i] + u2[i] - u1[i] for i in range(3)]
        d0 = sum(value * value for value in initial).sqrt()
        d1 = sum(value * value for value in current).sqrt()
        delta = d1 - d0
        return {
            "initial_length_mm": str(d0),
            "current_length_mm": str(d1),
            "elongation_mm": str(delta),
            "table_force_N": str(k * delta),
        }


def assess() -> dict:
    source_text = read_pinned_sources()
    raw = pinned_input_bytes()
    deck = raw["model.inp"].decode()
    case = json.loads(raw["model.json"])
    dat = raw["model.dat"].decode()
    response = json.loads(raw["response.json"])

    nodes, endpoint_nodes, table = parse_deck(deck)
    u = parse_final_displacements(dat)
    u_tokens = parse_final_displacement_tokens(dat)
    row = spring_component(response)
    connection = next(
        item for item in case["source_carrier_inventory_rows"] if item["element"] == 3690
    )
    assert connection["group"] == "SPR1787" and connection["intended_law"] == "tension_only"

    x1, x2 = nodes[endpoint_nodes[0]], nodes[endpoint_nodes[1]]
    u1, u2 = u[endpoint_nodes[0]], u[endpoint_nodes[1]]
    d0 = tuple(x2[i] - x1[i] for i in range(3))
    dd0 = length(d0)
    p1 = tuple(x1[i] + u1[i] for i in range(3))
    p2 = tuple(x2[i] + u2[i] for i in range(3))
    direct_elongation = length(tuple(p2[i] - p1[i] for i in range(3))) - dd0

    # Auxiliary common translation: preserve the parsed binary64 initial
    # relative vector exactly, leave displacement values and all MPC data alone.
    xt1 = (0.0, 0.0, 0.0)
    xt2 = d0
    tp1 = tuple(xt1[i] + u1[i] for i in range(3))
    tp2 = tuple(xt2[i] + u2[i] for i in range(3))
    translated_initial = length(tuple(xt2[i] - xt1[i] for i in range(3)))
    translated_elongation = length(tuple(tp2[i] - tp1[i] for i in range(3))) - translated_initial

    # The deck writes nonlinear spring pairs as force, displacement. The
    # pinned internal table path stores/interpolates displacement, force.
    q0, f0 = table[1][1], table[1][0]
    q1, f1 = table[2][1], table[2][0]
    stiffness = (f1 - f0) / (q1 - q0)
    assert math.isclose(stiffness, connection["stiffness_n_per_mm"], rel_tol=1e-15)
    direct_force = stiffness * max(direct_elongation, 0.0)
    translated_force = stiffness * max(translated_elongation, 0.0)

    x1_tokens = ["-134.5", "643.62182968176", "1192.0483260447"]
    x2_tokens = ["-134.5", "579.34306873736", "1115.4438817125"]
    k_decimal = Decimal("3975.8157914988024")
    exact = exact_decimal_result(
        x1_tokens,
        x2_tokens,
        u_tokens[21300],
        u_tokens[21301],
        k_decimal,
    )
    exact_float = float(exact["elongation_mm"])
    rf = float(row["native_endpoint_internal_force_N"])
    rf_radius = float(row["native_endpoint_internal_radius_N"])
    nominal_span_deficit = 100.0 - dd0

    # 17 significant digits round-trip the translated binary64 span; 14 do not
    # necessarily preserve its binary value, so the proposal keeps this gate.
    translation_serialization = [format(v, ".17g") for v in xt2]
    roundtrip = tuple(float(v) for v in translation_serialization)
    assert roundtrip == xt2

    expected_force = float(row["native_table_force_N_from_actual_dd_minus_dd0"])
    return {
        "scope": "read-only source-bound arithmetic diagnostic; no native run",
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_member_sha256": {Path(k).name: sha256(v.encode("latin1")) for k, v in source_text.items()},
        "case_input_sha256": {name: sha256(data) for name, data in raw.items()},
        "row": {
            "response_element": 3690,
            "source_group": connection["group"],
            "source_model_inventory_index": 1786,
            "intended_law": connection["intended_law"],
            "parent_reduced_force_vector_position": 1586,
        },
        "deck": {
            "nodes": {str(k): list(v) for k, v in nodes.items()},
            "endpoint_nodes": endpoint_nodes,
            "initial_relative_vector_mm": list(d0),
            "initial_length_mm": dd0,
            "nominal_100mm_minus_emitted_length_mm": nominal_span_deficit,
            "force_displacement_table_rows": [list(pair) for pair in table],
            "positive_branch_tangent_N_per_mm": stiffness,
        },
        "final_printed_displacements_mm": {str(k): list(v) for k, v in u.items()},
        "source_arithmetic": {
            "direct_emitted_coordinates_elongation_mm": direct_elongation,
            "direct_emitted_coordinates_table_force_N": direct_force,
            "translated_near_origin_elongation_mm": translated_elongation,
            "translated_near_origin_table_force_N": translated_force,
            "translated_minus_direct_elongation_mm": translated_elongation - direct_elongation,
            "translated_minus_direct_force_N": translated_force - direct_force,
            "high_precision_mathematical_elongation_mm": exact_float,
            "direct_minus_high_precision_mm": direct_elongation - exact_float,
            "translated_minus_high_precision_mm": translated_elongation - exact_float,
            "high_precision_table_force_N": float(exact["table_force_N"]),
            "maximum_absolute_emitted_coordinate_mm": max(abs(v) for xyz in nodes.values() for v in xyz),
        },
        "response_comparison": {
            "reported_q_relative_projection_mm": row["q_relative_projection_mm"],
            "reported_q_from_qghost_mm": row["q_from_qghost_mm"],
            "reported_geometric_elongation_mm": row["geometric_spring_elongation_mm"],
            "reported_table_force_N": expected_force,
            "reported_native_endpoint_RF_N": rf,
            "reported_native_endpoint_RF_radius_N": rf_radius,
            "direct_force_minus_native_RF_N": direct_force - rf,
            "translated_force_minus_native_RF_N": translated_force - rf,
            "direct_force_inside_reported_RF_radius": abs(direct_force - rf) <= rf_radius,
            "translated_force_inside_reported_RF_radius": abs(translated_force - rf) <= rf_radius,
        },
        "auxiliary_translation_only": {
            "common_shift_mm": [-v for v in x1],
            "translated_node_21300_mm": list(xt1),
            "translated_node_21301_mm": list(xt2),
            "translated_node_21301_17digit_roundtrip_tokens": translation_serialization,
            "relative_vector_bitwise_preserved_in_arithmetic": roundtrip == xt2,
            "physical_solids_or_MPC_coefficients_changed": False,
        },
    }


def close(a, b) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-13, abs_tol=1e-18)
    return a == b


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="compare with pinned known answer")
    args = parser.parse_args()
    result = assess()
    if args.verify:
        expected = json.loads(EXPECTED_ANSWER.read_text())
        if not close(result, expected):
            print("FAIL: recomputed arithmetic result differs from known-answer.json", file=sys.stderr)
            return 1
        print("PASS: source pins, emitted row parse, direct/translated arithmetic, and known answer")
    else:
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
