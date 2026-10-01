"""Assess a parent-run two-body relative-coordinate SPRINGA method coupon."""
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE / "native"


def _near(label, actual, expected, tolerance):
    if not math.isfinite(actual) or abs(actual - expected) > tolerance:
        raise AssertionError(
            f"{label}: actual={actual!r}, expected={expected!r}, tolerance={tolerance}"
        )


def _native_blocks(data):
    blocks = {}
    pattern = r"^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n"
    for match in re.finditer(pattern, data, re.MULTILINE):
        rows = {}
        started = False
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                if node in rows:
                    raise AssertionError(f"Duplicate node {node} in printed block")
                rows[node] = [float(v.replace("D", "E").replace("d", "e")) for v in fields[1:]]
                started = True
            elif started:
                break
        time = float(match.group(2).replace("D", "E").replace("d", "e"))
        key = (match.group(1), time)
        if key in blocks:
            raise AssertionError(f"Duplicate native output block {key}")
        blocks[key] = rows
    return blocks


def evaluate():
    freeze_path = NATIVE / "freeze.json"
    freeze = json.loads(freeze_path.read_text())
    for name, pin in freeze["files_sha256"].items():
        if hashlib.sha256((NATIVE / name).read_bytes()).hexdigest() != pin:
            raise AssertionError(f"Frozen input hash mismatch: {name}")

    execution = json.loads((NATIVE / "execution.json").read_text())
    if execution.get("native_solve_executed") is not True or execution.get("returncode") != 0:
        raise AssertionError("Native execution did not terminate successfully")
    native_stdout = (NATIVE / "native.stdout").read_text()
    native_stderr = (NATIVE / "native.stderr").read_text()
    output = native_stdout + native_stderr
    if "*ERROR" in output.upper():
        raise AssertionError("Native output contains a solver error")
    normalized_stdout = " ".join(native_stdout.lower().split())
    if "newton-raphson iterative procedure is active" not in normalized_stdout:
        raise AssertionError("Newton-Raphson iteration was not reported active")
    if normalized_stdout.count("effects are turned off") < 3:
        raise AssertionError("Geometric effects were not reported off for all three steps")
    if "nonlinear geometric effects are taken into account" in normalized_stdout:
        raise AssertionError("Solver reported nonlinear geometric effects active")

    model = json.loads((NATIVE / "model.json").read_text())
    blocks = _native_blocks((NATIVE / "model.dat").read_text())
    node_ids = {name: int(tag) for tag, name in model["node_roles"].items()}
    node_set = set(map(int, model["nodes"]))
    tolerance_u = float(model["tolerances"]["u_abs_mm"])
    tolerance_f = float(model["tolerances"]["force_abs_N"])
    stiffness = {row["name"]: float(row["stiffness_N_per_mm"])
                 for row in model["support_springs"]}
    result_steps = []

    for expected in model["known_answer"]["steps"]:
        time = float(expected["time"])
        u = blocks[("displacements", time)]
        rf = blocks[("forces", time)]
        if set(u) != node_set or set(rf) != node_set:
            raise AssertionError(f"Incomplete U/RF node inventory at time {time}")

        a, b = node_ids["A"], node_ids["B"]
        sa, ga = node_ids["SA"], node_ids["GA"]
        sb, gb = node_ids["SB"], node_ids["GB"]
        pa, pb = node_ids["PA"], node_ids["PB"]
        q, gq = node_ids["Q"], node_ids["GQ"]

        _near(f"u_A at t={time}", u[a][0], expected["u_a_mm"], tolerance_u)
        _near(f"u_B at t={time}", u[b][0], expected["u_b_mm"], tolerance_u)
        for slave, master, name in ((sa, a, "SA=A"), (pa, a, "PA=A"),
                                    (sb, b, "SB=B"), (pb, b, "PB=B")):
            _near(f"MPC {name} at t={time}", u[slave][0], u[master][0], tolerance_u)
        relative_from_projection = u[pb][0] - u[pa][0]
        _near(f"q=PB-PA at t={time}", u[q][0], relative_from_projection, tolerance_u)
        _near(f"q answer at t={time}", u[q][0], expected["q_mm"], tolerance_u)

        for name, vector in u.items():
            _near(f"Y displacement node {name} at t={time}", vector[1], 0., tolerance_u)
            _near(f"Z displacement node {name} at t={time}", vector[2], 0., tolerance_u)
        for name in ("GA", "GB", "GQ"):
            _near(f"fixed X at {name} at t={time}", u[node_ids[name]][0], 0., tolerance_u)

        # SPRINGA endpoint order is Q (X=100 mm), then grounded GQ (X=0).
        q = u[node_ids["Q"]][0]
        length = 100. + q
        if length <= 0. or abs(q) >= 10.:
            raise AssertionError(f"SPRINGA geometry/table range invalid at t={time}: q={q}")
        elongation = abs(length) - 100.
        _near(f"SPRINGA elongation at t={time}", elongation, q, 1.e-12)
        joint_internal = 50. * max(elongation, 0.)
        _near(f"joint hand law at t={time}", joint_internal,
              expected["joint_internal_N"], tolerance_f)
        joint_rf_q = rf[node_ids["Q"]][0]
        joint_rf_ground = rf[node_ids["GQ"]][0]
        _near(f"native SPRINGA RF at Q, t={time}", joint_rf_q,
              joint_internal, tolerance_f)
        _near(f"native SPRINGA RF at GQ, t={time}", joint_rf_ground,
              -joint_internal, tolerance_f)
        _near(f"SPRINGA endpoint action/reaction, t={time}",
              joint_rf_q + joint_rf_ground, 0., tolerance_f)

        support_rows = []
        recovered_support_action = {}
        for name, endpoint, ground in (("SUPPORT_A", sa, ga), ("SUPPORT_B", sb, gb)):
            generalized_internal = stiffness[name] * u[endpoint][0]
            rf_endpoint = rf[endpoint][0]
            rf_ground = rf[ground][0]
            _near(f"{name} endpoint RF, t={time}", rf_endpoint,
                  generalized_internal, tolerance_f)
            _near(f"{name} ground RF, t={time}", rf_ground,
                  -generalized_internal, tolerance_f)
            _near(f"{name} endpoint pair, t={time}", rf_endpoint + rf_ground,
                  0., tolerance_f)
            action_on_body = .5 * (rf_ground - rf_endpoint)
            body = "A" if name == "SUPPORT_A" else "B"
            recovered_support_action[body] = action_on_body
            support_rows.append({
                "name": name,
                "endpoint_rf_N": rf_endpoint,
                "ground_rf_N": rf_ground,
                "physical_action_on_body_N": action_on_body,
            })

        # With q=u_B-u_A, internal force transfer is (-f,+f) on (A,B);
        # physical actions are (+f,-f). GQ is only numerical.
        joint_action_a = .5 * (joint_rf_q - joint_rf_ground)
        joint_action_b = -joint_action_a
        _near(f"physical joint action on A, t={time}", joint_action_a,
              expected["joint_action_on_a_N"], tolerance_f)
        _near(f"physical joint action on B, t={time}", joint_action_b,
              expected["joint_action_on_b_N"], tolerance_f)
        _near(f"joint action pair on bodies, t={time}",
              joint_action_a + joint_action_b, 0., tolerance_f)

        loads = {int(n): float(force) for n, force in expected["loads_N"].items()}
        residual_a = loads[node_ids["A"]] + recovered_support_action["A"] + joint_action_a
        residual_b = loads[node_ids["B"]] + recovered_support_action["B"] + joint_action_b
        _near(f"body A force closure at t={time}", residual_a, 0., tolerance_f)
        _near(f"body B force closure at t={time}", residual_b, 0., tolerance_f)

        result_steps.append({
            "time": time,
            "u_A_mm": u[a][0],
            "u_B_mm": u[b][0],
            "q_mm": q,
            "joint_internal_N_from_native_RF": joint_rf_q,
            "joint_physical_action_A_B_N": [joint_action_a, joint_action_b],
            "supports": support_rows,
            "body_A_residual_N": residual_a,
            "body_B_residual_N": residual_b,
            "numerical_GQ_RF_N_excluded_from_physical_balance": joint_rf_ground,
        })

    return {
        "status": "PASS_NATIVE_TWO_BODY_RELATIVE_SPRINGA_MPC_FIXTURE",
        "method_fixture_passed": True,
        "native_solve_executed": True,
        "qualified_for_design": False,
        "floor_or_frame_validated": False,
        "complete_joint_validated": False,
        "newton_active_and_geometric_effects_off_verified": True,
        "input_freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        "execution_sha256": hashlib.sha256((NATIVE / "execution.json").read_bytes()).hexdigest(),
        "model_dat_sha256": hashlib.sha256((NATIVE / "model.dat").read_bytes()).hexdigest(),
        "steps": result_steps,
        "limits": model["limits"],
    }


if __name__ == "__main__":
    try:
        assessment = evaluate()
    except Exception as error:
        assessment = {
            "status": "FAILED_METHOD_CHECK",
            "method_fixture_passed": False,
            "qualified_for_design": False,
            "error": f"{type(error).__name__}: {error}",
        }
        (HERE / "assessment.json").write_text(json.dumps(assessment, indent=2) + "\n")
        raise
    (HERE / "assessment.json").write_text(json.dumps(assessment, indent=2) + "\n")
    print(assessment["status"])
