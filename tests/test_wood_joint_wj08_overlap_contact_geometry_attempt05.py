"""Attempt05 covers strict evidence equality and verification failures."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from scripts import wood_joint_wj08_overlap_contact_geometry_attempt05 as attempt05


def _graph():
    return json.loads(
        (attempt05.ROOT / attempt05.GRAPH_REL).read_text(encoding="utf-8")
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
        attempt05.GRAPH_PRODUCER_REL.as_posix(): "fixture",
        attempt05.RECEIVER_PRODUCER_REL.as_posix(): "fixture",
    }


def _refresh_packet_sums(packet):
    rows = []
    for filename in attempt05._packet_files():
        digest = hashlib.sha256((packet / filename).read_bytes()).hexdigest()
        rows.append(f"{digest}  {filename}")
    (packet / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_attempt05_preserves_geometry_only_evidence_and_pending_criterion():
    graph = _graph()
    evidence = attempt05.build_geometry_evidence(graph, _source_hashes())

    assert attempt05.validate_geometry_consistency(graph) == (
        attempt05.EXPECTED_CLASS_COUNTS
    )
    assert evidence["schema"] == attempt05.SCHEMA
    assert evidence["criterion_id"] == "overlap_contact"
    assert evidence["criterion_disposition"] == "pending"
    assert evidence["mechanics"]["active_contact_established"] is False
    assert evidence["counts"]["unordered_member_pairs"] == 1225


@pytest.mark.parametrize(
    ("state", "field", "value"),
    [
        ("separated", "minimum_separation_mm", 0.0),
        ("finite_opposed_planar_touch", "minimum_separation_mm", 1e-4),
        ("zero_area_touch_or_unresolved", "minimum_separation_mm", 1e-4),
        ("separated", "common_volume_mm3", 1.0001e-6),
        ("finite_opposed_planar_touch", "common_volume_mm3", 1.0001e-6),
        ("zero_area_touch_or_unresolved", "common_volume_mm3", 1.0001e-6),
        (
            "zero_area_touch_or_unresolved",
            "finite_shared_planar_face_area_mm2",
            1.0001e-6,
        ),
        ("separated", "opposed_planar_face_contact_area_mm2", 1.0001e-6),
        (
            "finite_opposed_planar_touch",
            "cooriented_planar_face_contact_area_mm2",
            1.0001e-6,
        ),
    ],
    ids=[
        "exact-separated-zero-gap",
        "finite-touch-beyond-distance-tolerance",
        "unresolved-beyond-distance-tolerance",
        "separated-volume-beyond-tolerance",
        "finite-touch-volume-beyond-tolerance",
        "unresolved-volume-beyond-tolerance",
        "unresolved-shared-area-beyond-tolerance",
        "separated-contact-area-beyond-tolerance",
        "opposed-touch-with-excess-cooriented-area",
    ],
)
def test_measurements_beyond_upstream_thresholds_fail_closed(
    state: str, field: str, value: float
):
    graph = _graph()
    interface_state = "separated" if state == "separated" else None
    _pair(graph, state, interface_state)[field] = value

    with pytest.raises(ValueError):
        attempt05.validate_geometry_consistency(graph)


def test_upstream_subthreshold_measurements_remain_accepted():
    graph = _graph()
    unresolved = _pair(graph, "zero_area_touch_or_unresolved")
    unresolved["finite_shared_planar_face_area_mm2"] = 1e-6
    unresolved["common_volume_mm3"] = 1e-6
    _pair(graph, "finite_opposed_planar_touch")["common_volume_mm3"] = 1e-6
    _pair(graph, "separated", "separated")["common_volume_mm3"] = 1e-6

    assert attempt05.validate_geometry_consistency(graph) == (
        attempt05.EXPECTED_CLASS_COUNTS
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate", "another-candidate"),
        ("revision_id", "another-revision"),
        ("scope", "complete mechanics and acceptance"),
    ],
)
def test_source_pin_identity_and_scope_metadata_are_enforced(
    tmp_path, field: str, value: str
):
    packet = tmp_path / "attempt05-packet"
    attempt05.freeze_packet(output_dir=packet)
    pins_path = packet / "source-pins.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8"))
    pins[field] = value
    pins_path.write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    _refresh_packet_sums(packet)

    with pytest.raises(ValueError, match="source-pins"):
        attempt05.verify_packet(output_dir=packet)


def test_tampered_frozen_evidence_is_rejected_after_hashes_refresh(tmp_path):
    packet = tmp_path / "attempt05-packet"
    attempt05.freeze_packet(output_dir=packet)
    evidence_path = packet / "geometry-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["counts"]["unordered_member_pairs"] += 1
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    pins_path = packet / "source-pins.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8"))
    pins["output_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    pins_path.write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    _refresh_packet_sums(packet)

    with pytest.raises(ValueError, match="does not reproduce"):
        attempt05.verify_packet(output_dir=packet)


def test_json_boolean_and_number_types_do_not_compare_equal(tmp_path):
    packet = tmp_path / "attempt05-packet"
    attempt05.freeze_packet(output_dir=packet)
    evidence_path = packet / "geometry-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["mechanics"]["active_contact_established"] is False
    evidence["mechanics"]["active_contact_established"] = 0
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    pins_path = packet / "source-pins.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8"))
    pins["output_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    pins_path.write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    _refresh_packet_sums(packet)

    with pytest.raises(ValueError, match="does not reproduce"):
        attempt05.verify_packet(output_dir=packet)


def test_cli_freeze_verify_and_documented_checksum_cycle(tmp_path):
    packet = tmp_path / "attempt05-packet"
    module = "scripts.wood_joint_wj08_overlap_contact_geometry_attempt05"
    freeze = subprocess.run(
        [sys.executable, "-m", module, "--freeze", "--output-dir", str(packet)],
        cwd=attempt05.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(freeze.stdout)["status"] == "FROZEN_GEOMETRY_ONLY_PENDING"

    verify = subprocess.run(
        [sys.executable, "-m", module, "--verify", "--output-dir", str(packet)],
        cwd=attempt05.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(verify.stdout)["criterion_disposition"] == "pending"
    readme = (packet / "README.md").read_text(encoding="utf-8")
    assert "canonical JSON representations" in " ".join(readme.split())

    checksums = subprocess.run(
        ["bash", "-lc", f"cd {packet} && sha256sum -c SHA256SUMS"],
        cwd=attempt05.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert checksums.stdout.count(": OK") == 3
