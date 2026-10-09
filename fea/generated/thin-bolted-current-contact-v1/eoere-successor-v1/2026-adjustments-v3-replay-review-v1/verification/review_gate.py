"""Independent source-only CLI/binding checks; never execute the CAD producer.

Run from repository root: uv run python -B PATH/TO/review_gate.py --out FRESH.json
Temporary fake-producer files are created and removed under this owned folder.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch


ROOT = Path.cwd()
OWN = Path(__file__).resolve().parent
BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
TARGET = Path("scripts/check_eoere_2026_replay_inputs.py")
TARGET_SHA = "d714ccb706443b6ebf4420d8ba5937d4e49612e4290b20538fd4cacaea929c76"
ISSUED = BASE / "2026-adjustments-v10/replay-gate-v2/result.json"
ISSUED_SHA = "a8e9efcf59fe0e4435e012c5d64a032d62e8c8a6ba4bb74f124efbaeec133266"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review():
    assert sha(TARGET) == TARGET_SHA
    assert sha(ISSUED) == ISSUED_SHA
    spec = importlib.util.spec_from_file_location("reviewed_source_gate", TARGET.resolve())
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    frozen, pins = gate.verify()
    issued = json.loads(ISSUED.read_bytes())
    assert len(frozen) == 570 and len(pins) == 572
    assert gate.join_pins(issued["source_sha256"]) == gate.join_pins(
        pins, {str(TARGET): TARGET_SHA}
    )
    controls = gate.controls()
    assert controls == issued["rejected_controls"] and len(controls) == 26
    assert Counter(row["mode"] for row in controls) == Counter(
        changed=9,
        missing=9,
        conflicting_relative_absolute_alias=1,
        missing_replay_binding=3,
        changed_replay_binding=3,
        unexpected_nongenerated_replay_binding=1,
    )
    cache = {name: Path(name).read_bytes() for name in pins}
    read_names = set()

    def cached_reader(path):
        name = str(path.resolve())
        read_names.add(name)
        return cache[name]

    assert gate.verify(cached_reader) == (frozen, pins)
    assert read_names == set(pins)
    checks = [
        "issued receipt exactly binds current 572 contract pins plus gate source",
        "all 26 issued rejection controls independently reproduced",
        "all 570 frozen sources and two report pins are read and authenticated",
    ]

    def rejected(call, error, text=None):
        try:
            call()
        except error as exc:
            assert text is None or text in str(exc), str(exc)
        else:
            raise AssertionError("negative control was accepted")

    with tempfile.TemporaryDirectory(prefix="source-only-", dir=OWN) as directory:
        temporary = Path(directory)
        output = temporary / "binding-output"
        generated = output / "new-output.brep"
        payload = b"independent synthetic generated output; not CAD"

        def generated_reader(path):
            return payload if path == generated else cached_reader(path)

        bindings = {**frozen, str(generated): gate.digest(payload)}
        assert len(gate.verify_replay_bindings(
            {"source_sha256": bindings}, frozen, output, generated_reader
        )) == 571
        replay_rejections = 0
        for name in frozen:
            for missing in (True, False):
                changed = dict(bindings)
                if missing:
                    changed.pop(name)
                else:
                    changed[name] = "0" * 64
                rejected(
                    lambda changed=changed: gate.verify_replay_bindings(
                        {"source_sha256": changed}, frozen, output, generated_reader
                    ),
                    ValueError,
                    "replayed frozen source differs or is missing",
                )
                replay_rejections += 1
        assert replay_rejections == 1140
        alias = str(ROOT / "scripts" / ".." / "scripts" / "thin_bolted_occupied.py")
        changed = {**bindings, alias: "0" * 64}
        rejected(
            lambda: gate.verify_replay_bindings(
                {"source_sha256": changed}, frozen, output, generated_reader
            ), ValueError, "conflicting source bindings",
        )
        same = {**bindings, alias: frozen[str(Path(alias).resolve())]}
        assert len(gate.verify_replay_bindings(
            {"source_sha256": same}, frozen, output, generated_reader
        )) == 571
        checks += [
            "new output binding accepted with correct authenticated payload",
            "each of 570 missing and 570 changed replay bindings rejected",
            "conflicting normalized aliases rejected; equal aliases collapse",
        ]

        def cli(receipt, replay=None, producer=None):
            argv = [str(TARGET), "--out", str(receipt)]
            if replay is not None:
                argv += ["--run-out", str(replay)]
            with patch.object(sys, "argv", argv), patch.object(
                gate.subprocess, "run", side_effect=producer
            ) as invoked, contextlib.redirect_stdout(io.StringIO()):
                gate.main()
            return json.loads(receipt.read_bytes()), invoked.call_count

        receipt = temporary / "default.json"
        default, calls = cli(receipt, producer=AssertionError("default invoked producer"))
        assert calls == 0 and default == issued
        checks.append("default CLI produces issued source-only receipt and never invokes producer")

        for argument in ("receipt", "replay"):
            for kind in ("file", "directory"):
                occupied = temporary / f"occupied-{argument}-{kind}"
                if kind == "file":
                    occupied.write_bytes(b"preserve existing bytes")
                else:
                    occupied.mkdir()
                fresh = temporary / f"fresh-{argument}-{kind}.json"
                with patch.object(gate, "verify", side_effect=AssertionError("read before freshness")):
                    rejected(
                        lambda: cli(occupied if argument == "receipt" else fresh,
                                    occupied if argument == "replay" else None),
                        ValueError, "fresh receipt and replay output paths required",
                    )
                assert not fresh.exists()
                assert kind != "file" or occupied.read_bytes() == b"preserve existing bytes"
        checks.append("existing receipt/replay files and directories rejected before source reads")

        def fake_producer(command, *, check):
            assert check is True
            assert command[:4] == [sys.executable, "-B", str(gate.PRODUCER), "--out"]
            replay = Path(command[4])
            assert not replay.exists()
            (replay / "base").mkdir(parents=True)
            part = replay / "new-generated.brep"
            part.write_bytes(payload)
            source = {**frozen, str(part): gate.digest(payload)}
            for report in (replay / "base/geometry.json", replay / "geometry.json"):
                report.write_text(json.dumps({"source_sha256": source}) + "\n")

        replay = temporary / "fake-replay"
        receipt = temporary / "fake-replay.json"
        successful, calls = cli(receipt, replay, fake_producer)
        assert calls == 1 and successful["mode"] == "VERIFIED_REPLAY"
        assert successful["cad_execution_this_check"] is True
        for name in ("base/geometry.json", "geometry.json"):
            report = replay / name
            assert successful["source_sha256"][str(report)] == sha(report)
        checks.append("optional CLI invokes producer once and authenticates both fresh report bindings")

        for fault in ("child-failure", "missing-report", "missing-generated",
                      "changed-generated", "missing-frozen", "outside-output"):
            replay = temporary / f"fake-{fault}"
            receipt = temporary / f"fake-{fault}.json"

            def defective(command, *, check, fault=fault):
                if fault == "child-failure":
                    raise subprocess.CalledProcessError(7, command)
                fake_producer(command, check=check)
                replay = Path(command[4])
                part = replay / "new-generated.brep"
                report = replay / "geometry.json"
                if fault == "missing-report":
                    report.unlink()
                elif fault == "missing-generated":
                    part.unlink()
                elif fault == "changed-generated":
                    part.write_bytes(payload + b" changed")
                else:
                    data = json.loads(report.read_bytes())
                    if fault == "missing-frozen":
                        data["source_sha256"].pop(next(iter(frozen)))
                    else:
                        data["source_sha256"][str(temporary / "outside.brep")] = "0" * 64
                    report.write_text(json.dumps(data) + "\n")

            rejected(lambda: cli(receipt, replay, defective),
                     (ValueError, FileNotFoundError, subprocess.CalledProcessError))
            assert not receipt.exists()
        checks.append("six fake child/report/source failures stop without a success receipt")

        original_verify = gate.verify
        default_verifications = 0

        def changed_after_child(*args, **kwargs):
            nonlocal default_verifications
            verified = original_verify(*args, **kwargs)
            if not args and not kwargs:
                default_verifications += 1
                if default_verifications == 3:
                    changed = dict(verified[1])
                    changed[next(iter(changed))] = "0" * 64
                    return verified[0], changed
            return verified

        receipt = temporary / "changed-after-child.json"
        with patch.object(gate, "verify", side_effect=changed_after_child):
            rejected(lambda: cli(receipt, temporary / "changed-after-child", fake_producer),
                     ValueError, "canonical replay inputs changed during execution")
        assert default_verifications == 3 and not receipt.exists()
        checks.append("changed contract after fake child execution stops before receipt")

    reused = [
        BASE / "2026-adjustments-v3-review-v1/correctness/review.json",
        BASE / "2026-adjustments-v3-review-v1/structure/receipt.json",
        BASE / "2026-adjustments-v3-review-v1/verification/verification-result-v1.json",
        BASE / "2026-adjustments-v3-review-v1/verification/independent-actual-mesh-check-v1.json",
    ]
    for path in reused:
        record = json.loads(path.read_bytes())
        for name, expected in record.get("source_sha256", {}).items():
            assert sha(Path(name)) == expected, name
    assert sha(TARGET) == TARGET_SHA and sha(ISSUED) == ISSUED_SHA
    sources = [TARGET, ISSUED, *gate.REPORTS, *reused, Path(__file__).resolve()]
    return {
        "schema": "eoere_replay_gate_independent_verification/v1",
        "passed": True,
        "substantial_findings": [],
        "source_sha256": {str(path): sha(path) for path in sources},
        "checks": checks,
        "issued_rejected_control_count": len(controls),
        "complete_frozen_source_count": len(frozen),
        "independent_missing_changed_replay_control_count": replay_rejections,
        "fake_subprocess_only": True,
        "actual_cad_replay_performed": False,
        "original_v3_execution_used_this_gate": False,
        "reused_reviews": [str(path) for path in reused],
        "documented_replay_command": "PYTHONPATH=. .venv/bin/python -B scripts/check_eoere_2026_replay_inputs.py --out FRESH_GATE_RECEIPT.json --run-out FRESH_CAD_DIRECTORY",
        "limits": [
            "Source and CLI verification only; existing nominal geometry, mesh and browser evidence reused within frozen v3 inputs.",
            "Optional real CAD replay remains unperformed; fake reports demonstrate orchestration and binding behavior only.",
            "The documented replay command supplies PYTHONPATH=.; no native/global/browser/full-test or physical qualification work.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("fresh independent review receipt required")
    result = review()
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "checks": len(result["checks"]),
                      "substantial_findings": result["substantial_findings"]}))
