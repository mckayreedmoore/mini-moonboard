"""Direct single-member substitutions; reject fit failures before structural solves."""
import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from mini_moonboard import box_frame as b
from mini_moonboard import screw_mvp_frame as screws
from mini_moonboard import wide_frame as wide
from mini_moonboard.connection_geometry import material_intervals

VARIANTS = ('baseline', 'rims', 'principals', 'posts', 'principals_posts', 'combined')
THICKNESS, DEPTH = 38.1, 139.7


connections = screws.connections


def candidates():
    # Preserve service pockets, housings and all hardware axes. No stock stacking.
    raw = {p.name: p for p in screws.wood_parts()}
    result = {}
    for variant in VARIANTS:
        parts = dict(raw)
        changed = []
        for name, p in raw.items():
            if variant in ('rims', 'combined') and name.startswith('base_side_'):
                tool = b.block(-2000., 2000., -1000., 4000., 0., DEPTH)
                blank = (p.blank[0], DEPTH, THICKNESS)
            elif ((variant in ('principals', 'principals_posts', 'combined') and name.startswith('base_principal_'))
                  or (variant in ('posts', 'principals_posts', 'combined') and name.startswith('base_post_center_'))):
                side = 'left' if 'left' in name else 'right'
                x = wide.CENTERS[side]
                tool = wide.base._world_box(x-THICKNESS/2, x+THICKNESS/2,
                                            -2000., 4000., -1000., 4000.)
                blank = (p.blank[0], DEPTH, THICKNESS)
            else:
                continue
            shape = p.shape.intersect(tool).clean()
            if not shape.isValid() or len(shape.Solids()) != 1:
                raise ValueError(f'Invalid single-member replacement: {variant}/{name}')
            parts[name] = replace(p, shape=shape, blank=blank)
            changed.append(name)
        result[variant] = (parts, changed)
    return result


def build():
    versions = candidates()
    hardware = connections()
    reference = versions['baseline'][0]
    result = {}
    for variant, (parts, changed) in versions.items():
        losses, edges = [], []
        for c in hardware:
            for name in set(c.members) & set(changed):
                old = material_intervals(reference[name].shape, c.start, c.direction, 0., c.length)
                new = material_intervals(parts[name].shape, c.start, c.direction, 0., c.length)
                old_length = sum(z-a for a, z in old)
                new_length = sum(z-a for a, z in new)
                if new_length < old_length-1e-5:
                    losses.append({'connection': c.name, 'member': name,
                                   'original_axial_wood_mm': old_length,
                                   'substituted_axial_wood_mm': new_length})
            if c.name.startswith('lumber_leg_bolt_'):
                n = (c.start-b.point(0., 0., 0.)).dot(b.normal())
                depth = DEPTH if variant in ('rims', 'combined') else wide.timber.SIDE_DEPTH
                distance = min(n, depth-n)
            elif c.name.startswith('timber_backing_bolt_'):
                distance = THICKNESS/2 if variant in ('principals', 'principals_posts', 'combined') else 88.9/2
            else:
                continue
            edges.append({'connection': c.name, 'minimum_transverse_edge_mm': distance,
                          'existing_reversible_4D_screen_mm': 4*c.diameter,
                          'passes_existing_edge_screen': distance >= 4*c.diameter-1e-6})
        failed_edges = [e for e in edges if not e['passes_existing_edge_screen']]
        result[variant] = {
            'changed_members': changed,
            'removed_net_wood_volume_mm3': sum(reference[n].shape.Volume()-parts[n].shape.Volume() for n in changed),
            'axial_material_losses': losses, 'bolt_edge_checks': edges,
            'passes_tested_direct_substitution_gates': not losses and not failed_edges,
            'structural_analysis_run': False, 'qualified_for_design': False}
    return {'basis': 'Compact 2x6/e0 legs, existing wide-frame service pockets and hardware axes; no doubled stock. Panel/kicker wood screws replace insert assemblies.',
            'hardware': {'panel_kicker_wood_screws': sum(isinstance(c, wide.timber.PanelScrew) for c in hardware),
                         'threaded_inserts': 0, 'frame_bolts': sum(c.kind == 'bolt' for c in hardware),
                         'bracket_screws': sum(c.name.startswith('clip_') for c in hardware)},
            'limits': 'Direct-substitution rejection screen only. Axial intervals do not establish annular bearing or effective thread engagement. '
                      'The 4D check retains the project reversible cross-grain screen; it is not an axial-withdrawal rule or a capacity calculation. '
                      'No new contact, strength, buckling, floor stability, collision or service-access acceptance. Baseline is not qualified.',
            'variants': result,
            'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [Path(__file__).relative_to(Path.cwd()), Path('docs/panel-insert-reference.json'),
                                        Path('docs/ml24z-reference.json'), *sorted(Path('mini_moonboard').glob('*.py'))]}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    with args.output.open('x') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
