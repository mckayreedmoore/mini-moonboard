"""Authenticate current-wide floor cases and independently check every witness."""
import gzip
import json
import math
from collections import Counter

import pytest

from fea import wide_floor_screen as screen


def test_current_wide_floor_evidence():
    report = json.loads(gzip.decompress(screen.OUTPUT.read_bytes()))
    source = json.loads(screen.SOURCE.read_text())
    assert report["candidate"] == source["candidate"] == "wide-principal-development"
    assert all(screen.digest(p) == sha for p, sha in report["source_sha256"].items())
    assert source["source_sha256"].items() <= report["source_sha256"].items()
    assert str(screen.SOURCE) in report["source_sha256"]
    floor = [[x, y, 0.] for x, y in source["state"]["support_polygon_mm"]]
    assert report["floor_vertices_mm"] == floor
    replay = list(screen.cases(source["state"], screen.locations()))
    assert len(replay) == len(report["cases"]) == 1296
    for saved, expected in zip(report["cases"], replay, strict=True):
        assert {k: saved[k] for k in expected} == expected
        wrench = saved["wrench_n_nmm"]
        ftol = 1e-7*max(1., *map(abs, wrench[:3]))
        mtol = 1e-7*max(1000., *map(abs, wrench[3:]),
                       max(abs(v) for p in floor for v in p)*max(1., *map(abs, wrench[:3])))
        assert set(saved["friction_results"]) == {str(mu) for mu in screen.MUS}
        for mu, result in saved["friction_results"].items():
            if result["status"] == "infeasible":
                assert result["circular_cone_infeasibility_proven"] is False
                assert "point_forces_n" not in result
                continue
            assert result["status"] == "feasible"
            forces = result["point_forces_n"]
            assert len(forces) == len(floor)
            for fx, fy, fz in forces:
                assert all(map(math.isfinite, (fx, fy, fz)))
                assert fz >= -ftol
                assert math.hypot(fx, fy) <= float(mu)*fz+ftol
            residual = [sum(f[i] for f in forces)+wrench[i] for i in range(3)]
            moments = [(y*fz, -x*fz, x*fy-y*fx)
                       for (x, y, _), (fx, fy, fz) in zip(floor, forces, strict=True)]
            residual += [sum(m[i] for m in moments)+wrench[3+i] for i in range(3)]
            assert max(map(abs, residual[:3])) <= ftol
            assert max(map(abs, residual[3:])) <= mtol
    for mu in screen.MUS:
        assert report["summary"][str(mu)] == dict(Counter(
            c["friction_results"][str(mu)]["status"] for c in report["cases"]))
        for status in report["summary"][str(mu)]:
            case = next(c for c in report["cases"] if c["friction_results"][str(mu)]["status"] == status)
            assert screen.solve(floor, case["wrench_n_nmm"], mu)["status"] == status


def test_refuses_to_replace_existing_evidence(tmp_path, monkeypatch):
    output = tmp_path/"existing.gz"
    output.write_bytes(b"preserve")
    monkeypatch.setattr(screen, "OUTPUT", output)
    with pytest.raises(FileExistsError):
        screen.run()
    assert output.read_bytes() == b"preserve"
