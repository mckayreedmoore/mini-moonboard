"""Build unfrozen, input-only CalculiX coupon decks for staged floor SPCs."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.horizontal_panel_frame import Structure, equation_lines, record_structure


def _number(value):
    token = format(float(value), ".14g")
    if "." not in token:
        if "e" in token.lower():
            mantissa, exponent = token.lower().split("e")
            token = mantissa + ".0e" + exponent
        else:
            token += ".0"
    return token


def _spring(model, first, second, dofs, stiffness, group, name):
    eid = model.element("SPRING2", [first, second], group)
    model.springs.append({
        "name": name, "element": eid, "group": group,
        "nodes": [first, second], "dofs": list(dofs),
        "stiffness_n_per_mm": stiffness,
        "bearing_closed_assumption": False,
    })


def _make_model():
    model = Structure()
    tags = {}
    for name, xyz in (
        ("T_BODY", (0., 0., 0.)),
        ("Q_BODY", (0., 0., 0.)),
        ("T_GROUND", (0., 0., 0.)),
        ("Q_GROUND", (0., 0., 0.)),
        ("NORMAL_PROJECTION", (0., -100., 0.)),
        ("NORMAL_GROUND", (0., 0., 0.)),
        ("T_REFERENCE", (0., 0., 0.)),
    ):
        tags[name] = model.node(xyz)

    t = tags["T_BODY"]
    q_body = tags["Q_BODY"]
    t_ground = tags["T_GROUND"]
    q_ground = tags["Q_GROUND"]
    normal_projection = tags["NORMAL_PROJECTION"]
    normal_ground = tags["NORMAL_GROUND"]
    t_reference = tags["T_REFERENCE"]

    # In generalized coordinates (t, q), the body DOFs are u_Tx=t and
    # u_Qy=-q. Two unit ground springs and a unit (T_x,Q_y) SPRING2 make
    # K=[[2,1],[1,2]] exactly.
    _spring(model, t, t_ground, (1, 1), 1., "T_GROUND_SPRING", "T_GROUND")
    _spring(model, q_body, q_ground, (2, 2), 1., "Q_GROUND_SPRING", "Q_GROUND")
    _spring(model, t, q_body, (1, 2), 1., "T_PLUS_Q_SPRING", "T_PLUS_Q")
    normal_eid = model.element(
        "SPRINGA", [normal_ground, normal_projection], "UNILATERAL_NORMAL")

    # The physical pivots are the first/dependent terms. Their separate scalar
    # references are masters, so SPCs may be added/removed on those masters.
    model.equations = [
        [(t, 1, 1.), (t_reference, 1, -1.)],
        [(normal_projection, 2, 1.), (q_body, 2, -1.)],
    ]
    dependent = [(terms[0][0], terms[0][1]) for terms in model.equations]
    if len(dependent) != len(set(dependent)):
        raise AssertionError("A DOF is dependent in more than one equation")

    permanent_boundaries = [
        {"node": t, "first_dof": 2, "last_dof": 3, "value": 0.},
        {"node": q_body, "first_dof": 1, "last_dof": 1, "value": 0.},
        {"node": q_body, "first_dof": 3, "last_dof": 3, "value": 0.},
        {"node": t_ground, "first_dof": 1, "last_dof": 3, "value": 0.},
        {"node": q_ground, "first_dof": 1, "last_dof": 3, "value": 0.},
        {"node": normal_projection, "first_dof": 1, "last_dof": 1, "value": 0.},
        {"node": normal_projection, "first_dof": 3, "last_dof": 3, "value": 0.},
        {"node": normal_ground, "first_dof": 1, "last_dof": 3, "value": 0.},
        {"node": t_reference, "first_dof": 2, "last_dof": 3, "value": 0.},
    ]
    boundary_dofs = {
        (item["node"], dof)
        for item in permanent_boundaries
        for dof in range(item["first_dof"], item["last_dof"] + 1)
    }
    if boundary_dofs.intersection(dependent):
        raise AssertionError("An equation-dependent DOF is also prescribed")

    model.fixed.update((t_ground, q_ground, normal_ground))
    model.loads = {t: [-4., 0., 0.], q_body: [0., 3., 0.]}
    return model, tags, permanent_boundaries, normal_eid


def _prefix(model, tags, permanent_boundaries, normal_eid):
    lines = [
        "*HEADING",
        "Staged floor MPC event/reference mapping coupon; input proposal only",
        "*NODE,NSET=ALL",
    ]
    lines += [
        f"{node},{_number(xyz[0])},{_number(xyz[1])},{_number(xyz[2])}"
        for node, xyz in model.nodes.items()
    ]
    for group, eids in model.groups.items():
        kind = model.elements[eids[0]][0]
        lines.append(f"*ELEMENT,TYPE={kind},ELSET={group}")
        lines.extend(",".join(map(str, [eid, *model.elements[eid][1]])) for eid in eids)
    for spring in model.springs:
        d1, d2 = spring["dofs"]
        lines += [
            f"*SPRING,ELSET={spring['group']}",
            f"{d1},{d2}",
            _number(spring["stiffness_n_per_mm"]),
        ]
    lines += [
        "*SPRING,ELSET=UNILATERAL_NORMAL,NONLINEAR",
        "",
        "0.0,-10.0",
        "0.0,0.0",
        "20.0,10.0",
        "*AMPLITUDE,NAME=CAPTURE",
        "0.0,1.0,1.0,1.0",
    ]
    for terms in model.equations:
        lines.extend(equation_lines(terms))
    lines.append("*BOUNDARY")
    lines.extend(
        f"{b['node']},{b['first_dof']},{b['last_dof']}"
        for b in permanent_boundaries
    )
    return lines


def _step(lines, *, change_loads=(), boundary=None, op="MOD", capture=False,
          restart=False, cload_op="MOD", title=""):
    lines.append(f"** {title}")
    lines += ["*STEP,NLGEOM,NLGEOM=NO,INC=40", "*STATIC", "0.1,1.0,1.e-8,0.25"]
    if restart:
        lines.append("*RESTART,WRITE,FREQUENCY=1")
    if boundary is not None:
        amp = ",AMPLITUDE=CAPTURE" if capture else ""
        lines.append(f"*BOUNDARY,OP={op}{amp}")
        lines.extend(
            f"{b['node']},{b['first_dof']},{b['last_dof']},{_number(b['value'])}"
            for b in boundary
        )
    if change_loads:
        lines.append(f"*CLOAD,OP={cload_op}")
        lines.extend(f"{node},{dof},{_number(force)}" for node, dof, force in change_loads)
    lines += ["*NODE PRINT,NSET=ALL,FREQUENCY=1", "U,RF", "*END STEP"]


def build_fixture():
    """Return (Structure, input-record, metadata, full staged coupon deck)."""
    model, tags, permanent, normal_eid = _make_model()
    answers = [
        {"label":"settled_open", "Ft_N":"-4", "Fq_N":"-3", "t_mm":"-5/3", "q_mm":"-2/3", "N_N":"0", "T_generalized_N":"0", "physical_support_reaction_on_body_N":"0", "stick":"open"},
        {"label":"first_contact_event", "Ft_N":"-4", "Fq_N":"-2", "t_mm":"-2", "q_mm":"0", "N_N":"0", "T_generalized_N":"0", "physical_support_reaction_on_body_N":"0", "stick":"open_until_event"},
        {"label":"first_held_final", "Ft_N":"-4", "Fq_N":"-1", "t_mm":"-2", "q_mm":"1/4", "N_N":"1/2", "T_generalized_N":"-1/4", "physical_support_reaction_on_body_N":"1/4", "stick":"reference_-2"},
        {"label":"unload_before_opening", "Ft_N":"-4", "Fq_N":"-3/2", "t_mm":"-2", "q_mm":"1/8", "N_N":"1/4", "T_generalized_N":"-1/8", "physical_support_reaction_on_body_N":"1/8", "stick":"reference_-2"},
        {"label":"first_opening_event", "Ft_N":"-4", "Fq_N":"-2", "t_mm":"-2", "q_mm":"0", "N_N":"0", "T_generalized_N":"0", "physical_support_reaction_on_body_N":"0", "stick":"reference_-2_until_event"},
        {"label":"first_open_after_release", "Ft_N":"-4", "Fq_N":"-5/2", "t_mm":"-11/6", "q_mm":"-1/3", "N_N":"0", "T_generalized_N":"0", "physical_support_reaction_on_body_N":"0", "stick":"open"},
        {"label":"open_lateral_change", "Ft_N":"-2", "Fq_N":"-3", "t_mm":"-1/3", "q_mm":"-4/3", "N_N":"0", "T_generalized_N":"0", "physical_support_reaction_on_body_N":"0", "stick":"open"},
        {"label":"second_contact_event", "Ft_N":"-2", "Fq_N":"-1", "t_mm":"-1", "q_mm":"0", "N_N":"0", "T_generalized_N":"0", "physical_support_reaction_on_body_N":"0", "stick":"open_until_event"},
        {"label":"reengaged_midpoint", "Ft_N":"-2", "Fq_N":"0", "t_mm":"-1", "q_mm":"1/4", "N_N":"1/2", "T_generalized_N":"-1/4", "physical_support_reaction_on_body_N":"1/4", "stick":"reference_-1"},
        {"label":"reengaged_final", "Ft_N":"-2", "Fq_N":"1", "t_mm":"-1", "q_mm":"1/2", "N_N":"1", "T_generalized_N":"-1/2", "physical_support_reaction_on_body_N":"1/2", "stick":"reference_-1"},
    ]
    metadata = {
        "schema":"staged_floor_native_mapping_coupon/v1",
        "status":"INPUT_ONLY_UNFROZEN_NOT_RUN",
        "synthetic_only":True,
        "native_solve_executed":False,
        "parent_native_readiness":False,
        "source_event_fixture":"current-coupled-contact-event-reference-fixture-attempt01",
        "generalized_coordinates":"t=u_T_BODY,1; q=-u_Q_BODY,2 (positive q is normal compression)",
        "source_contact_law":"N=2*max(q,0) N, right-side tangent at q=0; generalized T is zero whenever scalar reference is free",
        "structural_matrix_N_per_mm":[[2,1],[1,2]],
        "step_method":{
            "card":"*STEP,NLGEOM,NLGEOM=NO,INC=40",
            "static_amplitude":"RAMP (pinned *STEP/*STATIC default; no step-level AMPLITUDE override)",
            "intended_method":"Newton-Raphson iterations enabled; geometric effects off",
            "native_stdout_gates":[
                "Newton-Raphson iterative procedure is active",
                "effects are turned off",
                "Nonlinear geometric effects are taken into account must be absent",
            ],
            "source_basis":"Pinned 2.23 steps.f sequential parameter parsing: bare NLGEOM sets iperturb(1)=2, then NLGEOM=NO sets iperturb(2)=0; this is the validated mode used by current-exact-floor-mpc-fixture-attempt02.",
            "applicability_limit":"That fixture validates the card and nonlinear SPRINGA route on its coupon. This staged event/release deck still requires its own one-launch known-answer check.",
        },
        "normal_element":normal_eid,
        "episode_equations":"u_T_BODY,1-u_T_REFERENCE,1=0 and u_NORMAL_PROJECTION,2-u_Q_BODY,2=0 remain model-level; only the T_REFERENCE,1 SPC changes by step",
        "persistent_equations_no_remove":True,
        "reference_capture_amplitude":"CAPTURE is constant 1 over step time; each newly prescribed scalar receives its recorded event displacement from the first increment",
        "release_operation":"*BOUNDARY,OP=NEW restates all permanent SPCs and omits the reference scalar SPC",
        "restart":"The staged input writes every step. A continuation begins *RESTART,READ,STEP=n and retains the same model/equation set.",
        "reaction_sign_convention":{
            "generalized_T_N":"F_t-(2*t+q), the force exerted by the modeled body on the scalar restraint; it is not the force of the restraint on the physical body.",
            "physical_support_reaction_on_body_N":"-T = (2*t+q)-F_t.",
            "native_candidate_map_1":"RF(T_REFERENCE,1)-CLOAD(T_BODY,1) may recover the physical support reaction on the body, by analogy with the exact-floor MPC fixture; not yet verified for this equation graph.",
            "native_candidate_map_2":"CLOAD(T_BODY,1)-RF(T_REFERENCE,1) may recover generalized T; this is the negative of candidate map 1.",
            "gate":"The native coupon must select the sign by all-increment equilibrium; do not bake either candidate into frame acceptance.",
        },
        "limits":[
            "The two generalized coordinates are coupled by unit SPRING2 elements and do not model a frame.",
            "Normal unilateral states are native constitutive states; their conversion into a joint 100-cell tangential SPC set requires an external coupled active-set/event driver.",
            "No solver run, source freeze, frame input, state selection, zero-load gauge, or tangent-rank analysis is included.",
            "The exact event loads and references are oracle values for this synthetic coupon only; a frame continuation must localize events from accepted output and restart with the measured row coordinates.",
        ],
        "node_roles":tags,
        "permanent_boundary_conditions":permanent,
        "expected_states":answers,
    }
    record=record_structure(model, metadata)
    record["boundary_conditions"]=permanent
    record["node_roles"]=tags
    record["normal_law"]={
        "element":normal_eid,"endpoints":[tags["NORMAL_GROUND"],tags["NORMAL_PROJECTION"]],
        "initial_span_mm":100.,"coordinate":"q=-u_Q_BODY,2; extension of SPRINGA equals q",
        "force_N_then_elongation_mm_table":[[0.,-10.],[0.,0.],[20.,10.]],
        "law":"N=2*max(q,0)",
    }
    lines=_prefix(model,tags,permanent,normal_eid)
    tn, qn, ref = tags["T_BODY"], tags["Q_BODY"], tags["T_REFERENCE"]
    _step(lines, title="01 settle with tangent reference free", restart=True,
          cload_op="NEW", change_loads=[(tn,1,-4.),(qn,2,3.)])
    _step(lines, title="02 ramp to first open-side contact event",
          change_loads=[(qn,2,2.)])
    _step(lines, title="03 capture t=-2 immediately and load the bearing branch",
          boundary=[{"node":ref,"first_dof":1,"last_dof":1,"value":-2.}],
          capture=True, change_loads=[(qn,2,1.)])
    _step(lines, title="04 unload while bearing", change_loads=[(qn,2,1.5)])
    _step(lines, title="05 reach first zero-normal opening event", change_loads=[(qn,2,2.)])
    _step(lines, title="06 release tangent SPC; reissue all permanent SPCs",
          boundary=permanent, op="NEW", change_loads=[(qn,2,2.5)])
    _step(lines, title="07 change lateral load while open",
          change_loads=[(tn,1,-2.),(qn,2,3.)])
    _step(lines, title="08 reach second contact event with reference free",
          change_loads=[(qn,2,1.)])
    _step(lines, title="09 capture t=-1 immediately and re-engage",
          boundary=[{"node":ref,"first_dof":1,"last_dof":1,"value":-1.}],
          capture=True, change_loads=[(qn,2,0.)])
    _step(lines, title="10 complete re-engaged ramp", change_loads=[(qn,2,-1.)])
    deck="\n".join(lines)+"\n"
    metadata["deck_stage_count"]=10
    metadata["release_probe_target"]={
        "external_Ft_Fq_N":["-3","-2"],
        "held_state":{"t_mm":"-2","q_mm":"0","N_N":"0","T_generalized_N":"1","physical_support_reaction_on_body_N":"-1"},
        "same_load_after_release":{"t_mm":"-4/3","q_mm":"-1/3","N_N":"0","T_generalized_N":"0","physical_support_reaction_on_body_N":"0"},
        "purpose":"Prove OP=NEW removes a nonzero tangent SPC reaction without carrying it as an external load; this is a scheduled known-answer state, not the monotone event path.",
    }
    record["release_probe_target"]=metadata["release_probe_target"]
    record["source_equations"]=metadata["episode_equations"]
    return model, record, metadata, deck


def build_nonzero_release_probe():
    """Return a separate short deck testing release at identical load and T=1 N."""
    model, tags, permanent, normal_eid = _make_model()
    lines=_prefix(model,tags,permanent,normal_eid)
    tn, qn, ref = tags["T_BODY"], tags["Q_BODY"], tags["T_REFERENCE"]
    _step(lines, title="active state with nonzero tangent reaction",
          boundary=[{"node":ref,"first_dof":1,"last_dof":1,"value":-2.}],
          capture=True, restart=True, cload_op="NEW",
          change_loads=[(tn,1,-3.),(qn,2,2.)])
    _step(lines, title="release at unchanged external load; no scalar SPC",
          boundary=permanent, op="NEW")
    return "\n".join(lines)+"\n"


def build_restart_continuation():
    """Return a proposed restart continuation from the first event checkpoint."""
    _, tags, permanent, _ = _make_model()
    tn, qn, ref = tags["T_BODY"], tags["Q_BODY"], tags["T_REFERENCE"]
    lines=["*RESTART,READ,STEP=2", "*AMPLITUDE,NAME=CAPTURE", "0.0,1.0,1.0,1.0"]
    _step(lines, title="capture first event reference and continue from checkpoint",
          boundary=[{"node":ref,"first_dof":1,"last_dof":1,"value":-2.}],
          capture=True, change_loads=[(qn,2,1.)])
    _step(lines, title="unload while bearing", change_loads=[(qn,2,1.5)])
    _step(lines, title="reach first opening event", change_loads=[(qn,2,2.)])
    _step(lines, title="release and reissue permanent SPCs", boundary=permanent,
          op="NEW", change_loads=[(qn,2,2.5)])
    _step(lines, title="change lateral load while open",
          change_loads=[(tn,1,-2.),(qn,2,3.)])
    _step(lines, title="reach second contact event", change_loads=[(qn,2,1.)])
    _step(lines, title="capture second reference", boundary=[
        {"node":ref,"first_dof":1,"last_dof":1,"value":-1.}],
        capture=True, change_loads=[(qn,2,0.)])
    _step(lines, title="complete re-engaged ramp", change_loads=[(qn,2,-1.)])
    return "\n".join(lines)+"\n"


def main():
    _, record, metadata, deck = build_fixture()
    (HERE / "coupon-staged.inp").write_text(deck)
    (HERE / "coupon-nonzero-release-probe.inp").write_text(build_nonzero_release_probe())
    (HERE / "coupon-restart-continuation.inp").write_text(build_restart_continuation())
    (HERE / "model.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    (HERE / "known-answer.json").write_text(json.dumps({
        "schema":"staged_floor_native_mapping_coupon_known_answer/v1",
        "synthetic_only":True,
        "structural_matrix_N_per_mm":metadata["structural_matrix_N_per_mm"],
        "generalized_coordinates":metadata["generalized_coordinates"],
        "nodal_force_mapping":"CLOAD(T_BODY,1)=Ft; CLOAD(Q_BODY,2)=-Fq",
        "normal_law":"N=2*max(q,0), q=-U(Q_BODY,2)",
        "tangent_reaction_signs":metadata["reaction_sign_convention"],
        "states":metadata["expected_states"],
        "nonzero_reaction_release":metadata["release_probe_target"],
        "native_solve_executed":False,
    }, indent=2, allow_nan=False)+"\n")
    print("Wrote input-only staged and nonzero-release coupon proposals; no native solve or freeze was performed.")


if __name__ == "__main__":
    main()
