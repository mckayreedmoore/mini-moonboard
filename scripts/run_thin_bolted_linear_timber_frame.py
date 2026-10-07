"""One bounded first-order case with physical shafts and paired wood contact.

The frozen producer, incremental solver and finished-floor writer are reused.
Only the previously omitted timber compression path and its provenance are
added. No failed field supplies initial coefficients or accepted actions.
"""

from __future__ import annotations

import argparse
import copy
import json
import signal
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import run_thin_bolted_common_shaft_frame as common
from scripts import run_thin_bolted_common_shaft_incremental as reused
from scripts import run_thin_bolted_finite_frame as saved_panels
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as incremental
from scripts import thin_bolted_linear_timber_faces as faces
from scripts import thin_bolted_panel_mechanics as panel_tools
from scripts.thin_bolted_timber_face_contact import merge_pins

LOADED_DRIVER_SHA256 = frame.sha(Path(__file__))
REUSED_DRIVER_SHA256 = "342ca53532d08bab670bac13f923c00665bd4660722541ff936e4380131b1588"
PROOF = frame.PACKET / "timber-face-contact-geometry-v4.json"
PROOF_SHA256 = "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a"
SAVED_PANEL_HELPER_SHA256 = "5cf423d80e57b6f4386eb6c7aae39961ba083a7b4a457c7d37694cb80101361e"
PANEL_OPERATOR_PINS = {
    "fea/generated/thin-bolted-panel/operators-intervals8.npz": "2b97d8c1741a0fbef119eb00b3f43bdf5f76e802b4851962a62fc555f1813468",
    "fea/generated/thin-bolted-panel/operators-intervals8.json": "aeeb9b6ccd2c521896b32012ccbf9712fd67cdb7d0744e06d88afa4fd3f441d4"}


class CaseWallTimeLimit(RuntimeError):
    """A stopped case supplies no admitted force field."""


@contextmanager
def wall_limit(seconds: float):
    """Bound this one process and restore the caller's alarm configuration."""
    if not np.isfinite(seconds) or not 0. < seconds <= 1800.:
        raise ValueError("one case requires a positive wall limit at most 1800 seconds")
    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    if old_timer != (0., 0.):
        raise ValueError("case must not replace an existing process alarm")

    def stop(_signum, _frame):
        raise CaseWallTimeLimit("lean case wall-time limit")

    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.)
        signal.signal(signal.SIGALRM, old_handler)


def failed_wall_response(last: dict) -> dict:
    """Preserve diagnostics without calling an observed iterate a solution."""
    return {"converged": False, "termination": "lean case wall-time limit",
            "gradient_inf_n": last.get("gradient_inf_n"),
            "gradient_observation_available": "gradient_inf_n" in last,
            "potential_energy_nmm": last.get("potential_energy_nmm"),
            "diagnostic_last_q": last.get("q"),
            "diagnostic_last_q_is_a_converged_or_accepted_force_field": False,
            "generalized_residual_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
            "physical_residual_uses_unmodified_laws": True,
            "wall_time_limit_reached": True,
            "iteration_history": last.get("history", [])}


def write_interruption(path: Path, command: list[str], prepared: dict, panel_preparation: dict, last: dict) -> Path:
    """Keep a phase interruption distinct from a complete mechanics field."""
    sidecar = path.with_name(path.name + ".interrupted.json")
    pins = merge_pins(incremental.source_pins(), prepared.get("source_sha256", {}),
                      panel_preparation.get("source_sha256", {}), PANEL_OPERATOR_PINS,
                      {str(Path(__file__).relative_to(frame.ROOT)): LOADED_DRIVER_SHA256,
                       str(Path(reused.__file__).relative_to(frame.ROOT)): REUSED_DRIVER_SHA256,
                       str(Path(saved_panels.__file__).relative_to(frame.ROOT)): SAVED_PANEL_HELPER_SHA256})
    report = {"schema": "thin_bolted_linear_timber_interrupted/v1", "command": command,
              "termination": "lean case wall-time limit", "phase": last.get("phase"),
              "source_sha256": pins, "response": failed_wall_response(last),
              "usable_conditional_actions": False, "accepted_field_exported": False,
              "existing_output_sha256_not_admitted": frame.sha(path) if path.exists() else None,
              "release": frame.RELEASE}
    with sidecar.open("x") as stream:
        stream.write(common.finished.writer.dump(report))
    return sidecar


