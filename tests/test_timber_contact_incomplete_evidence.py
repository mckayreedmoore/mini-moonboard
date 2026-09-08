"""Preserve the rejected attempt without treating partial load as acceptance."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from fea.timber_panel_contact_audit import audit_with_history


def test_partial_attempt_identity_and_full_load_rejection():
    raw = Path("fea/results/timber-panel-contact-incomplete/attempt.tar.gz").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "dde03df1a09dbccc0dc57e50a47788c5cab3c0c92be0a48500b533c6ce9cbd5c"
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        files = {Path(m.name).name: archive.extractfile(m).read() for m in archive.getmembers()}
    assert set(files) == {"input.json", "contact.inp", "contact.dat", "contact.log",
                          "contact.sta", "contact.cvg", "launch.json", "timber_panel_contact.py"}
    info, launch = json.loads(files["input.json"]), json.loads(files["launch.json"])
    assert hashlib.sha256(files["input.json"]).hexdigest() == launch["input_sha256"]
    assert hashlib.sha256(files["contact.inp"]).hexdigest() == info["deck_sha256"] == launch["deck_sha256"]
    assert hashlib.sha256(files["timber_panel_contact.py"]).hexdigest() == info["source_sha256"]["fea/timber_panel_contact.py"]
    assert launch["timeout_seconds"] == 600
    records = [line.split() for line in files["contact.sta"].decode().splitlines() if line.split() and line.split()[0].isdigit()]
    assert [float(r[4]) for r in records] == [.025, .05, .0875, .14375, .228125]
    with pytest.raises(ValueError, match="Incomplete nodal endpoints"):
        audit_with_history(files["contact.dat"].decode(), info, files["contact.sta"].decode())
