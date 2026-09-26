"""Compare immutable first-knot monitor fields and native energy summaries."""

import hashlib
import json
import math
import re
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SNAPSHOTS = {
    "baseline": (
        "ordinary-transient-aligned-first-knot-snapshot-attempt01",
        "a91a8412e25c92952ab414e5b65e29cb89a6364a9f114a49fa1ef6c7e81d272e",
    ),
    "child": (
        "ordinary-transient-aligned-k1e4-first-knot-snapshot-attempt01",
        "168bf36c4d76b232696bf9099c06ec64d4c464c12ba8a4bd083059238ba9943e",
    ),
}
CONTRACT_SHA = "0d854a2d3d75bd395b00eae3c5b563a00e595b9b38da63d4ceb3d8c637ffd9b7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_snapshot(folder, expected):
    path = BASE / folder
    assert sha(path / "snapshot.json") == expected
    metadata = json.loads((path / "snapshot.json").read_text())
    for name, pin in metadata["files"].items():
        assert sha(path / name) == pin["sha256"], name
    freeze = json.loads((path / "input-freeze.json").read_text())
    pilot = BASE.parents[3] / metadata["source_directory"] / "pilot.inp"
    pilot_sha = sha(pilot)
    assert pilot_sha == freeze["artifacts_sha256"]["pilot.inp"]
    cards = []
    for line in pilot.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            cards.append((line.upper(), []))
        else:
            cards[-1][1].append(line)
    loads = [data for header, data in cards if header.startswith("*CLOAD")]
    ramps = [data for header, data in cards if header == "*AMPLITUDE,NAME=RAMP_N"]
    assert len(loads) == len(ramps) == 1
    assert [h for h, _ in cards if h.startswith("*CLOAD")] == [
        "*CLOAD,AMPLITUDE=RAMP_N"
    ]
    actual_load = {}
    for row in loads[0]:
        node, dof, value = row.split(",")
        key = (int(node), int(dof))
        assert key not in actual_load
        actual_load[key] = float(value)
    unit = {
        (int(node), axis + 1): float(value)
        for node, item in freeze["serialized_unit_load_nodes"].items()
        for axis, value in enumerate(item["force_xyz_n"])
        if float(value) != 0.0
    }
    assert actual_load.keys() == unit.keys()
    scales = [actual_load[key] / unit[key] for key in unit]
    scale = scales[0]
    assert all(math.isclose(s, scale, rel_tol=1e-12) for s in scales)
    ramp = [tuple(float(v) for v in row.split(",")) for row in ramps[0]]
    assert all(len(row) == 2 for row in ramp)
    assert ramp[0] == (0.0, 0.0) and ramp[1][0] == 0.001
    assert all(a[0] < b[0] for a, b in pairwise(ramp))
    load_evidence = {
        "pilot_sha256": pilot_sha,
        "cload_component_count": len(actual_load),
        "reference_pattern_scale_n": scale,
        "first_knot_amplitude": ramp[1][1],
        "first_knot_pattern_force_n": scale * ramp[1][1],
    }
    # CCX *RIGID BODY dummy ROT NODE uses printed U1..U3 as angular
    # coordinates, not physical translations (manual 2.21, section 7.112).
    carriers = BASE.parents[3] / metadata["source_directory"] / "rigid-carriers.inp"
    assert sha(carriers) == freeze["artifacts_sha256"]["rigid-carriers.inp"]
    rotation_ids = [
        int(n)
        for n in re.findall(
            r"^\*RIGID BODY[^\n]*ROT NODE=(\d+)", carriers.read_text(), re.MULTILINE
        )
    ]
    assert sorted(rotation_ids) == sorted(freeze["rotation_nodes"])
    status_rows = [
        line.split()
        for line in (path / "pilot-sta-prefix.txt").read_text().splitlines()
        if line.split() and line.split()[0].isdigit()
    ]
    assert len(status_rows) == 1
    status = status_rows[0]
    assert status[:3] == ["1", "1", "1"] and len(status) == 7
    assert float(status[4]) == float(status[5]) == float(status[6]) == 0.001
    dat = (path / "pilot.dat").read_text()
    headers = list(
        re.finditer(
            r"displacements \(vx,vy,vz\) for set PILOT_MONITOR and time\s+(\S+)", dat
        )
    )
    assert len(headers) == 1 and float(headers[0].group(1)) == 0.001
    nodes = set(freeze["monitor_nodes"])
    rows = {}
    for line in dat[headers[0].end() :].splitlines():
        parts = line.split()
        if not parts and not rows:
            continue
        if len(parts) != 4 or not parts[0].isdigit():
            break
        node = int(parts[0])
        assert node in nodes and node not in rows
        rows[node] = tuple(float(x) for x in parts[1:])
        assert all(math.isfinite(x) for x in rows[node])
        if len(rows) == len(nodes):
            break
    assert set(rows) == nodes
    weights = freeze["serialized_unit_load_nodes"]
    q = math.fsum(
        float(f) * rows[int(n)][i]
        for n, item in weights.items()
        for i, f in enumerate(item["force_xyz_n"])
    )
    assert math.isclose(q, metadata["observation"]["q_mm"], rel_tol=1e-14)
    log = (path / "pilot-log-prefix.txt").read_text()
    since = log.split("since start of the step:")
    assert len(since) == 2
    labels = [
        "external work",
        "internal energy",
        "kinetic energy",
        "elastic contact energy",
        "total energy",
        "energy balance (absolute)",
        "energy balance (relative)",
    ]
    energy = {}
    for label in labels:
        values = re.findall(
            r"^\s*" + re.escape(label) + r"\s*=\s*([-+\d.eE]+)", since[1], re.MULTILINE
        )
        assert len(values) == 1, label
        energy[label] = float(values[0])
    return metadata, freeze, rows, q, energy, load_evidence


