"""Audit firstpoint whole-patch momentum and native C3D10 kinetic energy.

The immutable native03 .0025 s snapshot is integrated over all positive-density
wood and steel owners. Four zero-density nut carriers are intentionally left
out of the physical mass sum. No solver or CAD geometry is loaded.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

from fea.dynamic_momentum import calculix_221_mass, momentum
from fea.wood_joint_mesh_jacobian_audit import parse_c3d10_deck


ROOT = Path.cwd().resolve()
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SNAPSHOT = BASE / "ordinary-transient-first-increment-snapshot-attempt01"
PILOT = BASE / "ordinary-transient-pilot-attempt03"
OUT = BASE / "ordinary-transient-global-momentum-audit-attempt01"
FIRST_AUDIT = BASE / "ordinary-transient-first-momentum-audit-attempt01/audit.py"
TIME = 0.0025
DAT_TIME = "0.2500000E-02"
GMSH_IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"

EXPECTED_SNAPSHOT_SHA = "82db7e5ccb0ad52d54a2b2c32499e6cac55b6cfb637fa2f6777a34b549f9d88f"
EXPECTED_FREEZE_SHA = "7a7c23a3f0ad6fe0f2342fcc9cc1f06ed2c85b9fbb194c1b39bb88c289222fe5"
EXPECTED_FIRST_AUDIT_SHA = "f484e6ad94803cac2b92a0ac64745296bd0c1d69afef5b5650a4ca9550250ec1"
EXPECTED_HELPER_SHAS = {
    "dynamic_momentum.py": "f97f0214a8dcd6ae8e539ed3f1377603031776e1b84235bb5dd058e48fd104e3",
    "wood_joint_mesh_jacobian_audit.py": "3f9cb7768f2ba0efb4e5b26f56222422a09048bfe5e1acdf5ded26f749d861c0",
}
EXPECTED_INPUT_SHAS = {
    "mesh.inp": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "rigid-carriers.inp": "a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815",
    "pilot-sets.inp": "7f5c158659658d60f6a3e48f714f4d8239cc7848c42732f747304b47fef9f5e0",
    "output-sets.inp": "e86adac9dfbe2a80bc62abcba3ea081efcad2e0262df100db22efc1e5020213c",
    "nut-coupling.inp": "af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903",
    "pilot.inp": "29c23fddf0800d8808ef9c28cea93caf4d019719aa68a3f089a7dd09d7870e4c",
    "actuator.json": "cc452f06600b72e576616adcd16f521c38f8bdfdcc7d90029f4eee0fb461b9a7",
    "contact-fragment.inc": "35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24",
    "producer.py.snapshot": "be28c15bdd095911979435b53f6e77955fd2d5b0f6ee80272c4e0ffcc29dde08",
    "nut-coupling.json": "568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960",
    "materials.inp": "e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb",
    "contact-manifest.json": "50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d",
    "preflight-input-freeze.json": "630c0819c51e1cdf727c182ba52ebaeacd23d2e8184e21cf5b01bcec4d447e26",
}

WOOD_BODIES = {
    "W00_BOTTOM_CENTER_RIGHT_CLEAT",
    "W01_BASE_RAIL_BOTTOM_RIGHT",
    "W02_BASE_PRINCIPAL_CENTER_RIGHT",
}
CLEAT_ID = "W00_BOTTOM_CENTER_RIGHT_CLEAT"
PRINCIPAL_ID = "W02_BASE_PRINCIPAL_CENTER_RIGHT"
NUT_BODIES = {
    "M03_A00_NUT",
    "M07_A01_NUT",
    "M11_A02_NUT",
    "M15_A03_NUT",
}
RHO_WOOD = 6.0e-10
RHO_STEEL = 7.85e-9


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} hash mismatch: {actual} != {expected}")
    return actual


def load_first_audit():
    require_hash(FIRST_AUDIT, EXPECTED_FIRST_AUDIT_SHA, "cleat audit helper")
    spec = importlib.util.spec_from_file_location("frozen_first_cleat_audit", FIRST_AUDIT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the frozen FRD/CLOAD parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_material_sections(path: Path) -> tuple[dict[str, float], dict[str, str]]:
    rows = path.read_text().splitlines()
    material = None
    densities: dict[str, float] = {}
    sections: dict[str, str] = {}
    for index, raw in enumerate(rows):
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("*MATERIAL,"):
            attrs = {}
            for field in upper.split(",")[1:]:
                key, sep, value = field.partition("=")
                if sep:
                    attrs[key.strip()] = value.strip()
            material = attrs.get("NAME")
        elif upper == "*DENSITY":
            if material is None:
                raise ValueError("DENSITY card without active material")
            data = next((row.strip() for row in rows[index + 1:] if row.strip() and not row.strip().startswith("**")), None)
            if data is None:
                raise ValueError(f"Missing density data for {material}")
            value = float(data.split(",")[0].strip())
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid density for {material}")
            if material in densities:
                raise ValueError(f"Duplicate density for {material}")
            densities[material] = value
        elif upper.startswith("*SOLID SECTION,"):
            attrs = {}
            for field in upper.split(",")[1:]:
                key, sep, value = field.partition("=")
                if sep:
                    attrs[key.strip()] = value.strip()
            elset, mat = attrs.get("ELSET"), attrs.get("MATERIAL")
            if not elset or not mat or elset in sections:
                raise ValueError(f"Malformed or duplicate solid section: {line}")
            sections[elset] = mat
    if not densities or not sections:
        raise ValueError("Material densities or solid sections are missing")
    return densities, sections


def read_elset(path: Path, target: str) -> set[int]:
    rows = path.read_text().splitlines()
    found: dict[str, set[int]] = {}
    active: str | None = None
    for raw in rows:
        line = raw.strip()
        upper = line.upper()
        if not line or upper.startswith("**"):
            continue
        if upper.startswith("*ELSET,"):
            active = None
            attrs = {}
            flags = set()
            for token in upper.split(",")[1:]:
                key, sep, value = token.partition("=")
                if sep:
                    attrs[key.strip()] = value.strip()
                else:
                    flags.add(key.strip())
            name = attrs.get("ELSET")
            if name == target.upper():
                if "GENERATE" in flags:
                    raise ValueError(f"Unexpected generated ELSET {target}")
                if name in found:
                    raise ValueError(f"Duplicate ELSET {target}")
                found[name] = set()
                active = name
        elif line.startswith("*"):
            active = None
        elif active == target.upper():
            try:
                values = [int(value.strip()) for value in line.split(",") if value.strip()]
            except ValueError as error:
                raise ValueError(f"Noninteger member in ELSET {target}") from error
            if not values or any(value <= 0 for value in values):
                raise ValueError(f"Invalid member in ELSET {target}")
            if len(set(values)) != len(values) or found[active].intersection(values):
                raise ValueError(f"Duplicate member in ELSET {target}")
            found[active].update(values)
    if target.upper() not in found or not found[target.upper()]:
        raise ValueError(f"Missing or empty ELSET {target}")
    return found[target.upper()]


def read_rigid_carriers(path: Path, nut_coupling_path: Path, bodies: dict[str, dict[int, tuple[int, ...]]]) -> dict:
    nsets: dict[str, set[int]] = {}
    cards = []
    active: str | None = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        upper = line.upper()
        if not line or upper.startswith("**"):
            continue
        if upper.startswith("*NSET,"):
            attrs = {}
            for field in upper.split(",")[1:]:
                key, sep, value = field.partition("=")
                if sep:
                    attrs[key.strip()] = value.strip()
            active = attrs.get("NSET")
            if not active or active in nsets:
                raise ValueError("Malformed or duplicate rigid carrier node set")
            nsets[active] = set()
        elif upper.startswith("*RIGID BODY,"):
            active = None
            attrs = {}
            for field in upper.split(",")[1:]:
                key, sep, value = field.partition("=")
                if sep:
                    attrs[key.strip()] = value.strip()
            cards.append(attrs)
        elif line.startswith("*"):
            active = None
        elif active:
            values = {int(value.strip()) for value in line.split(",") if value.strip()}
            if not values or min(values) <= 0 or nsets[active].intersection(values):
                raise ValueError(f"Invalid rigid carrier set {active}")
            nsets[active].update(values)

    expected_sets = {f"{body}_RIGID_NODES" for body in NUT_BODIES}
    if len(cards) != 4 or {card.get("NSET") for card in cards} != expected_sets:
        raise ValueError("Expected exactly four rigid-body carrier constraints")
    carrier_elements = {}
    for body in NUT_BODIES:
        expected_nodes = {node for row in bodies[body].values() for node in row}
        nset_name = f"{body}_RIGID_NODES"
        if nsets.get(nset_name) != expected_nodes:
            raise ValueError(f"Rigid carrier MPC node ownership mismatch for {body}")
        carrier_elements[body] = len(bodies[body])

    refs = {int(card["REF NODE"]) for card in cards}
    rots = {int(card["ROT NODE"]) for card in cards}
    control_nodes = set()
    in_node_card = False
    equation_cards = 0
    for raw in nut_coupling_path.read_text().splitlines():
        line = raw.strip()
        upper = line.upper()
        if not line or upper.startswith("**"):
            continue
        if upper == "*NODE":
            in_node_card = True
        elif upper.startswith("*EQUATION"):
            in_node_card = False
            equation_cards += 1
        elif line.startswith("*"):
            in_node_card = False
        elif in_node_card:
            control_nodes.add(int(line.split(",")[0].strip()))
    if refs | rots != control_nodes or refs & rots or len(refs) != 4 or len(rots) != 4:
        raise ValueError("RIGID BODY control nodes do not match the frozen nut coupling nodes")
    return {
        "carrier_bodies": sorted(NUT_BODIES),
        "rigid_body_card_count": len(cards),
        "carrier_element_counts": carrier_elements,
        "carrier_rigid_node_sets_match_all_body_nodes": True,
        "reference_nodes": sorted(refs),
        "rotation_nodes": sorted(rots),
        "control_nodes_added_by_nut_coupling": sorted(control_nodes),
        "nut_coupling_equation_card_count": equation_cards,
    }


def read_dat_total(path: Path, title: str, set_name: str) -> float:
    rows = path.read_text(errors="strict").splitlines()
    pattern = re.compile(
        rf"^{re.escape(title)}\s+for set\s+{re.escape(set_name)}\s+and time\s+{re.escape(DAT_TIME)}$",
        re.IGNORECASE,
    )
    starts = [i for i, row in enumerate(rows) if pattern.fullmatch(" ".join(row.split()))]
    if len(starts) != 1:
        raise ValueError(f"Expected one {title} total for {set_name} at {DAT_TIME}; found {len(starts)}")
    value_line = next((row.strip() for row in rows[starts[0] + 1:] if row.strip()), None)
    if value_line is None:
        raise ValueError(f"Missing value after {title} header for {set_name}")
    value = float(value_line)
    if not math.isfinite(value):
        raise ValueError(f"Nonfinite DAT total {title} for {set_name}")
    return value


def read_frd_half_quantums(path: Path, selected_nodes: set[int], reference_fields: dict, target_time: float) -> dict:
    """Read the printed FRD exponents and derive half-last-digit bounds."""
    wanted = {"DISP": ("D1", "D2", "D3"), "VELO": ("V1", "V2", "V3")}
    token_pattern = re.compile(r"^[+-]?\d\.\d{5}[Ee]([+-]\d{2})$")
    result = {}
    time = None
    expected_count = None
    active = None
    labels = []
    seen = set()
    quantums = {}
    with path.open("rt", encoding="ascii", errors="strict") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.startswith("  100CL"):
                parts = line.split()
                time, expected_count = float(parts[2]), int(parts[3])
                continue
            if line.startswith(" -4  "):
                parts = line.split()
                field = parts[1]
                if field in wanted and time is not None and math.isclose(time, target_time, rel_tol=0.0, abs_tol=1e-12):
                    if field in result or expected_count != len(selected_nodes):
                        raise ValueError(f"Unexpected or duplicate target FRD block {field}")
                    active = field
                    labels, seen, quantums = [], set(), {}
                else:
                    active = "SKIP"
                continue
            if active is None:
                continue
            if line.startswith(" -5"):
                labels.append(line.split()[1])
            elif line.startswith(" -1"):
                if active == "SKIP":
                    continue
                node = int(line[3:13])
                if node in seen:
                    raise ValueError(f"Duplicate {active} node at FRD line {line_number}")
                seen.add(node)
                if node not in selected_nodes:
                    continue
                row_quantums = []
                for axis, offset in enumerate((13, 25, 37)):
                    token = line[offset:offset + 12].strip()
                    match = token_pattern.fullmatch(token)
                    if not match:
                        raise ValueError(f"Unexpected FRD component format {token!r} at line {line_number}")
                    value = float(token)
                    if value != reference_fields[active][node][axis]:
                        raise ValueError(f"FRD values differ between source parser and quantization parser at line {line_number}")
                    exponent = int(match.group(1))
                    row_quantums.append(0.5 * (10.0 ** (exponent - 5)))
                quantums[node] = tuple(row_quantums)
            elif line.startswith(" -3"):
                if active != "SKIP":
                    if tuple(labels[:3]) != wanted[active] or len(seen) != expected_count or set(quantums) != selected_nodes:
                        raise ValueError(f"Incomplete {active} target block for FRD rounding audit")
                    result[active] = quantums
                active = None
                if set(result) == set(wanted):
                    break
    if active is not None or set(result) != set(wanted):
        raise ValueError("Missing firstpoint DISP/VELO blocks for FRD precision audit")
    return result


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vector_sum(rows):
    rows = tuple(rows)
    return [math.fsum(row[i] for row in rows) for i in range(3)]


def center_of_mass(nodes, blocks, field):
    mass_terms, first_moment = [], [[], [], []]
    for node_ids, block in blocks.values():
        for i, node_id in enumerate(node_ids):
            nodal_mass = math.fsum(block[i])
            mass_terms.append(nodal_mass)
            for axis in range(3):
                first_moment[axis].append(nodal_mass * field[node_id][axis])
    mass = math.fsum(mass_terms)
    center = [math.fsum(first_moment[axis]) / mass for axis in range(3)]
    return mass, center


def field_quantization_bounds(nodes, blocks, u, v, u_q, v_q, datum):
    """Bound momentum error from FRD half-quantums with absolute mass weights."""
    abs_column_terms: dict[int, list[float]] = {}
    h_origin_terms = [[], [], []]
    h_datum_terms = [[], [], []]
    axes = ((1, 2), (2, 0), (0, 1))
    for node_ids, block in blocks.values():
        for j, node_j in enumerate(node_ids):
            abs_column_terms.setdefault(node_j, []).append(
                math.fsum(abs(block[i][j]) for i in range(10))
            )
        local_origin = [0.0, 0.0, 0.0]
        local_datum = [0.0, 0.0, 0.0]
        for i, node_i in enumerate(node_ids):
            x = nodes[node_i]
            ui = u[node_i]
            dui = u_q[node_i]
            r0 = tuple(x[k] + ui[k] for k in range(3))
            ra = tuple(r0[k] - datum[k] for k in range(3))
            for j, node_j in enumerate(node_ids):
                mass_abs = abs(block[i][j])
                if not mass_abs:
                    continue
                vj, dvj = v[node_j], v_q[node_j]
                for component, (b, c) in enumerate(axes):
                    bound0 = (
                        dui[b] * (abs(vj[c]) + dvj[c]) + abs(r0[b]) * dvj[c]
                        + dui[c] * (abs(vj[b]) + dvj[b]) + abs(r0[c]) * dvj[b]
                    )
                    bounda = (
                        dui[b] * (abs(vj[c]) + dvj[c]) + abs(ra[b]) * dvj[c]
                        + dui[c] * (abs(vj[b]) + dvj[b]) + abs(ra[c]) * dvj[b]
                    )
                    local_origin[component] += mass_abs * bound0
                    local_datum[component] += mass_abs * bounda
        for component in range(3):
            h_origin_terms[component].append(local_origin[component])
            h_datum_terms[component].append(local_datum[component])
    linear = []
    for axis in range(3):
        linear.append(math.fsum(
            math.fsum(weights) * v_q[node][axis]
            for node, weights in abs_column_terms.items()
        ))
    return {
        "linear_momentum_xyz_Ns": linear,
        "angular_momentum_origin_xyz_Nmm_s": [math.fsum(values) for values in h_origin_terms],
        "angular_momentum_actuator_datum_xyz_Nmm_s": [math.fsum(values) for values in h_datum_terms],
    }


def integrate_positive_density_bodies(all_nodes, all_bodies, densities, sections, fields, quantums, actuator_datum):
    u, v = fields["DISP"], fields["VELO"]
    u_q, v_q = quantums["DISP"], quantums["VELO"]
    current = {node: tuple(x + du for x, du in zip(xyz, u[node])) for node, xyz in all_nodes.items()}
    physical_ids = sorted(body for body in all_bodies if densities[sections[body]] > 0.0)
    by_density = {}
    for body in physical_ids:
        by_density.setdefault(densities[sections[body]], []).append(body)
    body_rows = {}
    precision_parts = {name: [[], [], []] for name in (
        "linear_momentum_xyz_Ns",
        "angular_momentum_origin_xyz_Nmm_s",
        "angular_momentum_actuator_datum_xyz_Nmm_s",
    )}
    for rho, group_bodies in sorted(by_density.items()):
        group_elements = {}
        for body in group_bodies:
            if set(group_elements).intersection(all_bodies[body]):
                raise ValueError("Element owner collision across positive-density body sets")
            group_elements.update(all_bodies[body])
        group_node_ids = {node for row in group_elements.values() for node in row}
        group_nodes = {node: all_nodes[node] for node in group_node_ids}
        blocks = calculix_221_mass(group_elements, group_nodes, rho)
        group_precision = field_quantization_bounds(group_nodes, blocks, u, v, u_q, v_q, actuator_datum)
        for name, values in group_precision.items():
            for axis, value in enumerate(values):
                precision_parts[name][axis].append(value)
        datum_nodes = {node: tuple(x - actuator_datum[a] for a, x in enumerate(xyz))
                       for node, xyz in group_nodes.items()}
        for body in group_bodies:
            owned = {element: blocks[element] for element in all_bodies[body]}
            state = momentum(group_nodes, owned, u, v)
            datum_state = momentum(datum_nodes, owned, u, v)
            ref_mass, ref_center = center_of_mass(group_nodes, owned, group_nodes)
            current_mass, current_center = center_of_mass(group_nodes, owned, current)
            if not math.isclose(ref_mass, state["mass"], rel_tol=2e-12) or not math.isclose(current_mass, state["mass"], rel_tol=2e-12):
                raise ValueError(f"Mass/COM integration mismatch for {body}")
            kind = "wood" if body in WOOD_BODIES else "steel"
            body_rows[body] = {
                "kind": kind,
                "material": sections[body],
                "density_tonne_per_mm3": rho,
                "element_count": len(all_bodies[body]),
                "node_count": len({node for row in all_bodies[body].values() for node in row}),
                "mass_tonne": state["mass"],
                "mass_kg": 1000.0 * state["mass"],
                "reference_com_xyz_mm": ref_center,
                "current_com_xyz_mm": current_center,
                "linear_momentum_xyz_Ns": list(state["linear_momentum"]),
                "angular_momentum_origin_xyz_Nmm_s": list(state["angular_momentum"]),
                "angular_momentum_actuator_datum_xyz_Nmm_s": list(datum_state["angular_momentum"]),
                "kinetic_energy_Nmm": state["kinetic_energy"],
            }
        del blocks

    if set(body_rows) != set(physical_ids):
        raise ValueError("Not every positive-density owner was integrated")
    total_mass = math.fsum(row["mass_tonne"] for row in body_rows.values())
    p = vector_sum(row["linear_momentum_xyz_Ns"] for row in body_rows.values())
    h = vector_sum(row["angular_momentum_origin_xyz_Nmm_s"] for row in body_rows.values())
    h_datum = vector_sum(row["angular_momentum_actuator_datum_xyz_Nmm_s"] for row in body_rows.values())
    ke = math.fsum(row["kinetic_energy_Nmm"] for row in body_rows.values())
    reference_com = [math.fsum(row["mass_tonne"] * row["reference_com_xyz_mm"][axis] for row in body_rows.values()) / total_mass for axis in range(3)]
    current_com = [math.fsum(row["mass_tonne"] * row["current_com_xyz_mm"][axis] for row in body_rows.values()) / total_mass for axis in range(3)]
    h_com = cross(current_com, p)
    h_centered = [h[i] - h_com[i] for i in range(3)]
    h_datum_by_shift = [h[i] - component for i, component in enumerate(cross(actuator_datum, p))]
    translation_residual = [h_datum[i] - h_datum_by_shift[i] for i in range(3)]
    safety = 1.0 + 1e-10
    precision_bounds = {name: [math.fsum(parts) * safety for parts in axes]
                        for name, axes in precision_parts.items()}
    return {
        "physical_body_count": len(body_rows),
        "wood_body_count": sum(row["kind"] == "wood" for row in body_rows.values()),
        "steel_body_count": sum(row["kind"] == "steel" for row in body_rows.values()),
        "element_count": sum(row["element_count"] for row in body_rows.values()),
        "node_count_unique_across_physical_mesh": len({node for body in physical_ids for row in all_bodies[body].values() for node in row}),
        "mass_tonne": total_mass,
        "mass_kg": 1000.0 * total_mass,
        "reference_com_xyz_mm": reference_com,
        "current_com_xyz_mm": current_com,
        "linear_momentum_xyz_Ns": p,
        "angular_momentum_origin_xyz_Nmm_s": h,
        "actuator_datum_global_xyz_mm": list(actuator_datum),
        "angular_momentum_actuator_datum_xyz_Nmm_s": h_datum,
        "angular_momentum_actuator_datum_from_translation_identity_xyz_Nmm_s": h_datum_by_shift,
        "angular_momentum_translation_identity_residual_xyz_Nmm_s": translation_residual,
        "angular_momentum_current_com_xyz_Nmm_s": h_centered,
        "kinetic_energy_Nmm": ke,
        "frd_print_rounding_abs_error_bounds": precision_bounds,
        "frd_rounding_bound_safety_factor": safety,
        "bodies": body_rows,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = load_first_audit()
    snapshot_path = SNAPSHOT / "snapshot.json"
    snapshot_sha = require_hash(snapshot_path, EXPECTED_SNAPSHOT_SHA, "snapshot metadata")
    snapshot = json.loads(snapshot_path.read_text())
    freeze_path = SNAPSHOT / "input-freeze.json"
    freeze_sha = require_hash(freeze_path, EXPECTED_FREEZE_SHA, "snapshot input freeze")
    freeze = json.loads(freeze_path.read_text())
    if snapshot["target_time_seconds"] != TIME or snapshot["mechanical_acceptance"]:
        raise ValueError("Wrong snapshot time or scope")
    if Path(snapshot["source_directory"]).name != PILOT.name:
        raise ValueError("Snapshot is not from the frozen native03 pilot")
    if freeze.get("artifacts_sha256") != EXPECTED_INPUT_SHAS:
        raise ValueError("Frozen input artifact map changed")
    input_shas = {key: require_hash(PILOT / key, expected, f"frozen {key}") for key, expected in EXPECTED_INPUT_SHAS.items()}

    frd_path, dat_path = SNAPSHOT / "pilot.frd", SNAPSHOT / "pilot.dat"
    frd_sha = require_hash(frd_path, snapshot["files"]["pilot.frd"]["sha256"], "snapshot FRD")
    dat_sha = require_hash(dat_path, snapshot["files"]["pilot.dat"]["sha256"], "snapshot DAT")
    if dat_sha != "cbbca38de8de43d718be48442cc0c6f61ccbc6ff85b15014df47485aca0868f7":
        raise ValueError("Unexpected frozen firstpoint DAT")

    materials_path = PILOT / "materials.inp"
    densities, sections = read_material_sections(materials_path)
    if densities != {
        "WOOD_ELASTIC_DIAGNOSTIC": RHO_WOOD,
        "STEEL_ELASTIC_DIAGNOSTIC": RHO_STEEL,
        "NUT_ZERO_MASS_RIGID_CARRIER": 0.0,
    }:
        raise ValueError(f"Unexpected material densities: {densities}")
    if len(sections) != 19 or set(sections.values()) != set(densities):
        raise ValueError("Expected one section for each of the 19 owners and all three materials")
    if {body for body, mat in sections.items() if mat == "WOOD_ELASTIC_DIAGNOSTIC"} != WOOD_BODIES:
        raise ValueError("Timber section ownership changed")
    if {body for body, mat in sections.items() if mat == "NUT_ZERO_MASS_RIGID_CARRIER"} != NUT_BODIES:
        raise ValueError("Zero-density nut carrier ownership changed")
    steel_bodies = {body for body, mat in sections.items() if mat == "STEEL_ELASTIC_DIAGNOSTIC"}
    if len(steel_bodies) != 12 or steel_bodies & WOOD_BODIES or steel_bodies & NUT_BODIES:
        raise ValueError("Expected exactly twelve positive-density steel owners")

    mesh_path = PILOT / "mesh.inp"
    all_nodes, all_bodies = parse_c3d10_deck(mesh_path, expected_body_ids=frozenset(sections), elset_prefix="")
    if len(all_bodies) != 19 or set(all_bodies) != set(sections):
        raise ValueError("Mesh element owner map differs from material section map")
    body_node_sets = {body: {node for row in elements.values() for node in row} for body, elements in all_bodies.items()}
    all_element_ids = {element for elements in all_bodies.values() for element in elements}
    if len(all_element_ids) != sum(map(len, all_bodies.values())):
        raise ValueError("C3D10 element IDs are not unique across body owners")
    output_sets = PILOT / "output-sets.inp"
    output_all = read_elset(output_sets, "CURRENT_ALL_ELEMENTS")
    output_nuts = read_elset(output_sets, "CURRENT_NUT_CARRIERS")
    nut_elements = {element for body in NUT_BODIES for element in all_bodies[body]}
    if output_all != all_element_ids or output_nuts != nut_elements:
        raise ValueError("DAT element owner ELSETs differ from mesh/material ownership")
    if any(not body.startswith("M") or "NUT" not in body for body in NUT_BODIES):
        raise ValueError("Nut carrier classification contract changed")

    rigid = read_rigid_carriers(PILOT / "rigid-carriers.inp", PILOT / "nut-coupling.inp", all_bodies)
    included_inputs = [PILOT / name for name in (
        "pilot.inp", "materials.inp", "nut-coupling.inp", "rigid-carriers.inp",
        "contact-fragment.inc", "output-sets.inp", "pilot-sets.inp",
    )]
    boundary_cards = [str(path.name) for path in included_inputs
                      if any(row.strip().upper().startswith("*BOUNDARY") for row in path.read_text().splitlines())]
    if boundary_cards:
        raise ValueError(f"Unexpected externally restrained nodes in model input: {boundary_cards}")

    dat_total_ke = read_dat_total(dat_path, "total kinetic energy", "CURRENT_ALL_ELEMENTS")
    dat_total_mass = read_dat_total(dat_path, "total mass", "CURRENT_ALL_ELEMENTS")
    dat_nut_ke = read_dat_total(dat_path, "total kinetic energy", "CURRENT_NUT_CARRIERS")
    if dat_nut_ke != 0.0:
        raise ValueError("DAT reports nonzero kinetic energy for zero-density nut carriers")

    mesh_ids = set(all_nodes)
    fields = source.parse_frd_fields(frd_path, mesh_ids, TIME)
    if set(fields["DISP"]) != mesh_ids or set(fields["VELO"]) != mesh_ids:
        raise ValueError("Firstpoint FRD fields do not cover every physical mesh node")
    actuator = json.loads((PILOT / "actuator.json").read_text())
    actuator_datum = tuple(float(value) for value in actuator["datum_global_xyz_mm"])
    if len(actuator_datum) != 3 or not all(map(math.isfinite, actuator_datum)):
        raise ValueError("Invalid frozen actuator datum")
    quantums = read_frd_half_quantums(frd_path, mesh_ids, fields, TIME)
    max_half_quantum = {
        field: [max(row[axis] for row in quantums[field].values()) for axis in range(3)]
        for field in ("DISP", "VELO")
    }
    physical = integrate_positive_density_bodies(
        all_nodes, all_bodies, densities, sections, fields, quantums, actuator_datum
    )
    if physical["physical_body_count"] != 15 or physical["wood_body_count"] != 3 or physical["steel_body_count"] != 12:
        raise ValueError("Positive-density owner count mismatch")

    dat_mass_error = physical["mass_tonne"] - dat_total_mass
    dat_ke_error = physical["kinetic_energy_Nmm"] - dat_total_ke

    amplitude_samples, amplitude_end, continuous_impulse_factor = source.parse_amplitude(PILOT / "pilot.inp", TIME)
    cleat_nodes = body_node_sets[CLEAT_ID]
    principal_nodes = body_node_sets[PRINCIPAL_ID]
    loads = source.parse_cload(PILOT / "pilot.inp", cleat_nodes, principal_nodes)
    cleat_loads = {node: vector for node, vector in loads.items() if node in cleat_nodes}
    principal_loads = {node: vector for node, vector in loads.items() if node in principal_nodes}
    if len(loads) != 331 or len(cleat_loads) != 151 or len(principal_loads) != 180:
        raise ValueError("Serialized paired actuator CLOAD ownership changed")
    force_by_patch = {"cleat": vector_sum(cleat_loads.values()), "principal": vector_sum(principal_loads.values())}
    force_unit = vector_sum(loads.values())
    reference_moment_by_patch = {
        "cleat": vector_sum(cross(all_nodes[node], force) for node, force in cleat_loads.items()),
        "principal": vector_sum(cross(all_nodes[node], force) for node, force in principal_loads.items()),
    }
    current_nodes = {node: tuple(x + du for x, du in zip(all_nodes[node], fields["DISP"][node])) for node in loads}
    datum_nodes = {node: tuple(x - actuator_datum[axis] for axis, x in enumerate(xyz))
                   for node, xyz in current_nodes.items()}
    endpoint_moment_by_patch = {
        "cleat": vector_sum(cross(current_nodes[node], force) for node, force in cleat_loads.items()),
        "principal": vector_sum(cross(current_nodes[node], force) for node, force in principal_loads.items()),
    }
    endpoint_datum_moment_by_patch = {
        "cleat": vector_sum(cross(datum_nodes[node], force) for node, force in cleat_loads.items()),
        "principal": vector_sum(cross(datum_nodes[node], force) for node, force in principal_loads.items()),
    }
    reference_moment_unit = vector_sum(reference_moment_by_patch.values())
    endpoint_moment_unit = vector_sum(endpoint_moment_by_patch.values())
    endpoint_datum_moment_unit = vector_sum(endpoint_datum_moment_by_patch.values())
    force_endpoint = [amplitude_end * value for value in force_unit]
    impulse_factor = 0.5 * TIME * amplitude_end
    discrete_force_impulse = [impulse_factor * value for value in force_unit]
    discrete_moment_impulse = [impulse_factor * value for value in endpoint_moment_unit]
    discrete_datum_moment_impulse = [impulse_factor * value for value in endpoint_datum_moment_unit]
    source_volume_impulse = [continuous_impulse_factor * value for value in force_unit]

    linear_residual = [actual - target for actual, target in zip(physical["linear_momentum_xyz_Ns"], discrete_force_impulse)]
    angular_residual = [actual - target for actual, target in zip(physical["angular_momentum_origin_xyz_Nmm_s"], discrete_moment_impulse)]
    angular_datum_residual = [actual - target for actual, target in zip(physical["angular_momentum_actuator_datum_xyz_Nmm_s"], discrete_datum_moment_impulse)]
    moment_u_error_bound = [
        math.fsum(
            quantums["DISP"][node][b] * abs(force[c])
            + quantums["DISP"][node][c] * abs(force[b])
            for node, force in loads.items()
        )
        for b, c in ((1, 2), (2, 0), (0, 1))
    ]
    impulse_moment_error_bound = [impulse_factor * value for value in moment_u_error_bound]
    precision = physical["frd_print_rounding_abs_error_bounds"]
    total_p_residual_bound = precision["linear_momentum_xyz_Ns"]
    total_h_origin_residual_bound = [precision["angular_momentum_origin_xyz_Nmm_s"][i] + impulse_moment_error_bound[i] for i in range(3)]
    total_h_datum_residual_bound = [precision["angular_momentum_actuator_datum_xyz_Nmm_s"][i] + impulse_moment_error_bound[i] for i in range(3)]
    translation_bound = []
    for component, (b, c) in enumerate(((1, 2), (2, 0), (0, 1))):
        translation_bound.append(
            precision["angular_momentum_origin_xyz_Nmm_s"][component]
            + precision["angular_momentum_actuator_datum_xyz_Nmm_s"][component]
            + abs(actuator_datum[b]) * total_p_residual_bound[c]
            + abs(actuator_datum[c]) * total_p_residual_bound[b]
        )
    helper_shas = {
        "global_audit.py": sha256_file(Path(__file__)),
        "audit.py": require_hash(FIRST_AUDIT, EXPECTED_FIRST_AUDIT_SHA, "cleat audit helper"),
        "dynamic_momentum.py": require_hash(ROOT / "fea/dynamic_momentum.py", EXPECTED_HELPER_SHAS["dynamic_momentum.py"], "momentum helper"),
        "wood_joint_mesh_jacobian_audit.py": require_hash(ROOT / "fea/wood_joint_mesh_jacobian_audit.py", EXPECTED_HELPER_SHAS["wood_joint_mesh_jacobian_audit.py"], "mesh parser"),
        "gmsh_integration_image": GMSH_IMAGE,
    }

    report = {
        "schema": "wood_joint_first_transient_global_momentum_audit/v1",
        "scope": "The first completed .0025 s increment only; no full-pilot response or acceptance claim.",
        "snapshot": {
            "snapshot_json_sha256": snapshot_sha,
            "snapshot_input_freeze_sha256": freeze_sha,
            "snapshot_frd_sha256": frd_sha,
            "snapshot_dat_sha256": dat_sha,
            "target_time_seconds": TIME,
            "snapshot_source_process_still_running": snapshot["source_process_still_running"],
            "mechanical_acceptance": snapshot["mechanical_acceptance"],
            "physical_frd_nodes": len(mesh_ids),
            "frd_fields": ["DISP", "VELO"],
        },
        "frozen_inputs_sha256": input_shas,
        "helpers_sha256": helper_shas,
        "owner_map": {
            "material_densities_tonne_per_mm3": densities,
            "solid_sections_by_elset": sections,
            "physical_owners": sorted(physical["bodies"]),
            "zero_density_nut_owners_excluded": sorted(NUT_BODIES),
            "all_element_count": len(all_element_ids),
            "physical_positive_density_element_count": physical["element_count"],
            "nut_carrier_element_count": len(nut_elements),
            "output_set_ownership_validated": True,
        },
        "rigid_carrier_mpc": {
            **rigid,
            "nut_density_tonne_per_mm3": densities["NUT_ZERO_MASS_RIGID_CARRIER"],
            "dat_current_nut_carrier_kinetic_energy_Nmm": dat_nut_ke,
            "interpretation": "The four carrier solids have zero density and are omitted from physical inertia. Their *RIGID BODY constraints and shaft-fit *EQUATION controls can mediate internal force/moment transfer but add no carrier material mass; reference and rotation control nodes are not mass owners.",
        },
        "physical_positive_density_patch": physical,
        "frd_output_rounding": {
            "format_observed": "FRD component fields are 12-character scientific values with five fractional mantissa digits and a signed two-digit exponent.",
            "half_quantum_formula": "0.5 * 10**(printed_exponent - 5), per component and node.",
            "maximum_component_half_quantum": max_half_quantum,
            "momentum_residual_abs_error_bound_xyz_Ns": total_p_residual_bound,
            "angular_origin_residual_abs_error_bound_xyz_Nmm_s": total_h_origin_residual_bound,
            "angular_actuator_datum_residual_abs_error_bound_xyz_Nmm_s": total_h_datum_residual_bound,
            "translation_identity_residual_abs_error_bound_xyz_Nmm_s": translation_bound,
            "endpoint_applied_moment_from_DISP_rounding_abs_error_bound_unit_Nmm": moment_u_error_bound,
            "endpoint_angular_impulse_from_DISP_rounding_abs_error_bound_Nmm_s": impulse_moment_error_bound,
            "linear_residual_within_FRD_rounding_bound_by_component": [abs(value) <= bound for value, bound in zip(linear_residual, total_p_residual_bound)],
            "angular_origin_residual_within_FRD_rounding_bound_by_component": [abs(value) <= bound for value, bound in zip(angular_residual, total_h_origin_residual_bound)],
            "angular_actuator_datum_residual_within_FRD_rounding_bound_by_component": [abs(value) <= bound for value, bound in zip(angular_datum_residual, total_h_datum_residual_bound)],
            "translation_identity_residual_within_FRD_rounding_bound_by_component": [abs(value) <= bound for value, bound in zip(physical["angular_momentum_translation_identity_residual_xyz_Nmm_s"], translation_bound)],
            "interpretation_limit": "These bounds cover FRD decimal formatting only, with a 1e-10 summation guard; they do not cover contact/MPC-transformed mass or solver equation residuals.",
        },
        "dat_el_print": {
            "set": "CURRENT_ALL_ELEMENTS",
            "native_total_mass_tonne": dat_total_mass,
            "native_total_kinetic_energy_Nmm": dat_total_ke,
            "mass_native_minus_dat_tonne": dat_mass_error,
            "mass_relative_difference": dat_mass_error / dat_total_mass,
            "ke_four_point_minus_dat_Nmm": dat_ke_error,
            "ke_relative_difference": dat_ke_error / dat_total_ke if dat_total_ke else None,
            "units": "consistent mm, N, s, tonne model units; ELKE is N·mm",
        },
        "applied_pair_first_increment": {
            "source": "Frozen native03 pilot.inp CLOAD with RAMP_N, read from source mesh node coordinates and firstpoint FRD DISP",
            "loaded_node_count": len(loads),
            "cleat_loaded_node_count": len(cleat_loads),
            "principal_loaded_node_count": len(principal_loads),
            "ramp_sample_count": len(amplitude_samples),
            "endpoint_amplitude": amplitude_end,
            "unit_force_resultant_by_patch_N": force_by_patch,
            "unit_force_pair_resultant_N": force_unit,
            "endpoint_force_pair_resultant_N": force_endpoint,
            "newmark_endpoint_trapezoid_linear_impulse_Ns": discrete_force_impulse,
            "continuous_sampled_ramp_linear_impulse_Ns": source_volume_impulse,
            "unit_moment_about_origin_by_patch_Nmm_reference_geometry": reference_moment_by_patch,
            "unit_moment_about_origin_pair_Nmm_reference_geometry": reference_moment_unit,
            "unit_moment_about_origin_by_patch_Nmm_endpoint_geometry": endpoint_moment_by_patch,
            "unit_moment_about_origin_pair_Nmm_endpoint_geometry": endpoint_moment_unit,
            "actuator_datum_global_xyz_mm": list(actuator_datum),
            "unit_moment_about_actuator_datum_by_patch_Nmm_endpoint_geometry": endpoint_datum_moment_by_patch,
            "unit_moment_about_actuator_datum_pair_Nmm_endpoint_geometry": endpoint_datum_moment_unit,
            "newmark_endpoint_trapezoid_angular_impulse_Nmm_s": discrete_moment_impulse,
            "newmark_endpoint_trapezoid_angular_impulse_about_actuator_datum_Nmm_s": discrete_datum_moment_impulse,
            "global_linear_momentum_minus_discrete_pair_impulse_Ns": linear_residual,
            "global_angular_momentum_origin_minus_discrete_pair_impulse_Nmm_s": angular_residual,
            "global_angular_momentum_actuator_datum_minus_discrete_pair_impulse_Nmm_s": angular_datum_residual,
        },
        "limits": [
            "All physical mass and state integrals use the untransformed CalculiX 2.21 four-point C3D10 reference mass. The reported scalar ELKE comparison checks this snapshot only; it does not reconstruct or qualify a solver-wide contact/MPC-transformed mass operator.",
            "The four zero-density nut carriers are not included as physical material inertia. Rigid-body and shaft-fit MPCs are internal model constraints, but this audit does not reconstruct their transformed equations or local reactions.",
            "The firstpoint applied pair has near-zero net force; its angular impulse is evaluated from the actual nodal CLOAD distribution and endpoint geometry. Componentwise FRD print-rounding bounds distinguish output resolution from exact closure, but are not solver residual bounds.",
            "This is a single first increment from an immutable snapshot whose source process was still running. It does not establish time accuracy, capacity, response convergence, or joint acceptance.",
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    readme = f"""# First transient whole-patch momentum audit — attempt 01

