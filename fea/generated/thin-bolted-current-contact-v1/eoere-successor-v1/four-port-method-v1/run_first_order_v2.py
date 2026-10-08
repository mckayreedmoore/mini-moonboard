"""Serialized wrapper: capture exact original operators before one fresh solve.

The frozen first-order runner owns preparation, wall limits and recovery.
This wrapper adds replayable raw operators and truthful outer execution identity.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
BUNDLE = OWN.with_name("operator_bundle.py")
SPEC = importlib.util.spec_from_file_location("eoere_first_order_sparse_export", BUNDLE)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)
core, frame = bundle.core, bundle.frame
LOADED_SHA = frame.sha(OWN)
LOADED_BUNDLE_SHA = frame.sha(BUNDLE)
FROZEN_EXECUTE, FROZEN_MAIN, FROZEN_WRITE = core.execute, core.main, core.write_exclusive
SCHEMA = "eoere_first_order_common_shaft_four_port_candidate/v2"


def runtime_pins(extra=None):
    pins = bundle.source_pins(extra)
    for path, digest in ((OWN, LOADED_SHA), (BUNDLE, LOADED_BUNDLE_SHA)):
        bundle.require(frame.sha(path) == digest, "loaded sparse export wrapper changed")
        pins[str(path.relative_to(frame.ROOT))] = digest
    return pins


def bundle_paths(out):
    out = Path(out)
    return out.with_suffix(out.suffix+".operators.npz"), out.with_suffix(out.suffix+".operators.json")


@contextmanager
def execution_context(out, command):
    """Only parent serialized use; restore all three callbacks on every exit."""
    arrays_path, manifest_path = bundle_paths(out)
    bundle.require(not arrays_path.exists() and not manifest_path.exists(), "preserve existing operator export")
    context = {"operator_bundle": None, "bundle_pins": {}, "execute_calls": 0}
    outer = {"command": list(command), "loaded_driver_path": bundle.artifact_path(OWN), "loaded_driver_sha256": LOADED_SHA,
        "loaded_operator_export_path": bundle.artifact_path(BUNDLE), "loaded_operator_export_sha256": LOADED_BUNDLE_SHA,
        "frozen_inner_driver_path": bundle.artifact_path(bundle.CORE), "frozen_inner_driver_sha256": bundle.CORE_SHA,
        "nested_first_order_execution_is_reused_internal_call": True,
        "one_preparation_one_fresh_search": True, "historical_q_or_forces_used": False}

    def execute(prepared, **kwargs):
        context["execute_calls"] += 1
        bundle.require(context["execute_calls"] == 1 and kwargs["command"] == list(command),
                       "one truthful fresh execution required")
        pins = runtime_pins(kwargs["pins"])
        pointer = bundle.snapshot(prepared, arrays_path=arrays_path, manifest_path=manifest_path,
                                  pins=pins, command=list(command))
        context["operator_bundle"] = pointer
        context["bundle_pins"] = {record["path"]: record["sha256"] for record in pointer.values()}
        pins = runtime_pins({**pins, **context["bundle_pins"]})
        field = FROZEN_EXECUTE(prepared, **{**kwargs, "pins": pins})
        bundle.require(field["original_operator_fingerprint_sha256"] == bundle.read_snapshot(pointer).manifest[
            "original_operator_fingerprint_sha256"], "exported field does not match pre-solve operators")
        field.update(schema=SCHEMA, operator_bundle=copy.deepcopy(pointer), operator_bundle_execution=copy.deepcopy(outer))
        field["execution"]["role"] = "reused_frozen_first_order_core_execution"
        if field["disposition"].startswith("CONVERGED"):
            q = core.np.asarray(field["response"]["q"])
            chart = bundle.coordinate_map(prepared)
            field["panel_generalized_coefficients"] = {name: {**row, "global_dof_start": row["indices"][0],
                "coefficients": core.serial(q[row["indices"]])} for name, row in chart["panels"].items()}
        return field

    def write(path, payload):
        if payload.get("schema") in {"eoere_first_order_execution_interruption/v1", "eoere_first_order_execution_guard_failure/v1"}:
            payload = {**payload, "operator_bundle_execution": copy.deepcopy(outer),
                "operator_bundle": copy.deepcopy(context["operator_bundle"]),
                "attempted_operator_paths": [bundle.artifact_path(arrays_path), bundle.artifact_path(manifest_path)],
                "source_sha256": {**payload["source_sha256"], **context["bundle_pins"]}}
        FROZEN_WRITE(path, payload)

    with patch.object(core, "execute", execute), patch.object(core, "runtime_pins", runtime_pins), patch.object(core, "write_exclusive", write):
        yield context


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--out", type=Path, required=True)
    args, _ = parser.parse_known_args()
    with execution_context(args.out, list(sys.orig_argv)):
        return FROZEN_MAIN()


if __name__ == "__main__":
    raise SystemExit(main())
