"""Run from repository root in documented FEA Docker image; no solver launch."""
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.floor_contact import integrated_weights
from fea.full_frame_mortar import audit, verify_deck

ROOT = Path(__file__).parent
manifest = json.loads((ROOT/"weight_validation.json").read_text())
for name, sha in manifest["validator_source_sha256"].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
for formulation, witness in manifest["formulations"].items():
    with tarfile.open(ROOT/(formulation+".tar.gz")) as archive:
        deck = archive.extractfile("frame.inp").read()
        context = archive.extractfile("frame.json").read()
        dat = archive.extractfile("frame.dat").read()
    assert hashlib.sha256(context).hexdigest() == witness["terminal_context_sha256"]
    assert hashlib.sha256(dat).hexdigest() == witness["dat_sha256"]
    record = json.loads(context)
    nodes, elements, *_ = verify_deck(deck.decode(), record)
    expected = integrated_weights(elements, nodes)
    actual = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    assert expected.keys() == actual.keys()
    assert all(math.isclose(actual[n], expected[n], rel_tol=1e-10, abs_tol=1e-8) for n in actual)
    assert hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest() == witness["integrated_weights_sha256"]
    try:
        audit(deck.decode(), dat.decode(), record)
    except ValueError as error:
        assert str(error) == witness["production_audit_error"]
        print(formulation, len(expected), "weights reintegrated; expected rejected audit:", error)
    else:
        raise AssertionError("Historical rejected audit unexpectedly accepted")
