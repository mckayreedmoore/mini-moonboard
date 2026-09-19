"""Incomplete but explicit scaffold for the AB90 bolted candidate.

The scaffold preserves raw baseline geometry, twelve existing frame bolts, all
66 panel/kicker screws, and electrical datums. Structural AB90 family layouts
are intentionally absent until their physical stacks and access checks exist.
It must not be exported as a complete candidate.
"""

import math
from dataclasses import dataclass
from functools import cache

from . import compact_floor_flush_frame as baseline
from .bolted_layouts import (
    FAMILY_NAMES,
    all_fasteners,
    all_interfaces,
    all_machining_records,
    registered_layouts,
)

KEY = "compact-floor-flush-bolted-development"
BASELINE_KEY = baseline.KEY
STATUS = "connection_development_unqualified_incomplete"
STRUCTURAL_LAYOUTS_REQUIRED = FAMILY_NAMES


class IncompleteCandidateError(RuntimeError):
    """Raised when a consumer asks the scaffold for a finished drilled model."""


@dataclass(frozen=True)
class ReportedExistingHole:
    """Owner-sourced structural bore for a future retrofit geometry check."""

    member_name: str
    entry_xyz_mm: tuple[float, float, float]
    direction_xyz: tuple[float, float, float]
    diameter_mm: float
    depth_mm: float
    source: str

    def __post_init__(self) -> None:
        if not self.member_name or not self.source:
            raise ValueError("existing hole needs member identity and evidence source")
        if len(self.entry_xyz_mm) != 3 or not all(math.isfinite(value) for value in self.entry_xyz_mm):
            raise ValueError("existing hole entry must be a finite 3-vector")
        if len(self.direction_xyz) != 3 or not all(math.isfinite(value) for value in self.direction_xyz):
            raise ValueError("existing hole direction must be a finite 3-vector")
        if sum(value * value for value in self.direction_xyz) <= 0:
            raise ValueError("existing hole direction must be nonzero")
        if not math.isfinite(self.diameter_mm) or self.diameter_mm <= 0:
            raise ValueError("existing hole diameter must be positive and finite")
        if not math.isfinite(self.depth_mm) or self.depth_mm <= 0:
            raise ValueError("existing hole depth must be positive and finite")


def candidate_metadata() -> dict[str, object]:
    return {
        "candidate": KEY,
        "baseline_candidate": BASELINE_KEY,
        "baseline_commit": "7cdd2e37ed2d364b47879a960b9eb15b93c67048",
        "handoff_revision": "v2-structural-only",
        "status": STATUS,
        "selected_as_repository_default": False,
        "conversion_scope": "structural_frame_screws_only",
        "structural_connector_schedule_status": "AB90 prototype; bolt basis unresolved",
        "panel_policy": "retain_existing_66_hillman_screws",
        "future_panel_inserts": "deferred_not_a_dependency",
        "structural_wood_thread_removals_per_move_target": 0,
        "panel_wood_thread_removals_per_move": "allowed_per_actual_sequence",
        "actual_structural_stock_condition": "owner_confirmation_pending",
        "geometry_checked": False,
        "new_native_cases_complete": False,
        "fabrication_release": False,
    }


@cache
def uncut_wood_parts():
    """Return baseline raw wood, before candidate machining is applied."""
    return baseline.uncut_wood_parts()


@cache
def panel_connections():
    return baseline.panel_connections()


@cache
def connections():
    """Retain only the twelve frame bolts and frozen panel connections."""
    panels = {connection.name for connection in panel_connections()}
    return tuple(connection for connection in baseline.connections()
                  if connection.kind == "bolt" or connection.name in panels)


def attachment_datums():
    return baseline.attachment_datums()


def electrical_parts():
    return baseline.electrical_parts()


def structural_joint_records():
    return tuple(record for layout in registered_layouts().values() for record in layout)


def fastener_stack_records():
    return all_fasteners()


def machining_records(existing_holes: tuple[ReportedExistingHole, ...] | None = None):
    """Keep reported retrofit bores distinct from proposed prototype machining."""
    records = all_machining_records()
    if existing_holes is None:
        return records
    structural_names = {part.name for part in uncut_wood_parts()
                        if not part.name.startswith(("main_", "kicker_"))}
    if any(not isinstance(hole, ReportedExistingHole) or hole.member_name not in structural_names
           for hole in existing_holes):
        raise ValueError("reported existing holes must belong to preserved structural timber")
    reported = tuple({
        "member_name": hole.member_name,
        "entry_xyz_mm": hole.entry_xyz_mm,
        "direction_xyz": hole.direction_xyz,
        "diameter_mm": hole.diameter_mm,
        "depth_mm": hole.depth_mm,
        "source": hole.source,
        "operation": "retain_reported_existing_bore_for_retrofit_check",
        "status": "reported_not_geometry_verified",
    } for hole in existing_holes)
    return records + reported


def assembly_interface_records():
    return all_interfaces()


def parts():
    """Reject finished-model consumers until mechanics and machining are accepted."""
    missing = tuple(name for name in FAMILY_NAMES if name not in registered_layouts())
    if not missing:
        missing = ("mechanics/resistance/access acceptance",)
    raise IncompleteCandidateError(
        "Candidate is incomplete; missing structural layout families: " + ", ".join(missing))
