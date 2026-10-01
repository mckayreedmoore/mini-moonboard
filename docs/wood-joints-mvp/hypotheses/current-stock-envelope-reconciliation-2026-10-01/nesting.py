"""Deterministic one-dimensional stock-cut arithmetic for proposed blanks.

All distances are millimetres. ``section`` is the original stock/blank
cross-section class used for length nesting. ``rip_to_section`` stores the
prepared width/height in millimetres for a separate later operation; this
module does not perform that rip.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

SECTION_CLASSES = frozenset({"4x4", "4x6", "2x6"})
HEURISTIC = (
    "first-fit decreasing; minimum feasible nominal stock length for each new board"
)
# This absolute tolerance is only for validating emitted float records, never for packing.
_OUTPUT_SERIALIZATION_TOLERANCE = Decimal("1e-9")

type Number = int | float | Decimal
type StockLengthOptions = Number | Sequence[Number]
type PreparedSection = tuple[Number, Number]


@dataclass(frozen=True)
class Blank:
    """One proposed cut blank, before any optional section rip."""

    id: str
    length_mm: Number
    section: str
    rip_to_section: PreparedSection | None = None


@dataclass(frozen=True)
class Placement:
    """A blank's interval and its reserved trailing separation kerf."""

    item_id: str
    section: str
    rip_to_section: tuple[float, float] | None
    board_id: str
    board_length_mm: float
    start_mm: float
    end_mm: float
    blank_length_mm: float
    separation_kerf_after_mm: float
    sequence_in_board: int


@dataclass(frozen=True)
class Board:
    """One source-section stock board and its length-accounting record."""

    id: str
    section: str
    stock_length_mm: float
    start_trim_mm: float
    end_trim_mm: float
    item_ids: tuple[str, ...]
    blank_length_mm: float
    separation_kerf_mm: float
    occupied_length_mm: float
    remainder_start_mm: float
    remainder_end_mm: float
    remainder_mm: float
    remainder_section: str


@dataclass(frozen=True)
class SectionTotals:
    section: str
    requested_blank_count: int
    placed_blank_count: int
    infeasible_blank_count: int
    board_count: int
    stock_length_mm: float
    blank_length_mm: float
    start_trim_mm: float
    end_trim_mm: float
    separation_kerf_mm: float
    remainder_mm: float
    length_yield_fraction: float


@dataclass(frozen=True)
class NestingTotals:
    requested_blank_count: int
    placed_blank_count: int
    infeasible_blank_count: int
    board_count: int
    stock_length_mm: float
    blank_length_mm: float
    start_trim_mm: float
    end_trim_mm: float
    separation_kerf_mm: float
    remainder_mm: float
    length_yield_fraction: float


@dataclass(frozen=True)
class NestingResult:
    heuristic: str
    boards: tuple[Board, ...]
    placements: tuple[Placement, ...]
    infeasible_item_ids: tuple[str, ...]
    section_totals: tuple[SectionTotals, ...]
    totals: NestingTotals

    @property
    def complete(self) -> bool:
        return not self.infeasible_item_ids


@dataclass(frozen=True)
class _Item:
    id: str
    length: Decimal
    section: str
    rip_to_section: tuple[Decimal, Decimal] | None


@dataclass
class _BoardWork:
    id: str
    section: str
    stock_length: Decimal
    items: list[tuple[_Item, Decimal, Decimal]]
    blank_length: Decimal = Decimal(0)
    kerf_length: Decimal = Decimal(0)

    @property
    def occupied_length(self) -> Decimal:
        return self.blank_length + self.kerf_length


def _decimal(value: Number, name: str, *, strictly_positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{name} must be an int, float, or Decimal")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")
    if strictly_positive and parsed == 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


def _float(value: Decimal) -> float:
    return float(value)


