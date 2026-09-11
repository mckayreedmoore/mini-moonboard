"""Authentication failures must precede any expensive native-output replay."""
import hashlib
import json

import pytest

from fea import horizontal_frame_evidence as evidence


def test_artifact_tampering_and_escape_are_rejected(tmp_path):
    path=tmp_path/'frame.dat';path.write_bytes(b'original native bytes')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert evidence.authenticated_file(tmp_path,'frame.dat',digest)==path
    path.write_bytes(b'changed native bytes')
    with pytest.raises(ValueError,match='hash mismatch'):
        evidence.authenticated_file(tmp_path,'frame.dat',digest)
    with pytest.raises(ValueError,match='escaping'):
        evidence.authenticated_file(tmp_path,'../frame.dat',digest)


def test_missing_runtime_json_closure_is_rejected_before_replay(tmp_path):
    (tmp_path/'report.json').write_text(json.dumps({'artifact_sha256':{},'source_sha256':{}}))
    with pytest.raises(ValueError,match='reference closure'):
        evidence.verify_case(tmp_path)


def test_incomplete_batch_inventory_is_rejected(tmp_path):
    (tmp_path/'summary.json').write_text(json.dumps({'cases':[{'case':'c10-k1000'}]}))
    with pytest.raises(ValueError,match='inventory'):
        evidence.verify(tmp_path)
