"""Prepare, but never launch, the two-branch RF/opening method fixture."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
NATIVE = OUT / "native"
sys.path.insert(0, str(ROOT))

import numpy as np

from fea import horizontal_panel_frame as frame
from fea import wood_joint_reduced_native as native
from fea.round_insert_frame import normal_contact
from fea.wood_joint_reduced_force_output import _check_spring_isolation


K_CONTACT_N_PER_MM = 179183.109378
K_HOST_SUPPORT_N_PER_MM = 1_000_000.0
THRESHOLD_MM = 1.0e-7
BRANCHES = (
    {"id": "below", "opening_mm": 0.9e-7, "x_mm": 0.0},
    {"id": "above", "opening_mm": 1.1e-7, "x_mm": 1000.0},
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if NATIVE.exists():
        raise FileExistsError(f"Refusing to replace existing fixture freeze: {NATIVE}")

    model = frame.Structure()
    owners = {}
    branch_rows = []
    partial_fixed_dofs = {}

    for branch in BRANCHES:
        tag = branch["id"]
        point = [float(branch["x_mm"]), 0.0, 0.0]
        wood_host = model.node(point)
        panel_host = model.node(point)
        endpoints = normal_contact(
            model, f"contact_{tag}", wood_host, [panel_host], [1.0], point,
            [0.0, 0.0, 1.0], K_CONTACT_N_PER_MM,
        )
        support_anchor = model.node(point)
        model.spring(panel_host, support_anchor, K_HOST_SUPPORT_N_PER_MM,
                     f"host_support_{tag}", dofs=(3,))

        # Host relative motion is solved from the two parallel stiffness paths:
        # P = -(K_contact + K_host) * opening, giving panel-host U3=-opening.
        force_n = -(K_CONTACT_N_PER_MM + K_HOST_SUPPORT_N_PER_MM) * branch["opening_mm"]
        model.fixed.update((wood_host, support_anchor))
        model.loads[panel_host] = [0.0, 0.0, force_n]
        partial_fixed_dofs[str(panel_host)] = [1, 2]

        contact_name = f"contact_{tag}"
        support_name = f"host_support_{tag}"
        owners[contact_name] = {
            "first": f"wood_host_{tag}", "second": f"panel_host_{tag}",
            "point": point, "scalar_normal": [0.0, 0.0, 1.0],
        }
        owners[support_name] = {
            "first": f"panel_host_{tag}", "second": f"support_anchor_{tag}",
            "point": point, "force_basis": np.eye(3).tolist(),
        }
        branch_rows.append({
            **branch,
            "wood_host_node": wood_host,
            "panel_host_node": panel_host,
            "contact_endpoint_nodes": endpoints,
            "host_support_anchor_node": support_anchor,
            "contact_spring_name": contact_name,
            "host_support_spring_name": support_name,
            "host_load_node": panel_host,
            "host_load_dof": 3,
            "host_load_n": force_n,
            "expected_host_relative_u3_mm": -branch["opening_mm"],
            "expected_contact_force_on_first_n": -K_CONTACT_N_PER_MM * branch["opening_mm"],
        })

    model.rotation_masters.update(
        node for row in branch_rows for node in row["contact_endpoint_nodes"]
    )

    metadata = {
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "Two disconnected zero-offset normal-contact RF-to-opening known-answer branches; method check only",
        "connection_ownership": owners,
        "fixture_method": "Host-side CLOAD against a host-only support SPRING2 in parallel with the isolated normal_contact SPRING2",
        "contact_stiffness_n_per_mm": K_CONTACT_N_PER_MM,
        "host_support_stiffness_n_per_mm": K_HOST_SUPPORT_N_PER_MM,
        "opening_threshold_mm": THRESHOLD_MM,
        "branches": branch_rows,
        "host_partial_fixed_dofs": partial_fixed_dofs,
        "contact_endpoint_policy": "The two contact auxiliary DOF-1 endpoints per branch occur in the normal_contact MPC projection and exactly one contact SPRING2; they have no direct CLOAD or *BOUNDARY entry. Host support SPRING2 DOF 3 uses host nodes and remains separate from contact auxiliary DOF 1.",
        "native_solve_executed": False,
        "mechanical_acceptance": False,
    }

    deck = model.deck()
    before, rest = deck.split("*BOUNDARY\n", 1)
    _, after = rest.split("*STEP\n", 1)
    boundary_lines = [f"{node},1,3,0" for node in sorted(model.fixed)]
    boundary_lines.extend(f"{node},{dof},{dof},0" for node_text, dofs in partial_fixed_dofs.items()
                          for node, dof in [(int(node_text), value) for value in dofs])
    deck = before + "*BOUNDARY\n" + "\n".join(boundary_lines) + "\n*STEP\n" + after

    # Freeze the source helper and exact projection implementation alongside the deck.
    packet = native.freeze(
        NATIVE, model, metadata,
        extra_sources=(
            ROOT / "fea/round_insert_frame.py",
            ROOT / "fea/horizontal_panel_frame.py",
            ROOT / "fea/wood_joint_reduced_force_output.py",
            ROOT / "fea/current_response_run.py",
        ),
        deck_text=deck,
    )
    record = json.loads((NATIVE / "model.json").read_text())
    endpoint_map = _check_spring_isolation(record)

    contact_endpoint_nodes = {
        node for row in branch_rows for node in row["contact_endpoint_nodes"]
    }
    loaded_dofs = {
        (int(node), dof + 1)
        for node, vector in record["loads"].items()
        for dof, value in enumerate(vector) if abs(value) > 0.0
    }
    fixed_dofs = {
        (node, dof) for node in record["fixed_nodes"] for dof in (1, 2, 3)
    }
    fixed_dofs.update(
        (int(node), dof) for node, dofs in partial_fixed_dofs.items() for dof in dofs
    )
    contact_endpoint_dofs = {
        (node, 1) for node in contact_endpoint_nodes
    }
    assert not (contact_endpoint_dofs & loaded_dofs)
    assert not (contact_endpoint_dofs & fixed_dofs)
    assert len(endpoint_map) == 8

    preparation = {
        "schema": "rf_opening_known_answer_preparation/v1",
        "fixture_directory": str(OUT.relative_to(ROOT)),
        "native_directory": str(NATIVE.relative_to(ROOT)),
        "input_freeze_sha256": sha256(NATIVE / "freeze.json"),
        "deck_sha256": sha256(NATIVE / "model.inp"),
        "model_sha256": sha256(NATIVE / "model.json"),
        "solver_profile": packet["solver_profile"],
        "source_sha256": packet["source_sha256"],
        "branches": branch_rows,
        "contact_endpoint_dofs_isolated": True,
        "contact_endpoint_dofs_directly_loaded": False,
        "contact_endpoint_dofs_directly_supported": False,
        "native_solve_executed": False,
        "native_ledger_entry": "Required once, through the parent serialized native runner, after independent pre-run review of this exact freeze.",
        "ready_to_launch": False,
    }
    (OUT / "preparation.json").write_text(json.dumps(preparation, indent=2, sort_keys=True) + "\n")

    pins = {
        name: packet["source_sha256"][name]
        for name in (
            "fea/calculix_223/solver-profile.json",
            "fea/round_insert_frame.py",
            "fea/horizontal_panel_frame.py",
            "fea/wood_joint_reduced_force_output.py",
            "fea/current_response_run.py",
        )
    }
    print(json.dumps({
        "input_freeze_sha256": preparation["input_freeze_sha256"],
        "deck_sha256": preparation["deck_sha256"],
        "source_pins": pins,
        "native_solve_executed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
