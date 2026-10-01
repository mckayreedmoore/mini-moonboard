"""Known-answer tests for virtual-work force transfer and attribution limits."""

import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).with_name("nodal_transfer.py")
SPEC = importlib.util.spec_from_file_location("upper_outer_nodal_transfer", PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture():
    model = {"nodes":{"1":[-1.,0.,0.], "2":[1.,0.,0.]}}
    expansion = M.MPCExpansion([[[99,2,1.], [1,2,-.5], [2,2,-.5]]], {1:"wood",2:"wood"})
    row = {"first":"wood", "second":"other", "point":[0.,0.,0.],
           "force_on_first_xyz_n":[0.,10.,0.], "force_rounding_radius_xyz_n":[0.,.1,0.]}
    return model, expansion, row


def section(origin=(0.,0.,0.)):
    return {"plane_origin_xyz_mm":list(origin), "section_plane_normal_global_xyz":[1.,0.,0.]}


def test_transpose_preserves_virtual_work_and_whole_wrench():
    model, expansion, row = fixture()
    cloud, point, observed = M.nodal_action(model, expansion, row, "wood", [((99,2),10.,.1)])
    assert [a["force_n"] for a in cloud] == [[0.,5.,0.],[0.,5.,0.]]
    assert observed["force_n"] == [0.,10.,0.]
    assert observed["moment_nmm"] == [0.,0.,0.]
    assert observed["force_radius_n"] == [0.,.1,0.]
    physical_u = {(1,2):3., (2,2):-2.}
    ghost_u = sum(w*physical_u[k] for k,w in expansion.expand((99,2)).items())
    nodal_work = sum(a["force_n"][1]*physical_u[a["node"],2] for a in cloud)
    assert nodal_work == pytest.approx(10.*ghost_u)
    assert point["force_n"] == observed["force_n"]


def test_whole_wrench_equivalence_does_not_establish_local_cut_share():
    model, expansion, row = fixture()
    cloud, point, _ = M.nodal_action(model, expansion, row, "wood", [((99,2),10.,.1)])
    node = M.selected_wrench(cloud, section(), "minus")
    point_minus = M.selected_wrench([point], section(), "minus")
    point_plus = M.selected_wrench([point], section(), "plus")
    assert node["external_wrench"]["force_n"] == [0.,5.,0.]
    assert point_minus["external_wrench"]["force_n"] == [0.,10.,0.]
    assert point_plus["external_wrench"]["force_n"] == [0.,0.,0.]
    assert node["external_wrench"]["moment_nmm"] == [0.,0.,5.]
    for trace in ("minus", "plus"):
        positive = M.selected_wrench(cloud, section(), trace)
        negative = M.selected_wrench(cloud, section(), trace, "negative")
        assert M.add(positive["external_wrench"]["force_n"],negative["external_wrench"]["force_n"]) == [0.,10.,0.]


def test_axial_receiver_uses_its_own_seat_point_and_signed_force():
    model, expansion, row = fixture()
    row.update(second="wood",first="other",point=[7.,0.,0.],second_point=[0.,0.,0.],force_on_second_xyz_n=[0.,-10.,0.])
    cloud, point, observed = M.nodal_action(model,expansion,row,"wood",[((99,2),-10.,.1)])
    assert point["point_mm"] == [0.,0.,0.]
    assert observed["force_n"] == [0.,-10.,0.]
    assert observed["moment_nmm"] == [0.,0.,0.]
    assert sum(a["force_n"][1] for a in cloud) == -10.


def test_force_couple_and_moment_transport_are_retained():
    actions=[{"point_mm":[-2.,0.,0.],"force_n":[0.,-3.,0.],"radius_n":[0.,.01,0.]},
             {"point_mm":[2.,0.,0.],"force_n":[0.,3.,0.],"radius_n":[0.,.01,0.]}]
    for datum in ([0.,0.,0.],[100.,20.,-7.]):
        result=M.wrench(actions,datum)
        assert result["force_n"] == [0.,0.,0.]
        assert result["moment_nmm"] == [0.,0.,12.]
    one=M.wrench(actions[:1],[0.,0.,0.])
    shifted=M.wrench(actions[:1],[1.,2.,3.])
    assert shifted["moment_nmm"] == M.sub(one["moment_nmm"],M.cross([1.,2.,3.],one["force_n"]))


def test_recursive_projection_sign_and_negative_weights_are_kept():
    equations=[[[99,2,2.],[1,2,.5],[2,2,-2.5]],[[100,2,1.],[99,2,-1.]]]
    expansion=M.MPCExpansion(equations,{1:"wood",2:"wood"})
    assert expansion.expand((100,2)) == {(1,2):-.25,(2,2):1.25}
    model={"nodes":{"1":[-1.,0.,0.],"2":[1.,0.,0.]}}
    row={"first":"wood","second":"other","point":[1.5,0.,0.],"force_on_first_xyz_n":[0.,4.,0.],"force_rounding_radius_xyz_n":[0.,.2,0.]}
    cloud,_,observed=M.nodal_action(model,expansion,row,"wood",[((100,2),4.,.2)])
    assert cloud[0]["force_n"][1] == -1.
    assert cloud[1]["force_n"][1] == 5.
    assert observed["force_radius_n"][1] == pytest.approx(.3)
    assert observed["moment_nmm"][2] == 0.


@pytest.mark.parametrize("kind",["cycle","duplicate","zero","unknown","other_owner","fixed"])
def test_invalid_projection_or_ownership_is_rejected(kind):
    equations=[[[99,2,1.],[1,2,-1.]]]
    owner={1:"wood"}
    fixed=()
    if kind=="cycle": equations=[[[99,2,1.],[100,2,-1.]],[[100,2,1.],[99,2,-1.]]]
    if kind=="duplicate": equations=equations*2
    if kind=="zero": equations[0][0][2]=0.
    if kind=="unknown": equations[0][1][0]=2
    if kind=="other_owner": owner[1]="other"
    if kind=="fixed": fixed=(1,)
    with pytest.raises(M.TransferError):
        M.MPCExpansion(equations,owner,fixed).receiver((99,2),"wood")


@pytest.mark.parametrize("value",[float("nan"),float("inf"),True])
def test_nonfinite_or_boolean_force_is_rejected(value):
    model,expansion,row=fixture()
    with pytest.raises(M.TransferError): M.nodal_action(model,expansion,row,"wood",[((99,2),value,.1)])


@pytest.mark.parametrize("term,field,value",[(0,0,99.9),(0,1,2.9),(1,0,1.9),(1,1,2.9),
                                          (0,0,True),(1,1,True),(0,1,4),(1,1,0),
                                          (0,0,"99.9"),(1,0,-1)])
def test_malformed_mpc_node_and_dof_ids_are_rejected(term,field,value):
    equations=[[[99,2,1.],[1,2,-1.]]]
    equations[0][term][field]=value
    with pytest.raises(M.TransferError):
        M.MPCExpansion(equations,{1:"wood"}).receiver((99,2),"wood")


@pytest.mark.parametrize("location",["fixed","owner","query","body_nodes"])
def test_malformed_node_ids_cannot_enter_through_other_routes(location):
    with pytest.raises(M.TransferError):
        if location=="fixed":
            M.MPCExpansion([],{1:"wood"},[1.9])
        elif location=="owner":
            M.MPCExpansion([],{1.9:"wood"})
        elif location=="query":
            M.MPCExpansion([],{1:"wood"}).receiver((1.9,2),"wood")
        else:
            M.owner_map({"physical_body_nodes":{"wood":[1.9]}})


def test_pin_refuses_changed_bytes(tmp_path):
    p=tmp_path/"input.json"
    p.write_text('{"valid":true}')
    digest=M.sha(p)
    assert M.read_pinned("input.json",digest,tmp_path)=={"valid":True}
    p.write_text('{"valid":false}')
    with pytest.raises(M.TransferError,match="changed source"): M.read_pinned("input.json",digest,tmp_path)


@pytest.mark.parametrize("label,key",[("model","case_id"),("model","candidate"),("model","geometry_revision_id"),
                                    ("response","case_id"),("response","candidate"),("response","geometry_revision_id"),
                                    ("response","source_input_model_json_sha256")])
def test_source_identity_and_geometry_revision_are_bound(label,key):
    sources={"model":{"case_id":"case","candidate":"candidate","geometry_revision_id":"revision"},
             "response":{"case_id":"case","candidate":"candidate","geometry_revision_id":"revision","source_input_model_json_sha256":"hash"}}
    M.validate_case_identity(sources["model"],sources["response"],"case","candidate","revision","hash")
    sources[label][key]="wrong"
    with pytest.raises(M.TransferError):
        M.validate_case_identity(sources["model"],sources["response"],"case","candidate","revision","hash")


def test_verifier_compares_exact_bytes_and_rejects_conflicting_duplicate(tmp_path, monkeypatch, capsys):
    data={"complete_joint_resistance_established":False,"counts":{},"max_point_minus_nodal_cut_component_force_n":1.,"max_point_minus_nodal_cut_component_moment_nmm":2.}
    out=tmp_path/"output.json"
    monkeypatch.setattr(M,"OUTPUT",out)
    monkeypatch.setattr(M,"produce",lambda:data)
    monkeypatch.setattr("sys.argv",["nodal_transfer.py","--verify"])
    out.write_bytes(M.canonical(data))
    assert M.main()==0
    ambiguous=json.dumps(data).replace('{','{"complete_joint_resistance_established":true,',1)
    out.write_text(ambiguous)
    assert M.main()==2
    assert "output differs" in capsys.readouterr().out
