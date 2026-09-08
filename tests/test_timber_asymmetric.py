"""Small synthetic checks, without CAD, archived-mesh replay or solver execution."""
import math

import pytest

from fea import timber_asymmetric as screen


def test_face_mapping_rejects_backside_and_distant_nodes():
    nodes = {1: (0., 0., 0.), 2: (1., 0., 20.), 3: (0., 1., 20.)}
    assert screen.map_target(nodes, (0., 0., 20.), (0., 1., 0.), {1})["node"] == 2
    with pytest.raises(ValueError, match="20 mm"):
        screen.map_target(nodes, (100., 0., 20.), (0., 1., 0.), {1})


def synthetic():
    nodes = {1: (0., 0., 0.), 2: (0., 0., 10.)}
    elements = {1: (1, 2, 1, 2, 1, 2, 1, 2, 1, 2)}
    deck = screen.expected_deck(nodes, elements, [1], 2)
    # Zero height cannot balance horizontal moments with one support, so this
    # separate fixture checks endpoint/deck rejection before result arithmetic.
    return nodes, elements, deck


def test_exact_deck_and_endpoint_guards():
    _, _, deck = synthetic()
    with pytest.raises(ValueError, match="exact basis"):
        screen.audit(deck.replace("*CLOAD,OP=NEW", "*CLOAD"), "", 2)
    with pytest.raises(ValueError, match="endpoints"):
        screen.audit(deck, "", 2)
    with pytest.raises(ValueError, match="Invalid single"):
        screen.audit(deck, "", 1)


def test_basis_superposition_inventory_signs_and_equilibrium():
    point = (12., 34., 56.)
    basis = [{"loaded_displacement_mm": [v/1000. for v in c["force_n"]],
              "reaction_wrench_n_nmm": [-v for v in c["force_n"]+screen.cross(point, c["force_n"])]}
             for c in screen.BASIS]
    rows = list(screen.scenarios(basis, point))
    assert len(rows) == 72
    assert len({(r["climber_lb"], r["weight_factor"], r["horizontal_direction_deg"]) for r in rows}) == 72
    for row in rows:
        assert row["loaded_displacement_mm"] == pytest.approx([v/1000. for v in row["force_n"]])
        assert row["residual_wrench"] == pytest.approx([0.]*6, abs=1e-8)
        assert row["loaded_displacement_magnitude_mm"] == pytest.approx(math.dist(row["loaded_displacement_mm"], (0, 0, 0)))
    basis[0]["reaction_wrench_n_nmm"][0] += 10.
    with pytest.raises(ValueError, match="equilibrium"):
        list(screen.scenarios(basis, point))


def test_single_node_audit_accepts_balanced_output_and_rejects_changed_reaction():
    nodes = {1: (-10., -10., 0.), 2: (10., -10., 0.),
             3: (10., 10., 0.), 4: (-10., 10., 0.), 5: (0., 0., 10.)}
    elements = {1: (1, 2, 3, 5, 1, 2, 3, 4, 5, 4)}
    deck = screen.expected_deck(nodes, elements, [1, 2, 3, 4], 5)
    lines = []
    for time, case in enumerate(screen.BASIS, 1):
        fx, fy, fz = case["force_n"]
        lines += [f"displacements for set TOP and time {time}", "5 0.1 0.2 0.3", "",
                  f"forces for set FEET and time {time}"]
        for n in (1, 2, 3, 4):
            x, y, _ = nodes[n]
            lines.append(f"{n} {-fx/4} {-fy/4} {-fz/4+(x*fx+y*fy)*10/400}")
        lines.append("")
    data = "\n".join(lines)
    assert len(screen.audit(deck, data, 5)) == 3
    with pytest.raises(ValueError, match="equilibrium"):
        screen.audit(deck, data.replace("-250.0", "-240.0", 1), 5)


def test_preparation_and_summary_never_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(screen, "DIRECTORY", tmp_path)
    with pytest.raises(FileExistsError):
        screen.prepare()
    (tmp_path/"summary.json").write_text("original")
    with pytest.raises(FileExistsError):
        screen.summarize()
    assert (tmp_path/"summary.json").read_text() == "original"
