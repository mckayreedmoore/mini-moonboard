"""Source-bound insert attachment references; provisional dimensions, not a shop release."""
import argparse
import html
import json
from pathlib import Path

from . import round_insert_frame as model
from . import round_insert_hardware as hardware
from . import round_service_drilling as previous
from .selective_2x6_viewer import digest

AUDIT = Path('fea/results/round-insert-audit-v1.json')
LIMITS = hardware.LIMITS


def panel_fastening_rows():
    """Keep panel-local datums and distinguish body, pilot and clearance envelopes."""
    connections = {c.name: c for c in model.panel_connections()}
    result = {}
    for panel, rows in previous.panel_fastening_rows().items():
        result[panel] = []
        for row in rows:
            c = connections[row['name']]
            result[panel].append({**row,
                'attachment': 'machine_screw_and_threaded_insert',
                'insert_sku': hardware.INSERT['sku'], 'machine_screw_sku': hardware.SCREW['sku'],
                'panel_clearance_reservation_mm': hardware.PANEL_CLEARANCE_MM,
                'insert_body_nominal_od_mm': hardware.INSERT['nominal_outer_diameter'],
                'insert_body_maximum_reservation_od_mm': hardware.INSERT['nominal_outer_diameter']+
                    hardware.INSERT['drawing_general_tolerance_plus_minus'],
                'manufacturer_pilot_recommendation_mm': hardware.INSERT['pilot_diameter_inch_recommendation'],
                'pilot_diameter_mm': None,
                'receiver_reserve_depth_mm': hardware.RESERVE_DEPTH_MM,
                'head_angle_product_min_deg': hardware.SCREW['head_angle_min_deg'],
                'head_angle_product_max_deg': hardware.SCREW['head_angle_max_deg'],
                'head_envelope_max_diameter_mm': hardware.SCREW['head_diameter_max'],
                'machining_countersink_angle_deg': None, 'machining_countersink_depth_mm': None,
                'panel_front_world_mm': list(c.start.toTuple()),
                'receiver_face_world_mm': list((c.start+c.direction*hardware.PANEL).toTuple()),
                'insert_front_world_mm': list(c.insert_start.toTuple()),
                'drill_direction_world': list(c.direction.toTuple()),
                **hardware.recess_sensitivity(),
                'qualified_installation_torque_nm': None,
                'status': LIMITS})
    return result


def panel_fastening_svg(name, rows):
    drawing = previous.previous
    out = drawing.start_svg(name+' — INSERT / MACHINE-SCREW AXES',
        'FRONT / CLIMBING FACE: measure right from LEFT and up from BOTTOM; do not mirror. DEVELOPMENT ONLY.')
    lines = [f'{len(rows)} removable attachments; count and fit do not establish resistance.',
        'E-Z LOK 801420-13 zinc inserts; Dottie FMDD14114 1/4-20 x 1.25 in flat-head machine screws.',
        f'Panel clearance: {hardware.PANEL_CLEARANCE_MM:g} mm PROVISIONAL. Product head: 80–82 degrees; CAD envelope uses 80 degrees.',
        'No released countersink angle or depth. Check the actual head on an offcut; no SPAX 90-degree seat applies.',
        f'Insert nominal OD {hardware.INSERT["nominal_outer_diameter"]:.4f} mm is NOT the pilot diameter.',
        'Manufacturer pilot recommendation: 23/64 in (9.128125 mm); stock-specific installation remains unqualified.',
        f'Recess {hardware.INSERT_RECESS_MM:g} mm and receiver reserve {hardware.RESERVE_DEPTH_MM:g} mm are provisional assumptions.',
        'Reserve includes an assumed drill point; it is NOT a released drilling depth or full-diameter pilot depth.',
        'Effective thread engagement, installation torque and resistance remain unknown. Do not machine from this sheet.',
        'Panel axes below are perpendicular to the panel. Receiver/insert world coordinates are in drilling.json.',
        'AXIS / RECEIVER                                               FROM LEFT / FROM BOTTOM (mm)']
    lines += [f'{row["role"]} {row["name"].rsplit("_", 1)[1]} / {row["receiver"]}: '
              f'{row["from_left_mm"]:.3f} / {row["from_bottom_mm"]:.3f}' for row in rows]
    for i, line in enumerate(lines):
        out.append(f'<text x="35" y="{102+i*26}" font-size="13">{html.escape(line)}</text>')
    return drawing.finish_svg(out)


