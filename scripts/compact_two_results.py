"""Archive and recompute the actual two-bolt trial's first-stage checks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fea.compact_rail_checks import assess, hardware_assumptions


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path)
    parser.add_argument('--expected-candidate', default='compact-two-development')
    parser.add_argument('--model-source', default='mini_moonboard/compact_two_frame.py')
    parser.add_argument('--geometry', type=Path)
    parser.add_argument('--output', type=Path, default=Path('fea/results/compact-two-study'))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    if args.native:
        if args.geometry is None:
            parser.error('--geometry required with --native')
        raw = (args.native/'report.json').read_bytes()
        report = json.loads(raw)
        (out/'report.json.gz').write_bytes(gzip.compress(raw, mtime=0))
        (out/'geometry.json').write_bytes(args.geometry.read_bytes())
        with ZipFile(out/'sources.zip', 'w', ZIP_DEFLATED) as archive:
            for path, sha in report['source_sha256'].items():
                source = args.native/'source_snapshots'/path
                if digest(source) != sha:
                    raise ValueError('Native source snapshot mismatch: '+path)
                archive.write(source, path)
        manifest = {'candidate':report['candidate'], 'native_directory':str(args.native),
            'native_report_sha256':hashlib.sha256(raw).hexdigest(),
            'files':{name:digest(out/name) for name in ('report.json.gz', 'geometry.json', 'sources.zip')}}
        (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    manifest = json.loads((out/'manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if digest(out/name) != sha:
            raise ValueError('Archive changed: '+name)
    raw = gzip.decompress((out/'report.json.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest['native_report_sha256']:
        raise ValueError('Native report changed')
    report, geometry = json.loads(raw), json.loads((out/'geometry.json').read_text())
    if report['candidate'] != geometry['candidate'] or report['candidate'] != args.expected_candidate:
        raise ValueError('Candidate mismatch')
    model = args.model_source
    if geometry['source_sha256'][model] != report['source_sha256'][model]:
        raise ValueError('Geometry and native model source mismatch')
    hardware = {name:hardware_assumptions(row['diameter_mm'],
        washer_od_mm=row['washer_od_mm'], hole_diameter_mm=row['hole_diameter_mm'],
        washer_thickness_mm=row['washer_thickness_mm'])
        for name, row in geometry['hardware_by_name'].items()}
    result = assess(report, geometry['geometries_by_bolt_name'], hardware,
                    bolt_prefixes=('lumber_leg_bolt_',))
    result['receiver_fit_pass'] = geometry['receiver_fit_pass']
    (out/'checks.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key:result.get(key) for key in ('candidate', 'status', 'metrics', 'receiver_fit_pass')}, indent=2))


if __name__ == '__main__':
    main()
