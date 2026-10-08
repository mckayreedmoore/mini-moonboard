"""Reuse the immutable A12 runner, isolating only its floor observation.

Frozen SciPy power() deduplicates its receiver in place. Copies of floor B
rows prevent that observer from reordering live ports. No solver is copied,
no historical q is consumed, and the actual new caller is bound explicitly.
"""
from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import thin_bolted_frame_mechanics as frame

PACKET = Path(__file__).resolve().parent
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_SHA256 = frame.sha(Path(__file__))
FROZEN_DRIVER = "fea/generated/thin-bolted-direct-contact-a12-v1/runner.py"
FROZEN_DRIVER_SHA256 = "ea3b310657b66869b59c35b5cb126280df5b042b8c50e9848d463b3a9b5eef01"
FROZEN_GATE_SHA256 = "6797388b8a99e1f2d510d69c22ce932283b8128607842337e9cea300ae3fb5be"
PROBE_PINS = {
    "fea/generated/thin-bolted-direct-contact-a12-v1/method-input.json": "6257c7e9a300ed46ffdea26f416cbd1d3f155b0630413957b5128a6d2eeea1a9",
    "fea/generated/thin-bolted-direct-contact-a12-v1/operator-inputs.json": "16ef6d3228cd0cd8cc5a7b5d602a6ecf8d41a90b436089552bef3ac5eab945f3",
    "fea/generated/thin-bolted-direct-contact-a12-v1/operators.npz": "a45f9a1fe27349523f3617c99ad145d341d722a775184a6b650aadc1e73d5ffa"}


def load_leaf(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if frame.sha(ROOT / FROZEN_DRIVER) != FROZEN_DRIVER_SHA256:
    raise ValueError("preserve the immutable first A12 runner")
base = load_leaf("immutable_complete_a12_v1_for_observer_v2", ROOT / FROZEN_DRIVER)
gate = load_leaf("complete_a12_observer_isolation_gate_v2", PACKET / "admission.py")
require = base.require
KNOWN_ENABLED_FLOOR_HOSTS = base.lean.reused.enabled_floor_hosts
KNOWN_BASE_METHOD_SOURCES = base.method_sources
KNOWN_CAPTURE = base.capture_operators
KNOWN_METADATA = base.add_complete_metadata
KNOWN_WRITE_JSON = base.write_json
ORIGINAL_BASE_GATE = base.admission


def enabled_floor_hosts_readonly(linear, material, tangents):
    """Same known observer on copied B only; preserve metadata and live rows."""
    return KNOWN_ENABLED_FLOOR_HOSTS(linear, material,
        [{**row, "B": row["B"].copy()} for row in tangents])


def method_sources():
    require(frame.sha(Path(__file__)) == LOADED_SHA256, "loaded isolation wrapper changed")
    # Receipt forwarding may temporarily bind outer ownership. Authenticate
    # the genuine frozen implementation under its own original guards first.
    with patch.multiple(base, OWN=FROZEN_DRIVER, LOADED_SHA256=FROZEN_DRIVER_SHA256,
                        admission=ORIGINAL_BASE_GATE):
        pins = KNOWN_BASE_METHOD_SOURCES()
    pins = base.lean.merge_pins(pins, gate.source_pins(), PROBE_PINS,
        {OWN: LOADED_SHA256,
         base.relative(PACKET / "test_runner.py"): frame.sha(PACKET / "test_runner.py"),
         base.relative(PACKET / "test_admission.py"): frame.sha(PACKET / "test_admission.py")})
    require(pins[FROZEN_DRIVER] == FROZEN_DRIVER_SHA256
            and ORIGINAL_BASE_GATE.LOADED_PRODUCER_SHA256 == FROZEN_GATE_SHA256,
            "frozen implementation ownership changed")
    gate.linear.verify_pins(pins)
    return pins


@contextmanager
def receipt_owner():
    """Explicit outer receipt context; never spoof implementation __file__."""
    with patch.multiple(base, OWN=OWN, LOADED_SHA256=LOADED_SHA256,
                        method_sources=method_sources, admission=gate):
        yield


def freeze_method_inputs(path, *, reviewed_checks):
    original_dump = base.common.finished.writer.dump

    def dump(value):
        if value.get("schema") == base.RECEIPT_SCHEMA:
            value["observer_isolation"] = gate.observer_isolation_contract()
        return original_dump(value)

    with receipt_owner(), patch.object(base.common.finished.writer, "dump", dump):
        return base.freeze_method_inputs(path, reviewed_checks=reviewed_checks)


def read_method_inputs(path, expected_sha):
    with receipt_owner():
        receipt = base.read_method_inputs(path, expected_sha)
    require(receipt["observer_isolation"] == gate.observer_isolation_contract(),
            "new observer isolation receipt contract differs")
    return receipt


@contextmanager
def forwarding_scope(command):
    """Bind the new caller before capture/state identity; restore every seam."""
    original_common_metadata = base.common.bind_common_metadata

    def capture(*args, **kwargs):
        return KNOWN_CAPTURE(*args, **{**kwargs, "command": command})

    def metadata(*args, **kwargs):
        report = KNOWN_METADATA(*args, **{**kwargs, "command": command})
        report["parameters"]["complete_timber_a12_driver_sha256"] = LOADED_SHA256
        execution = report["complete_timber_a12_execution"]
        execution["loaded_driver_sha256"] = LOADED_SHA256
        execution["loaded_admission_sha256"] = gate.LOADED_PRODUCER_SHA256
        execution["observer_isolation"] = gate.observer_isolation_contract()
        return report

    def common_metadata(report, system, pins, _inner_command):
        return original_common_metadata(report, system, pins, command)

    def write_json(path, value):
        if value.get("schema") == "thin_bolted_complete_timber_a12_interrupted/v1":
            value = {**value, "command": command,
                     "observer_isolation": gate.observer_isolation_contract()}
        return KNOWN_WRITE_JSON(path, value)

    with (patch.object(base.lean.reused, "enabled_floor_hosts", enabled_floor_hosts_readonly),
          patch.object(base, "capture_operators", capture),
          patch.object(base, "add_complete_metadata", metadata),
          patch.object(base, "write_json", write_json),
          patch.object(base, "admission", gate),
          patch.object(base.common, "bind_common_metadata", common_metadata)):
        yield


def parse_options(arguments):
    with patch.object(base, "PACKET", PACKET):
        return base.parse_options(arguments)


def run_case(options, arguments, receipt):
    command = [sys.executable, str(Path(__file__).resolve()), *arguments]
    with forwarding_scope(command):
        return base.run_case(options, arguments, receipt)


def main():
    arguments = sys.argv[1:]
    options = parse_options(arguments)
    receipt = read_method_inputs(options.method_input, options.method_input_sha256)
    expected = {"cases": options.cases, "wood_bedding": options.wood_bedding,
        "intervals": options.intervals, "contact_edge": options.contact_edge,
        "newton_limit": options.newton_limit, "wall_seconds": options.wall_seconds}
    require(receipt["fixed_options"] == expected, "actual invocation differs from parent-frozen options")
    require(base.os.environ.get("OPENBLAS_NUM_THREADS") == "1", "serialized case requires OPENBLAS_NUM_THREADS=1")
    for path in (options.out, options.out.with_name(options.out.name + ".interrupted.json"),
                 PACKET / "operator-inputs.json", PACKET / "operators.npz",
                 PACKET / "final-branch-inputs.json", PACKET / "final-branch-operators.npz"):
        require(not path.exists(), "preserve existing output: " + str(path))
    run_case(options, arguments, receipt)


if __name__ == "__main__":
    main()
