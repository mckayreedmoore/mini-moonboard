"""New two-sided interpolation and actual parent replacement checks."""
import math

import pytest
from test_lumber_leg_mesh import docker_available  # noqa: F401 -- shared pytest fixture

from fea import lumber_leg_response as response
from fea.gusset_connector_trial import point_weights


@pytest.mark.usefixtures("docker_available")
def test_actual_frame_replacement_and_prepared_coupling():
    import json

    n, e, p, cases, sources, legs = response.prepare("2x8", 0., 40.)
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
    response.unchanged(sources)
    text, ctx = response.deck(n, e, p, cases, 1000., legs)
    assert text.count("*EQUATION") == 96 and text.count("*ELEMENT,TYPE=SPRING2") == 48
    assert text.count("*END STEP") == 9
    assert all(node in ctx["output"] for leg in legs.values() for node in leg["nodes"])


def triangle(start, scale):
    yz = [(0., 0.), (scale, 0.), (0., scale), (scale/2, 0.), (scale/2, scale/2), (0., scale/2)]
    return {start+i: (0., y, z+100.) for i, (y, z) in enumerate(yz)}


def test_independent_face_weights_not_borrowed_from_other_mesh():
    nodes = {**triangle(1, 2.), **triangle(7, 3.)}
    faces = lambda start: [{"element": 1, "face": 1, "nodes": list(range(start, start+6))}]
    first = point_weights(nodes, faces(1), (1., 101.))
    second = point_weights(nodes, faces(7), (1., 101.))
    point = {**first, "gusset_nodes": second["nodes"], "other_weights": second["weights"]}
    assert first["weights"] != second["weights"]
    elements = {1: list(range(1, 11)), 2: list(range(3, 13))}
    legs = {"right": {"element_ids": [2], "nodes": list(range(7, 13))}}
    cases = [{"node": 1, "force_n": [1000., 0., 0.]}]
    text, context = response.deck(nodes, elements, {"test": point}, cases, 1000., legs)
    assert text.count("*EQUATION") == 6
    assert text.count("*ELEMENT,TYPE=SPRING2") == 3
    assert context["connections"]["test"]["other_weights"] == second["weights"]
    # The same weights on this different face map to the wrong physical point.
    with pytest.raises(ValueError, match="rigid-motion"):
        response.deck(nodes, elements, {"test": {**point, "other_weights": first["weights"]}}, cases, 1000., legs)


@pytest.mark.parametrize("modulus", [0., -1., math.nan, math.inf])
def test_invalid_modulus_rejected_before_deck(modulus):
    with pytest.raises(ValueError):
        response.deck({}, {}, {}, [], 1000., {}, modulus)
