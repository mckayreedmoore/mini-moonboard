"""Reject invalid stiffness comparisons before creating publication artifacts."""
import json

import pytest

from fea import publish_timber_structural as publisher


@pytest.mark.parametrize(("change", "message"), [
    ("sizes", "Require one 40mm and one 60mm result"),
    ("geometry", "Mesh comparison inputs differ"),
    ("modulus", "Mesh comparison inputs differ"),
    ("candidate", "Unexpected candidate"),
    ("frozen_candidate", "Unexpected candidate"),
])
def test_invalid_comparison_never_publishes(tmp_path, monkeypatch, change, message):
    output = tmp_path/"published"
    monkeypatch.setattr(publisher, "OUTPUT", output)
    rows = [{"mesh_size_mm": size, "candidate": publisher.KEY,
             "frozen_geometry": {"candidate": publisher.KEY}, "modulus_mpa": 7000.}
            for size in (40., 60.)]
    if change == "sizes":
        rows[1]["mesh_size_mm"] = 40.
    elif change == "geometry":
        rows[1]["frozen_geometry"]["revision"] = "different"
    elif change == "modulus":
        rows[1]["modulus_mpa"] = 6000.
    elif change == "candidate":
        rows[0]["candidate"] = "historical-candidate"
    else:
        for row in rows:
            row["frozen_geometry"]["candidate"] = "historical-candidate"
    paths = [tmp_path/f"result{index}.json" for index in range(2)]
    for path, row in zip(paths, rows, strict=True):
        path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match=message):
        publisher.publish(paths)
    assert not output.exists()
