"""Deck/launcher guards on small synthetic fixtures; not frame contact approval."""
import hashlib
import json
import subprocess

import pytest

from fea import panel_contact_coupon as coupon
from fea import timber_panel_contact as run
from fea.floor_contact import FACES, mesh


def fixture():
    text, ctx = coupon.deck(coupon.SOURCE.read_text())
    nodes, elements = mesh(text)
    lower = {nodes[n]: n for n in ctx["lower"]}
    mapping = {n: lower[nodes[n]] for n in ctx["upper"] if nodes[n][2] == 0.}
    nodes = {n: (p[0], p[1], p[2]+100.) for n, p in nodes.items()}
    items = list(mapping.items())
    faces = {}
    for index, side in enumerate(("left", "right")):
        pair = {}
        for field, label in (("panel", "SLAVE"), ("leg", "MASTER")):
            e, f = ctx["surfaces"][label][index]
            pair[field] = {"element": e, "face": f"S{f}", "nodes": [elements[e][i] for i in FACES[f-1]]}
        faces[side] = {"pairs": [pair]}
    return {"nodes": nodes, "elements": elements, "floor_nodes": ctx["support"],
        "load_node": ctx["top"][0], "force_n": run.FORCE,
        "node_map": {"left": dict(items[:4]), "right": dict(items[4:])},
        "contact_faces": faces, "penalty": 10000., "increment": .125}


def test_two_contact_pairs_direct_load_and_complete_output():
    info = fixture()
    deck = run.expected_deck(info)
    assert run.expected_deck(json.loads(json.dumps(info))) == deck
    assert deck.count("*CONTACT PAIR,") == 2 and deck.count("*STEP,") == 1
    assert "*STEP,NLGEOM" in deck and "*DLOAD" not in deck and "*FRICTION" not in deck
    assert f'{info["load_node"]},3,{run.FORCE[2]:.15g}' in deck
    assert run.FORCE[2] == pytest.approx(-2668.93296912)
    assert f'{info["load_node"]},2,300' in deck
    assert "*NODE PRINT,NSET=FEET,FREQUENCY=1\nU,RF" in deck
    assert "*NODE PRINT,NSET=PAIRS,FREQUENCY=1\nU" in deck
    for side in ("LEFT", "RIGHT"):
        assert f"SLAVE_{side},MASTER_{side}" in deck
        assert f"*CONTACT PRINT,SLAVE=SLAVE_{side},MASTER=MASTER_{side},FREQUENCY=1\nCF" in deck


@pytest.mark.parametrize("defect", ["force", "penalty", "increment", "load", "pair", "face", "coordinates"])
def test_invalid_scope_or_geometry_rejected(defect):
    info = fixture()
    if defect == "force":
        info["force_n"] = [0, 0, -1000]
    elif defect in ("penalty", "increment"):
        info[defect] = float("nan")
    elif defect == "load":
        info["load_node"] = info["floor_nodes"][0]
    elif defect == "pair":
        del info["contact_faces"]["left"]
    elif defect == "coordinates":
        info["nodes"][info["load_node"]] = (0, 0, float("inf"))
    else:
        info["contact_faces"]["left"]["pairs"][0]["leg"]["nodes"] = [999]
    with pytest.raises(ValueError):
        run.expected_deck(info)


def test_preparation_refuses_existing_output_before_archives(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "authenticated_inputs", lambda: pytest.fail("Should refuse first"))
    with pytest.raises(FileExistsError):
        run.prepare(directory=tmp_path)


def test_timeout_retains_attempt_and_blocks_retry(monkeypatch, tmp_path):
    info = fixture()
    text = run.expected_deck(info)
    source = tmp_path/"source"
    source.write_text("unchanged")
    directory = tmp_path/"run"
    directory.mkdir()
    info.update(candidate="timber-base-development", limits=run.LIMITS,
        source_sha256={str(source): run.common.digest(source)}, deck_sha256=hashlib.sha256(text.encode()).hexdigest())
    (directory/"input.json").write_text(json.dumps(info))
    (directory/"contact.inp").write_text(text)

    def timeout(command, **kwargs):
        assert kwargs["timeout"] == 600
        assert kwargs["env"]["OMP_NUM_THREADS"] == "2"
        raise subprocess.TimeoutExpired(command, 600)

    monkeypatch.setattr(run.subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="preserved"):
        run.solve(directory)
    assert (directory/"launch.json").exists() and (directory/"contact.log").exists()
    with pytest.raises(FileExistsError):
        run.solve(directory)


def test_solve_cli_rejects_parameter_override():
    with pytest.raises(SystemExit):
        run.main(["solve", "--penalty", "100000"])
