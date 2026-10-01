"""Assess a parent-run transformed two-row floor reaction known-answer coupon."""
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
                rows[node] = [float(value.replace("D", "E").replace("d", "e"))
                              for value in fields[1:]]
                started = True
            elif started:
                break
        time = float(match.group(2).replace("D", "E").replace("d", "e"))
        key = (match.group(1), time)
        if key in blocks:
            raise AssertionError(f"Duplicate native output block {key}")
        blocks[key] = rows
    return blocks


def _transpose(matrix):
    return [list(row) for row in zip(*matrix, strict=True)]


def _matmul(left, right):
    right_t = _transpose(right)
    return [[sum(a * b for a, b in zip(row, col, strict=True))
             for col in right_t] for row in left]


def _matvec(matrix, vector):
    return [sum(a * b for a, b in zip(row, vector, strict=True))
            for row in matrix]


def _check_transform_and_pivots(model):
    transform = model["source_reaction_transform"]
    source = transform["source_matrix"]
    rows = [int(i) for i in transform["selected_source_rows_zero_based"]]
    pivots = [int(i) for i in transform["pivot_physical_columns_zero_based"]]
    if rows != [1, 0] or pivots != [1, 0]:
        raise AssertionError("Fixture must keep its reviewed nonidentity row/pivot permutation")
    if rows == list(range(len(rows))) or pivots == list(range(len(pivots))):
        raise AssertionError("The reaction transform is not exercising both permutations")

    selected = [source[i] for i in rows]
    s = [[row[j] for j in pivots] for row in selected]
    recorded_s = transform["S"]
    for i in range(2):
        for j in range(2):
            _near(f"S[{i},{j}]", s[i][j], recorded_s[i][j], 1.e-14)
    s_inv = transform["S_inverse"]
    identity = _matmul(s_inv, s)
    for i in range(2):
        for j in range(2):
            _near(f"S^-1*S[{i},{j}]", identity[i][j], 1. if i == j else 0., 1.e-13)
    h = _matmul(s_inv, selected)
    recorded_h = transform["H"]
    for i in range(2):
        for j in range(2):
            _near(f"H[{i},{j}]", h[i][j], recorded_h[i][j], 1.e-14)
    for equation_row, pivot_column in enumerate(pivots):
        for column in range(2):
            _near(f"unit pivot H[{equation_row},{column}]", h[equation_row][column],
                  1. if column == pivot_column else 0., 1.e-14)

    roles = {name: int(tag) for name, tag in model["node_roles"].items()}
    refs = [int(n) for n in model["reference_nodes_by_original_source_row"]]
    physical = [int(model["physical_nodes_by_body"][name]) for name in ("A", "B")]
    if [physical[i] for i in pivots] != [roles["PHYSICAL_B"], roles["PHYSICAL_A"]]:
        raise AssertionError("Pivot metadata does not point to the reviewed physical B,A DOFs")

    equations = model["equations"]
    if len(equations) < 2:
        raise AssertionError("Transformed floor equations are absent")
    expected_equations = []
    for row_index, pivot_column in enumerate(pivots):
        terms = [(physical[pivot_column], 1, 1.)]
        for selected_index, original_row in enumerate(rows):
            terms.append((refs[original_row], 1, -s_inv[row_index][selected_index]))
        expected_equations.append(terms)
    for i, (actual, expected) in enumerate(zip(equations[:2], expected_equations, strict=True)):
        if len(actual) != len(expected):
            raise AssertionError(f"Transformed source row {i} has the wrong term count")
        for j, (got, want) in enumerate(zip(actual, expected, strict=True)):
            if (int(got[0]), int(got[1])) != (want[0], want[1]):
                raise AssertionError(f"Transformed equation {i}, term {j} has the wrong DOF")
            _near(f"transformed equation {i}, coefficient {j}",
                  float(got[2]), float(want[2]), 1.e-14)

    dependent = [(int(eq[0][0]), int(eq[0][1])) for eq in equations]
    if len(dependent) != len(set(dependent)):
        raise AssertionError("A DOF is the first dependent term in more than one equation")
    fixed = set()
    for boundary in model["boundary_conditions"]:
        fixed.update((int(boundary["node"]), dof)
                     for dof in range(int(boundary["first_dof"]),
                                      int(boundary["last_dof"]) + 1))
    collision = fixed.intersection(dependent)
    if collision:
        raise AssertionError(f"Dependent DOF also appears in *BOUNDARY: {sorted(collision)}")

    # Verify source-point interpolation preserves affine translation and Y
    # position, which makes the source and physical tangential force resultants
    # and yaw moments equivalent.
    source_y = transform["source_coordinate_y_mm"]
    physical_y = transform["physical_coordinate_y_mm"]
    for source_row in range(2):
        _near(f"source row sum for row {source_row}", sum(source[source_row]), 1., 1.e-14)
        _near(f"affine Y transfer for source row {source_row}",
              sum(source[source_row][j] * physical_y[j] for j in range(2)),
              source_y[source_row], 1.e-14)
    return transform, roles, refs, physical, source


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
    if "*ERROR" in (stdout + stderr).upper():
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
        raise AssertionError("Frozen deck does not use the reviewed method card in every step")
    # Guard against the parser failure from the previous attempt: linear SPRING
    # real stiffness values must have a decimal point in the frozen data deck.
    for token in ("20.0", "98.75"):
        if token not in deck:
            raise AssertionError(f"Explicit real spring stiffness token {token} is absent")

    transform, roles, refs, physical, source = _check_transform_and_pivots(model)
    blocks = _native_blocks((NATIVE / "model.dat").read_text())
    expected_nodes = {int(n) for n in model["nodes"]}
    tolerance_u = float(model["tolerances"]["u_abs_mm"])
    tolerance_f = float(model["tolerances"]["force_abs_N"])
    tolerance_m = float(model["tolerances"]["moment_abs_Nmm"])
    pivot_columns = [int(i) for i in transform["pivot_physical_columns_zero_based"]]
    selected_rows = [int(i) for i in transform["selected_source_rows_zero_based"]]
    s_inv = transform["S_inverse"]
    source_y = [float(v) for v in transform["source_coordinate_y_mm"]]
    physical_y = [float(v) for v in transform["physical_coordinate_y_mm"]]
    body_names = ("A", "B")
    normal_by_body = {record["physical_body"]: record
                      for record in model["normal_springs"]}
    structural_by_name = {record["name"]: record for record in model["springs"]}
    step_results = []

    for expected in steps:
        time = float(expected["time"])
        u = blocks[("displacements", time)]
        rf = blocks[("forces", time)]
        if set(u) != expected_nodes or set(rf) != expected_nodes:
            raise AssertionError(f"Incomplete U/RF node inventory at time {time}")
        for equation_index, equation in enumerate(model["equations"], 1):
            residual = sum(float(term[2]) * u[int(term[0])][int(term[1]) - 1]
                           for term in equation)
            _near(f"MPC {equation_index} residual at t={time}", residual, 0., tolerance_u)
        for node in expected_nodes:
            for boundary in model["boundary_conditions"]:
                if int(boundary["node"]) != node:
                    continue
                for dof in range(int(boundary["first_dof"]),
                                 int(boundary["last_dof"]) + 1):
                    _near(f"SPC node {node} DOF {dof} at t={time}",
                          u[node][dof - 1], float(boundary["value"]), tolerance_u)

        physical_u = {}
        structural_x = []
        structural_z = []
        normal_force = []
        spring_endpoint_results = {}
        for body_index, name in enumerate(body_names):
            p = int(model["physical_nodes_by_body"][name])
            _near(f"physical {name} x at t={time}", u[p][0], 0., tolerance_u)
            expected_u = expected["physical_displacements_x_z_mm"][name]
            _near(f"physical {name} z at t={time}", u[p][2], expected_u["z"], tolerance_u)
            physical_u[name] = [u[p][0], u[p][2]]

            sx_record = structural_by_name[f"STRUCTURAL_XZ_{name}"]
            sz_record = structural_by_name[f"STRUCTURAL_Z_{name}"]
            for record, coordinate_dof in ((sx_record, 1), (sz_record, 3)):
                first, second = map(int, record["nodes"])
                component = int(record["dof"]) - 1
                delta = u[first][component] - u[second][component]
                value = float(record["stiffness_n_per_mm"]) * delta
                _near(f"{record['name']} endpoint RF at t={time}",
                      rf[first][component], value, tolerance_f)
                _near(f"{record['name']} anchor RF at t={time}",
                      rf[second][component], -value, tolerance_f)
                spring_endpoint_results[record["name"]] = value
            expected_s = expected["projected_coordinates_mm"][name]["s_xz"]
            xz_node = int(roles[f"XZ_PROJECTION_{name}"])
            vertical_node = int(roles[f"Z_PROJECTION_{name}"])
            _near(f"projected s for {name} at t={time}", u[xz_node][0], expected_s, tolerance_u)
            _near(f"projected z for {name} at t={time}", u[vertical_node][2], u[p][2], tolerance_u)
            fx = spring_endpoint_results[f"STRUCTURAL_XZ_{name}"]
            fz_vertical = spring_endpoint_results[f"STRUCTURAL_Z_{name}"]
            gx = fx
            gz = 0.25 * fx + fz_vertical
            structural_x.append(gx)
            structural_z.append(gz)

            normal_record = normal_by_body[name]
            q_node = int(normal_record["endpoint"])
            ground = int(normal_record["ground"])
            q = u[q_node][2]
            expected_q = expected["projected_coordinates_mm"][name]["q_normal"]
            _near(f"normal q for {name} at t={time}", q, expected_q, tolerance_u)
            if q <= 0. or abs(q) >= 10.:
                raise AssertionError(f"Normal {name} did not remain in the recorded compression table range")
            length = 100. + q
            elongation = length - 100.
            _near(f"SPRINGA elongation for {name}", elongation, q, 1.e-12)
            force = 100. * max(q, 0.)
            _near(f"normal {name} endpoint RF at t={time}", rf[q_node][2], force, tolerance_f)
            _near(f"normal {name} ground RF at t={time}", rf[ground][2], -force, tolerance_f)
            normal_force.append(force)
            _near(f"structural x answer for {name} at t={time}", gx,
                  expected["spring_internal_by_body_N"][name]["structural_x"], tolerance_f)
            _near(f"structural z answer for {name} at t={time}", gz,
                  expected["spring_internal_by_body_N"][name]["structural_z"], tolerance_f)
            _near(f"normal answer for {name} at t={time}", force,
                  expected["spring_internal_by_body_N"][name]["normal"], tolerance_f)

        load_by_body = expected["loads_by_body_N"]
        loads_x = [float(load_by_body[name]["x"]) for name in body_names]
        loads_z = [float(load_by_body[name]["z"]) for name in body_names]

        # Reconstruct the transformed equation load in source-row order. Keep
        # the raw reference RF values intact and check the algebraic output
        # contract already verified for the scalar exact-floor coupon.
        pivot_load = [loads_x[column] for column in pivot_columns]
        correction_selected = _matvec(_transpose(s_inv), pivot_load)
        correction_original = [0., 0.]
        for selected_index, original_row in enumerate(selected_rows):
            correction_original[original_row] = correction_selected[selected_index]
        raw_reference = [rf[node][0] for node in refs]

        pivot_internal = [structural_x[column] for column in pivot_columns]
        raw_selected_expected = _matvec(_transpose(s_inv), pivot_internal)
        raw_reference_expected = [0., 0.]
        for selected_index, original_row in enumerate(selected_rows):
            raw_reference_expected[original_row] = raw_selected_expected[selected_index]
        for row_index in range(2):
            _near(f"raw reference RF source row {row_index} at t={time}",
                  raw_reference[row_index], raw_reference_expected[row_index], tolerance_f)

        reaction_source = [raw_reference[i] - correction_original[i] for i in range(2)]
        for i, value in enumerate(reaction_source):
            _near(f"source reaction row {i} at t={time}", value,
                  expected["floor_tangential_reaction_source_rows_original_order_N"][i],
                  tolerance_f)

        # A^T maps the source point forces back to generalized physical loads.
        physical_support = _matvec(_transpose(source), reaction_source)
        for i, value in enumerate(physical_support):
            _near(f"physical support x on body {body_names[i]} at t={time}", value,
                  expected["physical_floor_support_x_by_body_N"][i], tolerance_f)
            x_residual = loads_x[i] + value - structural_x[i]
            _near(f"body {body_names[i]} x balance at t={time}", x_residual, 0., tolerance_f)
            z_residual = loads_z[i] - structural_z[i] + normal_force[i]
            _near(f"body {body_names[i]} z balance at t={time}", z_residual, 0., tolerance_f)

        source_force = sum(reaction_source)
        physical_force = sum(physical_support)
        source_moment_z = -sum(source_y[i] * reaction_source[i] for i in range(2))
        physical_moment_z = -sum(physical_y[i] * physical_support[i] for i in range(2))
        _near(f"source and physical support force sum at t={time}",
              source_force, physical_force, tolerance_f)
        _near(f"source and physical support Mz at t={time}",
              source_moment_z, physical_moment_z, tolerance_m)
        _near(f"known-answer source Mz at t={time}", source_moment_z,
              expected["source_moment_z_about_origin_Nmm"], tolerance_m)

        step_results.append({
            "time": time,
            "physical_displacements_x_z_mm": physical_u,
            "structural_internal_x_N": structural_x,
            "structural_internal_z_N": structural_z,
            "normal_internal_N": normal_force,
            "pivot_CLOAD_order_B_A_N": pivot_load,
            "raw_reference_RF_original_source_row_order_N": raw_reference,
            "transformed_CLOAD_correction_original_source_row_order_N": correction_original,
            "recovered_floor_reaction_original_source_row_order_N": reaction_source,
            "physical_support_x_on_A_B_N": physical_support,
            "source_and_physical_resultant_x_N": [source_force, physical_force],
            "source_and_physical_Mz_Nmm": [source_moment_z, physical_moment_z],
        })

    return {
        "status": "PASS_NATIVE_TRANSFORMED_FLOOR_REACTION_KNOWN_ANSWER",
        "method_fixture_passed": True,
        "native_solve_executed": True,
        "selected_source_rows_zero_based": selected_rows,
        "pivot_physical_order": transform["pivot_physical_node_order"],
        "reaction_mapping": transform["native_map"],
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
            "native_solve_executed": False,
            "error": f"{type(error).__name__}: {error}",
            "qualified_for_design": False,
            "floor_capacity_established": False,
            "friction_qualified": False,
            "complete_joint_validated": False,
        }
        print(json.dumps(assessment, indent=2))
        raise
    out = HERE / "assessment.json"
    out.write_text(json.dumps(assessment, indent=2, allow_nan=False) + "\n")
    print(json.dumps(assessment, indent=2, allow_nan=False))
