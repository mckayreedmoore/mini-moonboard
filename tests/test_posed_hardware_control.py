"""Portable preparation-only checks; no native process or launcher execution."""
import json
import sys
import tarfile
import types
from pathlib import Path

import pytest

from fea import hardware_mass_cache, moving_hardware_solve
from fea import posed_hardware_control as posed


@pytest.fixture(scope="module", autouse=True)
def gmsh_stub():
    """Host plumbing only: artificial unit-partition basis/mass, never physical evidence.

    Keep actual module/source guards live by replacing only the external Gmsh API.
    Real integration remains required in the bounded preparation worker.
    """
    state = {}
    def add_nodes(dim, entity, tags, xyz):
        state["nodes"] = dict(zip(tags, (tuple(xyz[i:i+3]) for i in range(0, len(xyz), 3)), strict=True))
        assert all(v == float(format(v, ".12g")) for p in state["nodes"].values() for v in p)
        assert min(p[0] for p in state["nodes"].values()) == .001
    def add_elements(entity, kind, tags, ids):
        state["elements"] = tags, ids
    api = types.SimpleNamespace(addNodes=add_nodes, addElementsByType=add_elements,
        getBasisFunctions=lambda *args: (1, [.1] * 40, 1),
        getElementsByType=lambda *args: state["elements"],
        getJacobians=lambda *args: ([], [6e-6 / (7.85e-9 * len(state["elements"][0]) / 6)] * (4 * len(state["elements"][0])), []))
    fake = types.SimpleNamespace(isInitialized=lambda: False, initialize=lambda: None, finalize=lambda: None,
        option=types.SimpleNamespace(setNumber=lambda *args: None),
        model=types.SimpleNamespace(add=lambda *args: None, addDiscreteEntity=lambda *args: 1, mesh=api))
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "gmsh", fake)
        yield


@pytest.fixture(scope="module")
def evidence(tmp_path_factory):
    root = tmp_path_factory.mktemp("posed-inputs")
    results = Path(__file__).resolve().parents[1] / "fea/results"
    for archive_path, prefix, destination in ((results / "moving_hardware_control/fourth-direct-quiescent.tar.gz", "prepared/", root / "centred"),
                                               (results / "moving_fixture_preparation/pose.tar.gz", "", root / "pose")):
        with tarfile.open(archive_path) as archive:
            for member in archive:
                if member.isfile() and member.name.startswith(prefix):
                    target = destination / member.name[len(prefix):]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
    return root


@pytest.fixture(scope="module")
def prepared(evidence, tmp_path_factory):
    return posed.prepare(evidence / "centred", evidence / "pose", tmp_path_factory.mktemp("posed-output"))


def test_preparation_uses_exact_pose_and_preserves_mechanical_contract(evidence, prepared):
    original = json.loads((evidence / "centred/context.json").read_text())
    context = json.loads((prepared / "context.json").read_text())
    coordinates = json.loads((evidence / "pose/posed-nodes.json").read_text())["nodes"]
    assert context["nodes"] == coordinates
    assert context["elements"] == original["elements"]
    for key in ("material", "contact_pairs", "quiescent_diagnostic_gates", "cases", "integration_intent"):
        assert context[key] == original[key]
    assert set(context["cases"]) == {"quiescent"}
    assert context["angular_reference_mm_local"] == [1.001, .7356, 0]
    assert not (prepared / "moving.inp").exists()
    assert context["diagnostic_reference_scales"]["reference_mass_tonne"] == pytest.approx(6e-6)  # Stub output, not copied centred mass.
    moving_hardware_solve.check_reference(context)
    hardware_mass_cache.deck_mesh((prepared / "quiescent.inp").read_text(), context)
    for name, surface in context["surfaces"].items():
        prior = original["surfaces"][name]
        assert surface["faces"] == prior["faces"] and surface["nodes"] == prior["nodes"]
        assert surface["reference_cad_bounds_mm_local"] == prior["cad_bounds_mm_local"]
        assert surface["cad_bounds_mm_local"] == pytest.approx(posed.translate_bounds(prior["cad_bounds_mm_local"], posed.pose.TRANSLATION_MM if surface["body"] == "WASHER" else (0, 0, 0)))
    for body in context["bodies"].values():
        points = [coordinates[str(n)] for n in body["nodes"]]
        assert body["local_bounds_mm"] == posed.control.bounds(points)
        for surface in body["surfaces"].values():
            assert surface["local_mesh_bounds_mm"] == posed.control.bounds([coordinates[str(n)] for n in surface["nodes"]])


