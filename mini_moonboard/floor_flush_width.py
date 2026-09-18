"""Official 4×4 vs 4×8 shared-kerf width option for the selected floor-runner.

The selected analysis geometry stays the official Mini 4×4 pair. The kerf
option models ripping a 4×8 with a 1/8 in kerf split equally: both face panels
are 1/16 in narrower and the same width. Moon hold/drill stations stay on the
official world-X layout measured from the assembled lower-left, so the missing
1/8 in sits at the K / right outer edge. The A / left outer face stays.
4×6/2×6 sections stay full. This is a fabrication presentation, not a second
native-case candidate.
"""
from dataclasses import replace

import cadquery as cq

from . import compact_floor_flush_frame as official

OFFICIAL = 'official'
KERF_RIGHT = 'kerf-right'
KERF_RIGHT_MM = 25.4 / 8
KERF_EACH_MM = 25.4 / 16
KERF_VIEWER_KEY = 'compact-floor-flush-kerf-right'
OPTIONS = (OFFICIAL, KERF_RIGHT)

# Outer-right stack moves inboard with the new K-side panel edge.
TRANSLATE_NAMES = frozenset({
    'lumber_leg_right', 'base_floor_right', 'base_side_right', 'base_post_outer_right',
    'clip_single_top_right_2', 'clip_timber_header_outer_right', 'clip_angle_base_right',
    'clip_horizontal_bottom_right_2', 'clip_horizontal_lower_right_2',
    'clip_horizontal_upper_right_2',
})

LEFT_PANEL_NAMES = frozenset({
    'main_lower_left', 'main_upper_left', 'kicker_left',
})
RIGHT_PANEL_NAMES = frozenset({
    'main_lower_right', 'main_upper_right', 'kicker_right',
})
# Header, top rail and right half-rails lose 1/8 in at +X so they still meet the
# translated right rim. Left half-rails and the A-side outer stack stay.
TRIM_XMAX_NAMES = frozenset({
    'base_header', 'base_rail_top',
    'base_rail_bottom_right', 'base_rail_service_lower_right', 'base_rail_service_upper_right',
})


def require_option(option):
    if option not in OPTIONS:
        raise ValueError(f'Width option must be {OFFICIAL} or {KERF_RIGHT}')
    return option


def trim_mm(option):
    return KERF_RIGHT_MM if require_option(option) == KERF_RIGHT else 0.


def _cut_xmax(shape, dx):
    bounds = shape.BoundingBox()
    cutter = cq.Solid.makeBox(
        dx + 2., bounds.ylen + 2., bounds.zlen + 2.,
        cq.Vector(bounds.xmax - dx, bounds.ymin - 1., bounds.zmin - 1.))
    return shape.cut(cutter).clean()


def transform_part(part, option):
    total = trim_mm(option)
    each = KERF_EACH_MM
    if total == 0. or part.name.startswith('hold_tnut_') or getattr(part, 'kind', None) in {
            'light', 'wire'}:
        return part
    if part.name in TRANSLATE_NAMES:
        return replace(part, shape=part.shape.translate((-total, 0., 0.)))
    blank = part.blank
    if part.name in LEFT_PANEL_NAMES:
        return replace(part, shape=_cut_xmax(part.shape, each),
                       blank=(blank[0] - each, blank[1], blank[2]))
    if part.name in RIGHT_PANEL_NAMES:
        shape = part.shape.translate((-each, 0., 0.))
        shape = _cut_xmax(shape, each)
        return replace(part, shape=shape, blank=(blank[0] - each, blank[1], blank[2]))
    if part.name in TRIM_XMAX_NAMES:
        return replace(part, shape=_cut_xmax(part.shape, total),
                       blank=(blank[0] - total, blank[1], blank[2]))
    return part


def transform_connection(connection, option):
    total = trim_mm(option)
    if total == 0. or not any(name in TRANSLATE_NAMES for name in connection.members):
        return connection
    return replace(connection, start=cq.Vector(
        connection.start.x - total, connection.start.y, connection.start.z))


class WidthAdapter:
    """Same selected candidate with equal 1/16 in panels and 1/8 in off the K-side."""

    def __init__(self, option):
        self.option = require_option(option)
        self.source = official

    @property
    def KEY(self):
        return KERF_VIEWER_KEY if self.option == KERF_RIGHT else official.KEY

    def __getattr__(self, name):
        return getattr(self.source, name)

    def uncut_wood_parts(self):
        return tuple(transform_part(part, self.option) for part in self.source.uncut_wood_parts())

    def parts(self):
        return tuple(transform_part(part, self.option) for part in self.source.parts())

    def connections(self):
        return tuple(transform_connection(c, self.option) for c in self.source.connections())

    def panel_connections(self):
        names = {c.name for c in self.source.panel_connections()}
        return tuple(c for c in self.connections() if c.name in names)

    def attachment_datums(self):
        xs = {c.name: c.start.x for c in self.panel_connections()}
        return tuple({**row, 'x': xs[row['name']]} for row in self.source.attachment_datums())

    def electrical_parts(self):
        return self.source.electrical_parts()


def variant(option=OFFICIAL):
    option = require_option(option)
    return WidthAdapter(option) if option == KERF_RIGHT else official


