"""Fail-closed publication guards; no solver execution."""
import json

import pytest

from fea import publish_panel_contact_coupon as publish


def test_existing_output_refuses_before_read(monkeypatch, tmp_path):
    monkeypatch.setattr(publish, "OUTPUT", tmp_path)
    monkeypatch.setattr(publish, "DIRECTORY", tmp_path/"missing")
    with pytest.raises(FileExistsError):
        publish.main()


def test_wrong_series_refuses_without_output(monkeypatch, tmp_path):
    monkeypatch.setattr(publish, "OUTPUT", tmp_path/"output")
    monkeypatch.setattr(publish, "DIRECTORY", tmp_path)
    with pytest.raises(ValueError, match="two-by-two"):
        publish.main()
    assert not publish.OUTPUT.exists()


def payload():
    text, info = publish.coupon.deck(publish.coupon.SOURCE.read_text(), 10000., .25)
    info.update(source_sha256={str(p): publish.coupon.digest(p) for p in publish.SOURCES},
                deck_sha256=publish.sha(text.encode()))
    raw = {n: b"" for n in publish.FILES}
    raw["input.json"] = json.dumps(info).encode()
    raw["coupon.inp"] = text.encode()
    raw["launch.json"] = json.dumps({"input_sha256": publish.sha(raw["input.json"]),
        "deck_sha256": info["deck_sha256"], "source_sha256": info["source_sha256"],
        "timeout_seconds": 60}).encode()
    return raw


@pytest.mark.parametrize("defect", ["context", "deck", "launch", "missing"])
def test_changed_identity_rejects(defect):
    raw = payload()
    if defect == "context":
        info = json.loads(raw["input.json"])
        info["modulus_mpa"] = 8000.
        raw["input.json"] = json.dumps(info).encode()
    elif defect == "deck":
        raw["coupon.inp"] += b"** changed\n"
    elif defect == "launch":
        raw["launch.json"] = b"{}"
    else:
        del raw["coupon.dat"]
    with pytest.raises(ValueError):
        publish.validate(raw, (10000., .25))
