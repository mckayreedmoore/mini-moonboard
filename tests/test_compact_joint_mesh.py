"""Mesher geometry gates and required replay of archived mesh evidence."""
import copy
import hashlib
import json
import math
import tarfile
from types import SimpleNamespace

import pytest

from fea import compact_joint_mesh as model
from fea.floor_contact import mesh


@pytest.mark.parametrize("values", [(0,2,.9),(40,float("nan"),.9),(40,2,3),(1,2,.9),(40,2,True)])
def test_invalid_sizes(values):
    with pytest.raises(ValueError):
        model.settings(*values)


@pytest.mark.parametrize("mutate_snapshot", [False, True])
def test_launcher_freezes_every_hashed_source_and_rejects_changed_snapshot(tmp_path, monkeypatch, mutate_snapshot):
    monkeypatch.setattr(model, "geometry", lambda _: {})
    output = tmp_path/"mesh"

    def execute(*args, **kwargs):
        launch = json.loads((output/"launch.json").read_text())
        for name, sha in launch["source_sha256"].items():
            assert model.digest(output/"launch_sources"/name) == sha
        if mutate_snapshot:
            (output/"launch_sources"/model.WORKER_SOURCES[0]).write_text("changed")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(model.subprocess, "run", execute)
    if mutate_snapshot:
        with pytest.raises(ValueError, match="source changed"):
            model.run(tmp_path, output)
    else:
        assert model.run(tmp_path, output) == output


def patch():
    c = {"start_xyz_mm":[0.,0.,0.],"axis_xyz":[1.,0.,0.],
         "planned_tied_engagement":{"diameter_mm":9.525,"underhead_interval_mm":[87.376,95.9358]}}
    r = 9.525/2
    s = {1:{"cad_type":"Cylinder","sample_xyz_mm":[90.,r,0.],
            "bounds_mm":[87.376,-r,-r,95.9358,r,r],"area_mm2":math.pi*9.525*(95.9358-87.376)}}
    return c,s


def test_exact_engagement_patch_and_rejected_approximations():
    c,s = patch()
    assert model.engagement(s,c) == [1]
    for key,value in (("area_mm2",1.),("bounds_mm",[74.6125,-4.7625,-4.7625,107.95,4.7625,4.7625]),
                      ("sample_xyz_mm",[90.,4.,0.]),("cad_type","Plane")):
        bad = copy.deepcopy(s)
        bad[1][key] = value
        with pytest.raises(ValueError):
            model.engagement(bad,c)


def test_negative_direction_patch_is_underhead_not_global_x():
    c,s = patch()
    c["axis_xyz"] = [-1.,0.,0.]
    s[1]["bounds_mm"][0],s[1]["bounds_mm"][3] = -95.9358,-87.376
    s[1]["sample_xyz_mm"][0] = -90.
    assert model.engagement(s,c) == [1]


def test_disjoint_append_does_not_merge_coincident_body_nodes():
    nodes = {i:p for i,p in enumerate([(0,0,0),(1,0,0),(0,1,0),(0,0,1),
        (.5,0,0),(.5,.5,0),(0,.5,0),(0,0,.5),(.5,0,.5),(0,.5,.5)],1)}
    elements = {1:tuple(nodes)}
    combined,ee = {},{}
    a,ae = model.append_body(combined,ee,nodes,elements)
    b,be = model.append_body(combined,ee,nodes,elements)
    assert not set(a.values()) & set(b.values())
    assert len(combined) == 20
    model.validate_ownership(combined,ee,{"a":{"nodes":list(a.values()),"elements":list(ae.values())},
                                        "b":{"nodes":list(b.values()),"elements":list(be.values())}})


def test_preserved_smooth_mesh_inventory_and_partition():
    with tarfile.open("fea/results/compact-contact-smooth-mesh-v2.tar.gz") as archive:
        r = json.load(archive.extractfile("mesh.json"))
        launch = json.load(archive.extractfile("launch.json"))
        deck = archive.extractfile("mesh.inp").read()
        assert set(launch["source_sha256"]) == {*model.WORKER_SOURCES,"fea/prescribed_tet_control.py"}
        for name,sha in launch["source_sha256"].items():
            assert hashlib.sha256(archive.extractfile("launch_sources/"+name).read()).hexdigest() == sha
    assert launch["returncode"] == 0
    assert r["status"] == "VERIFIED MESH ONLY; NO SOLVER"
    assert not r["qualified_for_design"] and not r["solved"]
    assert r["mesh_sha256"] == hashlib.sha256(deck).hexdigest()
    nodes,elements = mesh(deck.decode())
    del deck
    assert len(nodes) == r["node_count"] and len(elements) == r["element_count"]
    assert len(r["bodies"]) == 26
    model.validate_ownership(nodes,elements,r["bodies"])
    assert (len(r["interfaces"]["planar_contacts"]),len(r["interfaces"]["shaft_bore_contacts"]),
            len(r["interfaces"]["planned_nut_ties"])) == (25,8,4)
    assert len({frozenset(m["body"] for m in p["members"]) for p in r["interfaces"]["planar_contacts"]}) == 25
    for body in r["bodies"].values():
        assert body["min_sampled_jacobian"] > 0 and body["min_integration_jacobian"] > 0
        assert abs(body["mesh_volume_mm3"]/body["cad_volume_mm3"]-1) <= .001
        exterior = model.external_faces({e:elements[e] for e in body["elements"]})
        expected = {(e,f) for e,f,_ in exterior.values()}
        actual = [tuple(face) for s in body["surfaces"].values() for face in s["faces"]]
        assert len(actual) == len(set(actual)) and set(actual) == expected
    for tie in r["interfaces"]["planned_nut_ties"]:
        bolt_name = tie["members"][0]["body"]
        c = next(c for c in r["geometry"]["connections"] if c["hardware_bodies"][0] == bolt_name)
        for member in tie["members"]:
            surfaces = r["bodies"][member["body"]]["surfaces"]
            for tag in member["surface_tags"]:
                for n in surfaces[str(tag)]["nodes"]:
                    s = (nodes[n][0]-c["start_xyz_mm"][0])*c["axis_xyz"][0]
                    assert tie["underhead_interval_mm"][0]-1e-5 <= s <= tie["underhead_interval_mm"][1]+1e-5
    for pair in r["interfaces"]["shaft_bore_contacts"]:
        wood = pair["members"][1]
        surfaces = r["bodies"][wood["body"]]["surfaces"]
        area = sum(surfaces[str(t)]["area_mm2"] for t in wood["surface_tags"])
        assert area == pytest.approx(math.pi*11.1125*38.1,rel=1e-7)
