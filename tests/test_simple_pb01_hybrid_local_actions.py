"""Focused checks for the preserved PB01 diagnostic extractor."""

import pytest

from scripts.simple_pb01_hybrid_local_actions import ARCHIVE, extract, wrench


def test_preserved_case_has_signed_serial_actions():
    result = extract(ARCHIVE)
    assert result["scope"] == "diagnostic_only"
    assert result["proxy_station_count"] == 23
    assert set(result["interfaces"]) == {"upright", "rail"}
    for interface in result["interfaces"].values():
        assert len(interface["bolts"]) == 2
        assert len(interface["contacts"]) == 4
        assert sum(row["active"] for row in interface["contacts"]) == 2
        for bolt in interface["bolts"]:
            assert bolt["lateral_magnitude_n"] == pytest.approx(
                sum(value * value for value in bolt["lateral_xyz_n"]) ** 0.5
            )
        for first, second in zip(
            interface["resultant_on_host"]["force_xyz_n"],
            interface["resultant_on_cleat"]["force_xyz_n"],
        ):
            assert first == pytest.approx(-second)
    assert result["interfaces"]["upright"]["bolts"][0]["axial_n"] < 0


def test_wrench_uses_signed_force_and_common_datum():
    force, moment = wrench([1, 2, 3], [0, 1, 0], [1, 0, 0])
    assert force == [0, 1, 0]
    assert moment == [-3, 0, 0]


def test_rejects_wrong_archive_identity(tmp_path):
    bad = tmp_path / "changed.tar.gz"
    bad.write_bytes(ARCHIVE.read_bytes() + b"x")
    with pytest.raises(ValueError, match="archive SHA-256"):
        extract(bad)
