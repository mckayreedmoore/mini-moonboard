"""Replay all four nonlinear controls from committed compact archives."""
import gzip
import json
from pathlib import Path

from fea import publish_panel_contact_coupon as publish


def test_exact_series_source_and_all_endpoint_replay():
    report = json.loads((publish.OUTPUT/"summary.json").read_text())
    assert report["limits"] == publish.LIMITS
    assert report["case_count"] == 4
    assert set(report["cases"]) == set(publish.CASES)
    expected_sources = {str(p) for p in (*publish.SOURCES, *publish.AUDIT_SOURCES)}
    assert set(report["source_sha256"]) == expected_sources
    for path, digest in report["source_sha256"].items():
        assert publish.sha(Path(path).read_bytes()) == digest
    assert set(report["replay_archives"]) == {
        f"{case}/{name}.gz" for case in publish.CASES for name in publish.FILES}
    replayed = {}
    for case, parameters in publish.CASES.items():
        payload = {}
        for name in publish.FILES:
            path = f"{case}/{name}.gz"
            zipped = (publish.OUTPUT/path).read_bytes()
            raw = gzip.decompress(zipped)
            assert publish.sha(zipped) == report["replay_archives"][path]["gzip_sha256"]
            assert publish.sha(raw) == report["replay_archives"][path]["uncompressed_sha256"]
            payload[name] = raw
        replayed[case] = publish.validate(payload, parameters)
        assert publish.normalized(replayed[case]) == report["cases"][case]
        assert replayed[case]["endpoints"][-1]["time"] == 1.
    assert publish.comparisons(replayed) == report["comparisons"]
