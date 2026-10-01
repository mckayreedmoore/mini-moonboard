#!/usr/bin/env python3
"""Prepare the CalculiX 2.23 explicit C3D10 MPC mass-coordinate fixture.

This generator writes inputs and immutable preparation records only. It never
launches CalculiX and never creates a freeze or execution record.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tarfile


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents
            if (parent / "current-candidate.json").is_file())
EVAL = HERE.parent
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02" / "source.tar.bz2"
)
SOLVER_PROFILE = EVAL / "calculix-2.23-upgrade-attempt01" / "solver-profile.json"
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
PINNED_SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/e_c3d.f": {
        "sha256": "d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc",
        "lines": "1921-1975",
        "purpose": "C3D10 explicit diagonal mass lumping; nope=10 selects alp=0.1203.",
    },
    "CalculiX/ccx_2.23/src/nonlingeo.c": {
        "sha256": "8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f",
        "lines": "899-1052,1260-1444,1607-1615",
        "purpose": "Dynamic initialization, explicit stable-step selection, initial acceleration from external minus internal force over lumped mass, and the implicit-only stdout increment-trace guard.",
    },
    "CalculiX/ccx_2.23/src/tempload.f": {
        "sha256": "8933ca0a5bb9fa3db2b55b4ec9344be9dca1297763f5ea28f6ef7c9074ea84aa",
        "lines": "356-373",
        "purpose": "Unamplified non-static CLOAD remains at its reference value at dynamic-step start.",
    },
}
MANUAL_PDF_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
MANUAL_HTML_PAGES = {
    "node279.html": "822622f69585dcb9dee3eb86ae52b608f6b5d4944dfaf537ef89250dee26f19f",
    "node180.html": "b4766a18f82f1ed1d5aa9846366626476fa81c1d6104869aa415b16d3399140c",
    "node273.html": "c36c738d851edf257e10a428e9fffe8d8a01166536311dadb5fa07ae7d4a73b8",
    "node283.html": "e9d7eacbfd5debae8b32669522f551ad4e7fb9c76a92c5e15c4633652429d913",
}
IMAGE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BINARY_SHA256 = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
SCHEMA = "calculix_explicit_c3d10_mpc_known_answer/v1"
CASE_ORDER = ["direct", "mapped"]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: object) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode("utf-8")


def read_source_member(archive_path: Path, wanted: str) -> bytes:
    with tarfile.open(archive_path, mode="r:bz2") as archive:
        for member in archive.getmembers():
            if member.name.removeprefix("./") == wanted:
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"Missing source bytes for {wanted}")
                return extracted.read()
    raise RuntimeError(f"Pinned source member is absent: {wanted}")


def require_pinned_sources() -> tuple[dict, bytes]:
    archive_bytes = SOURCE_ARCHIVE.read_bytes()
    archive_digest = sha256(archive_bytes)
    if archive_digest != SOURCE_ARCHIVE_SHA256:
        raise RuntimeError("Official 2.23 source archive hash changed")
    profile = json.loads(SOLVER_PROFILE.read_text(encoding="utf-8"))
    if profile.get("version") != "2.23":
        raise RuntimeError("Solver profile is not pinned to CalculiX 2.23")
    if profile.get("image_id") != IMAGE_ID or profile.get("binary_sha256") != BINARY_SHA256:
        raise RuntimeError("Solver image or executable pin differs")
    manual = profile.get("manual", {})
    if manual.get("sha256") != MANUAL_PDF_SHA256:
        raise RuntimeError("Official 2.23 PDF manual hash differs from the solver profile")
    for name, expected in PINNED_SOURCE_MEMBERS.items():
        actual = sha256(read_source_member(SOURCE_ARCHIVE, name))
        if actual != expected["sha256"]:
            raise RuntimeError(f"Pinned source member hash changed: {name}")
    source_snapshot = {
        "schema": "calculix_223_explicit_c3d10_source_snapshot/v1",
        "source_archive": {
            "path_from_repo_root": str(SOURCE_ARCHIVE.relative_to(ROOT)),
            "sha256": archive_digest,
            "upstream": "CalculiX 2.23 official source archive, built without source patches",
        },
        "source_members": PINNED_SOURCE_MEMBERS,
        "manual": {
            "pdf_url": manual["url"],
            "pdf_sha256": manual["sha256"],
            "html_page_sha256": MANUAL_HTML_PAGES,
            "html_page_topics": {
                "node279.html": "*EL FILE output is nodally averaged FRD element data; ENER label is energy density",
                "node180.html": "explicit lumped-mass method and minimum-step scaling behavior",
                "node273.html": "*DYNAMIC EXPLICIT parameter and time-increment fields",
                "node283.html": "homogeneous *EQUATION; first term is eliminated dependent DOF",
            },
            "manual_profile_path_from_repo_root": str(SOLVER_PROFILE.relative_to(ROOT)),
        },
        "solver": {
            "version": "2.23",
            "image_id": IMAGE_ID,
            "binary_sha256": BINARY_SHA256,
        },
    }
    return source_snapshot, archive_bytes


def ftoken(value: float) -> str:
    token = format(value, ".16g")
    if len(token) > 19:
        raise RuntimeError(f"Numeric token exceeds conservative 19-character width: {token}")
    return token


def vector_det3(a: tuple[float, float, float],
                b: tuple[float, float, float],
                c: tuple[float, float, float]) -> float:
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def rank_fraction(matrix: list[list[Fraction]]) -> int:
    work = [row[:] for row in matrix]
    rows = len(work)
    cols = len(work[0]) if rows else 0
    pivot_row = 0
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if work[r][col]), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        divisor = work[pivot_row][col]
        work[pivot_row] = [value / divisor for value in work[pivot_row]]
        for r in range(rows):
            if r == pivot_row or not work[r][col]:
                continue
            factor = work[r][col]
            work[r] = [work[r][c] - factor * work[pivot_row][c]
                       for c in range(cols)]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def solve_fraction(matrix: list[list[Fraction]], rhs: list[Fraction]) -> list[Fraction]:
    size = len(rhs)
    work = [matrix[row][:] + [rhs[row]] for row in range(size)]
    for col in range(size):
        pivot = next((row for row in range(col, size) if work[row][col]), None)
        if pivot is None:
            raise RuntimeError("Analytical reduced mass matrix is singular")
        work[col], work[pivot] = work[pivot], work[col]
        divisor = work[col][col]
        work[col] = [value / divisor for value in work[col]]
        for row in range(size):
            if row == col:
                continue
            factor = work[row][col]
            if factor:
                work[row] = [work[row][k] - factor * work[col][k]
                             for k in range(size + 1)]
    return [work[row][-1] for row in range(size)]


def dot(a: list[Fraction], b: list[Fraction]) -> Fraction:
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def multiply(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [dot(row, vector) for row in matrix]


def mesh_record() -> dict:
    nodes = [
        [1, 0.0, 0.0, 0.0],
        [2, 1.0, 0.0, 0.0],
        [3, 0.0, 1.0, 0.0],
        [4, 0.0, 0.0, 1.0],
        [5, 0.5, 0.0, 0.0],
        [6, 0.5, 0.5, 0.0],
        [7, 0.0, 0.5, 0.0],
        [8, 0.0, 0.0, 0.5],
        [9, 0.5, 0.0, 0.5],
        [10, 0.0, 0.5, 0.5],
    ]
    return {
        "coordinate_unit": "mm",
        "physical_node_ids": list(range(1, 11)),
        "nodes_id_xyz_mm": nodes,
        "elements": [{"id": 1, "type": "C3D10", "connectivity": list(range(1, 11))}],
    }


def create_deck(case: str, mesh: dict, force_tokens: list[str]) -> bytes:
    lines = [
        "** CalculiX 2.23 explicit C3D10 mass-coordinate known-answer method fixture.",
        f"** Variant: {case}; no candidate joint geometry or acceptance.",
        "*NODE",
    ]
    for node_id, x, y, z in mesh["nodes_id_xyz_mm"]:
        lines.append(f"{node_id},{ftoken(x)},{ftoken(y)},{ftoken(z)}")
    if case == "mapped":
        # A free generalized coordinate, with only its unused transverse DOFs fixed.
        lines.append("11,2,0,0")
    lines.extend([
        "*ELEMENT,TYPE=C3D10,ELSET=BODY",
        "1,1,2,3,4,5,6,7,8,9,10",
        "*NSET,NSET=PHYSICAL",
        "1,2,3,4,5,6,7,8,9,10",
    ])
    if case == "mapped":
        lines.append("*NSET,NSET=CONTROLLER")
        lines.append("11")
        lines.extend([
            "*EQUATION",
            "5",
            "1,1,1,2,1,1,3,1,1,4,1,1",
            "11,1,-4",
        ])
    lines.extend([
        "*MATERIAL,NAME=MAT",
        "*ELASTIC",
        "1,0",
        "*DENSITY",
        "6",
        "*SOLID SECTION,ELSET=BODY,MATERIAL=MAT",
        "*STEP,INC=10000",
        "*DYNAMIC,EXPLICIT=2,ALPHA=0",
        "0.001,0.1,,0.001",
        "*BOUNDARY",
        "PHYSICAL,2,3,0",
    ])
    if case == "mapped":
        lines.append("CONTROLLER,2,3,0")
    lines.append("*CLOAD")
    for node_id, force in enumerate(force_tokens, start=1):
        lines.append(f"{node_id},1,{force}")
    lines.extend([
        "*NODE PRINT,NSET=PHYSICAL,FREQUENCY=1",
        "U,RF,V",
        "*NODE FILE,NSET=PHYSICAL,FREQUENCY=1",
        "U,RF,V",
    ])
    if case == "mapped":
        lines.extend([
            "*NODE PRINT,NSET=CONTROLLER,FREQUENCY=1",
            "U",
        ])
    lines.extend([
        "*EL PRINT,ELSET=BODY,TOTALS=ONLY,FREQUENCY=1",
        "ELSE,ELKE,EMAS,EVOL",
        "*EL FILE,FREQUENCY=1",
        "ENER",
        "*END STEP",
    ])
    return ("\n".join(lines) + "\n").encode("ascii")


def analytical_preflight(mesh: dict) -> tuple[dict, dict, list[Fraction], list[str]]:
    coords = {row[0]: tuple(row[1:]) for row in mesh["nodes_id_xyz_mm"]}
    p0, p1, p2, p3 = (coords[i] for i in (1, 2, 3, 4))
    a = tuple(p1[i] - p0[i] for i in range(3))
    b = tuple(p2[i] - p0[i] for i in range(3))
    c = tuple(p3[i] - p0[i] for i in range(3))
    volume = abs(vector_det3(a, b, c)) / 6.0
    density = Fraction(6, 1)
    total_mass = Fraction(1, 6) * density
    alpha = Fraction(1203, 10000)
    corner_mass = alpha / (1 + alpha) / 4
    midside_mass = 1 / (1 + alpha) / 6
    masses = [corner_mass] * 4 + [midside_mass] * 6
    if volume != 1 / 6 or sum(masses, Fraction(0)) != total_mass or total_mass != 1:
        raise RuntimeError("Unit-tetra volume or pinned C3D10 lumped mass check failed")
    load_tokens = [ftoken(float(value)) for value in masses]
    serialized_loads = [Fraction.from_float(float(token)) for token in load_tokens]
    if max(len(token) for token in load_tokens) > 19:
        raise RuntimeError("A force token exceeds the fixed-field safety margin")

    # The 10-by-10 invertible coordinate transformation has independent
    # coordinates [u2,u3,u4,u5,...,u10,q11] and u1=4*q11-u2-u3-u4.
    transform = [[Fraction(0) for _ in range(10)] for _ in range(10)]
    transform[0][0:3] = [Fraction(-1)] * 3
    transform[0][9] = Fraction(4)
    for physical_row in range(1, 10):
        transform[physical_row][physical_row - 1] = Fraction(1)
    if rank_fraction(transform) != 10:
        raise RuntimeError("The homogeneous coordinate mapping is not invertible")

    mass_matrix = [[Fraction(0) for _ in range(10)] for _ in range(10)]
    for i, mass in enumerate(masses):
        mass_matrix[i][i] = mass
    reduced_mass = [[
        sum((transform[k][i] * mass_matrix[k][k] * transform[k][j]
             for k in range(10)), Fraction(0))
        for j in range(10)] for i in range(10)]
    physical_load = serialized_loads
    reduced_load = [
        sum((transform[k][j] * physical_load[k] for k in range(10)), Fraction(0))
        for j in range(10)
    ]
    exact_acceleration = solve_fraction(reduced_mass, reduced_load)
    physical_acceleration = multiply(transform, exact_acceleration)
    diagonal_acceleration = [
        reduced_load[i] / reduced_mass[i][i] for i in range(10)
    ]
    diagonal_physical = multiply(transform, diagonal_acceleration)
    if max(abs(float(value) - 1.0) for value in physical_acceleration) > 1e-12:
        raise RuntimeError("Exact transformed mass oracle does not yield uniform acceleration")

    preflight = {
        "schema": "calculix_explicit_c3d10_mpc_preflight/v1",
        "status": "PASS_PREPARATION_ONLY",
        "geometry": {"straight_tetra_volume_mm3": volume, "physical_nodes": 10,
                     "elements": 1, "element_type": "C3D10"},
        "material_and_mass": {
            "E_N_per_mm2": 1.0,
            "nu": 0.0,
            "density_tonne_per_mm3": 6.0,
            "total_mass_tonne": float(total_mass),
            "source_lumped_mass_parameter_alp": 0.1203,
            "corner_mass_fraction_exact": str(corner_mass),
            "midside_mass_fraction_exact": str(midside_mass),
            "mass_fraction_sum_exact": str(sum(masses, Fraction(0))),
        },
        "force_and_motion": {
            "constant_acceleration_mm_per_s2": 1.0,
            "total_CLOAD_N_from_serialized_fields": float(sum(serialized_loads, Fraction(0))),
            "force_by_physical_node_N": [float(value) for value in serialized_loads],
            "expected_u1_mm": "0.5*t_s^2",
            "expected_v1_mm_per_s": "t_s",
            "expected_total_ELKE_Nmm": "0.5*t_s^2",
            "expected_total_ELSE_Nmm": 0.0,
            "expected_total_EMAS_tonne": 1.0,
        },
        "mapped_coordinate_oracle": {
            "independent_coordinates": ["u2", "u3", "u4", "u5", "u6", "u7", "u8", "u9", "u10", "q11"],
            "dependent_coordinate": "u1=4*q11-u2-u3-u4",
            "transformation_rank": 10,
            "full_transformed_mass_physical_acceleration_mm_per_s2": [float(v) for v in physical_acceleration],
            "full_transformed_mass_q11_acceleration_mm_per_s2": float(exact_acceleration[9]),
            "diagonal_only_initial_acceleration_signature_physical_mm_per_s2": [float(v) for v in diagonal_physical],
            "diagonal_only_initial_acceleration_signature_q11_mm_per_s2": float(diagonal_acceleration[9]),
            "diagonal_only_signature_is_failure_diagnostic": True,
            "interpretation": "The all-ones physical acceleration is the coordinate-invariant mechanical oracle. The separate diagonal-only signature is a source-sensitive failure diagnostic, never an acceptance result.",
        },
        "time_control": {
            "procedure": "*DYNAMIC,EXPLICIT=2,ALPHA=0",
            "explicit_alpha": 0.0,
            "source_beta": 0.25,
            "source_gamma": 0.5,
            "initial_time_increment_s": 0.001,
            "step_period_s": 0.1,
            "minimum_time_increment": None,
            "maximum_time_increment_s": 0.001,
            "direct_parameter": False,
            "expected_final_u1_mm": 0.005,
            "expected_final_v1_mm_per_s": 0.1,
            "expected_final_ELKE_Nmm": 0.005,
            "accepted_increment_count_is_not_assumed": True,
        },
        "tolerance": {
            "relative": 1e-4,
            "absolute": 1e-9,
            "applies_to": ["physical U/V", "mapped controller U", "ELSE", "ELKE", "EMAS", "EVOL", "ENER"],
            "formula": "abs(actual-expected) <= absolute + relative*abs(expected)",
            "RF": "required finite physical-node coverage only; diagnostic, no reaction-magnitude oracle",
        },
        "execution": {"native_run": False, "input_freeze": False,
                      "mechanics_acceptance": False, "joint_acceptance": False},
    }
    return preflight, {"mesh": mesh, "volume_mm3": volume}, masses, load_tokens


def build_all() -> tuple[dict[str, bytes], dict]:
    source_snapshot, source_archive_bytes = require_pinned_sources()
    mesh = mesh_record()
    preflight, _mesh_details, masses, load_tokens = analytical_preflight(mesh)
    mesh_bytes = canonical_json(mesh)
    mesh_hash = sha256(mesh_bytes)
    direct = create_deck("direct", mesh, load_tokens)
    mapped = create_deck("mapped", mesh, load_tokens)
    deck_hashes = {"direct": sha256(direct), "mapped": sha256(mapped)}
    expected = {
        "schema": SCHEMA,
        "case_order": CASE_ORDER,
        "mesh_sha256": mesh_hash,
        "deck_sha256": deck_hashes,
        "inputs": {"direct": "input/direct.inp", "mapped": "input/mapped.inp"},
        "mesh": mesh,
        "material": {"E_N_per_mm2": 1.0, "nu": 0.0, "density_tonne_per_mm3": 6.0},
        "solver": {"version": "2.23", "image_id": IMAGE_ID,
                   "binary_sha256": BINARY_SHA256},
        "cases": {
            "direct": {"physical_node_ids": list(range(1, 11)),
                       "controller_node_ids": [],
                       "constraint": "U2=U3=0 on all physical nodes; all physical U1 free."},
            "mapped": {"physical_node_ids": list(range(1, 11)),
                       "controller_node_ids": [11],
                       "constraint": "Homogeneous equation u1+u2+u3+u4-4*q11=0 with physical node 1 U1 dependent; q11 U1 free; U2/U3 fixed on all physical nodes and controller."},
        },
        "source_lumped_mass": {
            "parameter_alp": 0.1203,
            "corner_node_ids": [1, 2, 3, 4],
            "corner_mass_tonne_each_exact": "1203/44812",
            "midside_node_ids": [5, 6, 7, 8, 9, 10],
            "midside_mass_tonne_each_exact": "5000/33609",
            "mass_tonne_each_serialized": [float(value) for value in masses],
            "CLOAD_N_each_serialized": [float(value) for value in map(float, load_tokens)],
        },
        "known_answer": {
            "initial_velocity_mm_per_s": 0.0,
            "constant_physical_acceleration_mm_per_s2": 1.0,
            "physical_u1_mm_at_time_s": "0.5*t_s^2",
            "physical_v1_mm_per_s_at_time_s": "t_s",
            "mapped_q11_u1_mm_at_time_s": "0.5*t_s^2",
            "mapped_q11_v1_mm_per_s_at_time_s": "t_s",
            "physical_u2_u3_v2_v3": 0.0,
            "body_ELSE_Nmm": 0.0,
            "body_ELKE_Nmm_at_time_s": "0.5*t_s^2",
            "body_EMAS_tonne": 1.0,
            "body_EVOL_mm3": 1.0 / 6.0,
            "ENER_frd": 0.0,
            "final_time_s": 0.1,
            "final_u1_mm": 0.005,
            "final_v1_mm_per_s": 0.1,
            "final_ELKE_Nmm": 0.005,
            "final_total_CLOAD_N": float(sum(Fraction.from_float(float(v)) for v in load_tokens)),
            "tolerance_relative": 1e-4,
            "tolerance_absolute": 1e-9,
            "explicit_alpha_beta_gamma": {"alpha": 0.0, "beta": 0.25, "gamma": 0.5},
        },
        "output_contract": {
            "accepted_state_identity": "Use FRD 1PSTEP/100CL step-increment-time headers as the authoritative state identity. In this single-step model, match DAT physical-node and energy blocks by reported time; do not require an independent DAT increment identity. Do not assume 100 increments. Frequency=1 requests output at every accepted increment; require emitted FRD frames through terminal native completion. STA/CVG rows and stdout increment traces are not state sources for this explicit branch.",
            "state_headers": {
                "FRD": ["1PSTEP", "100CL"],
                "DAT": ["reported table time"],
                "matched_key": ["single step", "time"],
                "coverage": "Each emitted FRD frame is matched to DAT physical-node and energy records at the same reported time. FRD supplies increment identity; DAT increment identity is not required. Terminal frame reaches the requested 0.1 s period.",
                "native_terminal_gate": "Normal process/container completion with no timeout or OOM, plus final output frame at the requested step period.",
            },
            "node_print_physical": ["U", "RF", "V"],
            "node_file_physical": ["U", "RF", "V"],
            "frd_field_labels": {"U": "DISP", "RF": "FORC", "V": "VELO", "ENER": "ENER"},
            "controller_node_print_DAT_only": ["U"],
            "controller_node_file_requested": False,
            "element_print_DAT": ["ELSE", "ELKE", "EMAS", "EVOL"],
            "element_file_FRD": ["ENER"],
            "ENER_location": "Nodally averaged element output, expected at the ten physical-node labels under one C3D10.",
            "required_physical_node_coverage": {"DAT": 10, "FRD": 10},
            "RF_role": "Finite/full-coverage diagnostic only; no RF magnitude acceptance oracle.",
            "ENER_role": "Pinned *EL FILE manual defines FRD element fields as nodally averaged and ENER as energy density; expect zero at the ten physical nodes. It is a diagnostic, not the kinetic-energy oracle.",
            "STA_CVG": "Explicit branch does not emit numeric STA/CVG state rows; preserve files if present, but do not require or parse them as state sources.",
        },
        "acceptance_boundary": {
            "method_fixture_only": True,
            "current_joint_acceptance": False,
            "structural_criterion_acceptance": False,
            "physical_demand_history": False,
            "native_execution_authorized_by_this_packet": False,
        },
    }
    readme = make_readme(expected, source_snapshot, preflight)
    readiness = {
        "schema": "calculix_explicit_c3d10_mpc_readiness/v1",
        "status": "PREPARED_AWAITING_PARENT_REVIEW",
        "preparation_checks": "PASS",
        "native_ready": False,
        "freeze_created": False,
        "native_execution": False,
        "parent_review_required": True,
        "scope": "Small C3D10 mass-bearing homogeneous-MPC coordinate-invariance method check only.",
        "mechanics_acceptance": False,
        "work_energy_acceptance": False,
        "current_joint_acceptance": False,
        "release": False,
        "expected_sha256": sha256(canonical_json(expected)),
        "deck_sha256": deck_hashes,
        "mesh_sha256": mesh_hash,
    }
    files = {
        "input/direct.inp": direct,
        "input/mapped.inp": mapped,
        "expected.json": canonical_json(expected),
        "source-snapshot.json": canonical_json(source_snapshot),
        "preflight.json": canonical_json(preflight),
        "readiness.json": canonical_json(readiness),
        "README.md": readme.encode("utf-8"),
    }
    metadata = {
        "schema": "calculix_explicit_c3d10_mpc_preparation_metadata/v1",
        "status": "PASS_PREPARATION_ONLY",
        "generated_paths": sorted(files),
        "mesh_sha256": mesh_hash,
        "deck_sha256": deck_hashes,
        "source_archive_sha256": sha256(source_archive_bytes),
        "native_run": False,
        "input_freeze": False,
    }
    return files, metadata


def make_readme(expected: dict, source_snapshot: dict, preflight: dict) -> str:
    direct = expected["deck_sha256"]["direct"]
    mapped = expected["deck_sha256"]["mapped"]
    return f"""# Explicit C3D10 MPC mass-coordinate known-answer, attempt 01

