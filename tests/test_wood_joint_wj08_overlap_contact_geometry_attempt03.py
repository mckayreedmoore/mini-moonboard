"""Attempt03 mirrors geometry thresholds and exercises packet reproduction."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from scripts import wood_joint_wj08_overlap_contact_geometry_attempt02 as attempt02
from scripts import wood_joint_wj08_overlap_contact_geometry_attempt03 as attempt03


def _graph():
    return json.loads(
        (attempt02.ROOT / attempt02.attempt01.GRAPH_REL).read_text(encoding="utf-8")
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


def test_attempt03_reconciles_graph_and_keeps_criterion_pending():
    graph = _graph()
    classes = attempt03.validate_geometry_consistency(graph)
    evidence = attempt03.build_geometry_evidence(graph, _source_hashes())

    assert classes == attempt02.attempt01.EXPECTED_CLASS_COUNTS
    assert evidence["schema"] == attempt03.SCHEMA
    assert evidence["criterion_id"] == "overlap_contact"
    assert evidence["criterion_disposition"] == "pending"
    assert evidence["mechanics"]["active_contact_established"] is False
    assert evidence["counts"]["unordered_member_pairs"] == 1225
    assert evidence["upstream_classification_tolerances"] == {
        "distance_mm": 1e-5,
        "face_area_mm2": 1e-6,
        "common_volume_mm3": 1e-6,
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
    edge = _pair(graph, state, interface_state)
    edge[field] = value

    with pytest.raises(ValueError):
        attempt03.validate_geometry_consistency(graph)


def test_upstream_subthreshold_measurements_are_accepted():
    graph = _graph()
    unresolved = _pair(graph, "zero_area_touch_or_unresolved")
    unresolved["finite_shared_planar_face_area_mm2"] = 1e-6
    unresolved["common_volume_mm3"] = 1e-6

    finite_touch = _pair(graph, "finite_opposed_planar_touch")
    finite_touch["common_volume_mm3"] = 1e-6

    separated = _pair(graph, "separated", "separated")
    separated["common_volume_mm3"] = 1e-6

    assert attempt03.validate_geometry_consistency(graph) == (
        attempt02.attempt01.EXPECTED_CLASS_COUNTS
    )


def test_pinned_upstream_verifier_and_predecessor_packet_are_checked(monkeypatch):
    bad_hash = "0" * 64
    first_packet_input = next(iter(attempt03.ATTEMPT02_PACKET_HASHES))
    monkeypatch.setitem(attempt03.ATTEMPT02_PACKET_HASHES, first_packet_input, bad_hash)
    with pytest.raises(ValueError, match="Pinned attempt03 input hash mismatch"):
        attempt03._current_source_hashes()


def test_cli_freeze_verify_and_documented_checksum_cycle(tmp_path):
    packet = tmp_path / "attempt03-packet"
    module = "scripts.wood_joint_wj08_overlap_contact_geometry_attempt03"
    freeze = subprocess.run(
        [sys.executable, "-m", module, "--freeze", "--output-dir", str(packet)],
        cwd=attempt03.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(freeze.stdout)["status"] == "FROZEN_GEOMETRY_ONLY_PENDING"

    verify = subprocess.run(
        [sys.executable, "-m", module, "--verify", "--output-dir", str(packet)],
        cwd=attempt03.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(verify.stdout)["criterion_disposition"] == "pending"
    readme = (packet / "README.md").read_text(encoding="utf-8")
    assert f"python -m {module} --verify" in readme

    checksums = subprocess.run(
        ["bash", "-lc", f"cd {packet} && sha256sum -c SHA256SUMS"],
        cwd=attempt03.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert checksums.stdout.count(": OK") == 3
