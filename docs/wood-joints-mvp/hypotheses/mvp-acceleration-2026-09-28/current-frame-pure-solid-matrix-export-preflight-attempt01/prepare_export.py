#!/usr/bin/env python3
"""Build or verify an input-only pure-physical-solid MATRIXSTORAGE proposal."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
PINS_PATH = PACKET / "source-pins.json"
EXPECTED_PINS_SHA256 = "b3a47d14e438ba8f7717c91999cd98738ad569a371749f21a210b49cb8b44127"
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
ADAPTER = BASE / "current-springa-frame-input-adapter-attempt01"
RANK_PACKET = BASE / "current-frame-gravity-rank-readiness-attempt01"
GRAVITY_PACKET = BASE / "current-gravity-settle-climber-ramp-scenario-attempt01"
OPERATOR_PACKET = BASE / "current-native-elastic-operator-export-preflight-attempt01"
AUXILIARY_DENSITY_TONNE_PER_MM3 = 1.0e-9
AUXILIARY_DENSITY_TOKEN = "1.0e-9"
CASE_IDS = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
PHYSICAL_KEYWORDS = {
    "*MATERIAL",
    "*ELASTIC",
    "*ORIENTATION",
    "*SOLID SECTION",
}
PROPERTY_KEYWORDS = PHYSICAL_KEYWORDS | {"*DENSITY"}
EXPECTED_OUTPUT_KEYWORDS = {
    "*HEADING",
    "*NODE",
    "*ELEMENT",
    "*MATERIAL",
    "*ELASTIC",
    "*DENSITY",
    "*ORIENTATION",
    "*SOLID SECTION",
    "*STEP",
    "*FREQUENCY",
    "*END STEP",
}


class ProposalError(ValueError):
    pass


@dataclass
class Block:
    header: str
    lines: list[str] = field(default_factory=list)

    @property
    def keyword(self) -> str:
        return self.header.strip().split(",", 1)[0].upper()

    @property
    def options(self) -> dict[str, str | None]:
        parts = self.header.strip().split(",")
        result: dict[str, str | None] = {}
        for token in parts[1:]:
            token = token.strip()
            if not token:
                continue
            if "=" in token:
                key, value = token.split("=", 1)
                result[key.strip().upper()] = value.strip()
            else:
                result[token.upper()] = None
        return result


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    full = path if path.is_absolute() else ROOT / path
    return sha256_bytes(full.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def write_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def read_json(path: Path) -> Any:
    full = path if path.is_absolute() else ROOT / path
    return json.loads(full.read_text(encoding="utf-8"))


def verify_source_pins() -> dict[str, Any]:
    observed_pins_hash = sha256_file(PINS_PATH)
    if observed_pins_hash != EXPECTED_PINS_SHA256:
        raise ProposalError(
            f"source-pins.json changed: {observed_pins_hash} != {EXPECTED_PINS_SHA256}"
        )
    pins = read_json(PINS_PATH)
    if pins.get("schema") != "current_frame_pure_solid_matrix_export_source_pins/v1":
        raise ProposalError("unexpected source pin schema")
    seen: set[str] = set()
    for row in pins.get("files", []):
        path = str(row["path"])
        if path in seen:
            raise ProposalError(f"duplicate source pin path: {path}")
        seen.add(path)
        observed = sha256_file(Path(path))
        if observed != row["sha256"]:
            raise ProposalError(f"pinned input changed: {path}: {observed} != {row['sha256']}")
    if not seen:
        raise ProposalError("source pin list is empty")

    archive = Path(pins["source_archive"]["path"])
    archive_hash = sha256_file(archive)
    if archive_hash != pins["source_archive"]["sha256"]:
        raise ProposalError(f"CalculiX source archive changed: {archive_hash}")
    with tarfile.open(archive, mode="r:bz2") as archive_file:
        members = set(archive_file.getnames())
        for row in pins["source_archive"]["members"]:
            member_path = str(row["path"])
            if member_path not in members:
                raise ProposalError(f"missing pinned source member {member_path}")
            source = archive_file.extractfile(member_path)
            if source is None:
                raise ProposalError(f"cannot read pinned source member {member_path}")
            observed = sha256_bytes(source.read())
            if observed != row["sha256"]:
                raise ProposalError(f"source member changed: {member_path}: {observed}")
    return pins


def parse_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    current: Block | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**") or not stripped:
            continue
        if stripped.startswith("*"):
            if current is not None:
                blocks.append(current)
            current = Block(header=line)
        elif current is not None:
            current.lines.append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def render_block(block: Block, header: str | None = None) -> list[str]:
    result = [header if header is not None else block.header]
    result.extend(block.lines)
    return result


def adapter_node_real(value: float) -> str:
    """Match the source deck writer's coordinate token (Python .14g)."""
    number = float(value)
    if not math.isfinite(number):
        raise ProposalError("nonfinite source coordinate")
    token = format(number, ".14g")
    if len(token) > 20:
        raise ProposalError(f"source coordinate exceeds the adapter real width: {token}")
    return token