Status: preparation only. No native job or input freeze has been created.
Parent owns readiness review, verifier, freeze, and any serialized execution.

## Question and scope

This two-deck method fixture asks whether pinned CalculiX 2.23 explicit
structural dynamics preserves physical motion when the same free straight
C3D10 tetrahedron is expressed in either direct physical displacement
coordinates or an equivalent homogeneous MPC coordinate map. It specifically
checks the inertia/mass-bearing path through one dependent physical DOF and a
free controller DOF. It adds no physical restraint: the mapped form is an
invertible coordinate substitution and the controller is not prescribed.

Both decks use one unit tetrahedron, `E=1 N/mm²`, `nu=0`, and
`rho=6 tonne/mm³`; all physical U1 DOFs are free and physical U2/U3 are fixed.
The mapped deck adds only
`u1 + u2 + u3 + u4 - 4*q11 = 0`, with physical node 1 U1 dependent. The
constant physical nodal loads are `f_i = m_i * 1 mm/s²` for all ten nodes,
using the source-derived CalculiX C3D10 explicit lumped mass. Loads have no
amplitude and therefore start at full strength in the dynamic step.

The invariant analytical solution is rigid translation:
`U1(t)=0.5*t² mm`, `V1(t)=t mm/s` at each physical node, and the same motion
for mapped coordinate `q11`. There is zero strain, `ELSE=0`, body mass is
`EMAS=1 tonne`, and total `ELKE=0.5*t² N·mm`. At the requested final time
0.1 s, the values are 0.005 mm, 0.1 mm/s, 0.005 N·mm, and 1 tonne. This checks
the *declared explicit lumped-mass system*, not consistent-mass equivalence.

