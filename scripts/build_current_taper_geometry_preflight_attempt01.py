#!/usr/bin/env python3
"""Measure the reviewed current CAD taper; do not disposition fresh-case criteria."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
PACKET = BASE + "current-taper-geometry-preflight-attempt01"
BUNDLE = (
    BASE
    + "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
)
FRAME_MAP = (
    BASE
    + "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
)
STOCK = "docs/floor-flush-construction-kerf-right/stock-profiles.json"
INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
PREDICATES = "scripts/floor_taper_checks.py"
CRITERIA = "docs/floor-runner-mvp-criteria.md"
PRODUCER = "scripts/build_current_taper_geometry_preflight_attempt01.py"
TESTS = "tests/test_current_taper_geometry_preflight_attempt01.py"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
LEGS = ("lumber_leg_left", "lumber_leg_right")
GRAIN = (0.0, -0.2391518319632432, 0.9709821838059772)
GEOMETRY_TOLERANCE_MM = 1e-5
AXIS_TOLERANCE = 1e-10
REPORT = "current-taper-geometry-preflight.json"
CRITERION_IDS = (
    "taper_taper_at_least_one_in_ten",
    "taper_intended_stock_and_runout",
)
ANCHOR_PINS = {
    "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    INVENTORY: "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    STOCK: "65a4301c639a6eff14cb4365f321d4ab4712746dd3c916ffc14b00645841dfa8",
    PREDICATES: "bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3",
    CRITERIA: "f6b5591bbbb2aaf87553095e04fbe5abd66d38a926a3efb66711420492f0f090",
    BUNDLE: "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    FRAME_MAP: "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
}
LEG_STEP_PINS = {
    "lumber_leg_left": "1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065",
    "lumber_leg_right": "e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4",
}


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number: {value}")


def read_json(path: Path) -> dict[str, Any]:
    result = json.loads(
        path.read_text(), object_pairs_hook=_object, parse_constant=_constant
    )
    if not isinstance(result, dict):
        raise TypeError(f"JSON object required: {path}")
    return result


def finite(value: Any) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError("finite numeric coordinate or dimension required")
    return float(value)


def vector(value: Any) -> tuple[float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError("three finite coordinates required")
    return tuple(finite(x) for x in value)


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def close(a: float, b: float, tolerance: float = GEOMETRY_TOLERANCE_MM) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance)


def verify_pins(root: Path, pins: dict[str, str]) -> None:
    for relative, expected in pins.items():
        path = root / relative
        if path.is_symlink() or not path.is_file() or sha256(path) != expected:
            raise ValueError(f"source hash mismatch: {relative}")


def unique_rows(
    rows: list[dict[str, Any]], key: str, count: int
) -> dict[str, dict[str, Any]]:
    ids = [row.get(key) for row in rows]
    if (
        len(ids) != count
        or any(not isinstance(x, str) or not x for x in ids)
        or len(set(ids)) != count
    ):
        raise ValueError(f"expected exactly {count} unique {key} rows")
    return dict(zip(ids, rows, strict=True))


def validate_identity(sources: dict[str, dict[str, Any]]) -> None:
    candidate = sources["wood-joints-candidate.json"]
    if (
        candidate.get("candidate") != CANDIDATE
        or candidate.get("current_development_revision", {}).get("revision_id")
        != REVISION
    ):
        raise ValueError("current candidate/revision identity mismatch")
    for path in (BUNDLE, FRAME_MAP):
        if (
            sources[path].get("candidate") != CANDIDATE
            or sources[path].get("geometry_revision_id") != REVISION
        ):
            raise ValueError(f"current candidate/revision identity mismatch: {path}")
    bundle = unique_rows(sources[BUNDLE]["members"], "member_id", 50)
    if Counter(row["member_kind"] for row in bundle.values()) != {
        "timber": 20,
        "plywood_panel": 6,
        "candidate_block": 24,
    }:
        raise ValueError("50-member bundle kind inventory mismatch")
    frames = unique_rows(sources[FRAME_MAP]["members"], "member_id", 20)
    if set(frames) != {
        name for name, row in bundle.items() if row["member_kind"] == "timber"
    }:
        raise ValueError("timber frame and bundle member IDs differ")
    for name in LEGS:
        if name not in bundle or name not in frames:
            raise ValueError(f"missing exact current leg: {name}")
        row = bundle[name]
        if (
            row["geometry_source"] != "current_source_part_unchanged_in_composition"
            or row["step_sha256"] != LEG_STEP_PINS[name]
        ):
            raise ValueError(f"current leg lineage mismatch: {name}")
        expected_step = str(Path(BUNDLE).parent / "members" / f"{name}.step")
        if frames[name]["current_geometry_lineage"]["step_file"] != expected_step:
            raise ValueError(f"current leg STEP path mismatch: {name}")
        if (
            frames[name]["current_geometry_lineage"]["step_sha256"]
            != row["step_sha256"]
        ):
            raise ValueError(f"current leg frame/STEP mismatch: {name}")
        validate_grain(
            frames[name]["conditional_grain_assignment"]["proposed_global_xyz"]
        )


def validate_grain(value: Any) -> tuple[float, float, float]:
    grain = vector(value)
    if not close(dot(grain, grain), 1.0, AXIS_TOLERANCE) or any(
        not close(a, b, AXIS_TOLERANCE) for a, b in zip(grain, GRAIN, strict=True)
    ):
        raise ValueError("wrong current leg longitudinal axis")
    return grain


def load_sources(root: Path = ROOT) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    verify_pins(root, ANCHOR_PINS)
    sources = {
        path: read_json(root / path) for path in ANCHOR_PINS if path.endswith(".json")
    }
    validate_identity(sources)
    pins = dict(ANCHOR_PINS)
    inherited = dict(sources[BUNDLE]["source_files_sha256"])
    for path, record in sources[FRAME_MAP]["source_pins"].items():
        if path in inherited and inherited[path] != record["sha256"]:
            raise ValueError(f"conflicting inherited source pin: {path}")
        inherited[path] = record["sha256"]
    for row in sources[BUNDLE]["members"]:
        path = (Path(BUNDLE).parent.parent / row["step_file"]).as_posix()
        inherited[path] = row["step_sha256"]
    for path, digest in inherited.items():
        if path in pins and pins[path] != digest:
            raise ValueError(f"conflicting source pin: {path}")
        pins[path] = digest
    verify_pins(root, pins)
    pins.update({path: sha256(root / path) for path in (PRODUCER, TESTS)})
    return sources, pins


def planar_face_records(shape: Any) -> list[dict[str, Any]]:
    """Read exact BRep plane, vertices and edges; never use a face ordinal."""
    result = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        result.append(
            {
                "normal_xyz": list(vector(face.normalAt().toTuple())),
                "area_mm2": finite(face.Area()),
                "wire_count": len(face.Wires()),
                "vertices_xyz_mm": sorted(
                    [list(vector(v.Center().toTuple())) for v in face.Vertices()]
                ),
                "edges": sorted(
                    [
                        {
                            "type": edge.geomType(),
                            "length_mm": finite(edge.Length()),
                            "vertices_xyz_mm": sorted(
                                [
                                    list(vector(v.Center().toTuple()))
                                    for v in edge.Vertices()
                                ]
                            ),
                        }
                        for edge in face.Edges()
                    ],
                    key=lambda row: row["vertices_xyz_mm"],
                ),
            }
        )
    return result


def measure_taper(
    name: str, faces: list[dict[str, Any]], grain_value: Any
) -> dict[str, Any]:
    if name not in LEGS:
        raise ValueError("wrong current leg ID")
    grain = validate_grain(grain_value)
    cross_grain = (0.0, grain[2], -grain[1])
    possible = []
    for face in faces:
        normal = vector(face["normal_xyz"])
        if not close(dot(normal, normal), 1.0, AXIS_TOLERANCE):
            raise ValueError("nonunit plane normal")
        # No nominal slope is used to select the face being tested.
        if 1e-8 < abs(normal[0]) < 1.0 - 1e-8 and abs(dot(normal, grain)) > 1e-8:
            possible.append(face)
    if len(possible) != 1:
        raise ValueError(f"missing or ambiguous taper plane: {name}")
    face = possible[0]
    normal = vector(face["normal_xyz"])
    vertices = [vector(v) for v in face["vertices_xyz_mm"]]
    if (
        len(vertices) != 4
        or len(set(vertices)) != 4
        or face["wire_count"] != 1
        or len(face["edges"]) != 4
    ):
        raise ValueError("malformed taper face topology")
    if finite(face["area_mm2"]) <= 0 or not close(
        dot(normal, cross_grain), 0.0, AXIS_TOLERANCE
    ):
        raise ValueError("malformed taper plane or cross-grain alignment")
    normal_sign = 1.0 if name.endswith("left") else -1.0
    if normal[0] * normal_sign <= 0 or dot(normal, grain) >= 0:
        raise ValueError("taper plane has wrong inward-face orientation")
    projected = [(v[0], dot(v, grain), dot(v, cross_grain)) for v in vertices]
    xmin, xmax = min(p[0] for p in projected), max(p[0] for p in projected)
    start, end = min(p[1] for p in projected), max(p[1] for p in projected)
    qmin, qmax = min(p[2] for p in projected), max(p[2] for p in projected)
    run, depth, width = end - start, xmax - xmin, qmax - qmin
    if min(run, depth, width) <= 0:
        raise ValueError("degenerate taper face")
    expected_corners = [
        (xmin if normal_sign > 0 else xmax, start, q) for q in (qmin, qmax)
    ] + [(xmax if normal_sign > 0 else xmin, end, q) for q in (qmin, qmax)]
    if not all(
        sum(
            all(close(a, b) for a, b in zip(point, corner, strict=True))
            for point in projected
        )
        == 1
        for corner in expected_corners
    ):
        raise ValueError("malformed taper corner geometry")
    plane_offset = dot(normal, vertices[0])
    if any(not close(dot(normal, v), plane_offset) for v in vertices):
        raise ValueError("taper vertices do not lie on plane")
    expected_edge_lengths = sorted(
        [width, width, math.hypot(run, depth), math.hypot(run, depth)]
    )
    lengths = []
    endpoint_degrees = Counter()
    for edge in face["edges"]:
        ends = [vector(v) for v in edge["vertices_xyz_mm"]]
        length = finite(edge["length_mm"])
        if (
            edge["type"] != "LINE"
            or len(ends) != 2
            or ends[0] == ends[1]
            or not all(v in vertices for v in ends)
        ):
            raise ValueError("malformed taper straight-edge topology")
        if not close(math.dist(*ends), length):
            raise ValueError("taper straight-edge length mismatch")
        lengths.append(length)
        endpoint_degrees.update(ends)
    if set(endpoint_degrees) != set(vertices) or any(
        n != 2 for n in endpoint_degrees.values()
    ):
        raise ValueError("taper edges do not form one four-corner loop")
    if not all(
        close(a, b) for a, b in zip(sorted(lengths), expected_edge_lengths, strict=True)
    ) or not close(face["area_mm2"], width * math.hypot(run, depth), 1e-3):
        raise ValueError("taper area or edge extent mismatch")
    plane_ratio = abs(normal[0] / dot(normal, grain))
    if not close(plane_ratio, run / depth, 1e-8):
        raise ValueError("plane and vertex slope measurements disagree")
    return {
        "member_id": name,
        "grain_axis_xyz": list(grain),
        "cross_grain_axis_xyz": list(cross_grain),
        "taper_face_geometry": face,
        "taper_face_geometry_sha256": hashlib.sha256(json_bytes(face)).hexdigest(),
        "taper_start_grain_station_mm": start,
        "taper_end_grain_station_mm": end,
        "taper_run_mm": run,
        "recess_depth_mm": depth,
        "cross_grain_extent_mm": width,
        "taper_inner_x_at_start_mm": xmin if normal_sign > 0 else xmax,
        "taper_inner_x_at_end_mm": xmax if normal_sign > 0 else xmin,
        "run_over_depth": run / depth,
        "plane_normal_run_over_depth": plane_ratio,
        "slope_margin_before_tolerance_mm": run - 10.0 * depth,
    }


def geometry_predicates(
    run: Any, removed: Any, stock_width: Any, stock_depth: Any
) -> dict[str, bool]:
    run, removed, b, d = (finite(x) for x in (run, removed, stock_width, stock_depth))
    if min(run, removed, b, d) <= 0:
        raise ValueError("positive taper dimensions required")
    # Exact expressions from the hash-pinned source. Its other native checks are separate.
    return {
        CRITERION_IDS[0]: run >= 10 * removed - 1e-6,
        CRITERION_IDS[1]: math.isclose(b, 88.9, abs_tol=1e-5)
        and math.isclose(d, 139.7, abs_tol=1e-5)
        and math.isclose(removed, 38.1, abs_tol=1e-5)
        and run >= 457.2 - 1e-5,
    }


def build_report(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    import cadquery as cq

    sources, pins = load_sources(root)
    versions = {
        name: importlib.metadata.version(name) for name in ("cadquery", "cadquery-ocp")
    }
    if versions != {"cadquery": "2.8.0", "cadquery-ocp": "7.9.3.1.1"}:
        raise ValueError("pinned offline CAD environment is unavailable")
    bundle = {r["member_id"]: r for r in sources[BUNDLE]["members"]}
    frames = {r["member_id"]: r for r in sources[FRAME_MAP]["members"]}
    inventory = {r["part_id"]: r for r in sources[INVENTORY]["parts"]}
    measurements = []
    for name in LEGS:
        step_path = (Path(BUNDLE).parent.parent / bundle[name]["step_file"]).as_posix()
        shape = cq.importers.importStep(str(root / step_path)).val()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f"invalid or non-single-solid current STEP: {name}")
        if not close(
            finite(shape.Volume()),
            bundle[name]["step_roundtrip_summary"]["volume_mm3"],
            1e-3,
        ):
            raise ValueError(f"current STEP volume readback mismatch: {name}")
        grain = frames[name]["conditional_grain_assignment"]["proposed_global_xyz"]
        if list(validate_grain(inventory[name]["grain_axis_global_xyz"])) != grain:
            raise ValueError(f"inventory and frame longitudinal axes differ: {name}")
        row = measure_taper(name, planar_face_records(shape), grain)
        vertices = [vector(v.Center().toTuple()) for v in shape.Vertices()]
        q = vector(row["cross_grain_axis_xyz"])
        stock_width = max(v[0] for v in vertices) - min(v[0] for v in vertices)
        stock_depth = max(dot(v, q) for v in vertices) - min(
            dot(v, q) for v in vertices
        )
        source_section = sources[STOCK][name]["stock_blank_allowance_mm"][1:]
        if not all(
            close(a, b)
            for a, b in zip(
                sorted(source_section), sorted([stock_width, stock_depth]), strict=True
            )
        ) or not close(stock_depth, row["cross_grain_extent_mm"]):
            raise ValueError(
                f"actual STEP and intended stock cross-section differ: {name}"
            )
        inner_x = (
            max(v[0] for v in vertices)
            if name.endswith("left")
            else min(v[0] for v in vertices)
        )
        if not close(row["taper_inner_x_at_end_mm"], inner_x):
            raise ValueError(f"taper does not return to full inner stock face: {name}")
        row.update(
            {
                "step_file": step_path,
                "step_sha256": pins[step_path],
                "geometry_source": bundle[name]["geometry_source"],
                "stock_width_mm": stock_width,
                "stock_depth_mm": stock_depth,
                "source_stock_section_record_mm": source_section,
                "cad_predicate_results": geometry_predicates(
                    row["taper_run_mm"],
                    row["recess_depth_mm"],
                    stock_width,
                    stock_depth,
                ),
                "current_1_to_12_geometry_matches": all(
                    close(a, b)
                    for a, b in zip(
                        [
                            stock_width,
                            stock_depth,
                            row["taper_run_mm"],
                            row["recess_depth_mm"],
                        ],
                        [88.9, 139.7, 457.2, 38.1],
                        strict=True,
                    )
                ),
            }
        )
        measurements.append(row)
    adopted_text = (root / CRITERIA).read_text()
    criterion_rows = [
        line
        for line in adopted_text.splitlines()
        if any(f"`{key}`" in line for key in CRITERION_IDS)
    ]
    if len(criterion_rows) != 2 or any(
        "FR-3 and fresh case" not in row for row in criterion_rows
    ):
        raise ValueError("adopted fresh-case criterion text differs")
    supported = all(
        all(row["cad_predicate_results"].values())
        and row["current_1_to_12_geometry_matches"]
        for row in measurements
    )
    report = {
        "schema": "wood_joint_current_taper_geometry_preflight/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "status": "current_cad_geometry_preflight_supported"
        if supported
        else "current_cad_geometry_preflight_failed",
        "cad_geometry_preflight_supported": supported,
        "full_criterion_dispositions": dict.fromkeys(CRITERION_IDS, "pending"),
        "fresh_current_case_prerequisites_satisfied": False,
        "engineering_mvp_complete": False,
        "release": False,
        "native_run_performed": False,
        "delivered_stock_observed": False,
        "cad_environment": versions,
        "bundle_member_count": 50,
        "measured_member_ids": list(LEGS),
        "geometry_measurement_tolerance_mm": GEOMETRY_TOLERANCE_MM,
        "predicate_source": {
            "path": PREDICATES,
            "sha256": pins[PREDICATES],
            "lines": [116, 117, 118],
            "slope_tolerance_mm": 1e-6,
            "stock_and_runout_absolute_tolerance_mm": 1e-5,
            "stock_isclose_relative_tolerance": 1e-9,
        },
        "adopted_criterion_source": {
            "path": CRITERIA,
            "sha256": pins[CRITERIA],
            "rows": criterion_rows,
            "case_prerequisite": "Missing identity, provenance, convergence or inventory stops component assessment.",
        },
        "members": measurements,
        "remaining_requirements": [
            "Authenticate actual current native taper geometry against these same CAD/STEP fingerprints.",
            "Satisfy identity, provenance, convergence, equilibrium and complete inventory prerequisites for all six fresh current cases.",
            "Bind the geometry preflight to an independently reviewed per-scope criterion contract and fresh case evidence before full disposition.",
        ],
        "claim_limits": [
            "Current CAD taper input geometry only; no historical criterion pass is transferred.",
            "Longitudinal direction and intended stock are recorded design assumptions, not delivered-board observations.",
            "No native/CAD equivalence, mesh volume, section sampling, unbored-region applicability, resistance, joint response or structural acceptance is established.",
            "No geometry, stock purchase, candidate selection, physical work or release is authorized.",
        ],
    }
    return report, {
        "schema": "wood_joint_taper_preflight_source_pins/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "files_sha256": pins,
    }


def packet_files(root: Path = ROOT) -> dict[str, bytes]:
    report, pins = build_report(root)
    report_bytes = json_bytes(report)
    verification = {
        "schema": "wood_joint_taper_preflight_verification/v1",
        "scope": "current_CAD_geometry_input_only",
        "source_count": len(pins["files_sha256"]),
        "member_count": 2,
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "cad_geometry_preflight_supported": report["cad_geometry_preflight_supported"],
        "full_criteria_pending": list(CRITERION_IDS),
        "native_run_performed": False,
        "release": False,
    }
    readme = f"""# Current-CAD taper geometry preflight — attempt01

