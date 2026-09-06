import copy
import gzip
import json
import sys
import types
from pathlib import Path

import pytest

from fea import hardware_mass_cache as cache


def context():
    return {"nodes": {str(n): [float(n), 0., 0.] for n in range(1, 21)},
            "elements": {"1": list(range(1, 11)), "2": list(range(11, 21))},
            "bodies": {"BOLT_NUT": {"elements": [1], "nodes": list(range(1, 11))},
                       "WASHER": {"elements": [2], "nodes": list(range(11, 21))}},
            "material": {"density_tonne_mm3": 1.}}


def blocks(elements, nodes, density, **kwargs):
    assert not kwargs or kwargs == {"integration_rule": "Gauss8"}
    assert {n for ids in elements.values() for n in ids} == set(nodes)
    # Rank-one block with negative entries/row sums must not be lumped.
    values = [-1.] + [1.]*9
    block = [[density*a*b for b in values] for a in values]
    return {e: ([ids[i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 8)], block) for e, ids in elements.items()}


@pytest.fixture
def prepared(tmp_path):
    path = tmp_path / "context.json"
    data = context()
    lines = ["*NODE"] + [n + "," + ",".join(map(str, p)) for n, p in data["nodes"].items()]
    for name, body in data["bodies"].items():
        lines += [f"*ELEMENT,TYPE=C3D10,ELSET={name}"]
        lines += [str(e) + "," + ",".join(map(str, data["elements"][str(e)])) for e in body["elements"]]
        lines += [f"*SOLID SECTION,ELSET={name},MATERIAL=STEEL"]
    lines += ["*MATERIAL,NAME=STEEL", "*ELASTIC", "210000.,0.3", "*DENSITY", "1.0"]
    deck = tmp_path / "quiescent.inp"
    deck.write_text("\n".join(lines) + "\n")
    data["deck_sha256"] = {"quiescent": cache.sha(deck.read_bytes())}
    path.write_text(json.dumps(data))
    (tmp_path / "freeze.json").write_text(json.dumps({"files_sha256": {
        "context.json": cache.sha(path.read_bytes()), "quiescent.inp": cache.sha(deck.read_bytes())}}))
    return path


def stub_integration(monkeypatch):
    snapshot = cache.sources()
    monkeypatch.setattr(cache, "sources", lambda: snapshot)
    monkeypatch.setattr(cache.dynamic_momentum, "calculix_221_mass", blocks)
    monkeypatch.setattr(cache.dynamic_momentum, "consistent_mass", blocks)
    monkeypatch.setitem(sys.modules, "gmsh", types.SimpleNamespace(__version__="test-only-stub"))


def test_cache_preserves_each_full_operator_block_and_roundtrips(prepared, tmp_path, monkeypatch):
    stub_integration(monkeypatch)
    first = cache.build(prepared, tmp_path / "outputs")
    second = cache.build(prepared, tmp_path / "outputs")
    assert first != second
    report = json.loads((first / "report.json").read_text())
    data = (first / "blocks.json.gz").read_bytes()
    assert cache.sha(data) == report["blocks_sha256"]
    decoded = json.loads(gzip.decompress(data))
    assert report["gmsh_version"] == decoded["gmsh_version"] == "test-only-stub"
    assert cache.validate_cache(decoded, prepared.read_bytes()) == report["body_mass_tonne"]
    assert all(mass == 64 for bodies in report["body_mass_tonne"].values() for mass in bodies.values())
    ids, block = decoded["operators"]["native_four_point"]["BOLT_NUT"]["1"]
    assert ids == [1, 2, 3, 4, 5, 6, 7, 8, 10, 9]
    assert len(block) == 10 and all(len(row) == 10 for row in block)
    assert sum(block[0]) == -8
    assert (first / "context.json").read_bytes() == prepared.read_bytes()
    for name, digest in report["source_sha256"].items():
        assert cache.sha((first / (name + ".snapshot")).read_bytes()) == digest


@pytest.mark.parametrize("fault", ["missing", "order", "nan", "asymmetric", "zero", "dimension"])
def test_bad_mass_blocks_rejected(fault):
    data = {1: list(range(1, 11))}
    result = blocks(data, dict.fromkeys(range(1, 11)), 1)
    if fault == "missing":
        result = {}
    elif fault == "order":
        result[1][0][-2:] = [9, 10]
    elif fault == "nan":
        result[1][1][0][0] = float("nan")
    elif fault == "asymmetric":
        result[1][1][1][0] += .01
    elif fault == "zero":
        result[1] = (result[1][0], [[0.]*10 for _ in range(10)])
    else:
        result[1][1].pop()
    with pytest.raises(ValueError):
        cache.validate_blocks(result, data)


