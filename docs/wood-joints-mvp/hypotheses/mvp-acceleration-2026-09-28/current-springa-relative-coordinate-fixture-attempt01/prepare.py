"""Create an unfrozen, input-only two-body SPRINGA relative-coordinate fixture."""
import json
from pathlib import Path

from fea.horizontal_panel_frame import Structure, equation_lines, record_structure

HERE = Path(__file__).resolve().parent


def build_fixture():
    model = Structure()
    nodes = {}
    for name, xyz in (
        ("A", (0., 0., 0.)),
        ("B", (0., 0., 0.)),
        ("SA", (0., 0., 0.)),
        ("GA", (0., 0., 0.)),
        ("SB", (0., 0., 0.)),
        ("GB", (0., 0., 0.)),
        ("PA", (0., 0., 0.)),
        ("PB", (0., 0., 0.)),
        ("Q", (100., 0., 0.)),
        ("GQ", (0., 0., 0.)),
    ):
        nodes[name] = model.node(xyz)

    a, b = nodes["A"], nodes["B"]
    sa, ga = nodes["SA"], nodes["GA"]
    sb, gb = nodes["SB"], nodes["GB"]
    pa, pb = nodes["PA"], nodes["PB"]
    q, gq = nodes["Q"], nodes["GQ"]

    # Separate endpoint pairs make each native SPRING2 support force auditable.
    model.spring(sa, ga, 100., "SUPPORT_A", dofs=(1,))
    model.spring(sb, gb, 200., "SUPPORT_B", dofs=(1,))
    model.element("SPRINGA", [q, gq], "RELATIVE_JOINT")

    # The equation order follows the intended nested kinematics:
    # support/projected slaves -> body coordinates -> relative coordinate.
    model.equations = [
        [(sa, 1, 1.), (a, 1, -1.)],
        [(sb, 1, 1.), (b, 1, -1.)],
        [(pa, 1, 1.), (a, 1, -1.)],
        [(pb, 1, 1.), (b, 1, -1.)],
        [(q, 1, 1.), (pb, 1, -1.), (pa, 1, 1.)],
    ]
    model.fixed.update((ga, gb, gq))
    model.loads = {a: [-30., 0., 0.], b: [30., 0., 0.]}

    load_steps = [
        {"time": 1., "loads_N": {str(a): -30., str(b): 30.}},
        {"time": 2., "loads_N": {str(a): 30., str(b): -30.}},
        {"time": 3., "loads_N": {str(a): -30., str(b): 30.}},
    ]
    known_answers = [
        {
            "time": 1., "loads_N": {str(a): -30., str(b): 30.},
            "u_a_mm": -6. / 35., "u_b_mm": 3. / 35., "q_mm": 9. / 35.,
            "support_a_internal_N": -120. / 7.,
            "support_b_internal_N": 120. / 7.,
            "joint_internal_N": 90. / 7.,
            "joint_action_on_a_N": 90. / 7.,
            "joint_action_on_b_N": -90. / 7.,
            "exact": {
                "u_a_mm": "-6/35", "u_b_mm": "3/35", "q_mm": "9/35",
                "support_a_internal_N": "-120/7",
                "support_b_internal_N": "120/7",
                "joint_internal_N": "90/7",
            },
        },
        {
            "time": 2., "loads_N": {str(a): 30., str(b): -30.},
            "u_a_mm": .3, "u_b_mm": -.15, "q_mm": -.45,
            "support_a_internal_N": 30., "support_b_internal_N": -30.,
            "joint_internal_N": 0.,
            "joint_action_on_a_N": 0., "joint_action_on_b_N": 0.,
            "exact": {
                "u_a_mm": "3/10", "u_b_mm": "-3/20", "q_mm": "-9/20",
                "support_a_internal_N": "30", "support_b_internal_N": "-30",
                "joint_internal_N": "0",
            },
        },
        {
            "time": 3., "loads_N": {str(a): -30., str(b): 30.},
            "u_a_mm": -6. / 35., "u_b_mm": 3. / 35., "q_mm": 9. / 35.,
            "support_a_internal_N": -120. / 7.,
            "support_b_internal_N": 120. / 7.,
            "joint_internal_N": 90. / 7.,
            "joint_action_on_a_N": 90. / 7.,
            "joint_action_on_b_N": -90. / 7.,
            "exact": {
                "u_a_mm": "-6/35", "u_b_mm": "3/35", "q_mm": "9/35",
                "support_a_internal_N": "-120/7",
                "support_b_internal_N": "120/7",
                "joint_internal_N": "90/7",
            },
        },
    ]

    metadata = {
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "One disconnected two-moving-body scalar support and relative SPRINGA/MPC known-answer fixture; 3 load steps; no frame or joint",
        "parent_run_budget": {
            "max_launches": 1,
            "timeout_seconds": 60,
            "run_id": "current-springa-relative-coordinate-fixture-attempt01",
        },
        "manual": {
            "url": "https://www.dhondt.de/ccx_2.23.pdf",
            "sections": ["6.2.42 SPRINGA (p129)", "7.122 SPRING (pp598-599)", "7.56 *EQUATION (pp504-505)"],
            "interpretation": "SPRINGA force-versus-elongation table; SPRING2 linear support stiffness; homogeneous linear equations eliminate their first listed degree of freedom",
        },
        "node_roles": {str(tag): name for name, tag in nodes.items()},
        "relative_coordinate": {
            "equation": "u_Q = u_PB - u_PA = u_B - u_A",
            "spring_element": 3,
            "spring_nodes": [q, gq],
            "initial_span_mm": 100.,
            "physical_action_on_A": "joint_internal_N",
            "physical_action_on_B": "-joint_internal_N",
            "ground_endpoint_is_numerical_only": True,
            "zero_knot_tangent_rationale": "The pinned 2.23 ident routine selects the right-hand table interval at an exact knot. Orienting Q=u_B-u_A and using 50*max(Q,0) makes the right-hand tangent at zero the closed-side 50 N/mm without preload or stiffness regularization.",
        },
        "support_springs": [
            {"name": "SUPPORT_A", "element": 1, "nodes": [sa, ga], "stiffness_N_per_mm": 100.},
            {"name": "SUPPORT_B", "element": 2, "nodes": [sb, gb], "stiffness_N_per_mm": 200.},
        ],
        "loads_by_step": load_steps,
        "known_answer": {"steps": known_answers},
        "tolerances": {"u_abs_mm": 2.e-6, "force_abs_N": 2.e-3},
        "fixed_dofs": {
            str(n): [[2, 3]] for n in (a, b, sa, sb, pa, pb, q)
        } | {str(n): [[1, 3]] for n in (ga, gb, gq)},
        "native_nonlinear_spring_laws": [
            {
                "element": 3, "nodes": [q, gq], "initial_span_mm": 100.,
                "force_vs_elongation_N_mm": [[0., -10.], [0., 0.], [500., 10.]],
                "law": "50*max(delta_mm,0)",
            }
        ],
        "native_solve_executed": False,
        "qualified_for_design": False,
        "limits": [
            "The two bodies are scalar coordinates, not frame members or a joint model.",
            "The 100 mm SPRINGA span and its grounded endpoint are numerical devices only.",
            "Linear supports are known-answer fixture values, not floor or member properties.",
            "The fixture checks MPC force transfer and native endpoint force output; it does not validate member demand recovery or design capacity.",
        ],
    }

    record = record_structure(model, metadata)
    record["fixed_dofs"] = metadata["fixed_dofs"]
    record["boundary_conditions"] = [
        {"node": n, "first_dof": 2, "last_dof": 3, "value": 0.}
        for n in (a, b, sa, sb, pa, pb, q)
    ] + [
        {"node": n, "first_dof": 1, "last_dof": 3, "value": 0.}
        for n in (ga, gb, gq)
    ]

    lines = [
        "*HEADING",
        "Two-body relative SPRINGA known answer; not a frame or joint",
        "*NODE,NSET=N",
    ]
    lines += [
        f"{tag},{xyz[0]:.1f},{xyz[1]:.1f},{xyz[2]:.1f}"
        for tag, xyz in model.nodes.items()
    ]
    for group, element_ids in model.groups.items():
        kind = model.elements[element_ids[0]][0]
        lines.append(f"*ELEMENT,TYPE={kind},ELSET={group}")
        for element_id in element_ids:
            lines.append(",".join(map(str, [element_id, *model.elements[element_id][1]])))
    for spring in model.springs:
        lines += [
            f"*SPRING,ELSET={spring['group']}",
            f"{spring['dof']},{spring['dof']}",
            str(spring["stiffness_n_per_mm"]),
        ]
    lines += [
        "*SPRING,ELSET=RELATIVE_JOINT,NONLINEAR",
        "",
        "0.,-10.",
        "0.,0.",
        "500.,10.",
    ]
    for terms in model.equations:
        lines += equation_lines(terms)
    lines.append("*BOUNDARY")
    lines += [f"{n},2,3,0." for n in (a, b, sa, sb, pa, pb, q)]
    lines += [f"{n},1,3,0." for n in (ga, gb, gq)]
    for step in load_steps:
        lines += [
            "*STEP,NLGEOM,NLGEOM=NO,INC=40",
            "*STATIC",
            "0.1,1.,1.e-6,0.25",
            "*CLOAD,OP=NEW",
        ]
        lines += [f"{node},1,{force:.1f}" for node, force in step["loads_N"].items()]
        lines += ["*NODE PRINT,NSET=N", "U", "RF", "*END STEP"]

    return model, record, "\n".join(lines) + "\n"


def main():
    _, record, deck = build_fixture()
    (HERE / "model.inp").write_text(deck)
    (HERE / "model.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print("Wrote unfrozen input-only model.inp and model.json; no native run or freeze was performed.")


if __name__ == "__main__":
    main()
