"""Archived released-interface replay; no CAD construction or new solver run."""
import gzip
import hashlib
import json

import pytest

from fea import publish_timber_release as publisher
from fea import timber_release as run
from fea.floor_contact import mesh


@pytest.fixture(scope="module")
def evidence():
    report = json.loads((publisher.OUTPUT/"summary.json").read_text())
    assert set(report["replay_archives"]) == {name+".gz" for name in publisher.NAMES}
    assert {p.name for p in publisher.OUTPUT.iterdir()} == set(report["replay_archives"]) | {"summary.json"}
    decoded = {}
    for name, hashes in report["replay_archives"].items():
        data = (publisher.OUTPUT/name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == hashes["gzip_sha256"]
        raw = gzip.decompress(data)
        assert hashlib.sha256(raw).hexdigest() == hashes["uncompressed_sha256"]
        decoded[name.removesuffix(".gz")] = raw.decode()
    return report, decoded


def test_release_publication_source_launch_and_output_replay(evidence):
    report, decoded = evidence
    info, record, launch = (json.loads(decoded[name]) for name in ("input.json", "K12.json", "K12.launch.json"))
    assert report["input"] == info
    assert report["candidate"] == info["candidate"] == record["candidate"] == "timber-base-development"
    assert report["limits"] == record["limits"] == info["limits"] == run.LIMITS
    assert report["source_sha256"] == {**info["source_sha256"],
        "fea/publish_timber_release.py": run.basis_run.digest("fea/publish_timber_release.py")}
    assert all(run.basis_run.digest(p) == sha for p, sha in report["source_sha256"].items())
    input_sha = hashlib.sha256(decoded["input.json"].encode()).hexdigest()
    assert record["input_sha256"] == launch["input_sha256"] == input_sha
    assert launch["source_sha256"] == info["source_sha256"]
    assert launch["deck_sha256"] == info["deck_sha256"] == hashlib.sha256(decoded["K12.inp"].encode()).hexdigest()
    for name in publisher.NAMES:
        if name not in ("input.json", "K12.json"):
            assert hashlib.sha256(decoded[name].encode()).hexdigest() == record["artifacts"][name]
    assert "*ERROR" not in decoded["K12.log"].upper()
    replay = run.audit(decoded["K12.inp"], decoded["K12.dat"], info)
    assert len(replay["basis"]) == 3
    publisher.validate_replay(replay, report)
    publisher.validate_replay(replay, record)
    required = set(publisher.NAMES)-{"input.json", "K12.json"}
    assert report["omitted_diagnostic_artifacts_sha256"] == {
        name: sha for name, sha in record["artifacts"].items() if name not in required}


def test_archived_transformation_reconstructs_exact_accepted_mesh(evidence):
    from mini_moonboard import box_frame as b

    report, decoded = evidence
    info = report["input"]
    accepted, deck, _, sources = run.authenticated_inputs()
    assert info["accepted_mesh_deck_sha256"] == accepted["deck_sha256"]
    assert all(info["source_sha256"][p] == sha for p, sha in sources.items())
    joint = json.loads(run.REPORT.read_text())
    nodes, elements = mesh(deck)
    legs = {side: run.recover(nodes, elements, leg) for side, leg in joint["legs"].items()}
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    target, normal = next((p, n) for label, p, n in run.basis_run.locations() if label == "K12")
    mapping = run.basis_run.map_target(nodes, target, normal, set(feet))
    assert info["mapping"] == mapping
    assert info["floor_nodes"] == feet
    released_nodes, released_elements, proof = run.release(nodes, elements, legs,
        {"left": -b.HALF, "right": b.HALF}, b.point(0, 0, 0).toTuple(), b.normal().toTuple(),
        floor_nodes=feet, load_nodes={mapping["node"], *accepted["load_nodes"]})
    node_map = {side: data["node_map"] for side, data in proof["legs"].items()}
    assert json.loads(json.dumps(proof)) == info["release_proof"]
    assert json.loads(json.dumps(node_map)) == info["node_map"]
    assert decoded["K12.inp"] == run.expected_deck(released_nodes, released_elements, feet, mapping["node"], node_map)
    assert mesh(decoded["K12.inp"]) == (released_nodes, released_elements)
    assert len(released_nodes)-len(nodes) == 144
    assert elements.keys() == released_elements.keys()
    for element, ids in elements.items():
        assert tuple(nodes[n] for n in ids) == tuple(released_nodes[n] for n in released_elements[element])
    for n in {*feet, mapping["node"], *accepted["load_nodes"]}:
        assert released_nodes[n] == nodes[n]
    baseline = json.loads((run.BASELINE/"summary.json").read_text())
    assert info["bonded_basis"] == baseline["basis_results"]["K12"]["basis"]
