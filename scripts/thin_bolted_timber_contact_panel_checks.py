"""Admit timber-contact fields before reusing frozen finite panel diagnostics.

Only admission/orchestration is new. Panel ports, fields, screw references and
generalized correction methods retain their frozen bytes. No CAD, K or solve.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_panel_consumer as reused

method, ROOT, PACKET = reused.method, reused.method.ROOT, reused.method.PACKET
GATE_MODULE = "scripts.thin_bolted_timber_contact_admission"
GATE_SOURCE = "scripts/thin_bolted_timber_contact_admission.py"
GATE_SCHEMA = "thin_bolted_independent_timber_contact_admission/v1"
GATE_KEY = "independent_finite_timber_contact_support_load_and_equilibrium_checks_pass"
REUSED_SHA = "e41c1efefddfdce5e7bceee594f7fb2608b45edae69d368a1ae728a3b552210b"
KINEMATICS_SHA = "4d5467818a211f34c00aa897f1d0d64bc6c21dad07c2537a79c027820159174c"
LOADED_PRODUCER_SHA256 = method.sha(Path(__file__))
PINS = {**reused.BASE_PINS, "scripts/thin_bolted_finite_panel_consumer.py": REUSED_SHA}
IDENTITY_KEYS = ("state_id", "case_id", "accessory_placement")


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_name(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def merge_pins(*groups):
    pins = {}
    for group in groups:
        for path, digest in group.items():
            method.require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest) is not None
                           and (path not in pins or pins[path] == digest), "source pin is malformed or contradictory")
            pins[path] = digest
    reused.adapter.verify_pins(pins)
    return pins


def admit(field_path, admission_sha256):
    """One immutable payload through the fixed NEW timber-contact gate only."""
    method.require(isinstance(admission_sha256, str) and re.fullmatch("[0-9a-f]{64}", admission_sha256) is not None,
                   "explicit reviewed timber-contact admission SHA256 required")
    path = Path(field_path).resolve()
    payload = path.read_bytes()
    field = json.loads(payload)
    method.require(field.get("schema") == reused.FIELD_SCHEMA, "NEW finite field required; reference schema rejected")
    gate_path = ROOT / GATE_SOURCE
    method.require(method.sha(gate_path) == admission_sha256, "reviewed timber-contact gate source changed")
    gate = importlib.import_module(GATE_MODULE)
    method.require(Path(gate.__file__).resolve() == gate_path.resolve()
                   and getattr(gate, "LOADED_PRODUCER_SHA256", None) == admission_sha256,
                   "loaded timber-contact admission source/path differs")
    merge_pins(PINS, {source_name(__file__): LOADED_PRODUCER_SHA256, GATE_SOURCE: admission_sha256})
    receipt = gate.audit_timber_contact_state(payload)
    digest = hashlib.sha256(payload).hexdigest()
    method.require(receipt.get("schema") == GATE_SCHEMA and receipt.get(GATE_KEY) is True,
                   "NEW timber-contact current support/load/wrench admission failed")
    method.require(receipt.get("field_sha256") == digest and receipt.get("field_canonical_sha256") == canonical_sha(field)
                   and all(receipt.get(key) == field[key] for key in IDENTITY_KEYS)
                   and receipt.get("source_sha256", {}).get(GATE_SOURCE) == admission_sha256,
                   "timber-contact receipt does not bind exact payload/state/source")
    method.require(field.get("release") and not any(field["release"].values()), "analysis cannot authorize release")
    method.require(field["parameters"]["panel_intervals"] == 8
                   and field["parameters"]["foundation_port_cell_mm"] == 70.
                   and sum(row["kind"] == "panel_contact" for row in field["finite_interaction_actions"]) == 530,
                   "wrapper retains interval8/contact530 panel scenario only")
    pins = merge_pins(PINS, field["source_sha256"], receipt["source_sha256"],
                      {source_name(path): digest, source_name(__file__): LOADED_PRODUCER_SHA256})
    method.require(path.read_bytes() == payload, "finite field changed during admission")
    return path, payload, field, receipt, pins


def panels_from_map(field):
    """Frozen map/port reader, with no energy quadrature or stiffness assembly."""
    mapping = field["finite_kinematic_map"]
    q = np.asarray(field["response"]["q"], dtype=float)
    method.require(q.shape == (mapping["ndof"],) and np.isfinite(q).all()
                   and set(mapping["panels"]) == set(method.PANELS), "finite q/six-panel map differs")
    geometry = {row["panel"]: row for row in json.loads(reused.references.ASSESSMENT.read_bytes())["panel_geometry"]}
    integrated = json.loads(method.INTEGRATED.read_bytes())
    panels = {}
    for name, row in mapping["panels"].items():
        geo = {"origin": np.asarray(row["origin_xyz_mm"]), "axes": np.asarray(row["axes_columns_xyz"])}
        holes = [{**hole, "xy_mm": method.local_xy(hole["start_xyz_mm"], geo).tolist()}
                 for hole in integrated["panel_machining"]["features"] if hole["panel"] == name]
        panels[name] = reused.MappedFinitePanel(name, row, mapping["ndof"], geometry[name], holes)
    indices = np.concatenate([panel.indices for panel in panels.values()])
    method.require(len(set(indices.tolist())) == len(indices), "finite panel blocks overlap")
    return panels, q


def finish(path, payload, pins):
    merge_pins(pins)
    method.require(path.read_bytes() == payload, "finite field changed during diagnostics")


def evaluate(field_path, samples=41, *, admission_sha256):
    method.require(isinstance(samples, int) and samples >= 4, "at least four samples per axis required")
    path, payload, field, receipt, pins = admit(field_path, admission_sha256)
    panels, q = panels_from_map(field)
    expected = {row["axis_id"]: row for row in json.loads(method.LAYOUT.read_bytes())["screw_axes"]}
    actions = [row for row in field["finite_interaction_actions"] if row["kind"] == "panel_screw"]
    corrections = field["panel_generalized_load_corrections"]
    method.require(len(actions) == 66 and {row["id"] for row in actions} == set(expected)
                   and len(corrections) == 12, "all66 screws and both corrections for each panel required")
    method.require(all(all(row[key] == field[key] for key in IDENTITY_KEYS) for row in [*actions, *corrections]),
                   "finite panel actions/corrections mix identities")
    screws = [reused.current_screw_diagnostics(panels[expected[row["id"]]["panel"]], q, expected[row["id"]], row)
              for row in actions]
    rows = [{"panel": name, "state_id": field["state_id"],
             "same_state_head_witness": max((r for r in screws if r["panel"] == name), key=lambda r: r["withdrawal_n"]),
             "finite_section_diagnostics": reused.section_diagnostics(panel, q, samples),
             "generalized_correction_diagnostics": reused.correction_diagnostics(panel, q, [r for r in corrections if r["panel"] == name])}
            for name, panel in panels.items()]
    finish(path, payload, pins)
    return {"schema": "thin_bolted_timber_contact_panel_diagnostics/v1",
        **{key: field[key] for key in ("candidate", "revision", *IDENTITY_KEYS, "parameters")},
        "field_sha256": hashlib.sha256(payload).hexdigest(), "source_sha256": pins, "finite_admission": receipt,
        "panel_diagnostics": rows, "screw_actions_and_generic_references": screws,
        "maximum_head_witness": max(screws, key=lambda r: r["withdrawal_n"]),
        "method": {"frozen_panel_functions_reused": True, "old_gate_used": False,
                   "CAD_rebuilt": False, "energy_quadrature_prepared": False, "K_assembled": False, "response_solved": False},
        "limits": ["Generic head/withdrawal and mean-ring pressure do not establish Hillman42605 capacity or measured stiffness.",
            "Finite APA proxy resultants/linear target indices do not qualify a finite plywood laminate, local holes/seats/holds/edges or contact capacity.",
            "New current timber-contact admission is distinct from response/refinement/material/resistance qualification; CD1 and conditional wind/earthquake1.6 remain separate."],
        "complete_panel_resistance_established": False, "release": dict(reused.references.RELEASE)}


def evaluate_local_kinematics(field_path, *, admission_sha256):
    """Tiny new admission wrapper around the existing K-free evaluate_map API."""
    path, payload, field, receipt, pins = admit(field_path, admission_sha256)
    from scripts import thin_bolted_finite_kinematics as kinematics
    pins = merge_pins(pins, kinematics.source_pins(), {"scripts/thin_bolted_finite_kinematics.py": KINEMATICS_SHA})
    spans = kinematics.spans_method.read_member_span_geometry()
    basis = {name: row["basis_grain_u_v_xyz"] for name, row in spans.items()}
    result = kinematics.evaluate_map(field["finite_kinematic_map"], field["response"]["q"], basis)
    finish(path, payload, pins)
    return {**result, "schema": "thin_bolted_timber_contact_local_kinematics/v1",
            **{key: field[key] for key in IDENTITY_KEYS}, "field_sha256": hashlib.sha256(payload).hexdigest(),
            "source_sha256": pins, "finite_admission": receipt, "release": dict(reused.references.RELEASE)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--samples", type=int, default=41)
    parser.add_argument("--local-kinematics", action="store_true")
    args = parser.parse_args()
    result = (evaluate_local_kinematics(args.field, admission_sha256=args.admission_sha256) if args.local_kinematics
              else evaluate(args.field, args.samples, admission_sha256=args.admission_sha256))
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": method.sha(args.out), "state_id": result["state_id"]}))


if __name__ == "__main__":
    main()
