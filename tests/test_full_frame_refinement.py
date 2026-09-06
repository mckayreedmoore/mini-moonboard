import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_full_frame_mortar import fixture, output

from fea.full_frame_refinement import (
    digest,
    equilibrium_print_bound,
    print_bounds,
    read_archive,
    replay,
    verified_baseline,
)


def files_fixture():
    deck, record, rows = fixture()
    record.update(exit_code=0, elapsed_seconds=1., status="DIAGNOSTIC FIXTURE", prelaunch_sha256={})
    files = {"frame.inp": deck.encode(), "frame.dat": output(rows).encode(),
             "frame.sta": b"1 1 1 1 1.0 1.0 1.0\n2 1 1 1 2.0 1.0 1.0\n"}
    record["output_sha256"] = {n: digest(v) for n, v in files.items() if n != "frame.inp"}
    files["frame.json"] = json.dumps(record).encode()
    return files


def test_replay_reports_all_vectors_and_patch_moment_translation():
    files = files_fixture()
    result = replay(files)
    assert len(result["diagnostic_endpoints"]) == 2
    for endpoint in result["diagnostic_endpoints"]:
        assert endpoint["global_gate_pass"]
        assert len(endpoint["loaded_node_displacement_mm"]) == 5
        for patch in endpoint["patches"].values():
            from fea.floor_contact_results import cross
            translated = cross(patch["reference_mm"], patch["bottom_reaction_n"])
            assert patch["moment_about_origin_nmm"] == pytest.approx(
                [v+d for v, d in zip(patch["moment_about_bottom_centroid_nmm"], translated, strict=True)])


@pytest.mark.parametrize("mutation", ["digest", "duplicate_time", "missing_time", "missing_weights"])
def test_replay_rejects_corrupt_or_incomplete_output(mutation):
    files = deepcopy(files_fixture())
    record = json.loads(files["frame.json"])
    if mutation == "digest":
        files["frame.dat"] += b"changed"
    elif mutation == "duplicate_time":
        files["frame.sta"] += files["frame.sta"]
        record["output_sha256"]["frame.sta"] = digest(files["frame.sta"])
    elif mutation == "missing_time":
        files["frame.sta"] = b"1 1 1 1 0.5 0.5 0.5\n"
        record["output_sha256"]["frame.sta"] = digest(files["frame.sta"])
    else:
        del record["nodal_volume_mm3"]["1"]
    files["frame.json"] = json.dumps(record).encode()
    with pytest.raises(ValueError):
        replay(files)


@pytest.mark.parametrize("mutation", [None, "archive", "witness_digest", "weight_digest"])
def test_standalone_baseline_is_bound_to_published_integration_witness(tmp_path, monkeypatch, mutation):
    files = files_fixture()
    record = json.loads(files["frame.json"])
    weights = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    witness = {"weight_validation_pass": True, "terminal_context_sha256": digest(files["frame.json"]),
               "dat_sha256": digest(files["frame.dat"]), "deck_sha256": record["deck_sha256"],
               "integrated_weights_sha256": digest(json.dumps(weights, sort_keys=True).encode()),
               "weight_count": len(weights), "negative_weight_count": sum(v < 0 for v in weights.values())}
    if mutation == "weight_digest":
        witness["integrated_weights_sha256"] = "stale weights"
    validation = json.dumps({"formulations": {"mortar": witness}}).encode()
    report = {"weight_validation_sha256": digest(validation), "formulations": {"mortar": {
        "archive": "mortar.tar.gz", "archive_sha256": digest(b"archive fixture"),
        "archive_contents_sha256": {n: digest(v) for n, v in files.items()}}}}
    (tmp_path/"mortar.tar.gz").write_bytes(b"changed" if mutation == "archive" else b"archive fixture")
    (tmp_path/"weight_validation.json").write_bytes(validation+b" " if mutation == "witness_digest" else validation)
    (tmp_path/"report.json").write_text(json.dumps(report))
    monkeypatch.setattr("fea.full_frame_refinement.read_archive", lambda path: files)
    if mutation is None:
        assert verified_baseline(tmp_path)[1] == files
    else:
        with pytest.raises(ValueError, match="Baseline"):
            verified_baseline(tmp_path)


def test_print_rounding_bound_uses_rf_lever_arms_and_absolute_negative_weights():
    data = ("forces for set GROUND_LEFT and time 2\n1 1.234567E+02 2.345678E+01 3.456789E+02\n"
            "\ndisplacements for set WOODN and time 2\n2 1.234567E-01 2.345678E-02 0.000000E+00\n")
    bounds = print_bounds(data)
    assert bounds["forces", "GROUND_LEFT", 2.][1] == pytest.approx((5e-5, 5e-6, 5e-5))
    result = equilibrium_print_bound(2., bounds, {2: -100.}, {"LEFT": {1: (10., 20., -100.)}}, {"LEFT": [1]}, [2])
    magnitude = 100*6e-10*9806.65
    assert result["moment_nmm"] == pytest.approx([
        20*5e-5+100*5e-6+(magnitude+240)*5e-9,
        100*5e-5+10*5e-5+(magnitude+240)*5e-8,
        10*5e-6+20*5e-5])


@pytest.mark.parametrize("name", ["baseline", "0.125", "0.0625"])
def test_published_refinement_replays_exact_raw_vectors(name):
    root = Path("fea/results/full_frame_refinement")
    report = json.loads((root/"report.json").read_text())
    assert digest((root/"publisher.py").read_bytes()) == report["publisher_sha256"]
    baseline_path, baseline = verified_baseline(Path("fea/results/full_frame_mortar"))
    assert digest(baseline_path.read_bytes()) == report["baseline_archive_sha256"]
    item = report["runs"][name]
    if name == "baseline":
        files = baseline
    else:
        path = root/item["archive"]
        assert path.stat().st_size < 100_000_000
        assert digest(path.read_bytes()) == item["archive_sha256"]
        files = read_archive(path)
        assert {n: digest(v) for n, v in files.items()} == item["archive_contents_sha256"]
    actual = replay(files)
    assert actual == {k: item[k] for k in actual}
    record = json.loads(files["frame.json"])
    assert record["nodal_volume_mm3"] == json.loads(baseline["frame.json"])["nodal_volume_mm3"]
    increment = record["increment"]
    assert files["frame.inp"] == baseline["frame.inp"].replace(b"0.25,1,1e-6,0.25", f"{increment},1,1e-6,{increment}".encode())
    common = set.intersection(*({e["time"] for e in r["diagnostic_endpoints"]} for r in report["runs"].values()))
    assert report["common_accepted_times"] == sorted(common)
