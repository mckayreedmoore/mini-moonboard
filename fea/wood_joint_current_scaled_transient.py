"""Freeze a separate 100x clearance-seating diagnostic from the pinned pilot.

Only existing serialized CLOAD components change. The original unit load
weights continue to define q; actual load vectors are recorded separately.
No native execution, geometry change, or response acceptance is performed.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal
from pathlib import Path

from fea.wood_joint_current_native_preflight import BASE, ROOT, sha
from fea.wood_joint_current_transient import numeric

PARENT_FREEZE_SHA = "77090f458d68afc20abfa34203496527030d075c96868ae99d2aed7091043e66"
SCALE = Decimal(100)


def scale_cloads(deck, unit_nodes):
    """Scale each original term exactly, checking against the unit observer."""
    active = False
    blocks = 0
    observed = {}
    output = []
    for line in deck.splitlines():
        if line.startswith("*") and not line.startswith("**"):
            active = line.split(",", 1)[0].upper() == "*CLOAD"
            if active:
                if line != "*CLOAD,AMPLITUDE=RAMP_N":
                    raise ValueError("unexpected CLOAD options")
                blocks += 1
        elif active and line.strip() and not line.startswith("**"):
            fields = line.split(",")
            if len(fields) != 3:
                raise ValueError("unexpected CLOAD record")
            node, dof = int(fields[0]), int(fields[1])
            key = (node, dof)
            if key in observed or dof not in (1, 2, 3):
                raise ValueError("duplicate or invalid CLOAD degree of freedom")
            original = Decimal(fields[2])
            if not original.is_finite():
                raise ValueError("nonfinite CLOAD")
            expected = unit_nodes.get(str(node), {}).get("force_xyz_n")
            if expected is None or float(original) != expected[dof - 1]:
                raise ValueError("CLOAD does not match frozen unit observation")
            scaled = original * SCALE
            token = numeric(float(scaled))
            if Decimal(token) != scaled:
                raise ValueError("scaled CLOAD cannot be serialized exactly")
            observed[key] = float(scaled)
            line = f"{node},{dof},{token}"
        output.append(line)
    expected_keys = {
        (int(node), dof)
        for node, row in unit_nodes.items()
        for dof, force in enumerate(row["force_xyz_n"], 1)
        if force != 0
    }
    if blocks != 1 or set(observed) != expected_keys:
        raise ValueError("missing or extra applied load terms")
    actual = {
        node: [observed.get((int(node), dof), 0.0) for dof in (1, 2, 3)]
        for node in unit_nodes
    }
    return "\n".join(output) + "\n", actual


def prepare(destination):
    source = BASE / "ordinary-transient-pilot-attempt04"
    parent_file = source / "input-freeze.json"
    if sha(parent_file) != PARENT_FREEZE_SHA:
        raise ValueError("unexpected parent input freeze")
    parent = json.loads(parent_file.read_text())
    pins = parent["artifacts_sha256"]
    if not all(sha(source / name) == digest for name, digest in pins.items()):
        raise ValueError("parent inputs changed")
    deck, actual = scale_cloads(
        (source / "pilot.inp").read_text(), parent["serialized_unit_load_nodes"]
    )
    if sum(value != 0 for row in actual.values() for value in row) != 662:
        raise ValueError("expected the frozen 662 nonzero load terms")
    net_force = [math.fsum(row[a] for row in actual.values()) for a in range(3)]
    net_moment = []
    for axis in range(3):
        j, k = (axis + 1) % 3, (axis + 2) % 3
        net_moment.append(
            math.fsum(
                parent["serialized_unit_load_nodes"][node]["point_xyz_mm"][j] * force[k]
                - parent["serialized_unit_load_nodes"][node]["point_xyz_mm"][k]
                * force[j]
                for node, force in actual.items()
            )
        )
    if max(map(abs, net_force)) > 1e-9 or max(map(abs, net_moment)) > 1e-7:
        raise ValueError("scaled serialized applied wrench does not close")
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    for name in pins:
        (destination / name).write_bytes((source / name).read_bytes())
    (destination / "pilot.inp").write_text(deck)
    (destination / "parent-input-freeze.json").write_bytes(parent_file.read_bytes())
    (destination / "scale-producer.py.snapshot").write_bytes(
        Path(__file__).read_bytes()
    )
    report = dict(parent)
    report.update(
        status="FROZEN_NOT_EXECUTED",
        parent_input_freeze_sha256=PARENT_FREEZE_SHA,
        cload_reference_scale=100,
        cload_reference_force_n=100,
        amplitude_table_peak_factor=1,
        serialized_actual_cload_nodes_n=actual,
        serialized_unit_net_force_n=parent["serialized_net_force_n"],
        serialized_unit_initial_net_moment_nmm=parent[
            "serialized_initial_net_moment_nmm"
        ],
        serialized_net_force_n=net_force,
        serialized_initial_net_moment_nmm=net_moment,
        final_amplitude_n=parent["final_amplitude_n"] * 100,
        final_amplitude_table_factor=parent["final_amplitude_n"],
        step_scope=(
            "Separate gauge-free 100 N reference-amplitude clearance-seating "
            "diagnostic; 15.625 N per side at 0.025 s, sampled cubic rise over "
            "0.1 s. Provisional stiff engagement; no service, capacity, "
            "quasistatic or time-accuracy acceptance."
        ),
        derivative_operation=(
            "Each of the 662 existing serialized CLOAD terms multiplied exactly "
            "by 100; all other input cards unchanged. Original unit weights "
            "still define q and sampled-motion stops."
        ),
        source_paths={name: str((source / name).relative_to(ROOT)) for name in pins},
        source_sha256=dict(pins),
    )
    report["source_paths"]["parent-input-freeze.json"] = str(
        parent_file.relative_to(ROOT)
    )
    report["source_sha256"]["parent-input-freeze.json"] = PARENT_FREEZE_SHA
    report["source_paths"]["scale-producer.py.snapshot"] = str(
        Path(__file__).relative_to(ROOT)
    )
    report["source_sha256"]["scale-producer.py.snapshot"] = sha(Path(__file__))
    report["limits"] = list(parent["limits"]) + [
        "Coarse initial increment crosses ramp knots; impulse/time resolution remains unqualified.",
        "Linear free-travel extrapolation is not a prediction after contact activates.",
        "Per-bore closure and transfer, actual scaled-load work and momentum require audit.",
    ]
    report["artifacts_sha256"] = {
        name: sha(destination / name)
        for name in [*pins, "parent-input-freeze.json", "scale-producer.py.snapshot"]
    }
    if sha(parent_file) != PARENT_FREEZE_SHA or not all(
        sha(source / name) == digest for name, digest in pins.items()
    ):
        raise ValueError("parent inputs changed during freeze")
    (destination / "input-freeze.json").write_text(json.dumps(report, indent=2) + "\n")
    return {
        "input_freeze_sha256": sha(destination / "input-freeze.json"),
        "pilot_sha256": report["artifacts_sha256"]["pilot.inp"],
        "changed_load_terms": 662,
        "final_force_per_side_n": report["final_amplitude_n"],
        "status": report["status"],
    }
