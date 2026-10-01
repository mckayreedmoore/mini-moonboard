"""Attempt02 fails closed on geometry-state and measured-distance conflicts."""

from __future__ import annotations

import json
import shutil

import pytest

from scripts import wood_joint_wj08_overlap_contact_geometry as attempt01
from scripts import wood_joint_wj08_overlap_contact_geometry_attempt02 as attempt02


def _graph():
    return json.loads(
        (attempt01.ROOT / attempt01.GRAPH_REL).read_text(encoding="utf-8")
    )


def _pair(graph, geometry_state: str, interface_state: str | None = None):
    return next(
        row
        for row in graph["edges"]
        if row["geometry_state"] == geometry_state
        and (
            interface_state is None
            or row["interface_geometry_state"] == interface_state
        )
    )


def _source_hashes():
    return {
        attempt02.GRAPH_PRODUCER_REL.as_posix(): "fixture",
        attempt02.RECEIVER_PRODUCER_REL.as_posix(): "fixture",
    }


def test_attempt02_reconciles_current_graph_and_keeps_criterion_pending():
    graph = _graph()
    classes = attempt02.validate_geometry_consistency(graph)
    evidence = attempt02.build_geometry_evidence(graph, _source_hashes())

    assert classes == attempt01.EXPECTED_CLASS_COUNTS
    assert evidence["schema"] == attempt02.SCHEMA
    assert evidence["criterion_id"] == "overlap_contact"
    assert evidence["criterion_disposition"] == "pending"
    assert evidence["mechanics"]["active_contact_established"] is False
    assert evidence["counts"]["unordered_member_pairs"] == 1225
    assert evidence["upstream_classification_tolerances"] == {
        "distance_mm": 1e-5,
        "face_area_mm2": 1e-6,
        "source": {
            attempt02.GRAPH_PRODUCER_REL.as_posix(): "fixture",
            attempt02.RECEIVER_PRODUCER_REL.as_posix(): "fixture",
        },
        "interpretation": "Numerical geometry classification only; not an installed fit or contact law.",
    }


@pytest.mark.parametrize(
    ("state", "field", "value"),
    [
        ("separated", "minimum_separation_mm", 0.0),
        ("finite_opposed_planar_touch", "minimum_separation_mm", 1e-4),
        ("zero_area_touch_or_unresolved", "minimum_separation_mm", 1e-4),
        ("separated", "common_volume_mm3", 0.25),
        ("finite_opposed_planar_touch", "cooriented_planar_face_contact_area_mm2", 1.0),
    ],
    ids=[
        "exact-separated-zero-gap",
        "finite-touch-beyond-tolerance",
        "unresolved-beyond-tolerance",
        "separated-positive-overlap-volume",
        "opposed-touch-with-cooriented-area",
    ],
)
def test_contradictory_measured_distance_or_contact_state_fails_closed(
    state: str, field: str, value: float
):
    graph = _graph()
    interface_state = "separated" if state == "separated" else None
    edge = _pair(graph, state, interface_state)
    edge[field] = value

    with pytest.raises(ValueError):
        attempt02.validate_geometry_consistency(graph)


def test_aabb_only_pair_requires_lower_bound_above_classification_tolerance():
    graph = _graph()
    edge = _pair(graph, "separated", "not_evaluated_aabb_separated")
    edge["interface_geometry_state"] = "not_evaluated_aabb_separated"
    edge["broadphase_candidate"] = False
    edge["contact_measurement_basis"] = attempt02.AABB_BASIS
    edge["minimum_separation_mm"] = None
    edge["aabb_separation_lower_bound_mm"] = attempt02.GEOMETRY_TOLERANCE_MM

    with pytest.raises(ValueError, match="AABB-only"):
        attempt02.validate_geometry_consistency(graph)


def test_source_hash_drift_in_upstream_geometry_rule_is_rejected(tmp_path):
    paths = [
        *attempt01.PINNED_INPUTS,
        attempt01.PRODUCER_REL,
        attempt01.TEST_REL,
        *attempt02.EXPECTED_EXTRA_INPUTS,
        attempt02.PRODUCER_REL,
        attempt02.TEST_REL,
    ]
    for rel in paths:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(attempt01.ROOT / rel, target)

    hashes = attempt02._current_source_hashes(tmp_path)
    expected_count = (
        len(attempt01.PINNED_INPUTS) + 2 + len(attempt02.EXPECTED_EXTRA_INPUTS) + 2
    )
    assert len(hashes) == expected_count

    source = tmp_path / attempt02.GRAPH_PRODUCER_REL
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Pinned attempt02 input hash mismatch"):
        attempt02._current_source_hashes(tmp_path)


def test_attempt02_readme_checksum_command_runs_from_repository_root():
    evidence = attempt02.build_geometry_evidence(_graph(), _source_hashes())
    readme = attempt02._render_readme(evidence, {"source_hashes": {}})

    assert (
        "(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt02 && sha256sum -c SHA256SUMS)"
        in readme
    )