This post-processes only the immutable native03 first-converged snapshot at
`t={TIME:.4f} s`. The calculation integrates the actual firstpoint FRD `DISP`
and `VELO` fields over all positive-density physical timber and steel owners,
using their frozen material densities and the source-reconstructed
CalculiX 2.21 four-point C3D10 mass matrix. It runs no solver and imports no
CAD. Gmsh is used only to integrate the frozen mesh reference-volume mass.

The section map resolves 19 C3D10 owners: three timber owners at
`{RHO_WOOD:.3g} tonne/mm³`, twelve steel owners at `{RHO_STEEL:.3g}
tonne/mm³`, and the four nut carrier solids at exactly zero density. The
carrier element sets are excluded from material inertia; they remain present
as kinematic constraints. The four `*RIGID BODY` cards tie every node in each
nut carrier to reference/rotation control nodes, while the frozen
`nut-coupling.inp` shaft-fit equations connect those controls to the bolt
shaft model. These constraints may pass internal force and moment between
the physical owners, but the carriers and control nodes add no mass. The DAT
also reports zero kinetic energy for `CURRENT_NUT_CARRIERS`.

| Quantity | Four-point physical-owner audit | Native DAT |
| --- | ---: | ---: |
| Total mass | {physical['mass_kg']:.12g} kg | {dat_total_mass * 1000:.12g} kg |
| Total kinetic energy | {physical['kinetic_energy_Nmm']:.12g} N·mm | {dat_total_ke:.12g} N·mm |
| Linear momentum (X, Y, Z) | `{physical['linear_momentum_xyz_Ns']}` N·s | Compare with paired impulse below |
| Angular momentum about origin (X, Y, Z) | `{physical['angular_momentum_origin_xyz_Nmm_s']}` N·mm·s | Compare with applied angular impulse below |
| Angular momentum about actuator datum (X, Y, Z) | `{physical['angular_momentum_actuator_datum_xyz_Nmm_s']}` N·mm·s | Datum `{list(actuator_datum)}` mm |