def parse_node_block(block: Block) -> dict[int, tuple[str, list[str]]]:
    nodes: dict[int, tuple[str, list[str]]] = {}
    for line in block.lines:
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 4:
            raise ProposalError(f"expected one node ID and three coordinates: {line!r}")
        try:
            node = int(fields[0])
            xyz = [float(value) for value in fields[1:]]
        except ValueError as exc:
            raise ProposalError(f"invalid node record {line!r}") from exc
        if node in nodes or not all(math.isfinite(value) for value in xyz):
            raise ProposalError(f"duplicate or nonfinite node record {node}")
        nodes[node] = (line, fields[1:])
    return nodes


def parse_element_block(block: Block) -> list[tuple[int, list[int]]]:
    values: list[int] = []
    for line in block.lines:
        for token in line.split(","):
            token = token.strip()
            if token:
                values.append(int(token))
    if len(values) % 21:
        raise ProposalError(
            f"C3D20 data do not form 21-integer records in {block.header}: {len(values)} fields"
        )
    result = []
    for start in range(0, len(values), 21):
        record = values[start : start + 21]
        result.append((record[0], record[1:]))
    return result


def normalized_property_cards(blocks: list[Block], *, omit_density: bool = False) -> list[str]:
    cards: list[str] = []
    targets = PROPERTY_KEYWORDS - ({"*DENSITY"} if omit_density else set())
    for block in blocks:
        if block.keyword not in targets:
            continue
        rows = [re.sub(r"\s+", "", block.header).upper()]
        rows.extend(re.sub(r"\s+", "", line).upper() for line in block.lines if line.strip())
        cards.append("\n".join(rows))
    return cards


def card_hash(cards: list[str]) -> str:
    return sha256_bytes("\n\n".join(cards).encode("utf-8"))


def normalize_map(loads: dict[Any, Any]) -> dict[str, list[float]]:
    return {
        str(int(node)): [float(value) for value in vector]
        for node, vector in sorted(loads.items(), key=lambda item: int(item[0]))
    }


def add_force(target: dict[str, list[float]], node: Any, force: list[float]) -> None:
    key = str(int(node))
    vector = target.setdefault(key, [0.0, 0.0, 0.0])
    for axis in range(3):
        vector[axis] += float(force[axis])


