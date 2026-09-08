"""Wide runner boundaries and independent synthetic force/moment controls."""
import json
from types import SimpleNamespace

import pytest

from fea import wide_asymmetric as run


def synthetic():
    nodes = {1: (-10., -10., 0.), 2: (10., -10., 0.),
             3: (10., 10., 0.), 4: (-10., 10., 0.), 5: (0., 0., 10.)}
    # Parser-level control only; geometry validity comes from authenticated mesh.
    elements = {1: (1, 2, 3, 5, 1, 2, 3, 4, 5, 4)}
    deck = run.expected_deck(nodes, elements, [1, 2, 3, 4], 5)
    lines = []
    for time, case in enumerate(run.BASIS, 1):
        fx, fy, fz = case["force_n"]
        lines += [f"displacements for set TOP and time {time}", "5 0.1 0.2 0.3", "",
                  f"forces for set FEET and time {time}"]
        for n in (1, 2, 3, 4):
            x, y, _ = nodes[n]
            lines.append(f"{n} {-fx/4} {-fy/4} {-fz/4+(x*fx+y*fy)*10/400}")
        lines.append("")
    return deck, "\n".join(lines)


def test_wide_labeled_three_bases_and_216_scenarios():
    deck, data = synthetic()
    assert deck.startswith("** "+run.LIMITS)
    basis = run.audit(deck, data, 5)
    assert len(basis) == 3
    for row in basis:
        assert row["residual_wrench"] == pytest.approx([0.]*6)
    assert sum(len(list(run.scenarios(basis, (0., 0., 10.)))) for _ in run.HOLDS) == 216


@pytest.mark.parametrize("defect", ["deck", "force", "moment", "endpoint", "floor"])
def test_changed_basis_or_output_rejects(defect):
    deck, data = synthetic()
    node = 5
    if defect == "deck":
        deck = deck.replace("*CLOAD,OP=NEW", "*CLOAD")
    elif defect == "force":
        data = data.replace("-250.0", "-240.0", 1)
    elif defect == "moment":
        data = data.replace("1 -250.0 -0.0 -250.0", "1 -250.0 -0.0 -240.0", 1)
        data = data.replace("2 -250.0 -0.0 250.0", "2 -250.0 -0.0 240.0", 1)
    elif defect == "endpoint":
        data = ""
    else:
        node = 1
    with pytest.raises(ValueError):
        run.audit(deck, data, node)


def test_authentication_rejects_other_candidate_before_archives(monkeypatch, tmp_path):
    source = tmp_path/"mesh.json"
    source.write_text(json.dumps({"candidate": "timber-base-development", "mesh_size_mm": 40}))
    monkeypatch.setattr(run, "SOURCE", source)
    with pytest.raises(ValueError, match="wide 40mm"):
        run.authenticated_inputs()


def test_preparation_refuses_existing_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "DIRECTORY", tmp_path)
    with pytest.raises(FileExistsError):
        run.prepare()


def test_solve_refuses_existing_attempt_and_invalid_hold(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "DIRECTORY", tmp_path)
    (tmp_path/"input.json").write_text("{}")
    (tmp_path/"A12.inp").write_text("deck")
    (tmp_path/"A12.launch.json").write_text("preserved")
    with pytest.raises(FileExistsError):
        run.solve("A12")
    with pytest.raises(ValueError, match="Unknown"):
        run.solve("F12")
    assert (tmp_path/"A12.launch.json").read_text() == "preserved"


def test_roundtripped_preparation_can_launch_bounded_solver(monkeypatch, tmp_path):
    deck, data = synthetic()
    monkeypatch.setattr(run, "DIRECTORY", tmp_path)
    monkeypatch.setattr(run, "unchanged", lambda sources: None)
    (tmp_path/"A12.inp").write_text(deck)
    info = {"candidate": run.KEY, "limits": run.LIMITS, "basis": run.BASIS,
        "source_sha256": {"source": "digest"}, "mapping": {"A12": {"node": 5}},
        "deck_sha256": {"A12": run.digest(tmp_path/"A12.inp")}}
    (tmp_path/"input.json").write_text(json.dumps(info))
    def solve(command, **kwargs):
        assert command == ["ccx", "-i", "A12"]
        assert kwargs["timeout"] == 600 and kwargs["env"]["OMP_NUM_THREADS"] == "2"
        kwargs["stdout"].write("version fake test\n")
        (tmp_path/"A12.dat").write_text(data)
        (tmp_path/"A12.sta").write_text("synthetic status")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(run.subprocess, "run", solve)
    run.solve("A12")
    result = json.loads((tmp_path/"A12.json").read_text())
    assert len(result["basis"]) == 3
    assert result["input_sha256"] == run.digest(tmp_path/"input.json")
