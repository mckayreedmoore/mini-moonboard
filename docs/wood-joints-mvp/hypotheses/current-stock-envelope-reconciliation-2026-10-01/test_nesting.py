from __future__ import annotations

import math

import pytest
from nesting import Blank, nest_blanks


def test_exact_fit_charges_both_trims_and_a_separation_kerf_per_blank() -> None:
    result = nest_blanks(
        [Blank("a", 40, "4x4"), Blank("b", 41, "4x4")],
        {"4x4": 100},
        crosscut_kerf_mm=2,
        end_trim_start_mm=10,
        end_trim_end_mm=5,
    )

    assert result.complete
    assert result.totals.board_count == 1
    board = result.boards[0]
    assert board.item_ids == ("b", "a")
    assert [(p.start_mm, p.end_mm) for p in result.placements] == [
        (10.0, 51.0),
        (53.0, 93.0),
    ]
    assert board.separation_kerf_mm == 4
    assert board.remainder_mm == 0
    assert (
        board.start_trim_mm + board.end_trim_mm + board.occupied_length_mm
        == board.stock_length_mm
    )


def test_one_dimensional_packing_has_no_rotation_and_is_input_order_independent() -> (
    None
):
    blanks = [Blank("short", 30, "4x4"), Blank("long", 50, "4x4")]
    options = {"4x4": [100, 80]}
    first = nest_blanks(
        blanks,
        options,
        crosscut_kerf_mm=0,
        end_trim_start_mm=0,
        end_trim_end_mm=0,
    )
    second = nest_blanks(
        list(reversed(blanks)),
        options,
        crosscut_kerf_mm=0,
        end_trim_start_mm=0,
        end_trim_end_mm=0,
    )

    assert [(p.item_id, p.start_mm, p.end_mm) for p in first.placements] == [
        (p.item_id, p.start_mm, p.end_mm) for p in second.placements
    ]
    assert first.boards[0].stock_length_mm == 80
    assert first.boards[0].remainder_mm == 0
    assert all(p.end_mm - p.start_mm == p.blank_length_mm for p in first.placements)


def test_positive_tail_remainder_reserves_last_blank_separation_kerf() -> None:
    result = nest_blanks(
        [Blank("part", 70, "2x6")],
        {"2x6": 100},
        crosscut_kerf_mm=5,
        end_trim_start_mm=10,
        end_trim_end_mm=10,
    )

    board = result.boards[0]
    placement = result.placements[0]
    assert (placement.start_mm, placement.end_mm) == (10, 80)
    assert placement.separation_kerf_after_mm == 5
    assert (board.remainder_start_mm, board.remainder_end_mm, board.remainder_mm) == (
        85,
        90,
        5,
    )
    assert (
        board.start_trim_mm
        + board.end_trim_mm
        + board.blank_length_mm
        + board.separation_kerf_mm
        + board.remainder_mm
        == board.stock_length_mm
    )


def test_2500_mm_blank_fits_12_ft_stock_with_float_serialization() -> None:
    stock_length = 12 * 304.8
    result = nest_blanks(
        [Blank("frame", 2500, "2x6")],
        {"2x6": stock_length},
        crosscut_kerf_mm=3.2,
        end_trim_start_mm=10,
        end_trim_end_mm=10,
    )

    assert result.complete
    assert result.boards[0].stock_length_mm == stock_length
    assert result.placements[0].end_mm == pytest.approx(2510)
    assert result.boards[0].remainder_mm == pytest.approx(1134.4)


def test_8_ft_exact_boundary_fits_but_next_float_above_is_infeasible() -> None:
    stock_length = 8 * 304.8
    just_over = math.nextafter(stock_length, math.inf)
    result = nest_blanks(
        [
            Blank("exact", stock_length, "2x6"),
            Blank("too-long", just_over, "2x6"),
        ],
        {"2x6": stock_length},
        crosscut_kerf_mm=0,
        end_trim_start_mm=0,
        end_trim_end_mm=0,
    )

    assert [placement.item_id for placement in result.placements] == ["exact"]
    assert result.infeasible_item_ids == ("too-long",)


def test_residual_and_yield_totals_are_recorded() -> None:
    result = nest_blanks(
        [Blank("a", 40, "4x4"), Blank("b", 30, "4x4")],
        {"4x4": 100},
        crosscut_kerf_mm=2,
        end_trim_start_mm=5,
        end_trim_end_mm=5,
    )

    board = result.boards[0]
    totals = result.totals
    assert board.occupied_length_mm == 74
    assert board.remainder_mm == 16
    assert totals.requested_blank_count == totals.placed_blank_count == 2
    assert totals.blank_length_mm == 70
    assert totals.separation_kerf_mm == 4
    assert totals.remainder_mm == 16
    assert math.isclose(totals.length_yield_fraction, 0.7)


