"""Candidate-only F1–G1 passage; selected source remains unchanged."""

import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.owner_barrel_candidate_service import (
    F1_G1_BORE,
    F1_G1_DIAMETER_MM,
    candidate_service_cutters,
)


def test_only_candidate_f1_g1_service_passage_is_reduced():
    source = variant(KERF_RIGHT)
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    selected = {
        name: (member, cutter) for member, name, cutter in source.service_cutters()
    }
    candidate = {
        name: (member, cutter)
        for member, name, cutter in candidate_service_cutters(source, wood)
    }
    record = next(row for row in source.bore_records() if row["name"] == F1_G1_BORE)

    assert set(candidate) == set(selected)
    assert record["diameter_mm"] == 38.1
    assert F1_G1_DIAMETER_MM == 25.4
    assert candidate[F1_G1_BORE][0] == "base_principal_center_right"
    assert candidate[F1_G1_BORE][1].Volume() == pytest.approx(
        selected[F1_G1_BORE][1].Volume() * (25.4 / 38.1) ** 2
    )
    assert all(
        candidate[name][1].Volume() == pytest.approx(cutter.Volume())
        for name, (_, cutter) in selected.items()
        if name != F1_G1_BORE
    )
    wire = next(
        part for part in source.electrical_parts() if part.name == "wire_072_F1_G1"
    )
    inside = wire.shape.intersect(wood["base_principal_center_right"])
    assert inside.Volume() > 0
    assert inside.cut(candidate[F1_G1_BORE][1]).Volume() < 1e-3
    assert len(source.panel_connections()) == 66
    assert sum(row.kind == "bolt" for row in source.connections()) == 12
