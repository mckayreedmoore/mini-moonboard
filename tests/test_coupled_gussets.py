import hashlib
import json
import math
import tarfile
from pathlib import Path

import pytest
from replay_roundoff import assert_roundoff_equal

from fea.coupled_gussets import GATES, STIFFNESSES, audit, combine, deck, prepare
from fea.floor_contact import mesh
from fea.gusset_recovery import MAP
from fea.wide_asymmetric import authenticated_inputs


def test_release_changes_only_shared_gusset_node_identity_not_geometry():
    nodes, elements, points, cases, _, remaps = prepare()
    _, parent, _, _ = authenticated_inputs()
    old_nodes, old_elements = mesh(parent)
    mapping = json.loads(MAP.read_text())["gussets"]
    assert len(nodes)-len(old_nodes) == sum(map(len, remaps.values())) == 830
    assert set(elements) == set(old_elements)
    changed = set()
    for side, row in mapping.items():
        selected = set(row["element_ids"])
        changed |= selected
        assert set(remaps[side]) == set(row["shared_nodes"])
        owned = {n for e in selected for n in elements[e]}
        other = {n for e, ids in elements.items() if e not in selected for n in ids}
        assert not owned & other
        for eid in selected:
            assert tuple(nodes[n] for n in elements[eid]) == tuple(old_nodes[n] for n in old_elements[eid])
    assert all(elements[e] == ids for e, ids in old_elements.items() if e not in changed)
    assert len(points) == 8 and len(cases) == 9
    for p in points.values():
        assert set(p["nodes"]).isdisjoint(p["gusset_nodes"])
        assert [nodes[n] for n in p["nodes"]] == [nodes[n] for n in p["gusset_nodes"]]


def test_coupled_archive_replays_all_bases_and_superpositions():
    with tarfile.open("fea/results/coupled-gussets.tar.gz") as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    assert report["gates"] == GATES and report["passed"]
    assert set(report["artifact_sha256"]) == set(files)-{"report.json"}
    for name, value in report["artifact_sha256"].items():
        assert hashlib.sha256(files[name]).hexdigest() == value
    for name, value in report["source_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == value
    nodes, elements, points, cases, _, remaps = prepare()
    assert json.loads(json.dumps(remaps)) == report["duplicate_nodes"]
    assert_roundoff_equal(points, report["points"],
                          paths=[(name, "weights") for name in report["points"]])
    assert cases == report["cases"]
    # Historical solver input is byte-exact; fresh reconstruction above checks
    # the floating interpolation independently without changing archived data.
    points = report["points"]
    prior = None
    for stiffness in STIFFNESSES:
        name = f"k{int(stiffness)}"
        expected, context = deck(nodes, elements, points, cases, stiffness)
        assert expected == files[name+".inp"].decode()
        assert expected.count("*EQUATION") == 48
        assert "*TIE" not in expected and "*CONTACT" not in expected
        assert all(abs(nodes[n][2]) < 1e-5 for n in context["feet"])
        log = files[name+".log"].decode()
        assert "*ERROR" not in log.upper() and "Job finished" in log
        data = files[name+".dat"].decode()
        results = audit(data, context, cases, stiffness)
        assert results == report["runs"][name]["basis"]
        assert all(row["passed"] for row in results)
        if prior is not None:
            # Increasing positive connector stiffness cannot increase collocated
            # load compliance in this unchanged linear model.
            assert all(row["load_work_nmm"] <= old["load_work_nmm"]+.01
                       for row, old in zip(results, prior, strict=True))
        prior = results
        rows = combine(results, cases, nodes)
        assert rows == report["runs"][name]["scenarios"] and len(rows) == 216
        assert {r["climber_lb"] for r in rows} == {150, 200, 250, 300}
        for row in rows:
            for side in ("left", "right"):
                forces = [v for n, v in row["connector_force_on_gusset_n"].items() if side in n]
                assert math.hypot(*(sum(f[i] for f in forces) for i in range(3))) < .1
        with pytest.raises(ValueError, match="endpoints"):
            audit(data.replace("displacements", "removed_output", 1), context, cases, stiffness)