def test_overlength_items_are_reported_without_disappearing() -> None:
    result = nest_blanks(
        [Blank("too-long", 100, "4x6"), Blank("fits", 20, "4x6")],
        {"4x6": [50, 80]},
        crosscut_kerf_mm=2,
        end_trim_start_mm=10,
        end_trim_end_mm=10,
    )

    assert result.infeasible_item_ids == ("too-long",)
    assert [p.item_id for p in result.placements] == ["fits"]
    assert result.totals.requested_blank_count == 2
    assert result.totals.placed_blank_count == 1
    assert result.totals.infeasible_blank_count == 1
    assert not result.complete


def test_sections_do_not_mix_and_rip_metadata_does_not_change_remnant_section() -> None:
    result = nest_blanks(
        [
            Blank("ripped-a", 40, "4x6", rip_to_section=(83.9, 139.7)),
            Blank("ripped-b", 30, "4x6", rip_to_section=(88.9, 133.35)),
            Blank("full", 20, "4x6"),
            Blank("runner", 40, "2x6"),
        ],
        {"4x6": 120, "2x6": 100},
        crosscut_kerf_mm=2,
        end_trim_start_mm=5,
        end_trim_end_mm=5,
    )

    assert len(result.boards) == 2
    boards = {board.section: board for board in result.boards}
    assert boards["4x6"].item_ids == ("ripped-a", "ripped-b", "full")
    assert boards["4x6"].remainder_section == "4x6"
    assert boards["2x6"].item_ids == ("runner",)
    placements = {placement.item_id: placement for placement in result.placements}
    assert placements["ripped-a"].section == "4x6"
    assert placements["ripped-a"].rip_to_section == (83.9, 139.7)
    assert placements["ripped-b"].rip_to_section == (88.9, 133.35)
    assert placements["runner"].board_id != placements["ripped-a"].board_id


def test_empty_input_is_zero_boards_and_zero_totals() -> None:
    result = nest_blanks(
        [],
        {},
        crosscut_kerf_mm=0,
        end_trim_start_mm=0,
        end_trim_end_mm=0,
    )

    assert result.complete
    assert result.boards == result.placements == result.section_totals == ()
    assert result.totals.board_count == result.totals.requested_blank_count == 0
    assert result.totals.length_yield_fraction == 0


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate blank ID"):
        nest_blanks(
            [Blank("same", 10, "4x4"), Blank("same", 20, "4x4")],
            {"4x4": 100},
            crosscut_kerf_mm=0,
            end_trim_start_mm=0,
            end_trim_end_mm=0,
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1])
def test_invalid_blank_lengths_are_rejected(bad: float) -> None:
    with pytest.raises(ValueError):
        nest_blanks(
            [Blank("bad", bad, "4x4")],
            {"4x4": 100},
            crosscut_kerf_mm=0,
            end_trim_start_mm=0,
            end_trim_end_mm=0,
        )


@pytest.mark.parametrize(
    ("kerf", "start_trim", "end_trim"),
    [
        (float("nan"), 0, 0),
        (float("inf"), 0, 0),
        (-1, 0, 0),
        (0, float("nan"), 0),
        (0, 0, float("inf")),
        (0, -1, 0),
        (0, 0, -1),
    ],
)
def test_invalid_allowances_are_rejected(
    kerf: float, start_trim: float, end_trim: float
) -> None:
    with pytest.raises(ValueError):
        nest_blanks(
            [Blank("part", 10, "4x4")],
            {"4x4": 100},
            crosscut_kerf_mm=kerf,
            end_trim_start_mm=start_trim,
            end_trim_end_mm=end_trim,
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1])
def test_invalid_stock_lengths_are_rejected(bad: float) -> None:
    with pytest.raises(ValueError):
        nest_blanks(
            [Blank("part", 10, "4x4")],
            {"4x4": bad},
            crosscut_kerf_mm=0,
            end_trim_start_mm=0,
            end_trim_end_mm=0,
        )


def test_missing_section_stock_is_rejected() -> None:
    with pytest.raises(ValueError, match="no stock-length options"):
        nest_blanks(
            [Blank("part", 10, "2x6")],
            {"4x4": 100},
            crosscut_kerf_mm=0,
            end_trim_start_mm=0,
            end_trim_end_mm=0,
        )


@pytest.mark.parametrize(
    "dimensions",
    [
        (float("nan"), 2),
        (2, float("inf")),
        (-1, 2),
        (2, 0),
        (2,),
    ],
)
def test_invalid_prepared_rip_dimensions_are_rejected(
    dimensions: tuple[float, ...],
) -> None:
    with pytest.raises(ValueError):
        nest_blanks(
            [Blank("part", 10, "4x6", rip_to_section=dimensions)],
            {"4x6": 100},
            crosscut_kerf_mm=0,
            end_trim_start_mm=0,
            end_trim_end_mm=0,
        )


def test_zero_length_blank_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        nest_blanks(
            [Blank("zero", 0, "4x4")],
            {"4x4": 100},
            crosscut_kerf_mm=0,
            end_trim_start_mm=0,
            end_trim_end_mm=0,
        )
