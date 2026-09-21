"""PB-02 displaced-clip inventory boundaries and archival identity checks."""

import json
from types import SimpleNamespace

import pytest

from scripts import simple_center_displaced_clip_duties as duties


@pytest.fixture(scope="module")
def report():
    return duties.inventory()


def test_only_two_displaced_stations_and_exact_legacy_ownership(report):
    assert set(report["stations"]) == set(duties.STATIONS)
    assert report["pose"]["post_bounds_mm"] == [88.75, 177.65, -175.7, -86.8, 0, 238.9]
    assert report["pose"]["post_bolt_x_mm"] == 140
    assert report["pose"]["cleat_link_x_mm"] == 114.45
    assert report["stations"]["clip_split_base_center_right"]["origin_xyz_mm"] == [
        89.05,
        -124.9,
        277,
    ]
    assert report["stations"]["clip_split_header_center_right"]["origin_xyz_mm"] == [
        89.05,
        -105.85,
        238.9,
    ]
    for name, (_, partner) in duties.STATIONS.items():
        item = report["stations"][name]
        assert item["old_header_host"] == "base_header"
        assert item["old_partner"] == partner
        header = item["old_header_bounds_mm"]
        receiver = item["old_partner_bounds_mm"]
        sense = 1 if receiver[4] == header[5] else -1
        assert receiver[4] == header[5] or receiver[5] == header[4]
        assert item["inferred_historical_separation_partner_away_from_header_xyz"] == [
            0,
            0,
            sense,
        ]
        assert item["inferred_historical_separation_header_away_from_partner_xyz"] == [
            0,
            0,
            -sense,
        ]
        assert len(item["old_fasteners"]) == 6
        assert [s["wood_receiver"] for s in item["old_fasteners"]] == [
            "base_header"
        ] * 3 + [partner] * 3
        assert {s["product"] for s in item["old_fasteners"]} == {
            "Simpson SDS25112, separately purchased"
        }
        assert all(
            s["modeled_length_mm"] == 38.1 and s["modeled_diameter_mm"] == 6.35
            for s in item["old_fasteners"]
        )


def test_archival_actions_are_bounded_to_old_proxy_and_named_cases(report):
    assert set(report["archival_old_topology_actions"]) == set(duties.STATIONS)
    for rows in report["archival_old_topology_actions"].values():
        assert {row["case"] for row in rows} == {
            "a1-rear",
            "a12-left",
            "a12-rear",
            "k12-rear",
            "k12-right",
        }
        assert all(len(row["force_on_old_partner_via_clip_xyz_n"]) == 3 for row in rows)
        assert all(len(row["source_report_sha256"]) == 64 for row in rows)
    assert any("new bolt demand" in issue for issue in report["ambiguity"])
    assert "a12-forward missing" in report["archival_case_coverage"]


def test_separation_inference_requires_abutting_old_wood():
    def box(zmin, zmax):
        return SimpleNamespace(xmin=0, xmax=10, ymin=0, ymax=10, zmin=zmin, zmax=zmax)

    assert duties._historical_z_separation(box(10, 20), box(20, 30)) == 1
    assert duties._historical_z_separation(box(10, 20), box(0, 10)) == -1
    with pytest.raises(ValueError, match="not established"):
        duties._historical_z_separation(box(10, 20), box(21, 30))


def test_rejects_archival_origin_or_acceptance_change(monkeypatch, report):
    original = json.loads(duties.ARCHIVE.read_text())

    class AlteredArchive:
        def __init__(self, contents):
            self.contents = contents

        def read_text(self):
            return json.dumps(self.contents)

    altered = json.loads(json.dumps(original))
    altered["accepted_default_v2"][0]["sides"]["right"]["interfaces"][
        "principal_header"
    ]["origin_xyz_mm"][1] += 1
    monkeypatch.setattr(duties, "ARCHIVE", AlteredArchive(altered))
    with pytest.raises(ValueError, match="station does not match"):
        duties._old_actions(report["stations"])

    altered = json.loads(json.dumps(original))
    altered["accepted_default_v2"][0]["convergence"]["numerically_accepted"] = False
    monkeypatch.setattr(duties, "ARCHIVE", AlteredArchive(altered))
    with pytest.raises(ValueError, match="Unaccepted archival case"):
        duties._old_actions(report["stations"])
