"""Pure release output/free-body tests; no CAD, meshing or solver invocation."""
import json

import pytest

from fea import timber_release as run


def fixture():
    nodes = {1: (-10., -10., 0.), 2: (10., -10., 0.), 3: (10., 10., 0.),
             4: (-10., 10., 0.), 5: (0., 0., 10.), 6: (-1., 0., 5.),
             7: (-1., 0., 5.), 8: (1., 0., 5.), 9: (1., 0., 5.)}
    elements = {1: (1, 2, 3, 5, 1, 2, 3, 4, 5, 4)}
    mapping = {"left": {6: 7}, "right": {8: 9}}
    bonded = [{"loaded_displacement_mm": [v/1000 for v in c["force_n"]],
               "reaction_wrench_n_nmm": [-v for v in c["force_n"]+
                                        run.cross(nodes[5], c["force_n"])]} for c in run.basis_run.BASIS]
    info = {"floor_nodes": [1, 2, 3, 4], "mapping": {"node": 5}, "node_map": mapping,
            "bonded_basis": bonded}
    deck = run.expected_deck(nodes, elements, info["floor_nodes"], 5, mapping)
    lines = []
    for step, case in enumerate(run.basis_run.BASIS, 1):
        fx, fy, fz = case["force_n"]
        lines += [f"displacements for set TOP and time {step}", f"5 {fx/1000} {fy/1000} {fz/1000}", "",
                  f"forces for set FEET and time {step}"]
        for n in info["floor_nodes"]:
            x, y, _ = nodes[n]
            lines.append(f"{n} {-fx/4} {-fy/4} {-fz/4+(x*fx+y*fy)*10/400}")
        lines += ["", f"displacements for set PAIRS and time {step}",
                  "6 0 0 0", "7 0.001 0 0", "8 0 0 0", "9 0.002 0 0", ""]
    return nodes, elements, info, deck, "\n".join(lines)


def test_pair_gap_signs_complete_inventory_and_classification():
    mapping = {"left": {1: 2}, "right": {3: 4}}
    values = {1: (0., 0., 0.), 2: (.1, 0., 0.), 3: (0., 0., 0.), 4: (.2, 0., 0.)}
    result = run.gap_summary(values, mapping)
    assert result["left"]["minimum_signed_gap_mm"] == -.1
    assert result["left"]["interpenetrating_pair_count"] == 1
    assert result["right"]["minimum_signed_gap_mm"] == .2
    assert result["right"]["interpenetrating_pair_count"] == 0
    with pytest.raises(ValueError, match="Incomplete"):
        run.gap_summary({1: (0., 0., 0.)}, mapping)
    with pytest.raises(ValueError, match="overlap"):
        run.pair_ids({"left": {1: 2}, "right": {2: 3}})


def test_deck_protects_floor_and_requires_zero_initial_gap():
    nodes, elements, info, _, _ = fixture()
    with pytest.raises(ValueError, match="protected"):
        run.expected_deck(nodes, elements, [1, 2, 3, 4, 6], 5, info["node_map"])
    nodes[7] = (-1.1, 0., 5.)
    with pytest.raises(ValueError, match="coincide"):
        run.expected_deck(nodes, elements, info["floor_nodes"], 5, info["node_map"])


def test_complete_basis_audit_and_one_selected_superposition():
    _, _, info, deck, data = fixture()
    # JSON turns map keys into strings: the CLI must behave identically.
    result = run.audit(deck, data, json.loads(json.dumps(info)))
    assert len(result["basis"]) == 3
    for row in result["basis"]:
        assert row["residual_wrench"] == pytest.approx([0.]*6, abs=1e-8)
    scenario = result["scenario_300lb_2x_outward300"]
    assert scenario["force_n"] == pytest.approx([0., 300., -2668.93296912])
    scale = .3+2.66893296912
    assert scenario["gap"]["left"]["minimum_signed_gap_mm"] == pytest.approx(-.001*scale)
    assert scenario["gap"]["right"]["minimum_signed_gap_mm"] == pytest.approx(.002*scale)
    assert min(result["comparison"]["released_compliance"]["symmetric_eigenvalues_mm_per_n"]) > 0
    assert "Not a conservative bound" in run.LIMITS


@pytest.mark.parametrize("mutation,match", [("deck", "prescribed"), ("endpoint", "endpoints"),
                                             ("pair", "Incomplete"), ("reaction", "equilibrium")])
def test_changed_deck_missing_output_and_unbalanced_force_reject(mutation, match):
    _, _, info, deck, data = fixture()
    if mutation == "deck":
        deck = deck.replace("*CLOAD,OP=NEW", "*CLOAD")
    elif mutation == "endpoint":
        data = data.replace("PAIRS and time 3", "PAIRS and time 4")
    elif mutation == "pair":
        data = data.replace("7 0.001 0 0", "")
    else:
        data = data.replace("-250.0", "-240.0", 1)
    with pytest.raises(ValueError, match=match):
        run.audit(deck, data, info)


def test_existing_preparation_is_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "DIRECTORY", tmp_path)
    marker = tmp_path/"prior"
    marker.write_text("retain")
    with pytest.raises(FileExistsError, match="overwrite"):
        run.prepare()
    assert marker.read_text() == "retain"
