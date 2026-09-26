"""Add the omitted second-order print-quantization terms to attempt02 bounds.

This reads only the frozen attempt02 snapshot and its pinned contact manifest,
MPC input, and mesh report. It does not assemble mass operators or run a solver.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SNAPSHOT = BASE / "ordinary-finite-actuator-progress-snapshot-attempt02"
REPORT = HERE / "report.json"
OUTPUT = HERE / "rounding-bound-addendum.json"
CLEAT_ID = "W00_BOTTOM_CENTER_RIGHT_CLEAT"
TARGET_NODE = 117163
CONTACT_TIMES = tuple(Decimal(x) for x in ("0.0005", "0.001", "0.0015", "0.002"))

EXPECTED = {
    "audit.py": "d03ee3ea95c00f7137a07cf8d3a5b474bfd5f0c03786686838a66eeb935bbf1f",
    "report.json": "b4a8ada753a7f00a6c1e5a3697d53a25e7cdb1ae07a6bc70a855eec99f2e9f95",
    "parent-execution.json": "83a908620a33fb847b0c2e3943489f4fdb8db89df96aec698afed3deb75da24f",
    "snapshot.json": "e315511717f1da5ea94deeee6b582db0f454280487fc19a1ef6698177c3e2051",
    "pilot.dat": "cede252afb924f93857d26d6a7dd6d2496a210aa3346ab4a2d0d01212e06946b",
    "pilot.sta": "b6bd0ec4e4843d64b9ec308868aa1cb29edf4569fa474f3d68df7352c2f726ec",
    "pilot.inp": "840daddc53194bb2956d214d4e7d83cb69a21a93f3e830ab915f754ebc16791b",
    "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "contact-manifest.json": "e0a698bde664469f2d079ae5d6d98cd89a3b74af735752d3b9d5666d933beee7",
    "contact-audit.json": "9c1d4705f8848cda61fedd17cc18f5099969802e92c355956ffecce433d62cf1",
    "dynamic_momentum.py": "f97f0214a8dcd6ae8e539ed3f1377603031776e1b84235bb5dd058e48fd104e3",
    "wood_joint_mesh_jacobian_audit.py": "3f9cb7768f2ba0efb4e5b26f56222422a09048bfe5e1acdf5ded26f749d861c0",
    "current-work-audit.py": "c43341d3a72904641a973b017e591b02fdc32bc342f192f5148de5746cf212c6",
}

FLOAT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")
DAT_HEADER = re.compile(
    r"^\s*(displacements\s*\(vx,vy,vz\)|forces\s*\(fx,fy,fz\))\s+"
    r"for\s+set\s+(\S+)\s+and\s+time\s+(\S+)\s*$",
    re.IGNORECASE,
)
CONTACT_HEADER = re.compile(
    r"^\s*statistics for slave set\s+(WJCP_(\d{3})_S),\s*master set\s+"
    r"(WJCP_\d{3}_M)\s+and time\s+([0-9.EeDd+\-]+)\s*$",
    re.IGNORECASE,
)
CF_LABEL = "total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path, expected: str, label: str) -> str:
    value = digest(path.read_bytes())
    if value != expected:
        raise ValueError(f"{label} pin mismatch: {value} != {expected}")
    return value


def number(token: str) -> tuple[Decimal, Decimal]:
    if not FLOAT.fullmatch(token):
        raise ValueError(f"invalid numeric token: {token!r}")
    value = Decimal(token.replace("D", "E").replace("d", "e"))
    if not value.is_finite():
        raise ValueError(f"non-finite numeric token: {token!r}")
    half_quantum = abs(Decimal(5).scaleb(value.as_tuple().exponent - 1))
    return value, half_quantum


def finalize_driver(block: dict[str, Any] | None, rows: dict) -> None:
    if block is None:
        return
    if TARGET_NODE not in rows:
        return
    time_value, time_q = block["time"]
    target = rows[TARGET_NODE]
    record = {"time": time_value, "time_half_quantum": time_q, "rf": target[0][0], "rf_half_quantum": target[0][1]}
    if time_value in DRIVER_ROWS:
        raise ValueError(f"duplicate target-force record at {time_value}")
    DRIVER_ROWS[time_value] = record


DRIVER_ROWS: dict[Decimal, dict[str, Decimal]] = {}


def parse_frozen_dat(path: Path, expected_sha: str, cleat_signs: dict[int, int]) -> tuple[dict, dict]:
    """Stream only actuator target RF and requested complete-contact CF tokens."""
    hasher = hashlib.sha256()
    driver_block = None
    driver_rows: dict[int, tuple[tuple[Decimal, Decimal], ...]] = {}
    contact_block = None
    contact_counts: dict[tuple[Decimal, int], int] = defaultdict(int)
    contact_rows: dict[tuple[Decimal, int], dict[str, Any]] = {}

    def finish_contact() -> None:
        nonlocal contact_block
        if not contact_block or not contact_block["selected"]:
            contact_block = None
            return
        force = contact_block.get("force")
        if force is None:
            raise ValueError("selected first-request CF block has no total-force row")
        key = (contact_block["time"], contact_block["pair"])
        if key in contact_rows:
            raise ValueError(f"duplicate selected CF result for {key}")
        contact_rows[key] = {
            "force": [x[0] for x in force],
            "force_half_quantum": [x[1] for x in force],
            "time_half_quantum": contact_block["time_half_quantum"],
        }
        contact_block = None

    def finish_driver() -> None:
        nonlocal driver_block, driver_rows
        finalize_driver(driver_block, driver_rows)
        driver_block = None
        driver_rows = {}

    with path.open("rb") as stream:
        for raw in stream:
            hasher.update(raw)
            line = raw.decode("ascii").rstrip("\r\n")

            dat_match = DAT_HEADER.fullmatch(line)
            if dat_match:
                finish_driver()
                field, set_name, time_token = dat_match.groups()
                value, half_quantum = number(time_token)
                if field.lower().startswith("forces") and set_name.upper() == "ACTUATOR_DRIVER":
                    driver_block = {"time": (value, half_quantum)}
                continue

            contact_match = CONTACT_HEADER.fullmatch(line)
            if contact_match:
                finish_contact()
                if driver_block is not None:
                    finish_driver()
                slave, pair_digits, master, time_token = contact_match.groups()
                pair = int(pair_digits)
                time_value, time_half_quantum = number(time_token)
                if slave.upper() != f"WJCP_{pair:03d}_S" or master.upper() != f"WJCP_{pair:03d}_M":
                    raise ValueError(f"contact owner-set names disagree for pair {pair}")
                key = (time_value, pair)
                slot = contact_counts[key] % 3
                contact_counts[key] += 1
                contact_block = {
                    "pair": pair,
                    "time": time_value,
                    "time_half_quantum": time_half_quantum,
                    "selected": time_value in CONTACT_TIMES and pair in cleat_signs and slot == 0,
                    "awaiting_force": False,
                    "force": None,
                }
                continue

            if driver_block is not None:
                stripped = line.strip()
                if stripped:
                    fields = stripped.split()
                    if len(fields) == 4 and fields[0].isdigit() and all(FLOAT.fullmatch(x) for x in fields[1:]):
                        node = int(fields[0])
                        if node in driver_rows:
                            raise ValueError(f"duplicate ACTUATOR_DRIVER node row: {node}")
                        driver_rows[node] = tuple(number(x) for x in fields[1:])
                    elif driver_rows:
                        finish_driver()
                elif driver_rows:
                    finish_driver()

            if contact_block and contact_block["selected"]:
                if CF_LABEL in line.lower():
                    contact_block["awaiting_force"] = True
                    continue
                if contact_block["awaiting_force"] and line.strip():
                    fields = line.split()
                    if len(fields) != 6 or not all(FLOAT.fullmatch(x) for x in fields):
                        raise ValueError("malformed numeric CF row in a selected contact block")
                    contact_block["force"] = [number(x) for x in fields[:3]]
                    contact_block["awaiting_force"] = False

    finish_driver()
    finish_contact()
    if hasher.hexdigest() != expected_sha:
        raise ValueError(f"pilot.dat pin mismatch: {hasher.hexdigest()} != {expected_sha}")
    for time in CONTACT_TIMES:
        for pair in range(1, 36):
            if contact_counts[(time, pair)] != 3:
                raise ValueError(f"incomplete CF/CFN/CFS triplet coverage at {time}, pair {pair}")
    return DRIVER_ROWS.copy(), contact_rows


def read_mpc_weights(deck_path: Path, expected_sha: str, mesh_report_path: Path, mesh_sha: str) -> tuple[list[Decimal], list[Decimal]]:
    file_hash(deck_path, EXPECTED["pilot.inp"], "pilot.inp")
    mesh_raw = mesh_report_path.read_bytes()
    if digest(mesh_raw) != mesh_sha or mesh_sha != EXPECTED["mesh.json"]:
        raise ValueError("mesh report pin mismatch")
    mesh = json.loads(mesh_raw)
    cleat_nodes = {int(x) for x in mesh["bodies"][CLEAT_ID]["nodes"]}
    text = deck_path.read_text(encoding="ascii")
    lines = text.splitlines()
    positions = [i for i, line in enumerate(lines) if line.strip().upper() == "*EQUATION"]
    if len(positions) != 1:
        raise ValueError("pilot input must contain one serialized *EQUATION")
    position = positions[0] + 1
    count = int(lines[position].strip())
    fields = []
    for raw in lines[position + 1:]:
        if raw.lstrip().startswith("*"):
            break
        if raw.strip():
            fields.extend(x.strip() for x in raw.split(",") if x.strip())
    if len(fields) != 3 * count or count != 663:
        raise ValueError("serialized equation term count changed")
    sums_global = [Decimal(0), Decimal(0), Decimal(0)]
    sums_cleat = [Decimal(0), Decimal(0), Decimal(0)]
    seen = set()
    for i in range(0, len(fields), 3):
        node = int(fields[i])
        dof = int(fields[i + 1])
        coefficient, _ = number(fields[i + 2])
        key = (node, dof)
        if key in seen:
            raise ValueError(f"duplicate serialized MPC term {key}")
        seen.add(key)
        if key == (117162, 1):
            if coefficient != Decimal(1):
                raise ValueError("proxy coefficient differs from +1")
            continue
        weight = -coefficient
        if dof in (1, 2, 3):
            sums_global[dof - 1] += weight
            if node in cleat_nodes:
                sums_cleat[dof - 1] += weight
    if len(seen) != count:
        raise ValueError("serialized MPC term count has duplicates")
    return sums_global, sums_cleat


def main() -> None:
    file_hash(HERE / "audit.py", EXPECTED["audit.py"], "attempt02 audit producer")
    file_hash(REPORT, EXPECTED["report.json"], "attempt02 report")
    exec_sha = file_hash(HERE / "parent-execution.json", EXPECTED["parent-execution.json"], "parent execution record")
    snapshot_sha = file_hash(SNAPSHOT / "snapshot.json", EXPECTED["snapshot.json"], "snapshot manifest")
    sta_sha = file_hash(SNAPSHOT / "pilot.sta", EXPECTED["pilot.sta"], "pilot.sta")
    dat_sha = EXPECTED["pilot.dat"]
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    execution = json.loads((HERE / "parent-execution.json").read_text(encoding="utf-8"))
    if report["mechanical_acceptance"] is not False or execution["native_solver_run"] is not False:
        raise ValueError("source report or execution record does not withhold acceptance/native run")
    if execution["source_and_result_sha256"].get("fea/dynamic_momentum.py") != EXPECTED["dynamic_momentum.py"]:
        raise ValueError("parent execution did not bind the mass integration helper")
    if execution["source_and_result_sha256"].get("fea/wood_joint_mesh_jacobian_audit.py") != EXPECTED["wood_joint_mesh_jacobian_audit.py"]:
        raise ValueError("parent execution did not bind the mesh parser helper")
    if report["provenance"]["verified_sha256"].get("pilot_dat") != dat_sha:
        raise ValueError("report DAT hash differs")

    snapshot_freeze = json.loads((SNAPSHOT / "input-freeze.json").read_text(encoding="utf-8"))
    source_base = Path(snapshot_freeze["source_lineage"]["base_dir"])
    manifest_path = source_base / "contact-manifest.json"
    manifest_sha = file_hash(manifest_path, EXPECTED["contact-manifest.json"], "contact manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contact_audit_path = HERE.parent / "finite-actuator-progress-contact-audit-attempt02/contact-audit.json"
    contact_audit_sha = file_hash(contact_audit_path, EXPECTED["contact-audit.json"], "canonical contact-output audit")
    contact_audit = json.loads(contact_audit_path.read_text(encoding="utf-8"))
    if contact_audit.get("provenance", {}).get("child_pilot_dat_sha256") != EXPECTED["pilot.dat"]:
        raise ValueError("canonical contact-output audit is not bound to frozen DAT")
    pairs = manifest.get("pairs", [])
    if len(pairs) != 35:
        raise ValueError("contact manifest does not contain the pinned 35 pairs")
    for item in report["contact_owner_interfaces_on_cleat"]:
        pair = pairs[item["pair_index"] - 1]
        if pair["pair_id"] != item["pair_id"] or pair["master_owner"] != item["master_owner"] or pair["slave_owner"] != item["slave_owner"]:
            raise ValueError("report cleat ownership differs from pinned contact manifest")

    states = report["states"]
    accepted_times = [number(state["accepted_time_token"]) for state in states]
    drivers, contact = parse_frozen_dat(
        SNAPSHOT / "pilot.dat", dat_sha,
        {int(row["pair_index"]): int(row["cleat_contact_force_sign_from_CF_on_slave"]) for row in report["contact_owner_interfaces_on_cleat"]},
    )
    if len(drivers) != len(states):
        raise ValueError(f"expected {len(states)} driver force times, found {len(drivers)}")
    for state, (time, _q) in zip(states, accepted_times, strict=True):
        row = drivers.get(time)
        if row is None:
            raise ValueError(f"no unique ACTUATOR_DRIVER target RF at {time}")
        if float(row["rf"]) != state["actuator_target_RF_n"] or float(row["rf_half_quantum"]) != state["actuator_target_RF_half_quantum_n"]:
            raise ValueError(f"target RF tokens differ from the attempt02 report at {time}")

    pair_signs = {int(row["pair_index"]): int(row["cleat_contact_force_sign_from_CF_on_slave"]) for row in report["contact_owner_interfaces_on_cleat"]}
    contact_force_by_state: dict[Decimal, list[Decimal]] = {}
    contact_eps_by_state: dict[Decimal, list[Decimal]] = {}
    contact_time_q_by_state: dict[Decimal, Decimal] = {}
    for time in CONTACT_TIMES:
        forces = [Decimal(0), Decimal(0), Decimal(0)]
        eps = [Decimal(0), Decimal(0), Decimal(0)]
        time_quanta = []
        for pair, sign in pair_signs.items():
            row = contact.get((time, pair))
            if row is None:
                raise ValueError(f"missing CF token row for {time}, pair {pair}")
            for axis in range(3):
                forces[axis] += sign * row["force"][axis]
                eps[axis] += row["force_half_quantum"][axis]
            time_quanta.append(row["time_half_quantum"])
        if len([key for key in contact if key[0] == time]) < len(pair_signs):
            raise ValueError(f"incomplete cleat CF coverage at {time}")
        contact_force_by_state[time] = forces
        contact_eps_by_state[time] = eps
        contact_time_q_by_state[time] = max(time_quanta)

    # The emitted MPC card and the mesh-report cleat node set reproduce the
    # exact generalized-force weights used by attempt02, without mass assembly.
    weights_global, weights_cleat = read_mpc_weights(
        SNAPSHOT / "pilot.inp", EXPECTED["pilot.inp"],
        source_base / "mesh.json", EXPECTED["mesh.json"],
    )
    for i, state in enumerate(states):
        for weight_set, key in ((weights_global, "actuator_generalized_force_resultant_global_n"), (weights_cleat, "actuator_generalized_force_resultant_cleat_n")):
            rf = Decimal(str(state["actuator_target_RF_n"]))
            for axis in range(3):
                if abs(float(rf * weight_set[axis]) - state[key][axis]) > 2e-15:
                    raise ValueError(f"serialized MPC weight reconstruction differs at state {i}, axis {axis}")

    intervals = []
    for interval_index, report_interval in enumerate(report["accepted_intervals"]):
        t0, t1 = accepted_times[interval_index][0], accepted_times[interval_index + 1][0]
        status_q0, status_q1 = accepted_times[interval_index][1], accepted_times[interval_index + 1][1]
        dat0, dat1 = drivers[t0], drivers[t1]
        dt = t1 - t0
        rf_avg_half_quantum = (dat0["rf_half_quantum"] + dat1["rf_half_quantum"]) / 2
        actuator_dt_bound = status_q0 + status_q1 + dat0["time_half_quantum"] + dat1["time_half_quantum"]
        actuator_cross_global = [abs(w) * actuator_dt_bound * rf_avg_half_quantum for w in weights_global]
        actuator_cross_cleat = [abs(w) * actuator_dt_bound * rf_avg_half_quantum for w in weights_cleat]

        row: dict[str, Any] = {
            "start_time_seconds": float(t0),
            "end_time_seconds": float(t1),
            "actuator": {
                "accepted_dt_seconds": str(dt),
                "combined_endpoint_time_half_quantum_seconds": str(actuator_dt_bound),
                "average_target_rf_half_quantum_n": str(rf_avg_half_quantum),
                "physical_weight_global_xyz": [str(x) for x in weights_global],
                "physical_weight_cleat_xyz": [str(x) for x in weights_cleat],
                "omitted_product_cross_term_global_n_s": [str(x) for x in actuator_cross_global],
                "omitted_product_cross_term_cleat_n_s": [str(x) for x in actuator_cross_cleat],
            },
            "global_all_positive_mass_bodies": {},
            "cleat_complete_contact_coverage": bool(report_interval["cleat_complete_contact_coverage"]),
            "cleat_balance": None,
        }
        for operator, result in report_interval["global_all_positive_mass_bodies"].items():
            original = result["output_rounding_bound_n_s"]
            corrected = [original[a] + float(actuator_cross_global[a]) for a in range(3)]
            residual = result["balance_residual_n_s"]
            row["global_all_positive_mass_bodies"][operator] = {
                "first_order_reported_bound_n_s": original,
                "omitted_cross_term_added_n_s": [float(x) for x in actuator_cross_global],
                "corrected_bound_n_s": corrected,
                "balance_residual_n_s": residual,
                "within_corrected_bound": [abs(residual[a]) <= corrected[a] for a in range(3)],
            }

        if report_interval["cleat_complete_contact_coverage"]:
            eps0 = contact_eps_by_state[t0]
            eps1 = contact_eps_by_state[t1]
            contact_avg_half_quantum = [(eps0[a] + eps1[a]) / 2 for a in range(3)]
            contact_dt_bound = status_q0 + status_q1 + contact_time_q_by_state[t0] + contact_time_q_by_state[t1]
            contact_cross = [contact_dt_bound * x for x in contact_avg_half_quantum]
            row["contact"] = {
                "endpoint_cleat_force_n": [[str(x) for x in contact_force_by_state[t0]], [str(x) for x in contact_force_by_state[t1]]],
                "endpoint_cleat_force_half_quantum_sum_n": [[str(x) for x in eps0], [str(x) for x in eps1]],
                "combined_endpoint_time_half_quantum_seconds": str(contact_dt_bound),
                "average_force_half_quantum_n": [str(x) for x in contact_avg_half_quantum],
                "omitted_product_cross_term_n_s": [str(x) for x in contact_cross],
            }
            row["cleat_balance"] = {}
            for operator, result in report_interval["cleat_balance"].items():
                original = result["output_rounding_bound_n_s"]
                corrected = [original[a] + float(actuator_cross_cleat[a] + contact_cross[a]) for a in range(3)]
                residual = result["balance_residual_n_s"]
                row["cleat_balance"][operator] = {
                    "first_order_reported_bound_n_s": original,
                    "omitted_actuator_cross_term_added_n_s": [float(x) for x in actuator_cross_cleat],
                    "omitted_contact_cross_term_added_n_s": [float(x) for x in contact_cross],
                    "corrected_bound_n_s": corrected,
                    "balance_residual_n_s": residual,
                    "within_corrected_bound": [abs(residual[a]) <= corrected[a] for a in range(3)],
                }
        intervals.append(row)

    source_hashes = {
        "rounding_bound_addendum.py": digest(Path(__file__).read_bytes()),
        "audit.py": EXPECTED["audit.py"],
        "report.json": EXPECTED["report.json"],
        "parent-execution.json": exec_sha,
        "snapshot.json": snapshot_sha,
        "pilot.dat": dat_sha,
        "pilot.sta": sta_sha,
        "pilot.inp": EXPECTED["pilot.inp"],
        "mesh.json": EXPECTED["mesh.json"],
        "contact-manifest.json": manifest_sha,
        "finite-actuator-progress-contact-audit-attempt02/contact-audit.json": contact_audit_sha,
        "fea/dynamic_momentum.py": EXPECTED["dynamic_momentum.py"],
        "fea/wood_joint_mesh_jacobian_audit.py": EXPECTED["wood_joint_mesh_jacobian_audit.py"],
        "current-finite-actuator-work-audit-attempt03/audit.py": EXPECTED["current-work-audit.py"],
    }
    output = {
        "schema": "wood_joint_finite_actuator_momentum_rounding_bound_addendum/v1",
        "status": "SECOND_ORDER_OUTPUT_PRINT_CROSS_TERMS_INCLUDED",
        "mechanical_acceptance": False,
        "scope": {
            "parent_report_status": report["status"],
            "interpretation": "Original attempt02 output bounds are first-order product-propagation bounds. This addendum adds the omitted delta_time times delta_force cross term from the same frozen print-token intervals.",
            "actuator_formula": "cross = |w| * delta_t * delta_RF_average, with delta_RF_average=(epsilon_RF0+epsilon_RF1)/2 and delta_t=sum of both accepted .sta and DAT time half-quanta at the endpoints.",
            "contact_formula": "cross = delta_t * delta_F_average, with delta_F_average=(epsilon_F0+epsilon_F1)/2 and epsilon_Fi equal to the sum of the ten cleat-side CF component half-quanta; delta_t includes accepted .sta and CF report time half-quanta.",
            "limits": ["No mass operators were integrated by this addendum.", "No native solver or CAD was run.", "This corrects print-token product propagation only; it does not bound between-increment force variation, solver equilibrium residual, model uncertainty, or joint acceptance."],
        },
        "source_sha256": source_hashes,
        "intervals": intervals,
    }
    encoded = (json.dumps(output, indent=2, sort_keys=True) + "\n").encode("utf-8")
    OUTPUT.write_bytes(encoded)
    print(json.dumps({"output": str(OUTPUT), "sha256": digest(encoded), "interval_count": len(intervals)}, indent=2))


if __name__ == "__main__":
    main()
