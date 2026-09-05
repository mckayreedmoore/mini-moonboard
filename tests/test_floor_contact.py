import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

from fea.floor_contact import FACES, deck, floor_faces, job_name, mesh
from fea.floor_contact_results import audit, blocks, verify_deck


def test_decimal_penalty_jobs_have_distinct_safe_paths():
    integer = Path(job_name(.3,1000))
    decimal = Path(job_name(.3,1000.5))
    assert integer.name == "floor_mu0p3_k1000"
    assert decimal.name == "floor_mu0p3_k1000p5"
    assert job_name(.3,1000.0001) == "floor_mu0p3_k1000p0001"
    assert job_name(.30000001,1000) != integer.name
    for suffix in (".inp",".json",".log",".dat"):
        assert integer.with_suffix(suffix) != decimal.with_suffix(suffix)
        assert decimal.with_suffix(suffix).stem == decimal.name


def test_c3d10_floor_faces_and_unpinned_deck():
    nodes, elements = {}, {}
    for e, (x,y) in enumerate(((-1250,1400),(1250,1400),(0,0)),1):
        xyz = [(x,y,0),(x+10,y,0),(x,y+10,0),(x,y,10),
               (x+5,y,0),(x+5,y+5,0),(x,y+5,0),(x,y,5),(x+5,y,5),(x,y+5,5)]
        ids = tuple(range((e-1)*10+1,e*10+1))
        nodes.update(zip(ids,xyz,strict=True))
        elements[e] = ids
    groups = floor_faces(nodes,elements)
    assert groups == {"LEFT":[(1,1)],"RIGHT":[(2,1)],"KICKER":[(3,1)]}
    text, ground = deck(nodes,elements,groups,[4,14,24],.3,10000)
    assert "FEET,1,3" not in text
    assert "*BOUNDARY\nGROUND_LEFT,1,3,0\nGROUND_RIGHT,1,3,0\nGROUND_KICKER,1,3,0\n*STEP" in text
    assert "TIMBER,GRAV,9806.65,0,0,-1" in text
    assert "*DENSITY\n6e-10" in text
    assert len(ground) == 3
    assert text.count("TYPE=SURFACE TO SURFACE") == 3
    # The deck's C3D8 ground mesh is intentionally not part of timber extraction.
    actual_nodes, actual_elements = mesh(text)
    assert actual_elements == elements
    assert all(actual_nodes[n] == xyz for n,xyz in nodes.items())
    assert all(len(face)==6 for face in FACES)
    record = {"deck_sha256":hashlib.sha256(text.encode()).hexdigest(),"load_nodes":[4,14,24],
              "mu":.3,"normal_penalty_n_mm3":10000}
    verify_deck(text,nodes,elements,groups,record)
    for broken in (text.replace("7000,0.3","70,0.3"),text.replace("*STEP,NLGEOM","*STEP")):
        with pytest.raises(ValueError,match="digest"):
            verify_deck(broken,nodes,elements,groups,record)
        record["deck_sha256"] = hashlib.sha256(broken.encode()).hexdigest()
        with pytest.raises(ValueError,match="intended"):
            verify_deck(broken,nodes,elements,groups,record)
        record["deck_sha256"] = hashlib.sha256(text.encode()).hexdigest()


def test_output_blocks_fail_closed():
    data = "\n displacements (vx,vy,vz) for set WOODN and time 1.0\n\n 1 0 0 0\n"
    assert blocks(data)["displacements","WOODN",1.] == {1:(0.,0.,0.)}
    with pytest.raises(ValueError,match="Duplicate"):
        blocks(data+data)
    with pytest.raises(ValueError,match="Nonfinite"):
        blocks(data.replace("1 0 0 0","1 nan 0 0"))


@pytest.mark.parametrize("face",[1,2,3,4])
def test_all_c3d10_floor_face_ids(face):
    nodes, elements = {}, {}
    for tag,(x,y) in enumerate(((-1250,1400),(1250,1400),(0,0)),1):
        corners = [None]*4
        for i,xyz in zip(FACES[face-1][:3],((x,y,0),(x+10,y,0),(x,y+10,0)),strict=True):
            corners[i] = xyz
        corners[corners.index(None)] = (x,y,10)
        xyz = corners+[tuple((corners[a][i]+corners[b][i])/2 for i in range(3))
                       for a,b in ((0,1),(1,2),(2,0),(0,3),(1,3),(2,3))]
        ids = tuple(range((tag-1)*10+1,tag*10+1))
        nodes.update(zip(ids,xyz,strict=True)); elements[tag] = ids
    assert floor_faces(nodes,elements) == {"LEFT":[(1,face)],"RIGHT":[(2,face)],"KICKER":[(3,face)]}