def source_hashes():
    report = json.loads(AUDIT.read_text())
    sources = report.get('source_sha256', {})
    if report['candidate'] != model.KEY or not sources or any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError('Recompute the candidate geometry audit before drilling export')
    sources = dict(sources)
    for path in (AUDIT, Path(__file__).relative_to(Path.cwd()),
                 Path('mini_moonboard/round_service_drilling.py'),
                 Path('mini_moonboard/horizontal_service_drilling.py'),
                 Path('docs/panel-insert-reference.json'), Path('docs/round-insert-hardware-reference.json')):
        sources[str(path)] = digest(path)
    return sources


def generate(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    sources = source_hashes()
    drawing = previous.previous
    panels = drawing.panel_rows()
    kickers = previous.kicker_hold_rows()
    bolts, passages = drawing.bolt_rows(model), previous.passage_rows(model)
    files = {name+'.svg': drawing.panel_svg(name, record) for name, record in panels.items()}
    files.update({name+'-holds.svg': previous.kicker_hold_svg(name, record) for name, record in kickers.items()})
    panels.update(kickers)
    fastening = panel_fastening_rows()
    files.update({name+'-fastening.svg': panel_fastening_svg(name, rows) for name, rows in fastening.items()})
    for name, record in bolts.items():
        svg = drawing.bolt_svg(name, record).replace('Gusset bolts and panel screws are separate operations.',
            'No base gusset bolts remain. Insert attachments are separate operations.')
        files[name+'.svg'] = svg.replace('</g></svg>', '<text x="35" y="730" font-size="13">'
            'Leg joint: head OUTSIDE, nut INSIDE; retain one washer at each end.</text></g></svg>')
    for row in passages:
        files[row['name']+'.svg'] = previous.passage_svg(row).replace(
            'Panel screw cylinders do not specify approved pilot diameters.',
            'Insert receiver cuts are occupied envelopes, not approved installation pilots.')
    if source_hashes() != sources:
        raise ValueError('Sources changed during insert drilling generation')
    output.mkdir(parents=True)
    for name, svg in files.items():
        (output/name).write_text(svg)
    (output/'drilling.json').write_text(json.dumps({
        'candidate': model.KEY, 'qualified_for_design': False, 'qualified_for_machining': False,
        'limits': LIMITS, 'installation_order': 'Panels first; feed harness and install lights afterward',
        'panels': panels, 'panel_fastening_axes': fastening, 'leg_bolt_members': bolts,
        'circular_passages': passages, 'panel_kicker_machine_screw_count': len(model.panel_connections()),
        'panel_kicker_insert_count': len(model.panel_connections()),
        'ordinary_panel_kicker_screw_count': 0, 'released_installation_dimensions': False,
        'hardware_reference': 'docs/round-insert-hardware-reference.json',
    }, indent=2, allow_nan=False)+'\n')
    sections = ''.join('<section>'+svg+'</section>' for svg in files.values())
    (output/'drilling.html').write_text('<!doctype html><meta charset="utf-8"><title>Insert development references</title>'
        '<style>@page{size:A4 landscape;margin:0}body{margin:0}section{break-after:page;width:297mm;height:210mm}'
        'svg{display:block;width:297mm;height:210mm}</style>'+sections)
    if source_hashes() != sources:
        raise ValueError('Sources changed during insert drilling generation')
    (output/'manifest.json').write_text(json.dumps({'candidate': model.KEY, 'source_sha256': sources,
        'artifact_sha256': {p.name: digest(p) for p in output.iterdir() if p.is_file()}}, indent=2)+'\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/round-insert-drilling'))
    print(generate(parser.parse_args().output))
