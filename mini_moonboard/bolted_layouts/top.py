"""LB-07A top-rail AB90 prototype layout."""
from ..bolted_layout_common import (
    family_fasteners,
    family_interfaces,
    family_machining,
    family_records,
)

FAMILY = "top"
records = lambda: family_records(FAMILY)
fasteners = lambda: family_fasteners(FAMILY)
interfaces = lambda: family_interfaces(FAMILY)
machining = lambda: family_machining(FAMILY)
