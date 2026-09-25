"""Build an input-only finite-spring actuator derivative of a frozen pilot.

The source CLOAD pattern defines the relative coordinate. A massless dependent
proxy follows that coordinate through an MPC, while a separate prescribed
target drives a finite SPRING2 element. This producer does not run CalculiX.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from fea.wood_joint_current_native_preflight import SOLVER_IMAGE

SCHEMA = "wood_joint_current_spring_actuator_input/v1"
EXPECTED_SOURCE_SCHEMA = "wood_joint_current_transient/v1"
PROXY_NODE = 117162
TARGET_NODE = 117163
DRIVER_SET = "ACTUATOR_DRIVER"
DRIVER_SPRING_SET = "ACTUATOR_SPRING"
SPRING_TYPE = "SPRING2"
MPC_COEFFICIENT_WIDTH = 20
SOURCE_INCLUDE_FILES = (
    "mesh.inp",
    "materials.inp",
    "nut-coupling.inp",
    "rigid-carriers.inp",
    "contact-fragment.inc",
    "output-sets.inp",
    "pilot-sets.inp",
)


@dataclass(frozen=True)
class PreparedInput:
    """Frozen input files and metadata ready for an isolated output folder."""

    files: dict[str, bytes]
    pilot_text: str
    driver: dict
    freeze: dict


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finite_positive(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a finite positive number")
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a finite positive number")
    return value


def _integer_ratio(numerator: float, denominator: float, label: str) -> int:
    ratio = numerator / denominator
    nearest = round(ratio)
    if nearest < 1 or not math.isclose(ratio, nearest, rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"{label} must be an integer multiple of the time increment")
    return nearest


def _float(text: str) -> float:
    return float(text.strip().replace("D", "E").replace("d", "e"))


def _keyword(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("*") and not stripped.startswith("**")


def _card_name(header: str) -> str:
    return header.lstrip()[1:].split(",", 1)[0].strip().upper()


def _card_blocks(text: str) -> list[tuple[int, int, str]]:
    """Return (header-line, end-exclusive, header) for keyword cards."""
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if _keyword(line)]
    blocks = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        blocks.append((start, end, lines[start]))
    return blocks


def _card_options(header: str) -> dict[str, str | None]:
    parts = [part.strip() for part in header.lstrip()[1:].split(",")]
    options: dict[str, str | None] = {}
    for part in parts[1:]:
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            options[key.strip().upper()] = value.strip().strip("\"'")
        else:
            options[part.upper()] = None
    return options


def _include_names(text: str) -> list[str]:
    names = []
    for _start, _end, header in _card_blocks(text):
        if _card_name(header) != "INCLUDE":
            continue
        match = re.search(r"(?:^|,)\s*INPUT\s*=\s*([^,\s]+)", header, re.IGNORECASE)
        if match is None:
            raise ValueError("source include lacks an INPUT filename")
        name = match.group(1).strip("\"'")
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("source include must stay inside the frozen input folder")
        names.append(name)
    return names


def _resolve_includes(base_dir: Path, pilot: str) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    pending = list(_include_names(pilot))
    while pending:
        name = pending.pop(0)
        if name in result:
            continue
        path = base_dir / name
        if not path.is_file():
            raise ValueError(f"missing frozen solver include: {name}")
        data = path.read_bytes()
        result[name] = data
        try:
            nested = _include_names(data.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError(f"non-UTF-8 solver include: {name}") from exc
        pending.extend(nested)
    return result


def _node_and_element_ids(files: dict[str, bytes]) -> tuple[set[int], int]:
    node_ids: set[int] = set()
    maximum_element = 0
    for filename, data in files.items():
        text = data.decode("utf-8")
        lines = text.splitlines()
        for start, end, header in _card_blocks(text):
            name = _card_name(header)
            if name not in {"NODE", "ELEMENT"}:
                continue
            options = _card_options(header)
            generated = "GENERATE" in options
            for line in lines[start + 1 : end]:
                stripped = line.strip()
                if not stripped or stripped.startswith("**"):
                    continue
                fields = [field.strip() for field in stripped.split(",")]
                try:
                    labels = [int(fields[0])]
                except (ValueError, IndexError) as exc:
                    raise ValueError(f"invalid {name} label in {filename}") from exc
                if name == "NODE":
                    node_ids.add(labels[0])
                else:
                    if generated:
                        if len(fields) < 3:
                            raise ValueError(
                                f"invalid generated element range in {filename}"
                            )
                        first, last, increment = map(int, fields[:3])
                        if increment == 0:
                            raise ValueError(
                                f"invalid generated element increment in {filename}"
                            )
                        maximum_element = max(maximum_element, first, last)
                    else:
                        maximum_element = max(maximum_element, labels[0])
    if maximum_element == 0 or not node_ids:
        raise ValueError("source mesh has no labeled nodes or elements")
    return node_ids, maximum_element


def _source_unit_terms(actuator: dict) -> list[tuple[int, int, float]]:
    equation = actuator.get("equation", {})
    raw = equation.get("physical_terms_before_normalization")
    if equation.get("term_count") != len(raw or []) + 1 or not raw:
        raise ValueError("source actuator term count is inconsistent")
    terms = []
    seen = set()
    for row in raw:
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError("source actuator term is malformed")
        node, dof, weight = int(row[0]), int(row[1]), float(row[2])
        if (
            node <= 0
            or dof not in range(1, 7)
            or not math.isfinite(weight)
            or weight == 0.0
        ):
            raise ValueError("source actuator term is invalid")
        if (node, dof) in seen:
            raise ValueError("source actuator contains a duplicate physical DOF")
        seen.add((node, dof))
        terms.append((node, dof, weight))
    return terms


def _parse_cload(pilot: str) -> tuple[dict[tuple[int, int], float], int]:
    lines = pilot.splitlines()
    cards = []
    for start, end, header in _card_blocks(pilot):
        if _card_name(header) != "CLOAD":
            continue
        options = _card_options(header)
        cards.append((start, end, options, lines[start + 1 : end]))
    if len(cards) != 1 or cards[0][2].get("AMPLITUDE", "").upper() != "RAMP_N":
        raise ValueError("source pilot must contain exactly one RAMP_N CLOAD card")
    loads: dict[tuple[int, int], float] = {}
    rows = 0
    for line in cards[0][3]:
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        fields = [field.strip() for field in stripped.split(",")]
        if len(fields) != 3:
            raise ValueError("source CLOAD row must have node, DOF, and force")
        node, dof = int(fields[0]), int(fields[1])
        key = (node, dof)
        if key in loads:
            raise ValueError("source CLOAD contains a duplicate physical DOF")
        loads[key] = _float(fields[2])
        rows += 1
    return loads, rows


def _numeric_token(value: float) -> str:
    result = format(value, ".15g")
    if "e" not in result.lower() and "." not in result:
        result += ".0"
    return result


def _spring_token(value: float) -> str:
    """CalculiX 2.21 re-reads an integer-only spring value as a DOF field."""
    result = _numeric_token(value)
    if "." not in result:
        mantissa, exponent = result.split("e", 1)
        result = f"{mantissa}.0e{exponent}"
    if len(result) > 20:
        raise ValueError("serialized spring stiffness exceeds 20 characters")
    return result


def _mpc_token(value: float) -> str:
    result = f"{value:.16f}"
    if len(result) > MPC_COEFFICIENT_WIDTH:
        raise ValueError(f"serialized MPC coefficient exceeds 20 characters: {result}")
    return result


def _format_time(value: float) -> str:
    return format(value, ".15g")


def _history_rows(ramp: float, end: float, dt: float) -> list[tuple[float, float]]:
    ramp_steps = _integer_ratio(ramp, dt, "ramp duration")
    end_steps = _integer_ratio(end, dt, "end time")
    rows = []
    for index in range(ramp_steps + 1):
        fraction = index / ramp_steps
        # Quintic smoothstep; native *AMPLITUDE interpolation remains linear.
        value = fraction**3 * (10.0 - 15.0 * fraction + 6.0 * fraction**2)
        rows.append((index * dt, value))
    if end_steps > ramp_steps:
        rows.append((end, 1.0))
    return rows


def _remove_card(lines: list[str], header_matches) -> tuple[list[str], list[str]]:
    result = []
    removed_headers = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _keyword(line) and header_matches(line):
            removed_headers.append(line)
            index += 1
            while index < len(lines) and not _keyword(lines[index]):
                index += 1
            continue
        result.append(line)
        index += 1
    return result, removed_headers


def _replace_time_points(lines: list[str], frequency: int) -> tuple[list[str], int]:
    result = []
    count = 0
    for line in lines:
        if _keyword(line) and re.search(
            r"\bTIME\s+POINTS\s*=\s*RAMP_KNOTS\b", line, re.IGNORECASE
        ):
            line = re.sub(
                r"\bTIME\s+POINTS\s*=\s*RAMP_KNOTS\b",
                f"FREQUENCY={frequency}",
                line,
                flags=re.IGNORECASE,
            )
            count += 1
        result.append(line)
    return result, count


def _extend_driver_nodes_in_pilot_set(data: bytes) -> bytes:
    """Extend the single FRD output set while preserving every physical label."""
    text = data.decode("utf-8")
    lines = text.splitlines()
    blocks = [
        (start, end)
        for start, end, header in _card_blocks(text)
        if _card_name(header) == "NSET"
        and _card_options(header).get("NSET", "").upper() == "PILOT_ALL_NODES"
    ]
    if len(blocks) != 1:
        raise ValueError("source pilot-sets must define PILOT_ALL_NODES exactly once")
    start, end = blocks[0]
    members = set()
    for line in lines[start + 1 : end]:
        for field in line.split(","):
            field = field.strip()
            if field and field.lstrip("+-").isdigit():
                members.add(int(field))
    if PROXY_NODE in members or TARGET_NODE in members:
        raise ValueError("driver node already appears in PILOT_ALL_NODES")
    lines.insert(end, f"{PROXY_NODE},{TARGET_NODE}")
    return ("\n".join(lines) + "\n").encode()


def _render_equation(terms: list[tuple[int, int, float]]) -> str:
    rows = [(PROXY_NODE, 1, 1.0)] + [
        (node, dof, -weight) for node, dof, weight in terms
    ]
    lines = ["*EQUATION", str(len(rows))]
    for start in range(0, len(rows), 4):
        lines.append(
            ",".join(
                f"{node},{dof},{_mpc_token(coefficient)}"
                for node, dof, coefficient in rows[start : start + 4]
            )
        )
    return "\n".join(lines)


def _build_pilot(
    source_pilot: str,
    terms: list[tuple[int, int, float]],
    spring_element: int,
    stiffness: float,
    target_max: float,
    ramp: float,
    end: float,
    dt: float,
    minimum_dt: float,
    output_frequency: int,
) -> tuple[str, int, int]:
    lines = source_pilot.splitlines()
    lines, amplitudes = _remove_card(
        lines,
        lambda header: (
            _card_name(header) == "AMPLITUDE"
            and _card_options(header).get("NAME", "").upper() == "RAMP_N"
        ),
    )
    lines, time_points = _remove_card(
        lines,
        lambda header: (
            _card_name(header) == "TIME POINTS"
            and _card_options(header).get("NAME", "").upper() == "RAMP_KNOTS"
        ),
    )
    lines, cloads = _remove_card(
        lines,
        lambda header: (
            _card_name(header) == "CLOAD"
            and _card_options(header).get("AMPLITUDE", "").upper() == "RAMP_N"
        ),
    )
    if len(amplitudes) != 1 or len(time_points) != 1 or len(cloads) != 1:
        raise ValueError("source load and output schedules were not unique")

    lines, replaced_outputs = _replace_time_points(lines, output_frequency)
    if replaced_outputs == 0:
        raise ValueError("source output schedule has no RAMP_KNOTS requests")
    node_file_indexes = [
        index
        for index, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "NODE FILE"
    ]
    if len(node_file_indexes) != 1:
        raise ValueError(
            "source must have one NODE FILE request for the physical/driver union"
        )
    node_file_index = node_file_indexes[0]
    if (
        _card_options(lines[node_file_index]).get("NSET", "").upper()
        != "PILOT_ALL_NODES"
    ):
        raise ValueError("source NODE FILE must request the PILOT_ALL_NODES union")
    options = [
        option
        for option in lines[node_file_index].split(",")
        if not option.strip().upper().startswith("FREQUENCY=")
    ]
    lines[node_file_index] = ",".join(options) + ",FREQUENCY=1"
    if lines[node_file_index + 1].strip().upper() != "U,V":
        raise ValueError("source physical NODE FILE must request U,V")
    lines[node_file_index + 1] = "U,V,RF"

    step_indexes = [
        i
        for i, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "STEP"
    ]
    dynamic_indexes = [
        i
        for i, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "DYNAMIC"
    ]
    end_indexes = [
        i
        for i, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "END STEP"
    ]
    if len(step_indexes) != 1 or len(dynamic_indexes) != 1 or len(end_indexes) != 1:
        raise ValueError("source pilot must have one transient step")
    if dynamic_indexes[0] != step_indexes[0] + 1:
        raise ValueError("source dynamic card must immediately follow the step card")

    _integer_ratio(end, dt, "end time")
    if output_frequency != 1:
        raise ValueError("all CalculiX output cards must share FREQUENCY=1")

    step_header = lines[step_indexes[0]]
    if not re.search(r"\bNLGEOM\b", step_header, re.IGNORECASE):
        raise ValueError("source transient must retain NLGEOM")
    if not re.search(r"\bINC\s*=\s*\d+", step_header, re.IGNORECASE):
        raise ValueError("source step lacks an increment limit")
    step_increment_limit = 10000
    lines[step_indexes[0]] = re.sub(
        r"\bINC\s*=\s*\d+",
        f"INC={step_increment_limit}",
        step_header,
        flags=re.IGNORECASE,
    )
    lines[dynamic_indexes[0]] = "*DYNAMIC,ALPHA=0"
    del lines[dynamic_indexes[0] + 1]
    dynamic_values = (
        f"{_format_time(dt)},{_format_time(end)},"
        f"{_format_time(minimum_dt)},{_format_time(dt)}"
    )
    lines.insert(dynamic_indexes[0] + 1, dynamic_values)

    step_index = next(
        i
        for i, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "STEP"
    )
    model_cards = [
        "** Massless finite-spring actuator controls; target history is sampled quintic smoothstep.",
        "*NODE",
        f"{PROXY_NODE},0,1,0",
        f"{TARGET_NODE},0,2,0",
        f"*ELEMENT,TYPE={SPRING_TYPE},ELSET={DRIVER_SPRING_SET}",
        f"{spring_element},{PROXY_NODE},{TARGET_NODE}",
        f"*SPRING,ELSET={DRIVER_SPRING_SET}",
        "1,1",
        _spring_token(stiffness),
        f"*NSET,NSET={DRIVER_SET}",
        f"{PROXY_NODE},{TARGET_NODE}",
        _render_equation(terms),
        "*AMPLITUDE,NAME=Q_TARGET_HISTORY",
    ]
    for time, amplitude in _history_rows(ramp, end, dt):
        model_cards.append(f"{_format_time(time)},{_format_time(amplitude)}")
    lines[step_index:step_index] = model_cards

    dynamic_index = next(
        i
        for i, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "DYNAMIC"
    )
    lines[dynamic_index + 2 : dynamic_index + 2] = [
        "*BOUNDARY",
        f"{PROXY_NODE},2,3,0",
        f"{TARGET_NODE},2,3,0",
        "*BOUNDARY,AMPLITUDE=Q_TARGET_HISTORY",
        f"{TARGET_NODE},1,1,{_numeric_token(target_max)}",
    ]

    end_step_index = next(
        i
        for i, line in enumerate(lines)
        if _keyword(line) and _card_name(line) == "END STEP"
    )
    driver_output = [f"*NODE PRINT,NSET={DRIVER_SET},FREQUENCY=1", "U,RF"]
    lines[end_step_index:end_step_index] = driver_output

    rendered = "\n".join(lines) + "\n"
    upper = rendered.upper()
    if "RAMP_N" in upper or "RAMP_KNOTS" in upper or "*CLOAD" in upper:
        raise ValueError("legacy CLOAD/amplitude/output schedule remains in derivative")
    if "EXPLICIT" in upper or "TIME=STEP TIME" in upper:
        raise ValueError(
            "dynamic or amplitude card includes a forbidden implicit default"
        )
    if upper.count("*EQUATION") != 1 or upper.count("*SPRING,") != 1:
        raise ValueError("derivative must contain exactly one actuator MPC and spring")
    if upper.count("*BOUNDARY") != 2:
        raise ValueError("unexpected boundary cards in source or derivative")
    if "TIME POINTS=" in upper:
        raise ValueError("shared CalculiX output schedule must not mix TIME POINTS")
    if upper.count("*NODE FILE") != 1:
        raise ValueError(
            "driver and physical FRD fields must share one union NODE FILE"
        )
    if "*NODE FILE,NSET=PILOT_ALL_NODES" not in upper or "U,V,RF" not in upper:
        raise ValueError("union NODE FILE must retain physical U,V and add driver RF")
    return rendered, replaced_outputs, step_increment_limit


def build_current_spring_actuator(
    base_dir: str | Path,
    *,
    actuator_stiffness_n_per_mm: float,
    q_target_max_mm: float,
    ramp_seconds: float,
    end_seconds: float,
    time_increment_seconds: float,
    output_interval_seconds: float,
) -> PreparedInput:
    """Prepare a derivative from a pinned K1e4 or K1e5 source folder.

    Every numerical driver choice is required explicitly. The returned bundle
    is input-only and has not been submitted to a solver.
    """
    base = Path(base_dir).resolve()
    if not base.is_dir():
        raise ValueError("base_dir must name an existing frozen source folder")
    stiffness = _finite_positive(actuator_stiffness_n_per_mm, "actuator stiffness")
    target_max = _finite_positive(q_target_max_mm, "target displacement")
    ramp = _finite_positive(ramp_seconds, "ramp duration")
    end = _finite_positive(end_seconds, "end time")
    dt = _finite_positive(time_increment_seconds, "time increment")
    output_interval = _finite_positive(output_interval_seconds, "output interval")
    if end < ramp:
        raise ValueError("end time must be at least the target ramp duration")
    _integer_ratio(ramp, dt, "ramp duration")
    _integer_ratio(end, dt, "end time")
    output_every = _integer_ratio(output_interval, dt, "output interval")
    _integer_ratio(end, output_interval, "end/output interval")
    if output_every != 1:
        raise ValueError(
            "the pinned solver shares one output cadence; output interval must equal dt"
        )

    source_freeze_path = base / "input-freeze.json"
    source_actuator_path = base / "actuator.json"
    source_pilot_path = base / "pilot.inp"
    if not all(
        path.is_file()
        for path in (source_freeze_path, source_actuator_path, source_pilot_path)
    ):
        raise ValueError(
            "source folder must contain input-freeze.json, actuator.json, and pilot.inp"
        )
    source_freeze_bytes = source_freeze_path.read_bytes()
    source_freeze = json.loads(source_freeze_bytes)
    if source_freeze.get("schema") != EXPECTED_SOURCE_SCHEMA:
        raise ValueError("unsupported source transient freeze schema")
    if source_freeze.get("solver_image") != SOLVER_IMAGE:
        raise ValueError("source solver image is not the pinned CalculiX 2.21 image")
    source_artifact_pins = source_freeze.get("artifacts_sha256", {})
    source_hash_pins = source_freeze.get("source_sha256", {})
    if not source_hash_pins and not source_artifact_pins:
        raise ValueError("source freeze lacks source artifact hashes")
    actual_source_hashes = {}
    for name in sorted(set(source_hash_pins) | set(source_artifact_pins)):
        expected_hash = source_artifact_pins.get(name, source_hash_pins.get(name))
        if expected_hash is None:
            raise ValueError(f"source freeze lacks a hash for {name}")
        path = base / name
        if not path.is_file() or _sha256(path.read_bytes()) != expected_hash:
            raise ValueError(f"frozen source artifact changed or missing: {name}")
        actual_source_hashes[name] = expected_hash
    old_actuator_bytes = source_actuator_path.read_bytes()
    if actual_source_hashes.get("actuator.json") != _sha256(old_actuator_bytes):
        raise ValueError("source actuator is not bound by the current input freeze")
    actuator = json.loads(old_actuator_bytes)
    if actuator.get("schema") != "wood_joint_current_seating_actuator/v1":
        raise ValueError("unsupported source actuator reference schema")
    terms = _source_unit_terms(actuator)

    pilot_bytes = source_pilot_path.read_bytes()
    source_pilot = pilot_bytes.decode("utf-8")
    includes = _resolve_includes(base, source_pilot)
    node_ids, maximum_element = _node_and_element_ids(includes)
    for control_node in (PROXY_NODE, TARGET_NODE):
        if control_node in node_ids:
            raise ValueError(
                f"driver node {control_node} collides with a physical node"
            )
    if any(
        re.search(rf"\b{node}\b", data.decode("utf-8"))
        for node in (PROXY_NODE, TARGET_NODE)
        for data in includes.values()
    ):
        raise ValueError("driver node label appears in a source include")
    if DRIVER_SET in source_pilot.upper() or DRIVER_SPRING_SET in source_pilot.upper():
        raise ValueError("driver set names already exist in source pilot")
    for data in includes.values():
        text = data.decode("utf-8")
        if any(
            _card_name(header) == "BOUNDARY" for _a, _b, header in _card_blocks(text)
        ):
            raise ValueError("source include contains a boundary condition")
        if any(_card_name(header) == "CLOAD" for _a, _b, header in _card_blocks(text)):
            raise ValueError("source include contains an additional concentrated load")
    for name, data in includes.items():
        if actual_source_hashes.get(name) != _sha256(data):
            raise ValueError(
                f"solver include is not bound by the source freeze: {name}"
            )

    source_cloads, source_cload_rows = _parse_cload(source_pilot)
    scale = float(source_freeze.get("cload_reference_scale", 0.0))
    if scale <= 0.0 or not math.isfinite(scale):
        raise ValueError("source CLOAD reference scale is missing or invalid")
    term_map = {(node, dof): weight for node, dof, weight in terms}
    if set(source_cloads) != set(term_map) or source_cload_rows != len(terms):
        raise ValueError("source CLOAD components do not match actuator unit terms")
    for key, weight in term_map.items():
        if not math.isclose(
            source_cloads[key], scale * weight, rel_tol=1e-10, abs_tol=1e-10
        ):
            raise ValueError(
                f"source CLOAD differs from its unit-weight reference at {key}"
            )
    expected_old_cloads = source_freeze.get("cload_reference_force_n")
    if expected_old_cloads is not None and not math.isclose(
        float(expected_old_cloads), scale
    ):
        raise ValueError("source CLOAD scale and force metadata disagree")

    minimum_dt = _finite_positive(
        source_freeze.get("minimum_increment_seconds"),
        "source adaptive minimum increment",
    )
    if minimum_dt > dt:
        raise ValueError(
            "source adaptive minimum increment exceeds requested initial dt"
        )

    pilot, output_cards, steps = _build_pilot(
        source_pilot,
        terms,
        maximum_element + 1,
        stiffness,
        target_max,
        ramp,
        end,
        dt,
        minimum_dt,
        output_every,
    )
    source_terms_bytes = json.dumps(terms, separators=(",", ":")).encode()
    equation_bytes = _render_equation(terms).encode()
    producer_snapshot = Path(__file__).read_bytes()
    driver = {
        "schema": "wood_joint_current_spring_actuator_driving/v1",
        "status": "INPUT_ONLY_NOT_SOLVED",
        "driver_method": "massless_mpc_proxy_to_prescribed_target_finite_spring",
        "solver_image": SOLVER_IMAGE,
        "source_lineage": {
            "base_dir": str(base),
            "source_input_freeze_sha256": _sha256(source_freeze_bytes),
            "source_actuator_reference_sha256": _sha256(old_actuator_bytes),
            "source_pilot_sha256": _sha256(pilot_bytes),
            "source_artifacts_sha256": actual_source_hashes,
            "source_actuator_status_reference_only": actuator.get("status"),
            "producer_snapshot_sha256": _sha256(producer_snapshot),
        },
        "source_unit_pattern": {
            "terms_count": len(terms),
            "terms_sha256": _sha256(source_terms_bytes),
            "equation_sha256": _sha256(equation_bytes),
            "mpc_coefficient_format": "16 digits after decimal, <=20 characters",
            "mpc_coefficient_max_rounding_error": max(
                abs(weight - float(_mpc_token(-weight)))
                for _node, _dof, weight in terms
            ),
            "source_reference_load_scale_n": scale,
            "source_reference_only": True,
            "equation_convention": "q_proxy - sum(unit_weight_i * u_i) = 0",
        },
        "driver_nodes": {
            "set": DRIVER_SET,
            "proxy_node": PROXY_NODE,
            "target_node": TARGET_NODE,
            "proxy_is_first_dependent_mpc_term": True,
            "target_is_outside_mpc": True,
            "unused_dofs_constrained": [2, 3],
        },
        "actuator_spring": {
            "element_id": maximum_element + 1,
            "element_type": SPRING_TYPE,
            "element_set": DRIVER_SPRING_SET,
            "stiffness_n_per_mm": stiffness,
            "spring_data_token": _spring_token(stiffness),
        },
        "target_history": {
            "target_max_mm": target_max,
            "ramp_seconds": ramp,
            "end_seconds": end,
            "sample_increment_seconds": dt,
            "sample_count": len(_history_rows(ramp, end, dt)),
            "sample_function": "quintic smoothstep x^3*(10-15*x+6*x^2), x=t/ramp",
            "native_interpolation": "piecewise linear between explicit amplitude samples",
            "time_basis": "step time; no TIME=STEP TIME option is serialized",
        },
        "time_discretization": {
            "method": "implicit adaptive alpha0",
            "initial_increment_seconds": dt,
            "minimum_increment_seconds": minimum_dt,
            "maximum_increment_seconds": dt,
            "end_seconds": end,
            "step_increment_limit": steps,
            "output_interval_seconds": output_interval,
            "output_every_increments": output_every,
            "explicit_mode": False,
        },
        "source_load_conversion": {
            "source_cload_rows_removed": source_cload_rows,
            "active_physical_cload_rows": 0,
            "active_cpload_rows": 0,
            "source_cload_reference_scale_n": scale,
            "source_reference_only": True,
        },
        "native_solve_run": False,
        "mechanical_acceptance": False,
        "output_contract": {
            "shared_calculix_frequency_control": True,
            "time_points_cards_removed": True,
            "frequency_every_accepted_increment": 1,
            "physical_node_print_set": "PILOT_MONITOR",
            "driver_node_print_set": DRIVER_SET,
            "single_node_file_union_set": "PILOT_ALL_NODES",
            "node_file_union_added_nodes": [PROXY_NODE, TARGET_NODE],
            "node_file_variables": ["U", "V", "RF"],
            "contact_and_energy_requests_frequency": 1,
            "time_accuracy_across_sampled_amplitude_knots": "unresolved if accepted increments cut back",
        },
        "limits": [
            "The finite actuator is an input-only diagnostic driver, not an accepted joint capacity or service load.",
            "The source unit pattern defines the measured relative coordinate; the target coordinate differs by finite spring compliance.",
            "A sampled quintic amplitude is linearly interpolated by the solver between serialized points.",
            "Native RF, reaction, contact, force, energy, and joint acceptance require separate run-specific audits.",
        ],
    }

    modified_pilot_sets = _extend_driver_nodes_in_pilot_set(includes["pilot-sets.inp"])
    files: dict[str, bytes] = dict(includes)
    files["pilot-sets.inp"] = modified_pilot_sets
    files["pilot.inp"] = pilot.encode()
    files["source-input-freeze.json"] = source_freeze_bytes
    files["source-actuator-reference.json"] = old_actuator_bytes
    files["actuator-driving.json"] = (json.dumps(driver, indent=2) + "\n").encode()
    files["spring-actuator-producer.py.snapshot"] = producer_snapshot

    freeze = copy.deepcopy(source_freeze)
    for key in (
        "source_paths",
        "source_sha256",
        "step_scope",
        "final_amplitude_n",
        "cload_reference_scale",
        "cload_reference_force_n",
        "amplitude_table_peak_factor",
        "serialized_actual_cload_nodes_n",
        "serialized_net_force_n",
        "serialized_initial_net_moment_nmm",
        "serialized_unit_net_force_n",
        "serialized_unit_initial_net_moment_nmm",
        "final_amplitude_table_factor",
        "derivative_operation",
        "derivative_parent_artifact_sha256",
        "parent_input_freeze_sha256",
        "timing_parent_input_freeze_sha256",
        "time_point_review_sha256",
        "output_request_card_count",
        "output_schedule",
        "output_scope_limit",
        "penalty_parent_input_freeze_sha256",
        "penalty_method_review_sha256",
        "parent_contact_manifest_sha256",
        "parent_contact_fragment_sha256",
        "parent_penalty_n_per_mm3",
        "sensitivity_penalty_n_per_mm3",
        "ramp_interpolation",
        "time_points_name",
        "time_points_step_seconds",
    ):
        freeze.pop(key, None)
    freeze.update(
        {
            "schema": SCHEMA,
            "status": "INPUT_ONLY_NOT_SOLVED",
            "solver_image": SOLVER_IMAGE,
            "source_lineage": driver["source_lineage"],
            "driver_metadata_file": "actuator-driving.json",
            "driver_nodes": [PROXY_NODE, TARGET_NODE],
            "ramp_seconds": ramp,
            "end_seconds": end,
            "initial_increment_seconds": dt,
            "direct_fixed_increment": False,
            "maximum_increment_seconds": dt,
            "minimum_increment_seconds": minimum_dt,
            "hht_alpha": 0.0,
            "output_interval_seconds": output_interval,
            "output_every_increments": output_every,
            "amplitude_name": "Q_TARGET_HISTORY",
            "amplitude_time_basis": "step_time_default",
            "amplitude_sampling": driver["target_history"],
            "source_load_conversion": driver["source_load_conversion"],
            "source_unit_pattern_sha256": driver["source_unit_pattern"]["terms_sha256"],
            "source_input_freeze_sha256": _sha256(source_freeze_bytes),
            "source_actuator_reference_sha256": _sha256(old_actuator_bytes),
            "source_artifacts_sha256": actual_source_hashes,
            "source_include_modifications": {
                "pilot-sets.inp": {
                    "set_name": "PILOT_ALL_NODES",
                    "added_driver_nodes": [PROXY_NODE, TARGET_NODE],
                    "physical_membership_preserved": True,
                    "modified_sha256": _sha256(modified_pilot_sets),
                }
            },
            "output_contract": driver["output_contract"],
            "output_request_card_count": output_cards + 1,
            "output_schedule": "all NODE, EL, and CONTACT requests every accepted increment",
            "output_scope_limit": "single physical-plus-driver NODE FILE union; all requested fields at every accepted increment",
            "step_scope": "input-only current-joint finite-spring actuator diagnostic",
            "limits": driver["limits"],
            "mechanical_acceptance": False,
            "native_solve_run": False,
        }
    )
    freeze["artifacts_sha256"] = {
        name: _sha256(data) for name, data in sorted(files.items())
    }
    return PreparedInput(files=files, pilot_text=pilot, driver=driver, freeze=freeze)


def write_input_only_bundle(prepared: PreparedInput, output_dir: str | Path) -> Path:
    """Write a new isolated, reviewable input folder without invoking CCX."""
    destination = Path(output_dir).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite nonempty output directory: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in prepared.files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (destination / "actuator-driving.json").write_text(
        json.dumps(prepared.driver, indent=2) + "\n"
    )
    (destination / "input-freeze.json").write_text(
        json.dumps(prepared.freeze, indent=2) + "\n"
    )
    return destination


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--actuator-stiffness-n-per-mm", required=True, type=float)
    parser.add_argument("--q-target-max-mm", required=True, type=float)
    parser.add_argument("--ramp-seconds", required=True, type=float)
    parser.add_argument("--end-seconds", required=True, type=float)
    parser.add_argument("--dt-seconds", required=True, type=float)
    parser.add_argument("--output-interval-seconds", required=True, type=float)
    arguments = parser.parse_args()
    prepared = build_current_spring_actuator(
        arguments.base_dir,
        actuator_stiffness_n_per_mm=arguments.actuator_stiffness_n_per_mm,
        q_target_max_mm=arguments.q_target_max_mm,
        ramp_seconds=arguments.ramp_seconds,
        end_seconds=arguments.end_seconds,
        time_increment_seconds=arguments.dt_seconds,
        output_interval_seconds=arguments.output_interval_seconds,
    )
    destination = write_input_only_bundle(prepared, arguments.output_dir)
    print(f"wrote input-only spring actuator bundle: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
