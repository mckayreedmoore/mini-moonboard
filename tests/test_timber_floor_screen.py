"""Finite floor-screen scenarios and independent free-body arithmetic."""
import gzip
import itertools
import json
import math
from collections import Counter
from pathlib import Path

import pytest

from fea import timber_floor_screen as screen

STATE = {"mass_kg": 100., "centre_xyz_mm": [10., 20., 30.]}


def points():
    return [(label, [100., 200., 300.], [0., 1., 0.]) for label in screen.HOLDS]


def test_complete_finite_scenario_inventory():
    rows = list(screen.cases(STATE, points()))
    expected = set(itertools.product((150, 200, 250, 300), (1, 2), (.8, 1.),
                                    screen.HOLDS, (None, *range(0, 360, 45))))
    actual = [(r["climber_lb"], r["weight_factor"], r["mass_fraction"],
               r["hold"], r["horizontal_direction_deg"]) for r in rows]
    assert len(rows) == len(set(actual)) == 1296
    assert set(actual) == expected
    assert screen.HOLDS == ("A1", "F1", "K1", "A6", "F6", "K6", "A12", "F12", "K12")


def test_wrenches_include_whole_climber_and_gravity_at_distinct_points():
    for row in screen.cases(STATE, points()):
        downward = row["climber_lb"]*.45359237*9.80665*row["weight_factor"]
        dead = 100.*row["mass_fraction"]*9.80665
        angle = row["horizontal_direction_deg"]
        fx = 0. if angle is None else 300.*math.cos(math.radians(angle))
        fy = 0. if angle is None else 300.*math.sin(math.radians(angle))
        # Hold after standoff=(100,300,300); CG=(10,20,30).
        # Expanded r×F arithmetic is independent of NumPy cross in production.
        expected = [fx, fy, -downward-dead,
                    -300.*downward-300.*fy-20.*dead,
                    300.*fx+100.*downward+10.*dead,
                    100.*fy-300.*fx]
        assert row["wrench_n_nmm"] == pytest.approx(expected, abs=1e-7)


def test_missing_selected_hold_is_rejected():
    with pytest.raises(KeyError, match="K12"):
        list(screen.cases(STATE, points()[:-1]))


def test_current_hold_mapping_uses_corrected_panel_edge_datums():
    from mini_moonboard import box_frame as b

    selected = {label: (position, normal) for label, position, normal in screen.locations()
                if label in screen.HOLDS}
    assert set(selected) == set(screen.HOLDS)
    for column, x in (("A", 200.), ("F", 1200.), ("K", 2200.)):
        for row, station in ((1, 99.2), (6, 1099.2), (12, 2319.2)):
            position, normal = selected[f"{column}{row}"]
            assert position == pytest.approx(b.point(x-b.HALF, station, -18.25625).toTuple())
            assert normal == pytest.approx((-b.normal()).toTuple())


def test_existing_publication_is_untouched(tmp_path, monkeypatch):
    output = tmp_path/"previous.json.gz"
    output.write_bytes(b"previous evidence")
    monkeypatch.setattr(screen, "OUTPUT", output)
    monkeypatch.setattr(screen, "locations", lambda: pytest.fail("Should stop before geometry"))
    with pytest.raises(FileExistsError, match="overwrite"):
        screen.run()
    assert output.read_bytes() == b"previous evidence"


@pytest.mark.parametrize("mutation", ["candidate", "closure"])
def test_invalid_source_identity_is_rejected_before_solving(tmp_path, monkeypatch, mutation):
    source, output = tmp_path/"source.json", tmp_path/"output.json.gz"
    record = {"candidate": "timber-base-development", "source_sha256": {"unused": "unused"}}
    if mutation == "candidate":
        record["candidate"] = "historical-other-frame"
    else:
        record["source_sha256"] = {}
    source.write_text(json.dumps(record))
    monkeypatch.setattr(screen, "SOURCE", source)
    monkeypatch.setattr(screen, "OUTPUT", output)
    monkeypatch.setattr(screen, "solve", lambda *_: pytest.fail("Invalid source must not reach solver"))
    with pytest.raises(ValueError, match="nonempty source closure"):
        screen.run()
    assert not output.exists()


@pytest.fixture(scope="module")
def evidence():
    return json.loads(gzip.decompress(screen.OUTPUT.read_bytes())), json.loads(screen.SOURCE.read_text())