def build_load_map_packet(decomposition: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    cases = decomposition["cases"]
    by_case = {str(row["case_id"]): row for row in cases}
    if list(by_case) != CASE_IDS or set(by_case) != set(CASE_IDS):
        raise ProposalError("six-case gravity packet has an unexpected case set or order")
    map_cases = []
    summaries = []
    for case_id in CASE_IDS:
        report = by_case[case_id]
        model_path = Path(str(report["input_model_path"]))
        model = read_json(model_path)
        if sha256_file(model_path) != report["input_model_sha256"]:
            raise ProposalError(f"{case_id}: input model hash differs from decomposition")
        if model.get("case_id") != case_id:
            raise ProposalError(f"{case_id}: source input model case ID mismatch")
        total = normalize_map(model["physical_external_loads"])
        if total != normalize_map(model["loads"]):
            raise ProposalError(f"{case_id}: total source map differs from serialized load map")
        total_hash = canonical_hash(total)
        if total_hash != report["source_load_register_map_sha256"]:
            raise ProposalError(f"{case_id}: total nodal map differs from source register")
        patches = [
            row for row in model["panel_load_records"]
            if row.get("load_kind") == "uniform_square_patch_wrench"
        ]
        if len(patches) != 1:
            raise ProposalError(f"{case_id}: expected exactly one climber patch map")
        climber: dict[str, list[float]] = {}
        for row in patches[0]["physical_body_nodal_forces"]:
            add_force(climber, row["node"], row["force_xyz_n"])
        gravity = {
            node: [
                total[node][axis] - climber.get(node, [0.0, 0.0, 0.0])[axis]
                for axis in range(3)
            ]
            for node in sorted(total, key=int)
        }
        residual = 0.0
        exact_recomposition = True
        for node, total_force in total.items():
            for axis in range(3):
                recomposed = gravity[node][axis] + climber.get(node, [0.0, 0.0, 0.0])[axis]
                residual = max(residual, abs(recomposed - total_force[axis]))
                exact_recomposition = exact_recomposition and recomposed == total_force[axis]
        gravity_hash = canonical_hash(gravity)
        climber_hash = canonical_hash(climber)
        if gravity_hash != report["gravity_nodal_map_sha256"]:
            raise ProposalError(f"{case_id}: reconstructed gravity map differs from pinned summary")
        if climber_hash != report["climber_nodal_map_sha256"]:
            raise ProposalError(f"{case_id}: reconstructed climber map differs from pinned summary")
        if len(gravity) != report["gravity_nodal_map_node_count"]:
            raise ProposalError(f"{case_id}: reconstructed gravity map node count changed")
        if len(climber) != report["climber_nodal_map_node_count"]:
            raise ProposalError(f"{case_id}: reconstructed climber map node count changed")
        if not exact_recomposition or residual != 0.0:
            raise ProposalError(f"{case_id}: gravity plus climber does not exactly recompose total map")
        if int(report["physical_body_count"]) != 50:
            raise ProposalError(f"{case_id}: decomposition does not cover all 50 physical bodies")
        map_cases.append(
            {
                "case_id": case_id,
                "units": {"force": "N", "coordinate": "mm"},
                "source_input_model_path": model_path.as_posix(),
                "source_input_model_sha256": report["input_model_sha256"],
                "source_total_map_sha256": total_hash,
                "source_load_register_map_sha256": report["source_load_register_map_sha256"],
                "gravity_nodal_map_sha256": gravity_hash,
                "climber_nodal_map_sha256": climber_hash,
                "gravity_nodal_map_node_count": len(gravity),
                "climber_nodal_map_node_count": len(climber),
                "exact_nodal_recomposition": exact_recomposition,
                "gravity_nodal_map": gravity,
                "climber_nodal_map": climber,
            }
        )
        summaries.append(
            {
                "case_id": case_id,
                "input_model_sha256": report["input_model_sha256"],
                "total_map_sha256": total_hash,
                "gravity_map_sha256": gravity_hash,
                "climber_map_sha256": climber_hash,
                "gravity_map_node_count": len(gravity),
                "climber_map_node_count": len(climber),
                "exact_nodal_recomposition": exact_recomposition,
                "gravity_force_xyz_N": report["gravity_force_xyz_N"],
                "gravity_moment_about_origin_xyz_Nmm": report["gravity_moment_about_origin_xyz_Nmm"],
                "climber_force_xyz_N": report["climber_force_xyz_N"],
                "climber_moment_about_origin_xyz_Nmm": report["climber_moment_about_origin_xyz_Nmm"],
            }
        )
    packet = {
        "schema": "current_frame_external_load_maps_separate_from_operator/v1",
        "status": "SOURCE_MAPS_ONLY_NOT_EMITTED_IN_PURE_SOLID_DECK",
        "scope": (
            "The six pinned source-case gravity and climber nodal maps are preserved as explicit loads. "
            "Only a12-rear corresponds to the pure-solid deck in this packet; other case maps are retained "
            "as separate case evidence and are not projected onto this deck."
        ),
        "cases": map_cases,
    }
    return packet, {
        "case_summaries": summaries,
        "upstream_decomposition_status": decomposition["status"],
        "upstream_decomposition_sha256": sha256_file(GRAVITY_PACKET / "decomposition.json"),
        "six_case_gravity_map_max_component_difference_N": decomposition["gravity_source_inventory"][
            "case_gravity_map_max_component_difference_N"
        ],
    }


def material_name(block: Block) -> str:
    name = block.options.get("NAME")
    if not name:
        raise ProposalError(f"material card has no NAME: {block.header}")
    return str(name)


def build_proposal() -> dict[str, bytes]:
    pins = verify_source_pins()
    model_path = ADAPTER / "a12-rear" / "model.json"
    input_deck_path = ADAPTER / "a12-rear" / "model.inp"
    model = read_json(model_path)
    source_text = (ROOT / input_deck_path).read_text(encoding="utf-8")
    source_blocks = parse_blocks(source_text)
    c11_path = next(
        Path(path)
        for path in read_json(ADAPTER / "source-pins.json")["pinned_inputs"]
        if path.endswith("cycle-11-sign-closure-r1/model.inp")
    )
    c11_blocks = parse_blocks((ROOT / c11_path).read_text(encoding="utf-8"))

    if model.get("schema") != "current_springa_frame_input_model/v1":
        raise ProposalError("unexpected current adapter model schema")
    if model.get("candidate") != pins["candidate"]:
        raise ProposalError("candidate differs from source-pinned proposal")
    if model.get("geometry_revision_id") != pins["geometry_revision_id"]:
        raise ProposalError("geometry revision differs from source-pinned proposal")
    if model.get("case_id") != "a12-rear" or model.get("native_solve_executed") is not False:
        raise ProposalError("current adapter input is not the expected input-only a12-rear case")
    if sha256_file(model_path) != read_json(ADAPTER / "source-pins.json")["output_model_sha256"]:
        raise ProposalError("adapter model hash changed")
    if sha256_file(input_deck_path) != read_json(ADAPTER / "source-pins.json")["output_deck_sha256"]:
        raise ProposalError("adapter deck hash changed")

    node_blocks = [block for block in source_blocks if block.keyword == "*NODE"]
    if len(node_blocks) != 1:
        raise ProposalError(f"expected one source node block, found {len(node_blocks)}")
    source_nodes = parse_node_block(node_blocks[0])
    model_nodes = {int(node): xyz for node, xyz in model["nodes"].items()}
    if set(source_nodes) != set(model_nodes):
        raise ProposalError("source deck node IDs differ from adapter model node IDs")
    for node, xyz in model_nodes.items():
        expected = [adapter_node_real(value) for value in xyz]
        observed = source_nodes[node][1]
        if observed != expected:
            raise ProposalError(f"node {node}: source deck coordinates do not match adapter serialization")

    body_nodes = {str(body): {int(node) for node in nodes} for body, nodes in model["physical_body_nodes"].items()}
    body_elements = {
        str(body): {int(element) for element in elements}
        for body, elements in model["physical_body_elements"].items()
    }
    if len(body_nodes) != 50 or set(body_nodes) != set(model["expected_physical_body_names"]):
        raise ProposalError("physical-body node ownership is not exactly the 50 expected bodies")
    if set(body_elements) != set(body_nodes):
        raise ProposalError("physical-body element ownership differs from body node ownership")
    node_owners: dict[int, str] = {}
    for body, nodes in body_nodes.items():
        for node in nodes:
            if node in node_owners:
                raise ProposalError(f"physical node {node} is owned by multiple bodies")
            node_owners[node] = body
    element_owners: dict[int, str] = {}
    for body, elements in body_elements.items():
        for element in elements:
            if element in element_owners:
                raise ProposalError(f"physical element {element} is owned by multiple bodies")
            element_owners[element] = body
    physical_nodes = set(node_owners)
    physical_elements = set(element_owners)
    source_fixed_nodes = {int(node) for node in model["fixed_nodes"]}
    if source_fixed_nodes & physical_nodes:
        raise ProposalError("source SPC inventory unexpectedly includes a physical solid node")

    c3d20_blocks = [
        block
        for block in source_blocks
        if block.keyword == "*ELEMENT" and block.options.get("TYPE", "").upper() == "C3D20"
    ]
    if not c3d20_blocks:
        raise ProposalError("no source C3D20 element blocks found")
    expected_elements: dict[int, tuple[list[int], str]] = {}
    for element, raw in model["elements"].items():
        kind, connectivity, group = raw
        if kind == "C3D20":
            expected_elements[int(element)] = ([int(node) for node in connectivity], str(group))
    source_element_records: dict[int, list[int]] = {}
    element_set_rows: list[dict[str, Any]] = []
    elset_names: set[str] = set()
    element_block_by_elset: dict[str, Block] = {}
    for block in c3d20_blocks:
        elset = block.options.get("ELSET")
        if not elset:
            raise ProposalError(f"physical solid element block lacks ELSET: {block.header}")
        elset = str(elset)
        if elset in elset_names:
            raise ProposalError(f"duplicate C3D20 element set {elset}")
        elset_names.add(elset)
        element_block_by_elset[elset] = block
        rows = parse_element_block(block)
        if not rows:
            raise ProposalError(f"empty C3D20 element set {elset}")
        owners = set()
        for element, connectivity in rows:
            if element in source_element_records:
                raise ProposalError(f"duplicate C3D20 element ID {element}")
            source_element_records[element] = connectivity
            owner = element_owners.get(element)
            if owner is None:
                raise ProposalError(f"C3D20 element {element} is not assigned to any physical body")
            owners.add(owner)
            expected = expected_elements.get(element)
            if expected is None or connectivity != expected[0] or expected[1] != elset:
                raise ProposalError(f"C3D20 element {element} differs from adapter connectivity/body map")
        if len(owners) != 1:
            raise ProposalError(f"C3D20 elset {elset} spans multiple physical bodies: {sorted(owners)}")
        element_set_rows.append(
            {"elset": elset, "physical_body": next(iter(owners)), "element_count": len(rows)}
        )
    if set(source_element_records) != physical_elements or set(source_element_records) != set(expected_elements):
        raise ProposalError("source C3D20 IDs differ from the 50-body physical-element inventory")
    if len(expected_elements) != 1903 or len(physical_nodes) != 12549:
        raise ProposalError("current physical solid inventory is not 1,903 C3D20 / 12,549 nodes")
    connected_nodes = {node for row in source_element_records.values() for node in row}
    if connected_nodes != physical_nodes:
        raise ProposalError(
            f"C3D20 coverage differs from physical node ownership: missing={len(physical_nodes-connected_nodes)}, "
            f"extra={len(connected_nodes-physical_nodes)}"
        )
    if not physical_nodes <= set(source_nodes):
        raise ProposalError("physical body ownership refers to nodes absent from source deck")

    section_blocks = [block for block in source_blocks if block.keyword == "*SOLID SECTION"]
    material_blocks = [block for block in source_blocks if block.keyword == "*MATERIAL"]
    elastic_blocks = [block for block in source_blocks if block.keyword == "*ELASTIC"]
    orientation_blocks = [block for block in source_blocks if block.keyword == "*ORIENTATION"]
    density_blocks = [block for block in source_blocks if block.keyword == "*DENSITY"]
    c11_density_blocks = [block for block in c11_blocks if block.keyword == "*DENSITY"]
    if density_blocks:
        raise ProposalError("unexpected source density exists; proposal's auxiliary-density difference must be reviewed")
    if c11_density_blocks:
        raise ProposalError("pinned C11 property deck contains density; auxiliary-density premise must be reviewed")
    if (len(material_blocks), len(elastic_blocks), len(orientation_blocks), len(section_blocks)) != (50, 50, 50, 68):
        raise ProposalError("unexpected source material/orientation/solid-section inventory")

    material_names = {material_name(block) for block in material_blocks}
    orientation_names = {str(block.options.get("NAME", "")) for block in orientation_blocks}
    if len(material_names) != 50 or len(orientation_names) != 50:
        raise ProposalError("material or orientation names are not unique")
    sections_by_elset: dict[str, dict[str, str]] = {}
    for block in section_blocks:
        options = block.options
        elset, material, orientation = options.get("ELSET"), options.get("MATERIAL"), options.get("ORIENTATION")
        if not (elset and material and orientation):
            raise ProposalError(f"incomplete solid section association: {block.header}")
        if str(elset) in sections_by_elset:
            raise ProposalError(f"duplicate solid section assignment for {elset}")
        if str(material) not in material_names or str(orientation) not in orientation_names:
            raise ProposalError(f"solid section references missing material/orientation: {block.header}")
        sections_by_elset[str(elset)] = {"material": str(material), "orientation": str(orientation)}
    if set(sections_by_elset) != elset_names:
        raise ProposalError("solid section ELSETs do not exactly cover physical C3D20 sets")
    used_materials = {row["material"] for row in sections_by_elset.values()}
    used_orientations = {row["orientation"] for row in sections_by_elset.values()}
    if not used_materials <= material_names or used_orientations != orientation_names:
        raise ProposalError("a solid section references a missing property or an orientation is unreferenced")

    source_property_cards = normalized_property_cards(source_blocks, omit_density=True)
    c11_property_cards = normalized_property_cards(c11_blocks, omit_density=True)
    if source_property_cards != c11_property_cards:
        raise ProposalError("adapter material/orientation/section cards no longer match pinned C11 source")
    if model["material_deck_audit"].get("material_orientation_solid_section_cards_exactly_match_pinned_c11_input") is not True:
        raise ProposalError("upstream adapter material-card audit is not a pass")

    physical_node_sequence = [
        int(line.split(",", 1)[0])
        for line in node_blocks[0].lines
        if int(line.split(",", 1)[0]) in physical_nodes
    ]
    if physical_node_sequence != sorted(physical_nodes):
        raise ProposalError("source physical node records are not in the pinned ascending ID order")
    retained_nodes = [source_nodes[node][0] for node in physical_node_sequence]
    output_lines = [
        "*HEADING",
        "Source-bound pure physical-solid matrix export proposal; input-only and not frozen",
        "*NODE,NSET=PURE_PHYSICAL_SOLIDS",
        *retained_nodes,
    ]
    for block in c3d20_blocks:
        output_lines.extend(render_block(block))
    property_blocks = [block for block in source_blocks if block.keyword in PHYSICAL_KEYWORDS]
    current_material: str | None = None
    density_materials: list[str] = []
    for block in property_blocks:
        output_lines.extend(render_block(block))
        if block.keyword == "*MATERIAL":
            current_material = material_name(block)
        elif block.keyword == "*ELASTIC":
            if current_material is None:
                raise ProposalError("elastic card is not associated with a material")
            if current_material in density_materials:
                raise ProposalError(f"material has multiple elastic cards: {current_material}")
            output_lines.extend(["*DENSITY", AUXILIARY_DENSITY_TOKEN])
            density_materials.append(current_material)
    if set(density_materials) != material_names or len(density_materials) != 50:
        raise ProposalError("auxiliary positive density was not added exactly once per source material")
    output_lines.extend(
        [
            "*STEP",
            "*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES",
            "*END STEP",
        ]
    )
    deck_bytes = ("\n".join(output_lines) + "\n").encode("utf-8")
    deck_text = deck_bytes.decode("utf-8")
    output_blocks = parse_blocks(deck_text)
    keywords = [block.keyword for block in output_blocks]
    if set(keywords) != EXPECTED_OUTPUT_KEYWORDS:
        raise ProposalError(f"unexpected output keyword inventory: {sorted(set(keywords))}")
    if keywords[-3:] != ["*STEP", "*FREQUENCY", "*END STEP"]:
        raise ProposalError("MATRIXSTORAGE frequency step is not the terminal deck procedure")
    frequency = output_blocks[-2]
    if (
        frequency.options.get("SOLVER") != "MATRIXSTORAGE"
        or str(frequency.options.get("GLOBAL", "")).upper() != "YES"
    ):
        raise ProposalError("terminal frequency card is missing MATRIXSTORAGE/GLOBAL=YES options")
    if any(block.lines for block in output_blocks[-3:]):
        raise ProposalError("terminal MATRIXSTORAGE step must not carry another step or eigenvalue-count row")
    output_nodes = parse_node_block(next(block for block in output_blocks if block.keyword == "*NODE"))
    if set(output_nodes) != physical_nodes or len(output_nodes) != 12549:
        raise ProposalError("emitted node inventory is not the exact physical-node inventory")
    output_elements = {}
    output_element_sets = []
    for block in output_blocks:
        if block.keyword == "*ELEMENT":
            if block.options.get("TYPE", "").upper() != "C3D20":
                raise ProposalError(f"non-solid element survived output filter: {block.header}")
            output_element_sets.append(str(block.options.get("ELSET")))
            for element, connectivity in parse_element_block(block):
                output_elements[element] = connectivity
    if output_elements != source_element_records or len(output_elements) != 1903:
        raise ProposalError("emitted physical C3D20 IDs/connectivity differ from source adapter")
    output_property_cards = normalized_property_cards(output_blocks, omit_density=True)
    if output_property_cards != source_property_cards:
        raise ProposalError("emitted elastic/material/orientation/section cards differ from adapter source")
    output_density = [block for block in output_blocks if block.keyword == "*DENSITY"]
    if len(output_density) != 50 or any(block.lines != [AUXILIARY_DENSITY_TOKEN] for block in output_density):
        raise ProposalError("emitted auxiliary density inventory is not exact")
    all_output_elsets = set(output_element_sets)
    if all_output_elsets != elset_names or len(output_element_sets) != 68:
        raise ProposalError("emitted solid element sets differ from source inventory")

    source_node_lines_hash = sha256_bytes("\n".join(retained_nodes).encode("utf-8"))
    connectivity_hash = canonical_hash(
        [[int(element), source_element_records[element]] for element in sorted(source_element_records)]
    )
    coord_max_abs_diff = [0.0, 0.0, 0.0]
    for node in physical_nodes:
        expected_xyz = model_nodes[node]
        emitted_xyz = [float(value) for value in source_nodes[node][1]]
        for axis in range(3):
            coord_max_abs_diff[axis] = max(
                coord_max_abs_diff[axis], abs(float(expected_xyz[axis]) - emitted_xyz[axis])
            )

    body_inventory = []
    for body in sorted(body_nodes):
        owned_sets = sorted(row["elset"] for row in element_set_rows if row["physical_body"] == body)
        body_inventory.append(
            {
                "body": body,
                "physical_node_count": len(body_nodes[body]),
                "physical_C3D20_count": len(body_elements[body]),
                "source_C3D20_elsets": owned_sets,
            }
        )
    rank_audit = read_json(RANK_PACKET / "audit.json")
    if rank_audit.get("status") != "PASS_SOURCE_BOUND_RIGID_BODY_BRANCH_SCREEN_INITIAL_GRAVITY_GAUGE_OPEN":
        raise ProposalError("rank audit does not report its bounded source-only pass")
    if rank_audit.get("geometry_revision_id") != model["geometry_revision_id"]:
        raise ProposalError("rank audit geometry revision differs from pure-solid input")
    if rank_audit.get("native_solve_executed") is not False or rank_audit.get("geometry_changed") is not False:
        raise ProposalError("rank audit includes a native run or geometry edit")

    decomposition = read_json(GRAVITY_PACKET / "decomposition.json")
    load_maps, load_summary = build_load_map_packet(decomposition)
    current_map_summary = next(row for row in load_summary["case_summaries"] if row["case_id"] == "a12-rear")
    if current_map_summary["input_model_sha256"] != sha256_file(model_path):
        raise ProposalError("a12-rear explicit load map does not bind this current input model")
    load_maps_bytes = write_json_bytes(load_maps)

    output_keyword_counts: dict[str, int] = {}
    for block in output_blocks:
        output_keyword_counts[block.keyword] = output_keyword_counts.get(block.keyword, 0) + 1
    operator_pins = read_json(OPERATOR_PACKET / "source-pins.json")
    operator_runtime = operator_pins["pinned_runtime_profile"]
    source_archive_members = {
        row["path"].removeprefix("./CalculiX/ccx_2.23/src/"): row["sha256"]
        for row in pins["source_archive"]["members"]
    }
    report = {
        "schema": "current_frame_pure_solid_matrix_export_preflight/v1",
        "status": "PASS_SOURCE_BOUND_PURE_PHYSICAL_SOLID_EXPORT_PROPOSAL_NOT_FROZEN_NOT_RUN",
        "scope": (
            "One a12-rear unconstrained physical C3D20 operator input proposal. This produces no matrix and "
            "does not implement the full-frame connector/controller assembly."
        ),
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "case_id": model["case_id"],
        "input_only": True,
        "geometry_changed": False,
        "native_solve_executed": False,
        "matrix_export_executed": False,
        "producer_sha256": sha256_file(PACKET / "prepare_export.py"),
        "source_pins_sha256": sha256_file(PINS_PATH),
        "source_inputs": {
            "adapter_model_sha256": sha256_file(model_path),
            "adapter_deck_sha256": sha256_file(input_deck_path),
            "adapter_audit_sha256": sha256_file(ADAPTER / "a12-rear" / "audit.json"),
            "adapter_producer_sha256": sha256_file(ADAPTER / "prepare.py"),
            "rank_audit_sha256": sha256_file(RANK_PACKET / "audit.json"),
            "rank_audit_producer_sha256": sha256_file(RANK_PACKET / "audit.py"),
            "rank_audit_status": rank_audit["status"],
            "gravity_decomposition_sha256": load_summary["upstream_decomposition_sha256"],
            "gravity_decomposition_verifier_sha256": sha256_file(GRAVITY_PACKET / "verify_decomposition.py"),
            "gravity_decomposition_replay_status": load_summary["upstream_decomposition_status"],
            "source_load_map_file_sha256": sha256_bytes(load_maps_bytes),
            "source_load_map_summaries": load_summary["case_summaries"],
            "source_load_map_max_cross_case_gravity_difference_N": load_summary[
                "six_case_gravity_map_max_component_difference_N"
            ],
        },
        "source_inventory": {
            "adapter_total_node_count": len(source_nodes),
            "nonphysical_or_auxiliary_node_count_removed": len(source_nodes) - len(physical_nodes),
            "physical_node_count": len(physical_nodes),
            "physical_body_count": len(body_nodes),
            "physical_node_body_membership_count": sum(len(nodes) for nodes in body_nodes.values()),
            "physical_node_overlap_membership_count": sum(len(nodes) for nodes in body_nodes.values()) - len(physical_nodes),
            "unowned_C3D20_connectivity_node_count": len(connected_nodes - physical_nodes),
            "physical_node_not_connected_to_C3D20_count": len(physical_nodes - connected_nodes),
            "C3D20_connected_nonphysical_node_count": len(connected_nodes - physical_nodes),
            "physical_C3D20_count": len(source_element_records),
            "physical_body_element_membership_count": sum(len(elements) for elements in body_elements.values()),
            "physical_element_overlap_membership_count": sum(len(elements) for elements in body_elements.values()) - len(physical_elements),
            "physical_element_unowned_count": len(set(source_element_records) - set(element_owners)),
            "C3D20_element_set_count": len(element_set_rows),
            "solid_section_count": len(section_blocks),
            "material_count": len(material_blocks),
            "elastic_card_count": len(elastic_blocks),
            "orientation_count": len(orientation_blocks),
            "output_physical_translation_dof_count_expected_not_observed": 3 * len(physical_nodes),
            "physical_node_source_record_sha256": source_node_lines_hash,
            "physical_C3D20_connectivity_sha256": connectivity_hash,
            "C3D20_set_to_physical_body": sorted(element_set_rows, key=lambda row: row["elset"]),
            "all_50_physical_bodies": body_inventory,
            "source_coordinate_serialization": "Preserved byte-for-byte from the a12-rear adapter node records; each coordinate token matches the pinned model.json coordinate through the adapter's Python .14g formatter.",
            "max_adapter_model_to_source_deck_coord_difference_mm_by_axis": coord_max_abs_diff,
            "all_source_C3D20_connectivity_exactly_matches_model_json": True,
            "all_physical_nodes_are_unique_and_owned_by_exactly_one_body": True,
            "all_physical_nodes_are_covered_by_C3D20_connectivity": True,
            "all_C3D20_elements_are_owned_by_exactly_one_of_50_bodies": True,
        },
        "source_constraint_and_load_removal": {
            "source_equation_count_removed": len(model["equations"]),
            "conditional_exact_floor_stick_equation_count_removed": len(model["exact_floor_mpc_equations"]),
            "permanent_interpolation_equation_count_removed": len(model["equations"]) - len(model["exact_floor_mpc_equations"]),
            "source_distinct_SPC_node_count_removed": len(source_fixed_nodes),
            "physical_nodes_with_source_SPC_count": len(source_fixed_nodes & physical_nodes),
            "source_SPRING2_count_removed": model["adapted_element_kind_counts"]["SPRING2"],
            "source_SPRINGA_count_removed": model["adapted_element_kind_counts"]["SPRINGA"],
            "all_source_boundary_SPCs_removed": True,
            "all_source_CLOADs_and_other_load_cards_removed": True,
            "all_numerical_ground_and_projection_nodes_removed": True,
            "all_permanent_MPCs_removed": True,
            "output_has_no_boundary_equation_spring_or_load_keywords": True,
            "all_physical_source_loads_are_stored_in_separate_source_load_maps_json": True,
        },
        "material_density_difference": {
            "source_density_cards_present": False,
            "auxiliary_density_added_to_every_material": AUXILIARY_DENSITY_TONNE_PER_MM3,
            "unit": "tonne/mm^3",
            "density_card_count": len(output_density),
            "classification": "NONPHYSICAL EXPORT-ONLY POSITIVE HELPER; NOT A SOURCE OR WOOD PROPERTY",
            "only_permitted_use": "populate the matrixstorage .mas output alongside .sti",
            "mass_matrix_must_be_discarded": True,
            "must_not_use_M_times_g_for_physical_gravity": True,
            "physical_gravity_and_climber_loads": "separate source-bound explicit nodal maps; not in the matrix export deck",
            "density_does_not_change_unloaded_linear_elastic_stiffness_source_basis": {
                "source_archive_sha256": pins["source_archive"]["sha256"],
                "e_c3d_f_sha256": source_archive_members["e_c3d.f"],
                "materialdata_me_f_sha256": source_archive_members["materialdata_me.f"],
                "materialdata_rho_f_sha256": source_archive_members["materialdata_rho.f"],
                "observation": (
                    "Pinned 2.23 e_c3d.f builds the C3D20 elastic stiffness from material stiffness/orientation "
                    "arrays; rho is used by body-force and mass-matrix terms. materialdata_me.f reads rho and "
                    "elastic constants via separate paths. The proposal has no gravity/body-force cards, "
                    "rotation, prestress, static load step, SPC, MPC, or connector; therefore no rho-derived "
                    "load or geometric-stiffness contribution is requested."
                ),
                "applicability_limit": "Source-based linear unloaded C3D20 K rationale only; the generated full-frame matrix has not been observed.",
            },
        },
        "material_orientation_section_audit": {
            "source_and_pinned_C11_property_cards_exactly_equal_excluding_auxiliary_density": True,
            "source_property_card_count": len(source_property_cards),
            "source_adapter_property_card_sha256": card_hash(source_property_cards),
            "pinned_C11_property_card_sha256": card_hash(c11_property_cards),
            "emitted_property_card_sha256_excluding_auxiliary_density": card_hash(output_property_cards),
            "source_density_card_count": len(density_blocks),
            "pinned_C11_density_card_count": len(c11_density_blocks),
            "source_material_cards_have_density": False,
            "all_68_solid_sections_map_to_C3D20_ELSETs_and_defined_material_and_orientation": True,
            "all_section_materials_and_50_orientations_resolve": True,
            "source_material_cards_unreferenced_by_solid_sections_preserved": sorted(material_names - used_materials),
        },
        "proposed_terminal_operator_export": {
            "deck_path": "pure-physical-solid-matrixstorage.inp",
            "deck_sha256": sha256_bytes(deck_bytes),
            "matrixstorage_step": "*STEP / *FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES / *END STEP",
            "terminal_procedure": True,
            "global_coordinate_directions": True,
            "unconstrained_physical_equations_expected_not_observed": 3 * len(physical_nodes),
            "expected_dof_map_scope": "node.direction rows for the 12,549 physical solid nodes only",
            "expected_outputs_if_later_run": ["job.sti", "job.mas", "job.dof"],
            "matrixstorage_manual_sha256": pins["manual_basis"]["sha256"],
            "pinned_solver_version": operator_runtime["version"],
            "pinned_solver_binary_sha256": operator_runtime["binary_sha256"],
            "runtime_matrixstorage_feature_observed": operator_runtime["runtime_matrixstorage_feature_observed"],
            "deck_parser_or_output_behavior_for_this_full_model_observed": False,
        },
        "later_operator_rejoin_contract": [
            "Index the exported pure physical C3D20 K by the emitted .dof node.direction map; do not assume file row order equals node order.",
            "Build and independently validate the permanent interpolation/connector displacement expansion P from exact current source equations, numerical grounds, and SPC handling; the pure export deliberately includes none of these.",
            "Apply that same P to physical degrees and connector projection/ground endpoints. Form K_reduced = P^T K_physical P and F_reduced = P^T F_physical for explicitly selected load maps.",
            "Reintroduce all 348 bilateral SPRING2 and 1,292 unilateral SPRINGA laws outside this export. Determine state-dependent unilateral contributions from a separately validated coupled-state method.",
            "Keep the 200 conditional floor-stick rows outside the all-open pure operator and activate/release them only through the source-bound episode-reference logic; do not treat them as permanent constraints.",
            "Use explicit source gravity/climber nodal maps stored beside this packet. Never derive physical gravity from the auxiliary-density .mas file.",
        ],
        "limits": [
            "No native matrix export has been run; no .sti/.mas/.dof output is present or assessed.",
            "The source-pinned 2.23 runtime profile records runtime_matrixstorage_feature_observed=false; actual binary support/launch remains a parent-owned gate.",
            "This is a pure elastic solid K input proposal, not a constrained frame operator, active-set controller, gravity solution, state selection, rank result, or joint acceptance.",
            "The six explicit load maps are source records. Only a12-rear shares the geometry/model pinned by this deck; other case maps are retained separately, not applied here.",
            "Auxiliary density changes the mass matrix and must not be interpreted as material density or used for physical loading.",
        ],
        "output_keyword_counts": output_keyword_counts,
        "output_density_materials": sorted(density_materials),
    }
    return {
        "pure-physical-solid-matrixstorage.inp": deck_bytes,
        "source-load-maps.json": load_maps_bytes,
        "audit.json": write_json_bytes(report),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the source-bound input proposal outputs")
    mode.add_argument("--verify", action="store_true", help="rebuild in memory and compare exact output bytes")
    args = parser.parse_args()
    outputs = build_proposal()
    if args.write:
        PACKET.mkdir(parents=True, exist_ok=True)
        for name, contents in outputs.items():
            (PACKET / name).write_bytes(contents)
        print(
            "WROTE source-bound input-only proposal: "
            f"{len(outputs['pure-physical-solid-matrixstorage.inp'])} deck bytes, "
            f"{len(outputs['source-load-maps.json'])} explicit-load-map bytes"
        )
    else:
        mismatches = []
        for name, expected in outputs.items():
            path = PACKET / name
            if not path.is_file() or path.read_bytes() != expected:
                mismatches.append(name)
        if mismatches:
            raise SystemExit("Generated output differs or is missing: " + ", ".join(mismatches))
        print("PASS: source pins, physical-node/C3D20/material equality, explicit map decomposition, and output bytes")


if __name__ == "__main__":
    main()
