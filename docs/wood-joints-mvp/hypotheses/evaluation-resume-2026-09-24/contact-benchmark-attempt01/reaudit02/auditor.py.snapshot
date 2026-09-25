"""Prepare and audit a tiny CalculiX 2.21 contact-force/wrench benchmark.

The two generated decks reverse only the slave/master orientation of one
frictionless, face-to-face contact pair.  This checks solver contact-output
ownership, force location, and wrench accounting.  It does not model a wood
joint, establish a stiffness or resistance, or qualify any structure.  The
module never invokes CalculiX.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "fea" / "results" / "ccx_contact_wrench_benchmark"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
SCENARIOS = ("upper_slave", "lower_slave")
DECK_NAMES = {"upper_slave": "upper-slave.inp", "lower_slave": "lower-slave.inp"}
SOURCE_NAMES = {
    "fea/contact_wrench_benchmark.py",
    "fea/results/ccx_contact_wrench_benchmark/upper-slave.inp",
    "fea/results/ccx_contact_wrench_benchmark/lower-slave.inp",
}

MANUAL = {
    "title": "CalculiX 2.21 User's Manual",
    "url": "https://www.dhondt.de/ccx_2.21.pdf",
    "contact_print_pages": [430, 431],
}
LOAD_FORCE_N = (0.0, 0.0, -100.0)
LOAD_MOMENT_NMM = (-1000.0, 1000.0, 0.0)
CONTACT_CENTROID_MM = (10.0, 10.0, 0.0)
CONTACT_AREA_MM2 = 400.0
NORMAL_PENALTY_N_PER_MM3 = 10000.0
TOP_NODE_COORDS_MM = {
    15: (0.0, 0.0, 10.0),
    16: (20.0, 0.0, 10.0),
    17: (20.0, 20.0, 10.0),
    18: (0.0, 20.0, 10.0),
}
BOTTOM_NODE_COORDS_MM = {
    1: (0.0, 0.0, -10.0),
    2: (20.0, 0.0, -10.0),
    3: (20.0, 20.0, -10.0),
    4: (0.0, 20.0, -10.0),
}

_SCENARIO_ROWS: dict[str, dict[str, Any]] = {
    "upper_slave": {
        "slave_surface": "UPPER_INTERFACE",
        "master_surface": "LOWER_INTERFACE",
        "cf_owner_body": "UPPER",
        "expected_slave_mean_normal": [0.0, 0.0, -1.0],
        "expected_cf_force_n": [0.0, 0.0, 100.0],
        "expected_cfn_force_n": [0.0, 0.0, 100.0],
        "expected_cfs_force_n": [0.0, 0.0, 0.0],
        "expected_cfn_compression_magnitude_n": 100.0,
        "expected_contact_normal_force_signed_n": -100.0,
        "expected_cfs_shear_magnitude_n": 0.0,
        "expected_cf_moment_global_origin_nmm": [1000.0, -1000.0, 0.0],
        "expected_cfn_moment_global_origin_nmm": [1000.0, -1000.0, 0.0],
        "expected_cfs_moment_global_origin_nmm": [0.0, 0.0, 0.0],
        "expected_contact_centroid_xyz_mm": list(CONTACT_CENTROID_MM),
        "expected_cf_moment_at_contact_centroid_nmm": [0.0, 0.0, 0.0],
        "expected_master_action_force_n": [0.0, 0.0, -100.0],
        "expected_master_action_moment_global_origin_nmm": [-1000.0, 1000.0, 0.0],
    },
    "lower_slave": {
        "slave_surface": "LOWER_INTERFACE",
        "master_surface": "UPPER_INTERFACE",
        "cf_owner_body": "LOWER",
        "expected_slave_mean_normal": [0.0, 0.0, 1.0],
        "expected_cf_force_n": [0.0, 0.0, -100.0],
        "expected_cfn_force_n": [0.0, 0.0, -100.0],
        "expected_cfs_force_n": [0.0, 0.0, 0.0],
        "expected_cfn_compression_magnitude_n": 100.0,
        "expected_contact_normal_force_signed_n": -100.0,
        "expected_cfs_shear_magnitude_n": 0.0,
        "expected_cf_moment_global_origin_nmm": [-1000.0, 1000.0, 0.0],
        "expected_cfn_moment_global_origin_nmm": [-1000.0, 1000.0, 0.0],
        "expected_cfs_moment_global_origin_nmm": [0.0, 0.0, 0.0],
        "expected_contact_centroid_xyz_mm": list(CONTACT_CENTROID_MM),
        "expected_cf_moment_at_contact_centroid_nmm": [0.0, 0.0, 0.0],
        "expected_master_action_force_n": [0.0, 0.0, 100.0],
        "expected_master_action_moment_global_origin_nmm": [1000.0, -1000.0, 0.0],
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dot_deck(scenario: str) -> str:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unsupported scenario: {scenario}")
    pair = _SCENARIO_ROWS[scenario]
    contact_pair = f"{pair['slave_surface']},{pair['master_surface']}"
    return f"""** CCX 2.21 contact force/wrench output benchmark; not a joint model.
