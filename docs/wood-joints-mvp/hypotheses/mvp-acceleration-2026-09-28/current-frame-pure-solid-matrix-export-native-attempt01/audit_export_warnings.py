"""Bind the observed redundant GLOBAL=YES warning to pinned parser behavior."""
from pathlib import Path
import hashlib
import json
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.wood_joint_reduced_native import digest, verify, write_json


def audit():
    archive = Path('/tmp/ccx_2.23.src.tar.bz2')
    assert digest(archive) == '9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7'
    with tarfile.open(archive) as source:
        raw = source.extractfile('./CalculiX/ccx_2.23/src/frequencys.f').read()
    assert hashlib.sha256(raw).hexdigest() == '6fdc8f2f6e9cf84d354fedb034e5ebbc5cf983402815fd98b91fc49d7c0df8c8'
    parser = raw.decode()
    assert 'global=.true.' in parser
    assert "textpart(i)(1:9).eq.'GLOBAL=NO'" in parser
    assert 'GLOBAL=YES' not in parser
    assert "'*WARNING reading *FREQUENCY: parameter not recognized:'" in parser
    rows = []
    for directory, expected_warning_count in (
        (HERE.parent / 'current-free-c3d20-matrix-export-native-attempt01', 0),
        (HERE.parent / 'current-constrained-matrix-export-native-attempt01', 2),
        (HERE, 2),
    ):
        verify(directory, check_live=True)
        execution = json.loads((directory / 'execution.json').read_text())
        assert execution['returncode'] == 0 and execution['container_confirmed_terminal'] is True
        for name, expected in execution['outputs_sha256'].items():
            assert digest(directory / name) == expected
        log = (directory / 'native.stdout').read_text()
        warnings = [line.strip() for line in log.splitlines() if '*WARNING' in line]
        assert len(warnings) == expected_warning_count
        if expected_warning_count:
            assert warnings == ['*WARNING reading *FREQUENCY: parameter not recognized:',
                                '*WARNING reading *FREQUENCY. Card image:']
            assert 'GLOBAL=YES' in log
        assert '*ERROR' not in log
        assert 'Storing the node and global direction per entry' in log
        assert not (directory / 'native.stderr').read_text().strip()
        rows.append({'directory': str(directory.relative_to(ROOT)),
                     'native_stdout_sha256': digest(directory / 'native.stdout'),
                     'execution_sha256': digest(directory / 'execution.json'),
                     'warning_count': len(warnings),
                     'global_output_observed': True})
    return {'schema': 'calculix_223_matrixstorage_keyword_warning_audit/v1',
            'status': 'PASS_REPLAY_REDUNDANT_GLOBAL_YES_WARNING_AUDIT',
            'archive_sha256': digest(archive),
            'frequency_parser_sha256': hashlib.sha256(raw).hexdigest(),
            'parser_initializes_global_true': True,
            'explicit_global_yes_recognized': False,
            'recognized_global_override': 'GLOBAL=NO',
            'observed_exports': rows,
            'correction': 'Existing GLOBAL=YES tokens are ignored with a warning; these decks retain the default global output. Omit the redundant token in future new decks.',
            'limits': 'No input, native output or prior oracle is modified. This audit is specific to the recorded warning and pinned parser, and does not waive other warnings.',
            'producer_sha256': digest(Path(__file__))}


if __name__ == '__main__':
    result = audit()
    if '--verify' in sys.argv:
        assert result == json.loads((HERE / 'warning-audit.json').read_text())
    else:
        write_json(HERE / 'warning-audit.json', result)
    print(result['status'])
