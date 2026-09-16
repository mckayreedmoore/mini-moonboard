"""Export the selected compact spliced-knee flush-top development candidate."""
import argparse
import ast
import json
from pathlib import Path

from mini_moonboard import compact_spliced_flush_top as model
from scripts import compact_spliced_exports as previous

shared = previous.shared
PACKAGE = 'docs/compact-spliced-flush-top-build-package.md'
HARDWARE_SOURCES = (
    'docs/compact-half-inch-hardware.md',
    'docs/compact-splice-hardware.md',
    'docs/current-panel-screw-purchase.md',
)
STATUS = 'Development package · spliced knees · flush rear-leg tops · angle gate open'
SCOPE = ('Fresh-stock flush-top geometry with relocated upper bolt pairs. Retains '
         'the 7 mm rim reserve, four independent knee pieces, 20 complete outward '
         'bolt stacks, 66 panel/kicker screws and no-slip floor assumption. Six fresh '
         'listed assembled cases meet their conditional splice/member criteria. Retained '
         'ML24Z/SDS separation and flange-couple applicability remain open; this result is '
         'not transferred from prior cases and is not unconditional qualification.')


def sources():
    """Include predecessor closure plus every source imported by this adapter."""
    hashes = previous.sources()
    pending = [Path(__file__).resolve(), Path(model.__file__).resolve()]
    visited = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        hashes[str(path.relative_to(shared.ROOT))] = shared.digest(path)
        for node in ast.walk(ast.parse(path.read_text())):
            dependencies = []
            if isinstance(node, ast.ImportFrom):
                parent = path.parent if node.level else shared.ROOT
                for _ in range(max(0, node.level - 1)):
                    parent = parent.parent
                module = parent / (node.module or '').replace('.', '/')
                dependencies = [module, *(module / alias.name for alias in node.names)]
            elif isinstance(node, ast.Import):
                dependencies = [shared.ROOT / alias.name.replace('.', '/') for alias in node.names]
            for dependency in dependencies:
                for source in (dependency.with_suffix('.py'), dependency / '__init__.py'):
                    if source.is_file() and source.is_relative_to(shared.ROOT):
                        pending.append(source)
    for source in HARDWARE_SOURCES:
        hashes[source] = shared.digest(shared.ROOT / source)
    return dict(sorted(hashes.items()))


def bolt_hardware_spec(connection):
    """Catalog identity and delivered-part checks behind nominal-D resistance."""
    acceptance = {
        'specified_bolt_grade': 'SAE J429 Grade 5',
        'specified_bending_yield_ksi': 90,
        'assumed_washer_yield_ksi': 33,
        'nominal_diameter_acceptance': (
            'Accept only after delivered bolt passes full-body/transition and '
            'nut-seating checks.'),
        'thread_transition_rule': (
            'Count transition as threaded; threaded bearing must occupy no more '
            'than one quarter of each member bearing length.'),
        'nut_seating_rule': (
            'Nut must seat on washer before runout and retain full usable formed-thread '
            'engagement at tip.'),
    }
    if connection.name.startswith('lumber_leg_bolt_'):
        return {
            **acceptance,
            'hardware_reference': HARDWARE_SOURCES[0],
            'catalog_bolt_part': 'Bolt Depot 407',
            'catalog_bolt_size': '1/2-13 x 8 in, partially threaded',
            'catalog_nut_part': 'Bolt Depot 2573',
            'catalog_washer_part': 'Bolt Depot 15025',
            'catalog_min_thread_length_mm': 38.1,
            'minimum_full_body_through_transition_from_under_head_mm': 158.9278,
            'catalog_washer_min_od_mm': 34.7472,
            'catalog_washer_max_bore_mm': 14.6558,
            'catalog_washer_min_thickness_mm': 2.1844,
        }
    splice = connection.name.startswith('knee_splice_bolt_')
    threshold = 69.3166 if splice else (120.1166 if '_rim_' in connection.name else 107.4166)
    return {
        **acceptance,
        'hardware_reference': HARDWARE_SOURCES[1],
        'catalog_bolt_part': 'Bolt Depot 367' if splice else 'Bolt Depot 371',
        'catalog_bolt_size': ('3/8-16 x 4 in, partially threaded' if splice
                              else '3/8-16 x 6 in, partially threaded'),
        'catalog_nut_part': 'Bolt Depot 2571',
        'catalog_washer_part': 'Bolt Depot 15023',
        'catalog_min_thread_length_mm': 25.4,
        'minimum_full_body_through_transition_from_under_head_mm': threshold,
        'catalog_washer_min_od_mm': 25.2222,
        'catalog_washer_max_bore_mm': 11.5062,
        'catalog_washer_min_thickness_mm': 1.6256,
    }