## Time integration and output

The cards use `*DYNAMIC,EXPLICIT=2,ALPHA=0`, initial/max increment 0.001 s,
period 0.1 s, no `DIRECT`, and a blank minimum-increment field. The pinned
manual states that explicit structural dynamics uses lumped mass and one
iteration per increment; leaving minimum increment blank avoids requesting
selective mass scaling or spring-stiffness reduction. No mass/stiffness scaling
is authorized. The pinned `nonlingeo.c` initialization computes beta=0.25 and
gamma=0.5 at alpha=0, the undamped constant-acceleration coefficients used by
this trajectory oracle. Actual accepted times and increments must be read from
native output rather than assuming 100 increments.

Physical `U,RF,V` are requested in DAT and FRD for nodes 1–10. The mapped
controller `U` is requested in DAT only. Element `ELSE,ELKE,EMAS,EVOL` totals
are requested in DAT; `ENER` is requested in FRD as a nodally averaged
zero-strain energy-density diagnostic, not as the kinetic-energy oracle. The
pinned manual documents that output identity, but the exact zero-valued native
field block remains unobserved until parent-owned execution. Require full
finite physical node coverage. Use the FRD step/increment/time headers to key
frames and match DAT blocks by reported time for this single-step model; FRD
supplies increment identity, while DAT increment identity is not required.
`FREQUENCY=1` requests output at every accepted increment; require emitted FRD
frames through normal terminal completion. The explicit branch does not call the
STA/CVG writers or print the implicit increment trace, so these may be absent or
header-only and stdout is diagnostic/terminal evidence, not a state source. RF
is captured diagnostically with no reaction-magnitude gate.

