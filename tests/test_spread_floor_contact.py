"""Preparation/provenance checks only: no contact solve or numerical acceptance."""
import hashlib
import io
import json
import re
import tarfile

import pytest

from fea import spread_floor_contact as model


@pytest.fixture(scope="module", params=[model.ARCHIVE, model.COMPACT_ARCHIVE], ids=["extended", "compact"])
def prepared(request):
    return model.prepare(archive=request.param)


@pytest.mark.parametrize("settings", [
    {"mu": 0}, {"mu": -1}, {"mu": float("nan")}, {"mu": 1.01},
    {"stiffness": 0}, {"stiffness": 500}, {"stiffness": float("inf")},
    {"normal_penalty": 0}, {"normal_penalty": float("nan")},
    {"initial_increment": 0}, {"initial_increment": .2}, {"max_increment": 1.01},
    {"initial_increment": float("nan")}, {"max_increment": float("inf")},
    {"initial_increment": True},
])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):
        model.prepare(**settings)


def test_complete_unpinned_topology_and_loading(prepared):
    text, record = prepared
    value, context = record["mapped_input"], record["connector_context"]
    # Every actual mesh/virtual node survives; ground IDs never alias a spring
    # node, and ground elements never alias the appended SPRING2 elements.
    parsed_nodes, parsed_elements = model.floor.mesh(text)
    ground_ids = {n for group in record["ground_nodes"].values() for n in group}
    assert not ground_ids & context["nodes"].keys()
    assert parsed_nodes.keys() == context["nodes"].keys() | ground_ids
    assert parsed_elements == {e: tuple(ids) for e, ids in value["elements"].items()}
    assert all(parsed_nodes[n] == pytest.approx(p) for n,p in context["nodes"].items())
    element_ids = []
    in_elements = False
    for line in text.splitlines():
        if line.startswith("*"):
            in_elements = line.startswith("*ELEMENT,")
        elif in_elements and line.strip():
            element_ids.append(int(line.split(",")[0]))
    assert len(element_ids) == len(set(element_ids)) == len(parsed_elements)+48+3
    assert text.count("*EQUATION\n") == 96
    assert text.count("TYPE=SPRING2") == 48
    assert text.count("TYPE=MORTAR") == 3
    assert text.count("*DENSITY\n6e-10\n") == 2
    # Boundary cards constrain bottom ground nodes only, including both steps.
    boundaries = re.findall(r"\*BOUNDARY[^\n]*\n([^*]+)", text)
    assert len(boundaries) == 1
    assert set(boundaries[0].strip().splitlines()) == {
        "BOTTOM_LEFT,1,3,0", "BOTTOM_RIGHT,1,3,0", "BOTTOM_KICKER,1,3,0"}
    for name, ids in record["bottom_nodes"].items():
        assert len(ids) == 4
        assert all(record["ground_nodes"][name][n][2] == -100 for n in ids)
        assert f"*NODE PRINT,NSET=GROUND_{name}\nU,RF\n" in text
    groups = model.floor.floor_faces(value["nodes"], value["elements"])
    assert record["floor_faces"] == groups
    covered = {value["elements"][e][i] for faces in groups.values()
               for e,f in faces for i in model.floor.FACES[f-1]}
    assert covered == set(context["feet"])
    steps = text.split("*STEP,NLGEOM,INC=200\n")[1:]
    assert len(steps) == 2 and "*CLOAD" not in steps[0]
    assert all("TIMBER,GRAV,9806.65,0,0,-1" in s for s in steps)
    load = record["load"]
    assert load["hold"] == "A12" and load["node"] == 41876
    assert load["force_n"] == pytest.approx([0,300,-2224.11080763025])
    cload = steps[1].split("*CLOAD,OP=NEW\n")[1].split("*", 1)[0].splitlines()
    assert [line.split(",")[:2] for line in cload] == [["41876","2"],["41876","3"]]
    assert [float(line.split(",")[2]) for line in cload] == pytest.approx(load["force_n"][1:])
    assert text.count("*CONTACT FILE\nCDIS,CSTR") == 2
    assert text.count("*STATIC\n0.05,1,1e-6,0.1\n") == 2
    assert record["initial_increment"] == .05 and record["max_increment"] == .1
    if record["parent_report"]["extension_mm"] == 300:
        with tarfile.open("fea/results/spread-floor-contact/untied-mu02-k1000.tar.gz") as archive:
            assert text == archive.extractfile("contact.inp").read().decode()
    for side in ("left", "right"):
        assert {value["elements"][e][i] for e,f in groups[side.upper()] for i in model.floor.FACES[f-1]} == set(value["legs"][side]["floor_nodes"])


def test_source_closure_and_exclusive_output(prepared, monkeypatch, tmp_path):
    text, record = prepared
    assert record["archive_sha256"] == model.response.digest(record["archive"])
    assert record["parent_report"]["extension_mm"] == (0 if "-e0-" in record["archive"] else 300)
    model.response.unchanged(record["source_sha256"])
    assert record["deck_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert not record["solved"] and not record["qualified_for_design"]
    monkeypatch.setattr(model, "prepare", lambda **kw: prepared)
    path = model.write(tmp_path/"trial")
    assert (path/"contact.inp").read_text() == text
    assert json.loads((path/"input.json").read_text())["deck_sha256"] == record["deck_sha256"]
    with pytest.raises(FileExistsError):
        model.write(path)


def test_changed_source_rejected(monkeypatch):
    def reject(sources):
        raise ValueError("changed frozen source")
    monkeypatch.setattr(model.response, "unchanged", reject)
    with pytest.raises(ValueError, match="changed frozen source"):
        model.prepare()


def test_altered_archive_artifact_rejected(tmp_path):
    path = tmp_path/"bad.tar.gz"
    files = {"input.json": b"changed", "report.json": json.dumps({
        "artifact_sha256": {"input.json": hashlib.sha256(b"original").hexdigest()}
    }).encode()}
    with tarfile.open(path, "w:gz") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    with pytest.raises(ValueError, match="artifact identity"):
        model.prepare(archive=path)


@pytest.mark.parametrize("initial,maximum,minimum_text", [(.25, .5, "1e-6"), (1e-7, 1e-7, "1e-07")])
def test_compact_larger_ramp_preserves_model(prepared, monkeypatch, initial, maximum, minimum_text):
    original, record = prepared
    files, report, value = model.authenticated_input(record["archive"])
    monkeypatch.setattr(model, "authenticated_input", lambda path: (files, report, value))
    text, changed = model.prepare(archive=record["archive"], initial_increment=initial, max_increment=maximum)
    assert text == original.replace("0.05,1,1e-6,0.1", f"{initial:g},1,{minimum_text},{maximum:g}")
    assert changed["initial_increment"] == initial and changed["max_increment"] == maximum
    assert changed["minimum_increment"] <= initial
    assert changed["archive_sha256"] == record["archive_sha256"]
    assert changed["deck_sha256"] != record["deck_sha256"]


def test_unsupported_identity_rejected(tmp_path):
    # No artifacts are needed: valid source integrity closure reaches the
    # independent geometry identity gate before mapped-input parsing.
    path = tmp_path/"wrong.tar.gz"
    source_path = "fea/spread_floor_contact.py"
    report = {"artifact_sha256": {}, "source_sha256": {source_path: model.response.digest(source_path)}, "geometry": "spread-100x50-top150",
              "stock": "2x6", "mesh_size_mm": 40., "leg_modulus_mpa": 7000., "extension_mm": 150.}
    payload = json.dumps(report).encode()
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo("report.json")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    with pytest.raises(ValueError, match="e0 or e300"):
        model.authenticated_input(path)
