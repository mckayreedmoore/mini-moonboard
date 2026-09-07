"""Small parser/deck witnesses; these do not simulate or qualify a structure."""
import pytest

from fea.floor_contact import FACES, floor_faces
from fea.hybrid_results import deck_geometry
from fea.solve_easy_frame import LIMITS, audit, make_deck


@pytest.fixture
def witness():
    # Three quadratic tetrahedra supply distinct actual floor-patch sets.
    nodes, elements = {}, {}
    for element, (x, y) in enumerate(((0., 0.), (-100., 2000.), (100., 2000.)), 1):
        corners = ((x, y, 0.), (x+1, y, 0.), (x, y+1, 0.), (x, y, 1.))
        coordinates = list(corners) + [tuple((a+b)/2 for a, b in zip(corners[i], corners[j], strict=True))
                                      for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
        ids = tuple(range(10*(element-1)+1, 10*element+1))
        nodes.update(zip(ids, coordinates, strict=True))
        elements[element] = ids
    groups = floor_faces(nodes, elements)
    feet = sorted({elements[e][i] for faces in groups.values() for e, face in faces for i in FACES[face-1]})
    top = [4, 8, 9, 14, 24]
    text = "*NODE\n" + "\n".join(f"{n}," + ",".join(map(str, p)) for n, p in nodes.items())
    text += "\n*ELEMENT,TYPE=C3D10,ELSET=TIMBER\n"
    text += "\n".join(f"{e}," + ",".join(map(str, ids)) for e, ids in elements.items())
    info = {"audited_cases": [{"name": "down", "force_n": [0., 0., -1200.]}]}
    deck = make_deck(text, feet, top, info["audited_cases"], 7000.)
    mean_x, mean_y = [sum(nodes[n][i] for n in top)/len(top) for i in (0, 1)]
    rear = 1200*mean_y/2000
    right = (rear + 1200*mean_x/100)/2
    reactions = {1: 1200-rear, 11: rear-right, 21: right}
    data = "\n displacements (vx,vy,vz) for set TOP and time 1.0\n\n"
    data += "\n".join(f" {n} 0 0 -0.25" for n in top)
    data += "\n\n forces (fx,fy,fz) for set FEET and time 1.0\n\n"
    data += "\n".join(f" {n} 0 0 {reactions.get(n, 0):.9f}" for n in feet)
    data += "\n\n total force (fx,fy,fz)\n\n 0 0 1200\n"
    return deck, data, info, feet, top


def test_square_cut_deck_and_equilibrium_witness(witness):
    deck, data, info, feet, top = witness
    assert deck_geometry(deck, [("down", (0, 0, -1))])[1:] == (feet, top)
    result = audit(deck, data, info)
    assert result["max_top_displacement_mm"] == {"down": .25}
    assert result["reaction_totals_n"] == [[0., 0., 1200.]]
    assert {row["group"] for row in result["floor_patch_reactions"]} == {"LEFT", "RIGHT", "KICKER"}
    assert sum(row["reaction_n"][2] for row in result["floor_patch_reactions"]) == pytest.approx(1200)
    assert "independent leg plies" in LIMITS
    assert "not a joint ranking" in LIMITS


@pytest.mark.parametrize("mutation", [
    lambda text: text.replace("-240.000000000", "-241.000000000", 1),
    lambda text: text.replace("OP=NEW", "OP=MOD"),
    lambda text: text.replace("FEET,1,3,0", "FEET,1,2,0"),
])
def test_square_cut_audit_rejects_changed_load_or_support(witness, mutation):
    deck, data, info, _, _ = witness
    with pytest.raises(ValueError):
        audit(mutation(deck), data, info)


@pytest.mark.parametrize("mutation", [
    lambda text: text.replace(" 4 0 0 -0.25", ""),
    lambda text: text.replace(" 4 0 0 -0.25", " 999 0 0 -0.25"),
    lambda text: text.replace("-0.25", "nan", 1),
    lambda text: text.replace("time 1.0", "time 2.0"),
    lambda text: text.replace(" 2 0 0 0.000000000", ""),
    lambda text: text.replace(" 2 0 0 0.000000000", " 2 0 0 1.000000000"),
    lambda text: text.replace("0 0 1200\n", "0 0 1201\n"),
])
def test_square_cut_audit_rejects_incomplete_or_unbalanced_output(witness, mutation):
    deck, data, info, _, _ = witness
    changed = mutation(data)
    assert changed != data
    with pytest.raises(ValueError):
        audit(deck, changed, info)


def test_square_cut_audit_checks_moments_not_only_total_force(witness):
    deck, data, info, _, _ = witness
    # Equal/opposite added support forces preserve total force but not moment.
    changed = data.replace(" 2 0 0 0.000000000", " 2 0 0 10.000000000")
    changed = changed.replace(" 3 0 0 0.000000000", " 3 0 0 -10.000000000")
    with pytest.raises(ValueError, match="moment"):
        audit(deck, changed, info)


def test_square_cut_repeated_cases_replace_loads(witness):
    deck, _, _, _, _ = witness
    mesh_text = deck.split("*NSET,NSET=FEET")[0]
    cases = [{"name": "static", "force_n": [0., 0., -1200.]},
             {"name": "sensitivity", "force_n": [300., 0., -2400.]}]
    result = make_deck(mesh_text, witness[3], witness[4], cases, 5000.)
    normalized = [(c["name"], tuple(f/1200 for f in c["force_n"])) for c in cases]
    deck_geometry(result, normalized)
    assert result.count("*CLOAD,OP=NEW") == 2
    assert "5000,0.3" in result
def test_target_mapping_rejects_distant_or_duplicate_targets():
    from fea.solve_easy_frame import target_mapping

    nodes = {i: (i*100., 0., 0.) for i in range(5)}
    points = list(nodes.values())
    assert all(r["distance_mm"] == 0 for r in target_mapping(nodes, points, 40))
    with pytest.raises(ValueError, match="distant"):
        target_mapping(nodes, [(x, y, z+21) for x, y, z in points], 40)
    with pytest.raises(ValueError, match="duplicate"):
        target_mapping(nodes, [points[0]]*5, 40)

