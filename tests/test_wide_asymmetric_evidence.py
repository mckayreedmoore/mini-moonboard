"""Replay real wide-candidate outputs, including independent scalar free bodies."""
import gzip
import json
import math
from pathlib import Path

import pytest

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks
from fea.publish_wide_asymmetric import normalized, replay, sha


@pytest.fixture(scope="module")
def evidence():
    directory = Path("fea/results/wide-asymmetric")
    report = json.loads((directory/"summary.json").read_text())
    payload = {}
    for name, hashes in report["replay_archives"].items():
        raw = (directory/name).read_bytes()
        assert sha(raw) == hashes["gzip_sha256"]
        decoded = gzip.decompress(raw)
        assert sha(decoded) == hashes["uncompressed_sha256"]
        payload[name.removesuffix(".gz")] = decoded
    return report, payload


def test_real_wide_evidence_reconstructs_geometry_and_every_case(evidence):
    report, payload = evidence
    assert normalized(replay(payload)) == {k: v for k, v in report.items() if k != "replay_archives"}
    assert report["candidate"] == "wide-principal-development"
    assert report["basis_solve_count"] == 9 and report["scenario_count"] == 216
    assert len(report["ownership"]["base"]["members"]) == 11
    assert len([n for n in report["ownership"]["base"]["members"] if n.startswith("base_post_")]) == 6


def test_all_216_aggregate_actions_from_scalar_nodal_force_moments(evidence):
    report, payload = evidence
    seen = set()
    groups = {**report["ownership"]["legs"], "base": report["ownership"]["base"]}
    for hold in ("A12", "K12", "F6"):
        nodes, _ = mesh(payload[hold+".inp"].decode())
        data = blocks(payload[hold+".dat"].decode())
        for case in (c for c in report["cases"] if c["hold"] == hold):
            key = (hold, case["climber_lb"], case["weight_factor"], case["horizontal_direction_deg"])
            assert key not in seen
            seen.add(key)
            for name, group in groups.items():
                force, moment = [0., 0., 0.], [0., 0., 0.]
                for n in group["floor_nodes"]:
                    x, y, z = [a-b for a, b in zip(nodes[n], group["reference_world_mm"], strict=True)]
                    fx, fy, fz = [math.fsum(case["basis_coefficients"][j]*data["forces", "FEET", float(j+1)][n][i]
                                           for j in range(3)) for i in range(3)]
                    for i, value in enumerate((fx, fy, fz)):
                        force[i] += value
                    for i, value in enumerate((y*fz-z*fy, z*fx-x*fz, x*fy-y*fx)):
                        moment[i] += value
                assert case["aggregates"][name]["on_board_world_n_nmm"] == pytest.approx(force+moment, abs=1e-6)
    assert seen == {(h, w, f, a) for h in ("A12", "K12", "F6") for w in (150, 200, 250, 300)
                    for f in (1, 2) for a in (None, 0, 45, 90, 135, 180, 225, 270, 315)}
