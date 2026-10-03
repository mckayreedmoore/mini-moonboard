#!/usr/bin/env python3
"""Plan and measure source-bound finished sections for the upper outer joints.

The source plan is metadata-only.  ``--write`` and ``--verify`` additionally
import each of the five exact saved STEP solids once and query the declared
section planes with ``section_geometry.section_properties``.  The resulting
area properties describe saved geometry only; they do not establish stress,
resistance, common strain, integrated traction, or acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]

HOST_ACTIONS_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01"
)
FEATURE_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01"
)
ENVELOPE_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01"
)
ATTEMPT_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01"
)

OUTPUT = HERE / "sections.json"
PINS_OUTPUT = HERE / "source-pins.json"
KERNEL_SOURCE = ATTEMPT_DIR / "section_geometry.py"
KERNEL_TEST = ATTEMPT_DIR / "test_section_geometry.py"
PRODUCER_SOURCE = ATTEMPT_DIR / "produce.py"
PRODUCER_TEST = ATTEMPT_DIR / "test_source_plan.py"

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
SOURCE_PLAN_SCHEMA = "wood_joint_upper_outer_finished_section_plan/v1"
OUTPUT_SCHEMA = "wood_joint_upper_outer_finished_sections/v1"
PINS_SCHEMA = "wood_joint_upper_outer_finished_sections_source_pins/v1"

EXPECTED_RECEIVERS: dict[str, tuple[str, str]] = {
    "top_outer/clip_single_top_left_1/rail_1": (
        "base_rail_top",
        "top_outer_left_cleat",
    ),
    "top_outer/clip_single_top_left_1/rail_2": (
        "base_rail_top",
        "top_outer_left_cleat",
    ),
    "top_outer/clip_single_top_left_1/side_1": (
        "base_side_left",
        "top_outer_left_cleat",
    ),
    "top_outer/clip_single_top_left_1/side_2": (
        "base_side_left",
        "top_outer_left_cleat",
    ),
    "top_outer/clip_single_top_right_2/rail_1": (
        "base_rail_top",
        "top_outer_right_cleat",
    ),
    "top_outer/clip_single_top_right_2/rail_2": (
        "base_rail_top",
        "top_outer_right_cleat",
    ),
    "top_outer/clip_single_top_right_2/side_1": (
        "base_side_right",
        "top_outer_right_cleat",
    ),
    "top_outer/clip_single_top_right_2/side_2": (
        "base_side_right",
        "top_outer_right_cleat",
    ),
}
EXPECTED_INTERFACES: dict[str, tuple[str, str]] = {
    "base_rail_top<-top_outer_left_cleat": (
        "base_rail_top",
        "top_outer_left_cleat",
    ),
    "base_rail_top<-top_outer_right_cleat": (
        "base_rail_top",
        "top_outer_right_cleat",
    ),
    "base_side_left<-top_outer_left_cleat": (
        "base_side_left",
        "top_outer_left_cleat",
    ),
    "base_side_right<-top_outer_right_cleat": (
        "base_side_right",
        "top_outer_right_cleat",
    ),
}
HOSTS = frozenset({"base_rail_top", "base_side_left", "base_side_right"})
CLEATS = frozenset({"top_outer_left_cleat", "top_outer_right_cleat"})
MEMBERS = HOSTS | CLEATS

INPUT_ARTIFACTS: dict[str, Path] = {
    "host_actions": HOST_ACTIONS_DIR / "host-actions.json",
    "host_actions_producer": HOST_ACTIONS_DIR / "host_actions.py",
    "host_actions_test": HOST_ACTIONS_DIR / "test_host_actions.py",
    "host_actions_source_pins": HOST_ACTIONS_DIR / "source-pins.json",
    "finished_surfaces": FEATURE_DIR / "surfaces.json",
    "finished_surfaces_producer": FEATURE_DIR / "surfaces.py",
    "finished_surfaces_test": FEATURE_DIR / "test_surfaces.py",
    "finished_surfaces_source_pins": FEATURE_DIR / "source-pins.json",
    "axis_features": FEATURE_DIR / "axis-features.json",
    "axis_features_producer": FEATURE_DIR / "axis_features.py",
    "axis_features_test": FEATURE_DIR / "test_axis_features.py",
    "axis_features_source_pins": FEATURE_DIR / "axis-source-pins.json",
    "stock_envelopes": ENVELOPE_DIR / "envelopes.json",
    "stock_envelopes_producer": ENVELOPE_DIR / "envelopes.py",
    "stock_envelopes_test": ENVELOPE_DIR / "test_envelopes.py",
    "stock_envelopes_source_pins": ENVELOPE_DIR / "source-pins.json",
}
PIN_DOCUMENTS = tuple(
    INPUT_ARTIFACTS[key]
    for key in (
        "host_actions_source_pins",
        "finished_surfaces_source_pins",
        "axis_features_source_pins",
        "stock_envelopes_source_pins",
    )
)
LOCAL_CODE_BINDINGS = {
    "section_producer": PRODUCER_SOURCE,
    "section_producer_test": PRODUCER_TEST,
    "section_geometry_kernel": KERNEL_SOURCE,
    "section_geometry_test": KERNEL_TEST,
    "section_polygon_oracle_test": ATTEMPT_DIR / "test_polygon_oracle.py",
}

LINEAR_TOLERANCE_MM = 1.0e-5
PLANE_COINCIDENCE_TOLERANCE_MM = 1.0e-6
FRAME_TOLERANCE = 1.0e-6
AXIS_LINE_TOLERANCE_MM = 1.0e-5


class SourceRefusal(ValueError):
    """A saved artifact, source relation, or declared section is not exact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceRefusal(message)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _reject_constant(value: str) -> None:
    raise SourceRefusal(f"non-standard JSON numeric value: {value}")


def read_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceRefusal(f"cannot read JSON source {path}: {exc}") from exc


def finite(value: Any, label: str) -> float:
    require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label} must be numeric",
    )
    result = float(value)
    require(math.isfinite(result), f"{label} must be finite")
    return result


def vec3(value: Any, label: str) -> list[float]:
    require(
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) == 3,
        f"{label} must be a three-vector",
    )
    return [
        finite(component, f"{label}[{index}]") for index, component in enumerate(value)
    ]


