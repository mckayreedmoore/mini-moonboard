"""Three fresh round-service probes against conditional fastener references."""
import argparse
import hashlib
import json
from pathlib import Path

from fea import horizontal_panel_fastener_screen as shared


def build(root):
    from mini_moonboard import round_service_frame as model

    root = Path(root)
    result = shared.build(root, model=model, screw_count=56, case_count=3, coupled_count=3)
    summary = json.loads((root/'summary.json').read_text())
    holds = []
    for case in summary['cases']:
        directory = root/case['case']
        report = json.loads((directory/'report.json').read_text())
        record = json.loads((directory/report['final_cycle_directory']/'input.json').read_text())
        if (record['pounds'] != 250. or record['load_kind'] != 'full'
                or record['panel_screw_count'] != 56 or record['stiffness_n_per_mm'] != 1000.):
            raise ValueError('Require fresh 250lb full-vector 56-screw inputs')
        holds.append(record['hold'])
    if sorted(holds) != ['C10', 'C6', 'F10']:
        raise ValueError('Require independent C10, C6 and F10 probes')
    path = Path(__file__).resolve().relative_to(Path.cwd())
    result['input_sha256'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    result['limits'] += (' This round-bore candidate also changes screw positions and wood passages; '
                         'comparison with historical 87-screw results does not isolate screw count. '
                         'Owned Roseburg plywood properties and head resistance remain unverified.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.directory)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report['worst'], indent=2))
