"""Compose the frozen ordinary joint's zero-load native preflight.

This is a diagnostic stiff-engagement scenario, not an accepted joint model.
No geometry is changed. The nut display volumes carry a rigid seat only and
are assigned zero density; every nut controller is tied to the shaft fit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
MESH_SHA = "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803"
MESH_REPORT_SHA = "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07"
SOLVER_IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def set_cards(kind, name, ids):
    ids = sorted(set(ids))
    if not ids:
        raise ValueError(f"empty {kind}: {name}")
    lines = [f"*{kind},{kind}={name}"]
    lines.extend(",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16))
    return "\n".join(lines) + "\n"


def material_cards(reserved_materials, nut_elsets):
    """Add explicit scenario densities, assigning no physical nut mass."""
    text = reserved_materials
    wood_marker = "*MATERIAL,NAME=WOOD_ELASTIC_DIAGNOSTIC\n"
    steel_marker = "*MATERIAL,NAME=STEEL_ELASTIC_DIAGNOSTIC\n"
    if text.count(wood_marker) != 1 or text.count(steel_marker) != 1:
        raise ValueError("unexpected material fragment")
    if "*DENSITY" in text.upper():
        raise ValueError("input fragment already defines densities")
    # N, mm, seconds => mass unit tonne. These are nominal scenario values,
    # matching the current weight inventory, not measured delivered materials.
    text = text.replace(wood_marker, wood_marker + "*DENSITY\n6e-10\n")
    text = text.replace(steel_marker, steel_marker + "*DENSITY\n7.85e-9\n")
    text += (
        "** Nut envelopes are kinematic seat carriers, not physical solids.\n"
        "*MATERIAL,NAME=NUT_ZERO_MASS_RIGID_CARRIER\n"
        "*DENSITY\n0\n*ELASTIC\n200000,0.3\n"
    )
    for name in nut_elsets:
        text += f"*SOLID SECTION,ELSET={name},MATERIAL=NUT_ZERO_MASS_RIGID_CARRIER\n"
    return text


def prepare(
    output_directory, nut_directory, gauge_directory, *, step_cards, step_scope
):
    """Freeze actual source fragments and a separately declared no-load step."""
    destination = Path(output_directory).resolve()
    nut_directory, gauge_directory = Path(nut_directory), Path(gauge_directory)
    paths = {
        "mesh.inp": BASE / "ordinary-patch-mesh-attempt02/mesh/mesh.inp",
        "mesh.json": BASE / "ordinary-patch-mesh-attempt02/mesh/mesh.json",
        "materials-source.inp": BASE
        / "ordinary-patch-materials-attempt01/source_transverse_a__nuts_reserved_for_downstream_rigid_body.inp",
        "contact-fragment.inc": BASE
        / "ordinary-patch-contact-deck-attempt01/contact-fragment.inc",
        "contact-manifest.json": BASE
        / "ordinary-patch-contact-deck-attempt01/contact-manifest.json",
        "nut-coupling.inp": nut_directory / "nut-coupling.inp",
        "nut-coupling.json": nut_directory / "nut-coupling.json",
        "gauge.inp": gauge_directory / "gauge.inp",
        "gauge.json": gauge_directory / "gauge.json",
        "producer.py.snapshot": Path(__file__),
    }
    hashes = {name: sha(path) for name, path in paths.items()}
    if hashes["mesh.inp"] != MESH_SHA or hashes["mesh.json"] != MESH_REPORT_SHA:
        raise ValueError("current mesh hash mismatch")
    mesh = json.loads(paths["mesh.json"].read_text())
    nut = json.loads(paths["nut-coupling.json"].read_text())
    contacts = json.loads(paths["contact-manifest.json"].read_text())
    contact_text = paths["contact-fragment.inc"].read_text()
    if hashes["contact-fragment.inc"] != contacts["contact_fragment_sha256"]:
        raise ValueError("contact fragment/manifest mismatch")
    if (
        sum(line.startswith("*CONTACT PAIR,") for line in contact_text.splitlines())
        != 35
    ):
        raise ValueError("expected exactly 35 contact pairs")
    if hashes["nut-coupling.inp"] != nut["include_file_sha256"]:
        raise ValueError("nut coupling fragment/manifest mismatch")
    forbidden = (
        "*CLOAD",
        "*DLOAD",
        "*DSLOAD",
        "*TEMPERATURE",
        "*PRE-TENSION",
        "*INITIAL CONDITIONS",
        "*STABILIZE",
    )
    for name in ("nut-coupling.inp", "gauge.inp", "contact-fragment.inc"):
        if any(paths[name].read_text().upper().count(card) for card in forbidden):
            raise ValueError(f"load or stabilization in {name}")
    if any(card in step_cards.upper() for card in forbidden):
        raise ValueError("preflight must be zero-load without stabilization")
    nuts = [row for row in mesh["bodies"].values() if row["component_role"] == "nut"]
    if len(nuts) != 4 or len(nut["per_nut"]) != 4:
        raise ValueError("expected four rigid nut seat carriers")
    rigid = (
        "** Six-DOF shaft-fit stiff-engagement sensitivity; no physical thread claim.\n"
    )
    carriers = []
    for row in nut["per_nut"]:
        body_name = row["original_solid_nut_mesh"]["mesh_body_id"]
        body = mesh["bodies"][body_name]
        sets = row["control_node_sets"]
        # The controls are not members of the carrier node set.
        ref, rot = nut["nsets"][sets["rigid_control_nset"]]
        if ref in body["nodes"] or rot in body["nodes"]:
            raise ValueError("rigid control is embedded in the carrier mesh")
        node_set = body_name + "_RIGID_NODES"
        rigid += set_cards("NSET", node_set, body["nodes"])
        rigid += f"*RIGID BODY,NSET={node_set},REF NODE={ref},ROT NODE={rot}\n"
        carriers.append(
            {
                "elset": body_name,
                "nset": node_set,
                "reference_node": ref,
                "rotation_node": rot,
                "density_tonne_per_mm3": 0.0,
            }
        )
    material_text = material_cards(
        paths["materials-source.inp"].read_text(), [row["elset"] for row in carriers]
    )
    all_nodes = [node for row in mesh["bodies"].values() for node in row["nodes"]]
    all_elements = [elem for row in mesh["bodies"].values() for elem in row["elements"]]
    sets = set_cards("NSET", "CURRENT_ALL_PHYSICAL_NODES", all_nodes)
    sets += set_cards("ELSET", "CURRENT_ALL_ELEMENTS", all_elements)
    sets += set_cards(
        "ELSET",
        "CURRENT_NUT_CARRIERS",
        [elem for row in nuts for elem in row["elements"]],
    )
    deck = (
        "** Current ordinary joint zero-load preflight; provisional stiff engagement.\n"
        "*INCLUDE,INPUT=mesh.inp\n"
        "*INCLUDE,INPUT=materials.inp\n"
        "*INCLUDE,INPUT=nut-coupling.inp\n"
        "*INCLUDE,INPUT=rigid-carriers.inp\n"
        "*INCLUDE,INPUT=contact-fragment.inc\n"
        "*INCLUDE,INPUT=output-sets.inp\n"
        "*INCLUDE,INPUT=gauge.inp\n" + step_cards
    )
    if hashes != {name: sha(path) for name, path in paths.items()}:
        raise ValueError("source changed during native composition")
    destination.mkdir(parents=True, exist_ok=False)
    # The exact immutable source deck is included, not rebuilt or renumbered.
    for name, path in paths.items():
        (destination / name).write_bytes(path.read_bytes())
    for name, text in (
        ("materials.inp", material_text),
        ("rigid-carriers.inp", rigid),
        ("output-sets.inp", sets),
        ("preflight.inp", deck),
    ):
        (destination / name).write_text(text)
    report = {
        "schema": "wood_joint_current_native_preflight/v1",
        "status": "FROZEN_ZERO_LOAD_INPUT_NOT_EXECUTED",
        "source_paths": {
            name: str(path.relative_to(ROOT)) for name, path in paths.items()
        },
        "source_sha256": hashes,
        "step_scope": step_scope,
        "revision": "led-clearance-2x6-runner-seated-blocks-v1",
        "wood_density_kg_per_m3_scenario": 600.0,
        "deformable_metal_density_kg_per_m3_scenario": 7850.0,
        "density_basis": "nominal current board-weight inventory scenarios, unmeasured",
        "rigid_carriers": carriers,
        "solver_image": SOLVER_IMAGE,
        "artifacts_sha256": {p.name: sha(p) for p in destination.iterdir()},
        "limits": [
            "No external load, preload, friction or artificial stabilizing support.",
            "Nut controls assume six-DOF stiff engagement; actual thread fit and transfer unresolved.",
            "Zero carrier density and rigid kinematics must be verified in native output.",
            "A successful zero-load solve is not a unique tangent or a strength pass.",
            "Contact activity and free-mode interpretation require independent output audit.",
        ],
    }
    (destination / "input-freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
