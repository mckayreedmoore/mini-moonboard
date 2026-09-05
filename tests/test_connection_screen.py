import json
import math
from pathlib import Path

import pytest

from fea.solve_connection import final_block, seat_stiffness


def test_final_block_rejects_partial_solve_and_accepts_numeric_final_time():
    first="displacements for set ALLN and time 0.1000000E+00\n\n 1 0. 0. -0.1\n"
    last="displacements for set ALLN and time 0.1000000E+01\n\n 1 0. 0. -1.0\n"
    with pytest.raises(ValueError,match="final-time"):
        final_block(first,"displacements")
    assert "-1.0" in final_block(first+"\n"+last,"displacements")
    with pytest.raises(ValueError,match="final-time"):
        final_block(last.replace("0.1000000E+01","NaN"),"displacements")


def test_seat_stiffness_is_per_head_not_per_mesh_node():
    coarse=seat_stiffness({1:1.,2:3.},1000.)
    refined=seat_stiffness({1:.5,2:.5,3:1.5,4:1.5},1000.)
    assert sum(coarse.values())==pytest.approx(1000)
    assert sum(refined.values())==pytest.approx(1000)
    assert coarse[1]==pytest.approx(refined[1]+refined[2])
    for weights in ({},{1:0.},{1:-1.},{1:float("nan")}):
        with pytest.raises(ValueError,match="Positive finite"):
            seat_stiffness(weights,1000.)


def test_published_connection_records_are_balanced_and_comparable():
    records=json.loads((Path(__file__).resolve().parents[1]/"fea/results/connection_comparison.json").read_text())
    assert {r["variant"] for r in records}=={"baseline","stiffer_attachment","closer_backing"}
    keys={(r["mesh_mm"],r["variant"],r["assumed_axial_stiffness_n_per_mm"],
           r["backing_penalty_n_per_mm3"],r["modulus_mpa"],r["initial_backing_gap_mm"],r["load_direction"]) for r in records}
    assert len(keys)==len(records)
    for r in records:
        assert r["revision"].startswith("630a567")
        assert len(r["head_tension_n"])==12
        assert all(math.isfinite(v) and v>=-1e-4 for v in r["head_tension_n"].values())
        assert r["max_displacement_mm"]>0 and math.isfinite(r["max_displacement_mm"])
        assert r["max_spring_law_residual_n"]<.05
        assert r["wrong_sign_force_bound_n"]<.05
        assert r["active_contact_nodes"]>0
        assert r["stress_points"]%4==0 and r["panel_nodes"]>100000
        assert sum(r["head_tension_n"].values())-r["backing_compression_n"]==pytest.approx(1200,abs=.1)
        for a,b in zip(r["applied_force_n"],r["reaction_n"],strict=True):
            assert abs(a+b)<.1
        for a,b in zip(r["applied_moment_nmm"],r["reaction_moment_nmm"],strict=True):
            assert abs(a+b)<1
        assert len(r["evidence_sha256"])==2
        assert all(len(h)==64 for h in r["evidence_sha256"].values())
