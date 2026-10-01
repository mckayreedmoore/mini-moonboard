from __future__ import annotations

import copy
import hashlib
import math
from pathlib import Path

import cadquery as cq
import pytest

from scripts import build_current_taper_geometry_preflight_attempt01 as preflight


@pytest.fixture(scope="module")
def sources() -> dict:
    return preflight.load_sources()[0]


@pytest.fixture(scope="module")
def left_faces() -> list[dict]:
    path = Path(preflight.BUNDLE).parent / "members/lumber_leg_left.step"
    shape = cq.importers.importStep(str(preflight.ROOT / path)).val()
    return preflight.planar_face_records(shape)


@pytest.fixture(scope="module")
def report() -> dict:
    return preflight.build_report()[0]


def taper_face(left_faces: list[dict]) -> dict:
    measured = preflight.measure_taper(preflight.LEGS[0], left_faces, preflight.GRAIN)
    return copy.deepcopy(measured["taper_face_geometry"])


def test_exact_current_breps_supply_geometry_only(report: dict) -> None:
    assert report["candidate"] == preflight.CANDIDATE
    assert report["geometry_revision_id"] == preflight.REVISION
    assert report["bundle_member_count"] == 50
    assert report["measured_member_ids"] == list(preflight.LEGS)
    assert report["cad_geometry_preflight_supported"] is True
    assert report["full_criterion_dispositions"] == dict.fromkeys(
        preflight.CRITERION_IDS, "pending"
    )
    for field in (
        "fresh_current_case_prerequisites_satisfied",
        "engineering_mvp_complete",
        "release",
        "native_run_performed",
        "delivered_stock_observed",
    ):
        assert report[field] is False
    for row in report["members"]:
        assert row["taper_run_mm"] == pytest.approx(457.2, abs=1e-8)
        assert row["recess_depth_mm"] == pytest.approx(38.1, abs=1e-8)
        assert row["stock_width_mm"] == pytest.approx(88.9, abs=1e-8)
        assert row["stock_depth_mm"] == pytest.approx(139.7, abs=1e-8)
        assert row["cross_grain_extent_mm"] == pytest.approx(139.7, abs=1e-8)
        assert row["run_over_depth"] == pytest.approx(12, abs=1e-10)
        assert row["plane_normal_run_over_depth"] == pytest.approx(12, abs=1e-10)
        assert row["slope_margin_before_tolerance_mm"] == pytest.approx(76.2, abs=1e-8)
        assert all(row["cad_predicate_results"].values())
        assert row["step_sha256"] == preflight.LEG_STEP_PINS[row["member_id"]]
        assert "face_ordinal" not in row["taper_face_geometry"]


@pytest.mark.parametrize(
    "path,field",
    [
        ("wood-joints-candidate.json", "candidate"),
        (preflight.BUNDLE, "candidate"),
        (preflight.BUNDLE, "geometry_revision_id"),
        (preflight.FRAME_MAP, "candidate"),
        (preflight.FRAME_MAP, "geometry_revision_id"),
    ],
)
def test_candidate_or_revision_drift_fails(
    sources: dict, path: str, field: str
) -> None:
    mutated = copy.deepcopy(sources)
    mutated[path][field] = "historical-or-other-candidate"
    with pytest.raises(ValueError, match="identity mismatch"):
        preflight.validate_identity(mutated)


def test_authority_revision_drift_fails(sources: dict) -> None:
    mutated = copy.deepcopy(sources)
    mutated["wood-joints-candidate.json"]["current_development_revision"][
        "revision_id"
    ] = "old"
    with pytest.raises(ValueError, match="identity mismatch"):
        preflight.validate_identity(mutated)


@pytest.mark.parametrize("change", ["missing", "duplicate", "wrong"])
def test_both_exact_leg_ids_are_required(sources: dict, change: str) -> None:
    mutated = copy.deepcopy(sources)
    rows = mutated[preflight.BUNDLE]["members"]
    row = next(r for r in rows if r["member_id"] == preflight.LEGS[0])
    if change == "missing":
        rows.remove(row)
    elif change == "duplicate":
        row["member_id"] = preflight.LEGS[1]
    else:
        row["member_id"] = "historical_leg"
    with pytest.raises(ValueError, match="unique|member IDs differ|missing exact"):
        preflight.validate_identity(mutated)


def test_hash_drift_and_missing_file_fail(tmp_path: Path) -> None:
    path = tmp_path / "current.step"
    path.write_bytes(b"bound current STEP bytes")
    pins = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}
    preflight.verify_pins(tmp_path, pins)
    path.write_bytes(b"different STEP bytes")
    with pytest.raises(ValueError, match="source hash mismatch"):
        preflight.verify_pins(tmp_path, pins)
    path.unlink()
    with pytest.raises(ValueError, match="source hash mismatch"):
        preflight.verify_pins(tmp_path, pins)


