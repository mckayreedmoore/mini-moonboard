"""Preparation/provenance checks only: no contact solve or numerical acceptance."""
import hashlib
import io
import json
import re
import tarfile

import pytest

from fea import spread_floor_contact as model


@pytest.fixture(scope="module")
def prepared():
    return model.prepare()


@pytest.mark.parametrize("settings", [
    {"mu": 0}, {"mu": -1}, {"mu": float("nan")}, {"mu": 1.01},
    {"stiffness": 0}, {"stiffness": 500}, {"stiffness": float("inf")},
    {"normal_penalty": 0}, {"normal_penalty": float("nan")},
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


def test_source_closure_and_exclusive_output(prepared, monkeypatch, tmp_path):
    text, record = prepared
    assert record["archive_sha256"] == model.response.digest(model.ARCHIVE)
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