def _length_options(
    stock_lengths_mm: Mapping[str, StockLengthOptions],
) -> dict[str, tuple[Decimal, ...]]:
    if not isinstance(stock_lengths_mm, Mapping):
        raise TypeError("stock_lengths_mm must map section classes to stock lengths")
    options: dict[str, tuple[Decimal, ...]] = {}
    for section, raw_options in stock_lengths_mm.items():
        if section not in SECTION_CLASSES:
            raise ValueError(f"unsupported stock section: {section!r}")
        if isinstance(raw_options, (int, float, Decimal)) and not isinstance(
            raw_options, bool
        ):
            values = (raw_options,)
        elif isinstance(raw_options, Sequence) and not isinstance(
            raw_options, (str, bytes)
        ):
            values = tuple(raw_options)
        else:
            raise TypeError(
                f"stock lengths for {section} must be a number or a sequence"
            )
        if not values:
            raise ValueError(f"stock lengths for {section} must not be empty")
        parsed = {
            _decimal(value, f"stock length for {section}", strictly_positive=True)
            for value in values
        }
        options[section] = tuple(sorted(parsed))
    return options


def _items(blanks: Sequence[Blank]) -> list[_Item]:
    if isinstance(blanks, (str, bytes)) or not isinstance(blanks, Sequence):
        raise TypeError("blanks must be a sequence of Blank rows")
    seen: set[str] = set()
    items: list[_Item] = []
    for blank in blanks:
        if not isinstance(blank, Blank):
            raise TypeError("every row must be a Blank")
        if not isinstance(blank.id, str) or not blank.id.strip():
            raise ValueError("blank IDs must be non-empty strings")
        if blank.id in seen:
            raise ValueError(f"duplicate blank ID: {blank.id}")
        seen.add(blank.id)
        if not isinstance(blank.section, str) or blank.section not in SECTION_CLASSES:
            raise ValueError(
                f"unsupported source section for {blank.id}: {blank.section!r}"
            )
        rip_to_section = None
        if blank.rip_to_section is not None:
            raw_dimensions = blank.rip_to_section
            if (
                isinstance(raw_dimensions, (str, bytes))
                or not isinstance(raw_dimensions, Sequence)
                or len(raw_dimensions) != 2
            ):
                raise ValueError(
                    f"rip target for {blank.id} must be a two-dimension (width, height) tuple"
                )
            rip_to_section = tuple(
                _decimal(value, f"rip dimension for {blank.id}", strictly_positive=True)
                for value in raw_dimensions
            )
        items.append(
            _Item(
                id=blank.id,
                length=_decimal(
                    blank.length_mm, f"length for {blank.id}", strictly_positive=True
                ),
                section=blank.section,
                rip_to_section=rip_to_section,
            )
        )
    return items


def nest_blanks(
    blanks: Sequence[Blank],
    stock_lengths_mm: Mapping[str, StockLengthOptions],
    *,
    crosscut_kerf_mm: Number,
    end_trim_start_mm: Number,
    end_trim_end_mm: Number,
) -> NestingResult:
    """Pack blanks into section-specific stock using declared linear allowances.

    End-trim allowances are the total length charged at each end, including
    that end trim's saw loss if the caller includes it in the declared value.
    The function separately reserves one ``crosscut_kerf_mm`` after *every*
    placed blank, including the final blank ahead of a positive tail remnant.
    This is deliberately conservative and keeps trim and separation losses
    visible as separate terms.

    Stock lengths are available options per original source section. Existing
    boards are tried in creation order; if none fits, the shortest declared
    stock option that fits is selected. This is a deterministic heuristic,
    not an optimization or purchase recommendation.

    Items that fit no declared option appear in ``infeasible_item_ids``. Other
    items are still packed, and every requested ID is either placed once or
    reported infeasible. An empty input yields no boards, zero totals, and a
    zero length-yield fraction.
    """

    kerf = _decimal(crosscut_kerf_mm, "crosscut_kerf_mm")
    start_trim = _decimal(end_trim_start_mm, "end_trim_start_mm")
    end_trim = _decimal(end_trim_end_mm, "end_trim_end_mm")
    options = _length_options(stock_lengths_mm)
    item_rows = _items(blanks)

    groups: dict[str, list[_Item]] = defaultdict(list)
    for item in item_rows:
        groups[item.section].append(item)
    for section in groups:
        if section not in options:
            raise ValueError(
                f"no stock-length options declared for source section {section}"
            )

    work_boards: list[_BoardWork] = []
    infeasible: list[str] = []
    for section in sorted(groups):
        section_boards: list[_BoardWork] = []
        ordered = sorted(groups[section], key=lambda item: (-item.length, item.id))
        for item in ordered:
            needed = item.length + kerf
            board = next(
                (
                    candidate
                    for candidate in section_boards
                    if candidate.occupied_length + needed
                    <= candidate.stock_length - start_trim - end_trim
                ),
                None,
            )
            if board is None:
                stock_length = next(
                    (
                        candidate_length
                        for candidate_length in options[section]
                        if needed <= candidate_length - start_trim - end_trim
                    ),
                    None,
                )
                if stock_length is None:
                    infeasible.append(item.id)
                    continue
                board_id = f"{section}-{len(section_boards) + 1:03d}"
                board = _BoardWork(
                    id=board_id,
                    section=section,
                    stock_length=stock_length,
                    items=[],
                )
                section_boards.append(board)
                work_boards.append(board)

            start = start_trim + board.occupied_length
            end = start + item.length
            board.items.append((item, start, end))
            board.blank_length += item.length
            board.kerf_length += kerf

    result = _make_result(
        item_rows,
        work_boards,
        infeasible,
        start_trim=start_trim,
        end_trim=end_trim,
        kerf=kerf,
    )
    validate_nesting_result(
        blanks,
        result,
        stock_lengths_mm=options,
        crosscut_kerf_mm=kerf,
        end_trim_start_mm=start_trim,
        end_trim_end_mm=end_trim,
    )
    return result


