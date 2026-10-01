"""Verify the staged-floor proposal's exact scalar mechanics and card plan."""
from fractions import Fraction as F
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from prepare import build_fixture, build_nonzero_release_probe, build_restart_continuation


def _open(Ft,Fq):
    # K^-1 = (1/3) [[2,-1],[-1,2]].
    return ((2*Ft-Fq)/3,(-Ft+2*Fq)/3)


def _held(Ft,Fq,tref):
    q=(Fq-tref)/4
    N=2*max(q,F(0))
    T=Ft-(2*tref+q)
    return tref,q,N,T


def verify():
    _,record,metadata,deck=build_fixture()
    release=build_nonzero_release_probe()

    # The two independent unit supports and one unit relative spring have
    # energy .5*t^2 + .5*q^2 + .5*(t+q)^2.
    K=((F(2),F(1)),(F(1),F(2)))
    assert K==tuple(tuple(map(F,row)) for row in metadata["structural_matrix_N_per_mm"])
    assert metadata["generalized_coordinates"]=="t=u_T_BODY,1; q=-u_Q_BODY,2 (positive q is normal compression)"

    for row in metadata["expected_states"]:
        Ft,Fq=F(row["Ft_N"]),F(row["Fq_N"])
        if row["stick"].startswith("reference_"):
            tref=F(row["stick"].split("reference_",1)[1].split("_until",1)[0])
            t,q,N,T=_held(Ft,Fq,tref)
        else:
            t,q=_open(Ft,Fq)
            N=2*max(q,F(0))
            T=F(0)
        observed=tuple(map(F,(row["t_mm"],row["q_mm"],row["N_N"],row["T_generalized_N"])))
        assert (t,q,N,T)==observed,(row["label"],(t,q,N,T),observed)
        assert -T==F(row["physical_support_reaction_on_body_N"])
        assert q<=0 or N==2*q

    target=metadata["release_probe_target"]
    Ft,Fq=map(F,target["external_Ft_Fq_N"])
    held=_held(Ft,Fq,F(-2))
    opened=_open(Ft,Fq)
    assert held==tuple(F(target["held_state"][k]) for k in ("t_mm","q_mm","N_N","T_generalized_N"))
    assert -held[3]==F(target["held_state"]["physical_support_reaction_on_body_N"])
    assert opened==tuple(F(target["same_load_after_release"][k]) for k in ("t_mm","q_mm"))
    assert opened[1]<0 and 2*max(opened[1],F(0))==0
    assert F(target["same_load_after_release"]["T_generalized_N"])==0
    assert F(target["same_load_after_release"]["physical_support_reaction_on_body_N"])==0

    # These are syntax/placement guards only. Pinned native behavior still
    # requires the parent's controlled known-answer run.
    assert deck.count("*EQUATION\n")==2
    assert "*EQUATION,REMOVE" not in deck.upper()
    assert deck.count("*STEP,NLGEOM,NLGEOM=NO,INC=40")==metadata["deck_stage_count"]
    assert all(gate in metadata["step_method"]["native_stdout_gates"] for gate in (
        "Newton-Raphson iterative procedure is active",
        "effects are turned off",
        "Nonlinear geometric effects are taken into account must be absent",
    ))
    assert deck.count("*BOUNDARY,OP=MOD,AMPLITUDE=CAPTURE")==2
    assert "*BOUNDARY,OP=NEW" in deck
    assert "*RESTART,WRITE,FREQUENCY=1" in deck
    assert "*AMPLITUDE,NAME=CAPTURE\n0.0,1.0,1.0,1.0" in deck
    assert build_restart_continuation().splitlines()[0]=="*RESTART,READ,STEP=2"
    assert "*AMPLITUDE,NAME=CAPTURE" in build_restart_continuation().splitlines()[1]
    assert release.count("*BOUNDARY,OP=NEW")==1
    release_reset=release.split("*BOUNDARY,OP=NEW\n",1)[1].split("*CLOAD",1)[0]
    assert ",7,1,1," not in release_reset
    for line in ("7,2,3,0.0",):
        assert line in release_reset
    assert release.count("*RESTART,WRITE,FREQUENCY=1")==1
    assert not metadata["native_solve_executed"]
    assert not metadata["parent_native_readiness"]

    on_disk=json.loads((HERE/"known-answer.json").read_text())
    assert on_disk["states"]==metadata["expected_states"]
    normalized_equations=[[list(term) for term in equation] for equation in record["equations"]]
    assert normalized_equations==[
        [[metadata["node_roles"]["T_BODY"],1,1.],[metadata["node_roles"]["T_REFERENCE"],1,-1.]],
        [[metadata["node_roles"]["NORMAL_PROJECTION"],2,1.],[metadata["node_roles"]["Q_BODY"],2,-1.]],
    ]
    return {
        "status":"PASS_SYNTHETIC_MECHANICS_AND_INPUT_CARD_PLAN",
        "staged_state_count":len(metadata["expected_states"]),
        "nonzero_reaction_release":target,
        "native_solve_executed":False,
        "limitations":[
            "This does not verify CalculiX step/restart behavior; the coupon remains unrun.",
            "It does not select the coupled active normal set or establish a frame gauge/rank.",
        ],
    }


if __name__=="__main__":
    result=verify()
    print(result["status"])
