import json
import math
from pathlib import Path

import pytest

from fea.joint_math import bolt_forces, parse_joint_results, radial_loads
from fea.record_joint_results import read_deck


def test_bolt_group_force_and_moment_balance():
    for stations in ((1540,1620,1740,1820), (376,424)):
        forces = bolt_forces(stations,1000,300,100000)
        centre = sum(stations)/len(stations)
        assert sum(f[0] for f in forces) == pytest.approx(1000)
        assert sum(f[1] for f in forces) == pytest.approx(300)
        assert sum((s-centre)*f[1] for s,f in zip(stations,forces,strict=True)) == pytest.approx(100000)
    for stations in ((),(0,),(0,0),(0,math.nan)):
        with pytest.raises(ValueError):
            bolt_forces(stations,1000,0,0)


@pytest.mark.parametrize("force", [(1000,0), (0,-250), (131,712), (-131,-712), (0,0)])
def test_bore_tractions_compressive_radial_and_balanced(force):
    samples = [(i,1+(i%3)/3, math.cos(i*2*math.pi/32), math.sin(i*2*math.pi/32)) for i in range(32)]
    loads = radial_loads(samples, force)
    assert tuple(sum(f[k] for f in loads.values()) for k in (0,1)) == pytest.approx(force)
    for i, _, s, n in samples:
        if i in loads:
            fs,fn = loads[i]
            assert fs*s+fn*n >= -1e-10
            assert fs*n-fn*s == pytest.approx(0,abs=1e-10)
    with pytest.raises(ValueError):
        radial_loads([], (100,0))


def test_joint_parser_rejects_missing_and_unbalanced_output():
    data = "displacements (vx,vy,vz)\n\n 1 0.003 0.004 0\n\nstresses (sxx,syy,szz,sxy,sxz,syz)\n\n 1 1 10 0 0 0 0 0\n\ntotal force for set CLAMP\n\n 0 -1000 0\n"
    result = parse_joint_results(data, [0,1000,0])
    assert result["max_displacement_mm"] == pytest.approx(.005)
    assert result["peak_equivalent_stress_mpa"] == pytest.approx(10)
    with pytest.raises(ValueError,match="integration-point"):
        parse_joint_results(data,[0,1000,0],expected_elements={1})
    complete = data.replace(" 1 1 10 0 0 0 0 0", "\n".join(f" 1 {i} 10 0 0 0 0 0" for i in range(1,5)))
    assert parse_joint_results(complete,[0,1000,0],expected_elements={1})["stress_points"]==4
    with pytest.raises(ValueError,match="integration-point"):
        parse_joint_results(complete.replace("1 4 10", "1 3 10"),[0,1000,0],expected_elements={1})
    with pytest.raises(ValueError):
        parse_joint_results(data,[0,900,0])
    with pytest.raises(ValueError):
        parse_joint_results("",[0,1000,0])
    with pytest.raises(ValueError):
        parse_joint_results(data.replace("0.003", "nan"),[0,1000,0])
    nodal = data.replace("total force", "forces for set CLAMP\n\n 1 0 -1000 0\n\ntotal force")
    assert parse_joint_results(nodal,[0,1000,0],{1:(0,0,2)},[-2000,0,0])["reaction_moment_nmm"] == [2000,0,0]
    with pytest.raises(ValueError,match="moment equilibrium"):
        parse_joint_results(nodal,[0,1000,0],{1:(0,0,2)},[0,0,0])
    with pytest.raises(ValueError,match="Incomplete"):
        parse_joint_results(nodal,[0,1000,0],{1:(0,0,2),2:(0,0,3)},[-2000,0,0])


def test_recording_reconstructs_force_and_moment_from_actual_input():
    data = "*NODE\n1,0,0,2\n2,0,1,0\n*ELEMENT,TYPE=C3D10\n1,1,2\n*CLOAD\n1,2,1000\n2,3,200\n*END STEP\n"
    nodes, force, moment, elements = read_deck(data)
    assert len(nodes)==2
    assert elements=={1}
    assert force==[0,1000,200]
    assert moment==[-1800,0,0]
    with pytest.raises(ValueError):
        read_deck("*NODE\n1,0,0,2\n")


def test_committed_joint_results_have_complete_cases_and_balanced_evidence():
    directory = Path(__file__).parents[1]/"fea/results"
    for mesh in (12,8):
        rows = json.loads((directory/f"joint_bearing_{mesh}_7000.json").read_text())
        assert {(r["part"],r["case"]) for r in rows} == {
            (p,c) for p in ("leg_wall","leg_member","seat_wall","seat_member") for c in ("shear_s","shear_n","moment")}
        assert len(rows)==12
        for r in rows:
            assert r["mesh_mm"]==mesh and r["min_jacobian"]>0
            assert r["nodes"]>0 and r["stress_points"]>0 and r["stress_points"]%4==0
            assert r["peak_equivalent_stress_mpa"]>=r["p95_equivalent_stress_mpa"]>0
            assert r["max_displacement_mm"]>0
            assert max(abs(a+b) for a,b in zip(r["applied_force_n"],r["reaction_n"],strict=True))<.1
            assert max(abs(a+b) for a,b in zip(r["applied_global_moment_nmm"],r["reaction_moment_nmm"],strict=True))<1
            assert len(r["evidence_sha256"])==2
            assert all(len(h)==64 for h in r["evidence_sha256"].values())