def _make_result(
    items: list[_Item],
    work_boards: list[_BoardWork],
    infeasible: list[str],
    *,
    start_trim: Decimal,
    end_trim: Decimal,
    kerf: Decimal,
) -> NestingResult:
    boards: list[Board] = []
    placements: list[Placement] = []
    for work in work_boards:
        cursor = start_trim
        for sequence, (item, start, end) in enumerate(work.items, start=1):
            if start != cursor:
                raise AssertionError(
                    "internal placement sequence lost length conservation"
                )
            placements.append(
                Placement(
                    item_id=item.id,
                    section=item.section,
                    rip_to_section=(
                        None
                        if item.rip_to_section is None
                        else (
                            _float(item.rip_to_section[0]),
                            _float(item.rip_to_section[1]),
                        )
                    ),
                    board_id=work.id,
                    board_length_mm=_float(work.stock_length),
                    start_mm=_float(start),
                    end_mm=_float(end),
                    blank_length_mm=_float(item.length),
                    separation_kerf_after_mm=_float(kerf),
                    sequence_in_board=sequence,
                )
            )
            cursor = end + kerf

        remainder_end = work.stock_length - end_trim
        remainder = remainder_end - cursor
        if remainder < 0:
            raise AssertionError("internal placement exceeds declared stock envelope")
        boards.append(
            Board(
                id=work.id,
                section=work.section,
                stock_length_mm=_float(work.stock_length),
                start_trim_mm=_float(start_trim),
                end_trim_mm=_float(end_trim),
                item_ids=tuple(item.id for item, _, _ in work.items),
                blank_length_mm=_float(work.blank_length),
                separation_kerf_mm=_float(work.kerf_length),
                occupied_length_mm=_float(work.occupied_length),
                remainder_start_mm=_float(cursor),
                remainder_end_mm=_float(remainder_end),
                remainder_mm=_float(remainder),
                remainder_section=work.section,
            )
        )

    item_by_id = {item.id: item for item in items}
    section_names = sorted({item.section for item in items})
    section_totals: list[SectionTotals] = []
    for section in section_names:
        section_boards = [board for board in boards if board.section == section]
        section_placements = [
            placement for placement in placements if placement.section == section
        ]
        section_infeasible = sum(
            item_by_id[item_id].section == section for item_id in infeasible
        )
        stock_sum = sum(
            (_d(board.stock_length_mm) for board in section_boards), Decimal(0)
        )
        blank_sum = sum((_d(p.blank_length_mm) for p in section_placements), Decimal(0))
        rem_sum = sum((_d(board.remainder_mm) for board in section_boards), Decimal(0))
        section_totals.append(
            SectionTotals(
                section=section,
                requested_blank_count=sum(item.section == section for item in items),
                placed_blank_count=len(section_placements),
                infeasible_blank_count=section_infeasible,
                board_count=len(section_boards),
                stock_length_mm=_float(stock_sum),
                blank_length_mm=_float(blank_sum),
                start_trim_mm=_float(start_trim * len(section_boards)),
                end_trim_mm=_float(end_trim * len(section_boards)),
                separation_kerf_mm=_float(
                    sum((_d(b.separation_kerf_mm) for b in section_boards), Decimal(0))
                ),
                remainder_mm=_float(rem_sum),
                length_yield_fraction=_fraction(blank_sum, stock_sum),
            )
        )

    requested_count = len(items)
    placed_count = len(placements)
    stock_total = sum((_d(board.stock_length_mm) for board in boards), Decimal(0))
    blank_total = sum((_d(p.blank_length_mm) for p in placements), Decimal(0))
    remainder_total = sum((_d(board.remainder_mm) for board in boards), Decimal(0))
    totals = NestingTotals(
        requested_blank_count=requested_count,
        placed_blank_count=placed_count,
        infeasible_blank_count=len(infeasible),
        board_count=len(boards),
        stock_length_mm=_float(stock_total),
        blank_length_mm=_float(blank_total),
        start_trim_mm=_float(start_trim * len(boards)),
        end_trim_mm=_float(end_trim * len(boards)),
        separation_kerf_mm=_float(
            sum((_d(board.separation_kerf_mm) for board in boards), Decimal(0))
        ),
        remainder_mm=_float(remainder_total),
        length_yield_fraction=_fraction(blank_total, stock_total),
    )
    return NestingResult(
        heuristic=HEURISTIC,
        boards=tuple(boards),
        placements=tuple(placements),
        infeasible_item_ids=tuple(sorted(infeasible)),
        section_totals=tuple(section_totals),
        totals=totals,
    )


