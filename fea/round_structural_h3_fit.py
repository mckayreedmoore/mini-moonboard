"""Necessary H3 mounting screen; no guessed holes or detailed connector solid.

Reject a standard vertical-uplift placement if its entire rear wing envelope
cannot reach the rim, or its front receiver is completely covered by plywood.
A successful necessary check would not establish actual product fit/resistance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

REFERENCE = Path('docs/h3-geometry-reference.json')


def necessary_screen(*, rear_gap_mm, wing_reach_mm, front_layer_mm3,
                     front_panel_intersection_mm3):
    """Finite geometric obstructions, independent of fastener allocation."""
    values = (rear_gap_mm, wing_reach_mm, front_layer_mm3, front_panel_intersection_mm3)
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError('Require finite nonnegative geometric measurements')
    if wing_reach_mm <= 0 or front_layer_mm3 <= 0:
        raise ValueError('Require positive connector reach and receiver layer')
    if front_panel_intersection_mm3 > front_layer_mm3 + 1.e-4:
        raise ValueError('Panel intersections overlap or exceed the receiver layer')
    rear_rejected = rear_gap_mm > wing_reach_mm + 1.e-6
    front_rejected = abs(front_layer_mm3-front_panel_intersection_mm3) <= 1.e-4
    return {
        'rear_standard_mount_rejected': rear_rejected,
        'rear_nominal_reach_shortfall_mm': max(0., rear_gap_mm-wing_reach_mm),
        'front_standard_mount_rejected': front_rejected,
        'front_receiver_covered_fraction': front_panel_intersection_mm3/front_layer_mm3,
        'all_standard_vertical_uplift_mounts_rejected': rear_rejected and front_rejected,
        'actual_hole_pattern_checked': False,
        'qualified_for_design': False,
    }


def source_hashes():
    from fea.round_structural_audit import sources

    hashes = sources()
    for path in (REFERENCE, Path('fea/round_structural_h3_fit.py')):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def authenticated_assessment(producer, read_sources):
    """Bind the geometry run to unchanged inputs before and after evaluation."""
    before = dict(read_sources())
    report = producer()
    if read_sources() != before:
        raise ValueError('H3 geometry producer or reference changed during assessment')
    return {**report, 'source_sha256': before}


def assess_geometry():
    import cadquery as cq

    from mini_moonboard import round_structural_frame as model

    if model.KEY != 'round-structural-development':
        raise ValueError('Require current structural-screw candidate')
    reference = json.loads(REFERENCE.read_text())
    # Raw current timber is sufficient for the rear rejection: removing bores
    # or occupied fastener cuts cannot create wood beyond this envelope.
    parts = {p.name: p.shape for p in model.uncut_wood_parts()}
    header = parts['base_header'].BoundingBox()
    thickness = .1
    layer = cq.Solid.makeBox(header.xlen, thickness, header.zlen,
        cq.Vector(header.xmin, header.ymax, header.zmin))
    panel_volumes = {name: layer.intersect(parts[name]).Volume()
        for name in ('kicker_left', 'kicker_right')}
    # The kicker panels occupy disjoint X ranges. Reject unexpected overlap so
    # that summed intersection volumes really establish full coverage.
    if parts['kicker_left'].intersect(parts['kicker_right']).Volume() > 1.e-6:
        raise ValueError('Kicker panel interiors unexpectedly overlap')
    rows = []
    for side in ('left', 'right'):
        rim = parts['base_side_'+side]
        bounds = rim.BoundingBox()
        if abs(bounds.zmin-header.zmax) > 1.e-5:
            raise ValueError('Rim no longer bears at the header top')
        # The minimum Y over the entire raw rim is deliberately favorable to
        # reaching it; raised upper-flange screws cannot improve this bound.
        gap = bounds.ymin-header.ymin
        result = necessary_screen(rear_gap_mm=gap,
            wing_reach_mm=reference['nominal_mm']['wing_reach_from_bend'],
            front_layer_mm3=layer.Volume(),
            front_panel_intersection_mm3=sum(panel_volumes.values()))
        rows.append({'side': side, 'rim_side_planes_x_mm': [bounds.xmin, bounds.xmax],
            'minimum_rim_y_mm': bounds.ymin, 'rear_gap_mm': gap, **result})
    rejected = all(r['all_standard_vertical_uplift_mounts_rejected'] for r in rows)
    return {
        'candidate': model.KEY,
        'status': ('H3 standard vertical-uplift mounting rejected by necessary geometry'
                   if rejected else 'H3 needs actual hole-pattern and full fit assessment'),
        'header_front_y_mm': header.ymax, 'header_rear_y_mm': header.ymin,
        'header_z_range_mm': [header.zmin, header.zmax],
        'front_receiver_exterior_layer_thickness_mm': thickness,
        'front_receiver_exterior_layer_volume_mm3': layer.Volume(),
        'panel_intersection_volumes_mm3': panel_volumes,
        'sides': rows,
        'all_standard_vertical_uplift_mounts_rejected': rejected,
        'geometry_basis': 'US C-C-2026 page 299 H3 graphic: each wing 1 9/16 inch (39.6875 mm)',
        'limits': ('Necessary envelope rejection, not an H3 solid or hole/access audit. '
                   'The manufacturer isometric DXF is not treated as actual hole geometry. '
                   'No current parts, fastener axes, or strength ratings are changed. '
                   'Rotating the tie into a different load direction or cutting a panel '
                   'is a different unassessed detail.'),
    }


def assess():
    return authenticated_assessment(assess_geometry, source_hashes)


def write_report(output, producer=assess):
    """Refuse existing evidence, including files created while the producer runs."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    report = producer()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = write_report(args.output)
    print(report['status'])
