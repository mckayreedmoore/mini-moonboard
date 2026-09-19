"""Incomplete but explicit scaffold for the AB90 bolted candidate.

The scaffold preserves raw baseline geometry, twelve existing frame bolts, all
66 panel/kicker screws, and electrical datums. Structural AB90 family layouts
are intentionally absent until their physical stacks and access checks exist.
It must not be exported as a complete candidate.
"""

from functools import cache

from . import compact_floor_flush_frame as baseline
from .bolted_layouts import FAMILY_NAMES, registered_layouts
from .demountable_connections import ab90_prototype_fastener

KEY = "compact-floor-flush-bolted-development"
BASELINE_KEY = baseline.KEY
STATUS = "connection_development_unqualified_incomplete"
STRUCTURAL_LAYOUTS_REQUIRED = FAMILY_NAMES


class IncompleteCandidateError(RuntimeError):
    """Raised when a consumer asks the scaffold for a finished drilled model."""


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
    return (ab90_prototype_fastener(),)


def machining_records():
    return ()


def assembly_interface_records():
    return ()


def parts():
    """Reject finished-model consumers until all six families are registered."""
    missing = tuple(name for name in FAMILY_NAMES if name not in registered_layouts())
    raise IncompleteCandidateError(
        "Candidate is incomplete; missing structural layout families: " + ", ".join(missing))
