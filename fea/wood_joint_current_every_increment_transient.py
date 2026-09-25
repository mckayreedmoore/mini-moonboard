"""Freeze an every-accepted-increment force-driven current-joint diagnostic.

The source load pattern, sampled ramp, unit-weight motion observer, contacts,
mesh, materials, and nut model are preserved. Only the adaptive time controls
and output cadence change. This producer does not run CalculiX.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from fea import wood_joint_current_timed_transient as timed
from fea.wood_joint_current_native_preflight import SOLVER_IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SOURCE = BASE / "ordinary-transient-seating-100n-aligned-k1e4-attempt01"
DESTINATION_NAME = "ordinary-transient-seating-100n-every-increment-k1e4-attempt01"
SOURCE_FREEZE_SHA256 = (
    "4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367"
)
TIMED_HELPER_SHA256 = "bc2be9d10f0ef8c2be53730ef228e5d09fe20ca5acd9efc7e64bdf372a676268"
EXPECTED_SOURCE_ARTIFACTS = 23
EXPECTED_CLOAD_ROWS = 662
EXPECTED_OUTPUT_CARDS = 41
EXPECTED_REFERENCE_SCALE_N = 100.0
EXPECTED_ENDPOINT_FORCE_N = 15.625
INITIAL_INCREMENT_SECONDS = 0.001
END_SECONDS = 0.025
MINIMUM_INCREMENT_SECONDS = 1e-6
MAXIMUM_INCREMENT_SECONDS = 0.001
STEP_INCREMENT_LIMIT = 10000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha256(Path(path).read_bytes())


def _keyword(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("*") and not stripped.startswith("**")


def _card_name(header: str) -> str:
    return header.lstrip()[1:].split(",", 1)[0].strip().upper()


def _card_options(header: str) -> dict[str, str | None]:
    options: dict[str, str | None] = {}
    for part in header.lstrip()[1:].split(",")[1:]:
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            options[key.strip().upper()] = value.strip().strip("\"'")
        elif part:
            options[part.upper()] = None
    return options


def _card_blocks(deck: str) -> list[tuple[int, int, str]]:
    lines = deck.splitlines()
    starts = [index for index, line in enumerate(lines) if _keyword(line)]
    result = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        result.append((start, end, lines[start]))
    return result


def _matching_card(deck: str, name: str, option: tuple[str, str] | None = None):
    lines = deck.splitlines()
    matches = []
    for start, end, header in _card_blocks(deck):
        if _card_name(header) != name.upper():
            continue
        if option is not None:
            key, value = option
            if _card_options(header).get(key.upper(), "").upper() != value.upper():
                continue
        matches.append((lines, start, end, header))
    if len(matches) != 1:
        raise ValueError(f"expected one {name} card, found {len(matches)}")
    return matches[0]


def _number(token: str) -> float:
    return float(token.strip().replace("D", "E").replace("d", "e"))


def _verify_source_load_and_ramp(deck: str, freeze: dict) -> None:
    lines, start, end, header = _matching_card(deck, "CLOAD")
    if header.strip().upper() != "*CLOAD,AMPLITUDE=RAMP_N":
        raise ValueError("source CLOAD card/options changed")
    rows = {}
    for line in lines[start + 1 : end]:
        content = line.strip()
        if not content or content.startswith("**"):
            continue
        fields = [field.strip() for field in content.split(",")]
        if len(fields) != 3:
            raise ValueError("source CLOAD row is malformed")
        node, dof, force = int(fields[0]), int(fields[1]), _number(fields[2])
        if dof not in (1, 2, 3) or (node, dof) in rows:
            raise ValueError("source CLOAD contains an invalid or duplicate DOF")
        rows[(node, dof)] = force
    if len(rows) != EXPECTED_CLOAD_ROWS:
        raise ValueError(f"expected {EXPECTED_CLOAD_ROWS} source CLOAD components")

    unit_nodes = freeze.get("serialized_unit_load_nodes", {})
    scale = float(freeze.get("cload_reference_scale", math.nan))
    if scale != EXPECTED_REFERENCE_SCALE_N:
        raise ValueError("source CLOAD scale is not the frozen 100 N reference pattern")
    expected = {
        (int(node), dof): float(force) * scale
        for node, record in unit_nodes.items()
        for dof, force in enumerate(record["force_xyz_n"], 1)
        if float(force) != 0.0
    }
    if rows.keys() != expected.keys():
        raise ValueError(
            "source CLOAD components differ from the frozen unit observation"
        )
    for key, force in expected.items():
        if not math.isclose(rows[key], force, rel_tol=1e-12, abs_tol=1e-10):
            raise ValueError(f"source CLOAD differs from unit-load weights at {key}")

    amplitude_lines, amp_start, amp_end, amp_header = _matching_card(
        deck, "AMPLITUDE", ("NAME", "RAMP_N")
    )
    if ",TIME=" in amp_header.upper():
        raise ValueError("source RAMP_N amplitude time basis changed")
    table = []
    for line in amplitude_lines[amp_start + 1 : amp_end]:
        fields = [field.strip() for field in line.split(",") if field.strip()]
        if len(fields) % 2:
            raise ValueError("source amplitude rows must contain time/value pairs")
        table.extend(
            (_number(fields[i]), _number(fields[i + 1]))
            for i in range(0, len(fields), 2)
        )
    endpoint_values = [
        value for time, value in table if math.isclose(time, END_SECONDS)
    ]
    if endpoint_values != [0.15625]:
        raise ValueError("source amplitude at 0.025 s must remain 0.15625")
    if not math.isclose(scale * endpoint_values[0], EXPECTED_ENDPOINT_FORCE_N):
        raise ValueError("source force endpoint is not 15.625 N per side")
    if not math.isclose(
        float(freeze.get("final_amplitude_n", math.nan)), EXPECTED_ENDPOINT_FORCE_N
    ):
        raise ValueError("source freeze does not record the true force endpoint")
    if not math.isclose(
        float(freeze.get("final_amplitude_table_factor", math.nan)), 0.15625
    ):
        raise ValueError("source freeze amplitude endpoint factor changed")


def _change_time_controls(deck: str) -> tuple[str, dict]:
    lines = deck.splitlines()
    step_cards = [
        index
        for index, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "STEP"
    ]
    dynamic_cards = [
        index
        for index, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "DYNAMIC"
    ]
    if len(step_cards) != 1 or len(dynamic_cards) != 1:
        raise ValueError("source pilot must contain one transient step")
    step_index, dynamic_index = step_cards[0], dynamic_cards[0]
    if dynamic_index != step_index + 1 or dynamic_index + 1 >= len(lines):
        raise ValueError("source *DYNAMIC must immediately follow its *STEP header")
    step_header = lines[step_index]
    dynamic_header = lines[dynamic_index]
    if "NLGEOM" not in step_header.upper() or "INC=" not in step_header.upper():
        raise ValueError("source step must retain NLGEOM and an increment limit")
    if "DIRECT" in dynamic_header.upper() or "EXPLICIT" in dynamic_header.upper():
        raise ValueError("source must remain adaptive implicit dynamics")
    if dynamic_header.strip().upper() != "*DYNAMIC,ALPHA=0":
        raise ValueError("source dynamic method is not alpha=0 implicit")
    old_values = [part.strip() for part in lines[dynamic_index + 1].split(",")]
    if len(old_values) != 4:
        raise ValueError("source dynamic line must have four time-control values")
    old_dt, old_end, old_minimum, old_maximum = map(_number, old_values)
    if not (
        math.isclose(old_dt, 0.0025)
        and math.isclose(old_end, END_SECONDS)
        and math.isclose(old_minimum, MINIMUM_INCREMENT_SECONDS)
        and math.isclose(old_maximum, 0.0025)
    ):
        raise ValueError("source time-control tuple changed from the frozen K1e4 case")
    new_header = re.sub(
        r"\bINC\s*=\s*\d+",
        f"INC={STEP_INCREMENT_LIMIT}",
        step_header,
        flags=re.IGNORECASE,
    )
    if new_header == step_header:
        raise ValueError("source increment limit could not be updated")
    new_dynamic_values = (
        f"{INITIAL_INCREMENT_SECONDS:g},{END_SECONDS:g},"
        f"{MINIMUM_INCREMENT_SECONDS:g},{MAXIMUM_INCREMENT_SECONDS:g}"
    )
    lines[step_index] = new_header
    lines[dynamic_index + 1] = new_dynamic_values
    modified = "\n".join(lines) + "\n"
    controls = {
        "old_step_increment_limit": int(
            re.search(r"\bINC\s*=\s*(\d+)", step_header, re.IGNORECASE).group(1)
        ),
        "new_step_increment_limit": STEP_INCREMENT_LIMIT,
        "old_dynamic_values_seconds": [old_dt, old_end, old_minimum, old_maximum],
        "new_dynamic_values_seconds": [
            INITIAL_INCREMENT_SECONDS,
            END_SECONDS,
            MINIMUM_INCREMENT_SECONDS,
            MAXIMUM_INCREMENT_SECONDS,
        ],
        "dynamic_header": dynamic_header,
        "adaptive_implicit_alpha0": True,
    }
    changed = [
        (index, before, after)
        for index, (before, after) in enumerate(
            zip(deck.splitlines(), lines, strict=True)
        )
        if before != after
    ]
    if len(changed) != 2 or {changed[0][0], changed[1][0]} != {
        step_index,
        dynamic_index + 1,
    }:
        raise ValueError("normalized deck differs outside *STEP/*DYNAMIC time controls")
    controls["changed_line_count"] = len(changed)
    controls["changed_lines"] = [
        {"line_number": index + 1, "before": before, "after": after}
        for index, before, after in changed
    ]
    return modified, controls


def _output_cards(deck: str) -> list[str]:
    names = {"NODE FILE", "NODE PRINT", "EL PRINT", "CONTACT FILE", "CONTACT PRINT"}
    return [
        header
        for _start, _end, header in _card_blocks(deck)
        if _card_name(header) in names
    ]


def _verify_every_increment_outputs(deck: str) -> list[str]:
    cards = _output_cards(deck)
    if len(cards) != EXPECTED_OUTPUT_CARDS:
        raise ValueError(
            f"expected {EXPECTED_OUTPUT_CARDS} output cards, found {len(cards)}"
        )
    if any("FREQUENCY=1" not in card.upper() for card in cards):
        raise ValueError("every output card must request every accepted increment")
    if any("TIME POINTS=" in card.upper() for card in cards):
        raise ValueError("TIME POINTS output schedule remains in derivative")
    if any(
        line.lstrip().upper().startswith("*TIME POINTS") for line in deck.splitlines()
    ):
        raise ValueError("TIME POINTS card remains in derivative")
    return cards


def prepare(
    destination: str | Path,
    *,
    source_dir: str | Path = SOURCE,
) -> dict:
    """Create a fresh, source-pinned every-increment diagnostic input folder."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(f"destination must be fresh: {destination}")
    source = Path(source_dir).resolve()
    source_freeze_path = source / "input-freeze.json"
    if (
        not source_freeze_path.is_file()
        or sha(source_freeze_path) != SOURCE_FREEZE_SHA256
    ):
        raise ValueError("unexpected current K1e4 source input freeze")
    source_freeze_bytes = source_freeze_path.read_bytes()
    source_freeze = json.loads(source_freeze_bytes)
    if source_freeze.get("schema") != "wood_joint_current_transient/v1":
        raise ValueError("unsupported current transient source freeze")
    if source_freeze.get("solver_image") != SOLVER_IMAGE:
        raise ValueError("source is not tied to the pinned CalculiX 2.21 image")
    if source_freeze.get("status") != "FROZEN_NOT_EXECUTED":
        raise ValueError("source must remain a frozen diagnostic input")
    source_pins = source_freeze.get("artifacts_sha256", {})
    if len(source_pins) != EXPECTED_SOURCE_ARTIFACTS:
        raise ValueError("unexpected source artifact count")
    source_artifacts: dict[str, bytes] = {}
    for name, expected in source_pins.items():
        path = source / name
        if not path.is_file():
            raise ValueError(f"missing frozen source artifact: {name}")
        data = path.read_bytes()
        if sha256(data) != expected:
            raise ValueError(f"source artifact pin mismatch: {name}")
        source_artifacts[name] = data

    timed_helper_path = Path(timed.__file__).resolve()
    timed_helper_bytes = timed_helper_path.read_bytes()
    if sha256(timed_helper_bytes) != TIMED_HELPER_SHA256:
        raise ValueError("timed deck normalization helper changed")
    if source_pins.get("timed-producer.py.snapshot") != TIMED_HELPER_SHA256:
        raise ValueError("source freeze does not pin the timed normalization helper")
    if source_artifacts["timed-producer.py.snapshot"] != timed_helper_bytes:
        raise ValueError("source helper snapshot differs from current timed helper")

    source_deck = source_artifacts["pilot.inp"].decode("utf-8")
    _verify_source_load_and_ramp(source_deck, source_freeze)
    normalized_deck = timed.normalize_timed_deck(source_deck)
    normalized_hash = sha256(normalized_deck.encode())
    prior_timepoint_freeze = json.loads(
        source_artifacts["timing-parent-input-freeze.json"]
    )
    expected_normalized_hash = prior_timepoint_freeze.get("artifacts_sha256", {}).get(
        "pilot.inp"
    )
    if not expected_normalized_hash or normalized_hash != expected_normalized_hash:
        raise ValueError(
            "inverse-normalized deck differs from the pinned pre-timepoint pilot"
        )
    if sha256(source_artifacts["timing-parent-input-freeze.json"]) != source_freeze.get(
        "timing_parent_input_freeze_sha256"
    ):
        raise ValueError("prior timepoint parent freeze does not match source lineage")

    deck, time_control_delta = _change_time_controls(normalized_deck)
    output_cards = _verify_every_increment_outputs(deck)
    _verify_source_load_and_ramp(deck, source_freeze)
    if "TIME POINTS" in deck.upper() or "*EXPLICIT" in deck.upper():
        raise ValueError("forbidden timepoint or explicit-mode card in derivative")

    current_producer_bytes = Path(__file__).read_bytes()
    destination.mkdir(parents=True, exist_ok=False)

    files: dict[str, bytes] = {}
    for name, data in source_artifacts.items():
        if name == "pilot.inp":
            files["source-pilot.inp"] = data
        else:
            files[name] = data
    files["pilot.inp"] = deck.encode()
    files["source-input-freeze.json"] = source_freeze_bytes
    files["every-increment-producer.py.snapshot"] = current_producer_bytes
    files["every-increment-timed-helper.py.snapshot"] = timed_helper_bytes

    for name, data in files.items():
        (destination / name).write_bytes(data)
    if sha(source_freeze_path) != SOURCE_FREEZE_SHA256 or not all(
        sha(source / name) == digest for name, digest in source_pins.items()
    ):
        raise ValueError(
            "source freeze or artifacts changed during derivative creation"
        )
    for name, expected in source_pins.items():
        copied_name = "source-pilot.inp" if name == "pilot.inp" else name
        if sha(destination / copied_name) != expected:
            raise ValueError(f"copied source artifact differs from source pin: {name}")

    report = dict(source_freeze)
    for key in (
        "timing_parent_input_freeze_sha256",
        "time_point_review_sha256",
        "time_points_name",
        "time_points_step_seconds",
    ):
        report.pop(key, None)
    report.update(
        status="FROZEN_NOT_EXECUTED",
        initial_increment_seconds=INITIAL_INCREMENT_SECONDS,
        direct_fixed_increment=False,
        maximum_increment_seconds=MAXIMUM_INCREMENT_SECONDS,
        minimum_increment_seconds=MINIMUM_INCREMENT_SECONDS,
        end_seconds=END_SECONDS,
        hht_alpha=0,
        output_request_card_count=EXPECTED_OUTPUT_CARDS,
        output_schedule=(
            "All 41 NODE FILE, NODE PRINT, EL PRINT, CONTACT FILE, and CONTACT PRINT "
            "requests use FREQUENCY=1 at every accepted increment."
        ),
        output_scope_limit=(
            "Every accepted increment is emitted for motion, contact, and energy outputs. "
            "This supports discrete impulse/work/time audits, not a time-accuracy claim."
        ),
        step_scope=(
            "Separate gauge-free 0.025 s force-driven seating diagnostic on the frozen "
            "K1e4 current model. It preserves the 662 CLOAD terms scaled to a 100 N "
            "reference pattern and the source RAMP_N table, whose force endpoint at "
            "0.025 s is 15.625 N per side. Adaptive increments start and max at 0.001 s, "
            "with a 1e-6 s minimum and 10000 increment limit. Accepted increments may "
            "cross ramp knots after cutbacks; no time accuracy or joint acceptance is claimed."
        ),
        derivative_operation=(
            "Inverse-normalize the prior TIME POINTS derivative and verify the result "
            "matches its pinned pre-timepoint pilot; preserve all force, amplitude, "
            "unit-weight monitor, stop, mesh, contact, material, and nut inputs. Change "
            "only the adaptive initial/max increment to 0.001 s, retain the 0.025 s end "
            "and 1e-6 s minimum, raise STEP INC to 10000, and request all existing output "
            "cards every accepted increment."
        ),
        source_input_freeze_sha256=SOURCE_FREEZE_SHA256,
        inverse_normalized_pilot_sha256=normalized_hash,
        inverse_normalized_pilot_expected_sha256=expected_normalized_hash,
        source_pilot_preserved_as="source-pilot.inp",
        time_control_delta=time_control_delta,
        every_increment_output_cards=len(output_cards),
        output_frequency_every_accepted_increment=1,
        ramp_knot_alignment_after_adaptive_cutbacks="not guaranteed; time resolution remains unqualified",
        force_endpoint_n_per_side=EXPECTED_ENDPOINT_FORCE_N,
        force_reference_scale_n=EXPECTED_REFERENCE_SCALE_N,
        mechanical_acceptance=False,
        native_solve_run=False,
    )
    report["source_paths"] = {
        **source_freeze.get("source_paths", {}),
        "source-input-freeze.json": str(source_freeze_path),
        "source-pilot.inp": str(source / "pilot.inp"),
        "every-increment-producer.py.snapshot": str(Path(__file__).resolve()),
        "every-increment-timed-helper.py.snapshot": str(timed_helper_path),
    }
    report["source_sha256"] = {
        **source_freeze.get("source_sha256", {}),
        "source-input-freeze.json": SOURCE_FREEZE_SHA256,
        "source-pilot.inp": source_pins["pilot.inp"],
        "every-increment-producer.py.snapshot": sha256(current_producer_bytes),
        "every-increment-timed-helper.py.snapshot": TIMED_HELPER_SHA256,
    }
    report["derivative_parent_artifact_sha256"] = dict(source_pins)
    report["artifacts_sha256"] = {
        name: sha256(data) for name, data in sorted(files.items())
    }
    (destination / "input-freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    report["input_freeze_sha256"] = sha(destination / "input-freeze.json")
    return report


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--source-dir", type=Path, default=SOURCE)
    args = parser.parse_args()
    report = prepare(args.destination, source_dir=args.source_dir)
    print(
        json.dumps(
            {
                "destination": str(args.destination.resolve()),
                "input_freeze_sha256": report["input_freeze_sha256"],
                "pilot_sha256": report["artifacts_sha256"]["pilot.inp"],
                "source_input_freeze_sha256": report["source_input_freeze_sha256"],
                "output_cards": report["output_request_card_count"],
                "status": report["status"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