The serialized actuator pair sums to a unit resultant
`{force_unit}` N before amplitude scaling. Its firstpoint Newmark
endpoint-trapezoid linear impulse is `{discrete_force_impulse}` N·s. The
actual nodal force distribution has reference-geometry moment
`{reference_moment_unit}` N·mm per unit amplitude and endpoint-geometry
moment `{endpoint_moment_unit}` N·mm per unit amplitude, so the corresponding
discrete angular impulse is `{discrete_moment_impulse}` N·mm·s. At the actuator
datum the endpoint couple is `{endpoint_datum_moment_unit}` N·mm per unit
amplitude and its discrete impulse is `{discrete_datum_moment_impulse}`
N·mm·s. The pair is self-equilibrated in force; the report retains its moment
rather than assuming it is moment-free.

FRD values use 12-character scientific fields with five digits after the
mantissa decimal. For each printed exponent `e`, the audit uses a component
half-quantum of `0.5 × 10^(e−5)`. It propagates those node-specific `DISP`
and `VELO` bounds through absolute four-point mass-matrix weights for `P`
and through `Σ |Mᵢⱼ| rᵢ×vⱼ` for `H`, including `δr`, `δv`, and cross terms.
The momentum residual is `{linear_residual}` N·s against componentwise bound
`{total_p_residual_bound}` N·s; within-bound flags are
`{[abs(value) <= bound for value, bound in zip(linear_residual, total_p_residual_bound)]}`.
About the actuator datum, the angular residual is `{angular_datum_residual}`
N·mm·s against bound `{total_h_datum_residual_bound}` N·mm·s; within-bound
flags are `{[abs(value) <= bound for value, bound in zip(angular_datum_residual, total_h_datum_residual_bound)]}`.
These bounds decide what the printed fields resolve; they do not include
solver equation residuals or contact/MPC mass transformation.

