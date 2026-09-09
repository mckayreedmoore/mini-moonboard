"""Replay saved actual-CAD states and independent equilibrium witnesses."""
import gzip
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from fea.prepare_easy_structural import digest
from fea.timber_floor_screen import cases
from fea.wide_structural import locations, mass_state
from mini_moonboard import lumber_leg_frame as candidate
from mini_moonboard import wide_frame as parent

OPTIONS = [("plywood", 0.)]+[(size, extension) for size in candidate.WIDTHS for extension in candidate.EXTENSIONS]


@pytest.mark.parametrize("size,extension", OPTIONS)
def test_low_friction_case_exceeds_even_circular_global_force_bound(size, extension):
    report = json.loads(gzip.decompress((Path("fea/results/lumber-leg-floor")/
        f"{size}-e{extension:g}.json.gz").read_bytes()))
    row = next(r for r in report["cases"] if r["climber_lb"] == 150
        and r["weight_factor"] == 1 and r["mass_fraction"] == .8
        and r["hold"] == "A12" and r["horizontal_direction_deg"] == 0)
    force = row["wrench_n_nmm"][:3]
    # Triangle inequality: |sum(horizontal reactions)| <= mu*sum(normal).
    # This independent necessary condition does not assume the 16-ray cone.
    required_mu = np.linalg.norm(force[:2])/-force[2]
    assert .1 < required_mu < .2
    assert row["friction_results"]["0.1"]["status"] == "infeasible"


@pytest.mark.parametrize("size,extension", OPTIONS)
def test_floor_report_source_geometry_loads_and_witnesses(size, extension):
    path = Path("fea/results/lumber-leg-floor")/f"{size}-e{extension:g}.json.gz"
    report = json.loads(gzip.decompress(path.read_bytes()))
    assert report["qualified_for_design"] is False
    assert (report["stock"], report["extra_foot_extension_mm"]) == (size, extension)
    assert "fea/user_load_envelope.py" in report["source_sha256"]
    assert all(digest(p) == sha for p, sha in report["source_sha256"].items())
    parts = parent.parts(True) if size == "plywood" else candidate.parts(size, extension, True)
    state = mass_state(parts)
    for key in state:
        assert np.asarray(report["state"][key]) == pytest.approx(np.asarray(state[key]))
    expected = list(cases(state, locations()))
    assert len(report["cases"]) == len(expected) == 1296
    floor = np.array([[x, y, 0.] for x, y in state["support_polygon_mm"]])
    for row, case in zip(report["cases"], expected, strict=True):
        assert {key: row[key] for key in case} == case
        assert set(row["friction_results"]) == {"0.1", "0.2", "0.4"}
        for mu, value in row["friction_results"].items():
            assert value["status"] in ("feasible", "infeasible")
            if value["status"] == "infeasible":
                assert value["polygon_feasible"] is False
                assert value["circular_cone_infeasibility_proven"] is False
                continue
            forces = np.asarray(value["point_forces_n"])
            assert forces.shape == floor.shape and np.isfinite(forces).all()
            assert forces[:, 2].min() >= -1e-6
            assert (np.linalg.norm(forces[:, :2], axis=1)-float(mu)*forces[:, 2]).max() < 1e-6
            residual = np.r_[forces.sum(axis=0), np.cross(floor, forces).sum(axis=0)]+case["wrench_n_nmm"]
            assert np.abs(residual[:3]).max() < .001
            assert np.abs(residual[3:]).max() < 1.
    for mu in ("0.1", "0.2", "0.4"):
        assert dict(Counter(r["friction_results"][mu]["status"] for r in report["cases"])) == report["summary"][mu]
