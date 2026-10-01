"""Historical prescribed-port transient producer, disabled by native coupon failure.

The original source bundle and its audit remain byte-identical. Only the new
deck's procedure, amplitude, prescribed magnitudes and output requests differ.
This module does not run a solver or classify any response as accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.wood_joint_current_port_motion_audit import audit as audit_source
from fea.wood_joint_patch_contact_contract import parse_c3d10_deck

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SOURCE = BASE / "ordinary-port-motion-attempt09-common-map"
SOURCE_LOCK = "port-motion-n_plus-lock.json"
SOURCE_LOCK_SHA = "fcc72f0d627bfe233b7893c134a4a93c9c6a5038a366680de119a84ee497a6cb"
PRESCRIBED_MPC_TRANSIENT_VALIDATED = False


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cards(text: str) -> list[tuple[str, list[str]]]:
    """Read keyword/data blocks, ignoring comments without changing data."""
    result: list[tuple[str, list[str]]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            result.append((line, []))
        elif result:
            result[-1][1].append(line)
        else:
            raise ValueError("orphan solver data line")
    return result


def rows(ids: list[int]) -> list[str]:
    return [",".join(map(str, ids[i:i + 16])) for i in range(0, len(ids), 16)]


def prepare(destination: Path, *, motion_mm: float, ramp_s: float = 0.2,
            hold_s: float = 0.05, initial_dt_s: float = 0.001,
            maximum_dt_s: float = 0.005, ramp_segments: int = 200) -> dict:
    if not PRESCRIBED_MPC_TRANSIENT_VALIDATED:
        raise RuntimeError(
            "Pinned solver failed the prescribed-MPC dynamic known-answer fixture; "
            "see port-reaction-known-answer-attempt01/RESULTS.md. "
            "Use a separately audited balanced-force transient formulation.")
    values = (motion_mm, ramp_s, hold_s, initial_dt_s, maximum_dt_s)
    if not all(math.isfinite(x) and x > 0 for x in values):
        raise ValueError("motion and all durations must be finite and positive")
    if not 1e-6 <= initial_dt_s <= maximum_dt_s <= ramp_s / 20:
        raise ValueError("inconsistent time controls")
    if ramp_segments < 100:
        raise ValueError("sampled smooth ramp needs at least 100 segments")
    destination = destination.resolve()
    if sha(SOURCE / SOURCE_LOCK) != SOURCE_LOCK_SHA:
        raise ValueError("source port-motion lock changed")
    source_lock = json.loads((SOURCE / SOURCE_LOCK).read_text())
    source_pins = source_lock["input_sha256"] | {SOURCE_LOCK: SOURCE_LOCK_SHA}
    if any(sha(SOURCE / name) != digest for name, digest in source_pins.items()):
        raise ValueError("frozen source artifact changed")
    source_audit = audit_source(SOURCE, "n_plus")
    source_blocks = cards((SOURCE / "port_motion_n_plus.inp").read_text())
    boundary = [data for header, data in source_blocks if header.startswith("*BOUNDARY,")]
    if len(boundary) != 1 or len(boundary[0]) != 12:
        raise ValueError("expected twelve source port control boundaries")
    destination.mkdir(parents=True, exist_ok=True)
    if any(path.name != "README.md" for path in destination.iterdir()):
        raise FileExistsError("use a new attempt directory containing only its decision README")
    for name in source_pins:
        (destination / name).write_bytes((SOURCE / name).read_bytes())
    (destination / "source-independent-audit.json").write_text(json.dumps(source_audit, indent=2) + "\n")
    (destination / "source-auditor.py.snapshot").write_bytes(
        (ROOT / "fea/wood_joint_current_port_motion_audit.py").read_bytes())
    # Keep incident-element integration-point stresses for later independent
    # cap traction/reaction checks; SOF alone does not prove conjugate work.
    ports = json.loads((SOURCE / "external-ports.json").read_text())
    cap_nodes = {int(n) for port in ports["ports"].values() for n in port["node_ids"]}
    _, elements, _ = parse_c3d10_deck((SOURCE / "mesh.inp").read_text(), context="transient source")
    incident = sorted(eid for eid, ns in elements.items() if cap_nodes.intersection(ns))
    if not incident:
        raise ValueError("missing cap-incident elements")
    (destination / "transient-output-sets.inp").write_text(
        "*ELSET,ELSET=WJ_PORT_INCIDENT_ELEMENTS\n" + "\n".join(rows(incident)) + "\n")
    deck = ["** External-port implicit transient; all internal bodies remain free."]
    for header, data in source_blocks:
        if header.startswith("*INCLUDE,"):
            deck.extend([header, *data])
    deck.extend(["*INCLUDE,INPUT=transient-output-sets.inp",
                 "*AMPLITUDE,NAME=WJ_PORT_MOTION_RAMP"])
    ramp = []
    for i in range(ramp_segments + 1):
        s = i / ramp_segments
        pair = (float(f"{s * ramp_s:.12g}"), float(f"{s**3 * (10 - 15*s + 6*s*s):.12g}"))
        ramp.append(pair)
        deck.append(f"{pair[0]:.12g},{pair[1]:.12g}")
    deck.extend([f"{ramp_s + hold_s:.12g},1",
                 "*STEP,NLGEOM,INC=1000", "*DYNAMIC,ALPHA=0",
                 f"{initial_dt_s:.12g},{ramp_s + hold_s:.12g},1.e-6,{maximum_dt_s:.12g}",
                 "*BOUNDARY,AMPLITUDE=WJ_PORT_MOTION_RAMP"])
    for line in boundary[0]:
        node, lo, hi, value = line.split(",")
        deck.append(f"{node},{lo},{hi},{float(value) * motion_mm:.13e}")
    deck.extend([
        "*NODE PRINT,NSET=WJ_PORT_MOTION_MONITOR,FREQUENCY=1", "U,RF",
        "*NODE PRINT,NSET=CURRENT_ALL_PHYSICAL_NODES,FREQUENCY=1", "U,V",
        "*NODE FILE,NSET=CURRENT_ALL_PHYSICAL_NODES,FREQUENCY=1", "U,V",
        "*SECTION PRINT,SURFACE=WJ_RAIL_SECTION,NAME=WJ_RAIL_PORT", "SOF",
        "*SECTION PRINT,SURFACE=WJ_PRINCIPAL_SECTION,NAME=WJ_PRINCIPAL_PORT", "SOF",
        "*EL FILE,FREQUENCY=1", "S,E",
        "*EL PRINT,ELSET=WJ_PORT_INCIDENT_ELEMENTS,FREQUENCY=1,GLOBAL=YES", "S",
        "*EL PRINT,ELSET=CURRENT_ALL_ELEMENTS,TOTALS=ONLY,FREQUENCY=1", "ELSE,ELKE,EMAS,EVOL",
        "*EL PRINT,ELSET=CURRENT_NUT_CARRIERS,TOTALS=ONLY,FREQUENCY=1", "ELSE,ELKE",
    ])
    for header, data in source_blocks:
        if header.startswith("*CONTACT PRINT,"):
            deck.extend([header, *data])
    deck.extend(["*CONTACT FILE,FREQUENCY=1", "CDIS,CSTR,CELS", "*END STEP"])
    (destination / "port_transient_n_plus.inp").write_text("\n".join(deck) + "\n")
    (destination / "transient-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    plan = {
        "schema": "wood_joint_external_port_transient/v1",
        "status": "FROZEN_INPUT_REQUIRES_INDEPENDENT_AUDIT_BEFORE_EXECUTION",
        "source_directory": str(SOURCE.relative_to(ROOT)),
        "source_artifacts_sha256": source_pins,
        "solver_image": source_lock["solver_image"],
        "solver_binary_sha256": source_lock["source_solver_binary_sha256"],
        "case": "n_plus", "procedure": "implicit dynamic ALPHA=0; no numerical damping or mass scaling",
        "motion_mm": motion_mm, "ramp_s": ramp_s, "hold_s": hold_s,
        "initial_dt_s": initial_dt_s, "maximum_dt_s": maximum_dt_s, "minimum_dt_s": 1e-6,
        "ramp_segments": ramp_segments,
        "ramp_rule": "tabulated quintic 10s^3-15s^4+6s^5; native interpolation is piecewise linear",
        "ramp_samples": ramp,
        "initial_velocity": "zero by native default; no INITIAL CONDITIONS",
        "density_scenario_kg_per_m3": {"wood": 600, "steel": 7850, "nut_seat_carriers": 0},
        "clearance_event_rule": "observe local wood-bore gap/pressure/action; commanded port travel is not proof of engagement",
        "physical_inputs_unchanged": True, "cleat_restraint": False,
        "cap_incident_element_count": len(incident),
        "generalized_reaction_caveat": "SOF gives section resultants; validate sign/datum, dynamic cap balance and work before calling it the projection-conjugate reaction; control RF is not the reaction",
        "native_work_caveat": "prescribed MPC work accounting requires independent validation; do not assume native printed external work includes it",
        "numerical_gates": {
            "energy_balance_relative": 0.05, "energy_absolute_floor_Nmm": 1e-5,
            "kinetic_over_elastic_plus_contact_max_for_quasistatic": 0.05,
            "force_and_moment_balance_relative_including_inertia": 0.01,
            "force_absolute_floor_N": 0.01, "moment_absolute_floor_Nmm": 10,
            "matched_state_ramp_rate_and_dt_response_relative": 0.05,
            "interpretation": "analyst-selected diagnostic screens only; not design acceptance; compare only above absolute energy/force floors",
        },
        "resource_bounds": {"cpus": 2, "memory_gib": 12, "wallclock_seconds": 7200,
                            "no_first_accepted_increment_seconds": 1800},
        "stop_rule": "step completion, native failure, no accepted increment at 1800 s, or 7200 s wallclock; retain raw data and leave unmet response requirements unresolved",
        "mechanical_acceptance": False,
    }
    plan["artifacts_sha256"] = {p.name: sha(p) for p in destination.iterdir() if p.is_file()}
    (destination / "transient-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--motion-mm", type=float, required=True)
    parser.add_argument("--ramp-s", type=float, default=0.2)
    parser.add_argument("--hold-s", type=float, default=0.05)
    parser.add_argument("--initial-dt-s", type=float, default=0.001)
    parser.add_argument("--maximum-dt-s", type=float, default=0.005)
    args = parser.parse_args()
    report = prepare(args.directory, motion_mm=args.motion_mm, ramp_s=args.ramp_s,
                     hold_s=args.hold_s, initial_dt_s=args.initial_dt_s,
                     maximum_dt_s=args.maximum_dt_s)
    print(json.dumps({"status": report["status"], "files": len(report["artifacts_sha256"])}))
