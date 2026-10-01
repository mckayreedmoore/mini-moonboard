#!/usr/bin/env python3
"""Independent extraction and force audit; never executes a native solver."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "ordinary-port-motion-attempt09-common-map"


def cards(path):
    result = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            result.append([line.upper(), []])
        else:
            assert result
            result[-1][1].append(line)
    return result


def kind(card):
    return card[0].split(",")[0]


def rows(cs, key):
    return [row for c in cs if kind(c) == key for row in c[1]]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit():
    spec = importlib.util.spec_from_file_location("independent_mass", HERE / "parent-mass-reference.py")
    mass = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mass)
    ref, ids, md = mass.reference()
    expected = json.loads((HERE / "expected.json").read_text())
    source = cards(SOURCE / "mesh.inp")
    nodes = {int(row.split(",")[0]): [float(v.strip()[:20]) for v in row.split(",")[1:]]
             for row in rows(source, "*NODE")}
    elements = {int(row.split(",")[0]): [int(v) for v in row.split(",")[1:]]
                for row in rows(source, "*ELEMENT")}
    original_eq = [c for c in cards(SOURCE / "nut-coupling.inp") if kind(c) == "*EQUATION"][:6]
    mesh = json.loads((SOURCE / "mesh.json").read_text())
    body = mesh["bodies"]["M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION"]
    carrier = mesh["bodies"]["M03_A00_NUT"]
    result = {}
    previous_forces = None
    for case in expected["case_order"]:
        item = expected["inputs"][case]
        path = HERE / item["path"]
        assert sha(path) == item["sha256"]
        cs = cards(path)
        assert not any(kind(c) in {"*BOUNDARY", "*CONTACT PAIR", "*INITIAL CONDITIONS"} for c in cs)
        actual_nodes = {}
        for row in rows(cs, "*NODE"):
            a = [v.strip() for v in row.split(",")]
            assert int(a[0]) not in actual_nodes
            assert all(len(v) <= 20 for v in a[1:])
            actual_nodes[int(a[0])] = [float(v) for v in a[1:]]
        wanted = set(body["nodes"])
        wanted_elements = set(body["elements"])
        if case == "mapped_carrier":
            wanted.update(carrier["nodes"])
            wanted_elements.update(carrier["elements"])
        for n in wanted:
            assert actual_nodes[n] == nodes[n], (case, n)
        if case != "direct":
            wanted.update((116163, 116164))
            for n in (116163, 116164):
                assert actual_nodes[n] == ref["pivot_from_native_control_coordinate_mm"]
        assert set(actual_nodes) == wanted
        actual_elements = {}
        for row in rows(cs, "*ELEMENT"):
            a = [int(v) for v in row.split(",")]
            assert a[0] not in actual_elements
            actual_elements[a[0]] = a[1:]
        assert set(actual_elements) == wanted_elements
        assert all(actual_elements[e] == elements[e] for e in wanted_elements)
        eq = [c for c in cs if kind(c) == "*EQUATION"]
        assert eq == ([] if case == "direct" else original_eq)
        rigid = [c for c in cs if kind(c) == "*RIGID BODY"]
        assert len(rigid) == int(case == "mapped_carrier")
        forces = {}
        for row in rows(cs, "*CLOAD"):
            a = [v.strip() for v in row.split(",")]
            key = (int(a[0]), int(a[1]))
            assert key not in forces and key[0] in body["nodes"]
            assert len(a[2]) <= 20
            forces[key] = float(a[2])
        assert all(np.isfinite(v) for v in forces.values())
        if previous_forces is not None:
            assert forces == previous_forces
        previous_forces = forces
        load = np.array([[forces.get((n, c+1), 0.) for c in range(3)] for n in ids])
        difference = float(np.max(np.abs(load-md*.012)))
        assert difference < 1e-18
        assert len(forces) == 2*len(ids)
        totals = [c for c in cs if kind(c) == "*EL PRINT"]
        required = {"M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION"}
        if case == "mapped_carrier":
            required.add("M03_A00_NUT")
        assert len(totals) == len(required)
        for name in required:
            found = [c for c in totals if "ELSET="+name+"," in c[0]]
            assert len(found) == 1 and "TOTALS=ONLY" in found[0][0]
            assert {v.strip() for v in ",".join(found[0][1]).split(",")} == {"ELSE", "ELKE", "EMAS", "EVOL"}
        result[case] = {"input_sha256": sha(path), "nodes": len(actual_nodes),
                        "elements": len(actual_elements), "original_equations": len(eq),
                        "rigid_carriers": len(rigid), "CLOAD_rows": len(forces),
                        "maximum_independent_CLOAD_difference_N": difference,
                        "required_total_EL_PRINT_sets": sorted(required)}
    return {"schema": "parent_current_map_input_audit/v1", "status": "PASS_OFFLINE",
            "native_execution": False, "joint_acceptance": False, "cases": result,
            "scope": "Independent source extraction, original equations, parser-visible coordinates, load quadrature comparison and output-card coverage. Readiness and native response remain separate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, indent=2, sort_keys=True)+"\n"
    target = HERE / "parent-input-audit.json"
    if args.write:
        with target.open("x") as stream:
            stream.write(rendered)
    else:
        assert target.read_text() == rendered
    print(json.dumps(result))
