import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from fea.floor_contact_results import blocks
from fea.prescribed_tet_control import definition


def test_affine_control_has_exact_rigid_balance_and_strain_energy():
    deck, points, displacement, forces = definition()
    assert "*ELEMENT,TYPE=C3D10" in deck
    assert np.max(abs(forces.sum(axis=0))) < 1e-12
    assert np.max(abs(np.cross(points, forces).sum(axis=0))) < 1e-12
    assert .5*np.sum(displacement*forces) == pytest.approx(.5*7000*.001**2*(1000/6))
    assert np.max(abs(forces[:4])) == 0
    assert np.max(abs(forces[:, 1:])) == 0


def test_archived_native_control_replays_against_independent_forces():
    with tarfile.open("fea/results/prescribed-tet-control.tar.gz") as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    assert report["source_sha256"] == hashlib.sha256(Path("fea/prescribed_tet_control.py").read_bytes()).hexdigest()
    assert set(report["artifact_sha256"]) == set(files)-{"report.json"}
    assert all(hashlib.sha256(files[n]).hexdigest() == h for n, h in report["artifact_sha256"].items())
    deck, _, imposed, expected = definition()
    assert files["control.inp"].decode() == deck
    assert report["returncode"] == 0 and "*ERROR" not in files["run.log"].decode().upper()
    parsed = blocks(files["control.dat"].decode())
    forces = parsed["forces", "ALLN", 1.]
    displacement = parsed["displacements", "ALLN", 1.]
    assert set(forces) == set(displacement) == set(range(1, 11))
    assert np.max(abs(np.array([forces[i] for i in range(1, 11)])-expected)) < .001
    assert np.max(abs(np.array([displacement[i] for i in range(1, 11)])-imposed)) < 1e-9
