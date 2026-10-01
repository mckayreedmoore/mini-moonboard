#!/usr/bin/env python3
"""Read-only, standard-library replay for the ordinary-joint crosswalk."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path


BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
ATTEMPT01 = BASE / "ordinary-joint-active-map-crosswalk-attempt01-2026-09-28"
ATTEMPT02 = BASE / "ordinary-joint-active-map-crosswalk-attempt02-2026-09-28"
A09 = BASE / "ordinary-port-motion-attempt09-common-map"
MAP_SCOPE = BASE / "current-map-remaining-scope-attempt01"
FIXTURE = BASE / "implicit-current-map-known-answer-attempt01"


class ReplayFailure(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReplayFailure(message)


def find_repo_root() -> Path:
    candidates = [Path(__file__).resolve(), Path.cwd().resolve()]
    seen: set[Path] = set()
    for candidate in candidates:
        for parent in (candidate, *candidate.parents):
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / ".git").exists():
                return parent
    raise ReplayFailure("repository root with .git was not found")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplayFailure(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ReplayFailure(f"cannot read {path}: {exc}") from exc


def parse_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, f"invalid sha256 manifest line {path}:{line_number}")
        digest, name = match.groups()
        require(name not in entries, f"duplicate manifest path in {path}: {name}")
        entries[name] = digest
    return entries


def checked_manifest(entries: dict[str, str], base: Path, label: str) -> int:
    for name, expected in entries.items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts,
                f"unsafe path in {label}: {name}")
        path = base / relative
        require(sha256_file(path) == expected, f"hash mismatch in {label}: {name}")
    return len(entries)


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in zip(*a)]


def matvec(a: list[list[float]], x: list[float]) -> list[float]:
    return [sum(a[i][j] * x[j] for j in range(len(x))) for i in range(len(a))]


def determinant(a: list[list[float]]) -> float:
    require(len(a) == len(a[0]), "determinant requires a square matrix")
    work = [row[:] for row in a]
    sign = 1.0
    result = 1.0
    for col in range(len(work)):
        pivot = max(range(col, len(work)), key=lambda row: abs(work[row][col]))
        if abs(work[pivot][col]) < 1e-30:
            return 0.0
        if pivot != col:
            work[pivot], work[col] = work[col], work[pivot]
            sign *= -1.0
        value = work[col][col]
        result *= value
        for row in range(col + 1, len(work)):
            factor = work[row][col] / value
            for j in range(col + 1, len(work)):
                work[row][j] -= factor * work[col][j]
    return sign * result


def require_close(actual: float, expected: float, label: str, tolerance: float = 2e-11) -> None:
    require(math.isfinite(actual) and math.isfinite(expected), f"nonfinite value: {label}")
    require(abs(actual - expected) <= tolerance,
            f"numeric mismatch {label}: {actual!r} != {expected!r}")


def require_vector_close(actual: list[float], expected: list[float], label: str,
                         tolerance: float = 2e-11) -> None:
    require(len(actual) == len(expected), f"vector length mismatch: {label}")
    for index, (left, right) in enumerate(zip(actual, expected)):
        require_close(float(left), float(right), f"{label}[{index}]", tolerance)


def parsed_params(keyword: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in keyword.split(",")[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip().upper()] = value.strip()
    return result


def parse_equation_cards(text: str) -> list[tuple[int, int, int]]:
    lines = text.splitlines()
    cards: list[tuple[int, int, int]] = []
    index = 0
    while index < len(lines):
        if lines[index].strip().upper().startswith("*EQUATION"):
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            require(index < len(lines), "truncated *EQUATION card")
            try:
                term_count = int(lines[index].strip().split(",", 1)[0])
            except ValueError as exc:
                raise ReplayFailure("invalid *EQUATION term count") from exc
            require(term_count > 0, "nonpositive *EQUATION term count")
            index += 1
            tokens: list[str] = []
            while len(tokens) < term_count * 3:
                require(index < len(lines), "truncated *EQUATION data")
                row = lines[index].strip()
                require(not row.startswith("*"), "truncated *EQUATION before next keyword")
                tokens.extend(token.strip() for token in row.split(",") if token.strip())
                index += 1
            require(len(tokens) == term_count * 3, "unexpected *EQUATION data length")
            try:
                dependent_node = int(tokens[0])
                dependent_dof = int(tokens[1])
            except ValueError as exc:
                raise ReplayFailure("invalid dependent variable in *EQUATION") from exc
            cards.append((dependent_node, dependent_dof, term_count))
        else:
            index += 1
    return cards


def parse_rigid_body_cards(text: str) -> dict[str, tuple[int, int]]:
    cards: dict[str, tuple[int, int]] = {}
    for line in text.splitlines():
        if line.strip().upper().startswith("*RIGID BODY"):
            params = parsed_params(line.strip())
            require({"NSET", "REF NODE", "ROT NODE"} <= set(params),
                    f"incomplete *RIGID BODY card: {line.strip()}")
            nset = params["NSET"].upper()
            require(nset not in cards, f"duplicate *RIGID BODY NSET: {nset}")
            cards[nset] = (int(params["REF NODE"]), int(params["ROT NODE"]))
    return cards


def parse_node_coordinates(text: str) -> dict[int, list[float]]:
    lines = text.splitlines()
    coordinates: dict[int, list[float]] = {}
    in_nodes = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("*"):
            in_nodes = stripped.upper().startswith("*NODE")
            continue
        if not in_nodes or not stripped or stripped.startswith("**"):
            continue
        fields = [field.strip() for field in stripped.split(",")]
        if len(fields) >= 4:
            try:
                node = int(fields[0])
                coordinates[node] = [float(fields[1]), float(fields[2]), float(fields[3])]
            except ValueError:
                continue
    return coordinates


def run(root: Path) -> list[str]:
    p1 = root / ATTEMPT01
    p2 = root / ATTEMPT02
    a09 = root / A09
    crosswalk = load_json(p1 / "crosswalk.json")
    lines: list[str] = ["ordinary-joint active-map crosswalk attempt02 replay"]

    # Recheck attempt01 without modifying or regenerating any of its artifacts.
    p1_manifest = parse_manifest(p1 / "SHA256SUMS")
    require(set(p1_manifest) == {"README.md", "crosswalk.json", "SOURCE-SHA256SUMS"},
            "attempt01 SHA256SUMS inventory changed")
    p1_count = checked_manifest(p1_manifest, p1, "attempt01 SHA256SUMS")
    p1_sources = parse_manifest(p1 / "SOURCE-SHA256SUMS")
    require(len(p1_sources) == 35, "attempt01 source manifest must have 35 entries")
    require(p1_sources == crosswalk.get("source_sha256"),
            "attempt01 source_sha256 object differs from SOURCE-SHA256SUMS")
    p1_source_count = checked_manifest(p1_sources, root, "attempt01 SOURCE-SHA256SUMS")

    p2_sources = parse_manifest(p2 / "SOURCE-SHA256SUMS")
    required_p1_paths = {
        (ATTEMPT01 / name).as_posix()
        for name in ("README.md", "SHA256SUMS", "SOURCE-SHA256SUMS", "crosswalk.json")
    }
    require(set(p2_sources) == required_p1_paths,
            "attempt02 SOURCE-SHA256SUMS must pin the four attempt01 packet artifacts")
    p2_source_count = checked_manifest(p2_sources, root, "attempt02 SOURCE-SHA256SUMS")
    lines.append(
        f"PASS attempt01 packet hashes {p1_count}/3; source pins {p1_source_count}/35; "
        f"source_sha256 parity; attempt01 artifact pins {p2_source_count}/4"
    )

    # Freeze binding: exact case deck -> case lock -> external bundle lock -> base freeze.
    binding = crosswalk["freeze_binding"]
    case_lock_path = root / binding["case_lock_path"]
    case_lock = load_json(case_lock_path)
    bundle_path = root / binding["external_port_bundle_lock_path"]
    bundle = load_json(bundle_path)
    freeze_path = root / binding["base_input_freeze_path"]
    freeze = load_json(freeze_path)
    deck_path = a09 / "port_motion_n_plus.inp"
    deck_hash = sha256_file(deck_path)
    require(case_lock["case"] == "n_plus", "case lock identity is not n_plus")
    require(case_lock["status"] == "FROZEN_CONTROLLED_PORT_MOTION_INPUTS",
            "case lock is not frozen")
    require(sha256_file(case_lock_path) == binding["case_lock_sha256"],
            "case lock hash differs from the crosswalk")
    require(deck_hash == case_lock["input_sha256"]["port_motion_n_plus.inp"],
            "case deck hash differs from case lock")
    require(deck_hash == crosswalk["scope"]["case_sha256"] ==
            binding["case_deck_sha256_from_lock"] == binding["case_deck_sha256_recomputed"],
            "case deck hash chain mismatch")
    bundle_hash = sha256_file(bundle_path)
    freeze_hash = sha256_file(freeze_path)
    require(bundle_hash == case_lock["external_port_bundle_lock_sha256"] ==
            binding["external_port_bundle_lock_sha256"], "case lock to bundle lock hash mismatch")
    require(case_lock["input_sha256"]["bundle-lock.json"] == bundle_hash,
            "case lock input inventory does not bind the bundle lock")
    require(freeze_hash == bundle["input_freeze_sha256"] ==
            binding["base_input_freeze_sha256"], "bundle lock to base freeze hash mismatch")
    require(case_lock["input_sha256"]["input-freeze.json"] == freeze_hash,
            "case lock input inventory does not bind the base freeze")
    require(case_lock_path == a09 / "port-motion-n_plus-lock.json" and
            bundle_path == a09 / "bundle-lock.json" and freeze_path == a09 / "input-freeze.json",
            "freeze chain resolved to unexpected paths")
    frozen_artifacts = freeze["artifacts_sha256"]
    require(len(frozen_artifacts) == 14, "base freeze must contain 14 artifacts")
    for name, expected in frozen_artifacts.items():
        require(sha256_file(a09 / name) == expected, f"base freeze artifact hash mismatch: {name}")
    require(binding["base_frozen_artifacts_rechecked"] == 14 and
            binding["base_frozen_artifacts_all_match"] is True,
            "crosswalk base-freeze summary disagrees with replay")
    lines.append("PASS base freeze 14/14; case-deck -> case-lock -> bundle-lock -> base-freeze digest chain")

    # The seven direct includes must equal the inventory and be hash-covered.
    deck_text = deck_path.read_text(encoding="utf-8")
    direct_includes = re.findall(
        r"^\s*\*INCLUDE\s*,\s*INPUT\s*=\s*([^,\s]+)", deck_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    include_inventory = crosswalk["deck_binding"]["included_files"]
    require(direct_includes == include_inventory and len(direct_includes) == 7,
            "direct deck includes differ from the seven-entry inventory")
    source_pin_by_path = p1_sources
    freeze_pin_by_name = frozen_artifacts
    for name in direct_includes:
        repo_path = (A09 / name).as_posix()
        actual = sha256_file(a09 / name)
        covered = False
        if repo_path in source_pin_by_path:
            require(actual == source_pin_by_path[repo_path], f"include source pin mismatch: {name}")
            covered = True
        if name in freeze_pin_by_name:
            require(actual == freeze_pin_by_name[name], f"include base-freeze pin mismatch: {name}")
            covered = True
        require(covered, f"direct include is not covered by source/freeze pins: {name}")
    lines.append("PASS direct deck includes 7/7; all seven are covered by source or base-freeze pins")

    # Join the ordered four fitted maps across the frozen input, inventory and crosswalk.
    nut_json = load_json(a09 / "nut-coupling.json")
    current_map = load_json(root / MAP_SCOPE / "source-bound-review.json")
    per_nut = nut_json["per_nut"]
    inventory_axes = current_map["current_A09_map_inventory"]["axes"]
    active_maps = crosswalk["deck_binding"]["active_maps"]
    require(len(per_nut) == len(inventory_axes) == len(active_maps) == 4,
            "expected four ordered nut maps, inventory axes and crosswalk rows")
    require([row["axis_index"] for row in per_nut] == list(range(4)) and
            [row["axis_index"] for row in inventory_axes] == list(range(4)) and
            [row["axis_index"] for row in active_maps] == list(range(4)),
            "A00-A03 rows are not in axis_index order")
    require([row["map_id"] for row in active_maps] == ["A00", "A01", "A02", "A03"],
            "crosswalk map order is not A00-A03")

    equation_cards = nut_json["equation_cards"]
    actual_equations = parse_equation_cards((a09 / "nut-coupling.inp").read_text(encoding="utf-8"))
    require(len(equation_cards) == len(actual_equations) == 24,
            "expected 24 serialized and recorded nut equation rows")
    expected_equations: list[tuple[int, int, int]] = []
    for index, (nut, inventory, active) in enumerate(zip(per_nut, inventory_axes, active_maps)):
        axis_id = inventory["axis_id"]
        carrier_id = inventory["nut_carrier_id"]
        require(nut["axis_index"] == active["axis_index"] == index,
                f"axis index mismatch for A0{index}")
        require(nut["physical_bolt_id"] == axis_id == active["axis_id"],
                f"axis ID mismatch for A0{index}")
        require(nut["shaft_mesh_body_id"] == active["shaft_body_id"] ==
                inventory["shaft_body_id"], f"shaft body mismatch for A0{index}")
        require(active["nut_carrier_id"] == carrier_id,
                f"nut carrier mismatch for A0{index}")

        controls = nut["control_node_ids"]
        inventory_controls = inventory["control_nodes"]
        map_controls = active["nut_reference_rotation_control_nodes"]
        expected_controls = [controls["translation_reference_node_id"],
                             controls["rotation_control_node_id"]]
        require(expected_controls == map_controls ==
                [inventory_controls["translation_reference_node_id"],
                 inventory_controls["rotation_control_node_id"]],
                f"reference/rotation control node mismatch for A0{index}")

        pivot = nut["nut_seat_reference"]["global_xyz_mm"]
        require_vector_close(pivot, inventory["global_pivot_xyz_mm"],
                             f"inventory pivot A0{index}")
        require_vector_close(pivot, active["global_pivot_xyz_mm"],
                             f"crosswalk pivot A0{index}")

        fit = nut["least_squares_rigid_motion_fit"]
        support_ids = fit["node_ids"]
        support_count = inventory["map_support"]["selected_shaft_nodes"]
        require(len(support_ids) == len(set(support_ids)) == support_count ==
                active["map_support"]["selected_shaft_nodes"],
                f"fit support count/uniqueness mismatch for A0{index}")
        support_digest = sha256_bytes(
            ("\n".join(str(node) for node in sorted(support_ids)) + "\n").encode("ascii")
        )
        require(support_digest == inventory["fit_support_node_id_sha256_sorted"],
                f"fit support ID digest mismatch for A0{index}")
        require(fit["coefficient_matrix_rank"] == inventory["map_support"]["fit_rank"] ==
                active["map_support"]["fit_rank"] == 6,
                f"fit rank mismatch for A0{index}")

        source_rows = inventory["six_dependent_equation_rows"]
        crosswalk_rows = active["six_dependent_equation_rows"]
        recorded_rows = [row for row in equation_cards if row["physical_bolt_id"] == axis_id]
        require(len(source_rows) == len(crosswalk_rows) == len(recorded_rows) == 6,
                f"expected six equation rows for A0{index}")
        row_tuples = [(row["dependent_node_id"], row["dependent_dof"],
                       row["term_count_including_dependent"]) for row in source_rows]
        crosswalk_tuples = [(row["dependent_node_id"], row["dependent_dof"],
                             row["term_count_including_dependent"]) for row in crosswalk_rows]
        recorded_tuples = [(row["dependent_node_id"], row["dependent_dof"], row["term_count"])
                           for row in recorded_rows]
        require(row_tuples == crosswalk_tuples == recorded_tuples,
                f"equation row mismatch across inventory/nut JSON/crosswalk for A0{index}")
        require(all(row["term_count_including_dependent"] ==
                    inventory["map_support"]["term_count_per_equation_including_dependent"]
                    for row in source_rows), f"fit equation term count mismatch for A0{index}")
        expected_equations.extend(row_tuples)

    parsed_expected_equations = [(node, dof, terms) for node, dof, terms in expected_equations]
    require(actual_equations == parsed_expected_equations,
            "nut-coupling.inp dependent equation cards differ from ordered recorded rows")

    rigid_cards = parse_rigid_body_cards((a09 / "rigid-carriers.inp").read_text(encoding="utf-8"))
    require(len(rigid_cards) == 4, "expected four *RIGID BODY cards")
    for inventory, active in zip(inventory_axes, active_maps):
        carrier = inventory["carrier_mesh"]
        controls = carrier["rigid_body_controls"]
        nset = carrier["nset_name"].upper()
        expected_card = (controls["reference_node"], controls["rotation_node"])
        require(rigid_cards.get(nset) == expected_card,
                f"*RIGID BODY card mismatch for {active['map_id']}")
        require(expected_card == tuple(active["nut_reference_rotation_control_nodes"]),
                f"crosswalk carrier control mismatch for {active['map_id']}")
    section_elsets = {
        parsed_params(line.strip()).get("ELSET", "").upper()
        for line in (a09 / "materials.inp").read_text(encoding="utf-8").splitlines()
        if line.strip().upper().startswith("*SOLID SECTION")
    }
    require(all(row["shaft_body_id"].upper() in section_elsets for row in active_maps),
            "a fitted shaft body lacks an included solid section")
    nut_control_nodes = parse_node_coordinates((a09 / "nut-coupling.inp").read_text(encoding="utf-8"))
    for active in active_maps:
        for node in active["nut_reference_rotation_control_nodes"]:
            require(node in nut_control_nodes, f"missing nut control node {node}")
            require_vector_close(nut_control_nodes[node], active["global_pivot_xyz_mm"],
                                 f"nut control node pivot {node}")
    lines.append("PASS A00-A03 ordered joins: IDs, bodies, carriers, pivots, controls, support hashes, "
                 "equation rows and four *RIGID BODY cards")

    # Recompute 3D/6D basis identities and the N+ port, boundary and axis transforms.
    transform = crosswalk["coordinate_transform"]
    basis = transform["B_global_from_local_rows"]
    inverse = transform["B_transpose_local_from_global_rows"]
    require_vector_close([value for row in transpose(basis) for value in row],
                         [value for row in transform["basis_columns_global_xyz"] for value in row],
                         "basis columns")
    for product in (matmul(basis, inverse), matmul(inverse, basis)):
        for i in range(3):
            for j in range(3):
                require_close(product[i][j], 1.0 if i == j else 0.0,
                             f"3D basis inverse ({i},{j})")
    det3 = determinant(basis)
    require_close(det3, 1.0, "3D basis determinant")
    expected_inverse = transpose(basis)
    for i in range(3):
        require_vector_close(inverse[i], expected_inverse[i], f"basis inverse row {i}")

    basis6 = [[0.0] * 6 for _ in range(6)]
    inverse6 = [[0.0] * 6 for _ in range(6)]
    for i in range(3):
        for j in range(3):
            basis6[i][j] = basis[i][j]
            basis6[i + 3][j + 3] = basis[i][j]
            inverse6[i][j] = inverse[i][j]
            inverse6[i + 3][j + 3] = inverse[i][j]
    require_close(determinant(basis6), 1.0, "6D basis determinant")
    for product in (matmul(basis6, inverse6), matmul(inverse6, basis6)):
        for i in range(6):
            for j in range(6):
                require_close(product[i][j], 1.0 if i == j else 0.0,
                             f"6D basis inverse ({i},{j})")

    motion = load_json(a09 / "port-motion_n_plus.json")
    n_plus = transform["n_plus"]
    local_relative = motion["relative_joint_coordinate_mm"]
    require_vector_close(local_relative, n_plus["local_joint_relative_coordinate_mm_rad"],
                         "N+ local relative coordinate")
    global_relative = matvec(basis6, local_relative)
    require_vector_close(global_relative[:3], n_plus["global_relative_translation_xyz_mm"],
                         "N+ global relative translation")
    boundary_values: dict[int, tuple[int, float]] = {}
    in_boundary = False
    for raw in deck_text.splitlines():
        row = raw.strip()
        if row.startswith("*"):
            in_boundary = row.upper().startswith("*BOUNDARY")
            continue
        if in_boundary and row and not row.startswith("**"):
            fields = [field.strip() for field in row.split(",")]
            require(len(fields) == 4, "unexpected boundary row in N+ deck")
            node, dof_first, dof_last = map(int, fields[:3])
            require(dof_first == dof_last, f"non-scalar boundary interval at node {node}")
            require(node not in boundary_values, f"duplicate boundary node {node}")
            boundary_values[node] = (dof_first, float(fields[3]))
    require(len(boundary_values) == 12, "expected twelve serialized N+ boundary scalars")
    port_global: dict[str, list[float]] = {}
    for port_name, record_key in (("rail", "rail_controls"), ("principal", "principal_controls")):
        port = motion["ports"][port_name]
        control_nodes = port["control_node_ids"]
        local_q = port["controlled_q_port_local_mm"]
        require(len(control_nodes) == len(local_q) == 6, f"invalid {port_name} control vector")
        for node, expected in zip(control_nodes, local_q):
            require(node in boundary_values, f"missing boundary control node {node}")
            dof, actual = boundary_values[node]
            require(dof == 1, f"unexpected boundary DOF at control node {node}")
            require_close(actual, expected, f"boundary value at node {node}", 1e-13)
        global_q = matvec(basis6, local_q)
        port_global[port_name] = global_q
        control_record = n_plus[record_key]
        require(control_nodes == control_record["control_nodes"],
                f"{port_name} control-node inventory mismatch")
        require_vector_close(local_q[:3], control_record["local_X_T_N_mm"],
                             f"{port_name} local port translation")
        require_vector_close(global_q[:3], control_record["global_xyz_mm"],
                             f"{port_name} global port translation")
    local_port_relative = [a - b for a, b in zip(
        motion["ports"]["rail"]["controlled_q_port_local_mm"],
        motion["ports"]["principal"]["controlled_q_port_local_mm"],
    )]
    require_vector_close(local_port_relative, local_relative, "rail-minus-principal local motion")
    global_port_relative = [a - b for a, b in zip(port_global["rail"], port_global["principal"])]
    require_vector_close(global_port_relative, global_relative, "rail-minus-principal global motion")

    for active, inventory in zip(active_maps, inventory_axes):
        global_axis = inventory["shaft_axis_direction_head_to_nut_global_xyz"]
        require_vector_close(global_axis, active["shaft_axis_direction_head_to_nut_global_xyz"],
                             f"global shaft axis {active['map_id']}")
        local_axis = matvec(inverse, global_axis)
        require_vector_close(local_axis, active["shaft_axis_direction_head_to_nut_local_X_T_N"],
                             f"local shaft axis {active['map_id']}")

    # The A00 known-answer fixture is hash-bound and limited to the small alpha_y drive.
    fixture_input = load_json(root / FIXTURE / "input-freeze.json")
    fixture_verifier = load_json(root / FIXTURE / "verifier.json")
    fixture_acceptance = load_json(root / FIXTURE / "acceptance.json")
    fixture = crosswalk["qualified_A00_fixture_comparison"]
    fixture_input_hash = sha256_file(root / FIXTURE / "input-freeze.json")
    fixture_verifier_hash = sha256_file(root / FIXTURE / "verifier.json")
    require(fixture_input_hash == fixture["input_freeze_sha256"],
            "A00 fixture input-freeze hash mismatch")
    require(fixture_verifier_hash == fixture["verifier_report_sha256"],
            "A00 fixture verifier hash mismatch")
    require(fixture_verifier["input_freeze_sha256"] == fixture_input_hash,
            "A00 verifier does not bind its input freeze")
    require(fixture_verifier["status"] == fixture["status"] == "PASS_CURRENT_MAP_KNOWN_ANSWER",
            "A00 fixture status mismatch")
    require(fixture_verifier["scope"] == fixture["scope"] and
            "M00 A00" in fixture_verifier["scope"] and "M03" in fixture_verifier["scope"],
            "A00 fixture scope does not match the crosswalk")
    require(fixture["qualified_map"] == "M00_A00 only" and
            fixture["qualified_carrier"] == "M03_A00 only", "A00 fixture scope broadened")
    require(fixture_verifier["case_order"] == ["direct", "mapped_no_carrier", "mapped_carrier"] and
            fixture_acceptance["case_order"] == fixture_verifier["case_order"],
            "A00 fixture case order mismatch")
    for case_name, case_record in fixture["cases"].items():
        native = fixture_verifier["native_cases"][case_name]
        require(case_record["status"] == native["status"] == "PASS" and
                case_record["accepted_states"] == native["accepted_sta_state_count"] == 10,
                f"A00 fixture case mismatch: {case_name}")
    require(fixture_acceptance["scope"].startswith("One actual A00 coefficient set") and
            fixture_acceptance["joint_acceptance"] is False and
            fixture_acceptance["release"] is False,
            "A00 acceptance scope or fail-closed flags mismatch")
    require(fixture_verifier["mechanical_acceptance"] is False and
            fixture_verifier["joint_acceptance"] is False and
            fixture_verifier["release"] is False,
            "A00 verifier acceptance/release flags are not fail-closed")

    drive = fixture["drive"]
    global_rotation_axis = drive["global_rotation_axis_unit"]
    local_rotation_axis = matvec(inverse, global_rotation_axis)
    require_vector_close(local_rotation_axis, drive["global_axis_as_local_X_T_N"],
                         "A00 global-Y axis transform")
    alpha = re.search(r"alpha_y\(t\)\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*\*\s*t",
                      drive["global_angular_acceleration"])
    require(alpha is not None, "cannot parse A00 angular drive")
    alpha_scale = float(alpha.group(1))
    local_alpha_per_s = [alpha_scale * value for value in local_rotation_axis]
    require_vector_close(local_alpha_per_s,
                         drive["local_angular_acceleration_coefficient_rad_s2_per_s_X_T_N"],
                         "A00 transformed angular drive")

    # Preserve and classify the failed A09 attempt from its recorded execution and bytes.
    execution = load_json(a09 / "execution.json")
    response = crosswalk["response_and_follow_on"]
    require(execution["status"] == "wallclock_timeout" and execution["returncode"] == 137 and
            execution["wallclock_timeout"] is True and execution["frozen_inputs_unchanged"] is True,
            "A09 timeout execution record mismatch")
    require(response["static_attempt_status"] == execution["status"] and
            response["exit_code"] == execution["returncode"] and
            response["declared_timeout"] is True and response["frozen_inputs_unchanged"] is True and
            response["accepted_increment"] is False,
            "A09 no-accepted-increment record mismatch")
    attempt_readme = " ".join((a09 / "README.md").read_text(encoding="utf-8").lower().split())
    require("without accepting the increment" in attempt_readme,
            "A09 README does not record the unaccepted first increment")
    stdout = (a09 / "native.stdout").read_text(encoding="utf-8")
    iteration_numbers = [int(value) for value in re.findall(
        r"^\s*iteration\s+(\d+)\s*$", stdout, flags=re.IGNORECASE | re.MULTILINE
    )]
    require(iteration_numbers == list(range(1, 34)), "A09 native log iteration record changed")
    expected_sizes = {"dat": 0, "sta": 0, "frd": 80}
    recorded_sizes = response["raw_output_bytes"]
    for extension, expected_size in expected_sizes.items():
        path = a09 / f"port_motion_n_plus.{extension}"
        actual_size = path.stat().st_size
        require(actual_size == expected_size == recorded_sizes[extension],
                f"A09 .{extension} output size mismatch")
    for name, expected in execution["output_hashes"].items():
        if name.startswith("port_motion_n_plus."):
            require(sha256_file(a09 / name) == expected, f"A09 output hash mismatch: {name}")
    follow_on = response["follow_on_transient"]
    require(follow_on["selection"] == "UNSELECTED" and follow_on["frozen_input"] is False,
            "A09 follow-on transient is not recorded as unselected/unfrozen")

    # Acceptance and release flags must remain closed.
    gate_status = crosswalk["map_and_gate_status"]
    for flag in ("A01_A03_qualified", "T02_capture_coupon_completed",
                 "T03_attempt07_coupon_run", "ordinary_joint_response_accepted",
                 "mechanical_acceptance", "joint_acceptance", "criteria_resolved", "release"):
        require(gate_status[flag] is False, f"crosswalk gate flag must remain false: {flag}")
    require(crosswalk["scope"]["geometry_changed"] is False and
            crosswalk["scope"]["source_inputs_modified"] is False and
            crosswalk["scope"]["solver_run_by_this_packet"] is False,
            "crosswalk scope flags changed")
    require(case_lock["native_execution"] is False and case_lock["mechanical_acceptance"] is False,
            "case lock acceptance flags are not fail-closed")
    lines.append("PASS basis transforms: 3D and 6D inverse/determinant; N+ ports, 12 boundaries and A00-A03 axes")
    lines.append("PASS A00 fixture hashes/scope; transformed global-Y angular drive")
    lines.append("PASS A09 no accepted increment; .dat=0 .sta=0 .frd=80 bytes; follow-on unselected/unfrozen")
    lines.append("PASS acceptance, criteria and release flags remain false")
    lines.append("LIMIT source binding and arithmetic only; no mechanics or acceptance gate is closed")
    return lines


def main() -> int:
    try:
        output = run(find_repo_root())
    except (ReplayFailure, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
