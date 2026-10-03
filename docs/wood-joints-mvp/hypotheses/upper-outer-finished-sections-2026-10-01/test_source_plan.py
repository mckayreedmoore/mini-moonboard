from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PRODUCER_PATH = Path(__file__).with_name("produce.py")
SPEC = importlib.util.spec_from_file_location("upper_outer_finished_sections_producer_test", PRODUCER_PATH)
assert SPEC is not None and SPEC.loader is not None
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plane_candidate(
    identity: str,
    member: str,
    origin: list[float],
    station: float,
    frame: dict[str, list[float]],
    kind: str = "receiver_bore_center",
) -> dict:
    return {
        "identity_key": identity,
        "kind": kind,
        "member_id": member,
        "origin_global_xyz_mm": origin,
        "grain_station_mm": station,
        "frame": frame,
        "source_identity": {"identity": identity},
    }


def test_coincident_planes_retain_all_axis_and_feature_identities() -> None:
    frame = {
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "grain_axis_global_xyz": [0.0, 1.0, 0.0],
        "section_u_global_xyz": [0.0, 0.0, 1.0],
        "section_v_global_xyz": [1.0, 0.0, 0.0],
    }
    candidates = [
        _plane_candidate(
            "receiver:top_outer_left_cleat:axis:side_1:feature:facet006",
            "top_outer_left_cleat",
            [-20.0, 59.85, 1.0],
            59.85,
            frame,
        ),
        _plane_candidate(
            "receiver:top_outer_left_cleat:axis:side_2:feature:facet007",
            "top_outer_left_cleat",
            [-20.0, 59.8500000002, 2.0],
            59.8500000002,
            frame,
        ),
    ]
    planes, identity_to_plane = producer._merge_plane_candidates(candidates)

    assert len(planes) == 1
    assert planes[0]["source_identity_count"] == 2
    assert {row["identity_key"] for row in planes[0]["source_identities"]} == {
        candidates[0]["identity_key"],
        candidates[1]["identity_key"],
    }
    assert set(identity_to_plane) == {row["identity_key"] for row in candidates}
    assert identity_to_plane[candidates[0]["identity_key"]] == identity_to_plane[candidates[1]["identity_key"]]


def test_coincident_bore_and_bracket_planes_keep_both_source_kinds() -> None:
    frame = {
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "grain_axis_global_xyz": [1.0, 0.0, 0.0],
        "section_u_global_xyz": [0.0, 1.0, 0.0],
        "section_v_global_xyz": [0.0, 0.0, 1.0],
    }
    planes, _ = producer._merge_plane_candidates(
        [
            _plane_candidate("axis:rail_1:feature:facet016", "base_rail_top", [5.0, 1.0, 2.0], 5.0, frame),
            _plane_candidate("bracket:rail:left:before", "base_rail_top", [5.0, 0.0, 0.0], 5.0, frame, "host_bracket_section"),
        ]
    )

    assert len(planes) == 1
    assert {row["kind"] for row in planes[0]["source_identities"]} == {
        "receiver_bore_center",
        "host_bracket_section",
    }


def test_membership_guard_rejects_duplicate_missing_or_foreign_receivers() -> None:
    host = {"receiver_member_id": "base_rail_top"}
    cleat = {"receiver_member_id": "top_outer_left_cleat"}
    accepted = producer._validate_receiver_memberships(
        "fixture_axis", [host, cleat], "base_rail_top", "top_outer_left_cleat"
    )
    assert accepted == [host, cleat]

    with pytest.raises(producer.SourceRefusal, match="exactly one host and one cleat"):
        producer._validate_receiver_memberships(
            "fixture_axis", [host, host, cleat], "base_rail_top", "top_outer_left_cleat"
        )
    with pytest.raises(producer.SourceRefusal, match="exactly one host and one cleat"):
        producer._validate_receiver_memberships(
            "fixture_axis", [host], "base_rail_top", "top_outer_left_cleat"
        )
    with pytest.raises(producer.SourceRefusal, match="unexpected receiver"):
        producer._validate_receiver_memberships(
            "fixture_axis",
            [host, {"receiver_member_id": "other_member"}],
            "base_rail_top",
            "top_outer_left_cleat",
        )


def test_source_plan_refuses_candidate_mismatch_and_centroid_off_axis() -> None:
    matching = {"candidate": producer.CANDIDATE, "geometry_revision_id": producer.REVISION}
    bad_candidate = {"candidate": "other_candidate", "geometry_revision_id": producer.REVISION}
    with pytest.raises(producer.SourceRefusal, match="host-actions candidate mismatch"):
        producer.build_source_plan(
            Path("."),
            {
                "host_actions": bad_candidate,
                "finished_surfaces": matching,
                "axis_features": matching,
                "stock_envelopes": matching,
            },
        )

    distance = producer._centroid_axis_distance(
        [1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], "fixture/axis/receiver"
    )
    assert distance == 0.0
    with pytest.raises(producer.SourceRefusal, match="off the source axis line"):
        producer._centroid_axis_distance(
            [1.0, 0.0, 0.01], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], "fixture/axis/receiver"
        )


def test_plane_deduplication_refuses_transitive_tolerance_ambiguity() -> None:
    frame = {
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "grain_axis_global_xyz": [1.0, 0.0, 0.0],
        "section_u_global_xyz": [0.0, 1.0, 0.0],
        "section_v_global_xyz": [0.0, 0.0, 1.0],
    }
    candidates = [
        _plane_candidate(f"fixture:{index}", "base_rail_top", [station, 0.0, 0.0], station, frame)
        for index, station in enumerate((0.0, 0.75e-6, 1.5e-6))
    ]
    with pytest.raises(producer.SourceRefusal, match="ambiguous transitive coincidence"):
        producer._merge_plane_candidates(candidates)


def test_pin_closure_recursively_refuses_changed_bytes(tmp_path: Path) -> None:
    upstream = tmp_path / "upstream.txt"
    upstream.write_bytes(b"original")
    nested_directory = tmp_path / "upstream"
    nested_directory.mkdir()
    nested_pins = nested_directory / "source-pins.json"
    nested_pins.write_text(
        json.dumps(
            {
                "pins": {
                    "artifact": {
                        "path": "upstream.txt",
                        "sha256": _sha(upstream),
                        "size_bytes": upstream.stat().st_size,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    pin_document = tmp_path / "source-pins.json"
    pin_document.write_text(
        json.dumps(
            {
                "pins": {
                    "nested_pin_document": {
                        "path": "upstream/source-pins.json",
                        "sha256": _sha(nested_pins),
                        "size_bytes": nested_pins.stat().st_size,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    producer.collect_pin_closure(tmp_path, ["source-pins.json"], {}, {})

    upstream.write_bytes(b"changed")
    with pytest.raises(producer.SourceRefusal, match="changed pinned source upstream.txt"):
        producer.collect_pin_closure(tmp_path, ["source-pins.json"], {}, {})


def test_missing_kernel_is_a_readiness_refusal_without_cad_import(tmp_path: Path) -> None:
    with pytest.raises(producer.SourceRefusal, match="kernel is not ready"):
        producer._import_kernel(tmp_path / "section_geometry.py")