** One 20 x 20 x 10 mm linear-elastic block per side; interface at z=0.
** The 100 N total compressive top load acts at (10,10,10) mm.
** Fixture elastic constants and contact penalty are numerical inputs only.
*NODE
1,0,0,-10
2,20,0,-10
3,20,20,-10
4,0,20,-10
5,0,0,0
6,20,0,0
7,20,20,0
8,0,20,0
11,0,0,0
12,20,0,0
13,20,20,0
14,0,20,0
15,0,0,10
16,20,0,10
17,20,20,10
18,0,20,10
*ELEMENT,TYPE=C3D8,ELSET=LOWER
1,1,2,3,4,5,6,7,8
*ELEMENT,TYPE=C3D8,ELSET=UPPER
2,11,12,13,14,15,16,17,18
*NSET,NSET=BOTTOM
1,2,3,4
*NSET,NSET=UPPER
11,12,13,14,15,16,17,18
*NSET,NSET=TOP
15,16,17,18
*MATERIAL,NAME=FIXTURE_ONLY
*ELASTIC
1000,0
*SOLID SECTION,ELSET=LOWER,MATERIAL=FIXTURE_ONLY
,
*SOLID SECTION,ELSET=UPPER,MATERIAL=FIXTURE_ONLY
,
*SURFACE,NAME=LOWER_INTERFACE,TYPE=ELEMENT
1,S2
*SURFACE,NAME=UPPER_INTERFACE,TYPE=ELEMENT
2,S1
*SURFACE INTERACTION,NAME=FRICTIONLESS
*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR
{NORMAL_PENALTY_N_PER_MM3:g}
*CONTACT PAIR,INTERACTION=FRICTIONLESS,TYPE=SURFACE TO SURFACE
{contact_pair}
*BOUNDARY
BOTTOM,1,3,0
UPPER,1,2,0
*STEP,NLGEOM,INC=100
*STATIC
1,1,1e-6,1
*CLOAD
15,3,-25
16,3,-25
17,3,-25
18,3,-25
*NODE PRINT,NSET=TOP
U,RF
*NODE PRINT,NSET=BOTTOM
RF
*CONTACT PRINT,FREQUENCY=1
CDIS,CSTR
*CONTACT PRINT,SLAVE={pair['slave_surface']},MASTER={pair['master_surface']},FREQUENCY=1
CF,CFN,CFS
*END STEP
"""


def _manifest_data() -> dict[str, Any]:
    return {
        "schema": "ccx-contact-wrench-benchmark/v1",
        "solver": {"product": "CalculiX CrunchiX", "version": "2.21"},
        "scenario_order": list(SCENARIOS),
        "manual": MANUAL,
        "units": {"length": "mm", "force": "N", "moment": "N mm", "stress": "N/mm^2"},
        "fixture": {
            "body_dimensions_mm": [20.0, 20.0, 10.0],
            "interface_plane_z_mm": 0.0,
            "element_type": "C3D8",
            "elements_per_body": 1,
            "elastic_modulus_n_per_mm2": 1000.0,
            "poisson_ratio": 0.0,
            "fixture_material_notice": "Arbitrary linear-elastic fixture values used only to regularize the output probe; no wood property or capacity is represented.",
            "normal_penalty_n_per_mm3": NORMAL_PENALTY_N_PER_MM3,
            "contact_penalty_notice": "Numerical enforcement parameter for this output probe; not joint stiffness or resistance.",
        },
        "load": {
            "body": "UPPER",
            "top_nodes": [15, 16, 17, 18],
            "force_per_node_n": [0.0, 0.0, -25.0],
            "resultant_force_n": list(LOAD_FORCE_N),
            "resultant_moment_global_origin_nmm": list(LOAD_MOMENT_NMM),
            "resultant_application_point_mm": [10.0, 10.0, 10.0],
            "support_nodes": [1, 2, 3, 4],
        },
        "contact_patch": {
            "area_mm2": CONTACT_AREA_MM2,
            "nominal_centroid_xyz_mm": list(CONTACT_CENTROID_MM),
            "reported_centroid_xy_mm": list(CONTACT_CENTROID_MM[:2]),
            "reported_centroid_z_bounds_mm": [-0.003, 0.0001],
            "reported_centroid_z_interpretation": (
                "The 2.21 manual calls this the contact-area center of gravity without specifying reference/deformed coordinates. "
                "Accept the nominal z=0 plane or the predicted compressed interface: the lower block shortens 0.0025 mm "
                "at 100 N and the 10000 N/mm^3 penalty adds about 0.000025 mm closure."
            ),
            "expected_normal_force_magnitude_n": 100.0,
        },
        "result_tolerances": {
            "force_component_abs_n": 0.01,
            "force_component_relative": 1e-4,
            "moment_component_abs_nmm": 0.1,
            "moment_component_relative": 1e-4,
            "normal_force_abs_n": 0.01,
            "shear_force_abs_n": 0.01,
            "centroid_xy_abs_mm": 1e-4,
            "area_abs_mm2": 0.01,
            "mean_normal_component_abs": 1e-8,
            "guide_displacement_abs_mm": 1e-9,
            "step_end_time_abs": 1e-9,
        },
        "solver_completion_contract": {
            "maximum_increments": 100,
            "step_end_time": 1.0,
            "step_kind": "one quasi-static nonlinear contact step",
            "required_dat_output": "one ordered CF, CFN, CFS report group at every accepted increment for the named pair",
            "contact_report_quantity_order": ["CF", "CFN", "CFS"],
            "required_status": "one converged step 1 endpoint at time 1.0 with no trailing unconverged attempt",
            "required_log_marker": "Job finished",
            "audit_scope": "contact resultant, reported force location, and equilibrium with the known top load only",
        },
        "scenarios": _SCENARIO_ROWS,
        "source_files_sha256": {
            relative: _sha256(ROOT / relative)
            for relative in sorted(SOURCE_NAMES)
            if (ROOT / relative).is_file()
        },
    }


def prepare_artifacts() -> dict[str, Any]:
    """Write deterministic input decks and their source-pinned manifest."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for scenario, name in DECK_NAMES.items():
        (ARTIFACT_DIR / name).write_text(_dot_deck(scenario), encoding="utf-8")
    manifest = _manifest_data()
    if set(manifest["source_files_sha256"]) != SOURCE_NAMES:
        raise ValueError("Could not hash the complete contact-wrench source inventory")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def load_manifest(*, verify_hashes: bool = True) -> dict[str, Any]:
    """Load the fixed contract and reject a changed deck or producer source."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema") != "ccx-contact-wrench-benchmark/v1":
        raise ValueError("Unsupported contact-wrench benchmark manifest schema")
    if manifest.get("solver") != {"product": "CalculiX CrunchiX", "version": "2.21"}:
        raise ValueError("Contact-wrench benchmark solver pin changed")
    if tuple(manifest.get("scenario_order", ())) != SCENARIOS:
        raise ValueError("Contact-wrench benchmark scenarios are incomplete or reordered")
    files = manifest.get("source_files_sha256")
    if not isinstance(files, dict) or set(files) != SOURCE_NAMES:
        raise ValueError("Contact-wrench benchmark source file inventory changed")
    if verify_hashes:
        for relative, expected in files.items():
            path = ROOT / relative
            if not path.is_file() or _sha256(path) != expected:
                raise ValueError(f"Contact-wrench benchmark source hash mismatch: {relative}")
    if set(manifest.get("scenarios", {})) != set(SCENARIOS):
        raise ValueError("Contact-wrench benchmark scenarios are incomplete")
    if manifest.get("scenarios") != _SCENARIO_ROWS:
        raise ValueError("Contact-wrench benchmark analytical contract changed")
    reference = _manifest_data()
    for key in (
        "manual", "solver", "units", "fixture", "load", "contact_patch",
        "result_tolerances", "solver_completion_contract",
    ):
        if manifest.get(key) != reference[key]:
            raise ValueError(f"Contact-wrench benchmark contract changed: {key}")
    if manifest["source_files_sha256"] != reference["source_files_sha256"]:
        raise ValueError("Contact-wrench benchmark source hashes differ from the prepared files")
    for scenario, deck_name in DECK_NAMES.items():
        if (ARTIFACT_DIR / deck_name).read_text(encoding="utf-8") != _dot_deck(scenario):
            raise ValueError(f"Contact-wrench benchmark deck no longer matches its generator: {deck_name}")
    return manifest


def expected_wrench(scenario: str) -> dict[str, Any]:
    """Return the analytical contact-side wrench and its named owner."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unsupported scenario: {scenario}")
    manifest = load_manifest()
    row = manifest["scenarios"][scenario]
    return {
        "scenario": scenario,
        "slave_surface": row["slave_surface"],
        "master_surface": row["master_surface"],
        "cf_owner_body": row["cf_owner_body"],
        "units": manifest["units"],
        "expected_cf_force_n": row["expected_cf_force_n"],
        "expected_cfn_force_n": row["expected_cfn_force_n"],
        "expected_cfs_force_n": row["expected_cfs_force_n"],
        "expected_cfn_compression_magnitude_n": row["expected_cfn_compression_magnitude_n"],
        "expected_contact_normal_force_signed_n": row["expected_contact_normal_force_signed_n"],
        "expected_cfs_shear_magnitude_n": row["expected_cfs_shear_magnitude_n"],
        "expected_cf_moment_global_origin_nmm": row["expected_cf_moment_global_origin_nmm"],
        "expected_cfn_moment_global_origin_nmm": row["expected_cfn_moment_global_origin_nmm"],
        "expected_cfs_moment_global_origin_nmm": row["expected_cfs_moment_global_origin_nmm"],
        "expected_contact_centroid_xyz_mm": row["expected_contact_centroid_xyz_mm"],
        "expected_cf_moment_at_contact_centroid_nmm": row["expected_cf_moment_at_contact_centroid_nmm"],
        "expected_contact_area_mm2": manifest["contact_patch"]["area_mm2"],
        "expected_master_action_force_n": row["expected_master_action_force_n"],
        "expected_master_action_moment_global_origin_nmm": row["expected_master_action_moment_global_origin_nmm"],
    }