def metadata(parts, connections):
    bolts = [connection for connection in connections if connection.kind == 'bolt']
    upper = [connection for connection in bolts
             if connection.name.startswith('lumber_leg_bolt_')]
    return {
        **shared.design_metadata(parts, connections),
        'key': model.KEY,
        'status': STATUS,
        'description': STATUS + '. ' + SCOPE,
        'build_package': PACKAGE,
        'assessment_scope': SCOPE,
        'leg_stock': '4x6',
        'outer_rim_stock': '4x6',
        'leg_bolt_count': len(upper),
        'bolts_per_leg': len(upper) // 2,
        'total_bolt_count': len(bolts),
        'knee_piece_count': len(model.KNEE_NAMES),
        'upper_bolt_pitch_mm': model.UPPER_BOLT_PITCH_MM,
        'upper_bolt_centre_yz_mm': list(model.UPPER_BOLT_CENTRE_YZ_MM),
        'lower_kicker_screw_height_mm': model.LOWER_KICKER_Z_MM,
        'leg_top_projection_mm': model.LEG_TOP_PROJECTION_MM,
        'rear_rim_overhang_mm': model.REAR_OVERHANG_MM,
        'floor_runner_count': 0,
        'leg_taper': None,
        'fresh_stock_required': True,
        'bolt_installation': 'Heads inside; nuts and threaded ends outside',
        'panel_screw_purchase': {
            'product': 'Fas-n-Tite/Hillman model 42605',
            'retailer_item': "Lowe's 755741",
            'nominal_size': '#10 x 2-1/2 in',
            'quantity_required': 66,
            'status': ('Selected within owner-accepted panel scope. All axes enter the '
                       '139.7 mm receiver dimension; nominal timber penetration is '
                       '45.24375 mm with 94.45625 mm remaining before the rear face. '
                       'Public geometry and design values remain incomplete.'),
            'record': 'docs/current-panel-screw-purchase.md',
        },
        'joint_note': ('Rear-leg tops are flush to retained side-rim rear faces. '
                       'Upper pairs are relocated at 56 mm pitch. Four independent '
                       'unnotched knee pieces and 7 mm rim reserve remain. No composite '
                       'knee action or transferred historical qualification.'),
    }


def export(root=Path('site')):
    directory = shared.export(root, candidate=model, metadata=metadata, source_reader=sources)
    inventory_path = directory / 'parts.json'
    inventory = json.loads(inventory_path.read_text())
    for item in inventory['parts']:
        fabrication = item['fabrication']
        description = fabrication.get('description', '')
        stale_tail = '; Single 2x6 support legs with four existing bolts per leg;'
        if stale_tail in description:
            description = description.split(stale_tail, 1)[0]
        if description.startswith('Preferred compact 4x6 development geometry; three bolts per leg;'):
            description = ''
        description = description.replace('225mm kicker', '277mm kicker')
        fabrication['description'] = (
            description.rstrip(';. ') + '; selected 4x6 legs/rims, two upper bolts per '
            'leg, 277 mm kicker datum, and fresh six-case splice/member evidence. '
            'Retained ML24Z/SDS connection gate open; NOT a fabrication release.')
        if not fabrication.get('clearance_status', '').startswith('FAIL'):
            fabrication['clearance_status'] = STATUS
        fabrication['build_package'] = PACKAGE
        if fabrication['kind'] == 'bolt':
            connection = next(connection for connection in model.connections()
                              if connection.name == fabrication['connection_name'])
            fabrication.update(bolt_hardware_spec(connection))
        if item['name'].startswith(
                ('fastener_round_panel_', 'fastener_round_kicker_',
                 'fastener_kicker_header_')):
            fabrication['description'] = (
                'Historical SPAX occupied-geometry proxy. Owner purchased Fas-n-Tite/'
                'Hillman model 42605 #10 x 2-1/2 in for this axis. It is selected within '
                'the accepted panel scope and remains contained in the 139.7 mm receiver; '
                'actual geometry and resistance are not transferred or modeled. See '
                'docs/current-panel-screw-purchase.md. Retained ML24Z/SDS connection '
                'gate open; NOT an installation release.')
    inventory_path.write_text(json.dumps(inventory, indent=2, allow_nan=False) + '\n')
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['artifact_sha256']['parts.json'] = shared.digest(inventory_path)
    if sources() != manifest['source_sha256']:
        raise ValueError('Source changed during presentation export')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(shared.check(args.root, candidate=model, exporter=export) if args.check
          else export(args.root))
