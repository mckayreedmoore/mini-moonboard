"""Archive flush-top native evidence, then run existing splice checks explicitly."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from mini_moonboard import compact_spliced_flush_top as candidate
from scripts.compact_splice_results import PREFIXES

CANDIDATE = candidate.KEY
MODEL_SOURCE = str(Path(candidate.__file__).resolve().relative_to(Path.cwd()))
CORE_FILES = ('report.json.gz', 'geometry.json', 'sources.zip')
DERIVED_FILES = ('checks.json', 'splice-checks.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authenticate_derived_checks(output):
    """Bind both completed check records into the archive manifest."""
    manifest_path = output / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('candidate') != CANDIDATE or set(manifest.get('files', {})) != set(CORE_FILES):
        raise ValueError('Require fresh flush-top core archive before authenticating checks')
    for name in CORE_FILES:
        if digest(output / name) != manifest['files'][name]:
            raise ValueError('Core archive changed before check authentication: ' + name)
    for name in DERIVED_FILES:
        record = json.loads((output / name).read_text())
        if record.get('candidate') != CANDIDATE:
            raise ValueError('Derived check candidate differs: ' + name)
        manifest['files'][name] = digest(output / name)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


def archive_and_check(native, geometry, output):
    """Create new candidate-bound archive without modifying historical evidence."""
    native, geometry, output = Path(native), Path(geometry), Path(output)
    if output.exists():
        raise FileExistsError('Refuse to replace existing archive: '+str(output))
    report = json.loads((native/'report.json').read_text())
    actual_geometry = json.loads(geometry.read_text())
    if report.get('candidate') != CANDIDATE or actual_geometry.get('candidate') != CANDIDATE:
        raise ValueError('Require native and geometry inputs from selected flush-top candidate')
    subprocess.run([
        sys.executable, '-m', 'scripts.compact_two_results',
        '--native', str(native),
        '--geometry', str(geometry),
        '--output', str(output),
        '--expected-candidate', CANDIDATE,
        '--model-source', MODEL_SOURCE,
        '--bolt-prefix', *PREFIXES,
    ], check=True)
    subprocess.run([
        sys.executable, '-m', 'scripts.compact_splice_results',
        '--archive', str(output),
        '--expected-candidate', CANDIDATE,
    ], check=True)
    authenticate_derived_checks(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    archive_and_check(args.native, args.geometry, args.output)


if __name__ == '__main__':
    main()
