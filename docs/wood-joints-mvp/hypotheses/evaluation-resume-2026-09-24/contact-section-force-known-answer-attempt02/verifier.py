#!/usr/bin/env python3
"""Audit the inherited contact coupon gates, SOF checks, and full nodal stress FRD."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
BASE = EVAL / "contact-mortar-c3d10-fullstep-attempt01"
PREVIOUS = EVAL / "contact-section-force-known-answer-attempt01"
BASE_PINS = {
    "input-freeze.json": "978f8e49e79d6569dc033595ce565ce8587e36c4c5845c5615f120582634e8b0",
    "execution.json": "a485410aada87d2e149b39ee77b78d3efcada065c833a0c7e91acf1a60312574",
    "verifier.py": "d86d98494241657b1f8dda8ea42d747dac851c2319b914458f520008bc3a572b",
    "verifier.json": "813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14",
}
PREVIOUS_PINS = {
    "input-freeze.json": "eeced8a094e46672831a4d2236cb984f6217f47af8cf331bb106df03a5c063ec",
    "execution.json": "1dcf538de97cbd720e952facda23ad63e8989458411b2d3b7d1b3a9a86093703",
    "verifier.py": "f56c23a1e27f623ba6deb94529c08ee62d74ea7e3e3a0f849649e4f23514ca5b",
    "verifier.json": "394e410aea2171b81eacf624c1ea274392c8e70518098ae71c00d45fe3c6bebc",
    "expected.json": "61d1d3485839dee22f6aafbc83fc2f37028a393589a10d7b7de39927718f481a",
}
EL_FILE_BLOCK = "*EL FILE,FREQUENCY=1\nS\n"
SECTION_AND_STRESS_BLOCK = (
    "*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1\nSOF\n"
    "*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1\nSOF\n"
    + EL_FILE_BLOCK
)
STRESS_LABELS = ["SXX", "SYY", "SZZ", "SXY", "SYZ", "SZX"]
CONTACT_LABELS = ["COPEN", "CSLIP1", "CSLIP2", "CPRESS", "CSHEAR1", "CSHEAR2"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pinned_module(path: Path, name: str, pins: dict[str, str]):
    for artifact, digest in pins.items():
        require(sha(path / artifact) == digest, f"Pinned history changed: {artifact}")
    return load_module(name, path / "verifier.py")


def extended_frd_fields(path: Path, states: list[dict], node_ids: set[int], number):
    """Keep the base FRD checks and add exact, finite full-mesh STRESS coverage."""
    blocks = []
    time = None
    identity = None
    kind = None
    labels = []
    active = None
    for line in path.read_text().splitlines():
        fields = line.split()
        if fields and fields[0] == "1PSTEP":
            require(active is None, "Unterminated FRD dataset")
            require(len(fields) >= 4, "Malformed FRD state header")
            identity = (int(fields[3]), int(fields[2]))
        elif fields and fields[0] == "100CL":
            require(len(fields) >= 3, "Malformed FRD time header")
            time = number(fields[2])
        elif line.startswith(" -4"):
            require(active is None, "Unterminated FRD field")
            kind = fields[1]
            require(kind in ("DISP", "FORC", "CONTACT", "STRESS", "ERROR"),
                    f"Unexpected FRD field {kind}")
            active = {}
            labels = []
        elif active is not None and line.startswith(" -5"):
            labels.append(fields[1])
        elif active is not None and line.startswith(" -1"):
            node = int(line[3:13])
            require(node in node_ids and node not in active, "Bad/duplicate FRD node")
            values = [number(line[i:i + 12]) for i in range(13, len(line.rstrip()), 12)]
            expected_width = 6 if kind in ("CONTACT", "STRESS") else 3
            if kind == "ERROR":
                expected_width = 1
            require(len(values) == expected_width, f"Malformed {kind} FRD record")
            active[node] = values
        elif active is not None and line.startswith(" -3"):
            require(time is not None and identity is not None,
                    f"Untimed FRD {kind} block")
            if kind != "ERROR":
                require(active, f"Empty FRD {kind} block")
            matches = [state for state in states
                       if (state["step"], state["increment"]) == identity
                       and abs(state["total"] - time) < 2e-6]
            require(len(matches) == 1, "FRD dataset does not match an accepted state")
            require(not any(block["identity"] == identity and block["kind"] == kind
                            for block in blocks), "Duplicate FRD field/state")
            summary = {"time": time, "identity": identity, "kind": kind,
                       "nodes": len(active)}
            if kind == "CONTACT":
                require(labels == CONTACT_LABELS, "Unexpected contact components")
                summary.update(COPEN_min=min(values[0] for values in active.values()),
                               COPEN_max=max(values[0] for values in active.values()),
                               CPRESS_min=min(values[3] for values in active.values()),
                               CPRESS_max=max(values[3] for values in active.values()))
            elif kind in ("DISP", "FORC", "STRESS"):
                require(set(active) == node_ids, f"Incomplete FRD {kind} nodal coverage")
                required_labels = {
                    "DISP": ["D1", "D2", "D3", "ALL"],
                    "FORC": ["F1", "F2", "F3", "ALL"],
                    "STRESS": STRESS_LABELS,
                }[kind]
                require(labels == required_labels, f"Wrong FRD {kind} components")
                if kind == "STRESS":
                    summary["component_abs_max"] = [
                        max(abs(values[i]) for values in active.values())
                        for i in range(6)
                    ]
                    summary["all_values_finite"] = True
            elif kind == "ERROR":
                require(labels == ["STR(%)"], "Unexpected incidental ERR component")
            blocks.append(summary)
            active = None
    require(active is None, "Truncated FRD block")

    for state in states:
        key = (state["step"], state["increment"])
        kinds = {block["kind"] for block in blocks if block["identity"] == key}
        require(kinds >= {"DISP", "FORC", "STRESS"},
                "Missing accepted-state FRD nodal or stress output")
    require(any(block["kind"] == "CONTACT" and abs(block["time"] - 2) < 1e-6
                for block in blocks), "Missing compression-endpoint contact field evidence")
    stress_blocks = [block for block in blocks if block["kind"] == "STRESS"]
    require(len(stress_blocks) == 3, "Expected one full-mesh STRESS field per accepted state")
    return blocks


def lineage_audit(expected: dict) -> dict:
    base = pinned_module(BASE, "section_stress_base_verifier", BASE_PINS)
    require(base.read_json(BASE / "verifier.json")["status"] == "PASS_METHOD_FIXTURE",
            "Pinned fullstep fixture result is not a pass")
    require(base.audit()["status"] == "PASS_METHOD_FIXTURE",
            "Pinned fullstep fixture evidence no longer passes")

    previous = expected["prior_section_attempt"]
    pins = {
        "input-freeze.json": previous["input_freeze_sha256"],
        "execution.json": previous["execution_sha256"],
        "verifier.py": previous["verifier_source_sha256"],
        "verifier.json": previous["verifier_result_sha256"],
        "expected.json": PREVIOUS_PINS["expected.json"],
    }
    for artifact, digest in pins.items():
        require(sha(PREVIOUS / artifact) == digest, f"Prior failed attempt changed: {artifact}")
    old_inputs = previous["input_sha256"]
    case_hashes = {}
    for case in ("mortar_c3d10", "penalty_c3d10"):
        source = PREVIOUS / "input" / f"{case}.inp"
        current = HERE / "input" / f"{case}.inp"
        require(sha(source) == old_inputs[f"{case}.inp"], f"Prior input changed: {case}")
        expected_input = source.read_text().replace("*END STEP\n", EL_FILE_BLOCK + "*END STEP\n")
        require(current.read_text() == expected_input,
                f"Attempt02 input contains changes beyond EL FILE/S: {case}")
        case_hashes[case] = sha(current)
    require(case_hashes == {case: spec["input_sha256"]
                            for case, spec in expected["cases"].items()},
            "Attempt02 input hashes differ from expected.json")
    return {"status": "PASS_LINEAGE", "attempt01_preserved": True,
            "only_el_file_s_added": True, "input_sha256": case_hashes}


def audit() -> dict:
    expected = json.loads((HERE / "expected.json").read_text())
    lineage = lineage_audit(expected)

    base = pinned_module(BASE, "section_stress_fixture_verifier", BASE_PINS)
    base.HERE = HERE
    base.frd_fields = lambda path, states, node_ids: extended_frd_fields(
        path, states, node_ids, base.number
    )
    fixture = base.audit()

    section = load_module("section_stress_section_verifier", PREVIOUS / "verifier.py")
    section.HERE = HERE
    section.SECTION_CARDS = SECTION_AND_STRESS_BLOCK
    section_base = section.load_base()
    section_audits = {}
    for case in sorted(base.CASES):
        try:
            section_audits[case] = section.audit_sections(case, section_base)
        except Exception as exc:
            section_audits[case] = {"status": "FAIL", "error": str(exc)}

    stress_audits = {}
    fixture_cases = fixture.get("cases", {})
    for case in sorted(base.CASES):
        try:
            diagnostics = fixture_cases[case]["FRD_field_diagnostics"]
            reports = [item for item in diagnostics if item["kind"] == "STRESS"]
            require(len(reports) == 3, "Stress output is missing an accepted state")
            stress_audits[case] = {
                "status": "PASS",
                "states": reports,
                "interpretation": (
                    "Finite full-mesh nodal stress output only; no contact-traction, "
                    "strength, or joint-capacity inference."
                ),
            }
        except Exception as exc:
            stress_audits[case] = {"status": "FAIL", "error": str(exc)}

    passed = (
        fixture.get("status") == "PASS_METHOD_FIXTURE"
        and all(item.get("status") == "PASS" for item in section_audits.values())
        and all(item.get("status") == "PASS" for item in stress_audits.values())
    )
    return {
        "schema": "calculix_mortar_c3d10_section_force_stress_audit/v1",
        "status": "PASS_SECTION_STRESS_FIXTURE" if passed else "FAIL",
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
        "lineage_audit": lineage,
        "unchanged_fixture_audit": fixture,
        "section_force_audits": section_audits,
        "full_mesh_stress_audits": stress_audits,
        "baseline_pins": BASE_PINS,
        "verifier_sha256": sha(Path(__file__)),
        "execution_sha256": sha(HERE / "execution.json"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        result = audit()
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc),
                  "mechanical_acceptance": False, "joint_acceptance": False,
                  "release": False}
    if args.write:
        with (HERE / "verifier.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({
        "status": result["status"],
        "error": result.get("error"),
        "fixture_status": result.get("unchanged_fixture_audit", {}).get("status"),
        "section_force_audits": {
            case: {key: value for key, value in record.items()
                   if key in ("status", "error")}
            for case, record in result.get("section_force_audits", {}).items()
        },
        "full_mesh_stress_audits": {
            case: {key: value for key, value in record.items()
                   if key in ("status", "error")}
            for case, record in result.get("full_mesh_stress_audits", {}).items()
        },
    }))
    raise SystemExit(0 if result["status"] == "PASS_SECTION_STRESS_FIXTURE" else 1)
