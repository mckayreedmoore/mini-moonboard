"""Pure deck geometry and launcher guards; never invokes a real solver."""
import json
import subprocess
from types import SimpleNamespace

import pytest

from fea import panel_contact_coupon as coupon
from fea.floor_contact import FACES, mesh
from fea.solve_bearing_frame import straight_mesh_volume


def test_independent_quadratic_cubes_and_actual_interface_faces():
    text, info = coupon.deck(coupon.SOURCE.read_text())
    nodes, elements = mesh(text)
    assert len(elements) == 12 and len(nodes) == 54
    assert straight_mesh_volume(nodes, elements)[0] == pytest.approx(2e6)
    assert not set(info["upper"]) & set(info["lower"])
    upper = {tuple(nodes[n]) for n in info["upper"]}
    lower = {(nodes[n][0], nodes[n][1], nodes[n][2]+100.) for n in info["lower"]}
    assert lower == upper
    assert set(info["support"]) == {n for n, p in nodes.items() if p[2] == -100.}
    assert set(info["top"]) == {n for n, p in nodes.items() if p[2] == 100.}
    for faces in info["surfaces"].values():
        assert len(faces) == 2
        assert all(nodes[elements[e][i]][2] == 0. for e, f in faces for i in FACES[f-1])
    assert set(info["prescribed_top_z_mm"]) == set(info["top"])
    assert set(info["prescribed_top_z_mm"].values()) == {-.001, -.0015, -.002}
    assert "*CLOAD" not in text and "*DLOAD" not in text and "*FRICTION" not in text
    assert "C3D8" not in text and text.count("*STEP,") == 1
    assert "CF,CFN" not in text
    for name, output in (("UPPER", "U"), ("LOWER", "U"), ("TOP", "RF"), ("SUPPORT", "RF")):
        assert f"*NODE PRINT,NSET={name},FREQUENCY=1\n{output}\n" in text


@pytest.mark.parametrize("penalty,increment", [(0., .25), (float("nan"), .25), (10000., 0.),
                                               (10000., .5), (10000., float("inf"))])
def test_invalid_parameters_rejected(penalty, increment):
    with pytest.raises(ValueError):
        coupon.deck(coupon.SOURCE.read_text(), penalty, increment)


def test_changed_cube_rejected():
    with pytest.raises(ValueError):
        coupon.deck(coupon.SOURCE.read_text().replace("5,0,0,100", "5,0,0,101"))


def test_preparation_refuses_existing_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(coupon, "DIRECTORY", tmp_path)
    marker = tmp_path/"prior"
    marker.write_text("retain")
    with pytest.raises(FileExistsError):
        coupon.prepare()
    assert marker.read_text() == "retain"


@pytest.mark.parametrize("outcome", ["success", "timeout", "failure"])
def test_bounded_solver_attempt_preserved_and_cannot_repeat(monkeypatch, tmp_path, outcome):
    directory = tmp_path/"new"
    monkeypatch.setattr(coupon, "DIRECTORY", directory)
    coupon.prepare()

    def run(command, **kwargs):
        assert command == ["ccx", "-i", "coupon"]
        assert kwargs["timeout"] == 60 and kwargs["env"]["OMP_NUM_THREADS"] == "2"
        assert kwargs["cwd"] == directory
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(command, 60)
        return SimpleNamespace(returncode=1 if outcome == "failure" else 0)

    monkeypatch.setattr(coupon.subprocess, "run", run)
    if outcome == "success":
        coupon.solve()
        row = json.loads((directory/"execution.json").read_text())
        assert "audit pending" in row["status"]
    else:
        with pytest.raises(RuntimeError, match="preserved"):
            coupon.solve()
        assert not (directory/"execution.json").exists()
    assert (directory/"launch.json").exists() and (directory/"coupon.log").exists()
    with pytest.raises(FileExistsError):
        coupon.solve()


def test_changed_deck_rejected_before_launch(monkeypatch, tmp_path):
    monkeypatch.setattr(coupon, "DIRECTORY", tmp_path/"new")
    coupon.prepare()
    (coupon.DIRECTORY/"coupon.inp").write_text("changed")
    monkeypatch.setattr(coupon.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("Must not launch"))
    with pytest.raises(ValueError, match="deck differs"):
        coupon.solve()
    assert not (coupon.DIRECTORY/"launch.json").exists()


@pytest.mark.parametrize("penalty", [10000., 100000.])
@pytest.mark.parametrize("increment", [.25, .125])
def test_sensitivity_parameters_and_explicit_directory_round_trip(monkeypatch, tmp_path, penalty, increment):
    target = tmp_path/"case"
    original_default = coupon.DIRECTORY
    coupon.main(["prepare", "--directory", str(target), "--penalty", str(penalty), "--increment", str(increment)])
    info = json.loads((target/"input.json").read_text())
    assert info["penalty"] == penalty and info["increment"] == increment
    expected, _ = coupon.deck(coupon.SOURCE.read_text(), penalty, increment)
    assert (target/"coupon.inp").read_text() == expected
    called = []

    def run(_command, **kwargs):
        called.append(kwargs["cwd"])
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(coupon.subprocess, "run", run)
    coupon.main(["solve", "--directory", str(target)])
    assert called == [target]
    assert coupon.DIRECTORY == original_default
    with pytest.raises(FileExistsError):
        coupon.prepare(penalty, increment, target)


@pytest.mark.parametrize("args", [["prepare", "--penalty", "42"],
    ["prepare", "--increment", ".5"], ["solve", "--penalty", "10000"],
    ["solve", "--increment", ".125"]])
def test_cli_rejects_unsupported_or_nonfrozen_solve_parameters(monkeypatch, args):
    monkeypatch.setattr(coupon, "prepare", lambda *_: pytest.fail("Invalid options reached preparation"))
    monkeypatch.setattr(coupon, "solve", lambda *_: pytest.fail("Invalid options reached solver"))
    with pytest.raises(SystemExit):
        coupon.main(args)
