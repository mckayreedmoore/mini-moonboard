"""Dimensional screen for the source-bound WJ-04 ordinary fastener candidate.

This checks product/standard geometry and a conditional receiving envelope. It
does not calculate fastener or wood capacity, torque, preload, or tool access.
Actual wood layers and catalog bounds come from ``WJ04_TRIAL``; this module
does not maintain a second copy of those dimensions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product

from mini_moonboard.wood_joint_wj04_config import (
    WJ04_TRIAL,
    BoltStackConfig,
    WJ04TrialConfig,
)

WOOD_CUT_ALLOWANCE_MM = 0.5
MAX_THREAD_BEARING_FRACTION = 0.25
RECEIVING_FULL_THREAD_PROJECTION_MM = 2.54


@dataclass(frozen=True)
class StackScreen:
    stack_id: str
    interface_id: str
    bolt_candidate_id: str
    bolt_sku: str
    layer_member_ids: tuple[str, ...]
    layer_grip_mm: tuple[float, ...]
    delivered_length_min_mm: float
    delivered_length_max_mm: float
    standard_body_min_mm: float
    standard_full_thread_start_max_mm: float
    nut_bearing_face_min_mm: float
    nut_far_face_max_mm: float
    tip_projection_min_mm: float
    max_thread_bearing_fractions: tuple[float, ...]
    body_end_min_for_fraction_mm: float
    receiving_body_end_min_mm: float
    receiving_full_thread_start_max_mm: float
    receiving_full_thread_end_min_mm: float
    standards_guarantee_limited_thread_bearing: bool
    standards_guarantee_nut_thread_start: bool
    standards_guarantee_full_form_thread_end: bool
    standards_guarantee_tip_projection: bool

    @property
    def standards_guarantee_nut_engagement(self) -> bool:
        return (
            self.standards_guarantee_nut_thread_start
            and self.standards_guarantee_full_form_thread_end
        )

    @property
    def standards_guarantee_stack(self) -> bool:
        return (
            self.standards_guarantee_limited_thread_bearing
            and self.standards_guarantee_nut_engagement
            and self.standards_guarantee_tip_projection
        )

    def receipt_transition_fits(
        self,
        body_end_mm: float,
        full_thread_start_mm: float,
        full_thread_end_mm: float,
        delivered_length_mm: float,
        *,
        functional_nut_engagement_verified: bool,
    ) -> bool:
        """Check measured lot bounds; the candidate itself does not promise them.

        Measurements are from the bolt's under-head bearing plane. The received
        full-form thread must start before the earliest nut-bearing plane and
        continue 2.54 mm past the far nut face. Tip length alone is insufficient.
        """
        values = (
            body_end_mm,
            full_thread_start_mm,
            full_thread_end_mm,
            delivered_length_mm,
        )
        if not all(math.isfinite(value) for value in values):
            return False
        if min(values) < 0:
            return False
        return (
            self.delivered_length_min_mm
            <= delivered_length_mm
            <= self.delivered_length_max_mm
            and body_end_mm >= self.receiving_body_end_min_mm
            and body_end_mm <= full_thread_start_mm
            and full_thread_start_mm <= self.receiving_full_thread_start_max_mm
            and full_thread_end_mm >= self.receiving_full_thread_end_min_mm
            and full_thread_end_mm <= delivered_length_mm
            and functional_nut_engagement_verified
        )


def _fraction_in_thread_bearing(
    body_end_mm: float,
    member_start_mm: float,
    member_thickness_mm: float,
) -> float:
    thread_bearing_mm = max(
        0.0,
        member_start_mm + member_thickness_mm - body_end_mm,
    )
    return min(1.0, thread_bearing_mm / member_thickness_mm)


def screen_stack(
    stack: BoltStackConfig,
    config: WJ04TrialConfig = WJ04_TRIAL,
    *,
    wood_cut_allowance_mm: float = WOOD_CUT_ALLOWANCE_MM,
    max_thread_bearing_fraction: float = MAX_THREAD_BEARING_FRACTION,
    receiving_full_thread_projection_mm: float = RECEIVING_FULL_THREAD_PROJECTION_MM,
) -> StackScreen:
    """Evaluate each independent layer, washer, and nut tolerance corner.

    The ``wood_cut_allowance_mm`` is a diagnostic input, not a stock or cut
    acceptance tolerance. The 1/4 thread-bearing fraction is an explicit
    screen threshold, not a resistance calculation.
    """
    if not math.isfinite(wood_cut_allowance_mm) or wood_cut_allowance_mm < 0:
        raise ValueError("wood cut allowance must be finite and nonnegative")
    if not 0 < max_thread_bearing_fraction < 1:
        raise ValueError("thread-bearing fraction must be between zero and one")
    if (
        not math.isfinite(receiving_full_thread_projection_mm)
        or receiving_full_thread_projection_mm < 0
    ):
        raise ValueError("receiving projection must be finite and nonnegative")
    if not stack.layers:
        raise ValueError("a bolt stack must contain actual wood layers")

    bolt = stack.hardware_candidate
    washer = config.fasteners.washer
    nut = config.fasteners.nut
    if config.fasteners.washers_per_stack != 2:
        raise ValueError("the ordinary WJ-04 stack requires two washers")

    washer_min, washer_max = washer.thickness_range_mm
    nut_min, nut_max = nut.thickness_range_mm
    if washer_min <= 0 or washer_max < washer_min or nut_min <= 0 or nut_max < nut_min:
        raise ValueError("invalid washer or nut thickness bounds")
    if bolt.length_minus_tolerance_mm < 0:
        raise ValueError("bolt length tolerance must be nonnegative")
    if bolt.minimum_smooth_body_mm > bolt.maximum_full_thread_start_mm:
        raise ValueError("bolt body/thread transition bounds are inconsistent")

    nominal_layers = tuple(layer.thickness_mm for layer in stack.layers)
    if any(
        not math.isfinite(thickness) or thickness <= wood_cut_allowance_mm
        for thickness in nominal_layers
    ):
        raise ValueError("every wood layer must exceed its cut allowance")
    layer_bounds = tuple(
        (thickness - wood_cut_allowance_mm, thickness + wood_cut_allowance_mm)
        for thickness in nominal_layers
    )
    washer_bounds = washer.thickness_range_mm

    # Locate each wood member from the head-side bearing plane at every
    # independent body/wood tolerance corner.
    fraction_corners: list[list[float]] = [[] for _ in stack.layers]
    body_end_min_for_fraction = 0.0
    for corner in product(washer_bounds, *layer_bounds):
        head_washer = corner[0]
        wood_corner = corner[1:]
        member_start = head_washer
        for index, member_thickness in enumerate(wood_corner):
            fraction_corners[index].append(
                _fraction_in_thread_bearing(
                    bolt.minimum_smooth_body_mm,
                    member_start,
                    member_thickness,
                )
            )
            body_end_min_for_fraction = max(
                body_end_min_for_fraction,
                member_start + (1 - max_thread_bearing_fraction) * member_thickness,
            )
            member_start += member_thickness

    layer_minima = tuple(bounds[0] for bounds in layer_bounds)
    layer_maxima = tuple(bounds[1] for bounds in layer_bounds)
    nut_bearing_face_min = washer_min + sum(layer_minima) + washer_min
    nut_far_face_max = washer_max + sum(layer_maxima) + washer_max + nut_max
    delivered_length_min = bolt.nominal_length_mm - bolt.length_minus_tolerance_mm
    delivered_length_max = bolt.nominal_length_mm
    tip_projection_min = delivered_length_min - nut_far_face_max

    fractions = tuple(max(corners) for corners in fraction_corners)
    receiving_body_end_min = max(
        bolt.minimum_smooth_body_mm,
        body_end_min_for_fraction,
    )

    return StackScreen(
        stack_id=stack.stack_id,
        interface_id=stack.interface_id,
        bolt_candidate_id=bolt.candidate_id,
        bolt_sku=bolt.sku,
        layer_member_ids=tuple(layer.member_id for layer in stack.layers),
        layer_grip_mm=nominal_layers,
        delivered_length_min_mm=delivered_length_min,
        delivered_length_max_mm=delivered_length_max,
        standard_body_min_mm=bolt.minimum_smooth_body_mm,
        standard_full_thread_start_max_mm=bolt.maximum_full_thread_start_mm,
        nut_bearing_face_min_mm=nut_bearing_face_min,
        nut_far_face_max_mm=nut_far_face_max,
        tip_projection_min_mm=tip_projection_min,
        max_thread_bearing_fractions=fractions,
        body_end_min_for_fraction_mm=body_end_min_for_fraction,
        receiving_body_end_min_mm=receiving_body_end_min,
        receiving_full_thread_start_max_mm=nut_bearing_face_min,
        receiving_full_thread_end_min_mm=(
            nut_far_face_max + receiving_full_thread_projection_mm
        ),
        standards_guarantee_limited_thread_bearing=(
            all(fraction <= max_thread_bearing_fraction for fraction in fractions)
        ),
        standards_guarantee_nut_thread_start=(
            bolt.maximum_full_thread_start_mm <= nut_bearing_face_min
        ),
        standards_guarantee_full_form_thread_end=bolt.full_form_thread_end_guaranteed,
        standards_guarantee_tip_projection=(
            tip_projection_min >= receiving_full_thread_projection_mm
        ),
    )


def report(config: WJ04TrialConfig = WJ04_TRIAL) -> tuple[StackScreen, ...]:
    """Return one screen per actual config stack, without a capacity result."""
    return tuple(screen_stack(stack, config) for stack in config.stacks)
