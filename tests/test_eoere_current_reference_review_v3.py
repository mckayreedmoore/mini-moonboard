"""V3 admission controls use temporary files and never solve a response."""

import json
import sys
from pathlib import Path

import pytest

from scripts import eoere_current_reference_review_v3 as current
from scripts import eoere_paired_frame_basis as basis


@pytest.fixture
def captured_case(tmp_path, monkeypatch):
    issued_producer = (current.ROOT / "scripts/replay_eoere_leg_header.py").read_bytes()
    monkeypatch.setattr(basis, "ROOT", tmp_path)
    monkeypatch.setattr(current, "ROOT", tmp_path)

    def write(path, value):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))
        return basis.ref(target)

    material = write("material.json", {"properties": {"EA_N": 100}})
    producer_path = tmp_path / "scripts/replay_eoere_leg_header.py"
    producer_path.parent.mkdir(parents=True)
    producer_path.write_bytes(issued_producer)
    producer = basis.ref(producer_path)
    source_input = write("preparation/inputs.json", {"source": "unchanged"})
    launcher = write("preparation/producer-snapshot.py", {"source": "unchanged"})
    manifest = write("case/operators.json", {
        "schema": "eoere_first_order_original_operator_bundle/v1", "final_ndof": 24,
        "coordinate_map": {
            "schema": "eoere_first_order_owned_coordinate_map/v1",
            "timber": {name: {
                "source": {"name": name, "explicit_plywood_operator": {"EA_N": 100}},
                "index": [list(range(start, start + 6)), list(range(start + 6, start + 12))],
            } for name, start in (("eoere_cleat_left", 0), ("eoere_cleat_right", 12))},
        },
    })
    field = {"operator_bundle": {"manifest": manifest}, "source_inputs": {"plywood_material": material},
             "source_input_review": {"input": source_input},
             "source_sha256": {"scripts/eoere_leg_header_mechanics.py": launcher["sha256"]}}
    binding = write("case/field.json", field)
    certificate = {
        "schema": "eoere_leg_header_plywood_raw_operator_audit/v1",
        "field": binding, "material": material, "source": producer, "captured_launcher": launcher,
        "raw_operator_checks": [
            {"member": name, "dofs": 12, "maximum_K_entry_error": 5.82e-11}
            for name in ("eoere_cleat_left", "eoere_cleat_right")
        ],
        "all_unchanged_owner_map_checks_retained": True,
        "field_q_actions_or_operators_changed": False,
        "physical_stiffness_qualified": False, "production_admission_issued": False,
    }
    write("case/independent-replay-plywood.json", certificate)
    return field, binding, certificate, write


def test_admit_bound_certificate_and_pin_its_captured_manifest(captured_case):
    field, binding, certificate, _ = captured_case
    pins = {}

    assert current.verify_plywood_certificate(field, binding, pins) is None

    for record in (field["operator_bundle"]["manifest"], field["source_input_review"]["input"],
                   certificate["source"], certificate["captured_launcher"]):
        assert pins[record["path"]] == record["sha256"]
    assert "case/independent-replay-plywood.json" in pins


@pytest.mark.parametrize("change", ["duplicate", "excessive_error", "wrong_dofs", "old_material"])
def test_reject_wrong_certificate_before_returning_an_intake(captured_case, change):
    field, binding, certificate, write = captured_case
    if change == "duplicate":
        certificate["raw_operator_checks"][1] = dict(certificate["raw_operator_checks"][0])
    elif change == "excessive_error":
        certificate["raw_operator_checks"][0]["maximum_K_entry_error"] = 1e-6
    elif change == "wrong_dofs":
        certificate["raw_operator_checks"][0]["dofs"] = 24
    else:
        certificate["material"] = {"path": "old.json", "sha256": "0" * 64}
    write("case/independent-replay-plywood.json", certificate)

    with pytest.raises(ValueError):
        current.verify_plywood_certificate(field, binding, {})


@pytest.mark.parametrize("source", ["manifest", "source", "captured_launcher"])
def test_reject_changed_manifest_or_replay_source_bytes(captured_case, source):
    field, binding, certificate, write = captured_case
    record = field["operator_bundle"]["manifest"] if source == "manifest" else certificate[source]
    write(record["path"], {"changed": True})

    with pytest.raises(ValueError, match="hash-bound replay source changed"):
        current.verify_plywood_certificate(field, binding, {})


def test_reject_conflicting_previously_loaded_certificate_pin(captured_case):
    field, binding, _, _ = captured_case

    with pytest.raises(ValueError, match="conflicting replay source pin"):
        current.verify_plywood_certificate(
            field, binding, {"case/independent-replay-plywood.json": "0" * 64}
        )