def compare_field(a, b, floor, limit):
    assert a.keys() == b.keys()
    difference = {key: abs(b[key] - a[key]) for key in a}
    critical = max(difference, key=difference.get)
    reference_norm = max(abs(x) for x in a.values())
    ratio = difference[critical] / max(reference_norm, floor)
    return {
        "reference_infinity_norm": reference_norm,
        "absolute_infinity_difference": difference[critical],
        "critical_component": str(critical),
        "denominator_floor": floor,
        "normalized_difference": ratio,
        "triage_limit": limit,
        "flag": ratio > limit,
    }


def main():
    assert sha(BASE / "penalty-comparison-contract.md") == CONTRACT_SHA
    a, fa, ua, qa, ea, la = read_snapshot(*SNAPSHOTS["baseline"])
    b, fb, ub, qb, eb, lb = read_snapshot(*SNAPSHOTS["child"])
    assert la == lb
    assert fa["serialized_unit_load_nodes"] == fb["serialized_unit_load_nodes"]
    assert fa["monitor_nodes"] == fb["monitor_nodes"]
    assert fa["rotation_nodes"] == fb["rotation_nodes"]
    checks = {"q_mm": compare_field({"q": qa}, {"q": qb}, 1e-9, 0.05)}
    for name, ids, floor, limit in [
        (
            "loaded_displacement_mm",
            [int(n) for n in fa["serialized_unit_load_nodes"]],
            1e-9,
            0.05,
        ),
        ("controller_rotation_rad", fa["rotation_nodes"], 1e-9, 0.10),
    ]:
        va = {(n, i + 1): ua[n][i] for n in ids for i in range(3)}
        vb = {(n, i + 1): ub[n][i] for n in ids for i in range(3)}
        checks[name] = compare_field(va, vb, floor, limit)
    for label in ["internal energy", "kinetic energy"]:
        checks[label] = compare_field(
            {label: ea[label]}, {label: eb[label]}, 1e-12, 0.10
        )
    branches = {}
    for label, metadata, q, energy in [("baseline", a, qa, ea), ("child", b, qb, eb)]:
        total = sum(
            abs(energy[n])
            for n in ["internal energy", "kinetic energy", "elastic contact energy"]
        )
        ratio = abs(energy["elastic contact energy"]) / max(total, 1e-12)
        branches[label] = {
            "q_mm": q,
            "monitor_summary": metadata["observation"],
            "native_energy_summary": energy,
            "first_increment_discrete_work_nmm": (
                0.5 * la["first_knot_pattern_force_n"] * q
            ),
            "penalty_fraction_of_mechanical_energy": ratio,
            "penalty_fraction_flag_above_5_percent": ratio > 0.05,
        }
    delta_energy_percentage_points = (
        eb["energy balance (relative)"] - ea["energy balance (relative)"]
    )
    result = {
        "scope": "First-knot motion and energy numerical triage only; contact and per-owner momentum comparisons are separate",
        "time_seconds": 0.001,
        "same_single_accepted_first_increment_seconds": 0.001,
        "comparison_contract_sha256": CONTRACT_SHA,
        "snapshot_sha256": {k: v[1] for k, v in SNAPSHOTS.items()},
        "implementation_sha256": sha(Path(__file__)),
        "actual_load_evidence": la,
        "loaded_node_count": len(fa["serialized_unit_load_nodes"]),
        "rotation_node_count": len(fa["rotation_nodes"]),
        "rotation_semantics": "Printed U1..U3 at the four explicitly verified *RIGID BODY ROT NODE IDs are angular coordinates in radians; they are not U translations of physical mesh nodes.",
        "rigid_carriers_sha256": fa["artifacts_sha256"]["rigid-carriers.inp"],
        "branches": branches,
        "field_triage": checks,
        "energy_discrepancy_increase_percentage_points": delta_energy_percentage_points,
        "energy_discrepancy_flag": delta_energy_percentage_points > 0.5
        or eb["energy balance (relative)"] > 2.0,
        "mechanical_acceptance": False,
    }
    (HERE / "report.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "field_triage": checks,
                "energy_discrepancy_flag": result["energy_discrepancy_flag"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
