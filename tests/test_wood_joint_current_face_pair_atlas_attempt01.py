"""Focused face identity, scope, and fail-closed tests for atlas attempt01."""

from __future__ import annotations

import hashlib
import json

import cadquery as cq
import pytest

from scripts import wood_joint_current_face_pair_atlas_attempt01 as atlas


def _box_faces(member_id: str, shape: cq.Shape):
    return atlas.source_face_records(member_id, shape)


def _touching_boxes():
    first = cq.Workplane("XY").box(
        10, 10, 10, centered=(False, False, False)
    ).val()
    second = cq.Workplane("XY").box(
        10, 10, 10, centered=(False, False, False)
    ).translate((10, 0, 0)).val()
    return first, second


def test_exact_face_pair_has_stable_body_face_ids_normals_and_region():
    first, second = _touching_boxes()
    first_faces = _box_faces("member_a", first)
    second_faces = _box_faces("member_b", second)

    result = atlas.collect_opposed_face_pairs(
        "member_a",
        first_faces,
        "member_b",
        second_faces,
        expected_area_mm2=100.0,
        expected_shared_area_mm2=100.0,
    )

    assert result["face_pair_count"] == 1
    pair = result["face_pairs"][0]
    assert pair["face_a_id"].startswith("member_a/step-face-")
    assert pair["face_b_id"].startswith("member_b/step-face-")
    assert len(pair["face_a_signature_sha256"]) == 64
    assert len(pair["face_b_signature_sha256"]) == 64
    assert pair["normal_dot"] == -1.0
    assert pair["overlap_area_mm2"] == 100.0
    assert pair["overlap_regions"][0]["area_mm2"] == 100.0

    repeated_first = _box_faces("member_a", first)
    assert [row["face_id"] for row in first_faces] == [
        row["face_id"] for row in repeated_first
    ]
    assert [row["signature_sha256"] for row in first_faces] == [
        row["signature_sha256"] for row in repeated_first
    ]


def test_line_or_point_touch_is_not_promoted_to_a_finite_face_pair():
    first, _ = _touching_boxes()
    second = cq.Workplane("XY").box(
        10, 10, 10, centered=(False, False, False)
    ).translate((10, 10, 0)).val()

    with pytest.raises(ValueError, match="do not reproduce frozen opposed area"):
        atlas.collect_opposed_face_pairs(
            "member_a",
            _box_faces("member_a", first),
            "member_b",
            _box_faces("member_b", second),
            expected_area_mm2=10.0,
            expected_shared_area_mm2=10.0,
        )


@pytest.mark.parametrize(
    ("candidate", "revision"),
    [
        ("other-candidate", atlas.EXPECTED_REVISION),
        (atlas.EXPECTED_CANDIDATE, "stale-revision"),
    ],
)
def test_stale_candidate_or_revision_fails_closed(candidate: str, revision: str):
    with pytest.raises(ValueError, match="stale or unsupported"):
        atlas._validate_revision_identity(candidate, revision)


def test_duplicate_source_body_ids_are_rejected():
    rows = [{"member_id": "member_a"}, {"member_id": "member_a"}]
    with pytest.raises(ValueError, match="duplicate member_id"):
        atlas._unique_index(rows, "member_id", "fixture bodies")


def test_duplicate_json_object_keys_are_rejected():
    with pytest.raises(ValueError, match="Duplicate JSON object key"):
        json.loads('{"revision_id":"current","revision_id":"stale"}',
                   object_pairs_hook=atlas._unique_object)


def test_source_hash_mismatch_is_rejected(tmp_path):
    source = tmp_path / "source.step"
    source.write_bytes(b"pinned source")
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    pins: dict[str, str] = {}
    atlas._add_pin(tmp_path, pins, "source.step", expected)
    source.write_bytes(b"changed source")

    with pytest.raises(ValueError, match="pinned source hash mismatch"):
        atlas._add_pin(tmp_path, {}, "source.step", expected)


def test_attempt02_attempt07_pair_rosters_reconcile_without_resolving_six():
    graph = atlas._load_json(atlas.ROOT / atlas.GRAPH_REL)
    evidence = atlas._load_json(atlas.ROOT / atlas.OVERLAP_EVIDENCE_REL)

    finite, unresolved = atlas._validate_graph_and_evidence(graph, evidence)

    assert len(finite) == 115
    assert len(unresolved) == 6
    assert all(row["geometry_state"] == "zero_area_touch_or_unresolved" for row in unresolved)
    assert evidence["criterion_disposition"] == "pending"
    assert evidence["mechanics"]["active_contact_established"] is False


def test_area_reconciliation_rejects_a_tampered_expected_area():
    first, second = _touching_boxes()

    with pytest.raises(ValueError, match="do not reproduce frozen opposed area"):
        atlas.collect_opposed_face_pairs(
            "member_a",
            _box_faces("member_a", first),
            "member_b",
            _box_faces("member_b", second),
            expected_area_mm2=99.0,
            expected_shared_area_mm2=99.0,
        )