The origin-shift check gives direct actuator-datum angular momentum
`{physical['angular_momentum_actuator_datum_xyz_Nmm_s']}` and
`H₀ − a×P = {physical['angular_momentum_actuator_datum_from_translation_identity_xyz_Nmm_s']}`
N·mm·s, with translation residual
`{physical['angular_momentum_translation_identity_residual_xyz_Nmm_s']}`.
Per-owner mass, center of mass, momentum, angular momentum, kinetic energy,
source pins, and full residual bounds are in [`report.json`](report.json); the
executable method is [`audit.py`](audit.py).

The untransformed four-point mass gives a DAT total ELKE difference of
`{dat_ke_error:.6g} N·mm` (`{(dat_ke_error / dat_total_ke):.6g}` relative) on
this firstpoint. This scalar comparison is useful evidence for the summed
body kinetic energy; it does not qualify the solver's full effective mass
through contact or rigid-carrier MPC transformations. Momentum closure also
remains conditional on those internal transfer paths and the single-step
Newmark impulse. FRD rounding bounds apply only to printed-data uncertainty,
not to the solver's transformed mass or constraint residuals.
"""
    (OUT / "README.md").write_text(readme)
    print(json.dumps({
        "report": str((OUT / "report.json").relative_to(ROOT)),
        "sha256": sha256_file(OUT / "report.json"),
        "mass_kg": physical["mass_kg"],
        "ke_four_point_Nmm": physical["kinetic_energy_Nmm"],
        "ke_dat_Nmm": dat_total_ke,
        "linear_momentum_Ns": physical["linear_momentum_xyz_Ns"],
        "angular_momentum_origin_Nmm_s": physical["angular_momentum_origin_xyz_Nmm_s"],
        "force_pair_discrete_impulse_Ns": discrete_force_impulse,
        "moment_pair_discrete_impulse_Nmm_s": discrete_moment_impulse,
        "body_count": physical["physical_body_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