def dot(first: Sequence[float], second: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def sub(first: Sequence[float], second: Sequence[float]) -> list[float]:
    return [a - b for a, b in zip(first, second, strict=True)]


def cross(first: Sequence[float], second: Sequence[float]) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def norm(vector: Sequence[float]) -> float:
    return math.sqrt(dot(vector, vector))


def station(
    point: Sequence[float], datum: Sequence[float], grain: Sequence[float]
) -> float:
    return dot(sub(point, datum), grain)


def line_distance(
    point: Sequence[float], datum: Sequence[float], direction: Sequence[float]
) -> float:
    delta = sub(point, datum)
    along = dot(delta, direction)
    perpendicular = [delta[i] - along * direction[i] for i in range(3)]
    return norm(perpendicular)


def _centroid_axis_distance(
    centroid: Sequence[float],
    source_datum: Sequence[float],
    source_direction: Sequence[float],
    label: str,
) -> float:
    distance = line_distance(centroid, source_datum, source_direction)
    require(
        distance <= AXIS_LINE_TOLERANCE_MM,
        f"{label} cylinder centroid is off the source axis line: {distance:.9g} mm",
    )
    return distance


def _validate_receiver_memberships(
    axis_id: str,
    memberships: Any,
    host_id: str,
    cleat_id: str,
) -> list[Mapping[str, Any]]:
    require(isinstance(memberships, list), f"{axis_id} has no receiver memberships")
    member_counts: dict[str, int] = {}
    for membership in memberships:
        require(
            isinstance(membership, Mapping),
            f"{axis_id} has malformed receiver membership",
        )
        member_id = membership.get("receiver_member_id")
        require(
            member_id in (host_id, cleat_id),
            f"{axis_id} has an unexpected receiver membership: {member_id}",
        )
        member_counts[str(member_id)] = member_counts.get(str(member_id), 0) + 1
    require(
        member_counts == {host_id: 1, cleat_id: 1},
        f"{axis_id} must have exactly one host and one cleat receiver membership",
    )
    return memberships


def _check_frame(frame: Mapping[str, Any], label: str) -> None:
    origin = vec3(frame.get("origin_global_xyz_mm"), f"{label} origin")
    axes = [
        vec3(frame.get(field), f"{label} {field}")
        for field in (
            "grain_axis_global_xyz",
            "section_u_global_xyz",
            "section_v_global_xyz",
        )
    ]
    del origin
    for index, axis in enumerate(axes):
        require(
            abs(norm(axis) - 1.0) <= FRAME_TOLERANCE,
            f"{label} basis axis {index} is not unit",
        )
    for first_index in range(3):
        for second_index in range(first_index + 1, 3):
            require(
                abs(dot(axes[first_index], axes[second_index])) <= FRAME_TOLERANCE,
                f"{label} basis is not orthogonal",
            )
    handedness = dot(cross(axes[0], axes[1]), axes[2])
    require(
        abs(handedness - 1.0) <= FRAME_TOLERANCE,
        f"{label} basis is not right-handed",
    )


def _rooted_path(root: Path, relative: str | Path) -> Path:
    path = Path(relative)
    require(not path.is_absolute(), f"source path must be repository-relative: {path}")
    resolved_root = root.resolve()
    resolved = (resolved_root / path).resolve()
    require(
        resolved == resolved_root or resolved_root in resolved.parents,
        f"source path escapes repository root: {path}",
    )
    return resolved


def _pin_entry(value: Any, label: str) -> tuple[str, str, int | None]:
    require(isinstance(value, Mapping), f"{label} must be an object")
    relative = value.get("path")
    digest = value.get("sha256")
    require(isinstance(relative, str) and relative, f"{label} has no path")
    require(
        isinstance(digest, str) and len(digest) == 64,
        f"{label} has no SHA-256",
    )
    size = value.get("size_bytes")
    if size is not None:
        require(
            isinstance(size, int) and not isinstance(size, bool) and size >= 0,
            f"{label} has invalid size_bytes",
        )
    return relative, digest, size


def _iter_pin_entries(
    value: Any, label: str = "pin document"
) -> Iterable[tuple[str, str, int | None]]:
    """Find source pins in the two saved pin-document formats."""
    if isinstance(value, Mapping):
        if "path" in value and "sha256" in value:
            yield _pin_entry(value, label)
        else:
            for key, item in value.items():
                yield from _iter_pin_entries(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_pin_entries(item, f"{label}[{index}]")


def collect_pin_closure(
    root: Path,
    pin_documents: Sequence[str | Path],
    direct_artifacts: Mapping[str, str | Path],
    local_code: Mapping[str, str | Path],
) -> list[dict[str, Any]]:
    """Verify each stored pin recursively and return a deterministic byte map."""
    collected: dict[str, dict[str, Any]] = {}

    def bind(
        relative: str, expected_sha: str | None, expected_size: int | None, role: str
    ) -> None:
        path = _rooted_path(root, relative)
        require(path.is_file(), f"required source is missing: {relative}")
        raw = path.read_bytes()
        actual_sha = sha256_bytes(raw)
        actual_size = len(raw)
        if expected_sha is not None:
            require(
                actual_sha == expected_sha,
                f"changed pinned source {relative}: {actual_sha}",
            )
        if expected_size is not None:
            require(
                actual_size == expected_size,
                f"changed pinned source size {relative}: {actual_size}",
            )
        prior = collected.get(relative)
        if prior is None:
            collected[relative] = {
                "path": relative,
                "sha256": actual_sha,
                "size_bytes": actual_size,
                "roles": [role],
            }
            return
        require(prior["sha256"] == actual_sha, f"conflicting pin for {relative}")
        require(
            prior["size_bytes"] == actual_size, f"conflicting size pin for {relative}"
        )
        if role not in prior["roles"]:
            prior["roles"].append(role)

    for role, relative_path in sorted(direct_artifacts.items()):
        relative = Path(relative_path).as_posix()
        bind(relative, None, None, role)
    for role, relative_path in sorted(local_code.items()):
        relative = Path(relative_path).as_posix()
        bind(relative, None, None, role)

    pending = [Path(value).as_posix() for value in pin_documents]
    seen_pin_documents: set[str] = set()
    while pending:
        pin_path = pending.pop(0)
        if pin_path in seen_pin_documents:
            continue
        seen_pin_documents.add(pin_path)
        bind(pin_path, None, None, "upstream_source_pin_document")
        document = read_json(_rooted_path(root, pin_path))
        entries = list(_iter_pin_entries(document, pin_path))
        require(entries, f"source pin document contains no pins: {pin_path}")
        for relative, expected_sha, expected_size in entries:
            bind(relative, expected_sha, expected_size, "upstream_pinned_source")
            if Path(relative).name in {"source-pins.json", "axis-source-pins.json"}:
                pending.append(relative)
    return [
        {**record, "roles": sorted(record["roles"])}
        for _, record in sorted(collected.items())
    ]


def _verify_report_links(root: Path, artifacts: Mapping[str, Any]) -> None:
    host = artifacts["host_actions"]
    surfaces = artifacts["finished_surfaces"]
    axes = artifacts["axis_features"]
    envelopes = artifacts["stock_envelopes"]

    require(host.get("candidate") == CANDIDATE, "host-actions candidate mismatch")
    require(
        host.get("geometry_revision_id") == REVISION, "host-actions revision mismatch"
    )
    require(
        surfaces.get("candidate") == CANDIDATE, "finished-surfaces candidate mismatch"
    )
    require(
        surfaces.get("geometry_revision_id") == REVISION,
        "finished-surfaces revision mismatch",
    )
    require(axes.get("candidate") == CANDIDATE, "axis-features candidate mismatch")
    require(
        axes.get("geometry_revision_id") == REVISION, "axis-features revision mismatch"
    )
    require(
        envelopes.get("candidate") == CANDIDATE, "stock-envelopes candidate mismatch"
    )
    require(
        envelopes.get("geometry_revision_id") == REVISION,
        "stock-envelopes revision mismatch",
    )

    expected_artifact_schemas = {
        "host_actions": "upper-outer-host-point-actions/v1",
        "finished_surfaces": "wood_joint_current_finished_feature_register/v1",
        "axis_features": "wood_joint_axis_finished_feature_register/v1",
        "stock_envelopes": "wood_joint_proposed_starting_stock_envelopes/v1",
    }
    for key, expected_schema in expected_artifact_schemas.items():
        require(
            artifacts[key].get("schema") == expected_schema, f"{key} schema mismatch"
        )

    surfaces_pins_path = _rooted_path(
        root, INPUT_ARTIFACTS["finished_surfaces_source_pins"]
    )
    axes_pins_path = _rooted_path(root, INPUT_ARTIFACTS["axis_features_source_pins"])
    envelopes_pins_path = _rooted_path(
        root, INPUT_ARTIFACTS["stock_envelopes_source_pins"]
    )
    for key, path in (
        ("finished_surfaces_source_pins", surfaces_pins_path),
        ("axis_features_source_pins", axes_pins_path),
        ("stock_envelopes_source_pins", envelopes_pins_path),
    ):
        pin_document = read_json(path)
        if "candidate" in pin_document:
            require(
                pin_document.get("candidate") == CANDIDATE, f"{key} candidate mismatch"
            )
        if "geometry_revision_id" in pin_document:
            require(
                pin_document.get("geometry_revision_id") == REVISION,
                f"{key} revision mismatch",
            )
    require(
        surfaces.get("source_pins_sha256") == sha256_file(surfaces_pins_path),
        "finished-surfaces source-pin document hash mismatch",
    )
    require(
        axes.get("source_hashes", {}).get("surfaces_source_pins_sha256")
        == sha256_file(surfaces_pins_path),
        "axis-features surface source-pin hash mismatch",
    )
    require(
        axes.get("source_hashes", {}).get("surfaces_report_sha256")
        == sha256_file(_rooted_path(root, INPUT_ARTIFACTS["finished_surfaces"])),
        "axis-features finished-surfaces report hash mismatch",
    )
    require(
        surfaces.get("reviewed_stock_envelopes_sha256")
        == sha256_file(_rooted_path(root, INPUT_ARTIFACTS["stock_envelopes"])),
        "finished-surfaces stock-envelope report hash mismatch",
    )
    require(
        surfaces.get("reviewed_stock_source_pins_sha256")
        == sha256_file(envelopes_pins_path),
        "finished-surfaces stock-envelope source-pin hash mismatch",
    )
    require(
        envelopes.get("source_pins_sha256") == sha256_file(envelopes_pins_path),
        "stock-envelope source-pin document hash mismatch",
    )

    for report_key, producer_key, test_key in (
        ("finished_surfaces", "finished_surfaces_producer", "finished_surfaces_test"),
        ("stock_envelopes", "stock_envelopes_producer", "stock_envelopes_test"),
    ):
        report = artifacts[report_key]
        producer_path = _rooted_path(root, INPUT_ARTIFACTS[producer_key])
        test_path = _rooted_path(root, INPUT_ARTIFACTS[test_key])
        producer_field = "producer_sha256"
        require(
            report.get(producer_field) == sha256_file(producer_path),
            f"{report_key} producer hash does not match its source",
        )
        if report_key == "finished_surfaces":
            require(
                report.get("test_sha256") == sha256_file(test_path),
                "finished-surfaces test hash does not match its source",
            )

    axes_pin_doc = read_json(axes_pins_path)
    output_pin = axes_pin_doc.get("outputs", {}).get("axis_features", {})
    require(
        isinstance(output_pin, Mapping)
        and output_pin.get("sha256")
        == sha256_file(_rooted_path(root, INPUT_ARTIFACTS["axis_features"])),
        "axis-source-pins does not bind axis-features report",
    )

    host_report_pins = host.get("source_pins")
    require(
        isinstance(host_report_pins, list) and host_report_pins,
        "host-actions has no source pins",
    )
    for pin in host_report_pins:
        relative, expected_sha, expected_size = _pin_entry(
            pin, "host-actions source pin"
        )
        path = _rooted_path(root, relative)
        require(path.is_file(), f"host-actions pinned source is missing: {relative}")
        require(
            sha256_file(path) == expected_sha,
            f"host-actions pinned source changed: {relative}",
        )
        if expected_size is not None:
            require(
                path.stat().st_size == expected_size,
                f"host-actions pinned size changed: {relative}",
            )


def _unique_member_record(
    rows: Any, field: str, member_id: str, label: str
) -> dict[str, Any]:
    require(isinstance(rows, list), f"{label} must be an array")
    selected = [
        row for row in rows if isinstance(row, Mapping) and row.get(field) == member_id
    ]
    require(len(selected) == 1, f"{label} must contain exactly one {member_id} record")
    return dict(selected[0])


def _member_frames(
    root: Path,
    artifacts: Mapping[str, Any],
) -> tuple[
    dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]
]:
    surfaces = artifacts["finished_surfaces"]
    envelopes = artifacts["stock_envelopes"]
    host_actions = artifacts["host_actions"]
    surface_records: dict[str, dict[str, Any]] = {}
    envelope_records: dict[str, dict[str, Any]] = {}
    frames: dict[str, dict[str, Any]] = {}

    for member_id in sorted(MEMBERS):
        surface = _unique_member_record(
            surfaces.get("records"), "member_id", member_id, "surface records"
        )
        envelope = _unique_member_record(
            envelopes.get("records"), "member_id", member_id, "envelope records"
        )
        surface_binding = surface.get("step_binding")
        require(
            isinstance(surface_binding, Mapping),
            f"{member_id} has no exact finished STEP binding",
        )
        step_path = surface_binding.get("path")
        step_sha = surface_binding.get("file_sha256")
        step_size = surface_binding.get("size_bytes")
        require(
            isinstance(step_path, str) and step_path, f"{member_id} has no STEP path"
        )
        require(
            isinstance(step_sha, str) and len(step_sha) == 64,
            f"{member_id} has no STEP SHA-256",
        )
        require(
            isinstance(step_size, int) and step_size > 0,
            f"{member_id} has no STEP size",
        )
        require(
            surface_binding.get("solid_count") == 1,
            f"{member_id} saved STEP is not a single solid",
        )
        require(
            envelope.get("current_finished_step_path") == step_path,
            f"{member_id} envelope STEP path mismatch",
        )
        require(
            envelope.get("current_finished_step_sha256") == step_sha,
            f"{member_id} envelope STEP hash mismatch",
        )
        require(
            envelope.get("current_finished_step_size_bytes") == step_size,
            f"{member_id} envelope STEP size mismatch",
        )
        step_file = _rooted_path(root, step_path)
        require(step_file.is_file(), f"saved STEP is missing: {step_path}")
        require(sha256_file(step_file) == step_sha, f"saved STEP changed: {step_path}")
        require(
            step_file.stat().st_size == step_size,
            f"saved STEP size changed: {step_path}",
        )

        host_inventory = host_actions.get(
            "host_geometry_and_source_station_inventories", {}
        )
        if member_id in HOSTS:
            host_record = host_inventory.get(member_id)
            require(
                isinstance(host_record, Mapping),
                f"missing exact host frame for {member_id}",
            )
            require(
                host_record.get("host") == member_id,
                f"host frame identity mismatch for {member_id}",
            )
            require(
                host_record.get("step_path") == step_path,
                f"host frame STEP path mismatch for {member_id}",
            )
            require(
                host_record.get("step_sha256") == step_sha,
                f"host frame STEP hash mismatch for {member_id}",
            )
            frame = {
                "frame_source": "exact source-model host grain/u/v/start from host-actions static inventory",
                "datum_status": "source model member start; analytical frame datum only",
                "origin_global_xyz_mm": vec3(
                    host_record.get("member_start_xyz_mm"), f"{member_id} model start"
                ),
                "grain_axis_global_xyz": vec3(
                    host_record.get("grain_axis_global_xyz"), f"{member_id} grain"
                ),
                "section_u_global_xyz": vec3(
                    host_record.get("section_u_global_xyz"), f"{member_id} section u"
                ),
                "section_v_global_xyz": vec3(
                    host_record.get("section_v_global_xyz"), f"{member_id} section v"
                ),
                "member_end_global_xyz_mm": vec3(
                    host_record.get("member_end_xyz_mm"), f"{member_id} model end"
                ),
                "member_grain_length_mm": finite(
                    host_record.get("member_grain_length_mm"),
                    f"{member_id} model length",
                ),
            }
            start_to_end = sub(
                frame["member_end_global_xyz_mm"], frame["origin_global_xyz_mm"]
            )
            require(
                norm(
                    sub(
                        start_to_end,
                        [
                            component * frame["member_grain_length_mm"]
                            for component in frame["grain_axis_global_xyz"]
                        ],
                    )
                )
                <= LINEAR_TOLERANCE_MM,
                f"{member_id} host model start/end does not follow its exact grain frame",
            )
        else:
            stock = surface.get("stock_frame")
            proposal = envelope.get("proposed_frame")
            require(
                isinstance(stock, Mapping), f"{member_id} lacks proposed stock frame"
            )
            require(
                isinstance(proposal, Mapping),
                f"{member_id} lacks proposed stock frame source",
            )
            require(
                stock.get("basis_source")
                == "reviewed proposed stock envelope g/q/r basis",
                f"{member_id} has an unsupported stock basis source",
            )
            require(
                stock.get("datum_status")
                == "proposed minimum g/q/r corner; not a delivered-stock datum",
                f"{member_id} stock origin is not clearly proposed",
            )
            require(
                proposal.get("status") == "CONTAINED",
                f"{member_id} proposed stock frame is not contained",
            )
            basis = stock.get("basis_columns_global_xyz")
            require(
                isinstance(basis, Sequence) and len(basis) == 3,
                f"{member_id} stock frame must have g/q/r columns",
            )
            frame = {
                "frame_source": "pinned proposed stock g/q/r frame; origin is not an actual stock datum",
                "datum_status": "proposed minimum g/q/r corner; not a delivered-stock datum",
                "origin_global_xyz_mm": vec3(
                    stock.get("origin_global_xyz_mm"), f"{member_id} proposed origin"
                ),
                "grain_axis_global_xyz": vec3(basis[0], f"{member_id} proposed g"),
                "section_u_global_xyz": vec3(basis[1], f"{member_id} proposed q"),
                "section_v_global_xyz": vec3(basis[2], f"{member_id} proposed r"),
                "basis_source": stock["basis_source"],
            }
            require(
                norm(
                    sub(
                        frame["grain_axis_global_xyz"],
                        vec3(
                            proposal.get("grain_axis_global_xyz"),
                            f"{member_id} envelope g",
                        ),
                    )
                )
                <= FRAME_TOLERANCE,
                f"{member_id} surface g does not match proposed envelope g",
            )
            require(
                norm(
                    sub(
                        frame["section_u_global_xyz"],
                        vec3(
                            proposal.get("section_q_axis_global_xyz"),
                            f"{member_id} envelope q",
                        ),
                    )
                )
                <= FRAME_TOLERANCE,
                f"{member_id} surface q does not match proposed envelope q",
            )
            require(
                norm(
                    sub(
                        frame["section_v_global_xyz"],
                        vec3(
                            proposal.get("section_r_axis_global_xyz"),
                            f"{member_id} envelope r",
                        ),
                    )
                )
                <= FRAME_TOLERANCE,
                f"{member_id} surface r does not match proposed envelope r",
            )
            bounds = envelope.get("original_stock_containment", {}).get(
                "proposed_stock_bounds_g_q_r_mm"
            )
            require(
                isinstance(bounds, Sequence) and len(bounds) == 3,
                f"{member_id} envelope lacks proposed stock bounds",
            )
            projected_origin = [
                dot(frame["origin_global_xyz_mm"], axis)
                for axis in (
                    frame["grain_axis_global_xyz"],
                    frame["section_u_global_xyz"],
                    frame["section_v_global_xyz"],
                )
            ]
            for index, axis_bounds in enumerate(bounds):
                require(
                    isinstance(axis_bounds, Sequence) and len(axis_bounds) == 2,
                    f"{member_id} proposed stock bounds axis {index} is malformed",
                )
                minimum = finite(
                    axis_bounds[0], f"{member_id} proposed bound minimum {index}"
                )
                require(
                    abs(projected_origin[index] - minimum) <= LINEAR_TOLERANCE_MM,
                    f"{member_id} proposed frame origin does not match minimum stock corner",
                )

        _check_frame(frame, f"{member_id} section frame")
        surface_records[member_id] = surface
        envelope_records[member_id] = envelope
        frames[member_id] = {
            **frame,
            "member_id": member_id,
            "step_path": step_path,
            "step_sha256": step_sha,
            "step_size_bytes": step_size,
            "source_solid_count": 1,
        }
    return surface_records, envelope_records, frames


def _application_planes(host_actions: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    states = host_actions.get("states")
    require(isinstance(states, list) and states, "host-actions states are missing")
    expected_by_interface: dict[str, dict[str, Any]] = {}
    seen_state_count = 0
    for state_index, state in enumerate(states):
        require(
            isinstance(state, Mapping), f"host-actions state {state_index} is malformed"
        )
        interfaces = state.get("interfaces")
        require(
            isinstance(interfaces, list),
            f"host-actions state {state_index} has no interfaces",
        )
        selected: dict[str, Mapping[str, Any]] = {}
        for interface in interfaces:
            if not isinstance(interface, Mapping):
                continue
            interface_id = interface.get("interface_id")
            if interface_id not in EXPECTED_INTERFACES:
                continue
            require(
                interface_id not in selected,
                f"duplicate host-action interface in state: {interface_id}",
            )
            require(
                (interface.get("host"), interface.get("receiving_cleat"))
                == EXPECTED_INTERFACES[interface_id],
                f"host-action interface identity mismatch: {interface_id}",
            )
            selected[str(interface_id)] = interface
        require(
            set(selected) == set(EXPECTED_INTERFACES),
            f"host-actions state {state_index} has missing upper outer interfaces",
        )
        seen_state_count += 1
        for interface_id, interface in selected.items():
            host_id, cleat_id = EXPECTED_INTERFACES[interface_id]
            axes = interface.get("target_fastener_axes")
            require(
                isinstance(axes, list), f"{interface_id} lacks target_fastener_axes"
            )
            expected_axis_ids = {
                axis_id
                for axis_id, pair in EXPECTED_RECEIVERS.items()
                if pair == (host_id, cleat_id)
            }
            axis_map: dict[str, dict[str, Any]] = {}
            for axis in axes:
                require(
                    isinstance(axis, Mapping),
                    f"{interface_id} has malformed target axis",
                )
                axis_id = axis.get("axis_id")
                require(
                    isinstance(axis_id, str) and axis_id,
                    f"{interface_id} target axis has no ID",
                )
                require(
                    axis_id in expected_axis_ids,
                    f"unexpected target axis in upper outer interface: {axis_id}",
                )
                require(
                    axis_id not in axis_map,
                    f"duplicate target axis in interface {interface_id}: {axis_id}",
                )
                require(
                    axis.get("host") == host_id, f"target axis {axis_id} host mismatch"
                )
                require(
                    axis.get("block") == cleat_id,
                    f"target axis {axis_id} cleat mismatch",
                )
                step_path = axis.get("host_step_path")
                step_sha = axis.get("host_step_sha256")
                require(
                    isinstance(step_path, str) and step_path,
                    f"target axis {axis_id} has no host STEP path",
                )
                require(
                    isinstance(step_sha, str) and len(step_sha) == 64,
                    f"target axis {axis_id} has no host STEP SHA",
                )
                axis_map[axis_id] = {
                    "axis_id": axis_id,
                    "host": host_id,
                    "cleat": cleat_id,
                    "application_datum_global_xyz_mm": vec3(
                        axis.get("lateral_plane_xyz_mm"), f"{axis_id} application plane"
                    ),
                    "head_to_nut_axis_global_xyz": vec3(
                        axis.get("head_to_nut_axis_global_xyz"),
                        f"{axis_id} bolt direction",
                    ),
                    "host_step_path": step_path,
                    "host_step_sha256": step_sha,
                }
            require(
                set(axis_map) == expected_axis_ids,
                f"{interface_id} target-axis set is incomplete",
            )
            if interface_id not in expected_by_interface:
                expected_by_interface[interface_id] = axis_map
            else:
                require(
                    axis_map == expected_by_interface[interface_id],
                    f"source application axes changed between host-action states: {interface_id}",
                )
    require(seen_state_count == len(states), "not all host-action states were checked")
    flattened = [
        axis
        for per_interface in expected_by_interface.values()
        for axis in per_interface.values()
    ]
    require(
        len(flattened) == 8, "upper outer source application axis count must be eight"
    )
    result: dict[str, dict[str, Any]] = {}
    for interface_axes in expected_by_interface.values():
        for axis_id, axis in interface_axes.items():
            require(
                axis_id not in result,
                f"source application axis occurs at multiple interfaces: {axis_id}",
            )
            result[axis_id] = axis
    require(
        set(result) == set(EXPECTED_RECEIVERS),
        "source application axis identities are incomplete",
    )
    return result


def _merge_plane_candidates(
    candidates: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Deduplicate same-member grain planes and retain every source identity."""
    by_member: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        by_member.setdefault(candidate["member_id"], []).append(candidate)

    merged: list[dict[str, Any]] = []
    identity_to_plane: dict[str, str] = {}
    for member_id in sorted(by_member):
        rows = sorted(
            by_member[member_id],
            key=lambda row: (
                finite(row["grain_station_mm"], f"{member_id} section station"),
                row["identity_key"],
            ),
        )
        groups: list[list[dict[str, Any]]] = []
        for row in rows:
            compatible_groups: list[list[dict[str, Any]]] = []
            partial_group_matches = 0
            row_station = finite(
                row["grain_station_mm"], f"{member_id} section station"
            )
            for group in groups:
                g = group[0]["frame"]["grain_axis_global_xyz"]
                same_direction = (
                    norm(sub(g, row["frame"]["grain_axis_global_xyz"]))
                    <= FRAME_TOLERANCE
                )
                require(
                    same_direction,
                    f"{member_id} section candidates use mismatched grain frames",
                )
                distances = [
                    abs(row_station - finite(item["grain_station_mm"], "group station"))
                    for item in group
                ]
                if all(
                    distance <= PLANE_COINCIDENCE_TOLERANCE_MM for distance in distances
                ):
                    compatible_groups.append(group)
                elif any(
                    distance <= PLANE_COINCIDENCE_TOLERANCE_MM for distance in distances
                ):
                    partial_group_matches += 1
            require(
                partial_group_matches == 0,
                f"ambiguous transitive coincidence near {member_id} station {row_station:.12g}",
            )
            require(
                len(compatible_groups) <= 1,
                f"ambiguous coincident plane membership for {member_id} station {row_station:.12g}",
            )
            if compatible_groups:
                compatible_groups[0].append(row)
            else:
                groups.append([row])

        for group in groups:
            identities = sorted(row["identity_key"] for row in group)
            identity_digest = sha256_bytes(canonical_bytes(identities))[:16]
            plane_id = f"{member_id}:section:{identity_digest}"
            frame = group[0]["frame"]
            stations = [
                finite(row["grain_station_mm"], "group station") for row in group
            ]
            plane = {
                "plane_id": plane_id,
                "member_id": member_id,
                "plane_origin_global_xyz_mm": list(group[0]["origin_global_xyz_mm"]),
                "grain_axis_global_xyz": list(frame["grain_axis_global_xyz"]),
                "section_u_global_xyz": list(frame["section_u_global_xyz"]),
                "section_v_global_xyz": list(frame["section_v_global_xyz"]),
                "grain_station_mm": math.fsum(stations) / len(stations),
                "station_spread_mm": max(stations) - min(stations),
                "coincidence_tolerance_mm": PLANE_COINCIDENCE_TOLERANCE_MM,
                "source_identity_count": len(group),
                "source_identities": [
                    {
                        "identity_key": row["identity_key"],
                        "kind": row["kind"],
                        **row["source_identity"],
                        "origin_global_xyz_mm": list(row["origin_global_xyz_mm"]),
                        "grain_station_mm": row["grain_station_mm"],
                    }
                    for row in sorted(group, key=lambda item: item["identity_key"])
                ],
            }
            _check_frame(
                {
                    "origin_global_xyz_mm": plane["plane_origin_global_xyz_mm"],
                    "grain_axis_global_xyz": plane["grain_axis_global_xyz"],
                    "section_u_global_xyz": plane["section_u_global_xyz"],
                    "section_v_global_xyz": plane["section_v_global_xyz"],
                },
                f"{plane_id} section frame",
            )
            for identity in identities:
                require(
                    identity not in identity_to_plane,
                    f"duplicate section source identity: {identity}",
                )
                identity_to_plane[identity] = plane_id
            merged.append(plane)
    merged.sort(
        key=lambda row: (row["member_id"], row["grain_station_mm"], row["plane_id"])
    )
    return merged, identity_to_plane


def build_source_plan(
    root: Path,
    artifacts: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a metadata-only plan; it never opens a CAD runtime or STEP BRep."""
    require(
        set(artifacts)
        >= {"host_actions", "finished_surfaces", "axis_features", "stock_envelopes"},
        "source plan lacks required artifacts",
    )
    host_actions = artifacts["host_actions"]
    surfaces = artifacts["finished_surfaces"]
    axes_doc = artifacts["axis_features"]
    envelopes = artifacts["stock_envelopes"]
    for report, label in (
        (host_actions, "host-actions"),
        (surfaces, "finished-surfaces"),
        (axes_doc, "axis-features"),
        (envelopes, "stock-envelopes"),
    ):
        require(isinstance(report, Mapping), f"{label} artifact must be a JSON object")
        require(report.get("candidate") == CANDIDATE, f"{label} candidate mismatch")
        require(
            report.get("geometry_revision_id") == REVISION, f"{label} revision mismatch"
        )

    surface_records, _, frames = _member_frames(root, artifacts)

    axis_groups = axes_doc.get("source_axis_groups")
    require(isinstance(axis_groups, Mapping), "axis-features has no source axis groups")
    candidate_group = axis_groups.get("candidate_bolt_axes")
    require(
        isinstance(candidate_group, Mapping), "axis-features lacks candidate bolt axes"
    )
    axis_rows = candidate_group.get("axes")
    require(
        isinstance(axis_rows, list), "axis-features candidate bolt rows are missing"
    )
    selected_rows = [
        row
        for row in axis_rows
        if isinstance(row, Mapping) and row.get("axis_id") in EXPECTED_RECEIVERS
    ]
    selected_ids = [row.get("axis_id") for row in selected_rows]
    require(
        len(selected_ids) == len(set(selected_ids)),
        "duplicate selected candidate axis IDs",
    )
    require(
        set(selected_ids) == set(EXPECTED_RECEIVERS),
        "selected upper outer axis set is incomplete",
    )
    require(
        len(selected_ids) == 8,
        "upper outer section plan must select exactly eight bolt axes",
    )

    application_by_axis = _application_planes(host_actions)
    candidates: list[dict[str, Any]] = []
    memberships: list[dict[str, Any]] = []
    application_planes: list[dict[str, Any]] = []
    feature_lookup = {
        member_id: _surface_feature_map(surface_records[member_id], member_id)
        for member_id in sorted(surface_records)
    }
    for raw_axis in sorted(selected_rows, key=lambda row: str(row.get("axis_id"))):
        axis = dict(raw_axis)
        axis_id = axis.get("axis_id")
        host_id, cleat_id = EXPECTED_RECEIVERS[str(axis_id)]
        source_axis = axis.get("source_axis_fields")
        require(
            isinstance(source_axis, Mapping), f"{axis_id} has no source axis fields"
        )
        source_datum = vec3(
            source_axis.get("datum_global_xyz_mm"), f"{axis_id} source axis datum"
        )
        source_direction = vec3(
            source_axis.get("direction_global_xyz"), f"{axis_id} source axis direction"
        )
        require(
            abs(norm(source_direction) - 1.0) <= FRAME_TOLERANCE,
            f"{axis_id} source direction is not unit",
        )
        memberships_source = _validate_receiver_memberships(
            str(axis_id), axis.get("receiver_memberships"), host_id, cleat_id
        )

        for raw_membership in memberships_source:
            membership = dict(raw_membership)
            member_id = str(membership["receiver_member_id"])
            require(
                membership.get("binding_status")
                == "bound_to_current_finished_stock_frame",
                f"{axis_id}/{member_id} receiver frame is not bound",
            )
            require(
                membership.get("match_status") == "matched_bore_patch",
                f"{axis_id}/{member_id} bore feature is unresolved",
            )
            feature_ids = membership.get("matched_feature_ids")
            require(
                isinstance(feature_ids, list) and len(feature_ids) == 1,
                f"{axis_id}/{member_id} must match exactly one saved cylinder feature",
            )
            feature_id = feature_ids[0]
            require(
                isinstance(feature_id, str),
                f"{axis_id}/{member_id} matched feature ID is malformed",
            )
            cylinder_candidates = membership.get("cylinder_surface_candidates")
            require(
                isinstance(cylinder_candidates, list)
                and len(cylinder_candidates) == 1
                and isinstance(cylinder_candidates[0], Mapping),
                f"{axis_id}/{member_id} has missing or ambiguous cylinder candidates",
            )
            cylinder_candidate = cylinder_candidates[0]
            require(
                cylinder_candidate.get("association_status") == "eligible_bore_patch"
                and cylinder_candidate.get("feature_id") == feature_id
                and cylinder_candidate.get("surface_kind") == "CYLINDER",
                f"{axis_id}/{member_id} cylinder candidate is not the unique supported bore patch",
            )
            diagnostics = membership.get("diagnostics")
            require(
                isinstance(diagnostics, Mapping),
                f"{axis_id}/{member_id} feature diagnostics are missing",
            )
            require(
                diagnostics.get("eligible_bore_patches") == 1
                and diagnostics.get("coaxial_cylinder_features") == 1,
                f"{axis_id}/{member_id} feature match is not unique",
            )
            feature = feature_lookup[member_id].get(feature_id)
            require(
                feature is not None,
                f"{axis_id}/{member_id} matched feature is absent from saved surface register",
            )
            require(
                feature.get("surface_kind") == "CYLINDER",
                f"{axis_id}/{member_id} matched feature is not cylindrical",
            )
            cylinder = feature.get("cylinder")
            require(
                isinstance(cylinder, Mapping),
                f"{axis_id}/{member_id} matched cylinder metadata is missing",
            )
            require(
                cylinder.get("material_side_geometry") == "bore_like",
                f"{axis_id}/{member_id} cylinder is not source-classified bore-like",
            )
            require(
                finite(
                    cylinder.get("radius_mm"), f"{axis_id}/{member_id} cylinder radius"
                )
                > 0.0,
                f"{axis_id}/{member_id} cylinder radius is not positive",
            )
            center = vec3(
                cylinder.get("centroid_global_xyz_mm"),
                f"{axis_id}/{member_id} bore-center centroid",
            )
            cylinder_axis = vec3(
                cylinder.get("axis_unit_global_xyz"),
                f"{axis_id}/{member_id} cylinder axis",
            )
            require(
                abs(norm(cylinder_axis) - 1.0) <= FRAME_TOLERANCE,
                f"{axis_id}/{member_id} cylinder axis is not unit",
            )
            require(
                math.sqrt(
                    max(
                        0.0,
                        1.0 - min(1.0, abs(dot(cylinder_axis, source_direction))) ** 2,
                    )
                )
                <= FRAME_TOLERANCE,
                f"{axis_id}/{member_id} cylinder axis is not parallel to the source axis",
            )
            distance = _centroid_axis_distance(
                center, source_datum, source_direction, f"{axis_id}/{member_id}"
            )
            step_binding = membership.get("current_finished_step_binding")
            require(
                isinstance(step_binding, Mapping),
                f"{axis_id}/{member_id} membership has no finished STEP binding",
            )
            require(
                step_binding.get("path") == frames[member_id]["step_path"],
                f"{axis_id}/{member_id} membership STEP path mismatch",
            )
            require(
                step_binding.get("file_sha256") == frames[member_id]["step_sha256"],
                f"{axis_id}/{member_id} membership STEP hash mismatch",
            )
            require(
                step_binding.get("size_bytes") == frames[member_id]["step_size_bytes"],
                f"{axis_id}/{member_id} membership STEP size mismatch",
            )
            membership_stock = membership.get("stock_frame")
            surface_stock = surface_records[member_id].get("stock_frame")
            require(
                isinstance(membership_stock, Mapping),
                f"{axis_id}/{member_id} membership stock frame is missing",
            )
            require(
                isinstance(surface_stock, Mapping),
                f"{member_id} saved surface stock frame is missing",
            )
            require(
                norm(
                    sub(
                        vec3(
                            membership_stock.get("origin_global_xyz_mm"),
                            f"{axis_id}/{member_id} membership stock origin",
                        ),
                        vec3(
                            surface_stock.get("origin_global_xyz_mm"),
                            f"{member_id} surface stock origin",
                        ),
                    )
                )
                <= LINEAR_TOLERANCE_MM,
                f"{axis_id}/{member_id} membership stock origin disagrees with surface register",
            )
            membership_basis = membership_stock.get("basis_columns_global_xyz")
            surface_basis = surface_stock.get("basis_columns_global_xyz")
            require(
                isinstance(membership_basis, Sequence)
                and len(membership_basis) == 3
                and isinstance(surface_basis, Sequence)
                and len(surface_basis) == 3,
                f"{axis_id}/{member_id} membership stock basis is malformed",
            )
            for basis_index in range(3):
                require(
                    norm(
                        sub(
                            vec3(
                                membership_basis[basis_index],
                                f"{axis_id}/{member_id} membership basis {basis_index}",
                            ),
                            vec3(
                                surface_basis[basis_index],
                                f"{member_id} surface basis {basis_index}",
                            ),
                        )
                    )
                    <= FRAME_TOLERANCE,
                    f"{axis_id}/{member_id} membership stock basis disagrees with surface register",
                )
            axis_stock = membership.get("axis_in_stock_frame")
            require(
                isinstance(axis_stock, Mapping),
                f"{axis_id}/{member_id} lacks axis-in-stock coordinates",
            )
            source_stock_datum = vec3(
                axis_stock.get("datum_stock_gqr_mm"),
                f"{axis_id}/{member_id} stock datum",
            )
            membership_basis_vectors = [
                vec3(
                    membership_basis[index],
                    f"{axis_id}/{member_id} membership basis {index}",
                )
                for index in range(3)
            ]
            expected_stock_datum = [
                dot(
                    sub(
                        source_datum,
                        vec3(
                            membership_stock["origin_global_xyz_mm"],
                            f"{axis_id}/{member_id} stock origin",
                        ),
                    ),
                    membership_basis_vectors[index],
                )
                for index in range(3)
            ]
            require(
                norm(sub(source_stock_datum, expected_stock_datum))
                <= LINEAR_TOLERANCE_MM,
                f"{axis_id}/{member_id} source axis datum disagrees with its saved stock coordinates",
            )
            frame = frames[member_id]
            grain = frame["grain_axis_global_xyz"]
            frame_origin = frame["origin_global_xyz_mm"]
            center_station = station(center, frame_origin, grain)
            source_station = station(source_datum, frame_origin, grain)
            delta = center_station - source_station
            identity_key = f"receiver:{member_id}:axis:{axis_id}:feature:{feature_id}"
            candidates.append(
                {
                    "identity_key": identity_key,
                    "kind": "receiver_bore_center",
                    "member_id": member_id,
                    "origin_global_xyz_mm": center,
                    "grain_station_mm": center_station,
                    "frame": frame,
                    "source_identity": {
                        "axis_id": axis_id,
                        "receiver_member_id": member_id,
                        "feature_id": feature_id,
                    },
                }
            )
            memberships.append(
                {
                    "axis_id": axis_id,
                    "receiver_member_id": member_id,
                    "member_role": "host" if member_id == host_id else "cleat",
                    "feature_id": feature_id,
                    "step_path": frame["step_path"],
                    "step_sha256": frame["step_sha256"],
                    "source_axis_datum_global_xyz_mm": source_datum,
                    "source_axis_direction_global_xyz": source_direction,
                    "source_axis_datum_grain_station_mm": source_station,
                    "saved_bore_center_global_xyz_mm": center,
                    "saved_bore_center_grain_station_mm": center_station,
                    "bore_center_minus_source_axis_datum_station_mm": delta,
                    "source_axis_to_saved_bore_center_line_distance_mm": distance,
                    "plane_identity_key": identity_key,
                    "member_frame_source": frame["frame_source"],
                    "member_frame_datum_status": frame["datum_status"],
                }
            )

        app = application_by_axis.get(str(axis_id))
        require(app is not None, f"{axis_id} has no source application plane")
        require(
            app.get("host") == host_id, f"{axis_id} application plane host mismatch"
        )
        require(
            app.get("host_step_path") == frames[host_id]["step_path"],
            f"{axis_id} application plane STEP mismatch",
        )
        require(
            app.get("host_step_sha256") == frames[host_id]["step_sha256"],
            f"{axis_id} application plane STEP hash mismatch",
        )
        app_point = vec3(
            app["application_datum_global_xyz_mm"], f"{axis_id} application datum"
        )
        host_frame = frames[host_id]
        host_station = station(
            app_point,
            host_frame["origin_global_xyz_mm"],
            host_frame["grain_axis_global_xyz"],
        )
        host_membership = next(
            row
            for row in memberships
            if row["axis_id"] == axis_id and row["receiver_member_id"] == host_id
        )
        app_delta = host_membership["saved_bore_center_grain_station_mm"] - host_station
        application_planes.append(
            {
                "axis_id": axis_id,
                "interface_id": f"{host_id}<-{cleat_id}",
                "member_id": host_id,
                "application_datum_global_xyz_mm": app_point,
                "source_application_grain_station_mm": host_station,
                "source_application_axis_global_xyz": list(
                    app["head_to_nut_axis_global_xyz"]
                ),
                "saved_bore_center_grain_station_mm": host_membership[
                    "saved_bore_center_grain_station_mm"
                ],
                "bore_center_minus_source_application_station_mm": app_delta,
                "host_step_path": app["host_step_path"],
                "host_step_sha256": app["host_step_sha256"],
                "datum_semantics": "source host application plane point from host-actions target_fastener_axes.lateral_plane_xyz_mm",
            }
        )

    bracket_rows: list[dict[str, Any]] = []
    host_inventory = host_actions.get("host_geometry_and_source_station_inventories")
    require(
        isinstance(host_inventory, Mapping),
        "host-actions host geometry inventory is missing",
    )
    for interface_id, (host_id, cleat_id) in sorted(EXPECTED_INTERFACES.items()):
        host_record = host_inventory.get(host_id)
        require(
            isinstance(host_record, Mapping),
            f"{interface_id} has no static host record",
        )
        bracket_map = host_record.get("finished_step_bracket_sections")
        require(
            isinstance(bracket_map, Mapping),
            f"{host_id} has no finished-step bracket sections",
        )
        brackets = bracket_map.get(cleat_id)
        require(
            isinstance(brackets, Mapping), f"{interface_id} has no bracket sections"
        )
        require(
            set(brackets) == {"before", "after"},
            f"{interface_id} must have before and after bracket sections",
        )
        for side in ("before", "after"):
            section = brackets[side]
            require(
                isinstance(section, Mapping),
                f"{interface_id} {side} bracket section is malformed",
            )
            require(
                section.get("step_path") == frames[host_id]["step_path"],
                f"{interface_id} {side} bracket STEP path mismatch",
            )
            require(
                section.get("step_sha256") == frames[host_id]["step_sha256"],
                f"{interface_id} {side} bracket STEP hash mismatch",
            )
            origin = vec3(
                section.get("plane_origin_xyz_mm"),
                f"{interface_id} {side} source plane origin",
            )
            normal = vec3(
                section.get("section_plane_normal_global_xyz"),
                f"{interface_id} {side} source plane normal",
            )
            grain = frames[host_id]["grain_axis_global_xyz"]
            require(
                abs(abs(dot(normal, grain)) - 1.0) <= FRAME_TOLERANCE,
                f"{interface_id} {side} bracket plane normal is not host grain",
            )
            source_station = finite(
                section.get("station_mm"), f"{interface_id} {side} source station"
            )
            computed_station = station(
                origin, frames[host_id]["origin_global_xyz_mm"], grain
            )
            require(
                abs(computed_station - source_station) <= LINEAR_TOLERANCE_MM,
                f"{interface_id} {side} source bracket station does not match its plane origin",
            )
            identity_key = f"bracket:{interface_id}:{side}"
            terminal_boundary = _terminal_bracket_flag(
                host_actions, interface_id, side, source_station
            )
            candidates.append(
                {
                    "identity_key": identity_key,
                    "kind": "host_bracket_section",
                    "member_id": host_id,
                    "origin_global_xyz_mm": origin,
                    "grain_station_mm": computed_station,
                    "frame": frames[host_id],
                    "source_identity": {
                        "interface_id": interface_id,
                        "host": host_id,
                        "receiving_cleat": cleat_id,
                        "side": side,
                        "source_station_mm": source_station,
                        "source_plane_normal_global_xyz": normal,
                        "terminal_boundary": terminal_boundary,
                    },
                }
            )
            bracket_rows.append(
                {
                    "interface_id": interface_id,
                    "host": host_id,
                    "receiving_cleat": cleat_id,
                    "side": side,
                    "source_station_mm": source_station,
                    "source_plane_origin_global_xyz_mm": origin,
                    "source_plane_normal_global_xyz": normal,
                    "terminal_boundary": terminal_boundary,
                    "source_area_mm2_from_host_actions": finite(
                        section.get("section_area_mm2_from_saved_finished_step"),
                        f"{interface_id} {side} source area",
                    ),
                    "source_geometry_status": section.get("source_geometry_status"),
                    "plane_identity_key": identity_key,
                }
            )
    require(
        len(bracket_rows) == 8,
        "upper outer section plan must include eight before/after host bracket sections",
    )
    require(
        len(memberships) == 16,
        "each of eight selected upper outer axes must have exactly two receiver memberships",
    )
    require(
        len(application_planes) == 8,
        "each selected upper outer axis must have one source application plane",
    )

    planes, identity_to_plane = _merge_plane_candidates(candidates)
    for membership in memberships:
        membership["section_plane_id"] = identity_to_plane[
            membership.pop("plane_identity_key")
        ]
    for record in bracket_rows:
        record["section_plane_id"] = identity_to_plane[record.pop("plane_identity_key")]

    member_rows = [
        {key: value for key, value in frames[member_id].items()}
        for member_id in sorted(frames)
    ]
    require(set(frames) == MEMBERS, "section member set mismatch")
    return {
        "schema": SOURCE_PLAN_SCHEMA,
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "claim_boundary": {
            "scope": "five saved upper outer finished solids; eight upper outer bolt axes; sixteen receiver memberships; eight existing host bracket sections",
            "excluded": [
                "other joints",
                "the other 84 candidate bolt axes",
                "92-axis redesign",
                "modified or regenerated frame geometry",
            ],
            "measured_output": "geometric section area, centroid, area covariance integrals, connected component and wire topology only",
            "not_established": [
                "stress or strain",
                "resistance or capacity",
                "common-strain compatibility",
                "integrated FE traction",
                "connection acceptance",
                "physical inspection or delivered stock datum",
            ],
        },
        "source_counts": {
            "saved_solids": len(member_rows),
            "selected_bolt_axes": len(selected_rows),
            "receiver_memberships": len(memberships),
            "source_application_planes": len(application_planes),
            "host_bracket_sections": len(bracket_rows),
            "unique_section_planes": len(planes),
            "coincident_plane_groups": sum(
                1 for plane in planes if plane["source_identity_count"] > 1
            ),
        },
        "member_frames_and_step_bindings": member_rows,
        "axis_memberships": sorted(
            memberships, key=lambda row: (row["axis_id"], row["receiver_member_id"])
        ),
        "source_application_planes": sorted(
            application_planes, key=lambda row: row["axis_id"]
        ),
        "host_bracket_sections": sorted(
            bracket_rows,
            key=lambda row: (row["host"], row["receiving_cleat"], row["side"]),
        ),
        "section_planes": planes,
    }


def _terminal_bracket_flag(
    host_actions: Mapping[str, Any],
    interface_id: str,
    side: str,
    source_station: float,
) -> bool:
    field = (
        "before_cut_at_host_terminal_boundary"
        if side == "before"
        else "after_cut_at_host_terminal_boundary"
    )
    station_field = (
        "cut_before_group_station_mm"
        if side == "before"
        else "cut_after_group_station_mm"
    )
    found: list[bool] = []
    for state in host_actions.get("states", []):
        for interface in state.get("interfaces", []):
            if interface.get("interface_id") != interface_id:
                continue
            bracket = interface.get("bracket")
            require(
                isinstance(bracket, Mapping),
                f"{interface_id} has no bracket annotations",
            )
            require(
                field in bracket and station_field in bracket,
                f"{interface_id} lacks {side} bracket annotation",
            )
            require(
                abs(
                    finite(
                        bracket[station_field], f"{interface_id} {side} bracket station"
                    )
                    - source_station
                )
                <= LINEAR_TOLERANCE_MM,
                f"{interface_id} {side} action station disagrees with saved STEP bracket plane",
            )
            terminal = bracket[field]
            require(
                isinstance(terminal, bool),
                f"{interface_id} {side} terminal marker is not boolean",
            )
            found.append(terminal)
    require(found, f"{interface_id} has no frozen {side} bracket annotation")
    require(
        all(flag == found[0] for flag in found),
        f"{interface_id} {side} terminal marker varies by state",
    )
    return found[0]


def _surface_feature_map(
    surface: Mapping[str, Any], member_id: str
) -> dict[str, dict[str, Any]]:
    features = surface.get("features")
    require(isinstance(features, list), f"{member_id} surface feature list is missing")
    result: dict[str, dict[str, Any]] = {}
    for feature in features:
        require(isinstance(feature, Mapping), f"{member_id} feature row is malformed")
        feature_id = feature.get("feature_id")
        require(
            isinstance(feature_id, str) and feature_id,
            f"{member_id} feature row has no ID",
        )
        require(
            feature_id not in result,
            f"{member_id} has duplicate feature ID {feature_id}",
        )
        result[feature_id] = dict(feature)
    return result


def load_sources(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read and source-pin all packet inputs without importing CadQuery."""
    artifacts: dict[str, Any] = {}
    for key, relative in INPUT_ARTIFACTS.items():
        path = _rooted_path(root, relative)
        require(
            path.is_file(), f"required input artifact is missing: {relative.as_posix()}"
        )
        if key.endswith("source_pins"):
            continue
        artifacts[key] = (
            read_json(path)
            if key
            in {
                "host_actions",
                "finished_surfaces",
                "axis_features",
                "stock_envelopes",
            }
            else path
        )
    _verify_report_links(root, artifacts)
    direct = {
        key: relative
        for key, relative in INPUT_ARTIFACTS.items()
        if not key.endswith("source_pins")
    }
    local_code = {
        **LOCAL_CODE_BINDINGS,
    }
    pins = collect_pin_closure(
        root,
        [
            INPUT_ARTIFACTS[key]
            for key in (
                "host_actions_source_pins",
                "finished_surfaces_source_pins",
                "axis_features_source_pins",
                "stock_envelopes_source_pins",
            )
        ],
        direct,
        local_code,
    )
    return artifacts, pins


def build_live_source_plan(
    root: Path = ROOT,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    artifacts, pins = load_sources(root)
    plan = build_source_plan(root, artifacts)
    return plan, pins


def build_source_pin_document(pins: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema": PINS_SCHEMA,
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "pin_semantics": "current bytes, SHA-256, and size for every direct artifact, producer/test, saved STEP, and recursively verified upstream pin",
        "pins": list(pins),
    }


def _import_kernel(path: Path) -> Any:
    require(path.is_file(), f"section geometry kernel is not ready: missing {path}")
    spec = importlib.util.spec_from_file_location("upper_outer_section_geometry", path)
    require(
        spec is not None and spec.loader is not None,
        "cannot load section geometry kernel",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(
        callable(getattr(module, "section_properties", None)),
        "section geometry kernel has no section_properties API",
    )
    return module


def compute_sections(
    root: Path,
    source_plan: Mapping[str, Any],
    source_pins: Sequence[Mapping[str, Any]],
    *,
    kernel_path: Path | None = None,
) -> dict[str, Any]:
    """Import each saved solid once and evaluate each deduplicated plane once."""
    kernel = _import_kernel(kernel_path or _rooted_path(root, KERNEL_SOURCE))
    try:
        import cadquery as cq
    except ImportError as exc:
        raise SourceRefusal(
            "CadQuery is unavailable for saved-solid section queries"
        ) from exc

    source_plan_bytes = canonical_bytes(source_plan)
    source_pin_document = build_source_pin_document(source_pins)
    source_pin_bytes = canonical_bytes(source_pin_document)
    frames = {
        row["member_id"]: row for row in source_plan["member_frames_and_step_bindings"]
    }
    shape_by_member: dict[str, Any] = {}
    imports: list[dict[str, Any]] = []
    section_rows: list[dict[str, Any]] = []

    for member_id in sorted(frames):
        frame = frames[member_id]
        step_path = _rooted_path(root, frame["step_path"])
        workplane = cq.importers.importStep(str(step_path))
        shape = workplane.val()
        solids = shape.Solids()
        require(
            len(solids) == 1, f"{member_id} saved STEP imported as {len(solids)} solids"
        )
        shape_by_member[member_id] = shape
        imports.append(
            {
                "member_id": member_id,
                "step_path": frame["step_path"],
                "step_sha256": frame["step_sha256"],
                "step_size_bytes": frame["step_size_bytes"],
                "import_count": 1,
                "imported_solid_count": len(solids),
            }
        )

    for plane in source_plan["section_planes"]:
        frame = frames[plane["member_id"]]
        result = kernel.section_properties(
            shape_by_member[plane["member_id"]],
            plane["plane_origin_global_xyz_mm"],
            plane["grain_axis_global_xyz"],
            plane["section_u_global_xyz"],
            plane["section_v_global_xyz"],
            tolerance_mm=LINEAR_TOLERANCE_MM,
        )
        require(
            isinstance(result, Mapping),
            f"kernel returned no section properties for {plane['plane_id']}",
        )
        section_rows.append({**plane, "properties": dict(result)})

    return {
        "schema": OUTPUT_SCHEMA,
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_plan_schema": SOURCE_PLAN_SCHEMA,
        "source_plan_sha256": sha256_bytes(source_plan_bytes),
        "source_pins_sha256": sha256_bytes(source_pin_bytes),
        "claim_boundary": source_plan["claim_boundary"],
        "source_counts": source_plan["source_counts"],
        "member_frames_and_step_bindings": source_plan[
            "member_frames_and_step_bindings"
        ],
        "axis_memberships": source_plan["axis_memberships"],
        "source_application_planes": source_plan["source_application_planes"],
        "host_bracket_sections": source_plan["host_bracket_sections"],
        "saved_solid_imports": imports,
        "section_properties": section_rows,
        "kernel_claim_boundary": "geometric section properties only; no stress, resistance, common-strain, integrated-traction, or acceptance result",
    }


def execute(
    root: Path, mode: str, *, output: Path = OUTPUT, pins_output: Path = PINS_OUTPUT
) -> None:
    source_plan, pins = build_live_source_plan(root)
    source_pin_document = build_source_pin_document(pins)
    result = compute_sections(root, source_plan, pins)
    expected = {
        output: canonical_bytes(result),
        pins_output: canonical_bytes(source_pin_document),
    }
    if mode == "verify":
        for path, raw in expected.items():
            require(path.is_file(), f"verification output is missing: {path}")
            actual = path.read_bytes()
            require(actual == raw, f"verification output differs: {path}")
        return
    require(mode == "write", f"unsupported execution mode: {mode}")
    for path, raw in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write",
        action="store_true",
        help="recompute and write ignored local JSON evidence",
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="recompute and compare exact ignored local JSON evidence without writing",
    )
    mode.add_argument(
        "--plan-only",
        action="store_true",
        help="validate sources and print the metadata-only section plan counts",
    )
    args = parser.parse_args(argv)
    try:
        if args.plan_only:
            plan, pins = build_live_source_plan(ROOT)
            print(
                json.dumps(
                    {
                        "source_counts": plan["source_counts"],
                        "verified_input_pin_count": len(pins),
                        "kernel_ready": KERNEL_SOURCE.is_file()
                        and KERNEL_TEST.is_file(),
                        "geometry_executed": False,
                    },
                    sort_keys=True,
                )
            )
        else:
            execute(ROOT, "write" if args.write else "verify")
    except (SourceRefusal, OSError, ImportError, ValueError) as exc:
        print(f"source-bound section production refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
