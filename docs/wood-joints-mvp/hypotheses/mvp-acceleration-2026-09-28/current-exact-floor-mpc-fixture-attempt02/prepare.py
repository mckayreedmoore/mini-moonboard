"""Create an unfrozen known-answer coupon for exact floor MPC force recovery."""
from fractions import Fraction
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.horizontal_panel_frame import Structure, equation_lines, record_structure


def _hand_answers():
    """Derive exact scalar answers independently from the two spring laws."""
    cases = [
        (1., 6, -20, Fraction(-1, 10)),
        (2., -4, -40, Fraction(-1, 5)),
    ]
    answers = []
    matrix = ((Fraction(20), Fraction(5)),
              (Fraction(5), Fraction(100)))
    for time, wx, wz, z in cases:
        x = Fraction(0)
        q = -z
        projected = x + z / 4
        f_projected = 20 * projected
        f_vertical = Fraction(395, 4) * z
        f_normal = 100 * q
        f_internal_x = matrix[0][0] * x + matrix[0][1] * z
        f_internal_z = matrix[1][0] * x + matrix[1][1] * z
        rx = f_internal_x - wx
        rz = f_normal

        assert f_internal_x == f_projected
        assert f_internal_z == f_projected / 4 + f_vertical
        assert Fraction(wx) + rx - f_projected == 0
        assert Fraction(wz) - f_projected / 4 - f_vertical + f_normal == 0

        answers.append({
            "time": time,
            "external_Wx_N": wx,
            "external_Wz_N": wz,
            "u_x_mm": float(x),
            "u_z_mm": float(z),
            "projected_coordinate_s_mm": float(projected),
            "projected_spring_internal_N": float(f_projected),
            "vertical_spring_internal_N": float(f_vertical),
            "normal_coordinate_q_mm": float(q),
            "normal_spring_internal_N": float(f_normal),
            "floor_tangential_reaction_N": float(rx),
            "floor_normal_reaction_N": float(rz),
            "exact": {
                "u_x_mm": "0",
                "u_z_mm": str(z),
                "projected_coordinate_s_mm": str(projected),
                "projected_spring_internal_N": str(f_projected),
                "vertical_spring_internal_N": str(f_vertical),
                "normal_coordinate_q_mm": str(q),
                "normal_spring_internal_N": str(f_normal),
                "floor_tangential_reaction_N": str(rx),
                "floor_normal_reaction_N": str(rz),
            },
        })
    return answers


