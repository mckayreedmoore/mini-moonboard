"""Finite handoff inventory and archived diagnostic provenance, without CAD runs."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def test_each_exported_connection_has_exactly_one_boundary_disposition():
    document = Path("docs/joint-boundary-dispositions.md").read_text()
    families = re.findall(r"^\| ([a-z]+) \| (\d+) \| `([^`]+)` \|$", document, re.MULTILINE)
    assert len(families) == 12
    assert len({name for name, _, _ in families}) == 12
    with Path("exports/top-joint-development/top-joint-development_connections.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len({r["connection"] for r in rows}) == 278
    actual = Counter()
    for row in rows:
        matches = [name for name, _, pattern in families if re.fullmatch(pattern, row["connection"])]
        assert len(matches) == 1, (row["connection"], matches)
        actual[matches[0]] += 1
    assert actual == {name: int(count) for name, count, _ in families}
    dispositions = document.split("## Evidence shared by the families", 1)[1]
    for name, _, _ in families:
        assert len(re.findall(rf"^\| {name} \|", dispositions, re.MULTILINE)) == 1


def test_handoff_diagnostics_still_match_their_recorded_sources():
    for filename in ("top-joint-engagement.json", "top-joint-ply-profiles.json"):
        report = json.loads((Path("docs")/filename).read_text())
        assert report["variant"] == "top-joint-development"
        assert report["qualified_for_design"] is False
        assert report["sources"]
        for source, digest in report["sources"].items():
            assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == digest, source


def test_review_packet_local_deliverable_links_exist():
    for filename in ("candidate-review-packet.md", "joint-boundary-dispositions.md", "hardware-fit-dispositions.md"):
        document = Path("docs")/filename
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if "://" not in target:
                assert (document.parent/target.split("#", 1)[0]).exists(), (filename, target)