def test_wrong_step_lineage_and_axis_fail(sources: dict) -> None:
    mutated = copy.deepcopy(sources)
    row = next(
        r
        for r in mutated[preflight.BUNDLE]["members"]
        if r["member_id"] == preflight.LEGS[0]
    )
    row["step_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="lineage mismatch"):
        preflight.validate_identity(mutated)
    mutated = copy.deepcopy(sources)
    frame = next(
        r
        for r in mutated[preflight.FRAME_MAP]["members"]
        if r["member_id"] == preflight.LEGS[0]
    )
    frame["conditional_grain_assignment"]["proposed_global_xyz"] = [0, 1, 0]
    with pytest.raises(ValueError, match="wrong current leg longitudinal axis"):
        preflight.validate_identity(mutated)


def test_face_selection_does_not_depend_on_ordinal(left_faces: list[dict]) -> None:
    forward = preflight.measure_taper(preflight.LEGS[0], left_faces, preflight.GRAIN)
    reversed_faces = preflight.measure_taper(
        preflight.LEGS[0], list(reversed(left_faces)), preflight.GRAIN
    )
    assert forward == reversed_faces


def test_missing_or_duplicate_taper_plane_fails(left_faces: list[dict]) -> None:
    taper = taper_face(left_faces)
    for faces in ([], [f for f in left_faces if f != taper], [taper, taper]):
        with pytest.raises(ValueError, match="missing or ambiguous"):
            preflight.measure_taper(preflight.LEGS[0], faces, preflight.GRAIN)


@pytest.mark.parametrize(
    "change",
    [
        "missing_vertex",
        "duplicate_vertex",
        "wire",
        "curve",
        "length",
        "normal",
        "off_plane",
    ],
)
def test_malformed_taper_face_fails(left_faces: list[dict], change: str) -> None:
    face = taper_face(left_faces)
    if change == "missing_vertex":
        face["vertices_xyz_mm"].pop()
    elif change == "duplicate_vertex":
        face["vertices_xyz_mm"][0] = face["vertices_xyz_mm"][1]
    elif change == "wire":
        face["wire_count"] = 2
    elif change == "curve":
        face["edges"][0]["type"] = "CIRCLE"
    elif change == "length":
        face["edges"][0]["length_mm"] += 1
    elif change == "normal":
        face["normal_xyz"][0] *= 0.9
    else:
        face["vertices_xyz_mm"][0][0] += 1
    with pytest.raises(ValueError):
        preflight.measure_taper(preflight.LEGS[0], [face], preflight.GRAIN)


def test_wrong_leg_and_axis_do_not_receive_a_measurement(
    left_faces: list[dict],
) -> None:
    with pytest.raises(ValueError, match="wrong current leg ID"):
        preflight.measure_taper("historical_leg", left_faces, preflight.GRAIN)
    with pytest.raises(ValueError, match="wrong current leg longitudinal axis"):
        preflight.measure_taper(preflight.LEGS[0], left_faces, (0, 1, 0))
    with pytest.raises(ValueError, match="wrong inward-face"):
        preflight.measure_taper(preflight.LEGS[1], left_faces, preflight.GRAIN)


def test_exact_adopted_slope_threshold_boundary() -> None:
    depth = 38.1
    threshold = 10 * depth - 1e-6
    assert preflight.geometry_predicates(threshold, depth, 88.9, 139.7)[
        preflight.CRITERION_IDS[0]
    ]
    assert not preflight.geometry_predicates(
        math.nextafter(threshold, -math.inf), depth, 88.9, 139.7
    )[preflight.CRITERION_IDS[0]]
    assert preflight.geometry_predicates(
        math.nextafter(threshold, math.inf), depth, 88.9, 139.7
    )[preflight.CRITERION_IDS[0]]


def test_exact_adopted_stock_runout_threshold_and_wrong_stock() -> None:
    threshold = 457.2 - 1e-5
    assert preflight.geometry_predicates(threshold, 38.1, 88.9, 139.7)[
        preflight.CRITERION_IDS[1]
    ]
    assert not preflight.geometry_predicates(
        math.nextafter(threshold, -math.inf), 38.1, 88.9, 139.7
    )[preflight.CRITERION_IDS[1]]
    assert not preflight.geometry_predicates(457.2, 38.1, 38.1, 139.7)[
        preflight.CRITERION_IDS[1]
    ]


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True])
def test_nonfinite_or_boolean_values_fail(left_faces: list[dict], bad: object) -> None:
    for index in range(4):
        values = [457.2, 38.1, 88.9, 139.7]
        values[index] = bad
        with pytest.raises(ValueError, match="finite numeric"):
            preflight.geometry_predicates(*values)
    face = taper_face(left_faces)
    face["vertices_xyz_mm"][0][0] = bad
    with pytest.raises(ValueError, match="finite numeric"):
        preflight.measure_taper(preflight.LEGS[0], [face], preflight.GRAIN)


@pytest.mark.parametrize("text", ['{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}'])
def test_ambiguous_or_nonfinite_json_fails(tmp_path: Path, text: str) -> None:
    path = tmp_path / "input.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        preflight.read_json(path)


def test_current_source_pins_include_every_step_and_exact_authorities(
    sources: dict,
) -> None:
    _, pins = preflight.load_sources()
    for path, expected in preflight.ANCHOR_PINS.items():
        assert pins[path] == expected
    for row in sources[preflight.BUNDLE]["members"]:
        path = str(Path(preflight.BUNDLE).parent.parent / row["step_file"])
        assert pins[path] == row["step_sha256"]


def test_frozen_packet_reproduces_exactly() -> None:
    verification = preflight.check_packet()
    assert verification["cad_geometry_preflight_supported"] is True
    assert verification["full_criteria_pending"] == list(preflight.CRITERION_IDS)
    assert verification["native_run_performed"] is False
    assert verification["release"] is False