def test_final_step_force_moment_and_completeness():
    nodes = {1:(0.,0.,0.)}
    elements = {1:(1,)*10}
    groups = {"LEFT":[(1,1)]}
    record = {"ground_nodes":{"LEFT":{10:(0.,0.,0.)}},"nodal_volume_mm3":{1:1e9/600},
              "load_nodes":[1],"mu":.3}
    def data(time, force):
        return (f"\n displacements (vx,vy,vz) for set WOODN and time {time}\n 1 0 0 0\n"
                f"\n forces (fx,fy,fz) for set GROUND_LEFT and time {time}\n 10 0 0 {force}\n")
    first = data(1,9.80665)
    both = first+data(2,1209.80665)
    assert len(audit(both,nodes,elements,groups,record)) == 2
    with pytest.raises(ValueError,match="Incomplete wood"):
        audit(first,nodes,elements,groups,record)
    with pytest.raises(ValueError,match="Incomplete ground"):
        audit(both.replace(" 10 0 0 1209.80665",""),nodes,elements,groups,record)
    with pytest.raises(ValueError,match="equilibrium"):
        audit(both.replace("1209.80665","1200"),nodes,elements,groups,record)
    record["ground_nodes"]["LEFT"][10] = (10.,0.,0.)
    with pytest.raises(ValueError,match="equilibrium"):
        audit(both,nodes,elements,groups,record)
    record["ground_nodes"]["LEFT"][10] = (math.nan,0.,0.)
    with pytest.raises(ValueError,match="coordinate"):
        audit(both,nodes,elements,groups,record)
    record["ground_nodes"]["LEFT"][10] = (0.,0.,0.)
    record["nodal_volume_mm3"][1] = math.nan
    with pytest.raises(ValueError,match="gravity"):
        audit(both,nodes,elements,groups,record)
    record["nodal_volume_mm3"] = {}
    with pytest.raises(ValueError,match="gravity"):
        audit(both,nodes,elements,groups,record)


def test_quadrature_abaqus_ordering_in_solver_image():
    if not shutil.which("docker") or subprocess.run(
            ["docker","image","inspect","mini-moonboard-fea:box-v1"],capture_output=True,check=False).returncode:
        pytest.skip("Existing solver Docker image required for Gauss quadrature test")
    code = """
import math
from fea.floor_contact import integrated_weights
xyz=[(0,0,0),(1,0,0),(0,1,0),(0,0,1),(.5,0,0),(.5,.5,0),(0,.5,0),(0,0,.5),(.5,0,.5),(0,.5,.5)]
nodes=dict(enumerate(xyz,1)); elements={1:tuple(nodes)}
w=integrated_weights(elements,nodes); v=sum(w.values())
assert abs(v-1/6)<1e-10, v
assert all(abs(sum(w[n]*nodes[n][i] for n in nodes)/v-.25)<1e-10 for i in range(3))
nodes[9],nodes[10]=nodes[10],nodes[9]
try: integrated_weights(elements,nodes)
except ValueError: pass
else: raise AssertionError('Swapped curved midsides were not rejected')
print('quadrature passed')
"""
    result = subprocess.run(["docker","run","--rm","-v",f"{__import__('os').getcwd()}:/work",
                             "mini-moonboard-fea:box-v1","python3","-c",code],capture_output=True,text=True,timeout=60,check=False)
    assert result.returncode == 0, result.stdout+result.stderr
    assert "quadrature passed" in result.stdout
    assert math.isfinite(1/6)


def test_published_unresolved_trial_and_smoke_evidence():
    directory = Path("fea/results/floor_contact")
    report = json.loads((directory/"report.json").read_text())
    for name,digest in report["sources_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    assert len(report["trials"]) == 3
    for trial in report["trials"].values():
        assert trial["accepted_increments"] == 0 and not trial["climbing_load_reached"]
        assert trial["exit_code"] in (-15,-999)
        for name,digest in trial["evidence_sha256"].items():
            if name.endswith((".sta",".cvg",".log")):
                assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest
    for toy in report["toys"].values():
        for name,digest in toy["sha256"].items():
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest
        assert max(map(abs,toy["force_residual_n"])) < 1e-5
        assert max(map(abs,toy["moment_residual_nmm"])) < .001