def build_fixture():
    model = Structure()
    node_roles = {}
    for name, xyz in (
        ("P", (0., 0., 0.)),
        ("FLOOR_REF", (0., 0., 0.)),
        ("XZ_PROJECTION", (0., 0., 0.)),
        ("XZ_ANCHOR", (0., 0., 0.)),
        ("Z_PROJECTION", (0., 0., 0.)),
        ("Z_ANCHOR", (0., 0., 0.)),
        ("NORMAL_Q", (0., 0., 100.)),
        ("NORMAL_GROUND", (0., 0., 0.)),
    ):
        node_roles[name] = model.node(xyz)

    p = node_roles["P"]
    ref = node_roles["FLOOR_REF"]
    xz = node_roles["XZ_PROJECTION"]
    xz_anchor = node_roles["XZ_ANCHOR"]
    zproj = node_roles["Z_PROJECTION"]
    z_anchor = node_roles["Z_ANCHOR"]
    normal = node_roles["NORMAL_Q"]
    normal_ground = node_roles["NORMAL_GROUND"]

    # Isolated scalar carrier DOFs map to the physical x-z point.
    model.spring(xz, xz_anchor, 20., "STRUCTURAL_XZ", dofs=(1,))
    model.spring(zproj, z_anchor, 98.75, "STRUCTURAL_Z", dofs=(3,))
    model.element("SPRINGA", [normal, normal_ground], "FLOOR_NORMAL")

    # Each first term is a unique dependent DOF. P.x is the exact-stick pivot.
    model.equations = [
        [(p, 1, 1.), (ref, 1, -1.)],
        [(xz, 1, 1.), (p, 1, -1.), (p, 3, -.25)],
        [(zproj, 3, 1.), (p, 3, -1.)],
        [(normal, 3, 1.), (p, 3, 1.)],
    ]
    dependent = [(terms[0][0], terms[0][1]) for terms in model.equations]
    if len(dependent) != len(set(dependent)):
        raise AssertionError("A DOF is dependent in more than one equation")

    # Fully grounded numerical anchors; only the physical point has free z.
    model.fixed.update((ref, xz_anchor, z_anchor, normal_ground))
    model.loads = {p: [6., 0., -20.]}

    boundaries = [
        {"node": p, "first_dof": 2, "last_dof": 2, "value": 0.},
        {"node": ref, "first_dof": 1, "last_dof": 3, "value": 0.},
        {"node": xz, "first_dof": 2, "last_dof": 3, "value": 0.},
        {"node": xz_anchor, "first_dof": 1, "last_dof": 3, "value": 0.},
        {"node": zproj, "first_dof": 1, "last_dof": 2, "value": 0.},
        {"node": z_anchor, "first_dof": 1, "last_dof": 3, "value": 0.},
        {"node": normal, "first_dof": 1, "last_dof": 2, "value": 0.},
        {"node": normal_ground, "first_dof": 1, "last_dof": 3, "value": 0.},
    ]
    boundary_dofs = set()
    for item in boundaries:
        boundary_dofs.update((item["node"], dof)
                             for dof in range(item["first_dof"], item["last_dof"] + 1))
    if boundary_dofs.intersection(dependent):
        raise AssertionError("A dependent DOF is also fixed by an SPC")

    answers = _hand_answers()
    load_steps = [
        {"time": 1., "loads": [{"node": p, "dof": 1, "force_N": 6.},
                                {"node": p, "dof": 3, "force_N": -20.}]},
        {"time": 2., "loads": [{"node": p, "dof": 1, "force_N": -4.},
                                {"node": p, "dof": 3, "force_N": -40.}]},
    ]

    metadata = {
        "schema": "current_exact_floor_mpc_fixture/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": (
            "One physical 2D x-z node, exact x-stick equation to a fixed reference, "
            "two isolated linear spring projections, and one compression-only "
            "SPRINGA normal; two static known-answer cases; no frame or joint"
        ),
        "parent_run_budget": {
            "max_launches": 1,
            "timeout_seconds": 60,
            "run_id": "current-exact-floor-mpc-fixture-attempt02",
        },
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
            "sections": [
                "6.2.42 SPRINGA (p129)",
                "7.56 *EQUATION (pp504-505)",
                "7.122 SPRING (pp598-599)",
                "7.99 *NODE PRINT (p567)",
            ],
            "interpretation": (
                "*EQUATION eliminates its first listed DOF, which cannot also be "
                "dependent elsewhere or an SPC; NODE PRINT RF reports external forces "
                "including reactions and applied concentrated/distributed loads"
            ),
        },
        "node_roles": node_roles,
        "physical_node": p,
        "ground_reference_node": ref,
        "equations": {
            "floor_stick": "u_Px - u_floor_ref_x = 0; u_Px is the unique dependent pivot",
            "xz_projection": "u_XZ,1 = u_Px + 0.25*u_Pz",
            "vertical_projection": "u_Z,3 = u_Pz",
            "normal_coordinate": "q = u_NORMAL_Q,3 = -u_Pz",
        },
        "dependent_dofs": dependent,
        "fixed_dofs": {
            str(p): [[2, 2]],
            str(ref): [[1, 3]],
            str(xz): [[2, 3]],
            str(xz_anchor): [[1, 3]],
            str(zproj): [[1, 2]],
            str(z_anchor): [[1, 3]],
            str(normal): [[1, 2]],
            str(normal_ground): [[1, 3]],
        },
        "boundary_conditions": boundaries,
        "structural_matrix_N_per_mm": [[20., 5.], [5., 100.]],
        "structural_springs": [
            {"name": "STRUCTURAL_XZ", "coordinate": "s=x+0.25*z", "stiffness_N_per_mm": 20.,
             "endpoint": xz, "ground": xz_anchor, "dof": 1},
            {"name": "STRUCTURAL_Z", "coordinate": "z", "stiffness_N_per_mm": 98.75,
             "endpoint": zproj, "ground": z_anchor, "dof": 3},
        ],
        "normal_law": {
            "element": 3,
            "endpoint": normal,
            "ground": normal_ground,
            "initial_span_mm": 100.,
            "coordinate": "q=-z; positive q is physical compression",
            "current_length_mm": "100+q while q is within this fixture range",
            "force_law_N": "100*max(q_mm,0)",
            "force_N_then_elongation_mm_table": [[0., -10.], [0., 0.], [1000., 10.]],
            "closed_side_tangent_at_zero_N_per_mm": 100.,
            "zero_knot_rule": (
                "The inspected 2.23 ident.f chooses the right-hand interval at an exact knot; "
                "the interval immediately to the right of zero has slope 100 N/mm"
            ),
            "physical_reaction_direction": "+z equals the native internal spring force through q=-z",
        },
        "loads_by_step": load_steps,
        "known_answer": {"steps": answers},
        "tolerances": {"u_abs_mm": 2.e-6, "force_abs_N": 2.e-3},
        "reference_rf_candidate_maps": [
            {"name": "RF_REFERENCE", "formula": "RFref"},
            {"name": "NEGATIVE_RF_REFERENCE", "formula": "-RFref"},
            {"name": "RF_REFERENCE_MINUS_DEPENDENT_CLOAD", "formula": "RFref-Wx_dep"},
            {"name": "NEGATED_RF_REFERENCE_MINUS_DEPENDENT_CLOAD", "formula": "-RFref-Wx_dep"},
        ],
        "native_solve_executed": False,
        "qualified_for_design": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "complete_joint_validated": False,
        "limits": [
            "The physical system is one scalar 2D point, not a frame or corner model.",
            "Spring stiffnesses are chosen only to give a known matrix, not as floor, wood, or connector properties.",
            "The normal SPRINGA branch checks a scalar compression law, not floor contact history or capacity.",
            "RF-reference sign and transfer of a CLOAD on the dependent physical DOF remain unknown until the parent-run assessor passes.",
            "No floor friction, anchorage, capacity, construction condition, or complete-joint acceptance is established.",
        ],
    }
    record = record_structure(model, metadata)
    record["fixed_dofs"] = metadata["fixed_dofs"]
    record["boundary_conditions"] = boundaries

    def number(value):
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
        "Exact floor MPC reaction known answer; input only",
        "*NODE,NSET=N",
    ]
    lines += [
        f"{tag},{number(xyz[0])},{number(xyz[1])},{number(xyz[2])}"
        for tag, xyz in model.nodes.items()
    ]
    for group, element_ids in model.groups.items():
        kind = model.elements[element_ids[0]][0]
        lines.append(f"*ELEMENT,TYPE={kind},ELSET={group}")
        lines += [",".join(map(str, [eid, *model.elements[eid][1]])) for eid in element_ids]
    for spring in model.springs:
        lines += [
            f"*SPRING,ELSET={spring['group']}",
            f"{spring['dof']},{spring['dof']}",
            number(spring["stiffness_n_per_mm"]),
        ]
    lines += [
        "*SPRING,ELSET=FLOOR_NORMAL,NONLINEAR",
        "",
        "0.,-10.",
        "0.,0.",
        "1000.,10.",
    ]
    for terms in model.equations:
        lines += equation_lines(terms)
    lines.append("*BOUNDARY")
    lines += [
        f"{item['node']},{item['first_dof']},{item['last_dof']},{number(item['value'])}"
        for item in boundaries
    ]
    for step, expected in zip(load_steps, answers, strict=True):
        lines += [
            "*STEP,NLGEOM,NLGEOM=NO,INC=40",
            "*STATIC",
            "0.1,1.,1.e-6,0.25",
            "*CLOAD,OP=NEW",
            f"{p},1,{number(expected['external_Wx_N'])}",
            f"{p},3,{number(expected['external_Wz_N'])}",
            "*NODE PRINT,NSET=N,FREQUENCY=1",
            "U,RF",
            "*END STEP",
        ]
    deck = "\n".join(lines) + "\n"
    return model, record, metadata, deck


def main():
    _, record, _, deck = build_fixture()
    (HERE / "model.inp").write_text(deck)
    (HERE / "model.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print("Wrote unfrozen input-only model.inp and model.json; no native solve or freeze was performed.")


if __name__ == "__main__":
    main()
