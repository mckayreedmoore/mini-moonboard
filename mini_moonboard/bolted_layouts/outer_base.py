"""LB-07F outer-rim/base AB90 prototype layout."""
from ..bolted_layout_common import family_fasteners, family_interfaces, family_machining, family_records
FAMILY = "outer_base"
records = lambda: family_records(FAMILY)
fasteners = lambda: family_fasteners(FAMILY)
interfaces = lambda: family_interfaces(FAMILY)
machining = lambda: family_machining(FAMILY)