@pytest.mark.parametrize("substitution", ["material", "copied_producer", "changed_producer"])
def test_reject_hash_valid_foreign_replay_producer(captured_case, substitution):
    field, binding, certificate, write = captured_case
    if substitution == "material":
        certificate["source"] = field["source_inputs"]["plywood_material"]
    elif substitution == "copied_producer":
        duplicate = current.ROOT / "copied-replay.py"
        duplicate.write_bytes((current.ROOT / certificate["source"]["path"]).read_bytes())
        certificate["source"] = basis.ref(duplicate)
    else:
        certificate["source"] = write(certificate["source"]["path"], {"source": "changed"})
    write("case/independent-replay-plywood.json", certificate)

    with pytest.raises(ValueError, match="issued plywood replay producer"):
        current.verify_plywood_certificate(field, binding, {})


@pytest.mark.parametrize("substitution", ["material", "copied_launcher", "changed_launcher"])
def test_reject_hash_valid_foreign_captured_launcher(captured_case, substitution):
    field, binding, certificate, write = captured_case
    if substitution == "material":
        certificate["captured_launcher"] = field["source_inputs"]["plywood_material"]
    elif substitution == "copied_launcher":
        duplicate = current.ROOT / "copied-launcher.py"
        duplicate.write_bytes((current.ROOT / certificate["captured_launcher"]["path"]).read_bytes())
        certificate["captured_launcher"] = basis.ref(duplicate)
    else:
        certificate["captured_launcher"] = write(
            certificate["captured_launcher"]["path"], {"source": "changed"}
        )
    write("case/independent-replay-plywood.json", certificate)

    with pytest.raises(ValueError, match="captured launcher"):
        current.verify_plywood_certificate(field, binding, {})


@pytest.mark.parametrize("target", [current.PREVIOUS, current.VALIDATOR, current.OWN])
def test_changed_loaded_adapter_or_helper_stops_before_command_dispatch(monkeypatch, target):
    original = Path.read_bytes

    def changed(path):
        data = original(path)
        return data + b"\n# changed source\n" if path.resolve() == target else data

    monkeypatch.setattr(Path, "read_bytes", changed)

    with pytest.raises(ValueError, match="loaded V3 replay intake source changed"):
        current.main()


def own_bank():
    path = current.ROOT / "docs/bolted-frame-development/owner-frame-v9/response-bank.json"
    if not path.exists():
        pytest.skip("current V9 public bank is not present")
    bank = json.loads(path.read_bytes())
    if not all((current.ROOT / row["field"]["path"]).exists() for row in bank["cases"]):
        pytest.skip("restore the documented V9 response bank for this integration control")
    from scripts import eoere_v9_analysis as analysis

    bindings = analysis.context(bank["physical_geometry"]["sha256"], bank["physical_geometry_raw"]["sha256"])
    return analysis, bindings, bank


@pytest.mark.recovered_evidence
def test_current_six_fields_pass_v3_intake_with_all_successor_sources_pinned():
    analysis, bindings, _ = own_bank()

    _, fields, pins = current.Intake(bindings, analysis).load()

    assert len(fields) == 6
    for path in (current.PREVIOUS, current.VALIDATOR, current.OWN):
        binding = basis.ref(path)
        assert pins[binding["path"]] == binding["sha256"]
    for _, _, binding, field in fields:
        assert field["operator_bundle"]["manifest"]["path"] in pins
        assert str(Path(binding["path"]).parent / "independent-replay-plywood.json") in pins


@pytest.mark.recovered_evidence
@pytest.mark.parametrize("kind", ["preflight", "bracing-report"])
def test_bad_certificate_stops_each_dispatch_path_before_output(monkeypatch, kind):
    analysis, bindings, bank = own_bank()
    bad_path = (current.ROOT / bank["cases"][0]["independent_plywood_replay"]["path"]).resolve()
    replay = json.loads(bad_path.read_bytes())
    replay["raw_operator_checks"][0]["maximum_K_entry_error"] = 1e-6
    bad_bytes = json.dumps(replay).encode()
    original = Path.read_bytes

    def changed(path):
        return bad_bytes if path.resolve() == bad_path else original(path)

    output = analysis.BASE / "pytest-v3-never-created"
    assert not output.exists()
    monkeypatch.setattr(Path, "read_bytes", changed)
    monkeypatch.setattr(sys, "argv", [
        str(current.OWN), kind, "--analysis-module", "scripts.eoere_v9_analysis",
        "--receipt-sha256", bindings["receipt"]["sha256"],
        "--physical-sha256", bindings["physical_geometry"]["sha256"],
        "--review", str(output / "review"), "--bracing-out", str(output / "bracing"),
        "--public-folder", str(current.ROOT / "docs/bolted-frame-development/owner-frame-v9"),
    ])

    with pytest.raises(ValueError, match="operator error"):
        current.main()

    assert not output.exists()