This input-only packet authenticates `{CANDIDATE}` revision `{REVISION}`.
Both current leg STEP BReps have a measured 457.2 mm run, 38.1 mm recess,
12:1 run/depth ratio, and 88.9 × 139.7 mm intended section. The two exact
adopted geometry predicates pass on these CAD inputs. **Both full criteria
remain pending:** their adopted table requires FR-3 and a fresh current case.

The producer verifies {len(pins["files_sha256"])} source and implementation pins,
including the 50-member bundle, all 50 STEP hashes, the current candidate,
the longitudinal-axis map, the stock records and exact adopted predicate/text.
It imports only the two current leg STEP solids with CadQuery 2.8.0 and OCP
7.9.3.1.1. Taper selection uses plane orientation, never a face ordinal or a
nominal 12:1 slope. Four straight edges, the four corners, plane normal, area,
cross-grain extent and full-stock return independently constrain each result.
The geometric face record is hashed. Length consistency uses 1e-5 mm; area
uses 1e-3 mm²; the adopted predicates retain their own exact source tolerances.

This closes the missing current-CAD taper dimension input. It does not prove
native/CAD equivalence, mesh volume, section coverage, unbored torsion method
applicability, stock receipt, joint mechanics, resistance or acceptance. It
imports no historical result. All release and engineering completion flags
remain false. Fresh native geometry/case authentication and an independently
reviewed criterion binding remain required.