For U, V, energies, mass, and ENER, the frozen comparison rule is
`abs(actual-expected) <= 1e-9 + 1e-4*abs(expected)`. The analytical oracle is
checked at the actual native-reported accepted times. The separate diagonal-
only initial-acceleration signature in `preflight.json` is a failure
diagnostic, never an alternative pass criterion.

## Pinned primary sources

- Official CalculiX 2.23 source archive SHA-256:
  `{source_snapshot['source_archive']['sha256']}`.
- `e_c3d.f` SHA-256
  `{source_snapshot['source_members']['CalculiX/ccx_2.23/src/e_c3d.f']['sha256']}`,
  lines 1921–1975: explicit C3D10 mass lumping, with the 10-node factor
  `alp=0.1203`.
- `nonlingeo.c` SHA-256
  `{source_snapshot['source_members']['CalculiX/ccx_2.23/src/nonlingeo.c']['sha256']}`,
  lines 899–1052, 1260–1444 and 1607–1615: dynamic initialization,
  stable-step selection, explicit initial acceleration from net force divided
  by lumped mass, and the implicit-only stdout increment-trace guard.
- `tempload.f` SHA-256
  `{source_snapshot['source_members']['CalculiX/ccx_2.23/src/tempload.f']['sha256']}`,
  lines 356–373: an unamplified load remains at full reference value in a
  non-static step.
