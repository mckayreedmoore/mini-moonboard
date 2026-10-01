"""Assess parent-run exact-stick reference-force recovery against two hand cases."""
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
                rows[node] = [
                    float(value.replace("D", "E").replace("d", "e"))
                    for value in fields[1:]
                ]
                started = True
            elif started:
                break
        time = float(match.group(2).replace("D", "E").replace("d", "e"))
        key = (match.group(1), time)
        if key in blocks:
            raise AssertionError(f"Duplicate native output block {key}")
        blocks[key] = rows
    return blocks


def _check_unique_equation_pivots(model):
    dependent = [
        (int(equation[0][0]), int(equation[0][1]))
        for equation in model["equations"]
    ]
    if len(dependent) != len(set(dependent)):
        raise AssertionError("Repeated dependent degree of freedom in frozen equations")
    fixed = set()
    for row in model["boundary_conditions"]:
        fixed.update(
            (int(row["node"]), dof)
            for dof in range(int(row["first_dof"]), int(row["last_dof"]) + 1)
        )
    collision = fixed.intersection(dependent)
    if collision:
        raise AssertionError(f"Equation-dependent DOF also appears in *BOUNDARY: {sorted(collision)}")


def evaluate():
    freeze_path = NATIVE / "freeze.json"
    freeze = json.loads(freeze_path.read_text())
    for name, digest in freeze["files_sha256"].items():
        actual = hashlib.sha256((NATIVE / name).read_bytes()).hexdigest()
        if actual != digest:
            raise AssertionError(f"Frozen input hash mismatch: {name}")
    profile = freeze["solver_profile"]
    if profile.get("version") != "2.23":
        raise AssertionError("This method check is pinned to CalculiX 2.23")
    if profile.get("manual", {}).get("sha256") != (
        "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
    ):
        raise AssertionError("Pinned 2.23 manual digest does not match the reviewed manual")

    execution = json.loads((NATIVE / "execution.json").read_text())
    if execution.get("native_solve_executed") is not True or execution.get("returncode") != 0:
        raise AssertionError("Native execution did not terminate successfully")
    stdout = (NATIVE / "native.stdout").read_text()
    stderr = (NATIVE / "native.stderr").read_text()
    combined = stdout + stderr
    if "*ERROR" in combined.upper():
        raise AssertionError("Native output contains a solver error")

    model = json.loads((NATIVE / "model.json").read_text())
    steps = model["known_answer"]["steps"]
    if stdout.lower().count("newton-raphson iterative procedure is active") < len(steps):
        raise AssertionError("Newton-active evidence is missing for one or more steps")
    if stdout.lower().count("effects are turned off") < len(steps):
        raise AssertionError("Geometric-effects-off evidence is missing for one or more steps")
    if re.search(r"nonlinear geometric effects are taken into account", stdout, re.IGNORECASE):
        raise AssertionError("Solver output says nonlinear geometric effects were active")

    deck = (NATIVE / "model.inp").read_text()
    step_card = "*STEP,NLGEOM,NLGEOM=NO,INC=40"
    if deck.count(step_card) != len(steps):
        raise AssertionError("The frozen deck does not contain the reviewed method card in every step")

    _check_unique_equation_pivots(model)
    blocks = _native_blocks((NATIVE / "model.dat").read_text())
    node_roles = {name: int(tag) for name, tag in model["node_roles"].items()}
    expected_nodes = {int(node) for node in model["nodes"]}
    tolerance_u = float(model["tolerances"]["u_abs_mm"])
    tolerance_f = float(model["tolerances"]["force_abs_N"])
    p = node_roles["P"]
    ref = node_roles["FLOOR_REF"]
    xz = node_roles["XZ_PROJECTION"]
    xz_anchor = node_roles["XZ_ANCHOR"]
    zproj = node_roles["Z_PROJECTION"]
    z_anchor = node_roles["Z_ANCHOR"]
    normal = node_roles["NORMAL_Q"]
    normal_ground = node_roles["NORMAL_GROUND"]

    candidate_formulas = {
        "RF_REFERENCE": lambda rf_ref, wx: rf_ref,
        "NEGATIVE_RF_REFERENCE": lambda rf_ref, wx: -rf_ref,
        "RF_REFERENCE_MINUS_DEPENDENT_CLOAD": lambda rf_ref, wx: rf_ref - wx,
        "NEGATED_RF_REFERENCE_MINUS_DEPENDENT_CLOAD": lambda rf_ref, wx: -rf_ref - wx,
    }
    candidate_rows = {name: [] for name in candidate_formulas}
    step_results = []

    for expected in steps:
        time = float(expected["time"])
        u = blocks[("displacements", time)]
        rf = blocks[("forces", time)]
        if set(u) != expected_nodes or set(rf) != expected_nodes:
            raise AssertionError(f"Incomplete U/RF node inventory at time {time}")

        _near(f"physical x at t={time}", u[p][0], expected["u_x_mm"], tolerance_u)
        _near(f"physical z at t={time}", u[p][2], expected["u_z_mm"], tolerance_u)
        _near(f"ground-reference x at t={time}", u[ref][0], 0., tolerance_u)
        _near(f"projected s at t={time}", u[xz][0],
              expected["projected_coordinate_s_mm"], tolerance_u)
        _near(f"vertical projected z at t={time}", u[zproj][2], u[p][2], tolerance_u)
        _near(f"normal q at t={time}", u[normal][2],
              expected["normal_coordinate_q_mm"], tolerance_u)
        for equation_index, equation in enumerate(model["equations"], start=1):
            residual = sum(float(coefficient) * u[int(node)][int(dof) - 1]
                           for node, dof, coefficient in equation)
            _near(f"MPC {equation_index} residual at t={time}", residual, 0., tolerance_u)

        for node, displacement in u.items():
            _near(f"unused y DOF at node {node}, t={time}", displacement[1], 0., tolerance_u)
        for node in (ref, xz_anchor, z_anchor, normal_ground):
            for dof in range(3):
                _near(f"grounded node {node} DOF {dof + 1}, t={time}",
                      u[node][dof], 0., tolerance_u)
        for node, free_dof in ((xz, 1), (zproj, 3), (normal, 3)):
            for dof in range(3):
                if dof != free_dof - 1:
                    _near(f"clamped projection node {node} DOF {dof + 1}, t={time}",
                          u[node][dof], 0., tolerance_u)

        # Each isolated linear spring reports its generalized internal force at
        # the projected endpoint; the anchor carries the equal-and-opposite RF.
        spring_internal = {}
        for spring in model["springs"]:
            first, second = map(int, spring["nodes"])
            dof = int(spring["dof"])
            component = dof - 1
            delta = u[first][component] - u[second][component]
            force = float(spring["stiffness_n_per_mm"]) * delta
            _near(f"{spring['name']} endpoint RF at t={time}",
                  rf[first][component], force, tolerance_f)
            _near(f"{spring['name']} anchor RF at t={time}",
                  rf[second][component], -force, tolerance_f)
            _near(f"{spring['name']} RF action/reaction at t={time}",
                  rf[first][component] + rf[second][component], 0., tolerance_f)
            spring_internal[spring["name"]] = force

        q = u[normal][2]
        length = 100. + q
        if length <= 0. or abs(q) >= 10.:
            raise AssertionError(f"SPRINGA span or table range invalid at t={time}: q={q}")
        elongation = abs(length) - 100.
        _near(f"normal elongation equals q at t={time}", elongation, q, 1.e-12)
        normal_internal = 100. * max(q, 0.)
        if normal_internal <= 0.:
            raise AssertionError(f"The intended compression branch is not active at t={time}")
        _near(f"normal SPRINGA endpoint RF at t={time}",
              rf[normal][2], normal_internal, tolerance_f)
        _near(f"normal SPRINGA ground RF at t={time}",
              rf[normal_ground][2], -normal_internal, tolerance_f)
        _near(f"normal SPRINGA endpoint action/reaction at t={time}",
              rf[normal][2] + rf[normal_ground][2], 0., tolerance_f)
        _near(f"normal hand answer at t={time}", normal_internal,
              expected["normal_spring_internal_N"], tolerance_f)

        wx = float(expected["external_Wx_N"])
        wz = float(expected["external_Wz_N"])
        raw_reference_rf = rf[ref][0]
        f_xz = spring_internal["STRUCTURAL_XZ"]
        f_z = spring_internal["STRUCTURAL_Z"]
        residual_z = wz - .25 * f_xz - f_z + normal_internal
        _near(f"physical z-force balance at t={time}", residual_z, 0., tolerance_f)
        _near(f"projected spring internal answer at t={time}", f_xz,
              expected["projected_spring_internal_N"], tolerance_f)
        _near(f"vertical spring internal answer at t={time}", f_z,
              expected["vertical_spring_internal_N"], tolerance_f)

        mapped = {}
        for name, formula in candidate_formulas.items():
            recovered = formula(raw_reference_rf, wx)
            residual_x = wx + recovered - f_xz
            candidate_rows[name].append({
                "time": time,
                "RF_reference_raw_N": raw_reference_rf,
                "dependent_node_CLOAD_Wx_N": wx,
                "recovered_floor_tangential_reaction_N": recovered,
                "physical_x_force_residual_N": residual_x,
                "physical_z_force_residual_N": residual_z,
                "matches_hand_reaction": abs(recovered - expected["floor_tangential_reaction_N"]) <= tolerance_f,
                "closes_x_balance": abs(residual_x) <= tolerance_f,
            })
            mapped[name] = recovered

        step_results.append({
            "time": time,
            "physical_displacement_x_z_mm": [u[p][0], u[p][2]],
            "projected_s_mm": u[xz][0],
            "normal_q_mm": q,
            "structural_spring_internal_N": spring_internal,
            "normal_internal_N": normal_internal,
            "RF_reference_raw_N": raw_reference_rf,
            "RF_dependent_physical_node_raw_x_N": rf[p][0],
            "candidate_floor_tangential_reactions_N": mapped,
            "physical_z_force_residual_N": residual_z,
        })

    matches = []
    for name, rows in candidate_rows.items():
        if all(row["matches_hand_reaction"] and row["closes_x_balance"] for row in rows):
            matches.append(name)
    if len(matches) != 1:
        summary = {name: rows for name, rows in candidate_rows.items()}
        raise AssertionError(
            "Reference RF interpretation must be unique and close both physical cases; "
            f"matching_maps={matches}; candidate_evaluations={json.dumps(summary, sort_keys=True)}"
        )

    mapping = matches[0]
    for row in candidate_rows[mapping]:
        _near(f"floor reaction from {mapping} at t={row['time']}",
              row["recovered_floor_tangential_reaction_N"],
              next(answer["floor_tangential_reaction_N"] for answer in steps
                   if float(answer["time"]) == row["time"]),
              tolerance_f)
        _near(f"physical x-force balance from {mapping} at t={row['time']}",
              row["physical_x_force_residual_N"], 0., tolerance_f)

    return {
        "status": "PASS_NATIVE_EXACT_FLOOR_MPC_REACTION_KNOWN_ANSWER",
        "method_fixture_passed": True,
        "native_solve_executed": True,
        "floor_tangential_reaction_mapping": mapping,
        "candidate_mapping_evaluations": candidate_rows,
        "steps": step_results,
        "qualified_for_design": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "complete_joint_validated": False,
        "input_freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        "execution_sha256": hashlib.sha256((NATIVE / "execution.json").read_bytes()).hexdigest(),
        "model_dat_sha256": hashlib.sha256((NATIVE / "model.dat").read_bytes()).hexdigest(),
        "native_stdout_sha256": hashlib.sha256((NATIVE / "native.stdout").read_bytes()).hexdigest(),
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
