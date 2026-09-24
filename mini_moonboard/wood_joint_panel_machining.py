"""Candidate-only panel machining for the shared-kerf WJ-03 model.

The source kerf adapter translates right panels and some right receiver axes
by different amounts. This adapter rebuilds only the right panels from their
candidate outlines, restores the fixed hold/LED grid, then cuts the exact
kerf-right panel-connection axes. It does not change the selected baseline or
the shared width producer.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import base_frame, insert_frame
from . import floor_flush_width as width
from . import panel_grid_v2 as grid

KERF_RIGHT = width.KERF_RIGHT

RIGHT_PANEL_NAMES = frozenset(
    {
        "main_lower_right",
        "main_upper_right",
        "kicker_right",
    }
)
PANEL_NAMES = RIGHT_PANEL_NAMES | frozenset(
    {
        "main_lower_left",
        "main_upper_left",
        "kicker_left",
    }
)
PANEL_CONNECTION_COUNT = 66
_DATUM_TOLERANCE_MM = 1e-7


def _part_map(parts: Iterable, description: str) -> dict:
    result = {}
    for part in parts:
        if part.name in result:
            raise ValueError(f"Duplicate {description} part: {part.name}")
        result[part.name] = part
    return result


@cache
def _base_grid_cut_volumes() -> tuple[
    dict[str, cq.Shape], dict[str, cq.Shape], dict[str, cq.Shape], dict[str, cq.Shape]
]:
    """Return fixed cutters, displaced-only plugs and shifted panel outlines.

    The base producer is the authority for those exact feature diameters and
    axes. Its raw-to-drilled difference gives the exact hold/LED openings.
    Applying the shared width transform gives the inherited openings to plug
    before recutting those features at their fixed world datums.
    """
    raw = _part_map(base_frame.parts(drilled=False), "undrilled base")
    drilled = _part_map(base_frame.parts(drilled=True), "drilled base")
    missing = RIGHT_PANEL_NAMES - raw.keys() | RIGHT_PANEL_NAMES - drilled.keys()
    if missing:
        raise ValueError(f"Base grid source is missing panels: {sorted(missing)}")
    fixed = {}
    inherited = {}
    displaced = {}
    outlines = {}
    for name in sorted(RIGHT_PANEL_NAMES):
        fixed[name] = raw[name].shape.cut(drilled[name].shape).clean()
        shifted_raw = width.transform_part(raw[name], KERF_RIGHT).shape
        shifted_drilled = width.transform_part(drilled[name], KERF_RIGHT).shape
        inherited[name] = shifted_raw.cut(shifted_drilled).clean()
        displaced[name] = inherited[name].cut(fixed[name]).clean()
        outlines[name] = shifted_raw
    return fixed, inherited, displaced, outlines


def _main_panel_translation(model, panel_name: str) -> cq.Vector:
    source_half = base_frame.b.HALF
    candidate_half = model.b.HALF
    if not math.isclose(source_half, candidate_half, abs_tol=_DATUM_TOLERANCE_MM):
        raise ValueError("Source and candidate panel widths differ")
    for x, s in grid.main_tnut_datums().values():
        side = "left" if x < source_half else "right"
        band = "lower" if s < source_half else "upper"
        if f"main_{band}_{side}" != panel_name:
            continue
        source = base_frame.b.point(x - source_half, s, 0.0)
        candidate = model.b.point(x - candidate_half, s, 0.0)
        return candidate - source
    raise ValueError(f"No main-grid datum belongs to {panel_name}")


def _kicker_panel_translation(model, panel_name: str) -> cq.Vector:
    source_half = base_frame.b.HALF
    candidate_half = model.b.HALF
    if not math.isclose(source_half, candidate_half, abs_tol=_DATUM_TOLERANCE_MM):
        raise ValueError("Source and candidate panel widths differ")
    for x, z in grid.kicker_foothold_datums().values():
        side = "left" if x < source_half else "right"
        if f"kicker_{side}" != panel_name:
            continue
        source = cq.Vector(
            x - source_half,
            base_frame.HEADER_FRONT_Y,
            base_frame.b.V1_KICKER_HEIGHT_MM + z,
        )
        candidate = cq.Vector(
            x - candidate_half,
            model.base.HEADER_FRONT_Y,
            model.b.V1_KICKER_HEIGHT_MM + z,
        )
        return candidate - source
    raise ValueError(f"No kicker hold datum belongs to {panel_name}")


def _panel_connection_cutters(connection) -> tuple[cq.Shape, ...]:
    """Return the panel cut geometry used by the active panel producers."""
    panel_name = connection.members[0]
    components = connection.components()
    if len(components) != 2:
        raise ValueError(
            f"Panel screw needs shaft and head components: {connection.name}"
        )
    shaft, head = components
    if panel_name.startswith("main_"):
        # Same clearance bore and head-envelope convention as insert_frame /
        # wide_frame. Use the producer's assumptions instead of new dimensions.
        bore = cq.Solid.makeCylinder(
            insert_frame.ASSUMPTIONS["panel_clearance_bore_diameter"] / 2.0,
            insert_frame.PANEL + 2.0,
            connection.start - connection.direction,
            connection.direction,
        )
        return bore, head
    if panel_name.startswith("kicker_"):
        # compact_spliced_kicker rebuilds kicker panels from shaft + head.
        return shaft, head
    raise ValueError(f"Unsupported panel connection owner: {panel_name}")


def candidate_panel_replacements(
    model,
    *,
    current_parts: Iterable,
    uncut_parts: Iterable,
) -> dict:
    """Return replacement solids for the three kerf-right panels.

    The model must be the existing WidthAdapter(KERF_RIGHT). Pass its already
    built parts() and uncut_wood_parts() to avoid rebuilding the candidate.
    Returned parts retain metadata from current_parts; their shapes come from
    the exact transformed, uncut candidate outlines.
    """
    if getattr(model, "option", None) != KERF_RIGHT:
        raise ValueError("Panel remachining requires the kerf-right candidate")

    current = _part_map(current_parts, "current candidate")
    raw = _part_map(uncut_parts, "uncut candidate")
    missing = RIGHT_PANEL_NAMES - current.keys() | RIGHT_PANEL_NAMES - raw.keys()
    if missing:
        raise ValueError(f"Candidate is missing right panels: {sorted(missing)}")

    connections = tuple(model.panel_connections())
    if len(connections) != PANEL_CONNECTION_COUNT:
        raise ValueError(
            f"Expected {PANEL_CONNECTION_COUNT} kerf-right panel axes; got {len(connections)}"
        )
    connection_names = [connection.name for connection in connections]
    if len(set(connection_names)) != PANEL_CONNECTION_COUNT:
        raise ValueError("Kerf-right panel connection names must be unique")
    for connection in connections:
        if not connection.members or connection.members[0] not in PANEL_NAMES:
            raise ValueError(f"Connection is not owned by a panel: {connection.name}")

    fixed_grid_cut_volumes, _, displaced_grid_plugs, shifted_panel_outlines = (
        _base_grid_cut_volumes()
    )
    replacements = {}
    for name in sorted(RIGHT_PANEL_NAMES):
        if name.startswith("main_"):
            translation = _main_panel_translation(model, name)
        else:
            # Kicker datums use the candidate kicker height and rear face,
            # which can differ from the main-panel frame transform.
            translation = _kicker_panel_translation(model, name)

        # `uncut_wood_parts` already carries grid holes; the width adapter
        # moved those with the panel. Restore only their displaced crescents,
        # clipped to the shared uncut panel outline, then cut fixed datums.
        candidate_outline = shifted_panel_outlines[name].translate(translation)
        displaced_plug = displaced_grid_plugs[name].translate(translation)
        displaced_plug = displaced_plug.intersect(candidate_outline).clean()
        shape = raw[name].shape.fuse(displaced_plug).clean()
        shape = shape.cut(fixed_grid_cut_volumes[name].translate(translation))
        for connection in connections:
            if connection.members[0] != name:
                continue
            for cutter in _panel_connection_cutters(connection):
                shape = shape.cut(cutter)
        replacements[name] = replace(current[name], shape=shape.clean())
    return replacements