def main() -> None:
    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--wood-bedding", type=float, default=1.)
    parser.add_argument("--wall-seconds", type=float, default=1800.)
    custom, remainder = parser.parse_known_args(arguments)
    scope = argparse.ArgumentParser(add_help=False)
    scope.add_argument("--cases", nargs="+", default=["a12-rear"])
    scope.add_argument("--warm-start")
    scope.add_argument("--warm-start-sha256")
    scope.add_argument("--newton-limit", type=int, default=300)
    scope.add_argument("--out", type=Path)
    scope.add_argument("--out-dir", type=Path)
    scope.add_argument("--intervals", type=int, default=8)
    scope.add_argument("--contact-edge", type=float, default=70.)
    selected, _ = scope.parse_known_args(remainder)
    if (selected.cases != ["a12-rear"] or selected.warm_start
            or selected.warm_start_sha256 or not 0 < selected.newton_limit <= 300
            or selected.intervals != 8 or selected.contact_edge != 70.):
        parser.error("one A12-rear case, original initialization and at most 300 iterations per pattern required")
    if "--newton-limit" not in remainder:
        remainder = ["--newton-limit", "300", *remainder]
    if "--contact-edge" not in remainder:
        remainder = ["--contact-edge", "70", *remainder]
    if (selected.out is None) == (selected.out_dir is None):
        parser.error("one explicit output path or output directory required")
    output = selected.out or selected.out_dir / "compatible-frame-a12-rear-v4.json"
    if frame.sha(Path(__file__)) != LOADED_DRIVER_SHA256:
        raise ValueError("loaded lean driver differs from its source")
    if frame.sha(Path(reused.__file__)) != REUSED_DRIVER_SHA256:
        raise ValueError("preserve the frozen incremental orchestration")
    if frame.sha(Path(saved_panels.__file__)) != SAVED_PANEL_HELPER_SHA256:
        raise ValueError("preserve the existing saved-panel reuse helper")
    for path, expected in PANEL_OPERATOR_PINS.items():
        if frame.sha(frame.ROOT / path) != expected:
            raise ValueError("preserve the authenticated interval8 panel operators")
    command = [sys.executable, "-m", "scripts.run_thin_bolted_linear_timber_frame", *arguments]
    original_connections = frame.elastic_connections
    original_metadata = common.bind_common_metadata
    original_fields = incremental.ORIGINAL_FIELDS
    original_incremental_solve = incremental.compatible_contact_solve
    prepared: dict = {}
    panel_preparation: dict = {}
    last: dict = {"history": [], "phase": "frozen_preparation"}

    def panels(geometry_path, *, intervals=8, contact_edge=70., **kwargs):
        if (geometry_path != frame.GEOMETRY_CACHE or intervals != 8 or contact_edge != 70.
                or kwargs or panel_preparation):
            raise ValueError("one unchanged saved panel preparation required")
        result, pins, proof = saved_panels.reuse_panel_operators()
        panel_preparation.update({"source_sha256": pins, "proof": proof})
        return result, json.loads(frame.EVIDENCE.read_text()), json.loads(frame.GEOMETRY_CACHE.read_text())

    def connections(assembly, *args, **kwargs):
        if prepared:
            raise ValueError("one prepared case only")
        groups, contacts, tangents = original_connections(assembly, *args, **kwargs)
        prepared.update(faces.prepare_linear_timber_faces(
            assembly, PROOF, PROOF_SHA256, bedding_n_mm3=custom.wood_bedding))
        if (any(row.get("kind") == "timber_face_contact" for row in contacts)
                or {row["id"] for row in contacts} & {row["id"] for row in prepared["contacts"]}):
            raise ValueError("paired wood contact already present or contact identities overlap")
        return groups, [*contacts, *prepared["contacts"]], tangents

    def observe_fields(K, applied, groups, C, ck, q, *, tangent=False):
        result = original_fields(K, applied, groups, C, ck, q, tangent=tangent)
        if tangent:
            gradient, energy = result[:2]
            record = {"observation": len(last["history"]),
                      "gradient_inf_n": float(abs(gradient).max()),
                      "potential_energy_nmm": float(energy)}
            last.update(record, q=np.array(q, copy=True))
            last["history"].append(record)
            if record["observation"] % 10 == 0 or record["gradient_inf_n"] < 1e-5:
                print(json.dumps({"lean_case_progress": record}), flush=True)
        return result

    def solve(*args, **kwargs):
        last["phase"] = "response"
        try:
            result = original_incremental_solve(*args, **kwargs)
            last["phase"] = "post_response_recovery"
            return result
        except CaseWallTimeLimit:
            return failed_wall_response(last)

    def metadata(report, system, pins, _command):
        last["phase"] = "provenance_and_export"
        report = original_metadata(report, system, pins, command)
        if not prepared:
            raise ValueError("paired wood contacts were not prepared")
        report["parameters"].update(prepared["metadata"]["parameters"])
        report["parameters"].update({
            "linear_timber_frame_driver_sha256": LOADED_DRIVER_SHA256,
            "lean_case_wall_time_limit_seconds": custom.wall_seconds})
        if not panel_preparation:
            raise ValueError("saved panel operators were not reused")
        report["source_sha256"] = merge_pins(report["source_sha256"], prepared["source_sha256"],
            panel_preparation["source_sha256"], PANEL_OPERATOR_PINS, {
            str(Path(__file__).relative_to(frame.ROOT)): LOADED_DRIVER_SHA256,
            str(Path(reused.__file__).relative_to(frame.ROOT)): REUSED_DRIVER_SHA256,
            str(Path(saved_panels.__file__).relative_to(frame.ROOT)): SAVED_PANEL_HELPER_SHA256})
        report["reference_panel_preparation"] = copy.deepcopy(panel_preparation["proof"])
        report["linear_timber_face_method"] = prepared["metadata"]["method"]
        report["linear_timber_coordinate_map"] = copy.deepcopy(prepared["coordinate_map"])
        report["counts"].update({"paired_timber_interfaces": 6,
                                 "paired_timber_compression_cells": 272})
        if "q" in report["response"]:
            report = faces.stamp_recovered_actions(report, prepared, np.asarray(report["response"]["q"]))
        report["lean_joint_execution"] = {
            "command": command, "one_case_only": True,
            "automatic_retries": 0, "wall_time_limit_seconds": custom.wall_seconds,
            "warm_initialization": None, "frozen_floor_law_reused": True,
            "old_forces_or_acceptance_transferred": False,
            "new_solver_framework": False,
            "restored_timber_compression_path": True,
            "small_motion_applicability_established": False}
        report["limits"].append(
            "All six paired timber faces use reference-cell linear ports and friction-free compression with declared bedding. Actual contact stiffness, finite overlap, cut compliance and complete joint capacities remain unqualified.")
        if frame.sha(Path(__file__)) != LOADED_DRIVER_SHA256:
            raise ValueError("lean driver changed during the case")
        return report

    old_argv = copy.copy(sys.argv)
    try:
        sys.argv = [old_argv[0], *remainder]
        with (wall_limit(custom.wall_seconds),
              patch.object(frame, "elastic_connections", connections),
              patch.object(panel_tools, "prepare_panel_models", panels),
              patch.object(common, "bind_common_metadata", metadata),
              patch.object(incremental, "ORIGINAL_FIELDS", observe_fields),
              patch.object(incremental, "compatible_contact_solve", solve)):
            reused.main()
    except CaseWallTimeLimit:
        sidecar = write_interruption(output, command, prepared, panel_preparation, last)
        print(json.dumps({"interrupted_case": str(sidecar), "usable_conditional_actions": False}), flush=True)
        raise SystemExit(1) from None
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