def _d(value: float) -> Decimal:
    return Decimal(str(value))


def _fraction(numerator: Decimal, denominator: Decimal) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _serialized_matches(actual: float, expected: Decimal) -> bool:
    """Allow only float serialization error when checking a source Decimal."""

    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        return False
    if not math.isfinite(actual):
        return False
    emitted = Decimal(str(actual))
    return abs(emitted - expected) <= _OUTPUT_SERIALIZATION_TOLERANCE


def validate_nesting_result(
    blanks: Sequence[Blank],
    result: NestingResult,
    *,
    stock_lengths_mm: Mapping[str, StockLengthOptions],
    crosscut_kerf_mm: Number,
    end_trim_start_mm: Number,
    end_trim_end_mm: Number,
) -> None:
    """Raise ``AssertionError`` if placements or board balances are inconsistent.

    Float fields are checked against their Decimal inputs with an absolute
    1e-9 output-unit allowance for serialization only. Packing and fit decisions
    remain exact Decimal arithmetic.
    """

    normalized = _items(blanks)
    options = _length_options(stock_lengths_mm)
    item_by_id = {item.id: item for item in normalized}
    if len(item_by_id) != len(normalized):
        raise AssertionError("input IDs are not unique")
    kerf = _decimal(crosscut_kerf_mm, "crosscut_kerf_mm")
    start_trim = _decimal(end_trim_start_mm, "end_trim_start_mm")
    end_trim = _decimal(end_trim_end_mm, "end_trim_end_mm")
    infeasible = set(result.infeasible_item_ids)
    if len(infeasible) != len(result.infeasible_item_ids):
        raise AssertionError("infeasible IDs are duplicated")
    if not infeasible <= item_by_id.keys():
        raise AssertionError("infeasible IDs contain an unknown blank")

    placement_counts = Counter(placement.item_id for placement in result.placements)
    placed_ids = set(placement_counts)
    if any(count != 1 for count in placement_counts.values()):
        raise AssertionError("a blank is placed more than once")
    if placed_ids & infeasible:
        raise AssertionError("a blank is both placed and infeasible")
    if placed_ids | infeasible != item_by_id.keys():
        raise AssertionError("every blank must be placed once or reported infeasible")

    boards_by_id = {board.id: board for board in result.boards}
    if len(boards_by_id) != len(result.boards):
        raise AssertionError("board IDs are not unique")
    placements_by_board: dict[str, list[Placement]] = defaultdict(list)
    exact_placement_lengths: dict[str, Decimal] = {}
    for placement in result.placements:
        if placement.item_id not in item_by_id:
            raise AssertionError(f"unknown placed blank: {placement.item_id}")
        item = item_by_id[placement.item_id]
        if placement.section != item.section:
            raise AssertionError(f"section identity changed for {item.id}")
        if item.rip_to_section is None:
            if placement.rip_to_section is not None:
                raise AssertionError(f"rip metadata changed for {item.id}")
        elif (
            placement.rip_to_section is None
            or len(placement.rip_to_section) != 2
            or any(
                not _serialized_matches(actual, expected)
                for actual, expected in zip(
                    placement.rip_to_section, item.rip_to_section, strict=True
                )
            )
        ):
            raise AssertionError(f"rip metadata changed for {item.id}")
        if placement.board_id not in boards_by_id:
            raise AssertionError(f"unknown board for {item.id}")
        board = boards_by_id[placement.board_id]
        if board.section != item.section or board.remainder_section != item.section:
            raise AssertionError(f"source section changed on board {board.id}")
        if _d(placement.board_length_mm) != _d(board.stock_length_mm):
            raise AssertionError(f"stock length identity changed for {item.id}")
        if not _serialized_matches(placement.blank_length_mm, item.length):
            raise AssertionError(f"blank length identity changed for {item.id}")
        placements_by_board[placement.board_id].append(placement)
        exact_placement_lengths[item.id] = item.length

    exact_stock_by_board: dict[str, Decimal] = {}
    exact_remainder_by_board: dict[str, Decimal] = {}
    for board in result.boards:
        placements = sorted(
            placements_by_board.get(board.id, []),
            key=lambda placement: placement.sequence_in_board,
        )
        if not placements:
            raise AssertionError(f"unused board emitted: {board.id}")
        if tuple(p.item_id for p in placements) != board.item_ids:
            raise AssertionError(f"board identity list disagrees for {board.id}")
        if board.section not in options:
            raise AssertionError(f"missing stock options for {board.id}")
        matching_stock = [
            option
            for option in options[board.section]
            if _serialized_matches(board.stock_length_mm, option)
        ]
        if len(matching_stock) != 1:
            raise AssertionError(f"stock length identity is invalid for {board.id}")
        stock = matching_stock[0]
        exact_stock_by_board[board.id] = stock
        if not _serialized_matches(
            board.start_trim_mm, start_trim
        ) or not _serialized_matches(board.end_trim_mm, end_trim):
            raise AssertionError(f"trim allowance changed for {board.id}")
        cursor = start_trim
        blank_sum = Decimal(0)
        for sequence, placement in enumerate(placements, start=1):
            if placement.sequence_in_board != sequence:
                raise AssertionError(f"placement sequence is invalid for {board.id}")
            if not _serialized_matches(placement.start_mm, cursor):
                raise AssertionError(
                    f"placement start is invalid for {placement.item_id}"
                )
            item = item_by_id[placement.item_id]
            end = cursor + item.length
            if not _serialized_matches(placement.end_mm, end):
                raise AssertionError(
                    f"placement end is invalid for {placement.item_id}"
                )
            if not _serialized_matches(placement.separation_kerf_after_mm, kerf):
                raise AssertionError(
                    f"separation kerf is invalid for {placement.item_id}"
                )
            blank_sum += item.length
            cursor = end + kerf

        remainder_end = stock - end_trim
        remainder = remainder_end - cursor
        kerf_sum = kerf * len(placements)
        occupied = blank_sum + kerf_sum
        if remainder < 0:
            raise AssertionError(f"negative remainder for {board.id}")
        if not _serialized_matches(
            board.remainder_start_mm, cursor
        ) or not _serialized_matches(board.remainder_end_mm, remainder_end):
            raise AssertionError(f"remainder interval is invalid for {board.id}")
        if not _serialized_matches(board.remainder_mm, remainder):
            raise AssertionError(f"remainder length is invalid for {board.id}")
        if not _serialized_matches(board.blank_length_mm, blank_sum):
            raise AssertionError(f"blank total is invalid for {board.id}")
        if not _serialized_matches(board.separation_kerf_mm, kerf_sum):
            raise AssertionError(f"kerf total is invalid for {board.id}")
        if not _serialized_matches(board.occupied_length_mm, occupied):
            raise AssertionError(f"occupied length is invalid for {board.id}")
        if start_trim + end_trim + occupied + remainder != stock:
            raise AssertionError(f"stock length does not conserve for {board.id}")
        exact_remainder_by_board[board.id] = remainder

    if result.heuristic != HEURISTIC:
        raise AssertionError("heuristic label is invalid")
    placed_length = sum(exact_placement_lengths.values(), Decimal(0))
    stock_length = sum(exact_stock_by_board.values(), Decimal(0))
    start_trim_total = start_trim * len(result.boards)
    end_trim_total = end_trim * len(result.boards)
    kerf_total = kerf * len(result.placements)
    remainder_total = sum(exact_remainder_by_board.values(), Decimal(0))
    expected_totals = (
        ("requested blank count", result.totals.requested_blank_count, len(normalized)),
        (
            "placed blank count",
            result.totals.placed_blank_count,
            len(result.placements),
        ),
        (
            "infeasible blank count",
            result.totals.infeasible_blank_count,
            len(infeasible),
        ),
        ("board count", result.totals.board_count, len(result.boards)),
        ("stock length", result.totals.stock_length_mm, stock_length),
        ("blank length", result.totals.blank_length_mm, placed_length),
        ("start trim", result.totals.start_trim_mm, start_trim_total),
        ("end trim", result.totals.end_trim_mm, end_trim_total),
        ("separation kerf", result.totals.separation_kerf_mm, kerf_total),
        ("remainder", result.totals.remainder_mm, remainder_total),
    )
    for label, actual, expected in expected_totals:
        matches = (
            actual == expected
            if isinstance(actual, int)
            else _serialized_matches(actual, expected)
        )
        if not matches:
            raise AssertionError(f"aggregate {label} is invalid")
    expected_yield = Decimal(str(_fraction(placed_length, stock_length)))
    if not _serialized_matches(result.totals.length_yield_fraction, expected_yield):
        raise AssertionError("aggregate length-yield fraction is invalid")

    section_by_name = {summary.section: summary for summary in result.section_totals}
    expected_sections = {item.section for item in normalized}
    if (
        len(section_by_name) != len(result.section_totals)
        or set(section_by_name) != expected_sections
    ):
        raise AssertionError("section totals do not match source-section identities")
    for section in expected_sections:
        summary = section_by_name[section]
        section_items = [item for item in normalized if item.section == section]
        section_placements = [p for p in result.placements if p.section == section]
        section_boards = [board for board in result.boards if board.section == section]
        section_infeasible = sum(item.id in infeasible for item in section_items)
        section_stock = sum(
            (exact_stock_by_board[board.id] for board in section_boards), Decimal(0)
        )
        section_blank = sum(
            (item_by_id[p.item_id].length for p in section_placements), Decimal(0)
        )
        section_start_trim = start_trim * len(section_boards)
        section_end_trim = end_trim * len(section_boards)
        section_kerf = kerf * len(section_placements)
        section_remainder = sum(
            (exact_remainder_by_board[board.id] for board in section_boards),
            Decimal(0),
        )
        section_checks = (
            (
                "requested blank count",
                summary.requested_blank_count,
                len(section_items),
            ),
            ("placed blank count", summary.placed_blank_count, len(section_placements)),
            (
                "infeasible blank count",
                summary.infeasible_blank_count,
                section_infeasible,
            ),
            ("board count", summary.board_count, len(section_boards)),
            ("stock length", summary.stock_length_mm, section_stock),
            ("blank length", summary.blank_length_mm, section_blank),
            ("start trim", summary.start_trim_mm, section_start_trim),
            ("end trim", summary.end_trim_mm, section_end_trim),
            ("separation kerf", summary.separation_kerf_mm, section_kerf),
            ("remainder", summary.remainder_mm, section_remainder),
        )
        for label, actual, expected in section_checks:
            matches = (
                actual == expected
                if isinstance(actual, int)
                else _serialized_matches(actual, expected)
            )
            if not matches:
                raise AssertionError(f"{section} {label} is invalid")
        expected_yield = Decimal(str(_fraction(section_blank, section_stock)))
        if not _serialized_matches(summary.length_yield_fraction, expected_yield):
            raise AssertionError(f"{section} length-yield fraction is invalid")