def test_prepared_inventory_and_source_closure_are_launcher_compatible(prepared):
    context = json.loads((prepared / "context.json").read_text())
    inventory = json.loads((prepared / "freeze.json").read_text())["files_sha256"]
    assert set(inventory) == {p.relative_to(prepared).as_posix() for p in prepared.rglob("*") if p.is_file() and p.name != "freeze.json"} | {"frozen/centred/freeze.json"}
    for name, expected in inventory.items():
        assert posed.control.digest((prepared / name).read_bytes()) == expected
    for group in ("input_sha256", "source_sha256"):
        assert all(inventory["frozen/" + name] == digest for name, digest in context[group].items())
    assert inventory["quiescent.inp"] == context["deck_sha256"]["quiescent"]


@pytest.mark.parametrize("name", ["pose/posed-nodes.json", "pose/moving_hardware_pose.py.snapshot", "centred/context.json"])
def test_pose_source_and_input_edits_are_rejected(evidence, tmp_path, monkeypatch, name):
    read = Path.read_bytes
    target = (evidence / name).resolve()
    monkeypatch.setattr(Path, "read_bytes", lambda path: read(path) + b" " if path.resolve() == target else read(path))
    with pytest.raises(ValueError, match="identity|source differs|input hash"):
        posed.prepare(evidence / "centred", evidence / "pose", tmp_path / "reports")
    assert not (tmp_path / "reports").exists()


def test_negative_or_falsified_proof_cannot_prepare(evidence):
    inputs = posed.read_inputs(evidence / "centred", evidence / "pose")
    report = json.loads(inputs["pose/report.json"])
    report["quadratic_mesh"]["radial_gap_lower_mm"] = -1
    inputs["pose/report.json"] = json.dumps(report).encode()
    with pytest.raises(ValueError, match="clearance proof"):
        posed.build_context(inputs)


@pytest.mark.parametrize("field,value", [("geometry_sha256", "0" * 64), ("step_sha256", {})])
def test_pose_cad_identity_must_match_exact_centred_geometry(evidence, tmp_path, monkeypatch, field, value):
    target = (evidence / "pose/report.json").resolve()
    read = Path.read_bytes
    report = json.loads(read(target))
    report["CAD"][field] = value
    changed = json.dumps(report).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda path: changed if path.resolve() == target else read(path))
    with pytest.raises(ValueError, match="CAD geometry/STEP identity"):
        posed.prepare(evidence / "centred", evidence / "pose", tmp_path / "reports")
    assert not (tmp_path / "reports").exists()


@pytest.mark.parametrize("source_edit", [False, True])
def test_mid_calculation_drift_never_writes_launchable_freeze(evidence, tmp_path, monkeypatch, source_edit):
    read, loads, triggered = Path.read_bytes, json.loads, []
    original = read(evidence / "centred/context.json")
    target = Path(posed.__file__).resolve() if source_edit else (evidence / "centred/context.json").resolve()
    def load(data, *args, **kwargs):
        if data == original:
            triggered.append(True)
        return loads(data, *args, **kwargs)
    monkeypatch.setattr(json, "loads", load)
    monkeypatch.setattr(Path, "read_bytes", lambda path: read(path) + b"\n" if len(triggered) >= 2 and path.resolve() == target else read(path))
    with pytest.raises(ValueError, match="source changed|input hash differs"):
        posed.prepare(evidence / "centred", evidence / "pose", tmp_path / "reports")
    assert triggered and not (tmp_path / "reports").exists()
