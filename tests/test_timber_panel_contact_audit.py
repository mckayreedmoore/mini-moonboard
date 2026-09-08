"""Bounded nonlinear-frame audit controls; no solver or CAD execution."""
import pytest

from fea.timber_panel_contact_audit import audit, audit_with_history


def fixture():
    context = {"nodes": {1: (0., 1., 1.), 2: (-1., 1., 0.), 3: (1., 1., 0.),
                          4: (-1., 1., 1.), 5: (-1., 1., 1.),
                          6: (1., 1., 1.), 7: (1., 1., 1.)},
        "load_node": 1, "floor_nodes": [2, 3], "node_map": {"left": {4: 5}, "right": {6: 7}},
        "leg_floor_nodes": {"left": [2], "right": [3]},
        "leg_references_world_mm": {"left": (-1., 1., 1.), "right": (1., 1., 1.)},
        "force_n": (0., 0., -10.), "penalty": 10000., "increment": .125,
        "contact_faces": {s: {"pairs": [{"leg": {"element": e, "face": "S1"}}]}
                          for s, e in (("left", 10), ("right", 20))}}
    data = """
 displacements for set TOP and time 1.0

 1 0 0 -.001

 displacements for set FEET and time 1.0

 2 0 0 0
 3 0 0 0

 displacements for set PAIRS and time 1.0

 4 0 0 0
 5 0 0 0
 6 0 0 0
 7 0 0 0

 forces for set FEET and time 1.0

 2 0 0 5
 3 0 0 5

 relative contact displacement for all contact elements and time 1.0

 10 1 -.00001 0 0

 contact stress for all contact elements and time 1.0

 10 1 .1 0 0

 total number of contact elements for time 1.0

 1

 statistics for slave set SLAVE_LEFT, master set MASTER_LEFT and time 1.0

 total surface force and moment about the origin

 -1 0 0 0 -1 1

 statistics for slave set SLAVE_RIGHT, master set MASTER_RIGHT and time 1.0

 total surface force and moment about the origin

 0 0 0 0 0 0

"""
    return data, context


def test_open_side_and_common_reference_conditional_wrench():
    data, context = fixture()
    row, = audit(data, context)
    assert row["global_residual_n_nmm"] == pytest.approx([0.]*6)
    assert row["legs"]["right"]["reported_contact_point_count"] == 0
    assert row["legs"]["left"]["panel_on_leg_n_nmm"] == [-1., 0., 0., 0., 0., 0.]
    assert row["legs"]["left"]["inferred_leg_on_rim_common_edge_n_nmm"] == [-1., 0., 5., 0., 0., 0.]
    assert "not independently" in row["limits"]


def test_both_surfaces_open_with_explicit_empty_sections():
    data, context = fixture()
    data = data.replace(" 10 1 -.00001 0 0\n", "").replace(" 10 1 .1 0 0\n", "")
    data = data.replace("\n 1\n", "\n 0\n").replace("-1 0 0 0 -1 1", "0 0 0 0 0 0")
    row, = audit(data, context)
    assert all(v["reported_contact_point_count"] == 0 for v in row["legs"].values())


@pytest.mark.parametrize("old,new,match", [
    ("2 0 0 5", "2 0 0 4", "imbalance"),
    ("1 0 0 -.001", "1 .2 0 -.001", "imbalance"),
    ("2 0 0 0", "2 0 0 .001", "floor moved"),
    ("10 1 .1 0 0", "10 1 .2 0 0", "penalty law"),
    ("10 1 .1 0 0", "10 1 -.1 0 0", "Tensile"),
    ("10 1 .1 0 0", "10 1 .1 .01 0", "frictional"),
    ("10 1", "30 1", "ownership"),
    ("MASTER_RIGHT", "WRONG", "pair endpoints"),
    ("relative contact displacement", "missing contact section", "contact section"),
    ("7 0 0 0", "7 -.001 0 0", "nodal overlap"),
])
def test_bad_evidence_rejected(old, new, match):
    data, context = fixture()
    with pytest.raises(ValueError, match=match):
        audit(data.replace(old, new), context)


def test_every_endpoint_requires_status_history():
    data, context = fixture()
    with pytest.raises(ValueError, match="increment limit"):
        audit_with_history(data, context, "1 1 1 2 1 1 1\n")


@pytest.mark.parametrize("defect", ["nan_node", "nan_reference", "overlap", "empty", "floor"])
def test_invalid_context_fails(defect):
    data, context = fixture()
    if defect == "nan_node":
        context["nodes"][4] = (float("nan"), 0., 1.)
    elif defect == "nan_reference":
        context["leg_references_world_mm"]["left"] = (float("nan"), 0., 1.)
    elif defect == "overlap":
        context["node_map"]["left"] = {1: 5}
    elif defect == "empty":
        context["node_map"]["left"] = {}
    else:
        context["nodes"][8] = (0., 0., 0.)
    with pytest.raises(ValueError, match="context"):
        audit(data, context)