@pytest.mark.parametrize("fault", ["shared", "extra", "duplicate", "density", "nonfinite"])
def test_bad_context_ownership_rejected(fault):
    data = context()
    if fault == "shared":
        data["bodies"]["WASHER"] = copy.deepcopy(data["bodies"]["BOLT_NUT"])
    elif fault == "extra":
        data["nodes"]["21"] = [0, 0, 0]
    elif fault == "duplicate":
        data["bodies"]["WASHER"]["elements"].append(2)
    elif fault == "density":
        data["material"]["density_tonne_mm3"] = 0
    else:
        data["nodes"]["1"][0] = float("inf")
    with pytest.raises(ValueError):
        cache.context_mesh(data)


def test_modified_prepared_context_rejected_before_integration(prepared, tmp_path, monkeypatch):
    prepared.write_bytes(prepared.read_bytes() + b" ")
    snapshot = cache.sources()
    monkeypatch.setattr(cache.dynamic_momentum, "calculix_221_mass", lambda *args: pytest.fail("must not integrate"))
    monkeypatch.setattr(cache, "sources", lambda: snapshot)
    with pytest.raises(ValueError, match="Prepared context hash"):
        cache.build(prepared, tmp_path / "outputs")
    assert not (tmp_path / "outputs").exists()


def test_source_drift_and_foreign_import_rejected(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(cache.dynamic_momentum, "__file__", "/tmp/foreign/dynamic_momentum.py")
        with pytest.raises(ValueError, match="outside this checkout"):
            cache.sources()
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: original(p) + b"# changed" if p.name == "hardware_mass_cache.py" else original(p))
    with pytest.raises(ValueError, match="source changed"):
        cache.sources()


def test_drift_during_integration_cannot_publish_cache(prepared, tmp_path, monkeypatch):
    stub_integration(monkeypatch)
    def mutate(elements, nodes, density, **kwargs):
        prepared.write_bytes(prepared.read_bytes() + b" ")
        return blocks(elements, nodes, density)
    monkeypatch.setattr(cache.dynamic_momentum, "consistent_mass", mutate)
    with pytest.raises(ValueError, match="changed during integration"):
        cache.build(prepared, tmp_path / "outputs")
    directory, = (tmp_path / "outputs").iterdir()
    assert (directory / "context.json").exists()
    assert not (directory / "report.json").exists()
    assert not (directory / "blocks.json.gz").exists()


def test_serialized_deck_coordinates_must_match_even_with_valid_hashes(prepared, tmp_path):
    data = json.loads(prepared.read_bytes())
    data["nodes"]["1"][0] += .1
    prepared.write_text(json.dumps(data))
    freeze = json.loads((tmp_path / "freeze.json").read_text())
    freeze["files_sha256"]["context.json"] = cache.sha(prepared.read_bytes())
    (tmp_path / "freeze.json").write_text(json.dumps(freeze))
    with pytest.raises(ValueError, match="Serialized deck mesh differs"):
        cache.build(prepared, tmp_path / "outputs")
    assert not (tmp_path / "outputs").exists()


def test_in_memory_configuration_drift_is_rejected(monkeypatch):
    monkeypatch.setattr(cache, "LIMITS", "qualified")
    with pytest.raises(ValueError, match="configuration changed"):
        cache.sources()


@pytest.mark.parametrize("fault", ["different_density", "missing_density", "multiple_density", "wrong_material",
                                  "wrong_section", "missing_section", "duplicate_section", "wrong_body"])