def prepared_record() -> dict[str, Any]:
    """Return pinned inputs and comparison contract without running a solver."""
    manifest = load_manifest()
    return {
        "schema": "ccx-contact-wrench-prepared-run/v1",
        "status": "PREPARED_NOT_SOLVED",
        "native_run_performed": False,
        "benchmark_scope": "standalone frictionless contact output, force-location, and wrench accounting probe",
        "not_a_joint_acceptance": True,
        "manifest_sha256": _sha256(MANIFEST_PATH),
        "source_files_sha256": manifest["source_files_sha256"],
        "manual": manifest["manual"],
        "units": manifest["units"],
        "fixture": manifest["fixture"],
        "load": manifest["load"],
        "contact_patch": manifest["contact_patch"],
        "result_tolerances": manifest["result_tolerances"],
        "solver_completion_contract": manifest["solver_completion_contract"],
        "scenarios": {name: expected_wrench(name) for name in SCENARIOS},
    }


_REPORT_START = re.compile(
    r"^\s*statistics for slave set\s+(\S+),\s*master set\s+(\S+)\s+and time\s+([0-9.Ee+\-]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _numeric_row_after(lines: list[str], label_index: int, count: int, label: str) -> tuple[float, ...]:
    for line in lines[label_index + 1 :]:
        fields = line.split()
        if not fields:
            continue
        try:
            values = tuple(float(value) for value in fields)
        except ValueError as error:
            raise ValueError(f"Malformed numeric row after {label}") from error
        if len(values) != count or not all(math.isfinite(value) for value in values):
            raise ValueError(f"Invalid numeric row after {label}")
        return values
    raise ValueError(f"Missing numeric row after {label}")


def parse_contact_reports(data_text: str) -> list[dict[str, Any]]:
    """Parse all requested CF, CFN, and CFS blocks from a CalculiX .dat file.

    CalculiX 2.21 writes one identically labeled statistics block per requested
    key.  The quantity is therefore bound strictly by the deck's declared
    request order; same-time blocks are neither deduplicated nor inferred from
    their labels.
    """
    starts = list(_REPORT_START.finditer(data_text))
    if not starts:
        raise ValueError("No CalculiX contact resultant report found")
    reports = []
    for index, match in enumerate(starts):
        stop = starts[index + 1].start() if index + 1 < len(starts) else len(data_text)
        block = data_text[match.end() : stop]
        lines = block.splitlines()
        labels = (
            "total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)",
            "center of gravity and mean normal",
            "moment about the center of gravity(mx,my,mz)",
            "area,  normal force (+ = tension) and shear force (size)",
        )
        positions = []
        for label in labels:
            matches = [i for i, line in enumerate(lines) if label in line.lower()]
            if len(matches) != 1:
                raise ValueError(f"Expected one {label!r} line in each contact report")
            positions.append(matches[0])
        if positions != sorted(positions):
            raise ValueError("Contact report fields are out of order")
        values = (
            _numeric_row_after(lines, positions[0], 6, labels[0]),
            _numeric_row_after(lines, positions[1], 6, labels[1]),
            _numeric_row_after(lines, positions[2], 3, labels[2]),
            _numeric_row_after(lines, positions[3], 3, labels[3]),
        )
        try:
            time = float(match.group(3))
        except ValueError as error:
            raise ValueError("Invalid contact report step time") from error
        if not math.isfinite(time):
            raise ValueError("Nonfinite contact report step time")
        reports.append(
            {
                "slave_surface": match.group(1),
                "master_surface": match.group(2),
                "time": time,
                "force_n": values[0][:3],
                "moment_global_origin_nmm": values[0][3:],
                "centroid_xyz_mm": values[1][:3],
                "mean_normal": values[1][3:],
                "moment_at_centroid_nmm": values[2],
                "area_mm2": values[3][0],
                "normal_force_signed_n": values[3][1],
                "shear_force_magnitude_n": values[3][2],
            }
        )
    request_order = ("CF", "CFN", "CFS")
    if len(reports) % len(request_order):
        raise ValueError("Contact report count does not form complete CF/CFN/CFS groups")
    grouped_times = []
    for start in range(0, len(reports), len(request_order)):
        group = reports[start : start + len(request_order)]
        group_time = group[0]["time"]
        if any(abs(report["time"] - group_time) > 1e-12 for report in group[1:]):
            raise ValueError("CF, CFN, and CFS reports do not share a step time")
        for report, quantity in zip(group, request_order, strict=True):
            report["quantity"] = quantity
        grouped_times.append(group_time)
    if any(right <= left for left, right in zip(grouped_times, grouped_times[1:])):
        raise ValueError("Contact report groups are duplicate or out of order")
    return reports


def _assert_vector_close(actual: tuple[float, ...], expected: tuple[float, ...], absolute: float, relative: float, label: str) -> None:
    if len(actual) != len(expected):
        raise ValueError(f"{label} component count differs")
    for index, (value, target) in enumerate(zip(actual, expected, strict=True)):
        limit = max(absolute, relative * abs(target))
        if abs(value - target) > limit:
            raise ValueError(f"{label} component {index} differs: {value} vs {target} (tol {limit})")


def _cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _point_wrench(positions: dict[int, tuple[float, float, float]], forces: dict[int, tuple[float, float, float]]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    force = tuple(math.fsum(values[i] for values in forces.values()) for i in range(3))
    moments = [_cross(positions[node], value) for node, value in forces.items()]
    moment = tuple(math.fsum(value[i] for value in moments) for i in range(3))
    return force, moment


def _parse_node_table(data_text: str, quantity: str, set_name: str) -> tuple[float, dict[int, tuple[float, float, float]]]:
    number = r"[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+\-]?\d+)?"
    header = re.compile(
        rf"^\s*{re.escape(quantity)}\s+\([^)]+\)\s+for set\s+{re.escape(set_name)}\s+and time\s+({number})\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(header.finditer(data_text))
    if not matches:
        raise ValueError(f"Missing {quantity} table for node set {set_name}")
    tables = []
    for match in matches:
        table: dict[int, tuple[float, float, float]] = {}
        started = False
        for line in data_text[match.end() :].splitlines():
            fields = line.split()
            if not fields:
                if started:
                    break
                continue
            if not fields[0].isdigit():
                if started:
                    break
                continue
            started = True
            if len(fields) != 4:
                raise ValueError(f"Malformed {quantity} row for node set {set_name}")
            node = int(fields[0])
            try:
                vector = tuple(float(value) for value in fields[1:])
            except ValueError as error:
                raise ValueError(f"Malformed {quantity} row for node set {set_name}") from error
            if node in table or not all(math.isfinite(value) for value in vector):
                raise ValueError(f"Duplicate or nonfinite {quantity} row for node set {set_name}")
            table[node] = vector  # type: ignore[assignment]
        if not table:
            raise ValueError(f"Empty {quantity} table for node set {set_name}")
        tables.append((float(match.group(1)), table))
    return tables[-1]


def _audit_fixture_balance(data_text: str, step_time: float, tolerance: dict[str, float]) -> dict[str, Any]:
    top_u_time, top_u = _parse_node_table(data_text, "displacements", "TOP")
    top_f_time, top_f = _parse_node_table(data_text, "forces", "TOP")
    bottom_f_time, bottom_f = _parse_node_table(data_text, "forces", "BOTTOM")
    endpoint_tolerance = tolerance["step_end_time_abs"]
    if any(abs(value - step_time) > endpoint_tolerance for value in (top_u_time, top_f_time, bottom_f_time)):
        raise ValueError("Nodal output endpoint differs from the contact report")
    if top_u.keys() != TOP_NODE_COORDS_MM.keys() or top_f.keys() != TOP_NODE_COORDS_MM.keys():
        raise ValueError("Top nodal output does not cover the four prepared load nodes")
    if bottom_f.keys() != BOTTOM_NODE_COORDS_MM.keys():
        raise ValueError("Support output does not cover the four prepared bottom nodes")

    load_per_node = (0.0, 0.0, -25.0)
    for node, force in top_f.items():
        _assert_vector_close(
            force, load_per_node, tolerance["force_component_abs_n"], 0.0,
            f"reported top load at node {node}",
        )
    top_positions = {
        node: tuple(TOP_NODE_COORDS_MM[node][axis] + top_u[node][axis] for axis in range(3))
        for node in TOP_NODE_COORDS_MM
    }
    for node, position in top_positions.items():
        _assert_vector_close(
            position[:2], TOP_NODE_COORDS_MM[node][:2], tolerance["guide_displacement_abs_mm"], 0.0,
            f"top guide position at node {node}",
        )
    top_wrench = _point_wrench(top_positions, top_f)
    support_wrench = _point_wrench(BOTTOM_NODE_COORDS_MM, bottom_f)
    residual_force = tuple(a + b for a, b in zip(top_wrench[0], support_wrench[0], strict=True))
    residual_moment = tuple(a + b for a, b in zip(top_wrench[1], support_wrench[1], strict=True))
    _assert_vector_close(
        residual_force, (0.0, 0.0, 0.0), tolerance["force_component_abs_n"], 0.0,
        "top-load plus support force equilibrium",
    )
    _assert_vector_close(
        residual_moment, (0.0, 0.0, 0.0), tolerance["moment_component_abs_nmm"], 0.0,
        "top-load plus support moment equilibrium",
    )
    return {
        "top_force_wrench_n_nmm": list(top_wrench[0] + top_wrench[1]),
        "support_reaction_wrench_n_nmm": list(support_wrench[0] + support_wrench[1]),
        "global_force_residual_n": list(residual_force),
        "global_moment_residual_nmm": list(residual_moment),
    }


def audit_data(data_text: str, scenario: str) -> dict[str, Any]:
    """Audit ordered contact reports, force locations, and fixture equilibrium."""
    contract = expected_wrench(scenario)
    manifest = load_manifest()
    tolerance = manifest["result_tolerances"]
    reports = parse_contact_reports(data_text)
    request_order = manifest["solver_completion_contract"]["contact_report_quantity_order"]
    expected_pair = (contract["slave_surface"], contract["master_surface"])
    if any((report["slave_surface"], report["master_surface"]) != expected_pair for report in reports):
        raise ValueError("Contact report surfaces differ from the prepared pair")
    if len(reports) > manifest["solver_completion_contract"]["maximum_increments"] * len(request_order):
        raise ValueError("Contact report count exceeds the prepared increment limit")
    step_end = manifest["solver_completion_contract"]["step_end_time"]
    times = [reports[i]["time"] for i in range(0, len(reports), len(request_order))]
    if any(time <= 0.0 or time > step_end + tolerance["step_end_time_abs"] for time in times):
        raise ValueError("Contact report time lies outside the prepared step")
    if abs(times[-1] - step_end) > tolerance["step_end_time_abs"]:
        raise ValueError("Contact report does not reach the end of the prepared step")
    final_group = reports[-len(request_order) :]
    if [report["quantity"] for report in final_group] != request_order:
        raise ValueError("Final contact report quantity order differs from the deck")

    expected_centroid_xy = tuple(contract["expected_contact_centroid_xyz_mm"][:2])
    z_min, z_max = manifest["contact_patch"]["reported_centroid_z_bounds_mm"]
    expected_normal = tuple(_SCENARIO_ROWS[scenario]["expected_slave_mean_normal"])
    expected_components = {
        "CF": (
            tuple(contract["expected_cf_force_n"]),
            tuple(contract["expected_cf_moment_global_origin_nmm"]),
            contract["expected_contact_normal_force_signed_n"],
            contract["expected_cfs_shear_magnitude_n"],
            tuple(contract["expected_cf_moment_at_contact_centroid_nmm"]),
        ),
        "CFN": (
            tuple(contract["expected_cfn_force_n"]),
            tuple(contract["expected_cfn_moment_global_origin_nmm"]),
            contract["expected_contact_normal_force_signed_n"],
            0.0,
            tuple(contract["expected_cf_moment_at_contact_centroid_nmm"]),
        ),
        "CFS": (
            tuple(contract["expected_cfs_force_n"]),
            tuple(contract["expected_cfs_moment_global_origin_nmm"]),
            0.0,
            0.0,
            (0.0, 0.0, 0.0),
        ),
    }
    final_by_quantity = {}
    for report in final_group:
        quantity = report["quantity"]
        expected_force, expected_moment, expected_normal_force, expected_shear, expected_centroid_moment = expected_components[quantity]
        _assert_vector_close(
            report["force_n"], expected_force, tolerance["force_component_abs_n"],
            tolerance["force_component_relative"], f"{quantity} force",
        )
        _assert_vector_close(
            report["moment_global_origin_nmm"], expected_moment,
            tolerance["moment_component_abs_nmm"], tolerance["moment_component_relative"],
            f"{quantity} origin moment",
        )
        _assert_vector_close(
            report["centroid_xyz_mm"][:2], expected_centroid_xy,
            tolerance["centroid_xy_abs_mm"], 0.0, f"{quantity} contact centroid x/y",
        )
        if not z_min <= report["centroid_xyz_mm"][2] <= z_max:
            raise ValueError(
                f"{quantity} contact centroid z lies outside predeclared bounds [{z_min}, {z_max}] mm"
            )
        _assert_vector_close(
            report["mean_normal"], expected_normal,
            tolerance["mean_normal_component_abs"], 0.0, f"{quantity} slave mean normal",
        )
        _assert_vector_close(
            report["moment_at_centroid_nmm"], expected_centroid_moment,
            tolerance["moment_component_abs_nmm"], tolerance["moment_component_relative"],
            f"{quantity} moment at contact centroid",
        )
        if abs(report["area_mm2"] - contract["expected_contact_area_mm2"]) > tolerance["area_abs_mm2"]:
            raise ValueError(f"{quantity} contact area differs: {report['area_mm2']}")
        if abs(report["normal_force_signed_n"] - expected_normal_force) > tolerance["normal_force_abs_n"]:
            raise ValueError(f"{quantity} signed normal force differs")
        if abs(report["shear_force_magnitude_n"] - expected_shear) > tolerance["shear_force_abs_n"]:
            raise ValueError(f"{quantity} shear force differs")
        delta = tuple(-component for component in report["centroid_xyz_mm"])
        shift = _cross(delta, tuple(report["force_n"]))
        shifted = tuple(a + b for a, b in zip(report["moment_global_origin_nmm"], shift, strict=True))
        _assert_vector_close(
            shifted, tuple(report["moment_at_centroid_nmm"]),
            tolerance["moment_component_abs_nmm"], tolerance["moment_component_relative"],
            f"{quantity} origin-to-centroid wrench shift",
        )
        final_by_quantity[quantity] = report

    cf = final_by_quantity["CF"]
    side_sign = 1.0 if contract["cf_owner_body"] == "UPPER" else -1.0
    contact_on_upper_force = tuple(side_sign * component for component in cf["force_n"])
    contact_on_upper_moment = tuple(side_sign * component for component in cf["moment_global_origin_nmm"])
    loaded_force_residual = tuple(a + b for a, b in zip(LOAD_FORCE_N, contact_on_upper_force, strict=True))
    loaded_moment_residual = tuple(a + b for a, b in zip(LOAD_MOMENT_NMM, contact_on_upper_moment, strict=True))
    _assert_vector_close(
        loaded_force_residual, (0.0, 0.0, 0.0), tolerance["force_component_abs_n"], 0.0,
        "loaded-upper-body force equilibrium from CF",
    )
    _assert_vector_close(
        loaded_moment_residual, (0.0, 0.0, 0.0), tolerance["moment_component_abs_nmm"], 0.0,
        "loaded-upper-body moment equilibrium from CF",
    )
    fixture = _audit_fixture_balance(data_text, step_end, tolerance)
    return {
        "schema": "ccx-contact-wrench-benchmark-audit/v1",
        "status": "DAT_CONTACT_AND_FIXTURE_BALANCE_PASS_ONLY_NOT_JOINT_CAPACITY",
        "dat_output_audited": True,
        "scenario": scenario,
        "units": manifest["units"],
        "solver": manifest["solver"],
        "scope": "ordered CF/CFN/CFS output, contact resultant location, loaded-body wrench, and fixture global balance only",
        "contact_report_count": len(reports),
        "contact_report_quantity_order": request_order,
        "final_time": cf["time"],
        "contact_owner_body": contract["cf_owner_body"],
        "contact_components": {
            quantity: {
                "force_n": list(final_by_quantity[quantity]["force_n"]),
                "moment_global_origin_nmm": list(final_by_quantity[quantity]["moment_global_origin_nmm"]),
                "normal_force_signed_n": final_by_quantity[quantity]["normal_force_signed_n"],
                "shear_force_magnitude_n": final_by_quantity[quantity]["shear_force_magnitude_n"],
            }
            for quantity in request_order
        },
        "contact_action_on_loaded_upper_wrench_n_nmm": list(contact_on_upper_force + contact_on_upper_moment),
        "contact_centroid_xyz_mm": list(cf["centroid_xyz_mm"]),
        "reported_centroid_z_bounds_mm": manifest["contact_patch"]["reported_centroid_z_bounds_mm"],
        "contact_area_mm2": cf["area_mm2"],
        "loaded_upper_equilibrium_residual_force_n": list(loaded_force_residual),
        "loaded_upper_equilibrium_residual_moment_nmm": list(loaded_moment_residual),
        "fixture_global_balance": fixture,
        "tolerances": tolerance,
    }


def audit_solver_status(status_text: str, log_text: str, exit_code: int) -> dict[str, Any]:
    """Require a clean exit, one completed step, and a completed CCX log."""
    if exit_code != 0:
        raise ValueError(f"CalculiX process exit code is {exit_code}")
    if re.search(r"\*\*\*\s*(?:ERROR|FATAL)", log_text, re.IGNORECASE):
        raise ValueError("CalculiX log contains an error or fatal error")
    if len(re.findall(r"^\s*Job finished\s*$", log_text, re.IGNORECASE | re.MULTILINE)) != 1:
        raise ValueError("CalculiX log lacks one Job finished marker")
    if "SUMMARY OF JOB INFORMATION" not in status_text.upper():
        raise ValueError("CalculiX status file lacks its job summary")
    rows = []
    for line in status_text.splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        if len(fields) != 7:
            raise ValueError("Malformed CalculiX status row")
        step, increment = int(fields[0]), int(fields[1])
        attempt = fields[2]
        if not re.fullmatch(r"\d+U?", attempt, re.IGNORECASE):
            raise ValueError("Malformed CalculiX attempt field")
        try:
            iterations = int(fields[3])
            total_time, step_time, increment_time = (float(value) for value in fields[4:])
        except ValueError as error:
            raise ValueError("Malformed CalculiX status values") from error
        if not all(math.isfinite(value) for value in (total_time, step_time, increment_time)):
            raise ValueError("Nonfinite CalculiX status values")
        rows.append({
            "step": step, "increment": increment, "attempt": attempt,
            "iterations": iterations, "total_time": total_time,
            "step_time": step_time, "increment_time": increment_time,
            "unconverged": attempt.upper().endswith("U"),
        })
    if not rows or any(row["step"] != 1 for row in rows):
        raise ValueError("CalculiX status does not contain the single prepared step")
    if rows[-1]["unconverged"]:
        raise ValueError("CalculiX status ends with an unconverged attempt")
    accepted = [row for row in rows if not row["unconverged"]]
    maximum = load_manifest()["solver_completion_contract"]["maximum_increments"]
    if len(accepted) > maximum or [row["increment"] for row in accepted] != list(range(1, len(accepted) + 1)):
        raise ValueError("CalculiX accepted increment count or sequence differs")
    previous = 0.0
    for row in accepted:
        if (
            row["iterations"] < 1
            or row["increment_time"] <= 0.0
            or row["increment_time"] > 1.0 + 1e-9
            or abs(row["step_time"] - row["total_time"]) > 1e-6
            or abs(row["step_time"] - previous - row["increment_time"]) > 1e-6
        ):
            raise ValueError("CalculiX accepted status history is inconsistent")
        previous = row["step_time"]
    final_time = load_manifest()["solver_completion_contract"]["step_end_time"]
    if abs(previous - final_time) > 1e-9:
        raise ValueError("CalculiX status does not complete the prepared step")
    return {
        "exit_code": exit_code,
        "job_finished_marker_count": 1,
        "accepted_increment_count": len(accepted),
        "final_step_time": previous,
        "final_iterations": accepted[-1]["iterations"],
        "unconverged_attempts": sum(row["unconverged"] for row in rows),
    }


def audit_run(
    data_text: str,
    status_text: str,
    log_text: str,
    scenario: str,
    exit_code: int,
    input_deck_text: str,
) -> dict[str, Any]:
    deck_name = DECK_NAMES[scenario]
    expected_deck_hash = load_manifest()["source_files_sha256"][
        f"fea/results/ccx_contact_wrench_benchmark/{deck_name}"
    ]
    actual_deck_hash = hashlib.sha256(input_deck_text.encode("utf-8")).hexdigest()
    if actual_deck_hash != expected_deck_hash:
        raise ValueError("Run input deck does not match the prepared source-pinned deck")
    result = audit_data(data_text, scenario)
    completion = audit_solver_status(status_text, log_text, exit_code)
    expected_reports = completion["accepted_increment_count"] * len(
        load_manifest()["solver_completion_contract"]["contact_report_quantity_order"]
    )
    if result["contact_report_count"] != expected_reports:
        raise ValueError("DAT CF/CFN/CFS report groups do not match the accepted status increments")
    result["solver_completion"] = completion
    result["run_input_deck_sha256"] = actual_deck_hash
    result["status"] = "SOLVER_AND_DAT_ACCOUNTING_PASS_ONLY_NOT_JOINT_CAPACITY"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true", help="Write the two input decks and source-pinned manifest")
    modes.add_argument("--verify", action="store_true", help="Verify source pins and print the prepared run contract")
    modes.add_argument("--audit", nargs=2, metavar=("SCENARIO", "DAT"), help="Audit one native run; never starts a solver")
    parser.add_argument("--sta", help="CalculiX .sta file required with --audit")
    parser.add_argument("--log", help="CalculiX stdout/stderr log required with --audit")
    parser.add_argument("--inp", help="The exact solver input deck required with --audit")
    parser.add_argument("--exit-code", type=int, help="Native process exit code required with --audit")
    args = parser.parse_args()
    if args.prepare:
        prepare_artifacts()
        print(json.dumps(prepared_record(), indent=2, allow_nan=False))
        return 0
    if args.verify:
        print(json.dumps(prepared_record(), indent=2, allow_nan=False))
        return 0
    if args.sta is None or args.log is None or args.inp is None or args.exit_code is None:
        parser.error("--audit requires --sta, --log, --inp, and --exit-code")
    scenario, data_path = args.audit
    result = audit_run(
        Path(data_path).read_text(encoding="utf-8", errors="replace"),
        Path(args.sta).read_text(encoding="utf-8", errors="replace"),
        Path(args.log).read_text(encoding="utf-8", errors="replace"),
        scenario,
        args.exit_code,
        Path(args.inp).read_text(encoding="utf-8"),
    )
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
