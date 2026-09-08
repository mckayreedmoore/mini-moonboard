"""Actual accepted-mesh contact-surface proof; no CAD or solver execution."""
import gzip
import json

import pytest

from fea import timber_contact_faces as faces
from fea import timber_release as run
from fea.floor_contact import FACES, mesh


@pytest.fixture(scope="module")
def actual():
    accepted, deck, _, _ = run.authenticated_inputs()
    nodes, elements = mesh(deck)
    joint = json.loads(run.REPORT.read_text())
    run.basis_run.unchanged(joint["source_sha256"])
    legs = {s: run.recover(nodes, elements, row) for s, row in joint["legs"].items()}
    from pathlib import Path

    info = json.loads(gzip.decompress(Path("fea/results/timber-release/input.json.gz").read_bytes()))
    assert info["accepted_mesh_deck_sha256"] == accepted["deck_sha256"]
    from mini_moonboard import box_frame as b

    return (nodes, elements, legs, info["node_map"], {"left": -b.HALF, "right": b.HALF},
            b.point(0, 0, 0).toTuple(), b.normal().toTuple())


def test_actual_34_pairs_each_side_cover_all_release_nodes_and_keep_common_edge(actual):
    result = faces.reconstruct(*actual)
    _nodes, elements, legs, mapping, *_ = actual
    for side, sign in (("left", -1), ("right", 1)):
        row = result[side]
        assert len(row["pairs"]) == 34
        assert len(row["released_old_nodes"]) == 72
        assert len(row["retained_common_edge_nodes"]) == 29
        assert row["area_mm2"] == pytest.approx(9218.14883125195, abs=1e-7)
        remap = {int(k): v for k, v in mapping[side].items()}
        reverse = {v: k for k, v in remap.items()}
        covered = set()
        for pair in row["pairs"]:
            for role in ("panel", "leg"):
                item = pair[role]
                assert (item["element"] in legs[side]) == (role == "leg")
                original = [elements[item["element"]][i] for i in FACES[int(item["face"][1:])-1]]
                expected = [remap.get(n, n) if role == "leg" else n for n in original]
                assert item["nodes"] == expected
                assert item["outward_normal"] == pytest.approx((sign if role == "panel" else -sign, 0., 0.))
            assert set(pair["panel"]["nodes"]) == {reverse.get(n, n) for n in pair["leg"]["nodes"]}
            covered.update(set(pair["panel"]["nodes"]) & remap.keys())
        assert covered == set(row["released_old_nodes"]) == remap.keys()
        assert not covered & set(row["retained_common_edge_nodes"])


def test_incomplete_or_changed_actual_node_map_rejects(actual):
    mapping = {s: dict(v) for s, v in actual[3].items()}
    mapping["left"].pop(next(iter(mapping["left"])))
    with pytest.raises(ValueError, match="complete proven release"):
        faces.reconstruct(*actual[:3], mapping, *actual[4:])
