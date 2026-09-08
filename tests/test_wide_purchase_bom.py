"""Current hardware quantities replay without importing CAD."""
import csv
import io
import json

import pytest

from scripts import wide_purchase_bom as bom


def test_published_csv_replays_and_matches_current_hardware():
    text = bom.build()
    assert bom.OUTPUT.read_text() == text
    rows = list(csv.DictReader(io.StringIO(text)))
    bolts = {float(r["nominal_length_mm"]): int(r["quantity"]) for r in rows if r["item"] == "bolt"}
    assert bolts == {63.5: 6, 76.2: 8, 95.25: 8, 152.4: 2}
    assert {r["item"]: int(r["quantity"]) for r in rows if r["item"] != "bolt"} == {
        "nut": 24, "washer": 48, "insert": 56, "machine screw": 56, "angle": 18, "connector screw": 108}
    for row in rows:
        assert row["source_url"].startswith("https://") and row["qualification"]
        if row["nominal_length_mm"]:
            assert float(row["nominal_length_in"])*25.4 == pytest.approx(float(row["nominal_length_mm"]))


@pytest.mark.parametrize("defect", ["source", "inventory"])
def test_changed_source_or_inventory_fails_closed(tmp_path, monkeypatch, defect):
    manifest = json.loads((bom.EXPORT/"manifest.json").read_text())
    if defect == "source":
        manifest["sources"]["docs/panel-insert-reference.json"] = "wrong"
    for name in ("parts", "connections"):
        filename = f"{bom.KEY}_{name}.csv"
        data = (bom.EXPORT/filename).read_bytes()
        (tmp_path/filename).write_bytes(data+b"changed" if defect == "inventory" else data)
    (tmp_path/"manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(bom, "EXPORT", tmp_path)
    with pytest.raises(ValueError, match="differs"):
        bom.build()
