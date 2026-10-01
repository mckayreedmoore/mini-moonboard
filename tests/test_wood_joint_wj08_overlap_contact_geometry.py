"""The T04 geometry adapter preserves every unresolved mechanics boundary."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from scripts.wood_joint_wj08_overlap_contact_geometry import (
    GRAPH_REL,
    PINNED_INPUTS,
    PRODUCER_REL,
    ROOT,
    TEST_REL,
    _load_and_check_pinned_inputs,
    build_geometry_evidence,
)


def _graph():
    return json.loads((ROOT / GRAPH_REL).read_text(encoding="utf-8"))


def _build(graph=None):
    graph = graph if graph is not None else _graph()
    return build_geometry_evidence(graph, {"fixture": "sha256-test-only"})


def _copy_pinned_inputs(destination: Path) -> None:
    paths = [*PINNED_INPUTS, PRODUCER_REL, TEST_REL]
    for rel in paths:
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)


def test_geometry_evidence_reconciles_full_member_pair_snapshot_without_closing_criterion():
    evidence = _build()

    assert evidence["criterion_id"] == "overlap_contact"
    assert evidence["criterion_disposition"] == "pending"
    assert evidence["evidence_status"] == "partial_geometry_inventory_only"
    assert evidence["counts"] == {
        "physical_member_nodes": 50,
        "unordered_member_pairs": 1225,
        "exact_brep_evaluated_pairs": 147,
        "aabb_separated_not_exactly_evaluated_pairs": 1078,
        "geometry_classifications": {
            "aabb_separated_not_exactly_evaluated": 1078,
            "exact_brep_separated_geometry": 26,
            "finite_opposed_planar_geometry": 115,
            "zero_area_or_unresolved_geometry": 6,
        },
    }
    assert len({pair["pair_id"] for pair in evidence["pairs"]}) == 1225
    assert evidence["mechanics"]["active_contact_established"] is False
    assert evidence["mechanics"]["criterion_acceptance"] is False


def test_aabb_only_pairs_cannot_be_promoted_to_exact_separation_or_contact():
    evidence = _build()
    aabb_only = [
        pair
        for pair in evidence["pairs"]
        if pair["geometry_classification"] == "aabb_separated_not_exactly_evaluated"
    ]

    assert len(aabb_only) == 1078
    assert all(pair["exact_brep_evaluated"] is False for pair in aabb_only)
    assert all(
        pair["measurements"]["minimum_separation_mm"] is None for pair in aabb_only
    )
    assert all(
        pair["active_contact_state"] == "not_established_by_geometry_evidence"
        for pair in aabb_only
    )


def test_finite_geometric_touch_does_not_become_active_contact_or_load_path():
    evidence = _build()
    finite = next(
        pair
        for pair in evidence["pairs"]
        if pair["geometry_classification"] == "finite_opposed_planar_geometry"
    )

    assert finite["measurements"]["opposed_planar_face_contact_area_mm2"] > 0
    assert finite["face_owner_ids"] is None
    assert finite["active_contact_state"] == "not_established_by_geometry_evidence"
    assert finite["contact_law"] is None
    assert finite["load_path_owner_ids"] is None
    assert finite["mechanical_disposition"] == "unresolved"


def test_zero_area_unresolved_pair_stays_unresolved_even_at_zero_gap():
    evidence = _build()
    unresolved = [
        pair
        for pair in evidence["pairs"]
        if pair["geometry_classification"] == "zero_area_or_unresolved_geometry"
    ]

    assert len(unresolved) == 6
    assert all(
        pair["measurements"]["opposed_planar_face_contact_area_mm2"] == 0
        for pair in unresolved
    )
    assert all(
        pair["geometry_classification"] == "zero_area_or_unresolved_geometry"
        for pair in unresolved
    )
    assert all(pair["mechanical_disposition"] == "unresolved" for pair in unresolved)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda graph: graph["edges"].pop(),
        lambda graph: graph["edges"].append(copy.deepcopy(graph["edges"][0])),
        lambda graph: graph["edges"][0].update(
            geometry_state="finite_opposed_planar_touch",
            interface_geometry_state="finite_planar_face_contact",
            broadphase_candidate=False,
        ),
        lambda graph: graph["edges"][0].update(
            geometry_state="finite_opposed_planar_touch",
            interface_geometry_state="finite_planar_face_contact",
            broadphase_candidate=True,
            opposed_planar_face_contact_area_mm2=float("nan"),
        ),
    ],
    ids=["missing-pair", "duplicate-pair", "contradictory-exactness", "nonfinite-area"],
)
def test_malformed_or_incomplete_upstream_graph_fails_closed(mutate):
    graph = _graph()
    mutate(graph)

    with pytest.raises(ValueError):
        _build(graph)


def test_unknown_geometry_classification_fails_closed():
    graph = _graph()
    graph["edges"][0]["geometry_state"] = "touch_assumed_to_bear"

    with pytest.raises(ValueError, match="Unrecognized or contradictory"):
        _build(graph)


def test_source_hash_drift_is_rejected(tmp_path):
    _copy_pinned_inputs(tmp_path)
    hashes = _load_and_check_pinned_inputs(tmp_path)
    assert len(hashes) == len(PINNED_INPUTS) + 2

    graph_path = tmp_path / GRAPH_REL
    graph_path.write_text(
        graph_path.read_text(encoding="utf-8") + " ", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Pinned input hash mismatch"):
        _load_and_check_pinned_inputs(tmp_path)