From the repository root:

```sh
.venv/bin/python -B {PRODUCER} --check
.venv/bin/python -B -m pytest -q -p no:cacheprovider {TESTS}
.venv/bin/ruff check --no-cache {PRODUCER} {TESTS}
```

From this packet directory, `sha256sum -c SHA256SUMS` verifies its local files.
`--write` creates the packet once and refuses an existing directory. `--check`
authenticates the pinned inputs, remeasures both exact BReps and compares every
report, verification, source-pin, README and checksum byte. No solver or
geometry export is invoked.
"""
    files = {
        REPORT: report_bytes,
        "source-pins.json": json_bytes(pins),
        "verification.json": json_bytes(verification),
        "README.md": readme.encode(),
    }
    files["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in sorted(files.items())
    ).encode()
    return files


def check_packet(root: Path = ROOT) -> dict[str, Any]:
    for name, expected in packet_files(root).items():
        path = root / PACKET / name
        if not path.is_file() or path.read_bytes() != expected:
            raise ValueError(f"packet replay mismatch: {name}")
    return read_json(root / PACKET / "verification.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--write", action="store_true")
    operation.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        print(json.dumps(check_packet(), sort_keys=True))
    else:
        files = packet_files()
        directory = ROOT / PACKET
        directory.mkdir(exist_ok=False)
        for name, data in files.items():
            with (directory / name).open("xb") as handle:
                handle.write(data)
        print(f"Wrote input-only packet: {PACKET}")


if __name__ == "__main__":
    main()
