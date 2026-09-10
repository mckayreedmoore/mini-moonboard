"""Raw parent ownership, not local-joint mechanical acceptance."""
import cadquery as cq
import pytest

from fea import compact_rim_boundary as mapping


@pytest.fixture(scope="module")
def report():
    return mapping.build()


def test_actual_two_raw_rims_and_remote_interfaces(report):
    assert not report["boundary_values_assigned"]
    for side, row in report["rims"].items():
        assert row["mesh_volume_mm3"] == pytest.approx(row["cad_volume_mm3"], rel=1e-9)
        assert len(row["shared_faces"]) == 217
        assert len(row["shared_nodes_with_omitted_wood"]) == 595
        assert len(row["replaced_leg_mpcs"]) == 4
        assert set(row["remote_gusset_mpcs"]) == {f"timber_base_{side}_{i}" for i in (1, 2)}
        owned = set(row["node_ids"])
        for point in row["remote_gusset_mpcs"].values():
            assert set(point["nodes"]) <= owned
            assert not owned.intersection(point["gusset_nodes"])
            assert set(point["gusset_nodes"]) <= set(row["required_remote_displacement_nodes"])
        for pair in row["shared_faces"]:
            assert pair["rim"]["element"] in row["element_ids"]
            assert pair["omitted_wood"]["element"] not in row["element_ids"]
            assert set(pair["rim"]["nodes"]) == set(pair["omitted_wood"]["nodes"])


def tet(points):
    edges = ((0, 1), (1, 2), (0, 2), (0, 3), (1, 3), (2, 3))
    points = points+[[sum(points[j][i] for j in edge)/2 for i in range(3)] for edge in edges]
    return dict(enumerate(points, 1)), {1: list(range(1, 11))}


def test_partial_element_rejected():
    nodes, elements = tet([[.1,.1,.1], [1.1,.1,.1], [.1,.8,.1], [.1,.1,.8]])
    with pytest.raises(ValueError, match="Partial rim"):
        mapping.select(nodes, elements, cq.Solid.makeBox(1, 1, 1))


def test_incomplete_volume_rejected():
    nodes, elements = tet([[.1,.1,.1], [.8,.1,.1], [.1,.8,.1], [.1,.1,.8]])
    with pytest.raises(ValueError, match="CAD mismatch"):
        mapping.select(nodes, elements, cq.Solid.makeBox(1, 1, 1))


def test_partial_mpc_rejected():
    nodes, elements = tet([[0,0,0], [1,0,0], [0,1,0], [0,0,1]])
    points = {"bad": {"nodes": [1, 11], "gusset_nodes": [12], "member": "base_side_left"}}
    with pytest.raises(ValueError, match="Partial or unexpected"):
        mapping.interfaces(nodes, elements, elements, points, "left")
