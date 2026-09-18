"""Official 4×4 vs 4×8 kerf-right width option for the selected floor-runner.

The selected analysis geometry stays the official Mini 4×4 pair. The kerf-right
option removes 1/8 in (3.175 mm) from the K-side overall width: right panels and
spanning members are trimmed at +X, and the outer-right stack translates inboard
so 4×6/2×6 sections stay full. Hold/T-nut/LED world X is unchanged. This is a
fabrication presentation, not a second native-case candidate.
"""
from dataclasses import replace

import cadquery as cq

from . import compact_floor_flush_frame as official

OFFICIAL = 'official'
KERF_RIGHT = 'kerf-right'
KERF_RIGHT_MM = 25.4 / 8
KERF_VIEWER_KEY = 'compact-floor-flush-kerf-right'
OPTIONS = (OFFICIAL, KERF_RIGHT)

# Outer-right members that keep their full section and move inboard with the new
# panel edge. Center-right posts/principals and inner-right clips stay put.
TRANSLATE_NAMES = frozenset({
    'lumber_leg_right', 'base_floor_right', 'base_side_right', 'base_post_outer_right',
    'clip_single_top_right_2', 'clip_timber_header_outer_right', 'clip_angle_base_right',
    'clip_horizontal_bottom_right_2', 'clip_horizontal_lower_right_2',
    'clip_horizontal_upper_right_2',
})

# Members that keep their -X/seam end and lose 1/8 in at +X.
TRIM_XMAX_NAMES = frozenset({
    'main_lower_right', 'main_upper_right', 'kicker_right',
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
    dx = trim_mm(option)
    if dx == 0. or part.name.startswith('hold_tnut_') or getattr(part, 'kind', None) in {
            'light', 'wire'}:
        return part
    if part.name in TRANSLATE_NAMES:
        return replace(part, shape=part.shape.translate((-dx, 0., 0.)))
    if part.name in TRIM_XMAX_NAMES:
        blank = part.blank
        return replace(part, shape=_cut_xmax(part.shape, dx),
                       blank=(blank[0] - dx, blank[1], blank[2]))
    return part


def transform_connection(connection, option):
    dx = trim_mm(option)
    if dx == 0. or not any(name in TRANSLATE_NAMES for name in connection.members):
        return connection
    return replace(connection, start=cq.Vector(
        connection.start.x - dx, connection.start.y, connection.start.z))


class WidthAdapter:
    """Same selected candidate with an optional K-side 1/8 in fabrication trim."""

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
    dx = KERF_RIGHT_MM
    official_wood = {p.name: p for p in source.uncut_wood_parts()}
    kerf_wood = {p.name: p for p in kerf.uncut_wood_parts()}
    left = official_wood['main_lower_left'].shape.BoundingBox()
    left_k = kerf_wood['main_lower_left'].shape.BoundingBox()
    right = official_wood['main_lower_right'].shape.BoundingBox()
    right_k = kerf_wood['main_lower_right'].shape.BoundingBox()
    rim = official_wood['base_side_right'].shape.BoundingBox()
    rim_k = kerf_wood['base_side_right'].shape.BoundingBox()
    header = official_wood['base_header'].shape.BoundingBox()
    header_k = kerf_wood['base_header'].shape.BoundingBox()
    leg = official_wood['lumber_leg_right'].shape.BoundingBox()
    leg_k = kerf_wood['lumber_leg_right'].shape.BoundingBox()
    official_xmax = max(p.shape.BoundingBox().xmax for p in official_wood.values())
    kerf_xmax = max(p.shape.BoundingBox().xmax for p in kerf_wood.values())
    official_bolts = {c.name: c for c in source.connections() if c.kind == 'bolt'}
    kerf_bolts = {c.name: c for c in kerf.connections() if c.kind == 'bolt'}
    rim_screws = [c for c in kerf.panel_connections() if c.members[1] == 'base_side_right']
    k_edge = right_k.xmax - 980.8
    failures = []
    if abs((left_k.xmin - left.xmin) + (left_k.xmax - left.xmax)) > 1e-6:
        failures.append('left panel moved')
    if abs((right.xmax - right_k.xmax) - dx) > 1e-4:
        failures.append('right panel trim is not 1/8 in')
    if abs(right_k.xmin - right.xmin) > 1e-4:
        failures.append('right panel seam moved')
    if abs(rim.xlen - rim_k.xlen) > 1e-4:
        failures.append('right rim section changed')
    if abs(leg.xlen - leg_k.xlen) > 1e-4:
        failures.append('right leg section changed')
    if abs((official_xmax - kerf_xmax) - dx) > 1e-3:
        failures.append('overall width is not 1/8 in smaller')
    if abs((header.xlen - header_k.xlen) - dx) > 1e-4:
        failures.append('header length is not 1/8 in shorter')
    if any(abs(kerf_bolts[name].grip - bolt.grip) > 1e-9 for name, bolt in official_bolts.items()):
        failures.append('bolt grip changed')
    if any(abs(kerf_bolts[name].start.x - bolt.start.x) > 1e-4
           for name, bolt in official_bolts.items() if name.endswith(('_left_1', '_left_2'))):
        failures.append('left bolts moved')
    if any(abs((bolt.start.x - kerf_bolts[name].start.x) - dx) > 1e-4
           for name, bolt in official_bolts.items() if '_right_' in name):
        failures.append('right outer bolts did not follow the 1/8 in trim')
    if any(abs((right_k.xmax - c.start.x) - 19.05) > 1e-3 for c in rim_screws):
        failures.append('right rim screws are not 19.05 mm from the new edge')
    if k_edge + 1e-6 < 235.0:
        failures.append('K-column T-nut edge distance below 235 mm')
    return {
        'option': KERF_RIGHT,
        'trim_mm': dx,
        'official_overall_xmax_mm': official_xmax,
        'kerf_overall_xmax_mm': kerf_xmax,
        'right_panel_width_mm': right_k.xlen,
        'left_panel_width_mm': left_k.xlen,
        'right_rim_thickness_mm': rim_k.xlen,
        'k_column_edge_mm': k_edge,
        'right_rim_screw_edge_mm': min(right_k.xmax - c.start.x for c in rim_screws),
        'passed': not failures,
        'failures': failures,
        'scope': ('Geometry presentation screen only. Six no-slip cases remain those of the '
                  'official 4×4 selected geometry; this is not a fabrication release.'),
    }
