"""New two-sided interpolation and actual parent replacement checks."""
import pytest
from test_lumber_leg_mesh import docker_available  # noqa: F401 -- shared pytest fixture

from fea import spread_leg_response as response
from mini_moonboard import lumber_leg_spread_frame as model


def test_run_creates_work_directory_before_expensive_preparation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def stop(*args):
        assert (tmp_path/"fea/generated").is_dir()
        raise RuntimeError("stop before meshing")
    monkeypatch.setattr(response, "prepare", stop)
    with pytest.raises(RuntimeError, match="stop before meshing"):
        response.run("2x8", 300., 40., tmp_path/"result.tar.gz")


@pytest.mark.usefixtures("docker_available")
def test_actual_frame_replacement_and_prepared_coupling():
    import json

    n, e, p, cases, sources, legs = response.prepare("2x8", 300., 40.)
    original_n, original_e, original_p, original_cases, _, _ = response.parent_inputs()
    removed = {eid for leg in json.loads(response.LEG_MAP.read_text())["legs"].values()
               for eid in leg["element_ids"]}
    kept = set(original_e)-removed
    assert cases == original_cases
    assert all(e[eid] == original_e[eid] for eid in kept)
    used = {node for eid in kept for node in e[eid]}
    assert all(n[node] == original_n[node] for node in used)
    assert len(p) == 16 and len(cases) == 9
    for name, old in original_p.items():
        assert all(p[name][key] == value for key, value in old.items())
    assert set(e) == kept | {eid for leg in legs.values() for eid in leg["element_ids"]}
    assert {node for ids in e.values() for node in ids} == set(n)
    for side, leg in legs.items():
        selected = set(leg["element_ids"])
        owned = {node for eid in selected for node in e[eid]}
        others = {node for eid, ids in e.items() if eid not in selected for node in ids}
        assert not owned & others
        assert set(leg["floor_nodes"]) == {node for node in owned if abs(n[node][2]) < 1e-5}
        for name, point in p.items():
            if name.startswith(f"lumber_leg_bolt_{side}_"):
                assert set(point["nodes"]) <= used
                assert set(point["gusset_nodes"]) <= owned
                assert point["face_element"] in kept
                assert point["other_face_element"] in selected
                assert point["nodes"] == [e[point["face_element"]][i] for i in response.FACES[point["face"]-1]]
                assert point["gusset_nodes"] == [e[point["other_face_element"]][i]
                                                for i in response.FACES[point["other_face"]-1]]
    actual = {c.name: c for c in model.connections("2x8", 300.)}
    for name, point in p.items():
        if name.startswith("lumber_leg_bolt_"):
            assert point["point_mm"][1:] == pytest.approx([actual[name].start.y, actual[name].start.z])
    assert "mini_moonboard/lumber_leg_spread_frame.py" in sources
    assert "fea/spread_leg_response.py" in sources
    response.unchanged(sources)
    text, ctx = response.deck(n, e, p, cases, 1000., legs)
    assert text.count("*EQUATION") == 96 and text.count("*ELEMENT,TYPE=SPRING2") == 48
    assert text.count("*END STEP") == 9
    assert all(node in ctx["output"] for leg in legs.values() for node in leg["nodes"])