def geometry_screen(kerf=None, source=None):
    """Cheap fabrication-option checks. Not a six-case resistance result."""
    source = official if source is None else source
    kerf = WidthAdapter(KERF_RIGHT) if kerf is None else kerf
    total = KERF_RIGHT_MM
    each = KERF_EACH_MM
    official_wood = {p.name: p for p in source.uncut_wood_parts()}
    kerf_wood = {p.name: p for p in kerf.uncut_wood_parts()}
    left = official_wood['main_lower_left'].shape.BoundingBox()
    left_k = kerf_wood['main_lower_left'].shape.BoundingBox()
    right = official_wood['main_lower_right'].shape.BoundingBox()
    right_k = kerf_wood['main_lower_right'].shape.BoundingBox()
    left_rim = official_wood['base_side_left'].shape.BoundingBox()
    left_rim_k = kerf_wood['base_side_left'].shape.BoundingBox()
    right_rim = official_wood['base_side_right'].shape.BoundingBox()
    right_rim_k = kerf_wood['base_side_right'].shape.BoundingBox()
    header = official_wood['base_header'].shape.BoundingBox()
    header_k = kerf_wood['base_header'].shape.BoundingBox()
    official_xmin = min(p.shape.BoundingBox().xmin for p in official_wood.values())
    official_xmax = max(p.shape.BoundingBox().xmax for p in official_wood.values())
    kerf_xmin = min(p.shape.BoundingBox().xmin for p in kerf_wood.values())
    kerf_xmax = max(p.shape.BoundingBox().xmax for p in kerf_wood.values())
    official_bolts = {c.name: c for c in source.connections() if c.kind == 'bolt'}
    kerf_bolts = {c.name: c for c in kerf.connections() if c.kind == 'bolt'}
    left_screws = [c for c in kerf.panel_connections() if c.members[1] == 'base_side_left']
    right_screws = [c for c in kerf.panel_connections() if c.members[1] == 'base_side_right']
    failures = []
    if abs(left_k.xlen - (1219.2 - each)) > 1e-4 or abs(right_k.xlen - (1219.2 - each)) > 1e-4:
        failures.append('panels are not equal 1/16 in-narrow widths')
    if abs(left_k.xlen - right_k.xlen) > 1e-4:
        failures.append('left and right panels differ in width')
    if abs(left_k.xmin - left.xmin) > 1e-4:
        failures.append('left outer edge moved')
    if abs((right.xmax - right_k.xmax) - total) > 1e-4:
        failures.append('right outer edge is not 1/8 in inboard')
    if abs(left_k.xmax + each) > 1e-3:
        failures.append('panel seam is not 1/16 in toward A')
    if abs(left_rim_k.xlen - left_rim.xlen) > 1e-4 or abs(right_rim_k.xlen - right_rim.xlen) > 1e-4:
        failures.append('rim section changed')
    if abs((left_rim_k.xmin - left_rim.xmin) + (left_rim_k.xmax - left_rim.xmax)) > 1e-4:
        failures.append('left rim moved')
    if abs(((official_xmax - official_xmin) - (kerf_xmax - kerf_xmin)) - total) > 1e-3:
        failures.append('overall width is not 1/8 in smaller')
    if abs((header.xlen - header_k.xlen) - total) > 1e-4:
        failures.append('header length is not 1/8 in shorter')
    if any(abs(kerf_bolts[name].grip - bolt.grip) > 1e-9 for name, bolt in official_bolts.items()):
        failures.append('bolt grip changed')
    if any(abs(kerf_bolts[name].start.x - bolt.start.x) > 1e-4
           for name, bolt in official_bolts.items() if name.endswith(('_left_1', '_left_2'))):
        failures.append('left bolts moved')
    if any(abs((bolt.start.x - kerf_bolts[name].start.x) - total) > 1e-4
           for name, bolt in official_bolts.items() if '_right_' in name):
        failures.append('right outer bolts did not follow the 1/8 in K-side shift')
    if any(abs((c.start.x - left_k.xmin) - 19.05) > 1e-3 for c in left_screws):
        failures.append('left rim screws moved relative to the A-side edge')
    if any(abs((right_k.xmax - c.start.x) - 19.05) > 1e-3 for c in right_screws):
        failures.append('right rim screws are not 19.05 mm from the new K-side edge')
    return {
        'option': KERF_RIGHT,
        'trim_mm': total,
        'each_panel_trim_mm': each,
        'official_overall_width_mm': official_xmax - official_xmin,
        'kerf_overall_width_mm': kerf_xmax - kerf_xmin,
        'right_panel_width_mm': right_k.xlen,
        'left_panel_width_mm': left_k.xlen,
        'right_rim_thickness_mm': right_rim_k.xlen,
        'seam_x_mm': left_k.xmax,
        'k_column_edge_mm': right_k.xmax - 980.8,
        'right_rim_screw_edge_mm': min(right_k.xmax - c.start.x for c in right_screws),
        'passed': not failures,
        'failures': failures,
        'scope': ('Geometry presentation screen only. Six no-slip cases remain those of the '
                  'official 4×4 selected geometry; this is not a fabrication release.'),
    }
