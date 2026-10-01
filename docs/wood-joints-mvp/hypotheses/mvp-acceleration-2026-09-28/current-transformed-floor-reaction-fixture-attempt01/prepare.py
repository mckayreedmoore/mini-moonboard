"""Create an unfrozen two-row transformed floor reaction known-answer coupon."""
from fractions import Fraction
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.horizontal_panel_frame import Structure, record_structure


def _inverse_2x2(matrix):
    a, b = matrix[0]
    c, d = matrix[1]
    determinant = a * d - b * c
    if determinant == 0:
        raise ValueError("Source/pivot matrix is singular")
    return ((d / determinant, -b / determinant),
            (-c / determinant, a / determinant))


def _matvec(matrix, vector):
    return tuple(sum(a * b for a, b in zip(row, vector, strict=True))
                 for row in matrix)


def _transpose(matrix):
    return tuple(tuple(matrix[i][j] for i in range(len(matrix)))
                 for j in range(len(matrix[0])))


def _matmul(left, right):
    right_t = _transpose(right)
    return tuple(tuple(sum(a * b for a, b in zip(row, col, strict=True))
                       for col in right_t)
                 for row in left)


def _fraction_text(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _hand_answers(transform):
    """Derive per-body and source-row answers by exact rational statics."""
    source = tuple(tuple(Fraction(v) for v in row)
                   for row in transform["source_matrix_fraction"])
    source_t_inv = _inverse_2x2(_transpose(source))
    selected_rows = transform["selected_source_rows_zero_based"]
    pivot_cols = transform["pivot_physical_columns_zero_based"]
    s_inv = tuple(tuple(Fraction(v) for v in row)
                  for row in transform["S_inverse_fraction"])

    cases = [
        {
            "time": 1.0,
            "loads_by_body_N": {"A": {"x": 6, "z": -20},
                                "B": {"x": -4, "z": -40}},
            "z_mm": {"A": Fraction(-1, 10), "B": Fraction(-1, 5)},
        },
        {
            "time": 2.0,
            "loads_by_body_N": {"A": {"x": -3, "z": -30},
                                "B": {"x": 5, "z": -10}},
            "z_mm": {"A": Fraction(-3, 20), "B": Fraction(-1, 20)},
        },
    ]
    physical_names = ["A", "B"]
    y_physical = (Fraction(0), Fraction(100))
    y_source = (Fraction(25), Fraction(75))
    source_rows = transform["source_matrix_fraction"]
    answers = []

    for case in cases:
        z = tuple(case["z_mm"][name] for name in physical_names)
        loads_x = tuple(Fraction(case["loads_by_body_N"][name]["x"])
                        for name in physical_names)
        loads_z = tuple(Fraction(case["loads_by_body_N"][name]["z"])
                        for name in physical_names)
        projected = tuple(z_i / 4 for z_i in z)
        spring_x = tuple(20 * s_i for s_i in projected)
        spring_vertical = tuple(Fraction(395, 4) * z_i for z_i in z)
        structural_x = spring_x
        structural_z = tuple(spring_x_i / 4 + spring_z_i
                             for spring_x_i, spring_z_i
                             in zip(spring_x, spring_vertical, strict=True))
        normal_q = tuple(-z_i for z_i in z)
        normal = tuple(100 * q_i for q_i in normal_q)
        assert structural_z == tuple(100 * z_i for z_i in z)
        assert tuple(w - g + n for w, g, n
                     in zip(loads_z, structural_z, normal, strict=True)) == (0, 0)

        physical_support = tuple(g - w for g, w
                                 in zip(structural_x, loads_x, strict=True))
        source_reaction = _matvec(source_t_inv, physical_support)

        # Independently form the adapter's transformed equation coordinates:
        # selected rows Q*A, selected pivot columns S, then S^-1.
        a_selected = tuple(source[i] for i in selected_rows)
        s = tuple(tuple(row[j] for j in pivot_cols) for row in a_selected)
        inverse_s = _inverse_2x2(s)
        pivot_internal = tuple(structural_x[j] for j in pivot_cols)
        pivot_load = tuple(loads_x[j] for j in pivot_cols)
        raw_selected = _matvec(_transpose(inverse_s), pivot_internal)
        correction_selected = _matvec(_transpose(inverse_s), pivot_load)
        raw_original = [Fraction(0), Fraction(0)]
        correction_original = [Fraction(0), Fraction(0)]
        for selected_index, original_row in enumerate(selected_rows):
            raw_original[original_row] = raw_selected[selected_index]
            correction_original[original_row] = correction_selected[selected_index]
        recovered = tuple(raw_original[i] - correction_original[i]
                          for i in range(2))
        assert recovered == source_reaction

        mapped_support = _matvec(_transpose(source), recovered)
        assert mapped_support == physical_support
        source_force = sum(source_reaction)
        physical_force = sum(physical_support)
        # For points on +Y and forces along +X, M_z = -Y*F_x.
        source_moment_z = -sum(y * f for y, f in zip(y_source, source_reaction, strict=True))
        physical_moment_z = -sum(y * f for y, f in zip(y_physical, physical_support, strict=True))
        assert source_force == physical_force
        assert source_moment_z == physical_moment_z

        answers.append({
            "time": case["time"],
            "loads_by_body_N": case["loads_by_body_N"],
            "physical_displacements_x_z_mm": {
                name: {"x": 0.0, "z": float(case["z_mm"][name])}
                for name in physical_names
            },
            "projected_coordinates_mm": {
                name: {"s_xz": float(projected[i]), "q_normal": float(normal_q[i])}
                for i, name in enumerate(physical_names)
            },
            "spring_internal_by_body_N": {
                name: {
                    "xz_projection": float(spring_x[i]),
                    "vertical_projection": float(spring_vertical[i]),
                    "structural_x": float(structural_x[i]),
                    "structural_z": float(structural_z[i]),
                    "normal": float(normal[i]),
                }
                for i, name in enumerate(physical_names)
            },
            "physical_floor_support_x_by_body_N": [float(v) for v in physical_support],
            "expected_raw_reference_rf_x_original_row_order_N": [float(v) for v in raw_original],
            "transferred_pivot_cload_source_correction_original_row_order_N": [
                float(v) for v in correction_original
            ],
            "floor_tangential_reaction_source_rows_original_order_N": [
                float(v) for v in recovered
            ],
            "source_force_sum_N": float(source_force),
            "equivalent_physical_force_sum_N": float(physical_force),
            "source_moment_z_about_origin_Nmm": float(source_moment_z),
            "equivalent_physical_moment_z_about_origin_Nmm": float(physical_moment_z),
            "exact": {
                "z_mm": {name: _fraction_text(case["z_mm"][name])
                         for name in physical_names},
                "structural_x_N": [_fraction_text(v) for v in structural_x],
                "structural_z_N": [_fraction_text(v) for v in structural_z],
                "normal_N": [_fraction_text(v) for v in normal],
                "physical_floor_support_x_by_body_N": [
                    _fraction_text(v) for v in physical_support
                ],
                "expected_raw_reference_rf_x_original_row_order_N": [
                    _fraction_text(v) for v in raw_original
                ],
                "transferred_pivot_cload_source_correction_original_row_order_N": [
                    _fraction_text(v) for v in correction_original
                ],
                "floor_tangential_reaction_source_rows_original_order_N": [
                    _fraction_text(v) for v in recovered
                ],
                "source_moment_z_about_origin_Nmm": _fraction_text(source_moment_z),
                "equivalent_physical_moment_z_about_origin_Nmm": _fraction_text(physical_moment_z),
            },
        })
    return answers


def build_fixture():
    model = Structure()
    node_roles = {}

    def node(name, xyz):
        node_roles[name] = model.node(xyz)
        return node_roles[name]

    # The two physical points are 100 mm apart along Y. The source floor rows
    # lie at the affine interpolation points y=25 and 75 mm and use unit X.
    physical_a = node("PHYSICAL_A", (0., 0., 0.))
    physical_b = node("PHYSICAL_B", (0., 100., 0.))
    ref0 = node("SOURCE_REF_ROW_0", (0., 25., 0.))
    ref1 = node("SOURCE_REF_ROW_1", (0., 75., 0.))

    body_nodes = {"A": physical_a, "B": physical_b}
    spring_records = []
    normal_records = []
    for name, y in (("A", 0.), ("B", 100.)):
        physical = body_nodes[name]
        point = model.nodes[physical]
        xz = node(f"XZ_PROJECTION_{name}", point)
        xz_anchor = node(f"XZ_ANCHOR_{name}", point)
        vertical = node(f"Z_PROJECTION_{name}", point)
        vertical_anchor = node(f"Z_ANCHOR_{name}", point)
        normal = node(f"NORMAL_Q_{name}", (0., y, 100.))
        normal_ground = node(f"NORMAL_GROUND_{name}", point)

        model.spring(xz, xz_anchor, 20., f"STRUCTURAL_XZ_{name}", dofs=(1,))
        model.spring(vertical, vertical_anchor, 98.75,
                     f"STRUCTURAL_Z_{name}", dofs=(3,))
        normal_eid = model.element("SPRINGA", [normal, normal_ground],
                                   f"FLOOR_NORMAL_{name}")
        normal_records.append({
            "name": f"FLOOR_NORMAL_{name}",
            "element": normal_eid,
            "endpoint": normal,
            "ground": normal_ground,
            "physical_body": name,
            "initial_span_mm": 100.,
            "coordinate": f"q_{name}=-z_{name}",
            "force_law_N": "100*max(q_mm,0)",
            "force_N_then_elongation_mm_table": [[0., -10.], [0., 0.], [1000., 10.]],
            "closed_side_tangent_N_per_mm": 100.,
        })
        spring_records.extend([
            {"name": f"STRUCTURAL_XZ_{name}", "coordinate": f"s_{name}=x_{name}+0.25*z_{name}",
             "stiffness_N_per_mm": 20., "endpoint": xz, "ground": xz_anchor,
             "dof": 1, "physical_body": name},
            {"name": f"STRUCTURAL_Z_{name}", "coordinate": f"z_{name}",
             "stiffness_N_per_mm": 98.75, "endpoint": vertical,
             "ground": vertical_anchor, "dof": 3, "physical_body": name},
        ])

        # Isolated spring projection ghosts and normal carriers.
        model.equations.extend([
            [(xz, 1, 1.), (physical, 1, -1.), (physical, 3, -0.25)],
            [(vertical, 3, 1.), (physical, 3, -1.)],
            [(normal, 3, 1.), (physical, 3, 1.)],
        ])

    # A=[[.75,.25],[.25,.75]], selected rows=(1,0), pivot columns=(B,A).
    # Thus S=[[.75,.25],[.25,.75]], S^-1=[[1.5,-.5],[-.5,1.5]],
    # and H=S^-1*A_selected=[[0,1],[1,0]] in physical (A,B) column order.
    # The first term in each row is therefore a distinct physical pivot.
    transformed_equations = [
        [(physical_b, 1, 1.), (ref1, 1, -1.5), (ref0, 1, 0.5)],
        [(physical_a, 1, 1.), (ref1, 1, 0.5), (ref0, 1, -1.5)],
    ]
    model.equations = transformed_equations + model.equations

    # References, numerical spring anchors, and normal grounds are fixed. The
    # physical x DOFs are constrained pivots; their z DOFs remain free.
    model.fixed.update((ref0, ref1))
    for record in spring_records:
        model.fixed.add(record["ground"])
    for record in normal_records:
        model.fixed.add(record["ground"])

    boundaries = [
        {"node": physical_a, "first_dof": 2, "last_dof": 2, "value": 0.},
        {"node": physical_b, "first_dof": 2, "last_dof": 2, "value": 0.},
    ]
    for n in (ref0, ref1):
        boundaries.append({"node": n, "first_dof": 1, "last_dof": 3, "value": 0.})
    for record in spring_records:
        first_dof = 2 if record["dof"] == 1 else 1
        last_dof = 3 if record["dof"] == 1 else 2
        boundaries.append({"node": record["endpoint"], "first_dof": first_dof,
                           "last_dof": last_dof, "value": 0.})
        boundaries.append({"node": record["ground"], "first_dof": 1,
                           "last_dof": 3, "value": 0.})
    for record in normal_records:
        boundaries.append({"node": record["endpoint"], "first_dof": 1,
                           "last_dof": 2, "value": 0.})
        boundaries.append({"node": record["ground"], "first_dof": 1,
                           "last_dof": 3, "value": 0.})

    # The same grounded anchor nodes are repeated for separate spring metadata
    # and normal metadata only if they are distinct nodes; reject accidental
    # DOF overlaps with any equation-dependent pivot.
    boundary_dofs = set()
    for item in boundaries:
        boundary_dofs.update((item["node"], dof)
                             for dof in range(item["first_dof"], item["last_dof"] + 1))
    dependent_dofs = [(terms[0][0], terms[0][1]) for terms in model.equations]
    if len(dependent_dofs) != len(set(dependent_dofs)):
        raise AssertionError("An equation-dependent DOF appears more than once")
    if boundary_dofs.intersection(dependent_dofs):
        raise AssertionError("An equation-dependent DOF is also an SPC")

    source_a = ((Fraction(3, 4), Fraction(1, 4)),
                (Fraction(1, 4), Fraction(3, 4)))
    selected_rows = (1, 0)
    pivot_columns = (1, 0)
    a_selected = tuple(source_a[i] for i in selected_rows)
    s = tuple(tuple(row[j] for j in pivot_columns) for row in a_selected)
    s_inv = _inverse_2x2(s)
    h = _matmul(s_inv, a_selected)
    transform = {
        "physical_column_order": ["A", "B"],
        "source_row_order": [0, 1],
        "selected_source_rows_zero_based": list(selected_rows),
        "pivot_physical_columns_zero_based": list(pivot_columns),
        "pivot_physical_node_order": ["B", "A"],
        "source_matrix_fraction": [[_fraction_text(v) for v in row]
                                    for row in source_a],
        "selected_matrix_fraction": [[_fraction_text(v) for v in row]
                                      for row in a_selected],
        "S_fraction": [[_fraction_text(v) for v in row] for row in s],
        "S_inverse_fraction": [[_fraction_text(v) for v in row] for row in s_inv],
        "H_fraction": [[_fraction_text(v) for v in row] for row in h],
        "source_matrix": [[float(v) for v in row] for row in source_a],
        "selected_matrix": [[float(v) for v in row] for row in a_selected],
        "S": [[float(v) for v in row] for row in s],
        "S_inverse": [[float(v) for v in row] for row in s_inv],
        "H": [[float(v) for v in row] for row in h],
        "source_row_owners": [
            {"row_index": 0, "reference_node": ref0, "floor_point_xyz_mm": [0., 25., 0.],
             "tangent_unit_xyz": [1., 0., 0.]},
            {"row_index": 1, "reference_node": ref1, "floor_point_xyz_mm": [0., 75., 0.],
             "tangent_unit_xyz": [1., 0., 0.]},
        ],
        "reference_affine_source_order": ["r0", "r1"],
        "transformed_affine_order": ["r1", "r0"],
        "equation_form": "H*u_physical_order - S_inverse*r_selected = 0",
        "native_map": (
            "F_pivot is ordered [B,A]. Compute correction_selected=(S_inverse)^T*F_pivot; "
            "write correction_selected[j] into original source row selected_rows[j]. "
            "Then R_source[i]=RF(reference_i,1)-correction_original[i]."
        ),
        "source_coordinate_y_mm": [25., 75.],
        "physical_coordinate_y_mm": [0., 100.],
        "coordinate_transfer_identity": (
            "Each source row uses linear interpolation in Y; row sums are 1 and "
            "sum_j(A[i,j]*y_physical[j]) equals source y_i for each row. "
            "For unit-X force at those coordinates, Mz=-sum(y_i*Fx_i) is preserved."
        ),
    }

    answers = _hand_answers(transform)
    load_steps = []
    for answer in answers:
        loads = []
        for name in ("A", "B"):
            loads.append({"node": body_nodes[name], "body": name, "dof": 1,
                          "force_N": answer["loads_by_body_N"][name]["x"]})
            loads.append({"node": body_nodes[name], "body": name, "dof": 3,
                          "force_N": answer["loads_by_body_N"][name]["z"]})
        load_steps.append({"time": answer["time"], "loads": loads})

    fixed_dofs = {
        str(physical_a): [[2, 2]],
        str(physical_b): [[2, 2]],
        str(ref0): [[1, 3]],
        str(ref1): [[1, 3]],
    }
    for spring in spring_records:
        fixed_ranges = [[2, 3]] if spring["dof"] == 1 else [[1, 2]]
        fixed_dofs[str(spring["endpoint"])] = fixed_ranges
        fixed_dofs[str(spring["ground"])] = [[1, 3]]
    for normal in normal_records:
        fixed_dofs[str(normal["endpoint"])] = [[1, 2]]
        fixed_dofs[str(normal["ground"])] = [[1, 3]]

    metadata = {
        "schema": "current_transformed_floor_reaction_fixture/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": (
            "Two isolated physical x-z points with two affine unit-X floor-stick source rows; "
            "nontrivial selected-row and pivot permutations; transformed exact MPCs; "
            "compression-only normals; two known-answer static cases; no frame or joint"
        ),
        "parent_run_budget": {"max_launches": 1, "timeout_seconds": 60,
                              "run_id": "current-transformed-floor-reaction-fixture-attempt01"},
        "method_hypothesis": {
            "step_card": "*STEP,NLGEOM,NLGEOM=NO,INC=40",
            "intended_method": "Newton iterations enabled with geometrically linear response",
            "native_stdout_gates": [
                "Newton-Raphson iterative procedure is active",
                "effects are turned off",
                "Nonlinear geometric effects are taken into account must be absent",
            ],
            "source_archive": "https://www.dhondt.de/ccx_2.23.src.tar.bz2",
            "source_archive_sha256": "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7",
            "source_interpretation": (
                "steps.f parses bare NLGEOM before NLGEOM=NO: the first sets Newton "
                "iperturb(1)=2, and the second sets geometric effects iperturb(2)=0"
            ),
        },
        "manual": {
            "url": "https://www.dhondt.de/ccx_2.23.pdf",
            "local_path": "fea/generated/ccx_2.23.pdf",
            "sha256": "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330",
            "sections": ["6.2.42 SPRINGA (p129)", "7.56 *EQUATION (pp504-505)",
                          "7.122 *SPRING (pp598-599)", "7.99 *NODE PRINT (p567)"],
            "interpretation": (
                "*EQUATION eliminates its first listed DOF, which cannot also be dependent "
                "elsewhere or an SPC; NODE PRINT RF reports external forces including "
                "reactions and applied concentrated/distributed loads"
            ),
        },
        "node_roles": node_roles,
        "physical_nodes_by_body": body_nodes,
        "reference_nodes_by_original_source_row": [ref0, ref1],
        "source_reaction_transform": transform,
        "transformed_floor_equations": transformed_equations,
        "dependent_dofs": dependent_dofs,
        "fixed_dofs": fixed_dofs,
        "boundary_conditions": boundaries,
        "structural_matrix_by_body_N_per_mm": {"A": [[20., 5.], [5., 100.]],
                                                "B": [[20., 5.], [5., 100.]]},
        "structural_springs": spring_records,
        "normal_springs": normal_records,
        "loads_by_step": load_steps,
        "known_answer": {"steps": answers},
        "tolerances": {"u_abs_mm": 2.e-5, "force_abs_N": 2.e-3,
                       "moment_abs_Nmm": 2.e-1},
        "native_solve_executed": False,
        "qualified_for_design": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "complete_joint_validated": False,
        "limits": [
            "The two physical points and their springs are a method coupon, not wood, a frame, or a floor model.",
            "Spring stiffnesses are selected only to define known coupled matrices.",
            "The normal SPRINGA branches verify only the fixture compression states, not contact history or capacity.",
            "The result tests this fixed 2x2 source-row/pivot transform and reaction map only.",
            "No floor friction, anchorage, capacity, construction condition, or complete-joint acceptance is established.",
        ],
    }
    record = record_structure(model, metadata)
    record["fixed_dofs"] = fixed_dofs
    record["boundary_conditions"] = boundaries

    def real(value):
        token = format(float(value), ".14g")
        if "." not in token:
            if "e" in token.lower():
                mantissa, exponent = token.lower().split("e")
                token = mantissa + ".0e" + exponent
            else:
                token += ".0"
        return token

    lines = [
        "*HEADING",
        "Transformed floor reaction known answer; input only",
        "*NODE,NSET=N",
    ]
    lines.extend(
        f"{tag},{real(xyz[0])},{real(xyz[1])},{real(xyz[2])}"
        for tag, xyz in model.nodes.items()
    )
    for group, element_ids in model.groups.items():
        kind = model.elements[element_ids[0]][0]
        lines.append(f"*ELEMENT,TYPE={kind},ELSET={group}")
        lines.extend(",".join(map(str, [eid, *model.elements[eid][1]]))
                     for eid in element_ids)
    for spring in model.springs:
        lines.extend([
            f"*SPRING,ELSET={spring['group']}",
            f"{spring['dof']},{spring['dof']}",
            real(spring["stiffness_n_per_mm"]),
        ])
    for normal in normal_records:
        lines.extend([
            f"*SPRING,ELSET={normal['name']},NONLINEAR",
            "",
            "0.0,-10.0",
            "0.0,0.0",
            "1000.0,10.0",
        ])
    for terms in model.equations:
        lines.extend(["*EQUATION", str(len(terms))])
        lines.append(",".join(
            f"{node},{dof},{real(coefficient)}"
            for node, dof, coefficient in terms
        ))
    lines.append("*BOUNDARY")
    lines.extend(
        f"{item['node']},{item['first_dof']},{item['last_dof']},{real(item['value'])}"
        for item in boundaries
    )
    for answer in answers:
        lines.extend([
            "*STEP,NLGEOM,NLGEOM=NO,INC=40",
            "*STATIC",
            "0.1,1.0,1.e-6,0.25",
            "*CLOAD,OP=NEW",
        ])
        for name in ("A", "B"):
            loads = answer["loads_by_body_N"][name]
            lines.append(f"{body_nodes[name]},1,{real(loads['x'])}")
            lines.append(f"{body_nodes[name]},3,{real(loads['z'])}")
        lines.extend(["*NODE PRINT,NSET=N,FREQUENCY=1", "U,RF", "*END STEP"])

    deck = "\n".join(lines) + "\n"
    return model, record, metadata, deck


def main():
    _, record, _, deck = build_fixture()
    (HERE / "model.inp").write_text(deck)
    (HERE / "model.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print("Wrote unfrozen input-only model.inp and model.json; no native solve or freeze was performed.")


if __name__ == "__main__":
    main()
