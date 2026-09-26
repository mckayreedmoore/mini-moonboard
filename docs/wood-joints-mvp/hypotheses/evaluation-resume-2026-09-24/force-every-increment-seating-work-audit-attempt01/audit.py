"""Audit one immutable force-driven transient prefix without reading live output."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from fea.wood_joint_current_transient_history import (
    _input_closure,
    _parse_deck_patterns,
    _unit_weights,
    audit_history_texts,
    parse_accepted_sta,
)

SNAPSHOT_DIR = (
    REPO
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    / "force-every-increment-seating-prefix-attempt01"
)
EXPECTED_SNAPSHOT_SHA256 = (
    "001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a"
)
EXPECTED_INPUT_FREEZE_SHA256 = (
    "f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66"
)
MONITOR_HEADER = re.compile(
    r"displacements \(vx,vy,vz\) for set PILOT_MONITOR and time\s+(\S+)",
    re.IGNORECASE,
)
OUTPUT_NAMES = {"pilot.dat", "pilot.log", "pilot.sta", "pilot.frd"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_snapshot_file(folder: Path, manifest: dict, name: str) -> str:
    pin = manifest["files"].get(name)
    if not isinstance(pin, dict):
        raise TypeError(f"snapshot manifest lacks {name}")
    path = folder / name
    if path.stat().st_size != pin["bytes"] or _sha256(path) != pin["sha256"]:
        raise ValueError(f"snapshot file differs from manifest: {name}")
    return pin["sha256"]


def _monitor_blocks_streaming(path: Path, expected_nodes: set[int], expected_pin: dict):
    """Hash the full DAT while retaining only complete monitor blocks."""
    digest = hashlib.sha256()
    blocks: list[str] = []
    times: list[float] = []
    incomplete_blocks = 0
    partial_final_line = False
    byte_count = 0
    active = None

    with path.open("rb") as stream:
        for raw in stream:
            byte_count += len(raw)
            digest.update(raw)
            if not raw.endswith(b"\n"):
                partial_final_line = True
                break
            line = raw.decode("ascii").rstrip("\r\n")
            header = MONITOR_HEADER.search(line)
            if header is not None:
                if active is not None:
                    incomplete_blocks += 1
                active = {
                    "lines": [line],
                    "nodes": set(),
                    "time_token": header.group(1),
                }
                continue
            if active is None:
                continue
            fields = line.split()
            if not fields and not active["nodes"]:
                active["lines"].append(line)
                continue
            if len(fields) != 4 or not fields[0].isdigit():
                incomplete_blocks += 1
                active = None
                continue
            node = int(fields[0])
            if node not in expected_nodes or node in active["nodes"]:
                raise ValueError("unexpected or duplicate node in frozen monitor block")
            for token in fields[1:]:
                value = float(token.replace("D", "E").replace("d", "e"))
                if not math.isfinite(value):
                    raise ValueError("nonfinite displacement in frozen monitor block")
            active["nodes"].add(node)
            active["lines"].append(line)
            if active["nodes"] == expected_nodes:
                blocks.append("\n".join(active["lines"]) + "\n")
                times.append(float(active["time_token"].replace("D", "E")))
                active = None

    if active is not None:
        incomplete_blocks += 1
    if (
        byte_count != expected_pin["bytes"]
        or digest.hexdigest() != expected_pin["sha256"]
    ):
        raise ValueError("pilot.dat differs from immutable snapshot manifest")
    return blocks, {
        "bytes": byte_count,
        "sha256": digest.hexdigest(),
        "complete_monitor_block_count": len(blocks),
        "complete_monitor_times_seconds": times,
        "incomplete_monitor_block_count": incomplete_blocks,
        "partial_final_line_ignored": partial_final_line,
        "method": "single streaming pass over the full pinned DAT; only complete PILOT_MONITOR blocks retained",
    }


def _main() -> None:
    folder = Path(__file__).resolve().parent
    manifest_bytes = (SNAPSHOT_DIR / "snapshot.json").read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_sha != EXPECTED_SNAPSHOT_SHA256:
        raise ValueError("force-history snapshot manifest hash changed")
    manifest = json.loads(manifest_bytes)
    if manifest.get("status") != "IMMUTABLE_LIVE_OUTPUT_PREFIX_SNAPSHOT":
        raise ValueError("input is not the expected immutable prefix snapshot")

    freeze_sha = _verify_snapshot_file(SNAPSHOT_DIR, manifest, "input-freeze.json")
    if freeze_sha != EXPECTED_INPUT_FREEZE_SHA256:
        raise ValueError("force-history input-freeze hash changed")
    freeze = json.loads((SNAPSHOT_DIR / "input-freeze.json").read_text())
    if freeze.get("mechanical_acceptance") is not False:
        raise ValueError("frozen input must explicitly withhold mechanical acceptance")
    input_pins = freeze.get("artifacts_sha256")
    if not isinstance(input_pins, dict) or not input_pins:
        raise ValueError("input freeze has no source artifact pins")
    if OUTPUT_NAMES.intersection(input_pins):
        raise ValueError("an output file appears in the frozen input artifact map")

    source = Path(manifest["source_case"])
    for name, expected_hash in input_pins.items():
        path = source / name
        if not path.is_file() or _sha256(path) != expected_hash:
            raise ValueError(f"source input differs from frozen input hash: {name}")
    deck_texts = _input_closure(source, "pilot.inp", set(input_pins))

    sta_sha = _verify_snapshot_file(SNAPSHOT_DIR, manifest, "pilot.sta")
    dat_pin = manifest["files"]["pilot.dat"]
    dat_blocks, dat_scan = _monitor_blocks_streaming(
        SNAPSHOT_DIR / "pilot.dat",
        {int(node) for node in freeze["monitor_nodes"]},
        dat_pin,
    )
    log_sha = _verify_snapshot_file(SNAPSHOT_DIR, manifest, "pilot.log")
    sta_text = (SNAPSHOT_DIR / "pilot.sta").read_text()
    accepted, rejected = parse_accepted_sta(sta_text)
    accepted_increments = [row["increment"] for row in accepted]
    if accepted_increments != list(range(1, len(accepted) + 1)):
        raise ValueError("accepted increment sequence has a gap; refusing to bridge it")

    dat_text = "\n".join(block.rstrip("\n") for block in dat_blocks) + "\n"
    log_text = (SNAPSHOT_DIR / "pilot.log").read_text()
    report = audit_history_texts(
        freeze=freeze,
        deck_texts=deck_texts,
        sta_text=sta_text,
        dat_text=dat_text,
        log_text=log_text,
    )
    if report["rejected_attempt_count"] != rejected:
        raise ValueError("accepted status parser counts disagree")
    if report["monitor_coverage"]["status"] != "complete":
        raise ValueError("at least one accepted state lacks complete monitor coverage")
    if report["work"]["native_comparison_status"] != "available":
        raise ValueError("at least one accepted state lacks a native work row")

    points, load_scale = _parse_deck_patterns(deck_texts, freeze)
    nonzero_unit_terms = sum(
        value != 0.0 for row in _unit_weights(freeze).values() for value in row
    )
    if report["load_scale_from_actual_cload"] != load_scale:
        raise ValueError("reported actual CLOAD scale differs from deck parser")
    accepted_monitor_times = [
        row["time_seconds"] for row in report["work"]["accepted_rows"]
    ]
    impulse_intervals = report["force_impulse"]["intervals"]
    skipped_knots = []
    time_tolerance = report["time_match_tolerance_seconds"]
    for interval in impulse_intervals:
        start, end = interval["start_time_seconds"], interval["end_time_seconds"]
        knots = [
            time
            for time, _amplitude in points
            if start + time_tolerance < time < end - time_tolerance
        ]
        if knots:
            skipped_knots.append(
                {
                    "start_time_seconds": start,
                    "end_time_seconds": end,
                    "interior_ramp_knots_seconds": knots,
                }
            )

    report["snapshot_dat_scan"] = dat_scan
    report["ramp_and_load_validation"] = {
        "ramp_interpolation": freeze.get("ramp_interpolation"),
        "ramp_time_basis": freeze.get("amplitude_time_basis"),
        "serialized_ramp_point_count": len(points),
        "actual_cload_scale_from_unit_pattern": load_scale,
        "unit_pattern_node_count": len(_unit_weights(freeze)),
        "actual_nonzero_cload_scalar_term_count": nonzero_unit_terms,
        "accepted_monitor_times_seconds": accepted_monitor_times,
        "accepted_intervals_with_skipped_ramp_knots": skipped_knots,
        "every_accepted_endpoint_is_a_ramp_knot": all(
            any(abs(time - knot) <= time_tolerance for knot, _ in points)
            for time in accepted_monitor_times
        ),
    }
    report["mechanical_acceptance"] = False
    report["prefix_provenance"] = {
        "snapshot_manifest_sha256": manifest_sha,
        "snapshot_capture_status": manifest["status"],
        "snapshot_capture_policy": manifest.get("capture_policy"),
        "input_freeze_sha256": freeze_sha,
        "verified_source_input_artifact_count": len(input_pins),
        "verified_source_input_artifacts_sha256": input_pins,
        "consumed_snapshot_output_sha256": {
            "pilot.sta": sta_sha,
            "pilot.dat": dat_scan["sha256"],
            "pilot.log": log_sha,
            "input-freeze.json": freeze_sha,
        },
        "producer_sha256": _sha256(Path(__file__)),
        "scope": "Immutable non-atomic live-output prefix; no source-case outputs or FRD read; not a terminal response or contact audit.",
    }
    output = folder / "report.json"
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "accepted_increment_count": report["accepted_increment_count"],
                "rejected_attempt_count": report["rejected_attempt_count"],
                "work_nmm": report["work"]["cumulative_discrete_work_nmm"],
                "impulse_ns": report["force_impulse"][
                    "cumulative_piecewise_linear_pattern_impulse_ns"
                ],
                "skipped_ramp_knots": skipped_knots,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    _main()
