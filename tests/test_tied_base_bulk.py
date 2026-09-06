import hashlib
import json
import tarfile
from copy import deepcopy
from pathlib import Path

import pytest

from fea.hybrid_results import deck_geometry
from fea.tied_base_bulk import (
    audit_results,
    bulk_deck,
    digest,
    replay_archive,
    validate_mesh,
)
from fea.user_load_envelope import hull


def fixture():
    nodes = {999: (0., 0., 1000.)}
    elements = {}
    for e, (x, y) in enumerate(((-1250, 1300), (1250, 1300), (0, 0)), 1):
        corners = [(x, y, 0), (x+10, y, 0), (x, y+10, 0), nodes[999]]
        ids = [e*10, e*10+1, e*10+2, 999]+list(range(e*10+4, e*10+10))
        xyz = corners+[tuple((corners[a][i]+corners[b][i])/2 for i in range(3))
                       for a, b in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
        nodes.update(zip(ids, xyz, strict=True))
        elements[e] = tuple(ids)
    owners = {"left": [1], "right": [2], "kicker": [3]}
    info = {"parts": dict.fromkeys(owners), "intended_face_contacts": [],
            "cad": {"support_polygon_mm": hull([p[:2] for p in nodes.values() if p[2] == 0])}}
    return nodes, elements, owners, info


def test_only_original_floor_faces_receive_support():
    nodes, elements, owners, info = fixture()
    feet, groups, shared = validate_mesh(nodes, elements, owners, info)
    assert groups == {"LEFT": [(1, 1)], "RIGHT": [(2, 1)], "KICKER": [(3, 1)]}
    assert len(feet) == 18 and shared == [] and 999 not in feet
    bad = deepcopy(info)
    bad["parts"]["base_rail_left"] = bad["parts"].pop("left")
    owners["base_rail_left"] = owners.pop("left")
    with pytest.raises(ValueError, match="Floating base"):
        validate_mesh(nodes, elements, owners, bad)


def test_ownership_and_unconnected_interface_fail_closed():
    nodes, elements, owners, info = fixture()
    bad = deepcopy(owners)
    bad["left"].append(2)
    with pytest.raises(ValueError, match="ownership"):
        validate_mesh(nodes, elements, bad, info)
    info["intended_face_contacts"] = [{"parts": ["left", "right"], "area_mm2": 100.}]
    with pytest.raises(ValueError, match="shared quadratic nodes"):
        validate_mesh(nodes, elements, owners, info)


def test_disconnected_timber_and_changed_floor_polygon_fail():
    nodes, elements, owners, info = fixture()
    info["cad"]["support_polygon_mm"][0] = (-2000., 0.)
    with pytest.raises(ValueError, match="floor polygon"):
        validate_mesh(nodes, elements, owners, info)
    nodes[1000] = nodes[999]
    elements[1] = tuple(1000 if n == 999 else n for n in elements[1])
    with pytest.raises(ValueError, match="one connected"):
        validate_mesh(nodes, elements, owners, info)


def test_fixed_floor_six_load_deck_and_missing_mesh_rejected(tmp_path):
    nodes = {1: (0, 0, 0), **{n: (n, 0, 100) for n in range(2, 7)}}
    raw = "*NODE\n"+"\n".join(f"{n},{x},{y},{z}" for n, (x, y, z) in nodes.items())+"\n"
    cases = [{"name": str(i), "force_n": [0, 0, -1200]} for i in range(6)]
    text = bulk_deck(raw, [1], list(range(2, 7)), cases)
    _, feet, top = deck_geometry(text, [(str(i), (0, 0, -1)) for i in range(6)])
    assert feet == [1] and top == list(range(2, 7))
    assert "*DLOAD" not in text and "*DENSITY" not in text
    assert text.count("*CLOAD,OP=NEW") == 6
    assert "IDEALLY BONDED" in text and "no gravity" in text
    path = tmp_path/"bulk.inp"
    path.write_text(text)
    record = {"floor_nodes": feet, "load_nodes": top, "deck_path": str(path),
              "deck_sha256": hashlib.sha256(text.encode()).hexdigest()}
    with pytest.raises(ValueError, match="Missing"):
        audit_results(text, "", {"load_cases": cases}, record)
    changed_text = text.replace("7000,0.3", "700,0.3")
    with pytest.raises(ValueError, match="changed"):
        audit_results(changed_text, "", {"load_cases": cases}, record)
    assert path.read_text() == text


@pytest.fixture(scope="module")
def published_z275_raw():
    root = Path(__file__).parents[1]/"fea/results/tied_base_bulk"
    report = json.loads((root/"report.json").read_text())
    with tarfile.open(root/report["candidates"]["z275"]["archive"]) as archive:
        text = archive.extractfile("bulk.inp").read().decode()
        data = archive.extractfile("bulk.dat").read().decode()
        info = json.load(archive.extractfile("input.json"))
        record = json.load(archive.extractfile("run.json"))
    return text, data, info, record


@pytest.mark.parametrize("mutation", ["missing", "empty", "duplicate", "swapped", "cross_assigned"])
def test_patch_reaction_groups_must_match_actual_deck_faces(published_z275_raw, mutation):
    text, data, info, original = published_z275_raw
    record = deepcopy(original)
    groups = record["floor_group_nodes"]
    if mutation == "missing":
        del record["floor_group_nodes"]
    elif mutation == "empty":
        record["floor_group_nodes"] = {}
    elif mutation == "duplicate":
        groups["LEFT"].append(groups["LEFT"][0])
    elif mutation == "swapped":
        groups["LEFT"], groups["RIGHT"] = groups["RIGHT"], groups["LEFT"]
    else:
        node = groups["LEFT"].pop()
        groups["RIGHT"].append(node)
        groups["RIGHT"].sort()
    with pytest.raises(ValueError, match="floor patch nodes"):
        audit_results(text, data, info, record)


def test_complete_mesh_with_missing_solver_output_is_rejected(published_z275_raw):
    text, _, info, record = published_z275_raw
    with pytest.raises(ValueError, match="Missing"):
        audit_results(text, "", info, record)


@pytest.mark.parametrize("candidate", ["baseline", "z100", "z275"])
def test_published_bulk_evidence_replays_without_generated_files(candidate):
    root = Path(__file__).parents[1]/"fea/results/tied_base_bulk"
    report = json.loads((root/"report.json").read_text())
    expected = report["candidates"][candidate]
    archive = root/expected["archive"]
    assert digest(archive) == expected["archive_sha256"]
    record, info = replay_archive(archive)
    assert record["audited_results"] == expected["audited_results"]
    assert info["candidate"] == candidate
    assert len(record["audited_results"]["max_loaded_node_displacement_mm"]) == 6
    assert expected["cad_mass_kg"] == pytest.approx(expected["mesh_mass_kg"], rel=.001)
    for row in report["comparisons"]:
        assert row["max_loaded_node_displacement_mm"][candidate] == expected["audited_results"]["max_loaded_node_displacement_mm"][row["case"]]
