#!/usr/bin/env python3
"""Read-only review probes; mutate only in memory or temporary harness copies."""
from __future__ import annotations
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

sys.dont_write_bytecode = True
REVIEW = Path(__file__).resolve().parent
PACKAGE = REVIEW.parent / 'implicit-bounded-contact-capture-attempt06'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    testmod = load_module('attempt06_review_test_capture', PACKAGE / 'tests/test_capture.py')
    original_reader = testmod.reader
    reader_text = (PACKAGE / 'capture_reader.py').read_text()
    original = 'candidates_by_gen[gen] += candidates'
    mutant = 'candidates_by_gen[gen] = candidates'
    assert reader_text.count(original) == 1
    mutant_reader = types.ModuleType('attempt06_review_mutant_reader')
    mutant_reader.__file__ = str(PACKAGE / 'capture_reader.py')
    sys.modules[mutant_reader.__name__] = mutant_reader
    exec(compile(reader_text.replace(original, mutant), mutant_reader.__file__, 'exec'), mutant_reader.__dict__)
    testmod.reader = mutant_reader
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testmod.CaptureSinkTests)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (REVIEW / 'reader-cap-mutant-suite.txt').write_text(log.getvalue())
    record = {'reader_cap_mutation': {'from': original, 'to': mutant,
              'original_package_edited': False, 'tests_run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'survived': result.wasSuccessful()}}
    testmod.reader = original_reader
    testmod.CaptureSinkTests.setUpClass()
    try:
        testcase = testmod.CaptureSinkTests('test_positive_sink_stream_identity_join_force_energy_and_acceptance')
        source = testcase.run_sink().decode()
        boundary = testcase.run_sink(mode='candidate-cap-boundary', expected_faces=1).decode()
        record['isolated_combined_reader_cap_controls'] = []
        (REVIEW / 'synthetic-combined-cap-expected.json').write_text(
            json.dumps(testcase.expected(faces=1), indent=2, sort_keys=True) + '\n')
        for count in (125000, 125001):
            rows = []
            for line in boundary.splitlines():
                row = line.split('\t')
                if row[0] == 'GEN_BEGIN':
                    row[6] = str(count)
                elif row[0] == 'FACE':
                    row[7] = row[8] = str(count)
                elif row[0] == 'MAP_SUMMARY':
                    for field in (10, 11, 12, 15, 18, 47):
                        row[field] = str(count)
                elif row[0] == 'GEN_END':
                    row[2] = row[5] = '2'
                    row[3] = row[6] = str(2 * count)
                    row[4] = str(count)
                elif row[0] == 'RUN_END':
                    row[2] = '2'
                    row[3] = str(2 * count)
                    row[6] = str(len(('\n'.join(rows) + '\n').encode()))
                rows.append('\t'.join(row))
                if row[0] in ('FACE', 'MAP_SUMMARY'):
                    duplicate = list(row)
                    duplicate[3 if row[0] == 'FACE' else 7] = '2'
                    rows.append('\t'.join(duplicate))
            synthetic = '\n'.join(rows) + '\n'
            artifact = 'synthetic-combined-cap-' + str(2 * count) + '.tsv'
            (REVIEW / artifact).write_text(synthetic)
            outcome = {'combined_rows': 2 * count, 'rows_in_each_pass': count,
                       'artifact': artifact, 'synthetic_only': True}
            for label, validator in [('original_reader', original_reader), ('per_summary_mutant', mutant_reader)]:
                try:
                    accepted = validator.validate_capture(synthetic, testcase.expected(faces=1))
                except validator.CaptureError as exc:
                    outcome[label] = {'accepted': False, 'reason': str(exc)}
                else:
                    outcome[label] = {'accepted': True, 'status': accepted['status']}
            record['isolated_combined_reader_cap_controls'].append(outcome)
        mismatches = []
        for index, field in enumerate(('input_sha256', 'include_closure_sha256', 'source_archive_sha256',
                                       'patch_sha256', 'binary_sha256', 'pair_roster_sha256', 'face_roster_sha256'), 2):
            rows = source.splitlines()
            cells = rows[1].split('\t')
            cells[index] = 'f' * 64 if cells[index] != 'f' * 64 else 'e' * 64
            rows[1] = '\t'.join(cells)
            try:
                original_reader.validate_capture('\n'.join(rows) + '\n', testcase.expected())
            except original_reader.CaptureError as exc:
                mismatches.append({'field': field, 'rejected': True, 'reason': str(exc)})
            else:
                mismatches.append({'field': field, 'rejected': False})
        record['all_seven_provenance_fields'] = mismatches

        harness_source = (PACKAGE / 'tests/sink_harness.c').read_text()
        anchor = '  int status=fflush(stream);test_flush_calls++;\n'
        assert harness_source.count(anchor) == 1
        trace = anchor + '''  char partpath[8192],line[2048];int footer_seen=0;
  FILE *probe;
  snprintf(partpath,sizeof(partpath),"%s.ccxcap-part-%ld",getenv("CCX_CONTACT_CAPTURE_PATH"),(long)getpid());
  probe=fopen(partpath,"rb");
  if(probe){while(fgets(line,sizeof(line),probe))if(strncmp(line,"RUN_END\\t",8)==0)footer_seen=1;fclose(probe);}
  fprintf(stderr,"flush=%d footer_seen=%d injection=%d\\n",test_flush_calls,footer_seen,
    (test_io_failure_mode==1&&test_flush_calls==1)||(test_io_failure_mode==2&&test_flush_calls==3));
'''
        traced = '#include <string.h>\n#include <unistd.h>\n' + harness_source.replace(anchor, trace)
        record['footer_flush_schedule'] = []
        with tempfile.TemporaryDirectory(prefix='attempt06-review-io-') as tempdir:
            temporary = Path(tempdir)
            (temporary / 'tests').mkdir()
            (temporary / 'capture-sink.inc').symlink_to(PACKAGE / 'capture-sink.inc')
            for name, text in [('documented-call-3', traced),
                               ('actual-footer-call-4', traced.replace('test_flush_calls==3', 'test_flush_calls==4'))]:
                harness_path = temporary / 'tests/sink_harness.c'
                harness_path.write_text(text)
                executable = temporary / name
                compiler = shutil.which('cc') or shutil.which('gcc')
                build = subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-DWJCC_TEST_IO_FAILURE',
                                        str(harness_path), '-lm', '-o', str(executable)], capture_output=True, text=True, check=True)
                output = temporary / (name + '.tsv')
                proc = subprocess.run([str(executable), 'fail-footer-flush'],
                    env=testcase.capture_env(output), capture_output=True, text=True, check=True)
                assert proc.stdout == ''
                (REVIEW / (name + '.trace.txt')).write_text(proc.stderr)
                record['footer_flush_schedule'].append({'probe': name, 'returncode': proc.returncode,
                    'capture_published': output.exists(), 'trace': proc.stderr.splitlines(),
                    'temporary_sidecars_remaining': len(list(temporary.glob(output.name + '.ccxcap-part-*')))})

        with tempfile.TemporaryDirectory(prefix='attempt06-review-disabled-') as tempdir:
            output = Path(tempdir) / 'capture.tsv'
            env = testcase.capture_env(output)
            env.pop('CCX_CONTACT_CAPTURE_PATH', None)
            proc = subprocess.run([str(testmod.CaptureSinkTests.default_harness), 'disabled-path-multistep'],
                                  env=env, capture_output=True, text=True, check=True)
            record['truly_unset_capture_path'] = {'returncode': proc.returncode, 'stdout': proc.stdout,
                                                  'files_created': [p.name for p in Path(tempdir).iterdir()]}
        noenergy = testcase.run_sink(mode='noenergy').decode()
        record['nener_zero_reader_negative_controls'] = []
        for name, index, value in [('unexpected_energy_row', 12, '1'), ('unexpected_energy_value', 17, '0.05')]:
            rows = noenergy.splitlines()
            rownum = next(i for i,row in enumerate(rows) if row.startswith('TRIAL_SUMMARY\t'))
            cells = rows[rownum].split('\t'); cells[index] = value; rows[rownum] = '\t'.join(cells)
            try:
                original_reader.validate_capture('\n'.join(rows)+'\n', testcase.expected())
            except original_reader.CaptureError as exc:
                record['nener_zero_reader_negative_controls'].append({'probe':name,'rejected':True,'reason':str(exc)})
            else:
                record['nener_zero_reader_negative_controls'].append({'probe':name,'rejected':False})
    finally:
        testmod.CaptureSinkTests.tearDownClass()
    (REVIEW / 'coverage-probes.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
    print(json.dumps(record, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
