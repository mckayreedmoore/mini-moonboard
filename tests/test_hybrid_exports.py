import csv
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard.hybrid_exports import candidate


@pytest.mark.parametrize("folder,count",[("hybrid-full",10),("shallow-frame",5)])
def test_full_candidate_artifacts_match_recorded_sources_and_hashes(folder,count):
    directory=Path("exports")/folder
    manifest=json.loads((directory/"manifest.json").read_text())
    assert len(manifest["artifacts"])==count
    assert set(manifest["artifacts"])=={p.name for p in directory.iterdir() if p.name!="manifest.json"}
    for filename,digest in manifest["sources"].items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==digest,filename
    for filename,digest in manifest["artifacts"].items():
        assert hashlib.sha256((directory/filename).read_bytes()).hexdigest()==digest,filename


@pytest.mark.parametrize("size",["2x10","2x12","2x8-shallow"])
def test_full_candidate_schedules_and_step(size):
    directory=Path("exports")/("shallow-frame" if size=="2x8-shallow" else "hybrid-full")
    with (directory/f"{size}_parts.csv").open() as stream:
        rows=list(csv.DictReader(stream))
    parts,connections=candidate(size)
    assert {r["part"] for r in rows}=={p.name for p in parts}
    for row,p in zip(rows,parts,strict=True):
        assert int(row["layers"])==p.laminations
        assert [float(row[f"dimension_{i}_mm"]) for i in (1,2,3)]==pytest.approx(p.blank,abs=.00051)
    with (directory/f"{size}_connections.csv").open() as stream:
        rows=list(csv.DictReader(stream))
    assert {r["connection"] for r in rows}=={c.name for c in connections}
    expected=[p.shape for p in parts]
    expected.extend(shape for c in connections for shape in c.components())
    shape=cq.importers.importStep(str(directory/f"{size}.step")).val()
    assert len(shape.Solids())==sum(len(s.Solids()) for s in expected)
    assert shape.Volume()==pytest.approx(sum(s.Volume() for s in expected),rel=1e-8)
    def fingerprints(solids):
        rows=[]
        for solid in solids:
            bounds=solid.BoundingBox()
            rows.append((*solid.centerOfMass(solid).toTuple(), solid.Volume(),
                         *[getattr(bounds,axis+end) for axis in "xyz" for end in ("min","max")]))
        return rows
    actual=fingerprints(shape.Solids())
    intended=fingerprints([solid for item in expected for solid in item.Solids()])
    # STEP roundoff can reorder nominally equal-volume hardware. Match spatial
    # fingerprints within tolerance rather than sorting rounded volumes.
    for expected_row in intended:
        match=next((i for i,row in enumerate(actual) if all(
            math.isclose(a,b,rel_tol=1e-8,abs_tol=.001)
            for a,b in zip(row,expected_row,strict=True))),None)
        assert match is not None,expected_row
        actual.pop(match)
    assert not actual
