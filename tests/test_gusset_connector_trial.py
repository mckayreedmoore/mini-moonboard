import copy
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from fea.gusset_connector_trial import (
    GATES,
    STIFFNESSES,
    audit,
    deck,
    point_weights,
    prepare,
)


def test_quadratic_point_interpolation_reproduces_affine_and_quadratic_fields():
    xyz = [(0., 0., 0.), (0., 2., 0.), (0., 0., 2.),
           (0., 1., 0.), (0., 1., 1.), (0., 0., 1.)]
    nodes = dict(enumerate(xyz, 1))
    face = {"element": 1, "face": 1, "nodes": list(nodes)}
    p = point_weights(nodes, [face], (.4, .7))
    w = np.array(p["weights"])
    assert sum(w) == pytest.approx(1.)
    assert w@np.array(xyz) == pytest.approx([0., .4, .7])
    assert sum(v*(y*y+2*y*z+3*z*z) for v, (_, y, z) in zip(w, xyz, strict=True)) == pytest.approx(.4**2+2*.4*.7+3*.7**2)
    # Interpolated point forces preserve resultant and first moment, even with negative corner weights.
    force = np.array([13., -7., 11.])
    nodal = w[:, None]*force
    assert nodal.sum(axis=0) == pytest.approx(force)
    assert np.cross(xyz, nodal).sum(axis=0) == pytest.approx(np.cross(p["point_mm"], force))
    with pytest.raises(ValueError, match="outside"):
        point_weights(nodes, [face], (3., 3.))


def test_native_connector_trial_archive_replays_and_rejects_imbalanced_forces():
    with tarfile.open("fea/results/gusset-connector-trial.tar.gz") as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    assert report["gates"] == GATES and report["passed"]
    assert set(report["artifact_sha256"]) == set(files)-{"report.json"}
    for name, value in report["artifact_sha256"].items():
        assert hashlib.sha256(files[name]).hexdigest() == value
    for name, value in report["source_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == value
    nodes, elements, points, fields, _ = prepare()
    assert points == report["points"] and fields == report["fields"]
    assert len(points) == 8 and len(fields) == 15
    for stiffness in STIFFNESSES:
        name = f"k{int(stiffness)}"
        expected, all_nodes, connections = deck(nodes, elements, points, fields, stiffness)
        assert files[name+".inp"].decode() == expected
        assert expected.count("*EQUATION") == 24 and expected.count("*CLOAD,OP=NEW") == 15
        assert "*TIE" not in expected and "*CONTACT" not in expected
        log = files[name+".log"].decode()
        assert "*ERROR" not in log.upper() and "Job finished" in log
        data = files[name+".dat"].decode()
        result = audit(data, all_nodes, connections, fields, stiffness)
        assert result == report["runs"][name] and all(row["passed"] for row in result)
        # Perturb the physical eigen-displacement at one connector without
        # changing the solve: both rigid-motion and equilibrium gates must fail.
        changed = copy.deepcopy(fields)
        changed[9]["anchor_u_mm"]["timber_base_left_1"][0] += .1
        assert not audit(data, all_nodes, connections, changed, stiffness)[9]["passed"]


def test_failed_prescribed_anchor_attempt_is_preserved_not_qualified():
    with tarfile.open("fea/results/gusset-connector-trial-rejected.tar.gz") as archive:
        source = archive.extractfile("generator.py").read()
        old = archive.extractfile("initial-evidence.tar.gz").read()
    with tarfile.open(fileobj=io.BytesIO(old)) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    assert hashlib.sha256(source).hexdigest() == report["source_sha256"]["fea/gusset_connector_trial.py"]
    assert not report["passed"]
    assert all(not row["passed"] for rows in report["runs"].values() for row in rows)
    for name, value in report["artifact_sha256"].items():
        assert hashlib.sha256(files[name]).hexdigest() == value
