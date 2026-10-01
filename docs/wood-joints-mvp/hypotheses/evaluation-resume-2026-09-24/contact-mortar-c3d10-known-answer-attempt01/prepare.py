#!/usr/bin/env python3
"""Prepare a deterministic, non-executing C3D10 mortar known-answer packet."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tarfile
from typing import Iterable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
REFERENCE = (
    REPO
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    / "contact-output-known-answer-attempt01/baseline/coupon.inp"
)
REFERENCE_SHA256 = "059c07fb59b500e78578413d0d9538076cabacda7154b035baeee334fdc40404"
SOURCE_ARCHIVE = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/"
    "source.tar.bz2"
)
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
BASE_IMAGE_ID = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BASE_BINARY_SHA256 = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"

SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/contactpairs.f": (
        "e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488"
    ),
    "CalculiX/ccx_2.23/src/surfacebehaviors.f": (
        "f0088a364b9b069aa10be9c4b4f38d72df875295f339830d7e2df6762ad9e161"
    ),
    "CalculiX/ccx_2.23/src/getcontactparams.f": (
        "03384b3d55deb22010f19a4521f3b10380caaf16441d270bf35f886ec0aadbaa"
    ),
    "CalculiX/ccx_2.23/src/getnumberofnodes.f": (
        "5cbb55e69e10e63e7cb2ecd9900c0a42f660f798b05fcb6e0415b134a7281723"
    ),
    "CalculiX/ccx_2.23/src/slavintmortar.f": (
        "a993c9a84202b7ce642073e52994269697eb487afbc51c86ff61c303b4f6e808"
    ),
    "CalculiX/ccx_2.23/src/shape6tri.f": (
        "64f4596c6dc6ee41baf4cc514947c41348a43c0c6fd40763af07802cad23c2cc"
    ),
    "CalculiX/ccx_2.23/src/stressmortar.c": (
        "c62c65de7aba91260320a3c548ebc513a436e4243151ca0441dcc5d309dce621"
    ),
    "CalculiX/ccx_2.23/src/nonlingeo.c": (
        "8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f"
    ),
    "CalculiX/ccx_2.23/src/noelfiles.f": (
        "ed85b45d6987882e484f11a0be3dc9c2d716afba07d59483d364e0709107a59f"
    ),
    "CalculiX/ccx_2.23/src/mortar_prefrd.c": (
        "938f92db5dc4cd5beeeac0def8aa87d0688d7fdda4e7b39c9a02abedc40309ac"
    ),
    "CalculiX/ccx_2.23/src/frd.c": (
        "6439bca2ae53c813ab6887c3c560dd15db5947fd8cf9b9f01ada5753d5ed9915"
    ),
    "CalculiX/ccx_2.23/src/mortar_postfrd.c": (
        "df4111d2774c568a4fbebbf0ddfee09a8cbd75521ce749ccbff03d6d3c37aa54"
    ),
}

# C3D10 local edge positions: (1-2),(2-3),(3-1),(1-4),(2-4),(3-4).
TET10_EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
# Element-face labels using local corner indices and quadratic midside positions.
TET10_FACES = {
    "S1": ((0, 1, 2), (4, 5, 6), 3),
    "S2": ((0, 3, 1), (7, 8, 4), 2),
    "S3": ((1, 3, 2), (8, 9, 5), 0),
    "S4": ((2, 3, 0), (9, 7, 6), 1),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_reference() -> tuple[dict[int, tuple[float, float, float]], dict[str, dict[int, tuple[int, ...]]]]:
    raw = REFERENCE.read_bytes()
    if sha256(raw) != REFERENCE_SHA256:
        raise SystemExit("reference coupon hash mismatch; refusing to generate")
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[str, dict[int, tuple[int, ...]]] = {"UPPER": {}, "LOWER": {}}
    section = ""
    current_elset = ""
    for original in raw.decode("ascii").splitlines():
        line = original.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upper = line.upper()
            if upper == "*NODE":
                section = "NODE"
                current_elset = ""
            elif upper.startswith("*ELEMENT,"):
                section = "ELEMENT"
                current_elset = "UPPER" if "ELSET=UPPER" in upper else "LOWER"
            else:
                section = ""
                current_elset = ""
            continue
        fields = [item.strip() for item in line.split(",")]
        if section == "NODE":
            node_id = int(fields[0])
            nodes[node_id] = tuple(float(value) for value in fields[1:4])
        elif section == "ELEMENT":
            values = tuple(int(value) for value in fields)
            if len(values) != 11 or current_elset not in elements:
                raise SystemExit(f"unexpected C3D10 element row: {line}")
            elements[current_elset][values[0]] = values[1:]
    if len(nodes) != 54 or len(elements["UPPER"]) != 6 or len(elements["LOWER"]) != 6:
        raise SystemExit("reference mesh topology changed; refusing to generate")
    return nodes, elements


def scale_geometry(
    nodes: dict[int, tuple[float, float, float]],
    elements: dict[str, dict[int, tuple[int, ...]]],
) -> tuple[dict[int, tuple[float, float, float]], dict[str, set[int]]]:
    scale = 0.02
    scaled = {key: tuple(value * scale for value in xyz) for key, xyz in nodes.items()}
    part_nodes = {
        part: {node for connectivity in by_id.values() for node in connectivity}
        for part, by_id in elements.items()
    }
    tol = 1e-10
    for part, by_id in elements.items():
        for elem_id, connectivity in by_id.items():
            xyz = [scaled[node] for node in connectivity]
            corners = xyz[:4]
            for midside, (left, right) in zip(xyz[4:], TET10_EDGES, strict=True):
                midpoint = tuple((corners[left][axis] + corners[right][axis]) / 2 for axis in range(3))
                if max(abs(midside[axis] - midpoint[axis]) for axis in range(3)) > tol:
                    raise SystemExit(f"element {elem_id} has a non-midpoint C3D10 node")
            a, b, c, d = corners
            det = dot(sub(b, a), cross(sub(c, a), sub(d, a)))
            if det <= tol:
                raise SystemExit(f"element {elem_id} has a non-positive C3D10 Jacobian ({det})")
    return scaled, part_nodes


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(a[i] * b[i] for i in range(3))


def sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a[i] - b[i] for i in range(3))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def face_data(
    elem_id: int,
    connectivity: tuple[int, ...],
    label: str,
    nodes: dict[int, tuple[float, float, float]],
) -> tuple[tuple[int, ...], tuple[tuple[float, float, float], ...], float, float]:
    corner_local, midside_local, opposite_local = TET10_FACES[label]
    face_ids = tuple(connectivity[index] for index in (*corner_local, *midside_local))
    face_xyz = tuple(nodes[node] for node in face_ids)
    p0, p1, p2 = (nodes[connectivity[index]] for index in corner_local)
    opposite = nodes[connectivity[opposite_local]]
    normal = cross(sub(p1, p0), sub(p2, p0))
    if dot(normal, sub(opposite, p0)) > 0:
        normal = tuple(-value for value in normal)
    normal_z = normal[2] / math.sqrt(dot(normal, normal))
    area = math.sqrt(dot(normal, normal)) / 2
    if not math.isfinite(area) or area <= 0:
        raise SystemExit(f"element {elem_id} {label} has an invalid face area")
    return face_ids, face_xyz, area, normal_z


def validate_contact_mesh(
    nodes: dict[int, tuple[float, float, float]],
    elements: dict[str, dict[int, tuple[int, ...]]],
) -> dict[str, object]:
    upper_faces = [face_data(eid, elements["UPPER"][eid], "S1", nodes) for eid in (1, 2)]
    lower_faces = [face_data(eid, elements["LOWER"][eid], "S3", nodes) for eid in (11, 12)]
    if len(upper_faces) != len(lower_faces):
        raise SystemExit("contact face count mismatch")

    def coordinate_key(face: tuple[tuple[float, float, float], ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(sorted(tuple(round(value, 10) for value in xyz) for xyz in face))

    upper_keys = sorted(coordinate_key(face[1]) for face in upper_faces)
    lower_keys = sorted(coordinate_key(face[1]) for face in lower_faces)
    if upper_keys != lower_keys:
        raise SystemExit("selected upper/lower quadratic faces do not conform")
    if not all(abs(node[2]) < 1e-10 for face in (*upper_faces, *lower_faces) for node in face[1]):
        raise SystemExit("selected faces are not on the z=0 interface")
    if not all(face[3] < -0.999999 for face in upper_faces):
        raise SystemExit("upper element-face ownership does not point outward toward -z")
    if not all(face[3] > 0.999999 for face in lower_faces):
        raise SystemExit("lower element-face ownership does not point outward toward +z")

    upper_area = sum(face[2] for face in upper_faces)
    lower_area = sum(face[2] for face in lower_faces)
    if abs(upper_area - 4.0) > 1e-10 or abs(lower_area - 4.0) > 1e-10:
        raise SystemExit(f"unexpected contact area: upper={upper_area}, lower={lower_area}")

    upper_slave_nodes = {node for face in upper_faces for node in face[0]}
    # The six-node faces share their diagonal's three nodes, leaving nine slave nodes.
    if len(upper_slave_nodes) != 9:
        raise SystemExit(f"unexpected unique slave node count: {len(upper_slave_nodes)}")

    # Each selected face must occur once on its own body's tetrahedral boundary.
    for part, selected_ids, label in (("UPPER", (1, 2), "S1"), ("LOWER", (11, 12), "S3")):
        face_owners: dict[tuple[int, ...], int] = {}
        for connectivity in elements[part].values():
            for face_label, (corner_local, _, _) in TET10_FACES.items():
                key = tuple(sorted(connectivity[index] for index in corner_local))
                face_owners[key] = face_owners.get(key, 0) + 1
        for elem_id in selected_ids:
            connectivity = elements[part][elem_id]
            key = tuple(sorted(connectivity[index] for index in TET10_FACES[label][0]))
            if face_owners.get(key) != 1:
                raise SystemExit(f"selected {part} element {elem_id} {label} is not exterior")

    return {
        "element_count": sum(len(group) for group in elements.values()),
        "c3d10_per_body": {name.lower(): len(group) for name, group in elements.items()},
        "node_count": len(nodes),
        "quadratic_contact_faces_per_side": 2,
        "unique_slave_face_nodes": len(upper_slave_nodes),
        "contact_area_mm2_each_side": upper_area,
        "source_geometry": "two blocks from the frozen C3D10 contact coupon scaled by 0.02",
        "source_face_labels": {"upper_slave": "elements 1,2 S1", "lower_master": "elements 11,12 S3"},
        "orientation": "upper outward normal -z; lower outward normal +z",
        "geometry_checks": [
            "all 12 corner tetrahedra have positive Jacobian",
            "all C3D10 midside nodes equal straight-edge midpoints",
            "each selected quadratic face is an exterior face owned by one tetrahedron",
            "upper/lower six-node faces match by coordinates",
            "selected contact faces lie on z=0 and cover A=4 mm2",
        ],
    }


def list_block(name: str, values: Iterable[int]) -> list[str]:
    ordered = list(values)
    lines = [f"*NSET,NSET={name}"]
    for start in range(0, len(ordered), 12):
        lines.append(",".join(str(value) for value in ordered[start : start + 12]))
    return lines


def make_deck(
    contact_type: str,
    nodes: dict[int, tuple[float, float, float]],
    elements: dict[str, dict[int, tuple[int, ...]]],
    part_nodes: dict[str, set[int]],
) -> bytes:
    side_length = 2.0
    top = sorted(node for node in part_nodes["UPPER"] if abs(nodes[node][2] - side_length) < 1e-10)
    bottom = sorted(node for node in part_nodes["LOWER"] if abs(nodes[node][2] + side_length) < 1e-10)
    if len(top) != 9 or len(bottom) != 9:
        raise SystemExit(f"unexpected top/bottom face node counts: {len(top)}/{len(bottom)}")
    top_corners = [node for node in top if nodes[node][0] in (0.0, side_length) and nodes[node][1] in (0.0, side_length)]
    bottom_corners = [node for node in bottom if nodes[node][0] in (0.0, side_length) and nodes[node][1] in (0.0, side_length)]

    def corner_at(candidates: list[int], xyz: tuple[float, float, float]) -> int:
        matches = [node for node in candidates if all(abs(nodes[node][i] - xyz[i]) < 1e-10 for i in range(3))]
        if len(matches) != 1:
            raise SystemExit(f"could not uniquely find fixture corner {xyz}")
        return matches[0]

    top_anchor_a = corner_at(top_corners, (0.0, 0.0, side_length))
    top_anchor_b = corner_at(top_corners, (side_length, 0.0, side_length))
    bottom_anchor_a = corner_at(bottom_corners, (0.0, 0.0, -side_length))
    bottom_anchor_b = corner_at(bottom_corners, (side_length, 0.0, -side_length))
    upper_interface = sorted(
        node for node in part_nodes["UPPER"] if abs(nodes[node][2]) < 1e-10
    )
    lower_interface = sorted(
        node for node in part_nodes["LOWER"] if abs(nodes[node][2]) < 1e-10
    )

    lines = [
        "*HEADING",
        "C3D10 compression/open/reopen method coupon; not a joint model",
        "** Units: mm, N, MPa (N/mm2); no friction or other contact pair",
        "*NODE",
    ]
    for node_id in sorted(nodes):
        xyz = ",".join(f"{value:.12g}" for value in nodes[node_id])
        lines.append(f"{node_id},{xyz}")
    for part, by_id in elements.items():
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={part}")
        for elem_id, connectivity in sorted(by_id.items()):
            lines.append(",".join((str(elem_id), *(str(node) for node in connectivity))))
    lines.extend(list_block("N_UPPER", sorted(part_nodes["UPPER"])))
    lines.extend(list_block("N_LOWER", sorted(part_nodes["LOWER"])))
    lines.extend(list_block("ALLNODES", sorted(nodes)))
    lines.extend(list_block("TOP", top))
    lines.extend(list_block("BOTTOM", bottom))
    lines.extend(list_block("SLAVE_NODES", upper_interface))
    lines.extend(list_block("MASTER_NODES", lower_interface))
    lines.extend(
        [
            "*MATERIAL,NAME=ELASTIC",
            "*ELASTIC",
            "100000,0.0",
            "*SOLID SECTION,ELSET=UPPER,MATERIAL=ELASTIC",
            "*SOLID SECTION,ELSET=LOWER,MATERIAL=ELASTIC",
            "*SURFACE,NAME=SLAVE,TYPE=ELEMENT",
            "1,S1",
            "2,S1",
            "*SURFACE,NAME=MASTER,TYPE=ELEMENT",
            "11,S3",
            "12,S3",
            "*SURFACE INTERACTION,NAME=NORMAL_LAW",
            "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
            "100000",
            "** No *FRICTION card; default tangential response is frictionless.",
            f"*CONTACT PAIR,INTERACTION=NORMAL_LAW,TYPE={contact_type}",
            "SLAVE,MASTER",
            "*BOUNDARY",
            "BOTTOM,3,3,0",
            "TOP,3,3,0",
            f"{top_anchor_a},1,1,0",
            f"{top_anchor_a},2,2,0",
            f"{top_anchor_b},2,2,0",
            f"{bottom_anchor_a},1,1,0",
            f"{bottom_anchor_a},2,2,0",
            f"{bottom_anchor_b},2,2,0",
        ]
    )
    for label, displacement in (("OPEN", 0.001), ("COMPRESSION", -0.005), ("REOPEN", 0.001)):
        lines.extend(
            [
                f"** STEP: {label}; prescribed top-face U3={displacement:+.6f} mm",
                "*STEP,NLGEOM,INC=100",
                "*STATIC",
                "0.1,1.0,1e-8,0.1",
                "*BOUNDARY",
                f"TOP,3,3,{displacement:.6f}",
                "*NODE PRINT,NSET=ALLNODES,FREQUENCY=1",
                "U,RF",
                "*NODE FILE,FREQUENCY=1",
                "U,RF",
                "*CONTACT FILE,FREQUENCY=1",
                "CDIS,CSTR",
                "*END STEP",
            ]
        )
    return ("\n".join(lines) + "\n").encode("ascii")


def dump_json(path: Path, value: object) -> bytes:
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    return data


def verify_source_pins(source_archive_path: Path) -> None:
    manual_path = REPO / "fea/generated/ccx_2.23.pdf"
    if sha256(manual_path.read_bytes()) != MANUAL_SHA256:
        raise SystemExit("pinned CalculiX 2.23 manual hash mismatch; refusing to prepare")
    with tarfile.open(source_archive_path, "r:bz2") as archive:
        members = {}
        for member in archive.getmembers():
            normalized = member.name.removeprefix("./")
            if normalized in SOURCE_MEMBERS:
                stream = archive.extractfile(member)
                if stream is None:
                    raise SystemExit(f"missing pinned source member: {normalized}")
                members[normalized] = sha256(stream.read())
    if members != SOURCE_MEMBERS:
        raise SystemExit("one or more pinned CalculiX source member hashes mismatch")


def main() -> None:
    for frozen_path in (HERE / "input-freeze.json", HERE / "execution.json", HERE / "output"):
        if frozen_path.exists():
            raise SystemExit(f"refusing to regenerate after freeze/execution evidence exists: {frozen_path}")
    source_archive_path = REPO / SOURCE_ARCHIVE
    if sha256(source_archive_path.read_bytes()) != SOURCE_ARCHIVE_SHA256:
        raise SystemExit("pinned source archive hash mismatch; refusing to prepare")
    verify_source_pins(source_archive_path)
    original_nodes, original_elements = read_reference()
    scaled_nodes, part_nodes = scale_geometry(original_nodes, original_elements)
    mesh = validate_contact_mesh(scaled_nodes, original_elements)

    input_dir = HERE / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_decks = {
        "mortar_c3d10.inp": make_deck("MORTAR", scaled_nodes, original_elements, part_nodes),
        "penalty_c3d10.inp": make_deck(
            "SURFACE TO SURFACE", scaled_nodes, original_elements, part_nodes
        ),
    }
    for name, data in input_decks.items():
        (input_dir / name).write_bytes(data)

    compliance = 2.0 / 100000.0 + 2.0 / 100000.0 + 1.0 / 100000.0
    displacement = 0.005
    pressure = displacement / compliance
    area = 4.0
    force = pressure * area
    upper_slave_nodes = sorted(
        {
            node
            for elem_id in (1, 2)
            for node in face_data(elem_id, original_elements["UPPER"][elem_id], "S1", scaled_nodes)[0]
        }
    )
    lower_master_nodes = sorted(
        {
            node
            for elem_id in (11, 12)
            for node in face_data(elem_id, original_elements["LOWER"][elem_id], "S3", scaled_nodes)[0]
        }
    )
    upper_nodes = sorted(part_nodes["UPPER"])
    lower_nodes = sorted(part_nodes["LOWER"])
    top_nodes = sorted(node for node in upper_nodes if abs(scaled_nodes[node][2] - 2.0) < 1e-10)
    bottom_nodes = sorted(node for node in lower_nodes if abs(scaled_nodes[node][2] + 2.0) < 1e-10)
    expected = {
        "schema": "calculix_mortar_c3d10_known_answer/v1",
        "status": "FROZEN_FOR_PARENT_REVIEW_BEFORE_NATIVE_EXECUTION",
        "solver": {
            "version": "2.23",
            "base_image_id": BASE_IMAGE_ID,
            "binary_path": "/usr/local/bin/ccx-upstream-2.23",
            "binary_sha256": BASE_BINARY_SHA256,
            "patched_or_instrumented_binary": False,
            "manual_url": "https://www.dhondt.de/ccx_2.23.pdf",
            "manual_sha256": MANUAL_SHA256,
        },
        "source": {
            "archive_path": SOURCE_ARCHIVE,
            "archive_sha256": SOURCE_ARCHIVE_SHA256,
            "source_members_sha256": SOURCE_MEMBERS,
            "notes": [
                "contactpairs.f maps TYPE=MORTAR to mortar mode 2 and SURFACE TO SURFACE to mode 1",
                "getcontactparams.f maps LINEAR slope K to mortar fkninv=1/K",
                "getnumberofnodes.f and slavintmortar.f route C3D10 six-node faces to shape6tri",
                "noelfiles.f and mortar_prefrd.c/frd.c enable MORTAR CDIS/CSTR output",
                "stressmortar.c clears iflagact when iit exceeds source-derived ndiverg",
            ],
        },
        "reference_geometry": {
            "path": str(REFERENCE.relative_to(REPO)),
            "sha256": REFERENCE_SHA256,
            "scale_factor": 0.02,
            "mesh": mesh,
        },
        "cases": {
            "mortar_c3d10": {
                "input": "input/mortar_c3d10.inp",
                "input_sha256": sha256(input_decks["mortar_c3d10.inp"]),
                "contact_type": "MORTAR",
            },
            "penalty_c3d10": {
                "input": "input/penalty_c3d10.inp",
                "input_sha256": sha256(input_decks["penalty_c3d10.inp"]),
                "contact_type": "SURFACE TO SURFACE",
                "role": "separate law-matched method comparison; never mixed in one deck",
            },
        },
        "material_and_contact": {
            "youngs_modulus_each_body_N_per_mm2": 100000.0,
            "poisson_ratio_each_body": 0.0,
            "linear_pressure_overclosure_slope_K_N_per_mm3": 100000.0,
            "friction": "none",
            "contact_area_mm2": area,
            "slave": "upper body elements 1,2 S1",
            "master": "lower body elements 11,12 S3",
        },
        "fixture": {
            "method": "uniform axial displacement; no external pressure or force",
            "lower_face_support": "lower bottom face U3=0",
            "minimum_lateral_rigid_mode_anchors": (
                "one bottom/top non-slave corner fixed U1,U2 and a second corner on +x fixed U2"
            ),
            "contact_slave_edge_nodes_with_extra_MPC_or_SPC": 0,
            "nlgeom": True,
            "strain_range_note": "The series-compliance oracle is a small-strain linear reference; peak axial strain is about 0.1%, so finite-geometry deviation is covered by predeclared tolerances.",
            "all_node_groups": {
                "upper_body_nodes": upper_nodes,
                "lower_body_nodes": lower_nodes,
                "top_face_nodes": top_nodes,
                "bottom_face_nodes": bottom_nodes,
                "upper_slave_interface_nodes": upper_slave_nodes,
                "lower_master_interface_nodes": lower_master_nodes,
            },
        },
        "steps": [
            {"step": 1, "name": "OPEN", "top_u3_mm": 0.001, "nominal_increments": 10},
            {"step": 2, "name": "COMPRESSION", "top_u3_mm": -0.005, "nominal_increments": 10},
            {"step": 3, "name": "REOPEN", "top_u3_mm": 0.001, "nominal_increments": 10},
        ],
        "requested_outputs": {
            "every_increment": ["U,RF for all nodes in FRD", "U,RF for ALLNODES in DAT", "CDIS,CSTR via CONTACT FILE"],
            "case_output_layout_for_runner": "output/<case>/coupon.{inp,dat,cvg,sta,frd,log}; output/<case>/coupon.stdout; output/<case>/coupon.stderr; output/<case>/execution.json",
            "trace_contract": {
                "cvg_iteration_columns": ["STEP", "INC", "ATT", "ITER"],
                "sta_accepted_columns": ["STEP", "INC", "ATT", "ITRS"],
                "mortar_max_captured_iter": 14,
                "accepted_sta_itrs_must_match_final_cvg_iter": True,
                "no_mortar_cvg_iter_above_14": True,
            },
            "cases": ["mortar_c3d10", "penalty_c3d10"],
            "contact_fields": {
                "expected_frd_names": ["COPEN", "CPRESS"],
                "interpretation": "diagnostic availability, coverage, and sign summaries only; MORTAR gap/stress are weighted/transformed",
                "hard_gate": "fields are present and finite; no pointwise sign, law, or integrated-force gate",
                "not_a_gate": "no pointwise CPRESS=K*(-COPEN) assertion",
            },
        },
        "analytical_known_answer": {
            "normal_compliance_mm3_per_N": compliance,
            "formula": "C = L_upper/E + L_lower/E + 1/K",
            "compression": {
                "top_displacement_mm": -displacement,
                "expected_contact_pressure_N_per_mm2": pressure,
                "expected_force_magnitude_N": force,
                "expected_top_RF3_N": -force,
                "expected_bottom_RF3_N": force,
                "expected_upper_interface_average_u3_mm": -0.003,
                "expected_lower_interface_average_u3_mm": -0.002,
                "expected_upper_elastic_shortening_mm": 0.002,
                "expected_lower_elastic_shortening_mm": 0.002,
                "expected_contact_law_compression_mm": 0.001,
            },
            "open_and_reopen": {
                "top_displacement_mm": 0.001,
                "geometric_interface_gap_mm": 0.001,
                "expected_top_RF3_N": 0.0,
                "expected_bottom_RF3_N": 0.0,
                "expected_contact_normal_traction": 0.0,
            },
            "all_accepted_increment_profile": {
                "step1_open": "u3_upper(z)=u_top; u3_lower(z)=0; geometric_gap=u_top, where u_top ramps 0→+0.001mm",
                "step2_compression": "u_top=0.001-0.006*t; if u_top>=0, upper is rigid-open u3=u_top and lower u3=0; otherwise p=-u_top/C, u3_lower(z)=-p*(z+2)/E, u3_upper(z)=-p*(2/E+1/K)-p*z/E",
                "step3_reopen": "u_top=-0.005+0.006*t; use the same compression profile while u_top<0, then upper rigid-open u3=u_top and lower u3=0",
                "interface_geometry_gap_sign": "upper slave U3 minus lower master U3; positive is clearance, negative is overlap",
                "expected_tangential_displacement": "U1=U2=0 throughout; report residuals",
            },
            "force_sign_basis": "RF3 at prescribed top nodes follows the negative compression motion; bottom support balances it, consistent with existing CalculiX 2.23 coupon DAT convention.",
            "predeclared_tolerances": {
                "force_relative_error": 0.01,
                "force_abs_error_N": 0.001,
                "force_acceptance_inequality": "abs(F_measured - F_analytic) <= 0.01 * F_analytic + 0.001 N",
                "pressure_compliance_relative_error": 0.01,
                "pressure_compliance_abs_error_mm3_per_N": 1e-10,
                "pressure_compliance_acceptance_inequality": "abs(C_measured - C_analytic) <= 0.01 * C_analytic + 1e-10 mm3/N",
                "compression_pressure_compliance_formula": "C_pressure = A * abs(top_U3) / abs(sum(TOP RF3)); evaluate only at the compression endpoint",
                "accepted_state_u3_profile_interface_gap_and_face_warp_mm": 1e-5,
                "open_reopen_resultant_support_force_norm_N": 0.001,
                "tangential_reaction_and_top_plus_bottom_force_closure_norm_N": "<= 0.001 + 0.01 * current_analytic_compression_force_N",
            },
        },
        "mortar_iteration_guard": {
            "source_file": "CalculiX/ccx_2.23/src/stressmortar.c",
            "source_sha256": SOURCE_MEMBERS["CalculiX/ccx_2.23/src/stressmortar.c"],
            "source_lines": {"ndiverg_initial": 138, "ndiverg_update": 210, "iflagact_override": 752},
            "formula": "ndiverg = max(14, floor(nhelp/100) + ntie)",
            "fixture_source_bound_counts": {"maximum_unique_slave_nodes_nhelp": 9, "contact_pair_count_ntie": 1},
            "source_derived_ndiverg": 14,
            "acceptance": "reject if any captured MORTAR iteration iit > 14; require accepted increments to converge at or below 14 before the source override can run",
        },
        "acceptance": {
            "require_all_three_steps_accepted": True,
            "require_all_captured_mortar_iit_at_or_below": 14,
            "require_open_compression_reopen_force_and_series_compliance": True,
            "require_compression_pressure_compliance_within_tolerance": True,
            "require_force_balance_top_plus_bottom": True,
            "require_all_node_displacement_output_and_uniform_axial_response": True,
            "require_contact_fields_present_and_finite": True,
            "contact_field_sign_or_pointwise_law_is_hard_gate": False,
            "compare_mortar_and_penalty_compression_force_within_relative_tolerance": 0.01,
            "native_execution_authorized": False,
            "mechanical_or_joint_acceptance": False,
        },
    }
    expected_bytes = dump_json(HERE / "expected.json", expected)
    readiness = {
        "schema": "calculix_mortar_c3d10_readiness/v1",
        "status": "READY_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "parent_owns": ["input freeze", "serialized bounded native execution", "execution/result records", "final validation"],
        "prepare_py_sha256": sha256(Path(__file__).read_bytes()),
        "reference_coupon_sha256": REFERENCE_SHA256,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "manual_sha256": MANUAL_SHA256,
        "expected_json_sha256": sha256(expected_bytes),
        "input_sha256": {name: sha256(data) for name, data in sorted(input_decks.items())},
        "static_preparation_checks": {
            "reference_hash_verified": True,
            "positive_corner_jacobians": True,
            "straight_quadratic_midpoints": True,
            "contact_face_ownership_and_orientation": True,
            "upper_lower_contact_mesh_conforming": True,
            "contact_area_mm2": 4.0,
            "mortar_pair_count": 1,
            "penalty_pair_count": 1,
            "mixed_contact_types_in_any_deck": False,
            "slave_mpc_or_spc_count": 0,
            "ndiverg_source_bound": 14,
        },
        "review_required_before_native_execution": True,
    }
    dump_json(HERE / "readiness.json", readiness)
    print(json.dumps(readiness, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
