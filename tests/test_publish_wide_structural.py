"""Lightweight wrapper isolation and actual candidate-validation checks."""
import json
from pathlib import Path

import pytest

from fea import publish_wide_structural as archive


@pytest.mark.parametrize("fails", [False, True])
def test_publisher_settings_and_complete_provenance_are_restored(monkeypatch, fails):
    underlying = archive.publisher
    saved = underlying.KEY, underlying.OUTPUT, underlying.PUBLISHER_SOURCES
    inputs = [Path("mesh60.json"), Path("mesh40.json")]
    called = []

    def publish(results):
        called.append(results)
        assert underlying.KEY == "wide-principal-development"
        assert underlying.OUTPUT == Path("fea/results/wide-principal")
        assert set(underlying.PUBLISHER_SOURCES) == set(saved[2]) | {"fea/publish_wide_structural.py"}
        assert {"fea/publish_timber_structural.py", "fea/publish_bearing_structural.py",
                "fea/publish_wide_structural.py"} <= set(underlying.PUBLISHER_SOURCES)
        if fails:
            raise ValueError("simulated validation failure")
        return "published"

    monkeypatch.setattr(underlying, "publish", publish)
    if fails:
        with pytest.raises(ValueError, match="simulated"):
            archive.publish(inputs)
    else:
        assert archive.publish(inputs) == "published"
    assert called == [inputs]
    assert (underlying.KEY, underlying.OUTPUT, underlying.PUBLISHER_SOURCES) == saved


@pytest.mark.parametrize("wrong_field", ["candidate", "geometry"])
def test_underlying_validator_rejects_foreign_candidates_before_archival(tmp_path, monkeypatch, wrong_field):
    paths = []
    for size in (60, 40):
        row = {"mesh_size_mm": size, "modulus_mpa": 7000.,
               "candidate": "timber-base-development" if wrong_field == "candidate" else archive.KEY,
               "frozen_geometry": {"candidate": "timber-base-development" if wrong_field == "geometry" else archive.KEY}}
        path = tmp_path/f"mesh{size}.json"
        path.write_text(json.dumps(row))
        paths.append(path)
    output = tmp_path/"published"
    monkeypatch.setattr(archive, "OUTPUT", output)
    saved = archive.publisher.KEY, archive.publisher.OUTPUT, archive.publisher.PUBLISHER_SOURCES
    with pytest.raises(ValueError, match="Unexpected candidate"):
        archive.publish(paths)
    assert not output.exists()
    assert (archive.publisher.KEY, archive.publisher.OUTPUT, archive.publisher.PUBLISHER_SOURCES) == saved
