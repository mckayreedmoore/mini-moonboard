"""Replay nine solved bases and 216 conditional linear scenarios; no new solve."""
import gzip
import hashlib
import itertools
import json
import math

import numpy as np
import pytest

from fea import publish_timber_asymmetric as publisher
from fea import timber_asymmetric as run
from fea.floor_contact import mesh
from fea.floor_contact_results import blocks


@pytest.fixture(scope="module")
def evidence():
    report = json.loads((publisher.OUTPUT/"summary.json").read_text())
    decoded = {}
    for name, hashes in report["replay_archives"].items():
        payload = (publisher.OUTPUT/name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == hashes["gzip_sha256"]
        data = gzip.decompress(payload)
        assert hashlib.sha256(data).hexdigest() == hashes["uncompressed_sha256"]
        decoded[name.removesuffix(".gz")] = data.decode()
    return report, decoded, json.loads(publisher.JOINTS.read_text())


def test_sources_archives_and_all_nine_basis_solves_replay(evidence):
    report, decoded, joint = evidence
    accepted, original, _, sources = publisher.authenticated_inputs()
    expected = set(sources) | set(report["input"]["source_sha256"]) | set(joint["source_sha256"]) | {
        str(publisher.JOINTS), "fea/publish_timber_asymmetric.py", "uv.lock"}
    assert set(report["source_sha256"]) == expected
    assert all(run.digest(p) == sha for p, sha in report["source_sha256"].items())
    assert report["candidate"] == "timber-base-development"
    assert report["limits"] == run.LIMITS
    assert report["basis_solve_count"] == 9
    names = {"input.json"} | {h+s for h in run.HOLDS for s in
        (".inp", ".dat", ".log", ".sta", ".launch.json", ".json")}
    assert set(decoded) == names and len(names) == 19
    assert {p.name for p in publisher.OUTPUT.iterdir()} == {name+".gz" for name in names} | {"summary.json"}
    info = json.loads(decoded["input.json"])
    assert info == report["input"]
    assert info["accepted_mesh_deck_sha256"] == accepted["deck_sha256"]
    accepted_mesh = mesh(original)
    for hold in run.HOLDS:
        deck, data = decoded[hold+".inp"], decoded[hold+".dat"]
        assert mesh(deck) == accepted_mesh
        assert hashlib.sha256(deck.encode()).hexdigest() == info["deck_sha256"][hold]
        record, launch = (json.loads(decoded[hold+suffix]) for suffix in (".json", ".launch.json"))
        input_sha = hashlib.sha256(decoded["input.json"].encode()).hexdigest()
        assert record["input_sha256"] == launch["input_sha256"] == input_sha
        assert launch["source_sha256"] == info["source_sha256"]
        assert launch["deck_sha256"] == info["deck_sha256"][hold]
        for suffix in (".inp", ".dat", ".log", ".sta", ".launch.json"):
            assert hashlib.sha256(decoded[hold+suffix].encode()).hexdigest() == record["artifacts"][hold+suffix]
        assert "*ERROR" not in decoded[hold+".log"].upper()
        basis = run.audit(deck, data, info["mapping"][hold]["node"])
        assert json.loads(json.dumps(basis)) == record["basis"] == report["basis_results"][hold]["basis"]
        compliance = np.array([b["loaded_displacement_mm"] for b in basis]).T/np.array([1000., 1000., -1000.])
        saved = report["basis_results"][hold]["compliance"]
        assert np.array(saved["matrix_mm_per_n"]) == pytest.approx(compliance)
        assert compliance == pytest.approx(compliance.T, rel=1e-5, abs=1e-8)
        eigenvalues = np.linalg.eigvalsh((compliance+compliance.T)/2)
        assert min(eigenvalues) > 0
        assert saved["symmetric_eigenvalues_mm_per_n"] == pytest.approx(eigenvalues)


def test_leg_basis_and_all_scenario_free_bodies_replay(evidence):
    report, decoded, joint = evidence
    leg_bases = {}
    for hold in run.HOLDS:
        nodes, _ = mesh(decoded[hold+".inp"])
        parsed = blocks(decoded[hold+".dat"])
        leg_bases[hold] = {}
        for side, leg in joint["legs"].items():
            assert report["leg_references_world_mm"][side] == leg["reference_world_mm"]
            values = []
            for step in (1., 2., 3.):
                reactions = parsed["forces", "FEET", step]
                terms = []
                for n in leg["floor_nodes"]:
                    x, y, z = [nodes[n][i]-leg["reference_world_mm"][i] for i in range(3)]
                    fx, fy, fz = reactions[n]
                    terms.append((fx, fy, fz, y*fz-z*fy, z*fx-x*fz, x*fy-y*fx))
                values.append([math.fsum(t[i] for t in terms) for i in range(6)])
            leg_bases[hold][side] = values
            assert np.array(report["basis_results"][hold]["leg_on_board_basis_world_n_nmm"][side]) == pytest.approx(np.array(values), abs=1e-7)
    expected = set(itertools.product(run.HOLDS, (150, 200, 250, 300), (1, 2), (None, *range(0, 360, 45))))
    rows = report["cases"]
    keys = [(r["hold"], r["climber_lb"], r["weight_factor"], r["horizontal_direction_deg"]) for r in rows]
    assert report["scenario_count"] == len(rows) == len(set(keys)) == 216
    assert set(keys) == expected
    for row in rows:
        angle = row["horizontal_direction_deg"]
        fx = 0. if angle is None else 300*math.cos(math.radians(angle))
        fy = 0. if angle is None else 300*math.sin(math.radians(angle))
        fz = -row["climber_lb"]*.45359237*9.80665*row["weight_factor"]
        assert row["force_n"] == pytest.approx([fx, fy, fz])
        coefficients = [fx/1000, fy/1000, -fz/1000]
        assert row["basis_coefficients"] == pytest.approx(coefficients)
        basis = report["basis_results"][row["hold"]]["basis"]
        u = [math.fsum(c*b["loaded_displacement_mm"][i] for c, b in zip(coefficients, basis, strict=True)) for i in range(3)]
        assert row["loaded_displacement_mm"] == pytest.approx(u)
        assert row["loaded_displacement_magnitude_mm"] == pytest.approx(math.sqrt(sum(v*v for v in u)))
        x, y, z = report["input"]["mapping"][row["hold"]]["coordinates_mm"]
        external = [fx, fy, fz, y*fz-z*fy, z*fx-x*fz, x*fy-y*fx]
        reaction = [math.fsum(c*b["reaction_wrench_n_nmm"][i] for c, b in zip(coefficients, basis, strict=True)) for i in range(6)]
        assert row["reaction_wrench_n_nmm"] == pytest.approx(reaction)
        residual = [r+f for r, f in zip(reaction, external, strict=True)]
        assert row["residual_wrench"] == pytest.approx(residual, abs=1e-7)
        assert max(map(abs, residual[:3])) <= .1*sum(map(abs, coefficients))
        assert max(map(abs, residual[3:])) <= sum(map(abs, coefficients))
        for side, saved in row["legs"].items():
            world = [math.fsum(c*v[i] for c, v in zip(coefficients, leg_bases[row["hold"]][side], strict=True)) for i in range(6)]
            assert saved["leg_on_board_world_n_nmm"] == pytest.approx(world)
            assert saved["board_on_leg_world_n_nmm"] == pytest.approx([-v for v in world])
            local = [sum(world[offset+i]*axis[i] for i in range(3))
                     for offset in (0, 3) for axis in joint["local_axes_world"]]
            assert saved["leg_on_board_local_xsn_n_nmm"] == pytest.approx(local)
    assert report["local_axes_world"] == joint["local_axes_world"]
    for weight in (150, 200, 250, 300):
        maximum = max((r for r in rows if r["climber_lb"] == weight), key=lambda r: r["loaded_displacement_magnitude_mm"])
        assert report["maximum_loaded_displacement_by_weight"][str(weight)] == maximum
        assert (maximum["hold"], maximum["weight_factor"], maximum["horizontal_direction_deg"]) == ("K12", 2, 90)
