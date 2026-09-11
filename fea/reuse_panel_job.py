"""Replay authenticated byte-identical shell jobs without claiming a new solve."""
import hashlib
import json
import shutil
from pathlib import Path

from fea import vertical_panel_comparison as shell


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_input(record):
    """Match the frozen shell runner's input serialization, including newlines."""
    return (json.dumps(record, indent=2)+'\n').encode()


def reuse(record, source_dir, destination, assessor):
    """Require identical current input/deck, authenticate all evidence, then audit.

    No mismatched job falls back to a fresh solve. The caller decides whether
    a different physics job should be launched, and records that separately.
    """
    source, target = Path(source_dir), Path(destination)
    if target.exists():
        raise FileExistsError('Refusing to overwrite replay destination')
    source_result = (source/'result.json').read_bytes()
    saved = json.loads(source_result)
    hashes = saved['evidence_sha256']
    required = {'input.json', 'panel.inp', 'panel.dat', 'panel.log'}
    if not isinstance(hashes, dict) or not required <= hashes.keys():
        raise ValueError('Incomplete source solver evidence hashes')
    for name, sha in hashes.items():
        if Path(name).name != name or name in ('.', '..', 'result.json'):
            raise ValueError('Unsafe or circular source artifact name')
        artifact = source/name
        if artifact.is_symlink() or not artifact.is_file() or digest(artifact) != sha:
            raise ValueError(f'Source solver artifact hash differs: {name}')
    if (source/'input.json').read_bytes() != canonical_input(record):
        raise ValueError('Current canonical input differs from reusable job')
    if (source/'panel.inp').read_bytes() != shell.deck(record).encode():
        raise ValueError('Current shell deck differs from reusable job')
    # Assess before creating a destination; an audit failure leaves no replay.
    result = assessor(record, (source/'panel.dat').read_text())
    target.mkdir(parents=True, exist_ok=False)
    for name in hashes:
        shutil.copyfile(source/name, target/name)
        if digest(target/name) != hashes[name]:
            raise ValueError('Source changed while copying reusable evidence')
    result['evidence_sha256'] = {name: digest(target/name) for name in hashes}
    provenance = {
        'fresh_solver_run': False,
        'method': 'Current canonical input and deck byte-identical; all saved raw artifact hashes verified; current output assessor rerun',
        'source_directory': str(source.resolve()),
        'source_result_sha256': hashlib.sha256(source_result).hexdigest(),
        'source_input_sha256': hashes['input.json'],
        'source_deck_sha256': hashes['panel.inp'],
        'source_dat_sha256': hashes['panel.dat'],
        'source_log_sha256': hashes['panel.log'],
    }
    if (source/'result.json').read_bytes() != source_result:
        raise ValueError('Source result changed during reuse')
    (target/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result, provenance
