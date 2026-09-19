"""Family registration boundary for the bolted candidate.

Family modules are intentionally absent until their shared LB-05 API is frozen
and each layout has its own physical stack and access evidence.
"""

from ..bolted_layout_common import (
    FAMILY_STATIONS,
    family_fasteners,
    family_interfaces,
    family_machining,
    family_records,
)

FAMILY_NAMES = tuple(FAMILY_STATIONS)


def registered_layouts() -> dict[str, object]:
    """Return all six current prototype family records."""
    return {family: family_records(family) for family in FAMILY_NAMES}


def all_fasteners():
    return tuple(fastener for family in FAMILY_NAMES for fastener in family_fasteners(family))


def all_interfaces():
    return tuple(interface for family in FAMILY_NAMES for interface in family_interfaces(family))


def all_machining_records():
    return tuple(record for family in FAMILY_NAMES for record in family_machining(family))