def test_published_source_inventory_and_input_wrenches(evidence):
    report, source = evidence
    assert report["candidate"] == source["candidate"] == "timber-base-development"
    expected = set(source["source_sha256"]) | {
        str(screen.SOURCE), "fea/timber_floor_screen.py", "fea/rigid_floor_screen.py", "uv.lock"}
    assert set(report["source_sha256"]) == expected
    assert all(report["source_sha256"][p] == sha for p, sha in source["source_sha256"].items())
    assert all(screen.digest(Path(p)) == sha for p, sha in report["source_sha256"].items())
    assert report["floor_vertices_mm"] == [[x, y, 0.] for x, y in source["state"]["support_polygon_mm"]]
    replay = list(screen.cases(source["state"], screen.locations()))
    assert len(report["cases"]) == len(replay) == 1296
    indexed = {label: (p, n) for label, p, n in screen.locations()}
    cg = source["state"]["centre_xyz_mm"]
    for saved, current in zip(report["cases"], replay, strict=True):
        assert {k: saved[k] for k in current} == current
        p, n = indexed[saved["hold"]]
        x, y, z = [v+100.*normal for v, normal in zip(p, n, strict=True)]
        dead = source["state"]["mass_kg"]*saved["mass_fraction"]*9.80665
        live = saved["climber_lb"]*.45359237*9.80665*saved["weight_factor"]
        angle = saved["horizontal_direction_deg"]
        fx = 0. if angle is None else 300.*math.cos(math.radians(angle))
        fy = 0. if angle is None else 300.*math.sin(math.radians(angle))
        assert saved["wrench_n_nmm"] == pytest.approx([
            fx, fy, -dead-live, -y*live-z*fy-cg[1]*dead,
            z*fx+x*live+cg[0]*dead, x*fy-y*fx], abs=1e-7)
        assert set(saved["friction_results"]) == {"0.1", "0.2", "0.4"}
    for mu in ("0.1", "0.2", "0.4"):
        assert report["summary"][mu] == dict(Counter(c["friction_results"][mu]["status"] for c in report["cases"]))
    assert "not all azimuths" in report["assumptions"]
    assert "does not prove circular" in report["assumptions"]


def test_all_published_feasible_witnesses_balance_and_respect_friction(evidence):
    report, _ = evidence
    floor = report["floor_vertices_mm"]
    checked = 0
    for case in report["cases"]:
        wrench = case["wrench_n_nmm"]
        ftol = 1e-7*max(1., *(abs(v) for v in wrench[:3]))
        mtol = 1e-7*max(1000., *(abs(v) for v in wrench[3:]),
            max(abs(v) for p in floor for v in p)*max(1., *(abs(v) for v in wrench[:3])))
        for mu_text, result in case["friction_results"].items():
            if result["status"] == "infeasible":
                assert result["polygon_feasible"] is False
                assert result["circular_cone_infeasibility_proven"] is False
                assert "point_forces_n" not in result
                continue
            assert result["status"] == "feasible" and result["polygon_feasible"] is True
            forces = result["point_forces_n"]
            assert len(forces) == len(floor)
            assert all(len(f) == 3 and all(map(math.isfinite, f)) for f in forces)
            mu = float(mu_text)
            for fx, fy, fz in forces:
                assert fz >= -ftol
                assert math.hypot(fx, fy) <= mu*fz+ftol
                # Independent half-plane check of the actual 16-ray polygon.
                for side in range(16):
                    angle = (side+.5)*2*math.pi/16
                    assert fx*math.cos(angle)+fy*math.sin(angle) <= mu*fz*math.cos(math.pi/16)+ftol
            residual = [sum(f[i] for f in forces)+wrench[i] for i in range(3)]
            moments = [(y*fz, -x*fz, x*fy-y*fx)
                       for (x, y, _), (fx, fy, fz) in zip(floor, forces, strict=True)]
            residual += [sum(m[i] for m in moments)+wrench[3+i] for i in range(3)]
            assert max(map(abs, residual[:3])) <= ftol
            assert max(map(abs, residual[3:])) <= mtol
            assert result["residual_wrench"] == pytest.approx(residual, abs=1e-7)
            checked += 1
    assert checked > 1296


def test_low_friction_failures_and_selected_solver_replay(evidence):
    report, _ = evidence
    failures = [c for c in report["cases"]
                if math.hypot(*c["wrench_n_nmm"][:2]) > .1*(-c["wrench_n_nmm"][2])+1e-7]
    assert len(failures) == 576
    assert all(c["friction_results"]["0.1"]["status"] == "infeasible" for c in failures)
    for mu in (.1, .2, .4):
        statuses = {c["friction_results"][str(mu)]["status"] for c in report["cases"]}
        for status in statuses:
            case = next(c for c in report["cases"] if c["friction_results"][str(mu)]["status"] == status)
            # Nonunique reaction witnesses need not reproduce componentwise.
            assert screen.solve(report["floor_vertices_mm"], case["wrench_n_nmm"], mu)["status"] == status