- Official 2.23 manual PDF SHA-256: `{source_snapshot['manual']['pdf_sha256']}`.
  Relevant HTML manual pages and recorded digests are in `source-snapshot.json`:
  node180 (explicit integration/scaling), node273 (`*DYNAMIC`), node279 (`*EL FILE`
  and `ENER`), and node283 (`*EQUATION` first-term elimination).

The packet is reproducible against the pinned source archive and solver
profile. Input hashes are `direct={direct}` and `mapped={mapped}`; the shared
mesh digest is `{expected['mesh_sha256']}`.

## Limits

A pass would qualify only this single-element method question: whether this
homogeneous MPC coordinate substitution preserves a known force-driven
acceleration and energy response under the pinned explicit implementation.
It does not qualify contact, wood, bolts, joint bearing, the current joint,
service demand histories, or a quasi-static interpretation. It creates no
physical load history and makes no structural acceptance claim.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="Read-only comparison against generated packet files")
    args = parser.parse_args()
    files, metadata = build_all()
    if args.check:
        missing = [name for name in files if not (HERE / name).is_file()]
        changed = [name for name, data in files.items()
                   if (HERE / name).is_file() and (HERE / name).read_bytes() != data]
        if missing or changed:
            raise SystemExit(json.dumps({"status": "FAIL", "missing": missing,
                                         "changed": changed}, indent=2))
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return
    paths = [HERE / name for name in files]
    existing = [str(path.relative_to(HERE)) for path in paths if path.exists()]
    if existing:
        raise SystemExit("Refusing to overwrite existing packet artifacts: " + ", ".join(existing))
    for name, data in files.items():
        path = HERE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
