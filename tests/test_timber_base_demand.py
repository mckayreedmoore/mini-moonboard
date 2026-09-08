"""Base free-body partition and wrench tests; no geometry construction."""
import pytest

from fea import timber_base_demand as demand


def fixture():
    nodes = {1: (-2., 0., 0.), 2: (2., 0., 0.), 3: (0., 0., 0.), 4: (0., 1., 0.)}
    legs = {"left": [1], "right": [2]}
    contacts = {"post": lambda p: p == nodes[3], "kicker": lambda p: p == nodes[4]}
    return nodes, legs, contacts


def test_partition_includes_kicker_and_deduplicates_shared_contact():
    nodes, legs, contacts = fixture()
    contacts["boundary"] = contacts["post"]
    base, bodies = demand.partition_floor(nodes, set(nodes), legs, contacts)
    assert base == {3, 4}
    assert bodies == {"post": [3], "kicker": [4], "boundary": [3]}


@pytest.mark.parametrize("defect", ["missing_kicker", "overlap", "missing_floor"])
def test_bad_floor_partition_rejected(defect):
    nodes, legs, contacts = fixture()
    feet = set(nodes)
    if defect == "missing_kicker":
        del contacts["kicker"]
    elif defect == "overlap":
        legs["left"].append(3)
    else:
        feet.remove(4)
    with pytest.raises(ValueError):
        demand.partition_floor(nodes, feet, legs, contacts)


def test_reference_and_sign_for_base_on_board_action():
    nodes = {1: (2., 0., 0.)}
    reaction = {1: (0., 0., 10.)}
    axes = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    result = demand.actions(nodes, reaction, {1}, (0., 0., 0.), axes)
    assert result["base_on_board_world_n_nmm"] == [0., 0., 10., 0., -20., 0.]
    assert result["board_on_base_world_n_nmm"] == [0., 0., -10., 0., 20., 0.]
    assert result["base_on_board_local_xsn_n_nmm"] == result["base_on_board_world_n_nmm"]


def test_existing_output_refuses_before_evidence_read(monkeypatch, tmp_path):
    path = tmp_path/"report.json"
    path.write_text("unchanged")
    monkeypatch.setattr(demand, "OUTPUT", path)
    monkeypatch.setattr(demand, "authenticated_inputs", lambda: pytest.fail("Evidence should not be read"))
    with pytest.raises(FileExistsError):
        demand.main()
    assert path.read_text() == "unchanged"


def test_conflicting_source_closure_rejected():
    with pytest.raises(ValueError, match="conflicting"):
        demand.merge_sources({"file": "old"}, {"file": "new"})
