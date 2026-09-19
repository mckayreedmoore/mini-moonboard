"""Family registration boundary for the bolted candidate.

Family modules are intentionally absent until their shared LB-05 API is frozen
and each layout has its own physical stack and access evidence.
"""

FAMILY_NAMES = (
    "top",
    "bottom",
    "service",
    "header_post",
    "center_base",
    "outer_base",
)


def registered_layouts() -> dict[str, object]:
    """Return implemented family layouts; an empty map is an explicit scaffold state."""
    return {}
