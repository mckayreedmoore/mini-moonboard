import csv
import hashlib
import json
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import hybrid_frame as h


def test_full_candidate_artifacts_match_recorded_sources_and_hashes():
    directory=Path("exports/hybrid-full")
    manifest=json.loads((directory/"manifest.json").read_text())
    assert len(manifest["artifacts"])==10
    assert set(manifest["artifacts"])=={p.name for p in directory.iterdir() if p.name!="manifest.json"}
    for filename,digest in manifest["sources"].items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==digest,filename
    for filename,digest in manifest["artifacts"].items():
        assert hashlib.sha256((directory/filename).read_bytes()).hexdigest()==digest,filename


@pytest.mark.parametrize("size",["2x10","2x12"])
def test_full_candidate_schedules_and_step(size):
    directory=Path("exports/hybrid-full")
    with (directory/f"{size}_parts.csv").open() as stream:
        rows=list(csv.DictReader(stream))
    parts=h.parts(size)
    assert {r["part"] for r in rows}=={p.name for p in parts}
    for row,p in zip(rows,parts,strict=True):
        assert int(row["layers"])==p.laminations
        assert [float(row[f"dimension_{i}_mm"]) for i in (1,2,3)]==pytest.approx(p.blank,abs=.00051)
    with (directory/f"{size}_connections.csv").open() as stream:
        rows=list(csv.DictReader(stream))
    assert {r["connection"] for r in rows}=={c.name for c in h.connections(size)}
    expected=[p.shape for p in parts]
    expected.extend(shape for c in h.connections(size) for shape in c.components())
    shape=cq.importers.importStep(str(directory/f"{size}.step")).val()
    assert len(shape.Solids())==sum(len(s.Solids()) for s in expected)
    assert shape.Volume()==pytest.approx(sum(s.Volume() for s in expected),rel=1e-8)
