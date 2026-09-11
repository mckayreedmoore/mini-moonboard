"""Run the finite insert/contact sensitivity matrix sequentially."""
import argparse
import hashlib
import json
from pathlib import Path

from fea.round_insert_frame import run

CASES = (
    ('f10-contact', {}),
    ('f10-no-contact', {'contact': False}),
    ('c6-contact', {'hold': 'C6'}),
    ('c10-contact', {'hold': 'C10'}),
    ('f10-k100', {'panel_stiffness': 100.}),
    ('f10-k10000', {'panel_stiffness': 10000.}),
    ('f10-samples5', {'samples': 5}),
    ('f10-penalty10', {'penalty': 10.}),
)


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output/'launch.py').write_bytes(source)
    rows = []
    for name, overrides in CASES:
        parameters = {'hold': 'F10', 'contact': True, 'panel_stiffness': 1000.,
                      'samples': 3, 'penalty': 100., **overrides}
        report = run(output/name, **parameters)
        row = {'case': name, 'parameters': parameters,
               'report_sha256': hashlib.sha256((output/name/'report.json').read_bytes()).hexdigest(),
               'contact_diagnostic_checks_passed': report['contact_diagnostic_checks_passed'],
               'maximum_panel_displacement_mm': report['maximum_panel_displacement_mm'],
               'contact_cycles': len(report['contact_cycles'])}
        rows.append(row)
        print(json.dumps(row), flush=True)
        (output/'summary.json').write_text(json.dumps({
            'candidate': 'round-insert-development', 'qualified_for_design': False,
            'batch_complete': len(rows) == len(CASES),
            'launch_sha256': hashlib.sha256(source).hexdigest(), 'cases': rows}, indent=2)+'\n')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
