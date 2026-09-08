import copy
import hashlib
import json
import tarfile
from pathlib import Path

import pytest

from fea.floor_contact import mesh
from fea.gusset_recovery import GATES, compare, partition, prescribed_deck, summarize
from fea.timber_asymmetric import HOLDS
from fea.wide_asymmetric import authenticated_inputs


def test_partition_retains_ambiguous_edge_without_double_counting():
    row = {"node_ids": [1, 2, 3, 4], "shared_nodes": [1, 2, 3],
           "interfaces": {"rim": [{"nodes": [1, 2]}], "header": [{"nodes": [2, 3]}]}}
    assert partition(row) == {"rim": [1], "header & rim": [2], "header": [3], "unshared": [4]}
    row["shared_nodes"].append(4)
    with pytest.raises(ValueError, match="Unclassified"):
        partition(row)


def test_archive_replays_mesh_fields_decks_reactions_and_precision_gates():
    with tarfile.open("fea/results/gusset-recovery.tar.gz") as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    assert report["gates"] == GATES
    assert set(files)-{"report.json"} == set(report["artifact_sha256"])
    for name, sha in report["artifact_sha256"].items():
        assert hashlib.sha256(files[name]).hexdigest() == sha
    for name, sha in report["source_sha256"].items():
        assert not Path(name).is_absolute()
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
    _, parent, _, _ = authenticated_inputs()
    all_nodes, all_elements = mesh(parent)
    gussets = json.loads(Path("fea/results/gusset-interfaces.json").read_text())["gussets"]
    nodes = {n: all_nodes[n] for g in gussets.values() for n in g["node_ids"]}
    elements = {e: all_elements[e] for g in gussets.values() for e in g["element_ids"]}
    assert len(nodes) == 3455 and len(elements) == 1622
    for hold in HOLDS:
        fields = {float(t): {int(n): v for n, v in rows.items()}
                  for t, rows in json.loads(files[f"{hold}.selected.json"]).items()}
        for digits in (6, 5):
            name = f"{hold}-{digits}"
            deck = files[name+".inp"].decode()
            assert deck == prescribed_deck(nodes, elements, fields, digits)
            assert mesh(deck) == (nodes, elements)
            assert deck.count("*BOUNDARY,OP=NEW") == 3
            assert "*CLOAD" not in deck and "*DLOAD" not in deck
            log = files[name+".log"].decode()
            assert "*ERROR" not in log.upper() and "Job finished" in log
            replay = summarize(files[name+".dat"].decode(), nodes, fields, digits, gussets)
            assert replay == report["runs"][name]
            for step in replay.values():
                for side in step["sides"].values():
                    # Independent complete-body numerical balance checks, not connection strength.
                    assert max(map(abs, side["body_residual_n_nmm"][:3])) < .001
                    assert max(map(abs, side["body_residual_n_nmm"][3:])) < .1
        nominal, rounded = (report["runs"][f"{hold}-{d}"] for d in (6, 5))
        assert compare(nominal, rounded) == report["comparisons"][hold]
        assert report["comparisons"][hold]["passed_numerical_gates"]
        broken = copy.deepcopy(rounded)
        broken["1.0"]["sides"]["left"]["buckets"]["unshared"]["maximum_node_force_n"] = 1.01
        assert not compare(nominal, broken)["passed_numerical_gates"]
        broken = copy.deepcopy(rounded)
        broken["1.0"]["sides"]["left"]["buckets"]["base_header"]["force_n"][0] += 1000
        assert not compare(nominal, broken)["passed_numerical_gates"]
    assert report["passed_numerical_gates"]


def test_prescribed_fields_reject_missing_steps_nodes_and_nonfinite_values():
    nodes = {1: (0., 0., 0.)}
    fields = {t: {1: [0., 0., 0.]} for t in (1., 2., 3.)}
    with pytest.raises(ValueError, match="three bases"):
        prescribed_deck(nodes, {}, {1.: fields[1.]}, 6)
    fields[1.] = {}
    with pytest.raises(ValueError, match="coverage"):
        prescribed_deck(nodes, {}, fields, 6)
    fields[1.] = {1: [float("nan"), 0., 0.]}
    with pytest.raises(ValueError, match="Invalid displacement"):
        prescribed_deck(nodes, {}, fields, 6)
