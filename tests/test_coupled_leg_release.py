import hashlib
import json
import math
import tarfile
from pathlib import Path

import pytest
from replay_roundoff import assert_roundoff_equal

from fea import coupled_gussets as base
from fea import coupled_leg_release as leg
from fea.leg_connector_map import build


def test_leg_interface_map_replays_current_cad_and_complete_faces():
    saved = json.loads(leg.MAP.read_text())
    assert_roundoff_equal(build(), saved,
                          paths=[("legs", side, "points", name, "weights")
                                 for side, row in saved["legs"].items()
                                 for name in row["points"]])
    for side, row in saved["legs"].items():
        assert len(row["shared_nodes"]) == 405
        assert len(row["interfaces"][f"base_side_{side}"]) == 148
        assert len(row["interfaces"][f"main_upper_{side}"]) == 34
        assert len(row["points"]) == 4


def test_leg_release_changes_only_interface_identity_and_preserves_floor():
    nodes, elements, points, cases, _, legs, remaps = leg.prepare()
    before_nodes, before_elements, _, before_cases, _, _ = base.prepare()
    assert cases == before_cases and len(points) == 16
    assert len(nodes)-len(before_nodes) == sum(map(len, remaps.values())) == 810
    assert {n for n, p in nodes.items() if abs(p[2]) < 1e-5} == {n for n, p in before_nodes.items() if abs(p[2]) < 1e-5}
    changed = set()
    for side, body in legs.items():
        selected = set(body["element_ids"])
        changed |= selected
        owned = {n for e in selected for n in elements[e]}
        other = {n for e, ids in elements.items() if e not in selected for n in ids}
        assert not owned & other
        assert set(body["floor_nodes"]) <= owned
        assert set(remaps[side]) == set(body["shared_nodes"])
        for eid in selected:
            assert [nodes[n] for n in elements[eid]] == [before_nodes[n] for n in before_elements[eid]]
    assert all(elements[e] == ids for e, ids in before_elements.items() if e not in changed)


def test_native_leg_release_archive_replay():
    with tarfile.open(leg.OUTPUT) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    assert report["gates"] == leg.GATES and report["inherited_gates"] == base.GATES
    for name, sha in report["source_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
    assert set(report["artifact_sha256"]) == set(files)-{"report.json"}
    for name, sha in report["artifact_sha256"].items():
        assert hashlib.sha256(files[name]).hexdigest() == sha
    nodes, elements, points, cases, _, legs, remaps = leg.prepare()
    assert json.loads(json.dumps(remaps)) == report["leg_duplicate_nodes"]
    # The leg report inherits the gusset preparation but does not duplicate its
    # point map. Obtain the historical weights from that retained source report;
    # the exact leg deck comparison below authenticates every emitted coefficient.
    with tarfile.open("fea/results/coupled-gussets.tar.gz") as archive:
        gussets = json.loads(archive.extractfile("report.json").read())
    for source, digest in gussets["source_sha256"].items():
        assert report["source_sha256"][source] == digest
    fresh = {name: points[name] for name in gussets["points"]}
    assert_roundoff_equal(fresh, gussets["points"],
                          paths=[(name, "weights") for name in gussets["points"]])
    points = {**points, **gussets["points"]}
    previous = None
    for k in base.STIFFNESSES:
        name = f"k{int(k)}"
        text, context = base.deck(nodes, elements, points, cases, k)
        assert text.replace("** "+base.LIMITS, "** "+leg.LIMITS, 1) == files[name+".inp"].decode()
        assert text.count("*EQUATION") == 96 and text.count("*ELEMENT,TYPE=SPRING2") == 48
        log = files[name+".log"].decode()
        assert "*ERROR" not in log.upper() and "Job finished" in log
        data = files[name+".dat"].decode()
        rows = leg.audit(data, context, cases, k, legs)
        assert rows == report["runs"][name]["basis"]
        assert len(rows) == 9 and all(r["passed"] for r in rows)
        if previous is not None:
            assert all(r["load_work_nmm"] <= old["load_work_nmm"]+.01 for r, old in zip(rows, previous, strict=True))
        previous = rows
        combined = leg.combine(rows, cases, nodes)
        assert combined == report["runs"][name]["scenarios"] and len(combined) == 216
        assert all(len(r["leg_connector_force_on_leg_n"]) == 8 for r in combined)
        assert all(math.isfinite(v) for r in combined for f in r["leg_connector_force_on_leg_n"].values() for v in f)
        with pytest.raises(ValueError, match="endpoints"):
            leg.audit(data.replace("displacements", "removed_output", 1), context, cases, k, legs)
    assert report["passed"]
