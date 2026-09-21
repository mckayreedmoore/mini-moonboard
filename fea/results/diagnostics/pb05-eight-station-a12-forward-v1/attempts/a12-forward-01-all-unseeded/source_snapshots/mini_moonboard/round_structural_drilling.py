"""Source-bound structural-screw references; future insert reserves are not pilot cuts."""
import argparse
import json
from pathlib import Path

from . import round_service_drilling as previous
from . import round_structural_frame as model
from .selective_2x6_viewer import digest

AUDIT = Path('fea/results/round-structural-audit-v1.json')
LIMITS = model.LIMITS


def panel_fastening_rows():
    """Derive panel-local coordinates from this candidate's actual attachment axes."""
    result = {}
    for row in model.attachment_datums():
        panel = row['panel']
        left = -model.b.HALF if panel.endswith('_left') else 0.
        bottom = model.b.HALF if panel.startswith('main_upper_') else 0.
        result.setdefault(panel, []).append({**row,
            'from_left_mm': row['x']-left, 'from_bottom_mm': row['s']-bottom,
            'station_axis': 'vertical Z' if panel.startswith('kicker_') else 'slope S',
            'attachment': 'structural_panel_screw', 'pilot_diameter_mm': None,
            'future_insert_pilot_cut': False, 'qualified_for_machining': False})
    return result


def panel_fastening_svg(name, rows):
    svg = previous.panel_fastening_svg(name, rows)
    return svg.replace('</g></svg>', '<text x="35" y="730" font-size="13">'
        'Future insert space is reserved only; no inserts installed or future insert pilots cut.</text></g></svg>')


def source_hashes():
    report = json.loads(AUDIT.read_text())
    sources = report.get('source_sha256', {})
    if report['candidate'] != model.KEY or not sources or any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError('Recompute the candidate geometry audit before drilling export')
    sources = dict(sources)
    for path in (AUDIT, Path(__file__).relative_to(Path.cwd()),
                 Path('mini_moonboard/round_service_drilling.py'),
                 Path('mini_moonboard/horizontal_service_drilling.py'),
                 Path('docs/panel-insert-reference.json'), Path('docs/round-panel-countersink-reference.json')):
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
            'No base gusset bolts remain. Structural panel screws are separate operations.')
        files[name+'.svg'] = svg.replace('</g></svg>', '<text x="35" y="730" font-size="13">'
            'Leg joint: head OUTSIDE, nut INSIDE; retain one washer at each end.</text></g></svg>')
    for row in passages:
        files[row['name']+'.svg'] = previous.passage_svg(row).replace(
            'Panel screw cylinders do not specify approved pilot diameters.',
            'Future insert space is reserved only; no future insert pilots cut.')
    if source_hashes() != sources:
        raise ValueError('Sources changed during structural-screw drilling generation')
    output.mkdir(parents=True)
    for name, svg in files.items():
        (output/name).write_text(svg)
    (output/'drilling.json').write_text(json.dumps({
        'candidate': model.KEY, 'qualified_for_design': False, 'qualified_for_machining': False,
        'limits': LIMITS, 'installation_order': 'Panels first; feed harness and install lights afterward',
        'panels': panels, 'panel_fastening_axes': fastening, 'leg_bolt_members': bolts,
        'circular_passages': passages, 'panel_kicker_screw_count': len(model.panel_connections()),
        'panel_kicker_insert_count': 0, 'panel_screw_pilots_specified': False,
        'future_insert_pilots_cut': False, 'released_installation_dimensions': False,
        'hardware_reference': 'docs/round-panel-countersink-reference.json',
    }, indent=2, allow_nan=False)+'\n')
    sections = ''.join('<section>'+svg+'</section>' for svg in files.values())
    (output/'drilling.html').write_text('<!doctype html><meta charset="utf-8"><title>Structural-screw development references</title>'
        '<style>@page{size:A4 landscape;margin:0}body{margin:0}section{break-after:page;width:297mm;height:210mm}'
        'svg{display:block;width:297mm;height:210mm}</style>'+sections)
    if source_hashes() != sources:
        raise ValueError('Sources changed during structural-screw drilling generation')
    (output/'manifest.json').write_text(json.dumps({'candidate': model.KEY, 'source_sha256': sources,
        'artifact_sha256': {p.name: digest(p) for p in output.iterdir() if p.is_file()}}, indent=2)+'\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/round-structural-drilling'))
    print(generate(parser.parse_args().output))
