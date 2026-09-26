"""Freeze a ramp-knot-aligned derivative of the 100 N seating diagnostic.

This changes output scheduling only: the scaled CLOADs, unit-load actuator
observation, amplitude, physical inputs, and adaptive time-step limits remain
from the pinned 100 N child. It performs no native execution or CAD work.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SOURCE = BASE / "ordinary-transient-seating-100n-attempt01"
SOURCE_FREEZE_SHA256 = "6024c734d50148ec959f972f41f15bc3f8f87ec42fbad65e13261e720fe5d9fa"
REVIEW = BASE / "native-ramp-time-points-review.md"
TIME_POINT_REVIEW_SHA256 = "3b7d99503afb507557e523b0065133cfcbe42875ccc51237cfb1115a519bfc0d"
TIME_POINT_NAME = "RAMP_KNOTS"
TIME_POINT_SECONDS = tuple(i / 1000 for i in range(1, 26))
TIME_POINT_ROWS = (
    "0.001,0.002,0.003,0.004,0.005,0.006,0.007,0.008",
    "0.009,0.010,0.011,0.012,0.013,0.014,0.015,0.016",
    "0.017,0.018,0.019,0.020,0.021,0.022,0.023,0.024",
    "0.025",
)
OUTPUT_KEYWORDS = (
    "*NODE FILE",
    "*NODE PRINT",
    "*EL PRINT",
    "*CONTACT FILE",
    "*CONTACT PRINT",
)
EXPECTED_OUTPUT_CARDS = 41


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def is_output_card(line: str) -> bool:
    upper = line.upper()
    return not upper.startswith("**") and upper.startswith(OUTPUT_KEYWORDS)


def output_cards(deck: str) -> list[str]:
    return [line for line in deck.splitlines() if is_output_card(line)]


def _replace_frequency(line: str) -> str:
    fields = line.split(",")
    frequency_indexes = [
        i for i, field in enumerate(fields) if field.strip().upper() == "FREQUENCY=1"
    ]
    if len(frequency_indexes) != 1:
        raise ValueError(f"expected one FREQUENCY=1 option on output card: {line}")
    fields[frequency_indexes[0]] = f"TIME POINTS={TIME_POINT_NAME}"
    return ",".join(fields)


def _format_time_points() -> list[str]:
    return [f"*TIME POINTS,NAME={TIME_POINT_NAME}", *TIME_POINT_ROWS]


def normalize_timed_deck(deck: str) -> str:
    """Remove the added sequence and restore the original output schedule."""
    lines = deck.splitlines()
    normalized: list[str] = []
    i = 0
    point_card = f"*TIME POINTS,NAME={TIME_POINT_NAME}"
    while i < len(lines):
        line = lines[i]
        if line.strip().upper() == point_card:
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                i += 1
            continue
        if is_output_card(line):
            fields = line.split(",")
            indexes = [
                j for j, field in enumerate(fields)
                if field.strip().upper() == f"TIME POINTS={TIME_POINT_NAME}"
            ]
            if len(indexes) != 1:
                raise ValueError(f"timed output card lacks a unique sequence: {line}")
            fields[indexes[0]] = "FREQUENCY=1"
            line = ",".join(fields)
        normalized.append(line)
        i += 1
    return "\n".join(normalized) + ("\n" if deck.endswith("\n") else "")


def transform_deck(deck: str) -> str:
    """Add the knot list and apply it to every existing output request."""
    lines = deck.splitlines()
    if any(line.strip().upper().startswith("*TIME POINTS") for line in lines):
        raise ValueError("source deck already defines TIME POINTS")
    if not any(line.strip().upper() == "*AMPLITUDE,NAME=RAMP_N" for line in lines):
        raise ValueError("source RAMP_N amplitude card is missing or changed")
    if any(",DIRECT" in line.upper() for line in lines if line.upper().startswith("*DYNAMIC")):
        raise ValueError("TIME POINTS output is incompatible with DIRECT dynamics")
    if len([line for line in lines if line.upper().startswith("*STEP")]) != 1:
        raise ValueError("expected exactly one step")

    source_outputs = output_cards(deck)
    if len(source_outputs) != EXPECTED_OUTPUT_CARDS:
        raise ValueError(f"expected {EXPECTED_OUTPUT_CARDS} output cards, found {len(source_outputs)}")
    if any("TIME POINTS=" in line.upper() for line in source_outputs):
        raise ValueError("source output request already has a time-point schedule")

    result: list[str] = []
    inserted = False
    for line in lines:
        if line.upper().startswith("*STEP"):
            if inserted:
                raise ValueError("multiple steps")
            result.extend(_format_time_points())
            inserted = True
        result.append(_replace_frequency(line) if is_output_card(line) else line)
    if not inserted:
        raise ValueError("step card is missing")
    timed = "\n".join(result) + ("\n" if deck.endswith("\n") else "")
    timed_outputs = output_cards(timed)
    if len(timed_outputs) != EXPECTED_OUTPUT_CARDS or any(
        f"TIME POINTS={TIME_POINT_NAME}" not in line.upper()
        or "FREQUENCY=" in line.upper()
        for line in timed_outputs
    ):
        raise ValueError("not every output request uses RAMP_KNOTS")
    if normalize_timed_deck(timed) != deck:
        raise ValueError("unexpected deck change outside time-point schedule/output cards")
    return timed


def prepare(destination: Path, *, source_dir: Path = SOURCE,
            expected_source_freeze_sha256: str = SOURCE_FREEZE_SHA256) -> dict:
    """Freeze a child with source pins and the exact transformed pilot deck."""
    source_dir = Path(source_dir).resolve()
    source_freeze_path = source_dir / "input-freeze.json"
    if sha(source_freeze_path) != expected_source_freeze_sha256:
        raise ValueError("unexpected 100 N source freeze")
    source_freeze = json.loads(source_freeze_path.read_text())
    if source_freeze.get("status") != "FROZEN_NOT_EXECUTED":
        raise ValueError("100 N source is not a frozen, unexecuted diagnostic")
    if source_freeze.get("cload_reference_scale") != 100:
        raise ValueError("source does not preserve the 100x reference CLOAD scale")
    if not math.isclose(source_freeze.get("final_amplitude_n", math.nan), 15.625):
        raise ValueError("unexpected 0.025 s endpoint force for the 100 N reference ramp")
    if source_freeze.get("parent_input_freeze_sha256") != (
        "77090f458d68afc20abfa34203496527030d075c96868ae99d2aed7091043e66"
    ):
        raise ValueError("source is not tied to the frozen pilot04 parent")
    source_pins = source_freeze.get("artifacts_sha256", {})
    if not source_pins or not all(
        sha(source_dir / name) == digest for name, digest in source_pins.items()
    ):
        raise ValueError("100 N source artifact pin mismatch")
    if sha(REVIEW) != TIME_POINT_REVIEW_SHA256:
        raise ValueError("time-point source review changed")
    if sha(source_dir / "parent-input-freeze.json") != source_pins.get(
        "parent-input-freeze.json"
    ):
        raise ValueError("pilot04 parent freeze changed")
    if sha(source_dir / "scale-producer.py.snapshot") != source_pins.get(
        "scale-producer.py.snapshot"
    ):
        raise ValueError("100 N scale-producer snapshot changed")

    source_deck_path = source_dir / "pilot.inp"
    source_deck = source_deck_path.read_text()
    deck = transform_deck(source_deck)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)

    for name in source_pins:
        if name == "pilot.inp":
            continue
        (destination / name).write_bytes((source_dir / name).read_bytes())
    (destination / "pilot.inp").write_text(deck)
    # Preserve the pilot04 lineage under its existing name; add the immediate
    # scaled-parent freeze under a distinct name instead of overwriting it.
    (destination / "timing-parent-input-freeze.json").write_bytes(
        source_freeze_path.read_bytes()
    )
    (destination / "timed-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())

    if sha(source_freeze_path) != expected_source_freeze_sha256 or not all(
        sha(source_dir / name) == digest for name, digest in source_pins.items()
    ):
        raise ValueError("100 N source changed during derivative freeze")
    if sha(destination / "parent-input-freeze.json") != source_pins[
        "parent-input-freeze.json"
    ]:
        raise ValueError("pilot04 parent freeze was not preserved byte-for-byte")
    if sha(destination / "scale-producer.py.snapshot") != source_pins[
        "scale-producer.py.snapshot"
    ]:
        raise ValueError("scale producer snapshot was not preserved byte-for-byte")

    report = dict(source_freeze)
    report.update(
        status="FROZEN_NOT_EXECUTED",
        timing_parent_input_freeze_sha256=expected_source_freeze_sha256,
        time_point_review_sha256=TIME_POINT_REVIEW_SHA256,
        time_points_name=TIME_POINT_NAME,
        time_points_step_seconds=list(TIME_POINT_SECONDS),
        output_request_card_count=EXPECTED_OUTPUT_CARDS,
        output_schedule=(
            "All 41 active *NODE FILE, *NODE PRINT, *EL PRINT, *CONTACT FILE, "
            "and *CONTACT PRINT cards reference TIME POINTS=RAMP_KNOTS."
        ),
        output_scope_limit=(
            "Fields are requested at listed times plus step end only, not at "
            "every adaptive substep; sparse displacements do not provide "
            "per-substep work history."
        ),
        step_scope=(
            "Separate gauge-free 0.025 s, 100 N reference-amplitude seating "
            "diagnostic. Integration endpoints are aligned with the sampled "
            "0.001 s ramp knots while retaining the 0.0025 s adaptive initial "
            "increment limit. This does not establish time accuracy, service "
            "response, capacity, or joint acceptance."
        ),
        derivative_operation=(
            "Output-schedule-only derivative of the frozen 100 N reference "
            "CLOAD child: preserve its 662 scaled CLOAD terms, original "
            "RAMP_N table, unit-load q weights, all physical inputs, and "
            "initial/adaptive step limits; add the named knot schedule and "
            "apply it to all 41 output requests."
        ),
        source_paths={
            **source_freeze["source_paths"],
            "timing-parent-input-freeze.json": repo_path(source_freeze_path),
            "time-point-review.md": repo_path(REVIEW),
            "timed-producer.py.snapshot": repo_path(Path(__file__)),
        },
        derivative_parent_artifact_sha256=dict(source_pins),
    )
    report["source_sha256"] = {
        **source_freeze["source_sha256"],
        "timing-parent-input-freeze.json": expected_source_freeze_sha256,
        "time-point-review.md": TIME_POINT_REVIEW_SHA256,
        "timed-producer.py.snapshot": sha(Path(__file__)),
    }
    report["artifacts_sha256"] = {
        name: sha(destination / name)
        for name in [*source_pins, "timing-parent-input-freeze.json", "timed-producer.py.snapshot"]
    }
    report["artifacts_sha256"]["pilot.inp"] = sha(destination / "pilot.inp")
    (destination / "input-freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    return {
        "input_freeze_sha256": sha(destination / "input-freeze.json"),
        "pilot_sha256": report["artifacts_sha256"]["pilot.inp"],
        "source_input_freeze_sha256": expected_source_freeze_sha256,
        "time_points": len(TIME_POINT_SECONDS),
        "output_cards": EXPECTED_OUTPUT_CARDS,
        "status": report["status"],
    }


if __name__ == "__main__":
    destination = BASE / "ordinary-transient-seating-100n-aligned-attempt01"
    print(json.dumps(prepare(destination), indent=2))