def test_actual_density_and_body_sections_rejected_even_with_resealed_hashes(prepared, tmp_path, fault):
    deck = tmp_path / "quiescent.inp"
    text = deck.read_text()
    if fault == "different_density":
        text = text.replace("*DENSITY\n1.0", "*DENSITY\n7.85e-9")
    elif fault == "missing_density":
        text = text.replace("*DENSITY\n1.0\n", "")
    elif fault == "multiple_density":
        text += "*DENSITY\n1.0\n"
    elif fault == "wrong_material":
        text = text.replace("*MATERIAL,NAME=STEEL", "*MATERIAL,NAME=OTHER")
    elif fault == "wrong_section":
        text = text.replace("ELSET=WASHER,MATERIAL=STEEL", "ELSET=WASHER,MATERIAL=OTHER")
    elif fault == "missing_section":
        text = text.replace("*SOLID SECTION,ELSET=WASHER,MATERIAL=STEEL\n", "")
    elif fault == "duplicate_section":
        text += "*SOLID SECTION,ELSET=WASHER,MATERIAL=STEEL\n"
    else:
        text = text.replace("*ELEMENT,TYPE=C3D10,ELSET=WASHER", "*ELEMENT,TYPE=C3D10,ELSET=OTHER")
    deck.write_text(text)
    context_data = json.loads(prepared.read_text())
    context_data["deck_sha256"]["quiescent"] = cache.sha(deck.read_bytes())
    prepared.write_text(json.dumps(context_data))
    freeze = json.loads((tmp_path / "freeze.json").read_text())
    freeze["files_sha256"].update({"context.json": cache.sha(prepared.read_bytes()), "quiescent.inp": cache.sha(deck.read_bytes())})
    (tmp_path / "freeze.json").write_text(json.dumps(freeze))
    with pytest.raises(ValueError, match="assignment differs|sections or density differ"):
        cache.build(prepared, tmp_path / "outputs")
    assert not (tmp_path / "outputs").exists()


def add_moving_deck(prepared):
    directory = prepared.parent
    moving = (directory / "quiescent.inp").read_bytes() + b"** separately frozen moving deck\n"
    (directory / "moving.inp").write_bytes(moving)
    data = json.loads(prepared.read_bytes())
    data["deck_sha256"]["moving"] = cache.sha(moving)
    prepared.write_text(json.dumps(data))
    path = directory / "freeze.json"
    freeze = json.loads(path.read_bytes())
    freeze["files_sha256"].update({"context.json": cache.sha(prepared.read_bytes()), "moving.inp": cache.sha(moving)})
    path.write_text(json.dumps(freeze))
    return moving


def test_explicit_moving_selects_only_its_frozen_deck(prepared, tmp_path, monkeypatch):
    moving = add_moving_deck(prepared)
    stub_integration(monkeypatch)
    directory = cache.build(prepared, tmp_path / "outputs", case="moving")
    assert (directory / "moving.inp").read_bytes() == moving
    assert not (directory / "quiescent.inp").exists()
    report = json.loads((directory / "report.json").read_text())
    assert report["case"] == "moving" and report["deck_sha256"] == cache.sha(moving)


def test_explicit_quiet_keeps_default_payload_and_schema(prepared, tmp_path, monkeypatch):
    stub_integration(monkeypatch)
    default = cache.build(prepared, tmp_path / "outputs")
    explicit = cache.build(prepared, tmp_path / "outputs", case="quiescent")
    assert {p.name: p.read_bytes() for p in default.iterdir()} == {p.name: p.read_bytes() for p in explicit.iterdir()}
    assert "case" not in json.loads((default / "report.json").read_text())


@pytest.mark.parametrize("case", ["", "MOVING", "../moving", None, True, []])
def test_invalid_case_rejected_before_read_or_integration(tmp_path, case):
    with pytest.raises(ValueError, match="case must be"):
        cache.build(tmp_path / "missing", tmp_path / "outputs", case=case)
    assert not (tmp_path / "outputs").exists()


def test_absent_moving_case_is_not_inferred_from_quiet(prepared, tmp_path):
    with pytest.raises(ValueError, match="case/deck is absent"):
        cache.build(prepared, tmp_path / "outputs", case="moving")
    assert not (tmp_path / "outputs").exists()


@pytest.mark.parametrize("fault", ["hash", "coordinate", "density"])
def test_moving_deck_identity_and_mesh_checked_before_integration(prepared, tmp_path, fault):
    moving = add_moving_deck(prepared)
    if fault == "hash":
        moving += b"changed"
    elif fault == "coordinate":
        moving = moving.replace(b"1,1.0,0.0,0.0", b"1,1.1,0.0,0.0", 1)
    else:
        moving = moving.replace(b"*DENSITY\n1.0", b"*DENSITY\n2.0")
    (tmp_path / "moving.inp").write_bytes(moving)
    if fault != "hash":
        data = json.loads(prepared.read_bytes())
        data["deck_sha256"]["moving"] = cache.sha(moving)
        prepared.write_text(json.dumps(data))
        freeze = json.loads((tmp_path / "freeze.json").read_bytes())
        freeze["files_sha256"].update({"context.json": cache.sha(prepared.read_bytes()), "moving.inp": cache.sha(moving)})
        (tmp_path / "freeze.json").write_text(json.dumps(freeze))
    with pytest.raises(ValueError, match="deck hash differs|deck mesh differs|density differ"):
        cache.build(prepared, tmp_path / "outputs", case="moving")
    assert not (tmp_path / "outputs").exists()
